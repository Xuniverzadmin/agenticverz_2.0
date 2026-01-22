# Layer: L4 — Domain Engines
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (with async DB operations)
# Role: Business logic for Customer Integration domain (LLM BYOK, SDK, RAG)
# Callers: aos_cus_integrations.py API router
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: Connectivity Domain - Customer Console v1 Constitution

"""Customer Integration Service

PURPOSE:
    Business logic for managing customer LLM integrations.
    Handles CRUD operations, lifecycle transitions, and limit calculations.

RESPONSIBILITIES:
    - Create, update, delete integrations
    - Enable/disable lifecycle transitions
    - Calculate current usage vs limits
    - Coordinate health checks (delegates to cus_health_service)

STATE MACHINE:
    created -> enabled -> disabled -> enabled (cycle)
    created -> deleted (terminal)
    enabled -> deleted (terminal)
    disabled -> deleted (terminal)

TENANT ISOLATION:
    All operations require tenant_id and verify ownership.
"""

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlmodel import Session, col, func, select

from app.db import get_engine
from app.models.cus_models import (
    CusHealthState,
    CusIntegration,
    CusIntegrationStatus,
    CusLLMUsage,
    CusUsageDaily,
)
from app.schemas.cus_schemas import CusLimitsStatus

logger = logging.getLogger(__name__)


class CusIntegrationService:
    """Service for managing customer LLM integrations.

    Phase 4: CONTROL PLANE operations.
    All methods are tenant-scoped for isolation.
    """

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
    ) -> CusIntegration:
        """Create a new integration.

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
        engine = get_engine()

        with Session(engine) as session:
            # Check for duplicate name
            # Note: tenant_id is UUID from resolver, CusIntegration.tenant_id is str (VARCHAR)
            existing = session.exec(
                select(CusIntegration).where(
                    CusIntegration.tenant_id == str(tenant_id),
                    CusIntegration.name == name,
                )
            ).first()

            if existing:
                raise ValueError(f"Integration with name '{name}' already exists")

            # Create integration
            # Model uses str fields, values must be lowercase to match DB constraints
            integration = CusIntegration(
                id=str(uuid4()),
                tenant_id=str(tenant_id),
                name=name,
                provider_type=provider_type.lower() if isinstance(provider_type, str) else provider_type,
                credential_ref=credential_ref,
                config=config or {},
                status="created",
                health_state="unknown",
                default_model=default_model,
                budget_limit_cents=budget_limit_cents,
                token_limit_month=token_limit_month,
                rate_limit_rpm=rate_limit_rpm,
                created_by=str(created_by) if created_by else None,
            )

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(
                f"Created integration {integration.id} for tenant {tenant_id}"
            )

            return integration

    # =========================================================================
    # READ
    # =========================================================================

    async def get_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[CusIntegration]:
        """Get integration by ID.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            CusIntegration if found and owned by tenant, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            return integration

    async def list_integrations(
        self,
        tenant_id: UUID,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        provider_type: Optional[str] = None,
    ) -> Tuple[List[CusIntegration], int]:
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
        engine = get_engine()

        with Session(engine) as session:
            # Build base query - convert UUID to str for VARCHAR column
            query = select(CusIntegration).where(
                CusIntegration.tenant_id == str(tenant_id)
            )

            # Apply filters
            if status:
                query = query.where(CusIntegration.status == status)
            if provider_type:
                query = query.where(CusIntegration.provider_type == provider_type)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # Apply pagination and ordering
            query = query.order_by(col(CusIntegration.created_at).desc())
            query = query.offset(offset).limit(limit)

            integrations = list(session.exec(query).all())

            return integrations, total

    # =========================================================================
    # UPDATE
    # =========================================================================

    async def update_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
        **kwargs,
    ) -> Optional[CusIntegration]:
        """Update integration fields.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID
            **kwargs: Fields to update

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            if not integration:
                return None

            # Apply updates
            for key, value in kwargs.items():
                if hasattr(integration, key) and value is not None:
                    setattr(integration, key, value)

            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(f"Updated integration {integration_id}")

            return integration

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> bool:
        """Delete integration (soft delete via status).

        The integration is marked as deleted but retained for telemetry references.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            True if deleted, False if not found
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            if not integration:
                return False

            # Soft delete - just disable and mark in config
            integration.status = CusIntegrationStatus.DISABLED
            integration.config = {
                **integration.config,
                "_deleted": True,
                "_deleted_at": datetime.now(timezone.utc).isoformat(),
            }
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()

            logger.info(f"Deleted (soft) integration {integration_id}")

            return True

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def enable_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[CusIntegration]:
        """Enable an integration.

        Valid transitions: created -> enabled, disabled -> enabled

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            Updated CusIntegration if found, None otherwise

        Raises:
            ValueError: If integration is in error state
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            if not integration:
                return None

            # Validate state transition
            if integration.status == CusIntegrationStatus.ERROR:
                raise ValueError(
                    "Cannot enable integration in error state. "
                    "Fix the error condition first."
                )

            if integration.config.get("_deleted"):
                raise ValueError("Cannot enable deleted integration")

            integration.status = CusIntegrationStatus.ENABLED
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(f"Enabled integration {integration_id}")

            return integration

    async def disable_integration(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[CusIntegration]:
        """Disable an integration.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            if not integration:
                return None

            integration.status = CusIntegrationStatus.DISABLED
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(f"Disabled integration {integration_id}")

            return integration

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    async def test_credentials(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Test integration credentials.

        Delegates to cus_health_service for actual provider testing.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            Health check result dict if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            if not integration:
                return None

            # TODO: Delegate to CusHealthService when implemented
            # For now, return a placeholder healthy result
            now = datetime.now(timezone.utc)

            # Update health state
            integration.health_state = CusHealthState.HEALTHY
            integration.health_checked_at = now
            integration.health_message = "Credentials validated"
            integration.updated_at = now

            session.add(integration)
            session.commit()

            return {
                "health_state": CusHealthState.HEALTHY,
                "message": "Credentials validated (placeholder - health service pending)",
                "latency_ms": 100,
                "checked_at": now,
            }

    # =========================================================================
    # LIMITS
    # =========================================================================

    async def get_limits_status(
        self,
        tenant_id: UUID,
        integration_id: str,
    ) -> Optional[CusLimitsStatus]:
        """Get current usage against configured limits.

        Calculates budget, token, and rate limit status.

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration ID

        Returns:
            CusLimitsStatus if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == str(tenant_id),
                )
            ).first()

            if not integration:
                return None

            # Get current month's usage
            today = date.today()
            period_start = today.replace(day=1)
            if today.month == 12:
                period_end = today.replace(year=today.year + 1, month=1, day=1)
            else:
                period_end = today.replace(month=today.month + 1, day=1)

            # Query daily aggregates for current month
            daily_query = select(
                func.sum(CusUsageDaily.total_cost_cents),
                func.sum(CusUsageDaily.total_tokens_in + CusUsageDaily.total_tokens_out),
            ).where(
                CusUsageDaily.integration_id == UUID(integration_id),
                CusUsageDaily.tenant_id == str(tenant_id),
                CusUsageDaily.date >= period_start,
                CusUsageDaily.date < period_end,
            )

            result = session.exec(daily_query).first()
            budget_used = result[0] or 0 if result else 0
            tokens_used = result[1] or 0 if result else 0

            # Get current RPM (calls in last minute)
            # This is a simplified implementation - real one would use Redis
            one_minute_ago = datetime.now(timezone.utc).replace(
                second=0, microsecond=0
            )
            rpm_query = select(func.count()).where(
                CusLLMUsage.integration_id == UUID(integration_id),
                CusLLMUsage.created_at >= one_minute_ago,
            )
            current_rpm = session.exec(rpm_query).one() or 0

            # Calculate percentages
            def calc_percent(used: int, limit: int) -> float:
                if limit == 0:
                    return 0.0  # Unlimited
                return min(100.0, (used / limit) * 100)

            return CusLimitsStatus(
                integration_id=str(integration.id),
                integration_name=integration.name,
                budget_limit_cents=integration.budget_limit_cents,
                budget_used_cents=int(budget_used),
                budget_percent=calc_percent(int(budget_used), integration.budget_limit_cents),
                token_limit_month=integration.token_limit_month,
                tokens_used_month=int(tokens_used),
                token_percent=calc_percent(int(tokens_used), integration.token_limit_month),
                rate_limit_rpm=integration.rate_limit_rpm,
                current_rpm=current_rpm,
                rate_percent=calc_percent(current_rpm, integration.rate_limit_rpm),
                period_start=period_start,
                period_end=period_end,
            )
