# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via prediction_read_driver (L6)
#   Writes: none
# Role: Prediction read engine - business logic for PB-S5 prediction API (READ-ONLY)
# Callers: analytics_handler.py (L4 handler)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, L2 first-principles purity migration
# artifact_class: CODE

"""
Prediction Read Engine (L5)

Business logic for prediction event read operations (PB-S5 compliant).
Delegates all DB access to L6 PredictionReadDriver.

Operations:
- list_predictions: Paginated list with aggregation
- get_prediction: Single record detail
- get_predictions_for_subject: All predictions for a subject
- get_prediction_stats: Summary statistics with advisory compliance
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.hoc.cus.analytics.L6_drivers.prediction_read_driver import (
    get_prediction_read_driver,
)


class PredictionReadEngine:
    """
    L5 engine for prediction read operations.

    Business logic (aggregation, compliance check, formatting) lives here.
    DB access delegated to L6 driver.
    """

    async def list_predictions(
        self,
        session: Any,
        tenant_id: str,
        prediction_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        include_expired: bool = False,
        limit: int = 50,
        offset: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """List prediction events with pagination and aggregation."""
        now = datetime.utcnow()
        driver = get_prediction_read_driver(session)
        data = await driver.fetch_prediction_list(
            tenant_id=tenant_id if tenant_id != "system" else None,
            prediction_type=prediction_type,
            subject_type=subject_type,
            subject_id=subject_id,
            include_expired=include_expired,
            now=now,
            limit=limit,
            offset=offset,
        )

        records = data["records"]
        total = data["total"]

        # Aggregate by type and subject_type
        by_type: dict[str, int] = {}
        by_subject_type: dict[str, int] = {}
        items = []
        for r in records:
            by_type[r.prediction_type] = by_type.get(r.prediction_type, 0) + 1
            by_subject_type[r.subject_type] = by_subject_type.get(r.subject_type, 0) + 1
            items.append({
                "id": str(r.id),
                "tenant_id": r.tenant_id,
                "prediction_type": r.prediction_type,
                "subject_type": r.subject_type,
                "subject_id": r.subject_id,
                "confidence_score": r.confidence_score,
                "is_advisory": r.is_advisory,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "is_valid": (r.expires_at is None or r.expires_at > now),
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "by_type": by_type,
            "by_subject_type": by_subject_type,
            "items": items,
        }

    async def get_prediction(
        self,
        session: Any,
        tenant_id: str,
        prediction_id: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Get detailed prediction record by ID."""
        try:
            prediction_uuid = UUID(prediction_id)
        except ValueError:
            return None

        now = datetime.utcnow()
        driver = get_prediction_read_driver(session)
        record = await driver.fetch_prediction_by_id(prediction_uuid)

        if not record:
            return None

        return {
            "id": str(record.id),
            "tenant_id": record.tenant_id,
            "prediction_type": record.prediction_type,
            "subject_type": record.subject_type,
            "subject_id": record.subject_id,
            "confidence_score": record.confidence_score,
            "prediction_value": record.prediction_value or {},
            "contributing_factors": record.contributing_factors or [],
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "is_advisory": record.is_advisory,
            "notes": record.notes,
            "is_valid": (record.expires_at is None or record.expires_at > now),
        }

    async def get_predictions_for_subject(
        self,
        session: Any,
        tenant_id: str,
        subject_type: str,
        subject_id: str,
        include_expired: bool = False,
        limit: int = 20,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get all predictions for a specific subject."""
        now = datetime.utcnow()
        driver = get_prediction_read_driver(session)
        records = await driver.fetch_predictions_for_subject(
            subject_type=subject_type,
            subject_id=subject_id,
            include_expired=include_expired,
            now=now,
            limit=limit,
        )

        return {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "predictions": [
                {
                    "id": str(r.id),
                    "prediction_type": r.prediction_type,
                    "confidence_score": r.confidence_score,
                    "prediction_value": r.prediction_value,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                    "is_advisory": r.is_advisory,
                    "is_valid": (r.expires_at is None or r.expires_at > now),
                }
                for r in records
            ],
            "count": len(records),
            "read_only": True,
            "pb_s5_compliant": True,
        }

    async def get_prediction_stats(
        self,
        session: Any,
        tenant_id: str,
        include_expired: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get prediction statistics summary."""
        now = datetime.utcnow()
        driver = get_prediction_read_driver(session)
        records = await driver.fetch_prediction_stats(
            tenant_id=tenant_id if tenant_id != "system" else None,
            include_expired=include_expired,
            now=now,
        )

        total = len(records)
        by_type: dict[str, int] = {}
        by_subject_type: dict[str, int] = {}
        confidence_sum = 0.0
        high_confidence_count = 0

        for r in records:
            by_type[r.prediction_type] = by_type.get(r.prediction_type, 0) + 1
            by_subject_type[r.subject_type] = by_subject_type.get(r.subject_type, 0) + 1
            confidence_sum += r.confidence_score
            if r.confidence_score > 0.7:
                high_confidence_count += 1

        avg_confidence = (confidence_sum / total) if total > 0 else 0
        non_advisory = sum(1 for r in records if not r.is_advisory)

        return {
            "total": total,
            "by_type": by_type,
            "by_subject_type": by_subject_type,
            "avg_confidence": round(avg_confidence, 3),
            "high_confidence_count": high_confidence_count,
            "advisory_compliance": {
                "all_advisory": non_advisory == 0,
                "non_advisory_count": non_advisory,
            },
            "read_only": True,
            "pb_s5_compliant": True,
        }


_engine_instance: Optional[PredictionReadEngine] = None


def get_prediction_read_engine() -> PredictionReadEngine:
    """Get prediction read engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PredictionReadEngine()
    return _engine_instance
