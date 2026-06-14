from __future__ import annotations

import subprocess
from pathlib import Path


def git_blame_line(path: Path, line: int, repo_root: Path | None = None) -> str | None:
    root = repo_root or Path.cwd()
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line},{line}", "--", str(relative)],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
