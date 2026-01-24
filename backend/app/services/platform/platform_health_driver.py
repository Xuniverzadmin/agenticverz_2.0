# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: engine-call
#   Execution: sync
# Role: Data access for platform health evaluation
# Callers: PlatformHealthEngine (L4)
# Allowed Imports: sqlalchemy, sqlmodel, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, PIN-284

"""Platform Health Driver

L6 driver for platform health data access.

Pure persistence - no business logic.
Returns raw facts: signals, incidents, counts.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlmodel import Session

from app.models.governance import GovernanceSignal
from app.models.killswitch import Incident


@dataclass(frozen=True)
class SignalRow:
    """Immutable signal data for health evaluation."""

    signal_type: str
    decision: str
    scope: str
    reason: Optional[str]
    recorded_by: str
    recorded_at: datetime
    expires_at: Optional[datetime]


@dataclass(frozen=True)
class IncidentCount:
    """Immutable incident count for capability."""

    capability_name: str
    open_count: int


class PlatformHealthDriver:
    """L6 driver for platform health data access.

    Pure persistence - no business logic.
    Returns raw facts for engine to interpret.
    """

    def __init__(self, session: Session):
        """Initialize driver with database session.

        Args:
            session: SQLModel Session for data access
        """
        self._session = session

    # =========================================================================
    # SYSTEM-LEVEL SIGNALS
    # =========================================================================

    def fetch_blca_status(self) -> Optional[str]:
        """Fetch current BLCA status from governance signals.

        Returns:
            Decision value (e.g., "BLOCKED", "CLEAN") or None if not found
        """
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "BLCA_STATUS",
                    GovernanceSignal.scope == "SYSTEM",
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision
        return None

    def fetch_lifecycle_coherence(self) -> Optional[str]:
        """Fetch lifecycle/qualifier coherence status.

        Returns:
            Decision value (e.g., "COHERENT", "INCOHERENT") or None if not found
        """
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "LIFECYCLE_QUALIFIER_COHERENCE",
                    GovernanceSignal.scope == "SYSTEM",
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision
        return None

    # =========================================================================
    # CAPABILITY-LEVEL SIGNALS
    # =========================================================================

    def fetch_blocking_signals(self, capability_name: str) -> List[SignalRow]:
        """Fetch blocking governance signals for a capability.

        Args:
            capability_name: Capability to check

        Returns:
            List of blocking signal rows (decision = "BLOCKED")
        """
        now = datetime.now(timezone.utc)

        stmt = select(GovernanceSignal).where(
            and_(
                or_(
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.scope == "SYSTEM",
                ),
                GovernanceSignal.decision == "BLOCKED",
                GovernanceSignal.superseded_at.is_(None),
                or_(
                    GovernanceSignal.expires_at.is_(None),
                    GovernanceSignal.expires_at > now,
                ),
            )
        )

        results = self._session.execute(stmt).scalars().all()
        return [
            SignalRow(
                signal_type=s.signal_type,
                decision=s.decision,
                scope=s.scope,
                reason=s.reason,
                recorded_by=s.recorded_by,
                recorded_at=s.recorded_at,
                expires_at=s.expires_at,
            )
            for s in results
        ]

    def fetch_warning_signals(self, capability_name: str) -> List[SignalRow]:
        """Fetch warning governance signals for a capability.

        Args:
            capability_name: Capability to check

        Returns:
            List of warning signal rows (decision = "WARN")
        """
        now = datetime.now(timezone.utc)

        stmt = select(GovernanceSignal).where(
            and_(
                or_(
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.scope == "SYSTEM",
                ),
                GovernanceSignal.decision == "WARN",
                GovernanceSignal.superseded_at.is_(None),
                or_(
                    GovernanceSignal.expires_at.is_(None),
                    GovernanceSignal.expires_at > now,
                ),
            )
        )

        results = self._session.execute(stmt).scalars().all()
        return [
            SignalRow(
                signal_type=s.signal_type,
                decision=s.decision,
                scope=s.scope,
                reason=s.reason,
                recorded_by=s.recorded_by,
                recorded_at=s.recorded_at,
                expires_at=s.expires_at,
            )
            for s in results
        ]

    def fetch_qualifier_state(self, capability_name: str) -> Optional[str]:
        """Fetch qualifier state for a capability.

        Args:
            capability_name: Capability to check

        Returns:
            Decision value (e.g., "QUALIFIED", "DISQUALIFIED") or None
        """
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "QUALIFIER_STATUS",
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision
        return None

    def fetch_lifecycle_status(self, capability_name: str) -> Optional[str]:
        """Fetch lifecycle status for a capability.

        Args:
            capability_name: Capability to check

        Returns:
            Decision value (e.g., "COMPLETE", "PARTIAL") or None
        """
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "LIFECYCLE_STATUS",
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision
        return None

    # =========================================================================
    # INCIDENT DATA
    # =========================================================================

    def fetch_open_incident_count(self, capability_name: str) -> int:
        """Fetch count of open incidents affecting a capability.

        Uses savepoint to avoid aborting parent transaction on failure.

        Args:
            capability_name: Capability to check (not used in current query)

        Returns:
            Count of open incidents (0 on any error)
        """
        try:
            nested = self._session.begin_nested()
            try:
                stmt = select(func.count(Incident.id)).where(
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
                )

                result = self._session.execute(stmt).scalar()
                nested.commit()
                return result or 0
            except Exception:
                nested.rollback()
                return 0
        except Exception:
            return 0


# Factory function
def get_platform_health_driver(session: Session) -> PlatformHealthDriver:
    """Get driver instance with session.

    Args:
        session: SQLModel Session

    Returns:
        PlatformHealthDriver instance
    """
    return PlatformHealthDriver(session=session)
