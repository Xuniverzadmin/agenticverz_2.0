# capability_id: CAP-009
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

WIRING:
    - Persists to usage_records table via UsageRecordDriver (L6)
    - Records 3 meters per step: cost_cents, tokens_used, step_latency_ms

IMPLEMENTATION NOTES:
    - record_usage is fire-and-forget (does NOT raise)
    - No limit checking (that's LimitEnforcer)
    - No time/UUID generation
"""

import logging
from typing import Callable, Optional

from app.hoc.int.policies.L5_engines.usage_monitor_contract import (
    UsageMonitorProtocol,
)

logger = logging.getLogger("nova.hoc.policies.usage_monitor")


class UsageMonitor:
    """
    UsageMonitor implementation wired to UsageRecordDriver.

    Persists cost, token, and latency usage records per step execution.

    Layer: L5 (Domain Engine)
    Contract: UsageMonitorProtocol
    """

    def __init__(self, session_factory: Optional[Callable] = None):
        """
        Args:
            session_factory: Async callable returning AsyncSession.
                             If None, falls back to log-only.
        """
        self._session_factory = session_factory

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

        Persists 3 usage records: cost_cents, tokens_used, step_latency_ms.
        Fire-and-forget: never raises.
        """
        try:
            if self._session_factory is not None:
                session = await self._session_factory()
                from app.hoc.int.policies.drivers.usage_record_driver import UsageRecordDriver
                driver = UsageRecordDriver(session)

                metadata = {"run_id": run_id, "step_index": step_index}

                # Record cost
                if cost > 0:
                    await driver.insert_usage(
                        tenant_id=tenant_id,
                        meter_name="cost_cents",
                        amount=cost,
                        unit="cents",
                        worker_id=run_id,
                        metadata=metadata,
                    )

                # Record tokens
                if tokens > 0:
                    await driver.insert_usage(
                        tenant_id=tenant_id,
                        meter_name="tokens_used",
                        amount=tokens,
                        unit="tokens",
                        worker_id=run_id,
                        metadata=metadata,
                    )

                # Record latency
                if latency_ms > 0:
                    await driver.insert_usage(
                        tenant_id=tenant_id,
                        meter_name="step_latency_ms",
                        amount=int(latency_ms),
                        unit="milliseconds",
                        worker_id=run_id,
                        metadata=metadata,
                    )

            logger.debug(
                "usage_monitor.record_usage",
                extra={
                    "tenant_id": tenant_id,
                    "run_id": run_id,
                    "step_index": step_index,
                    "cost_cents": cost,
                    "tokens_used": tokens,
                    "latency_ms": latency_ms,
                    "persisted": self._session_factory is not None,
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


def get_usage_monitor_impl(
    session_factory: Optional[Callable] = None,
) -> UsageMonitor:
    """Get the UsageMonitor instance.

    Args:
        session_factory: Optional async callable returning AsyncSession.

    Returns:
        UsageMonitor implementation instance
    """
    global _usage_monitor_instance

    if _usage_monitor_instance is None:
        _usage_monitor_instance = UsageMonitor(session_factory=session_factory)
        logger.info("usage_monitor.created", extra={"wired": session_factory is not None})

    return _usage_monitor_instance


def reset_usage_monitor() -> None:
    """Reset the singleton (for testing)."""
    global _usage_monitor_instance
    _usage_monitor_instance = None
