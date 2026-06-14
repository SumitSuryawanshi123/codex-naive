from __future__ import annotations

import json
from pathlib import Path

from app.database import Base
from app.evidence.store import append_artifact
from app.orchestrator import create_investigation, step_investigation
from app.report import investigation_report
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def run_fixture(path: Path) -> dict:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    data = json.loads(path.read_text(encoding="utf-8"))
    with Session() as db:
        inv = create_investigation(db, budget=3, summary=data["summary"])
        append_artifact(db, inv.id, "log", data["input"], {"fixture": path.name})
        step_investigation(db, inv.id)
        report = investigation_report(db, inv.id)
    top = report["ranked_causes"][0] if report["ranked_causes"] else {}
    return {
        "fixture": path.name,
        "expected_category": data["expected_category"],
        "actual_category": top.get("category"),
        "correct_category": top.get("category") == data["expected_category"],
        "expected_root_cause": data["expected_root_cause"],
        "top_statement": top.get("statement"),
    }


def main() -> None:
    paths = sorted((Path(__file__).parent / "incidents").glob("*.json"))
    results = [run_fixture(path) for path in paths]
    correct = sum(1 for result in results if result["correct_category"])
    for result in results:
        marker = "PASS" if result["correct_category"] else "FAIL"
        print(f"{marker} {result['fixture']}: expected {result['expected_category']}, got {result['actual_category']}")
    print(f"category_accuracy={correct}/{len(results)}")


if __name__ == "__main__":
    main()
