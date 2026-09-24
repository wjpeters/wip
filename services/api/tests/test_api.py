"""Integration tests use a throwaway database. Never mutate the user's mtt database."""

import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import psycopg
from psycopg import sql
import pytest
from fastapi.testclient import TestClient
from app import main


@pytest.fixture(scope="module")
def client():
    if not Path("/run/secrets/db_password").exists():
        pytest.skip("Integration tests run inside Docker with private Postgres")
    database = "test_mtt_" + uuid.uuid4().hex[:12]
    password = Path("/run/secrets/db_password").read_text().strip()
    admin = psycopg.connect(
        host="postgres",
        user="mtt",
        dbname="postgres",
        password=password,
        autocommit=True,
    )
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    original = main.db
    main.db = lambda: psycopg.connect(
        host="postgres", user="mtt", dbname=database, password=password
    )
    try:
        with TestClient(main.app, base_url=f"http://localhost:{main.PORT}") as c:
            c.headers["origin"] = f"http://localhost:{main.PORT}"
            pw = secrets.token_urlsafe(24)
            assert c.get("/session").json()["setup_required"]
            assert c.post("/session/setup", json={"password": pw}).status_code == 200
            result = c.post("/session", json={"password": pw})
            assert result.status_code == 200
            c.headers["x-csrf-token"] = result.json()["csrf"]
            yield c
    finally:
        main.db = original
        admin.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
        )
        admin.close()


def preview(client, **updates):
    intent = {
        "instrument_id": "sim:BTC-EUR",
        "side": "BUY",
        "quantity": "0.0100",
        "limit_price": "62500.00",
        **updates,
    }
    r = client.post("/orders/preview", json=intent)
    assert r.status_code == 200, r.text
    return r.json()


def test_origin_csrf_host_and_no_live_route(client):
    assert client.get("/bootstrap", headers={"host": "evil.example"}).status_code == 403
    assert (
        client.post(
            "/orders/preview", json={}, headers={"origin": "http://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/orders/preview", json={}, headers={"x-csrf-token": ""}
        ).status_code
        == 403
    )
    assert client.post("/orders/submit", json={}).status_code == 404
    assert (
        client.post(
            "/session/setup", json={"password": "another-test-password"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/orders/preview",
            json={
                "instrument_id": "sim:BTC-EUR",
                "side": "BUY",
                "quantity": "0.01",
                "limit_price": "62500",
                "mode": "LIVE",
            },
        ).status_code
        == 422
    )


def test_order_is_atomic_and_idempotent_under_concurrency(client):
    p = preview(client)
    body = {"preview_id": p["preview_id"]}
    with ThreadPoolExecutor(4) as pool:
        results = list(
            pool.map(lambda _: client.post("/orders/paper", json=body), range(4))
        )
    assert all(r.status_code == 200 for r in results)
    assert len({r.json()["order_id"] for r in results}) == 1
    after = client.get("/bootstrap").json()
    assert after["portfolio"]["cash"] == p["cash_after"]
    event = results[0].json()["order_id"]
    lines = client.get("/ledger").json()
    assert len([line for line in lines["lines"] if line["event_id"] == event]) == 3
    assert lines["balanced"]
    assert after["orders"][0]["portfolio_after"]["total"] == after["portfolio"]["total"]


def test_concurrent_previews_cannot_spend_old_cash(client):
    a = preview(client)
    b = preview(client)
    with ThreadPoolExecutor(2) as pool:
        r = list(
            pool.map(
                lambda p: client.post(
                    "/orders/paper", json={"preview_id": p["preview_id"]}
                ),
                [a, b],
            )
        )
    assert sorted(x.status_code for x in r) == [200, 409]


def test_expired_preview_and_tampering(client):
    p = preview(client)
    assert (
        client.post(
            "/orders/paper", json={"preview_id": p["preview_id"], "quantity": "1"}
        ).status_code
        == 422
    )
    with main.db() as c:
        c.execute(
            "UPDATE previews SET expires_at=now()-interval '1 second' WHERE id=%s",
            (p["preview_id"],),
        )
    assert (
        client.post("/orders/paper", json={"preview_id": p["preview_id"]}).status_code
        == 409
    )


def test_pause_blocks_and_invalidates_preview(client):
    p = preview(client)
    assert (
        client.post("/sources/demo-fixture/pause", json={"paused": True}).status_code
        == 200
    )
    assert all(
        q["quality"] == "STALE"
        for q in client.get("/bootstrap").json()["quotes"].values()
    )
    assert (
        client.post("/orders/paper", json={"preview_id": p["preview_id"]}).status_code
        == 409
    )
    r = client.post("/orders/preview", json=p["intent"])
    assert r.status_code == 422
    assert "STALE_DATA" in r.text
    assert (
        client.post("/sources/demo-fixture/pause", json={"paused": False}).status_code
        == 200
    )


def test_plan_changes_invalidate_preview_and_persist(client):
    p = preview(client)
    r = client.post(
        "/planning",
        json={"reserve": "30000.00", "monthly_in": "123.45", "monthly_out": "23.45"},
    )
    assert r.status_code == 200
    assert (
        client.post("/orders/paper", json={"preview_id": p["preview_id"]}).status_code
        == 409
    )
    w = client.get("/wealth").json()
    assert w["assumptions"]["reserve"] == "30000.00"
    assert len(w["cash_path"]) == 25


def test_all_instruments_fill_and_reconcile_on_restart(client):
    for instrument, quantity, limit in [
        ("sim:ETH-EUR", "0.1000", "3000.00"),
        ("sim:SOL-EUR", "1.0000", "115.00"),
    ]:
        p = preview(
            client, instrument_id=instrument, quantity=quantity, limit_price=limit
        )
        assert (
            client.post(
                "/orders/paper", json={"preview_id": p["preview_id"]}
            ).status_code
            == 200
        )
    before = client.get("/bootstrap").json()["portfolio"]
    main.migrate()
    after = client.get("/bootstrap").json()["portfolio"]
    assert before == after
    assert client.get("/ledger").json()["balanced"]


def test_health_ai_tax_and_sources_are_honest(client):
    assert client.get("/health").json()["privacy"] == "LOCAL_ONLY"
    assert client.get("/ai/status").json()["disposition"] == "ABSTAIN"
    assert client.get("/tax/status").json()["result"] is None
    sources = client.get("/sources").json()["sources"]
    assert sources[1]["verification"] == "NOT_RUN_EXTERNAL_NETWORK"
    assert (
        client.post("/sources/kraken/test", json={}).json()["verification"]
        == "TESTED_WITH_FIXTURES"
    )
    assert (
        client.get("/history", params={"instrument_id": "does-not-exist"}).status_code
        == 404
    )


def test_restart_refuses_corrupt_position(client):
    from copy import deepcopy

    with main.db() as c:
        original = main.get_state(c)
        corrupted = deepcopy(original)
        corrupted["positions"]["sim:BTC-EUR"]["quantity"] = "99.0000"
        main.save_state(c, corrupted)
    try:
        with pytest.raises(RuntimeError, match="INCOMPLETE_POSITION"):
            main.migrate()
    finally:
        with main.db() as c:
            main.save_state(c, original)
    main.migrate()


def test_snapshot_routes_agree_on_revision(client):
    snapshot = client.get("/bootstrap").json()
    ledger = client.get("/ledger").json()
    wealth = client.get("/wealth").json()
    assert snapshot["portfolio"]["revision"] == ledger["revision"] == wealth["revision"]
    assert snapshot["portfolio"]["cash"] == wealth["cash"]
    assert ledger["balanced"]
