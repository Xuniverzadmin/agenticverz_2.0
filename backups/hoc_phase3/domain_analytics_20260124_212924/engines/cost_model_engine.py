# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Cost modeling and risk estimation domain authority
# Callers: CostSimV2Adapter (L3), simulation endpoints
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-254 Phase B Fix

"""
L4 Cost Model Engine - Domain Authority for Cost/Risk Estimation

B02 FIX: Moved from L3 CostSimV2Adapter to L4 domain engine.
This engine is the authoritative source for:
- Cost model coefficients (per-skill pricing)
- Risk estimation logic
- Feasibility determination
- Drift classification

L3 adapters must delegate all domain decisions to this engine.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.cost_model_engine")


# =============================================================================
# L4 Domain Authority: Cost Model Coefficients
# =============================================================================
# These are domain rules that define how we estimate costs and risks.
# L3 adapters must use these, not define their own.

# V2 Model coefficients (learned from historical data)
# Updated via canary runs and ML pipelines
SKILL_COST_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    "http_call": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 350.0,
        "latency_variance_ms": 150.0,
        "confidence_base": 0.85,
        "timeout_risk_factor": 0.08,
    },
    "llm_invoke": {
        "base_cost_cents": 3.5,
        "cost_per_1k_input_chars": 0.8,
        "cost_per_1k_output_chars": 1.2,
        "latency_base_ms": 1800.0,
        "latency_per_1k_chars_ms": 200.0,
        "confidence_base": 0.92,
        "rate_limit_risk_factor": 0.03,
    },
    "json_transform": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 5.0,
        "confidence_base": 0.98,
        "error_risk_factor": 0.005,
    },
    "fs_read": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 30.0,
        "confidence_base": 0.95,
        "not_found_risk_factor": 0.03,
    },
    "fs_write": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 50.0,
        "confidence_base": 0.94,
        "permission_risk_factor": 0.02,
    },
    "shell_lite": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 150.0,
        "confidence_base": 0.88,
        "timeout_risk_factor": 0.07,
    },
    "kv_get": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 3.0,
        "confidence_base": 0.97,
        "miss_risk_factor": 0.01,
    },
    "kv_set": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 5.0,
        "confidence_base": 0.97,
        "quota_risk_factor": 0.01,
    },
    "webhook_send": {
        "base_cost_cents": 0.0,
        "latency_base_ms": 200.0,
        "confidence_base": 0.90,
        "timeout_risk_factor": 0.08,
    },
    "email_send": {
        "base_cost_cents": 0.8,
        "latency_base_ms": 350.0,
        "confidence_base": 0.93,
        "delivery_risk_factor": 0.03,
    },
}

# Default for unknown skills
UNKNOWN_SKILL_COEFFICIENTS: Dict[str, float] = {
    "base_cost_cents": 5.0,
    "latency_base_ms": 500.0,
    "confidence_base": 0.70,
    "unknown_risk_factor": 0.15,
}


# =============================================================================
# L4 Domain Authority: Drift Classification
# =============================================================================


class DriftVerdict(str, Enum):
    """Classification of drift between V1 and V2 simulation results."""

    MATCH = "MATCH"  # <= 5% drift
    MINOR_DRIFT = "MINOR_DRIFT"  # <= 15% drift
    MAJOR_DRIFT = "MAJOR_DRIFT"  # <= 30% drift
    MISMATCH = "MISMATCH"  # > 30% drift


# Drift thresholds (L4 policy)
DRIFT_THRESHOLD_MATCH = 0.05
DRIFT_THRESHOLD_MINOR = 0.15
DRIFT_THRESHOLD_MAJOR = 0.30


# =============================================================================
# L4 Domain Authority: Risk Thresholds
# =============================================================================

# Default risk threshold for feasibility
DEFAULT_RISK_THRESHOLD = 0.5

# Minimum significant risk factor (below this, risk is ignored)
SIGNIFICANT_RISK_THRESHOLD = 0.02

# Confidence degradation thresholds
CONFIDENCE_DEGRADATION_LONG_PROMPT = 2000  # chars
CONFIDENCE_DEGRADATION_VERY_LONG_PROMPT = 4000  # chars


@dataclass
class StepCostEstimate:
    """Enhanced step estimate with confidence (L4 domain output)."""

    step_index: int
    skill_id: str
    cost_cents: float
    latency_ms: float
    confidence: float
    risk_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class FeasibilityResult:
    """Result of feasibility check (L4 domain output)."""

    feasible: bool
    budget_sufficient: bool
    has_permissions: bool
    risk_acceptable: bool
    cumulative_risk: float
    reason: Optional[str] = None


@dataclass
class DriftAnalysis:
    """Result of drift analysis between V1 and V2 (L4 domain output)."""

    verdict: DriftVerdict
    drift_score: float
    cost_delta_pct: float
    feasibility_match: bool
    details: Dict[str, Any] = field(default_factory=dict)


def get_skill_coefficients(skill_id: str) -> Dict[str, float]:
    """
    Get cost model coefficients for a skill (L4 domain function).

    Args:
        skill_id: Skill identifier

    Returns:
        Coefficient dictionary
    """
    return SKILL_COST_COEFFICIENTS.get(skill_id, UNKNOWN_SKILL_COEFFICIENTS)


def estimate_step_cost(
    step_index: int,
    skill_id: str,
    params: Dict[str, Any],
) -> StepCostEstimate:
    """
    Estimate cost and latency for a single step (L4 domain function).

    L3 adapters must NOT implement their own estimation logic.

    Args:
        step_index: Step position in plan
        skill_id: Skill identifier
        params: Step parameters

    Returns:
        StepCostEstimate with cost, latency, confidence, and risks
    """
    coef = get_skill_coefficients(skill_id)

    # Base estimates
    cost_cents = coef.get("base_cost_cents", 0.0)
    latency_ms = coef.get("latency_base_ms", 500.0)
    confidence = coef.get("confidence_base", 0.70)
    risk_factors: Dict[str, float] = {}

    # Skill-specific adjustments
    if skill_id == "llm_invoke":
        # Estimate based on prompt/output length
        prompt = str(params.get("prompt", ""))
        prompt_len = len(prompt)
        estimated_output_len = min(prompt_len * 2, 4000)  # Heuristic

        cost_cents += (prompt_len / 1000) * coef.get("cost_per_1k_input_chars", 0.8)
        cost_cents += (estimated_output_len / 1000) * coef.get("cost_per_1k_output_chars", 1.2)
        latency_ms += (prompt_len / 1000) * coef.get("latency_per_1k_chars_ms", 200.0)

        risk_factors["rate_limit"] = coef.get("rate_limit_risk_factor", 0.03)

        # Confidence decreases with longer prompts
        if prompt_len > CONFIDENCE_DEGRADATION_LONG_PROMPT:
            confidence *= 0.95
        if prompt_len > CONFIDENCE_DEGRADATION_VERY_LONG_PROMPT:
            confidence *= 0.90

    elif skill_id == "http_call":
        timeout = params.get("timeout", 30)
        latency_ms = min(latency_ms + coef.get("latency_variance_ms", 150), timeout * 1000)
        risk_factors["timeout"] = coef.get("timeout_risk_factor", 0.08)

        # External URLs have higher risk
        url = params.get("url", "")
        if not url.startswith(("http://localhost", "http://127.0.0.1")):
            risk_factors["timeout"] *= 1.5
            confidence *= 0.95

    elif skill_id == "json_transform":
        risk_factors["transform_error"] = coef.get("error_risk_factor", 0.005)

    elif skill_id in ("fs_read", "fs_write"):
        risk_key = "not_found_risk_factor" if skill_id == "fs_read" else "permission_risk_factor"
        risk_factors[skill_id.split("_")[1]] = coef.get(risk_key, 0.03)

    elif skill_id == "shell_lite":
        risk_factors["timeout"] = coef.get("timeout_risk_factor", 0.07)
        cmd = str(params.get("command", ""))
        if len(cmd) > 100:
            risk_factors["timeout"] *= 1.2
            confidence *= 0.95

    elif skill_id in ("kv_get", "kv_set"):
        risk_key = "miss_risk_factor" if skill_id == "kv_get" else "quota_risk_factor"
        risk_factors[skill_id.split("_")[1]] = coef.get(risk_key, 0.01)

    elif skill_id == "webhook_send":
        risk_factors["timeout"] = coef.get("timeout_risk_factor", 0.08)

    elif skill_id == "email_send":
        risk_factors["delivery"] = coef.get("delivery_risk_factor", 0.03)

    else:
        # Unknown skill
        risk_factors["unknown"] = coef.get("unknown_risk_factor", 0.15)
        confidence = 0.60

    return StepCostEstimate(
        step_index=step_index,
        skill_id=skill_id,
        cost_cents=cost_cents,
        latency_ms=latency_ms,
        confidence=confidence,
        risk_factors=risk_factors,
    )


def calculate_cumulative_risk(risks: List[Dict[str, float]]) -> float:
    """
    Calculate cumulative risk from individual risk factors (L4 domain function).

    Uses probability complement formula: 1 - prod(1 - p_i)

    Args:
        risks: List of risk factor dictionaries

    Returns:
        Cumulative risk probability (0.0 to 1.0)
    """
    cumulative = 0.0
    for risk in risks:
        for probability in risk.values():
            cumulative = 1.0 - ((1.0 - cumulative) * (1.0 - probability))
    return cumulative


def check_feasibility(
    estimated_cost_cents: int,
    budget_cents: int,
    permission_gaps: List[str],
    cumulative_risk: float,
    risk_threshold: float = DEFAULT_RISK_THRESHOLD,
) -> FeasibilityResult:
    """
    Check if a plan is feasible (L4 domain function).

    L3 adapters must NOT implement feasibility logic.

    Args:
        estimated_cost_cents: Estimated total cost
        budget_cents: Available budget
        permission_gaps: Skills without permission
        cumulative_risk: Cumulative risk probability
        risk_threshold: Maximum acceptable risk

    Returns:
        FeasibilityResult with decision and reasons
    """
    budget_sufficient = estimated_cost_cents <= budget_cents
    has_permissions = len(permission_gaps) == 0
    risk_acceptable = cumulative_risk <= risk_threshold

    feasible = budget_sufficient and has_permissions and risk_acceptable

    reason = None
    if not budget_sufficient:
        reason = f"Budget insufficient: need {estimated_cost_cents} cents, have {budget_cents}"
    elif not has_permissions:
        reason = f"Permission denied for skills: {permission_gaps}"
    elif not risk_acceptable:
        reason = f"Risk too high: {cumulative_risk * 100:.1f}% > {risk_threshold * 100:.1f}%"

    return FeasibilityResult(
        feasible=feasible,
        budget_sufficient=budget_sufficient,
        has_permissions=has_permissions,
        risk_acceptable=risk_acceptable,
        cumulative_risk=cumulative_risk,
        reason=reason,
    )


def classify_drift(
    v1_cost_cents: int,
    v2_cost_cents: int,
    v1_feasible: bool,
    v2_feasible: bool,
) -> DriftAnalysis:
    """
    Classify drift between V1 and V2 simulation results (L4 domain function).

    L3 adapters must NOT implement drift classification.

    Args:
        v1_cost_cents: V1 estimated cost
        v2_cost_cents: V2 estimated cost
        v1_feasible: V1 feasibility
        v2_feasible: V2 feasibility

    Returns:
        DriftAnalysis with verdict and details
    """
    # Calculate cost delta
    cost_delta = v2_cost_cents - v1_cost_cents
    cost_delta_pct = abs(cost_delta) / max(v1_cost_cents, 1) if v1_cost_cents > 0 else 0.0

    feasibility_match = v1_feasible == v2_feasible

    # Calculate drift score (weighted)
    cost_weight = 0.6
    feasibility_weight = 0.4

    normalized_cost_drift = min(cost_delta_pct, 1.0)
    feasibility_drift = 0.0 if feasibility_match else 1.0

    drift_score = (cost_weight * normalized_cost_drift) + (feasibility_weight * feasibility_drift)

    # Classify verdict
    if drift_score <= DRIFT_THRESHOLD_MATCH:
        verdict = DriftVerdict.MATCH
    elif drift_score <= DRIFT_THRESHOLD_MINOR:
        verdict = DriftVerdict.MINOR_DRIFT
    elif drift_score <= DRIFT_THRESHOLD_MAJOR:
        verdict = DriftVerdict.MAJOR_DRIFT
    else:
        verdict = DriftVerdict.MISMATCH

    return DriftAnalysis(
        verdict=verdict,
        drift_score=round(drift_score, 4),
        cost_delta_pct=round(cost_delta_pct, 4),
        feasibility_match=feasibility_match,
        details={
            "cost_delta_cents": cost_delta,
            "v1_cost_cents": v1_cost_cents,
            "v2_cost_cents": v2_cost_cents,
        },
    )


def is_significant_risk(probability: float) -> bool:
    """Check if a risk factor is significant enough to report (L4 domain function)."""
    return probability > SIGNIFICANT_RISK_THRESHOLD


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Constants
    "SKILL_COST_COEFFICIENTS",
    "UNKNOWN_SKILL_COEFFICIENTS",
    "DEFAULT_RISK_THRESHOLD",
    "SIGNIFICANT_RISK_THRESHOLD",
    "DRIFT_THRESHOLD_MATCH",
    "DRIFT_THRESHOLD_MINOR",
    "DRIFT_THRESHOLD_MAJOR",
    # Enums
    "DriftVerdict",
    # Classes
    "StepCostEstimate",
    "FeasibilityResult",
    "DriftAnalysis",
    # Functions
    "get_skill_coefficients",
    "estimate_step_cost",
    "calculate_cumulative_risk",
    "check_feasibility",
    "classify_drift",
    "is_significant_risk",
]
