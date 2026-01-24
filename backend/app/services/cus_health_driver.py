# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: engine-call
#   Execution: sync
# Role: Data access for customer integration health checks
# Callers: CusHealthEngine (L4)
# Allowed Imports: sqlalchemy, sqlmodel, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Health Driver

L6 driver for customer integration health data access.

Pure persistence - no business logic.
Returns raw facts: integration data, health state.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.db import get_engine
from app.models.cus_models import CusHealthState, CusIntegration


@dataclass(frozen=True)
class IntegrationHealthRow:
    """Immutable integration data for health checking."""

    id: str
    tenant_id: str
    name: str
    provider_type: str
    status: str
    credential_ref: str
    config: dict
    health_state: CusHealthState
    health_checked_at: Optional[datetime]
    health_message: Optional[str]


@dataclass(frozen=True)
class HealthSummaryRow:
    """Immutable health summary data."""

    total: int
    healthy: int
    degraded: int
    unhealthy: int
    unknown: int
    stale_count: int


class CusHealthDriver:
    """L6 driver for customer health data access.

    Pure persistence - no business logic.
    Returns raw facts for engine to interpret.
    """

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    def fetch_integration(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Optional[IntegrationHealthRow]:
        """Fetch integration data for health check.

        Args:
            tenant_id: Tenant ID for ownership verification
            integration_id: Integration ID

        Returns:
            IntegrationHealthRow if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == UUID(tenant_id),
                )
            ).first()

            if not integration:
                return None

            return IntegrationHealthRow(
                id=str(integration.id),
                tenant_id=str(integration.tenant_id),
                name=integration.name,
                provider_type=integration.provider_type,
                status=integration.status.value if hasattr(integration.status, 'value') else str(integration.status),
                credential_ref=integration.credential_ref,
                config=integration.config or {},
                health_state=integration.health_state,
                health_checked_at=integration.health_checked_at,
                health_message=integration.health_message,
            )

    def fetch_stale_integrations(
        self,
        tenant_id: str,
        stale_threshold_minutes: int,
    ) -> List[IntegrationHealthRow]:
        """Fetch integrations that need health checking.

        Args:
            tenant_id: Tenant ID
            stale_threshold_minutes: Only return if last check older than this

        Returns:
            List of integrations needing health check
        """
        engine = get_engine()

        with Session(engine) as session:
            stale_threshold = datetime.now(timezone.utc) - timedelta(
                minutes=stale_threshold_minutes
            )

            query = (
                select(CusIntegration)
                .where(
                    CusIntegration.tenant_id == UUID(tenant_id),
                    CusIntegration.status == "enabled",
                )
                .where(
                    (CusIntegration.health_checked_at.is_(None))
                    | (CusIntegration.health_checked_at < stale_threshold)
                )
            )

            integrations = list(session.exec(query).all())

            return [
                IntegrationHealthRow(
                    id=str(i.id),
                    tenant_id=str(i.tenant_id),
                    name=i.name,
                    provider_type=i.provider_type,
                    status=i.status.value if hasattr(i.status, 'value') else str(i.status),
                    credential_ref=i.credential_ref,
                    config=i.config or {},
                    health_state=i.health_state,
                    health_checked_at=i.health_checked_at,
                    health_message=i.health_message,
                )
                for i in integrations
            ]

    def fetch_all_integrations(self, tenant_id: str) -> List[IntegrationHealthRow]:
        """Fetch all integrations for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of all integrations
        """
        engine = get_engine()

        with Session(engine) as session:
            integrations = list(
                session.exec(
                    select(CusIntegration).where(
                        CusIntegration.tenant_id == UUID(tenant_id),
                    )
                ).all()
            )

            return [
                IntegrationHealthRow(
                    id=str(i.id),
                    tenant_id=str(i.tenant_id),
                    name=i.name,
                    provider_type=i.provider_type,
                    status=i.status.value if hasattr(i.status, 'value') else str(i.status),
                    credential_ref=i.credential_ref,
                    config=i.config or {},
                    health_state=i.health_state,
                    health_checked_at=i.health_checked_at,
                    health_message=i.health_message,
                )
                for i in integrations
            ]

    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================

    def update_health_state(
        self,
        integration_id: str,
        health_state: CusHealthState,
        health_message: str,
        health_checked_at: datetime,
    ) -> bool:
        """Update integration health state.

        Args:
            integration_id: Integration to update
            health_state: New health state
            health_message: Health message
            health_checked_at: When check was performed

        Returns:
            True if updated, False if not found
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                )
            ).first()

            if not integration:
                return False

            integration.health_state = health_state
            integration.health_checked_at = health_checked_at
            integration.health_message = health_message
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            return True


# Factory function
def get_cus_health_driver() -> CusHealthDriver:
    """Get driver instance.

    Returns:
        CusHealthDriver instance
    """
    return CusHealthDriver()
