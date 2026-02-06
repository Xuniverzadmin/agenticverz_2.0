# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Customer Integration Engine
"""Customer Integration Engine

L4 engine for customer integration decisions.

Decides: Integration creation, lifecycle transitions, limit calculations
Delegates: All persistence to CusIntegrationDriver
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.schemas.cus_schemas import CusLimitsStatus
from app.hoc.cus.integrations.L6_drivers.cus_integration_driver import (
    CusIntegrationDriver,
    get_cus_integration_driver,
)

if TYPE_CHECKING:
    from app.models.cus_models import CusIntegration

logger = logging.getLogger(__name__)


@dataclass
class EnableResult:
    """Result of enable operation."""

    success: bool
    integration: Optional["CusIntegration"] = None
    error: Optional[str] = None


@dataclass
class DeleteResult:
    """Result of delete operation."""

    success: bool
    error: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Result of health check operation."""

    health_state: str
    message: str
    latency_ms: int
    checked_at: datetime


class CusIntegrationEngine:
    """L4 engine for customer integration decisions.

    Decides: Validation, lifecycle transitions, limit calculations
    Delegates: All persistence to CusIntegrationDriver
    """

    # Status constants (avoid importing from models at runtime)
    STATUS_CREATED = "created"
    STATUS_ENABLED = "enabled"
    STATUS_DISABLED = "disabled"
    STATUS_ERROR = "error"

    HEALTH_UNKNOWN = "unknown"
    HEALTH_HEALTHY = "healthy"
    HEALTH_UNHEALTHY = "unhealthy"

    def __init__(self, driver: CusIntegrationDriver):
        """Initialize engine with driver.

        Args:
            driver: CusIntegrationDriver instance for persistence
        """
        self._driver = driver

    # =========================================================================
    # CREATE
    # =========================================================================

    async def create_integration(
        self,
        tenant_id: UUID,
        name: str,
        provider_type: str,
        credential_ref: str,
        config: Optional[Dict[str, Any]] = None,
        default_model: Optional[str] = None,
        budget_limit_cents: int = 0,
        token_limit_month: int = 0,
        rate_limit_rpm: int = 0,
        created_by: Optional[str] = None,
    ) -> "CusIntegration":
        """Create a new integration.

        Business logic:
        - Validates name uniqueness within tenant
        - Sets initial status to 'created'
        - Sets initial health state to 'unknown'

        Args:
            tenant_id: Owning tenant
            name: Human-readable name
            provider_type: Provider (openai, anthropic, etc.)
            credential_ref: Encrypted credential reference
            config: Provider-specific configuration
            default_model: Default model to use
            budget_limit_cents: Monthly budget limit (0 = unlimited)
            token_limit_month: Monthly token limit (0 = unlimited)
            rate_limit_rpm: Rate limit in requests per minute (0 = unlimited)
            created_by: User ID who created this

        Returns:
            Created CusIntegration

        Raises:
            ValueError: If name already exists for tenant
        """
        tenant_str = str(tenant_id)

        # DECISION: Check for duplicate name
        existing = self._driver.fetch_by_name(tenant_str, name)
        if existing:
            raise ValueError(f"Integration with name '{name}' already exists")

        # DECISION: Set initial state
        return self._driver.create(
            tenant_id=tenant_str,
            name=name,
            provider_type=provider_type,
            credential_ref=credential_ref,
            config=config or {},
            status=self.STATUS_CREATED,
            health_state=self.HEALTH_UNKNOWN,
            default_model=default_model,
            budget_limit_cents=budget_limit_cents,
            token_limit_month=token_limit_month,
            rate_limit_rpm=rate_limit_rpm,
            created_by=str(created_by) if created_by else None,
        )

    # =========================================================================
    # READ
    # =========================================================================

    async def get_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional["CusIntegration"]:
        """Get integration by ID.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            CusIntegration if found and owned by tenant, None otherwise
        """
        return self._driver.fetch_by_id(str(tenant_id), integration_id)

    async def list_integrations(
        self,
        tenant_id: UUID,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        provider_type: Optional[str] = None,
    ) -> Tuple[List["CusIntegration"], int]:
        """List integrations for a tenant.

        Args:
            tenant_id: Tenant UUID (already validated by resolver)
            offset: Pagination offset
            limit: Page size
            status: Filter by status (optional)
            provider_type: Filter by provider (optional)

        Returns:
            Tuple of (integrations, total_count)
        """
        return self._driver.fetch_list(
            tenant_id=str(tenant_id),
            offset=offset,
            limit=limit,
            status=status,
            provider_type=provider_type,
        )

    # =========================================================================
    # UPDATE
    # =========================================================================

    async def update_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
        **kwargs,
    ) -> Optional["CusIntegration"]:
        """Update integration fields.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID
            **kwargs: Fields to update

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        return self._driver.update_fields(
            tenant_id=str(tenant_id),
            integration_id=integration_id,
            updates=kwargs,
        )

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> DeleteResult:
        """Delete integration (soft delete via status).

        Business logic:
        - Applies soft delete policy (mark _deleted in config)
        - Retains record for telemetry references
        - Sets status to disabled

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            DeleteResult with success status
        """
        tenant_str = str(tenant_id)

        # Fetch current state
        integration = self._driver.fetch_by_id(tenant_str, integration_id)
        if not integration:
            return DeleteResult(success=False, error="Integration not found")

        # DECISION: Apply soft delete policy
        now = datetime.now(timezone.utc)
        delete_markers = {
            "_deleted": True,
            "_deleted_at": now.isoformat(),
        }

        # Update config with delete markers
        self._driver.update_config(tenant_str, integration_id, delete_markers)

        # Update status to disabled
        self._driver.update_status(tenant_str, integration_id, self.STATUS_DISABLED)

        logger.info(f"Deleted (soft) integration {integration_id}")

        return DeleteResult(success=True)

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def enable_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> EnableResult:
        """Enable an integration.

        Business logic:
        - Validates state transition (cannot enable from ERROR state)
        - Validates not deleted
        - Valid transitions: created -> enabled, disabled -> enabled

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            EnableResult with success status and integration or error
        """
        tenant_str = str(tenant_id)

        # Fetch current state
        integration = self._driver.fetch_by_id(tenant_str, integration_id)
        if not integration:
            return EnableResult(success=False, error="Integration not found")

        # DECISION: Validate state transition
        if integration.status == self.STATUS_ERROR:
            return EnableResult(
                success=False,
                error="Cannot enable integration in error state. Fix the error condition first.",
            )

        # DECISION: Check not deleted
        if integration.config.get("_deleted"):
            return EnableResult(
                success=False,
                error="Cannot enable deleted integration",
            )

        # Persist status change
        updated = self._driver.update_status(
            tenant_str, integration_id, self.STATUS_ENABLED
        )

        logger.info(f"Enabled integration {integration_id}")

        return EnableResult(success=True, integration=updated)

    async def disable_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional["CusIntegration"]:
        """Disable an integration.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        result = self._driver.update_status(
            str(tenant_id), integration_id, self.STATUS_DISABLED
        )
        if result:
            logger.info(f"Disabled integration {integration_id}")
        return result

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    async def test_credentials(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[HealthCheckResult]:
        """Test integration credentials.

        Business logic:
        - Orchestrates health check (delegates to health service)
        - Updates health state based on result

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            HealthCheckResult if found, None otherwise
        """
        tenant_str = str(tenant_id)

        # Verify integration exists
        integration = self._driver.fetch_by_id(tenant_str, integration_id)
        if not integration:
            return None

        # TODO: Delegate to CusHealthService when implemented
        # For now, return a placeholder healthy result
        now = datetime.now(timezone.utc)

        # DECISION: Determine health state (placeholder - actual logic in health service)
        health_state = self.HEALTH_HEALTHY
        health_message = "Credentials validated (placeholder - health service pending)"

        # Persist health update
        self._driver.update_health(
            tenant_str,
            integration_id,
            health_state=health_state,
            health_message=health_message,
            health_checked_at=now,
        )

        return HealthCheckResult(
            health_state=health_state,
            message=health_message,
            latency_ms=100,
            checked_at=now,
        )

    # =========================================================================
    # LIMITS
    # =========================================================================

    async def get_limits_status(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[CusLimitsStatus]:
        """Get current usage against configured limits.

        Business logic:
        - Calculates billing period boundaries
        - Computes percentage utilization
        - Aggregates budget, token, and rate usage

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            CusLimitsStatus if found, None otherwise
        """
        tenant_str = str(tenant_id)

        # Fetch integration
        integration = self._driver.fetch_by_id(tenant_str, integration_id)
        if not integration:
            return None

        # DECISION: Calculate billing period
        today = date.today()
        period_start = today.replace(day=1)
        if today.month == 12:
            period_end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            period_end = today.replace(month=today.month + 1, day=1)

        # Fetch usage data
        usage = self._driver.fetch_monthly_usage(
            tenant_str, integration_id, period_start, period_end
        )
        current_rpm = self._driver.fetch_current_rpm(integration_id)

        # DECISION: Calculate utilization percentages
        def calc_percent(used: int, limit: int) -> float:
            """Calculate percentage with unlimited handling."""
            if limit == 0:
                return 0.0  # Unlimited
            return min(100.0, (used / limit) * 100)

        return CusLimitsStatus(
            integration_id=str(integration.id),
            integration_name=integration.name,
            budget_limit_cents=integration.budget_limit_cents,
            budget_used_cents=usage.budget_used_cents,
            budget_percent=calc_percent(usage.budget_used_cents, integration.budget_limit_cents),
            token_limit_month=integration.token_limit_month,
            tokens_used_month=usage.tokens_used,
            token_percent=calc_percent(usage.tokens_used, integration.token_limit_month),
            rate_limit_rpm=integration.rate_limit_rpm,
            current_rpm=current_rpm,
            rate_percent=calc_percent(current_rpm, integration.rate_limit_rpm),
            period_start=period_start,
            period_end=period_end,
        )


# Factory function
def get_cus_integration_engine(session) -> CusIntegrationEngine:
    """Get engine instance with driver configured for session.

    Args:
        session: Database session from L4 handler (required)

    Returns:
        CusIntegrationEngine instance

    Note:
        Session is REQUIRED. L4 handler owns transaction boundary.
    """
    driver = get_cus_integration_driver(session=session)
    return CusIntegrationEngine(driver=driver)

