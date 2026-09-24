"""Official source evidence and human rule review; content never edits executable rules."""

from datetime import datetime, timezone, timedelta
import hashlib
import re
from html.parser import HTMLParser
from . import tax


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignore += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.ignore = max(0, self.ignore - 1)

    def handle_data(self, data):
        if not self.ignore:
            self.parts.append(data)


def empty():
    return {"checks": {}, "reviews": [], "approval": None}


def test_vectors():
    common = {"resident_full_year": True, "inputs_complete": True}
    cases = [
        (
            "box2",
            {"gross_income": "10000", "dividend_tax_withheld": "1500"},
            "remaining_tax",
            "950.00",
            "box2",
        ),
        (
            "box3",
            {
                "savings": "150000",
                "other_assets": "0",
                "debts": "0",
                "fiscal_partner_all_year": False,
            },
            "tax",
            "455.00",
            "box3",
        ),
        (
            "box3",
            {
                "savings": "150000",
                "other_assets": "275000",
                "debts": "100000",
                "fiscal_partner_all_year": False,
            },
            "tax",
            "4638.00",
            "box3",
        ),
        (
            "box3",
            {
                "savings": "150000",
                "other_assets": "0",
                "debts": "0",
                "fiscal_partner_all_year": True,
                "allocation_percent": "50",
            },
            "tax",
            "85.00",
            "box3",
        ),
    ]
    results = []
    for kind, inputs, field, expected, source in cases:
        actual = tax.calculate(kind, {**common, **inputs}, concept=True)["result"][
            field
        ]
        results.append(
            {
                "calculator": kind,
                "field": field,
                "expected": expected,
                "actual": actual,
                "passed": expected == actual,
                "source_id": source,
            }
        )
    return {
        "passed": all(r["passed"] for r in results),
        "cases": results,
        "rule_hash": tax.rule_hash(),
    }


def binding(state):
    return hashlib.sha256(
        (
            tax.rule_hash()
            + "".join(
                s["id"] + str(state["checks"].get(s["id"], {}).get("latest_hash", ""))
                for s in tax.SOURCES
            )
        ).encode()
    ).hexdigest()


def status(state):
    report = test_vectors()
    missing = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    for source in tax.SOURCES:
        check = state["checks"].get(source["id"], {})
        if (
            check.get("status") not in {"BASELINE_CAPTURED", "UNCHANGED", "CHANGED"}
            or check.get("checked_at", "") < cutoff
        ):
            missing.append(source["id"])
    approved = state.get("approval")
    valid = bool(
        approved
        and approved["binding"] == binding(state)
        and not missing
        and report["passed"]
    )
    return {
        **tax.registry(),
        "review_status": "APPROVED_SCOPED" if valid else "NEEDS_HUMAN_REVIEW",
        "approval": {k: v for k, v in approved.items() if k != "session"}
        if approved
        else None,
        "checks": state["checks"],
        "reviews": [
            {k: v for k, v in item.items() if k != "session"}
            for item in state["reviews"][-30:]
        ],
        "test_report": report,
        "missing_source_checks": missing,
        "current_binding": binding(state),
    }


def fetch_source(source, previous, client):
    now = datetime.now(timezone.utc).isoformat()
    try:
        # URL is from the immutable allowlist, never from a document or user request.
        with client.stream(
            "GET",
            source["url"],
            follow_redirects=False,
            headers={"User-Agent": "ModernTradeTerminal-LocalRuleCheck/1.0"},
        ) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("UNEXPECTED_STATUS")
            chunks = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > 8 * 1024 * 1024:
                    raise ValueError("SOURCE_TOO_LARGE")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if not raw:
                raise ValueError("EMPTY_SOURCE")
            mime = response.headers.get("content-type", "")
        fingerprint = hashlib.sha256(raw).hexdigest()
        text_hash = fingerprint
        if "html" in mime:
            parser = Text()
            parser.feed(raw.decode("utf-8", errors="replace"))
            normalized = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
            if len(normalized) < 100:
                raise ValueError("SOURCE_CONTENT_MISSING")
            text_hash = hashlib.sha256(normalized.encode()).hexdigest()
        old = previous.get("latest_hash")
        result = {
            "status": "BASELINE_CAPTURED"
            if not old
            else "UNCHANGED"
            if old == text_hash
            else "CHANGED",
            "checked_at": now,
            "latest_hash": text_hash,
            "raw_hash": fingerprint,
            "previous_hash": old,
            "bytes": size,
            "url": source["url"],
            "mime": mime,
            "failure": None,
        }
        return result
    except Exception as e:
        # Never equate a failed crawl with no change, and never log network credentials.
        return {
            **previous,
            "status": "FETCH_FAILED",
            "checked_at": now,
            "url": source["url"],
            "failure": type(e).__name__,
        }
