# capability_id: CAP-018
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: Health check data access operations
# Callers: cus_health_engine.py (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-520 (L6 Purity)

"""Customer Health Driver

L6 driver for health-check-specific data access operations.

Pure persistence - no business logic.
All methods accept a Session from the caller (L4 or L5 via L4 session).

L6 Contract:
    - Session REQUIRED (passed from L4 handler / coordinator)
    - L6 does NOT commit (L4 owns transaction boundary)
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator, List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.cus_models import CusHealthState, CusIntegration

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HealthIntegrationRow:
    """Immutable data transfer object for health-relevant integration data.

    Represents raw database row fields needed by health engine — no business
    interpretation.
    """

    id: str
    tenant_id: str
    name: str
    provider_type: str
    credential_ref: str
    config: Optional[dict]
    status: str
    health_state: str
    health_checked_at: Optional[datetime]
    health_message: Optional[str]


def _to_row(integration: CusIntegration) -> HealthIntegrationRow:
    """Convert ORM model to frozen DTO."""
    return HealthIntegrationRow(
        id=str(integration.id),
        tenant_id=str(integration.tenant_id),
        name=integration.name,
        provider_type=integration.provider_type,
        credential_ref=integration.credential_ref,
        config=integration.config,
        status=integration.status,
        health_state=(
            integration.health_state.value
            if isinstance(integration.health_state, CusHealthState)
            else str(integration.health_state) if integration.health_state else "unknown"
        ),
        health_checked_at=integration.health_checked_at,
        health_message=integration.health_message,
    )


class CusHealthDriver:
    """L6 driver for health-check data access.

    Pure persistence - no business logic.
    L6 does NOT commit — L4 handler owns transaction boundary.
    """

    def __init__(self, session: Session):
        """Initialize driver with required session.

        Args:
            session: Session from L4 handler (required)
        """
        self._session = session

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    def fetch_integration_for_health_check(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Optional[HealthIntegrationRow]:
        """Fetch a single integration by ID+tenant for health checking.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)

        Returns:
            HealthIntegrationRow if found, None otherwise
        """
        integration = self._session.exec(
            select(CusIntegration).where(
                CusIntegration.id == UUID(integration_id),
                CusIntegration.tenant_id == UUID(tenant_id),
            )
        ).first()

        if not integration:
            return None

        return _to_row(integration)

    def fetch_stale_enabled_integrations(
        self,
        tenant_id: str,
        stale_threshold: datetime,
    ) -> List[HealthIntegrationRow]:
        """Fetch enabled integrations that need health checking.

        Returns integrations that are enabled AND either:
        - have never been health-checked (health_checked_at is NULL), or
        - were last checked before the stale_threshold.

        Args:
            tenant_id: Tenant ID (string)
            stale_threshold: Integrations checked before this time are stale

        Returns:
            List of HealthIntegrationRow
        """
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

        integrations = list(self._session.exec(query).all())
        return [_to_row(i) for i in integrations]

    def fetch_all_integrations_for_tenant(
        self,
        tenant_id: str,
    ) -> List[HealthIntegrationRow]:
        """Fetch all integrations for a tenant (for health summary).

        Args:
            tenant_id: Tenant ID (string)

        Returns:
            List of HealthIntegrationRow
        """
        integrations = list(
            self._session.exec(
                select(CusIntegration).where(
                    CusIntegration.tenant_id == UUID(tenant_id),
                )
            ).all()
        )
        return [_to_row(i) for i in integrations]

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def update_health_state(
        self,
        tenant_id: str,
        integration_id: str,
        health_state: str,
        health_message: str,
        health_checked_at: datetime,
    ) -> bool:
        """Update integration health state after a health check.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)
            health_state: New health state value (e.g. "healthy", "degraded")
            health_message: Human-readable health message
            health_checked_at: Timestamp of the health check

        Returns:
            True if the integration was found and updated, False otherwise

        Note:
            L6 does NOT commit — L4 handler owns transaction boundary.
        """
        integration = self._session.exec(
            select(CusIntegration).where(
                CusIntegration.id == UUID(integration_id),
                CusIntegration.tenant_id == UUID(tenant_id),
            )
        ).first()

        if not integration:
            return False

        integration.health_state = health_state
        integration.health_message = health_message
        integration.health_checked_at = health_checked_at
        integration.updated_at = datetime.now(timezone.utc)

        self._session.add(integration)
        self._session.flush()

        return True


# Factory function
def get_cus_health_driver(session: Session) -> CusHealthDriver:
    """Get driver instance.

    Args:
        session: Session from L4 handler (required)

    Returns:
        CusHealthDriver instance

    Note:
        Session is REQUIRED. L4 handler owns transaction boundary.
    """
    return CusHealthDriver(session=session)


@contextmanager
def cus_health_driver_session() -> Generator[CusHealthDriver, None, None]:
    """Context manager that creates a Session-bound CusHealthDriver.

    Use this when no L4 session is available (e.g., CLI callers,
    scheduler triggers). The session is created and closed automatically.

    Yields:
        CusHealthDriver bound to a fresh Session

    Note:
        The session is NOT committed — the caller or L4 handler must
        commit if writes are intended.
    """
    from app.db import get_engine

    engine = get_engine()
    with Session(engine) as session:
        yield CusHealthDriver(session=session)
