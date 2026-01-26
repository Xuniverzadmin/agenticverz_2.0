# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: UsageMonitor implementation - post-step usage recording
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: limit_hook.py (via contract)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, sqlalchemy
# Reference: SWEEP-03 (GAP-053)

"""
UsageMonitor Implementation (GAP-053)

PURPOSE:
    Post-step usage recording for cost, token, and latency metrics.
    Called by limit_hook.py after step execution.

IMPLEMENTATION NOTES:
    - This is a minimal implementation satisfying the contract
    - record_usage is fire-and-forget (does NOT raise)
    - No limit checking (that's LimitEnforcer)
    - No time/UUID generation

    Future enhancement: Wire to actual usage storage via L6 driver.
    Current: Logs usage metrics only.
"""

import logging
from typing import Optional

from app.hoc.int.policies.L5_engines.usage_monitor_contract import (
    UsageMonitorProtocol,
)

logger = logging.getLogger("nova.hoc.policies.usage_monitor")


class UsageMonitor:
    """
    UsageMonitor implementation.

    This is a minimal implementation that satisfies the UsageMonitorProtocol.
    It currently logs usage metrics without persisting to storage.

    Future versions will wire to actual usage storage via L6 driver to:
    - Persist usage records for billing
    - Track cumulative usage per tenant
    - Enable usage analytics

    Layer: L5 (Domain Engine)
    Contract: UsageMonitorProtocol
    """

    async def record_usage(
        self,
        tenant_id: str,
        run_id: str,
        step_index: int,
        cost: int,
        tokens: int,
        latency_ms: float,
    ) -> None:
        """Record usage metrics for a step execution.

        Args:
            tenant_id: Tenant identifier
            run_id: Run identifier
            step_index: Step index in the plan
            cost: Actual cost in cents
            tokens: Actual token usage
            latency_ms: Step execution latency in milliseconds

        Note:
            This method is fire-and-forget. Does NOT raise exceptions.
        """
        try:
            # TODO: Wire to L6 driver to persist usage records
            # For now, just log the usage metrics
            logger.debug(
                "usage_monitor.record_usage",
                extra={
                    "tenant_id": tenant_id,
                    "run_id": run_id,
                    "step_index": step_index,
                    "cost_cents": cost,
                    "tokens_used": tokens,
                    "latency_ms": latency_ms,
                },
            )
        except Exception as e:
            # Fire-and-forget: never raise, only log warnings
            logger.warning(
                "usage_monitor.record_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                },
            )


# =============================================================================
# Protocol Verification (compile-time type check)
# =============================================================================

# Verify that UsageMonitor satisfies the protocol
def _verify_protocol() -> None:
    """Compile-time verification that implementation matches protocol."""
    monitor: UsageMonitorProtocol = UsageMonitor()  # noqa: F841


# =============================================================================
# Singleton Factory
# =============================================================================

_usage_monitor_instance: Optional[UsageMonitor] = None


def get_usage_monitor_impl() -> UsageMonitor:
    """Get the UsageMonitor instance.

    This is called by the contract's get_usage_monitor() function.

    Returns:
        UsageMonitor implementation instance
    """
    global _usage_monitor_instance

    if _usage_monitor_instance is None:
        _usage_monitor_instance = UsageMonitor()
        logger.info("usage_monitor.created")

    return _usage_monitor_instance


def reset_usage_monitor() -> None:
    """Reset the singleton (for testing)."""
    global _usage_monitor_instance
    _usage_monitor_instance = None
