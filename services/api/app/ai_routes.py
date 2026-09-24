"""The API selects evidence and binds a public-only consent preview before any cloud call."""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import os
import json
import hashlib
import uuid
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import Field
from .accounting_routes import Strict
from typing import Literal
from .storage import document, save
from .research import fixture_news


class AnalysisPreview(Strict):
    provider: Literal["CODEX", "JEV"]
    prompt: str = Field(min_length=1, max_length=4000)
    source_ids: list[str] = Field(min_length=1, max_length=8)
    task: Literal["news_kind", "source_support", "relevance"] = "news_kind"
    conversation_id: str = Field(pattern=r"^[0-9a-f-]{36}$")


class AnalysisConfirm(Strict):
    preview_id: str
    public_confirmed: bool


class LocalExplanation(Strict):
    topic: Literal["fees", "ownership", "tax", "pension", "source_quality"]


EXPLANATIONS = {
    "fees": "Een aankoop zet cash om in een positie. Kosten worden apart geboekt. De paperpreview rekent met de ask bij koop en de bid bij verkoop; gedeeltelijke uitvoering laat het restant vervallen.",
    "ownership": "De administratie volgt juridische eigenaren en eigendomspercentages. Onderliggende BV-bezittingen en hetzelfde aandelenbelang worden niet beide meegeteld. Leningen tussen entiteiten blijven per eigenaar een vordering of schuld.",
    "tax": "Belastingbedragen komen uitsluitend uit deterministische code. Een versie heeft een jaar, toepassingsgrenzen, officiële bronnen en menselijke review. Een concept is geen aangifte. Ontbrekende input blokkeert een definitief deelresultaat.",
    "pension": "Jaarruimte 2025 gebruikt inkomen en pensioenopbouw uit 2024. Het juiste pensioenregime bepaalt de aftrek voor opbouw. Reserveringsruimte vergt bewijs over de tien voorafgaande jaren. Pensioenkapitaal is geen vrij beschikbaar geld.",
    "source_quality": "Synthetische koersen zijn fixtures. Vertraging, venue, valuta, sessie en herkomst bepalen of koersen vergelijkbaar zijn. Twee uitgevers met dezelfde onderliggende feed vormen geen onafhankelijke bevestiging.",
}


def router(db, session, audit):
    r = APIRouter()

    def local(c, lock=False):
        return document(
            c, "assistant", lambda: {"previews": {}, "conversations": {}}, lock
        )

    def bridge():
        return os.getenv("AI_BRIDGE_URL", "")

    def headers():
        path = Path("/run/secrets/assistant_token")
        if not path.exists():
            raise HTTPException(503, "ASSISTANT_TOKEN_NOT_CONFIGURED")
        return {"Authorization": "Bearer " + path.read_text().strip()}

    @r.get("/ai/research/status")
    def status(request: Request):
        session(request)
        if not bridge():
            return {
                "privacy": "LOCAL_ONLY",
                "enabled": False,
                "verification": "NOT_RUN_MISSING_CREDENTIALS",
                "codex_protocol": "0.141.0",
                "public_sources": fixture_news(),
                "tools": [
                    "market_get_snapshot",
                    "research_get_sources",
                    "calculation_get_result",
                ],
                "personal_uploads": False,
            }
        try:
            response = httpx.get(
                bridge() + "/status", headers=headers(), timeout=3, trust_env=False
            )
            response.raise_for_status()
            result = response.json()
        except Exception:
            result = {"enabled": False, "verification": "BRIDGE_UNAVAILABLE"}
        return {**result, "public_sources": fixture_news(), "personal_uploads": False}

    @r.get("/ai/evaluation")
    def evaluation(request: Request):
        session(request)
        return json.loads((Path(__file__).parent / "ai_evaluation.json").read_text())

    @r.post("/ai/local-explanation")
    def explain(body: LocalExplanation, request: Request):
        session(request)
        return {
            "kind": "DETERMINISTIC_HELP_NOT_AI",
            "topic": body.topic,
            "text": EXPLANATIONS[body.topic],
            "cloud_call": False,
        }

    @r.post("/ai/research/preview")
    def preview(body: AnalysisPreview, request: Request):
        token, _ = session(request)
        available = {n["id"]: n for n in fixture_news()}
        if len(set(body.source_ids)) != len(body.source_ids) or any(
            i not in available for i in body.source_ids
        ):
            raise HTTPException(422, "ONLY_APPROVED_PUBLIC_OR_SYNTHETIC_SOURCES")
        sources = [available[i] for i in body.source_ids]
        context = {
            "scope": "PUBLIC_OR_SYNTHETIC",
            "sources": sources,
            "market": [],
            "calculations": [],
        }
        payload = {**body.model_dump(), "privacy": "PUBLIC_DATA_AI", "context": context}
        payload.pop("source_ids")
        pid = str(uuid.uuid4())
        expires = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        with db() as c:
            st = local(c, True)
            st["previews"] = {
                k: v
                for k, v in st["previews"].items()
                if v["expires_at"] > datetime.now(timezone.utc).isoformat()
            }
            st["previews"][pid] = {
                "payload": payload,
                "session": token,
                "expires_at": expires,
                "input_hash": digest,
                "used": False,
            }
            save(c, "assistant", st)
            audit(c, "AI_PUBLIC_PREVIEW", pid)
        return {
            "preview_id": pid,
            "payload": payload,
            "input_hash": digest,
            "expires_at": expires,
            "destination": "OpenAI Codex"
            if body.provider == "CODEX"
            else "TypeSafe Jev",
            "privacy": "PUBLIC_DATA_AI",
            "warning": "Alleen deze vraag en geselecteerde broninhoud worden verstuurd. Neem geen privégegevens op in je vraag. Er worden geen documenten, bankgegevens of financiële dossiers toegevoegd.",
            "connection_configured": bool(bridge()),
        }

    @r.post("/ai/research/stream")
    def stream(body: AnalysisConfirm, request: Request):
        token, _ = session(request)
        if not body.public_confirmed:
            raise HTTPException(422, "PUBLIC_DATA_CONFIRMATION_REQUIRED")
        with db() as c:
            st = local(c, True)
            item = st["previews"].get(body.preview_id)
            if not item or item["session"] != token:
                raise HTTPException(404, "PREVIEW_NOT_FOUND")
            if (
                item["used"]
                or item["expires_at"] <= datetime.now(timezone.utc).isoformat()
            ):
                raise HTTPException(409, "PREVIEW_USED_OR_EXPIRED")
            payload = {**item["payload"], "public_confirmed": True}
            item["used"] = True
            save(c, "assistant", st)
            audit(c, "AI_PREVIEW_CONFIRMED", body.preview_id)

        def emit():
            final = None
            if not bridge():
                final = {
                    "schema_version": 1,
                    "disposition": "ABSTAIN",
                    "reason": "NOT_RUN_MISSING_CREDENTIALS",
                    "cloud_call": False,
                    "execution_authorized": False,
                }
                yield json.dumps({"type": "result", "result": final}) + "\n"
            else:
                try:
                    with httpx.Client(
                        timeout=httpx.Timeout(70, connect=3), trust_env=False
                    ) as client:
                        with client.stream(
                            "POST",
                            bridge() + "/analyze",
                            json=payload,
                            headers=headers(),
                        ) as response:
                            if response.status_code != 200:
                                raise ValueError("BRIDGE_REJECTED")
                            size = 0
                            if "ndjson" not in response.headers.get("content-type", ""):
                                response.read()
                                final = response.json()
                                yield (
                                    json.dumps({"type": "result", "result": final})
                                    + "\n"
                                )
                            else:
                                for line in response.iter_lines():
                                    size += len(line)
                                    if size > 300000:
                                        raise ValueError("STREAM_LIMIT")
                                    event = json.loads(line)
                                    if event.get("type") not in {
                                        "started",
                                        "delta",
                                        "tool",
                                        "result",
                                    }:
                                        raise ValueError("UNKNOWN_STREAM_EVENT")
                                    if event["type"] == "result":
                                        final = event["result"]
                                    yield json.dumps(event) + "\n"
                except (httpx.HTTPError, ValueError):
                    final = {
                        "disposition": "ABSTAIN",
                        "reason": "BRIDGE_TIMEOUT_OR_INVALID_RESPONSE",
                        "execution_authorized": False,
                    }
                    yield json.dumps({"type": "result", "result": final}) + "\n"
            if final is not None:
                with db() as c:
                    st = local(c, True)
                    cid = payload["conversation_id"]
                    turns = st["conversations"].setdefault(cid, [])
                    turns.append(
                        {
                            "prompt": payload["prompt"],
                            "provider": payload["provider"],
                            "source_ids": [
                                s["id"] for s in payload["context"]["sources"]
                            ],
                            "input_hash": item["input_hash"],
                            "result": final,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    st["conversations"][cid] = turns[-30:]
                    save(c, "assistant", st)
                    audit(c, "AI_RESULT_RECORDED", body.preview_id)

        return StreamingResponse(
            emit(),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"},
        )

    @r.get("/ai/research/conversations")
    def conversations(request: Request):
        session(request)
        with db() as c:
            st = local(c)
        return {
            "conversations": [
                {"id": cid, "turns": turns}
                for cid, turns in st["conversations"].items()
            ]
        }

    return r
