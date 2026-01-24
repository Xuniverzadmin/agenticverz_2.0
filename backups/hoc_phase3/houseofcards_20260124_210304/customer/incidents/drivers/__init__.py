# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access drivers for incidents domain
# Reference: PHASE2_EXTRACTION_PROTOCOL.md

"""
incidents / drivers

L6 drivers for incident data access operations.
All drivers are pure data access - no business logic.
"""

from app.houseofcards.customer.incidents.drivers.incident_read_driver import (
    IncidentReadDriver,
    get_incident_read_driver,
)
from app.houseofcards.customer.incidents.drivers.incident_write_driver import (
    IncidentWriteDriver,
    get_incident_write_driver,
)

__all__ = [
    "IncidentReadDriver",
    "get_incident_read_driver",
    "IncidentWriteDriver",
    "get_incident_write_driver",
]
