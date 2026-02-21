# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: aos_trace_mismatches, aos_traces
#   Writes: aos_trace_mismatches
# Database:
#   Scope: domain (logs)
#   Models: aos_trace_mismatches, aos_traces
# Role: Data access for trace mismatch operations (report, list, resolve, bulk)
# Callers: trace_mismatch_engine.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit() — L6 DOES NOT COMMIT (caller owns transaction)
# Reference: PIN-470, M8 Trace System, L2 first-principles purity migration
# artifact_class: CODE

"""
Trace Mismatch Driver (L6)

Pure database operations for trace mismatch management.

All methods are pure DB operations — no business logic.
No GitHub/Slack notification logic — that stays in L5 engine.

Operations:
- Query mismatches with filtering
- Verify trace tenant ownership
- Insert mismatch records
- Update mismatch records (resolve, set issue URL)
- Bulk query mismatches by IDs
"""

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TraceMismatchDriver:
    """
    L6 driver for trace mismatch data access.

    Pure database access — no business logic.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_trace_tenant(self, trace_id: str) -> Optional[str]:
        """Fetch tenant_id for a trace. Returns None if trace not found."""
        result = await self._session.execute(
            text("SELECT tenant_id FROM aos_traces WHERE trace_id = :trace_id"),
            {"trace_id": trace_id},
        )
        row = result.first()
        return row[0] if row else None

    async def insert_mismatch(
        self,
        mismatch_id: str,
        trace_id: str,
        tenant_id: str,
        reported_by: str,
        step_index: int,
        reason: str,
        expected_hash: Optional[str],
        actual_hash: Optional[str],
        details: dict,
    ) -> None:
        """Insert a mismatch record."""
        await self._session.execute(
            text("""
                INSERT INTO aos_trace_mismatches
                (id, trace_id, tenant_id, reported_by, step_index, reason,
                 expected_hash, actual_hash, details)
                VALUES (:id, :trace_id, :tenant_id, :reported_by, :step_index,
                        :reason, :expected_hash, :actual_hash, :details)
            """),
            {
                "id": mismatch_id,
                "trace_id": trace_id,
                "tenant_id": tenant_id,
                "reported_by": reported_by,
                "step_index": step_index,
                "reason": reason,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "details": str(details),
            },
        )
        # L6 does NOT commit — L4 handler owns transaction boundary

    async def update_mismatch_issue_url(
        self,
        mismatch_id: str,
        issue_url: str,
    ) -> None:
        """Update mismatch with GitHub issue URL."""
        await self._session.execute(
            text("""
                UPDATE aos_trace_mismatches
                SET issue_url = :issue_url, notification_sent = TRUE
                WHERE id = :id
            """),
            {"issue_url": issue_url, "id": mismatch_id},
        )
        # L6 does NOT commit — L4 handler owns transaction boundary

    async def update_mismatch_notification(
        self,
        mismatch_id: str,
    ) -> None:
        """Mark notification sent for a mismatch."""
        await self._session.execute(
            text("""
                UPDATE aos_trace_mismatches
                SET notification_sent = TRUE
                WHERE id = :id
            """),
            {"id": mismatch_id},
        )
        # L6 does NOT commit — L4 handler owns transaction boundary

    async def resolve_mismatch(
        self,
        mismatch_id: str,
        trace_id: str,
        resolved_by: str,
    ) -> Optional[dict[str, Any]]:
        """Resolve a mismatch. Returns the row if found, None otherwise."""
        result = await self._session.execute(
            text("""
                UPDATE aos_trace_mismatches
                SET resolved = TRUE, resolved_at = now(), resolved_by = :resolved_by
                WHERE id = :id AND trace_id = :trace_id
                RETURNING id, issue_url
            """),
            {"resolved_by": resolved_by, "id": mismatch_id, "trace_id": trace_id},
        )
        row = result.first()
        # L6 does NOT commit — L4 handler owns transaction boundary
        if not row:
            return None
        return {"id": str(row[0]), "issue_url": row[1]}

    async def fetch_mismatches_for_trace(
        self,
        trace_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch all mismatches for a trace."""
        result = await self._session.execute(
            text("""
                SELECT id, step_index, reason, expected_hash, actual_hash, details,
                       notification_sent, issue_url, resolved, resolved_at, resolved_by, created_at
                FROM aos_trace_mismatches
                WHERE trace_id = :trace_id
                ORDER BY created_at DESC
            """),
            {"trace_id": trace_id},
        )
        return [
            {
                "mismatch_id": str(r[0]),
                "step_index": r[1],
                "reason": r[2],
                "expected_hash": r[3],
                "actual_hash": r[4],
                "details": r[5],
                "notification_sent": r[6],
                "issue_url": r[7],
                "resolved": r[8],
                "resolved_at": r[9].isoformat() if r[9] else None,
                "resolved_by": r[10],
                "created_at": r[11].isoformat(),
            }
            for r in result.all()
        ]

    async def fetch_all_mismatches(
        self,
        window_since: Optional[Any] = None,
        resolved_filter: Optional[bool] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Fetch all mismatches with optional filters."""
        conditions = []
        params: dict[str, Any] = {"limit": limit}

        if window_since is not None:
            conditions.append("created_at >= :since")
            params["since"] = window_since

        if resolved_filter is not None:
            conditions.append("resolved = :resolved")
            params["resolved"] = resolved_filter

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Get mismatches
        result = await self._session.execute(
            text(f"""
                SELECT id, trace_id, step_index, reason, expected_hash, actual_hash,
                       details, resolved, resolved_at, created_at
                FROM aos_trace_mismatches
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            params,
        )
        rows = result.all()

        # Get summary counts
        count_base = "SELECT COUNT(*) FROM aos_trace_mismatches"
        count_where = f"WHERE {conditions[0]}" if window_since and conditions else ""
        count_params = {"since": params.get("since")} if window_since else {}

        open_result = await self._session.execute(
            text(f"{count_base} {count_where} {'AND' if count_where else 'WHERE'} resolved = FALSE"),
            count_params,
        )
        open_count = open_result.scalar() or 0

        resolved_result = await self._session.execute(
            text(f"{count_base} {count_where} {'AND' if count_where else 'WHERE'} resolved = TRUE"),
            count_params,
        )
        resolved_count = resolved_result.scalar() or 0

        return {
            "rows": [
                {
                    "id": str(r[0]),
                    "trace_id": r[1],
                    "step_index": r[2],
                    "reason": r[3],
                    "expected_hash": r[4],
                    "actual_hash": r[5],
                    "details": r[6],
                    "resolved": r[7],
                    "resolved_at": r[8].isoformat() if r[8] else None,
                    "created_at": r[9].isoformat() if r[9] else None,
                }
                for r in rows
            ],
            "open_count": open_count,
            "resolved_count": resolved_count,
        }

    async def fetch_mismatches_by_ids(
        self,
        mismatch_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Fetch mismatches by a list of IDs."""
        if not mismatch_ids:
            return []

        # Use parameterized IN clause
        placeholders = ", ".join([f":id_{i}" for i in range(len(mismatch_ids))])
        params = {f"id_{i}": mid for i, mid in enumerate(mismatch_ids)}

        result = await self._session.execute(
            text(f"""
                SELECT id, trace_id, step_index, reason, expected_hash, actual_hash, details
                FROM aos_trace_mismatches
                WHERE id IN ({placeholders})
                ORDER BY trace_id, step_index
            """),
            params,
        )
        return [
            {
                "id": str(r[0]),
                "trace_id": r[1],
                "step_index": r[2],
                "reason": r[3],
                "expected_hash": r[4],
                "actual_hash": r[5],
                "details": r[6],
            }
            for r in result.all()
        ]

    async def bulk_update_issue_url(
        self,
        mismatch_ids: list[str],
        issue_url: str,
    ) -> None:
        """Update issue URL for multiple mismatches."""
        if not mismatch_ids:
            return

        placeholders = ", ".join([f":id_{i}" for i in range(len(mismatch_ids))])
        params = {f"id_{i}": mid for i, mid in enumerate(mismatch_ids)}
        params["issue_url"] = issue_url

        await self._session.execute(
            text(f"""
                UPDATE aos_trace_mismatches
                SET issue_url = :issue_url, notification_sent = TRUE
                WHERE id IN ({placeholders})
            """),
            params,
        )
        # L6 does NOT commit — L4 handler owns transaction boundary


def get_trace_mismatch_driver(session: AsyncSession) -> TraceMismatchDriver:
    """Get trace mismatch driver instance."""
    return TraceMismatchDriver(session)
