# Layer: L5 — Driver
# AUDIENCE: CUSTOMER
# Role: Integrations domain facade - unified entry point for integration management
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB operations)
# Callers: L2 integrations API (aos_cus_integrations.py)
# Allowed Imports: L4 (CusIntegrationService), L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Connectivity Domain - Customer Console v1 Constitution
#

"""
Integrations Domain Facade (L4)

Unified facade for LLM integration management (BYOK - Bring Your Own Key).

Provides:
- CRUD: list, get, create, update, delete integrations
- Lifecycle: enable, disable
- Health: get health status, test credentials
- Limits: get usage vs limits

This facade wraps the CusIntegrationService and provides dataclass result types
for consistency with other domain facades.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

# PIN-468: Import from engine (provides CusIntegrationService alias for compatibility)
from app.services.cus_integration_engine import CusIntegrationService


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class IntegrationSummaryResult:
    """Integration summary for list view."""

    id: str
    name: str
    provider_type: str
    status: str
    health_state: str
    default_model: Optional[str]
    created_at: datetime


@dataclass
class IntegrationListResult:
    """Integration list response."""

    items: list[IntegrationSummaryResult]
    total: int


@dataclass
class IntegrationDetailResult:
    """Integration detail response."""

    id: str
    tenant_id: str
    name: str
    provider_type: str
    status: str
    health_state: str
    health_checked_at: Optional[datetime]
    health_message: Optional[str]
    default_model: Optional[str]
    budget_limit_cents: int
    token_limit_month: int
    rate_limit_rpm: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]


@dataclass
class IntegrationLifecycleResult:
    """Result of enable/disable operation."""

    integration_id: str
    status: str
    message: str


@dataclass
class IntegrationDeleteResult:
    """Result of delete operation."""

    deleted: bool
    integration_id: str


@dataclass
class HealthCheckResult:
    """Health check result."""

    integration_id: str
    health_state: str
    message: Optional[str]
    latency_ms: Optional[int]
    checked_at: datetime


@dataclass
class HealthStatusResult:
    """Cached health status."""

    integration_id: str
    health_state: str
    health_message: Optional[str]
    health_checked_at: Optional[datetime]


@dataclass
class LimitsStatusResult:
    """Usage vs limits status."""

    integration_id: str
    budget_limit_cents: int
    budget_used_cents: int
    budget_percent: float
    token_limit_month: int
    tokens_used_month: int
    token_percent: float
    rate_limit_rpm: int
    requests_this_minute: int
    rate_percent: float
    period_start: datetime
    period_end: datetime


# =============================================================================
# Integrations Facade
# =============================================================================


class IntegrationsFacade:
    """
    Unified facade for LLM integration management.

    Provides:
    - CRUD: list, get, create, update, delete integrations
    - Lifecycle: enable, disable
    - Health: get health status, test credentials
    - Limits: get usage vs limits

    All operations are tenant-scoped for isolation.
    """

    def __init__(self) -> None:
        """Initialize with CusIntegrationService."""
        self._service = CusIntegrationService()

    # -------------------------------------------------------------------------
    # List / Read Operations
    # -------------------------------------------------------------------------

    async def list_integrations(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        provider_type: Optional[str] = None,
    ) -> IntegrationListResult:
        """List all integrations for the tenant."""
        integrations, total = await self._service.list_integrations(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            status=status,
            provider_type=provider_type,
        )

        items = [
            IntegrationSummaryResult(
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

        return IntegrationListResult(items=items, total=total)

    async def get_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[IntegrationDetailResult]:
        """Get full details for a specific integration."""
        integration = await self._service.get_integration(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if not integration:
            return None

        return IntegrationDetailResult(
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

    # -------------------------------------------------------------------------
    # Create / Update / Delete Operations
    # -------------------------------------------------------------------------

    async def create_integration(
        self,
        tenant_id: UUID,
        *,
        name: str,
        provider_type: str,
        credential_ref: str,
        config: Optional[dict[str, Any]] = None,
        default_model: Optional[str] = None,
        budget_limit_cents: int = 0,
        token_limit_month: int = 0,
        rate_limit_rpm: int = 0,
        created_by: Optional[str] = None,
    ) -> IntegrationDetailResult:
        """Create a new LLM integration."""
        integration = await self._service.create_integration(
            tenant_id=tenant_id,
            name=name,
            provider_type=provider_type,
            credential_ref=credential_ref,
            config=config,
            default_model=default_model,
            budget_limit_cents=budget_limit_cents,
            token_limit_month=token_limit_month,
            rate_limit_rpm=rate_limit_rpm,
            created_by=created_by,
        )

        return IntegrationDetailResult(
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

    async def update_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
        **update_data: Any,
    ) -> Optional[IntegrationDetailResult]:
        """Update an existing integration."""
        integration = await self._service.update_integration(
            tenant_id=tenant_id,
            integration_id=integration_id,
            **update_data,
        )

        if not integration:
            return None

        return IntegrationDetailResult(
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

    async def delete_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> IntegrationDeleteResult:
        """Delete an integration (soft delete)."""
        success = await self._service.delete_integration(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        return IntegrationDeleteResult(
            deleted=success,
            integration_id=integration_id,
        )

    # -------------------------------------------------------------------------
    # Lifecycle Operations
    # -------------------------------------------------------------------------

    async def enable_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[IntegrationLifecycleResult]:
        """Enable an integration."""
        integration = await self._service.enable_integration(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if not integration:
            return None

        return IntegrationLifecycleResult(
            integration_id=str(integration.id),
            status=integration.status,
            message="Integration enabled successfully",
        )

    async def disable_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[IntegrationLifecycleResult]:
        """Disable an integration."""
        integration = await self._service.disable_integration(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if not integration:
            return None

        return IntegrationLifecycleResult(
            integration_id=str(integration.id),
            status=integration.status,
            message="Integration disabled successfully",
        )

    # -------------------------------------------------------------------------
    # Health Operations
    # -------------------------------------------------------------------------

    async def get_health_status(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[HealthStatusResult]:
        """Get cached health status without running a new check."""
        integration = await self._service.get_integration(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if not integration:
            return None

        return HealthStatusResult(
            integration_id=str(integration.id),
            health_state=integration.health_state,
            health_message=integration.health_message,
            health_checked_at=integration.health_checked_at,
        )

    async def test_credentials(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[HealthCheckResult]:
        """Test credentials and update health status."""
        result = await self._service.test_credentials(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if result is None:
            return None

        return HealthCheckResult(
            integration_id=integration_id,
            health_state=result["health_state"],
            message=result.get("message"),
            latency_ms=result.get("latency_ms"),
            checked_at=result["checked_at"],
        )

    # -------------------------------------------------------------------------
    # Limits Operations
    # -------------------------------------------------------------------------

    async def get_limits_status(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[LimitsStatusResult]:
        """Get current usage against configured limits."""
        limits = await self._service.get_limits_status(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if limits is None:
            return None

        return LimitsStatusResult(
            integration_id=limits.integration_id,
            budget_limit_cents=limits.budget_limit_cents,
            budget_used_cents=limits.budget_used_cents,
            budget_percent=limits.budget_percent,
            token_limit_month=limits.token_limit_month,
            tokens_used_month=limits.tokens_used_month,
            token_percent=limits.token_percent,
            rate_limit_rpm=limits.rate_limit_rpm,
            requests_this_minute=limits.requests_this_minute,
            rate_percent=limits.rate_percent,
            period_start=limits.period_start,
            period_end=limits.period_end,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_facade_instance: IntegrationsFacade | None = None


def get_integrations_facade() -> IntegrationsFacade:
    """Get the singleton IntegrationsFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = IntegrationsFacade()
    return _facade_instance


__all__ = [
    # Facade
    "IntegrationsFacade",
    "get_integrations_facade",
    # Result types
    "IntegrationSummaryResult",
    "IntegrationListResult",
    "IntegrationDetailResult",
    "IntegrationLifecycleResult",
    "IntegrationDeleteResult",
    "HealthCheckResult",
    "HealthStatusResult",
    "LimitsStatusResult",
]
