# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for incidents capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Incidents Bridge (PIN-510)

Domain-scoped capability accessor for incidents domain.
Returns capability-satisfying objects bound to caller's session.

Rules:
- Max 5 capability methods (CI check 19)
- Never accepts session in constructor
- Lazy imports only
- Only L4 handlers/coordinators may use this
"""


class IncidentsBridge:
    """Capabilities for incidents domain. Max 5 methods."""

    def incident_read_capability(self, session):
        """Return IncidentReadCapability for the given session."""
        from app.hoc.cus.incidents.L5_engines.incident_read_engine import IncidentReadService
        return IncidentReadService(session)

    def incident_write_capability(self, session):
        """Return IncidentWriteCapability for the given session."""
        from app.hoc.cus.incidents.L5_engines.incident_write_engine import IncidentWriteService
        return IncidentWriteService(session)

    def lessons_capability(self, session):
        """Return LessonsQueryCapability for the given session."""
        from app.hoc.cus.incidents.L6_drivers.lessons_driver import LessonsDriver
        return LessonsDriver(session)

    def export_capability(self):
        """Return ExportEngine wired to L6 ExportBundleDriver.

        PIN-511 Phase 2.1: Export business logic via L5 engine + L6 driver.
        """
        from app.hoc.cus.incidents.L6_drivers.export_bundle_driver import get_export_bundle_driver
        from app.hoc.cus.incidents.L5_engines.export_engine import ExportEngine
        driver = get_export_bundle_driver()
        return ExportEngine(driver)

    def incidents_for_run_capability(self, session):
        """Return IncidentReadService for run-scoped queries (PIN-519)."""
        from app.hoc.cus.incidents.L6_drivers.incident_run_read_driver import (
            IncidentRunReadDriver,
        )
        return IncidentRunReadDriver(session)


# Singleton
_instance = None


def get_incidents_bridge() -> IncidentsBridge:
    """Get the singleton IncidentsBridge instance."""
    global _instance
    if _instance is None:
        _instance = IncidentsBridge()
    return _instance


# =============================================================================
# PIN-511 Option B: IncidentDriver wiring (L4 composes L5 + L6)
# =============================================================================

_driver_instance = None


def get_incident_driver(db_url=None):
    """Get the singleton IncidentDriver, wired with IncidentEngine via Protocol.

    PIN-511 Option B: L4 is the only layer that sees both L5 and L6.
    This factory creates the L5 engine, injects it into the L6 driver
    via IncidentDecisionPort, and returns the composed driver.

    Args:
        db_url: Optional database URL override

    Returns:
        IncidentDriver instance (L6) backed by IncidentEngine (L5)
    """
    global _driver_instance
    if _driver_instance is None:
        from app.hoc.cus.incidents.L5_engines.incident_engine import IncidentEngine
        from app.hoc.cus.incidents.L6_drivers.incident_driver import IncidentDriver

        def _emit_incident_ack(run_id: str, result_id: str | None, error: str | None) -> None:
            # L4 owns hoc_spine dependencies; L6 drivers must not import hoc_spine.
            from uuid import UUID

            from app.hoc.cus.hoc_spine.schemas.rac_models import (
                AuditAction,
                AuditDomain,
                DomainAck,
            )
            from app.hoc.cus.hoc_spine.services.audit_store import get_audit_store

            ack = DomainAck(
                run_id=UUID(run_id),
                domain=AuditDomain.INCIDENTS,
                action=AuditAction.CREATE_INCIDENT,
                result_id=result_id,
                error=error,
            )

            store = get_audit_store()
            store.add_ack(UUID(run_id), ack)

        engine = IncidentEngine(db_url=db_url)
        _driver_instance = IncidentDriver(decision_port=engine, ack_emitter=_emit_incident_ack)
    return _driver_instance


# Backward compatibility alias
get_incident_facade = get_incident_driver


# =============================================================================
# INCIDENTS ENGINE BRIDGE (extends IncidentsBridge to avoid 5-method limit)
# =============================================================================


class IncidentsEngineBridge:
    """Extended capabilities for incidents domain engines. Max 5 methods."""

    def recovery_rule_engine_capability(self):
        """
        Return recovery rule engine for error classification (PIN-L2-PURITY).

        Used by recovery.py for evaluating recovery rules on failures.
        """
        from app.hoc.cus.incidents.L5_engines import recovery_rule_engine

        return recovery_rule_engine

    def evidence_recorder_capability(self):
        """
        Return lessons coordinator for evidence recording (PIN-520).

        Used to inject into IncidentEngine for cross-domain evidence recording.
        L5 incident_engine.get_incident_engine(evidence_recorder=...) should receive this.
        """
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.lessons_coordinator import (
            get_lessons_coordinator,
        )

        return get_lessons_coordinator()


_engine_bridge_instance = None


def get_incidents_engine_bridge() -> IncidentsEngineBridge:
    """Get the singleton IncidentsEngineBridge instance."""
    global _engine_bridge_instance
    if _engine_bridge_instance is None:
        _engine_bridge_instance = IncidentsEngineBridge()
    return _engine_bridge_instance


__all__ = [
    "IncidentsBridge",
    "get_incidents_bridge",
    "get_incident_driver",
    "get_incident_facade",
    "IncidentsEngineBridge",
    "get_incidents_engine_bridge",
]
