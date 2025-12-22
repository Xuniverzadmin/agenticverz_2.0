"""
RBAC Management API - M7 Implementation

Provides endpoints for managing RBAC policies:
- GET /api/v1/rbac/info - Get current policy info
- POST /api/v1/rbac/reload - Hot-reload policies from file
- GET /api/v1/rbac/matrix - Get current permission matrix
- GET /api/v1/rbac/audit - Query audit logs

Requires RBAC permission: rbac:read or rbac:reload
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text

from ..auth.rbac_engine import check_permission, get_rbac_engine
from ..db import get_session as get_db_session

logger = logging.getLogger("nova.api.rbac")

router = APIRouter(prefix="/api/v1/rbac", tags=["rbac"])


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

    # Check permission
    decision = check_permission("rbac", "read", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    engine = get_rbac_engine()
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
    # Check permission
    decision = check_permission("rbac", "reload", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    engine = get_rbac_engine()

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
    # Check permission
    decision = check_permission("rbac", "read", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    engine = get_rbac_engine()

    # Access internal policy (not ideal but needed for introspection)
    with engine._policy_lock:
        if engine._policy:
            return {"version": engine._policy.version, "hash": engine._policy.hash, "matrix": engine._policy.matrix}
        return {"version": "default", "hash": "default", "matrix": engine._default_matrix}


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
    db=Depends(get_db_session),
):
    """
    Query RBAC audit logs.

    Supports filtering by resource, action, decision, subject, tenant, and time.

    Requires RBAC permission: rbac:read
    """
    # Check permission
    decision = check_permission("rbac", "read", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        # Build query
        where_clauses = []
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if resource:
            where_clauses.append("resource = :resource")
            params["resource"] = resource

        if action:
            where_clauses.append("action = :action")
            params["action"] = action

        if allowed is not None:
            where_clauses.append("allowed = :allowed")
            params["allowed"] = allowed

        if subject:
            where_clauses.append("subject = :subject")
            params["subject"] = subject

        if tenant_id:
            where_clauses.append("tenant_id = :tenant_id")
            params["tenant_id"] = tenant_id

        if since:
            where_clauses.append("ts >= :since")
            params["since"] = since

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM system.rbac_audit WHERE {where_sql}"), params)
        total = count_result.scalar() or 0

        # Get entries
        result = db.execute(
            text(
                f"""
                SELECT id, ts, subject, resource, action, allowed, reason, roles, path, method, tenant_id, latency_ms
                FROM system.rbac_audit
                WHERE {where_sql}
                ORDER BY ts DESC
                LIMIT :limit OFFSET :offset
            """
            ),
            params,
        )

        entries = []
        for row in result:
            entries.append(
                AuditEntry(
                    id=row.id,
                    ts=row.ts,
                    subject=row.subject,
                    resource=row.resource,
                    action=row.action,
                    allowed=row.allowed,
                    reason=row.reason,
                    roles=row.roles,
                    path=row.path,
                    method=row.method,
                    tenant_id=row.tenant_id,
                    latency_ms=row.latency_ms,
                )
            )

        return AuditResponse(entries=entries, total=total, limit=limit, offset=offset)

    except Exception as e:
        logger.error(f"Error querying audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/cleanup")
async def cleanup_audit_logs(
    request: Request, retention_days: int = Query(default=90, ge=1, le=365), db=Depends(get_db_session)
):
    """
    Clean up old audit logs.

    Deletes audit entries older than retention_days.

    Requires RBAC permission: rbac:reload (admin action)
    """
    # Check permission
    decision = check_permission("rbac", "reload", request)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        result = db.execute(text("SELECT system.cleanup_rbac_audit(:days)"), {"days": retention_days})
        db.commit()
        deleted_count = result.scalar() or 0

        logger.info(
            "rbac_audit_cleanup",
            extra={
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "by": ",".join(decision.roles) if decision.roles else "unknown",
            },
        )

        return {
            "deleted_count": deleted_count,
            "retention_days": retention_days,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
