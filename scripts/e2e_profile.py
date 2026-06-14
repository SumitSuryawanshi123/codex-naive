"""Profile E2E flow timing and classification failures."""
from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.ingestion.logs import ingest_text
from app.main import app
from app.orchestrator import create_investigation, step_investigation
from app.report import investigation_report
from app.evidence.store import append_artifact


def profile_fixture(name: str) -> dict:
    path = Path("eval/incidents") / name
    data = json.loads(path.read_text(encoding="utf-8"))
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    timings: dict[str, float] = {}
    with Session() as db:
        t0 = time.perf_counter()
        _, _, candidates = ingest_text(data["input"])
        timings["ingest_ms"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        inv = create_investigation(db, budget=3, summary=data["summary"])
        timings["create_ms"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        append_artifact(db, inv.id, "log", data["input"], {"fixture": name})
        timings["store_ms"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        step_investigation(db, inv.id)
        timings["step_ms"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        report = investigation_report(db, inv.id)
        timings["report_ms"] = (time.perf_counter() - t0) * 1000

    top = report["ranked_causes"][0] if report["ranked_causes"] else {}
    all_causes = [(c["category"], c["evidence_score"]) for c in report["ranked_causes"][:5]]
    return {
        "fixture": name,
        "expected": data["expected_category"],
        "got": top.get("category"),
        "top_score": top.get("evidence_score"),
        "margin": (report["ranked_causes"][0]["evidence_score"] - report["ranked_causes"][1]["evidence_score"])
        if len(report["ranked_causes"]) > 1
        else top.get("evidence_score", 0),
        "ranking": all_causes,
        "tags": sorted({t for c in candidates for t in c.signal_tags}),
        "status": report["investigation"]["status"],
        **timings,
    }


def profile_large_log(lines: int = 5000) -> dict:
    body = "\n".join(
        f"2026-06-14T08:{i % 60:02d}:{i % 60:02d}Z INFO request handled id={i}" for i in range(lines)
    )
    body += "\n2026-06-14T08:59:59Z ERROR NullPointerException at UserService.java:82\n"
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        t0 = time.perf_counter()
        append_artifact(db, 1, "log", body, {}) if False else None
        inv = create_investigation(db)
        t1 = time.perf_counter()
        append_artifact(db, inv.id, "log", body, {})
        t2 = time.perf_counter()
        step_investigation(db, inv.id)
        t3 = time.perf_counter()
    return {
        "lines": lines,
        "chars": len(body),
        "create_ms": (t1 - t0) * 1000,
        "ingest_store_ms": (t2 - t1) * 1000,
        "step_ms": (t3 - t2) * 1000,
    }


def http_profile() -> dict:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        fixture = json.loads(Path("eval/incidents/timeout_stripe.json").read_text(encoding="utf-8"))
        times = {}
        t0 = time.perf_counter()
        inv = client.post("/investigations", json={"summary": fixture["summary"], "budget": 4}).json()
        times["create"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        client.post(f"/investigations/{inv['id']}/evidence", json={"type": "log", "raw_text": fixture["input"], "source_meta": {}})
        times["evidence"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        client.post(f"/investigations/{inv['id']}/step")
        times["step"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        client.get(f"/investigations/{inv['id']}/report")
        times["report"] = (time.perf_counter() - t0) * 1000
        return times
    finally:
        app.dependency_overrides.clear()


def main() -> None:
    print("=== PER-FIXTURE TIMING & RANKING ===")
    for path in sorted(Path("eval/incidents").glob("*.json")):
        r = profile_fixture(path.name)
        ok = "PASS" if r["expected"] == r["got"] else "FAIL"
        print(
            f"{ok} {r['fixture']}: {r['expected']} -> {r['got']} "
            f"score={r['top_score']} margin={r['margin']} status={r['status']}"
        )
        print(f"    ranking={r['ranking']} tags={r['tags']}")
        print(
            f"    ingest={r['ingest_ms']:.1f}ms store={r['store_ms']:.1f}ms "
            f"step={r['step_ms']:.1f}ms report={r['report_ms']:.1f}ms"
        )

    print("\n=== LARGE LOG STRESS ===")
    for n in [500, 2000, 5000]:
        print(n, profile_large_log(n))

    print("\n=== HTTP PROFILE ===")
    print(http_profile())


if __name__ == "__main__":
    main()
