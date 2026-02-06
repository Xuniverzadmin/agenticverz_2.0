# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Limit override endpoint (PIN-LIM-05)
# Callers: Customer Console, Ops Console
# Allowed Imports: L4, L5_schemas
# Forbidden Imports: L1, L5_engines, L6
# Reference: PIN-LIM-05

"""
Limit Override API (PIN-LIM-05)

Temporary limit override request endpoints.

Allows authorized users to request temporary increases to limits,
with approval workflow and automatic expiry.

Endpoints:
    POST /api/v1/limits/overrides         → Request new override
    GET  /api/v1/limits/overrides         → List overrides for tenant
    GET  /api/v1/limits/overrides/{id}    → Get specific override
    DELETE /api/v1/limits/overrides/{id}  → Cancel override
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.auth.gateway_middleware import get_auth_context
from app.schemas.limits.overrides import (
    LimitOverrideRequest,
    LimitOverrideResponse,
    OverrideStatus,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


router = APIRouter(prefix="/limits", tags=["limits"])


# =============================================================================
# Request/Response Wrappers
# =============================================================================


class CreateOverrideRequest(BaseModel):
    """Request to create a limit override."""

    limit_id: str = Field(..., description="ID of the limit to override")
    override_value: Decimal = Field(..., gt=0, description="New limit value")
    duration_hours: int = Field(..., ge=1, le=168, description="Duration in hours (max 1 week)")
    reason: str = Field(..., min_length=10, max_length=500, description="Justification for override")
    start_immediately: bool = Field(default=True, description="Start immediately or schedule")
    scheduled_start: Optional[datetime] = Field(default=None, description="Scheduled start time")


class OverrideListItem(BaseModel):
    """Override summary for list view."""

    override_id: str
    limit_id: str
    limit_name: str
    original_value: Decimal
    override_value: Decimal
    status: str
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    requested_at: datetime
    requested_by: str


class OverrideDetail(BaseModel):
    """Full override details."""

    override_id: str
    limit_id: str
    limit_name: str
    tenant_id: str
    original_value: Decimal
    override_value: Decimal
    effective_value: Decimal
    status: str
    requested_at: datetime
    approved_at: Optional[datetime]
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    requested_by: str
    approved_by: Optional[str]
    reason: str
    rejection_reason: Optional[str]


class OverrideListResponse(BaseModel):
    """Response for override list."""

    items: list[OverrideListItem]
    total: int
    limit: int
    offset: int


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/overrides",
    response_model=OverrideDetail,
    status_code=201,
    summary="Request a limit override",
    description="Request a temporary increase to a limit. Requires justification.",
)
async def create_override(
    request: Request,
    body: CreateOverrideRequest,
    session = Depends(get_session_dep),
) -> OverrideDetail:
    """
    Request a temporary limit override.

    - Requires justification (reason)
    - Maximum 5 active overrides per tenant
    - Maximum duration: 168 hours (1 week)
    - Cannot stack multiple overrides on same limit
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None) or "unknown"

    override_request = LimitOverrideRequest(
        limit_id=body.limit_id,
        override_value=body.override_value,
        duration_hours=body.duration_hours,
        reason=body.reason,
        start_immediately=body.start_immediately,
        scheduled_start=body.scheduled_start,
    )

    # Route through L4 handler (PIN-504: L2 must not import L6 directly)
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.overrides",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "request_override",
                "tenant_id": tenant_id,
                "request": override_request,
                "requested_by": user_id,
            },
        ),
    )

    if not op.success:
        error_map = {
            "LIMIT_NOT_FOUND": (404, "limit_not_found"),
            "STACKING_ABUSE": (429, "too_many_overrides"),
            "VALIDATION_ERROR": (400, "validation_error"),
            "SERVICE_ERROR": (400, "override_error"),
        }
        status_code, error_key = error_map.get(op.error_code, (400, "override_error"))
        raise HTTPException(
            status_code=status_code,
            detail={"error": error_key, "message": op.error},
        )

    return _to_detail(op.data)


@router.get(
    "/overrides",
    response_model=OverrideListResponse,
    summary="List limit overrides",
    description="List all limit overrides for the current tenant.",
)
async def list_overrides(
    request: Request,
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session = Depends(get_session_dep),
) -> OverrideListResponse:
    """List overrides for the tenant."""
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id

    registry = get_operation_registry()
    op = await registry.execute(
        "controls.overrides",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "list_overrides",
                "tenant_id": tenant_id,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        ),
    )

    if not op.success:
        raise HTTPException(
            status_code=400,
            detail={"error": "list_error", "message": op.error},
        )

    items, total = op.data
    return OverrideListResponse(
        items=[_to_list_item(o) for o in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/overrides/{override_id}",
    response_model=OverrideDetail,
    summary="Get override details",
    description="Get full details of a specific limit override.",
)
async def get_override(
    request: Request,
    override_id: str,
    session = Depends(get_session_dep),
) -> OverrideDetail:
    """Get override by ID."""
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id

    registry = get_operation_registry()
    op = await registry.execute(
        "controls.overrides",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_override",
                "tenant_id": tenant_id,
                "override_id": override_id,
            },
        ),
    )

    if not op.success:
        if op.error_code == "OVERRIDE_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "override_not_found", "message": op.error},
            )
        raise HTTPException(status_code=400, detail={"error": "service_error", "message": op.error})

    return _to_detail(op.data)


@router.delete(
    "/overrides/{override_id}",
    response_model=OverrideDetail,
    summary="Cancel an override",
    description="Cancel a pending or active limit override.",
)
async def cancel_override(
    request: Request,
    override_id: str,
    session = Depends(get_session_dep),
) -> OverrideDetail:
    """Cancel a pending or active override."""
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None) or "unknown"

    registry = get_operation_registry()
    op = await registry.execute(
        "controls.overrides",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "cancel_override",
                "tenant_id": tenant_id,
                "override_id": override_id,
                "cancelled_by": user_id,
            },
        ),
    )

    if not op.success:
        error_map = {
            "OVERRIDE_NOT_FOUND": (404, "override_not_found"),
            "VALIDATION_ERROR": (400, "cannot_cancel"),
        }
        status_code, error_key = error_map.get(op.error_code, (400, "service_error"))
        raise HTTPException(
            status_code=status_code,
            detail={"error": error_key, "message": op.error},
        )

    return _to_detail(op.data)


# =============================================================================
# Helpers
# =============================================================================


def _to_detail(result: LimitOverrideResponse) -> OverrideDetail:
    """Convert service response to API response."""
    return OverrideDetail(
        override_id=result.override_id,
        limit_id=result.limit_id,
        limit_name=result.limit_name,
        tenant_id=result.tenant_id,
        original_value=result.original_value,
        override_value=result.override_value,
        effective_value=result.effective_value,
        status=result.status.value,
        requested_at=result.requested_at,
        approved_at=result.approved_at,
        starts_at=result.starts_at,
        expires_at=result.expires_at,
        requested_by=result.requested_by,
        approved_by=result.approved_by,
        reason=result.reason,
        rejection_reason=result.rejection_reason,
    )


def _to_list_item(result: LimitOverrideResponse) -> OverrideListItem:
    """Convert service response to list item."""
    return OverrideListItem(
        override_id=result.override_id,
        limit_id=result.limit_id,
        limit_name=result.limit_name,
        original_value=result.original_value,
        override_value=result.override_value,
        status=result.status.value,
        starts_at=result.starts_at,
        expires_at=result.expires_at,
        requested_at=result.requested_at,
        requested_by=result.requested_by,
    )
