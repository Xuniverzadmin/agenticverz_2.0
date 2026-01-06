# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6)
# Role: Activity domain read operations (L4)
# Callers: customer_activity_adapter.py (L3)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-281 (ACTIVITY Domain Qualification)
#
# GOVERNANCE NOTE:
# This L4 service provides READ operations for the Activity domain.
# All activity reads must go through this service.
# The L3 adapter should NOT import L6 directly.
# CUSTOMER-SAFE: No cost_cents exposure.

"""
Customer Activity Read Service (L4)

This service provides all READ operations for the Activity domain.
It sits between L3 (CustomerActivityAdapter) and L6 (WorkerRun model).

L3 (Adapter) → L4 (this service) → L6 (TenantService/WorkerRun)

Responsibilities:
- Query runs with tenant isolation (MANDATORY)
- Get run details with tenant verification
- Translate internal runs → customer-visible activity
- Hide internal fields (cost_cents, replay_token, input_json internals)
- Stable pagination and ordering

Reference: ACTIVITY Domain Qualification Task
"""

from dataclasses import dataclass
from typing import Any, List, Optional, cast

from sqlmodel import Session, select

# L6 imports (allowed)
from app.models.tenant import WorkerRun


@dataclass
class ActivitySummary:
    """
    Customer-visible activity summary.

    IMPORTANT: No cost_cents, no replay_token, no internal IDs.
    This is what customers see in the Activity domain.
    """

    run_id: str
    worker_name: str  # Translated from worker_id
    task_preview: str  # Truncated task (max 200 chars)
    status: str
    success: Optional[bool]
    total_steps: Optional[int]
    duration_ms: Optional[int]
    created_at: str
    completed_at: Optional[str]
    # NO cost_cents - internal metric only


@dataclass
class ActivityDetail:
    """
    Customer-visible activity detail.

    Provides more context than summary but still hides internals.
    """

    run_id: str
    worker_name: str
    task: str  # Full task (up to 2000 chars)
    status: str
    success: Optional[bool]
    error_summary: Optional[str]  # Redacted error (no stack traces)
    total_steps: Optional[int]
    recoveries: int
    policy_violations: int
    duration_ms: Optional[int]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    # NO cost_cents, NO input_json, NO output_json, NO replay_token


@dataclass
class ActivityListResult:
    """Paginated list of activities."""

    items: List[ActivitySummary]
    total: int
    limit: int
    offset: int
    has_more: bool


class CustomerActivityReadService:
    """
    L4 service for activity read operations.

    Provides tenant-scoped, bounded reads for the Activity domain.
    All L3 adapters must use this service for activity reads.

    INVARIANT: tenant_id is REQUIRED for all operations.
    """

    def __init__(self, session: Session):
        """
        Initialize with database session.

        Args:
            session: SQLModel session (injected by L3)
        """
        self._session = session

    def list_activities(
        self,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> ActivityListResult:
        """
        List activities for a tenant.

        INVARIANT: tenant_id is REQUIRED - cannot list cross-tenant.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            limit: Max items to return (1-100)
            offset: Pagination offset (>= 0)
            status: Filter by status (optional)
            worker_id: Filter by worker (optional)

        Returns:
            ActivityListResult with customer-safe summaries
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for list_activities")

        # Bound limits
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        # Build query with tenant scope (MANDATORY)
        stmt = select(WorkerRun).where(WorkerRun.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(WorkerRun.status == status)
        if worker_id:
            stmt = stmt.where(WorkerRun.worker_id == worker_id)

        # Order by created_at DESC (most recent first)
        stmt = stmt.order_by(cast(Any, WorkerRun.created_at).desc())

        # Get total count (for pagination)
        count_stmt = select(WorkerRun).where(WorkerRun.tenant_id == tenant_id)
        if status:
            count_stmt = count_stmt.where(WorkerRun.status == status)
        if worker_id:
            count_stmt = count_stmt.where(WorkerRun.worker_id == worker_id)

        # Execute with pagination
        runs = list(self._session.exec(stmt.offset(offset).limit(limit)))
        total = len(list(self._session.exec(count_stmt)))

        # Transform to customer-safe summaries
        items = [self._to_summary(run) for run in runs]

        return ActivityListResult(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def get_activity(
        self,
        tenant_id: str,
        run_id: str,
    ) -> Optional[ActivityDetail]:
        """
        Get activity detail for a specific run.

        INVARIANT: tenant_id is REQUIRED - cannot fetch cross-tenant.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            run_id: Run ID to fetch

        Returns:
            ActivityDetail if found and belongs to tenant, None otherwise
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_activity")
        if not run_id:
            raise ValueError("run_id is required for get_activity")

        # Query with tenant scope (MANDATORY)
        stmt = select(WorkerRun).where(
            WorkerRun.id == run_id,
            WorkerRun.tenant_id == tenant_id,  # Tenant isolation
        )

        run = self._session.exec(stmt).first()
        if not run:
            return None

        return self._to_detail(run)

    def _to_summary(self, run: WorkerRun) -> ActivitySummary:
        """
        Transform internal WorkerRun to customer-safe ActivitySummary.

        HIDES: cost_cents, replay_token, input_json, output_json
        """
        return ActivitySummary(
            run_id=run.id,
            worker_name=run.worker_id,  # Could be translated via worker registry
            task_preview=run.task[:200] if run.task else "",
            status=run.status,
            success=run.success,
            total_steps=run.stages_completed,
            duration_ms=run.total_latency_ms,
            created_at=run.created_at.isoformat() if run.created_at else "",
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )

    def _to_detail(self, run: WorkerRun) -> ActivityDetail:
        """
        Transform internal WorkerRun to customer-safe ActivityDetail.

        HIDES: cost_cents, replay_token, input_json, output_json, raw stack traces
        """
        # Redact error message (remove stack traces, limit length)
        error_summary = None
        if run.error:
            # Take first line only, max 500 chars
            error_lines = run.error.split("\n")
            error_summary = error_lines[0][:500] if error_lines else None

        return ActivityDetail(
            run_id=run.id,
            worker_name=run.worker_id,
            task=run.task[:2000] if run.task else "",
            status=run.status,
            success=run.success,
            error_summary=error_summary,
            total_steps=run.stages_completed,
            recoveries=run.recoveries or 0,
            policy_violations=run.policy_violations or 0,
            duration_ms=run.total_latency_ms,
            created_at=run.created_at.isoformat() if run.created_at else "",
            started_at=None,  # Not exposed in WorkerRun, would need join
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )


def get_customer_activity_read_service(session: Optional[Session] = None) -> CustomerActivityReadService:
    """
    Factory function for CustomerActivityReadService.

    Args:
        session: Optional SQLModel session. If not provided, creates one internally.

    Returns:
        Configured CustomerActivityReadService instance
    """
    if session is None:
        from app.db import engine

        session = Session(engine)
    return CustomerActivityReadService(session)
