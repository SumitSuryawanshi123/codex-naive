from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Hypothesis


SUGGESTIONS = {
    "CODE": (
        "Inspect the failing stack frame and add a guard or corrected control flow at the cited source line.",
        "Run the focused unit test for the touched module, then replay the original log/trace fixture.",
    ),
    "CONFIGURATION": (
        "Compare the effective runtime configuration with the expected deployment configuration and restore the missing or invalid key.",
        "Restart the affected service in a staging environment and confirm startup logs no longer contain the configuration error.",
    ),
    "DATA": (
        "Validate the failing record shape and reconcile application expectations with the applied database migration.",
        "Run migration status checks and replay the failing request with a representative record.",
    ),
    "BUSINESS_LOGIC": (
        "Review the rejected invariant with the product rule owner and adjust either the request or the rule implementation.",
        "Add a regression test for the accepted and rejected domain cases.",
    ),
    "INFRASTRUCTURE": (
        "Increase or rebalance the constrained resource and inspect orchestration events around the incident window.",
        "Watch pod/process restarts and resource metrics under a representative workload.",
    ),
    "DEPENDENCY": (
        "Check the named dependency health, version, and saturation, then add a fallback or backoff if the dependency is transient.",
        "Run an integration check against the dependency and confirm error rates recover.",
    ),
    "NETWORK": (
        "Verify DNS, routing, and firewall policy from the failing service environment to the target endpoint.",
        "Run connectivity checks from the same pod or host and confirm successful resolution and connection.",
    ),
    "SECURITY": (
        "Inspect token claims, scopes, and policy decision logs, then grant the least privilege needed for the operation.",
        "Replay the request with corrected claims and confirm the authorization decision changes to allow.",
    ),
    "EXTERNAL_SERVICE": (
        "Confirm provider status and request latency, then tune timeout/retry behavior or route through a fallback path.",
        "Replay the provider call with tracing enabled and verify latency/error rates are within threshold.",
    ),
}


def remediation_suggestions(db: Session, investigation_id: int) -> list[dict[str, str]]:
    top = db.scalar(
        select(Hypothesis)
        .where(Hypothesis.investigation_id == investigation_id)
        .order_by(Hypothesis.evidence_score.desc(), Hypothesis.id.asc())
        .limit(1)
    )
    if not top or top.evidence_score <= 0:
        return []
    action, validation = SUGGESTIONS.get(
        top.category,
        (
            "Collect the requested evidence before changing production behavior.",
            "Replay the investigation after adding the new evidence.",
        ),
    )
    return [
        {
            "category": top.category,
            "action": action,
            "validation": validation,
            "status": "proposed",
        }
    ]
