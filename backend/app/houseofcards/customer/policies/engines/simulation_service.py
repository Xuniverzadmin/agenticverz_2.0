# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Limits simulation service (PIN-LIM-04)
# Callers: api/limits/simulate.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-LIM-04

"""
Limits Simulation Service (PIN-LIM-04)

Coordination layer for pre-execution limit checks.

Responsibilities:
- Aggregate all limit types (tenant quotas, cost budgets, worker limits, policy limits)
- Load active overrides
- Call evaluator
- Normalize response for API
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import Limit, LimitStatus
from app.models.tenant import Tenant
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
from app.runtime.limits.override_resolver import OverrideRecord, OverrideResolver
from app.schemas.limits.simulation import (
    LimitSimulationRequest,
    LimitSimulationResponse,
    SimulationDecision,
)


class LimitsSimulationServiceError(Exception):
    """Base exception for simulation service."""
    pass


class TenantNotFoundError(LimitsSimulationServiceError):
    """Raised when tenant is not found."""
    pass


class LimitsSimulationService:
    """
    Service for pre-execution limit simulation.

    Aggregates data from multiple sources and uses the evaluator
    to determine if an execution would be allowed.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.evaluator = LimitsEvaluator()
        self.override_resolver = OverrideResolver()

    async def simulate(
        self,
        tenant_id: str,
        request: LimitSimulationRequest,
    ) -> LimitSimulationResponse:
        """
        Simulate an execution against all limits.

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
        result = self.evaluator.evaluate(context)

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

    async def _build_context(
        self,
        tenant_id: str,
        request: LimitSimulationRequest,
    ) -> EvaluationContext:
        """Build full evaluation context from database."""
        # Load tenant quotas
        tenant_quotas = await self._load_tenant_quotas(tenant_id)

        # Load cost budgets
        cost_budgets = await self._load_cost_budgets(tenant_id, request)

        # Load policy limits
        policy_limits = await self._load_policy_limits(tenant_id, request)

        # Load worker limits (if worker specified)
        worker_limits = None
        if request.worker_id:
            worker_limits = await self._load_worker_limits(tenant_id, request.worker_id)

        # Load active overrides
        active_overrides = await self._load_active_overrides(tenant_id)

        # Estimate cost if not provided
        estimated_cost = request.estimated_cost_cents or 0
        if estimated_cost == 0 and request.estimated_tokens > 0:
            # Simple cost estimation: $0.01 per 1000 tokens
            estimated_cost = int(request.estimated_tokens / 1000 * 1)  # 1 cent per 1K

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

    async def _load_tenant_quotas(self, tenant_id: str) -> TenantQuotas:
        """Load tenant quota information."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        # For concurrent runs, we need to count active runs
        # This is a simplified version - in production, query runs table
        concurrent_runs = 0

        return TenantQuotas(
            max_runs_per_day=tenant.max_runs_per_day,
            max_concurrent_runs=tenant.max_concurrent_runs,
            max_tokens_per_month=tenant.max_tokens_per_month,
            runs_today=tenant.runs_today,
            concurrent_runs=concurrent_runs,
            tokens_this_month=tenant.tokens_this_month,
        )

    async def _load_cost_budgets(
        self,
        tenant_id: str,
        request: LimitSimulationRequest,
    ) -> list[CostBudget]:
        """Load applicable cost budgets."""
        # This would query the cost_budgets table
        # Simplified for now - return empty list
        # TODO: Query cost_budgets table when implemented
        return []

    async def _load_policy_limits(
        self,
        tenant_id: str,
        request: LimitSimulationRequest,
    ) -> list[PolicyLimit]:
        """Load applicable policy limits."""
        stmt = select(Limit).where(
            and_(
                Limit.tenant_id == tenant_id,
                Limit.status == LimitStatus.ACTIVE.value,
            )
        )
        result = await self.session.execute(stmt)
        limits = result.scalars().all()

        policy_limits = []
        for limit in limits:
            # Calculate current value based on limit type
            # This is simplified - in production, query actual usage
            current_value = Decimal(0)

            policy_limits.append(PolicyLimit(
                limit_id=limit.id,
                name=limit.name,
                limit_category=limit.limit_category,
                limit_type=limit.limit_type,
                max_value=limit.max_value,
                current_value=current_value,
                enforcement=limit.enforcement,
                scope=limit.scope,
                scope_id=limit.scope_id,
            ))

        return policy_limits

    async def _load_worker_limits(
        self,
        tenant_id: str,
        worker_id: str,
    ) -> Optional[WorkerLimit]:
        """Load worker-specific limits."""
        # This would query the workers/worker_configs table
        # Simplified for now - return None
        # TODO: Query worker config when implementing
        return None

    async def _load_active_overrides(self, tenant_id: str) -> list[ActiveOverride]:
        """Load active limit overrides."""
        # This would query the limit_overrides table
        # Simplified for now - return empty list
        # TODO: Query limit_overrides table when migration is created
        return []
