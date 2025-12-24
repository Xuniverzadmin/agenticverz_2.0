"""M29 Category 7: Legacy Route Handlers

This module returns 410 Gone for deprecated routes that have been
permanently removed from the API. This prevents:
1. Confusion when legacy paths silently fail
2. Clients relying on deprecated endpoints
3. Security issues from undocumented paths

Forbidden paths return 410 Gone with explanatory message.
These are NOT redirects (301/302) - the old paths are dead.

PIN-153: M29 Category 7 - Redirect Expiry & Cleanup
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Legacy (Deprecated)"])


# =============================================================================
# 410 Gone Response Helper
# =============================================================================


def gone_response(
    path: str,
    reason: str,
    replacement: str | None = None,
) -> JSONResponse:
    """Return a 410 Gone response with migration guidance.

    Args:
        path: The deprecated path that was accessed
        reason: Why this path was removed
        replacement: Optional new path to use instead
    """
    content = {
        "error": "GONE",
        "status": 410,
        "path": path,
        "message": f"This endpoint has been permanently removed: {reason}",
    }

    if replacement:
        content["migration"] = {
            "new_path": replacement,
            "note": "Please update your client to use the new endpoint.",
        }

    return JSONResponse(status_code=410, content=content)


# =============================================================================
# /dashboard - Removed (M29)
# =============================================================================


@router.get("/dashboard")
@router.post("/dashboard")
@router.put("/dashboard")
@router.delete("/dashboard")
async def legacy_dashboard():
    """410 Gone - Dashboard is not available for MVP customers.

    The dashboard has been replaced by domain-specific consoles:
    - /guard/* for customers (trust + control)
    - /ops/* for founders (intelligence + action)
    """
    return gone_response(
        path="/dashboard",
        reason="Dashboard consolidated into domain-specific consoles",
        replacement="/guard/overview (for customers) or /ops/overview (for founders)",
    )


# =============================================================================
# /operator/* - Merged into /ops/* (M28/PIN-145)
# =============================================================================


@router.get("/operator")
@router.post("/operator")
@router.put("/operator")
@router.delete("/operator")
@router.get("/operator/{path:path}")
@router.post("/operator/{path:path}")
@router.put("/operator/{path:path}")
@router.delete("/operator/{path:path}")
async def legacy_operator(path: str = ""):
    """410 Gone - Operator console merged into /ops/*.

    The /operator/* routes were merged into /ops/* in M28 (PIN-145).
    Common migrations:
    - /operator/status → /ops/overview
    - /operator/tenants → /ops/customers
    - /operator/incidents → /ops/incidents
    """
    return gone_response(
        path=f"/operator/{path}" if path else "/operator",
        reason="Merged into Founder Ops Console (M28/PIN-145)",
        replacement="/ops/*",
    )


# =============================================================================
# /demo/* - Simulation Tools Removed (M28/PIN-145)
# =============================================================================


@router.get("/demo")
@router.post("/demo")
@router.get("/demo/{path:path}")
@router.post("/demo/{path:path}")
async def legacy_demo(path: str = ""):
    """410 Gone - Demo/simulation endpoints removed.

    Demo and simulation endpoints were removed in M28:
    - /demo/simulate-incident removed
    - /v1/demo/* removed

    For testing, use the canary deployment or staging environment.
    """
    return gone_response(
        path=f"/demo/{path}" if path else "/demo",
        reason="Simulation tools removed from production (M28/PIN-145)",
        replacement=None,
    )


# =============================================================================
# /simulation/* - Pre-M29 Testing Tools Removed
# =============================================================================


@router.get("/simulation")
@router.post("/simulation")
@router.get("/simulation/{path:path}")
@router.post("/simulation/{path:path}")
async def legacy_simulation(path: str = ""):
    """410 Gone - Simulation endpoints removed.

    Pre-M29 simulation tools have been removed from production.
    For cost simulation, use /cost/simulate with proper auth.
    """
    return gone_response(
        path=f"/simulation/{path}" if path else "/simulation",
        reason="Simulation tools consolidated or removed (M29)",
        replacement="/cost/simulate (for cost estimation)",
    )


# =============================================================================
# /api/v1/operator/* - Legacy API Path (M28/PIN-145)
# =============================================================================


@router.get("/api/v1/operator")
@router.get("/api/v1/operator/{path:path}")
@router.post("/api/v1/operator/{path:path}")
async def legacy_api_operator(path: str = ""):
    """410 Gone - /api/v1/operator/* merged into /ops/*.

    The versioned operator API has been merged into the /ops/* domain.
    """
    return gone_response(
        path=f"/api/v1/operator/{path}" if path else "/api/v1/operator",
        reason="Merged into Founder Ops Console (M28/PIN-145)",
        replacement="/ops/*",
    )
