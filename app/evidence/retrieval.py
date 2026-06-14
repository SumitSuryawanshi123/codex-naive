from __future__ import annotations

import json
import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Evidence


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z_]{3,}", text.lower()) if token not in {"the", "and", "for", "with"}}


def ranked_evidence(db: Session, investigation_id: int, query: str = "", token_budget: int = 1200) -> list[Evidence]:
    rows = list(db.scalars(select(Evidence).where(Evidence.investigation_id == investigation_id)))
    query_terms = tokenize(query)
    tag_counts = Counter()
    for row in rows:
        tag_counts.update(json.loads(row.signal_tags))

    def score(row: Evidence) -> tuple[int, int]:
        tags = json.loads(row.signal_tags)
        overlap = len(query_terms & tokenize(row.normalized_text)) if query_terms else 0
        rarity = sum(max(1, 5 - tag_counts[tag]) for tag in tags)
        severity = sum(3 for tag in tags if tag in {"error", "fatal", "critical", "exception"})
        return (overlap * 5 + rarity + severity, -len(row.normalized_text))

    ranked = sorted(rows, key=score, reverse=True)
    selected: list[Evidence] = []
    used = 0
    for row in ranked:
        cost = max(1, len(row.normalized_text.split()))
        if selected and used + cost > token_budget:
            continue
        selected.append(row)
        used += cost
    return selected
