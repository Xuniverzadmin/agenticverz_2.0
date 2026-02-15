# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: signal_feedback
#   Writes: signal_feedback
# Role: Signal feedback persistence operations
# Callers: signal_feedback_engine.py (L5 engine), activity_handler.py (L4)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: UC-010 Activity Feedback Lifecycle
# artifact_class: CODE

"""
Signal Feedback Driver (L6 Data Access)

Handles database operations for signal feedback lifecycle:
- Insert ack/suppress/reopen records
- Query current feedback state
- List active suppressions
- Cleanup expired feedback
- Bulk operations with target_set_hash

L6 INVARIANT: Never commit/rollback — L4 owns transaction boundaries.
"""

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SignalFeedbackDriver:
    """L6 Driver for signal feedback persistence."""

    async def insert_feedback(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        signal_fingerprint: str,
        feedback_state: str,
        as_of: str,
        actor_id: str,
        ttl_seconds: Optional[int] = None,
        expires_at: Optional[str] = None,
        bulk_action_id: Optional[str] = None,
        target_set_hash: Optional[str] = None,
        target_count: Optional[int] = None,
    ) -> dict[str, Any]:
        """Insert a feedback record. Returns the inserted row as dict."""
        result = await session.execute(
            text("""
                INSERT INTO signal_feedback
                    (tenant_id, signal_fingerprint, feedback_state, as_of,
                     actor_id, ttl_seconds, expires_at, bulk_action_id,
                     target_set_hash, target_count, created_at, updated_at)
                VALUES
                    (:tenant_id, :signal_fingerprint, :feedback_state,
                     :as_of::timestamptz, :actor_id, :ttl_seconds,
                     :expires_at::timestamptz, :bulk_action_id,
                     :target_set_hash, :target_count, NOW(), NOW())
                RETURNING id, tenant_id, signal_fingerprint, feedback_state,
                          as_of, actor_id, ttl_seconds, expires_at,
                          bulk_action_id, created_at
            """),
            {
                "tenant_id": tenant_id,
                "signal_fingerprint": signal_fingerprint,
                "feedback_state": feedback_state,
                "as_of": as_of,
                "actor_id": actor_id,
                "ttl_seconds": ttl_seconds,
                "expires_at": expires_at,
                "bulk_action_id": bulk_action_id,
                "target_set_hash": target_set_hash,
                "target_count": target_count,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else {}

    async def query_feedback(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        signal_fingerprint: str,
    ) -> Optional[dict[str, Any]]:
        """Get most recent feedback for a signal (tenant-scoped)."""
        result = await session.execute(
            text("""
                SELECT id, tenant_id, signal_fingerprint, feedback_state,
                       as_of, actor_id, ttl_seconds, expires_at,
                       bulk_action_id, created_at, updated_at
                FROM signal_feedback
                WHERE tenant_id = :tenant_id
                  AND signal_fingerprint = :signal_fingerprint
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "signal_fingerprint": signal_fingerprint},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_feedback_state(
        self,
        session: AsyncSession,
        *,
        feedback_id: int,
        new_state: str,
    ) -> bool:
        """Update feedback_state for a record. Returns True if updated."""
        result = await session.execute(
            text("""
                UPDATE signal_feedback
                SET feedback_state = :new_state, updated_at = NOW()
                WHERE id = :feedback_id
            """),
            {"feedback_id": feedback_id, "new_state": new_state},
        )
        return result.rowcount > 0

    async def list_active_suppressions(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        as_of: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List currently active (non-expired) suppressions."""
        result = await session.execute(
            text("""
                SELECT id, signal_fingerprint, feedback_state, as_of,
                       actor_id, ttl_seconds, expires_at, created_at
                FROM signal_feedback
                WHERE tenant_id = :tenant_id
                  AND feedback_state = 'SUPPRESSED'
                  AND (expires_at IS NULL OR expires_at > :as_of::timestamptz)
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"tenant_id": tenant_id, "as_of": as_of, "limit": limit},
        )
        return [dict(row) for row in result.mappings().all()]

    async def count_expired(
        self,
        session: AsyncSession,
        *,
        as_of: str,
    ) -> int:
        """Count expired suppressions (for audit)."""
        result = await session.execute(
            text("""
                SELECT COUNT(*) AS cnt
                FROM signal_feedback
                WHERE feedback_state = 'SUPPRESSED'
                  AND expires_at IS NOT NULL
                  AND expires_at <= :as_of::timestamptz
            """),
            {"as_of": as_of},
        )
        row = result.mappings().first()
        return row["cnt"] if row else 0

    async def mark_expired_as_evaluated(
        self,
        session: AsyncSession,
        *,
        as_of: str,
    ) -> int:
        """Mark expired suppressions as EVALUATED. Returns count updated."""
        result = await session.execute(
            text("""
                UPDATE signal_feedback
                SET feedback_state = 'EVALUATED', updated_at = NOW()
                WHERE feedback_state = 'SUPPRESSED'
                  AND expires_at IS NOT NULL
                  AND expires_at <= :as_of::timestamptz
            """),
            {"as_of": as_of},
        )
        return result.rowcount
