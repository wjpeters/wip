from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import Field
from psycopg.types.json import Jsonb
from .storage import document, save
from .accounting_routes import Scope, Strict
from . import tax, rules, vault, estate, planning, lab, accounting
from .contracts import DecimalString


class TaxRequest(Strict):
    calculator: Literal["box1", "box2", "box3", "pension", "gift"]
    inputs: (
        tax.Box1Input | tax.Box2Input | tax.Box3Input | tax.PensionInput | tax.GiftInput
    )
    concept: bool = True
    scope: Scope


class RuleReview(Strict):
    rule_hash: str
    binding: str
    decision: Literal["APPROVE", "REJECT"]
    reviewer: str = Field(min_length=2, max_length=100)
    note: str = Field(min_length=10, max_length=2000)
    scope_understood: bool


class ScenarioJob(Strict):
    scenario: planning.Scenario
    mode: Literal["SCENARIO", "MONTE_CARLO"] = "SCENARIO"
    seed: int = Field(default=2025, ge=0, le=2147483647)
    paths: int = Field(default=100, ge=20, le=500)
    volatility: DecimalString = "15"


class ImpactInput(Strict):
    cash: DecimalString
    trade_amount: DecimalString
    fee: DecimalString
    tax_reserve: DecimalString
    long_term_reserve: DecimalString
    trading_pot: DecimalString


class EntityImpactInput(Strict):
    scope: Scope
    account_id: str
    scenario_id: str
    trade_amount: DecimalString
    fee: DecimalString
    long_term_reserve: DecimalString
    trading_pot: DecimalString


class VaultInput(Strict):
    name: str = Field(min_length=1, max_length=180)
    mime: str
    content_b64: str = Field(max_length=7000000)
    category: Literal["TAX", "PENSION", "ESTATE", "ACCOUNT", "OTHER"]
    entity_id: str = Field(max_length=80)
    note: str = Field(default="", max_length=1000)
    supersedes: str | None = None


class EstateInput(Strict):
    plan: estate.EstatePlan


class ComparisonInput(Strict):
    left: str
    right: str


class JobConfirm(Strict):
    job_id: str


def router(db, session, audit):
    r = APIRouter()

    def guarded(fn):
        try:
            return fn()
        except (ValueError, KeyError, ArithmeticError) as e:
            raise HTTPException(422, str(e))

    def state(c, lock=False):
        return document(c, "rules", rules.empty, lock)

    def enqueue(c, kind, request):
        c.execute("SELECT pg_advisory_xact_lock(10002)")
        count = c.execute(
            "SELECT count(*) FROM analysis_jobs WHERE status IN ('QUEUED','RUNNING')"
        ).fetchone()[0]
        if count >= 5:
            raise HTTPException(429, "ANALYSIS_QUEUE_FULL")
        jid = str(uuid.uuid4())
        c.execute(
            "INSERT INTO analysis_jobs(id,kind,status,request) VALUES(%s,%s,'QUEUED',%s)",
            (jid, kind, Jsonb(request)),
        )
        audit(c, "ANALYSIS_QUEUED", jid)
        return {"id": jid, "status": "QUEUED"}

    @r.get("/forms")
    def forms(request: Request):
        session(request)
        from .accounting_routes import (
            EntityInput,
            AccountInput,
            OwnershipInput,
            AssetInput,
            MarkInput,
            SplitInput,
            PerformanceInput,
            FXMarkInput,
        )

        models = {
            "scenario": planning.Scenario,
            "box1": tax.Box1Input,
            "box2": tax.Box2Input,
            "box3": tax.Box3Input,
            "pension": tax.PensionInput,
            "gift": tax.GiftInput,
            "estate": estate.EstatePlan,
            "backtest": lab.BacktestInput,
            "impact": ImpactInput,
            "entity": EntityInput,
            "account": AccountInput,
            "ownership": OwnershipInput,
            "asset": AssetInput,
            "mark": MarkInput,
            "split": SplitInput,
            "performance": PerformanceInput,
            "fxmark": FXMarkInput,
            "entity_impact": EntityImpactInput,
        }
        return {key: model.model_json_schema() for key, model in models.items()}

    @r.get("/tax/rules")
    def get_rules(request: Request):
        session(request)
        with db() as c:
            return rules.status(state(c))

    @r.post("/tax/source-check")
    def check_sources(request: Request):
        session(request)
        with db() as c:
            return enqueue(
                c, "SOURCE_CHECK", {"scope": "PUBLIC", "rule_hash": tax.rule_hash()}
            )

    @r.post("/tax/review")
    def review(body: RuleReview, request: Request):
        token, _ = session(request)
        with db() as c:
            st = state(c, True)
            status = rules.status(st)
            if (
                body.rule_hash != tax.rule_hash()
                or body.binding != status["current_binding"]
            ):
                raise HTTPException(409, "RULE_OR_SOURCE_CHANGED")
            if body.decision == "APPROVE" and (
                not body.scope_understood
                or status["missing_source_checks"]
                or not status["test_report"]["passed"]
            ):
                raise HTTPException(422, "RULE_APPROVAL_REQUIREMENTS_NOT_MET")
            item = {
                **body.model_dump(),
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "session": token,
            }
            st["reviews"].append(item)
            st["approval"] = item if body.decision == "APPROVE" else None
            save(c, "rules", st)
            audit(c, "RULE_" + body.decision, body.rule_hash)
        return {"saved": True}

    @r.post("/tax/calculate")
    def calculate_tax(body: TaxRequest, request: Request):
        session(request)
        with db() as c:
            current = rules.status(state(c))
            approved = (
                tax.rule_hash()
                if current["review_status"] == "APPROVED_SCOPED"
                else None
            )
            result = guarded(
                lambda: tax.calculate(
                    body.calculator,
                    body.inputs.model_dump(),
                    approved_hash=approved,
                    concept=body.concept,
                )
            )
            result["scope"] = body.scope
            result["source_binding"] = current["current_binding"]
            result["calculated_at"] = datetime.now(timezone.utc).isoformat()
            rid = str(uuid.uuid4())
            result["id"] = rid
            c.execute(
                "INSERT INTO analysis_jobs(id,kind,status,request,result) VALUES(%s,'TAX','COMPLETED',%s,%s)",
                (rid, Jsonb(body.model_dump()), Jsonb(result)),
            )
            audit(c, "TAX_SCENARIO_CALCULATED", rid)
        return result

    @r.post("/plans/analyze")
    def scenario(body: ScenarioJob, request: Request):
        session(request)
        guarded(lambda: planning.validate(body.scenario))
        with db() as c:
            # A scenario records an explicit accounting revision. Never quietly refresh facts.
            book = document(
                c,
                "finance:" + body.scenario.scope,
                lambda: accounting.new_book(body.scenario.scope),
            )
            if book["revision"] != body.scenario.source_revision:
                raise HTTPException(409, "FINANCE_REVISION_CHANGED")
            if body.scenario.entity_id not in book.get("entities", {}):
                raise HTTPException(422, "SCENARIO_ENTITY_REQUIRED")
            return enqueue(c, body.mode, body.model_dump())

    @r.post("/plans/compare")
    def compare(body: ComparisonInput, request: Request):
        session(request)
        with db() as c:
            items = []
            for jid in [body.left, body.right]:
                row = c.execute(
                    "SELECT kind,request,result FROM analysis_jobs WHERE id=%s AND status='COMPLETED'",
                    (jid,),
                ).fetchone()
                if not row:
                    raise HTTPException(422, "COMPLETED_SNAPSHOT_REQUIRED")
                items.append(row)
        left, right = items

        def scope(row):
            return row[1].get("scope", row[1].get("scenario", {}).get("scope"))

        if left[0] != right[0] or scope(left) != scope(right):
            raise HTTPException(422, "INCOMPARABLE_SNAPSHOT_SCOPES")
        if left[0] == "SCENARIO":
            if left[2]["inputs"]["months"] != right[2]["inputs"]["months"]:
                raise HTTPException(422, "SCENARIO_HORIZON_MISMATCH")
            a, b = left[2]["base"]["rows"][-1], right[2]["base"]["rows"][-1]
            keys = [
                "cash",
                "investments",
                "pension_locked",
                "tax_reserve",
                "liquid_wealth",
                "real_liquid_wealth",
            ]
        elif left[0] == "TAX":
            if left[2]["calculator"] != right[2]["calculator"]:
                raise HTTPException(422, "CALCULATOR_MISMATCH")
            a, b = left[2]["result"], right[2]["result"]
            keys = [
                k
                for k in [
                    "tax",
                    "gross_tax_before_credits",
                    "remaining_tax",
                    "annual_room",
                    "reserve_room",
                    "deductible_paid",
                ]
                if a.get(k) is not None and b.get(k) is not None
            ]
        else:
            raise HTTPException(422, "COMPARISON_KIND_NOT_SUPPORTED")
        delta = [
            {
                "field": k,
                "before": a[k],
                "after": b[k],
                "difference": accounting.money(
                    accounting.amount(b[k]) - accounting.amount(a[k])
                ),
            }
            for k in keys
        ]
        ai, bi = left[2].get("inputs", {}), right[2].get("inputs", {})
        changes = [
            {"field": k, "before": ai.get(k), "after": bi.get(k)}
            for k in sorted(set(ai) | set(bi))
            if ai.get(k) != bi.get(k)
        ]
        return {
            "scope": scope(left),
            "deltas": delta,
            "changed_assumptions": changes,
            "left_version": left[2].get("rule_hash", left[2].get("model_version")),
            "right_version": right[2].get("rule_hash", right[2].get("model_version")),
            "explanation": "Verschillen volgen uit de getoonde invoerwijzigingen en versies; geen causaal bewijs of advies.",
        }

    @r.post("/plans/impact")
    def impact(body: ImpactInput, request: Request):
        session(request)
        return guarded(lambda: planning.trade_impact(**body.model_dump()))

    @r.post("/plans/entity-impact")
    def entity_impact(body: EntityImpactInput, request: Request):
        session(request)
        with db() as c:
            book = document(
                c, "finance:" + body.scope, lambda: accounting.new_book(body.scope)
            )
            account = book["accounts"].get(body.account_id)
            row = c.execute(
                "SELECT request,result FROM analysis_jobs WHERE id=%s AND kind='SCENARIO' AND status='COMPLETED'",
                (body.scenario_id,),
            ).fetchone()
            if not account or not row:
                raise HTTPException(422, "ACCOUNT_AND_COMPLETED_SCENARIO_REQUIRED")
            scenario = row[0]["scenario"]
            if (
                scenario["scope"] != body.scope
                or scenario["entity_id"] != account["entity"]
            ):
                raise HTTPException(422, "PLAN_OWNER_MISMATCH")
            if scenario["source_revision"] != book["revision"]:
                raise HTTPException(409, "PLAN_ACCOUNTING_REVISION_CHANGED")
            if account["currency"] != "EUR":
                raise HTTPException(422, "EUR_ACCOUNT_REQUIRED")
            snapshot = accounting.snapshot(book)
            cash = next(
                a["balance_eur"]
                for a in snapshot["accounts"]
                if a["id"] == body.account_id
            )
            result = guarded(
                lambda: planning.trade_impact(
                    cash,
                    body.trade_amount,
                    body.fee,
                    scenario["initial_tax_reserve"],
                    body.long_term_reserve,
                    body.trading_pot,
                )
            )
            return {
                **result,
                "scope": body.scope,
                "entity_id": account["entity"],
                "account_id": body.account_id,
                "scenario_id": body.scenario_id,
                "source_revision": book["revision"],
                "scenario_name": scenario["name"],
                "assumption": "Separate protected reserves on this account; no tax assessed or order authorized.",
            }

    @r.get("/analysis")
    def jobs(request: Request, scope: Literal["DEMO", "PERSONAL", "PUBLIC"] = "DEMO"):
        session(request)
        with db() as c:
            rows = c.execute(
                "SELECT id,kind,status,request,created_at FROM analysis_jobs WHERE COALESCE(request->>'scope',request->'scenario'->>'scope')=%s ORDER BY created_at DESC LIMIT 100",
                (scope,),
            ).fetchall()
        return {
            "jobs": [
                {
                    "id": row[0],
                    "kind": row[1],
                    "status": row[2],
                    "name": row[3]
                    .get("scenario", {})
                    .get("name", row[3].get("calculator", row[1]).upper()),
                    "created_at": row[4].isoformat(),
                }
                for row in rows
            ]
        }

    @r.get("/analysis/{job_id}")
    def job(job_id: str, request: Request):
        session(request)
        with db() as c:
            row = c.execute(
                "SELECT id,kind,status,result,created_at FROM analysis_jobs WHERE id=%s",
                (job_id,),
            ).fetchone()
        if not row:
            raise HTTPException(404, "JOB_NOT_FOUND")
        return {
            "id": row[0],
            "kind": row[1],
            "status": row[2],
            "result": row[3],
            "created_at": row[4].isoformat(),
        }

    @r.post("/analysis/{job_id}/cancel")
    def cancel(job_id: str, request: Request):
        session(request)
        with db() as c:
            changed = c.execute(
                "UPDATE analysis_jobs SET status='CANCELED' WHERE id=%s AND status IN ('QUEUED','RUNNING') RETURNING id",
                (job_id,),
            ).fetchone()
            audit(c, "ANALYSIS_CANCEL", job_id)
        return {"canceled": bool(changed)}

    @r.post("/lab/replay")
    def replay(body: lab.ReplayInput, request: Request):
        session(request)
        return guarded(lambda: lab.replay(body))

    @r.post("/lab/backtest")
    def backtest(body: lab.BacktestInput, request: Request):
        session(request)
        with db() as c:
            return enqueue(c, "BACKTEST", {**body.model_dump(), "scope": "DEMO"})

    @r.get("/estate/{scope}")
    def estate_list(scope: Scope, request: Request):
        session(request)
        with db() as c:
            return document(c, "estate:" + scope, lambda: {"plans": []})

    @r.post("/estate/{scope}")
    def estate_save(body: EstateInput, scope: Scope, request: Request):
        session(request)
        assessment = guarded(lambda: estate.assess(body.plan))
        pid = str(uuid.uuid4())
        with db() as c:
            for did in body.plan.document_ids:
                if not c.execute(
                    "SELECT id FROM vault WHERE id=%s AND scope=%s", (did, scope)
                ).fetchone():
                    raise HTTPException(422, "DOCUMENT_SCOPE_MISMATCH")
            st = document(c, "estate:" + scope, lambda: {"plans": []}, True)
            st["plans"].append(
                {
                    "id": pid,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "plan": body.plan.model_dump(),
                    "assessment": assessment,
                    "rule_hash": tax.rule_hash(),
                    "status": "CONCEPT_REQUIRES_NOTARY_REVIEW",
                }
            )
            save(c, "estate:" + scope, st)
            audit(c, "ESTATE_SCENARIO_SAVED", pid)
        return {"id": pid, "assessment": assessment}

    @r.get("/vault/{scope}")
    def documents(scope: Scope, request: Request):
        session(request)
        with db() as c:
            rows = c.execute(
                "SELECT id,name,mime,content_hash,size,created_at FROM vault WHERE scope=%s ORDER BY created_at DESC",
                (scope,),
            ).fetchall()
        return {
            "documents": [
                {
                    "id": row[0],
                    **guarded(lambda: vault.metadata(row[1])),
                    "mime": row[2],
                    "sha256": row[3],
                    "size": row[4],
                    "created_at": row[5].isoformat(),
                }
                for row in rows
            ],
            "storage": "LOCAL_AUTHENTICATED_ENCRYPTION",
            "max_bytes": vault.MAX_BYTES,
        }

    @r.post("/vault/{scope}")
    def upload(body: VaultInput, scope: Scope, request: Request):
        session(request)
        vid = str(uuid.uuid4())
        payload = guarded(
            lambda: vault.encrypt(
                body.name,
                body.mime,
                body.content_b64,
                {
                    "category": body.category,
                    "entity_id": body.entity_id,
                    "note": body.note,
                    "supersedes": body.supersedes,
                },
            )
        )
        with db() as c:
            c.execute("SELECT pg_advisory_xact_lock(10003)")
            if c.execute("SELECT count(*) FROM vault").fetchone()[0] >= 500:
                raise HTTPException(422, "VAULT_DOCUMENT_LIMIT")
            if (
                body.supersedes
                and not c.execute(
                    "SELECT id FROM vault WHERE id=%s AND scope=%s",
                    (body.supersedes, scope),
                ).fetchone()
            ):
                raise HTTPException(422, "PREVIOUS_DOCUMENT_NOT_FOUND")
            c.execute(
                "INSERT INTO vault(id,scope,name,mime,ciphertext,content_hash,size) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (
                    vid,
                    scope,
                    payload["name"],
                    payload["mime"],
                    payload["ciphertext"],
                    payload["content_hash"],
                    payload["size"],
                ),
            )
            audit(c, "VAULT_DOCUMENT_ADDED", vid)
        return {"id": vid, "sha256": payload["content_hash"]}

    @r.get("/vault/{scope}/{document_id}/download")
    def download(scope: Scope, document_id: str, request: Request):
        session(request)
        with db() as c:
            row = c.execute(
                "SELECT name,mime,ciphertext,content_hash FROM vault WHERE id=%s AND scope=%s",
                (document_id, scope),
            ).fetchone()
            if not row:
                raise HTTPException(404, "DOCUMENT_NOT_FOUND")
            audit(c, "VAULT_DOCUMENT_DOWNLOADED", document_id)
        metadata = guarded(lambda: vault.metadata(row[0]))
        raw = guarded(lambda: vault.decrypt(row[2], row[3]))
        return Response(
            raw,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": "attachment; filename*=UTF-8''"
                + quote(metadata["name"], safe=""),
                "Content-Security-Policy": "sandbox; default-src 'none'",
            },
        )

    return r
