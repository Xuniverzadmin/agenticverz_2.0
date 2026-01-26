# CostSim V2 Adapter (M6)
# Layer: L3 — Boundary Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: Cost simulation adapter (translation only)
# Callers: simulation endpoints, workflow engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2
# Reference: PIN-254 Phase B Fix
# Location: hoc/cus/analytics/L3_adapters/v2_adapter.py
"""
CostSim V2 Adapter - Enhanced simulation with confidence scoring.

B02 FIX: Cost modeling logic moved to L4 CostModelEngine.
This adapter now delegates domain decisions to L4:
- Step cost estimation → L4 estimate_step_cost()
- Feasibility checks → L4 check_feasibility()
- Drift classification → L4 classify_drift()

L3 responsibility: shape, transport, provenance, context binding.

This adapter wraps V1 CostSimulator and adds:
1. Confidence scoring (delegated to L4)
2. V2-specific model calculations (delegated to L4)
3. Provenance logging integration
4. Comparison with V1 results
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


# B02 FIX: Cost model coefficients moved to L4 CostModelEngine
# See: app/services/cost_model_engine.py for SKILL_COST_COEFFICIENTS


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
        # B02 FIX: model_coefficients parameter kept for API compatibility but ignored.
        # Coefficients are now managed by L4 CostModelEngine.
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
        """
        Get V2 model coefficients for a skill.

        B02 FIX: Delegates to L4 CostModelEngine.
        """
        # L5 engine import (migrated to HOC per SWEEP-44)
        from app.hoc.cus.analytics.L5_engines.cost_model_engine import get_skill_coefficients

        return get_skill_coefficients(skill_id)

    def _estimate_step_v2(self, step_index: int, step: Dict[str, Any]) -> V2StepEstimate:
        """
        Estimate cost and latency using V2 model.

        B02 FIX: Delegates to L4 CostModelEngine.estimate_step_cost().
        L3 no longer contains estimation logic.
        """
        # L5 engine import (migrated to HOC per SWEEP-44)
        from app.hoc.cus.analytics.L5_engines.cost_model_engine import estimate_step_cost

        skill_id = step.get("skill", "unknown")
        params = step.get("params", {})

        # Delegate to L4 for domain logic
        l4_estimate = estimate_step_cost(step_index, skill_id, params)

        # Convert L4 output to adapter output format
        return V2StepEstimate(
            step_index=l4_estimate.step_index,
            skill_id=l4_estimate.skill_id,
            cost_cents=l4_estimate.cost_cents,
            latency_ms=l4_estimate.latency_ms,
            confidence=l4_estimate.confidence,
            risk_factors=l4_estimate.risk_factors,
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
            warnings.append(f"Risk too high: {cumulative_risk * 100:.1f}% > {self.risk_threshold * 100:.1f}%")
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
        """
        Compare V1 and V2 simulation results.

        B02 FIX: Delegates drift classification to L4 CostModelEngine.
        L3 only handles shape/transport, not classification thresholds.
        """
        # L5 engine import (migrated to HOC per SWEEP-44)
        from app.hoc.cus.analytics.L5_engines.cost_model_engine import classify_drift

        # Delegate drift classification to L4
        drift_analysis = classify_drift(
            v1_cost_cents=v1.estimated_cost_cents,
            v2_cost_cents=v2.estimated_cost_cents,
            v1_feasible=v1.feasible,
            v2_feasible=v2.feasible,
        )

        # Map L4 verdict to L3 ComparisonVerdict
        verdict_map = {
            "MATCH": ComparisonVerdict.MATCH,
            "MINOR_DRIFT": ComparisonVerdict.MINOR_DRIFT,
            "MAJOR_DRIFT": ComparisonVerdict.MAJOR_DRIFT,
            "MISMATCH": ComparisonVerdict.MISMATCH,
        }
        verdict = verdict_map.get(drift_analysis.verdict.value, ComparisonVerdict.MISMATCH)

        # Calculate duration delta (L3 shape responsibility - not a policy decision)
        duration_delta = v2.estimated_duration_ms - v1.estimated_duration_ms

        return ComparisonResult(
            verdict=verdict,
            v1_cost_cents=v1.estimated_cost_cents,
            v2_cost_cents=v2.estimated_cost_cents,
            cost_delta_cents=drift_analysis.details.get("cost_delta_cents", 0),
            cost_delta_pct=drift_analysis.cost_delta_pct,
            v1_duration_ms=v1.estimated_duration_ms,
            v2_duration_ms=v2.estimated_duration_ms,
            duration_delta_ms=duration_delta,
            v1_feasible=v1.feasible,
            v2_feasible=v2.feasible,
            feasibility_match=drift_analysis.feasibility_match,
            drift_score=drift_analysis.drift_score,
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
