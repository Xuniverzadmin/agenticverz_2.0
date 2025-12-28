"""
Prediction Service (PB-S5)

Generates predictions WITHOUT affecting execution behavior.

PB-S5 Contract:
- Advise → Observe → Do Nothing
- Predictions are advisory only
- Predictions have zero side-effects
- Predictions never modify execution, scheduling, or history

Rule: Advise, don't influence.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.feedback import PatternFeedback
from app.models.prediction import PredictionEvent, PredictionEventCreate
from app.models.tenant import WorkerRun

logger = logging.getLogger("nova.services.prediction")

# Configuration for prediction thresholds
FAILURE_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to emit prediction
COST_OVERRUN_THRESHOLD_PERCENT = 30  # Projected overrun percentage
PREDICTION_VALIDITY_HOURS = 24  # How long predictions remain valid


async def predict_failure_likelihood(
    session: AsyncSession,
    tenant_id: Optional[UUID] = None,
    worker_id: Optional[str] = None,
) -> list[dict]:
    """
    Predict likelihood of failure for upcoming runs.

    PB-S5: This function READS historical data only. No modifications.
    Predictions are advisory and have ZERO side-effects.

    Returns list of predictions with:
    - subject_id: worker or tenant being predicted
    - confidence_score: likelihood of failure (0.0-1.0)
    - contributing_factors: signals used for prediction
    """
    predictions = []

    # Query historical failure patterns (from PB-S3 feedback)
    feedback_query = (
        select(PatternFeedback)
        .where(PatternFeedback.pattern_type == "failure_pattern")
        .order_by(PatternFeedback.detected_at.desc())
        .limit(100)
    )

    if tenant_id:
        feedback_query = feedback_query.where(PatternFeedback.tenant_id == str(tenant_id))

    result = await session.execute(feedback_query)
    feedback_records = result.scalars().all()

    # Query recent failures (from worker_runs)
    runs_query = (
        select(WorkerRun)
        .where(WorkerRun.status == "failed")
        .where(WorkerRun.created_at >= datetime.utcnow() - timedelta(days=7))
        .order_by(WorkerRun.created_at.desc())
        .limit(100)
    )

    if tenant_id:
        runs_query = runs_query.where(WorkerRun.tenant_id == tenant_id)
    if worker_id:
        runs_query = runs_query.where(WorkerRun.worker_id == worker_id)

    result = await session.execute(runs_query)
    failed_runs = result.scalars().all()

    if not failed_runs and not feedback_records:
        return []

    # Group by worker_id and calculate failure rate
    worker_failures: dict[str, list[WorkerRun]] = {}
    for run in failed_runs:
        wid = str(run.worker_id)
        if wid not in worker_failures:
            worker_failures[wid] = []
        worker_failures[wid].append(run)

    # Get total runs per worker for rate calculation
    total_runs_query = (
        select(WorkerRun.worker_id, func.count().label("total"))
        .where(WorkerRun.created_at >= datetime.utcnow() - timedelta(days=7))
        .group_by(WorkerRun.worker_id)
    )

    if tenant_id:
        total_runs_query = total_runs_query.where(WorkerRun.tenant_id == tenant_id)

    result = await session.execute(total_runs_query)
    total_by_worker = {str(row.worker_id): row.total for row in result}

    # Generate predictions
    for worker_id, failures in worker_failures.items():
        total = total_by_worker.get(worker_id, len(failures))
        if total == 0:
            continue

        failure_rate = len(failures) / total
        confidence = min(failure_rate * 1.5, 1.0)  # Scale up slightly, cap at 1.0

        if confidence >= FAILURE_CONFIDENCE_THRESHOLD:
            # Get contributing factors
            factors = []
            if failures:
                # Get unique error signatures
                error_samples = list(set(r.error[:100] if r.error else "unknown" for r in failures[:5]))
                factors.append({"type": "recent_failures", "count": len(failures)})
                factors.append({"type": "failure_rate", "value": round(failure_rate, 3)})
                factors.append({"type": "error_samples", "samples": error_samples[:3]})

            # Check for feedback patterns
            worker_feedback = [
                f for f in feedback_records if f.extra_data and f.extra_data.get("worker_id") == worker_id
            ]
            if worker_feedback:
                factors.append({"type": "feedback_patterns", "count": len(worker_feedback)})

            predictions.append(
                {
                    "subject_type": "worker",
                    "subject_id": worker_id,
                    "tenant_id": str(failures[0].tenant_id),
                    "confidence_score": round(confidence, 3),
                    "prediction_value": {
                        "predicted_outcome": "high_failure_likelihood",
                        "failure_rate": round(failure_rate, 3),
                        "recent_failures": len(failures),
                        "total_runs": total,
                    },
                    "contributing_factors": factors,
                }
            )

    logger.info(
        "failure_predictions_generated",
        extra={
            "prediction_count": len(predictions),
            "threshold": FAILURE_CONFIDENCE_THRESHOLD,
        },
    )

    return predictions


async def predict_cost_overrun(
    session: AsyncSession,
    tenant_id: Optional[UUID] = None,
    worker_id: Optional[str] = None,
) -> list[dict]:
    """
    Predict likelihood of cost overrun for upcoming runs.

    PB-S5: This function READS cost data only. No modifications.
    Predictions are advisory and have ZERO side-effects.

    Returns list of predictions with:
    - subject_id: worker or tenant being predicted
    - confidence_score: likelihood of overrun (0.0-1.0)
    - projected_cost: expected cost
    - contributing_factors: signals used for prediction
    """
    predictions = []

    # Query recent costs
    runs_query = (
        select(WorkerRun)
        .where(WorkerRun.status == "completed")
        .where(WorkerRun.cost_cents.isnot(None))
        .where(WorkerRun.cost_cents > 0)
        .where(WorkerRun.created_at >= datetime.utcnow() - timedelta(days=7))
        .order_by(WorkerRun.created_at.desc())
        .limit(200)
    )

    if tenant_id:
        runs_query = runs_query.where(WorkerRun.tenant_id == tenant_id)
    if worker_id:
        runs_query = runs_query.where(WorkerRun.worker_id == worker_id)

    result = await session.execute(runs_query)
    runs = result.scalars().all()

    if len(runs) < 3:  # Need enough data for trend
        return []

    # Group by worker and analyze cost trends
    worker_costs: dict[str, list[tuple[datetime, int]]] = {}
    for run in runs:
        wid = str(run.worker_id)
        if wid not in worker_costs:
            worker_costs[wid] = []
        worker_costs[wid].append((run.created_at, run.cost_cents))

    for worker_id, costs in worker_costs.items():
        if len(costs) < 3:
            continue

        # Sort by time (newest first already)
        costs_sorted = sorted(costs, key=lambda x: x[0], reverse=True)

        # Calculate average and trend
        recent_costs = [c[1] for c in costs_sorted[:3]]
        older_costs = [c[1] for c in costs_sorted[3:]] if len(costs_sorted) > 3 else recent_costs

        recent_avg = sum(recent_costs) / len(recent_costs)
        older_avg = sum(older_costs) / len(older_costs) if older_costs else recent_avg

        if older_avg == 0:
            continue

        # Calculate projected cost and overrun percentage
        trend_multiplier = recent_avg / older_avg
        projected_cost = recent_avg * trend_multiplier
        overrun_percent = ((projected_cost - older_avg) / older_avg) * 100

        if overrun_percent >= COST_OVERRUN_THRESHOLD_PERCENT:
            confidence = min(overrun_percent / 100, 0.95)  # Cap at 95%

            factors = [
                {"type": "recent_avg_cost", "value": round(recent_avg, 2)},
                {"type": "historical_avg_cost", "value": round(older_avg, 2)},
                {"type": "trend_multiplier", "value": round(trend_multiplier, 3)},
                {"type": "sample_size", "recent": len(recent_costs), "historical": len(older_costs)},
            ]

            predictions.append(
                {
                    "subject_type": "worker",
                    "subject_id": worker_id,
                    "tenant_id": str(runs[0].tenant_id),
                    "confidence_score": round(confidence, 3),
                    "prediction_value": {
                        "predicted_outcome": "cost_overrun",
                        "projected_cost_cents": round(projected_cost, 2),
                        "historical_avg_cents": round(older_avg, 2),
                        "overrun_percent": round(overrun_percent, 1),
                    },
                    "contributing_factors": factors,
                }
            )

    logger.info(
        "cost_predictions_generated",
        extra={
            "prediction_count": len(predictions),
            "threshold_percent": COST_OVERRUN_THRESHOLD_PERCENT,
        },
    )

    return predictions


async def emit_prediction(
    session: AsyncSession,
    prediction: PredictionEventCreate,
) -> PredictionEvent:
    """
    Emit a prediction event.

    PB-S5: This creates a NEW record in prediction_events.
    It does NOT modify any execution data. Predictions are advisory only.
    """
    record = PredictionEvent(
        tenant_id=prediction.tenant_id,
        prediction_type=prediction.prediction_type,
        subject_type=prediction.subject_type,
        subject_id=prediction.subject_id,
        confidence_score=prediction.confidence_score,
        prediction_value=prediction.prediction_value,
        contributing_factors=prediction.contributing_factors,
        valid_until=prediction.valid_until or (datetime.utcnow() + timedelta(hours=PREDICTION_VALIDITY_HOURS)),
        created_at=datetime.utcnow(),
        is_advisory=True,  # ALWAYS TRUE - enforced by design
        notes=prediction.notes,
    )

    session.add(record)
    await session.flush()

    logger.info(
        "prediction_event_emitted",
        extra={
            "prediction_id": str(record.id),
            "prediction_type": record.prediction_type,
            "subject_type": record.subject_type,
            "subject_id": record.subject_id,
            "confidence": record.confidence_score,
            "is_advisory": record.is_advisory,
        },
    )

    return record


async def run_prediction_cycle(
    tenant_id: Optional[UUID] = None,
) -> dict:
    """
    Run full prediction cycle.

    PB-S5: Generates predictions. No execution modifications.

    Returns summary of generated predictions.
    """
    result = {
        "failure_predictions": [],
        "cost_predictions": [],
        "predictions_created": 0,
        "errors": [],
    }

    try:
        async with get_async_session() as session:
            # Generate failure predictions
            failure_predictions = await predict_failure_likelihood(session, tenant_id)
            result["failure_predictions"] = failure_predictions

            # Emit failure predictions
            for pred in failure_predictions:
                try:
                    prediction = PredictionEventCreate(
                        tenant_id=pred["tenant_id"],
                        prediction_type="failure_likelihood",
                        subject_type=pred["subject_type"],
                        subject_id=pred["subject_id"],
                        confidence_score=pred["confidence_score"],
                        prediction_value=pred["prediction_value"],
                        contributing_factors=pred["contributing_factors"],
                        notes="ADVISORY: This is a prediction, not a fact.",
                    )
                    await emit_prediction(session, prediction)
                    result["predictions_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Failed to emit failure prediction: {e}")

            # Generate cost predictions
            cost_predictions = await predict_cost_overrun(session, tenant_id)
            result["cost_predictions"] = cost_predictions

            # Emit cost predictions
            for pred in cost_predictions:
                try:
                    prediction = PredictionEventCreate(
                        tenant_id=pred["tenant_id"],
                        prediction_type="cost_overrun",
                        subject_type=pred["subject_type"],
                        subject_id=pred["subject_id"],
                        confidence_score=pred["confidence_score"],
                        prediction_value=pred["prediction_value"],
                        contributing_factors=pred["contributing_factors"],
                        notes="ADVISORY: This is a projection based on trends.",
                    )
                    await emit_prediction(session, prediction)
                    result["predictions_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Failed to emit cost prediction: {e}")

            await session.commit()

    except Exception as e:
        logger.error(f"prediction_cycle_error: {e}", exc_info=True)
        result["errors"].append(str(e))

    return result


async def get_prediction_summary(
    tenant_id: Optional[UUID] = None,
    prediction_type: Optional[str] = None,
    include_expired: bool = False,
    limit: int = 50,
) -> dict:
    """
    Get prediction summary for ops visibility.

    PB-S5: Read-only query of predictions table.
    """
    async with get_async_session() as session:
        query = select(PredictionEvent).order_by(PredictionEvent.created_at.desc())

        if tenant_id:
            query = query.where(PredictionEvent.tenant_id == str(tenant_id))
        if prediction_type:
            query = query.where(PredictionEvent.prediction_type == prediction_type)
        if not include_expired:
            query = query.where(
                (PredictionEvent.valid_until.is_(None)) | (PredictionEvent.valid_until > datetime.utcnow())
            )

        query = query.limit(limit)

        result = await session.execute(query)
        predictions = result.scalars().all()

        # Count by type
        type_counts: dict[str, int] = {}
        for pred in predictions:
            ptype = pred.prediction_type
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        return {
            "total": len(predictions),
            "by_type": type_counts,
            "predictions": [
                {
                    "id": str(p.id),
                    "prediction_type": p.prediction_type,
                    "subject_type": p.subject_type,
                    "subject_id": p.subject_id,
                    "confidence_score": p.confidence_score,
                    "prediction_value": p.prediction_value,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "valid_until": p.valid_until.isoformat() if p.valid_until else None,
                    "is_advisory": p.is_advisory,
                }
                for p in predictions
            ],
        }
