from app.market_service import FeedStore, allowed
from app.markets import CoinbaseAdapter


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
