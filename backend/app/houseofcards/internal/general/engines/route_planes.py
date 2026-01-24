# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Route authentication plane declarations and enforcement
# Callers: gateway_middleware
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Route Plane Declarations

Defines which authentication plane (HUMAN, MACHINE, or BOTH)
is allowed for each route pattern.

DESIGN:
- Routes are matched by prefix patterns
- More specific patterns take precedence
- Worker/agent routes are MACHINE only
- Admin routes are HUMAN only
- Most API routes allow BOTH

INVARIANTS:
1. Worker endpoints NEVER accept JWT (workers can't impersonate users)
2. Admin endpoints NEVER accept API keys (prevent privilege escalation)
3. Mismatch = 403 Forbidden (not 401)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .contexts import AuthPlane


class PlaneRequirement(str, Enum):
    """What authentication plane(s) a route accepts."""

    HUMAN_ONLY = "human_only"  # Only JWT auth
    MACHINE_ONLY = "machine_only"  # Only API key auth
    BOTH = "both"  # Either JWT or API key


@dataclass
class RoutePlaneRule:
    """A rule mapping route pattern to plane requirement."""

    pattern: str  # Prefix pattern (e.g., "/api/v1/workers/")
    requirement: PlaneRequirement
    description: str
    regex: Optional[re.Pattern] = None

    def __post_init__(self):
        """Compile regex pattern for more complex matching."""
        if "*" in self.pattern or "(" in self.pattern:
            # Convert glob-style to regex
            regex_pattern = self.pattern.replace("*", ".*")
            self.regex = re.compile(f"^{regex_pattern}")

    def matches(self, path: str) -> bool:
        """Check if this rule matches the given path."""
        if self.regex:
            return self.regex.match(path) is not None
        return path.startswith(self.pattern)


# =============================================================================
# Route Plane Rules
# =============================================================================
# Order matters: more specific rules should come first

ROUTE_PLANE_RULES: list[RoutePlaneRule] = [
    # ---------------------------------------------------------------------
    # MACHINE ONLY - Agent/Worker endpoints
    # ---------------------------------------------------------------------
    RoutePlaneRule(
        pattern="/api/v1/workers/",
        requirement=PlaneRequirement.MACHINE_ONLY,
        description="Worker execution - machine only",
    ),
    RoutePlaneRule(
        pattern="/api/v1/agent/execute",
        requirement=PlaneRequirement.MACHINE_ONLY,
        description="Agent execution - machine only",
    ),
    RoutePlaneRule(
        pattern="/api/v1/sdk/",
        requirement=PlaneRequirement.MACHINE_ONLY,
        description="SDK endpoints - machine only",
    ),
    # ---------------------------------------------------------------------
    # HUMAN ONLY - Admin/Founder endpoints
    # ---------------------------------------------------------------------
    RoutePlaneRule(
        pattern="/api/v1/admin/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Admin endpoints - human only",
    ),
    RoutePlaneRule(
        pattern="/api/v1/founder/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Founder endpoints - human only",
    ),
    RoutePlaneRule(
        pattern="/api/v1/ops/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Ops console - human only",
    ),
    RoutePlaneRule(
        pattern="/api/v1/billing/",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Billing endpoints - human only",
    ),
    RoutePlaneRule(
        pattern="/api/v1/tenants/*/members",
        requirement=PlaneRequirement.HUMAN_ONLY,
        description="Team member management - human only",
    ),
    # ---------------------------------------------------------------------
    # BOTH - General API endpoints
    # ---------------------------------------------------------------------
    RoutePlaneRule(
        pattern="/api/v1/runs",
        requirement=PlaneRequirement.BOTH,
        description="Run management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/agents",
        requirement=PlaneRequirement.BOTH,
        description="Agent management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/workflows",
        requirement=PlaneRequirement.BOTH,
        description="Workflow management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/runtime/",
        requirement=PlaneRequirement.BOTH,
        description="Runtime APIs - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/skills",
        requirement=PlaneRequirement.BOTH,
        description="Skill management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/incidents",
        requirement=PlaneRequirement.BOTH,
        description="Incident viewing - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/policies",
        requirement=PlaneRequirement.BOTH,
        description="Policy management - human or machine",
    ),
    RoutePlaneRule(
        pattern="/api/v1/logs",
        requirement=PlaneRequirement.BOTH,
        description="Log viewing - human or machine",
    ),
    # Default catch-all (allow both by default)
    RoutePlaneRule(
        pattern="/api/",
        requirement=PlaneRequirement.BOTH,
        description="Default API - human or machine",
    ),
]


def get_plane_requirement(path: str) -> PlaneRequirement:
    """
    Get the plane requirement for a path.

    Args:
        path: The request path

    Returns:
        PlaneRequirement for the path (defaults to BOTH)
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

    Args:
        path: The request path
        actual_plane: The actual authentication plane

    Returns:
        Tuple of (is_allowed, error_message)
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
    """
    Check if path is a worker execution path.

    Worker paths MUST NOT use JWT authentication.
    """
    return path.startswith("/api/v1/workers/") or path.startswith("/api/v1/agent/execute")


def is_admin_path(path: str) -> bool:
    """
    Check if path is an admin/founder path.

    Admin paths MUST NOT use API key authentication.
    """
    return path.startswith("/api/v1/admin/") or path.startswith("/api/v1/founder/") or path.startswith("/api/v1/ops/")


# =============================================================================
# Route Plane Middleware Hook
# =============================================================================


async def enforce_plane_requirement(
    path: str,
    actual_plane: AuthPlane,
) -> Optional[dict]:
    """
    Enforce plane requirement for a path.

    Returns None if allowed, or error dict if blocked.

    Usage in middleware:
        error = await enforce_plane_requirement(path, context.plane)
        if error:
            return JSONResponse(status_code=403, content=error)
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
