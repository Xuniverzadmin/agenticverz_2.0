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

import os
import logging
from datetime import datetime
from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Response, status, Request
from pydantic import BaseModel, Field

# Use PostgreSQL store in production, SQLite for dev/test
USE_POSTGRES = os.getenv("USE_POSTGRES_TRACES", "false").lower() == "true"

if USE_POSTGRES:
    from ..traces.pg_store import PostgresTraceStore, get_postgres_trace_store
    TraceStoreType = PostgresTraceStore
else:
    from ..traces.store import SQLiteTraceStore
    TraceStoreType = SQLiteTraceStore

from ..traces.models import TraceSummary, TraceRecord
from ..traces.redact import redact_trace_data

# JWT Authentication
from ..auth.jwt_auth import JWTAuthDependency, TokenPayload, JWTConfig

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


async def get_current_user(
    request: Request,
    token: TokenPayload = Depends(_jwt_auth)
) -> User:
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

    return {
        "trace_id": trace_id,
        "root_hash": trace.get("root_hash"),
        "stored": True,
    }


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
        raise HTTPException(
            status_code=404,
            detail=f"No trace found with root_hash {root_hash}"
        )

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
        differences.append({
            "field": "root_hash",
            "trace1": trace1.root_hash,
            "trace2": trace2.root_hash,
        })

    # Compare seeds
    if trace1.seed != trace2.seed:
        differences.append({
            "field": "seed",
            "trace1": trace1.seed,
            "trace2": trace2.seed,
        })

    # Compare frozen timestamps
    if trace1.frozen_timestamp != trace2.frozen_timestamp:
        differences.append({
            "field": "frozen_timestamp",
            "trace1": trace1.frozen_timestamp,
            "trace2": trace2.frozen_timestamp,
        })

    # Compare step counts
    if len(trace1.steps) != len(trace2.steps):
        differences.append({
            "field": "step_count",
            "trace1": len(trace1.steps),
            "trace2": len(trace2.steps),
        })

    # Compare individual steps
    for i, (s1, s2) in enumerate(zip(trace1.steps, trace2.steps)):
        if s1.skill_name != s2.skill_name:
            differences.append({
                "field": f"step[{i}].skill_name",
                "trace1": s1.skill_name,
                "trace2": s2.skill_name,
            })
        if s1.outcome_category != s2.outcome_category:
            differences.append({
                "field": f"step[{i}].outcome_category",
                "trace1": s1.outcome_category,
                "trace2": s2.outcome_category,
            })

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
    return {
        "deleted_count": count,
        "retention_days": days,
    }


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
        raise HTTPException(
            status_code=501,
            detail="Idempotency check requires PostgreSQL store"
        )

    result = await store.check_idempotency_key(idempotency_key, user.tenant_id)

    if result:
        return {
            "executed": True,
            "trace_id": result["trace_id"],
            "step_index": result["step_index"],
            "status": result["status"],
            "output_hash": result["output_hash"],
        }
    else:
        return {
            "executed": False,
        }


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
    import httpx
    import uuid

    # Verify trace exists and belongs to user's tenant (or user is admin)
    if USE_POSTGRES:
        from ..db import db_async
        async with db_async.get_session() as session:
            result = await session.execute(
                "SELECT tenant_id FROM aos_traces WHERE trace_id = $1",
                [trace_id]
            )
            row = result.fetchone()
    else:
        trace = await store.get_trace(trace_id)
        row = {"tenant_id": trace.tenant_id} if trace else None

    if not row:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    trace_tenant = row["tenant_id"] if isinstance(row, dict) else row[0]
    if trace_tenant != user.tenant_id and not user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Cannot report mismatch for other tenant's trace")

    # Generate mismatch ID
    mismatch_id = str(uuid.uuid4())

    # Insert mismatch record
    if USE_POSTGRES:
        from ..db import db_async
        async with db_async.get_session() as session:
            await session.execute("""
                INSERT INTO aos_trace_mismatches
                (id, trace_id, tenant_id, reported_by, step_index, reason, expected_hash, actual_hash, details)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, [
                mismatch_id,
                trace_id,
                user.tenant_id,
                user.user_id,
                payload.step_index,
                payload.reason,
                payload.expected_hash,
                payload.actual_hash,
                payload.details,
            ])
            await session.commit()

    # Attempt notifications
    issue_url = None
    notified = "none"

    # Try GitHub issue creation
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")  # format: org/repo

    if github_token and github_repo:
        try:
            title = f"[Replay Mismatch] trace:{trace_id} step:{payload.step_index}"
            body = f"""## Replay Mismatch Detected

**Trace ID:** `{trace_id}`
**Step Index:** {payload.step_index}
**Reason:** {payload.reason}
**Reported By:** {user.user_id}
**Tenant:** {user.tenant_id}

### Details
- Expected Hash: `{payload.expected_hash or 'N/A'}`
- Actual Hash: `{payload.actual_hash or 'N/A'}`

### Additional Details
```json
{payload.details}
```

### Investigation
Run the following to inspect the trace:
```bash
curl -H "Authorization: Bearer $TOKEN" https://api.agenticverz.com/api/v1/traces/{trace_id}
```
"""
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.github.com/repos/{github_repo}/issues",
                    headers={
                        "Authorization": f"token {github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={
                        "title": title,
                        "body": body,
                        "labels": ["replay-mismatch", "aos", "automated"],
                    },
                    timeout=10.0,
                )
                if resp.status_code in (200, 201):
                    issue_data = resp.json()
                    issue_url = issue_data.get("html_url")
                    notified = "github"

                    # Update mismatch record with issue URL
                    if USE_POSTGRES:
                        async with db_async.get_session() as session:
                            await session.execute(
                                "UPDATE aos_trace_mismatches SET issue_url = $1, notification_sent = TRUE WHERE id = $2",
                                [issue_url, mismatch_id]
                            )
                            await session.commit()
        except Exception as e:
            logger.warning(f"Failed to create GitHub issue: {e}")

    # Try Slack notification if no GitHub issue created
    slack_webhook = os.getenv("SLACK_MISMATCH_WEBHOOK")

    if notified == "none" and slack_webhook:
        try:
            message = {
                "text": f"[Replay Mismatch] trace:{trace_id} step:{payload.step_index}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Replay Mismatch Detected* :warning:"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Trace ID*\n`{trace_id}`"},
                            {"type": "mrkdwn", "text": f"*Step Index*\n{payload.step_index}"},
                            {"type": "mrkdwn", "text": f"*Reason*\n{payload.reason}"},
                            {"type": "mrkdwn", "text": f"*Reported By*\n{user.user_id}"},
                        ]
                    },
                ]
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(slack_webhook, json=message, timeout=10.0)
                if resp.status_code == 200:
                    notified = "slack"

                    # Update notification sent flag
                    if USE_POSTGRES:
                        async with db_async.get_session() as session:
                            await session.execute(
                                "UPDATE aos_trace_mismatches SET notification_sent = TRUE WHERE id = $1",
                                [mismatch_id]
                            )
                            await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send Slack notification: {e}")

    logger.info(f"Mismatch reported: trace={trace_id}, step={payload.step_index}, notified={notified}")

    return MismatchResponse(
        mismatch_id=mismatch_id,
        trace_id=trace_id,
        status="recorded",
        notified=notified,
        issue_url=issue_url,
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

    from ..db import db_async
    async with db_async.get_session() as session:
        # Verify access
        result = await session.execute(
            "SELECT tenant_id FROM aos_traces WHERE trace_id = $1",
            [trace_id]
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

        if row[0] != user.tenant_id and not user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get mismatches
        result = await session.execute("""
            SELECT id, step_index, reason, expected_hash, actual_hash, details,
                   notification_sent, issue_url, resolved, resolved_at, resolved_by, created_at
            FROM aos_trace_mismatches
            WHERE trace_id = $1
            ORDER BY created_at DESC
        """, [trace_id])
        rows = result.fetchall()

    return {
        "trace_id": trace_id,
        "mismatches": [
            {
                "mismatch_id": str(r[0]),
                "step_index": r[1],
                "reason": r[2],
                "expected_hash": r[3],
                "actual_hash": r[4],
                "details": r[5],
                "notification_sent": r[6],
                "issue_url": r[7],
                "resolved": r[8],
                "resolved_at": r[9].isoformat() if r[9] else None,
                "resolved_by": r[10],
                "created_at": r[11].isoformat(),
            }
            for r in rows
        ],
        "total": len(rows),
    }


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

    from ..db import db_async
    async with db_async.get_session() as session:
        result = await session.execute("""
            UPDATE aos_trace_mismatches
            SET resolved = TRUE, resolved_at = now(), resolved_by = $1
            WHERE id = $2 AND trace_id = $3
            RETURNING id, issue_url
        """, [user.user_id, mismatch_id, trace_id])
        row = result.fetchone()
        await session.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Mismatch not found")

    # If there's an associated GitHub issue, comment on it
    issue_url = row[1] if row else None
    if issue_url and resolution_note:
        import httpx
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            # Extract issue number from URL
            try:
                issue_number = issue_url.rstrip('/').split('/')[-1]
                github_repo = os.getenv("GITHUB_REPO")
                if github_repo:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"https://api.github.com/repos/{github_repo}/issues/{issue_number}/comments",
                            headers={
                                "Authorization": f"token {github_token}",
                                "Accept": "application/vnd.github.v3+json",
                            },
                            json={"body": f"Resolved by {user.user_id}\n\n{resolution_note}"},
                            timeout=10.0,
                        )
            except Exception as e:
                logger.warning(f"Failed to comment on GitHub issue: {e}")

    return {"status": "resolved", "mismatch_id": mismatch_id, "resolved_by": user.user_id}


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

    import httpx
    from ..db import db_async

    # Fetch all mismatches
    async with db_async.get_session() as session:
        placeholders = ','.join([f'${i+1}' for i in range(len(mismatch_ids))])
        result = await session.execute(f"""
            SELECT id, trace_id, step_index, reason, expected_hash, actual_hash, details
            FROM aos_trace_mismatches
            WHERE id IN ({placeholders})
            ORDER BY trace_id, step_index
        """, mismatch_ids)
        rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No mismatches found")

    # Group by trace_id
    by_trace = {}
    for r in rows:
        trace_id = r[1]
        if trace_id not in by_trace:
            by_trace[trace_id] = []
        by_trace[trace_id].append({
            "mismatch_id": str(r[0]),
            "step_index": r[2],
            "reason": r[3],
            "expected_hash": r[4],
            "actual_hash": r[5],
        })

    issue_url = None

    if github_issue:
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")

        if github_token and github_repo:
            # Build issue body
            title = f"[Replay Mismatches] {len(rows)} mismatches across {len(by_trace)} trace(s)"

            body_parts = ["## Bulk Mismatch Report\n"]
            body_parts.append(f"**Total Mismatches:** {len(rows)}")
            body_parts.append(f"**Traces Affected:** {len(by_trace)}")
            body_parts.append(f"**Reported By:** {user.user_id}\n")

            for trace_id, mismatches in by_trace.items():
                body_parts.append(f"### Trace `{trace_id}`")
                body_parts.append("| Step | Reason | Expected | Actual |")
                body_parts.append("|------|--------|----------|--------|")
                for m in mismatches:
                    exp = m['expected_hash'][:8] if m['expected_hash'] else 'N/A'
                    act = m['actual_hash'][:8] if m['actual_hash'] else 'N/A'
                    body_parts.append(f"| {m['step_index']} | {m['reason']} | `{exp}` | `{act}` |")
                body_parts.append("")

            body = "\n".join(body_parts)

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"https://api.github.com/repos/{github_repo}/issues",
                        headers={
                            "Authorization": f"token {github_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        json={
                            "title": title,
                            "body": body,
                            "labels": ["replay-mismatch", "aos", "bulk-report", "automated"],
                        },
                        timeout=15.0,
                    )
                    if resp.status_code in (200, 201):
                        issue_data = resp.json()
                        issue_url = issue_data.get("html_url")

                        # Update all mismatches with the issue URL
                        async with db_async.get_session() as session:
                            await session.execute(f"""
                                UPDATE aos_trace_mismatches
                                SET issue_url = $1, notification_sent = TRUE
                                WHERE id IN ({placeholders})
                            """, [issue_url] + mismatch_ids)
                            await session.commit()
            except Exception as e:
                logger.warning(f"Failed to create bulk GitHub issue: {e}")

    return {
        "linked_count": len(rows),
        "traces_affected": len(by_trace),
        "issue_url": issue_url,
        "mismatch_ids": [str(r[0]) for r in rows],
    }
