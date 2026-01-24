# Layer: L5 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Callers: None
# Reference: PIN-240
#
# STATUS: DORMANT BY DESIGN
# =========================
# This file is complete, contract-safe (PB-S3), and intentionally unwired.
# Do NOT activate without review. Cost anomaly detection is already handled
# by cost_anomaly_detector.py for the primary use case.
#
# If wiring is needed in the future:
#   - Route through detection_facade.py, not direct import
#   - Ensure PB-S3 contract is preserved (observe → feedback → no mutation)
#   - Review governance implications before activation
#
# WARNING: If this logic is wrong, ALL products break.

"""
Pattern Detection Service (PB-S3)

Detects patterns in execution data and emits feedback WITHOUT modifying history.

PB-S3 Contract:
- Observe patterns → create feedback → do nothing else
- NO modification of worker_runs, traces, or costs
- Feedback stored SEPARATELY in pattern_feedback table

Pattern Types:
- failure_pattern: Same error signature N times
- cost_spike: Abnormal cost increase detected
"""

import hashlib
import logging
import os
from datetime import timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.hoc.cus.general.L5_utils.time import utc_now
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.feedback import PatternFeedback, PatternFeedbackCreate
from app.models.tenant import WorkerRun

logger = logging.getLogger("nova.services.pattern_detection")

# Configuration
FAILURE_PATTERN_THRESHOLD = int(os.getenv("FAILURE_PATTERN_THRESHOLD", "3"))
FAILURE_PATTERN_WINDOW_HOURS = int(os.getenv("FAILURE_PATTERN_WINDOW_HOURS", "24"))
COST_SPIKE_THRESHOLD_PERCENT = float(os.getenv("COST_SPIKE_THRESHOLD_PERCENT", "50"))
COST_SPIKE_MIN_RUNS = int(os.getenv("COST_SPIKE_MIN_RUNS", "5"))


def compute_error_signature(error: str) -> str:
    """
    Compute a stable signature for an error message.

    Strips variable parts (IDs, timestamps) to group similar errors.
    """
    if not error:
        return "empty_error"

    # Normalize: lowercase, strip whitespace
    normalized = error.lower().strip()

    # Remove common variable patterns (UUIDs, numbers, timestamps)
    import re

    normalized = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<uuid>", normalized)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "<timestamp>", normalized)
    normalized = re.sub(r"\b\d+\b", "<n>", normalized)

    # Hash for stable signature
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


async def detect_failure_patterns(
    session: AsyncSession,
    tenant_id: Optional[UUID] = None,
    threshold: int = FAILURE_PATTERN_THRESHOLD,
    window_hours: int = FAILURE_PATTERN_WINDOW_HOURS,
) -> list[dict]:
    """
    Detect repeated failure patterns.

    PB-S3: This function READS execution data only. No modifications.

    Returns list of detected patterns with:
    - signature: error signature
    - count: number of occurrences
    - run_ids: list of affected runs (provenance)
    - sample_error: example error message
    """
    window_start = utc_now() - timedelta(hours=window_hours)

    # Query failed runs within window
    query = (
        select(WorkerRun)
        .where(WorkerRun.status == "failed")
        .where(WorkerRun.created_at >= window_start)
        .where(WorkerRun.error.isnot(None))
    )

    if tenant_id:
        query = query.where(WorkerRun.tenant_id == tenant_id)

    result = await session.execute(query)
    failed_runs = result.scalars().all()

    if not failed_runs:
        return []

    # Group by error signature
    signature_groups: dict[str, list[WorkerRun]] = {}
    for run in failed_runs:
        sig = compute_error_signature(run.error)
        if sig not in signature_groups:
            signature_groups[sig] = []
        signature_groups[sig].append(run)

    # Find patterns exceeding threshold
    patterns = []
    for signature, runs in signature_groups.items():
        if len(runs) >= threshold:
            patterns.append(
                {
                    "signature": signature,
                    "count": len(runs),
                    "run_ids": [str(r.id) for r in runs],
                    "sample_error": runs[0].error[:500] if runs[0].error else "",
                    "worker_id": runs[0].worker_id,
                    "tenant_id": str(runs[0].tenant_id),
                }
            )

    logger.info(
        "failure_patterns_detected",
        extra={
            "pattern_count": len(patterns),
            "threshold": threshold,
            "window_hours": window_hours,
        },
    )

    return patterns


async def detect_cost_spikes(
    session: AsyncSession,
    tenant_id: Optional[UUID] = None,
    spike_threshold_percent: float = COST_SPIKE_THRESHOLD_PERCENT,
    min_runs: int = COST_SPIKE_MIN_RUNS,
) -> list[dict]:
    """
    Detect abnormal cost increases.

    PB-S3: This function READS cost data only. No modifications.

    Returns list of detected cost spikes with:
    - worker_id: affected worker
    - avg_cost: rolling average
    - recent_cost: recent run cost
    - spike_percent: percentage increase
    - run_ids: affected runs (provenance)
    """
    # Get completed runs with costs
    query = (
        select(WorkerRun)
        .where(WorkerRun.status == "completed")
        .where(WorkerRun.cost_cents.isnot(None))
        .where(WorkerRun.cost_cents > 0)
        .order_by(WorkerRun.created_at.desc())
    )

    if tenant_id:
        query = query.where(WorkerRun.tenant_id == tenant_id)

    result = await session.execute(query)
    runs = result.scalars().all()

    if len(runs) < min_runs:
        return []

    # Group by worker_id and analyze costs
    worker_runs: dict[str, list[WorkerRun]] = {}
    for run in runs:
        wid = str(run.worker_id)
        if wid not in worker_runs:
            worker_runs[wid] = []
        worker_runs[wid].append(run)

    spikes = []
    for worker_id, wruns in worker_runs.items():
        if len(wruns) < min_runs:
            continue

        # Calculate rolling average (older runs)
        older_runs = wruns[1:]  # Exclude most recent
        if not older_runs:
            continue

        avg_cost = sum(r.cost_cents for r in older_runs) / len(older_runs)
        if avg_cost == 0:
            continue

        # Check most recent run for spike
        recent_run = wruns[0]
        recent_cost = recent_run.cost_cents

        spike_percent = ((recent_cost - avg_cost) / avg_cost) * 100

        if spike_percent >= spike_threshold_percent:
            spikes.append(
                {
                    "worker_id": worker_id,
                    "tenant_id": str(recent_run.tenant_id),
                    "avg_cost_cents": round(avg_cost, 2),
                    "recent_cost_cents": recent_cost,
                    "spike_percent": round(spike_percent, 1),
                    "run_ids": [str(recent_run.id)],
                    "baseline_run_count": len(older_runs),
                }
            )

    logger.info(
        "cost_spikes_detected",
        extra={
            "spike_count": len(spikes),
            "threshold_percent": spike_threshold_percent,
        },
    )

    return spikes


async def emit_feedback(
    session: AsyncSession,
    feedback: PatternFeedbackCreate,
) -> PatternFeedback:
    """
    Emit a feedback record.

    PB-S3: This creates a NEW record in pattern_feedback.
    It does NOT modify any execution data.
    """
    record = PatternFeedback(
        tenant_id=feedback.tenant_id,
        pattern_type=feedback.pattern_type,
        severity=feedback.severity,
        description=feedback.description,
        signature=feedback.signature,
        provenance=feedback.provenance,
        occurrence_count=feedback.occurrence_count,
        time_window_minutes=feedback.time_window_minutes,
        threshold_used=feedback.threshold_used,
        extra_data=feedback.metadata,  # Maps to 'metadata' column in DB
        detected_at=utc_now(),
        created_at=utc_now(),
    )

    session.add(record)
    await session.flush()

    logger.info(
        "pattern_feedback_emitted",
        extra={
            "feedback_id": str(record.id),
            "pattern_type": record.pattern_type,
            "tenant_id": str(record.tenant_id),
            "provenance_count": len(record.provenance),
        },
    )

    return record


async def run_pattern_detection(
    tenant_id: Optional[UUID] = None,
) -> dict:
    """
    Run full pattern detection cycle.

    PB-S3: Detects patterns and emits feedback. No execution modifications.

    Returns summary of detected patterns and emitted feedback.
    """
    result = {
        "failure_patterns": [],
        "cost_spikes": [],
        "feedback_created": 0,
        "errors": [],
    }

    try:
        async with get_async_session() as session:
            # Detect failure patterns
            failure_patterns = await detect_failure_patterns(session, tenant_id)
            result["failure_patterns"] = failure_patterns

            # Emit feedback for each failure pattern
            for pattern in failure_patterns:
                try:
                    feedback = PatternFeedbackCreate(
                        tenant_id=pattern["tenant_id"],  # String, not UUID
                        pattern_type="failure_pattern",
                        severity="warning",
                        description=f"Repeated failure detected: {pattern['count']} occurrences. Sample: {pattern['sample_error'][:200]}",
                        signature=pattern["signature"],
                        provenance=pattern["run_ids"],
                        occurrence_count=pattern["count"],
                        time_window_minutes=FAILURE_PATTERN_WINDOW_HOURS * 60,
                        threshold_used=f"threshold={FAILURE_PATTERN_THRESHOLD}",
                        metadata={"worker_id": pattern["worker_id"]},
                    )
                    await emit_feedback(session, feedback)
                    result["feedback_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Failed to emit failure feedback: {e}")

            # Detect cost spikes
            cost_spikes = await detect_cost_spikes(session, tenant_id)
            result["cost_spikes"] = cost_spikes

            # Emit feedback for each cost spike
            for spike in cost_spikes:
                try:
                    feedback = PatternFeedbackCreate(
                        tenant_id=spike["tenant_id"],  # String, not UUID
                        pattern_type="cost_spike",
                        severity="warning",
                        description=f"Cost spike detected: {spike['spike_percent']}% increase. Recent: {spike['recent_cost_cents']}¢, Avg: {spike['avg_cost_cents']}¢",
                        signature=f"cost_spike_{spike['worker_id']}",
                        provenance=spike["run_ids"],
                        occurrence_count=1,
                        threshold_used=f"spike_threshold={COST_SPIKE_THRESHOLD_PERCENT}%",
                        metadata={
                            "worker_id": spike["worker_id"],
                            "avg_cost_cents": spike["avg_cost_cents"],
                            "recent_cost_cents": spike["recent_cost_cents"],
                            "baseline_run_count": spike["baseline_run_count"],
                        },
                    )
                    await emit_feedback(session, feedback)
                    result["feedback_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Failed to emit cost feedback: {e}")

            await session.commit()

    except Exception as e:
        logger.error(f"pattern_detection_error: {e}", exc_info=True)
        result["errors"].append(str(e))

    return result


async def get_feedback_summary(
    tenant_id: Optional[UUID] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
) -> dict:
    """
    Get feedback summary for ops visibility.

    PB-S3: Read-only query of feedback table.
    """
    async with get_async_session() as session:
        query = select(PatternFeedback).order_by(PatternFeedback.detected_at.desc())

        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == tenant_id)
        if acknowledged is not None:
            query = query.where(PatternFeedback.acknowledged == acknowledged)

        query = query.limit(limit)

        result = await session.execute(query)
        feedback_records = result.scalars().all()

        # Count by type
        type_counts: dict[str, int] = {}
        for record in feedback_records:
            ptype = record.pattern_type
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        return {
            "total": len(feedback_records),
            "by_type": type_counts,
            "records": [
                {
                    "id": str(r.id),
                    "pattern_type": r.pattern_type,
                    "severity": r.severity,
                    "description": r.description[:200],
                    "occurrence_count": r.occurrence_count,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                    "acknowledged": r.acknowledged,
                    "provenance_count": len(r.provenance) if r.provenance else 0,
                }
                for r in feedback_records
            ],
        }
