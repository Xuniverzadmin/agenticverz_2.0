# Layer: L4 — Domain Engine
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Customer killswitch read operations (L4 service)
# Callers: customer_killswitch_adapter.py (L3)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-280, PIN-281 (L2 Promotion Governance)
#
# GOVERNANCE NOTE:
# This L4 service provides read operations for customer killswitch status.
# It queries L6 models and returns domain DTOs.
# The L3 adapter transforms these to customer-safe DTOs.

"""
Customer Killswitch Read Service (L4)

This service provides read operations for customer killswitch status.
L3 adapters call this service to get killswitch state, guardrails, and incident info.

L3 (customer_killswitch_adapter.py) → L4 (this service) → L6 (models)

The service:
1. Queries KillSwitchState for tenant freeze status
2. Queries DefaultGuardrail for active guardrails
3. Queries Incident for incident statistics
4. Returns domain DTOs (not customer-safe - L3 transforms)

Reference: PIN-280 (L2 Promotion Governance), PIN-281 (Claude Task TODO)
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

from app.db import get_session
from app.models.killswitch import (
    DefaultGuardrail,
    Incident,
    KillSwitchState,
)

# =============================================================================
# L4 DTOs (Domain-level, not customer-safe)
# =============================================================================


class KillswitchState(BaseModel):
    """Killswitch state information."""

    is_frozen: bool
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[str] = None


class GuardrailInfo(BaseModel):
    """Active guardrail information."""

    name: str


class IncidentStats(BaseModel):
    """Incident statistics for a tenant."""

    incidents_blocked_24h: int
    last_incident_time: Optional[datetime] = None


class KillswitchStatusInfo(BaseModel):
    """Complete killswitch status information."""

    state: KillswitchState
    active_guardrails: List[str]
    incident_stats: IncidentStats


# =============================================================================
# L4 Service Class
# =============================================================================


class CustomerKillswitchReadService:
    """
    Read operations for customer killswitch status.

    This service provides domain-level access to killswitch state,
    guardrails, and incident statistics. The L3 adapter transforms
    these results to customer-safe DTOs.

    INVARIANT: All methods require tenant_id for isolation.
    INVARIANT: Read-only - no mutations.

    PIN-280 Rule: L4 Is DB Access + Domain Logic
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session (lazy loaded)."""
        self._session = session

    def _get_session(self) -> Session:
        """Get the database session (lazy loaded)."""
        if self._session is None:
            self._session = next(get_session())
        return self._session

    def get_killswitch_status(
        self,
        tenant_id: str,
    ) -> KillswitchStatusInfo:
        """
        Get complete killswitch status for a tenant.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED)

        Returns:
            KillswitchStatusInfo with state, guardrails, and incident stats

        Raises:
            ValueError: If tenant_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_killswitch_status")

        session = self._get_session()

        # Get tenant killswitch state
        state = self._get_killswitch_state(session, tenant_id)

        # Get active guardrails
        active_guardrails = self._get_active_guardrails(session)

        # Get incident stats
        incident_stats = self._get_incident_stats(session, tenant_id)

        return KillswitchStatusInfo(
            state=state,
            active_guardrails=active_guardrails,
            incident_stats=incident_stats,
        )

    def _get_killswitch_state(
        self,
        session: Session,
        tenant_id: str,
    ) -> KillswitchState:
        """Get killswitch state for a tenant."""
        stmt = select(KillSwitchState).where(
            and_(
                KillSwitchState.entity_type == "tenant",
                KillSwitchState.entity_id == tenant_id,
            )
        )
        row = session.exec(stmt).first()
        state = row[0] if row else None

        return KillswitchState(
            is_frozen=state.is_frozen if state else False,
            frozen_at=state.frozen_at if state else None,
            frozen_by=state.frozen_by if state else None,
        )

    def _get_active_guardrails(
        self,
        session: Session,
    ) -> List[str]:
        """Get list of active guardrail names."""
        stmt = select(DefaultGuardrail).where(DefaultGuardrail.is_enabled == True)
        rows = session.exec(stmt).all()
        return [g[0].name if hasattr(g, "__getitem__") else g.name for g in rows]

    def _get_incident_stats(
        self,
        session: Session,
        tenant_id: str,
    ) -> IncidentStats:
        """Get incident statistics for a tenant."""
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)

        # Count incidents in last 24h
        count_stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.created_at >= yesterday,
            )
        )
        count_row = session.exec(count_stmt).first()
        incidents_count = count_row[0] if count_row else 0

        # Get last incident time
        last_stmt = select(Incident).where(Incident.tenant_id == tenant_id).order_by(desc(Incident.created_at)).limit(1)
        last_row = session.exec(last_stmt).first()
        last_incident = last_row[0] if last_row else None

        return IncidentStats(
            incidents_blocked_24h=incidents_count,
            last_incident_time=last_incident.created_at if last_incident else None,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_customer_killswitch_read_service_instance: Optional[CustomerKillswitchReadService] = None


def get_customer_killswitch_read_service() -> CustomerKillswitchReadService:
    """
    Get the singleton CustomerKillswitchReadService instance.

    This is the ONLY way L3 should obtain a killswitch read service.
    Direct instantiation is discouraged.

    Returns:
        CustomerKillswitchReadService singleton instance
    """
    global _customer_killswitch_read_service_instance
    if _customer_killswitch_read_service_instance is None:
        _customer_killswitch_read_service_instance = CustomerKillswitchReadService()
    return _customer_killswitch_read_service_instance


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerKillswitchReadService",
    "get_customer_killswitch_read_service",
    # DTOs
    "KillswitchState",
    "GuardrailInfo",
    "IncidentStats",
    "KillswitchStatusInfo",
]
