# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Customer LLM Integration Management - BYOK (Bring Your Own Key) API
# Callers: Customer Console frontend, SDK
# Allowed Imports: L4 (cus_integration_service), L6 (schemas)
# Forbidden Imports: L1, L3, L5
# Reference: Connectivity Domain - Customer Console v1 Constitution
#
# GOVERNANCE NOTE:
# This is the customer-facing API for managing LLM provider integrations.
# Customers register their own API keys (Anthropic, OpenAI, etc.) and
# AOS manages lifecycle, limits, and health checks.

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

from fastapi import APIRouter, HTTPException, Query, Request

from app.auth.tenant_resolver import resolve_tenant_id
from app.schemas.cus_schemas import (
    CusHealthCheckResponse,
    CusIntegrationCreate,
    CusIntegrationResponse,
    CusIntegrationSummary,
    CusIntegrationUpdate,
)
from app.schemas.response import wrap_dict, wrap_list
from app.hoc.cus.integrations.L5_engines.integrations_facade import get_integrations_facade

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# =============================================================================
# DEPENDENCIES
# =============================================================================


# NOTE: Tenant resolution moved to app.auth.tenant_resolver.resolve_tenant_id
# Services receive UUID, never strings. No guessing, no fallbacks.


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
):
    """List all integrations for the tenant.

    Returns paginated list of integration summaries.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.list_integrations(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            status=status,
            provider_type=provider_type,
        )

        summaries = [
            CusIntegrationSummary(
                id=i.id,
                name=i.name,
                provider_type=i.provider_type,
                status=i.status,
                health_state=i.health_state,
                default_model=i.default_model,
                created_at=i.created_at,
            )
            for i in result.items
        ]

        return wrap_list(
            [s.model_dump() for s in summaries],
            total=result.total,
        )

    except Exception as e:
        logger.exception(f"Failed to list integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}", summary="Get integration details")
async def get_integration(
    integration_id: UUID,
    request: Request,
):
    """Get full details for a specific integration.

    Includes health state, limits configuration, and timestamps.
    Does NOT include credential_ref or sensitive config.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.get_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not result:
            raise HTTPException(status_code=404, detail="Integration not found")

        response = CusIntegrationResponse(
            id=result.id,
            tenant_id=result.tenant_id,
            name=result.name,
            provider_type=result.provider_type,
            status=result.status,
            health_state=result.health_state,
            health_checked_at=result.health_checked_at,
            health_message=result.health_message,
            default_model=result.default_model,
            budget_limit_cents=result.budget_limit_cents,
            token_limit_month=result.token_limit_month,
            rate_limit_rpm=result.rate_limit_rpm,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
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
):
    """Create a new LLM integration.

    The integration starts in 'created' status. Use /enable to activate it.
    Delegates to L4 IntegrationsFacade.

    SECURITY:
        - credential_ref must be a vault reference or encrypted value
        - Raw API keys are rejected by schema validation
    """
    tenant_id = resolve_tenant_id(request)
    user_id = get_user_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.create_integration(
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
            id=result.id,
            tenant_id=result.tenant_id,
            name=result.name,
            provider_type=result.provider_type,
            status=result.status,
            health_state=result.health_state,
            health_checked_at=result.health_checked_at,
            health_message=result.health_message,
            default_model=result.default_model,
            budget_limit_cents=result.budget_limit_cents,
            token_limit_month=result.token_limit_month,
            rate_limit_rpm=result.rate_limit_rpm,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
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
):
    """Update an existing integration.

    Partial update - only provided fields are changed.
    Status changes should use dedicated enable/disable endpoints.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        # Build update dict from non-None fields
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        facade = get_integrations_facade()
        result = await facade.update_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
            **update_data,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Integration not found")

        response = CusIntegrationResponse(
            id=result.id,
            tenant_id=result.tenant_id,
            name=result.name,
            provider_type=result.provider_type,
            status=result.status,
            health_state=result.health_state,
            health_checked_at=result.health_checked_at,
            health_message=result.health_message,
            default_model=result.default_model,
            budget_limit_cents=result.budget_limit_cents,
            token_limit_month=result.token_limit_month,
            rate_limit_rpm=result.rate_limit_rpm,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
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
):
    """Delete an integration (soft delete).

    The integration is marked as deleted but retained for telemetry references.
    Telemetry data is NOT deleted.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.delete_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not result.deleted:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({"deleted": result.deleted, "integration_id": result.integration_id})

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
):
    """Enable an integration.

    Transitions status from 'created' or 'disabled' to 'enabled'.
    SDK can only use enabled integrations.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.enable_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not result:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": result.integration_id,
            "status": result.status,
            "message": result.message,
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
):
    """Disable an integration.

    Transitions status to 'disabled'. SDK calls will fail for disabled integrations.
    Telemetry continues to be accepted for in-flight calls.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.disable_integration(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not result:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": result.integration_id,
            "status": result.status,
            "message": result.message,
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
):
    """Get current health status without running a new check.

    Returns cached health state from last check.
    Use POST /test to trigger a fresh health check.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.get_health_status(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if not result:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": result.integration_id,
            "health_state": result.health_state,
            "health_message": result.health_message,
            "health_checked_at": (
                result.health_checked_at.isoformat()
                if result.health_checked_at
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
):
    """Test integration credentials and update health status.

    Performs a lightweight API call to the provider to verify:
    - Credentials are valid
    - Provider is reachable
    - Rate limits allow access

    This is NON-BLOCKING but may take a few seconds.
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.test_credentials(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if result is None:
            raise HTTPException(status_code=404, detail="Integration not found")

        response = CusHealthCheckResponse(
            integration_id=result.integration_id,
            health_state=result.health_state,
            message=result.message,
            latency_ms=result.latency_ms,
            checked_at=result.checked_at,
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
):
    """Get current usage against configured limits.

    Returns budget, token, and rate limit status with percentages.
    Used by SDK to check limits before making calls (Phase 5).
    Delegates to L4 IntegrationsFacade.
    """
    tenant_id = resolve_tenant_id(request)

    try:
        facade = get_integrations_facade()
        result = await facade.get_limits_status(
            tenant_id=tenant_id,
            integration_id=str(integration_id),
        )

        if result is None:
            raise HTTPException(status_code=404, detail="Integration not found")

        return wrap_dict({
            "integration_id": result.integration_id,
            "budget_limit_cents": result.budget_limit_cents,
            "budget_used_cents": result.budget_used_cents,
            "budget_percent": result.budget_percent,
            "token_limit_month": result.token_limit_month,
            "tokens_used_month": result.tokens_used_month,
            "token_percent": result.token_percent,
            "rate_limit_rpm": result.rate_limit_rpm,
            "requests_this_minute": result.requests_this_minute,
            "rate_percent": result.rate_percent,
            "period_start": result.period_start.isoformat(),
            "period_end": result.period_end.isoformat(),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get limits status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
