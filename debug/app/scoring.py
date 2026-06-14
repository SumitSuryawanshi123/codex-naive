from __future__ import annotations

import json
import math
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import EvidenceLink, Hypothesis
from app.reasoning.linking import CATEGORY_TAGS

STRENGTH_WEIGHTS = {"weak": 1, "moderate": 2, "strong": 3}


def score_hypothesis(hypothesis: Hypothesis, k: float = 4.0) -> tuple[int, dict[str, int | float]]:
    buckets: dict[tuple[int, str], int] = defaultdict(int)
    supporting = 0
    contradicting = 0
    for link in hypothesis.links:
        if not link.verified:
            continue
        tags = set(json.loads(link.evidence.signal_tags))
        matched_tags = tags & CATEGORY_TAGS.get(hypothesis.category, tags)
        weight = STRENGTH_WEIGHTS.get(link.strength, 1)
        for tag in matched_tags:
            key = (link.evidence.artifact_id, tag)
            previous = buckets[key]
            capped = min(3, previous + weight) - previous
            buckets[key] += capped
            if link.relation == "contradicts":
                contradicting += capped
            else:
                supporting += capped
    raw = max(0, supporting - contradicting)
    score = round(10 * (1 - math.exp(-raw / k)))
    return min(10, score), {"supporting": supporting, "contradicting": contradicting, "raw": raw}


def rescore_all(db: Session, hypotheses: list[Hypothesis]) -> None:
    for hypothesis in hypotheses:
        hypothesis.evidence_score, _ = score_hypothesis(hypothesis)
    db.commit()


def margin(hypotheses: list[Hypothesis]) -> int:
    ranked = sorted(hypotheses, key=lambda item: item.evidence_score, reverse=True)
    if not ranked:
        return 0
    if len(ranked) == 1:
        return ranked[0].evidence_score
    return ranked[0].evidence_score - ranked[1].evidence_score
