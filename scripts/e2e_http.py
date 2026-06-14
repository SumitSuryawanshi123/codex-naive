"""HTTP E2E timing and report check."""
from __future__ import annotations

import json
import time
from pathlib import Path

from httpx import ASGITransport, Client

from app.main import app


def main() -> None:
    transport = ASGITransport(app=app)
    with Client(transport=transport, base_url="http://test") as client:
        fixture = json.loads((Path("eval/incidents/timeout_stripe.json")).read_text(encoding="utf-8"))

        t0 = time.perf_counter()
        inv = client.post("/investigations", json={"summary": fixture["summary"], "budget": 4}).json()
        t1 = time.perf_counter()

        client.post(
            f"/investigations/{inv['id']}/evidence",
            json={"type": "log", "raw_text": fixture["input"], "source_meta": {"source": "e2e"}},
        )
        t2 = time.perf_counter()

        status = client.post(f"/investigations/{inv['id']}/step").json()
        t3 = time.perf_counter()

        report = client.get(f"/investigations/{inv['id']}/report").json()
        t4 = time.perf_counter()

    print("=== HTTP E2E TIMING (ms) ===")
    print(f"  create: {(t1 - t0) * 1000:.1f}")
    print(f"  add evidence: {(t2 - t1) * 1000:.1f}")
    print(f"  step: {(t3 - t2) * 1000:.1f}")
    print(f"  report: {(t4 - t3) * 1000:.1f}")
    print(f"  total: {(t4 - t0) * 1000:.1f}")
    print("=== INVESTIGATION STATUS ===", status["status"], "steps=", status["step_count"])
    print("=== RANKED CAUSES ===")
    for cause in report["ranked_causes"][:3]:
        print(
            f"  {cause['category']}: score={cause['evidence_score']} "
            f"signals={len(cause['signals'])} breakdown={cause['breakdown']}"
        )
    print("=== EVIDENCE REQUESTS ===", len(report["evidence_requests"]))


if __name__ == "__main__":
    main()
