# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: sync
# Role: Phase-7 Protection FastAPI dependencies
# Callers: API endpoints, middleware
# Allowed Imports: L4 (protection, billing, auth.onboarding_state)
# Forbidden Imports: L1, L5, L6
# Reference: PIN-399 Phase-7 (Abuse & Protection Layer)

"""
Phase-7 Protection Dependencies — FastAPI Integration

Provides dependencies for protection checks in API endpoints.

ENFORCEMENT SURFACE:
    Protection applies to:
    - SDK endpoints
    - Runtime execution paths
    - Background workers

    Protection does NOT apply to:
    - Onboarding endpoints
    - Auth endpoints
    - Founder endpoints
    - Internal ops endpoints

DESIGN INVARIANTS:
- ABUSE-001: Protection does not affect onboarding, roles, or billing state
- ABUSE-002: All enforcement outcomes are explicit (no silent failure)
- ABUSE-003: Anomaly detection never blocks user traffic
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Request, HTTPException
import logging

from app.protection.decisions import (
    Decision,
    ProtectionResult,
    AnomalySignal,
    allow,
)
from app.protection.provider import get_protection_provider
from app.auth.onboarding_state import OnboardingState

logger = logging.getLogger(__name__)


# Endpoints that are exempt from protection (per Phase-7 design)
EXEMPT_PREFIXES = (
    "/health",
    "/metrics",
    "/api/v1/auth/",
    "/founder/",
    "/docs",
    "/openapi.json",
    "/redoc",
)


@dataclass
class ProtectionContext:
    """
    Protection context for a request.

    Attributes:
        tenant_id: The tenant identifier
        endpoint: The endpoint being accessed
        operation: The operation being performed
        result: Result of protection checks
        anomaly: Anomaly signal if detected (non-blocking)
        is_exempt: True if endpoint is exempt from protection
    """

    tenant_id: str
    endpoint: str
    operation: str
    result: ProtectionResult
    anomaly: Optional[AnomalySignal]
    is_exempt: bool


def is_exempt_endpoint(path: str) -> bool:
    """Check if an endpoint is exempt from protection."""
    return path.startswith(EXEMPT_PREFIXES)


def check_protection(request: Request) -> ProtectionContext:
    """
    FastAPI dependency: Run protection checks for current request.

    Returns ProtectionContext with decision and any anomaly signals.
    Does NOT raise exceptions - caller decides how to handle.

    Usage:
        @router.post("/runs")
        async def create_run(
            protection: ProtectionContext = Depends(check_protection),
        ):
            if protection.result.decision == Decision.REJECT:
                raise HTTPException(status_code=429, detail=protection.result.to_error_response())
            ...
    """
    # Get path
    path = request.url.path

    # Check exemption
    if is_exempt_endpoint(path):
        return ProtectionContext(
            tenant_id="",
            endpoint=path,
            operation="exempt",
            result=allow(),
            anomaly=None,
            is_exempt=True,
        )

    # Get tenant_id from request state
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        # No tenant context - allow (auth should handle this)
        return ProtectionContext(
            tenant_id="unknown",
            endpoint=path,
            operation="unknown",
            result=allow(),
            anomaly=None,
            is_exempt=False,
        )

    # Check onboarding state - protection doesn't apply before COMPLETE
    onboarding_state = getattr(request.state, "onboarding_state", None)
    if onboarding_state is None or onboarding_state != OnboardingState.COMPLETE:
        # Per ABUSE-001: Protection does not affect onboarding
        return ProtectionContext(
            tenant_id=tenant_id,
            endpoint=path,
            operation="onboarding",
            result=allow(),
            anomaly=None,
            is_exempt=True,  # Treat as exempt during onboarding
        )

    # Determine operation type from method
    method = request.method.upper()
    operation = "read" if method == "GET" else "write"

    # Run protection checks
    provider = get_protection_provider()
    result = provider.check_all(tenant_id, path, operation)

    # Check for anomaly (non-blocking per ABUSE-003)
    anomaly = provider.detect_anomaly(tenant_id)
    if anomaly:
        logger.warning(
            f"Anomaly detected for tenant {tenant_id}: "
            f"{anomaly.observed}/{anomaly.baseline} ({anomaly.window})"
        )

    return ProtectionContext(
        tenant_id=tenant_id,
        endpoint=path,
        operation=operation,
        result=result,
        anomaly=anomaly,
        is_exempt=False,
    )


def require_protection_allow(request: Request) -> ProtectionContext:
    """
    FastAPI dependency: Require protection checks to pass.

    Raises HTTP 429 if protection rejects the request.
    Raises HTTP 503 if protection throttles (with Retry-After header).

    Usage:
        @router.post("/runs")
        async def create_run(
            protection: ProtectionContext = Depends(require_protection_allow),
        ):
            # Protection checks passed
            ...
    """
    context = check_protection(request)

    if context.result.decision == Decision.REJECT:
        error_response = context.result.to_error_response()
        raise HTTPException(
            status_code=429,
            detail=error_response,
            headers={"Retry-After": str((context.result.retry_after_ms or 60000) // 1000)},
        )

    if context.result.decision == Decision.THROTTLE:
        error_response = context.result.to_error_response()
        raise HTTPException(
            status_code=503,
            detail=error_response,
            headers={"Retry-After": str((context.result.retry_after_ms or 1000) // 1000)},
        )

    return context


def emit_protection_event(context: ProtectionContext) -> dict:
    """
    Emit a structured protection event for observability.

    Per Phase-7 design Section 7.9, all rejections emit structured events.

    Returns:
        Event dict suitable for logging/dashboards
    """
    event = {
        "event": "abuse_protection_triggered",
        "tenant_id": context.tenant_id,
        "dimension": context.result.dimension,
        "action": context.result.decision.value,
        "endpoint": context.endpoint,
        "operation": context.operation,
    }

    if context.anomaly:
        event["anomaly"] = context.anomaly.to_signal_response()

    return event


__all__ = [
    "ProtectionContext",
    "check_protection",
    "require_protection_allow",
    "emit_protection_event",
    "is_exempt_endpoint",
    "EXEMPT_PREFIXES",
]
