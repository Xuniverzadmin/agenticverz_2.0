# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: worker (called after threshold evaluation)
#   Execution: sync
# Role: Signal coordinator — cross-domain threshold signal dispatch (C4 Loop Model)
# Callers: worker/runner.py, analytics/engines/runner.py
# Allowed Imports: hoc_spine, hoc.cus.controls (lazy), hoc.cus.activity (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model), PIN-507 (Law 4)
# artifact_class: CODE

"""
Signal Coordinator (C4 — Loop Model)

Context-free cross-domain mediator for threshold signal dispatch.
Owns TOPOLOGY only — controls→activity emission order.
Session binding happens in emit_and_persist_threshold_signal (L4 entry point),
never inside the coordinator itself.

Law 4 (PIN-507): Coordinators must NEVER accept session or execution context.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("nova.hoc_spine.orchestrator.coordinators.signal")


class SignalCoordinator:
    """
    Context-free cross-domain signal dispatch coordinator.

    Owns topology only: emit first (controls), then update risk (activity).
    Never receives session or execution context.
    """

    def emit_and_update_risk(self, *, emit_signals: Callable, update_risk: Callable) -> None:
        """Pure topology: emit first, then update risk. No session awareness.

        CALLABLE CONTRACT (PIN-507 Law 4):
            Callables must be side-effect isolated and non-catching.
            Exceptions must propagate to the handler (single blame point).
            No try/except inside callables — let failures surface.
        """
        emit_signals()
        update_risk()


# =============================================================================
# Module Singleton
# =============================================================================

_signal_coordinator_instance: Optional[SignalCoordinator] = None


def get_signal_coordinator() -> SignalCoordinator:
    """Get the signal coordinator singleton."""
    global _signal_coordinator_instance
    if _signal_coordinator_instance is None:
        _signal_coordinator_instance = SignalCoordinator()
    return _signal_coordinator_instance


# =============================================================================
# L4 Entry Point — Session Binding
# =============================================================================


def emit_and_persist_threshold_signal(
    session: Any,
    tenant_id: str,
    run_id: str,
    state: str,
    signals: list,
    params_used: dict,
) -> None:
    """L4 orchestration — binds session to callables, delegates to coordinator.

    This is the ONLY place where session meets cross-domain topology.
    Session binding happens here; coordinator never sees it.

    Args:
        session: SQLAlchemy sync session
        tenant_id: Tenant identifier
        run_id: Run identifier
        state: Run state ("live" or "completed")
        signals: List of ThresholdSignal values
        params_used: The threshold params that were evaluated against
    """
    from app.hoc.cus.controls.L6_drivers.threshold_driver import emit_threshold_signal_sync
    from app.hoc.cus.activity.L6_drivers.run_signal_driver import RunSignalDriver

    coordinator = get_signal_coordinator()
    coordinator.emit_and_update_risk(
        emit_signals=lambda: [
            emit_threshold_signal_sync(session, tenant_id, run_id, state, s, params_used)
            for s in signals
        ],
        update_risk=lambda: RunSignalDriver(session).update_risk_level(run_id, signals),
    )

    logger.info(
        "dual_signal_emission_complete",
        extra={
            "run_id": run_id,
            "tenant_id": tenant_id,
            "state": state,
            "signal_count": len(signals),
        },
    )
