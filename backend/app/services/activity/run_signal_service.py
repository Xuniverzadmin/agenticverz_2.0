# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api | worker
#   Execution: sync
# Role: Update runs table with computed signals for Customer Console
# Callers: llm_threshold_service.py, incident_engine.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Writes to: runs table (risk_level, incident_count, policy_violation)
# Consumed by: v_runs_o2 -> api/activity.py -> Customer Console
#
# =============================================================================
# SIGNAL AUDIENCE NOTE
# =============================================================================
#
# This service updates the RUNS TABLE for CUSTOMER CONSOLE panels.
# It does NOT write to ops_events (that's EventEmitter for Founder Console).
#
# Signal Audience Map:
# +-----------------+-------------------+---------------------+
# | Signal Type     | Founder Console   | Customer Console    |
# +-----------------+-------------------+---------------------+
# | Threshold       | ops_events        | runs.risk_level     |
# | Incident        | ops_events        | runs.incident_count |
# | Policy Violation| ops_events        | runs.policy_violation|
# +-----------------+-------------------+---------------------+
#
# =============================================================================

"""
Run Signal Service

Updates runs table with threshold and incident signals for Customer Console.

This service populates the signal columns that feed:
- Activity API (/api/v1/activity/runs)
- Customer Console panels (ACT-LLM-LIVE-O2, ACT-LLM-COMP-O3)

Reference: Threshold Signal Wiring to Customer Console Plan
"""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("nova.services.run_signal_service")


class RunSignalService:
    """
    Updates runs table with threshold and incident signals.

    This service populates the signal columns that feed:
    - Activity API (/api/v1/activity/runs)
    - Customer Console panels (ACT-LLM-LIVE-O2, ACT-LLM-COMP-O3)

    It does NOT emit to ops_events - that's handled by EventEmitter
    for Founder Console monitoring.
    """

    def __init__(self, session: Session):
        self._session = session

    def update_risk_level(self, run_id: str, signals: list) -> str:
        """
        Compute and persist risk_level based on threshold signals.

        Mapping:
        - EXECUTION_TIME_EXCEEDED, TOKEN_LIMIT_EXCEEDED, COST_LIMIT_EXCEEDED -> VIOLATED
        - RUN_FAILED -> AT_RISK
        - No signals -> NORMAL (no update needed)

        Args:
            run_id: The run identifier
            signals: List of ThresholdSignal enum values

        Returns:
            The computed risk_level
        """
        if not signals:
            return "NORMAL"

        # Import here to avoid circular dependencies
        from app.services.llm_threshold_service import ThresholdSignal

        # Convert to enum values if they are enum instances
        signal_values = []
        for s in signals:
            if hasattr(s, "value"):
                signal_values.append(s.value)
            else:
                signal_values.append(str(s))

        # Determine risk level based on signals
        # VIOLATED takes precedence over AT_RISK
        risk_level = "NORMAL"

        violation_signals = {
            ThresholdSignal.EXECUTION_TIME_EXCEEDED.value,
            ThresholdSignal.TOKEN_LIMIT_EXCEEDED.value,
            ThresholdSignal.COST_LIMIT_EXCEEDED.value,
        }

        at_risk_signals = {
            ThresholdSignal.RUN_FAILED.value,
        }

        for signal in signal_values:
            if signal in violation_signals:
                risk_level = "VIOLATED"
                break  # VIOLATED is highest severity
            elif signal in at_risk_signals:
                risk_level = "AT_RISK"

        # Update the runs table
        try:
            self._session.execute(
                text("""
                    UPDATE runs
                    SET risk_level = :risk_level
                    WHERE id = :run_id
                """),
                {"run_id": run_id, "risk_level": risk_level},
            )
            self._session.commit()

            logger.info(
                "run_risk_level_updated",
                extra={
                    "run_id": run_id,
                    "risk_level": risk_level,
                    "signals": signal_values,
                },
            )

        except Exception as e:
            logger.error(
                "run_risk_level_update_failed",
                extra={"run_id": run_id, "error": str(e)},
            )
            # Re-raise to let caller handle
            raise

        return risk_level

    def increment_incident_count(self, run_id: str) -> None:
        """
        Increment incident_count after incident creation.

        Called by IncidentEngine after INSERT to incidents table.
        This allows ACT-LLM-* panels to show "incidents caused by this run".

        Args:
            run_id: The run identifier
        """
        try:
            self._session.execute(
                text("""
                    UPDATE runs
                    SET incident_count = incident_count + 1
                    WHERE id = :run_id
                """),
                {"run_id": run_id},
            )
            self._session.commit()

            logger.info(
                "run_incident_count_incremented",
                extra={"run_id": run_id},
            )

        except Exception as e:
            logger.error(
                "run_incident_count_update_failed",
                extra={"run_id": run_id, "error": str(e)},
            )
            # Don't re-raise - incident creation should not fail
            # because of this update

    def set_policy_violation(self, run_id: str, violated: bool) -> None:
        """
        Set policy_violation flag when policy breach detected.

        Args:
            run_id: The run identifier
            violated: Whether a policy was violated
        """
        try:
            self._session.execute(
                text("""
                    UPDATE runs
                    SET policy_violation = :violated
                    WHERE id = :run_id
                """),
                {"run_id": run_id, "violated": violated},
            )
            self._session.commit()

            logger.info(
                "run_policy_violation_updated",
                extra={"run_id": run_id, "violated": violated},
            )

        except Exception as e:
            logger.error(
                "run_policy_violation_update_failed",
                extra={"run_id": run_id, "error": str(e)},
            )


def get_run_signal_service(session: Session) -> RunSignalService:
    """Factory function for RunSignalService."""
    return RunSignalService(session)
