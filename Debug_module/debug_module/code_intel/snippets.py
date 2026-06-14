from __future__ import annotations

from pathlib import Path


def source_snippet(path: Path, line: int, context: int = 3) -> str | None:
    if line < 1:
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if line > len(lines):
        return None

    start = max(1, line - context)
    end = min(len(lines), line + context)
    width = len(str(end))
    return "\n".join(f"{number:>{width}}: {lines[number - 1]}" for number in range(start, end + 1))
