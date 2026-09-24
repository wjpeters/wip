"""All mutation tests share an isolated throwaway database, not the user's account."""

import test_api as fixtures
from app import main, worker
from psycopg.types.json import Jsonb
import base64

client = fixtures.client


def post(client, path, body):
    r = client.post(path, json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_market_research_context_and_safe_import(client):
    assert len(client.get("/market/catalog").json()["instruments"]) >= 6
    c = client.get("/market/context").json()
    assert c["book"]["status"] == "SYNCED" and c["profile"]["quality"] == "SIMULATED"
    assert (
        client.get("/market/context?instrument_id=metadata:AAPL").json()["comparison"][
            "status"
        ]
        == "MISSING_DATA"
    )
    assert (
        post(client, "/market/adapter-test/coinbase", {})["verification"]
        == "TESTED_WITH_FIXTURES"
    )
    assert post(client, "/market/adapter-test/alpaca", {})["live_verified"] is False
    assert (
        client.post(
            "/research/import-feed",
            json={
                "content": "<bad",
                "publisher": "Fixture",
                "source_family": "fixture",
                "region": "EU",
                "display_rights_confirmed": True,
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/market/fx",
            json={"amount": "1", "base": "EUR", "quote": "USD", "purpose": "EXECUTION"},
        ).status_code
        == 422
    )


def test_personal_is_empty_and_import_confirmation_is_atomic(client):
    assert client.get("/finance/PERSONAL").json()["entities"] == []
    post(client, "/finance/DEMO/load-example", {})
    content = "date,type,amount,currency,account,reference\n2025-01-01,INCOME,100,EUR,demo-bank,test-income\n"
    p = post(client, "/finance/DEMO/imports/preview", {"content": content})
    assert p["importable"] == 1
    before = client.get("/finance/DEMO").json()["cash_eur"]
    r = post(client, "/finance/DEMO/imports/confirm", {"preview_id": p["preview_id"]})
    assert r["imported"] == 1
    assert (
        post(client, "/finance/DEMO/imports/confirm", {"preview_id": p["preview_id"]})
        == r
    )
    again = post(client, "/finance/DEMO/imports/preview", {"content": content})
    assert again["duplicates"] == 1
    conflict = post(
        client,
        "/finance/DEMO/imports/preview",
        {"content": content.replace(",100,", ",200,")},
    )
    assert conflict["review_count"] == 1
    assert (
        client.post(
            "/finance/DEMO/imports/confirm", json={"preview_id": conflict["preview_id"]}
        ).status_code
        == 422
    )
    assert client.get("/finance/DEMO").json()["cash_eur"] != before
    assert client.get("/finance/PERSONAL").json()["journal"] == []


def test_changed_revision_invalidates_import_and_personal_csrf(client):
    p = post(
        client,
        "/finance/DEMO/imports/preview",
        {
            "content": "date,type,amount,currency,account,reference\n2025-01-02,INCOME,1,EUR,demo-bank,revision-test\n"
        },
    )
    post(client, "/finance/DEMO/entities", {"name": "Extra fixture", "kind": "PERSON"})
    assert (
        client.post(
            "/finance/DEMO/imports/confirm", json={"preview_id": p["preview_id"]}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/finance/PERSONAL/entities",
            json={"name": "Denied", "kind": "PERSON"},
            headers={"x-csrf-token": ""},
        ).status_code
        == 403
    )


def test_tax_registry_concepts_and_approval_gate(client):
    registry = client.get("/tax/rules").json()
    assert registry["test_report"]["passed"]
    body = {
        "calculator": "box2",
        "scope": "DEMO",
        "concept": True,
        "inputs": {
            "resident_full_year": True,
            "inputs_complete": True,
            "gross_income": "10000",
            "dividend_tax_withheld": "1500",
        },
    }
    result = post(client, "/tax/calculate", body)
    assert result["result"]["remaining_tax"] == "950.00"
    assert (
        client.post("/tax/calculate", json={**body, "concept": False}).status_code
        == 422
    )
    assert (
        client.post(
            "/tax/review",
            json={
                "rule_hash": registry["hash"],
                "binding": registry["current_binding"],
                "decision": "APPROVE",
                "reviewer": "Fixture reviewer",
                "note": "Evidence not fetched so approval must fail",
                "scope_understood": True,
            },
        ).status_code
        == 422
    )
    assert client.get("/analysis/" + result["id"]).json()["result"] == result
    assert client.get("/forms").json()["scenario"]["additionalProperties"] is False


def test_encrypted_document_persists_and_never_crosses_scope(client):
    text = b"Synthetic confidential test document"
    r = post(
        client,
        "/vault/DEMO",
        {
            "name": "fixture.txt",
            "mime": "text/plain",
            "content_b64": base64.b64encode(text).decode(),
            "category": "OTHER",
            "entity_id": "",
        },
    )
    listed = client.get("/vault/DEMO").json()
    assert listed["documents"][0]["name"] == "fixture.txt"
    response = client.get("/vault/DEMO/" + r["id"] + "/download")
    assert response.content == text
    assert response.headers["content-disposition"].startswith("attachment;")
    assert client.get("/vault/PERSONAL/" + r["id"] + "/download").status_code == 404
    with main.db() as c:
        raw = c.execute(
            "SELECT ciphertext,name FROM vault WHERE id=%s", (r["id"],)
        ).fetchone()
        assert text not in bytes(raw[0]) and "fixture.txt" not in raw[1]


def test_background_backtest_snapshot_and_cancel(client):
    payload = {
        "instrument_id": "sim:BTC-EUR",
        "short_window": 5,
        "long_window": 20,
        "start": 0,
        "end": 119,
    }
    j = post(client, "/lab/backtest", payload)
    with main.db() as c:
        row = c.execute(
            "SELECT kind,request FROM analysis_jobs WHERE id=%s", (j["id"],)
        ).fetchone()
    output = worker.execute(*row)
    with main.db() as c:
        c.execute(
            "UPDATE analysis_jobs SET status='COMPLETED',result=%s WHERE id=%s",
            (Jsonb(output), j["id"]),
        )
    assert (
        client.get("/analysis/" + j["id"]).json()["result"]["live_execution"] is False
    )
    next_job = post(client, "/lab/backtest", payload)
    assert post(client, "/analysis/" + next_job["id"] + "/cancel", {})["canceled"]
    assert client.get("/analysis/" + next_job["id"]).json()["status"] == "CANCELED"


def test_ai_consent_scope_single_use_and_no_provider(client, monkeypatch):
    monkeypatch.delenv("AI_BRIDGE_URL", raising=False)
    status = client.get("/ai/research/status").json()
    assert status["privacy"] == "LOCAL_ONLY" and not status["enabled"]
    assert (
        post(client, "/ai/local-explanation", {"topic": "fees"})["cloud_call"] is False
    )
    payload = {
        "provider": "CODEX",
        "prompt": "Leg deze fictieve bron uit.",
        "source_ids": [status["public_sources"][0]["id"]],
        "conversation_id": "11111111-1111-4111-8111-111111111111",
    }
    assert (
        client.post(
            "/ai/research/preview",
            json={**payload, "source_ids": ["personal-document"]},
        ).status_code
        == 422
    )
    preview = post(client, "/ai/research/preview", payload)
    assert preview["payload"]["context"]["scope"] == "PUBLIC_OR_SYNTHETIC"
    assert not preview["payload"]["context"]["calculations"]
    assert (
        client.post(
            "/ai/research/stream",
            json={"preview_id": preview["preview_id"], "public_confirmed": False},
        ).status_code
        == 422
    )
    response = client.post(
        "/ai/research/stream",
        json={"preview_id": preview["preview_id"], "public_confirmed": True},
    )
    import json

    result = json.loads(response.text)["result"]
    assert result["disposition"] == "ABSTAIN" and result["cloud_call"] is False
    assert (
        client.post(
            "/ai/research/stream",
            json={"preview_id": preview["preview_id"], "public_confirmed": True},
        ).status_code
        == 409
    )
    assert (
        client.get("/ai/research/conversations").json()["conversations"][0]["turns"][0][
            "result"
        ]
        == result
    )


def test_local_calendar_no_external_delivery_and_readonly_service_off(
    client, monkeypatch
):
    monkeypatch.delenv("MARKET_BRIDGE_URL", raising=False)
    assert client.get("/market/live").json()["status"] == "NOT_CONFIGURED"
    row = post(
        client,
        "/calendar/local",
        {
            "title": "SYNTHETIC TEST DEADLINE",
            "scheduled_at": "2030-01-01T12:00:00Z",
            "timezone": "Europe/Amsterdam",
            "scope": "DEMO",
            "source": "fixture",
        },
    )
    assert row["status"] == "PENDING"
    assert not client.get("/calendar/local?scope=PERSONAL").json()["reminders"]
    assert post(client, "/calendar/local/" + row["id"] + "/acknowledge", {})["saved"]
    assert (
        client.get("/calendar/local?scope=DEMO").json()["reminders"][0]["status"]
        == "ACKNOWLEDGED"
    )


def test_performance_schema_blocks_invalid_amounts(client):
    payload = {
        "periods": [{"start": "10000", "end": "12000", "external_flow": "1000"}],
        "flows": [
            {"date": "2025-01-01", "amount": "-10000"},
            {"date": "2026-01-01", "amount": "11000"},
        ],
    }
    assert post(client, "/finance/performance/calculate", payload)["twr"] == "0.100000"
    payload["periods"][0]["start"] = "NaN"
    assert (
        client.post("/finance/performance/calculate", json=payload).status_code == 422
    )


def test_asset_revaluation_and_news_json_contract(client):
    post(client, "/finance/DEMO/load-example", {})
    body = {
        "name": "Synthetic house",
        "entity": "private",
        "kind": "PROPERTY",
        "value_eur": "10000",
        "as_of": "2025-01-01",
    }
    aid = post(client, "/finance/DEMO/assets", body)["id"]
    post(
        client,
        "/finance/DEMO/assets",
        {**body, "asset_id": aid, "value_eur": "11000", "as_of": "2025-02-01"},
    )
    assets = client.get("/finance/DEMO").json()["assets"]
    assert len([a for a in assets if a["id"] == aid]) == 1
    assert next(a for a in assets if a["id"] == aid)["value_eur"] == "11000"
    assert (
        client.post(
            "/finance/DEMO/assets", json={**body, "asset_id": "unknown"}
        ).status_code
        == 404
    )
    import json

    article = {
        "title": "Synthetic primary source",
        "url": "https://example.invalid/test",
        "published_at": "2025-01-01T12:00:00Z",
        "instruments": ["BTC"],
    }
    payload = {
        "format": "NEWS_JSON",
        "content": json.dumps({"articles": [article]}),
        "publisher": "Synthetic",
        "source_family": "fixture-contract",
        "region": "EU",
        "display_rights_confirmed": True,
    }
    post(client, "/research/import-feed", payload)
    payload["content"] = json.dumps({"articles": [{**article, "instruments": 123}]})
    assert client.post("/research/import-feed", json=payload).status_code == 422


def test_entity_impact_uses_owner_cash_revision_and_separate_reserves(client):
    from test_planning import scenario

    b = client.get("/finance/DEMO").json()
    s = scenario().model_dump()
    s.update(
        entity_id="private", source_revision=b["revision"], initial_tax_reserve="1000"
    )
    j = post(client, "/plans/analyze", {"scenario": s})
    with main.db() as c:
        c.execute(
            "UPDATE analysis_jobs SET status='COMPLETED',result=%s WHERE id=%s",
            (Jsonb({"fixture": True}), j["id"]),
        )
    payload = {
        "scope": "DEMO",
        "account_id": "demo-bank",
        "scenario_id": j["id"],
        "trade_amount": "100",
        "fee": "1",
        "long_term_reserve": "500",
        "trading_pot": "2000",
    }
    r = post(client, "/plans/entity-impact", payload)
    assert r["entity_id"] == "private" and r["source_revision"] == b["revision"]
    assert (
        client.post(
            "/plans/entity-impact", json={**payload, "account_id": "demo-holding"}
        ).status_code
        == 422
    )
    post(
        client, "/finance/DEMO/entities", {"name": "Revision fixture", "kind": "PERSON"}
    )
    assert client.post("/plans/entity-impact", json=payload).status_code == 409
