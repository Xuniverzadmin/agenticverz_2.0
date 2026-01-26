# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: LimitEnforcer contract - defines interface for limit enforcement
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: limit_hook.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, sqlalchemy
# Reference: SWEEP-03 (GAP-055)
#
# GOVERNANCE NOTE:
# This is the CONTRACT for LimitEnforcer.
# Implementation follows in limit_enforcer.py.
# Contract defines ONLY what limit_hook.py requires TODAY.

"""
LimitEnforcer Contract (GAP-055)

PURPOSE:
    Pre-step limit checks for cost, token, and rate limits.
    Called by limit_hook.py before step execution.

INTERFACE:
    - check_cost_limit(tenant_id, estimated_cost) -> LimitCheckResponse
    - check_token_limit(tenant_id, estimated_tokens) -> LimitCheckResponse
    - check_rate_limit(tenant_id, operation) -> LimitCheckResponse

INVARIANTS:
    - All methods are async
    - All methods return LimitCheckResponse (never raise for limit violations)
    - No state mutation (read-only checks)
    - No time/UUID generation
    - No calls to UsageMonitor (that's Module 2)
"""

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


# =============================================================================
# Response Types
# =============================================================================


@dataclass(frozen=True)
class LimitCheckResponse:
    """Response from a limit check operation.

    Attributes:
        exceeded: True if limit is exceeded (should block)
        current_usage: Current usage value
        max_allowed: Maximum allowed value (0 means unlimited)
        warning: True if approaching limit (optional soft warning)
        policy_id: ID of the policy that set this limit (optional)
    """
    exceeded: bool
    current_usage: float
    max_allowed: float
    warning: bool = False
    policy_id: Optional[str] = None

    @classmethod
    def allow(cls) -> "LimitCheckResponse":
        """Factory for allowed result (no limit hit)."""
        return cls(exceeded=False, current_usage=0.0, max_allowed=0.0)

    @classmethod
    def block(
        cls,
        current_usage: float,
        max_allowed: float,
        policy_id: Optional[str] = None,
    ) -> "LimitCheckResponse":
        """Factory for blocked result (limit exceeded)."""
        return cls(
            exceeded=True,
            current_usage=current_usage,
            max_allowed=max_allowed,
            policy_id=policy_id,
        )

    @classmethod
    def warn(
        cls,
        current_usage: float,
        max_allowed: float,
    ) -> "LimitCheckResponse":
        """Factory for warning result (approaching limit)."""
        return cls(
            exceeded=False,
            current_usage=current_usage,
            max_allowed=max_allowed,
            warning=True,
        )


# =============================================================================
# Protocol Definition
# =============================================================================


@runtime_checkable
class LimitEnforcerProtocol(Protocol):
    """Protocol defining the LimitEnforcer interface.

    This is the contract that limit_hook.py depends on.
    Any implementation must satisfy this protocol.
    """

    async def check_cost_limit(
        self,
        tenant_id: str,
        estimated_cost: float,
    ) -> LimitCheckResponse:
        """Check if estimated cost exceeds tenant's cost/budget limit.

        Args:
            tenant_id: Tenant identifier
            estimated_cost: Estimated cost in cents for the operation

        Returns:
            LimitCheckResponse with exceeded=True if over budget
        """
        ...

    async def check_token_limit(
        self,
        tenant_id: str,
        estimated_tokens: int,
    ) -> LimitCheckResponse:
        """Check if estimated tokens exceed tenant's token limit.

        Args:
            tenant_id: Tenant identifier
            estimated_tokens: Estimated token count for the operation

        Returns:
            LimitCheckResponse with exceeded=True if over limit
        """
        ...

    async def check_rate_limit(
        self,
        tenant_id: str,
        operation: str,
    ) -> LimitCheckResponse:
        """Check if operation exceeds tenant's rate limit.

        Args:
            tenant_id: Tenant identifier
            operation: Operation type (e.g., "step_execution")

        Returns:
            LimitCheckResponse with exceeded=True if rate limited
        """
        ...


# =============================================================================
# Singleton Factory (Contract Only)
# =============================================================================


def get_limit_enforcer() -> LimitEnforcerProtocol:
    """Get the LimitEnforcer instance.

    Returns:
        LimitEnforcer implementation satisfying LimitEnforcerProtocol

    Note:
        Implementation provided in limit_enforcer.py
    """
    # Import implementation here to avoid circular imports
    from app.hoc.int.policies.L5_engines.limit_enforcer import get_limit_enforcer_impl
    return get_limit_enforcer_impl()
