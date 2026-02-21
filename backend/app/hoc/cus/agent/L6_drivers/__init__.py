# capability_id: CAP-008
# Layer: L6 — Domain Drivers
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Agent domain L6 drivers package
# Reference: PIN-284 (Platform Monitoring System), PIN-484 (HOC Topology V2.0.0)
# artifact_class: CODE

"""
Agent L6 Drivers

Database access layer for agent domain operations.

Drivers:
    platform_driver.py - Platform health and capability queries
    routing_driver.py - Routing decisions and agent strategy operations
"""

from app.hoc.cus.agent.L6_drivers.platform_driver import (
    PlatformDriver,
    get_platform_driver,
)
from app.hoc.cus.agent.L6_drivers.routing_driver import (
    RoutingDriver,
    get_routing_driver,
)

__all__ = [
    "PlatformDriver",
    "get_platform_driver",
    "RoutingDriver",
    "get_routing_driver",
]
