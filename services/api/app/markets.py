"""Provider-normalization, reference FX and orderflow. No order execution capability."""

from __future__ import annotations
from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal as D
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .contracts import DecimalString


class MarketQuote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instrument_id: str
    economic_id: str
    provider: str
    venue: str
    origin_feed: str
    currency: str
    bid: DecimalString
    ask: DecimalString
    last: DecimalString | None = None
    source_time: str
    received_at: str
    quality: Literal["SIMULATED", "REALTIME_UNVERIFIED", "DELAYED", "STALE"]
    delay_ms: int = Field(default=0, ge=0)
    session: str = "REGULAR"
    adjustment: str = "RAW"
    rights: str = "UNVERIFIED"
    schema_version: str = "1"

    def checked(self):
        if D(self.bid) <= 0 or D(self.ask) < D(self.bid):
            raise ValueError("INVALID_QUOTE")
        if self.last is not None and D(self.last) <= 0:
            raise ValueError("INVALID_LAST")
        parse_time(self.source_time)
        return self


def parse_time(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def decode(raw):
    if len(raw) > 1048576:
        raise ValueError("MESSAGE_TOO_LARGE")
    return json.loads(raw, parse_float=D, parse_int=D)


class CoinbaseAdapter:
    endpoint = "wss://advanced-trade-ws.coinbase.com"
    symbols = {"BTC-EUR": "BTC", "ETH-EUR": "ETH", "SOL-EUR": "SOL"}

    @classmethod
    def quotes(cls, raw):
        message = decode(raw)
        if message.get("channel") != "ticker":
            raise ValueError("NOT_TICKER")
        result = []
        for event in message["events"]:
            for item in event.get("tickers", []):
                symbol = item["product_id"]
                if symbol not in cls.symbols:
                    raise ValueError("UNMAPPED_SYMBOL")
                result.append(
                    MarketQuote(
                        instrument_id="coinbase:" + symbol,
                        economic_id=cls.symbols[symbol],
                        provider="coinbase",
                        venue="COINBASE_SPOT",
                        origin_feed="coinbase-advanced-ticker",
                        currency="EUR",
                        bid=str(item["best_bid"]),
                        ask=str(item["best_ask"]),
                        last=str(item["price"]),
                        source_time=message["timestamp"],
                        received_at=utcnow(),
                        quality="REALTIME_UNVERIFIED",
                    ).checked()
                )
        return result


class AlpacaAdapter:
    feeds = {"iex": 0, "sip": 0, "delayed_sip": 900000}
    symbols = {"AAPL": "US0378331005", "MSFT": "US5949181045", "SPY": "US78462F1030"}

    @classmethod
    def quotes(cls, raw, feed, entitlements):
        if feed not in cls.feeds or feed not in entitlements:
            raise PermissionError("ENTITLEMENT_REQUIRED")
        result = []
        for item in decode(raw):
            if item.get("T") != "q":
                continue
            symbol = item["S"]
            if symbol not in cls.symbols:
                raise ValueError("UNMAPPED_SYMBOL")
            result.append(
                MarketQuote(
                    instrument_id=f"alpaca:{feed}:{symbol}",
                    economic_id=cls.symbols[symbol],
                    provider="alpaca",
                    venue="IEX" if feed == "iex" else "US_CONSOLIDATED",
                    origin_feed=f"alpaca-{feed}",
                    currency="USD",
                    bid=str(item["bp"]),
                    ask=str(item["ap"]),
                    source_time=item["t"],
                    received_at=utcnow(),
                    quality="DELAYED" if cls.feeds[feed] else "REALTIME_UNVERIFIED",
                    delay_ms=cls.feeds[feed],
                ).checked()
            )
        return result


def compare_quotes(
    left: MarketQuote,
    right: MarketQuote,
    *,
    allow_cross_venue=False,
    threshold_bps="25",
    max_time_difference=2,
):
    reasons = []
    for field in ["economic_id", "currency", "session", "adjustment", "delay_ms"]:
        if getattr(left, field) != getattr(right, field):
            reasons.append(field.upper() + "_MISMATCH")
    if left.venue != right.venue and not allow_cross_venue:
        reasons.append("VENUE_MISMATCH")
    if "STALE" in [left.quality, right.quality]:
        reasons.append("STALE_DATA")
    if (left.quality == "SIMULATED") != (right.quality == "SIMULATED"):
        reasons.append("FIXTURE_LIVE_MISMATCH")
    if (
        abs(
            (
                parse_time(left.source_time) - parse_time(right.source_time)
            ).total_seconds()
        )
        > max_time_difference
    ):
        reasons.append("TIME_MISMATCH")
    if reasons:
        return {
            "status": "NIET_VERGELIJKBAAR",
            "reasons": reasons,
            "basis_points": None,
        }
    a = (D(left.bid) + D(left.ask)) / 2
    b = (D(right.bid) + D(right.ask)) / 2
    delta = ((b - a) / a * 10000).quantize(D(".01"))
    return {
        "status": "DEVIATION" if abs(delta) > D(threshold_bps) else "WITHIN_THRESHOLD",
        "basis_points": str(delta),
        "price_type": "MIDPOINT_REFERENCE",
        "cross_venue": left.venue != right.venue,
        "independent_feed": left.origin_feed != right.origin_feed,
        "threshold_bps": threshold_bps,
        "reasons": [],
        "execution_allowed": False,
    }


class ReferenceFX:
    def __init__(self, rates, as_of, source="ECB", quality="REFERENCE"):
        self.rates = {k: D(v) for k, v in rates.items()}
        if self.rates.get("EUR") != 1 or any(
            not v.is_finite() or v <= 0 for v in self.rates.values()
        ):
            raise ValueError("INVALID_FX")
        self.as_of, self.source, self.quality = as_of, source, quality

    def convert(self, amount, base, quote, purpose="VALUATION"):
        if purpose not in {"VALUATION", "REPORTING"}:
            raise ValueError("REFERENCE_FX_NOT_EXECUTABLE")
        if base not in self.rates or quote not in self.rates:
            raise ValueError("MISSING_FX")
        rate = self.rates[quote] / self.rates[base]
        return {
            "original_amount": str(amount),
            "base": base,
            "quote": quote,
            "rate": str(rate),
            "amount": str((D(amount) * rate).quantize(D(".01"))),
            "path": [base, "EUR", quote],
            "as_of": self.as_of,
            "source": self.source,
            "quality": self.quality,
            "purpose": purpose,
        }


class OrderBook:
    """Strict contiguous sequence contract. Caller must provide provider-specific sequence scope."""

    def __init__(self):
        self.sequence = None
        self.status = "BOOK_UNTRUSTED"
        self.bids, self.asks = {}, {}

    def snapshot(self, sequence, bids, asks):
        def levels(rows):
            result = {D(p): D(q) for p, q in rows}
            if any(
                not p.is_finite() or not q.is_finite() or p <= 0 or q <= 0
                for p, q in result.items()
            ):
                raise ValueError("INVALID_BOOK")
            return result

        self.bids, self.asks = levels(bids), levels(asks)
        if self.bids and self.asks and max(self.bids) >= min(self.asks):
            self.status = "BOOK_UNTRUSTED"
            raise ValueError("CROSSED_BOOK")
        self.sequence = int(sequence)
        self.status = "SYNCED"

    def update(self, sequence, updates):
        sequence = int(sequence)
        if self.sequence is not None and sequence <= self.sequence:
            return "DUPLICATE"
        if self.status != "SYNCED" or sequence != self.sequence + 1:
            self.status = "BOOK_UNTRUSTED"
            return "RESYNC_REQUIRED"
        # Validate the complete message before mutating the book.
        parsed = []
        for side, price, quantity in updates:
            p, q = D(price), D(quantity)
            if (
                side not in {"bid", "ask"}
                or not p.is_finite()
                or not q.is_finite()
                or p <= 0
                or q < 0
            ):
                self.status = "BOOK_UNTRUSTED"
                raise ValueError("INVALID_DELTA")
            parsed.append((side, p, q))
        for side, p, q in parsed:
            levels = self.bids if side == "bid" else self.asks
            if q == 0:
                levels.pop(p, None)
            else:
                levels[p] = q
        self.sequence = sequence
        if self.bids and self.asks and max(self.bids) >= min(self.asks):
            self.status = "BOOK_UNTRUSTED"
            return "RESYNC_REQUIRED"
        return "APPLIED"

    def summary(self, depth=10):
        if self.status != "SYNCED":
            return {
                "status": self.status,
                "bids": [],
                "asks": [],
                "imbalance": None,
                "sequence": str(self.sequence),
            }
        bids = sorted(self.bids.items(), reverse=True)[:depth]
        asks = sorted(self.asks.items())[:depth]
        b = sum((q for _, q in bids), D(0))
        a = sum((q for _, q in asks), D(0))
        return {
            "status": self.status,
            "bids": [[str(p), str(q)] for p, q in bids],
            "asks": [[str(p), str(q)] for p, q in asks],
            "imbalance": str(((b - a) / (b + a)).quantize(D(".0001")))
            if b + a
            else None,
            "sequence": str(self.sequence),
        }


class TradeTape:
    def __init__(self, capacity=10000):
        self.events = OrderedDict()
        self.capacity = capacity
        self.evicted = 0

    def add(self, event):
        key = (event["provider_id"], event["event_id"])
        if key in self.events:
            return False
        q = D(event["quantity"])
        if not q.is_finite() or q <= 0:
            raise ValueError("INVALID_QUANTITY")
        self.events[key] = event
        if len(self.events) > self.capacity:
            self.events.popitem(last=False)
            self.evicted += 1
        return True

    def pressure(self):
        totals = {side: D(0) for side in ["BUY", "SELL", "UNKNOWN"]}
        for event in self.events.values():
            totals[event.get("taker_side", "UNKNOWN")] += D(event["quantity"])
        classified = totals["BUY"] + totals["SELL"]
        total = classified + totals["UNKNOWN"]
        return {
            "buy_volume": str(totals["BUY"]),
            "sell_volume": str(totals["SELL"]),
            "unknown_volume": str(totals["UNKNOWN"]),
            "buy_pressure": str(totals["BUY"] / classified) if classified else None,
            "coverage": str(classified / total) if total else None,
            "unit": "BASE_ASSET",
            "observed_trades": len(self.events),
            "evicted": self.evicted,
        }


MANIFESTS = [
    {
        "id": "coinbase",
        "name": "Coinbase Advanced",
        "asset_classes": ["CRYPTO"],
        "regions": ["GLOBAL"],
        "venues": ["COINBASE_SPOT"],
        "origin_feed_ids": ["coinbase-advanced-ticker"],
        "capabilities": ["quotes", "trades", "l2"],
        "requires_secret": False,
    },
    {
        "id": "alpaca",
        "name": "Alpaca Market Data",
        "asset_classes": ["STOCK", "ETF"],
        "regions": ["US"],
        "venues": ["IEX", "US_CONSOLIDATED"],
        "origin_feed_ids": ["alpaca-iex", "alpaca-sip", "alpaca-delayed_sip"],
        "capabilities": ["quotes", "trades", "history"],
        "requires_secret": True,
    },
    {
        "id": "ecb",
        "name": "ECB referentie-FX",
        "asset_classes": ["FX"],
        "regions": ["EU"],
        "venues": [],
        "origin_feed_ids": ["ecb-reference-daily"],
        "capabilities": ["reference_fx"],
        "requires_secret": False,
    },
    {
        "id": "rss",
        "name": "RSS / Atom",
        "asset_classes": [],
        "regions": ["EU", "US", "ASIA"],
        "venues": [],
        "origin_feed_ids": [],
        "capabilities": ["news"],
        "requires_secret": False,
    },
    {
        "id": "sec",
        "name": "SEC EDGAR",
        "asset_classes": ["STOCK"],
        "regions": ["US"],
        "venues": [],
        "origin_feed_ids": ["sec-edgar"],
        "capabilities": ["fundamentals", "filings"],
        "requires_secret": False,
    },
]


def manifests():
    return [
        {
            **m,
            "adapter_version": "1.0.0",
            "schema_version": "1",
            "status": "NOT_CONNECTED",
            "verification": "NOT_RUN_MISSING_CREDENTIALS"
            if m["requires_secret"]
            else "NOT_RUN_EXTERNAL_NETWORK",
            "fixture_verification": "TESTED_WITH_FIXTURES",
            "license": {
                k: "UNVERIFIED"
                for k in [
                    "display",
                    "non_display",
                    "storage",
                    "derived_data",
                    "redistribution",
                    "ai_processing",
                ]
            },
            "last_verified_at": None,
            "last_error": None,
            "declared_delay_ms": 900000 if m["id"] == "alpaca" else None,
            "execution_capabilities": [],
            "retention_policy": "No live storage before explicit source policy",
            "professional_status_requirement": "UNVERIFIED",
        }
        for m in MANIFESTS
    ]
