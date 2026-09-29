from app.market_service import FeedStore, allowed
from app.markets import CoinbaseAdapter, select_display_quotes


def test_default_optional_service_has_no_credentials_or_orders():
    assert not allowed("coinbase") and not allowed("alpaca")
    assert FeedStore().snapshot()["execution_enabled"] is False


def test_readonly_source_stale_and_book_cleared_on_disconnect():
    store = FeedStore()
    q = CoinbaseAdapter.quotes(
        '{"channel":"ticker","timestamp":"2026-09-24T12:00:00Z","events":[{"tickers":[{"product_id":"BTC-EUR","best_bid":"100","best_ask":"101","price":"100.5"}]}]}'
    )[0].model_dump()
    store.status("coinbase:quotes", "RECEIVING")
    store.quote(q)
    assert store.snapshot()["quotes"][0]["quality"] == "REALTIME_UNVERIFIED"
    store.books[q["instrument_id"]] = {
        "status": "SYNCED",
        "bids": [["100", "1"]],
        "asks": [["101", "1"]],
    }
    store.status("coinbase:level2", "RECEIVING")
    assert store.snapshot()["books"][q["instrument_id"]]["bids"]
    store.status("coinbase:quotes", "RESYNC_REQUIRED")
    store.status("coinbase:level2", "RESYNC_REQUIRED")
    snapshot = store.snapshot()
    assert (
        snapshot["quotes"][0]["quality"] == "STALE"
        and not snapshot["books"][q["instrument_id"]]["bids"]
    )


def test_coinbase_transport_only_subscribes_and_normalizes(monkeypatch):
    import asyncio
    import json
    from app import market_service as m

    sent = []

    class Socket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def send(self, text):
            sent.append(json.loads(text))

        def __aiter__(self):
            return self

        async def __anext__(self):
            if len(sent) > 2:
                raise StopAsyncIteration
            sent.append({"fixture": "received"})
            return '{"channel":"ticker","timestamp":"2026-09-24T12:00:00Z","events":[{"tickers":[{"product_id":"BTC-EUR","best_bid":"100","best_ask":"101","price":"100.5"}]}]}'

    monkeypatch.setattr(m, "connect", lambda *a, **kw: Socket())
    monkeypatch.setattr(m, "STORE", FeedStore())
    asyncio.run(m.coinbase("ticker"))
    assert [v["type"] for v in sent[:2]] == ["subscribe", "subscribe"]
    assert m.STORE.snapshot()["quotes"][0]["bid"] == "100"
    assert m.STORE.snapshot()["quotes"][0]["session"] == "CONTINUOUS"
    assert m.STORE.health["coinbase:quotes"]["live_verified"] is False


def test_normal_disconnect_marks_resync_before_retry(monkeypatch):
    import asyncio
    from app import market_service as m

    monkeypatch.setattr(m, "STORE", FeedStore())

    async def ended():
        return

    async def stop(delay):
        raise asyncio.CancelledError()

    monkeypatch.setattr(m.asyncio, "sleep", stop)
    try:
        asyncio.run(m.supervise("coinbase", "quotes", ended))
    except asyncio.CancelledError:
        pass
    assert m.STORE.health["coinbase:quotes"]["status"] == "RESYNC_REQUIRED"

def test_display_router_fails_over_only_to_fresh_compatible_rights_confirmed_quote():
    base = {
        "economic_id": "BTC",
        "currency": "EUR",
        "session": "CONTINUOUS",
        "adjustment": "RAW",
        "delay_ms": 0,
        "quality": "REALTIME_UNVERIFIED",
        "rights": "OPERATOR_CONFIRMED_DISPLAY",
        "age_seconds": 0.4,
        "bid": "100",
        "ask": "101",
    }
    quotes = [
        {**base, "provider": "kraken", "venue": "KRAKEN_SPOT", "quality": "STALE"},
        {**base, "provider": "coinbase", "venue": "COINBASE_SPOT"},
    ]
    health = {
        "kraken:quotes": {"status": "RESYNC_REQUIRED"},
        "coinbase:quotes": {"status": "RECEIVING"},
    }
    result = select_display_quotes(quotes, health, ["kraken", "coinbase"])
    assert len(result) == 1
    assert result[0]["state"] == "AUTO_FAILOVER"
    assert result[0]["selected"]["provider"] == "coinbase"
    assert result[0]["execution_allowed"] is False


def test_display_router_never_fails_over_across_delay_or_unconfirmed_rights():
    base = {
        "economic_id": "AAPL",
        "currency": "USD",
        "session": "REGULAR",
        "adjustment": "RAW",
        "delay_ms": 0,
        "quality": "REALTIME_UNVERIFIED",
        "rights": "UNVERIFIED",
        "age_seconds": 0.2,
        "bid": "200",
        "ask": "201",
    }
    quotes = [
        {**base, "provider": "alpaca"},
        {**base, "provider": "other", "delay_ms": 900000, "rights": "OPERATOR_CONFIRMED_DISPLAY"},
    ]
    health = {
        "alpaca:quotes": {"status": "RECEIVING"},
        "other:quotes": {"status": "RECEIVING"},
    }
    result = select_display_quotes(quotes, health, ["alpaca", "other"])
    assert len(result) == 2
    realtime = next(route for route in result if route["delay_ms"] == 0)
    delayed = next(route for route in result if route["delay_ms"] == 900000)
    assert realtime["state"] == "NO_ELIGIBLE_SOURCE"
    assert realtime["selected"] is None
    assert delayed["state"] == "PRIMARY"
    assert delayed["selected"]["provider"] == "other"
