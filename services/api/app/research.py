"""Read-only research domain; articles are untrusted source material, never instructions."""

from datetime import datetime, time, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

AT = "2026-09-24T12:00:00+00:00"


def canonical_url(value):
    u = urlsplit(value)
    if u.scheme not in {"https", "http"} or not u.hostname or u.username or u.password:
        raise ValueError("INVALID_SOURCE_URL")
    query = urlencode(
        [(k, v) for k, v in parse_qsl(u.query) if not k.lower().startswith("utm_")]
    )
    return urlunsplit((u.scheme, u.netloc.lower(), u.path or "/", query, ""))


def plain(value):
    return re.sub(r"<[^>]+>", "", value or "")[:4000]


def parse_feed(raw, *, publisher, family, region, license_display=False):
    if (
        len(raw.encode()) > 524288
        or "<!DOCTYPE" in raw.upper()
        or "<!ENTITY" in raw.upper()
    ):
        raise ValueError("UNSAFE_FEED")
    if not license_display:
        raise PermissionError("SOURCE_RIGHTS_REQUIRED")
    root = ET.fromstring(raw)
    items = root.findall(".//item") or root.findall(
        "{http://www.w3.org/2005/Atom}entry"
    )
    result = []
    for item in items[:100]:

        def text(name):
            el = item.find(name)
            if el is None:
                el = item.find("{http://www.w3.org/2005/Atom}" + name)
            return el.text if el is not None else None

        link = text("link")
        if not link:
            el = item.find("{http://www.w3.org/2005/Atom}link")
            link = el.get("href") if el is not None else None
        if not link:
            continue
        url = canonical_url(link)
        pub = text("pubDate") or text("published") or text("updated")
        if not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        except ValueError:
            dt = parsedate_to_datetime(pub)
        if not dt.tzinfo:
            raise ValueError("TIMEZONE_REQUIRED")
        title = plain(text("title"))
        result.append(
            {
                "id": sha256(url.encode()).hexdigest()[:20],
                "title": title,
                "snippet": plain(text("description") or text("summary"))[:400],
                "url": url,
                "publisher": publisher,
                "source_family": family,
                "region": region,
                "language": "UNKNOWN",
                "published_at": dt.astimezone(timezone.utc).isoformat(),
                "updated_at": text("updated"),
                "first_available_at": datetime.now(timezone.utc).isoformat(),
                "quality": "UNVERIFIED_SOURCE",
                "kind": "NEWS",
                "rights": "HEADLINE_SNIPPET_LINK",
                "fingerprint": sha256(ET.tostring(item, encoding="utf-8")).hexdigest(),
                "cluster_key": sha256(title.lower().encode()).hexdigest(),
                "revision": 1,
            }
        )
    return result


def cluster_news(items):
    clusters = {}
    for item in items:
        # Exact URL/fingerprint grouping only; do not claim semantic event independence.
        key = (
            item.get("cluster_key")
            or sha256(item["title"].lower().encode()).hexdigest()
        )
        group = clusters.setdefault(
            key, {"id": key[:16], "items": [], "families": set()}
        )
        if any(
            x["url"] == item["url"] and x.get("revision") == item.get("revision")
            for x in group["items"]
        ):
            continue
        group["items"].append(item)
        group["families"].add(item["source_family"])
    return [
        {
            **g,
            "families": sorted(g["families"]),
            "independent_source_families": len(g["families"]),
        }
        for g in clusters.values()
    ]


def session_state(
    at,
    timezone_name,
    open_time="09:30",
    close_time="16:00",
    holidays=(),
    early_closes=None,
):
    instant = datetime.fromisoformat(at.replace("Z", "+00:00"))
    if not instant.tzinfo:
        raise ValueError("TIMEZONE_REQUIRED")
    local = instant.astimezone(ZoneInfo(timezone_name))
    date = local.date().isoformat()
    if local.weekday() >= 5 or date in holidays:
        return {
            "status": "CLOSED",
            "reason": "HOLIDAY_OR_WEEKEND",
            "local_time": local.isoformat(),
        }
    close = (early_closes or {}).get(date, close_time)
    opened = (
        time.fromisoformat(open_time)
        <= local.time().replace(tzinfo=None)
        < time.fromisoformat(close)
    )
    return {
        "status": "OPEN" if opened else "CLOSED",
        "reason": "CONFIGURED_SESSION",
        "local_time": local.isoformat(),
        "close_time": close,
    }


def fixture_news():
    values = [
        (
            "EU",
            "Oefenbericht: Europese rentevergadering",
            "Synthetisch persbericht om broncontrole en rentegevoeligheid te oefenen.",
            "fixture-centralbank",
            "MACRO",
            ["EUR"],
        ),
        (
            "US",
            "Oefenbericht: kwartaalresultaten technologiebedrijf",
            "Fictieve earningspublicatie. Er zijn geen echte omzet- of winstcijfers opgehaald.",
            "fixture-issuer",
            "EARNINGS",
            ["AAPL"],
        ),
        (
            "ASIA",
            "Oefenbericht: Aziatische handelsdag",
            "Fictieve marktcontext; geen actuele gebeurtenis of koersverwachting.",
            "fixture-asia",
            "MARKET",
            ["BTC"],
        ),
        (
            "EU",
            "Oefenbericht: netwerkupdate",
            "Een fictieve technische wijziging voor de reviewworkflow.",
            "fixture-network",
            "TECHNOLOGY",
            ["ETH"],
        ),
        (
            "US",
            "Oefenbericht: kwartaalresultaten technologiebedrijf",
            "Herpublicatie van dezelfde synthetische bronfamilie.",
            "fixture-issuer",
            "EARNINGS",
            ["AAPL"],
        ),
        (
            "EU",
            "Oefenbericht: correctie op netwerkupdate",
            "Versie 2 corrigeert versie 1. Beide versies blijven herkenbaar.",
            "fixture-network",
            "CORRECTION",
            ["ETH"],
        ),
    ]
    return [
        {
            "id": f"news-demo-{i + 1}",
            "title": title,
            "snippet": snippet,
            "url": f"https://example.invalid/mtt/news/{i + 1}",
            "publisher": family,
            "source_family": family,
            "region": region,
            "language": "nl",
            "published_at": AT,
            "updated_at": AT if kind == "CORRECTION" else None,
            "first_available_at": AT,
            "event_time": None,
            "quality": "SIMULATED",
            "kind": kind,
            "rights": "OWN_SYNTHETIC",
            "instruments": instruments,
            "revision": 2 if kind == "CORRECTION" else 1,
            "revision_of": "news-demo-4" if kind == "CORRECTION" else None,
            "fingerprint": sha256(title.encode()).hexdigest(),
        }
        for i, (region, title, snippet, family, kind, instruments) in enumerate(values)
    ]


def fixture_calendar():
    return [
        {
            "id": "cal-demo-1",
            "title": "Oefenevent · rentevergadering",
            "kind": "MACRO",
            "region": "EU",
            "scheduled_at": "2026-09-24T12:15:00Z",
            "actual_at": None,
            "published_at": AT,
            "updated_at": AT,
            "timezone": "Europe/Amsterdam",
            "status": "SCHEDULED",
            "quality": "SIMULATED",
            "revision": 1,
            "instruments": ["EUR"],
            "consensus": None,
            "actual": None,
        },
        {
            "id": "cal-demo-2",
            "title": "Oefenevent · bedrijfsresultaten",
            "kind": "EARNINGS",
            "region": "US",
            "scheduled_at": "2026-09-24T20:30:00Z",
            "actual_at": None,
            "published_at": AT,
            "updated_at": AT,
            "timezone": "America/New_York",
            "status": "SCHEDULED",
            "quality": "SIMULATED",
            "revision": 1,
            "instruments": ["AAPL"],
            "consensus": None,
            "actual": None,
        },
        {
            "id": "cal-demo-3",
            "title": "Oefenevent · herziene publicatie",
            "kind": "REVISION",
            "region": "ASIA",
            "scheduled_at": "2026-09-23T00:00:00Z",
            "actual_at": "2026-09-23T00:01:00Z",
            "published_at": "2026-09-23T00:01:00Z",
            "updated_at": AT,
            "timezone": "Asia/Tokyo",
            "status": "REVISED",
            "quality": "SIMULATED",
            "revision": 2,
            "instruments": ["JPY"],
            "consensus": None,
            "actual": None,
        },
    ]


def profiles():
    return [
        {
            "id": "sim:BTC-EUR",
            "symbol": "BTC/EUR",
            "name": "Bitcoin · demomarkt",
            "asset_class": "CRYPTO",
            "region": "GLOBAL",
            "currency": "EUR",
            "venue": "SIMULATED",
            "economic_id": "BTC",
            "capabilities": ["history", "quotes", "trades", "paper"],
            "metadata": {
                "network": "Bitcoin",
                "contract_address": None,
                "supply": None,
            },
            "source": "Lokale demonstratie",
            "quality": "SIMULATED",
            "as_of": AT,
        },
        {
            "id": "sim:ETH-EUR",
            "symbol": "ETH/EUR",
            "name": "Ether · demomarkt",
            "asset_class": "CRYPTO",
            "region": "GLOBAL",
            "currency": "EUR",
            "venue": "SIMULATED",
            "economic_id": "ETH",
            "capabilities": ["history", "quotes", "trades", "paper"],
            "metadata": {
                "network": "Ethereum",
                "contract_address": None,
                "supply": None,
            },
            "source": "Lokale demonstratie",
            "quality": "SIMULATED",
            "as_of": AT,
        },
        {
            "id": "sim:SOL-EUR",
            "symbol": "SOL/EUR",
            "name": "Solana · demomarkt",
            "asset_class": "CRYPTO",
            "region": "GLOBAL",
            "currency": "EUR",
            "venue": "SIMULATED",
            "economic_id": "SOL",
            "capabilities": ["history", "quotes", "trades", "paper"],
            "metadata": {"network": "Solana", "contract_address": None, "supply": None},
            "source": "Lokale demonstratie",
            "quality": "SIMULATED",
            "as_of": AT,
        },
        {
            "id": "metadata:AAPL",
            "symbol": "AAPL",
            "name": "Apple · metadata",
            "asset_class": "STOCK",
            "region": "US",
            "currency": "USD",
            "venue": "XNAS",
            "economic_id": "US0378331005",
            "capabilities": ["metadata"],
            "metadata": {
                "cik": "0000320193",
                "revenue": None,
                "earnings": None,
                "filings_url": "https://www.sec.gov/edgar/browse/?CIK=320193",
            },
            "source": "Statische identiteit; fundamentals niet opgehaald",
            "quality": "METADATA_ONLY",
            "as_of": None,
        },
        {
            "id": "metadata:SPY",
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF · metadata",
            "asset_class": "ETF",
            "region": "US",
            "currency": "USD",
            "venue": "ARCX",
            "economic_id": "US78462F1030",
            "capabilities": ["metadata"],
            "metadata": {
                "holdings": None,
                "expense_ratio": None,
                "holdings_date": None,
            },
            "source": "Statische identiteit; holdings niet opgehaald",
            "quality": "METADATA_ONLY",
            "as_of": None,
        },
        {
            "id": "metadata:EURUSD",
            "symbol": "EUR/USD",
            "name": "EUR/USD · referentie",
            "asset_class": "FX",
            "region": "EU",
            "currency": "USD",
            "venue": "REFERENCE",
            "economic_id": "EUR",
            "capabilities": ["metadata", "reference_fx"],
            "metadata": {"execution": False},
            "source": "ECB-adaptercontract; lokale fixture voor demo",
            "quality": "METADATA_ONLY",
            "as_of": None,
        },
    ]


def parse_news_api(raw, *, publisher, family, region, license_display=False):
    """Provider-independent licensed headline contract; adapters map their JSON to this shape."""
    import json

    if not license_display:
        raise PermissionError("SOURCE_RIGHTS_REQUIRED")
    if len(raw.encode()) > 524288:
        raise ValueError("NEWS_BATCH_TOO_LARGE")
    payload = json.loads(raw)
    if (
        not isinstance(payload, dict)
        or set(payload) != {"articles"}
        or not isinstance(payload["articles"], list)
        or len(payload["articles"]) > 100
    ):
        raise ValueError("NEWS_BATCH_SCHEMA")
    result = []
    for article in payload["articles"]:
        if not isinstance(article, dict) or set(article) - {
            "title",
            "url",
            "published_at",
            "updated_at",
            "snippet",
            "language",
            "instruments",
        }:
            raise ValueError("NEWS_ARTICLE_SCHEMA")
        if not all(
            isinstance(article.get(k), str) and article[k]
            for k in ["title", "url", "published_at"]
        ):
            raise ValueError("NEWS_REQUIRED_FIELDS")
        if any(
            k in article and article[k] is not None and not isinstance(article[k], str)
            for k in ["snippet", "language", "updated_at"]
        ):
            raise ValueError("NEWS_OPTIONAL_FIELD_TYPE")
        instruments = article.get("instruments", [])
        if (
            not isinstance(instruments, list)
            or len(instruments) > 50
            or not all(isinstance(i, str) and len(i) <= 100 for i in instruments)
        ):
            raise ValueError("NEWS_INSTRUMENTS_SCHEMA")
        dt = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("TIMEZONE_REQUIRED")
        updated = article.get("updated_at")
        if (
            updated
            and datetime.fromisoformat(updated.replace("Z", "+00:00")).tzinfo is None
        ):
            raise ValueError("TIMEZONE_REQUIRED")
        url = canonical_url(article["url"])
        title = plain(article["title"])
        snippet = plain(article.get("snippet", ""))[:400]
        result.append(
            {
                "id": sha256(url.encode()).hexdigest()[:20],
                "title": title,
                "snippet": snippet,
                "url": url,
                "published_at": dt.astimezone(timezone.utc).isoformat(),
                "updated_at": updated,
                "first_available_at": datetime.now(timezone.utc).isoformat(),
                "publisher": publisher,
                "source_family": family,
                "region": region,
                "language": article.get("language", "UNKNOWN"),
                "instruments": article.get("instruments", []),
                "quality": "UNVERIFIED_SOURCE",
                "kind": "NEWS",
                "rights": "HEADLINE_SNIPPET_LINK",
                "fingerprint": sha256(
                    json.dumps(article, sort_keys=True).encode()
                ).hexdigest(),
                "cluster_key": sha256(title.lower().encode()).hexdigest(),
                "revision": 1,
            }
        )
    return result
