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
        from app.hoc.cus.incidents.L5_engines.incident_read_engine import IncidentReadService
        return IncidentReadService(session)


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
        engine = IncidentEngine(db_url=db_url)
        _driver_instance = IncidentDriver(decision_port=engine)
    return _driver_instance


# Backward compatibility alias
get_incident_facade = get_incident_driver


__all__ = [
    "IncidentsBridge",
    "get_incidents_bridge",
    "get_incident_driver",
    "get_incident_facade",
]
