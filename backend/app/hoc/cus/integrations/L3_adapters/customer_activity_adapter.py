# Layer: L3 — Boundary Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L5 ActivityFacade)
# Role: Customer activity boundary adapter (L2 → L3 → L5)
# Callers: L2 activity routes
# Allowed Imports: L5
# Forbidden Imports: L1, L2, L6
# Reference: ACTIVITY Domain Qualification Task, SWEEP-03
#
# GOVERNANCE NOTE:
# This L3 adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only see their own data)
# - Customer-safe schema (no internal fields exposed)
# - RBAC context validation
#
# This adapter qualifies ACTIVITY_LIST and ACTIVITY_DETAIL capabilities.
#
# MIGRATION NOTE (SWEEP-03):
# Updated to use HOC ActivityFacade. Field mapping:
# - ActivitySummary → RunSummaryResult (with field translation)
# - ActivityDetail → RunDetailResult (with field translation)
# - ActivityListResult → RunListResult

"""
Customer Activity Boundary Adapter (L3)

This adapter sits between L2 (Activity API routes) and L5 (ActivityFacade).

L2 (API) → L3 (this adapter) → L5 (ActivityFacade)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation (customer can only see their own activities)
3. Transforms to customer-safe schema (no internal fields)
4. Delegates to L5 facade
5. Returns customer-friendly results to L2

This is a thin translation layer - no business logic, no domain decisions.

Reference: ACTIVITY Domain Qualification Task, SWEEP-03 Migration
"""

from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

# L5 imports (migrated to HOC per SWEEP-03)
from app.hoc.cus.activity.L5_engines.activity_facade import (
    ActivityFacade,
    RunDetailResult,
    RunListResult,
    RunSummaryResult,
    get_activity_facade,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Customer-Safe DTOs (No Internal Fields)
# =============================================================================


class CustomerActivitySummary(BaseModel):
    """Customer-safe activity summary for list view."""

    run_id: str
    worker_name: str
    task_preview: str = Field(max_length=200)
    status: str
    success: Optional[bool] = None
    total_steps: Optional[int] = None
    duration_ms: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    # NO cost_cents - internal metric only


class CustomerActivityDetail(BaseModel):
    """Customer-safe activity detail."""

    run_id: str
    worker_name: str
    task: str = Field(max_length=2000)
    status: str
    success: Optional[bool] = None
    error_summary: Optional[str] = Field(default=None, max_length=500)
    total_steps: Optional[int] = None
    recoveries: int = 0
    policy_violations: int = 0
    duration_ms: Optional[int] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    # NO cost_cents, NO input_json, NO output_json, NO replay_token


class CustomerActivityListResponse(BaseModel):
    """Paginated list of customer activities."""

    items: List[CustomerActivitySummary]
    total: int
    limit: int
    offset: int
    has_more: bool


# =============================================================================
# Customer Activity Adapter (L3)
# =============================================================================


class CustomerActivityAdapter:
    """
    L3 boundary adapter for customer activity operations.

    INVARIANT: All methods require tenant_id for isolation.
    INVARIANT: No L6 imports - delegates to L5 only.

    NOTE: This adapter now uses async methods to match HOC ActivityFacade.
    """

    def __init__(self):
        """Initialize adapter with lazy L5 facade loading."""
        self._facade: Optional[ActivityFacade] = None

    def _get_facade(self) -> ActivityFacade:
        """Get the L5 ActivityFacade (lazy loaded)."""
        if self._facade is None:
            self._facade = get_activity_facade()
        return self._facade

    async def list_activities(
        self,
        session: "AsyncSession",
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> CustomerActivityListResponse:
        """
        List activities for the customer's tenant.

        INVARIANT: tenant_id REQUIRED - enforces tenant isolation.

        Args:
            session: Database session
            tenant_id: Customer's tenant ID (REQUIRED)
            limit: Max items (1-100)
            offset: Pagination offset
            status: Filter by status
            worker_id: Filter by worker (maps to source filter)

        Returns:
            CustomerActivityListResponse with customer-safe data

        Raises:
            ValueError: If tenant_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for list_activities")

        # Map status filter to HOC format
        status_list = [status] if status else None

        # Map worker_id to source filter (HOC uses source/provider_type)
        source_list = [worker_id] if worker_id else None

        # Delegate to L5 facade
        result: RunListResult = await self._get_facade().get_runs(
            session=session,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            status=status_list,
            source=source_list,
        )

        # Transform L5 DTOs to L3 customer-safe DTOs
        items = [self._to_customer_summary(s) for s in result.items]

        return CustomerActivityListResponse(
            items=items,
            total=result.total,
            limit=limit,
            offset=offset,
            has_more=result.has_more,
        )

    async def get_activity(
        self,
        session: "AsyncSession",
        tenant_id: str,
        run_id: str,
    ) -> Optional[CustomerActivityDetail]:
        """
        Get activity detail for a specific run.

        INVARIANT: tenant_id REQUIRED - enforces tenant isolation.
        If run doesn't exist or belongs to different tenant, returns None.

        Args:
            session: Database session
            tenant_id: Customer's tenant ID (REQUIRED)
            run_id: Run ID to fetch

        Returns:
            CustomerActivityDetail if found, None otherwise

        Raises:
            ValueError: If tenant_id or run_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_activity")
        if not run_id:
            raise ValueError("run_id is required for get_activity")

        # Delegate to L5 facade
        detail: Optional[RunDetailResult] = await self._get_facade().get_run_detail(
            session=session,
            tenant_id=tenant_id,
            run_id=run_id,
        )

        if not detail:
            return None

        return self._to_customer_detail(detail)

    def _to_customer_summary(self, summary: RunSummaryResult) -> CustomerActivitySummary:
        """
        Transform L5 RunSummaryResult to L3 CustomerActivitySummary.

        Field mapping (HOC → Customer):
        - run_id → run_id
        - source → worker_name (best available approximation)
        - status → task_preview (truncated)
        - status → status
        - status == 'COMPLETED' → success (derived)
        - None → total_steps (not available in HOC summary)
        - duration_ms → duration_ms
        - started_at → created_at (ISO string)
        - completed_at → completed_at (ISO string)
        """
        # Derive success from status
        success = summary.status.upper() == "COMPLETED" if summary.status else None

        return CustomerActivitySummary(
            run_id=summary.run_id,
            worker_name=summary.source or "unknown",
            task_preview=f"Run {summary.run_id[:8]}... ({summary.status})"[:200],
            status=summary.status or "unknown",
            success=success,
            total_steps=None,  # Not available in RunSummaryResult
            duration_ms=int(summary.duration_ms) if summary.duration_ms else None,
            created_at=summary.started_at.isoformat() if summary.started_at else "",
            completed_at=summary.completed_at.isoformat() if summary.completed_at else None,
        )

    def _to_customer_detail(self, detail: RunDetailResult) -> CustomerActivityDetail:
        """
        Transform L5 RunDetailResult to L3 CustomerActivityDetail.

        Field mapping (HOC → Customer):
        - run_id → run_id
        - source → worker_name
        - goal → task
        - status → status
        - status == 'COMPLETED' → success (derived)
        - error_message → error_summary
        - None → total_steps (not in HOC)
        - 0 → recoveries (not in HOC)
        - policy_violation (bool) → policy_violations (int, 1 if true)
        - duration_ms → duration_ms
        - started_at → created_at, started_at
        - completed_at → completed_at
        """
        success = detail.status.upper() == "COMPLETED" if detail.status else None

        return CustomerActivityDetail(
            run_id=detail.run_id,
            worker_name=detail.source or "unknown",
            task=detail.goal or f"Run {detail.run_id}",
            status=detail.status or "unknown",
            success=success,
            error_summary=detail.error_message[:500] if detail.error_message else None,
            total_steps=None,  # Not available in RunDetailResult
            recoveries=0,  # Not tracked in HOC
            policy_violations=1 if detail.policy_violation else 0,
            duration_ms=int(detail.duration_ms) if detail.duration_ms else None,
            created_at=detail.started_at.isoformat() if detail.started_at else "",
            started_at=detail.started_at.isoformat() if detail.started_at else None,
            completed_at=detail.completed_at.isoformat() if detail.completed_at else None,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_customer_activity_adapter_instance: Optional[CustomerActivityAdapter] = None


def get_customer_activity_adapter() -> CustomerActivityAdapter:
    """
    Get the singleton CustomerActivityAdapter instance.

    This is the ONLY way L2 should obtain an activity adapter.
    Direct instantiation is discouraged.

    Returns:
        CustomerActivityAdapter singleton instance

    Reference: ACTIVITY Domain Qualification (L2→L3→L5 pattern)
    """
    global _customer_activity_adapter_instance
    if _customer_activity_adapter_instance is None:
        _customer_activity_adapter_instance = CustomerActivityAdapter()
    return _customer_activity_adapter_instance


# Explicit exports for L2 consumers
__all__ = [
    "CustomerActivityAdapter",
    "CustomerActivitySummary",
    "CustomerActivityDetail",
    "CustomerActivityListResponse",
    "get_customer_activity_adapter",
]
