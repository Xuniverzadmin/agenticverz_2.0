# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Workflow policy enforcement
# Callers: workflow engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Workflow System
# capability_id: CAP-009

# Policy Enforcer (M4)
"""
Per-step policy enforcement for workflow execution.

Provides:
1. Budget ceiling enforcement (per-step, per-workflow, per-tenant)
2. Rate limit checks
3. Idempotency validation
4. Emergency stop controls

Integrates with existing BudgetTracker from Phase 5.

Design Principles:
- Fail-fast: Reject before execution, not after
- Deterministic: Same inputs produce same policy decisions
- Zero hidden state: All decisions are based on explicit contracts
- Multi-worker safe: Budget tracking via shared store (Redis/DB)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

logger = logging.getLogger("nova.workflow.policies")


# ============================================================================
# Budget Store Protocol (for multi-worker deployments)
# ============================================================================


class BudgetStore(Protocol):
    """Protocol for shared budget storage across workers."""

    async def get_workflow_cost(self, run_id: str) -> int:
        """Get accumulated cost for a workflow."""
        ...

    async def add_workflow_cost(self, run_id: str, cost_cents: int) -> int:
        """Add cost to workflow and return new total."""
        ...

    async def reset_workflow_cost(self, run_id: str) -> None:
        """Reset accumulated costs for a workflow."""
        ...


class InMemoryBudgetStore:
    """In-memory budget store for single-worker or testing."""

    def __init__(self):
        self._workflow_costs: Dict[str, int] = {}

    async def get_workflow_cost(self, run_id: str) -> int:
        return self._workflow_costs.get(run_id, 0)

    async def add_workflow_cost(self, run_id: str, cost_cents: int) -> int:
        current = self._workflow_costs.get(run_id, 0)
        new_total = current + cost_cents
        self._workflow_costs[run_id] = new_total
        return new_total

    async def reset_workflow_cost(self, run_id: str) -> None:
        if run_id in self._workflow_costs:
            del self._workflow_costs[run_id]


class RedisBudgetStore:
    """
    Redis-based budget store for multi-worker deployments.

    Uses Redis INCRBY for atomic cost accumulation.
    Keys expire after 24 hours to prevent unbounded growth.
    """

    KEY_PREFIX = "workflow:cost:"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        """
        Initialize Redis budget store.

        Args:
            redis_url: Redis connection URL. If None, uses REDIS_URL env var.
            ttl_seconds: TTL for cost keys (default 24h)
        """
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._ttl = ttl_seconds
        self._client = None

    async def _get_client(self):
        """Lazy initialize Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as aioredis

                self._client = aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.warning("redis package not available, falling back to in-memory")
                raise
        return self._client

    def _key(self, run_id: str) -> str:
        return f"{self.KEY_PREFIX}{run_id}"

    async def get_workflow_cost(self, run_id: str) -> int:
        try:
            client = await self._get_client()
            value = await client.get(self._key(run_id))
            return int(value) if value else 0
        except Exception as e:
            logger.warning(f"Redis get failed: {e}, returning 0")
            return 0

    async def add_workflow_cost(self, run_id: str, cost_cents: int) -> int:
        """Atomically add cost using INCRBY."""
        try:
            client = await self._get_client()
            key = self._key(run_id)
            new_total = await client.incrby(key, cost_cents)
            # Set TTL on first access
            await client.expire(key, self._ttl)
            return int(new_total)
        except Exception as e:
            logger.warning(f"Redis incrby failed: {e}, returning cost")
            return cost_cents

    async def add_workflow_cost_if_below(self, run_id: str, cost_cents: int, ceiling: int) -> tuple[int, bool]:
        """
        Atomically add cost only if result stays below ceiling.

        Uses Lua script for atomic check-and-increment.

        Args:
            run_id: Workflow run ID
            cost_cents: Cost to add
            ceiling: Maximum allowed total

        Returns:
            Tuple of (new_total, success). If success is False, cost was not added.
        """
        try:
            client = await self._get_client()
            key = self._key(run_id)

            # Lua script for atomic check-and-increment
            lua_script = """
            local current = tonumber(redis.call('GET', KEYS[1]) or '0')
            local cost = tonumber(ARGV[1])
            local ceiling = tonumber(ARGV[2])
            local ttl = tonumber(ARGV[3])

            local projected = current + cost
            if projected > ceiling then
                return {current, 0}  -- Return current total and failure flag
            end

            local new_total = redis.call('INCRBY', KEYS[1], cost)
            redis.call('EXPIRE', KEYS[1], ttl)
            return {new_total, 1}  -- Return new total and success flag
            """

            result = await client.eval(lua_script, 1, key, cost_cents, ceiling, self._ttl)
            new_total = int(result[0])
            success = bool(result[1])
            return (new_total, success)

        except Exception as e:
            logger.warning(f"Redis atomic add failed: {e}, falling back to non-atomic")
            # Fallback to non-atomic check
            current = await self.get_workflow_cost(run_id)
            if current + cost_cents > ceiling:
                return (current, False)
            new_total = await self.add_workflow_cost(run_id, cost_cents)
            return (new_total, True)

    async def reset_workflow_cost(self, run_id: str) -> None:
        try:
            client = await self._get_client()
            await client.delete(self._key(run_id))
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


class BudgetExceededError(Exception):
    """Raised when budget limits are exceeded."""

    def __init__(self, message: str, breach_type: str = "unknown", limit_cents: int = 0, current_cents: int = 0):
        super().__init__(message)
        self.breach_type = breach_type
        self.limit_cents = limit_cents
        self.current_cents = current_cents


class PolicyViolationError(Exception):
    """Raised when a policy is violated."""

    def __init__(self, message: str, policy: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.policy = policy
        self.details = details or {}


@dataclass
class PolicyCheckResult:
    """Result of a policy check."""

    allowed: bool
    reason: Optional[str] = None
    policy: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PolicyEnforcer:
    """
    Policy enforcer for workflow step execution.

    Enforces:
    - Per-step cost ceilings
    - Per-workflow budget limits
    - Per-tenant daily limits
    - Idempotency requirements
    - Emergency stop flags

    Multi-worker safe: Uses pluggable BudgetStore for shared state.

    Usage:
        # Single worker (in-memory)
        enforcer = PolicyEnforcer()

        # Multi-worker (Redis)
        store = RedisBudgetStore()
        enforcer = PolicyEnforcer(budget_store=store)

        await enforcer.check_can_execute(step, ctx, agent_id="agent-123")
    """

    # Configuration from environment
    DEFAULT_STEP_CEILING_CENTS = int(os.getenv("DEFAULT_STEP_CEILING_CENTS", "100"))
    DEFAULT_WORKFLOW_CEILING_CENTS = int(os.getenv("DEFAULT_WORKFLOW_CEILING_CENTS", "1000"))
    EMERGENCY_STOP_ENABLED = os.getenv("WORKFLOW_EMERGENCY_STOP", "false").lower() == "true"

    def __init__(
        self,
        step_ceiling_cents: Optional[int] = None,
        workflow_ceiling_cents: Optional[int] = None,
        require_idempotency: bool = True,
        budget_store: Optional[BudgetStore] = None,
    ):
        """
        Initialize policy enforcer.

        Args:
            step_ceiling_cents: Max cost per step (default from env)
            workflow_ceiling_cents: Max cost per workflow (default from env)
            require_idempotency: Require idempotency_key for non-GET operations
            budget_store: Shared store for budget tracking (default: in-memory)
        """
        self.step_ceiling = step_ceiling_cents or self.DEFAULT_STEP_CEILING_CENTS
        self.workflow_ceiling = workflow_ceiling_cents or self.DEFAULT_WORKFLOW_CEILING_CENTS
        self.require_idempotency = require_idempotency
        self._budget_store = budget_store or InMemoryBudgetStore()
        # Legacy compatibility - keep local dict for sync access
        self._workflow_costs: Dict[str, int] = {}

    async def check_can_execute(
        self,
        step: "StepDescriptor",
        ctx: "StepContext",
        agent_id: Optional[str] = None,
    ) -> PolicyCheckResult:
        """
        Check if step execution is allowed.

        Raises:
            BudgetExceededError: If budget limits exceeded
            PolicyViolationError: If other policy violated

        Returns:
            PolicyCheckResult if allowed
        """
        # 1. Emergency stop check
        if self.EMERGENCY_STOP_ENABLED:
            raise PolicyViolationError(
                "Workflow engine emergency stop is enabled",
                policy="emergency_stop",
            )

        # 2. Per-step ceiling check
        estimated_cost = step.estimated_cost_cents
        if step.max_cost_cents is not None:
            ceiling = step.max_cost_cents
        else:
            ceiling = self.step_ceiling

        if estimated_cost > ceiling:
            raise BudgetExceededError(
                f"Step cost ({estimated_cost}c) exceeds ceiling ({ceiling}c)",
                breach_type="step_ceiling",
                limit_cents=ceiling,
                current_cents=estimated_cost,
            )

        # 3. Per-workflow accumulated cost check (via shared store)
        # Use atomic check-and-increment if available (for race-free budget enforcement)
        run_id = ctx.run_id

        if hasattr(self._budget_store, "add_workflow_cost_if_below"):
            # Atomic check-and-increment (race-safe)
            new_total, success = await self._budget_store.add_workflow_cost_if_below(
                run_id, estimated_cost, self.workflow_ceiling
            )
            if not success:
                raise BudgetExceededError(
                    f"Workflow cost ({new_total + estimated_cost}c) would exceed ceiling ({self.workflow_ceiling}c)",
                    breach_type="workflow_ceiling",
                    limit_cents=self.workflow_ceiling,
                    current_cents=new_total,
                )
            # Update local cache
            self._workflow_costs[run_id] = new_total
        else:
            # Non-atomic fallback (for InMemoryBudgetStore)
            accumulated = await self._budget_store.get_workflow_cost(run_id)
            projected = accumulated + estimated_cost

            if projected > self.workflow_ceiling:
                raise BudgetExceededError(
                    f"Workflow cost ({projected}c) would exceed ceiling ({self.workflow_ceiling}c)",
                    breach_type="workflow_ceiling",
                    limit_cents=self.workflow_ceiling,
                    current_cents=accumulated,
                )
            # Track accumulated cost for this workflow (via shared store)
            await self._budget_store.add_workflow_cost(run_id, estimated_cost)
            # Update local cache
            self._workflow_costs[run_id] = projected

        # 4. Idempotency check for side-effect operations
        if self.require_idempotency:
            method = step.inputs.get("method", "GET").upper()
            if method in ("POST", "PUT", "DELETE", "PATCH") and not step.idempotency_key:
                raise PolicyViolationError(
                    f"Step {step.id} has side-effect method {method} but no idempotency_key",
                    policy="idempotency_required",
                    details={"step_id": step.id, "method": method},
                )

        # 5. Agent budget check (integrate with existing BudgetTracker)
        if agent_id:
            budget_check = await self._check_agent_budget(agent_id, estimated_cost)
            if not budget_check.allowed:
                raise BudgetExceededError(
                    budget_check.reason or "Agent budget exceeded",
                    breach_type="agent_budget",
                    limit_cents=budget_check.details.get("limit_cents", 0) if budget_check.details else 0,
                    current_cents=budget_check.details.get("current_cents", 0) if budget_check.details else 0,
                )

        # Cost tracking already done in step 3 (atomically for Redis, non-atomically for in-memory)
        accumulated = self._workflow_costs.get(run_id, 0)
        logger.debug(
            "policy_check_passed",
            extra={
                "step_id": step.id,
                "run_id": run_id,
                "estimated_cost": estimated_cost,
                "accumulated_cost": accumulated,
            },
        )

        return PolicyCheckResult(allowed=True)

    async def _check_agent_budget(
        self,
        agent_id: str,
        estimated_cost: int,
    ) -> PolicyCheckResult:
        """
        Check agent budget using existing BudgetTracker.

        Returns:
            PolicyCheckResult with allowed status
        """
        try:
            from app.utils.budget_tracker import BudgetCheckResult, enforce_budget

            result: BudgetCheckResult = enforce_budget(
                agent_id=agent_id,
                estimated_cost_cents=estimated_cost,
            )

            if result.allowed:
                return PolicyCheckResult(allowed=True)
            else:
                return PolicyCheckResult(
                    allowed=False,
                    reason=result.reason,
                    policy="agent_budget",
                    details={
                        "breach_type": result.breach_type,
                        "limit_cents": result.limit_cents,
                        "current_cents": result.current_cents,
                    },
                )

        except ImportError:
            # BudgetTracker not available, allow by default
            logger.warning("BudgetTracker not available, skipping agent budget check")
            return PolicyCheckResult(allowed=True)
        except Exception as e:
            # Log but don't block on budget check failures
            logger.error(f"Agent budget check failed: {e}")
            return PolicyCheckResult(allowed=True)

    def can_retry(self, step: "StepDescriptor", ctx: "StepContext") -> bool:
        """
        Check if step can be retried.

        Deterministic based on step configuration.
        """
        return step.retry and step.max_retries > 0

    async def record_step_cost_async(self, run_id: str, cost_cents: int) -> None:
        """
        Record actual step cost (for post-execution tracking, async).

        Args:
            run_id: Workflow run ID
            cost_cents: Actual cost incurred
        """
        await self._budget_store.add_workflow_cost(run_id, cost_cents)
        # Update local cache
        current = self._workflow_costs.get(run_id, 0)
        self._workflow_costs[run_id] = current + cost_cents

    def record_step_cost(self, run_id: str, cost_cents: int) -> None:
        """
        Record actual step cost (for post-execution tracking, sync).

        Note: This only updates local cache. Use record_step_cost_async
        for shared store updates in multi-worker deployments.

        Args:
            run_id: Workflow run ID
            cost_cents: Actual cost incurred
        """
        current = self._workflow_costs.get(run_id, 0)
        self._workflow_costs[run_id] = current + cost_cents

    async def reset_workflow_costs_async(self, run_id: str) -> None:
        """
        Reset accumulated costs for a workflow (async, for shared store).

        Args:
            run_id: Workflow run ID
        """
        await self._budget_store.reset_workflow_cost(run_id)
        if run_id in self._workflow_costs:
            del self._workflow_costs[run_id]

    def reset_workflow_costs(self, run_id: str) -> None:
        """
        Reset accumulated costs for a workflow (sync, local cache only).

        Note: This only updates local cache. Use reset_workflow_costs_async
        for shared store updates in multi-worker deployments.

        Args:
            run_id: Workflow run ID
        """
        if run_id in self._workflow_costs:
            del self._workflow_costs[run_id]

    async def get_workflow_cost_async(self, run_id: str) -> int:
        """
        Get accumulated cost for a workflow from shared store.

        Args:
            run_id: Workflow run ID

        Returns:
            Accumulated cost in cents
        """
        return await self._budget_store.get_workflow_cost(run_id)

    def get_workflow_cost(self, run_id: str) -> int:
        """
        Get accumulated cost for a workflow from local cache.

        Note: In multi-worker deployments, use get_workflow_cost_async
        for accurate cross-worker totals.

        Args:
            run_id: Workflow run ID

        Returns:
            Accumulated cost in cents (from local cache)
        """
        return self._workflow_costs.get(run_id, 0)


# Import dependencies at end to avoid circular imports
from .engine import StepContext, StepDescriptor
