# Layer: L5 — Domain Engine
# AUDIENCE: FOUNDER
# Role: Founder AUTO_EXECUTE review queries (READ + audit writes)
# Callers: L4 handler (fdr_review_handler)
# Forbidden Imports: L1, L2
# artifact_class: CODE

"""
Founder Review Engine (L5)

Evidence-only queries for reviewing SUB-019 auto-execution decisions.
PIN-333 constraints: read-only evidence, no control, no behavior change.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.hoc.fdr.review_engine")


class ReviewEngine:
    """Evidence-only engine for auto-execute review."""

    async def emit_audit_event(
        self,
        session: AsyncSession,
        *,
        founder_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        try:
            await session.execute(
                text("""
                    INSERT INTO audit_events (
                        event_type, actor_id, actor_type, resource_type,
                        resource_id, action, details, created_at
                    ) VALUES (
                        'FOUNDER_REVIEW_ACCESS', :founder_id, 'FOUNDER', :resource_type,
                        :resource_id, :action, :details::jsonb, NOW()
                    )
                """),
                {
                    "founder_id": founder_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "action": action,
                    "details": str(details) if details else "{}",
                },
            )
            await session.commit()
        except Exception as e:
            logger.warning(f"Failed to emit review audit event: {e}")

    async def list_auto_execute_decisions(
        self,
        session: AsyncSession,
        *,
        start_dt: datetime,
        end_dt: datetime,
        tenant_id: Optional[str] = None,
        decision: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        has_safety_flags: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        base_query = """
            SELECT
                e.invocation_id, e.envelope_id, e.timestamp, e.tenant_id,
                e.account_id, e.project_id, e.capability_id, e.execution_vector,
                e.confidence_score, e.confidence_threshold,
                e.confidence_auto_execute_triggered, e.recovery_action,
                e.recovery_candidate_id, e.input_hash, e.plan_hash,
                e.plan_mutation_detected, e.worker_identity, e.safety_checked,
                e.safety_passed, e.safety_flags, e.safety_warnings
            FROM execution_envelopes e
            WHERE e.capability_id = 'SUB-019'
            AND e.execution_vector = 'AUTO_EXEC'
            AND e.timestamp >= :start_time AND e.timestamp <= :end_time
        """
        params: dict[str, Any] = {"start_time": start_dt, "end_time": end_dt}

        if tenant_id:
            base_query += " AND e.tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id
        if decision == "EXECUTED":
            base_query += " AND e.confidence_auto_execute_triggered = true"
        elif decision == "SKIPPED":
            base_query += " AND e.confidence_auto_execute_triggered = false"
        if min_confidence is not None:
            base_query += " AND e.confidence_score >= :min_confidence"
            params["min_confidence"] = min_confidence
        if max_confidence is not None:
            base_query += " AND e.confidence_score <= :max_confidence"
            params["max_confidence"] = max_confidence
        if has_safety_flags is not None:
            if has_safety_flags:
                base_query += " AND array_length(e.safety_flags, 1) > 0"
            else:
                base_query += " AND (e.safety_flags IS NULL OR array_length(e.safety_flags, 1) = 0)"

        # Count
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subq"
        try:
            total_count = (await session.execute(text(count_query), params)).scalar() or 0
        except Exception as e:
            logger.warning(f"Auto-execute query failed (table may not exist): {e}")
            return {"items": [], "total_count": 0, "page": page, "page_size": page_size,
                    "executed_count": 0, "skipped_count": 0, "flagged_count": 0}

        offset = (page - 1) * page_size
        paginated_query = f"{base_query} ORDER BY e.timestamp DESC LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = offset

        try:
            rows = (await session.execute(text(paginated_query), params)).fetchall()
        except Exception:
            rows = []

        items = []
        executed_count = skipped_count = flagged_count = 0
        for row in rows:
            dec = "EXECUTED" if row.confidence_auto_execute_triggered else "SKIPPED"
            if dec == "EXECUTED":
                executed_count += 1
            else:
                skipped_count += 1
            flags = row.safety_flags or []
            if flags:
                flagged_count += 1
            items.append({
                "invocation_id": row.invocation_id,
                "envelope_id": row.envelope_id,
                "timestamp": row.timestamp.isoformat() if row.timestamp else "",
                "tenant_id": row.tenant_id,
                "account_id": row.account_id,
                "project_id": row.project_id,
                "capability_id": "SUB-019",
                "execution_vector": "AUTO_EXEC",
                "confidence_score": row.confidence_score or 0.0,
                "threshold": row.confidence_threshold or 0.8,
                "decision": dec,
                "recovery_action": row.recovery_action,
                "recovery_candidate_id": row.recovery_candidate_id,
                "incident_id": None,
                "execution_result": None,
                "input_hash": row.input_hash or "",
                "plan_hash": row.plan_hash or "",
                "plan_mutation_detected": row.plan_mutation_detected or False,
                "worker_identity": row.worker_identity or "recovery_claim_worker",
                "safety_checked": row.safety_checked or False,
                "safety_passed": row.safety_passed if row.safety_passed is not None else True,
                "safety_flags": flags,
                "safety_warnings": row.safety_warnings or [],
            })

        return {
            "items": items, "total_count": total_count, "page": page,
            "page_size": page_size, "executed_count": executed_count,
            "skipped_count": skipped_count, "flagged_count": flagged_count,
        }

    async def get_auto_execute_stats(
        self,
        session: AsyncSession,
        *,
        start_dt: datetime,
        end_dt: datetime,
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"start_time": start_dt, "end_time": end_dt}
        tenant_filter = ""
        if tenant_id:
            tenant_filter = "AND e.tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id

        count_q = f"""
            SELECT COUNT(*) as total,
                COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = true) as executed,
                COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = false) as skipped,
                COUNT(*) FILTER (WHERE array_length(e.safety_flags, 1) > 0) as flagged
            FROM execution_envelopes e
            WHERE e.capability_id = 'SUB-019' AND e.execution_vector = 'AUTO_EXEC'
            AND e.timestamp >= :start_time AND e.timestamp <= :end_time {tenant_filter}
        """
        try:
            counts = (await session.execute(text(count_q), params)).fetchone()
            total = counts.total or 0
            executed = counts.executed or 0
            skipped = counts.skipped or 0
            flagged = counts.flagged or 0
        except Exception:
            total = executed = skipped = flagged = 0

        conf_q = f"""
            SELECT CASE
                WHEN e.confidence_score < 0.5 THEN '0.0-0.5'
                WHEN e.confidence_score < 0.6 THEN '0.5-0.6'
                WHEN e.confidence_score < 0.7 THEN '0.6-0.7'
                WHEN e.confidence_score < 0.8 THEN '0.7-0.8'
                WHEN e.confidence_score < 0.85 THEN '0.8-0.85'
                WHEN e.confidence_score < 0.9 THEN '0.85-0.9'
                WHEN e.confidence_score < 0.95 THEN '0.9-0.95'
                ELSE '0.95-1.0' END as bucket, COUNT(*) as count
            FROM execution_envelopes e
            WHERE e.capability_id = 'SUB-019' AND e.execution_vector = 'AUTO_EXEC'
            AND e.timestamp >= :start_time AND e.timestamp <= :end_time {tenant_filter}
            GROUP BY bucket ORDER BY bucket
        """
        confidence_distribution: dict[str, int] = {}
        try:
            for row in (await session.execute(text(conf_q), params)).fetchall():
                confidence_distribution[row.bucket] = row.count
        except Exception:
            pass

        flag_q = f"""
            SELECT unnest(e.safety_flags) as flag, COUNT(*) as count
            FROM execution_envelopes e
            WHERE e.capability_id = 'SUB-019' AND e.execution_vector = 'AUTO_EXEC'
            AND e.timestamp >= :start_time AND e.timestamp <= :end_time
            AND array_length(e.safety_flags, 1) > 0 {tenant_filter}
            GROUP BY flag ORDER BY count DESC
        """
        flag_counts: dict[str, int] = {}
        try:
            for row in (await session.execute(text(flag_q), params)).fetchall():
                flag_counts[row.flag] = row.count
        except Exception:
            pass

        daily_q = f"""
            SELECT DATE(e.timestamp) as date,
                COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = true) as executed,
                COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = false) as skipped
            FROM execution_envelopes e
            WHERE e.capability_id = 'SUB-019' AND e.execution_vector = 'AUTO_EXEC'
            AND e.timestamp >= :start_time AND e.timestamp <= :end_time {tenant_filter}
            GROUP BY DATE(e.timestamp) ORDER BY date
        """
        daily_counts: list[dict[str, Any]] = []
        try:
            for row in (await session.execute(text(daily_q), params)).fetchall():
                daily_counts.append({
                    "date": row.date.isoformat() if row.date else "",
                    "executed": row.executed or 0,
                    "skipped": row.skipped or 0,
                })
        except Exception:
            pass

        return {
            "start_time": start_dt.isoformat(), "end_time": end_dt.isoformat(),
            "total_decisions": total, "executed_count": executed,
            "skipped_count": skipped, "confidence_distribution": confidence_distribution,
            "flagged_count": flagged, "flag_counts": flag_counts,
            "daily_counts": daily_counts,
        }

    async def get_single_decision(
        self, session: AsyncSession, *, invocation_id: str
    ) -> Optional[dict[str, Any]]:
        query = """
            SELECT e.invocation_id, e.envelope_id, e.timestamp, e.tenant_id,
                e.account_id, e.project_id, e.capability_id, e.execution_vector,
                e.confidence_score, e.confidence_threshold,
                e.confidence_auto_execute_triggered, e.recovery_action,
                e.recovery_candidate_id, e.input_hash, e.plan_hash,
                e.plan_mutation_detected, e.worker_identity, e.safety_checked,
                e.safety_passed, e.safety_flags, e.safety_warnings
            FROM execution_envelopes e
            WHERE e.invocation_id = :invocation_id AND e.capability_id = 'SUB-019'
        """
        try:
            row = (await session.execute(text(query), {"invocation_id": invocation_id})).fetchone()
        except Exception:
            return None
        if not row:
            return None
        dec = "EXECUTED" if row.confidence_auto_execute_triggered else "SKIPPED"
        return {
            "invocation_id": row.invocation_id, "envelope_id": row.envelope_id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else "",
            "tenant_id": row.tenant_id, "account_id": row.account_id,
            "project_id": row.project_id, "capability_id": "SUB-019",
            "execution_vector": "AUTO_EXEC",
            "confidence_score": row.confidence_score or 0.0,
            "threshold": row.confidence_threshold or 0.8, "decision": dec,
            "recovery_action": row.recovery_action,
            "recovery_candidate_id": row.recovery_candidate_id,
            "incident_id": None, "execution_result": None,
            "input_hash": row.input_hash or "", "plan_hash": row.plan_hash or "",
            "plan_mutation_detected": row.plan_mutation_detected or False,
            "worker_identity": row.worker_identity or "recovery_claim_worker",
            "safety_checked": row.safety_checked or False,
            "safety_passed": row.safety_passed if row.safety_passed is not None else True,
            "safety_flags": row.safety_flags or [],
            "safety_warnings": row.safety_warnings or [],
        }


def get_review_engine() -> ReviewEngine:
    return ReviewEngine()
