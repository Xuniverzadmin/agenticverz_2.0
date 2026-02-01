# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — circuit breaker control plane (single authority)
# Callers: Admin APIs, CostSim orchestrator, drift detector, monitoring
# Allowed Imports: hoc_spine, hoc.cus.controls.L5_engines (lazy), hoc.cus.controls.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 2A Wiring
# artifact_class: CODE

"""
Circuit Breaker Handler (PIN-513 Batch 2A Wiring)

L4 handler that owns ALL circuit breaker operations. Single authority
for the CostSim V2 control plane.

Wires:
  From controls/L5_engines/cb_sync_wrapper_engine.py:
    - get_state_sync(timeout)
    - is_v2_disabled_sync(timeout)
    - shutdown_executor()

  From controls/L6_drivers/circuit_breaker_async_driver.py:
    - get_async_circuit_breaker()
    - get_state()
    - is_v2_disabled(session)
    - disable_v2(reason, disabled_by, disabled_until)
    - enable_v2(enabled_by, reason)
    - report_drift(drift_score, sample_count, details)
    - report_schema_error(error_count, details)
    - get_incidents(include_resolved, limit)

  From controls/L6_drivers/circuit_breaker_driver.py:
    - create_circuit_breaker(session, ...)
    - disable_v2(session, ...)
    - enable_v2(session, ...)
    - is_v2_disabled(session)

Flow:
  Admin API / CostSim orchestrator / drift detector
    → CircuitBreakerHandler.<method>()
        → L5/L6 driver call
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nova.hoc_spine.handlers.circuit_breaker")


class CircuitBreakerHandler:
    """L4 handler: circuit breaker control plane.

    Single authority for all CostSim V2 circuit breaker operations.
    No L2 or L5 may call drivers directly.
    """

    # ── Async operations (via circuit_breaker_async_driver) ──

    async def get_state(self) -> Any:
        """Get current circuit breaker state snapshot (async)."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            get_state,
        )

        return await get_state()

    async def is_v2_disabled(
        self,
        session: Optional[Any] = None,
    ) -> bool:
        """Check if CostSim V2 is disabled (async). Handles TTL auto-recovery."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            is_v2_disabled,
        )

        return await is_v2_disabled(session=session)

    async def disable_v2(
        self,
        reason: str,
        disabled_by: str,
        disabled_until: Optional[datetime] = None,
    ) -> Tuple[bool, Any]:
        """Manually disable CostSim V2. Idempotent. Creates incident."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            disable_v2,
        )

        result = await disable_v2(
            reason=reason,
            disabled_by=disabled_by,
            disabled_until=disabled_until,
        )
        logger.info(
            "circuit_breaker_disable_v2",
            extra={
                "reason": reason,
                "disabled_by": disabled_by,
                "state_changed": result[0],
            },
        )
        return result

    async def enable_v2(
        self,
        enabled_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Manually enable CostSim V2. Resolves incident, sends alert."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            enable_v2,
        )

        result = await enable_v2(enabled_by=enabled_by, reason=reason)
        logger.info(
            "circuit_breaker_enable_v2",
            extra={"enabled_by": enabled_by, "state_changed": result},
        )
        return result

    async def report_drift(
        self,
        drift_score: float,
        sample_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Report drift observation. May trip breaker if threshold exceeded."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            report_drift,
        )

        return await report_drift(
            drift_score=drift_score,
            sample_count=sample_count,
            details=details,
        )

    async def report_schema_error(
        self,
        error_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Report schema error. May trip breaker if threshold exceeded."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            report_schema_error,
        )

        return await report_schema_error(
            error_count=error_count,
            details=details,
        )

    async def get_incidents(
        self,
        include_resolved: bool = False,
        limit: int = 10,
    ) -> List[Any]:
        """Get recent circuit breaker incidents."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            get_incidents,
        )

        return await get_incidents(
            include_resolved=include_resolved,
            limit=limit,
        )

    def get_singleton(self) -> Any:
        """Get the global AsyncCircuitBreaker singleton."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            get_async_circuit_breaker,
        )

        return get_async_circuit_breaker()

    # ── Sync operations (via cb_sync_wrapper_engine) ──

    def get_state_sync(self, timeout: float = 5.0) -> Any:
        """Get circuit breaker state (sync-safe). Returns None on error."""
        from app.hoc.cus.controls.L5_engines.cb_sync_wrapper_engine import (
            get_state_sync,
        )

        return get_state_sync(timeout=timeout)

    def is_v2_disabled_sync(self, timeout: float = 5.0) -> bool:
        """Check V2 disabled (sync-safe). Returns False on error."""
        from app.hoc.cus.controls.L5_engines.cb_sync_wrapper_engine import (
            is_v2_disabled_sync,
        )

        return is_v2_disabled_sync(timeout=timeout)

    def shutdown(self) -> None:
        """Shutdown thread pool executor. Call on application shutdown."""
        from app.hoc.cus.controls.L5_engines.cb_sync_wrapper_engine import (
            shutdown_executor,
        )

        shutdown_executor()
        logger.info("circuit_breaker_executor_shutdown")

    # ── Sync driver operations (caller-owned session) ──

    def create_breaker(
        self,
        session: Any,
        failure_threshold: Optional[int] = None,
        drift_threshold: Optional[float] = None,
        name: str = "costsim_v2",
    ) -> Any:
        """Create circuit breaker bound to session (sync). L6 does NOT commit."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_driver import (
            create_circuit_breaker,
        )

        return create_circuit_breaker(
            session=session,
            failure_threshold=failure_threshold,
            drift_threshold=drift_threshold,
            name=name,
        )

    async def disable_v2_sync(
        self,
        session: Any,
        reason: str,
        disabled_by: str,
        disabled_until: Optional[datetime] = None,
    ) -> Tuple[bool, Any]:
        """Disable V2 with caller-owned session (sync driver)."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_driver import (
            disable_v2,
        )

        return await disable_v2(
            session=session,
            reason=reason,
            disabled_by=disabled_by,
            disabled_until=disabled_until,
        )

    async def enable_v2_sync(
        self,
        session: Any,
        enabled_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Enable V2 with caller-owned session (sync driver)."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_driver import (
            enable_v2,
        )

        return await enable_v2(
            session=session,
            enabled_by=enabled_by,
            reason=reason,
        )

    async def is_v2_disabled_with_session(self, session: Any) -> bool:
        """Check V2 disabled with caller-owned session (sync driver)."""
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_driver import (
            is_v2_disabled,
        )

        return await is_v2_disabled(session=session)
