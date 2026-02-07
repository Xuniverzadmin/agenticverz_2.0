# Layer: L2a — Internal/SDK API (NOT domain authority)
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Trace storage, indexing, query, and determinism validation
# Authority: WRITE trace mismatch reports (via store abstraction)
# Callers: SDK, Replay system, Internal services
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1
# Reference: M8 Trace System
#
# GOVERNANCE NOTE (LOGS Domain V2):
# This is NOT the canonical LOGS domain facade.
# The canonical facade is /logs/* (logs.py).
# This file provides SDK-facing trace APIs for:
# - Trace ingestion from SDK
# - Replay verification
# - Determinism validation
# Console users should use /logs/llm-runs/* for log viewing.

"""
Trace Query API
M8 Deliverable: Trace storage, indexing, and query endpoints

Provides REST API for:
- Listing and searching traces
- Getting trace details
- Finding traces by root_hash (for replay verification)
- Comparing traces for determinism validation
- RBAC-protected access via JWT/OIDC
- PII redaction on storage
"""

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

# Use PostgreSQL store in production, SQLite for dev/test
USE_POSTGRES = os.getenv("USE_POSTGRES_TRACES", "false").lower() == "true"

if USE_POSTGRES:
    from app.traces.pg_store import PostgresTraceStore, get_postgres_trace_store

    TraceStoreType = PostgresTraceStore
else:
    from app.traces.store import SQLiteTraceStore

    TraceStoreType = SQLiteTraceStore

# JWT Authentication
from app.auth.jwt_auth import JWTAuthDependency, JWTConfig, TokenPayload
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_async_session_context,
    get_operation_registry,
    get_session_dep,
)
from app.schemas.response import wrap_dict
from app.traces.redact import redact_trace_data

# Import handler registration (ensures handlers are registered at import time)
from app.hoc.cus.hoc_spine.orchestrator.handlers.traces_handler import (
    register_traces_handlers,
)

# Register handlers at module load
register_traces_handlers()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traces", tags=["traces"])


# =============================================================================
# Auth/RBAC - JWT/OIDC Integration (M8 Production)
# =============================================================================


class User:
    """
    User model for RBAC - wraps JWT TokenPayload for backwards compatibility.
    """

    def __init__(
        self,
        user_id: str = "anonymous",
        tenant_id: str = "default",
        roles: List[str] = None,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles or ["developer"]

    def has_role(self, role: str) -> bool:
        return role in self.roles or "admin" in self.roles

    @classmethod
    def from_token(cls, token: TokenPayload) -> "User":
        """Create User from JWT token payload."""
        return cls(
            user_id=token.sub,
            tenant_id=token.tenant_id,
            roles=token.roles,
        )


# Create JWT auth dependency
_jwt_auth = JWTAuthDependency(JWTConfig())


async def get_current_user(request: Request, token: TokenPayload = Depends(_jwt_auth)) -> User:
    """
    Get current authenticated user from JWT token.

    Supports:
    - Bearer JWT tokens (OIDC/Keycloak)
    - X-API-Key header (legacy/backwards compatible)
    - Development tokens (dev:xxx prefix)
    """
    return User.from_token(token)


def require_role(user: User, role: str) -> bool:
    """Check if user has required role."""
    return user.has_role(role)


# =============================================================================
# Store Dependency
# =============================================================================

_trace_store: Optional[TraceStoreType] = None


def get_trace_store() -> TraceStoreType:
    """Get the trace store instance."""
    global _trace_store
    if _trace_store is None:
        if USE_POSTGRES:
            _trace_store = get_postgres_trace_store()
        else:
            _trace_store = SQLiteTraceStore()
    return _trace_store


# =============================================================================
# Response Models
# =============================================================================


class TraceSummaryResponse(BaseModel):
    """Trace summary for list views."""

    run_id: str
    correlation_id: str
    tenant_id: str
    agent_id: Optional[str] = None
    total_steps: int
    success_count: int
    failure_count: int
    total_cost_cents: float
    total_duration_ms: float
    started_at: str
    completed_at: Optional[str] = None
    status: str
    # v1.1 determinism fields
    seed: Optional[int] = None
    root_hash: Optional[str] = None


class TraceStepResponse(BaseModel):
    """Individual trace step."""

    step_index: int
    skill_name: str
    params: dict
    status: str
    outcome_category: str
    outcome_code: Optional[str] = None
    outcome_data: Optional[dict] = None
    cost_cents: float
    duration_ms: float
    retry_count: int
    timestamp: str
    # v1.1 idempotency fields
    idempotency_key: Optional[str] = None
    replay_behavior: str = "execute"
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None


class TraceDetailResponse(BaseModel):
    """Full trace with all steps."""

    run_id: str
    correlation_id: str
    tenant_id: str
    agent_id: Optional[str] = None
    plan: List[dict]
    steps: List[TraceStepResponse]
    started_at: str
    completed_at: Optional[str] = None
    status: str
    metadata: dict = Field(default_factory=dict)
    # v1.1 determinism fields
    seed: int = 42
    frozen_timestamp: Optional[str] = None
    root_hash: Optional[str] = None
    plan_hash: Optional[str] = None
    schema_version: str = "1.1"


class TraceListResponse(BaseModel):
    """Paginated trace list."""

    traces: List[TraceSummaryResponse]
    total: int
    limit: int
    offset: int


class TraceCompareResponse(BaseModel):
    """Result of comparing two traces."""

    match: bool
    trace1_root_hash: Optional[str]
    trace2_root_hash: Optional[str]
    differences: List[dict] = Field(default_factory=list)
    summary: str


class StoreTraceRequest(BaseModel):
    """Request to store a client-provided trace."""

    trace: dict
    overwrite: bool = False


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=TraceListResponse)
async def list_traces(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    root_hash: Optional[str] = Query(None, description="Filter by root hash"),
    plan_hash: Optional[str] = Query(None, description="Filter by plan hash"),
    seed: Optional[int] = Query(None, description="Filter by random seed"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO8601)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    List and search traces with optional filters.

    RBAC: Users can only see traces from their tenant unless admin.
    """
    # RBAC: Enforce tenant isolation
    if tenant_id and tenant_id != user.tenant_id and not user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Cannot access other tenant's traces")

    # Default to user's tenant if not admin
    if not tenant_id and not user.has_role("admin"):
        tenant_id = user.tenant_id

    traces = await store.search_traces(
        tenant_id=tenant_id,
        agent_id=agent_id,
        root_hash=root_hash,
        plan_hash=plan_hash,
        seed=seed,
        status=status,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    total = await store.get_trace_count(tenant_id)

    return TraceListResponse(
        traces=[
            TraceSummaryResponse(
                run_id=t.run_id,
                correlation_id=t.correlation_id,
                tenant_id=t.tenant_id,
                agent_id=t.agent_id,
                total_steps=t.total_steps,
                success_count=t.success_count,
                failure_count=t.failure_count,
                total_cost_cents=t.total_cost_cents,
                total_duration_ms=t.total_duration_ms,
                started_at=t.started_at.isoformat(),
                completed_at=t.completed_at.isoformat() if t.completed_at else None,
                status=t.status,
            )
            for t in traces
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=201)
async def store_trace(
    request: StoreTraceRequest,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Store a client-provided trace.

    Applies PII redaction before storage.
    """
    trace = request.trace

    # Validate required fields
    if not trace.get("run_id") and not trace.get("trace_id"):
        raise HTTPException(status_code=400, detail="trace must have run_id or trace_id")

    # Redact PII
    redacted_trace = redact_trace_data(trace)

    # Store using PostgreSQL if available
    if USE_POSTGRES:
        trace_id = await store.store_trace(
            trace=redacted_trace,
            tenant_id=user.tenant_id,
            stored_by=user.user_id,
            redact_pii=False,  # Already redacted
        )
    else:
        # SQLite path - start trace and record steps
        run_id = trace.get("run_id") or trace.get("trace_id")
        await store.start_trace(
            run_id=run_id,
            correlation_id=trace.get("correlation_id", run_id),
            tenant_id=user.tenant_id,
            agent_id=trace.get("agent_id"),
            plan=trace.get("plan", []),
        )
        trace_id = run_id

    return wrap_dict({
        "trace_id": trace_id,
        "root_hash": trace.get("root_hash"),
        "stored": True,
    })


# =============================================================================
# Static routes MUST come before parameter routes
# =============================================================================


@router.get("/mismatches")
async def list_all_mismatches(
    window: Optional[str] = Query(None, description="Time window (e.g., 24h, 7d)"),
    status: Optional[str] = Query(None, regex="^(open|resolved)$", description="Filter by status"),
    limit: int = Query(100, le=500, description="Max results"),
):
    """
    List all trace mismatches across the system.

    READ-ONLY endpoint for observability. No side effects.
    Returns mismatches with summary counts.

    Auth: OBSERVER-safe (SDSR compatible)
    """
    if not USE_POSTGRES:
        raise HTTPException(status_code=501, detail="Requires PostgreSQL store")

    registry = get_operation_registry()

    async with get_async_session_context() as session:
        result = await registry.execute(
            "traces.list_mismatches",
            OperationContext(
                session=session,
                tenant_id="system",  # System-wide query, not tenant-scoped
                params={
                    "window": window,
                    "status": status,
                    "limit": limit,
                },
            ),
        )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return wrap_dict(result.data)


@router.get("/{run_id}", response_model=TraceDetailResponse)
async def get_trace(
    run_id: str,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Get a complete trace by run ID.

    RBAC: Users can only access their tenant's traces.
    """
    # Get trace with tenant check for PostgreSQL
    if USE_POSTGRES:
        if user.has_role("admin"):
            trace = await store.get_trace(run_id)
        else:
            trace = await store.get_trace(run_id, tenant_id=user.tenant_id)
    else:
        trace = await store.get_trace(run_id)
        # Manual tenant check for SQLite
        if trace and trace.tenant_id != user.tenant_id and not user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Access denied")

    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {run_id} not found")

    return TraceDetailResponse(
        run_id=trace.run_id,
        correlation_id=trace.correlation_id,
        tenant_id=trace.tenant_id,
        agent_id=trace.agent_id,
        plan=trace.plan,
        steps=[
            TraceStepResponse(
                step_index=s.step_index,
                skill_name=s.skill_name,
                params=s.params,
                status=s.status.value,
                outcome_category=s.outcome_category,
                outcome_code=s.outcome_code,
                outcome_data=s.outcome_data,
                cost_cents=s.cost_cents,
                duration_ms=s.duration_ms,
                retry_count=s.retry_count,
                timestamp=s.timestamp.isoformat(),
            )
            for s in trace.steps
        ],
        started_at=trace.started_at.isoformat(),
        completed_at=trace.completed_at.isoformat() if trace.completed_at else None,
        status=trace.status,
        metadata=trace.metadata,
        seed=trace.seed,
        frozen_timestamp=trace.frozen_timestamp,
        root_hash=trace.root_hash,
    )


@router.get("/by-hash/{root_hash}", response_model=TraceDetailResponse)
async def get_trace_by_hash(
    root_hash: str,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Get a trace by its deterministic root hash.

    Useful for replay verification.
    """
    if USE_POSTGRES:
        if user.has_role("admin"):
            trace = await store.get_trace_by_root_hash(root_hash)
        else:
            trace = await store.get_trace_by_root_hash(root_hash, tenant_id=user.tenant_id)
    else:
        trace = await store.get_trace_by_root_hash(root_hash)
        if trace and trace.tenant_id != user.tenant_id and not user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Access denied")

    if not trace:
        raise HTTPException(status_code=404, detail=f"No trace found with root_hash {root_hash}")

    return TraceDetailResponse(
        run_id=trace.run_id,
        correlation_id=trace.correlation_id,
        tenant_id=trace.tenant_id,
        agent_id=trace.agent_id,
        plan=trace.plan,
        steps=[
            TraceStepResponse(
                step_index=s.step_index,
                skill_name=s.skill_name,
                params=s.params,
                status=s.status.value,
                outcome_category=s.outcome_category,
                outcome_code=s.outcome_code,
                outcome_data=s.outcome_data,
                cost_cents=s.cost_cents,
                duration_ms=s.duration_ms,
                retry_count=s.retry_count,
                timestamp=s.timestamp.isoformat(),
            )
            for s in trace.steps
        ],
        started_at=trace.started_at.isoformat(),
        completed_at=trace.completed_at.isoformat() if trace.completed_at else None,
        status=trace.status,
        metadata=trace.metadata,
        seed=trace.seed,
        frozen_timestamp=trace.frozen_timestamp,
        root_hash=trace.root_hash,
    )


@router.get("/compare/{run_id1}/{run_id2}", response_model=TraceCompareResponse)
async def compare_traces(
    run_id1: str,
    run_id2: str,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Compare two traces for deterministic equality.

    Compares root_hash and step hashes to verify replay parity.
    """
    trace1 = await store.get_trace(run_id1)
    trace2 = await store.get_trace(run_id2)

    if not trace1:
        raise HTTPException(status_code=404, detail=f"Trace {run_id1} not found")
    if not trace2:
        raise HTTPException(status_code=404, detail=f"Trace {run_id2} not found")

    # RBAC check
    if not user.has_role("admin"):
        if trace1.tenant_id != user.tenant_id or trace2.tenant_id != user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")

    differences = []

    # Compare root hashes
    if trace1.root_hash != trace2.root_hash:
        differences.append(
            {
                "field": "root_hash",
                "trace1": trace1.root_hash,
                "trace2": trace2.root_hash,
            }
        )

    # Compare seeds
    if trace1.seed != trace2.seed:
        differences.append(
            {
                "field": "seed",
                "trace1": trace1.seed,
                "trace2": trace2.seed,
            }
        )

    # Compare frozen timestamps
    if trace1.frozen_timestamp != trace2.frozen_timestamp:
        differences.append(
            {
                "field": "frozen_timestamp",
                "trace1": trace1.frozen_timestamp,
                "trace2": trace2.frozen_timestamp,
            }
        )

    # Compare step counts
    if len(trace1.steps) != len(trace2.steps):
        differences.append(
            {
                "field": "step_count",
                "trace1": len(trace1.steps),
                "trace2": len(trace2.steps),
            }
        )

    # Compare individual steps
    for i, (s1, s2) in enumerate(zip(trace1.steps, trace2.steps)):
        if s1.skill_name != s2.skill_name:
            differences.append(
                {
                    "field": f"step[{i}].skill_name",
                    "trace1": s1.skill_name,
                    "trace2": s2.skill_name,
                }
            )
        if s1.outcome_category != s2.outcome_category:
            differences.append(
                {
                    "field": f"step[{i}].outcome_category",
                    "trace1": s1.outcome_category,
                    "trace2": s2.outcome_category,
                }
            )

    match = len(differences) == 0

    if match:
        summary = "Traces are deterministically identical"
    else:
        fields = [d["field"] for d in differences[:3]]
        summary = f"Traces differ in {len(differences)} field(s): {', '.join(fields)}"
        if len(differences) > 3:
            summary += f" and {len(differences) - 3} more"

    return TraceCompareResponse(
        match=match,
        trace1_root_hash=trace1.root_hash,
        trace2_root_hash=trace2.root_hash,
        differences=differences,
        summary=summary,
    )


@router.delete("/{run_id}")
async def delete_trace(
    run_id: str,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Delete a trace by run ID.

    RBAC: Requires admin or operator role.
    """
    if not user.has_role("admin") and not user.has_role("operator"):
        raise HTTPException(status_code=403, detail="Requires admin or operator role")

    if USE_POSTGRES:
        deleted = await store.delete_trace(run_id)
    else:
        deleted = await store.delete_trace(run_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Trace {run_id} not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/cleanup")
async def cleanup_old_traces(
    days: int = Query(30, ge=1, le=365, description="Delete traces older than N days"),
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Delete traces older than specified number of days.

    RBAC: Requires admin role.
    """
    if not user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Requires admin role")

    count = await store.cleanup_old_traces(days)
    return wrap_dict({
        "deleted_count": count,
        "retention_days": days,
    })


# =============================================================================
# Idempotency Check Endpoint
# =============================================================================


@router.get("/idempotency/{idempotency_key}")
async def check_idempotency(
    idempotency_key: str,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Check if an idempotency key has been executed.

    Returns execution status and output if found.
    """
    if not USE_POSTGRES:
        raise HTTPException(status_code=501, detail="Idempotency check requires PostgreSQL store")

    result = await store.check_idempotency_key(idempotency_key, user.tenant_id)

    if result:
        return wrap_dict({
            "executed": True,
            "trace_id": result["trace_id"],
            "step_index": result["step_index"],
            "status": result["status"],
            "output_hash": result["output_hash"],
        })
    else:
        return wrap_dict({
            "executed": False,
        })


# =============================================================================
# Replay Mismatch Reporting (M8)
# =============================================================================


class MismatchReport(BaseModel):
    """Report a replay mismatch for operator review."""

    step_index: int = Field(..., description="Index of the mismatched step")
    reason: str = Field(..., description="Reason for mismatch (output_mismatch, hash_mismatch, etc.)")
    expected_hash: Optional[str] = Field(None, description="Expected output hash")
    actual_hash: Optional[str] = Field(None, description="Actual output hash")
    details: dict = Field(default_factory=dict, description="Additional details")


class MismatchResponse(BaseModel):
    """Response after reporting a mismatch."""

    mismatch_id: str
    trace_id: str
    status: str
    notified: str
    issue_url: Optional[str] = None


# NOTE: Static routes MUST come before parameter routes
@router.post("/mismatches/bulk-report")
async def bulk_report_mismatches(
    mismatch_ids: List[str] = Query(..., description="List of mismatch IDs to link"),
    github_issue: bool = Query(True, description="Create a GitHub issue for all"),
    user: User = Depends(get_current_user),
):
    """
    Create a single GitHub issue for multiple mismatches.

    Useful when a replay causes multiple step mismatches that should be tracked together.

    RBAC: Requires admin or operator role.
    """
    if not user.has_role("admin") and not user.has_role("operator"):
        raise HTTPException(status_code=403, detail="Requires admin or operator role")

    if not USE_POSTGRES:
        raise HTTPException(status_code=501, detail="Requires PostgreSQL store")

    registry = get_operation_registry()

    async with get_async_session_context() as session:
        result = await registry.execute(
            "traces.bulk_report_mismatches",
            OperationContext(
                session=session,
                tenant_id=user.tenant_id,
                params={
                    "mismatch_ids": mismatch_ids,
                    "user_id": user.user_id,
                    "github_issue": github_issue,
                },
            ),
        )

    if not result.success:
        if result.error_code == "NO_MISMATCHES_FOUND":
            raise HTTPException(status_code=404, detail="No mismatches found")
        raise HTTPException(status_code=500, detail=result.error)

    return wrap_dict(result.data)


# Parameter route MUST come after static routes
@router.post("/{trace_id}/mismatch", response_model=MismatchResponse, status_code=201)
async def report_mismatch(
    trace_id: str,
    payload: MismatchReport,
    store: TraceStoreType = Depends(get_trace_store),
    user: User = Depends(get_current_user),
):
    """
    Report a replay mismatch for operator review.

    This endpoint:
    1. Records the mismatch in the database
    2. Optionally creates a GitHub issue or sends a Slack notification
    3. Returns the mismatch ID for tracking

    RBAC: Requires authenticated user. Only allows reporting mismatches for user's tenant.
    """
    if not USE_POSTGRES:
        # SQLite path - use store directly (no mismatch support)
        raise HTTPException(status_code=501, detail="Requires PostgreSQL store")

    registry = get_operation_registry()

    async with get_async_session_context() as session:
        result = await registry.execute(
            "traces.report_mismatch",
            OperationContext(
                session=session,
                tenant_id=user.tenant_id,
                params={
                    "trace_id": trace_id,
                    "step_index": payload.step_index,
                    "reason": payload.reason,
                    "expected_hash": payload.expected_hash,
                    "actual_hash": payload.actual_hash,
                    "details": payload.details,
                    "user_id": user.user_id,
                    "is_admin": user.has_role("admin"),
                },
            ),
        )

    if not result.success:
        if result.error_code == "TRACE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        if result.error_code == "ACCESS_DENIED":
            raise HTTPException(status_code=403, detail="Cannot report mismatch for other tenant's trace")
        raise HTTPException(status_code=500, detail=result.error)

    return MismatchResponse(
        mismatch_id=result.data["mismatch_id"],
        trace_id=result.data["trace_id"],
        status=result.data["status"],
        notified=result.data["notified"],
        issue_url=result.data.get("issue_url"),
    )


@router.get("/{trace_id}/mismatches")
async def list_trace_mismatches(
    trace_id: str,
    user: User = Depends(get_current_user),
):
    """
    List all mismatches reported for a trace.
    """
    if not USE_POSTGRES:
        raise HTTPException(status_code=501, detail="Requires PostgreSQL store")

    registry = get_operation_registry()

    async with get_async_session_context() as session:
        result = await registry.execute(
            "traces.list_trace_mismatches",
            OperationContext(
                session=session,
                tenant_id=user.tenant_id,
                params={
                    "trace_id": trace_id,
                    "is_admin": user.has_role("admin"),
                },
            ),
        )

    if not result.success:
        if result.error_code == "TRACE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        if result.error_code == "ACCESS_DENIED":
            raise HTTPException(status_code=403, detail="Access denied")
        raise HTTPException(status_code=500, detail=result.error)

    return wrap_dict(result.data)


@router.post("/{trace_id}/mismatches/{mismatch_id}/resolve")
async def resolve_mismatch(
    trace_id: str,
    mismatch_id: str,
    resolution_note: Optional[str] = Query(None, description="Optional note about the resolution"),
    user: User = Depends(get_current_user),
):
    """
    Mark a mismatch as resolved.

    RBAC: Requires admin or operator role.
    """
    if not user.has_role("admin") and not user.has_role("operator"):
        raise HTTPException(status_code=403, detail="Requires admin or operator role")

    if not USE_POSTGRES:
        raise HTTPException(status_code=501, detail="Requires PostgreSQL store")

    registry = get_operation_registry()

    async with get_async_session_context() as session:
        result = await registry.execute(
            "traces.resolve_mismatch",
            OperationContext(
                session=session,
                tenant_id=user.tenant_id,
                params={
                    "trace_id": trace_id,
                    "mismatch_id": mismatch_id,
                    "user_id": user.user_id,
                    "resolution_note": resolution_note,
                },
            ),
        )

    if not result.success:
        if result.error_code == "MISMATCH_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Mismatch not found")
        raise HTTPException(status_code=500, detail=result.error)

    return wrap_dict(result.data)
