"""Local reminders. Missed host monitoring is distinct from on-time delivery."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Literal
from pydantic import Field
from fastapi import APIRouter, Request, HTTPException
from .accounting_routes import Strict
from .storage import document, save
import uuid


class Reminder(Strict):
    title: str = Field(min_length=1, max_length=160)
    scheduled_at: str
    timezone: str
    scope: Literal["DEMO", "PERSONAL"]
    kind: Literal[
        "PERSONAL_DEADLINE",
        "EARNINGS",
        "DIVIDEND",
        "SPLIT",
        "MACRO",
        "EXPIRY",
        "SESSION",
        "HALT",
    ] = "PERSONAL_DEADLINE"
    instrument_id: str = Field(default="", max_length=100)
    source: str = Field(min_length=1, max_length=300)


def empty():
    return {"last_tick": None, "monitoring_gaps": [], "reminders": []}


def instant(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    return d.astimezone(timezone.utc)


def tick(state, now):
    previous = instant(state["last_tick"]) if state["last_tick"] else None
    gap = previous is None or (now - previous).total_seconds() > 20
    if gap and previous:
        state["monitoring_gaps"] = (
            state["monitoring_gaps"]
            + [{"from": previous.isoformat(), "to": now.isoformat()}]
        )[-50:]
    for item in state["reminders"]:
        if item["status"] != "PENDING":
            continue
        due = instant(item["scheduled_at"])
        if due <= now:
            missed = (
                gap
                and (previous is None or due > previous)
                or (now - due).total_seconds() > 20
            )
            item.update(
                status="MISSED_MONITORING_WINDOW" if missed else "DUE",
                observed_at=now.isoformat(),
            )
    state["last_tick"] = now.isoformat()
    return state


def router(db, session, audit):
    r = APIRouter()

    @r.get("/calendar/local")
    def get(request: Request, scope: Literal["DEMO", "PERSONAL"] = "DEMO"):
        session(request)
        with db() as c:
            st = document(c, "calendar", empty)
        last = instant(st["last_tick"]) if st["last_tick"] else None
        return {
            **st,
            "reminders": [i for i in st["reminders"] if i["scope"] == scope],
            "monitor": "ACTIVE"
            if last and (datetime.now(timezone.utc) - last).total_seconds() < 20
            else "NOT_MONITORED",
            "delivery": "Local app inbox only; no push, email or calendar writes",
        }

    @r.post("/calendar/local")
    def create(body: Reminder, request: Request):
        session(request)
        try:
            due = instant(body.scheduled_at)
            ZoneInfo(body.timezone)
        except (ValueError, KeyError):
            raise HTTPException(422, "VALID_TIME_AND_TIMEZONE_REQUIRED")
        item = {
            **body.model_dump(),
            "scheduled_at": due.isoformat(),
            "id": str(uuid.uuid4()),
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "quality": "USER_ENTERED" if body.scope == "PERSONAL" else "SIMULATED",
            "revision": 1,
        }
        with db() as c:
            st = document(c, "calendar", empty, True)
            if len(st["reminders"]) >= 1000:
                raise HTTPException(422, "REMINDER_LIMIT")
            st["reminders"].append(item)
            save(c, "calendar", st)
            audit(c, "LOCAL_REMINDER_CREATED", item["id"])
        return item

    @r.post("/calendar/local/{reminder_id}/acknowledge")
    def acknowledge(reminder_id: str, request: Request):
        session(request)
        with db() as c:
            st = document(c, "calendar", empty, True)
            item = next((i for i in st["reminders"] if i["id"] == reminder_id), None)
            if item is None:
                raise HTTPException(404, "REMINDER_NOT_FOUND")
            item.update(
                status="ACKNOWLEDGED",
                acknowledged_at=datetime.now(timezone.utc).isoformat(),
            )
            save(c, "calendar", st)
            audit(c, "LOCAL_REMINDER_ACKNOWLEDGED", reminder_id)
        return {"saved": True}

    return r
