# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access for killswitch read operations
# Callers: killswitch engines (L4)
# Allowed Imports: ORM models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-280, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for killswitch reads.
# No business logic - only DB reads and ORM ↔ DTO transformation.
# Extracted from customer_killswitch_read_service.py (Phase 2)

"""
Killswitch Read Driver (L6)

Pure data access layer for killswitch read operations.
No business logic - only query construction and data retrieval.

Architecture:
    L3 (Adapter) → L4 (Engine) → L6 (this driver) → Database

Operations:
- Query killswitch state for tenant
- Query active guardrails
- Query incident statistics
- No mutations (read-only)

Reference: PHASE2_EXTRACTION_PROTOCOL.md
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
# L6 DTOs (Domain-level data transfer objects)
# =============================================================================


class KillswitchStateDTO(BaseModel):
    """Killswitch state information."""

    is_frozen: bool
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[str] = None


class GuardrailInfoDTO(BaseModel):
    """Active guardrail information."""

    name: str


class IncidentStatsDTO(BaseModel):
    """Incident statistics for a tenant."""

    incidents_blocked_24h: int
    last_incident_time: Optional[datetime] = None


class KillswitchStatusDTO(BaseModel):
    """Complete killswitch status information."""

    state: KillswitchStateDTO
    active_guardrails: List[str]
    incident_stats: IncidentStatsDTO


# =============================================================================
# L6 Driver Class
# =============================================================================


class KillswitchReadDriver:
    """
    L6 driver for killswitch read operations.

    Pure data access - no business logic.
    All methods require tenant_id for isolation.
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize driver with optional session (lazy loaded)."""
        self._session = session

    def _get_session(self) -> Session:
        """Get the database session (lazy loaded)."""
        if self._session is None:
            self._session = next(get_session())
        return self._session

    def get_killswitch_status(
        self,
        tenant_id: str,
    ) -> KillswitchStatusDTO:
        """
        Get complete killswitch status for a tenant.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED)

        Returns:
            KillswitchStatusDTO with state, guardrails, and incident stats

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

        return KillswitchStatusDTO(
            state=state,
            active_guardrails=active_guardrails,
            incident_stats=incident_stats,
        )

    def _get_killswitch_state(
        self,
        session: Session,
        tenant_id: str,
    ) -> KillswitchStateDTO:
        """Get killswitch state for a tenant."""
        stmt = select(KillSwitchState).where(
            and_(
                KillSwitchState.entity_type == "tenant",
                KillSwitchState.entity_id == tenant_id,
            )
        )
        row = session.exec(stmt).first()
        state = row[0] if row else None

        return KillswitchStateDTO(
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
    ) -> IncidentStatsDTO:
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

        return IncidentStatsDTO(
            incidents_blocked_24h=incidents_count,
            last_incident_time=last_incident.created_at if last_incident else None,
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_killswitch_read_driver(session: Optional[Session] = None) -> KillswitchReadDriver:
    """
    Get KillswitchReadDriver instance.

    Args:
        session: Optional SQLModel session. If not provided, creates one internally.

    Returns:
        KillswitchReadDriver instance
    """
    return KillswitchReadDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "KillswitchReadDriver",
    "get_killswitch_read_driver",
    # DTOs
    "KillswitchStateDTO",
    "GuardrailInfoDTO",
    "IncidentStatsDTO",
    "KillswitchStatusDTO",
]
