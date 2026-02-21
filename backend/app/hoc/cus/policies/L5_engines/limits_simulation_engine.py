# capability_id: CAP-009
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Limits Simulation Engine (PIN-LIM-04)
"""Limits Simulation Engine (PIN-LIM-04)

L4 engine for pre-execution limit simulation.

Decides: Cost estimation, context assembly, response normalization
Delegates: Data access to LimitsSimulationDriver, evaluation to LimitsEvaluator
"""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from app.runtime.limits.evaluator import (
    ActiveOverride,
    CostBudget,
    EvaluationContext,
    ExecutionIntent,
    LimitsEvaluator,
    PolicyLimit,
    TenantQuotas,
    WorkerLimit,
)
from app.schemas.limits.simulation import (
    LimitSimulationRequest,
    LimitSimulationResponse,
)
from app.hoc.cus.policies.L6_drivers.limits_simulation_driver import (
    LimitsSimulationDriver,
    get_limits_simulation_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class LimitsSimulationServiceError(Exception):
    """Base exception for simulation engine."""

    pass


class TenantNotFoundError(LimitsSimulationServiceError):
    """Raised when tenant is not found."""

    pass


class LimitsSimulationEngine:
    """L4 engine for pre-execution limit simulation.

    Decides: Cost estimation, context assembly
    Delegates: Data access to driver, evaluation to evaluator
    """

    # Cost estimation: $0.01 per 1000 tokens (1 cent per 1K)
    COST_PER_1K_TOKENS_CENTS = 1

    def __init__(self, driver: LimitsSimulationDriver):
        """Initialize engine with driver.

        Args:
            driver: LimitsSimulationDriver for data access
        """
        self._driver = driver
        self._evaluator = LimitsEvaluator()

    # =========================================================================
    # MAIN SIMULATION
    # =========================================================================

    async def simulate(
        self,
        tenant_id: str,
        request: LimitSimulationRequest,
    ) -> LimitSimulationResponse:
        """Simulate an execution against all limits.

        DECISION LOGIC:
        1. Build evaluation context from driver data
        2. Estimate cost if not provided
        3. Run evaluator
        4. Convert to response

        Args:
            tenant_id: Tenant to simulate for
            request: Simulation request with execution intent

        Returns:
            Simulation response with decision and details

        Raises:
            TenantNotFoundError: If tenant not found
        """
        # Build evaluation context
        context = await self._build_context(tenant_id, request)

        # Run evaluation
        result = self._evaluator.evaluate(context)

        # Convert to response
        return LimitSimulationResponse(
            decision=result.decision,
            blocking_limit_id=result.blocking_limit_id,
            blocking_limit_type=result.blocking_limit_type,
            blocking_message_code=result.blocking_message_code,
            warnings=result.warnings,
            headroom=result.headroom,
            checks=result.checks,
            overrides_applied=result.overrides_applied,
        )

    # =========================================================================
    # CONTEXT BUILDING
    # =========================================================================

    async def _build_context(
        self,
        tenant_id: str,
        request: LimitSimulationRequest,
    ) -> EvaluationContext:
        """Build full evaluation context from driver data.

        DECISION LOGIC:
        - Estimate cost if not provided
        - Load all limit types from driver
        - Assemble evaluation context

        Args:
            tenant_id: Tenant ID
            request: Simulation request

        Returns:
            EvaluationContext for evaluator
        """
        # Load tenant quotas
        tenant_quotas = await self._load_tenant_quotas(tenant_id)

        # Load cost budgets
        cost_budgets = await self._load_cost_budgets(tenant_id)

        # Load policy limits
        policy_limits = await self._load_policy_limits(tenant_id)

        # Load worker limits (if worker specified)
        worker_limits = None
        if request.worker_id:
            worker_limits = await self._load_worker_limits(tenant_id, request.worker_id)

        # Load active overrides
        active_overrides = await self._load_active_overrides(tenant_id)

        # DECISION: Estimate cost if not provided
        estimated_cost = request.estimated_cost_cents or 0
        if estimated_cost == 0 and request.estimated_tokens > 0:
            estimated_cost = self._estimate_cost(request.estimated_tokens)

        # Build intent
        intent = ExecutionIntent(
            tenant_id=tenant_id,
            estimated_tokens=request.estimated_tokens,
            estimated_cost_cents=estimated_cost,
            run_count=request.run_count,
            concurrency_delta=request.concurrency_delta,
            worker_id=request.worker_id,
            feature_id=request.feature_id,
            user_id=request.user_id,
            project_id=request.project_id,
        )

        return EvaluationContext(
            intent=intent,
            tenant_quotas=tenant_quotas,
            cost_budgets=cost_budgets,
            policy_limits=policy_limits,
            worker_limits=worker_limits,
            active_overrides=active_overrides,
        )

    def _estimate_cost(self, tokens: int) -> int:
        """Estimate cost from token count.

        DECISION: Simple linear estimation

        Args:
            tokens: Estimated tokens

        Returns:
            Estimated cost in cents
        """
        return int(tokens / 1000 * self.COST_PER_1K_TOKENS_CENTS)

    # =========================================================================
    # DATA LOADING (Delegates to driver)
    # =========================================================================

    async def _load_tenant_quotas(self, tenant_id: str) -> TenantQuotas:
        """Load tenant quota information."""
        quota_row = await self._driver.fetch_tenant_quotas(tenant_id)

        if not quota_row:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        # For concurrent runs, we would need to count active runs
        # This is a simplified version
        concurrent_runs = 0

        return TenantQuotas(
            max_runs_per_day=quota_row.max_runs_per_day,
            max_concurrent_runs=quota_row.max_concurrent_runs,
            max_tokens_per_month=quota_row.max_tokens_per_month,
            runs_today=quota_row.runs_today,
            concurrent_runs=concurrent_runs,
            tokens_this_month=quota_row.tokens_this_month,
        )

    async def _load_cost_budgets(self, tenant_id: str) -> List[CostBudget]:
        """Load applicable cost budgets."""
        # Stubbed in driver - returns empty list
        return []

    async def _load_policy_limits(self, tenant_id: str) -> List[PolicyLimit]:
        """Load applicable policy limits."""
        limit_rows = await self._driver.fetch_policy_limits(tenant_id)

        policy_limits = []
        for row in limit_rows:
            # Current value would need separate usage query
            current_value = Decimal(0)

            policy_limits.append(
                PolicyLimit(
                    limit_id=row.limit_id,
                    name=row.name,
                    limit_category=row.limit_category,
                    limit_type=row.limit_type,
                    max_value=row.max_value,
                    current_value=current_value,
                    enforcement=row.enforcement,
                    scope=row.scope,
                    scope_id=row.scope_id,
                )
            )

        return policy_limits

    async def _load_worker_limits(
        self,
        tenant_id: str,
        worker_id: str,
    ) -> Optional[WorkerLimit]:
        """Load worker-specific limits."""
        # Stubbed in driver - returns None
        return None

    async def _load_active_overrides(self, tenant_id: str) -> List[ActiveOverride]:
        """Load active limit overrides."""
        # Stubbed in driver - returns empty list
        return []


# Factory function
def get_limits_simulation_engine(session: "AsyncSession") -> LimitsSimulationEngine:
    """Get engine instance with driver.

    Args:
        session: AsyncSession for driver

    Returns:
        LimitsSimulationEngine instance
    """
    driver = get_limits_simulation_driver(session)
    return LimitsSimulationEngine(driver=driver)

