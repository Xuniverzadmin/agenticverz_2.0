# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Route authentication plane declarations (HUMAN / MACHINE / BOTH)
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Callers: auth/route_planes.py (shim), gateway_middleware
# Allowed Imports: auth.contexts (AuthPlane enum only)
# Forbidden Imports: FastAPI, Starlette, DB
# Reference: CAP-006, PIN-306

"""
Route Plane Policy (Canonical)

Defines which authentication plane (HUMAN, MACHINE, or BOTH)
is allowed for each route pattern. All paths use canonical
(unversioned) form.

INVARIANTS:
1. Worker endpoints NEVER accept JWT (workers can't impersonate users)
2. Admin endpoints NEVER accept API keys (prevent privilege escalation)
3. Mismatch = 403 Forbidden (not 401)

This module contains NO framework imports — it is pure policy data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.auth.contexts import AuthPlane


class PlaneRequirement(str, Enum):
    """What authentication plane(s) a route accepts."""

    HUMAN_ONLY = "human_only"   # Only JWT auth
    MACHINE_ONLY = "machine_only"  # Only API key auth
    BOTH = "both"               # Either JWT or API key


@dataclass
class RoutePlaneRule:
    """A rule mapping route pattern to plane requirement."""

    pattern: str  # Prefix pattern (e.g., "/workers/")
    requirement: PlaneRequirement
    description: str
    regex: Optional[re.Pattern] = None

    def __post_init__(self):
        """Compile regex pattern for more complex matching."""
        if "*" in self.pattern or "(" in self.pattern:
            regex_pattern = self.pattern.replace("*", ".*")
            self.regex = re.compile(f"^{regex_pattern}")

    def matches(self, path: str) -> bool:
        """Check if this rule matches the given path."""
        if self.regex:
            return self.regex.match(path) is not None
        return path.startswith(self.pattern)


# =============================================================================
# Route Plane Rules (Canonical Paths)
# =============================================================================
# Order matters: more specific rules come first.
# All paths are canonical (no /api/v1 prefix).

ROUTE_PLANE_RULES: list[RoutePlaneRule] = [
    # -----------------------------------------------------------------------
    # MACHINE ONLY — Agent/Worker endpoints
    # -----------------------------------------------------------------------
    RoutePlaneRule(
        pattern="/workers/",
        requirement=PlaneRequirement.MACHINE_ONLY,
        description="Worker execution - machine only",
    ),
    RoutePlaneRule(
        pattern="/agent/execute",
        requirement=PlaneRequirement.MACHINE_ONLY,
        description="Agent execution - machine only",
    ),
    RoutePlaneRule(
        pattern="/sdk/",
        requirement=PlaneRequirement.MACHINE_ONLY,
        description="SDK endpoints - machine only",
    ),
    # -----------------------------------------------------------------------
    # HUMAN ONLY — Admin/Founder endpoints
    # -----------------------------------------------------------------------
    RoutePlaneRule(
        pattern="/admin/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Admin endpoints - human only",
    ),
    RoutePlaneRule(
        pattern="/fdr/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Founder endpoints - human only",
    ),
    RoutePlaneRule(
        pattern="/ops/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Ops console - human only",
    ),
    RoutePlaneRule(
        pattern="/billing/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Billing endpoints - human only",
    ),
    RoutePlaneRule(
        pattern="/tenants/*/members",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Team member management - human only",
    ),
    # -----------------------------------------------------------------------
    # BOTH — General API endpoints
    # -----------------------------------------------------------------------
    RoutePlaneRule(
        pattern="/runs",
        requirement=PlaneRequirement.BOTH,
        description="Run management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/agents",
        requirement=PlaneRequirement.BOTH,
        description="Agent management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/workflows",
        requirement=PlaneRequirement.BOTH,
        description="Workflow management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/runtime/",
        requirement=PlaneRequirement.BOTH,
        description="Runtime APIs - human or machine",
    ),
    RoutePlaneRule(
        pattern="/skills",
        requirement=PlaneRequirement.BOTH,
        description="Skill management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/incidents",
        requirement=PlaneRequirement.BOTH,
        description="Incident viewing - human or machine",
    ),
    RoutePlaneRule(
        pattern="/policies",
        requirement=PlaneRequirement.BOTH,
        description="Policy management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/logs",
        requirement=PlaneRequirement.BOTH,
        description="Log viewing - human or machine",
    ),
    # Default catch-all for any /api/ prefix (legacy 410 routes)
    RoutePlaneRule(
        pattern="/api/",
        requirement=PlaneRequirement.BOTH,
        description="Default API - human or machine",
    ),
]


def get_plane_requirement(path: str) -> PlaneRequirement:
    """
    Get the plane requirement for a path.

    Returns PlaneRequirement.BOTH if no rule matches.
    """
    for rule in ROUTE_PLANE_RULES:
        if rule.matches(path):
            return rule.requirement
    return PlaneRequirement.BOTH


def check_plane_match(
    path: str,
    actual_plane: AuthPlane,
) -> tuple[bool, Optional[str]]:
    """
    Check if the actual auth plane matches the route requirement.

    Returns (is_allowed, error_message).
    """
    requirement = get_plane_requirement(path)

    if requirement == PlaneRequirement.BOTH:
        return True, None

    if requirement == PlaneRequirement.HUMAN_ONLY:
        if actual_plane == AuthPlane.HUMAN:
            return True, None
        return False, "This endpoint requires human (JWT) authentication"

    if requirement == PlaneRequirement.MACHINE_ONLY:
        if actual_plane == AuthPlane.MACHINE:
            return True, None
        return False, "This endpoint requires machine (API key) authentication"

    return True, None


def is_worker_path(path: str) -> bool:
    """Check if path is a worker execution path (MACHINE_ONLY)."""
    return path.startswith("/workers/") or path.startswith("/agent/execute")


def is_admin_path(path: str) -> bool:
    """Check if path is an admin/founder path (HUMAN_ONLY)."""
    return (
        path.startswith("/admin/")
        or path.startswith("/fdr/")
        or path.startswith("/ops/")
    )


async def enforce_plane_requirement(
    path: str,
    actual_plane: AuthPlane,
) -> Optional[dict]:
    """
    Enforce plane requirement for a path.

    Returns None if allowed, or error dict if blocked.
    """
    is_allowed, error_msg = check_plane_match(path, actual_plane)

    if is_allowed:
        return None

    return {
        "error": "plane_mismatch",
        "message": error_msg,
        "required": get_plane_requirement(path).value,
        "actual": actual_plane.value,
    }


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
