"""Optional isolated public/read-only feeds. No financial database or order endpoints."""

import asyncio
import json
import os
import time
import secrets
from pathlib import Path
from contextlib import asynccontextmanager
from collections import deque
from fastapi import FastAPI, Request, HTTPException
from websockets.asyncio.client import connect
from .markets import CoinbaseAdapter, AlpacaAdapter, utcnow
from .market import KrakenPublicProvider
from .providers import CoinbaseStream, coinbase_trades, alpaca_events, RevisionTape

CONFIG_PATH = Path(os.getenv("MTT_MARKET_CONFIG", "/run/secrets/providers"))
TOKEN_PATH = Path(os.getenv("MTT_MARKET_TOKEN", "/run/secrets/market_token"))
CONFIG = (
    json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {"enabled": False}
)
TOKEN = TOKEN_PATH.read_text().strip() if TOKEN_PATH.exists() else ""


class FeedStore:
    def __init__(self):
        self.quotes = {}
        self.books = {}
        self.trades = {}
        self.health = {}
        self.revision_tape = RevisionTape()
        self.bars = {}

    def status(self, key, status, reason=None):
        prior = self.health.get(key, {})
        self.health[key] = {
            **prior,
            "status": status,
            "reason": reason,
            "updated_at": utcnow(),
            "updated_monotonic": time.monotonic(),
            "mode": "READ_ONLY_LIVE",
            "live_verified": False,
            "data_received": prior.get("data_received", False) or status == "RECEIVING",
        }

    def quote(self, q):
        self.quotes[q["instrument_id"]] = {**q, "stored_monotonic": time.monotonic()}

    def trade(self, t):
        buffer = self.trades.setdefault(t["instrument_id"], deque(maxlen=500))
        if not any(x["event_id"] == t["event_id"] for x in buffer):
            buffer.append(t)

    def snapshot(self):
        now = time.monotonic()
        quotes = []
        for q in self.quotes.values():
            result = {k: v for k, v in q.items() if k != "stored_monotonic"}
            age = now - q["stored_monotonic"]
            result["age_seconds"] = round(age, 3)
            if (
                age > 5
                or self.health.get(q["provider"] + ":quotes", {}).get("status")
                != "RECEIVING"
            ):
                result["quality"] = "STALE"
            quotes.append(result)
        health = {
            key: {k: v for k, v in status.items() if k != "updated_monotonic"}
            for key, status in self.health.items()
        }
        for key, status in self.health.items():
            if (
                status["status"] == "RECEIVING"
                and now - status["updated_monotonic"] > 15
            ):
                health[key]["status"] = "STALE"
        books = {key: dict(value) for key, value in self.books.items()}
        for key, value in books.items():
            if (
                health.get(key.split(":")[0] + ":level2", {}).get("status")
                != "RECEIVING"
            ):
                value.update(status="BOOK_UNTRUSTED", bids=[], asks=[])
        return {
            "mode": "READ_ONLY_LIVE",
            "quotes": quotes,
            "books": books,
            "trades": {k: list(v) for k, v in self.trades.items()},
            "health": health,
            "bars": self.bars,
            "execution_enabled": False,
            "retention": "Memory only; reset and resync after restart",
            "notices": self.revision_tape.missing[-20:],
        }


STORE = FeedStore()


def allowed(provider):
    p = CONFIG.get(provider, {})
    return (
        CONFIG.get("enabled") is True
        and p.get("enabled") is True
        and p.get("display_rights_confirmed") is True
    )


async def coinbase(channel):
    key = "coinbase:" + ("quotes" if channel == "ticker" else channel)
    STORE.status(key, "CONNECTING")
    book = CoinbaseStream()
    async with connect(
        CoinbaseAdapter.endpoint, open_timeout=8, max_size=1048576, proxy=None
    ) as ws:
        await ws.send(
            json.dumps(
                {
                    "type": "subscribe",
                    "channel": channel,
                    "product_ids": list(CoinbaseAdapter.symbols),
                }
            )
        )
        # A dedicated connection per channel makes its sequence scope unambiguous.
        await ws.send(json.dumps({"type": "subscribe", "channel": "heartbeats"}))
        async for raw in ws:
            message = json.loads(raw)
            if message.get("channel") == "ticker":
                for q in CoinbaseAdapter.quotes(raw):
                    STORE.quote(
                        q.model_copy(
                            update={"rights": "OPERATOR_CONFIRMED_DISPLAY"}
                        ).model_dump()
                    )
                STORE.status(key, "RECEIVING")
            elif message.get("channel") == "market_trades":
                for t in coinbase_trades(raw):
                    STORE.trade(t)
                STORE.status(key, "RECEIVING")
            elif channel == "level2" and message.get("channel") in {
                "l2_data",
                "heartbeats",
            }:
                result = book.ingest(raw)
                if result["status"] == "RESYNC_REQUIRED":
                    raise ValueError("RESYNC_REQUIRED")
                for product, b in result.get("books", {}).items():
                    STORE.books["coinbase:" + product] = {
                        **b,
                        "quality": "REALTIME_UNVERIFIED",
                        "source": "coinbase-level2",
                        "received_at": utcnow(),
                    }
                STORE.status(
                    key,
                    "RECEIVING"
                    if result["status"] == "SYNCED"
                    else "AWAITING_SNAPSHOT",
                )
            elif message.get("channel") == "heartbeats":
                STORE.status(key, STORE.health[key]["status"])
            elif message.get("type") == "error":
                raise ValueError("PROVIDER_REJECTED_SUBSCRIPTION")


async def kraken(channel):
    key = "kraken:" + ("quotes" if channel == "ticker" else channel)
    STORE.status(key, "CONNECTING")
    async with connect(
        "wss://ws.kraken.com/v2", open_timeout=8, max_size=1048576, proxy=None
    ) as ws:
        await ws.send(
            json.dumps(
                {
                    "method": "subscribe",
                    "params": {
                        "channel": channel,
                        "symbol": ["BTC/EUR", "ETH/EUR", "SOL/EUR"],
                    },
                }
            )
        )
        async for raw in ws:
            message = json.loads(raw)
            if message.get("channel") == "ticker":
                # Parse raw numbers with Decimal before constructing each message.
                from .markets import decode

                original = decode(raw)
                for row in original["data"]:
                    q = KrakenPublicProvider.normalize_ticker(
                        json.dumps({**original, "data": [row]}, default=str)
                    ).model_dump()
                    at = q["source_time"]
                    received = q["received_at"]
                    STORE.quote(
                        {
                            "instrument_id": q["instrument_id"],
                            "economic_id": q["instrument_id"]
                            .split(":")[1]
                            .split("-")[0],
                            "provider": "kraken",
                            "venue": "KRAKEN_SPOT",
                            "origin_feed": q["origin_feed_id"],
                            "currency": "EUR",
                            "bid": q["bid"],
                            "ask": q["ask"],
                            "last": q["last"],
                            "source_time": at if at != "NOT_PROVIDED" else received,
                            "time_basis": "PROVIDER"
                            if at != "NOT_PROVIDED"
                            else "RECEIVED_ONLY",
                            "received_at": received,
                            "quality": "REALTIME_UNVERIFIED",
                            "delay_ms": 0,
                            "session": "CONTINUOUS",
                            "adjustment": "RAW",
                            "rights": "OPERATOR_CONFIRMED_DISPLAY",
                        }
                    )
                STORE.status(key, "RECEIVING")
            elif message.get("channel") == "trade":
                for t in KrakenPublicProvider.normalize_trades(raw):
                    STORE.trade(t.model_dump())
                STORE.status(key, "RECEIVING")
            elif message.get("success") is False:
                raise ValueError("PROVIDER_REJECTED_SUBSCRIPTION")
            elif message.get("channel") == "heartbeat":
                STORE.status(key, STORE.health[key]["status"])


async def alpaca():
    c = CONFIG.get("alpaca", {})
    feed = c.get("feed", "iex")
    key = "alpaca:quotes"
    STORE.status(key, "CONNECTING")
    if not c.get("key") or not c.get("secret"):
        STORE.status(key, "NOT_RUN_MISSING_CREDENTIALS")
        return
    if feed not in AlpacaAdapter.feeds or feed not in c.get("entitlements", []):
        STORE.status(key, "ENTITLEMENT_DENIED")
        return
    async with connect(
        "wss://stream.data.alpaca.markets/v2/" + feed,
        open_timeout=8,
        max_size=1048576,
        proxy=None,
    ) as ws:
        await ws.send(
            json.dumps({"action": "auth", "key": c["key"], "secret": c["secret"]})
        )
        async for raw in ws:
            messages = json.loads(raw)
            for m in messages:
                if m.get("T") == "error":
                    STORE.status(key, "ENTITLEMENT_OR_AUTH_ERROR")
                    return
                if m.get("msg") == "authenticated":
                    await ws.send(
                        json.dumps(
                            {
                                "action": "subscribe",
                                "quotes": list(AlpacaAdapter.symbols),
                                "trades": list(AlpacaAdapter.symbols),
                                "bars": list(AlpacaAdapter.symbols),
                                "updatedBars": list(AlpacaAdapter.symbols),
                            }
                        )
                    )
            quotes = AlpacaAdapter.quotes(raw, feed, c["entitlements"])
            for q in quotes:
                STORE.quote(
                    q.model_copy(
                        update={"rights": "OPERATOR_CONFIRMED_DISPLAY"}
                    ).model_dump()
                )
            if quotes:
                STORE.status(key, "RECEIVING")
            for event in alpaca_events(raw, feed, c["entitlements"]):
                instrument = event["instrument_id"]
                if event["kind"] in {"TRADE", "CORRECTION", "CANCEL"}:
                    STORE.revision_tape.ingest(event)
                    del STORE.revision_tape.revisions[:-3000]
                    del STORE.revision_tape.missing[:-100]
                    STORE.trades[instrument] = deque(
                        [
                            v
                            for v in STORE.revision_tape.trades.values()
                            if v["instrument_id"] == instrument
                        ][-500:],
                        maxlen=500,
                    )
                    # Bounded observation window; missing old corrections stay explicit.
                    if len(STORE.revision_tape.trades) > 3000:
                        STORE.revision_tape.trades.pop(
                            next(iter(STORE.revision_tape.trades))
                        )
                else:
                    bars = STORE.bars.setdefault(instrument, [])
                    previous = next(
                        (x for x in bars if x["source_time"] == event["source_time"]),
                        None,
                    )
                    if previous:
                        bars.remove(previous)
                    bars.append(event)
                    bars.sort(key=lambda x: x["source_time"])
                    del bars[:-2000]


async def supervise(provider, channel, operation):
    attempts = 0
    key = provider + ":" + channel
    while True:
        try:
            await asyncio.wait_for(operation(), timeout=3600)
            if STORE.health.get(key, {}).get("status") in {
                "NOT_RUN_MISSING_CREDENTIALS",
                "ENTITLEMENT_DENIED",
                "ENTITLEMENT_OR_AUTH_ERROR",
            }:
                return
            raise ConnectionError("STREAM_ENDED_RESYNC_REQUIRED")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            attempts += 1
            STORE.status(key, "RESYNC_REQUIRED", type(e).__name__)
            for instrument in list(STORE.books):
                if instrument.startswith(provider + ":"):
                    STORE.books[instrument] = {
                        **STORE.books[instrument],
                        "status": "BOOK_UNTRUSTED",
                        "bids": [],
                        "asks": [],
                    }
            await asyncio.sleep(min(30, 2 ** min(attempts, 5)))


@asynccontextmanager
async def lifespan(app):
    tasks = []
    if allowed("coinbase"):
        for channel in ["ticker", "market_trades", "level2"]:
            tasks.append(
                asyncio.create_task(
                    supervise(
                        "coinbase",
                        "quotes" if channel == "ticker" else channel,
                        lambda ch=channel: coinbase(ch),
                    )
                )
            )
    if allowed("kraken"):
        for channel in ["ticker", "trade"]:
            tasks.append(
                asyncio.create_task(
                    supervise(
                        "kraken",
                        "quotes" if channel == "ticker" else channel,
                        lambda ch=channel: kraken(ch),
                    )
                )
            )
    if allowed("alpaca"):
        tasks.append(asyncio.create_task(supervise("alpaca", "quotes", alpaca)))
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health():
    return {"status": "ok", "enabled": CONFIG.get("enabled", False), "orders": False}


@app.get("/snapshot")
def snapshot(request: Request):
    if not TOKEN or not secrets.compare_digest(
        request.headers.get("authorization", ""), "Bearer " + TOKEN
    ):
        raise HTTPException(403, "INTERNAL_ACCESS_REQUIRED")
    return STORE.snapshot()
