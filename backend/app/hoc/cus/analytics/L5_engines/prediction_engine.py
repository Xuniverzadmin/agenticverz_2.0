# Layer: L5 — Domain Engine
# NOTE: Renamed prediction.py → prediction_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/scheduler
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via prediction_driver (L6)
#   Writes: via prediction_driver (L6)
# Role: Prediction generation and orchestration (advisory only)
# Callers: predictions API (read-side)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Forbidden: session.commit(), session.rollback() — L5 DOES NOT COMMIT (L4 coordinator owns)
# Reference: PIN-470, Phase-2.5A Analytics Extraction, PIN-240
#
# GOVERNANCE NOTE:
# This L4 engine handles PREDICTION LOGIC only:
# - Confidence scoring
# - Threshold comparisons
# - Factor aggregation
# - Orchestration flow
#
# PERSISTENCE (L6 Driver): prediction_driver.py
#
# ============================================================================
# AUTHORITY PARTITION — PREDICTION ENGINE
# ============================================================================
# Method                       | Bucket      | Notes
# ---------------------------- | ----------- | --------------------------------
# predict_failure_likelihood   | DECISION    | Calculates confidence scores
# predict_cost_overrun         | DECISION    | Calculates cost projections
# emit_prediction              | PERSISTENCE | → Delegated to driver
# run_prediction_cycle         | DECISION    | Orchestrates full cycle
# get_prediction_summary       | PERSISTENCE | → Delegated to driver
# ============================================================================
#
# NOTE: Advisory only. Predictions have zero side-effects on execution.

"""
Prediction Service (PB-S5)

Generates predictions WITHOUT affecting execution behavior.

Phase-2.5A Extraction:
- PERSISTENCE: Delegated to PredictionDriver (L6)
- DECISIONS: Retained in this engine (L4)

PB-S5 Contract:
- Advise → Observe → Do Nothing
- Predictions are advisory only
- Predictions have zero side-effects
- Predictions never modify execution, scheduling, or history

Rule: Advise, don't influence.
"""

import logging
from datetime import timedelta
from typing import Optional
from uuid import UUID

from app.hoc.hoc_spine.services.time import utc_now
from app.db import get_async_session

logger = logging.getLogger("nova.services.prediction")

# Configuration for prediction thresholds
FAILURE_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to emit prediction
COST_OVERRUN_THRESHOLD_PERCENT = 30  # Projected overrun percentage
PREDICTION_VALIDITY_HOURS = 24  # How long predictions remain valid


async def predict_failure_likelihood(
    driver: "PredictionDriver",
    tenant_id: Optional[UUID] = None,
    worker_id: Optional[str] = None,
) -> list[dict]:
    """
    Predict likelihood of failure for upcoming runs.

    Phase-2.5A: Data fetching delegated to driver (L6).

    PB-S5: This function calculates predictions only. No modifications.
    Predictions are advisory and have ZERO side-effects.

    Returns list of predictions with:
    - subject_id: worker or tenant being predicted
    - confidence_score: likelihood of failure (0.0-1.0)
    - contributing_factors: signals used for prediction
    """
    from app.hoc.cus.analytics.L6_drivers.prediction_driver import (
        PredictionDriver,
    )

    predictions = []
    since = utc_now() - timedelta(days=7)

    # Phase-2.5A: Delegate fetches to driver
    feedback_records = await driver.fetch_failure_patterns(tenant_id=tenant_id, limit=100)
    failed_runs = await driver.fetch_failed_runs(
        since=since, tenant_id=tenant_id, worker_id=worker_id, limit=100
    )

    if not failed_runs and not feedback_records:
        return []

    # L4 DECISION: Group by worker_id and calculate failure rate
    worker_failures: dict[str, list] = {}
    for run in failed_runs:
        wid = str(run.worker_id)
        if wid not in worker_failures:
            worker_failures[wid] = []
        worker_failures[wid].append(run)

    # Phase-2.5A: Delegate fetch to driver
    total_by_worker = await driver.fetch_run_totals(since=since, tenant_id=tenant_id)

    # L4 DECISION: Generate predictions based on thresholds
    for wid, failures in worker_failures.items():
        total = total_by_worker.get(wid, len(failures))
        if total == 0:
            continue

        # L4 DECISION: Calculate confidence score
        failure_rate = len(failures) / total
        confidence = min(failure_rate * 1.5, 1.0)  # Scale up slightly, cap at 1.0

        if confidence >= FAILURE_CONFIDENCE_THRESHOLD:
            # L4 DECISION: Build contributing factors
            factors = []
            if failures:
                # Get unique error signatures
                error_samples = list(set(r.error[:100] if r.error else "unknown" for r in failures[:5]))
                factors.append({"type": "recent_failures", "count": len(failures)})
                factors.append({"type": "failure_rate", "value": round(failure_rate, 3)})
                factors.append({"type": "error_samples", "samples": error_samples[:3]})

            # Check for feedback patterns
            worker_feedback = [
                f for f in feedback_records if f.extra_data and f.extra_data.get("worker_id") == wid
            ]
            if worker_feedback:
                factors.append({"type": "feedback_patterns", "count": len(worker_feedback)})

            predictions.append(
                {
                    "subject_type": "worker",
                    "subject_id": wid,
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
    driver: "PredictionDriver",
    tenant_id: Optional[UUID] = None,
    worker_id: Optional[str] = None,
) -> list[dict]:
    """
    Predict likelihood of cost overrun for upcoming runs.

    Phase-2.5A: Data fetching delegated to driver (L6).

    PB-S5: This function calculates predictions only. No modifications.
    Predictions are advisory and have ZERO side-effects.

    Returns list of predictions with:
    - subject_id: worker or tenant being predicted
    - confidence_score: likelihood of overrun (0.0-1.0)
    - projected_cost: expected cost
    - contributing_factors: signals used for prediction
    """
    from datetime import datetime

    predictions = []
    since = utc_now() - timedelta(days=7)

    # Phase-2.5A: Delegate fetch to driver
    runs = await driver.fetch_cost_runs(
        since=since, tenant_id=tenant_id, worker_id=worker_id, limit=200
    )

    if len(runs) < 3:  # Need enough data for trend
        return []

    # L4 DECISION: Group by worker and analyze cost trends
    worker_costs: dict[str, list[tuple[datetime, int]]] = {}
    for run in runs:
        wid = str(run.worker_id)
        if wid not in worker_costs:
            worker_costs[wid] = []
        worker_costs[wid].append((run.created_at, run.cost_cents))

    for wid, costs in worker_costs.items():
        if len(costs) < 3:
            continue

        # L4 DECISION: Sort by time (newest first already)
        costs_sorted = sorted(costs, key=lambda x: x[0], reverse=True)

        # L4 DECISION: Calculate average and trend
        recent_costs = [c[1] for c in costs_sorted[:3]]
        older_costs = [c[1] for c in costs_sorted[3:]] if len(costs_sorted) > 3 else recent_costs

        recent_avg = sum(recent_costs) / len(recent_costs)
        older_avg = sum(older_costs) / len(older_costs) if older_costs else recent_avg

        if older_avg == 0:
            continue

        # L4 DECISION: Calculate projected cost and overrun percentage
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
                    "subject_id": wid,
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
    driver: "PredictionDriver",
    tenant_id: str,
    prediction_type: str,
    subject_type: str,
    subject_id: str,
    confidence_score: float,
    prediction_value: dict,
    contributing_factors: list,
    notes: Optional[str] = None,
    valid_until: Optional["datetime"] = None,
) -> "PredictionEvent":
    """
    Emit a prediction event.

    Phase-2.5A: Persistence delegated to driver (L6).

    PB-S5: This creates a NEW record in prediction_events.
    It does NOT modify any execution data. Predictions are advisory only.
    """
    from datetime import datetime
    from app.models.prediction import PredictionEvent

    now = utc_now()
    valid_until_ts = valid_until or (now + timedelta(hours=PREDICTION_VALIDITY_HOURS))

    # Phase-2.5A: Delegate insert to driver
    record = await driver.insert_prediction(
        tenant_id=tenant_id,
        prediction_type=prediction_type,
        subject_type=subject_type,
        subject_id=subject_id,
        confidence_score=confidence_score,
        prediction_value=prediction_value,
        contributing_factors=contributing_factors,
        valid_until=valid_until_ts,
        created_at=now,
        notes=notes,
    )

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

    Phase-2.5A: Data access delegated to driver (L6).
    This method orchestrates the prediction flow (L4 DECISION).

    PB-S5: Generates predictions. No execution modifications.

    Returns summary of generated predictions.
    """
    from app.hoc.cus.analytics.L6_drivers.prediction_driver import (
        get_prediction_driver,
    )

    result = {
        "failure_predictions": [],
        "cost_predictions": [],
        "predictions_created": 0,
        "errors": [],
    }

    try:
        async with get_async_session() as session:
            driver = get_prediction_driver(session)

            # L4 DECISION: Generate failure predictions
            failure_predictions = await predict_failure_likelihood(driver, tenant_id)
            result["failure_predictions"] = failure_predictions

            # L4 DECISION: Emit failure predictions via driver
            for pred in failure_predictions:
                try:
                    await emit_prediction(
                        driver=driver,
                        tenant_id=pred["tenant_id"],
                        prediction_type="failure_likelihood",
                        subject_type=pred["subject_type"],
                        subject_id=pred["subject_id"],
                        confidence_score=pred["confidence_score"],
                        prediction_value=pred["prediction_value"],
                        contributing_factors=pred["contributing_factors"],
                        notes="ADVISORY: This is a prediction, not a fact.",
                    )
                    result["predictions_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Failed to emit failure prediction: {e}")

            # L4 DECISION: Generate cost predictions
            cost_predictions = await predict_cost_overrun(driver, tenant_id)
            result["cost_predictions"] = cost_predictions

            # L4 DECISION: Emit cost predictions via driver
            for pred in cost_predictions:
                try:
                    await emit_prediction(
                        driver=driver,
                        tenant_id=pred["tenant_id"],
                        prediction_type="cost_overrun",
                        subject_type=pred["subject_type"],
                        subject_id=pred["subject_id"],
                        confidence_score=pred["confidence_score"],
                        prediction_value=pred["prediction_value"],
                        contributing_factors=pred["contributing_factors"],
                        notes="ADVISORY: This is a projection based on trends.",
                    )
                    result["predictions_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Failed to emit cost prediction: {e}")

            # NO COMMIT — L4 coordinator owns transaction boundary

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

    Phase-2.5A: Data fetching delegated to driver (L6).

    PB-S5: Read-only query of predictions table.
    """
    from app.hoc.cus.analytics.L6_drivers.prediction_driver import (
        get_prediction_driver,
    )

    async with get_async_session() as session:
        driver = get_prediction_driver(session)

        # Phase-2.5A: Delegate fetch to driver
        valid_after = None if include_expired else utc_now()
        predictions = await driver.fetch_predictions(
            tenant_id=tenant_id,
            prediction_type=prediction_type,
            valid_after=valid_after,
            limit=limit,
        )

        # L4 DECISION: Count by type (business logic)
        type_counts: dict[str, int] = {}
        for pred in predictions:
            ptype = pred.prediction_type
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        # L4 DECISION: Format response (presentation logic)
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
