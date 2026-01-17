# Layer: L2a — Product API (Console-scoped)
# Product: AI Console (Customer Console)
# Auth: verify_console_token (aud=console)
# Reference: PIN-280, PIN-281 (L2 Promotion Governance)
# NOTE: Workers NEVER call this. SDK NEVER imports this.

"""Guard Logs API - Customer Console Logs Endpoint

This router provides endpoints for the Customer Console (guard.agenticverz.com).
Focused on LOG VISIBILITY - customers can see their execution audit trail.

Endpoints:
- GET  /guard/logs          - List customer logs (execution audit trail)
- GET  /guard/logs/export   - Export logs (JSON or CSV)
- GET  /guard/logs/{id}     - Log detail with steps

PIN-281 Promotion:
- L4→L3: customer_logs_adapter.py (boundary adapter)
- L3→L2: This file (API route)

Rule: One adapter per route. No business logic here.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

# L3 Adapter (only import from L3)
from app.adapters.customer_logs_adapter import (
    CustomerLogDetail,
    CustomerLogListResponse,
    get_customer_logs_adapter,
)

# Category 2 Auth: Domain-separated authentication for Customer Console
from app.auth.console_auth import verify_console_token
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.guard_logs")

# =============================================================================
# Router - Customer Console Logs (tenant-scoped)
# =============================================================================

router = APIRouter(
    prefix="/guard/logs",
    tags=["Guard Console - Logs"],
    dependencies=[Depends(verify_console_token)],  # Category 2: Strict console auth
)


# =============================================================================
# List Logs Endpoint
# =============================================================================


@router.get("", response_model=CustomerLogListResponse)
async def list_logs(
    tenant_id: str = Query(..., description="Tenant ID (required)"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status (running, completed, failed)"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(50, le=100, description="Page size (max 100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List execution logs for customer.

    Returns paginated list of customer logs (execution audit trail).
    Customer can only see their own tenant's logs (enforced by adapter).

    This endpoint:
    - Shows what ran / is running
    - Provides step counts and status
    - Enables filtering by agent, status, date range
    - Supports pagination

    No internal fields exposed (cost_cents, hashes, replay data).

    Reference: PIN-281 Phase 5 (L3→L2 promotion)
    """
    adapter = get_customer_logs_adapter()

    try:
        response = await adapter.list_logs(
            tenant_id=tenant_id,
            agent_id=agent_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
        return response
    except Exception as e:
        logger.error(f"Error listing logs for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


# =============================================================================
# Export Endpoint (MUST come before /{log_id} to avoid route collision)
# =============================================================================


@router.get("/export")
async def export_logs(
    tenant_id: str = Query(..., description="Tenant ID (required)"),
    format: str = Query("json", description="Export format (json, csv)"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(1000, le=10000, description="Max records (max 10000)"),
):
    """
    Export logs for customer.

    Returns logs in requested format (JSON or CSV).
    Customer can only export their own tenant's logs (enforced by adapter).

    Supports:
    - JSON format (default)
    - CSV format for spreadsheet import

    Reference: PIN-281 Phase 5 (L3→L2 promotion)
    """
    adapter = get_customer_logs_adapter()

    try:
        export_data = await adapter.export_logs(
            tenant_id=tenant_id,
            format=format,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

        if format == "csv":
            # Return as CSV file
            import io

            output = io.StringIO()
            output.write(",".join(export_data["headers"]) + "\n")
            for row in export_data["rows"]:
                output.write(",".join(f'"{v}"' for v in row) + "\n")

            content = output.getvalue()
            return StreamingResponse(
                iter([content]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=logs_export_{tenant_id}.csv",
                },
            )
        else:
            # Return JSON
            return wrap_dict(export_data)

    except Exception as e:
        logger.error(f"Error exporting logs for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export logs")


# =============================================================================
# Log Detail Endpoint
# =============================================================================


@router.get("/{log_id}", response_model=CustomerLogDetail)
async def get_log(
    log_id: str,
    tenant_id: str = Query(..., description="Tenant ID (required)"),
):
    """
    Get log detail with execution steps.

    Returns detailed view of a single log including all steps.
    Customer can only see their own tenant's logs (enforced by adapter).

    This endpoint:
    - Shows step-by-step execution trace
    - Shows outcome categories and codes
    - Shows duration per step
    - No cost or internal hash data

    Reference: PIN-281 Phase 5 (L3→L2 promotion)
    """
    adapter = get_customer_logs_adapter()

    try:
        log_detail = await adapter.get_log(
            log_id=log_id,
            tenant_id=tenant_id,
        )

        if log_detail is None:
            raise HTTPException(
                status_code=404,
                detail=f"Log {log_id} not found or access denied",
            )

        return wrap_dict(log_detail.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting log {log_id} for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log detail")
