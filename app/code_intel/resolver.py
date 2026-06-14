from __future__ import annotations

from pathlib import Path


def resolve_source_path(frame_file: str, repo_root: Path | None = None) -> Path | None:
    root = (repo_root or Path.cwd()).resolve()
    candidate = Path(frame_file)
    candidates = []
    if candidate.is_absolute():
        candidates.append(candidate)
    candidates.append(root / candidate)
    candidates.extend(root.glob(f"**/{candidate.name}"))

    for path in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not resolved.is_file():
            continue
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        return resolved
    return None
