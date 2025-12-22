# CostSim V2 Adapter (M6)
"""
CostSim V2 Adapter - Enhanced simulation with confidence scoring.

This adapter wraps V1 CostSimulator and adds:
1. Confidence scoring (0.0 - 1.0)
2. V2-specific model calculations
3. Provenance logging integration
4. Comparison with V1 results

The V2 model uses historical data and machine learning coefficients
to provide more accurate estimates than V1's static lookup.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.costsim.config import get_commit_sha, get_config
from app.costsim.models import (
    ComparisonResult,
    ComparisonVerdict,
    V2SimulationResult,
    V2SimulationStatus,
)
from app.costsim.provenance import get_provenance_logger
from app.worker.simulate import CostSimulator, SimulationResult

logger = logging.getLogger("nova.costsim.v2_adapter")


# V2 Model coefficients (learned from historical data)
# These would be updated via canary runs and ML pipelines
V2_MODEL_COEFFICIENTS: Dict[str, Dict[str, float]] = {
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
V2_UNKNOWN_SKILL = {
    "base_cost_cents": 5.0,
    "latency_base_ms": 500.0,
    "confidence_base": 0.70,
    "unknown_risk_factor": 0.15,
}


@dataclass
class V2StepEstimate:
    """Enhanced step estimate with confidence."""

    step_index: int
    skill_id: str
    cost_cents: float
    latency_ms: float
    confidence: float
    risk_factors: Dict[str, float]


class CostSimV2Adapter:
    """
    CostSim V2 Adapter with enhanced modeling.

    Usage:
        adapter = CostSimV2Adapter(budget_cents=1000)
        result = await adapter.simulate(plan)

        # Or with V1 comparison
        result, comparison = await adapter.simulate_with_comparison(plan)
    """

    def __init__(
        self,
        budget_cents: int = 1000,
        allowed_skills: Optional[List[str]] = None,
        model_coefficients: Optional[Dict[str, Dict[str, float]]] = None,
        risk_threshold: float = 0.5,
        enable_provenance: bool = True,
        tenant_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ):
        """
        Initialize V2 adapter.

        Args:
            budget_cents: Available budget in cents
            allowed_skills: List of allowed skill IDs
            model_coefficients: Override V2 model coefficients
            risk_threshold: Maximum acceptable cumulative risk
            enable_provenance: Log provenance data
            tenant_id: Tenant identifier for provenance
            run_id: Run identifier for provenance
        """
        config = get_config()

        self.budget_cents = budget_cents
        self.allowed_skills = set(allowed_skills) if allowed_skills else None
        self.coefficients = {**V2_MODEL_COEFFICIENTS, **(model_coefficients or {})}
        self.risk_threshold = risk_threshold
        self.enable_provenance = enable_provenance and config.provenance_enabled
        self.tenant_id = tenant_id
        self.run_id = run_id

        # V1 simulator for comparison
        self._v1_simulator = CostSimulator(
            budget_cents=budget_cents,
            allowed_skills=list(allowed_skills) if allowed_skills else None,
            risk_threshold=risk_threshold,
        )

        # Config for versioning
        self._model_version = config.model_version
        self._adapter_version = config.adapter_version

    def _get_coefficients(self, skill_id: str) -> Dict[str, float]:
        """Get V2 model coefficients for a skill."""
        return self.coefficients.get(skill_id, V2_UNKNOWN_SKILL)

    def _estimate_step_v2(self, step_index: int, step: Dict[str, Any]) -> V2StepEstimate:
        """
        Estimate cost and latency using V2 model.

        V2 uses learned coefficients and considers more factors
        than V1's static lookup.
        """
        skill_id = step.get("skill", "unknown")
        params = step.get("params", {})
        coef = self._get_coefficients(skill_id)

        # Base estimates
        cost_cents = coef.get("base_cost_cents", 0.0)
        latency_ms = coef.get("latency_base_ms", 500.0)
        confidence = coef.get("confidence_base", 0.70)
        risk_factors = {}

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

            # Model confidence decreases with longer prompts
            if prompt_len > 2000:
                confidence *= 0.95
            if prompt_len > 4000:
                confidence *= 0.90

        elif skill_id == "http_call":
            # Adjust for timeout parameter
            timeout = params.get("timeout", 30)
            latency_ms = min(latency_ms + coef.get("latency_variance_ms", 150), timeout * 1000)
            risk_factors["timeout"] = coef.get("timeout_risk_factor", 0.08)

            # External URLs have higher risk
            url = params.get("url", "")
            if not url.startswith(("http://localhost", "http://127.0.0.1")):
                risk_factors["timeout"] *= 1.5
                confidence *= 0.95

        elif skill_id == "json_transform":
            # Simple and fast
            risk_factors["transform_error"] = coef.get("error_risk_factor", 0.005)

        elif skill_id in ("fs_read", "fs_write"):
            # File operations
            risk_key = "not_found_risk_factor" if skill_id == "fs_read" else "permission_risk_factor"
            risk_factors[skill_id.split("_")[1]] = coef.get(risk_key, 0.03)

        elif skill_id == "shell_lite":
            # Shell commands have variable latency
            risk_factors["timeout"] = coef.get("timeout_risk_factor", 0.07)
            # Longer commands have more risk
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
            confidence = 0.60  # Low confidence for unknown skills

        return V2StepEstimate(
            step_index=step_index,
            skill_id=skill_id,
            cost_cents=cost_cents,
            latency_ms=latency_ms,
            confidence=confidence,
            risk_factors=risk_factors,
        )

    async def simulate(self, plan: List[Dict[str, Any]]) -> V2SimulationResult:
        """
        Run V2 simulation on a plan.

        Args:
            plan: List of steps to simulate

        Returns:
            V2SimulationResult with enhanced estimates
        """
        start_time = time.monotonic()

        if not plan:
            result = V2SimulationResult(
                feasible=False,
                status=V2SimulationStatus.SCHEMA_ERROR,
                estimated_cost_cents=0,
                estimated_duration_ms=0,
                budget_remaining_cents=self.budget_cents,
                confidence_score=0.0,
                model_version=self._model_version,
                warnings=["Empty plan provided"],
            )
            runtime_ms = int((time.monotonic() - start_time) * 1000)
            result.runtime_ms = runtime_ms
            return result

        # Estimate each step
        step_estimates: List[V2StepEstimate] = []
        total_cost = 0.0
        total_latency = 0.0
        combined_confidence = 1.0
        all_risks: List[Dict[str, Any]] = []
        warnings: List[str] = []
        permission_gaps: List[str] = []

        for i, step in enumerate(plan):
            skill_id = step.get("skill", "unknown")

            # Permission check
            if self.allowed_skills is not None and skill_id not in self.allowed_skills:
                permission_gaps.append(skill_id)

            # V2 estimate
            estimate = self._estimate_step_v2(i, step)
            step_estimates.append(estimate)

            total_cost += estimate.cost_cents
            total_latency += estimate.latency_ms

            # Combine confidence (product of individual confidences)
            combined_confidence *= estimate.confidence

            # Collect risks
            for risk_type, probability in estimate.risk_factors.items():
                if probability > 0.02:  # Only significant risks
                    all_risks.append(
                        {
                            "step_index": i,
                            "skill_id": skill_id,
                            "risk_type": risk_type,
                            "probability": probability,
                        }
                    )

        # Round cost to integer cents
        estimated_cost_cents = int(round(total_cost))
        estimated_duration_ms = int(round(total_latency))
        budget_remaining = self.budget_cents - estimated_cost_cents

        # Determine feasibility
        budget_sufficient = estimated_cost_cents <= self.budget_cents
        has_permissions = len(permission_gaps) == 0

        # Calculate cumulative risk
        cumulative_risk = 0.0
        for risk in all_risks:
            cumulative_risk = 1.0 - ((1.0 - cumulative_risk) * (1.0 - risk["probability"]))
        risk_acceptable = cumulative_risk <= self.risk_threshold

        # Determine status
        if not budget_sufficient:
            status = V2SimulationStatus.ERROR
            feasible = False
            warnings.append(f"Budget insufficient: need {estimated_cost_cents} cents, have {self.budget_cents}")
        elif not has_permissions:
            status = V2SimulationStatus.ERROR
            feasible = False
            warnings.append(f"Permission denied for skills: {permission_gaps}")
        elif not risk_acceptable:
            status = V2SimulationStatus.ERROR
            feasible = False
            warnings.append(f"Risk too high: {cumulative_risk*100:.1f}% > {self.risk_threshold*100:.1f}%")
        else:
            status = V2SimulationStatus.SUCCESS
            feasible = True

        # Build result
        result = V2SimulationResult(
            feasible=feasible,
            status=status,
            estimated_cost_cents=estimated_cost_cents,
            estimated_duration_ms=estimated_duration_ms,
            budget_remaining_cents=budget_remaining,
            confidence_score=round(combined_confidence, 4),
            model_version=self._model_version,
            step_estimates=[
                {
                    "step_index": e.step_index,
                    "skill_id": e.skill_id,
                    "cost_cents": round(e.cost_cents, 2),
                    "latency_ms": round(e.latency_ms, 2),
                    "confidence": round(e.confidence, 4),
                }
                for e in step_estimates
            ],
            risks=all_risks,
            warnings=warnings,
            metadata={
                "plan_steps": len(plan),
                "cumulative_risk": round(cumulative_risk, 4),
                "budget_utilization": round(estimated_cost_cents / max(self.budget_cents, 1), 4),
                "adapter_version": self._adapter_version,
                "commit_sha": get_commit_sha(),
            },
        )

        runtime_ms = int((time.monotonic() - start_time) * 1000)
        result.runtime_ms = runtime_ms

        # Log provenance
        if self.enable_provenance:
            try:
                provenance_logger = get_provenance_logger()
                await provenance_logger.log(
                    input_data={"plan": plan, "budget_cents": self.budget_cents},
                    output_data=result.to_dict(),
                    runtime_ms=runtime_ms,
                    status=status.value,
                    tenant_id=self.tenant_id,
                    run_id=self.run_id,
                )
            except Exception as e:
                logger.warning(f"Failed to log provenance: {e}")

        return result

    async def simulate_with_comparison(self, plan: List[Dict[str, Any]]) -> tuple[V2SimulationResult, ComparisonResult]:
        """
        Run V2 simulation and compare with V1.

        Args:
            plan: List of steps to simulate

        Returns:
            Tuple of (V2SimulationResult, ComparisonResult)
        """
        # Run V2
        v2_result = await self.simulate(plan)

        # Run V1
        v1_result = self._v1_simulator.simulate(plan)

        # Compare
        comparison = self._compare_results(v1_result, v2_result)

        return v2_result, comparison

    def _compare_results(self, v1: SimulationResult, v2: V2SimulationResult) -> ComparisonResult:
        """Compare V1 and V2 simulation results."""
        config = get_config()

        # Calculate deltas
        cost_delta = v2.estimated_cost_cents - v1.estimated_cost_cents
        cost_delta_pct = abs(cost_delta) / max(v1.estimated_cost_cents, 1) if v1.estimated_cost_cents > 0 else 0.0

        duration_delta = v2.estimated_duration_ms - v1.estimated_duration_ms

        feasibility_match = v1.feasible == v2.feasible

        # Calculate drift score
        # Weighted combination of cost drift and feasibility mismatch
        cost_weight = 0.6
        feasibility_weight = 0.4

        normalized_cost_drift = min(cost_delta_pct, 1.0)
        feasibility_drift = 0.0 if feasibility_match else 1.0

        drift_score = (cost_weight * normalized_cost_drift) + (feasibility_weight * feasibility_drift)

        # Determine verdict
        if drift_score <= 0.05:
            verdict = ComparisonVerdict.MATCH
        elif drift_score <= config.drift_warning_threshold:
            verdict = ComparisonVerdict.MINOR_DRIFT
        elif drift_score <= config.drift_threshold:
            verdict = ComparisonVerdict.MAJOR_DRIFT
        else:
            verdict = ComparisonVerdict.MISMATCH

        return ComparisonResult(
            verdict=verdict,
            v1_cost_cents=v1.estimated_cost_cents,
            v2_cost_cents=v2.estimated_cost_cents,
            cost_delta_cents=cost_delta,
            cost_delta_pct=round(cost_delta_pct, 4),
            v1_duration_ms=v1.estimated_duration_ms,
            v2_duration_ms=v2.estimated_duration_ms,
            duration_delta_ms=duration_delta,
            v1_feasible=v1.feasible,
            v2_feasible=v2.feasible,
            feasibility_match=feasibility_match,
            drift_score=round(drift_score, 4),
            details={
                "v1_status": v1.status.value,
                "v2_status": v2.status.value,
                "v2_confidence": v2.confidence_score,
                "v1_risks_count": len(v1.risks),
                "v2_risks_count": len(v2.risks),
            },
        )


async def simulate_v2(
    plan: List[Dict[str, Any]],
    budget_cents: int = 1000,
    allowed_skills: Optional[List[str]] = None,
    tenant_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> V2SimulationResult:
    """
    Convenience function for V2 simulation.

    Args:
        plan: List of steps
        budget_cents: Available budget
        allowed_skills: Optional skill allowlist
        tenant_id: Tenant identifier
        run_id: Run identifier

    Returns:
        V2SimulationResult
    """
    adapter = CostSimV2Adapter(
        budget_cents=budget_cents,
        allowed_skills=allowed_skills,
        tenant_id=tenant_id,
        run_id=run_id,
    )
    return await adapter.simulate(plan)


async def simulate_v2_with_comparison(
    plan: List[Dict[str, Any]],
    budget_cents: int = 1000,
    allowed_skills: Optional[List[str]] = None,
) -> tuple[V2SimulationResult, ComparisonResult]:
    """
    Convenience function for V2 simulation with V1 comparison.

    Args:
        plan: List of steps
        budget_cents: Available budget
        allowed_skills: Optional skill allowlist

    Returns:
        Tuple of (V2SimulationResult, ComparisonResult)
    """
    adapter = CostSimV2Adapter(
        budget_cents=budget_cents,
        allowed_skills=allowed_skills,
    )
    return await adapter.simulate_with_comparison(plan)
