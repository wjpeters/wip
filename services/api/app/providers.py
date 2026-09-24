"""Read-only provider protocols. Transport permission and data rights remain explicit."""

from datetime import date
from decimal import Decimal as D
from xml.etree import ElementTree as ET
from .markets import (
    CoinbaseAdapter,
    AlpacaAdapter,
    OrderBook,
    ReferenceFX,
    decode,
    parse_time,
    utcnow,
)


class CoinbaseStream:
    """One dedicated level2 connection. Sequence scope is the entire connection."""

    def __init__(self):
        self.sequence = None
        self.books = {}
        self.status = "DISCONNECTED"
        self.last_received = None

    def disconnect(self, reason="DISCONNECTED"):
        self.status = reason
        self.sequence = None
        for book in self.books.values():
            book.status = "BOOK_UNTRUSTED"

    def ingest(self, raw):
        m = decode(raw)
        seq = int(m["sequence_num"])
        parse_time(m["timestamp"])
        if self.sequence is not None:
            if seq <= self.sequence:
                return {"status": "DUPLICATE", "books": {}}
            if seq != self.sequence + 1:
                self.disconnect("RESYNC_REQUIRED")
                return {"status": self.status, "books": {}}
        self.sequence = seq
        self.last_received = utcnow()
        if m["channel"] == "l2_data":
            for event in m["events"]:
                product = event["product_id"]
                if product not in CoinbaseAdapter.symbols:
                    raise ValueError("UNMAPPED_SYMBOL")
                book = self.books.setdefault(product, OrderBook())
                updates = []
                for u in event["updates"]:
                    if u["side"] not in {"bid", "offer"}:
                        raise ValueError("INVALID_BOOK_SIDE")
                    updates.append(
                        (
                            "bid" if u["side"] == "bid" else "ask",
                            u["price_level"],
                            u["new_quantity"],
                        )
                    )
                if event["type"] == "snapshot":
                    book.snapshot(
                        seq,
                        [[p, q] for s, p, q in updates if s == "bid" and D(q) > 0],
                        [[p, q] for s, p, q in updates if s == "ask" and D(q) > 0],
                    )
                elif event["type"] == "update":
                    if book.status != "SYNCED":
                        self.disconnect("RESYNC_REQUIRED")
                        return {"status": self.status, "books": {}}
                    # Contiguity was checked at connection scope, including messages for other products.
                    book.sequence = seq - 1
                    if book.update(seq, updates) == "RESYNC_REQUIRED":
                        self.disconnect("RESYNC_REQUIRED")
                        return {"status": self.status, "books": {}}
                else:
                    raise ValueError("UNKNOWN_BOOK_EVENT")
        self.status = (
            "SYNCED"
            if self.books and all(b.status == "SYNCED" for b in self.books.values())
            else "AWAITING_SNAPSHOT"
        )
        return {
            "status": self.status,
            "books": {p: b.summary() for p, b in self.books.items()},
            "sequence": seq,
        }


def coinbase_trades(raw):
    m = decode(raw)
    if m["channel"] != "market_trades":
        raise ValueError("NOT_TRADES")
    result = []
    for event in m["events"]:
        for t in event["trades"]:
            symbol = t["product_id"]
            if symbol not in CoinbaseAdapter.symbols:
                raise ValueError("UNMAPPED_SYMBOL")
            parse_time(t["time"])
            if D(t["price"]) <= 0 or D(t["size"]) <= 0:
                raise ValueError("INVALID_TRADE")
            result.append(
                {
                    "provider_id": "coinbase",
                    "event_id": symbol + ":" + str(t["trade_id"]),
                    "instrument_id": "coinbase:" + symbol,
                    "price": str(t["price"]),
                    "quantity": str(t["size"]),
                    "maker_side": t.get("side", "UNKNOWN"),
                    "taker_side": {"BUY": "SELL", "SELL": "BUY"}.get(
                        t.get("side"), "UNKNOWN"
                    ),
                    "source_time": t["time"],
                    "received_at": utcnow(),
                    "quality": "REALTIME_UNVERIFIED",
                    "origin_feed": "coinbase-market-trades",
                }
            )
    return result


def alpaca_events(raw, feed, entitlements):
    if feed not in AlpacaAdapter.feeds or feed not in entitlements:
        raise PermissionError("ENTITLEMENT_REQUIRED")
    result = []
    for t in decode(raw):
        kind = t.get("T")
        if kind not in {"t", "c", "x", "b", "u", "d"}:
            continue
        symbol = t["S"]
        if symbol not in AlpacaAdapter.symbols:
            raise ValueError("UNMAPPED_SYMBOL")
        parse_time(t["t"])
        base = {
            "provider_id": "alpaca",
            "instrument_id": f"alpaca:{feed}:{symbol}",
            "origin_feed": "alpaca-" + feed,
            "source_time": t["t"],
            "received_at": utcnow(),
            "quality": "DELAYED" if feed == "delayed_sip" else "REALTIME_UNVERIFIED",
            "delay_ms": AlpacaAdapter.feeds[feed],
        }
        if kind in {"t", "c", "x"}:
            price = t["cp"] if kind == "c" else t["p"]
            qty = t["cs"] if kind == "c" else t["s"]
            if price <= 0 or qty <= 0:
                raise ValueError("INVALID_TRADE")
            base.update(
                kind={"t": "TRADE", "c": "CORRECTION", "x": "CANCEL"}[kind],
                event_id=str(t["ci"] if kind == "c" else t["i"]),
                original_id=str(t["oi"]) if kind == "c" else str(t["i"]),
                price=str(price),
                quantity=str(qty),
                venue=t["x"],
                taker_side="UNKNOWN",
            )
        else:
            values = {key: str(t[key]) for key in ["o", "h", "l", "c", "v"]}
            if (
                any(D(values[k]) <= 0 for k in ["o", "h", "l", "c"])
                or D(values["v"]) < 0
                or not D(values["l"])
                <= min(D(values["o"]), D(values["c"]))
                <= max(D(values["o"]), D(values["c"]))
                <= D(values["h"])
            ):
                raise ValueError("INVALID_BAR")
            base.update(
                kind="BAR_REVISION" if kind == "u" else "BAR",
                timeframe="1d" if kind == "d" else "1m",
                adjustment="RAW",
                **values,
            )
        result.append(base)
    return result


class RevisionTape:
    def __init__(self):
        self.trades = {}
        self.revisions = []
        self.missing = []

    def ingest(self, event):
        key = (
            event["origin_feed"],
            event["instrument_id"],
            event.get("venue", ""),
            event["event_id"],
        )
        old = (key[0], key[1], key[2], event.get("original_id", key[3]))
        if event["kind"] == "TRADE":
            self.trades.setdefault(key, event)
            return
        if event["kind"] not in {"CORRECTION", "CANCEL"}:
            raise ValueError("NOT_TRADE_REVISION")
        if event in self.revisions:
            return
        self.revisions.append(event)
        if old not in self.trades:
            self.missing.append(
                {"status": "RECONCILIATION_REQUIRED", "original_id": old[-1]}
            )
        self.trades.pop(old, None)
        if event["kind"] == "CORRECTION":
            self.trades[key] = event


def ecb_reference(raw):
    if len(raw) > 1048576 or "<!DOCTYPE" in raw.upper() or "<!ENTITY" in raw.upper():
        raise ValueError("UNSAFE_XML")
    root = ET.fromstring(raw)
    days = [e for e in root.iter() if "time" in e.attrib]
    if len(days) != 1:
        raise ValueError("ONE_FX_DATE_REQUIRED")
    as_of = date.fromisoformat(days[0].attrib["time"]).isoformat()
    rates = {"EUR": "1"}
    for e in days[0]:
        currency = e.attrib["currency"]
        if len(currency) != 3 or not currency.isalpha() or currency in rates:
            raise ValueError("INVALID_CURRENCY")
        rates[currency] = e.attrib["rate"]
    if len(rates) < 2:
        raise ValueError("EMPTY_RATES")
    return ReferenceFX(rates, as_of)


def sec_facts(raw, cik, as_of):
    m = decode(raw)
    if str(int(m["cik"])).zfill(10) != str(cik).zfill(10):
        raise ValueError("CIK_MISMATCH")
    cutoff = date.fromisoformat(as_of)
    result = []
    for taxonomy, concepts in m.get("facts", {}).items():
        for concept, info in concepts.items():
            for unit, items in info.get("units", {}).items():
                for item in items:
                    if date.fromisoformat(item["filed"]) > cutoff:
                        continue
                    result.append(
                        {
                            "taxonomy": taxonomy,
                            "concept": concept,
                            "unit": unit,
                            "value": str(item["val"]),
                            "period_start": item.get("start"),
                            "period_end": item["end"],
                            "filed": item["filed"],
                            "accession": item["accn"],
                            "form": item["form"],
                            "fiscal_period": item.get("fp"),
                            "frame": item.get("frame"),
                            "source": "SEC_EDGAR",
                            "quality": "PRIMARY_REPORTED_UNREVIEWED",
                        }
                    )
    # All original periods and amendments are preserved; never silently choose a restatement.
    return {
        "cik": str(cik).zfill(10),
        "entity_name": m.get("entityName"),
        "facts": result,
        "as_of": as_of,
        "policy": "FILED_BY_CUTOFF; amendments retained; no inferred ratios",
    }


class SourceHealth:
    def __init__(self):
        self.state = "DISCONNECTED"
        self.received = None
        self.reason = None
        self.gaps = 0

    def update(self, event, now, reason=None):
        allowed = {
            "CONNECTED",
            "SYNCED",
            "DISCONNECTED",
            "RATE_LIMITED",
            "ENTITLEMENT_DENIED",
            "RESYNC_REQUIRED",
            "STALE",
            "SLEEP_WAKE",
        }
        if event not in allowed:
            raise ValueError("UNKNOWN_HEALTH_EVENT")
        self.state = "RESYNC_REQUIRED" if event == "SLEEP_WAKE" else event
        self.reason = reason
        if event == "SYNCED":
            self.received = now
        if self.state == "RESYNC_REQUIRED":
            self.gaps += 1

    def status(self, now, max_age=5):
        state = self.state
        if state == "SYNCED" and (
            self.received is None or now - self.received > max_age
        ):
            state = "STALE"
        return {
            "state": state,
            "age_seconds": None
            if self.received is None
            else max(0, now - self.received),
            "reason": self.reason,
            "resync_count": self.gaps,
            "usable": state == "SYNCED",
        }


def select_source(candidates, priorities, required):
    compatible = [
        c
        for c in candidates
        if c.get("health") == "SYNCED"
        and c.get("display_rights") is True
        and all(c.get(k) == v for k, v in required.items())
    ]
    compatible.sort(
        key=lambda c: priorities.index(c["provider"])
        if c["provider"] in priorities
        else len(priorities)
    )
    return {
        "selected": compatible[0] if compatible else None,
        "status": "SELECTED" if compatible else "NO_COMPATIBLE_SOURCE",
        "implicit_feed_upgrade": False,
    }
