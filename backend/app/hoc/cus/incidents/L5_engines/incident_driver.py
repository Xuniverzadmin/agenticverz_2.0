# Layer: L5 — TOMBSTONE
# AUDIENCE: INTERNAL
# Role: Tombstone re-export — incident_driver.py moved to L6_drivers (PIN-511 Phase 0.1)
# TOMBSTONE_EXPIRY: 2026-03-01
# Reference: PIN-511 Phase 0.1, Option B
# artifact_class: CODE
#
# This file is a transitional re-export. The actual implementation now lives at:
#   app/hoc/cus/incidents/L6_drivers/incident_driver.py
# The wiring factory lives at:
#   app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py
#
# All new code should import from the L6_drivers location (class) or bridge (factory).
# This tombstone will be removed after TOMBSTONE_EXPIRY or when zero dependents remain.

"""
TOMBSTONE: incident_driver.py moved to L6_drivers (PIN-511)

This re-export exists for backward compatibility during migration.
Import from app.hoc.cus.incidents.L6_drivers.incident_driver instead.
"""

# Tombstone re-export — class from L6, factory from L4 bridge
from app.hoc.cus.incidents.L6_drivers.incident_driver import (  # noqa: F401
    IncidentDriver,
    IncidentFacade,
)
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge import (  # noqa: F401
    get_incident_driver,
    get_incident_facade,
)

__all__ = [
    "IncidentDriver",
    "IncidentFacade",
    "get_incident_driver",
    "get_incident_facade",
]
