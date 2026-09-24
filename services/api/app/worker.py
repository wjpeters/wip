"""One bounded background analysis worker. It has no order API or AI credentials."""

import time
import signal
import threading
from datetime import datetime, timezone
import httpx
from psycopg.types.json import Jsonb
from .main import db
from . import planning, lab, rules, tax, calendar
from .storage import document, save, migrate_extended

running = True


def stop(*_):
    global running
    running = False


def execute(kind, payload):
    if kind == "SCENARIO":
        return planning.calculate(planning.Scenario.model_validate(payload["scenario"]))
    if kind == "MONTE_CARLO":
        return planning.monte_carlo(
            planning.Scenario.model_validate(payload["scenario"]),
            payload["seed"],
            payload["paths"],
            payload["volatility"],
        )
    if kind == "BACKTEST":
        return lab.backtest(
            lab.BacktestInput.model_validate(
                {k: v for k, v in payload.items() if k != "scope"}
            )
        )
    if kind == "SOURCE_CHECK":
        if payload["rule_hash"] != tax.rule_hash():
            raise ValueError("RULE_VERSION_CHANGED")
        with db() as c:
            previous = document(c, "rules", rules.empty)
        changes = {}
        with httpx.Client(
            timeout=httpx.Timeout(15, connect=5), trust_env=False
        ) as client:
            for source in tax.SOURCES:
                changes[source["id"]] = rules.fetch_source(
                    source, previous["checks"].get(source["id"], {}), client
                )
        with db() as c:
            current = document(c, "rules", rules.empty, True)
            current["checks"].update(changes)
            save(c, "rules", current)
        return {
            "checks": changes,
            "all_fetched": all(v["status"] != "FETCH_FAILED" for v in changes.values()),
        }
    raise ValueError("UNKNOWN_JOB_KIND")


def monitor():
    while running:
        try:
            with db() as c:
                state = document(c, "calendar", calendar.empty, True)
                calendar.tick(state, datetime.now(timezone.utc))
                save(c, "calendar", state)
        except Exception:
            pass  # Persisted heartbeat ages out visibly; never mark a failed tick as successful.
        for _ in range(10):
            if not running:
                return
            time.sleep(0.5)


def run():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with db() as c:
        migrate_extended(c)
        # This compose profile guarantees one worker; interrupted calculations are never published.
        c.execute(
            "UPDATE analysis_jobs SET status='INTERRUPTED',result=%s WHERE status='RUNNING'",
            (Jsonb({"reason": "WORKER_RESTARTED_RETRY_EXPLICITLY"}),),
        )
    threading.Thread(target=monitor, daemon=True).start()
    while running:
        with db() as c:
            row = c.execute(
                "SELECT id,kind,request FROM analysis_jobs WHERE status='QUEUED' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
            ).fetchone()
            if row:
                c.execute(
                    "UPDATE analysis_jobs SET status='RUNNING' WHERE id=%s", (row[0],)
                )
        if not row:
            time.sleep(0.5)
            continue
        jid, kind, payload = row
        try:
            result = execute(kind, payload)
            status = "COMPLETED"
        except Exception as e:
            result = {
                "reason": str(e)[:500]
                if isinstance(e, (ValueError, ArithmeticError))
                else type(e).__name__
            }
            status = "FAILED"
        with db() as c:
            c.execute(
                "UPDATE analysis_jobs SET status=%s,result=%s WHERE id=%s AND status='RUNNING'",
                (status, Jsonb(result), jid),
            )


if __name__ == "__main__":
    run()
