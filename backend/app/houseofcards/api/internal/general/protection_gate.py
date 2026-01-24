# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Protection enforcement gate
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: sync
# Callers: FastAPI middleware, route dependencies
# Allowed Imports: L4 (protection provider, decisions)
# Forbidden Imports: L1, L5, L6
# Reference: PIN-401 Track A (Production Wiring)


"""
Protection Gate Middleware

Applies AbuseProtectionProvider decisions at request boundaries.

DESIGN RULES:
- Pure wiring - no new protection logic
- Calls existing provider.check_all()
- Non-blocking for anomaly signals (ABUSE-003)
- Respects all ABUSE invariants

ENFORCEMENT SURFACE:
- SDK execution paths
- Runtime endpoints
- Write operations

EXEMPT PATHS:
- Health/metrics
- Auth endpoints
- Founder endpoints
- Docs
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Request, HTTPException
import logging

from app.protection.decisions import Decision, ProtectionResult, AnomalySignal
from app.protection.provider import get_protection_provider

logger = logging.getLogger(__name__)


# Paths exempt from protection enforcement
EXEMPT_PREFIXES: tuple[str, ...] = (
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
        operation: The operation (read/write)
        result: Protection check result
        anomaly: Anomaly signal if detected (non-blocking)
        is_exempt: Whether this path is exempt
    """

    tenant_id: str
    endpoint: str
    operation: str
    result: ProtectionResult
    anomaly: Optional[AnomalySignal]
    is_exempt: bool


def is_exempt_path(path: str) -> bool:
    """Check if path is exempt from protection."""
    return path.startswith(EXEMPT_PREFIXES)


class ProtectionGate:
    """
    Protection enforcement gate (ASGI middleware).

    Applies rate limits and abuse protection at the middleware level.

    Usage:
        app.add_middleware(ProtectionGate)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        path = request.url.path

        # Check exemption
        if is_exempt_path(path):
            await self.app(scope, receive, send)
            return

        # Get tenant_id from request state
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            await self.app(scope, receive, send)
            return

        # Determine operation type
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

        # Handle decisions
        if result.decision == Decision.REJECT:
            logger.warning(
                f"Protection gate rejected request for tenant {tenant_id} "
                f"(dimension={result.dimension})"
            )
            response = result.to_error_response()
            retry_after = (result.retry_after_ms or 60000) // 1000
            await self._send_error(send, 429, response, retry_after)
            return

        if result.decision == Decision.THROTTLE:
            logger.info(
                f"Protection gate throttling tenant {tenant_id} "
                f"(dimension={result.dimension})"
            )
            response = result.to_error_response()
            retry_after = (result.retry_after_ms or 1000) // 1000
            await self._send_error(send, 503, response, retry_after)
            return

        # ALLOW or WARN - proceed
        if result.decision == Decision.WARN:
            logger.info(
                f"Protection warning for tenant {tenant_id}: {result.message}"
            )

        await self.app(scope, receive, send)

    async def _send_error(
        self, send, status_code: int, body: dict, retry_after: int
    ):
        """Send JSON error response with Retry-After header."""
        import json

        body_bytes = json.dumps(body).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body_bytes)).encode()],
                [b"retry-after", str(retry_after).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================


def check_protection(request: Request) -> ProtectionContext:
    """
    FastAPI dependency: Run protection checks for current request.

    Returns ProtectionContext with decision and any anomaly signals.
    Does NOT raise - caller decides how to handle.
    """
    from app.protection.decisions import allow

    path = request.url.path

    # Check exemption
    if is_exempt_path(path):
        return ProtectionContext(
            tenant_id="",
            endpoint=path,
            operation="exempt",
            result=allow(),
            anomaly=None,
            is_exempt=True,
        )

    # Get tenant_id
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        return ProtectionContext(
            tenant_id="unknown",
            endpoint=path,
            operation="unknown",
            result=allow(),
            anomaly=None,
            is_exempt=False,
        )

    # Determine operation
    method = request.method.upper()
    operation = "read" if method == "GET" else "write"

    # Run protection checks
    provider = get_protection_provider()
    result = provider.check_all(tenant_id, path, operation)

    # Check for anomaly (non-blocking)
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

    Raises HTTP 429 if rejected.
    Raises HTTP 503 if throttled.
    """
    context = check_protection(request)

    if context.is_exempt:
        return context

    if context.result.decision == Decision.REJECT:
        raise HTTPException(
            status_code=429,
            detail=context.result.to_error_response(),
            headers={
                "Retry-After": str((context.result.retry_after_ms or 60000) // 1000)
            },
        )

    if context.result.decision == Decision.THROTTLE:
        raise HTTPException(
            status_code=503,
            detail=context.result.to_error_response(),
            headers={
                "Retry-After": str((context.result.retry_after_ms or 1000) // 1000)
            },
        )

    return context


__all__ = [
    "ProtectionGate",
    "ProtectionContext",
    "check_protection",
    "require_protection_allow",
    "is_exempt_path",
    "EXEMPT_PREFIXES",
]
