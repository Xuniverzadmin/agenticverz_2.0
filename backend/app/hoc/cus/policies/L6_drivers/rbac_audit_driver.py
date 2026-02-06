# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: system.rbac_audit
#   Writes: system.rbac_audit (cleanup only)
# Database:
#   Scope: system (RBAC)
#   Models: raw SQL (system.rbac_audit table)
# Role: Data access driver for RBAC audit log operations
# Callers: L4 handler (policies_handler.py RbacAuditHandler)
# Allowed Imports: L6, L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-L2-PURITY, rbac_api.py L2 violation fix
# artifact_class: CODE

"""
RBAC Audit Driver (L6)

Pure data access layer for RBAC audit log operations.
Handles DB queries and cleanup for system.rbac_audit table.

Operations:
- query_audit_logs: Query audit entries with filters
- cleanup_audit_logs: Delete old audit entries (L4 owns commit)

Architecture:
    L2 (rbac_api.py) -> L4 (registry dispatch) -> L6 (this driver) -> Database
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session


# =============================================================================
# L6 DTOs (Raw data from database)
# =============================================================================


class AuditEntryDTO(BaseModel):
    """Raw audit entry data from database."""

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


class AuditQueryResultDTO(BaseModel):
    """Query result containing entries and total count."""

    entries: List[AuditEntryDTO]
    total: int


class AuditCleanupResultDTO(BaseModel):
    """Cleanup operation result."""

    deleted_count: int


# =============================================================================
# L6 Driver Class
# =============================================================================


class RbacAuditDriver:
    """
    L6 driver for RBAC audit log operations.

    Pure data access - no business logic.
    Handles DB queries and cleanup for RBAC audit logs.

    Transaction ownership:
    - query_audit_logs: Read-only, no commit needed
    - cleanup_audit_logs: NO COMMIT — L4 handler owns commit/rollback
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def query_audit_logs(
        self,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        allowed: Optional[bool] = None,
        subject: Optional[str] = None,
        tenant_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditQueryResultDTO:
        """
        Query RBAC audit logs with optional filters.

        Args:
            resource: Filter by resource
            action: Filter by action
            allowed: Filter by decision (allowed/denied)
            subject: Filter by subject
            tenant_id: Filter by tenant
            since: Filter entries since this timestamp
            limit: Maximum entries to return (1-1000)
            offset: Pagination offset

        Returns:
            AuditQueryResultDTO with entries and total count
        """
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
        count_result = self._session.execute(
            text(f"SELECT COUNT(*) FROM system.rbac_audit WHERE {where_sql}"),
            params,
        )
        total = count_result.scalar() or 0

        # Get entries
        result = self._session.execute(
            text(
                f"""
                SELECT id, ts, subject, resource, action, allowed, reason, roles,
                       path, method, tenant_id, latency_ms
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
                AuditEntryDTO(
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

        return AuditQueryResultDTO(entries=entries, total=total)

    def cleanup_audit_logs(self, retention_days: int) -> AuditCleanupResultDTO:
        """
        Clean up old audit logs.

        Deletes audit entries older than retention_days.
        L6 driver does NOT commit — L4 handler owns transaction boundary.

        Args:
            retention_days: Number of days to retain (1-365)

        Returns:
            AuditCleanupResultDTO with deleted count
        """
        result = self._session.execute(
            text("SELECT system.cleanup_rbac_audit(:days)"),
            {"days": retention_days},
        )
        deleted_count = result.scalar() or 0

        return AuditCleanupResultDTO(deleted_count=deleted_count)


# =============================================================================
# Factory Function
# =============================================================================


def get_rbac_audit_driver(session: Session) -> RbacAuditDriver:
    """
    Get RbacAuditDriver instance.

    Args:
        session: SQLModel session (sync)

    Returns:
        RbacAuditDriver instance
    """
    return RbacAuditDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "RbacAuditDriver",
    "get_rbac_audit_driver",
    # DTOs
    "AuditEntryDTO",
    "AuditQueryResultDTO",
    "AuditCleanupResultDTO",
]
