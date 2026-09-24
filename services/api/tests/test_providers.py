import json
import pytest
from app.providers import (
    CoinbaseStream,
    coinbase_trades,
    alpaca_events,
    RevisionTape,
    ecb_reference,
    sec_facts,
    SourceHealth,
    select_source,
)


def book_message(sequence, product="BTC-EUR", kind="snapshot"):
    return json.dumps(
        {
            "channel": "l2_data",
            "timestamp": "2026-09-24T12:00:00Z",
            "sequence_num": sequence,
            "events": [
                {
                    "product_id": product,
                    "type": kind,
                    "updates": [
                        {"side": "bid", "price_level": "100", "new_quantity": "2"},
                        {"side": "offer", "price_level": "101", "new_quantity": "3"},
                    ],
                }
            ],
        }
    )


def test_coinbase_multi_product_sequence_gap_and_sleep_wake():
    stream = CoinbaseStream()
    assert stream.ingest(book_message(0))["status"] == "SYNCED"
    stream.ingest(book_message(1, "ETH-EUR"))
    assert stream.ingest(book_message(2, kind="update"))["status"] == "SYNCED"
    assert stream.ingest(book_message(2, kind="update"))["status"] == "DUPLICATE"
    assert stream.ingest(book_message(4, kind="update"))["status"] == "RESYNC_REQUIRED"
    assert not stream.books["BTC-EUR"].summary()["bids"]
    assert stream.ingest(book_message(0))["status"] == "AWAITING_SNAPSHOT"
    assert stream.ingest(book_message(1, "ETH-EUR"))["status"] == "SYNCED"
    stream.disconnect("SLEEP_WAKE")
    assert not stream.books["BTC-EUR"].summary()["bids"]


def test_coinbase_maker_side_is_inverted_not_mislabeled():
    raw = json.dumps(
        {
            "channel": "market_trades",
            "events": [
                {
                    "trades": [
                        {
                            "trade_id": "123",
                            "product_id": "BTC-EUR",
                            "time": "2026-09-24T12:00:00Z",
                            "price": "100",
                            "size": "0.1",
                            "side": "BUY",
                        }
                    ]
                }
            ],
        }
    )
    assert coinbase_trades(raw)[0]["taker_side"] == "SELL"


def test_alpaca_correction_cancel_preserves_provenance_and_unknown_side():
    items = [
        {
            "T": "t",
            "S": "AAPL",
            "i": 1,
            "x": "Q",
            "p": 100,
            "s": 2,
            "t": "2026-09-24T12:00:00Z",
        },
        {
            "T": "c",
            "S": "AAPL",
            "oi": 1,
            "ci": 2,
            "x": "Q",
            "cp": 101,
            "cs": 3,
            "t": "2026-09-24T12:00:01Z",
        },
        {
            "T": "x",
            "S": "AAPL",
            "i": 2,
            "x": "Q",
            "p": 101,
            "s": 3,
            "t": "2026-09-24T12:00:02Z",
        },
    ]
    events = alpaca_events(json.dumps(items), "iex", ["iex"])
    tape = RevisionTape()
    for e in events:
        tape.ingest(e)
    assert not tape.trades and len(tape.revisions) == 2 and not tape.missing
    assert events[0]["taker_side"] == "UNKNOWN"
    with pytest.raises(PermissionError):
        alpaca_events(json.dumps(items), "sip", ["iex"])
    orphan = RevisionTape()
    orphan.ingest(events[-1])
    assert orphan.missing[0]["status"] == "RECONCILIATION_REQUIRED"


def test_ecb_decimal_pivot_and_xml_security():
    fx = ecb_reference(
        '<Envelope><Cube><Cube time="2025-01-02"><Cube currency="USD" rate="1.10"/><Cube currency="GBP" rate="0.88"/></Cube></Cube></Envelope>'
    )
    assert fx.convert("110", "USD", "GBP")["amount"] == "88.00"
    with pytest.raises(ValueError):
        fx.convert("1", "EUR", "USD", "EXECUTION")
    with pytest.raises(ValueError):
        ecb_reference("<!DOCTYPE x><x/>")


def test_sec_cutoff_keeps_original_and_later_amendment_separate():
    original = {
        "filed": "2025-02-01",
        "end": "2024-12-31",
        "val": 1000,
        "accn": "original",
        "form": "10-K",
        "fp": "FY",
    }
    amendment = {
        **original,
        "filed": "2025-04-01",
        "val": 900,
        "accn": "amended",
        "form": "10-K/A",
    }
    raw = json.dumps(
        {
            "cik": 123,
            "entityName": "SYNTHETIC TEST COMPANY",
            "facts": {
                "us-gaap": {"Revenues": {"units": {"USD": [original, amendment]}}}
            },
        }
    )
    assert len(sec_facts(raw, "0000000123", "2025-03-01")["facts"]) == 1
    assert len(sec_facts(raw, "0000000123", "2025-05-01")["facts"]) == 2
    with pytest.raises(ValueError):
        sec_facts(raw, "456", "2025-05-01")


def test_source_health_and_priority_never_upgrade_entitlements():
    health = SourceHealth()
    health.update("SYNCED", 100)
    assert health.status(101)["usable"]
    assert health.status(106)["state"] == "STALE"
    for state in ["RATE_LIMITED", "ENTITLEMENT_DENIED", "SLEEP_WAKE", "DISCONNECTED"]:
        health.update(state, 107)
        assert not health.status(108)["usable"]
    a = {
        "provider": "a",
        "health": "SYNCED",
        "display_rights": True,
        "feed": "iex",
        "delay_ms": 0,
    }
    b = {**a, "provider": "b", "feed": "sip"}
    assert (
        select_source([a, b], ["b", "a"], {"feed": "iex", "delay_ms": 0})["selected"]
        == a
    )
    assert select_source([b], ["b"], {"feed": "iex"})["selected"] is None


def test_local_reminder_reconnect_distinguishes_missed_monitoring():
    from app.calendar import empty, tick, instant

    st = empty()
    st["last_tick"] = "2026-09-24T12:00:00Z"
    st["reminders"] = [
        {"id": "fixture", "scheduled_at": "2026-09-24T12:00:05Z", "status": "PENDING"}
    ]
    tick(st, instant("2026-09-24T12:00:06Z"))
    assert st["reminders"][0]["status"] == "DUE"
    st["reminders"].append(
        {
            "id": "offline-fixture",
            "scheduled_at": "2026-09-24T12:02:00Z",
            "status": "PENDING",
        }
    )
    tick(st, instant("2026-09-24T13:00:00Z"))
    assert (
        st["reminders"][1]["status"] == "MISSED_MONITORING_WINDOW"
        and st["monitoring_gaps"]
    )
