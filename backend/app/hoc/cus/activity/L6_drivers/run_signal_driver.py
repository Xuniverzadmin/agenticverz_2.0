# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: RunSignalDriver - updates run risk levels based on threshold signals
# NOTE: Renamed run_signal_service.py → run_signal_driver.py (2026-01-31)
#       per BANNED_NAMING rule (*_service.py → *_driver.py for L6 files)
# Temporal:
#   Trigger: api (via threshold drivers)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: runs
#   Writes: runs.risk_level
# Database:
#   Scope: domain (activity)
#   Models: Run
# Callers: threshold_driver.py, llm_threshold_driver.py
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L5
# Reference: SWEEP-03

"""
RunSignalService (L6 Driver)

PURPOSE:
    Updates run risk levels based on threshold signals.
    Bridges threshold evaluation (L5) to run state (L7).

INTERFACE:
    - RunSignalService(session): Constructor takes sync session
    - update_risk_level(run_id, signals): Updates risk level for a run

L6 CONTRACT:
    - Pure data access, no business logic
    - Does NOT determine which signals to emit (that's L5)
    - Only persists signal outcomes to runs table

CALLERS:
    - threshold_driver.py: emit_and_persist_threshold_signal()
    - llm_threshold_driver.py: emit_and_persist_threshold_signal()
"""

import logging
from typing import Any, List

from sqlalchemy import text

logger = logging.getLogger("nova.hoc.activity.run_signal_service")


# =============================================================================
# Risk Level Mapping
# =============================================================================

# Map signal types to risk levels
# Higher number = higher risk
SIGNAL_TO_RISK_LEVEL = {
    "EXECUTION_TIME_EXCEEDED": 2,
    "TOKEN_LIMIT_EXCEEDED": 2,
    "COST_LIMIT_EXCEEDED": 2,
    "RUN_FAILED": 3,
}

# Default risk level when no signals
DEFAULT_RISK_LEVEL = 0


class RunSignalDriver:
    """
    Service for updating run risk levels based on threshold signals.

    L6 Driver Contract:
    - Pure data access, no business logic
    - Takes sync session (for worker/callback context)
    - Updates runs.risk_level column

    Usage:
        service = RunSignalService(session)
        service.update_risk_level(run_id, signals)
    """

    def __init__(self, session: Any):
        """
        Initialize with a sync SQLAlchemy Session.

        Args:
            session: Sync SQLAlchemy Session
        """
        self._session = session

    def update_risk_level(
        self,
        run_id: str,
        signals: List[Any],
    ) -> None:
        """
        Update risk level for a run based on threshold signals.

        The risk level is set to the maximum severity of all provided signals.

        Args:
            run_id: Run identifier (UUID as string)
            signals: List of ThresholdSignal enum values

        Note:
            This method does NOT commit the transaction.
            The caller is responsible for committing.
        """
        if not signals:
            logger.debug(
                "run_signal_service.no_signals",
                extra={"run_id": run_id},
            )
            return

        # Calculate maximum risk level from signals
        max_risk = DEFAULT_RISK_LEVEL
        for signal in signals:
            signal_name = signal.value if hasattr(signal, "value") else str(signal)
            risk = SIGNAL_TO_RISK_LEVEL.get(signal_name, 1)
            max_risk = max(max_risk, risk)

        # Update runs table
        try:
            self._session.execute(
                text("""
                    UPDATE runs
                    SET risk_level = :risk_level,
                        updated_at = NOW()
                    WHERE id = :run_id::uuid
                """),
                {"run_id": run_id, "risk_level": max_risk},
            )

            logger.info(
                "run_signal_service.risk_level_updated",
                extra={
                    "run_id": run_id,
                    "risk_level": max_risk,
                    "signal_count": len(signals),
                },
            )

        except Exception as e:
            logger.error(
                "run_signal_service.update_failed",
                extra={
                    "run_id": run_id,
                    "error": str(e),
                },
            )
            # Re-raise to let caller handle
            raise

    def get_risk_level(self, run_id: str) -> int:
        """
        Get current risk level for a run.

        Args:
            run_id: Run identifier (UUID as string)

        Returns:
            Risk level (0-3) or DEFAULT_RISK_LEVEL if not found
        """
        try:
            result = self._session.execute(
                text("""
                    SELECT risk_level
                    FROM runs
                    WHERE id = :run_id::uuid
                """),
                {"run_id": run_id},
            )
            row = result.fetchone()

            if row is None:
                return DEFAULT_RISK_LEVEL

            return row.risk_level or DEFAULT_RISK_LEVEL

        except Exception as e:
            logger.warning(
                "run_signal_service.get_failed",
                extra={
                    "run_id": run_id,
                    "error": str(e),
                },
            )
            return DEFAULT_RISK_LEVEL


# Backward-compatible alias (deprecated, use RunSignalDriver)
RunSignalService = RunSignalDriver
