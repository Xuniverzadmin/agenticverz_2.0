# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Role: Overview domain drivers - pure data access
# Location: hoc/cus/overview/L6_drivers/
# Reference: PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md

"""
Overview L6 Drivers

Pure data access for overview domain aggregation.
"""

from app.hoc.cus.overview.L6_drivers.overview_facade_driver import (
    OverviewFacadeDriver,
)

__all__ = [
    "OverviewFacadeDriver",
]
