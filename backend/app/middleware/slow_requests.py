# Layer: L2 — Product APIs (Middleware)
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: sync (request-response)
# Role: Diagnostic middleware for slow request detection
# Callers: FastAPI middleware stack
# Allowed Imports: stdlib only
# Forbidden Imports: app.*, domain logic
# Reference: PIN-443 (Cold-Start Observability)

"""
Slow Request Diagnostic Middleware (PIN-443)

Logs warnings for requests exceeding a configurable threshold.
Used to diagnose VPS hangs (e.g., /openapi.json cold generation).

This is OBSERVABILITY ONLY:
- No impact on request semantics
- No impact on auth, RBAC, or Evidence Plane
- Zero cost when disabled
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("slow_requests")


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs requests exceeding a time threshold.

    Enabled via: ENABLE_SLOW_REQUEST_LOGS=true
    Default threshold: 500ms (configurable)
    """

    def __init__(self, app, threshold_ms: int = 500):
        super().__init__(app)
        self.threshold_ms = threshold_ms

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        if duration_ms > self.threshold_ms:
            logger.warning(
                "slow_request",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": self.threshold_ms,
                },
            )

        return response
