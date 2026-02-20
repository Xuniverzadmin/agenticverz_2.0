# capability_id: CAP-002
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine, L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: CostSimCanaryReportModel
#   Writes: CostSimCanaryReportModel
# Database:
#   Scope: domain (analytics)
#   Models: CostSimCanaryReportModel
# Role: CostSim Canary Report Driver - DB operations for canary validation reports
# Callers: canary_engine.py (L5), canary_coordinator.py (L4)
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-518, PIN-520 (L6 Purity)
"""
Canary Report Driver for CostSim V2.

Handles database operations for canary validation reports. Separated from
provenance_driver.py (PIN-518 Gap 2) because canary reports have different:
- Write pattern: low-volume, atomic (vs high-volume buffered)
- Retention: medium (vs long)
- Query pattern: dashboard-style (vs audit-style)
- Failure tolerance: must-succeed (vs best-effort)

Usage:
    from app.hoc.cus.analytics.L6_drivers.canary_report_driver import (
        write_canary_report,
        query_canary_reports,
        get_canary_report_by_run_id,
    )

    # Write report
    report_id = await write_canary_report(
        run_id="canary_20260203_120000",
        timestamp=datetime.now(timezone.utc),
        status="pass",
        ...
    )

    # Query reports
    reports = await query_canary_reports(status="fail", limit=10)

    # Get by run ID
    report = await get_canary_report_by_run_id("canary_20260203_120000")
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import async_session_context
from app.models.costsim_cb import CostSimCanaryReportModel

logger = logging.getLogger("nova.costsim.canary_report_driver")


async def write_canary_report(
    session: AsyncSession,
    run_id: str,
    timestamp: datetime,
    status: str,
    total_samples: int,
    matching_samples: int,
    minor_drift_samples: int,
    major_drift_samples: int,
    median_cost_diff: Optional[float] = None,
    p90_cost_diff: Optional[float] = None,
    kl_divergence: Optional[float] = None,
    outlier_count: Optional[int] = None,
    passed: bool = True,
    failure_reasons: Optional[List[str]] = None,
    artifact_paths: Optional[List[str]] = None,
    golden_comparison: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Write a canary report to the database.

    L6 Contract:
        - Session REQUIRED (passed from L4 coordinator)
        - L6 does NOT commit (L4 owns transaction boundary)

    Args:
        session: Async session (required, from L4 coordinator)
        run_id: Unique run identifier
        timestamp: Run timestamp
        status: Run status (pass, fail, error, skipped)
        total_samples: Total samples tested
        matching_samples: Samples with matching V1/V2 results
        minor_drift_samples: Samples with minor drift
        major_drift_samples: Samples with major drift
        median_cost_diff: Median cost difference
        p90_cost_diff: 90th percentile cost difference
        kl_divergence: KL divergence score
        outlier_count: Number of outliers
        passed: Whether canary passed
        failure_reasons: List of failure reasons
        artifact_paths: List of artifact file paths
        golden_comparison: Golden comparison results

    Returns:
        ID of created record
    """
    record = CostSimCanaryReportModel(
        run_id=run_id,
        timestamp=timestamp,
        status=status,
        total_samples=total_samples,
        matching_samples=matching_samples,
        minor_drift_samples=minor_drift_samples,
        major_drift_samples=major_drift_samples,
        median_cost_diff=median_cost_diff,
        p90_cost_diff=p90_cost_diff,
        kl_divergence=kl_divergence,
        outlier_count=outlier_count,
        passed=passed,
        failure_reasons_json=json.dumps(failure_reasons) if failure_reasons else None,
        artifact_paths_json=json.dumps(artifact_paths) if artifact_paths else None,
        golden_comparison_json=json.dumps(golden_comparison) if golden_comparison else None,
    )

    session.add(record)
    await session.flush()
    await session.refresh(record)
    # L6 does NOT commit — L4 coordinator owns transaction boundary

    logger.info(f"Canary report created: id={record.id}, run_id={run_id}, passed={passed}")

    return record.id


async def query_canary_reports(
    status: Optional[str] = None,
    passed: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Query canary reports from the database.

    Args:
        status: Filter by status (pass, fail, error, skipped)
        passed: Filter by passed status
        start_date: Start of time range
        end_date: End of time range
        limit: Maximum records to return
        offset: Pagination offset

    Returns:
        List of canary reports as dictionaries
    """
    async with async_session_context() as session:
        conditions = []

        if status:
            conditions.append(CostSimCanaryReportModel.status == status)
        if passed is not None:
            conditions.append(CostSimCanaryReportModel.passed == passed)
        if start_date:
            conditions.append(CostSimCanaryReportModel.timestamp >= start_date)
        if end_date:
            conditions.append(CostSimCanaryReportModel.timestamp <= end_date)

        statement = select(CostSimCanaryReportModel)

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = statement.order_by(CostSimCanaryReportModel.timestamp.desc()).limit(limit).offset(offset)

        result = await session.execute(statement)

        return [record.to_dict() for record in result.scalars()]


async def get_canary_report_by_run_id(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a canary report by run ID.

    Args:
        run_id: Run identifier

    Returns:
        Canary report as dictionary or None if not found
    """
    async with async_session_context() as session:
        result = await session.execute(
            select(CostSimCanaryReportModel).where(CostSimCanaryReportModel.run_id == run_id)
        )
        record = result.scalars().first()
        return record.to_dict() if record else None
