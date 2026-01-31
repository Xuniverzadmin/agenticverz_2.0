# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (called by L4 handlers after L5 engine execution)
#   Execution: sync + async
# Role: Audit coordinator — cross-domain audit dispatch (C4 Loop Model)
# Callers: incidents_handler.py, policies_handler.py (L4 handlers)
# Allowed Imports: hoc_spine, hoc.cus.logs (lazy — L4 can import L5/L6)
# Forbidden Imports: L1, L2
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model)
# artifact_class: CODE

"""
Audit Coordinator (C4 — Loop Model)

Mediates audit event dispatch between domain engines and the logs domain.
Replaces direct L5→L5/L6 imports (incidents→logs, policies→logs).

Pattern:
    L4 handler → L5 engine (returns audit metadata) → L4 handler → AuditCoordinator → logs L5/L6

The coordinator lazy-imports logs audit services internally.
This is legal because L4 can import L5/L6.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.hoc_spine.orchestrator.coordinators.audit")


class AuditCoordinator:
    """
    Cross-domain audit dispatch coordinator.

    Provides sync and async methods for recording audit events,
    delegating to the logs domain's audit ledger services.
    """

    def record_incident_event(
        self,
        session: Any,
        event_method: str,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: Any = None,
        reason: Optional[str] = None,
        **extra_kwargs: Any,
    ) -> Any:
        """
        Record a sync incident audit event.

        Args:
            session: Sync SQLAlchemy Session
            event_method: Method name on AuditLedgerService
                (incident_acknowledged, incident_resolved, incident_manually_closed)
            tenant_id: Tenant identifier
            incident_id: Incident identifier
            actor_id: Who performed the action
            actor_type: ActorType enum value
            reason: Reason for the action
            **extra_kwargs: Additional kwargs passed to the audit method
        """
        from app.hoc.cus.logs.L5_engines.audit_ledger_service import (
            AuditLedgerService,
        )

        audit = AuditLedgerService(session)
        method = getattr(audit, event_method, None)
        if method is None:
            logger.error(
                "audit_coordinator.unknown_method",
                extra={"event_method": event_method},
            )
            return None

        return method(
            tenant_id=tenant_id,
            incident_id=incident_id,
            actor_id=actor_id,
            actor_type=actor_type,
            reason=reason,
            **extra_kwargs,
        )

    async def record_policy_event(
        self,
        session: Any,
        event_method: str,
        tenant_id: str,
        entity_id: str,
        actor_id: Optional[str] = None,
        actor_type: Any = None,
        reason: Optional[str] = None,
        **extra_kwargs: Any,
    ) -> Any:
        """
        Record an async policy audit event.

        Args:
            session: Async SQLAlchemy Session
            event_method: Method name on AuditLedgerServiceAsync
                (limit_created, limit_updated, policy_rule_created,
                 policy_rule_modified, policy_rule_retired,
                 policy_proposal_approved, policy_proposal_rejected)
            tenant_id: Tenant identifier
            entity_id: Entity identifier (limit_id, rule_id, proposal_id)
            actor_id: Who performed the action
            actor_type: ActorType enum value
            reason: Reason for the action
            **extra_kwargs: Additional kwargs passed to the audit method
        """
        from app.hoc.cus.logs.L6_drivers.audit_ledger_service_async import (
            AuditLedgerServiceAsync,
        )

        audit = AuditLedgerServiceAsync(session)
        method = getattr(audit, event_method, None)
        if method is None:
            logger.error(
                "audit_coordinator.unknown_async_method",
                extra={"event_method": event_method},
            )
            return None

        # Determine the entity_id parameter name from the method name
        if "limit" in event_method:
            entity_kwarg = "limit_id"
        elif "rule" in event_method:
            entity_kwarg = "rule_id"
        elif "proposal" in event_method:
            entity_kwarg = "proposal_id"
        else:
            entity_kwarg = "entity_id"

        return await method(
            tenant_id=tenant_id,
            **{entity_kwarg: entity_id},
            actor_id=actor_id,
            actor_type=actor_type,
            reason=reason,
            **extra_kwargs,
        )


# =============================================================================
# Module Singleton
# =============================================================================

_audit_coordinator_instance: Optional[AuditCoordinator] = None


def get_audit_coordinator() -> AuditCoordinator:
    """Get the audit coordinator singleton."""
    global _audit_coordinator_instance
    if _audit_coordinator_instance is None:
        _audit_coordinator_instance = AuditCoordinator()
    return _audit_coordinator_instance
