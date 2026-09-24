from __future__ import annotations
import xml.etree.ElementTree as ET
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from . import accounting as core
from .storage import document, save
from .contracts import DecimalString

Scope = Literal["DEMO", "PERSONAL"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EntityInput(Strict):
    name: str = Field(min_length=1, max_length=100)
    kind: Literal["PERSON", "HOUSEHOLD", "HOLDING", "OPERATING_COMPANY"]


class AccountInput(Strict):
    name: str = Field(min_length=1, max_length=100)
    entity: str
    currency: Literal["EUR", "USD", "GBP"] = "EUR"
    opening: DecimalString = "0"


class OwnershipInput(Strict):
    parent: str
    child: str
    percentage: DecimalString


class ImportInput(Strict):
    content: str = Field(max_length=2000000)
    format: Literal["CSV", "CAMT053"] = "CSV"
    account: str = ""
    delimiter: Literal[",", ";", "\t"] = ","
    decimal_separator: Literal[".", ","] = "."
    date_format: Literal["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"] = "%Y-%m-%d"
    mapping: dict[str, str] | None = None


class ImportRow(Strict):
    date: str
    kind: Literal[
        "INCOME",
        "EXPENSE",
        "TRANSFER",
        "INTERCOMPANY",
        "BUY",
        "SELL",
        "DIVIDEND",
        "INTEREST",
        "FEE",
        "REVIEW",
    ]
    amount: DecimalString
    currency: str
    account: str
    reference: str = Field(min_length=1, max_length=160)
    counteraccount: str = ""
    asset: str = ""
    quantity: DecimalString = "0"
    fee: DecimalString = "0"
    fx_rate: DecimalString = "1"
    line: int = 0


class ReviewedImport(Strict):
    rows: list[ImportRow] = Field(max_length=2000)
    original_preview_id: str


class ConfirmImport(Strict):
    preview_id: str


class AssetInput(Strict):
    asset_id: str | None = None
    name: str = Field(min_length=1, max_length=100)
    entity: str
    kind: Literal[
        "PROPERTY",
        "LIABILITY",
        "RECEIVABLE",
        "EQUITY_INTEREST",
        "PENSION_RIGHT",
        "CASH_EQUIVALENT",
    ]
    value_eur: DecimalString
    as_of: str
    linked_entity: str | None = None


class MarkInput(Strict):
    position_id: str
    price_eur: DecimalString
    as_of: str
    source: str = Field(min_length=1, max_length=120)


class ReverseInput(Strict):
    event_id: str
    reason: str = Field(min_length=8, max_length=500)


class SplitInput(Strict):
    position_id: str
    action_id: str = Field(min_length=1, max_length=100)
    numerator: DecimalString
    denominator: DecimalString
    effective_date: str


class FXMarkInput(Strict):
    account_id: str
    rate_to_eur: DecimalString
    as_of: str
    source: str = Field(min_length=1, max_length=120)


class PerformancePeriod(Strict):
    start: DecimalString
    end: DecimalString
    external_flow: DecimalString


class PerformanceFlow(Strict):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    amount: DecimalString


class PerformanceInput(Strict):
    periods: list[PerformancePeriod] = Field(min_length=1, max_length=1000)
    flows: list[PerformanceFlow] = Field(max_length=1000)


def router(db, session, audit):
    r = APIRouter()

    def load(c, scope, lock=False):
        return document(c, "finance:" + scope, lambda: core.new_book(scope), lock)

    def persist(c, scope, b, action, ref):
        b["revision"] += 1
        save(c, "finance:" + scope, b)
        audit(c, action, ref)

    def guard(fn):
        try:
            return fn()
        except (ValueError, ArithmeticError, KeyError, ET.ParseError) as e:
            raise HTTPException(422, str(e))

    def preview(c, scope, b, rows, token, source_hash):
        result = guard(lambda: core.preview_import(b, rows))
        result.pop("book_after")
        pid = str(uuid.uuid4())
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        # Persist only rows/result; no client-provided book snapshot is trusted.
        b["previews"] = {
            k: v
            for k, v in b["previews"].items()
            if v["expires_at"] > datetime.now(timezone.utc).isoformat()
        }
        b["previews"][pid] = {
            "session": token,
            "rows": rows,
            "revision": b["revision"],
            "expires_at": expiry,
            "source_hash": source_hash,
        }
        save(c, "finance:" + scope, b)
        return {
            **result,
            "preview_id": pid,
            "revision": b["revision"],
            "scope": scope,
            "expires_at": expiry,
            "source_hash": source_hash,
        }

    @r.get("/finance/{scope}")
    def get_book(scope: Scope, request: Request, entity: str | None = None):
        session(request)
        with db() as c:
            return guard(lambda: core.snapshot(load(c, scope), entity))

    @r.post("/finance/DEMO/load-example")
    def example(request: Request):
        session(request)
        with db() as c:
            b = load(c, "DEMO", True)
            if b["entities"]:
                return {"loaded": False, "reason": "DEMO_ALREADY_PRESENT"}
            save(c, "finance:DEMO", core.demo_book())
            audit(c, "DEMO_FINANCE_CREATED", "DEMO")
        return {"loaded": True}

    @r.post("/finance/{scope}/entities")
    def entity(body: EntityInput, scope: Scope, request: Request):
        session(request)
        eid = uuid.uuid4().hex[:12]
        with db() as c:
            b = load(c, scope, True)
            guard(lambda: core.add_entity(b, eid, body.name, body.kind))
            persist(c, scope, b, "ENTITY_CREATED", eid)
        return {"id": eid}

    @r.post("/finance/{scope}/accounts")
    def account(body: AccountInput, scope: Scope, request: Request):
        session(request)
        aid = body.asset_id or uuid.uuid4().hex[:12]
        with db() as c:
            b = load(c, scope, True)
            guard(
                lambda: core.add_account(
                    b, aid, body.name, body.entity, body.currency, body.opening
                )
            )
            persist(c, scope, b, "FINANCE_ACCOUNT_CREATED", aid)
        return {"id": aid}

    @r.post("/finance/{scope}/ownership")
    def ownership(body: OwnershipInput, scope: Scope, request: Request):
        session(request)
        with db() as c:
            b = load(c, scope, True)
            guard(
                lambda: core.set_ownership(b, body.parent, body.child, body.percentage)
            )
            persist(c, scope, b, "OWNERSHIP_UPDATED", body.child)
        return {"saved": True}

    @r.post("/finance/{scope}/imports/preview")
    def import_preview(body: ImportInput, scope: Scope, request: Request):
        token, _ = session(request)
        rows = guard(
            lambda: core.parse_csv(
                body.content,
                body.mapping,
                body.delimiter,
                body.decimal_separator,
                body.date_format,
            )
            if body.format == "CSV"
            else core.parse_camt(body.content, body.account)
        )
        fingerprint = hashlib.sha256(body.content.encode()).hexdigest()
        with db() as c:
            return preview(c, scope, load(c, scope, True), rows, token, fingerprint)

    @r.post("/finance/{scope}/imports/review")
    def import_review(body: ReviewedImport, scope: Scope, request: Request):
        token, _ = session(request)
        with db() as c:
            b = load(c, scope, True)
            original = b["previews"].get(body.original_preview_id)
            if not original or original["session"] != token:
                raise HTTPException(404, "PREVIEW_NOT_FOUND")
            if original["expires_at"] <= datetime.now(timezone.utc).isoformat():
                raise HTTPException(409, "PREVIEW_EXPIRED")
            return preview(
                c,
                scope,
                b,
                [row.model_dump() for row in body.rows],
                token,
                original["source_hash"],
            )

    @r.post("/finance/{scope}/imports/confirm")
    def import_confirm(body: ConfirmImport, scope: Scope, request: Request):
        token, _ = session(request)
        with db() as c:
            b = load(c, scope, True)
            item = b["previews"].get(body.preview_id)
            if body.preview_id in b["imports"]:
                previous = b["imports"][body.preview_id]
                if previous.get("session") != token:
                    raise HTTPException(404, "PREVIEW_NOT_FOUND")
                return {k: v for k, v in previous.items() if k != "session"}
            if not item or item["session"] != token:
                raise HTTPException(404, "PREVIEW_NOT_FOUND")
            if (
                item["expires_at"] <= datetime.now(timezone.utc).isoformat()
                or item["revision"] != b["revision"]
            ):
                raise HTTPException(409, "PREVIEW_CHANGED_OR_EXPIRED")
            result = guard(lambda: core.preview_import(b, item["rows"]))
            if result["review_count"]:
                raise HTTPException(422, "IMPORT_REQUIRES_REVIEW")
            b = result.pop("book_after")
            answer = {
                "imported": result["importable"],
                "duplicates": result["duplicates"],
                "source_hash": item["source_hash"],
            }
            b["imports"][body.preview_id] = {**answer, "session": token}
            persist(c, scope, b, "FINANCE_IMPORT_COMMITTED", body.preview_id)
        return answer

    @r.post("/finance/{scope}/assets")
    def asset(body: AssetInput, scope: Scope, request: Request):
        session(request)
        aid = body.asset_id or uuid.uuid4().hex[:12]
        with db() as c:
            b = load(c, scope, True)
            if body.entity not in b["entities"]:
                raise HTTPException(422, "UNKNOWN_ENTITY")
            if body.linked_entity and body.linked_entity not in b["entities"]:
                raise HTTPException(422, "UNKNOWN_LINKED_ENTITY")
            if body.asset_id and body.asset_id not in b.get("assets", {}):
                raise HTTPException(404, "ASSET_NOT_FOUND")
            if body.asset_id:
                b["valuations"].append(
                    {
                        "kind": "ASSET_UPDATE",
                        "id": aid,
                        "previous": b["assets"][aid],
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            value = core.amount(body.value_eur)
            if (body.kind == "LIABILITY" and value > 0) or (
                body.kind != "LIABILITY" and value < 0
            ):
                raise HTTPException(422, "INVALID_ASSET_SIGN")
            guard(lambda: core.date.fromisoformat(body.as_of))
            if core.date.fromisoformat(body.as_of) > core.date.today():
                raise HTTPException(422, "FUTURE_VALUATION_NOT_CURRENT")
            b.setdefault("assets", {})[aid] = {
                "id": aid,
                **body.model_dump(),
                "quality": "USER_ENTERED" if scope == "PERSONAL" else "SIMULATED",
            }
            persist(c, scope, b, "ASSET_RECORDED", aid)
        return {"id": aid}

    @r.post("/finance/{scope}/mark")
    def mark(body: MarkInput, scope: Scope, request: Request):
        session(request)
        with db() as c:
            b = load(c, scope, True)
            pos = b["positions"].get(body.position_id)
            if not pos:
                raise HTTPException(404, "UNKNOWN_POSITION")
            price = core.amount(body.price_eur)
            if price < 0:
                raise HTTPException(422, "NEGATIVE_MARK")
            guard(lambda: core.date.fromisoformat(body.as_of))
            if core.date.fromisoformat(body.as_of) > core.date.today():
                raise HTTPException(422, "FUTURE_VALUATION_NOT_CURRENT")
            b["valuations"].append(
                {
                    "position_id": body.position_id,
                    "previous": pos.get("mark_eur"),
                    **body.model_dump(),
                }
            )
            pos["mark_eur"] = str(price)
            pos["mark_at"] = body.as_of
            persist(c, scope, b, "VALUATION_RECORDED", body.position_id)
        return {"saved": True}

    @r.post("/finance/{scope}/fx-valuation")
    def fx_valuation(body: FXMarkInput, scope: Scope, request: Request):
        session(request)
        with db() as c:
            b = load(c, scope, True)
            result = guard(lambda: core.revalue_cash(b, **body.model_dump()))
            persist(c, scope, b, "FX_VALUATION_RECORDED", body.account_id)
        return result

    @r.post("/finance/{scope}/reverse")
    def reverse(body: ReverseInput, scope: Scope, request: Request):
        session(request)
        with db() as c:
            b = load(c, scope, True)
            guard(lambda: core.reverse_event(b, body.event_id, body.reason))
            persist(c, scope, b, "JOURNAL_REVERSED", body.event_id)
        return {"saved": True}

    @r.post("/finance/{scope}/split")
    def split(body: SplitInput, scope: Scope, request: Request):
        session(request)
        with db() as c:
            b = load(c, scope, True)
            result = guard(lambda: core.corporate_action(b, **body.model_dump()))
            persist(c, scope, b, "CORPORATE_ACTION_RECORDED", body.action_id)
        return {"status": result}

    @r.get("/finance/{scope}/export")
    def export(scope: Scope, request: Request):
        session(request)
        with db() as c:
            content = core.csv_export(load(c, scope))
        return Response(
            content,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="mtt-ledger.csv"'},
        )

    @r.post("/finance/performance/calculate")
    def performance(body: PerformanceInput, request: Request):
        session(request)
        return guard(
            lambda: core.performance(
                [p.model_dump() for p in body.periods],
                [f.model_dump() for f in body.flows],
            )
        )

    return r
