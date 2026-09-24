"""Explicit bounded read-only connector checks; never called by application startup."""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
from app.markets import CoinbaseAdapter, AlpacaAdapter  # noqa: E402 - local package path is initialized above
from app.providers import ecb_reference, sec_facts  # noqa: E402 - local package path is initialized above
import httpx  # noqa: E402 - local package path is initialized above
from websockets.asyncio.client import connect  # noqa: E402 - local package path is initialized above

parser = argparse.ArgumentParser()
parser.add_argument("provider", choices=["coinbase", "alpaca", "ecb", "sec"])
parser.add_argument("--confirm-readonly", action="store_true")
args = parser.parse_args()
if not args.confirm_readonly:
    raise SystemExit(
        "Read-only check requires --confirm-readonly. No network request made."
    )
config_path = ROOT / ".secrets/providers.json"
config = json.loads(config_path.read_text()) if config_path.exists() else {}


async def check():
    provider = args.provider
    if provider == "coinbase":
        async with connect(
            CoinbaseAdapter.endpoint, open_timeout=8, max_size=1048576, proxy=None
        ) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "subscribe",
                        "channel": "ticker",
                        "product_ids": ["BTC-EUR"],
                    }
                )
            )
            for _ in range(20):
                raw = await asyncio.wait_for(ws.recv(), timeout=8)
                if json.loads(raw).get("channel") == "ticker":
                    return {
                        "records": len(CoinbaseAdapter.quotes(raw)),
                        "feed": "coinbase-advanced-ticker",
                    }
    elif provider == "alpaca":
        c = config.get("alpaca", {})
        feed = c.get("feed", "iex")
        if not c.get("key") or not c.get("secret"):
            return {"status": "NOT_RUN_MISSING_CREDENTIALS"}
        if feed not in AlpacaAdapter.feeds or feed not in c.get("entitlements", []):
            return {"status": "NOT_RUN_MISSING_ENTITLEMENT_CONFIRMATION"}
        async with connect(
            "wss://stream.data.alpaca.markets/v2/" + feed,
            open_timeout=8,
            max_size=1048576,
            proxy=None,
        ) as ws:
            await ws.send(
                json.dumps({"action": "auth", "key": c["key"], "secret": c["secret"]})
            )
            authenticated = False
            for _ in range(20):
                raw = await asyncio.wait_for(ws.recv(), timeout=8)
                events = json.loads(raw)
                if any(e.get("T") == "error" for e in events):
                    return {"status": "PROVIDER_AUTH_OR_ENTITLEMENT_REJECTED"}
                if (
                    any(e.get("msg") == "authenticated" for e in events)
                    and not authenticated
                ):
                    authenticated = True
                    await ws.send(
                        json.dumps({"action": "subscribe", "quotes": ["AAPL"]})
                    )
                quotes = AlpacaAdapter.quotes(raw, feed, c["entitlements"])
                if quotes:
                    return {"records": len(quotes), "feed": feed}
    else:
        c = config.get("sec", {})
        if provider == "sec" and not c.get("user_agent_contact"):
            return {"status": "NOT_RUN_MISSING_SEC_CONTACT"}
        url = (
            "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
            if provider == "ecb"
            else "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
        )
        headers = {
            "User-Agent": "ModernTradeTerminal "
            + c.get("user_agent_contact", "LocalReferenceCheck")
        }
        with httpx.Client(timeout=15, trust_env=False) as client:
            with client.stream(
                "GET", url, headers=headers, follow_redirects=False
            ) as response:
                response.raise_for_status()
                parts = []
                size = 0
                for part in response.iter_bytes():
                    size += len(part)
                    if size > 8_000_000:
                        raise ValueError("RESPONSE_SIZE_LIMIT")
                    parts.append(part)
            raw = b"".join(parts).decode()
        if provider == "ecb":
            fx = ecb_reference(raw)
            return {
                "records": len(fx.rates),
                "as_of": fx.as_of,
                "feed": "ecb-reference-daily",
            }
        from datetime import date

        facts = sec_facts(raw, "0000320193", date.today().isoformat())
        return {"records": len(facts["facts"]), "feed": "sec-edgar"}
    return {"status": "NO_MARKET_MESSAGE_WITHIN_BOUNDED_PROBE"}


try:
    result = asyncio.run(asyncio.wait_for(check(), timeout=30))
    result.setdefault("status", "LIVE_READ_ONLY_PROBE_PASSED")
except Exception as e:
    result = {"status": "PROBE_FAILED", "failure_class": type(e).__name__}
result.update(
    provider=args.provider,
    checked_at=time.time(),
    orders_enabled=False,
    persistent_subscription=False,
    data_retained=False,
)
print(json.dumps(result, indent=2))
