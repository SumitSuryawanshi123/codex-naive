from __future__ import annotations

import json

from debug_module.models import Evidence, Hypothesis
from debug_module.reasoning.hypotheses import generate_hypotheses
from debug_module.reasoning.linking import link_evidence


class FakeLLM:
    def __init__(self, response: dict | None) -> None:
        self.response = response

    def complete_json(self, task: str, payload: dict, schema: dict | None = None) -> dict | None:
        return self.response


def evidence(tags: list[str], text: str = "ERROR timeout calling Stripe") -> Evidence:
    return Evidence(
        id=10,
        investigation_id=1,
        artifact_id=1,
        type="log",
        span_start=0,
        span_end=len(text),
        normalized_text=text,
        signal_tags=json.dumps(tags),
        fingerprint="abc",
    )


def test_llm_hypothesis_generation_accepts_valid_schema() -> None:
    result = generate_hypotheses(
        [evidence(["timeout", "dependency"])],
        llm_client=FakeLLM(
            {
                "hypotheses": [
                    {
                        "category": "SECURITY",
                        "statement": "A payment permission boundary may be blocking checkout.",
                        "novelty_score": 0.25,
                    }
                ]
            }
        ),
    )

    assert {
        "category": "SECURITY",
        "statement": "A payment permission boundary may be blocking checkout.",
        "novelty_score": 0.25,
    } in result


def test_llm_hypothesis_generation_falls_back_on_malformed_response() -> None:
    result = generate_hypotheses([evidence(["security"])], llm_client=FakeLLM({"hypotheses": "bad"}))

    assert result[0]["category"] == "SECURITY"


def test_llm_linking_accepts_known_evidence_ids_only() -> None:
    item = evidence(["timeout"], "ERROR timeout calling provider")
    hypothesis = Hypothesis(
        id=1,
        investigation_id=1,
        category="EXTERNAL_SERVICE",
        statement="Provider timeout caused the request failure.",
    )

    result = link_evidence(
        hypothesis,
        [item],
        llm_client=FakeLLM(
            {
                "links": [
                    {"evidence_id": 999, "relation": "supports", "strength": "strong", "rationale": "invented"},
                    {"evidence_id": 10, "relation": "supports", "strength": "strong", "rationale": "timeout signal"},
                ]
            }
        ),
    )

    assert len(result) == 1
    assert result[0]["evidence_id"] == 10
    assert result[0]["relation"] == "supports"


def test_llm_linking_falls_back_on_malformed_response() -> None:
    item = evidence(["network"], "ERROR DNS lookup failed")
    hypothesis = Hypothesis(
        id=1,
        investigation_id=1,
        category="NETWORK",
        statement="DNS resolution failed.",
    )

    result = link_evidence(hypothesis, [item], llm_client=FakeLLM({"links": "bad"}))

    assert result[0]["evidence_id"] == 10
    assert result[0]["relation"] == "supports"
