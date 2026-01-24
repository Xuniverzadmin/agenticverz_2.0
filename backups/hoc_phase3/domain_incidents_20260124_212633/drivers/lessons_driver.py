# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access for lessons_learned operations
# Callers: LessonsLearnedEngine (L4)
# Allowed Imports: ORM models, sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for lessons_learned table.
# NO business logic - only DB operations.
# Business logic (state machine, debounce decisions) stays in L4 engine.
#
# EXTRACTION STATUS:
# - 2026-01-23: Initial extraction from lessons_engine.py (PIN-468)
#
# ============================================================================
# L6 DRIVER INVENTORY — LESSONS DOMAIN (CANONICAL)
# ============================================================================
# Method                         | Purpose
# ------------------------------ | ------------------------------------------
# insert_lesson                  | Create lesson record
# fetch_lesson_by_id             | Get single lesson with all fields
# fetch_lessons_list             | List lessons with filters
# fetch_lesson_stats             | Aggregate stats by type/status
# update_lesson_deferred         | Set deferred status + deferred_until
# update_lesson_dismissed        | Set dismissed status + metadata
# update_lesson_converted        | Set converted_to_draft + proposal_id
# update_lesson_reactivated      | Set pending status, clear deferred_until
# fetch_debounce_count           | Check recent lessons for debounce
# fetch_expired_deferred         | Get deferred lessons past expiry
# insert_policy_proposal         | Create draft proposal (for conversion)
# commit                         | Transaction commit
# ============================================================================
# This is the SINGLE persistence authority for lessons_learned writes.
# Do NOT create competing drivers. Extend this file.
# ============================================================================

"""
Lessons Driver (L6)

Pure database operations for lessons_learned table.
All business logic stays in L4 engine.

Operations:
- Create lessons from various triggers
- Query lessons with filters
- Update lesson state (defer, dismiss, convert, reactivate)
- Debounce checks
- Scheduler support (expired deferred)

NO business logic:
- NO state machine validation (L4)
- NO debounce decisions (L4)
- NO severity mapping (L4)
- NO description generation (L4)

Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlmodel import Session


class LessonsDriver:
    """
    L6 driver for lessons_learned operations.

    Pure database access - no business logic.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    # =========================================================================
    # LESSON CREATION
    # =========================================================================

    def insert_lesson(
        self,
        lesson_id: str,
        tenant_id: str,
        lesson_type: str,
        severity: Optional[str],
        source_event_id: str,
        source_event_type: str,
        source_run_id: Optional[str],
        title: str,
        description: str,
        proposed_action: Optional[str],
        detected_pattern: Optional[Dict[str, Any]],
        now: datetime,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> bool:
        """
        Insert a new lesson record.

        Args:
            lesson_id: Generated lesson UUID
            tenant_id: Tenant scope
            lesson_type: Type (failure, near_threshold, critical_success)
            severity: Severity level (optional for some types)
            source_event_id: Source event UUID
            source_event_type: Event type (run, incident, etc.)
            source_run_id: Source run UUID (optional)
            title: Lesson title
            description: Lesson description
            proposed_action: Suggested action
            detected_pattern: JSON pattern data
            now: Timestamp
            is_synthetic: SDSR flag
            synthetic_scenario_id: SDSR scenario ID

        Returns:
            True if inserted, False on conflict
        """
        result = self._session.execute(
            text("""
                INSERT INTO lessons_learned (
                    id, tenant_id, lesson_type, severity,
                    source_event_id, source_event_type, source_run_id,
                    title, description, proposed_action, detected_pattern,
                    status, created_at,
                    is_synthetic, synthetic_scenario_id
                ) VALUES (
                    :id, :tenant_id, :lesson_type, :severity,
                    :source_event_id, :source_event_type, :source_run_id,
                    :title, :description, :proposed_action, :detected_pattern::jsonb,
                    'pending', :created_at,
                    :is_synthetic, :synthetic_scenario_id
                )
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """),
            {
                "id": lesson_id,
                "tenant_id": tenant_id,
                "lesson_type": lesson_type,
                "severity": severity,
                "source_event_id": source_event_id,
                "source_event_type": source_event_type,
                "source_run_id": source_run_id,
                "title": title,
                "description": description,
                "proposed_action": proposed_action,
                "detected_pattern": json.dumps(detected_pattern) if detected_pattern else None,
                "created_at": now,
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
            },
        )
        row = result.fetchone()
        return row is not None

    # =========================================================================
    # LESSON QUERIES
    # =========================================================================

    def fetch_lesson_by_id(
        self,
        lesson_id: str,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific lesson by ID.

        Args:
            lesson_id: Lesson UUID string
            tenant_id: Tenant scope (for isolation)

        Returns:
            Lesson dict or None if not found
        """
        result = self._session.execute(
            text("""
                SELECT
                    id, tenant_id, lesson_type, severity,
                    source_event_id, source_event_type, source_run_id,
                    title, description, proposed_action, detected_pattern,
                    status, draft_proposal_id,
                    created_at, converted_at, deferred_until,
                    dismissed_at, dismissed_by, dismissed_reason
                FROM lessons_learned
                WHERE id = :lesson_id AND tenant_id = :tenant_id
            """),
            {"lesson_id": lesson_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row[0]),
            "tenant_id": row[1],
            "lesson_type": row[2],
            "severity": row[3],
            "source_event_id": str(row[4]) if row[4] else None,
            "source_event_type": row[5],
            "source_run_id": str(row[6]) if row[6] else None,
            "title": row[7],
            "description": row[8],
            "proposed_action": row[9],
            "detected_pattern": row[10],
            "status": row[11],
            "draft_proposal_id": str(row[12]) if row[12] else None,
            "created_at": row[13].isoformat() if row[13] else None,
            "converted_at": row[14].isoformat() if row[14] else None,
            "deferred_until": row[15].isoformat() if row[15] else None,
            "dismissed_at": row[16].isoformat() if row[16] else None,
            "dismissed_by": row[17],
            "dismissed_reason": row[18],
        }

    def fetch_lessons_list(
        self,
        tenant_id: str,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List lessons with optional filters.

        Args:
            tenant_id: Tenant scope
            lesson_type: Filter by type
            status: Filter by status
            severity: Filter by severity
            include_synthetic: Include SDSR lessons
            limit: Max results
            offset: Pagination offset

        Returns:
            List of lesson summary dicts
        """
        filters = ["tenant_id = :tenant_id"]
        params: Dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        if not include_synthetic:
            filters.append("is_synthetic = false")

        if lesson_type:
            filters.append("lesson_type = :lesson_type")
            params["lesson_type"] = lesson_type

        if status:
            filters.append("status = :status")
            params["status"] = status

        if severity:
            filters.append("severity = :severity")
            params["severity"] = severity

        where_clause = " AND ".join(filters)

        result = self._session.execute(
            text(f"""
                SELECT
                    id, tenant_id, lesson_type, severity,
                    title, status, source_event_type,
                    created_at, proposed_action IS NOT NULL as has_proposed_action
                FROM lessons_learned
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        )
        rows = result.fetchall()

        return [
            {
                "id": str(row[0]),
                "tenant_id": row[1],
                "lesson_type": row[2],
                "severity": row[3],
                "title": row[4],
                "status": row[5],
                "source_event_type": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "has_proposed_action": row[8],
            }
            for row in rows
        ]

    def fetch_lesson_stats(self, tenant_id: str) -> List[tuple]:
        """
        Get lesson counts grouped by type and status.

        Args:
            tenant_id: Tenant scope

        Returns:
            List of (lesson_type, status, count) tuples
        """
        result = self._session.execute(
            text("""
                SELECT lesson_type, status, COUNT(*) as count
                FROM lessons_learned
                WHERE tenant_id = :tenant_id
                GROUP BY lesson_type, status
            """),
            {"tenant_id": tenant_id},
        )
        return list(result.fetchall())

    # =========================================================================
    # STATE TRANSITIONS
    # =========================================================================

    def update_lesson_deferred(
        self,
        lesson_id: str,
        tenant_id: str,
        deferred_status: str,
        defer_until: datetime,
    ) -> bool:
        """
        Update lesson to deferred status.

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant scope
            deferred_status: Status value (should be 'deferred')
            defer_until: When to resurface

        Returns:
            True if updated, False if not found or wrong status
        """
        result = self._session.execute(
            text("""
                UPDATE lessons_learned
                SET status = :status, deferred_until = :defer_until
                WHERE id = :lesson_id
                  AND tenant_id = :tenant_id
                  AND status = 'pending'
                RETURNING id
            """),
            {
                "status": deferred_status,
                "defer_until": defer_until,
                "lesson_id": lesson_id,
                "tenant_id": tenant_id,
            },
        )
        row = result.fetchone()
        return row is not None

    def update_lesson_dismissed(
        self,
        lesson_id: str,
        tenant_id: str,
        dismissed_status: str,
        dismissed_at: datetime,
        dismissed_by: str,
        reason: str,
    ) -> bool:
        """
        Update lesson to dismissed status.

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant scope
            dismissed_status: Status value (should be 'dismissed')
            dismissed_at: Timestamp
            dismissed_by: Who dismissed
            reason: Dismissal reason

        Returns:
            True if updated, False if not found or wrong status
        """
        result = self._session.execute(
            text("""
                UPDATE lessons_learned
                SET status = :status,
                    dismissed_at = :dismissed_at,
                    dismissed_by = :dismissed_by,
                    dismissed_reason = :reason
                WHERE id = :lesson_id
                  AND tenant_id = :tenant_id
                  AND status = 'pending'
                RETURNING id
            """),
            {
                "status": dismissed_status,
                "dismissed_at": dismissed_at,
                "dismissed_by": dismissed_by,
                "reason": reason,
                "lesson_id": lesson_id,
                "tenant_id": tenant_id,
            },
        )
        row = result.fetchone()
        return row is not None

    def update_lesson_converted(
        self,
        lesson_id: str,
        tenant_id: str,
        converted_status: str,
        proposal_id: str,
        converted_at: datetime,
    ) -> bool:
        """
        Update lesson to converted_to_draft status.

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant scope
            converted_status: Status value (should be 'converted_to_draft')
            proposal_id: Created proposal UUID
            converted_at: Timestamp

        Returns:
            True if updated, False if not found or wrong status
        """
        result = self._session.execute(
            text("""
                UPDATE lessons_learned
                SET status = :status,
                    draft_proposal_id = :proposal_id,
                    converted_at = :converted_at
                WHERE id = :lesson_id
                  AND tenant_id = :tenant_id
                  AND status = 'pending'
                RETURNING id
            """),
            {
                "status": converted_status,
                "proposal_id": proposal_id,
                "converted_at": converted_at,
                "lesson_id": lesson_id,
                "tenant_id": tenant_id,
            },
        )
        row = result.fetchone()
        return row is not None

    def update_lesson_reactivated(
        self,
        lesson_id: str,
        tenant_id: str,
        pending_status: str,
        from_status: str,
    ) -> bool:
        """
        Reactivate a deferred lesson to pending.

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant scope
            pending_status: Status value (should be 'pending')
            from_status: Expected current status (should be 'deferred')

        Returns:
            True if updated, False if not found or wrong status
        """
        result = self._session.execute(
            text("""
                UPDATE lessons_learned
                SET status = :status,
                    deferred_until = NULL
                WHERE id = :lesson_id
                  AND tenant_id = :tenant_id
                  AND status = :from_status
                RETURNING id
            """),
            {
                "status": pending_status,
                "from_status": from_status,
                "lesson_id": lesson_id,
                "tenant_id": tenant_id,
            },
        )
        row = result.fetchone()
        return row is not None

    # =========================================================================
    # DEBOUNCE & SCHEDULER SUPPORT
    # =========================================================================

    def fetch_debounce_count(
        self,
        tenant_id: str,
        lesson_type: str,
        metric_type: str,
        hours: int,
        threshold_band: Optional[str] = None,
    ) -> int:
        """
        Count recent lessons for debounce check.

        Args:
            tenant_id: Tenant scope
            lesson_type: Lesson type to check
            metric_type: Metric type (budget, tokens, rate)
            hours: Lookback window in hours
            threshold_band: Optional band for near-threshold granularity

        Returns:
            Count of matching lessons in window
        """
        base_query = f"""
            SELECT COUNT(*) as count
            FROM lessons_learned
            WHERE tenant_id = :tenant_id
              AND lesson_type = :lesson_type
              AND detected_pattern->>'threshold_type' = :metric_type
              AND created_at >= NOW() - INTERVAL '{hours} hours'
        """

        params: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "lesson_type": lesson_type,
            "metric_type": metric_type,
        }

        if threshold_band:
            base_query += """
              AND detected_pattern->>'threshold_band' = :threshold_band
            """
            params["threshold_band"] = threshold_band

        result = self._session.execute(text(base_query), params)
        row = result.fetchone()
        return row[0] if row else 0

    def fetch_expired_deferred(
        self,
        deferred_status: str,
        limit: int = 100,
    ) -> List[tuple]:
        """
        Get deferred lessons whose deferred_until has passed.

        Args:
            deferred_status: Status value to match
            limit: Max results

        Returns:
            List of (lesson_id, tenant_id) tuples
        """
        result = self._session.execute(
            text("""
                SELECT id, tenant_id
                FROM lessons_learned
                WHERE status = :status
                  AND deferred_until IS NOT NULL
                  AND deferred_until <= NOW()
                ORDER BY deferred_until ASC
                LIMIT :limit
            """),
            {"status": deferred_status, "limit": limit},
        )
        return list(result.fetchall())

    # =========================================================================
    # POLICY PROPOSAL (for conversion)
    # =========================================================================

    def insert_policy_proposal_from_lesson(
        self,
        proposal_id: str,
        tenant_id: str,
        title: str,
        description: str,
        proposed_action: Optional[str],
        source_lesson_id: str,
        created_at: datetime,
        created_by: str,
    ) -> bool:
        """
        Insert a draft policy proposal from a lesson.

        Args:
            proposal_id: Generated proposal UUID
            tenant_id: Tenant scope
            title: Proposal title
            description: Proposal description
            proposed_action: Suggested action
            source_lesson_id: Source lesson UUID
            created_at: Timestamp
            created_by: Creator identifier

        Returns:
            True if inserted
        """
        self._session.execute(
            text("""
                INSERT INTO policy_proposals (
                    id, tenant_id, title, description,
                    proposed_action, status, source_type, source_id,
                    created_at, created_by
                ) VALUES (
                    :id, :tenant_id, :title, :description,
                    :proposed_action, 'draft', 'lesson', :source_id,
                    :created_at, :created_by
                )
            """),
            {
                "id": proposal_id,
                "tenant_id": tenant_id,
                "title": title,
                "description": description,
                "proposed_action": proposed_action,
                "source_id": source_lesson_id,
                "created_at": created_at,
                "created_by": created_by,
            },
        )
        return True

    def commit(self) -> None:
        """Commit the current transaction."""
        self._session.commit()


def get_lessons_driver(session: Session) -> LessonsDriver:
    """Factory function to get LessonsDriver instance."""
    return LessonsDriver(session)


__all__ = [
    "LessonsDriver",
    "get_lessons_driver",
]
