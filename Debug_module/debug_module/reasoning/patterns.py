from __future__ import annotations

import re
from dataclasses import dataclass

from debug_module.ingestion.fingerprint import fingerprint
from debug_module.ingestion.logs import EvidenceCandidate


@dataclass(frozen=True)
class FailurePattern:
    id: str
    category: str
    description: str
    regex: re.Pattern[str]


PATTERNS = [
    FailurePattern(
        id="external_service_timeout",
        category="EXTERNAL_SERVICE",
        description="Named external provider call timed out.",
        regex=re.compile(r"(?i)\b(timeout|timed out|deadline exceeded)\b.*\b(stripe|sendgrid|s3|provider)\b"),
    ),
    FailurePattern(
        id="missing_runtime_config",
        category="CONFIGURATION",
        description="Required runtime configuration is missing or invalid.",
        regex=re.compile(r"(?i)\b(missing env|missing config|invalid config|KeyError: [A-Z0-9_]+)\b"),
    ),
    FailurePattern(
        id="permission_scope_denied",
        category="SECURITY",
        description="Request is denied because a permission or scope is missing.",
        regex=re.compile(r"(?i)\b(403|forbidden|permission denied|missing scope|unauthorized)\b"),
    ),
    FailurePattern(
        id="oom_kill",
        category="INFRASTRUCTURE",
        description="Process or pod was killed by memory pressure.",
        regex=re.compile(r"(?i)\b(OOMKilled|out of memory|memory pressure)\b"),
    ),
]


def pattern_evidence_from_text(text: str) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for pattern in PATTERNS:
        match = pattern.regex.search(text)
        if not match:
            continue
        normalized = f"known_failure_pattern {pattern.id}: {pattern.description}"
        candidates.append(
            EvidenceCandidate(
                type="failure_pattern",
                span_start=match.start(),
                span_end=match.end(),
                normalized_text=normalized,
                signal_tags=["known_pattern", f"pattern_{pattern.category.lower()}"],
                fingerprint=fingerprint(normalized),
            )
        )
    return candidates
