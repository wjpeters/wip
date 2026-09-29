import xml.etree.ElementTree as ET
import os
from pathlib import Path
import httpx
from decimal import Decimal as D
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from .markets import (
    MarketQuote,
    CoinbaseAdapter,
    AlpacaAdapter,
    OrderBook,
    TradeTape,
    ReferenceFX,
    compare_quotes,
    manifests,
    select_display_quotes,
)
from .market import fixture_quote, fixture_trades, INSTRUMENTS, history
from .research import (
    fixture_news,
    fixture_calendar,
    profiles,
    cluster_news,
    parse_feed,
    parse_news_api,
)
from .storage import document, save
from .contracts import DecimalString


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priorities: list[str] = Field(max_length=12)


class FeedImport(BaseModel):
    format: str = Field(default="RSS_ATOM", pattern="^(RSS_ATOM|NEWS_JSON)$")
    model_config = ConfigDict(extra="forbid")
    content: str = Field(max_length=524288)
    publisher: str = Field(min_length=1, max_length=120)
    source_family: str = Field(min_length=1, max_length=120)
    region: str = Field(pattern="^(EU|US|ASIA|GLOBAL)$")
    display_rights_confirmed: bool = False


class FXRequest(BaseModel):
    amount: DecimalString
    base: str = Field(pattern="^[A-Z]{3,6}$")
    quote: str = Field(pattern="^[A-Z]{3,6}$")
    purpose: str = "VALUATION"


def router(db, session, audit):
    r = APIRouter()

    @r.get("/market/live")
    def live(request: Request):
        session(request)
        url = os.getenv("MARKET_BRIDGE_URL", "")
        if not url:
            return {
                "mode": "READ_ONLY_LIVE",
                "status": "NOT_CONFIGURED",
                "quotes": [],
                "health": {},
                "books": {},
                "trades": {},
                "execution_enabled": False,
                "display_routes": [],
            }
        token_path = Path("/run/secrets/market_token")
        if not token_path.exists():
            raise HTTPException(503, "MARKET_TOKEN_MISSING")
        try:
            response = httpx.get(
                url + "/snapshot",
                headers={"Authorization": "Bearer " + token_path.read_text().strip()},
                timeout=2,
                trust_env=False,
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError):
            return {
                "mode": "READ_ONLY_LIVE",
                "status": "BRIDGE_UNAVAILABLE",
                "quotes": [],
                "health": {},
                "books": {},
                "trades": {},
                "execution_enabled": False,
                "display_routes": [],
            }
        with db() as c:
            preferences = document(
                c,
                "research",
                lambda: {"articles": [], "priorities": ["demo-fixture", "kraken", "coinbase", "alpaca"]},
            )
        result["display_routes"] = select_display_quotes(
            result.get("quotes", []),
            result.get("health", {}),
            preferences.get("priorities", []),
        )
        return {
            **result,
            "status": "RECEIVING"
            if result.get("quotes")
            else "WAITING_FOR_CONFIGURED_PROVIDER",
            "display_refresh_seconds": 2,
        }

    @r.get("/market/catalog")
    def catalog(request: Request):
        session(request)
        return {
            "instruments": [
                {
                    **p,
                    "day_change_percent": str(
                        (
                            (
                                D(history(p["id"], "1d")["rows"][-1]["close"])
                                / D(history(p["id"], "1d")["rows"][-2]["close"])
                                - 1
                            )
                            * 100
                        ).quantize(D(".01"))
                    )
                    if p["id"] in INSTRUMENTS
                    else None,
                }
                for p in profiles()
            ],
            "providers": manifests(),
            "mode": "DEMO_AND_METADATA",
        }

    @r.get("/market/context")
    def context(request: Request, instrument_id: str = "sim:BTC-EUR"):
        session(request)
        if instrument_id not in INSTRUMENTS:
            profile = next((p for p in profiles() if p["id"] == instrument_id), None)
            if not profile:
                raise HTTPException(404, "UNKNOWN_INSTRUMENT")
            return {
                "profile": profile,
                "quotes": [],
                "comparison": {
                    "status": "MISSING_DATA",
                    "reasons": ["PROVIDER_NOT_CONNECTED"],
                },
                "book": {"status": "NOT_AVAILABLE", "bids": [], "asks": []},
                "pressure": None,
                "trades": [],
            }
        q = fixture_quote(instrument_id)
        profile = next(p for p in profiles() if p["id"] == instrument_id)
        base = profile["economic_id"]
        left = MarketQuote(
            instrument_id=instrument_id,
            economic_id=base,
            provider="fixture-a",
            venue="SIM_A",
            origin_feed="synthetic-a",
            currency="EUR",
            bid=q.bid,
            ask=q.ask,
            last=q.last,
            source_time=q.source_time,
            received_at=q.received_at,
            quality="SIMULATED",
            rights="OWN_SYNTHETIC",
        )
        right = left.model_copy(
            update={
                "provider": "fixture-b",
                "venue": "SIM_B",
                "origin_feed": "synthetic-b",
                "bid": str((D(q.bid) * D("1.0002")).quantize(D(".01"))),
                "ask": str((D(q.ask) * D("1.0002")).quantize(D(".01"))),
            }
        )
        book = OrderBook()
        book.snapshot(
            100,
            [[str(D(q.bid) - i), str(D(".1") + D(i) / 10)] for i in range(10)],
            [[str(D(q.ask) + i), str(D(".15") + D(i) / 10)] for i in range(10)],
        )
        tape = TradeTape()
        trades = fixture_trades(instrument_id)
        for t in trades:
            tape.add(t)
        return {
            "profile": profile,
            "quotes": [left.model_dump(), right.model_dump()],
            "comparison": compare_quotes(left, right, allow_cross_venue=True),
            "book": {
                **book.summary(),
                "quality": "SIMULATED",
                "source": "synthetic-orderbook-v1",
            },
            "pressure": tape.pressure(),
            "trades": trades,
        }

    @r.get("/research")
    def research(request: Request, region: str = "", query: str = ""):
        session(request)
        with db() as c:
            data = document(
                c,
                "research",
                lambda: {
                    "articles": [],
                    "priorities": ["demo-fixture", "kraken", "coinbase", "alpaca"],
                },
            )
        items = fixture_news() + data["articles"]
        items = [
            n
            for n in items
            if (not region or n["region"] == region)
            and query.lower() in (n["title"] + " " + n["snippet"]).lower()
        ]
        return {
            "clusters": cluster_news(items),
            "calendar": fixture_calendar(),
            "priorities": data["priorities"],
            "rights": "Headlines, short snippets and source links only; fulltext not redistributed",
        }

    @r.post("/research/import-feed")
    def import_feed(body: FeedImport, request: Request):
        session(request)
        try:
            items = (parse_news_api if body.format == "NEWS_JSON" else parse_feed)(
                body.content,
                publisher=body.publisher,
                family=body.source_family,
                region=body.region,
                license_display=body.display_rights_confirmed,
            )
        except (ValueError, PermissionError, ET.ParseError) as e:
            raise HTTPException(422, str(e))
        with db() as c:
            data = document(
                c,
                "research",
                lambda: {
                    "articles": [],
                    "priorities": ["demo-fixture", "kraken", "coinbase", "alpaca"],
                },
                True,
            )
            existing = {(n["id"], n["fingerprint"]) for n in data["articles"]}
            added = 0
            for item in items:
                if (item["id"], item["fingerprint"]) in existing:
                    continue
                previous = [n for n in data["articles"] if n["id"] == item["id"]]
                item["revision"] = len(previous) + 1
                item["revision_of"] = previous[-1]["id"] if previous else None
                data["articles"].append(item)
                existing.add((item["id"], item["fingerprint"]))
                added += 1
            if len(data["articles"]) > 10000:
                raise HTTPException(
                    422,
                    "RESEARCH_RETENTION_LIMIT: export/archive before further ingest",
                )
            save(c, "research", data)
            audit(c, "NEWS_IMPORTED", str(added))
        return {"imported": added, "duplicate_count": len(items) - added}

    @r.post("/market/source-priorities")
    def priorities(body: Preferences, request: Request):
        session(request)
        allowed = {"demo-fixture", "kraken", "coinbase", "alpaca", "ecb", "rss", "sec"}
        if (
            len(set(body.priorities)) != len(body.priorities)
            or not set(body.priorities) <= allowed
        ):
            raise HTTPException(422, "INVALID_PRIORITY")
        with db() as c:
            data = document(
                c, "research", lambda: {"articles": [], "priorities": []}, True
            )
            data["priorities"] = body.priorities
            save(c, "research", data)
            audit(c, "SOURCE_PRIORITIES_UPDATED", "research")
        return {
            "saved": True,
            "priorities": body.priorities,
            "failover_policy": "Capabilities, rights, venue and delay must match; priority never overrides compatibility",
        }

    @r.post("/market/fx")
    def fx(body: FXRequest, request: Request):
        session(request)
        try:
            return ReferenceFX(
                {"EUR": "1", "USD": "1.10", "GBP": "0.85"},
                "2026-09-24",
                "synthetic-ecb-shape",
                "SIMULATED",
            ).convert(body.amount, body.base, body.quote, body.purpose)
        except ValueError as e:
            raise HTTPException(422, str(e))

    @r.post("/market/adapter-test/{provider}")
    def adapter_test(provider: str, request: Request):
        session(request)
        if provider == "coinbase":
            data = CoinbaseAdapter.quotes(
                '{"channel":"ticker","timestamp":"2026-09-24T12:00:00Z","events":[{"tickers":[{"product_id":"BTC-EUR","best_bid":"62430.25","best_ask":"62448.20","price":"62439.00"}]}]}'
            )
        elif provider == "alpaca":
            data = AlpacaAdapter.quotes(
                '[{"T":"q","S":"AAPL","bp":200.12,"ap":200.14,"t":"2026-09-24T12:00:00Z"}]',
                "iex",
                ["iex"],
            )
        else:
            raise HTTPException(404, "UNKNOWN_ADAPTER_TEST")
        return {
            "status": "PASS",
            "verification": "TESTED_WITH_FIXTURES",
            "records": len(data),
            "live_verified": False,
        }

    return r
