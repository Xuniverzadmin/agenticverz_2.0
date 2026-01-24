# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access drivers for general controls domain
# Reference: PHASE2_EXTRACTION_PROTOCOL.md

"""
general/controls / drivers

L6 drivers for guard/killswitch data access operations.
All drivers are pure data access - no business logic.
"""

from app.hoc.cus.general.controls.drivers.guard_write_driver import (
    GuardWriteDriver,
    get_guard_write_driver,
)

__all__ = [
    "GuardWriteDriver",
    "get_guard_write_driver",
]
