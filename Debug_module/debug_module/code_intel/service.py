from __future__ import annotations

from pathlib import Path

from debug_module.code_intel.blame import git_blame_line
from debug_module.code_intel.resolver import resolve_source_path
from debug_module.code_intel.snippets import source_snippet
from debug_module.ingestion.fingerprint import fingerprint
from debug_module.ingestion.logs import EvidenceCandidate
from debug_module.ingestion.stack_traces import parse_stack_frames


def source_evidence_from_text(text: str, repo_root: Path | None = None) -> list[EvidenceCandidate]:
    root = repo_root or Path.cwd()
    candidates: list[EvidenceCandidate] = []
    seen: set[tuple[str, int]] = set()
    for frame in parse_stack_frames(text):
        frame_file = str(frame["file"])
        line = int(frame["line"])
        key = (frame_file, line)
        if key in seen:
            continue
        seen.add(key)

        path = resolve_source_path(frame_file, root)
        if not path:
            continue
        snippet = source_snippet(path, line)
        if not snippet:
            continue
        blame = git_blame_line(path, line, root)
        relative = path.resolve().relative_to(root.resolve())
        normalized = f"source_context {relative}:{line}\n{snippet}"
        if blame:
            normalized = f"{normalized}\nblame: {blame}"
        candidates.append(
            EvidenceCandidate(
                type="source_snippet",
                span_start=0,
                span_end=0,
                normalized_text=normalized,
                signal_tags=["code_context", "source"],
                fingerprint=fingerprint(normalized),
            )
        )
    return candidates
