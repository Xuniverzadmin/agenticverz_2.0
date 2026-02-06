# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via feedback_read_driver (L6)
#   Writes: none
# Role: Feedback read engine - business logic for PB-S3 feedback API (READ-ONLY)
# Callers: analytics_handler.py (L4 handler)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, L2 first-principles purity migration
# artifact_class: CODE

"""
Feedback Read Engine (L5)

Business logic for pattern feedback read operations (PB-S3 compliant).
Delegates all DB access to L6 FeedbackReadDriver.

Operations:
- list_feedback: Paginated list with aggregation
- get_feedback: Single record detail
- get_feedback_stats: Summary statistics
"""

from typing import Any, Optional
from uuid import UUID

from app.hoc.cus.analytics.L6_drivers.feedback_read_driver import (
    get_feedback_read_driver,
)


class FeedbackReadEngine:
    """
    L5 engine for feedback read operations.

    Business logic (aggregation, formatting) lives here.
    DB access delegated to L6 driver.
    """

    async def list_feedback(
        self,
        session: Any,
        tenant_id: str,
        pattern_type: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """List feedback records with pagination and aggregation."""
        driver = get_feedback_read_driver(session)
        result = driver.fetch_feedback_list(
            tenant_id=tenant_id if tenant_id != "system" else None,
            pattern_type=pattern_type,
            severity=severity,
            acknowledged=acknowledged,
            limit=limit,
            offset=offset,
        )
        data = await result

        records = data["records"]
        total = data["total"]

        # Aggregate by type and severity
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        items = []
        for r in records:
            by_type[r.pattern_type] = by_type.get(r.pattern_type, 0) + 1
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1
            items.append({
                "id": str(r.id),
                "tenant_id": r.tenant_id,
                "pattern_type": r.pattern_type,
                "severity": r.severity,
                "description": r.description[:200] if r.description else "",
                "signature": r.signature,
                "occurrence_count": r.occurrence_count,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                "acknowledged": r.acknowledged,
                "provenance_count": len(r.provenance) if r.provenance else 0,
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "by_type": by_type,
            "by_severity": by_severity,
            "items": items,
        }

    async def get_feedback(
        self,
        session: Any,
        tenant_id: str,
        feedback_id: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Get detailed feedback record by ID."""
        try:
            feedback_uuid = UUID(feedback_id)
        except ValueError:
            return None

        driver = get_feedback_read_driver(session)
        record = await driver.fetch_feedback_by_id(feedback_uuid)

        if not record:
            return None

        return {
            "id": str(record.id),
            "tenant_id": record.tenant_id,
            "pattern_type": record.pattern_type,
            "severity": record.severity,
            "description": record.description,
            "signature": record.signature,
            "provenance": record.provenance or [],
            "occurrence_count": record.occurrence_count,
            "time_window_minutes": record.time_window_minutes,
            "threshold_used": record.threshold_used,
            "extra_data": record.extra_data,
            "detected_at": record.detected_at.isoformat() if record.detected_at else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "acknowledged": record.acknowledged,
            "acknowledged_at": record.acknowledged_at.isoformat() if record.acknowledged_at else None,
            "acknowledged_by": record.acknowledged_by,
        }

    async def get_feedback_stats(
        self,
        session: Any,
        tenant_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get feedback statistics summary."""
        driver = get_feedback_read_driver(session)
        records = await driver.fetch_feedback_stats(
            tenant_id=tenant_id if tenant_id != "system" else None,
        )

        total = len(records)
        acknowledged_count = sum(1 for r in records if r.acknowledged)
        unacknowledged_count = total - acknowledged_count

        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for r in records:
            by_type[r.pattern_type] = by_type.get(r.pattern_type, 0) + 1
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1

        return {
            "total": total,
            "acknowledged": acknowledged_count,
            "unacknowledged": unacknowledged_count,
            "by_type": by_type,
            "by_severity": by_severity,
            "read_only": True,
            "pb_s3_compliant": True,
        }


_engine_instance: Optional[FeedbackReadEngine] = None


def get_feedback_read_engine() -> FeedbackReadEngine:
    """Get feedback read engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = FeedbackReadEngine()
    return _engine_instance
