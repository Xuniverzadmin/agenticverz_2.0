# Layer: L3 — Boundary Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L4)
# Role: Customer activity boundary adapter (L2 → L3 → L4)
# Callers: L2 activity routes
# Allowed Imports: L4
# Forbidden Imports: L1, L2, L5, L6
# Reference: ACTIVITY Domain Qualification Task
#
# GOVERNANCE NOTE:
# This L3 adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only see their own data)
# - Customer-safe schema (no internal fields exposed)
# - RBAC context validation
#
# This adapter qualifies ACTIVITY_LIST and ACTIVITY_DETAIL capabilities.

"""
Customer Activity Boundary Adapter (L3)

This adapter sits between L2 (Activity API routes) and L4 (CustomerActivityReadService).

L2 (API) → L3 (this adapter) → L4 (CustomerActivityReadService)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation (customer can only see their own activities)
3. Transforms to customer-safe schema (no internal fields)
4. Delegates to L4 service
5. Returns customer-friendly results to L2

This is a thin translation layer - no business logic, no domain decisions.

Reference: ACTIVITY Domain Qualification Task
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# L4 imports ONLY (no L6!)
from app.services.activity.customer_activity_read_service import (
    ActivityDetail,
    ActivityListResult,
    ActivitySummary,
    CustomerActivityReadService,
    get_customer_activity_read_service,
)

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
    INVARIANT: No L6 imports - delegates to L4 only.
    """

    def __init__(self):
        """Initialize adapter with lazy L4 service loading."""
        self._service: Optional[CustomerActivityReadService] = None

    def _get_service(self) -> CustomerActivityReadService:
        """Get the L4 CustomerActivityReadService (lazy loaded)."""
        if self._service is None:
            self._service = get_customer_activity_read_service()
        return self._service

    def list_activities(
        self,
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
            tenant_id: Customer's tenant ID (REQUIRED)
            limit: Max items (1-100)
            offset: Pagination offset
            status: Filter by status
            worker_id: Filter by worker

        Returns:
            CustomerActivityListResponse with customer-safe data

        Raises:
            ValueError: If tenant_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for list_activities")

        # Delegate to L4 service
        result: ActivityListResult = self._get_service().list_activities(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            status=status,
            worker_id=worker_id,
        )

        # Transform L4 DTOs to L3 customer-safe DTOs
        items = [self._to_customer_summary(s) for s in result.items]

        return CustomerActivityListResponse(
            items=items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            has_more=result.has_more,
        )

    def get_activity(
        self,
        tenant_id: str,
        run_id: str,
    ) -> Optional[CustomerActivityDetail]:
        """
        Get activity detail for a specific run.

        INVARIANT: tenant_id REQUIRED - enforces tenant isolation.
        If run doesn't exist or belongs to different tenant, returns None.

        Args:
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

        # Delegate to L4 service
        detail: Optional[ActivityDetail] = self._get_service().get_activity(
            tenant_id=tenant_id,
            run_id=run_id,
        )

        if not detail:
            return None

        return self._to_customer_detail(detail)

    def _to_customer_summary(self, summary: ActivitySummary) -> CustomerActivitySummary:
        """Transform L4 ActivitySummary to L3 CustomerActivitySummary."""
        return CustomerActivitySummary(
            run_id=summary.run_id,
            worker_name=summary.worker_name,
            task_preview=summary.task_preview,
            status=summary.status,
            success=summary.success,
            total_steps=summary.total_steps,
            duration_ms=summary.duration_ms,
            created_at=summary.created_at,
            completed_at=summary.completed_at,
        )

    def _to_customer_detail(self, detail: ActivityDetail) -> CustomerActivityDetail:
        """Transform L4 ActivityDetail to L3 CustomerActivityDetail."""
        return CustomerActivityDetail(
            run_id=detail.run_id,
            worker_name=detail.worker_name,
            task=detail.task,
            status=detail.status,
            success=detail.success,
            error_summary=detail.error_summary,
            total_steps=detail.total_steps,
            recoveries=detail.recoveries,
            policy_violations=detail.policy_violations,
            duration_ms=detail.duration_ms,
            created_at=detail.created_at,
            started_at=detail.started_at,
            completed_at=detail.completed_at,
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

    Reference: ACTIVITY Domain Qualification (L2→L3→L4 pattern)
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
