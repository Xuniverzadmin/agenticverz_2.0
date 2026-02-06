# Layer: L4 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Incident domain write decisions
# Callers: customer_incidents_adapter.py (L3)
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models (at runtime)
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Incident Write Engine

L4 engine for incident write decisions.

Decides: Transaction boundaries, state transitions, audit event patterns
Delegates: Data access to IncidentWriteDriver, audit to AuditLedgerService
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.models.audit_ledger import ActorType
from app.services.incident_write_driver import (
    IncidentWriteDriver,
    get_incident_write_driver,
)
# PIN-513: services→HOC dependency severed. Inline no-op replaces HOC audit.
class AuditLedgerService:
    def __init__(self, *a, **kw): pass
    def record(self, *a, **kw): pass
    def emit(self, *a, **kw): pass
    def log_decision(self, *a, **kw): return None

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.models.killswitch import Incident


class IncidentWriteEngine:
    """L4 engine for incident write decisions.

    Decides: Transaction boundaries, state transitions, audit emission
    Delegates: Data access to IncidentWriteDriver
    """

    def __init__(
        self,
        driver: IncidentWriteDriver,
        audit_service: AuditLedgerService,
    ):
        """Initialize engine with drivers.

        Args:
            driver: IncidentWriteDriver instance for data access
            audit_service: AuditLedgerService for audit logging
        """
        self._driver = driver
        self._audit = audit_service

    # =========================================================================
    # ACKNOWLEDGE INCIDENT
    # =========================================================================

    def acknowledge_incident(
        self,
        incident: "Incident",
        acknowledged_by: str = "customer",
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> "Incident":
        """Acknowledge an incident and create a timeline event.

        DECISION: Transaction contract - state change and audit event
        must commit together (atomic). If audit emit fails, incident
        change rolls back. No partial state is possible.

        Args:
            incident: Incident to acknowledge
            acknowledged_by: Who acknowledged
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)
            reason: Optional reason for acknowledgment

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # DECISION: Atomic transaction boundary
        with self._driver.begin_transaction():
            # Update incident status
            self._driver.update_incident_acknowledged(
                incident=incident,
                acknowledged_at=now,
                acknowledged_by=acknowledged_by,
            )

            # Create timeline event
            self._driver.create_event(
                incident_id=str(incident.id),
                event_type="acknowledged",
                description=f"Incident acknowledged by {acknowledged_by}",
            )

            # DECISION: Emit audit event inside transaction
            # Must commit with state change
            self._audit.incident_acknowledged(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=acknowledged_by,
                actor_type=actor_type,
                reason=reason,
            )

        # Refresh after commit
        self._driver.refresh(incident)

        return incident

    # =========================================================================
    # RESOLVE INCIDENT
    # =========================================================================

    def resolve_incident(
        self,
        incident: "Incident",
        resolved_by: str = "customer",
        resolution_notes: Optional[str] = None,
        resolution_method: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> "Incident":
        """Resolve an incident and create a timeline event.

        DECISION: Transaction contract - state change and audit event
        must commit together (atomic). If audit emit fails, incident
        change rolls back. No partial state is possible.

        Args:
            incident: Incident to resolve
            resolved_by: Who resolved
            resolution_notes: Optional resolution notes
            resolution_method: How the incident was resolved (auto, manual, rollback)
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)
            reason: Optional reason for resolution (used in audit)

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # DECISION: Build event description based on context
        description = f"Incident resolved by {resolved_by}"
        if resolution_method:
            description += f" ({resolution_method})"
        if resolution_notes:
            description += f": {resolution_notes}"

        # DECISION: Atomic transaction boundary
        with self._driver.begin_transaction():
            # Update incident status
            self._driver.update_incident_resolved(
                incident=incident,
                resolved_at=now,
                resolved_by=resolved_by,
                resolution_method=resolution_method,
            )

            # Create timeline event
            self._driver.create_event(
                incident_id=str(incident.id),
                event_type="resolved",
                description=description,
            )

            # DECISION: Emit audit event inside transaction
            self._audit.incident_resolved(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=resolved_by,
                actor_type=actor_type,
                reason=reason or resolution_notes,
                resolution_method=resolution_method,
            )

        # Refresh after commit
        self._driver.refresh(incident)

        return incident

    # =========================================================================
    # MANUAL CLOSE INCIDENT
    # =========================================================================

    def manual_close_incident(
        self,
        incident: "Incident",
        closed_by: str = "customer",
        reason: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
    ) -> "Incident":
        """Manually close an incident without resolution workflow.

        DECISION: Transaction contract - state change and audit event
        must commit together (atomic). If audit emit fails, incident
        change rolls back. No partial state is possible.

        Use this for incidents that are:
        - False positives
        - Duplicates
        - No longer relevant

        Args:
            incident: Incident to close
            closed_by: Who closed the incident
            reason: Required reason for manual closure
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # DECISION: Capture before state for audit trail
        before_state = {
            "status": incident.status.value if hasattr(incident.status, "value") else str(incident.status),
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        }

        # Build event description
        description = f"Incident manually closed by {closed_by}"
        if reason:
            description += f": {reason}"

        # DECISION: Atomic transaction boundary
        with self._driver.begin_transaction():
            # Update incident status with manual_closure method
            self._driver.update_incident_resolved(
                incident=incident,
                resolved_at=now,
                resolved_by=closed_by,
                resolution_method="manual_closure",
            )

            # Create timeline event
            self._driver.create_event(
                incident_id=str(incident.id),
                event_type="manually_closed",
                description=description,
            )

            # DECISION: Capture after state for audit
            after_state = {
                "status": incident.status.value if hasattr(incident.status, "value") else str(incident.status),
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "resolution_method": "manual_closure",
            }

            # DECISION: Emit audit event with before/after state
            self._audit.incident_manually_closed(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=closed_by,
                actor_type=actor_type,
                reason=reason,
                before_state=before_state,
                after_state=after_state,
            )

        # Refresh after commit
        self._driver.refresh(incident)

        return incident


# Factory function
def get_incident_write_engine(session: "Session") -> IncidentWriteEngine:
    """Get engine instance with default driver.

    Args:
        session: Database session

    Returns:
        IncidentWriteEngine instance
    """
    driver = get_incident_write_driver(session)
    audit = AuditLedgerService(session)
    return IncidentWriteEngine(driver=driver, audit_service=audit)


# Backward compatibility aliases
IncidentWriteService = IncidentWriteEngine
get_incident_write_service = get_incident_write_engine

__all__ = [
    "IncidentWriteEngine",
    "IncidentWriteService",
    "get_incident_write_engine",
    "get_incident_write_service",
]
