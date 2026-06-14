from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingestion.fingerprint import fingerprint
from app.ingestion.redaction import redact
from app.ingestion.stack_traces import looks_like_stack_trace, parse_stack_frames

TIMESTAMP_RE = re.compile(r"^\s*(?:\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}|\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})")
LEVEL_RE = re.compile(r"\b(ERROR|ERR|WARN|WARNING|FATAL|CRITICAL|INFO|DEBUG)\b", re.I)


@dataclass
class EvidenceCandidate:
    type: str
    span_start: int
    span_end: int
    normalized_text: str
    signal_tags: list[str] = field(default_factory=list)
    fingerprint: str = ""


def stitch_records(text: str) -> list[tuple[int, int, str]]:
    lines = text.splitlines(keepends=True)
    records: list[tuple[int, int, str]] = []
    current: list[str] = []
    start = 0
    offset = 0
    for line in lines:
        is_new = bool(TIMESTAMP_RE.match(line)) or (LEVEL_RE.search(line) and not line.startswith((" ", "\t")))
        if current and is_new and not looks_like_stack_trace(line):
            body = "".join(current)
            records.append((start, start + len(body), body.strip()))
            current = []
            start = offset
        if not current:
            start = offset
        current.append(line)
        offset += len(line)
    if current:
        body = "".join(current)
        records.append((start, start + len(body), body.strip()))
    return [(s, e, b) for s, e, b in records if b]


def tags_for(text: str) -> list[str]:
    lowered = text.lower()
    tags: set[str] = set()
    if any(term in lowered for term in ["exception", "traceback", "stack trace", "nullpointer", "keyerror"]):
        tags.add("exception")
    if any(term in lowered for term in ["timeout", "timed out", "deadline exceeded"]):
        tags.add("timeout")
    if any(term in lowered for term in ["connection refused", "econnrefused", "dns", "network unreachable"]):
        tags.add("network")
    if any(term in lowered for term in ["401", "403", "unauthorized", "forbidden", "permission denied"]):
        tags.add("security")
    if any(term in lowered for term in ["missing env", "config", "feature flag", "invalid setting"]):
        tags.add("configuration")
    if any(term in lowered for term in ["migration", "schema", "duplicate key", "foreign key", "constraint"]):
        tags.add("data")
    if any(term in lowered for term in ["redis", "s3", "stripe", "sendgrid", "postgres", "mysql", "kafka"]):
        tags.add("dependency")
    if any(term in lowered for term in ["business rule", "validation failed", "invariant"]):
        tags.add("business_logic")
    if any(term in lowered for term in ["oom", "out of memory", "disk full", "cpu", "kubernetes", "pod"]):
        tags.add("infrastructure")
    if LEVEL_RE.search(text):
        tags.add(LEVEL_RE.search(text).group(1).lower())
    return sorted(tags or {"log"})


def normalize_record(span_start: int, span_end: int, text: str) -> EvidenceCandidate:
    frames = parse_stack_frames(text)
    kind = "stack_trace" if frames or "traceback" in text.lower() else "log"
    normalized = re.sub(r"\s+", " ", text).strip()
    if frames:
        frame_bits = ", ".join(f"{f['file']}:{f['line']}:{f['symbol']}" for f in frames[:5])
        normalized = f"{normalized} | frames={frame_bits}"
    tags = tags_for(text)
    if frames:
        tags.append("stack_frame")
    return EvidenceCandidate(
        type=kind,
        span_start=span_start,
        span_end=span_end,
        normalized_text=normalized,
        signal_tags=sorted(set(tags)),
        fingerprint=fingerprint(normalized),
    )


def ingest_text(text: str) -> tuple[str, dict[str, str], list[EvidenceCandidate]]:
    redacted, redaction_map = redact(text)
    candidates = [normalize_record(s, e, body) for s, e, body in stitch_records(redacted)]
    return redacted, redaction_map, candidates
