from __future__ import annotations

import hashlib
import re


def canonicalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\b[0-9a-f]{8,}\b", "<hex>", text)
    text = re.sub(r"\b\d+\b", "<num>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fingerprint(text: str) -> str:
    return hashlib.sha256(canonicalize(text).encode("utf-8")).hexdigest()
