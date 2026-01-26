# Layer: L3 — Boundary Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L4)
# Role: Customer logs boundary adapter (L2 → L3 → L4)
# Callers: guard_logs.py (L2)
# Allowed Imports: L4
# Forbidden Imports: L1, L2, L5, L6
# Reference: PIN-280, PIN-281 (L2 Promotion Governance - PHASE 1 L3 Closure)
#
# GOVERNANCE NOTE:
# This L3 adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only see their own data)
# - Customer-safe schema (no internal fields exposed)
# - Rate limiting (via caller context)
#
# This adapter promotes LOGS_LIST capability from L4 to L3.

"""
Customer Logs Boundary Adapter (L3)

This adapter sits between L2 (guard_logs.py API) and L4 (LogsReadService).

L2 (Guard API) → L3 (this adapter) → L4 (LogsReadService)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation (customer can only see their own logs)
3. Transforms to customer-safe schema (no internal fields)
4. Delegates to L4 service
5. Returns customer-friendly results to L2

This is a thin translation layer - no business logic, no domain decisions.

Reference: PIN-280 (L2 Promotion Governance), PIN-281 (PHASE 1 L3 Closure)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# =============================================================================
# Customer-Safe DTOs (No Internal Fields)
# =============================================================================


class CustomerLogSummary(BaseModel):
    """Customer-safe log summary for list view."""

    log_id: str
    run_id: str
    agent_id: Optional[str] = None
    status: str
    total_steps: int
    success_count: int
    failure_count: int
    started_at: str
    completed_at: Optional[str] = None
    # Customer-visible metrics only
    total_duration_ms: float = 0.0
    # No cost_cents exposed to customer (internal metric)


class CustomerLogStep(BaseModel):
    """Customer-safe log step for detail view."""

    step_index: int
    skill_name: str
    status: str
    outcome_category: str
    outcome_code: Optional[str] = None
    # Redacted outcome_data - only safe fields
    duration_ms: float
    timestamp: str
    # No cost_cents, no internal hashes, no replay behavior


class CustomerLogDetail(BaseModel):
    """Customer-safe log detail."""

    log_id: str
    run_id: str
    correlation_id: str
    agent_id: Optional[str] = None
    status: str
    started_at: str
    completed_at: Optional[str] = None
    steps: List[CustomerLogStep]
    # Summary metrics
    total_steps: int
    success_count: int
    failure_count: int
    total_duration_ms: float
    # No plan, no root_hash, no seed, no internal metadata


class CustomerLogListResponse(BaseModel):
    """Paginated customer log list."""

    items: List[CustomerLogSummary]
    total: int
    page: int
    page_size: int


# =============================================================================
# L3 Adapter Class
# =============================================================================


class CustomerLogsAdapter:
    """
    Boundary adapter for customer logs operations.

    This class provides the ONLY interface that L2 (guard_logs.py) may use
    to access log/trace functionality. It enforces tenant isolation and
    transforms data to customer-safe schemas.

    PIN-280 Rule: L3 Is Translation Only + Tenant Scoping
    PIN-281 Rule: L3 imports L4 only (no L6 direct access)
    """

    def __init__(self):
        """Initialize adapter with lazy L4 service loading."""
        self._service = None

    async def _get_service(self):
        """Get the L4 LogsReadService (lazy loaded)."""
        if self._service is None:
            # L5 engine import (migrated to HOC per SWEEP-03)
            from app.hoc.cus.logs.L5_engines.logs_read_engine import get_logs_read_service

            self._service = get_logs_read_service()
        return self._service

    async def list_logs(
        self,
        tenant_id: str,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CustomerLogListResponse:
        """
        List logs for a customer.

        Enforces tenant isolation - customer can only see their own logs.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            agent_id: Filter by agent
            status: Filter by status (running, completed, failed)
            from_date: Filter from date (ISO format)
            to_date: Filter to date (ISO format)
            limit: Page size (max 100)
            offset: Pagination offset

        Returns:
            CustomerLogListResponse with customer-safe summaries

        Reference: PIN-281 Phase 4 (L4→L3 promotion)
        """
        # Enforce pagination limits
        limit = min(limit, 100)

        # L3 → L4 delegation
        service = await self._get_service()
        summaries = await service.search_traces(
            tenant_id=tenant_id,  # REQUIRED - enforces tenant isolation
            agent_id=agent_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

        # Get total count for pagination
        total_count = await service.get_trace_count(tenant_id=tenant_id)

        # Transform to customer-safe schema
        items = [
            CustomerLogSummary(
                log_id=f"log_{s.run_id.replace('run_', '')}" if s.run_id.startswith("run_") else f"log_{s.run_id}",
                run_id=s.run_id,
                agent_id=s.agent_id,
                status=s.status or "unknown",
                total_steps=s.total_steps,
                success_count=s.success_count,
                failure_count=s.failure_count,
                started_at=s.started_at.isoformat() if isinstance(s.started_at, datetime) else str(s.started_at),
                completed_at=s.completed_at.isoformat()
                if s.completed_at and isinstance(s.completed_at, datetime)
                else (str(s.completed_at) if s.completed_at else None),
                total_duration_ms=s.total_duration_ms,
                # cost_cents intentionally omitted - internal metric
            )
            for s in summaries
        ]

        return CustomerLogListResponse(
            items=items,
            total=total_count,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit,
        )

    async def get_log(
        self,
        log_id: str,
        tenant_id: str,
    ) -> Optional[CustomerLogDetail]:
        """
        Get log detail for a customer.

        Enforces tenant isolation - returns None if log belongs to different tenant.

        Args:
            log_id: Log ID (log_xxx format)
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerLogDetail if found and authorized, None otherwise

        Reference: PIN-281 Phase 4 (L4→L3 promotion)
        """
        # Convert log_id to trace_id format
        trace_id = log_id.replace("log_", "trace_") if log_id.startswith("log_") else log_id

        # L3 → L4 delegation with tenant enforcement
        service = await self._get_service()
        trace = await service.get_trace(
            trace_id=trace_id,
            tenant_id=tenant_id,  # REQUIRED - enforces tenant isolation
        )

        if trace is None:
            # Also try by run_id
            trace = await service.get_trace(
                trace_id=log_id.replace("log_", "run_") if log_id.startswith("log_") else log_id,
                tenant_id=tenant_id,
            )

        if trace is None:
            return None

        # Transform steps to customer-safe schema
        customer_steps = [
            CustomerLogStep(
                step_index=step.step_index,
                skill_name=step.skill_name,
                status=step.status.value if hasattr(step.status, "value") else str(step.status),
                outcome_category=step.outcome_category,
                outcome_code=step.outcome_code,
                duration_ms=step.duration_ms,
                timestamp=step.timestamp.isoformat() if isinstance(step.timestamp, datetime) else str(step.timestamp),
                # cost_cents, hashes, replay_behavior intentionally omitted
            )
            for step in trace.steps
        ]

        # Calculate summary metrics
        success_count = sum(1 for s in trace.steps if s.outcome_category == "SUCCESS")
        failure_count = sum(1 for s in trace.steps if s.outcome_category == "FAILURE")
        total_duration = sum(s.duration_ms for s in trace.steps)

        return CustomerLogDetail(
            log_id=log_id,
            run_id=trace.run_id,
            correlation_id=trace.correlation_id,
            agent_id=trace.agent_id,
            status=trace.status or "unknown",
            started_at=trace.started_at.isoformat()
            if isinstance(trace.started_at, datetime)
            else str(trace.started_at),
            completed_at=trace.completed_at.isoformat()
            if trace.completed_at and isinstance(trace.completed_at, datetime)
            else None,
            steps=customer_steps,
            total_steps=len(trace.steps),
            success_count=success_count,
            failure_count=failure_count,
            total_duration_ms=total_duration,
            # plan, root_hash, seed, metadata intentionally omitted
        )

    async def export_logs(
        self,
        tenant_id: str,
        format: str = "json",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """
        Export logs for a customer.

        Enforces tenant isolation and format constraints.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            format: Export format (json, csv)
            from_date: Filter from date
            to_date: Filter to date
            limit: Max records (capped at 10000)

        Returns:
            Export data in requested format

        Reference: PIN-281 Phase 4 (L4→L3 promotion)
        """
        # Enforce export limits
        limit = min(limit, 10000)

        # Get logs
        response = await self.list_logs(
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=0,
        )

        if format == "csv":
            # CSV header and rows
            headers = [
                "log_id",
                "run_id",
                "agent_id",
                "status",
                "total_steps",
                "success_count",
                "failure_count",
                "started_at",
                "completed_at",
                "duration_ms",
            ]
            rows = [
                [
                    item.log_id,
                    item.run_id,
                    item.agent_id or "",
                    item.status,
                    str(item.total_steps),
                    str(item.success_count),
                    str(item.failure_count),
                    item.started_at,
                    item.completed_at or "",
                    str(item.total_duration_ms),
                ]
                for item in response.items
            ]
            return {
                "format": "csv",
                "headers": headers,
                "rows": rows,
                "total": response.total,
            }
        else:
            # JSON format (default)
            return {
                "format": "json",
                "logs": [item.model_dump() for item in response.items],
                "total": response.total,
                "exported_at": datetime.utcnow().isoformat(),
            }


# =============================================================================
# Singleton Factory
# =============================================================================

_customer_logs_adapter_instance: Optional[CustomerLogsAdapter] = None


def get_customer_logs_adapter() -> CustomerLogsAdapter:
    """
    Get the singleton CustomerLogsAdapter instance.

    This is the ONLY way L2 should obtain a logs adapter.
    Direct instantiation is discouraged.

    Returns:
        CustomerLogsAdapter singleton instance

    Reference: PIN-281 (L3 Is the Only Entry for L2)
    """
    global _customer_logs_adapter_instance
    if _customer_logs_adapter_instance is None:
        _customer_logs_adapter_instance = CustomerLogsAdapter()
    return _customer_logs_adapter_instance


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerLogsAdapter",
    "get_customer_logs_adapter",
    # DTOs for L2 convenience
    "CustomerLogSummary",
    "CustomerLogStep",
    "CustomerLogDetail",
    "CustomerLogListResponse",
]
