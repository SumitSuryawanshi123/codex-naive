from __future__ import annotations

import json

from sqlalchemy import select
from pathlib import Path

from sqlalchemy.orm import Session

from debug_module.code_intel import source_evidence_from_text
from debug_module.ingestion.configs import ingest_config_text
from debug_module.ingestion.har import ingest_har_text
from debug_module.ingestion import ingest_text
from debug_module.ingestion.otel import ingest_otel_text
from debug_module.models import Artifact, Evidence
from debug_module.reasoning.patterns import pattern_evidence_from_text


def _candidates_for_artifact(artifact_type: str, text: str):
    if artifact_type == "config":
        return ingest_config_text(text)
    if artifact_type == "har":
        return ingest_har_text(text)
    if artifact_type in {"otel", "otel_trace", "trace"}:
        return ingest_otel_text(text)
    return ingest_text(text)[2]


def append_artifact(
    db: Session,
    investigation_id: int,
    artifact_type: str,
    raw_text: str,
    source_meta: dict,
    repo_root: Path | None = None,
) -> Artifact:
    redacted, redaction_map, candidates = ingest_text(raw_text)
    typed_candidates = _candidates_for_artifact(artifact_type, redacted)
    if typed_candidates:
        candidates = typed_candidates
    artifact = Artifact(
        investigation_id=investigation_id,
        type=artifact_type,
        raw_text=redacted,
        redaction_map=json.dumps(redaction_map),
        source_meta=json.dumps(source_meta),
    )
    db.add(artifact)
    db.flush()

    existing_fingerprints = {
        item[0]
        for item in db.execute(
            select(Evidence.fingerprint).where(Evidence.investigation_id == investigation_id)
        ).all()
    }
    for candidate in [*candidates, *pattern_evidence_from_text(redacted)]:
        if candidate.fingerprint in existing_fingerprints:
            continue
        db.add(
            Evidence(
                investigation_id=investigation_id,
                artifact_id=artifact.id,
                type=candidate.type,
                span_start=candidate.span_start,
                span_end=candidate.span_end,
                normalized_text=candidate.normalized_text,
                signal_tags=json.dumps(candidate.signal_tags),
                fingerprint=candidate.fingerprint,
            )
        )
        existing_fingerprints.add(candidate.fingerprint)

    for candidate in source_evidence_from_text(redacted, repo_root):
        if candidate.fingerprint in existing_fingerprints:
            continue
        source_artifact = Artifact(
            investigation_id=investigation_id,
            type="source",
            raw_text=candidate.normalized_text,
            redaction_map="{}",
            source_meta=json.dumps({"derived_from_artifact_id": artifact.id}),
        )
        db.add(source_artifact)
        db.flush()
        db.add(
            Evidence(
                investigation_id=investigation_id,
                artifact_id=source_artifact.id,
                type=candidate.type,
                span_start=0,
                span_end=len(candidate.normalized_text),
                normalized_text=candidate.normalized_text,
                signal_tags=json.dumps(candidate.signal_tags),
                fingerprint=candidate.fingerprint,
            )
        )
        existing_fingerprints.add(candidate.fingerprint)
    db.commit()
    db.refresh(artifact)
    return artifact
