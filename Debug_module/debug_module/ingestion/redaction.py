from __future__ import annotations

import re


PATTERNS = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("API_KEY", re.compile(r"(?i)\b(api[_-]?key|token|secret|password)=([A-Za-z0-9_\-./+=]{8,})")),
    ("BEARER", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-./+=]{12,}")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def redact(text: str) -> tuple[str, dict[str, str]]:
    redaction_map: dict[str, str] = {}
    result = text
    counter = 1
    for label, pattern in PATTERNS:
        def replace(match: re.Match[str]) -> str:
            nonlocal counter
            token = f"[REDACTED_{label}_{counter}]"
            redaction_map[token] = match.group(0)
            counter += 1
            if label == "API_KEY":
                prefix = match.group(1)
                return f"{prefix}={token}"
            return token

        result = pattern.sub(replace, result)
    return result, redaction_map
