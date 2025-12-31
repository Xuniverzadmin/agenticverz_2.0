# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Callers: recovery_claim_worker.py (L5 worker)
# Reference: PIN-257 Phase E-4 Extraction #4
# WARNING: If this logic is wrong, claim processing breaks.

# M10 Claim Decision Engine
"""
Domain engine for recovery claim decisions.

This L4 engine defines the authoritative rules for:
1. Claim eligibility - what candidates qualify for evaluation
2. Status determination - how evaluation results map to status

All claim decision semantics live here. L5 workers must call these functions,
not implement their own decision logic.

Reference: PIN-257 Phase E-4 Extraction #4
Governance: DOMAIN_EXTRACTION_TEMPLATE.md
"""

from typing import Any, Dict, Optional


# =============================================================================
# L4 Domain Decision Thresholds
# =============================================================================
# These thresholds are the AUTHORITATIVE source for claim decisions.
# L5 workers must call these functions, not implement their own thresholds.
# Reference: PIN-257 Phase E-4 Extraction #4


# Claim eligibility threshold (L4 domain rule)
# Candidates with confidence at or below this threshold are eligible for claiming.
# This defines what "unevaluated" means in the claim processing context.
CLAIM_ELIGIBILITY_THRESHOLD: float = 0.2


def is_candidate_claimable(confidence: Optional[float]) -> bool:
    """
    Determine if a candidate is eligible for claiming based on confidence.

    This is an L4 domain decision. L5 workers must NOT hardcode thresholds.

    A candidate is claimable if:
    - confidence is None (never evaluated), OR
    - confidence is at or below the eligibility threshold

    Args:
        confidence: Current confidence score (0.0 to 1.0), or None if never evaluated

    Returns:
        True if candidate is eligible for claiming and evaluation

    Reference: PIN-257 Phase E-4 Extraction #4
    """
    if confidence is None:
        return True
    return confidence <= CLAIM_ELIGIBILITY_THRESHOLD


# =============================================================================
# Status Determination (L4 Domain Decision)
# =============================================================================


def determine_claim_status(evaluation_result: Dict[str, Any]) -> str:
    """
    Determine the execution status from an evaluation result.

    This is an L4 domain decision. L5 workers must NOT implement status logic.

    Status mapping:
    - "succeeded": No error in result
    - "failed": Error present in result

    Args:
        evaluation_result: Result dict from evaluation, may contain "error" key

    Returns:
        Status string: "succeeded" or "failed"

    Reference: PIN-257 Phase E-4 Extraction #4
    """
    has_error = evaluation_result.get("error") is not None
    return "failed" if has_error else "succeeded"


def get_result_confidence(evaluation_result: Dict[str, Any]) -> float:
    """
    Extract confidence from evaluation result with default fallback.

    This is an L4 domain decision for confidence extraction.

    Args:
        evaluation_result: Result dict from evaluation

    Returns:
        Confidence score (defaults to 0.2 if not present)

    Reference: PIN-257 Phase E-4 Extraction #4
    """
    return evaluation_result.get("confidence", CLAIM_ELIGIBILITY_THRESHOLD)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CLAIM_ELIGIBILITY_THRESHOLD",
    "is_candidate_claimable",
    "determine_claim_status",
    "get_result_confidence",
]
