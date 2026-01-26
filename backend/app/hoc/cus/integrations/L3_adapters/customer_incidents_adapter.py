# Layer: L3 — Boundary Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L4)
# Role: Customer incidents boundary adapter (L2 → L3 → L4)
# Callers: guard.py (L2) — to be wired
# Allowed Imports: L4
# Forbidden Imports: L1, L2, L5, L6
# Reference: PIN-280, PIN-281 (L2 Promotion Governance - PHASE 1 L3 Closure)
#
# GOVERNANCE NOTE:
# This L3 adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only see their own incidents)
# - Customer-safe schema (calm vocabulary per M29)
# - No internal fields exposed (root cause analysis, internal notes)

"""
Customer Incidents Boundary Adapter (L3)

This adapter sits between L2 (guard.py API) and L4 (services).

L2 (Guard API) → L3 (this adapter) → L4 (IncidentReadService/IncidentWriteService)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation
3. Transforms to customer-safe schema (calm vocabulary)
4. Delegates to L4 services (no L6 access)
5. Returns customer-friendly results

Reference: PIN-280 (L2 Promotion Governance), PIN-281 (PHASE 1 L3 Closure)
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Session

# L4 imports (allowed) - no L6 direct access per PIN-281
from app.hoc.cus.incidents.L5_engines.incident_read_engine import get_incident_read_service
from app.hoc.cus.incidents.L5_engines.incident_write_engine import get_incident_write_service

# =============================================================================
# Customer-Safe DTOs (Calm Vocabulary per M29)
# =============================================================================


class CustomerIncidentSummary(BaseModel):
    """Customer-safe incident summary for list view."""

    id: str
    title: str
    severity: str  # info, attention, action, urgent (calm vocabulary)
    status: str  # open, acknowledged, resolved
    trigger_type: str
    action_taken: Optional[str] = None
    cost_avoided_cents: int
    calls_affected: int
    started_at: str
    ended_at: Optional[str] = None
    # No internal fields: root_cause, internal_notes, debug_data


class CustomerIncidentEvent(BaseModel):
    """Customer-safe timeline event."""

    id: str
    event_type: str
    description: str
    timestamp: str
    # No internal data field


class CustomerIncidentDetail(BaseModel):
    """Customer-safe incident detail."""

    incident: CustomerIncidentSummary
    timeline: List[CustomerIncidentEvent]
    # No internal fields: correlation_id, trace_ids, replay_data


class CustomerIncidentListResponse(BaseModel):
    """Paginated customer incident list."""

    items: List[CustomerIncidentSummary]
    total: int
    page: int
    page_size: int


# =============================================================================
# Severity Translation (Internal → Calm Vocabulary)
# =============================================================================


def _translate_severity(internal_severity: str) -> str:
    """Translate internal severity to calm customer vocabulary."""
    mapping = {
        "critical": "urgent",
        "high": "action",
        "medium": "attention",
        "low": "info",
        "info": "info",
    }
    return mapping.get(internal_severity.lower(), "info")


def _translate_status(internal_status: str) -> str:
    """Translate internal status to customer vocabulary."""
    mapping = {
        "open": "open",
        "active": "open",
        "acknowledged": "acknowledged",
        "resolved": "resolved",
        "closed": "resolved",
    }
    return mapping.get(internal_status.lower(), "open")


# =============================================================================
# L3 Adapter Class
# =============================================================================


class CustomerIncidentsAdapter:
    """
    Boundary adapter for customer incident operations.

    This class provides the ONLY interface that L2 (guard.py) may use
    to access incident functionality. It enforces tenant isolation and
    transforms data to customer-safe schemas.

    PIN-280 Rule: L3 Is Translation Only + Tenant Scoping
    PIN-281 Rule: L3 imports L4 only (no L6 direct access)
    """

    def __init__(self, session: Session):
        """Initialize adapter with database session."""
        self._session = session
        self._read_service = get_incident_read_service(session)
        self._write_service = get_incident_write_service(session)

    def list_incidents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CustomerIncidentListResponse:
        """
        List incidents for a customer.

        Enforces tenant isolation - customer can only see their own incidents.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            status: Filter by status
            severity: Filter by severity
            from_date: Filter from date (ISO format)
            to_date: Filter to date (ISO format)
            limit: Page size (max 100)
            offset: Pagination offset

        Returns:
            CustomerIncidentListResponse with customer-safe summaries
        """
        # Parse dates if provided
        from_dt = datetime.fromisoformat(from_date) if from_date else None
        to_dt = datetime.fromisoformat(to_date) if to_date else None

        # L3 → L4 delegation
        incidents, total = self._read_service.list_incidents(
            tenant_id=tenant_id,
            status=status,
            severity=severity,
            from_date=from_dt,
            to_date=to_dt,
            limit=limit,
            offset=offset,
        )

        # Transform to customer-safe schema
        items = []
        for incident in incidents:
            items.append(
                CustomerIncidentSummary(
                    id=incident.id,
                    title=incident.title,
                    severity=_translate_severity(
                        incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
                    ),
                    status=_translate_status(
                        incident.status.value if hasattr(incident.status, "value") else str(incident.status)
                    ),
                    trigger_type=incident.trigger_type.value
                    if hasattr(incident.trigger_type, "value")
                    else str(incident.trigger_type),
                    action_taken=incident.action_taken,
                    cost_avoided_cents=int(incident.cost_avoided_cents or 0),
                    calls_affected=incident.calls_affected or 0,
                    started_at=incident.created_at.isoformat() if incident.created_at else "",
                    ended_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
                )
            )

        return CustomerIncidentListResponse(
            items=items,
            total=total,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit,
        )

    def get_incident(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> Optional[CustomerIncidentDetail]:
        """
        Get incident detail with timeline.

        Enforces tenant isolation - returns None if incident belongs to different tenant.

        Args:
            incident_id: Incident ID
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerIncidentDetail if found and authorized, None otherwise
        """
        # L3 → L4 delegation
        incident = self._read_service.get_incident(incident_id, tenant_id)

        if incident is None:
            return None

        # Get timeline events via L4 service
        events = self._read_service.get_incident_events(incident_id)

        timeline = []
        for event in events:
            timeline.append(
                CustomerIncidentEvent(
                    id=event.id,
                    event_type=event.event_type,
                    description=event.description,
                    timestamp=event.created_at.isoformat() if event.created_at else "",
                )
            )

        summary = CustomerIncidentSummary(
            id=incident.id,
            title=incident.title,
            severity=_translate_severity(
                incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
            ),
            status=_translate_status(
                incident.status.value if hasattr(incident.status, "value") else str(incident.status)
            ),
            trigger_type=incident.trigger_type.value
            if hasattr(incident.trigger_type, "value")
            else str(incident.trigger_type),
            action_taken=incident.action_taken,
            cost_avoided_cents=int(incident.cost_avoided_cents or 0),
            calls_affected=incident.calls_affected or 0,
            started_at=incident.created_at.isoformat() if incident.created_at else "",
            ended_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        )

        return CustomerIncidentDetail(
            incident=summary,
            timeline=timeline,
        )

    def acknowledge_incident(
        self,
        incident_id: str,
        tenant_id: str,
        acknowledged_by: str = "customer",
    ) -> Optional[CustomerIncidentSummary]:
        """
        Acknowledge an incident.

        Args:
            incident_id: Incident ID
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            acknowledged_by: Who acknowledged

        Returns:
            Updated CustomerIncidentSummary if found and authorized, None otherwise
        """
        # L3 → L4 delegation for read
        incident = self._read_service.get_incident(incident_id, tenant_id)

        if incident is None:
            return None

        # L3 → L4 delegation for write
        incident = self._write_service.acknowledge_incident(incident, acknowledged_by)

        return CustomerIncidentSummary(
            id=incident.id,
            title=incident.title,
            severity=_translate_severity(
                incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
            ),
            status="acknowledged",
            trigger_type=incident.trigger_type.value
            if hasattr(incident.trigger_type, "value")
            else str(incident.trigger_type),
            action_taken=incident.action_taken,
            cost_avoided_cents=int(incident.cost_avoided_cents or 0),
            calls_affected=incident.calls_affected or 0,
            started_at=incident.created_at.isoformat() if incident.created_at else "",
            ended_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        )

    def resolve_incident(
        self,
        incident_id: str,
        tenant_id: str,
        resolved_by: str = "customer",
        resolution_notes: Optional[str] = None,
    ) -> Optional[CustomerIncidentSummary]:
        """
        Resolve an incident.

        Args:
            incident_id: Incident ID
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            resolved_by: Who resolved
            resolution_notes: Optional resolution notes

        Returns:
            Updated CustomerIncidentSummary if found and authorized, None otherwise
        """
        # L3 → L4 delegation for read
        incident = self._read_service.get_incident(incident_id, tenant_id)

        if incident is None:
            return None

        # L3 → L4 delegation for write
        incident = self._write_service.resolve_incident(incident, resolved_by, resolution_notes)

        return CustomerIncidentSummary(
            id=incident.id,
            title=incident.title,
            severity=_translate_severity(
                incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
            ),
            status="resolved",
            trigger_type=incident.trigger_type.value
            if hasattr(incident.trigger_type, "value")
            else str(incident.trigger_type),
            action_taken=incident.action_taken,
            cost_avoided_cents=int(incident.cost_avoided_cents or 0),
            calls_affected=incident.calls_affected or 0,
            started_at=incident.created_at.isoformat() if incident.created_at else "",
            ended_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        )


# =============================================================================
# Factory
# =============================================================================


def get_customer_incidents_adapter(session: Session) -> CustomerIncidentsAdapter:
    """
    Get a CustomerIncidentsAdapter instance.

    Args:
        session: Database session

    Returns:
        CustomerIncidentsAdapter instance
    """
    return CustomerIncidentsAdapter(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerIncidentsAdapter",
    "get_customer_incidents_adapter",
    # DTOs for L2 convenience
    "CustomerIncidentSummary",
    "CustomerIncidentEvent",
    "CustomerIncidentDetail",
    "CustomerIncidentListResponse",
]
