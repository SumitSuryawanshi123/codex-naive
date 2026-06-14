"""Temporary E2E diagnostic script."""
from __future__ import annotations

import json
import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.evidence.store import append_artifact
from app.ingestion.logs import ingest_text
from app.orchestrator import create_investigation, step_investigation
from app.report import investigation_report


def main() -> None:
    raw = (
        '2026-06-14T01:00:00Z ERROR token=supersecret123 exception\n'
        '  File "app/main.py", line 12, in handler\n'
    )
    _, _, candidates = ingest_text(raw)
    print("=== INGESTION ===")
    for c in candidates:
        print(f"  type={c.type} tags={c.signal_tags}")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        inv = create_investigation(db, budget=2, summary="checkout failing")
        t0 = time.perf_counter()
        append_artifact(
            db,
            inv.id,
            "log",
            "2026-06-14T08:15:01Z ERROR checkout timeout calling Stripe after 30000ms",
            {"test": True},
        )
        t1 = time.perf_counter()
        step_investigation(db, inv.id)
        t2 = time.perf_counter()
        report = investigation_report(db, inv.id)
        t3 = time.perf_counter()

    print("=== TIMING (ms) ===")
    print(f"  append_artifact: {(t1 - t0) * 1000:.1f}")
    print(f"  step_investigation: {(t2 - t1) * 1000:.1f}")
    print(f"  report: {(t3 - t2) * 1000:.1f}")
    print("=== REPORT (top cause) ===")
    top = report["ranked_causes"][0] if report["ranked_causes"] else {}
    print(json.dumps(top, indent=2))

    print("\n=== FIXTURE TAG ANALYSIS ===")
    for path in sorted((Path("eval/incidents")).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        _, _, cands = ingest_text(data["input"])
        all_tags = sorted({t for c in cands for t in c.signal_tags})
        with Session() as db:
            Base.metadata.create_all(engine)
            inv = create_investigation(db, budget=1, summary=data["summary"])
            append_artifact(db, inv.id, "log", data["input"], {"fixture": path.name})
            step_investigation(db, inv.id)
            rpt = investigation_report(db, inv.id)
        top = rpt["ranked_causes"][0] if rpt["ranked_causes"] else {}
        ok = "PASS" if top.get("category") == data["expected_category"] else "FAIL"
        print(
            f"{ok} {path.name}: expected={data['expected_category']} "
            f"got={top.get('category')} score={top.get('evidence_score')} tags={all_tags}"
        )


if __name__ == "__main__":
    main()
