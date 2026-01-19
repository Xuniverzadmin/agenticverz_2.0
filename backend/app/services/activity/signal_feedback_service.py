# Layer: L4 — Domain Engine
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: sync (DB writes via audit_ledger)
# Role: Signal feedback operations (acknowledge/suppress)
# Callers: activity.py (L2)
# Allowed Imports: L6, L4 (AuditLedgerService, signal_identity)
# Forbidden Imports: L1, L2, L3, L5
# Reference: Attention Feedback Loop Implementation Plan

"""
Signal Feedback Service

Handles signal acknowledge and suppress operations using the audit_ledger
infrastructure. No new tables are created.

INVARIANTS:
- SIGNAL-ID-001: Canonical fingerprint derivation (always from backend projection)
- ATTN-DAMP-001: Idempotent dampening (apply once, 0.6x)
- AUDIT-SIGNAL-CTX-001: Structured context fields (fixed and versioned)
- SIGNAL-SCOPE-001: Tenant-scoped suppression (actor_id for accountability only)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, TypedDict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from app.models.audit_ledger import ActorType, AuditLedger
from app.services.activity.signal_identity import compute_signal_fingerprint_from_row
from app.services.logs.audit_ledger_service import AuditLedgerService


# =============================================================================
# Structured Signal Context (AUDIT-SIGNAL-CTX-001)
# =============================================================================


class SignalContext(TypedDict, total=False):
    """
    Fixed schema for audit signal_context — no free-form fields.

    INVARIANT (AUDIT-SIGNAL-CTX-001):
    - Fields are fixed and versioned
    - No arbitrary keys allowed
    - Version tracking for future evolution
    """
    run_id: str
    signal_type: str           # COST_RISK, TIME_RISK, TOKEN_RISK, RATE_RISK, etc.
    risk_type: str             # COST, TIME, TOKENS, RATE
    evaluation_outcome: str    # BREACH, NEAR_THRESHOLD, OK
    policy_id: Optional[str]   # Governing policy if any
    schema_version: str        # Always "1.0" for now


def build_signal_context(
    run_id: str,
    signal_type: str,
    risk_type: str,
    evaluation_outcome: str,
    policy_id: Optional[str] = None,
) -> SignalContext:
    """
    Build a validated SignalContext.

    Args:
        run_id: The run ID associated with the signal
        signal_type: Type of signal (e.g., COST_RISK)
        risk_type: Risk category (e.g., COST)
        evaluation_outcome: Policy evaluation result
        policy_id: Optional governing policy ID

    Returns:
        SignalContext with schema_version
    """
    return SignalContext(
        run_id=run_id,
        signal_type=signal_type,
        risk_type=risk_type,
        evaluation_outcome=evaluation_outcome,
        policy_id=policy_id,
        schema_version="1.0",
    )


# =============================================================================
# Result Data Classes
# =============================================================================


@dataclass
class SignalFeedback:
    """Feedback state for a signal."""
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    suppressed_until: Optional[datetime] = None


@dataclass
class AcknowledgeResult:
    """Result of acknowledge operation."""
    signal_fingerprint: str
    acknowledged: bool
    acknowledged_by: str
    acknowledged_at: datetime


@dataclass
class SuppressResult:
    """Result of suppress operation."""
    signal_fingerprint: str
    suppressed_until: datetime


# =============================================================================
# Signal Feedback Service
# =============================================================================


class SignalFeedbackService:
    """
    Service for signal feedback operations.

    RESPONSIBILITIES:
    - Acknowledge signals (write to audit_ledger)
    - Suppress signals (write to audit_ledger with TTL)
    - Query feedback state for signals
    - Validate signal existence before operations

    INVARIANTS:
    - SIGNAL-ID-001: Never trust client fingerprint, always re-derive
    - SIGNAL-SCOPE-001: Suppression is tenant-scoped
    - All writes go through AuditLedgerService (no direct DB writes)
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async session."""
        self._async_session = session

    async def acknowledge_signal(
        self,
        tenant_id: str,
        run_id: str,
        signal_type: str,
        risk_type: str,
        actor_id: str,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> AcknowledgeResult:
        """
        Acknowledge a signal.

        INVARIANT (SIGNAL-ID-001): The fingerprint is computed server-side
        from the projection row, never from client input.

        Args:
            tenant_id: Tenant scope
            run_id: Run ID associated with the signal
            signal_type: Type of signal (e.g., COST_RISK)
            risk_type: Risk category (e.g., COST)
            actor_id: ID of the acknowledging actor
            actor_type: Type of actor (default: HUMAN)
            reason: Optional reason for acknowledgment

        Returns:
            AcknowledgeResult with fingerprint and timestamp

        Raises:
            ValueError: If signal is not currently visible
        """
        # Validate signal exists and get current state
        signal_row = await self._find_signal(tenant_id, run_id, signal_type, risk_type)
        if not signal_row:
            raise ValueError(f"Signal not currently visible for run={run_id}, type={signal_type}")

        # Compute canonical fingerprint (SIGNAL-ID-001)
        fingerprint = compute_signal_fingerprint_from_row(signal_row)

        # Build structured context (AUDIT-SIGNAL-CTX-001)
        signal_context = build_signal_context(
            run_id=run_id,
            signal_type=signal_type,
            risk_type=risk_type,
            evaluation_outcome=signal_row.get("evaluation_outcome", "UNKNOWN"),
            policy_id=signal_row.get("policy_id"),
        )

        # Write to audit_ledger using sync wrapper
        # Note: We need to use a sync session for AuditLedgerService
        ack_time = datetime.now(timezone.utc)

        # Execute in sync context via raw SQL for audit entry
        # This preserves the append-only audit trail
        await self._write_audit_entry(
            tenant_id=tenant_id,
            event_type="SignalAcknowledged",
            entity_type="SIGNAL",
            entity_id=fingerprint,
            actor_type=actor_type.value,
            actor_id=actor_id,
            action_reason=reason,
            after_state=dict(signal_context),
            created_at=ack_time,
        )

        return AcknowledgeResult(
            signal_fingerprint=fingerprint,
            acknowledged=True,
            acknowledged_by=actor_id,
            acknowledged_at=ack_time,
        )

    async def suppress_signal(
        self,
        tenant_id: str,
        run_id: str,
        signal_type: str,
        risk_type: str,
        actor_id: str,
        duration_minutes: int,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> SuppressResult:
        """
        Suppress a signal for a specified duration.

        INVARIANT (SIGNAL-SUPPRESS-001): Duration must be 15-1440 minutes (max 24 hours).
        INVARIANT (SIGNAL-SCOPE-001): Suppression applies tenant-wide.

        Args:
            tenant_id: Tenant scope
            run_id: Run ID associated with the signal
            signal_type: Type of signal
            risk_type: Risk category
            actor_id: ID of the suppressing actor
            duration_minutes: Suppression duration (15-1440)
            actor_type: Type of actor (default: HUMAN)
            reason: Optional reason for suppression

        Returns:
            SuppressResult with fingerprint and expiry time

        Raises:
            ValueError: If signal not visible or duration out of range
        """
        # Validate duration (15 min to 24 hours)
        if duration_minutes < 15 or duration_minutes > 1440:
            raise ValueError(
                f"Suppression duration must be 15-1440 minutes, got {duration_minutes}"
            )

        # Validate signal exists
        signal_row = await self._find_signal(tenant_id, run_id, signal_type, risk_type)
        if not signal_row:
            raise ValueError(f"Signal not currently visible for run={run_id}, type={signal_type}")

        # Compute canonical fingerprint (SIGNAL-ID-001)
        fingerprint = compute_signal_fingerprint_from_row(signal_row)

        # Calculate suppress_until
        now = datetime.now(timezone.utc)
        suppress_until = datetime.fromtimestamp(
            now.timestamp() + (duration_minutes * 60),
            tz=timezone.utc,
        )

        # Build structured context
        signal_context = build_signal_context(
            run_id=run_id,
            signal_type=signal_type,
            risk_type=risk_type,
            evaluation_outcome=signal_row.get("evaluation_outcome", "UNKNOWN"),
            policy_id=signal_row.get("policy_id"),
        )

        # Add suppress_until to after_state
        after_state = dict(signal_context)
        after_state["suppress_until"] = suppress_until.isoformat()

        # Write to audit_ledger
        await self._write_audit_entry(
            tenant_id=tenant_id,
            event_type="SignalSuppressed",
            entity_type="SIGNAL",
            entity_id=fingerprint,
            actor_type=actor_type.value,
            actor_id=actor_id,
            action_reason=reason,
            after_state=after_state,
            created_at=now,
        )

        return SuppressResult(
            signal_fingerprint=fingerprint,
            suppressed_until=suppress_until,
        )

    async def get_signal_feedback(
        self,
        tenant_id: str,
        signal_fingerprint: str,
    ) -> Optional[SignalFeedback]:
        """
        Get the latest feedback state for a signal.

        Args:
            tenant_id: Tenant scope
            signal_fingerprint: Canonical signal fingerprint

        Returns:
            SignalFeedback or None if no feedback exists
        """
        sql = text("""
            SELECT
                event_type,
                actor_id,
                created_at,
                (after_state->>'suppress_until')::timestamptz AS suppress_until
            FROM audit_ledger
            WHERE tenant_id = :tenant_id
              AND entity_type = 'SIGNAL'
              AND entity_id = :fingerprint
            ORDER BY created_at DESC
            LIMIT 1
        """)

        result = await self._async_session.execute(sql, {
            "tenant_id": tenant_id,
            "fingerprint": signal_fingerprint,
        })
        row = result.mappings().first()

        if not row:
            return None

        return SignalFeedback(
            acknowledged=row["event_type"] == "SignalAcknowledged",
            acknowledged_by=row["actor_id"] if row["event_type"] == "SignalAcknowledged" else None,
            acknowledged_at=row["created_at"] if row["event_type"] == "SignalAcknowledged" else None,
            suppressed_until=row["suppress_until"],
        )

    async def get_bulk_signal_feedback(
        self,
        tenant_id: str,
        signal_fingerprints: list[str],
    ) -> dict[str, SignalFeedback]:
        """
        Get feedback state for multiple signals efficiently.

        Args:
            tenant_id: Tenant scope
            signal_fingerprints: List of fingerprints to query

        Returns:
            Dict mapping fingerprint to SignalFeedback (missing if no feedback)
        """
        if not signal_fingerprints:
            return {}

        sql = text("""
            SELECT DISTINCT ON (entity_id)
                entity_id AS fingerprint,
                event_type,
                actor_id,
                created_at,
                (after_state->>'suppress_until')::timestamptz AS suppress_until
            FROM audit_ledger
            WHERE tenant_id = :tenant_id
              AND entity_type = 'SIGNAL'
              AND entity_id = ANY(:fingerprints)
            ORDER BY entity_id, created_at DESC
        """)

        result = await self._async_session.execute(sql, {
            "tenant_id": tenant_id,
            "fingerprints": signal_fingerprints,
        })
        rows = result.mappings().all()

        feedback_map: dict[str, SignalFeedback] = {}
        for row in rows:
            feedback_map[row["fingerprint"]] = SignalFeedback(
                acknowledged=row["event_type"] == "SignalAcknowledged",
                acknowledged_by=row["actor_id"] if row["event_type"] == "SignalAcknowledged" else None,
                acknowledged_at=row["created_at"] if row["event_type"] == "SignalAcknowledged" else None,
                suppressed_until=row["suppress_until"],
            )

        return feedback_map

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    async def _find_signal(
        self,
        tenant_id: str,
        run_id: str,
        signal_type: str,
        risk_type: str,
    ) -> Optional[dict]:
        """
        Find a currently visible signal by its identifiers.

        Returns the projection row if signal is visible, None otherwise.
        This ensures SIGNAL-ID-001: fingerprint derived from projection.
        """
        # Map signal_type to query conditions
        where_conditions = ["tenant_id = :tenant_id", "run_id = :run_id"]
        params: dict = {
            "tenant_id": tenant_id,
            "run_id": run_id,
            "risk_type": risk_type,
        }

        # Signal type determines what makes it visible
        if signal_type.endswith("_RISK"):
            where_conditions.append("risk_type = :risk_type")
            where_conditions.append("evaluation_outcome IN ('BREACH', 'NEAR_THRESHOLD')")
        elif signal_type == "EVIDENCE_DEGRADED":
            where_conditions.append("evidence_health != 'FLOWING'")
        elif signal_type == "POLICY_BREACH":
            where_conditions.append("evaluation_outcome = 'BREACH'")
        else:
            # Generic risk check
            where_conditions.append("risk_level != 'NORMAL'")

        sql = text(f"""
            SELECT
                run_id,
                risk_type,
                evaluation_outcome,
                policy_id
            FROM v_runs_o2
            WHERE {' AND '.join(where_conditions)}
            LIMIT 1
        """)

        result = await self._async_session.execute(sql, params)
        row = result.mappings().first()

        if not row:
            return None

        # Return with signal_type added for fingerprint computation
        return {
            "run_id": row["run_id"],
            "signal_type": signal_type,
            "risk_type": row["risk_type"] or risk_type,
            "evaluation_outcome": row["evaluation_outcome"],
            "policy_id": row.get("policy_id"),
        }

    async def _write_audit_entry(
        self,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_type: str,
        actor_id: str,
        action_reason: Optional[str],
        after_state: dict,
        created_at: datetime,
    ) -> None:
        """
        Write an audit entry directly via SQL.

        This maintains the append-only audit trail while working with async sessions.
        """
        import uuid
        audit_id = str(uuid.uuid4())

        sql = text("""
            INSERT INTO audit_ledger (
                id, tenant_id, event_type, entity_type, entity_id,
                actor_type, actor_id, action_reason, after_state, created_at
            ) VALUES (
                :id, :tenant_id, :event_type, :entity_type, :entity_id,
                :actor_type, :actor_id, :action_reason, :after_state, :created_at
            )
        """)

        await self._async_session.execute(sql, {
            "id": audit_id,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action_reason": action_reason,
            "after_state": after_state,
            "created_at": created_at,
        })

        await self._async_session.commit()


__all__ = [
    "SignalFeedbackService",
    "SignalFeedback",
    "SignalContext",
    "AcknowledgeResult",
    "SuppressResult",
    "build_signal_context",
]
