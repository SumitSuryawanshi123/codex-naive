from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.code_intel import source_evidence_from_text
from app.database import Base
from app.evidence.store import append_artifact
from app.models import Evidence
from app.orchestrator import create_investigation


def test_source_evidence_extracts_snippet_for_repo_stack_frame() -> None:
    candidates = source_evidence_from_text('  File "app/config.py", line 8, in <module>\n')

    assert candidates
    assert candidates[0].type == "source_snippet"
    assert "source_context app\\config.py:8" in candidates[0].normalized_text or "source_context app/config.py:8" in candidates[0].normalized_text
    assert "code_context" in candidates[0].signal_tags


def test_append_artifact_adds_source_snippet_evidence_for_resolvable_frame() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        inv = create_investigation(db, budget=2, summary="worker crashes")
        append_artifact(
            db,
            inv.id,
            "log",
            'Traceback (most recent call last):\n  File "app/config.py", line 8, in <module>\n',
            {"test": True},
        )
        evidence = list(db.scalars(select(Evidence).where(Evidence.investigation_id == inv.id)))

    assert any(item.type == "source_snippet" for item in evidence)
