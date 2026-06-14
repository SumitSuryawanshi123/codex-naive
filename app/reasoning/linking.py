from __future__ import annotations

import json
from typing import Any, Protocol

from app.config import get_settings
from app.llm import CachedLLMClient
from app.models import Evidence, Hypothesis

CATEGORY_TAGS = {
    "CODE": {"exception", "stack_frame", "code_context"},
    "CONFIGURATION": {"configuration"},
    "DATA": {"data"},
    "BUSINESS_LOGIC": {"business_logic"},
    "INFRASTRUCTURE": {"infrastructure"},
    "DEPENDENCY": {"dependency", "timeout"},
    "NETWORK": {"network", "timeout"},
    "SECURITY": {"security"},
    "EXTERNAL_SERVICE": {"timeout", "dependency", "external_service"},
}

DOMAIN_TAGS = set().union(*(tags for category, tags in CATEGORY_TAGS.items() if category != "CODE"))


class LinkLLM(Protocol):
    def complete_json(self, task: str, payload: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any] | None:
        ...


LINK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "links": {
            "type": "array",
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "evidence_id": {"type": "integer"},
                    "relation": {"type": "string", "enum": ["supports", "contradicts"]},
                    "strength": {"type": "string", "enum": ["weak", "moderate", "strong"]},
                    "rationale": {"type": "string"},
                },
                "required": ["evidence_id", "relation", "strength", "rationale"],
            },
        }
    },
    "required": ["links"],
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


def _rule_based_links(hypothesis: Hypothesis, evidence: list[Evidence]) -> list[dict[str, str | int]]:
    wanted = CATEGORY_TAGS.get(hypothesis.category, set())
    links: list[dict[str, str | int]] = []
    for item in evidence:
        tags = set(json.loads(item.signal_tags))
        if hypothesis.category == "CODE" and tags & DOMAIN_TAGS:
            continue
        overlap = tags & wanted
        if not overlap:
            continue
        strength = "strong" if {"fatal", "critical", "exception", "stack_frame"} & overlap else "moderate"
        if "timeout" in overlap and hypothesis.category in {"NETWORK", "EXTERNAL_SERVICE"}:
            strength = "strong"
        links.append(
            {
                "evidence_id": item.id,
                "relation": "supports",
                "strength": strength,
                "rationale": f"Matched signal tags: {', '.join(sorted(overlap))}.",
            }
        )
    return links[:6]


def _llm_links(hypothesis: Hypothesis, evidence: list[Evidence], llm_client: LinkLLM) -> list[dict[str, str | int]]:
    known_ids = {item.id for item in evidence}
    response = llm_client.complete_json(
        "debugos_evidence_linking",
        {
            "instruction": (
                "Link only evidence that directly supports or contradicts the hypothesis. "
                "Use evidence_id values exactly as supplied. Do not invent evidence."
            ),
            "hypothesis": {
                "id": hypothesis.id,
                "category": hypothesis.category,
                "statement": hypothesis.statement,
            },
            "evidence": _evidence_payload(evidence),
        },
        LINK_SCHEMA,
    )
    if not response or not isinstance(response.get("links"), list):
        return []

    links: list[dict[str, str | int]] = []
    seen: set[int] = set()
    for item in response["links"]:
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("evidence_id")
        relation = item.get("relation")
        strength = item.get("strength")
        rationale = item.get("rationale", "")
        if evidence_id not in known_ids or evidence_id in seen:
            continue
        if relation not in {"supports", "contradicts"} or strength not in {"weak", "moderate", "strong"}:
            continue
        links.append(
            {
                "evidence_id": evidence_id,
                "relation": relation,
                "strength": strength,
                "rationale": str(rationale)[:500],
            }
        )
        seen.add(evidence_id)
        if len(links) >= 6:
            break
    return links


def link_evidence(hypothesis: Hypothesis, evidence: list[Evidence], llm_client: LinkLLM | None = None) -> list[dict[str, str | int]]:
    rule_links = _rule_based_links(hypothesis, evidence)
    if llm_client is None and not get_settings().enable_llm_reasoning:
        return rule_links

    llm_client = llm_client or CachedLLMClient()
    try:
        llm_links = _llm_links(hypothesis, evidence, llm_client)
    except Exception:
        llm_links = []

    merged: dict[int, dict[str, str | int]] = {int(link["evidence_id"]): link for link in rule_links}
    for link in llm_links:
        evidence_id = int(link["evidence_id"])
        if evidence_id not in merged:
            merged[evidence_id] = link
    return list(merged.values())[:6]
