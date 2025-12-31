# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api|worker|scheduler
#   Execution: sync
# Role: Governance signal persistence service
# Callers: L7 (BLCA, CI) for writes, L4/L5 for reads
# Allowed Imports: L6 (db, models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-256 Phase E FIX-03

"""
Governance Signal Service (Phase E FIX-03)

L6 service for persisting and querying governance signals.

Write Path (L7 → L6):
- BLCA, CI, OPS write signals via record_signal()
- Signals are persisted to governance_signals table
- Previous signals for same scope/type are superseded

Read Path (L4/L5 ← L6):
- Domain orchestrators check governance before decisions
- Workers check governance before execution
- Returns blocking/warning signals for scope

Contract:
- All governance influence becomes visible data
- No implicit pressure - only explicit signals
- L4/L5 can query WHY they're blocked
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.models.governance import (
    GovernanceCheckResult,
    GovernanceSignal,
    GovernanceSignalCreate,
    GovernanceSignalResponse,
)


class GovernanceSignalService:
    """
    Service for governance signal operations.

    Phase E: Makes L7 → L4/L5 influence explicit and queryable.
    """

    def __init__(self, session: Session):
        self.session = session

    def record_signal(
        self,
        signal_type: str,
        scope: str,
        decision: str,
        recorded_by: str,
        reason: Optional[str] = None,
        constraints: Optional[dict] = None,
        expires_at: Optional[datetime] = None,
    ) -> GovernanceSignal:
        """
        Record a new governance signal (L7 → L6 write).

        Supersedes any existing active signals for the same scope/type.

        Args:
            signal_type: BLCA_STATUS, CI_STATUS, DEPLOYMENT_GATE, SESSION_BLOCK
            scope: What this applies to (file path, PR number, session ID)
            decision: CLEAN, BLOCKED, WARN, PENDING
            recorded_by: Source (BLCA, CI, OPS, MANUAL)
            reason: Human-readable explanation
            constraints: Structured block details
            expires_at: Optional expiration for temporary blocks

        Returns:
            The newly created governance signal
        """
        now = datetime.now(timezone.utc)

        # Supersede any existing active signals for this scope/type
        self._supersede_existing_signals(scope, signal_type, now)

        # Create new signal
        signal = GovernanceSignal(
            signal_type=signal_type,
            scope=scope,
            decision=decision,
            reason=reason,
            constraints=constraints,
            recorded_by=recorded_by,
            recorded_at=now,
            expires_at=expires_at,
        )

        self.session.add(signal)
        self.session.flush()

        return signal

    def _supersede_existing_signals(
        self, scope: str, signal_type: str, superseded_at: datetime
    ) -> int:
        """Mark existing active signals as superseded."""
        stmt = (
            update(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.scope == scope,
                    GovernanceSignal.signal_type == signal_type,
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .values(superseded_at=superseded_at)
        )
        result = self.session.execute(stmt)
        return result.rowcount

    def check_governance(
        self,
        scope: str,
        signal_type: Optional[str] = None,
        include_expired: bool = False,
    ) -> GovernanceCheckResult:
        """
        Check governance status for a scope (L4/L5 ← L6 read).

        Used by domain orchestrators and workers before proceeding.

        Args:
            scope: What to check (file path, session ID, etc.)
            signal_type: Optional filter by signal type
            include_expired: Whether to include expired signals

        Returns:
            GovernanceCheckResult with blocking/warning status
        """
        now = datetime.now(timezone.utc)

        # Build query for active (non-superseded) signals
        conditions = [
            GovernanceSignal.scope == scope,
            GovernanceSignal.superseded_at.is_(None),
        ]

        if signal_type:
            conditions.append(GovernanceSignal.signal_type == signal_type)

        if not include_expired:
            conditions.append(
                or_(
                    GovernanceSignal.expires_at.is_(None),
                    GovernanceSignal.expires_at > now,
                )
            )

        stmt = select(GovernanceSignal).where(and_(*conditions))
        signals = list(self.session.execute(stmt).scalars().all())

        # Categorize signals
        blocking = []
        warnings = []

        for signal in signals:
            response = GovernanceSignalResponse(
                id=signal.id,
                signal_type=signal.signal_type,
                scope=signal.scope,
                decision=signal.decision,
                reason=signal.reason,
                constraints=signal.constraints,
                recorded_by=signal.recorded_by,
                recorded_at=signal.recorded_at,
                expires_at=signal.expires_at,
                superseded_by=signal.superseded_by,
                superseded_at=signal.superseded_at,
            )

            if signal.decision == "BLOCKED":
                blocking.append(response)
            elif signal.decision == "WARN":
                warnings.append(response)

        return GovernanceCheckResult(
            scope=scope,
            is_blocked=len(blocking) > 0,
            blocking_signals=blocking,
            warning_signals=warnings,
            last_checked=now,
        )

    def is_blocked(
        self, scope: str, signal_type: Optional[str] = None
    ) -> bool:
        """
        Quick check if scope is blocked (convenience method).

        Used by L4/L5 for fast governance checks.
        """
        result = self.check_governance(scope, signal_type)
        return result.is_blocked

    def get_active_signals(
        self, scope: str, signal_type: Optional[str] = None
    ) -> list[GovernanceSignal]:
        """Get all active (non-superseded, non-expired) signals for a scope."""
        now = datetime.now(timezone.utc)

        conditions = [
            GovernanceSignal.scope == scope,
            GovernanceSignal.superseded_at.is_(None),
            or_(
                GovernanceSignal.expires_at.is_(None),
                GovernanceSignal.expires_at > now,
            ),
        ]

        if signal_type:
            conditions.append(GovernanceSignal.signal_type == signal_type)

        stmt = select(GovernanceSignal).where(and_(*conditions))
        return list(self.session.execute(stmt).scalars().all())

    def clear_signal(
        self,
        scope: str,
        signal_type: str,
        cleared_by: str,
        reason: Optional[str] = None,
    ) -> GovernanceSignal:
        """
        Clear a governance block by recording a CLEAN signal.

        This supersedes any existing BLOCKED/WARN signals.
        """
        return self.record_signal(
            signal_type=signal_type,
            scope=scope,
            decision="CLEAN",
            recorded_by=cleared_by,
            reason=reason or f"Cleared by {cleared_by}",
        )


# Convenience functions for use without instantiating service

def check_governance_status(
    session: Session,
    scope: str,
    signal_type: Optional[str] = None,
) -> GovernanceCheckResult:
    """Check governance status for a scope."""
    service = GovernanceSignalService(session)
    return service.check_governance(scope, signal_type)


def is_governance_blocked(
    session: Session,
    scope: str,
    signal_type: Optional[str] = None,
) -> bool:
    """Quick check if scope is blocked."""
    service = GovernanceSignalService(session)
    return service.is_blocked(scope, signal_type)


def record_governance_signal(
    session: Session,
    signal_type: str,
    scope: str,
    decision: str,
    recorded_by: str,
    reason: Optional[str] = None,
    constraints: Optional[dict] = None,
) -> GovernanceSignal:
    """Record a governance signal."""
    service = GovernanceSignalService(session)
    return service.record_signal(
        signal_type=signal_type,
        scope=scope,
        decision=decision,
        recorded_by=recorded_by,
        reason=reason,
        constraints=constraints,
    )
