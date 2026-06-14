from __future__ import annotations

import re

FRAME_RE = re.compile(
    r"\"?(?P<file>[A-Za-z]:)?(?P<path>[\w./\\-]+\.(?:py|js|ts|java|go|rb|cs|php))\"?"
    r"(?::|, line )(?P<line>\d+)"
    r"(?:,?\s*(?:in|at)\s*(?P<symbol>[\w.$<>-]+))?"
)


def parse_stack_frames(text: str) -> list[dict[str, str | int]]:
    frames: list[dict[str, str | int]] = []
    for match in FRAME_RE.finditer(text):
        frames.append(
            {
                "file": f"{match.group('file') or ''}{match.group('path')}",
                "line": int(match.group("line")),
                "symbol": match.group("symbol") or "<unknown>",
            }
        )
    return frames


def looks_like_stack_trace(line: str) -> bool:
    lowered = line.lower()
    return (
        "traceback" in lowered
        or line.lstrip().startswith(("at ", "File "))
        or bool(FRAME_RE.search(line))
    )
