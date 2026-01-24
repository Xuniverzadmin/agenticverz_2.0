# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: runtime
#   Execution: sync
# Role: Core limits evaluation engine (PIN-LIM-03)
# Callers: services/limits/simulation_service.py, worker/runtime/*
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Evaluation Order Contract (Section B)

"""
Limits Evaluator (PIN-LIM-03)

The single deterministic decision engine for all limit checks.
This is the CRITICAL piece that makes limits enforcement work.

Evaluation Order (HARD → SOFT):
1. Tenant Quotas (HARD, PLAN-LOCKED)
2. Active Overrides (TEMPORARY MUTATION)
3. Policy Limits (HARD unless advisory)
4. Worker Limits (HARD)
5. Cost Budgets (SOFT by default, HARD if flagged)

Algorithm (Normative):
- FOR each limit_group IN ordered_groups:
    - resolve_effective_limit(limit_group, overrides)
    - IF limit_group.is_hard:
        - IF projected_usage > allowed:
            - RETURN BLOCK(limit_id, reason_code, remaining=allowed - current)
    - IF limit_group.is_soft:
        - IF projected_usage > allowed:
            - record_warning(limit_id)

Rules:
- First HARD failure terminates evaluation
- No free-text messages (message codes only)
- Same input → same output (idempotent)
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.schemas.limits.simulation import (
    HeadroomInfo,
    LimitCheckResult,
    LimitWarning,
    MessageCode,
    SimulationDecision,
)


class LimitGroup(str, Enum):
    """Limit groups in evaluation order."""
    TENANT_QUOTAS = "TENANT_QUOTAS"       # 1. HARD, PLAN-LOCKED
    ACTIVE_OVERRIDES = "ACTIVE_OVERRIDES" # 2. TEMPORARY MUTATION
    POLICY_LIMITS = "POLICY_LIMITS"       # 3. HARD unless advisory
    WORKER_LIMITS = "WORKER_LIMITS"       # 4. HARD
    COST_BUDGETS = "COST_BUDGETS"         # 5. SOFT by default


# Evaluation order (DO NOT CHANGE)
EVALUATION_ORDER = [
    LimitGroup.TENANT_QUOTAS,
    LimitGroup.POLICY_LIMITS,
    LimitGroup.WORKER_LIMITS,
    LimitGroup.COST_BUDGETS,
]


@dataclass
class ExecutionIntent:
    """Input: what the caller intends to execute."""
    tenant_id: str
    estimated_tokens: int
    estimated_cost_cents: int = 0
    run_count: int = 1
    concurrency_delta: int = 1
    worker_id: Optional[str] = None
    feature_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class TenantQuotas:
    """Current tenant quota state."""
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    runs_today: int
    concurrent_runs: int
    tokens_this_month: int


@dataclass
class CostBudget:
    """Cost budget state."""
    budget_id: str
    budget_type: str  # tenant, feature, user
    daily_limit_cents: int
    monthly_limit_cents: int
    current_daily_spend: int
    current_monthly_spend: int
    hard_limit_enabled: bool


@dataclass
class PolicyLimit:
    """Policy limit state."""
    limit_id: str
    name: str
    limit_category: str  # BUDGET, RATE, THRESHOLD
    limit_type: str
    max_value: Decimal
    current_value: Decimal
    enforcement: str  # BLOCK, WARN, etc.
    scope: str
    scope_id: Optional[str] = None


@dataclass
class WorkerLimit:
    """Worker-specific limit state."""
    worker_id: str
    max_runs_per_day: int
    max_tokens_per_run: int
    runs_today: int


@dataclass
class ActiveOverride:
    """Active override state."""
    override_id: str
    limit_id: str
    original_value: Decimal
    override_value: Decimal


@dataclass
class EvaluationContext:
    """All data needed for evaluation."""
    intent: ExecutionIntent
    tenant_quotas: TenantQuotas
    cost_budgets: list[CostBudget] = field(default_factory=list)
    policy_limits: list[PolicyLimit] = field(default_factory=list)
    worker_limits: Optional[WorkerLimit] = None
    active_overrides: list[ActiveOverride] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Output: evaluation decision."""
    decision: SimulationDecision
    blocking_limit_id: Optional[str] = None
    blocking_limit_type: Optional[str] = None
    blocking_message_code: Optional[MessageCode] = None
    warnings: list[LimitWarning] = field(default_factory=list)
    headroom: Optional[HeadroomInfo] = None
    checks: list[LimitCheckResult] = field(default_factory=list)
    overrides_applied: list[str] = field(default_factory=list)


class LimitsEvaluator:
    """
    Core limits evaluation engine.

    Provides deterministic evaluation of all limits for an execution intent.
    Used by both simulation API and runtime enforcement.

    INVARIANTS:
    - Same input → same output (idempotent)
    - First HARD failure terminates evaluation
    - No free-text messages (message codes only)
    - Evaluation order is fixed and MUST NOT change
    """

    def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """
        Evaluate all limits against the execution intent.

        Returns EvaluationResult with decision, blocking limit (if any),
        warnings, headroom, and detailed check results.
        """
        result = EvaluationResult(decision=SimulationDecision.ALLOW)
        result.checks = []
        result.warnings = []
        result.overrides_applied = []

        # Build override lookup
        override_map = {o.limit_id: o for o in context.active_overrides}
        result.overrides_applied = [o.override_id for o in context.active_overrides]

        # 1. Evaluate Tenant Quotas (HARD)
        quota_result = self._evaluate_tenant_quotas(context)
        result.checks.extend(quota_result.checks)
        if quota_result.decision == SimulationDecision.BLOCK:
            return self._finalize_block(result, quota_result)

        # 2. Evaluate Policy Limits (HARD unless advisory)
        policy_result = self._evaluate_policy_limits(context, override_map)
        result.checks.extend(policy_result.checks)
        result.warnings.extend(policy_result.warnings)
        if policy_result.decision == SimulationDecision.BLOCK:
            return self._finalize_block(result, policy_result)

        # 3. Evaluate Worker Limits (HARD)
        if context.worker_limits:
            worker_result = self._evaluate_worker_limits(context)
            result.checks.extend(worker_result.checks)
            if worker_result.decision == SimulationDecision.BLOCK:
                return self._finalize_block(result, worker_result)

        # 4. Evaluate Cost Budgets (SOFT by default)
        budget_result = self._evaluate_cost_budgets(context)
        result.checks.extend(budget_result.checks)
        result.warnings.extend(budget_result.warnings)
        if budget_result.decision == SimulationDecision.BLOCK:
            return self._finalize_block(result, budget_result)

        # Calculate headroom
        result.headroom = self._calculate_headroom(context)

        # Set final decision
        if result.warnings:
            result.decision = SimulationDecision.WARN
        else:
            result.decision = SimulationDecision.ALLOW

        return result

    def _evaluate_tenant_quotas(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate tenant quotas (HARD limits)."""
        result = EvaluationResult(decision=SimulationDecision.ALLOW)
        result.checks = []
        intent = context.intent
        quotas = context.tenant_quotas

        # Check daily run limit
        projected_runs = quotas.runs_today + intent.run_count
        if projected_runs > quotas.max_runs_per_day:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="DAILY_RUNS",
                limit_name="Daily Run Limit",
                current_value=Decimal(quotas.runs_today),
                limit_value=Decimal(quotas.max_runs_per_day),
                projected_value=Decimal(projected_runs),
                enforcement="BLOCK",
                decision=SimulationDecision.BLOCK,
                message_code=MessageCode.DAILY_RUN_LIMIT_EXCEEDED,
            ))
            result.decision = SimulationDecision.BLOCK
            result.blocking_limit_type = "DAILY_RUNS"
            result.blocking_message_code = MessageCode.DAILY_RUN_LIMIT_EXCEEDED
            return result
        else:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="DAILY_RUNS",
                limit_name="Daily Run Limit",
                current_value=Decimal(quotas.runs_today),
                limit_value=Decimal(quotas.max_runs_per_day),
                projected_value=Decimal(projected_runs),
                enforcement="BLOCK",
                decision=SimulationDecision.ALLOW,
                message_code=MessageCode.DAILY_RUN_LIMIT_EXCEEDED,
            ))

        # Check concurrent run limit
        projected_concurrent = quotas.concurrent_runs + intent.concurrency_delta
        if projected_concurrent > quotas.max_concurrent_runs:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="CONCURRENT_RUNS",
                limit_name="Concurrent Run Limit",
                current_value=Decimal(quotas.concurrent_runs),
                limit_value=Decimal(quotas.max_concurrent_runs),
                projected_value=Decimal(projected_concurrent),
                enforcement="BLOCK",
                decision=SimulationDecision.BLOCK,
                message_code=MessageCode.CONCURRENT_RUN_LIMIT_EXCEEDED,
            ))
            result.decision = SimulationDecision.BLOCK
            result.blocking_limit_type = "CONCURRENT_RUNS"
            result.blocking_message_code = MessageCode.CONCURRENT_RUN_LIMIT_EXCEEDED
            return result
        else:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="CONCURRENT_RUNS",
                limit_name="Concurrent Run Limit",
                current_value=Decimal(quotas.concurrent_runs),
                limit_value=Decimal(quotas.max_concurrent_runs),
                projected_value=Decimal(projected_concurrent),
                enforcement="BLOCK",
                decision=SimulationDecision.ALLOW,
                message_code=MessageCode.CONCURRENT_RUN_LIMIT_EXCEEDED,
            ))

        # Check monthly token limit
        projected_tokens = quotas.tokens_this_month + intent.estimated_tokens
        if projected_tokens > quotas.max_tokens_per_month:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="MONTHLY_TOKENS",
                limit_name="Monthly Token Limit",
                current_value=Decimal(quotas.tokens_this_month),
                limit_value=Decimal(quotas.max_tokens_per_month),
                projected_value=Decimal(projected_tokens),
                enforcement="BLOCK",
                decision=SimulationDecision.BLOCK,
                message_code=MessageCode.MONTHLY_TOKEN_LIMIT_EXCEEDED,
            ))
            result.decision = SimulationDecision.BLOCK
            result.blocking_limit_type = "MONTHLY_TOKENS"
            result.blocking_message_code = MessageCode.MONTHLY_TOKEN_LIMIT_EXCEEDED
            return result
        else:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="MONTHLY_TOKENS",
                limit_name="Monthly Token Limit",
                current_value=Decimal(quotas.tokens_this_month),
                limit_value=Decimal(quotas.max_tokens_per_month),
                projected_value=Decimal(projected_tokens),
                enforcement="BLOCK",
                decision=SimulationDecision.ALLOW,
                message_code=MessageCode.MONTHLY_TOKEN_LIMIT_EXCEEDED,
            ))

        return result

    def _evaluate_policy_limits(
        self,
        context: EvaluationContext,
        override_map: dict[str, ActiveOverride],
    ) -> EvaluationResult:
        """Evaluate policy limits with override application."""
        result = EvaluationResult(decision=SimulationDecision.ALLOW)
        result.checks = []
        result.warnings = []

        for limit in context.policy_limits:
            # Apply override if exists
            effective_max = limit.max_value
            if limit.limit_id in override_map:
                override = override_map[limit.limit_id]
                effective_max = override.override_value

            # Calculate projected value based on limit type
            projected = self._project_limit_value(limit, context.intent)

            # Check if limit would be breached
            is_breached = projected > effective_max
            is_hard = limit.enforcement in ("BLOCK", "REJECT")

            check_result = LimitCheckResult(
                limit_id=limit.limit_id,
                limit_type=limit.limit_type,
                limit_name=limit.name,
                current_value=limit.current_value,
                limit_value=effective_max,
                projected_value=projected,
                enforcement=limit.enforcement,
                decision=SimulationDecision.BLOCK if (is_breached and is_hard) else SimulationDecision.ALLOW,
                message_code=MessageCode.POLICY_LIMIT_BREACHED,
            )
            result.checks.append(check_result)

            if is_breached:
                if is_hard:
                    result.decision = SimulationDecision.BLOCK
                    result.blocking_limit_id = limit.limit_id
                    result.blocking_limit_type = limit.limit_type
                    result.blocking_message_code = MessageCode.POLICY_LIMIT_BREACHED
                    return result
                else:
                    # Soft limit - add warning
                    result.warnings.append(LimitWarning(
                        limit_id=limit.limit_id,
                        limit_type=limit.limit_type,
                        message_code=MessageCode.LIMIT_APPROACHING,
                        current_percent=float(limit.current_value / effective_max * 100) if effective_max > 0 else 0,
                    ))

        return result

    def _evaluate_worker_limits(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate worker-specific limits (HARD)."""
        result = EvaluationResult(decision=SimulationDecision.ALLOW)
        result.checks = []
        intent = context.intent
        worker = context.worker_limits

        if not worker:
            return result

        # Check worker daily run limit
        projected_runs = worker.runs_today + intent.run_count
        if projected_runs > worker.max_runs_per_day:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="WORKER_DAILY_RUNS",
                limit_name=f"Worker {worker.worker_id} Daily Limit",
                current_value=Decimal(worker.runs_today),
                limit_value=Decimal(worker.max_runs_per_day),
                projected_value=Decimal(projected_runs),
                enforcement="BLOCK",
                decision=SimulationDecision.BLOCK,
                message_code=MessageCode.WORKER_DAILY_LIMIT_EXCEEDED,
            ))
            result.decision = SimulationDecision.BLOCK
            result.blocking_limit_type = "WORKER_DAILY_RUNS"
            result.blocking_message_code = MessageCode.WORKER_DAILY_LIMIT_EXCEEDED
            return result

        # Check worker token limit per run
        if intent.estimated_tokens > worker.max_tokens_per_run:
            result.checks.append(LimitCheckResult(
                limit_id=None,
                limit_type="WORKER_TOKEN_LIMIT",
                limit_name=f"Worker {worker.worker_id} Token Limit",
                current_value=Decimal(0),
                limit_value=Decimal(worker.max_tokens_per_run),
                projected_value=Decimal(intent.estimated_tokens),
                enforcement="BLOCK",
                decision=SimulationDecision.BLOCK,
                message_code=MessageCode.WORKER_TOKEN_LIMIT_EXCEEDED,
            ))
            result.decision = SimulationDecision.BLOCK
            result.blocking_limit_type = "WORKER_TOKEN_LIMIT"
            result.blocking_message_code = MessageCode.WORKER_TOKEN_LIMIT_EXCEEDED
            return result

        return result

    def _evaluate_cost_budgets(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate cost budgets (SOFT by default, HARD if flagged)."""
        result = EvaluationResult(decision=SimulationDecision.ALLOW)
        result.checks = []
        result.warnings = []
        intent = context.intent

        for budget in context.cost_budgets:
            # Check daily budget
            projected_daily = budget.current_daily_spend + intent.estimated_cost_cents
            if projected_daily > budget.daily_limit_cents:
                check_result = LimitCheckResult(
                    limit_id=budget.budget_id,
                    limit_type=f"{budget.budget_type.upper()}_DAILY_COST",
                    limit_name=f"{budget.budget_type.title()} Daily Cost Budget",
                    current_value=Decimal(budget.current_daily_spend),
                    limit_value=Decimal(budget.daily_limit_cents),
                    projected_value=Decimal(projected_daily),
                    enforcement="BLOCK" if budget.hard_limit_enabled else "WARN",
                    decision=SimulationDecision.BLOCK if budget.hard_limit_enabled else SimulationDecision.WARN,
                    message_code=MessageCode.DAILY_COST_BUDGET_EXCEEDED,
                )
                result.checks.append(check_result)

                if budget.hard_limit_enabled:
                    result.decision = SimulationDecision.BLOCK
                    result.blocking_limit_id = budget.budget_id
                    result.blocking_limit_type = f"{budget.budget_type.upper()}_DAILY_COST"
                    result.blocking_message_code = MessageCode.DAILY_COST_BUDGET_EXCEEDED
                    return result
                else:
                    result.warnings.append(LimitWarning(
                        limit_id=budget.budget_id,
                        limit_type=f"{budget.budget_type.upper()}_DAILY_COST",
                        message_code=MessageCode.DAILY_COST_BUDGET_EXCEEDED,
                        current_percent=float(budget.current_daily_spend / budget.daily_limit_cents * 100) if budget.daily_limit_cents > 0 else 0,
                    ))

            # Check monthly budget
            projected_monthly = budget.current_monthly_spend + intent.estimated_cost_cents
            if projected_monthly > budget.monthly_limit_cents:
                check_result = LimitCheckResult(
                    limit_id=budget.budget_id,
                    limit_type=f"{budget.budget_type.upper()}_MONTHLY_COST",
                    limit_name=f"{budget.budget_type.title()} Monthly Cost Budget",
                    current_value=Decimal(budget.current_monthly_spend),
                    limit_value=Decimal(budget.monthly_limit_cents),
                    projected_value=Decimal(projected_monthly),
                    enforcement="BLOCK" if budget.hard_limit_enabled else "WARN",
                    decision=SimulationDecision.BLOCK if budget.hard_limit_enabled else SimulationDecision.WARN,
                    message_code=MessageCode.MONTHLY_COST_BUDGET_EXCEEDED,
                )
                result.checks.append(check_result)

                if budget.hard_limit_enabled:
                    result.decision = SimulationDecision.BLOCK
                    result.blocking_limit_id = budget.budget_id
                    result.blocking_limit_type = f"{budget.budget_type.upper()}_MONTHLY_COST"
                    result.blocking_message_code = MessageCode.MONTHLY_COST_BUDGET_EXCEEDED
                    return result
                else:
                    result.warnings.append(LimitWarning(
                        limit_id=budget.budget_id,
                        limit_type=f"{budget.budget_type.upper()}_MONTHLY_COST",
                        message_code=MessageCode.MONTHLY_COST_BUDGET_EXCEEDED,
                        current_percent=float(budget.current_monthly_spend / budget.monthly_limit_cents * 100) if budget.monthly_limit_cents > 0 else 0,
                    ))

        return result

    def _project_limit_value(self, limit: PolicyLimit, intent: ExecutionIntent) -> Decimal:
        """Project the value after execution based on limit type."""
        current = limit.current_value

        # Map limit types to intent fields
        if "TOKEN" in limit.limit_type.upper():
            return current + Decimal(intent.estimated_tokens)
        elif "COST" in limit.limit_type.upper():
            return current + Decimal(intent.estimated_cost_cents)
        elif "RUN" in limit.limit_type.upper() or "REQUEST" in limit.limit_type.upper():
            return current + Decimal(intent.run_count)
        else:
            # Default: assume run count
            return current + Decimal(intent.run_count)

    def _calculate_headroom(self, context: EvaluationContext) -> HeadroomInfo:
        """Calculate remaining capacity before hitting limits."""
        quotas = context.tenant_quotas

        # Token headroom
        token_headroom = max(0, quotas.max_tokens_per_month - quotas.tokens_this_month)

        # Run headroom
        run_headroom = max(0, quotas.max_runs_per_day - quotas.runs_today)

        # Concurrent run headroom
        concurrent_headroom = max(0, quotas.max_concurrent_runs - quotas.concurrent_runs)

        # Cost headroom (from all budgets)
        cost_headroom = float("inf")
        for budget in context.cost_budgets:
            daily_remaining = budget.daily_limit_cents - budget.current_daily_spend
            monthly_remaining = budget.monthly_limit_cents - budget.current_monthly_spend
            cost_headroom = min(cost_headroom, daily_remaining, monthly_remaining)
        if cost_headroom == float("inf"):
            cost_headroom = 0

        return HeadroomInfo(
            tokens=token_headroom,
            cost_cents=int(cost_headroom),
            runs=run_headroom,
            concurrent_runs=concurrent_headroom,
        )

    def _finalize_block(
        self,
        result: EvaluationResult,
        blocking_result: EvaluationResult,
    ) -> EvaluationResult:
        """Finalize a BLOCK result by copying blocking info."""
        result.decision = SimulationDecision.BLOCK
        result.blocking_limit_id = blocking_result.blocking_limit_id
        result.blocking_limit_type = blocking_result.blocking_limit_type
        result.blocking_message_code = blocking_result.blocking_message_code
        return result
