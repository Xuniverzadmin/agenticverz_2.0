# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: CostSim V2 sandbox routing (V1/V2 comparison, shadow mode)
# Callers: cost simulation API
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel

# CostSim V2 Sandbox Routing (M6)
"""
Sandbox routing layer for CostSim V1 vs V2.

Feature flag controlled routing:
- COSTSIM_V2_SANDBOX=false (default): Only V1, no V2
- COSTSIM_V2_SANDBOX=true: Run both V1 and V2, log comparison

The sandbox NEVER changes production behavior. V1 is always
the source of truth. V2 runs in shadow mode for validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Use async circuit breaker for non-blocking DB operations
from app.costsim.circuit_breaker_async import (
    is_v2_disabled,
    report_drift,
)
from app.costsim.config import is_v2_sandbox_enabled
from app.costsim.models import (
    ComparisonResult,
    ComparisonVerdict,
    V2SimulationResult,
)
from app.costsim.v2_adapter import CostSimV2Adapter
from app.worker.simulate import CostSimulator, SimulationResult

logger = logging.getLogger("nova.costsim.sandbox")


@dataclass
class SandboxResult:
    """Result from sandbox routing."""

    # V1 result (always present, always the production result)
    v1_result: SimulationResult

    # V2 result (only present if sandbox enabled)
    v2_result: Optional[V2SimulationResult] = None

    # Comparison (only present if V2 ran)
    comparison: Optional[ComparisonResult] = None

    # Sandbox metadata
    sandbox_enabled: bool = False
    v2_error: Optional[str] = None

    @property
    def production_result(self) -> SimulationResult:
        """Get the production result (always V1)."""
        return self.v1_result


class CostSimSandbox:
    """
    Sandbox router for CostSim V1 vs V2.

    Usage:
        sandbox = CostSimSandbox(budget_cents=1000)
        result = await sandbox.simulate(plan)

        # Production code uses v1_result
        if result.v1_result.feasible:
            execute_plan(plan)

        # V2 comparison logged for validation
        if result.comparison:
            logger.info(f"V2 drift: {result.comparison.drift_score}")
    """

    def __init__(
        self,
        budget_cents: int = 1000,
        allowed_skills: Optional[List[str]] = None,
        risk_threshold: float = 0.5,
        tenant_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ):
        """
        Initialize sandbox router.

        Args:
            budget_cents: Available budget in cents
            allowed_skills: List of allowed skill IDs
            risk_threshold: Maximum acceptable risk
            tenant_id: Tenant identifier for isolation
            run_id: Run identifier for provenance
        """
        self.budget_cents = budget_cents
        self.allowed_skills = allowed_skills
        self.risk_threshold = risk_threshold
        self.tenant_id = tenant_id
        self.run_id = run_id

        # V1 simulator (always used)
        self._v1_simulator = CostSimulator(
            budget_cents=budget_cents,
            allowed_skills=allowed_skills,
            risk_threshold=risk_threshold,
        )

        # V2 adapter (lazy init, only if sandbox enabled)
        self._v2_adapter: Optional[CostSimV2Adapter] = None

    def _get_v2_adapter(self) -> CostSimV2Adapter:
        """Get or create V2 adapter."""
        if self._v2_adapter is None:
            self._v2_adapter = CostSimV2Adapter(
                budget_cents=self.budget_cents,
                allowed_skills=self.allowed_skills,
                risk_threshold=self.risk_threshold,
                enable_provenance=True,
                tenant_id=self.tenant_id,
                run_id=self.run_id,
            )
        return self._v2_adapter

    async def simulate(self, plan: List[Dict[str, Any]]) -> SandboxResult:
        """
        Run simulation through sandbox.

        V1 always runs and provides the production result.
        V2 runs in shadow mode if COSTSIM_V2_SANDBOX=true and circuit breaker is closed.

        Args:
            plan: List of steps to simulate

        Returns:
            SandboxResult with V1 result and optional V2 comparison
        """
        # Always run V1 (production)
        v1_result = self._v1_simulator.simulate(plan)

        # Check if sandbox enabled
        if not is_v2_sandbox_enabled():
            return SandboxResult(
                v1_result=v1_result,
                sandbox_enabled=False,
            )

        # Check if circuit breaker has disabled V2
        if await is_v2_disabled():
            logger.warning("V2 sandbox disabled by circuit breaker")
            return SandboxResult(
                v1_result=v1_result,
                sandbox_enabled=False,
                v2_error="V2 disabled by circuit breaker",
            )

        # Run V2 in shadow mode
        v2_result: Optional[V2SimulationResult] = None
        comparison: Optional[ComparisonResult] = None
        v2_error: Optional[str] = None

        try:
            v2_adapter = self._get_v2_adapter()
            v2_result, comparison = await v2_adapter.simulate_with_comparison(plan)

            # Log comparison for monitoring
            self._log_comparison(comparison)

            # Report drift to circuit breaker (async, non-blocking)
            if comparison:
                incident = await report_drift(
                    drift_score=comparison.drift_score,
                    sample_count=1,
                    details={
                        "verdict": comparison.verdict.value,
                        "cost_delta_cents": comparison.cost_delta_cents,
                        "cost_delta_pct": comparison.cost_delta_pct,
                        "feasibility_match": comparison.feasibility_match,
                        "tenant_id": self.tenant_id,
                        "run_id": self.run_id,
                    },
                )
                if incident:
                    logger.error(f"Circuit breaker tripped: incident_id={incident.id}")
                    v2_error = f"Circuit breaker tripped: {incident.reason}"

        except Exception as e:
            logger.error(f"V2 sandbox error: {e}")
            v2_error = str(e)

        return SandboxResult(
            v1_result=v1_result,
            v2_result=v2_result,
            comparison=comparison,
            sandbox_enabled=True,
            v2_error=v2_error,
        )

    def _log_comparison(self, comparison: ComparisonResult) -> None:
        """Log comparison result for monitoring."""
        verdict = comparison.verdict.value
        drift = comparison.drift_score

        if comparison.verdict == ComparisonVerdict.MATCH:
            logger.debug(f"V2 sandbox MATCH: drift={drift:.4f}, cost_delta={comparison.cost_delta_cents}")
        elif comparison.verdict == ComparisonVerdict.MINOR_DRIFT:
            logger.info(
                f"V2 sandbox MINOR_DRIFT: drift={drift:.4f}, "
                f"cost_delta={comparison.cost_delta_cents}, "
                f"feasibility_match={comparison.feasibility_match}"
            )
        elif comparison.verdict == ComparisonVerdict.MAJOR_DRIFT:
            logger.warning(
                f"V2 sandbox MAJOR_DRIFT: drift={drift:.4f}, "
                f"cost_delta={comparison.cost_delta_cents}, "
                f"cost_delta_pct={comparison.cost_delta_pct:.2%}, "
                f"feasibility_match={comparison.feasibility_match}"
            )
        else:  # MISMATCH
            logger.error(
                f"V2 sandbox MISMATCH: drift={drift:.4f}, "
                f"v1_cost={comparison.v1_cost_cents}, "
                f"v2_cost={comparison.v2_cost_cents}, "
                f"v1_feasible={comparison.v1_feasible}, "
                f"v2_feasible={comparison.v2_feasible}"
            )


async def simulate_with_sandbox(
    plan: List[Dict[str, Any]],
    budget_cents: int = 1000,
    allowed_skills: Optional[List[str]] = None,
    tenant_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> SandboxResult:
    """
    Convenience function for sandbox simulation.

    Args:
        plan: List of steps
        budget_cents: Available budget
        allowed_skills: Optional skill allowlist
        tenant_id: Tenant identifier
        run_id: Run identifier

    Returns:
        SandboxResult
    """
    sandbox = CostSimSandbox(
        budget_cents=budget_cents,
        allowed_skills=allowed_skills,
        tenant_id=tenant_id,
        run_id=run_id,
    )
    return await sandbox.simulate(plan)


# Module-level sandbox instance for convenience
_sandbox_instance: Optional[CostSimSandbox] = None


def get_sandbox(
    budget_cents: int = 1000,
    tenant_id: Optional[str] = None,
) -> CostSimSandbox:
    """
    Get a sandbox instance.

    Note: For tenant isolation, always create a new instance
    with the correct tenant_id rather than using the global.

    Args:
        budget_cents: Available budget
        tenant_id: Tenant identifier

    Returns:
        CostSimSandbox instance
    """
    global _sandbox_instance

    # Always create new instance for tenant isolation
    if tenant_id:
        return CostSimSandbox(
            budget_cents=budget_cents,
            tenant_id=tenant_id,
        )

    # Reuse global instance for non-tenant requests
    if _sandbox_instance is None:
        _sandbox_instance = CostSimSandbox(budget_cents=budget_cents)

    return _sandbox_instance
