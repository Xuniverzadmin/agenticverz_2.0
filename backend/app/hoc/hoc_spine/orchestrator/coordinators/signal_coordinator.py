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
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model)
# artifact_class: CODE

"""
Signal Coordinator (C4 — Loop Model)

Mediates threshold signal emission between controls and activity domains.
Replaces direct controls→activity L6 import in emit_and_persist_threshold_signal.

Pattern:
    worker → SignalCoordinator.emit_and_update_risk() → controls emit + activity risk update

The coordinator lazy-imports both domain drivers internally.
This is legal because L4 can import L5/L6.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger("nova.hoc_spine.orchestrator.coordinators.signal")


class SignalCoordinator:
    """
    Cross-domain signal dispatch coordinator.

    Performs dual emission of threshold signals:
    1. ops_events (Founder Console) — via controls threshold_driver
    2. runs.risk_level (Customer Console) — via activity run_signal_driver
    """

    def emit_and_update_risk(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
        state: str,
        signals: list,
        params_used: dict,
    ) -> None:
        """
        Emit threshold signals to both consoles.

        Replaces emit_and_persist_threshold_signal() which had a cross-domain
        controls→activity import.

        Args:
            session: SQLAlchemy sync session
            tenant_id: Tenant identifier
            run_id: Run identifier
            state: Run state ("live" or "completed")
            signals: List of ThresholdSignal values
            params_used: The threshold params that were evaluated against
        """
        # 1. Emit to ops_events for Founder Console monitoring (controls domain)
        from app.hoc.cus.controls.L6_drivers.threshold_driver import (
            emit_threshold_signal_sync,
        )

        for signal in signals:
            emit_threshold_signal_sync(session, tenant_id, run_id, state, signal, params_used)

        # 2. Update runs.risk_level for Customer Console Activity panels (activity domain)
        from app.hoc.cus.activity.L6_drivers.run_signal_driver import RunSignalDriver

        run_signal_driver = RunSignalDriver(session)
        run_signal_driver.update_risk_level(run_id, signals)

        logger.info(
            "dual_signal_emission_complete",
            extra={
                "run_id": run_id,
                "tenant_id": tenant_id,
                "state": state,
                "signal_count": len(signals),
            },
        )


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
