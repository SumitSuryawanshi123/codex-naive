from __future__ import annotations

from app.models import Hypothesis


REQUESTS_BY_CATEGORY = {
    "CODE": ("full stack trace and request parameters", "This can isolate the exact failing function.", "top frame, exception type, input shape"),
    "CONFIGURATION": ("effective environment/config for the failing service", "This confirms missing or invalid runtime settings.", "missing key, invalid flag, wrong endpoint"),
    "DATA": ("failing record shape and latest migration status", "This separates bad input from schema drift.", "constraint error, schema mismatch"),
    "NETWORK": ("DNS/connectivity check from the service pod or host", "This confirms whether the failure is transport-level.", "resolution failure, connection refused, packet loss"),
    "SECURITY": ("auth policy decision logs and token claims", "This confirms whether the request is blocked by identity or permission.", "401/403 reason, missing scope"),
    "DEPENDENCY": ("health and error logs from the named dependency", "This checks whether a backing service is the source.", "dependency outage, saturation, version mismatch"),
    "INFRASTRUCTURE": ("resource metrics around the incident window", "This confirms capacity or orchestration failure.", "OOM, CPU throttling, disk pressure"),
    "EXTERNAL_SERVICE": ("external provider status and request latency/error sample", "This validates timeout or provider-side failure.", "5xx, timeout, degraded status"),
}


def build_evidence_request(hypothesis: Hypothesis) -> dict[str, str]:
    what, why, expected = REQUESTS_BY_CATEGORY.get(
        hypothesis.category,
        ("additional logs around the incident", "The current evidence is not discriminating enough.", "new supporting or contradicting signal"),
    )
    return {"what": what, "why": why, "expected_signal": expected, "format": "paste text or upload log excerpt"}
