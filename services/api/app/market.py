"""Bounded synthetic market and a separate Kraken read-only adapter. No execution APIs."""

import asyncio
import json
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal as D
from .contracts import Identity, Quote, Trade

FIXTURE_AT = "2026-09-24T12:00:00+00:00"
VALUES = {
    "BTC": ("62430.25", "62448.20", "62439.00", "0.050"),
    "ETH": ("2981.40", "2983.10", "2982.10", "1.50"),
    "SOL": ("113.90", "114.25", "114.10", "20.00"),
}
INSTRUMENTS = {
    "sim:" + base + "-EUR": Identity(
        instrument_id="sim:" + base + "-EUR",
        symbol=base + "/EUR",
        base=base,
        venue_id="SIMULATED",
        tick_size="0.01",
        lot_size="0.0001",
        min_notional="10.00",
        paper_supported=True,
    ).model_dump()
    for base in VALUES
}


def now():
    return datetime.now(timezone.utc).isoformat()


def fixture_quote(instrument_id, paused=False, revision=0):
    instrument = INSTRUMENTS[instrument_id]
    bid, ask, last, liquidity = VALUES[instrument["base"]]
    return Quote(
        instrument_id=instrument_id,
        bid=bid,
        ask=ask,
        last=last,
        available_quantity=liquidity,
        provider_id="demo-fixture",
        venue_id="SIMULATED",
        origin_feed_id="mtt-synthetic-v1",
        source_event_id="fixture-v1-" + instrument["base"],
        adapter_version="1.0.0",
        source_time=FIXTURE_AT,
        received_at=now(),
        license_status="OWN_SYNTHETIC",
        quality="STALE" if paused else "SIMULATED",
        revision=revision,
    )


def history(instrument_id, interval="1u"):
    if interval not in {"15m", "1u", "4u", "1d"}:
        raise ValueError("INVALID_INTERVAL")
    base = INSTRUMENTS[instrument_id]["base"]
    last = D(VALUES[base][2])
    rng = random.Random(base + interval + "v1")
    minutes = {"15m": 15, "1u": 60, "4u": 240, "1d": 1440}[interval]
    end = datetime.fromisoformat(FIXTURE_AT)
    closes = []
    price = last
    for _ in range(120):
        closes.append(price)
        price = (price * (D("1") - D(rng.randint(-65, 95)) / D("10000"))).quantize(
            D(".01")
        )
    closes.reverse()
    rows = []
    for i, close in enumerate(closes):
        op = closes[i - 1] if i else close * D(".999")
        spread = close * D(rng.randint(5, 35)) / D("10000")
        rows.append(
            {
                "time": int((end - timedelta(minutes=minutes * (119 - i))).timestamp()),
                "open": str(op.quantize(D(".01"))),
                "high": str((max(op, close) + spread).quantize(D(".01"))),
                "low": str((min(op, close) - spread).quantize(D(".01"))),
                "close": str(close),
                "volume": str(D(rng.randint(10, 800)) / D("100")),
                "sma20": str((sum(closes[i - 19 : i + 1]) / 20).quantize(D(".01")))
                if i >= 19
                else None,
            }
        )
    return {
        "instrument_id": instrument_id,
        "interval": interval,
        "quality": "SIMULATED",
        "fixture_version": "1",
        "source_time": FIXTURE_AT,
        "rows": rows,
    }


def fixture_trades(instrument_id):
    q = fixture_quote(instrument_id)
    return [
        Trade(
            event_id=f"demo-{instrument_id}-{i}",
            instrument_id=instrument_id,
            price=q.ask if i % 2 else q.bid,
            quantity="0.0010",
            taker_side="BUY" if i % 2 else "SELL",
            provider_id="demo-fixture",
            origin_feed_id="mtt-synthetic-v1",
            source_time=FIXTURE_AT,
            quality="SIMULATED",
        ).model_dump()
        for i in range(8)
    ]


class KrakenPublicProvider:
    """Contract-tested; explicitly opt-in CLI probe only. Never used for paper fill quotes."""

    provider_id = "kraken"

    @staticmethod
    def normalize_ticker(raw: str):
        data = json.loads(raw, parse_float=D, parse_int=D)
        if data.get("channel") != "ticker" or not data.get("data"):
            raise ValueError("NOT_A_TICKER")
        row = data["data"][0]
        symbol = row["symbol"]
        if symbol not in {"BTC/EUR", "ETH/EUR", "SOL/EUR"}:
            raise ValueError("UNMAPPED_SYMBOL")
        bid, ask, last = [D(str(row[k])) for k in ["bid", "ask", "last"]]
        if not all(x.is_finite() and x > 0 for x in [bid, ask, last]) or ask < bid:
            raise ValueError("INVALID_QUOTE")
        return Quote(
            instrument_id="kraken:" + symbol.replace("/", "-"),
            bid=str(bid),
            ask=str(ask),
            last=str(last),
            available_quantity="0",
            provider_id="kraken",
            venue_id="KRAKEN_SPOT",
            origin_feed_id="kraken-ws-v2-ticker",
            source_event_id="snapshot",
            adapter_version="1.0.0",
            source_time=str(row.get("timestamp", "NOT_PROVIDED")),
            received_at=now(),
            license_status="UNVERIFIED",
            quality="READ_ONLY_PUBLIC",
            revision=0,
        )

    @staticmethod
    def normalize_trades(raw: str):
        data = json.loads(raw, parse_float=D, parse_int=D)
        if data.get("channel") != "trade":
            raise ValueError("NOT_TRADES")
        events = []
        for row in data["data"]:
            if row["symbol"] not in {"BTC/EUR", "ETH/EUR", "SOL/EUR"}:
                raise ValueError("UNMAPPED_SYMBOL")
            if D(str(row["price"])) <= 0 or D(str(row["qty"])) <= 0:
                raise ValueError("INVALID_TRADE")
            events.append(
                Trade(
                    event_id="kraken-trade-" + str(row["trade_id"]),
                    instrument_id="kraken:" + row["symbol"].replace("/", "-"),
                    price=str(row["price"]),
                    quantity=str(row["qty"]),
                    taker_side={"buy": "BUY", "sell": "SELL"}.get(
                        row["side"], "UNKNOWN"
                    ),
                    provider_id="kraken",
                    origin_feed_id="kraken-ws-v2-trade",
                    source_time=row["timestamp"],
                    quality="READ_ONLY_PUBLIC",
                )
            )
        return events

    async def probe(self, symbol="BTC/EUR"):
        import websockets

        if symbol not in {"BTC/EUR", "ETH/EUR", "SOL/EUR"}:
            raise ValueError("UNMAPPED_SYMBOL")
        async with asyncio.timeout(10):
            async with websockets.connect(
                "wss://ws.kraken.com/v2", open_timeout=5, max_size=65536, max_queue=16
            ) as ws:
                await ws.send(
                    json.dumps(
                        {
                            "method": "subscribe",
                            "params": {"channel": "ticker", "symbol": [symbol]},
                        }
                    )
                )
                async for raw in ws:
                    if json.loads(raw).get("channel") == "ticker":
                        return self.normalize_ticker(raw)
        raise TimeoutError("UPSTREAM_TIMEOUT")
