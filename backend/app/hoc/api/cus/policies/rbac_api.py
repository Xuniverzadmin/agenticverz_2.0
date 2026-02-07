# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: RBAC Management API endpoints
# Callers: Customer Console, Admin tools
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: PIN-310
"""
RBAC Management API

Provides endpoints for managing RBAC policies:
- GET /rbac/info - Get current policy info
- POST /rbac/reload - Hot-reload policies from file
- GET /rbac/matrix - Get current permission matrix
- GET /rbac/audit - Query audit logs

Requires RBAC permission: rbac:read or rbac:reload

NOTE (PIN-310): Authorization now routes through M28 via authorization_choke.py.
Policy introspection (info, matrix, reload) still uses rbac_engine for admin functions.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.auth.authorization_choke import check_permission_request

# L4 session + registry for dispatching to L6 drivers (PIN-L2-PURITY)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_sync_session_dep,
    OperationContext,
)
# L4 bridge for account domain (PIN-L2-PURITY)
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges import (
    get_account_bridge,
)
from app.schemas.response import wrap_dict


def _get_rbac_engine():
    """Get rbac_engine via L4 bridge to maintain L2 purity."""
    # L4 bridge for RBAC engine (PIN-L2-PURITY)
    return get_account_bridge().rbac_engine_capability()

logger = logging.getLogger("nova.api.rbac")

router = APIRouter(prefix="/rbac", tags=["rbac"])


# =============================================================================
# Response Schemas
# =============================================================================


class PolicyInfoResponse(BaseModel):
    """Current policy information."""

    version: str
    hash: str
    loaded_at: str
    roles: List[str]
    resources: List[str]
    enforce_mode: bool
    fail_open: bool


class ReloadResponse(BaseModel):
    """Policy reload response."""

    success: bool
    message: str
    previous_hash: str
    new_hash: str
    timestamp: str


class AuditEntry(BaseModel):
    """Single audit log entry."""

    id: int
    ts: datetime
    subject: str
    resource: str
    action: str
    allowed: bool
    reason: Optional[str]
    roles: Optional[List[str]]
    path: Optional[str]
    method: Optional[str]
    tenant_id: Optional[str]
    latency_ms: Optional[float]


class AuditResponse(BaseModel):
    """Audit log query response."""

    entries: List[AuditEntry]
    total: int
    limit: int
    offset: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/info", response_model=PolicyInfoResponse)
async def get_policy_info(request: Request):
    """
    Get current RBAC policy information.

    Returns version, hash, loaded timestamp, roles, and resources.

    Requires RBAC permission: rbac:read
    """
    import os

    # Check permission (routed through M28 via authorization_choke)
    decision = await check_permission_request("rbac", "read", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    engine = _get_rbac_engine()
    info = engine.get_policy_info()

    return PolicyInfoResponse(
        version=info.get("version", "unknown"),
        hash=info.get("hash", "unknown"),
        loaded_at=info.get("loaded_at", datetime.now(timezone.utc).isoformat()),
        roles=info.get("roles", []),
        resources=info.get("resources", []),
        enforce_mode=os.getenv("RBAC_ENFORCE", "false").lower() == "true",
        fail_open=os.getenv("RBAC_FAIL_OPEN", "false").lower() == "true",
    )


@router.post("/reload", response_model=ReloadResponse)
async def reload_policies(request: Request):
    """
    Hot-reload RBAC policies from file.

    Reloads the policy file and updates the in-memory policy matrix.
    Returns the previous and new policy hashes for verification.

    Requires RBAC permission: rbac:reload
    """
    # Check permission (routed through M28 via authorization_choke)
    decision = await check_permission_request("rbac", "reload", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    engine = _get_rbac_engine()

    # Get current hash before reload
    info_before = engine.get_policy_info()
    previous_hash = info_before.get("hash", "unknown")

    # Reload
    success, message = engine.reload_policy()

    # Get new hash
    info_after = engine.get_policy_info()
    new_hash = info_after.get("hash", "unknown")

    logger.info(
        "rbac_policy_reload",
        extra={
            "success": success,
            "previous_hash": previous_hash,
            "new_hash": new_hash,
            "by": ",".join(decision.roles) if decision.roles else "unknown",
        },
    )

    if not success:
        raise HTTPException(status_code=500, detail={"error": "reload_failed", "message": message})

    return ReloadResponse(
        success=success,
        message=message,
        previous_hash=previous_hash,
        new_hash=new_hash,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/matrix")
async def get_permission_matrix(request: Request) -> Dict[str, Any]:
    """
    Get current permission matrix.

    Returns the full role->resource->actions mapping.

    Requires RBAC permission: rbac:read
    """
    # Check permission (routed through M28 via authorization_choke)
    decision = await check_permission_request("rbac", "read", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    engine = _get_rbac_engine()

    # Access internal policy (not ideal but needed for introspection)
    with engine._policy_lock:
        if engine._policy:
            return wrap_dict({"version": engine._policy.version, "hash": engine._policy.hash, "matrix": engine._policy.matrix})
        return wrap_dict({"version": "default", "hash": "default", "matrix": engine._default_matrix})


@router.get("/audit", response_model=AuditResponse)
async def query_audit_logs(
    request: Request,
    resource: Optional[str] = Query(default=None, description="Filter by resource"),
    action: Optional[str] = Query(default=None, description="Filter by action"),
    allowed: Optional[bool] = Query(default=None, description="Filter by decision"),
    subject: Optional[str] = Query(default=None, description="Filter by subject"),
    tenant_id: Optional[str] = Query(default=None, description="Filter by tenant"),
    since: Optional[datetime] = Query(default=None, description="Filter since timestamp"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_sync_session_dep),
):
    """
    Query RBAC audit logs.

    Supports filtering by resource, action, decision, subject, tenant, and time.

    Requires RBAC permission: rbac:read
    """
    # Check permission (routed through M28 via authorization_choke)
    decision = await check_permission_request("rbac", "read", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        # L2 purity: dispatch to L6 driver via L4 registry
        registry = get_operation_registry()
        result = await registry.execute(
            "rbac.audit",
            OperationContext(
                session=None,  # Async session not used; sync session passed via params
                tenant_id="",  # System-wide operation
                params={
                    "method": "query_audit_logs",
                    "sync_session": db,
                    "resource": resource,
                    "action": action,
                    "allowed": allowed,
                    "subject": subject,
                    "tenant_id": tenant_id,
                    "since": since,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        # Transform L6 DTOs to API response
        entries = [AuditEntry(**e) for e in result.data["entries"]]
        return AuditResponse(
            entries=entries,
            total=result.data["total"],
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/cleanup")
async def cleanup_audit_logs(
    request: Request, retention_days: int = Query(default=90, ge=1, le=365), db=Depends(get_sync_session_dep)
):
    """
    Clean up old audit logs.

    Deletes audit entries older than retention_days.

    Requires RBAC permission: rbac:reload (admin action)
    """
    # Check permission (routed through M28 via authorization_choke)
    decision = await check_permission_request("rbac", "reload", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        # L2 purity: dispatch to L6 driver via L4 registry
        # L2 purity: L4 handler owns commit/rollback (L6 driver does not commit)
        registry = get_operation_registry()
        result = await registry.execute(
            "rbac.audit",
            OperationContext(
                session=None,  # Async session not used; sync session passed via params
                tenant_id="",  # System-wide operation
                params={
                    "method": "cleanup_audit_logs",
                    "sync_session": db,
                    "retention_days": retention_days,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        deleted_count = result.data["deleted_count"]

        logger.info(
            "rbac_audit_cleanup",
            extra={
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "by": ",".join(decision.roles) if decision.roles else "unknown",
            },
        )

        return wrap_dict({
            "deleted_count": deleted_count,
            "retention_days": retention_days,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
