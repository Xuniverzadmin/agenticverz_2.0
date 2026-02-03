# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: Customer Integration Driver
"""Customer Integration Driver

L6 driver for customer integration data access.

Pure persistence - no business logic.
All methods accept primitive parameters and return raw facts.
"""

import logging
from dataclasses import dataclass
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IntegrationRow:
    """Immutable data transfer object.

    Represents raw database row - no business interpretation.
    """

    id: str
    tenant_id: str
    name: str
    provider_type: str
    credential_ref: str
    config: Dict[str, Any]
    status: str
    health_state: str
    health_checked_at: Optional[datetime]
    health_message: Optional[str]
    default_model: Optional[str]
    budget_limit_cents: int
    token_limit_month: int
    rate_limit_rpm: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UsageAggregate:
    """Immutable usage aggregate row."""

    budget_used_cents: int
    tokens_used: int


class CusIntegrationDriver:
    """L6 driver for customer integration data access.

    Pure persistence - no business logic.
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize driver.

        Args:
            session: Optional session for transaction scope.
                     If None, creates new session per operation.
        """
        self._external_session = session

    def _get_session(self) -> Tuple[Session, bool]:
        """Get session, returning (session, should_close)."""
        if self._external_session:
            return self._external_session, False
        engine = get_engine()
        return Session(engine), True

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    def fetch_by_id(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Optional[CusIntegration]:
        """Fetch integration by ID.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)

        Returns:
            CusIntegration if found, None otherwise
        """
        session, should_close = self._get_session()
        try:
            return session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()
        finally:
            if should_close:
                session.close()

    def fetch_by_name(
        self,
        tenant_id: str,
        name: str,
    ) -> Optional[CusIntegration]:
        """Fetch integration by name.

        Args:
            tenant_id: Tenant ID (string)
            name: Integration name

        Returns:
            CusIntegration if found, None otherwise
        """
        session, should_close = self._get_session()
        try:
            return session.exec(
                select(CusIntegration).where(
                    CusIntegration.tenant_id == tenant_id,
                    CusIntegration.name == name,
                )
            ).first()
        finally:
            if should_close:
                session.close()

    def fetch_list(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        provider_type: Optional[str] = None,
    ) -> Tuple[List[CusIntegration], int]:
        """Fetch integrations for tenant with pagination.

        Args:
            tenant_id: Tenant ID (string)
            offset: Pagination offset
            limit: Page size
            status: Optional status filter
            provider_type: Optional provider filter

        Returns:
            Tuple of (integrations, total_count)
        """
        session, should_close = self._get_session()
        try:
            # Build base query
            query = select(CusIntegration).where(
                CusIntegration.tenant_id == tenant_id
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
        finally:
            if should_close:
                session.close()

    def fetch_monthly_usage(
        self,
        tenant_id: str,
        integration_id: str,
        period_start: date,
        period_end: date,
    ) -> UsageAggregate:
        """Fetch aggregated usage for a billing period.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)
            period_start: Start of billing period
            period_end: End of billing period

        Returns:
            UsageAggregate with budget and token totals
        """
        session, should_close = self._get_session()
        try:
            query = select(
                func.sum(CusUsageDaily.total_cost_cents),
                func.sum(CusUsageDaily.total_tokens_in + CusUsageDaily.total_tokens_out),
            ).where(
                CusUsageDaily.integration_id == UUID(integration_id),
                CusUsageDaily.tenant_id == tenant_id,
                CusUsageDaily.date >= period_start,
                CusUsageDaily.date < period_end,
            )

            result = session.exec(query).first()
            budget_used = result[0] or 0 if result else 0
            tokens_used = result[1] or 0 if result else 0

            return UsageAggregate(
                budget_used_cents=int(budget_used),
                tokens_used=int(tokens_used),
            )
        finally:
            if should_close:
                session.close()

    def fetch_current_rpm(
        self,
        integration_id: str,
    ) -> int:
        """Fetch current requests per minute.

        Args:
            integration_id: Integration ID (string)

        Returns:
            Count of requests in the last minute
        """
        session, should_close = self._get_session()
        try:
            one_minute_ago = datetime.now(timezone.utc).replace(
                second=0, microsecond=0
            )
            query = select(func.count()).where(
                CusLLMUsage.integration_id == UUID(integration_id),
                CusLLMUsage.created_at >= one_minute_ago,
            )
            return session.exec(query).one() or 0
        finally:
            if should_close:
                session.close()

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def create(
        self,
        tenant_id: str,
        name: str,
        provider_type: str,
        credential_ref: str,
        config: Dict[str, Any],
        status: str,
        health_state: str,
        default_model: Optional[str],
        budget_limit_cents: int,
        token_limit_month: int,
        rate_limit_rpm: int,
        created_by: Optional[str],
    ) -> CusIntegration:
        """Create integration record.

        Args:
            All fields for the integration

        Returns:
            Created CusIntegration
        """
        session, should_close = self._get_session()
        try:
            integration = CusIntegration(
                id=str(uuid4()),
                tenant_id=tenant_id,
                name=name,
                provider_type=provider_type.lower() if isinstance(provider_type, str) else provider_type,
                credential_ref=credential_ref,
                config=config,
                status=status,
                health_state=health_state,
                default_model=default_model,
                budget_limit_cents=budget_limit_cents,
                token_limit_month=token_limit_month,
                rate_limit_rpm=rate_limit_rpm,
                created_by=created_by,
            )

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(f"Created integration {integration.id} for tenant {tenant_id}")

            return integration
        finally:
            if should_close:
                session.close()

    def update_fields(
        self,
        tenant_id: str,
        integration_id: str,
        updates: Dict[str, Any],
    ) -> Optional[CusIntegration]:
        """Update integration fields.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)
            updates: Dict of field -> value to update

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        session, should_close = self._get_session()
        try:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return None

            for key, value in updates.items():
                if hasattr(integration, key) and value is not None:
                    setattr(integration, key, value)

            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(f"Updated integration {integration_id}")

            return integration
        finally:
            if should_close:
                session.close()

    def update_status(
        self,
        tenant_id: str,
        integration_id: str,
        status: str,
    ) -> Optional[CusIntegration]:
        """Update integration status.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)
            status: New status value

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        session, should_close = self._get_session()
        try:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return None

            integration.status = status
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            session.refresh(integration)

            logger.info(f"Updated integration {integration_id} status to {status}")

            return integration
        finally:
            if should_close:
                session.close()

    def update_config(
        self,
        tenant_id: str,
        integration_id: str,
        config_updates: Dict[str, Any],
    ) -> Optional[CusIntegration]:
        """Update integration config (merge).

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)
            config_updates: Dict to merge into existing config

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        session, should_close = self._get_session()
        try:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return None

            integration.config = {**integration.config, **config_updates}
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()
            session.refresh(integration)

            return integration
        finally:
            if should_close:
                session.close()

    def update_health(
        self,
        tenant_id: str,
        integration_id: str,
        health_state: str,
        health_message: Optional[str],
        health_checked_at: datetime,
    ) -> Optional[CusIntegration]:
        """Update integration health state.

        Args:
            tenant_id: Tenant ID (string)
            integration_id: Integration ID (string)
            health_state: New health state
            health_message: Health check message
            health_checked_at: Timestamp of health check

        Returns:
            Updated CusIntegration if found, None otherwise
        """
        session, should_close = self._get_session()
        try:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return None

            integration.health_state = health_state
            integration.health_message = health_message
            integration.health_checked_at = health_checked_at
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            session.commit()

            return integration
        finally:
            if should_close:
                session.close()


# Factory function
def get_cus_integration_driver(session: Optional[Session] = None) -> CusIntegrationDriver:
    """Get driver instance.

    Args:
        session: Optional session for transaction scope

    Returns:
        CusIntegrationDriver instance
    """
    return CusIntegrationDriver(session=session)
