from __future__ import annotations

import json
from typing import Any, Protocol

from debug_module.config import get_settings
from debug_module.llm import CachedLLMClient
from debug_module.models import Evidence

CATEGORIES = [
    "CODE",
    "CONFIGURATION",
    "DATA",
    "BUSINESS_LOGIC",
    "INFRASTRUCTURE",
    "DEPENDENCY",
    "NETWORK",
    "SECURITY",
    "EXTERNAL_SERVICE",
]

TAG_TO_HYPOTHESIS = {
    "exception": ("CODE", "An application code path is throwing an unhandled exception."),
    "stack_frame": ("CODE", "The failing stack frame points to a defective or unguarded code path."),
    "configuration": ("CONFIGURATION", "A missing or invalid runtime configuration is causing the failure."),
    "data": ("DATA", "The incident is caused by invalid data shape, constraints, or migration drift."),
    "business_logic": ("BUSINESS_LOGIC", "A domain rule or invariant is rejecting the request."),
    "infrastructure": ("INFRASTRUCTURE", "Underlying compute, memory, disk, or orchestration capacity is unhealthy."),
    "dependency": ("DEPENDENCY", "A required backing service or library dependency is failing."),
    "network": ("NETWORK", "Network connectivity or DNS is preventing a required call."),
    "security": ("SECURITY", "Authentication, authorization, or secret handling is blocking the operation."),
    "timeout": ("EXTERNAL_SERVICE", "A slow or unavailable external service is causing timeouts."),
    "external_service": ("EXTERNAL_SERVICE", "A slow or unavailable external service is causing timeouts."),
}


class HypothesisLLM(Protocol):
    def complete_json(self, task: str, payload: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any] | None:
        ...


HYPOTHESIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "hypotheses": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "category": {"type": "string", "enum": CATEGORIES},
                    "statement": {"type": "string", "minLength": 8},
                    "novelty_score": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["category", "statement", "novelty_score"],
            },
        }
    },
    "required": ["hypotheses"],
}


def _evidence_payload(evidence: list[Evidence]) -> list[dict[str, Any]]:
    return [
        {
            "id": item.id,
            "type": item.type,
            "text": item.normalized_text,
            "tags": json.loads(item.signal_tags),
            "span": [item.span_start, item.span_end],
        }
        for item in evidence
    ]


def _rule_based_hypotheses(evidence: list[Evidence]) -> list[dict[str, str | float]]:
    seen: set[str] = set()
    known_pattern_categories = {
        tag.removeprefix("pattern_").upper()
        for item in evidence
        for tag in json.loads(item.signal_tags)
        if tag.startswith("pattern_")
    }
    hypotheses: list[dict[str, str | float]] = []
    for item in evidence:
        for tag in json.loads(item.signal_tags):
            if tag not in TAG_TO_HYPOTHESIS:
                continue
            category, statement = TAG_TO_HYPOTHESIS[tag]
            if category in seen:
                continue
            novelty_score = 0.2 if category in known_pattern_categories else 0.5
            hypotheses.append({"category": category, "statement": statement, "novelty_score": novelty_score})
            seen.add(category)
            if len(hypotheses) >= 5:
                return hypotheses
    if not hypotheses:
        hypotheses.append({"category": "CODE", "statement": "The incident has too little signal to identify a root cause yet.", "novelty_score": 0.8})
    return hypotheses


def _llm_hypotheses(evidence: list[Evidence], llm_client: HypothesisLLM) -> list[dict[str, str | float]]:
    response = llm_client.complete_json(
        "debugos_hypothesis_generation",
        {
            "instruction": (
                "Generate category-diverse root-cause hypotheses from verified debugging evidence. "
                "Prefer specific operational categories over generic CODE when tags support them."
            ),
            "allowed_categories": CATEGORIES,
            "evidence": _evidence_payload(evidence),
        },
        HYPOTHESIS_SCHEMA,
    )
    if not response or not isinstance(response.get("hypotheses"), list):
        return []

    seen: set[str] = set()
    candidates: list[dict[str, str | float]] = []
    for item in response["hypotheses"]:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        statement = item.get("statement")
        novelty_score = item.get("novelty_score", 0.5)
        if category not in CATEGORIES or category in seen or not isinstance(statement, str) or not statement.strip():
            continue
        try:
            novelty = max(0.0, min(1.0, float(novelty_score)))
        except (TypeError, ValueError):
            novelty = 0.5
        candidates.append({"category": category, "statement": statement.strip(), "novelty_score": novelty})
        seen.add(category)
        if len(candidates) >= 5:
            break
    return candidates


def generate_hypotheses(evidence: list[Evidence], llm_client: HypothesisLLM | None = None) -> list[dict[str, str | float]]:
    rule_candidates = _rule_based_hypotheses(evidence)
    if llm_client is None and not get_settings().enable_llm_reasoning:
        return rule_candidates

    llm_client = llm_client or CachedLLMClient()
    try:
        llm_candidates = _llm_hypotheses(evidence, llm_client)
    except Exception:
        llm_candidates = []

    merged = list(rule_candidates)
    seen = {str(item["category"]) for item in merged}
    for candidate in llm_candidates:
        if candidate["category"] in seen:
            continue
        merged.append(candidate)
        seen.add(str(candidate["category"]))
        if len(merged) >= 5:
            break
    return merged
