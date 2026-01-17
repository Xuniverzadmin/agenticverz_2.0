# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api (console, SDK)
#   Execution: sync
# Role: Integration management API for customer LLM integrations
# Callers: Customer console, admin tooling, SDK
# Allowed Imports: L4 (cus_integration_service), L6 (schemas)
# Forbidden Imports: L1, L3
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer LLM Integration Management API

PURPOSE:
    CONTROL PLANE for customer LLM integrations. This API manages the lifecycle
    of integrations - create, update, enable, disable, delete, health checks.

ENDPOINTS:
    CRUD:
        GET    /integrations           - List integrations (paginated)
        GET    /integrations/{id}      - Get integration details
        POST   /integrations           - Create new integration
        PUT    /integrations/{id}      - Update integration
        DELETE /integrations/{id}      - Delete integration (soft)

    Lifecycle:
        POST   /integrations/{id}/enable   - Enable integration
        POST   /integrations/{id}/disable  - Disable integration

    Health:
        GET    /integrations/{id}/health   - Get health status
        POST   /integrations/{id}/test     - Test credentials

    Limits:
        GET    /integrations/{id}/limits   - Get current usage vs limits

SEMANTIC:
    - Tenant-isolated: All operations scoped to authenticated tenant
    - Status lifecycle: created -> enabled -> disabled
    - Health checks are non-blocking
    - Soft delete preserves telemetry references

AUTHENTICATION:
    Uses standard tenant authentication via gateway middleware.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.schemas.cus_schemas import (
    CusHealthCheckResponse,
    CusIntegrationCreate,
    CusIntegrationResponse,
    CusIntegrationSummary,
    CusIntegrationUpdate,
    CusLimitsStatus,
)
from app.schemas.response import wrap_dict, wrap_error, wrap_list
from app.services.cus_integration_service import CusIntegrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Customer Integrations"])


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_integration_service() -> CusIntegrationService:
    """Dependency to get integration service instance."""
    return CusIntegrationService()


def get_tenant_id(request: Request) -> str:
    """Extract tenant_id from authenticated request.

    In production, this comes from the auth gateway middleware.
    For now, uses a header or default for development.
    """
    # Try to get from auth context
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context and hasattr(auth_context, "tenant_id"):
        return str(auth_context.tenant_id)

    # Fallback: header for development
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # Final fallback: demo tenant
    return "demo-tenant"


def get_user_id(request: Request) -> Optional[str]:
    """Extract user_id from authenticated request."""
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context and hasattr(auth_context, "user_id"):
        return str(auth_context.user_id)
    return request.headers.get("X-User-ID")


# =============================================================================
# LIST / READ ENDPOINTS
# =============================================================================


@router.get("", summary="List integrations")
async def list_integrations(
    request: Request,
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    provider_type: Optional[str] = Query(default=None, description="Filter by provider"),
    service: CusIntegrationService = Depends(get_integration_service),
):
    """List all integrations for the tenant.

    Returns paginated list of integration summaries.
    """
    tenant_id = get_tenant_id(request)

    try:
        integrations, total = await service.list_integrations(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            status=status,
            provider_type=provider_type,
        )

        summaries = [
            CusIntegrationSummary(
                id=str(i.id),
                name=i.name,
                provider_type=i.provider_type,
                status=i.status,
                health_state=i.health_state,
                default_model=i.default_model,
                created_at=i.created_at,
            )
            for i in integrations
        ]

        return wrap_list(
            [s.model_dump() for s in summaries],
            total=total,
        )

    except Exception as e:
        logger.exception(f"Failed to list integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}", summary="Get integration details")
async def get_integration(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Get full details for a specific integration.

    Includes health state, limits configuration, and timestamps.
    Does NOT include credential_ref or sensitive config.
    """
    tenant_id = get_tenant_id(request)

    try:
        integration = await service.get_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        response = CusIntegrationResponse(
            id=str(integration.id),
            tenant_id=str(integration.tenant_id),
            name=integration.name,
            provider_type=integration.provider_type,
            status=integration.status,
            health_state=integration.health_state,
            health_checked_at=integration.health_checked_at,
            health_message=integration.health_message,
            default_model=integration.default_model,
            budget_limit_cents=integration.budget_limit_cents,
            token_limit_month=integration.token_limit_month,
            rate_limit_rpm=integration.rate_limit_rpm,
            created_at=integration.created_at,
            updated_at=integration.updated_at,
            created_by=str(integration.created_by) if integration.created_by else None,
        )

        return wrap_dict(response.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CREATE / UPDATE / DELETE ENDPOINTS
# =============================================================================


@router.post("", summary="Create integration", status_code=201)
async def create_integration(
    payload: CusIntegrationCreate,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Create a new LLM integration.

    The integration starts in 'created' status. Use /enable to activate it.

    SECURITY:
        - credential_ref must be a vault reference or encrypted value
        - Raw API keys are rejected by schema validation
    """
    tenant_id = get_tenant_id(request)
    user_id = get_user_id(request)

    try:
        integration = await service.create_integration(
            tenant_id=tenant_id,
            name=payload.name,
            provider_type=payload.provider_type.value,
            credential_ref=payload.credential_ref,
            config=payload.config,
            default_model=payload.default_model,
            budget_limit_cents=payload.budget_limit_cents,
            token_limit_month=payload.token_limit_month,
            rate_limit_rpm=payload.rate_limit_rpm,
            created_by=user_id,
        )

        response = CusIntegrationResponse(
            id=str(integration.id),
            tenant_id=str(integration.tenant_id),
            name=integration.name,
            provider_type=integration.provider_type,
            status=integration.status,
            health_state=integration.health_state,
            health_checked_at=integration.health_checked_at,
            health_message=integration.health_message,
            default_model=integration.default_model,
            budget_limit_cents=integration.budget_limit_cents,
            token_limit_month=integration.token_limit_month,
            rate_limit_rpm=integration.rate_limit_rpm,
            created_at=integration.created_at,
            updated_at=integration.updated_at,
            created_by=str(integration.created_by) if integration.created_by else None,
        )

        return wrap_dict(response.model_dump())

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to create integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{integration_id}", summary="Update integration")
async def update_integration(
    integration_id: UUID,
    payload: CusIntegrationUpdate,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Update an existing integration.

    Partial update - only provided fields are changed.
    Status changes should use dedicated enable/disable endpoints.
    """
    tenant_id = get_tenant_id(request)

    try:
        # Build update dict from non-None fields
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        integration = await service.update_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
            **update_data,
        )

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        response = CusIntegrationResponse(
            id=str(integration.id),
            tenant_id=str(integration.tenant_id),
            name=integration.name,
            provider_type=integration.provider_type,
            status=integration.status,
            health_state=integration.health_state,
            health_checked_at=integration.health_checked_at,
            health_message=integration.health_message,
            default_model=integration.default_model,
            budget_limit_cents=integration.budget_limit_cents,
            token_limit_month=integration.token_limit_month,
            rate_limit_rpm=integration.rate_limit_rpm,
            created_at=integration.created_at,
            updated_at=integration.updated_at,
            created_by=str(integration.created_by) if integration.created_by else None,
        )

        return wrap_dict(response.model_dump())

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to update integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{integration_id}", summary="Delete integration")
async def delete_integration(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Delete an integration (soft delete).

    The integration is marked as deleted but retained for telemetry references.
    Telemetry data is NOT deleted.
    """
    tenant_id = get_tenant_id(request)

    try:
        success = await service.delete_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({"deleted": True, "integration_id": str(integration_id)})

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LIFECYCLE ENDPOINTS
# =============================================================================


@router.post("/{integration_id}/enable", summary="Enable integration")
async def enable_integration(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Enable an integration.

    Transitions status from 'created' or 'disabled' to 'enabled'.
    SDK can only use enabled integrations.
    """
    tenant_id = get_tenant_id(request)

    try:
        integration = await service.enable_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": str(integration.id),
            "status": integration.status.value,
            "message": "Integration enabled successfully",
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to enable integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/disable", summary="Disable integration")
async def disable_integration(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Disable an integration.

    Transitions status to 'disabled'. SDK calls will fail for disabled integrations.
    Telemetry continues to be accepted for in-flight calls.
    """
    tenant_id = get_tenant_id(request)

    try:
        integration = await service.disable_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": str(integration.id),
            "status": integration.status.value,
            "message": "Integration disabled successfully",
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to disable integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================


@router.get("/{integration_id}/health", summary="Get health status")
async def get_integration_health(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Get current health status without running a new check.

    Returns cached health state from last check.
    Use POST /test to trigger a fresh health check.
    """
    tenant_id = get_tenant_id(request)

    try:
        integration = await service.get_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": str(integration.id),
            "health_state": integration.health_state.value,
            "health_message": integration.health_message,
            "health_checked_at": (
                integration.health_checked_at.isoformat()
                if integration.health_checked_at
                else None
            ),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/test", summary="Test credentials")
async def test_integration_credentials(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Test integration credentials and update health status.

    Performs a lightweight API call to the provider to verify:
    - Credentials are valid
    - Provider is reachable
    - Rate limits allow access

    This is NON-BLOCKING but may take a few seconds.
    """
    tenant_id = get_tenant_id(request)

    try:
        result = await service.test_credentials(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if result is None:
            raise HTTPException(status_code=404, detail="Integration not found")

        response = CusHealthCheckResponse(
            integration_id=str(integration_id),
            health_state=result["health_state"],
            message=result.get("message"),
            latency_ms=result.get("latency_ms"),
            checked_at=result["checked_at"],
        )

        return wrap_dict(response.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to test credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LIMITS ENDPOINT
# =============================================================================


@router.get("/{integration_id}/limits", summary="Get usage vs limits")
async def get_integration_limits(
    integration_id: UUID,
    request: Request,
    service: CusIntegrationService = Depends(get_integration_service),
):
    """Get current usage against configured limits.

    Returns budget, token, and rate limit status with percentages.
    Used by SDK to check limits before making calls (Phase 5).
    """
    tenant_id = get_tenant_id(request)

    try:
        limits = await service.get_limits_status(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if limits is None:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict(limits.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get limits status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
