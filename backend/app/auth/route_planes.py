# Layer: L3 — Boundary Adapter (Shim)
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Re-export shim — policy lives in hoc_spine/authority/route_planes.py
# Callers: gateway_middleware
# Reference: CAP-006, PIN-306

"""
Route Plane Declarations — Shim

All policy is defined in app.hoc.cus.hoc_spine.authority.route_planes.
This module re-exports for backward compatibility.
"""

from app.hoc.cus.hoc_spine.authority.route_planes import (  # noqa: F401
    PlaneRequirement,
    RoutePlaneRule,
    ROUTE_PLANE_RULES,
    check_plane_match,
    enforce_plane_requirement,
    get_plane_requirement,
    is_admin_path,
    is_worker_path,
)

__all__ = [
    "PlaneRequirement",
    "RoutePlaneRule",
    "ROUTE_PLANE_RULES",
    "get_plane_requirement",
    "check_plane_match",
    "is_worker_path",
    "is_admin_path",
    "enforce_plane_requirement",
]
