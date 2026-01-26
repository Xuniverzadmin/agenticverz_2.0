# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: LimitEnforcer implementation - pre-step limit checks for cost, token, and rate limits
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: limit_hook.py (via contract)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, sqlalchemy
# Reference: SWEEP-03 (GAP-055)

"""
LimitEnforcer Implementation (GAP-055)

PURPOSE:
    Pre-step limit checks for cost, token, and rate limits.
    Called by limit_hook.py before step execution.

IMPLEMENTATION NOTES:
    - This is a minimal implementation satisfying the contract
    - All methods return LimitCheckResponse (never raise for limit violations)
    - No state mutation (read-only checks)
    - No time/UUID generation
    - No calls to UsageMonitor (that's Module 2)

    Future enhancement: Wire to actual limit/policy storage via L6 driver.
    Current: Returns allow() for all checks (no limits configured = unlimited).
"""

import logging
from typing import Optional

from app.hoc.int.policies.L5_engines.limit_enforcer_contract import (
    LimitCheckResponse,
    LimitEnforcerProtocol,
)

logger = logging.getLogger("nova.hoc.policies.limit_enforcer")


class LimitEnforcer:
    """
    LimitEnforcer implementation.

    This is a minimal implementation that satisfies the LimitEnforcerProtocol.
    It currently returns allow() for all checks (no limits enforced).

    Future versions will wire to actual limit storage via L6 driver to:
    - Look up tenant-specific cost/budget limits
    - Look up tenant-specific token limits
    - Track rate limit windows

    Layer: L5 (Domain Engine)
    Contract: LimitEnforcerProtocol
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
        logger.debug(
            "limit_enforcer.check_cost_limit",
            extra={
                "tenant_id": tenant_id,
                "estimated_cost": estimated_cost,
            },
        )

        # TODO: Wire to L6 driver to fetch tenant limits
        # For now, no limits configured = allow all
        return LimitCheckResponse.allow()

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
        logger.debug(
            "limit_enforcer.check_token_limit",
            extra={
                "tenant_id": tenant_id,
                "estimated_tokens": estimated_tokens,
            },
        )

        # TODO: Wire to L6 driver to fetch tenant limits
        # For now, no limits configured = allow all
        return LimitCheckResponse.allow()

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
        logger.debug(
            "limit_enforcer.check_rate_limit",
            extra={
                "tenant_id": tenant_id,
                "operation": operation,
            },
        )

        # TODO: Wire to L6 driver + rate limit window tracking
        # For now, no rate limits configured = allow all
        return LimitCheckResponse.allow()


# =============================================================================
# Protocol Verification (compile-time type check)
# =============================================================================

# Verify that LimitEnforcer satisfies the protocol
def _verify_protocol() -> None:
    """Compile-time verification that implementation matches protocol."""
    enforcer: LimitEnforcerProtocol = LimitEnforcer()  # noqa: F841


# =============================================================================
# Singleton Factory
# =============================================================================

_limit_enforcer_instance: Optional[LimitEnforcer] = None


def get_limit_enforcer_impl() -> LimitEnforcer:
    """Get the LimitEnforcer instance.

    This is called by the contract's get_limit_enforcer() function.

    Returns:
        LimitEnforcer implementation instance
    """
    global _limit_enforcer_instance

    if _limit_enforcer_instance is None:
        _limit_enforcer_instance = LimitEnforcer()
        logger.info("limit_enforcer.created")

    return _limit_enforcer_instance


def reset_limit_enforcer() -> None:
    """Reset the singleton (for testing)."""
    global _limit_enforcer_instance
    _limit_enforcer_instance = None
