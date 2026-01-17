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
    POST   /api/v1/policies/limits              → Create limit
    PUT    /api/v1/policies/limits/{limit_id}   → Update limit
    DELETE /api/v1/policies/limits/{limit_id}   → Soft-delete limit
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.schemas.limits.policy_limits import (
    CreatePolicyLimitRequest,
    LimitCategoryEnum,
    LimitEnforcementEnum,
    LimitScopeEnum,
    PolicyLimitResponse,
    ResetPeriodEnum,
    UpdatePolicyLimitRequest,
)
from app.services.limits.policy_limits_service import (
    ImmutableFieldError,
    LimitNotFoundError,
    LimitValidationError,
    PolicyLimitsService,
    PolicyLimitsServiceError,
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
    session: AsyncSession = Depends(get_async_session_dep),
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

    service = PolicyLimitsService(session)

    try:
        # Parse enums
        category = LimitCategoryEnum(body.limit_category)
        scope = LimitScopeEnum(body.scope)
        enforcement = LimitEnforcementEnum(body.enforcement)
        reset_period = ResetPeriodEnum(body.reset_period) if body.reset_period else None

        create_request = CreatePolicyLimitRequest(
            name=body.name,
            description=body.description,
            limit_category=category,
            limit_type=body.limit_type,
            scope=scope,
            scope_id=body.scope_id,
            max_value=body.max_value,
            enforcement=enforcement,
            reset_period=reset_period,
            window_seconds=body.window_seconds,
        )

        result = await service.create(
            tenant_id=tenant_id,
            request=create_request,
            created_by=user_id,
        )

        return _to_detail(result)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_enum", "message": str(e)},
        )
    except LimitValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": str(e)},
        )
    except PolicyLimitsServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "create_error", "message": str(e)},
        )


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
    session: AsyncSession = Depends(get_async_session_dep),
) -> LimitDetail:
    """
    Update an existing policy limit.

    - Category and type are immutable (cannot be changed)
    - Other fields can be updated
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    service = PolicyLimitsService(session)

    try:
        # Parse enums if provided
        enforcement = LimitEnforcementEnum(body.enforcement) if body.enforcement else None
        reset_period = ResetPeriodEnum(body.reset_period) if body.reset_period else None

        update_request = UpdatePolicyLimitRequest(
            name=body.name,
            description=body.description,
            max_value=body.max_value,
            enforcement=enforcement,
            reset_period=reset_period,
            window_seconds=body.window_seconds,
            status=body.status,
        )

        result = await service.update(
            tenant_id=tenant_id,
            limit_id=limit_id,
            request=update_request,
            updated_by=user_id,
        )

        return _to_detail(result)

    except LimitNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "limit_not_found", "message": str(e)},
        )
    except ImmutableFieldError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "immutable_field", "message": str(e)},
        )
    except LimitValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": str(e)},
        )
    except PolicyLimitsServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "update_error", "message": str(e)},
        )


@router.delete(
    "/limits/{limit_id}",
    status_code=204,
    summary="Delete a policy limit",
    description="Soft-delete a policy limit (sets status to DISABLED).",
)
async def delete_limit(
    request: Request,
    limit_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> None:
    """
    Soft-delete a policy limit.

    Sets status to DISABLED. The limit is not actually removed.
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    service = PolicyLimitsService(session)

    try:
        await service.delete(
            tenant_id=tenant_id,
            limit_id=limit_id,
            deleted_by=user_id,
        )

    except LimitNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "limit_not_found", "message": str(e)},
        )
    except PolicyLimitsServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "delete_error", "message": str(e)},
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
