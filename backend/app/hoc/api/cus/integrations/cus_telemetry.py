# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api (SDK calls)
#   Execution: sync
# Role: Telemetry ingestion API for customer LLM usage
# Callers: SDK cus_reporter.py, external integrations
# Allowed Imports: L4 (cus_telemetry_service), L6 (schemas)
# Forbidden Imports: L1, L3
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer LLM Telemetry Ingestion API

PURPOSE:
    Receives telemetry data from customer SDKs reporting LLM usage.
    This is the DATA PLANE ingestion surface - it records facts about
    what happened during LLM calls.

ENDPOINTS:
    POST /telemetry/llm-usage     - Single call telemetry
    POST /telemetry/llm-usage/batch - Batch telemetry (up to 100 records)
    GET  /telemetry/usage-summary  - Usage summary for dashboard

SEMANTIC:
    - Append-only: Telemetry records are never updated or deleted
    - Idempotent: call_id prevents duplicate ingestion
    - Tenant-isolated: All data scoped to authenticated tenant

AUTHENTICATION:
    Uses integration API key (X-CUS-Integration-Key header) to identify
    both the tenant and the specific integration being reported.
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.schemas.cus_schemas import (
    CusLLMUsageBatchIngest,
    CusLLMUsageIngest,
    CusLLMUsageResponse,
    CusUsageSummary,
)
from app.schemas.response import wrap_dict, wrap_error, wrap_list
from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

router = APIRouter(prefix="/telemetry", tags=["Customer Telemetry"])


# =============================================================================
# DEPENDENCIES
# =============================================================================






async def get_integration_context(
    request: Request,
    x_cus_integration_key: Optional[str] = Header(None, alias="X-CUS-Integration-Key"),
) -> dict:
    """Extract and validate integration context from request.

    The integration key encodes both tenant_id and integration_id,
    allowing SDK to authenticate and route telemetry.

    Returns:
        dict with tenant_id and integration_id
    """
    # First try integration-specific header
    if x_cus_integration_key:
        # Integration key format: {tenant_id}:{integration_id}:{secret}
        # For now, simplified parsing - will add proper validation
        parts = x_cus_integration_key.split(":")
        if len(parts) >= 2:
            return {
                "tenant_id": parts[0],
                "integration_id": parts[1],
                "authenticated": True,
            }

    # Fallback to gateway auth context if available
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context:
        return {
            "tenant_id": getattr(auth_context, "tenant_id", "demo-tenant"),
            "integration_id": None,  # Must be provided in payload
            "authenticated": True,
        }

    # Development fallback
    return {
        "tenant_id": "demo-tenant",
        "integration_id": None,
        "authenticated": False,
    }


# =============================================================================
# TELEMETRY INGESTION ENDPOINTS
# =============================================================================


@router.post("/llm-usage")
async def ingest_llm_usage(
    payload: CusLLMUsageIngest,
    ctx: dict = Depends(get_integration_context),
):
    """Ingest a single LLM usage telemetry record.

    PURPOSE:
        SDK calls this endpoint after each LLM call to report:
        - Token counts (input/output)
        - Cost calculation
        - Latency measurement
        - Policy enforcement result

    IDEMPOTENCY:
        The call_id field serves as an idempotency key. If a record
        with the same call_id already exists, this is a no-op.

    Args:
        payload: Telemetry data from SDK

    Returns:
        Envelope with ingestion result
    """
    tenant_id = ctx["tenant_id"]

    # Use integration_id from context if available, else from payload
    integration_id = ctx.get("integration_id") or payload.integration_id

    if not integration_id:
        return wrap_error(
            "integration_id required",
            code="MISSING_INTEGRATION_ID",
        )

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "activity.telemetry",
            OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "ingest_usage",
                    "tenant_id": tenant_id,
                    "integration_id": integration_id,
                    "payload": payload,
                },
            ),
        )
        if not op.success:
            return wrap_error(op.error, code="INGESTION_ERROR")
        return wrap_dict(op.data)
    except ValueError as e:
        return wrap_error(str(e), code="VALIDATION_ERROR")
    except Exception as e:
        return wrap_error(
            f"Telemetry ingestion failed: {str(e)}",
            code="INGESTION_ERROR",
        )


@router.post("/llm-usage/batch")
async def ingest_llm_usage_batch(
    payload: CusLLMUsageBatchIngest,
    ctx: dict = Depends(get_integration_context),
):
    """Ingest a batch of LLM usage telemetry records.

    PURPOSE:
        SDK may buffer telemetry and send in batches for efficiency.
        Maximum 100 records per batch.

    IDEMPOTENCY:
        Each record's call_id is checked. Duplicates are silently ignored.

    Args:
        payload: Batch of telemetry records

    Returns:
        Envelope with batch ingestion result (accepted/duplicates counts)
    """
    tenant_id = ctx["tenant_id"]
    integration_id = ctx.get("integration_id")

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "activity.telemetry",
            OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "ingest_batch",
                    "tenant_id": tenant_id,
                    "default_integration_id": integration_id,
                    "records": payload.records,
                },
            ),
        )
        if not op.success:
            return wrap_error(op.error or "Batch ingestion failed", code="BATCH_INGESTION_ERROR")
        return wrap_dict(op.data)
    except Exception as e:
        return wrap_error(
            f"Batch ingestion failed: {str(e)}",
            code="BATCH_INGESTION_ERROR",
        )


# =============================================================================
# USAGE QUERY ENDPOINTS
# =============================================================================


@router.get("/usage-summary")
async def get_usage_summary(
    request: Request,
    integration_id: Optional[str] = Query(None, description="Filter by integration"),
    start_date: Optional[date] = Query(None, description="Period start (default: 30 days ago)"),
    end_date: Optional[date] = Query(None, description="Period end (default: today)"),
    ctx: dict = Depends(get_integration_context),
):
    """Get aggregated usage summary for dashboard.

    PURPOSE:
        Provides rolled-up usage statistics for a tenant's integrations.
        Used by dashboard to show cost, token, and call totals.

    Args:
        integration_id: Optional filter for specific integration
        start_date: Period start (default: 30 days ago)
        end_date: Period end (default: today)

    Returns:
        CusUsageSummary with aggregated metrics
    """
    tenant_id = ctx["tenant_id"]

    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "activity.telemetry",
            OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "get_usage_summary",
                    "tenant_id": tenant_id,
                    "integration_id": integration_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            ),
        )
        if not op.success:
            return wrap_error(op.error or "Query failed", code="QUERY_ERROR")
        summary = op.data
        return wrap_dict(summary.model_dump())
    except Exception as e:
        return wrap_error(
            f"Failed to get usage summary: {str(e)}",
            code="QUERY_ERROR",
        )


@router.get("/usage-history")
async def get_usage_history(
    request: Request,
    integration_id: Optional[str] = Query(None, description="Filter by integration"),
    limit: int = Query(50, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    ctx: dict = Depends(get_integration_context),
):
    """Get detailed usage history records.

    PURPOSE:
        Detailed view of individual LLM calls for audit and debugging.
        Paginated for large datasets.

    Args:
        integration_id: Optional filter for specific integration
        limit: Max records per page (default 50, max 1000)
        offset: Pagination offset

    Returns:
        List of CusLLMUsageResponse records
    """
    tenant_id = ctx["tenant_id"]

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "activity.telemetry",
            OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "get_usage_history",
                    "tenant_id": tenant_id,
                    "integration_id": integration_id,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            return wrap_error(op.error or "Query failed", code="QUERY_ERROR")
        records, total = op.data
        return wrap_list(
            items=[r.model_dump() for r in records],
            total=total,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit,
        )
    except Exception as e:
        return wrap_error(
            f"Failed to get usage history: {str(e)}",
            code="QUERY_ERROR",
        )


@router.get("/daily-aggregates")
async def get_daily_aggregates(
    request: Request,
    integration_id: Optional[str] = Query(None, description="Filter by integration"),
    start_date: Optional[date] = Query(None, description="Period start"),
    end_date: Optional[date] = Query(None, description="Period end"),
    ctx: dict = Depends(get_integration_context),
):
    """Get daily aggregated usage for charts.

    PURPOSE:
        Pre-computed daily aggregates for time-series visualization.
        More efficient than computing from raw usage records.

    Args:
        integration_id: Optional filter for specific integration
        start_date: Period start (default: 30 days ago)
        end_date: Period end (default: today)

    Returns:
        List of daily aggregate records
    """
    tenant_id = ctx["tenant_id"]

    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "activity.telemetry",
            OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "get_daily_aggregates",
                    "tenant_id": tenant_id,
                    "integration_id": integration_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            ),
        )
        if not op.success:
            return wrap_error(op.error or "Query failed", code="QUERY_ERROR")
        aggregates = op.data
        return wrap_list(items=aggregates)
    except Exception as e:
        return wrap_error(
            f"Failed to get daily aggregates: {str(e)}",
            code="QUERY_ERROR",
        )
