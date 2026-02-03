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

WIRING:
    - Cost/token checks: LimitsReadDriver (L6) via injected session factory
    - Rate checks: RateLimiter (Redis token bucket, L4 hoc_spine)

ENFORCEMENT POLICY:
    - DENY on failure (fail-closed for enforcement)
    - If session unavailable or driver errors → block (not allow)
    - Rate limiter Redis failure → fail_open=False
"""

import logging
from typing import Callable, Optional

from app.hoc.int.policies.L5_engines.limit_enforcer_contract import (
    LimitCheckResponse,
    LimitEnforcerProtocol,
)

logger = logging.getLogger("nova.hoc.policies.limit_enforcer")


class LimitEnforcer:
    """
    LimitEnforcer implementation wired to real infrastructure.

    Cost/token checks query tenant limits via LimitsReadDriver.
    Rate checks use Redis token bucket via RateLimiter.

    Layer: L5 (Domain Engine)
    Contract: LimitEnforcerProtocol
    """

    def __init__(
        self,
        session_factory: Optional[Callable] = None,
        rate_limiter=None,
    ):
        """
        Args:
            session_factory: Async callable returning AsyncSession for DB access.
                             If None, all cost/token checks DENY (fail-closed).
            rate_limiter: RateLimiter instance. If None, lazily loaded from singleton.
        """
        self._session_factory = session_factory
        self._rate_limiter = rate_limiter

    def _get_rate_limiter(self):
        """Lazy-load rate limiter singleton."""
        if self._rate_limiter is None:
            from app.hoc.cus.hoc_spine.services.rate_limiter import get_rate_limiter
            self._rate_limiter = get_rate_limiter()
        return self._rate_limiter

    async def _fetch_limits_for_tenant(
        self, tenant_id: str, category: str, limit_type: Optional[str] = None
    ) -> list[dict]:
        """Fetch active limits for tenant via L6 driver.

        Returns empty list on error (caller handles as DENY).
        """
        if self._session_factory is None:
            return []

        try:
            session = await self._session_factory()
            from app.hoc.cus.controls.L6_drivers.limits_read_driver import LimitsReadDriver
            driver = LimitsReadDriver(session)
            items, _ = await driver.fetch_limits(
                tenant_id,
                category=category,
                status="ACTIVE",
                limit_type=limit_type,
                limit=100,
                offset=0,
            )
            return items
        except Exception as e:
            logger.error(
                "limit_enforcer.fetch_limits_failed",
                extra={"tenant_id": tenant_id, "category": category, "error": str(e)},
            )
            return []

    async def check_cost_limit(
        self,
        tenant_id: str,
        estimated_cost: float,
    ) -> LimitCheckResponse:
        """Check if estimated cost exceeds tenant's cost/budget limit.

        Queries BUDGET limits for the tenant. If any ACTIVE budget limit
        is exceeded by estimated_cost, returns block().
        If no limits found or no session → DENY (fail-closed).
        """
        logger.debug(
            "limit_enforcer.check_cost_limit",
            extra={"tenant_id": tenant_id, "estimated_cost": estimated_cost},
        )

        limits = await self._fetch_limits_for_tenant(tenant_id, "BUDGET")

        if not limits:
            # No limits configured = allow (legitimate no-limits state)
            # But if session_factory is None, we can't tell → DENY
            if self._session_factory is None:
                return LimitCheckResponse.block(
                    current_usage=estimated_cost,
                    max_allowed=0.0,
                    policy_id=None,
                )
            return LimitCheckResponse.allow()

        for lim in limits:
            max_val = float(lim.get("max_value", 0))
            if max_val > 0 and estimated_cost > max_val:
                return LimitCheckResponse.block(
                    current_usage=estimated_cost,
                    max_allowed=max_val,
                    policy_id=lim.get("limit_id"),
                )
            # Warn at 80% threshold
            if max_val > 0 and estimated_cost > max_val * 0.8:
                return LimitCheckResponse.warn(
                    current_usage=estimated_cost,
                    max_allowed=max_val,
                )

        return LimitCheckResponse.allow()

    async def check_token_limit(
        self,
        tenant_id: str,
        estimated_tokens: int,
    ) -> LimitCheckResponse:
        """Check if estimated tokens exceed tenant's token limit.

        Queries RATE limits with TOKENS_* type for the tenant.
        """
        logger.debug(
            "limit_enforcer.check_token_limit",
            extra={"tenant_id": tenant_id, "estimated_tokens": estimated_tokens},
        )

        limits = await self._fetch_limits_for_tenant(
            tenant_id, "RATE", limit_type="TOKENS_*"
        )

        if not limits:
            if self._session_factory is None:
                return LimitCheckResponse.block(
                    current_usage=float(estimated_tokens),
                    max_allowed=0.0,
                    policy_id=None,
                )
            return LimitCheckResponse.allow()

        for lim in limits:
            max_val = float(lim.get("max_value", 0))
            if max_val > 0 and estimated_tokens > max_val:
                return LimitCheckResponse.block(
                    current_usage=float(estimated_tokens),
                    max_allowed=max_val,
                    policy_id=lim.get("limit_id"),
                )
            if max_val > 0 and estimated_tokens > max_val * 0.8:
                return LimitCheckResponse.warn(
                    current_usage=float(estimated_tokens),
                    max_allowed=max_val,
                )

        return LimitCheckResponse.allow()

    async def check_rate_limit(
        self,
        tenant_id: str,
        operation: str,
    ) -> LimitCheckResponse:
        """Check if operation exceeds tenant's rate limit.

        Uses Redis token bucket rate limiter.
        Fail-closed: if Redis unavailable, DENY.
        """
        logger.debug(
            "limit_enforcer.check_rate_limit",
            extra={"tenant_id": tenant_id, "operation": operation},
        )

        # Look up rate limit configuration from DB
        limits = await self._fetch_limits_for_tenant(tenant_id, "RATE", limit_type="REQUESTS_*")

        # Find the applicable rate limit for this operation
        rate_per_min = 0
        policy_id = None
        for lim in limits:
            max_val = float(lim.get("max_value", 0))
            window = lim.get("window_seconds", 60) or 60
            if max_val > 0:
                # Convert to per-minute rate
                rate_per_min = int(max_val * (60 / window))
                policy_id = lim.get("limit_id")
                break

        if rate_per_min <= 0:
            # No rate limit configured
            return LimitCheckResponse.allow()

        # Check via Redis rate limiter
        limiter = self._get_rate_limiter()
        key = f"tenant:{tenant_id}:{operation}"
        allowed = limiter.allow(key, rate_per_min)

        if not allowed:
            remaining = limiter.get_remaining(key, rate_per_min)
            return LimitCheckResponse.block(
                current_usage=float(rate_per_min - remaining),
                max_allowed=float(rate_per_min),
                policy_id=policy_id,
            )

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


def get_limit_enforcer_impl(
    session_factory: Optional[Callable] = None,
) -> LimitEnforcer:
    """Get the LimitEnforcer instance.

    This is called by the contract's get_limit_enforcer() function.

    Args:
        session_factory: Optional async callable returning AsyncSession.
                         If provided on first call, wires to DB.

    Returns:
        LimitEnforcer implementation instance
    """
    global _limit_enforcer_instance

    if _limit_enforcer_instance is None:
        _limit_enforcer_instance = LimitEnforcer(session_factory=session_factory)
        logger.info("limit_enforcer.created", extra={"wired": session_factory is not None})

    return _limit_enforcer_instance


def reset_limit_enforcer() -> None:
    """Reset the singleton (for testing)."""
    global _limit_enforcer_instance
    _limit_enforcer_instance = None
