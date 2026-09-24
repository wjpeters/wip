"""Small M1 warm snapshot measurement against QA only; not a streaming load test."""

import json
import platform
import time
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
base = "http://localhost:4187"
with httpx.Client(
    base_url=base, headers={"Origin": base}, timeout=10, trust_env=False
) as client:
    response = client.post(
        "/api/session",
        json={"password": (root / ".secrets/e2e_password").read_text().strip()},
    )
    response.raise_for_status()
    durations = []
    for i in range(110):
        start = time.perf_counter()
        response = client.get("/api/bootstrap")
        response.raise_for_status()
        assert response.json()["mode"] == "PAPER"
        if i >= 10:
            durations.append((time.perf_counter() - start) * 1000)
    durations.sort()
    report = {
        "scope": "M1: 100 serial warm authenticated /bootstrap requests, 10 warmups, 3 fixture instruments; not streaming benchmark",
        "platform": platform.platform(),
        "p50_ms": round(durations[49], 2),
        "p95_ms": round(durations[94], 2),
        "p99_ms": round(durations[98], 2),
        "max_ms": round(durations[-1], 2),
        "target_p95_ms": 100,
        "target_met": durations[94] < 100,
    }
    (root / "docs/evidence/performance.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
