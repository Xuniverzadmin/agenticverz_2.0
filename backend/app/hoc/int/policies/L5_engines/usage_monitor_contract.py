# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: UsageMonitor contract - defines interface for usage recording
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: limit_hook.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, sqlalchemy
# Reference: SWEEP-03 (GAP-053)
#
# GOVERNANCE NOTE:
# This is the CONTRACT for UsageMonitor.
# Implementation follows in usage_monitor.py.
# Contract defines ONLY what limit_hook.py requires TODAY.

"""
UsageMonitor Contract (GAP-053)

PURPOSE:
    Post-step usage recording for cost, token, and latency metrics.
    Called by limit_hook.py after step execution.

INTERFACE:
    - record_usage(tenant_id, run_id, step_index, cost, tokens, latency_ms) -> None

INVARIANTS:
    - All methods are async
    - record_usage does NOT raise (fire-and-forget semantics)
    - No limit checking (that's LimitEnforcer, Module 1)
    - No time/UUID generation
"""

from typing import Optional, Protocol, runtime_checkable


# =============================================================================
# Protocol Definition
# =============================================================================


@runtime_checkable
class UsageMonitorProtocol(Protocol):
    """Protocol defining the UsageMonitor interface.

    This is the contract that limit_hook.py depends on.
    Any implementation must satisfy this protocol.
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
            This method is fire-and-forget. Implementations should NOT raise
            exceptions for recording failures (log warnings instead).
        """
        ...


# =============================================================================
# Singleton Factory (Contract Only)
# =============================================================================


def get_usage_monitor() -> UsageMonitorProtocol:
    """Get the UsageMonitor instance.

    Returns:
        UsageMonitor implementation satisfying UsageMonitorProtocol

    Note:
        Implementation provided in usage_monitor.py
    """
    # Import implementation here to avoid circular imports
    from app.hoc.int.policies.L5_engines.usage_monitor import get_usage_monitor_impl
    return get_usage_monitor_impl()
