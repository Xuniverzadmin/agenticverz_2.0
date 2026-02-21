# capability_id: CAP-012
# Layer: L2 — API
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: async
# Role: Lifecycle enforcement gate (middleware + dependencies)
# Callers: FastAPI middleware, route dependencies, tests
# Allowed Imports: L4 (operation_registry), L5_schemas (lifecycle enums/state)
# Forbidden Imports: L1, L6, L7
# Reference: PIN-401 Track A (Production Wiring), HOC_LAYER_TOPOLOGY_V2.0.0

"""
Lifecycle Gate Middleware

Enforces TenantLifecycleState at request boundaries.

DESIGN RULES:
- Pure wiring - no new states or logic
- Reads canonical persisted state (Tenant.status) via async DB context
- Respects OFFBOARD invariants

ENFORCEMENT SURFACE:
- SDK execution paths (/api/v1/runs, /api/v1/runtime/*)
- Write operations (POST, PUT, PATCH, DELETE)

EXEMPT PATHS:
- Health/metrics
- Auth endpoints
- Founder endpoints (self-service)
- Docs
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Set

from fastapi import HTTPException, Request

from app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums import (
    TenantLifecycleStatus,
    normalize_status,
)
from app.hoc.cus.account.L5_schemas.tenant_lifecycle_state import (
    TenantLifecycleState,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_async_session_context,
    sql_text,
)

logger = logging.getLogger(__name__)

# Map L5 string status → L4 IntEnum state
_STATUS_TO_INT_STATE = {
    TenantLifecycleStatus.ACTIVE: TenantLifecycleState.ACTIVE,
    TenantLifecycleStatus.SUSPENDED: TenantLifecycleState.SUSPENDED,
    TenantLifecycleStatus.TERMINATED: TenantLifecycleState.TERMINATED,
    TenantLifecycleStatus.ARCHIVED: TenantLifecycleState.ARCHIVED,
}


async def _fetch_lifecycle_state(tenant_id: str) -> TenantLifecycleState:
    """Fetch lifecycle state from DB (Tenant.status), returns IntEnum."""
    async with get_async_session_context() as session:
        row = (
            await session.execute(
                sql_text("SELECT status FROM tenants WHERE id = :tid"),
                {"tid": tenant_id},
            )
        ).mappings().first()
        if row is None:
            return TenantLifecycleState.ACTIVE
        status = normalize_status(row["status"])
        return _STATUS_TO_INT_STATE.get(status, TenantLifecycleState.ACTIVE)


# Paths exempt from lifecycle enforcement
EXEMPT_PREFIXES: tuple[str, ...] = (
    "/health",
    "/metrics",
    "/api/v1/auth/",
    "/fdr/",
    "/docs",
    "/openapi.json",
    "/redoc",
)

# SDK execution paths (require ACTIVE)
SDK_PATHS: tuple[str, ...] = (
    "/api/v1/runs",
    "/api/v1/runtime/",
    "/api/v1/skills/",
    "/api/v1/agents/",
)

# Write methods
WRITE_METHODS: Set[str] = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass
class LifecycleContext:
    """
    Lifecycle context for a request.

    Attributes:
        tenant_id: The tenant identifier
        state: Current lifecycle state
        allows_sdk: Whether SDK execution is allowed
        allows_writes: Whether writes are allowed
        allows_reads: Whether reads are allowed
        is_exempt: Whether this path is exempt from enforcement
    """

    tenant_id: str
    state: TenantLifecycleState
    allows_sdk: bool
    allows_writes: bool
    allows_reads: bool
    is_exempt: bool


def is_exempt_path(path: str) -> bool:
    """Check if path is exempt from lifecycle enforcement."""
    return path.startswith(EXEMPT_PREFIXES)


def is_sdk_path(path: str) -> bool:
    """Check if path requires SDK execution permission."""
    return any(path.startswith(prefix) for prefix in SDK_PATHS)


class LifecycleGate:
    """
    Lifecycle enforcement gate.

    Can be used as FastAPI middleware or dependency.

    Usage as middleware:
        app.add_middleware(LifecycleGate)

    Usage as dependency:
        @router.post("/runs")
        async def create_run(
            lifecycle: LifecycleContext = Depends(require_active_lifecycle),
        ):
            ...
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        path = request.url.path

        if is_exempt_path(path):
            await self.app(scope, receive, send)
            return

        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            await self.app(scope, receive, send)
            return

        state = await _fetch_lifecycle_state(tenant_id)

        if is_sdk_path(path) and not state.allows_sdk_execution():
            logger.warning(
                "lifecycle_gate_blocked_sdk",
                extra={"tenant_id": tenant_id, "state": state.name, "path": path},
            )
            await self._send_error(
                send,
                403,
                {
                    "error": "lifecycle_blocked",
                    "state": state.name,
                    "message": f"SDK execution not allowed in {state.name} state",
                    "allowed_states": ["ACTIVE"],
                },
            )
            return

        method = request.method.upper()
        if method in WRITE_METHODS and not state.allows_writes():
            logger.warning(
                "lifecycle_gate_blocked_write",
                extra={"tenant_id": tenant_id, "state": state.name, "method": method, "path": path},
            )
            await self._send_error(
                send,
                403,
                {
                    "error": "lifecycle_blocked",
                    "state": state.name,
                    "message": f"Write operations not allowed in {state.name} state",
                    "allowed_states": ["ACTIVE"],
                },
            )
            return

        if method == "GET" and not state.allows_reads():
            logger.warning(
                "lifecycle_gate_blocked_read",
                extra={"tenant_id": tenant_id, "state": state.name, "path": path},
            )
            await self._send_error(
                send,
                403,
                {
                    "error": "lifecycle_blocked",
                    "state": state.name,
                    "message": f"Read operations not allowed in {state.name} state",
                    "allowed_states": ["ACTIVE", "SUSPENDED"],
                },
            )
            return

        await self.app(scope, receive, send)

    async def _send_error(self, send, status_code: int, body: dict):
        import json

        body_bytes = json.dumps(body).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body_bytes)).encode()],
                ],
            }
        )
        await send({"type": "http.response.body", "body": body_bytes})


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================


async def check_lifecycle(request: Request) -> LifecycleContext:
    """FastAPI dependency: evaluate lifecycle state for this request."""
    path = request.url.path

    if is_exempt_path(path):
        return LifecycleContext(
            tenant_id="",
            state=TenantLifecycleState.ACTIVE,
            allows_sdk=True,
            allows_writes=True,
            allows_reads=True,
            is_exempt=True,
        )

    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        return LifecycleContext(
            tenant_id="unknown",
            state=TenantLifecycleState.ACTIVE,
            allows_sdk=True,
            allows_writes=True,
            allows_reads=True,
            is_exempt=False,
        )

    state = await _fetch_lifecycle_state(tenant_id)

    return LifecycleContext(
        tenant_id=tenant_id,
        state=state,
        allows_sdk=state.allows_sdk_execution(),
        allows_writes=state.allows_writes(),
        allows_reads=state.allows_reads(),
        is_exempt=False,
    )


async def require_active_lifecycle(request: Request) -> LifecycleContext:
    """FastAPI dependency: require tenant lifecycle to permit this request."""
    ctx = await check_lifecycle(request)
    if ctx.is_exempt:
        return ctx

    method = request.method.upper()
    path = request.url.path

    if is_sdk_path(path) and not ctx.allows_sdk:
        raise HTTPException(status_code=403, detail="SDK execution not allowed for tenant lifecycle state")

    if method in WRITE_METHODS and not ctx.allows_writes:
        raise HTTPException(status_code=403, detail="Write not allowed for tenant lifecycle state")

    if method == "GET" and not ctx.allows_reads:
        raise HTTPException(status_code=403, detail="Read not allowed for tenant lifecycle state")

    return ctx


async def require_sdk_execution(request: Request) -> LifecycleContext:
    """FastAPI dependency: require SDK execution permission."""
    ctx = await check_lifecycle(request)
    if ctx.is_exempt:
        return ctx
    if not ctx.allows_sdk:
        raise HTTPException(status_code=403, detail="SDK execution not allowed for tenant lifecycle state")
    return ctx


__all__ = [
    "LifecycleGate",
    "LifecycleContext",
    "check_lifecycle",
    "require_active_lifecycle",
    "require_sdk_execution",
    "is_exempt_path",
    "is_sdk_path",
    "EXEMPT_PREFIXES",
    "SDK_PATHS",
]

