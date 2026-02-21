# capability_id: CAP-009
# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Policy limits mutating operations (PIN-LIM-01)
# Callers: Customer Console frontend, Admin tools
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-LIM-01

"""
Policy Limits CRUD API (PIN-LIM-01)

Mutating endpoints for policy limits.

Extends the read-only policies.py facade with write operations.

Endpoints:
    POST   /policies/limits              → Create limit
    PUT    /policies/limits/{limit_id}   → Update limit
    DELETE /policies/limits/{limit_id}   → Soft-delete limit
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app.auth.gateway_middleware import get_auth_context
from app.schemas.limits.policy_limits import (
    CreatePolicyLimitRequest,
    LimitCategoryEnum,
    LimitEnforcementEnum,
    LimitScopeEnum,
    PolicyLimitResponse,
    ResetPeriodEnum,
    UpdatePolicyLimitRequest,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


router = APIRouter(prefix="/policies", tags=["policies"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateLimitRequest(BaseModel):
    """API request to create a policy limit."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    limit_category: str = Field(..., description="BUDGET, RATE, or THRESHOLD")
    limit_type: str = Field(..., description="Type within category")
    scope: str = Field(default="TENANT", description="TENANT, PROJECT, AGENT, USER, or GLOBAL")
    scope_id: Optional[str] = Field(default=None, description="Scope target ID")
    max_value: Decimal = Field(..., gt=0)
    enforcement: str = Field(default="HARD", description="HARD, SOFT, or ADVISORY")
    reset_period: Optional[str] = Field(default=None, description="DAILY, WEEKLY, MONTHLY, YEARLY")
    window_seconds: Optional[int] = Field(default=None, ge=1, description="Window for RATE limits")


class UpdateLimitRequest(BaseModel):
    """API request to update a policy limit."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    max_value: Optional[Decimal] = Field(default=None, gt=0)
    enforcement: Optional[str] = Field(default=None)
    reset_period: Optional[str] = Field(default=None)
    window_seconds: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, description="ACTIVE or DISABLED")


class ThresholdParamsRequest(BaseModel):
    """
    API request to set execution threshold parameters.

    Used for: Policies → Limits → Thresholds → Set Params panel.

    These params drive LLM run governance:
    - Activity → LLM Runs → Live → Signals
    - Activity → LLM Runs → Completed → Signals
    """

    max_execution_time_ms: Optional[int] = Field(
        default=None,
        ge=1000,
        le=300_000,
        description="Maximum execution time in milliseconds (1s-5min)",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=256,
        le=200_000,
        description="Maximum tokens allowed (256-200k)",
    )
    max_cost_usd: Optional[float] = Field(
        default=None,
        ge=0.01,
        le=100.0,
        description="Maximum cost in USD (0.01-100)",
    )
    failure_signal: Optional[bool] = Field(
        default=None,
        description="Emit signal on run failure",
    )

    model_config = {"extra": "forbid"}


class ThresholdParamsResponse(BaseModel):
    """Response with effective threshold params."""

    limit_id: str
    tenant_id: str
    params: dict = Field(description="Threshold parameters")
    effective_params: dict = Field(description="Resolved params with defaults applied")
    updated_at: datetime


class LimitDetail(BaseModel):
    """Full limit response."""

    limit_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    limit_category: str
    limit_type: str
    scope: str
    scope_id: Optional[str]
    max_value: Decimal
    enforcement: str
    status: str
    reset_period: Optional[str]
    window_seconds: Optional[int]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/limits",
    response_model=LimitDetail,
    status_code=201,
    summary="Create a policy limit",
    description="Create a new policy limit for the tenant.",
)
async def create_limit(
    request: Request,
    body: CreateLimitRequest,
    session = Depends(get_session_dep),
) -> LimitDetail:
    """
    Create a new policy limit.

    - Category and type are immutable after creation
    - BUDGET limits require reset_period
    - RATE limits require window_seconds
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.limits",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "create",
                "name": body.name,
                "description": body.description,
                "limit_category": body.limit_category,
                "limit_type": body.limit_type,
                "scope": body.scope,
                "scope_id": body.scope_id,
                "max_value": str(body.max_value),
                "enforcement": body.enforcement,
                "reset_period": body.reset_period,
                "window_seconds": body.window_seconds,
                "created_by": user_id,
            },
        ),
    )

    if not op.success:
        error_code = getattr(op, "error_code", None) or ""
        if error_code == "VALIDATION_ERROR":
            raise HTTPException(
                status_code=400,
                detail={"error": "validation_error", "message": op.error},
            )
        elif error_code == "SERVICE_ERROR":
            raise HTTPException(
                status_code=400,
                detail={"error": "create_error", "message": op.error},
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "create_error", "message": op.error},
            )

    return _to_detail(op.data)


@router.put(
    "/limits/{limit_id}",
    response_model=LimitDetail,
    summary="Update a policy limit",
    description="Update mutable fields of a policy limit.",
)
async def update_limit(
    request: Request,
    limit_id: str,
    body: UpdateLimitRequest,
    session = Depends(get_session_dep),
) -> LimitDetail:
    """
    Update an existing policy limit.

    - Category and type are immutable (cannot be changed)
    - Other fields can be updated
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.limits",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "update",
                "limit_id": limit_id,
                "name": body.name,
                "description": body.description,
                "max_value": str(body.max_value) if body.max_value is not None else None,
                "enforcement": body.enforcement,
                "reset_period": body.reset_period,
                "window_seconds": body.window_seconds,
                "status": body.status,
                "updated_by": user_id,
            },
        ),
    )

    if not op.success:
        error_code = getattr(op, "error_code", None) or ""
        if error_code == "LIMIT_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "limit_not_found", "message": op.error},
            )
        elif error_code == "IMMUTABLE_FIELD":
            raise HTTPException(
                status_code=400,
                detail={"error": "immutable_field", "message": op.error},
            )
        elif error_code == "VALIDATION_ERROR":
            raise HTTPException(
                status_code=400,
                detail={"error": "validation_error", "message": op.error},
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "update_error", "message": op.error},
            )

    return _to_detail(op.data)


@router.delete(
    "/limits/{limit_id}",
    status_code=204,
    summary="Delete a policy limit",
    description="Soft-delete a policy limit (sets status to DISABLED).",
)
async def delete_limit(
    request: Request,
    limit_id: str,
    session = Depends(get_session_dep),
) -> None:
    """
    Soft-delete a policy limit.

    Sets status to DISABLED. The limit is not actually removed.
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.limits",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "delete",
                "limit_id": limit_id,
                "deleted_by": user_id,
            },
        ),
    )

    if not op.success:
        error_code = getattr(op, "error_code", None) or ""
        if error_code == "LIMIT_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "limit_not_found", "message": op.error},
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "delete_error", "message": op.error},
            )


# =============================================================================
# Threshold Params Endpoints
# =============================================================================


@router.get(
    "/limits/{limit_id}/params",
    response_model=ThresholdParamsResponse,
    summary="Get threshold params",
    description="Get threshold parameters for a THRESHOLD category limit.",
)
async def get_threshold_params(
    request: Request,
    limit_id: str,
    session = Depends(get_session_dep),
) -> ThresholdParamsResponse:
    """
    Get threshold parameters for a limit.

    Returns both raw params and effective params (with defaults applied).
    Only valid for limits with limit_category = THRESHOLD.
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id

    # Fetch the limit and compute effective params via L4 operation registry
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.thresholds",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_threshold_params",
                "limit_id": limit_id,
            },
        ),
    )
    if not op.success:
        error_code = getattr(op, "error_code", None) or ""
        if error_code == "LIMIT_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "limit_not_found", "message": f"Limit {limit_id} not found"},
            )
        elif error_code == "INVALID_CATEGORY":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_limit_category",
                    "message": f"Limit {limit_id} is not a THRESHOLD category limit",
                },
            )
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data

    return ThresholdParamsResponse(
        limit_id=result["limit_id"],
        tenant_id=result["tenant_id"],
        params=result["params"],
        effective_params=result["effective_params"],
        updated_at=result["updated_at"],
    )


@router.put(
    "/limits/{limit_id}/params",
    response_model=ThresholdParamsResponse,
    summary="Set threshold params",
    description="Set threshold parameters for a THRESHOLD category limit.",
)
async def set_threshold_params(
    request: Request,
    limit_id: str,
    body: ThresholdParamsRequest,
    session = Depends(get_session_dep),
) -> ThresholdParamsResponse:
    """
    Set threshold parameters for a limit.

    This is the authoritative input surface for:
    - Policies → Limits → Thresholds → Set Params panel

    These params drive LLM run governance signals.

    Validation Rules (Hard Stop):
    - max_execution_time_ms: 1000-300000 (1s to 5min)
    - max_tokens: 256-200000
    - max_cost_usd: 0.01-100.00
    - failure_signal: boolean

    No partial garbage. No unknown keys. No absurd values.
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id

    update_data = body.model_dump(exclude_none=True)

    # Validate, update, and compute effective params via L4 operation registry
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.thresholds",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "set_threshold_params",
                "limit_id": limit_id,
                "update_data": update_data,
            },
        ),
    )
    if not op.success:
        error_code = getattr(op, "error_code", None) or ""
        if error_code == "LIMIT_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "limit_not_found", "message": f"Limit {limit_id} not found"},
            )
        elif error_code == "INVALID_CATEGORY":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_limit_category",
                    "message": f"Limit {limit_id} is not a THRESHOLD category limit",
                },
            )
        elif error_code == "INVALID_PARAMS":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_params",
                    "message": op.error,
                },
            )
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data

    return ThresholdParamsResponse(
        limit_id=result["limit_id"],
        tenant_id=result["tenant_id"],
        params=result["params"],
        effective_params=result["effective_params"],
        updated_at=result["updated_at"],
    )


# =============================================================================
# Helpers
# =============================================================================


def _to_detail(result: PolicyLimitResponse) -> LimitDetail:
    """Convert service response to API response."""
    return LimitDetail(
        limit_id=result.limit_id,
        tenant_id=result.tenant_id,
        name=result.name,
        description=result.description,
        limit_category=result.limit_category,
        limit_type=result.limit_type,
        scope=result.scope,
        scope_id=result.scope_id,
        max_value=result.max_value,
        enforcement=result.enforcement,
        status=result.status,
        reset_period=result.reset_period,
        window_seconds=result.window_seconds,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
