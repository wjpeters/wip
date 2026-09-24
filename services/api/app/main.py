from __future__ import annotations
import hashlib
import hmac
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from decimal import Decimal as D
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from .contracts import OrderIntent, JournalLine, DecimalString
from .finance import calculate, initial_state, portfolio, cash_path, PolicyError
from .market import (
    INSTRUMENTS,
    fixture_quote,
    fixture_trades,
    history,
    now,
    KrakenPublicProvider,
)
from .ai import assess_public_text

PORT = os.getenv("WEB_PORT", "4186")
ORIGINS = {f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"}
HOSTS = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
SESSION_SECONDS = 28800
LOGIN_ATTEMPTS = {}


def db():
    if os.getenv("DATABASE_URL"):
        return psycopg.connect(os.environ["DATABASE_URL"])
    return psycopg.connect(
        host="postgres",
        dbname="mtt",
        user="mtt",
        password=Path("/run/secrets/db_password").read_text().strip(),
    )


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(value, salt):
    return hashlib.pbkdf2_hmac("sha256", value.encode(), salt.encode(), 600000).hex()


def migrate():
    with db() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, salt TEXT NOT NULL, password_hash TEXT NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS account (id TEXT PRIMARY KEY, state JSONB NOT NULL)"
        )
        c.execute(
            "INSERT INTO account VALUES ('demo-paper',%s) ON CONFLICT DO NOTHING",
            (Jsonb({**initial_state(), "source_paused": False, "source_revision": 0}),),
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS previews (id TEXT PRIMARY KEY, session_hash TEXT NOT NULL, intent JSONB NOT NULL, result JSONB NOT NULL, account_revision INT NOT NULL, source_revision INT NOT NULL, expires_at TIMESTAMPTZ NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, preview_id TEXT UNIQUE NOT NULL REFERENCES previews(id), result JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS ledger (id BIGSERIAL PRIMARY KEY, event_id TEXT NOT NULL, line_no INT NOT NULL, account TEXT NOT NULL, amount NUMERIC(28,8) NOT NULL, created_at TIMESTAMPTZ NOT NULL, UNIQUE(event_id,line_no))"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS audit (id BIGSERIAL PRIMARY KEY, action TEXT NOT NULL, reference TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL)"
        )
        c.execute(
            "INSERT INTO ledger(event_id,line_no,account,amount,created_at) VALUES ('opening-balance',0,'cash',100000,now()),('opening-balance',1,'opening_equity',-100000,now()) ON CONFLICT DO NOTHING"
        )
        c.execute("DELETE FROM sessions WHERE expires_at < now()")
        c.execute(
            "INSERT INTO audit(action,reference,created_at) VALUES('STARTUP_RECONCILIATION','demo-paper',now())"
        )
        # Persisted quantities/cash must reconcile before serving any order.
        state = c.execute("SELECT state FROM account WHERE id='demo-paper'").fetchone()[
            0
        ]
        cash = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM ledger WHERE account='cash'"
        ).fetchone()[0]
        balance = c.execute("SELECT COALESCE(SUM(amount),0) FROM ledger").fetchone()[0]
        if cash != D(state["cash"]) or balance != 0:
            raise RuntimeError("INCOMPLETE_LEDGER")
        for instrument_id, pos in state["positions"].items():
            cost = c.execute(
                "SELECT COALESCE(SUM(amount),0) FROM ledger WHERE account=%s",
                ("inventory:" + instrument_id,),
            ).fetchone()[0]
            if cost != D(pos["cost"]):
                raise RuntimeError("INCOMPLETE_LEDGER")
            fills = c.execute(
                "SELECT result FROM orders WHERE result->'intent'->>'instrument_id'=%s",
                (instrument_id,),
            ).fetchall()
            quantity = sum(
                (
                    D(r[0]["fill_quantity"])
                    * (1 if r[0]["intent"]["side"] == "BUY" else -1)
                    for r in fills
                ),
                D("0"),
            )
            if quantity != D(pos["quantity"]):
                raise RuntimeError("INCOMPLETE_POSITION")


@asynccontextmanager
async def lifespan(app):
    migrate()
    yield


app = FastAPI(
    title="Modern Trade Terminal",
    version="0.2.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.middleware("http")
async def boundary(request: Request, call_next):
    from fastapi.responses import JSONResponse

    if request.url.path != "/health":
        if request.headers.get("host") not in HOSTS:
            return JSONResponse({"detail": "HOST_DENIED"}, status_code=403)
        if (
            request.method not in {"GET", "HEAD", "OPTIONS"}
            and request.headers.get("origin") not in ORIGINS
        ):
            return JSONResponse({"detail": "ORIGIN_DENIED"}, status_code=403)
    if request.url.path not in {"/health", "/session", "/session/setup"}:
        from starlette.concurrency import run_in_threadpool

        try:
            await run_in_threadpool(session, request)
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def session(request):
    token = request.cookies.get("mtt_session", "")
    with db() as c:
        row = c.execute(
            "SELECT csrf FROM sessions WHERE token_hash=%s AND expires_at>now()",
            (digest(token),),
        ).fetchone()
    if not row:
        raise HTTPException(401, "SESSION_REQUIRED")
    if request.method not in {"GET", "HEAD"} and not hmac.compare_digest(
        request.headers.get("x-csrf-token", ""), row[0]
    ):
        raise HTTPException(403, "CSRF_DENIED")
    return digest(token), row[0]


def get_state(c, lock=False, share=False):
    return c.execute(
        "SELECT state FROM account WHERE id='demo-paper'"
        + (" FOR UPDATE" if lock else " FOR SHARE" if share else "")
    ).fetchone()[0]


def save_state(c, state):
    c.execute("UPDATE account SET state=%s WHERE id='demo-paper'", (Jsonb(state),))


def quotes(state):
    return {
        key: fixture_quote(key, state["source_paused"], state["source_revision"])
        for key in INSTRUMENTS
    }


def audit(c, action, reference):
    c.execute(
        "INSERT INTO audit(action,reference,created_at) VALUES(%s,%s,now())",
        (action, reference),
    )


class Password(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=12, max_length=128)


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preview_id: str = Field(pattern=r"^[0-9a-f-]{36}$")


class Pause(BaseModel):
    paused: bool


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reserve: DecimalString
    monthly_in: DecimalString
    monthly_out: DecimalString


@app.get("/health")
def health():
    with db() as c:
        c.execute("SELECT 1")
    return {"status": "ok", "mode": "PAPER", "privacy": "LOCAL_ONLY"}


@app.get("/session")
def get_session(request: Request):
    with db() as c:
        setup = c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    try:
        _, csrf = session(request)
    except HTTPException:
        return {"authenticated": False, "setup_required": setup}
    return {"authenticated": True, "setup_required": False, "csrf": csrf}


@app.post("/session/setup")
def setup(body: Password):
    with db() as c:
        c.execute("SELECT pg_advisory_xact_lock(10001)")
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            raise HTTPException(409, "ALREADY_CONFIGURED")
        salt = secrets.token_hex(16)
        c.execute(
            "INSERT INTO users VALUES(1,%s,%s)",
            (salt, password_hash(body.password, salt)),
        )
        audit(c, "LOCAL_ACCOUNT_CREATED", "owner")
    return {"configured": True}


@app.post("/session")
def login(body: Password, request: Request, response: Response):
    address = request.client.host if request.client else "local"
    t = time.monotonic()
    attempts = [at for at in LOGIN_ATTEMPTS.get(address, []) if t - at < 60]
    if len(attempts) >= 5:
        raise HTTPException(429, "TRY_AGAIN_IN_60_SECONDS")
    with db() as c:
        row = c.execute("SELECT salt,password_hash FROM users WHERE id=1").fetchone()
        if not row or not hmac.compare_digest(
            password_hash(body.password, row[0]), row[1]
        ):
            LOGIN_ATTEMPTS[address] = attempts + [t]
            raise HTTPException(401, "Wachtwoord klopt niet.")
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        c.execute(
            "INSERT INTO sessions VALUES(%s,%s,%s)",
            (
                digest(token),
                csrf,
                datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS),
            ),
        )
        audit(c, "LOGIN", "owner")
    LOGIN_ATTEMPTS.pop(address, None)
    response.set_cookie(
        "mtt_session",
        token,
        httponly=True,
        samesite="strict",
        max_age=SESSION_SECONDS,
        path="/",
    )
    return {"authenticated": True, "csrf": csrf}


@app.post("/logout")
def logout(request: Request, response: Response):
    token, _ = session(request)
    with db() as c:
        c.execute("DELETE FROM sessions WHERE token_hash=%s", (token,))
    response.delete_cookie("mtt_session", path="/")
    return {"authenticated": False}


@app.get("/bootstrap")
def bootstrap(request: Request):
    session(request)
    with db() as c:
        state = get_state(c, share=True)
        orders = [
            row[0]
            for row in c.execute(
                "SELECT result FROM orders ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        ]
    return {
        "mode": "PAPER",
        "privacy": "LOCAL_ONLY",
        "instruments": list(INSTRUMENTS.values()),
        "quotes": {key: q.model_dump() for key, q in quotes(state).items()},
        "portfolio": portfolio(state, quotes(state)),
        "orders": orders,
        "plan": {key: state[key] for key in ["reserve", "monthly_in", "monthly_out"]},
        "source_paused": state["source_paused"],
        "source_revision": state["source_revision"],
    }


@app.get("/instruments")
def instruments(request: Request):
    session(request)
    return list(INSTRUMENTS.values())


@app.get("/history")
def get_history(request: Request, instrument_id: str, interval: str = "1u"):
    session(request)
    if instrument_id not in INSTRUMENTS:
        raise HTTPException(404, "UNKNOWN_INSTRUMENT")
    try:
        return history(instrument_id, interval)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/trades")
def get_trades(request: Request, instrument_id: str):
    session(request)
    if instrument_id not in INSTRUMENTS:
        raise HTTPException(404, "UNKNOWN_INSTRUMENT")
    return fixture_trades(instrument_id)


@app.post("/orders/preview")
def preview(intent: OrderIntent, request: Request):
    token, _ = session(request)
    if intent.instrument_id not in INSTRUMENTS:
        raise HTTPException(422, "UNSUPPORTED_INSTRUMENT")
    with db() as c:
        state = get_state(c, True)
        q = quotes(state)[intent.instrument_id]
        try:
            result = calculate(intent, q, state, INSTRUMENTS[intent.instrument_id])
        except PolicyError as e:
            raise HTTPException(422, str(e))
        public = {
            k: v for k, v in result.items() if k not in {"state_after", "postings"}
        }
        preview_id = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(seconds=60)
        public.update(
            {
                "preview_id": preview_id,
                "intent": intent.model_dump(),
                "quote": q.model_dump(),
                "expires_at": expires.isoformat(),
                "account_revision": state["revision"],
                "calculation_version": "paper-ioc-v1",
                "tax_status": "NOT_CALCULATED",
            }
        )
        c.execute(
            "INSERT INTO previews VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (
                preview_id,
                token,
                Jsonb(intent.model_dump()),
                Jsonb(public),
                state["revision"],
                state["source_revision"],
                expires,
            ),
        )
        audit(c, "PREVIEW_CREATED", preview_id)
    return public


@app.post("/orders/paper")
def submit(body: Confirmation, request: Request):
    token, _ = session(request)
    with db() as c:
        state = get_state(c, True)
        saved = c.execute(
            "SELECT session_hash,intent,result,account_revision,source_revision,expires_at FROM previews WHERE id=%s",
            (body.preview_id,),
        ).fetchone()
        if not saved or saved[0] != token:
            raise HTTPException(404, "PREVIEW_NOT_FOUND")
        existing = c.execute(
            "SELECT result FROM orders WHERE preview_id=%s", (body.preview_id,)
        ).fetchone()
        if existing:
            return existing[0]
        if saved[5] <= datetime.now(timezone.utc):
            raise HTTPException(409, "PREVIEW_EXPIRED: bereken opnieuw.")
        if state["revision"] != saved[3] or state["source_revision"] != saved[4]:
            raise HTTPException(
                409, "PREVIEW_CHANGED: rekening of bron gewijzigd; bereken opnieuw."
            )
        intent = OrderIntent.model_validate(saved[1])
        q = quotes(state)[intent.instrument_id]
        try:
            result = calculate(intent, q, state, INSTRUMENTS[intent.instrument_id])
        except PolicyError as e:
            raise HTTPException(422, str(e))
        for key in ["fill_quantity", "fill_price", "cash_after", "fee"]:
            if saved[2][key] != result[key]:
                raise HTTPException(409, "PREVIEW_CHANGED")
        order_id = "P-" + uuid.uuid4().hex[:12].upper()
        created = now()
        after = result.pop("state_after")
        lines = result.pop("postings")
        after["revision"] += 1
        result.update(
            {
                "order_id": order_id,
                "preview_id": body.preview_id,
                "intent": intent.model_dump(),
                "created_at": created,
                "quote_source_event_id": q.source_event_id,
                "quality": "SIMULATED",
            }
        )
        result["portfolio_after"] = portfolio(after, quotes(after))
        for line_no, (account, amount) in enumerate(lines):
            JournalLine(
                event_id=order_id, account=account, amount=amount, created_at=created
            )
            c.execute(
                "INSERT INTO ledger(event_id,line_no,account,amount,created_at) VALUES(%s,%s,%s,%s,%s)",
                (order_id, line_no, account, amount, created),
            )
        save_state(c, after)
        c.execute(
            "INSERT INTO orders VALUES(%s,%s,%s,%s)",
            (order_id, body.preview_id, Jsonb(result), created),
        )
        audit(c, "PAPER_ORDER_COMMITTED", order_id)
    return result


@app.get("/ledger")
def ledger(request: Request, offset: int = 0, limit: int = 100):
    session(request)
    if offset < 0 or not 1 <= limit <= 200:
        raise HTTPException(422, "INVALID_PAGE")
    with db() as c:
        state = get_state(c, share=True)
        rows = c.execute(
            "SELECT event_id,account,amount,created_at FROM ledger ORDER BY id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        ).fetchall()
        count = c.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        balance = c.execute("SELECT SUM(amount) FROM ledger").fetchone()[0]
    return {
        "lines": [
            JournalLine(
                event_id=r[0],
                account=r[1],
                amount=str(r[2]),
                created_at=r[3].isoformat(),
            ).model_dump()
            for r in rows
        ],
        "count": count,
        "revision": state["revision"],
        "offset": offset,
        "balanced": balance == 0,
    }


@app.get("/wealth")
def wealth(request: Request):
    session(request)
    with db() as c:
        state = get_state(c, share=True)
        changes = c.execute(
            "SELECT result FROM orders ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return {
        **portfolio(state, quotes(state)),
        "cash_path": cash_path(state),
        "history": [{"label": "Start oefening", "value": "100000.00"}]
        + [
            {"label": r[0]["order_id"], "value": r[0]["portfolio_after"]["total"]}
            for r in reversed(changes)
        ],
        "assumptions": {k: state[k] for k in ["monthly_in", "monthly_out", "reserve"]},
    }


@app.post("/planning")
def update_plan(body: Plan, request: Request):
    session(request)
    values = {k: D(v) for k, v in body.model_dump().items()}
    if any(
        v < 0 or v > 10000000 or v.as_tuple().exponent < -2 for v in values.values()
    ):
        raise HTTPException(422, "INVALID_PLAN_AMOUNT")
    with db() as c:
        state = get_state(c, True)
        if values["reserve"] > D(state["cash"]):
            raise HTTPException(422, "Reserve overschrijdt beschikbare oefencash.")
        state.update({k: str(v.quantize(D(".01"))) for k, v in values.items()})
        state["revision"] += 1
        save_state(c, state)
        audit(c, "PAPER_PLAN_UPDATED", "demo-paper")
    return {"saved": True, "revision": state["revision"]}


@app.get("/sources")
def sources(request: Request):
    session(request)
    with db() as c:
        state = get_state(c, share=True)
    return {
        "sources": [
            {
                "id": "demo-fixture",
                "name": "Lokale simulatie",
                "capabilities": ["quotes", "history", "trades", "paper"],
                "status": "PAUSED" if state["source_paused"] else "ACTIVE_SIMULATED",
                "verification": "TESTED_WITH_FIXTURES",
                "origin_feed": "mtt-synthetic-v1",
                "coverage": "3 synthetische EUR-spotparen",
                "license": "OWN_SYNTHETIC",
                "last_message": "2026-09-24T12:00:00Z",
                "latency": "Niet van toepassing: lokale fixture",
                "ai_processing": "Geen modelcalls",
                "mapping": list(INSTRUMENTS.values()),
            },
            {
                "id": "kraken",
                "name": "Kraken Spot v2",
                "capabilities": ["ticker contract", "trade contract"],
                "status": "NOT_CONNECTED",
                "verification": "NOT_RUN_EXTERNAL_NETWORK",
                "origin_feed": "Kraken Spot WebSocket v2",
                "coverage": "BTC/EUR, ETH/EUR, SOL/EUR mapping; extern bereik niet bewezen",
                "license": "UNKNOWN: gebruiksrechten vóór activering controleren",
                "last_message": None,
                "latency": "Niet gemeten",
                "credentials": "Publieke feed vereist geen key; provider-aansluiting door eigenaar",
                "ai_processing": "Niet toegestaan zonder bronbeleid",
            },
            {
                "id": "codex",
                "name": "Codex",
                "capabilities": ["onderzoek", "uitleg"],
                "status": "LOCAL_ONLY",
                "verification": "NOT_RUN_MISSING_CREDENTIALS",
                "origin_feed": "Niet aangesloten",
                "license": "Account en runtime-autorisatie nodig",
                "coverage": "Contractgrens; runtime M4",
                "last_message": None,
            },
            {
                "id": "jev",
                "name": "Jev / TypeSafe",
                "capabilities": ["begrensde beoordeling", "ABSTAIN"],
                "status": "LOCAL_ONLY",
                "verification": "NOT_RUN_MISSING_CREDENTIALS",
                "origin_feed": "Niet aangesloten",
                "license": "API-toegang en cloudbeleid nodig",
                "coverage": "Contractgrens; runtime M4",
                "last_message": None,
            },
        ]
    }


@app.post("/sources/demo-fixture/pause")
def pause(body: Pause, request: Request):
    session(request)
    with db() as c:
        state = get_state(c, True)
        state["source_paused"] = body.paused
        state["source_revision"] += 1
        save_state(c, state)
        audit(c, "SOURCE_PAUSED" if body.paused else "SOURCE_RESUMED", "demo-fixture")
    return {"paused": body.paused}


@app.post("/sources/{source_id}/test")
def diagnose(source_id: str, request: Request):
    session(request)
    if source_id == "demo-fixture":
        for key in INSTRUMENTS:
            fixture_quote(key)
        return {
            "status": "PASS",
            "verification": "TESTED_WITH_FIXTURES",
            "message": "Drie lokale quotecontracten gevalideerd. Geen externe verbinding uitgevoerd.",
        }
    if source_id == "kraken":
        raw = '{"channel":"ticker","data":[{"symbol":"BTC/EUR","bid":62430.25,"ask":62448.20,"last":62439.00}]}'
        KrakenPublicProvider.normalize_ticker(raw)
        return {
            "status": "PASS",
            "verification": "TESTED_WITH_FIXTURES",
            "message": "Kraken-parser getest met synthetisch bericht. Live verificatie: NOT_RUN_EXTERNAL_NETWORK.",
        }
    if source_id in {"codex", "jev"}:
        return assess_public_text("", source_id)
    raise HTTPException(404, "UNKNOWN_SOURCE")


@app.get("/ai/status")
def ai_status(request: Request):
    session(request)
    return assess_public_text("")


@app.get("/tax/status")
def tax_status(request: Request):
    session(request)
    return {
        "status": "UNAPPROVED_RULESET",
        "result": None,
        "reason": "Geen fiscale calculator in M1. Paperdata is geen fiscaal feit.",
    }


@app.get("/audit")
def get_audit(request: Request):
    session(request)
    with db() as c:
        rows = c.execute(
            "SELECT action,reference,created_at FROM audit ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return [
        {"action": r[0], "reference": r[1], "created_at": r[2].isoformat()}
        for r in rows
    ]
