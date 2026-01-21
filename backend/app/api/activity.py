# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified ACTIVITY domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: ACTIVITY Domain - One Facade Architecture
#
# GOVERNANCE NOTE:
# This is the ONE facade for ACTIVITY domain.
# All activity data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

from __future__ import annotations

"""
Unified Activity API (L2)

Customer-facing endpoints for viewing execution activity.
All requests are tenant-scoped via auth_context.

V2 Endpoints (Topic-Scoped - PREFERRED):
- GET /api/v1/activity/live              → LIVE runs with policy context
- GET /api/v1/activity/completed         → COMPLETED runs with policy context
- GET /api/v1/activity/signals           → Synthesized attention signals
- GET /api/v1/activity/metrics           → Aggregated activity metrics
- GET /api/v1/activity/threshold-signals → Threshold proximity tracking

V1 Endpoints (Legacy):
- GET /api/v1/activity/runs              → [DEPRECATED] O2 list with filters
- GET /api/v1/activity/runs/{run_id}     → O3 detail
- GET /api/v1/activity/runs/{run_id}/evidence → O4 context (preflight)
- GET /api/v1/activity/runs/{run_id}/proof    → O5 raw (preflight)
- GET /api/v1/activity/summary/by-status → COMP-O3 status summary
- GET /api/v1/activity/runs/by-dimension → [DEPRECATED] dimension grouping
- GET /api/v1/activity/patterns          → SIG-O3 pattern detection
- GET /api/v1/activity/cost-analysis     → SIG-O4 cost anomalies
- GET /api/v1/activity/attention-queue   → SIG-O5 attention ranking
- GET /api/v1/activity/risk-signals      → Risk signal aggregates

Architecture:
- ONE facade for all ACTIVITY needs
- Uses v_runs_o2 view (pre-computed risk, latency, evidence, policy context)
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
- V2 endpoints return policy_context in every response

Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
"""

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep

# =============================================================================
# Logging
# =============================================================================

logger = logging.getLogger(__name__)
from app.services.activity import (
    PatternDetectionService,
    CostAnalysisService,
    AttentionRankingService,
)
from app.schemas.response import wrap_dict

# =============================================================================
# Environment Configuration
# =============================================================================

_CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


def require_preflight() -> None:
    """Guard for preflight-only endpoints (O4, O5)."""
    if _CURRENT_ENVIRONMENT != "preflight":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "preflight_only",
                "message": "This endpoint is only available in preflight console.",
            },
        )


# =============================================================================
# Enums
# =============================================================================


class RunState(str, Enum):
    """Run lifecycle state."""

    LIVE = "LIVE"
    COMPLETED = "COMPLETED"


class RunStatus(str, Enum):
    """Run execution status."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABORTED = "aborted"
    QUEUED = "queued"
    RETRY = "retry"


class RiskLevel(str, Enum):
    """Risk classification."""

    NORMAL = "NORMAL"
    NEAR_THRESHOLD = "NEAR_THRESHOLD"
    AT_RISK = "AT_RISK"
    VIOLATED = "VIOLATED"


class LatencyBucket(str, Enum):
    """Latency classification."""

    OK = "OK"
    SLOW = "SLOW"
    STALLED = "STALLED"


class EvidenceHealth(str, Enum):
    """Evidence capture health."""

    FLOWING = "FLOWING"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"


class IntegrityStatus(str, Enum):
    """Integrity verification status."""

    UNKNOWN = "UNKNOWN"
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class RunSource(str, Enum):
    """Run initiator type."""

    AGENT = "agent"
    HUMAN = "human"
    SDK = "sdk"


class ProviderType(str, Enum):
    """LLM provider."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    INTERNAL = "internal"


class SortField(str, Enum):
    """Allowed sort fields."""

    STARTED_AT = "started_at"
    COMPLETED_AT = "completed_at"
    DURATION_MS = "duration_ms"
    RISK_LEVEL = "risk_level"


class SortOrder(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class EvaluationOutcome(str, Enum):
    """Policy evaluation outcome."""

    OK = "OK"
    NEAR_THRESHOLD = "NEAR_THRESHOLD"
    BREACH = "BREACH"
    OVERRIDDEN = "OVERRIDDEN"
    ADVISORY = "ADVISORY"


class PolicyScope(str, Enum):
    """Policy/limit scope."""

    TENANT = "TENANT"
    PROJECT = "PROJECT"
    AGENT = "AGENT"
    PROVIDER = "PROVIDER"
    GLOBAL = "GLOBAL"


class RiskType(str, Enum):
    """Risk type classification for panels."""

    COST = "COST"
    TIME = "TIME"
    TOKENS = "TOKENS"
    RATE = "RATE"
    OTHER = "OTHER"


# =============================================================================
# Response Models
# =============================================================================


# =============================================================================
# V2 Response Models (Policy Context)
# =============================================================================


class PolicyContext(BaseModel):
    """
    Policy context for a run (V2).

    Advisory metadata showing why a run is at-risk.
    Derived at query time from limits table via v_runs_o2 view.

    Cross-Domain Navigation (PIN-447):
    - facade_ref: Links to /policy/active/{policy_id}
    - threshold_ref: Links to /policy/thresholds/{id} (if limit-based)
    - violation_ref: Links to /policy/violations/{id} (if violation exists)

    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md, CROSS_DOMAIN_POLICY_CONTRACT.md
    """

    policy_id: str
    policy_name: str
    policy_scope: str
    limit_type: str | None = None
    threshold_value: float | None = None
    threshold_unit: str | None = None
    threshold_source: str
    evaluation_outcome: str
    actual_value: float | None = None
    risk_type: str | None = None
    proximity_pct: float | None = None

    # Cross-domain navigation refs (PIN-447 - Policy V2 Facade)
    facade_ref: str | None = None  # "/policy/active/{policy_id}"
    threshold_ref: str | None = None  # "/policy/thresholds/{id}"
    violation_ref: str | None = None  # "/policy/violations/{id}"


class RunSummaryV2(BaseModel):
    """
    Run summary with policy context (V2).

    Extends RunSummary with mandatory policy_context field.
    Used by topic-scoped endpoints: /live, /completed.

    Reference: ACTIVITY_DOMAIN_CONTRACT.md (V2 sections)
    """

    # Identity & Scope
    run_id: str
    tenant_id: str | None
    project_id: str | None
    is_synthetic: bool
    source: str
    provider_type: str

    # Execution State
    state: str
    status: str
    started_at: datetime | None
    last_seen_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None

    # Risk & Health (pre-computed)
    risk_level: str
    latency_bucket: str
    evidence_health: str
    integrity_status: str

    # Impact Signals
    incident_count: int = 0
    policy_draft_count: int = 0
    policy_violation: bool = False

    # Cost / Volume
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None

    # Policy Context (V2 - MANDATORY)
    policy_context: PolicyContext

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    next_offset: int | None = None


class LiveRunsResponse(BaseModel):
    """
    GET /activity/live response (V2).

    Topic-scoped endpoint - hardcoded state=LIVE.
    Every run includes policy_context.

    Panels: LIVE-O1, LIVE-O3, LIVE-O5
    """

    items: list[RunSummaryV2]
    total: int
    has_more: bool
    pagination: Pagination
    generated_at: datetime


class CompletedRunsResponse(BaseModel):
    """
    GET /activity/completed response (V2).

    Topic-scoped endpoint - hardcoded state=COMPLETED.
    Every run includes policy_context.

    Panels: COMP-O2, COMP-O5
    """

    items: list[RunSummaryV2]
    total: int
    has_more: bool
    pagination: Pagination
    generated_at: datetime


class SignalFeedbackModel(BaseModel):
    """
    Feedback state for a signal.

    INVARIANTS:
    - ATTN-DAMP-001: Acknowledgement dampening is idempotent (apply once, 0.6x)
    - SIGNAL-SUPPRESS-001: Suppression is temporary (15-1440 minutes)
    - SIGNAL-ACK-001: Acknowledgement records responsibility, doesn't hide signals
    """

    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    suppressed_until: datetime | None = None


class SignalProjection(BaseModel):
    """
    A signal projection (V2).

    SIGNALS is NOT a run state - it's a computed projection over LIVE + COMPLETED.
    Each signal includes policy_context for the underlying run.

    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    """

    signal_id: str
    signal_fingerprint: str  # Canonical fingerprint for feedback operations
    run_id: str
    signal_type: str  # COST_RISK | TIME_RISK | TOKEN_RISK | RATE_RISK | EVIDENCE_DEGRADED | POLICY_BREACH
    severity: str  # HIGH | MEDIUM | LOW
    summary: str
    policy_context: PolicyContext
    created_at: datetime
    feedback: SignalFeedbackModel | None = None  # Populated from audit_ledger


class SignalsResponse(BaseModel):
    """
    GET /activity/signals response (V2).

    Projection endpoint - synthesizes signals from LIVE + COMPLETED runs.
    Returns SignalProjection[], NOT runs.

    Panels: SIG-O1
    """

    signals: list[SignalProjection]
    total: int
    generated_at: datetime


class MetricsResponse(BaseModel):
    """
    GET /activity/metrics response (V2).

    Extends /risk-signals with topic-aware counts.

    Panels: LIVE-O1, LIVE-O2, LIVE-O4, COMP-O1, COMP-O3
    """

    # Risk counts (from /risk-signals)
    at_risk_count: int
    violated_count: int
    near_threshold_count: int
    total_at_risk: int

    # Topic-aware counts (V2)
    live_count: int
    completed_count: int

    # Evidence health breakdown
    evidence_flowing_count: int
    evidence_degraded_count: int
    evidence_missing_count: int

    # By risk type
    cost_risk_count: int
    time_risk_count: int
    token_risk_count: int
    rate_risk_count: int

    generated_at: datetime


class ThresholdSignal(BaseModel):
    """
    A threshold proximity signal (V2).

    Used for runs approaching or exceeding limits.
    """

    run_id: str
    limit_type: str
    proximity_pct: float
    evaluation_outcome: str
    policy_context: PolicyContext


class ThresholdSignalsResponse(BaseModel):
    """
    GET /activity/threshold-signals response (V2).

    Returns runs with typed threshold proximity.

    Panels: LIVE-O2, COMP-O4, SIG-O2
    """

    signals: list[ThresholdSignal]
    total: int
    risk_type_filter: str | None
    generated_at: datetime


# =============================================================================
# Signal Feedback Request/Response Models (V2)
# =============================================================================


class SignalAckRequest(BaseModel):
    """
    POST /activity/signals/{signal_fingerprint}/ack request.

    INVARIANT (SIGNAL-ID-001): The signal_fingerprint in the path MUST match
    the server-computed fingerprint. Clients provide identifying info for
    server-side validation.
    """

    run_id: str
    signal_type: str  # COST_RISK, TIME_RISK, etc.
    risk_type: str    # COST, TIME, TOKENS, RATE
    comment: str | None = None


class SignalAckResponse(BaseModel):
    """
    POST /activity/signals/{signal_fingerprint}/ack response.
    """

    signal_fingerprint: str
    acknowledged: bool
    acknowledged_by: str
    acknowledged_at: datetime


class SignalSuppressRequest(BaseModel):
    """
    POST /activity/signals/{signal_fingerprint}/suppress request.

    INVARIANT (SIGNAL-SUPPRESS-001): duration_minutes must be 15-1440 (max 24 hours).
    """

    run_id: str
    signal_type: str
    risk_type: str
    duration_minutes: int  # 15-1440
    reason: str | None = None


class SignalSuppressResponse(BaseModel):
    """
    POST /activity/signals/{signal_fingerprint}/suppress response.
    """

    signal_fingerprint: str
    suppressed_until: datetime


class RunSummary(BaseModel):
    """Run summary for list view (O2)."""

    # Identity & Scope
    run_id: str
    tenant_id: str | None
    project_id: str | None
    is_synthetic: bool
    source: str
    provider_type: str

    # Execution State
    state: str
    status: str
    started_at: datetime | None
    last_seen_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None

    # Risk & Health (pre-computed)
    risk_level: str
    latency_bucket: str
    evidence_health: str
    integrity_status: str

    # Impact Signals
    incident_count: int = 0
    policy_draft_count: int = 0
    policy_violation: bool = False

    # Cost / Volume
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None

    class Config:
        from_attributes = True


class RunListResponse(BaseModel):
    """GET /runs response."""

    items: list[RunSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]
    pagination: Pagination


class RunDetailResponse(BaseModel):
    """GET /runs/{run_id} response (O3)."""

    run_id: str
    tenant_id: str | None
    project_id: str | None
    is_synthetic: bool
    source: str
    provider_type: str
    state: str
    status: str
    started_at: datetime | None
    last_seen_at: datetime | None
    completed_at: datetime | None
    duration_ms: float | None
    risk_level: str
    latency_bucket: str
    evidence_health: str
    integrity_status: str
    incident_count: int
    policy_draft_count: int
    policy_violation: bool
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    # O3 additions
    goal: str | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


# =============================================================================
# COMP-O3 Response Models
# =============================================================================


class StatusBucket(BaseModel):
    """A bucket in status summary."""

    status: str
    count: int
    percentage: float


class StatusSummaryResponse(BaseModel):
    """GET /summary/by-status response (COMP-O3)."""

    buckets: list[StatusBucket]
    total_runs: int
    generated_at: datetime


# =============================================================================
# LIVE-O5 Response Models
# =============================================================================


class DimensionValue(str, Enum):
    """Allowed dimension values for grouping."""

    PROVIDER_TYPE = "provider_type"
    SOURCE = "source"
    AGENT_ID = "agent_id"
    RISK_LEVEL = "risk_level"
    STATUS = "status"


class DimensionGroup(BaseModel):
    """A group in dimension breakdown."""

    value: str
    count: int
    percentage: float


class DimensionBreakdownResponse(BaseModel):
    """GET /runs/by-dimension response (LIVE-O5)."""

    dimension: str
    groups: list[DimensionGroup]
    total_runs: int
    state_filter: str | None
    generated_at: datetime


# =============================================================================
# SIG-O3 Response Models (Patterns)
# =============================================================================


class PatternMatchResponse(BaseModel):
    """A detected pattern."""

    pattern_type: str
    run_id: str
    confidence: float
    details: dict


class PatternDetectionResponse(BaseModel):
    """GET /patterns response (SIG-O3)."""

    patterns: list[PatternMatchResponse]
    window_start: datetime
    window_end: datetime
    runs_analyzed: int


# =============================================================================
# SIG-O4 Response Models (Cost Analysis)
# =============================================================================


class AgentCostResponse(BaseModel):
    """Cost analysis for a single agent."""

    agent_id: str
    current_cost_usd: float
    run_count: int
    baseline_avg_usd: float | None
    baseline_p95_usd: float | None
    z_score: float
    is_anomaly: bool


class CostAnalysisResponse(BaseModel):
    """GET /cost-analysis response (SIG-O4)."""

    agents: list[AgentCostResponse]
    total_anomalies: int
    total_cost_usd: float
    window_current: str
    window_baseline: str


# =============================================================================
# SIG-O5 Response Models (Attention Queue)
# =============================================================================


class AttentionItemResponse(BaseModel):
    """An item in the attention queue."""

    run_id: str
    attention_score: float
    reasons: list[str]
    state: str
    status: str
    started_at: datetime | None


class AttentionQueueResponse(BaseModel):
    """GET /attention-queue response (SIG-O5)."""

    queue: list[AttentionItemResponse]
    total_attention_items: int
    weights_version: str
    generated_at: datetime


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/activity",
    tags=["activity"],
)


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth_context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Authentication required."},
        )

    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context.",
            },
        )

    return tenant_id


# =============================================================================
# GET /runs - O2 List
# =============================================================================


@router.get(
    "/runs",
    response_model=RunListResponse,
    summary="[DEPRECATED] List runs (O2)",
    description="""
    **DEPRECATED:** Use topic-scoped endpoints instead:
    - `/activity/live` for LIVE runs
    - `/activity/completed` for COMPLETED runs
    - `/activity/signals` for attention signals

    Returns paginated list of runs matching filter criteria.
    Tenant isolation enforced via auth_context.

    Topic mapping:
    - Live Topic: `?state=LIVE`
    - Completed Topic: `?state=COMPLETED`
    - Risk Signals Topic: `?risk=true`

    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md (Phase 5 - Lockdown)
    """,
    deprecated=True,
)
async def list_runs(
    request: Request,
    # Scope
    project_id: Annotated[str | None, Query(description="Project scope")] = None,
    # State filters
    state: Annotated[RunState | None, Query(description="Run lifecycle state")] = None,
    status: Annotated[list[str] | None, Query(description="Run status (multiple)")] = None,
    # Risk filters
    risk: Annotated[bool, Query(description="If true, returns runs with risk signals")] = False,
    risk_level: Annotated[list[RiskLevel] | None, Query(description="Filter by risk level")] = None,
    # Health filters
    latency_bucket: Annotated[list[LatencyBucket] | None, Query(description="Filter by latency")] = None,
    evidence_health: Annotated[list[EvidenceHealth] | None, Query(description="Filter by evidence health")] = None,
    integrity_status: Annotated[list[IntegrityStatus] | None, Query(description="Filter by integrity")] = None,
    # Source filters
    source: Annotated[list[RunSource] | None, Query(description="Filter by run source")] = None,
    provider_type: Annotated[list[ProviderType] | None, Query(description="Filter by LLM provider")] = None,
    # SDSR filter
    is_synthetic: Annotated[bool | None, Query(description="Filter by synthetic data flag")] = None,
    # Time filters
    started_after: Annotated[datetime | None, Query(description="Filter runs started after")] = None,
    started_before: Annotated[datetime | None, Query(description="Filter runs started before")] = None,
    completed_after: Annotated[datetime | None, Query(description="Filter runs completed after")] = None,
    completed_before: Annotated[datetime | None, Query(description="Filter runs completed before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=200, description="Max runs to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of runs to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.STARTED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> RunListResponse:
    """List runs with unified query filters. READ-ONLY from v_runs_o2 view."""

    # Tenant isolation from auth_context
    tenant_id = get_tenant_id_from_auth(request)

    # ==========================================================================
    # DEPRECATION WARNING (Phase 5 - Lockdown)
    # ==========================================================================
    # This endpoint is DEPRECATED. Use topic-scoped endpoints instead:
    # - /activity/live for LIVE runs
    # - /activity/completed for COMPLETED runs
    # - /activity/signals for attention signals
    # Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    # ==========================================================================
    user_agent = request.headers.get("user-agent", "unknown")
    logger.warning(
        "DEPRECATED_ENDPOINT_CALLED: /api/v1/activity/runs | "
        f"tenant_id={tenant_id} | "
        f"state={state.value if state else 'none'} | "
        f"user_agent={user_agent[:100]} | "
        "migration_path=Use /activity/live or /activity/completed"
    )

    # Build filters
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}
    where_clauses = ["tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Optional filters
    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id
        filters_applied["project_id"] = project_id

    if state:
        where_clauses.append("state = :state")
        params["state"] = state.value
        filters_applied["state"] = state.value

    if status:
        where_clauses.append("status = ANY(:status)")
        params["status"] = status
        filters_applied["status"] = status

    if risk:
        where_clauses.append("(risk_level != 'NORMAL' OR incident_count > 0 OR policy_violation = true)")
        filters_applied["risk"] = True

    if risk_level:
        values = [r.value for r in risk_level]
        where_clauses.append("risk_level = ANY(:risk_level)")
        params["risk_level"] = values
        filters_applied["risk_level"] = values

    if latency_bucket:
        values = [lb.value for lb in latency_bucket]
        where_clauses.append("latency_bucket = ANY(:latency_bucket)")
        params["latency_bucket"] = values
        filters_applied["latency_bucket"] = values

    if evidence_health:
        values = [e.value for e in evidence_health]
        where_clauses.append("evidence_health = ANY(:evidence_health)")
        params["evidence_health"] = values
        filters_applied["evidence_health"] = values

    if integrity_status:
        values = [i.value for i in integrity_status]
        where_clauses.append("integrity_status = ANY(:integrity_status)")
        params["integrity_status"] = values
        filters_applied["integrity_status"] = values

    if source:
        values = [s.value for s in source]
        where_clauses.append("source = ANY(:source)")
        params["source"] = values
        filters_applied["source"] = values

    if provider_type:
        values = [p.value for p in provider_type]
        where_clauses.append("provider_type = ANY(:provider_type)")
        params["provider_type"] = values
        filters_applied["provider_type"] = values

    if is_synthetic is not None:
        where_clauses.append("is_synthetic = :is_synthetic")
        params["is_synthetic"] = is_synthetic
        filters_applied["is_synthetic"] = is_synthetic

    if started_after:
        where_clauses.append("started_at >= :started_after")
        params["started_after"] = started_after
        filters_applied["started_after"] = started_after.isoformat()

    if started_before:
        where_clauses.append("started_at <= :started_before")
        params["started_before"] = started_before
        filters_applied["started_before"] = started_before.isoformat()

    if completed_after:
        where_clauses.append("completed_at >= :completed_after")
        params["completed_after"] = completed_after
        filters_applied["completed_after"] = completed_after.isoformat()

    if completed_before:
        where_clauses.append("completed_at <= :completed_before")
        params["completed_before"] = completed_before
        filters_applied["completed_before"] = completed_before.isoformat()

    where_sql = " AND ".join(where_clauses)
    sort_column = sort_by.value
    sort_dir = "DESC" if sort_order == SortOrder.DESC else "ASC"

    # Count query
    count_sql = f"SELECT COUNT(*) as total FROM v_runs_o2 WHERE {where_sql}"

    # Data query
    data_sql = f"""
        SELECT
            run_id, tenant_id, project_id, is_synthetic, source, provider_type,
            state, status, started_at, last_seen_at, completed_at, duration_ms,
            risk_level, latency_bucket, evidence_health, integrity_status,
            incident_count, policy_draft_count, policy_violation,
            input_tokens, output_tokens, estimated_cost_usd
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_dir}
        LIMIT :limit OFFSET :offset
    """

    params["limit"] = limit
    params["offset"] = offset

    try:
        count_result = await session.execute(text(count_sql), params)
        total = count_result.scalar() or 0

        data_result = await session.execute(text(data_sql), params)
        rows = data_result.mappings().all()

        items = [
            RunSummary(
                run_id=row["run_id"],
                tenant_id=row["tenant_id"],
                project_id=row["project_id"],
                is_synthetic=row["is_synthetic"],
                source=row["source"],
                provider_type=row["provider_type"],
                state=row["state"],
                status=row["status"],
                started_at=row["started_at"],
                last_seen_at=row["last_seen_at"],
                completed_at=row["completed_at"],
                duration_ms=float(row["duration_ms"]) if row["duration_ms"] else None,
                risk_level=row["risk_level"],
                latency_bucket=row["latency_bucket"],
                evidence_health=row["evidence_health"],
                integrity_status=row["integrity_status"],
                incident_count=row["incident_count"] or 0,
                policy_draft_count=row["policy_draft_count"] or 0,
                policy_violation=row["policy_violation"] or False,
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                estimated_cost_usd=float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None,
            )
            for row in rows
        ]

        has_more = offset + len(items) < total
        next_offset = offset + limit if has_more else None

        return RunListResponse(
            items=items,
            total=total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /runs/{run_id} - O3 Detail
# =============================================================================


@router.get(
    "/runs/{run_id}",
    response_model=RunDetailResponse,
    summary="Get run detail (O3)",
    description="Returns detailed information about a specific run.",
)
async def get_run_detail(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RunDetailResponse:
    """Get run detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    sql = """
        SELECT *
        FROM v_runs_o2
        WHERE run_id = :run_id AND tenant_id = :tenant_id
    """

    result = await session.execute(text(sql), {"run_id": run_id, "tenant_id": tenant_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunDetailResponse(
        run_id=row["run_id"],
        tenant_id=row["tenant_id"],
        project_id=row["project_id"],
        is_synthetic=row["is_synthetic"],
        source=row["source"],
        provider_type=row["provider_type"],
        state=row["state"],
        status=row["status"],
        started_at=row["started_at"],
        last_seen_at=row["last_seen_at"],
        completed_at=row["completed_at"],
        duration_ms=float(row["duration_ms"]) if row["duration_ms"] else None,
        risk_level=row["risk_level"],
        latency_bucket=row["latency_bucket"],
        evidence_health=row["evidence_health"],
        integrity_status=row["integrity_status"],
        incident_count=row["incident_count"] or 0,
        policy_draft_count=row["policy_draft_count"] or 0,
        policy_violation=row["policy_violation"] or False,
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        estimated_cost_usd=float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None,
        goal=row.get("goal"),
        error_message=row.get("error_message"),
    )


# =============================================================================
# GET /runs/{run_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/runs/{run_id}/evidence",
    summary="Get run evidence (O4)",
    description="Returns cross-domain impact and evidence context. Preflight only.",
)
async def get_run_evidence(
    request: Request,
    run_id: str,
) -> dict[str, Any]:
    """Get run evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return wrap_dict({
        "run_id": run_id,
        "incidents_caused": [],
        "policies_triggered": [],
        "decisions_made": [],
        "traces_linked": [],
    })


# =============================================================================
# GET /runs/{run_id}/proof - O5 Raw (Preflight Only)
# =============================================================================


@router.get(
    "/runs/{run_id}/proof",
    summary="Get run proof (O5)",
    description="Returns raw traces, logs, and integrity proof. Preflight only.",
)
async def get_run_proof(
    request: Request,
    run_id: str,
    include_payloads: bool = False,
) -> dict[str, Any]:
    """Get run proof (O5). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth
    _ = include_payloads  # Reserved for future use

    return wrap_dict({
        "run_id": run_id,
        "integrity": {
            "root_hash": None,
            "verification_status": "UNKNOWN",
            "chain_length": 0,
        },
        "aos_traces": [],
        "aos_trace_steps": [],
        "raw_logs": [],
    })


# =============================================================================
# GET /summary/by-status - COMP-O3 Status Summary
# =============================================================================


@router.get(
    "/summary/by-status",
    response_model=StatusSummaryResponse,
    summary="Summary by status (COMP-O3)",
    description="""
    Returns run counts grouped by status for the tenant.
    Provides a high-level overview of execution distribution.
    """,
)
async def get_summary_by_status(
    request: Request,
    state: Annotated[RunState | None, Query(description="Filter by run state")] = None,
    session: AsyncSession = Depends(get_async_session_dep),
) -> StatusSummaryResponse:
    """Get run summary by status (COMP-O3). READ-ONLY from v_runs_o2."""

    tenant_id = get_tenant_id_from_auth(request)

    # Build query
    where_clause = "tenant_id = :tenant_id"
    params: dict[str, Any] = {"tenant_id": tenant_id}

    if state:
        where_clause += " AND state = :state"
        params["state"] = state.value

    sql = text(f"""
        SELECT
            status,
            COUNT(*) as count
        FROM v_runs_o2
        WHERE {where_clause}
        GROUP BY status
        ORDER BY count DESC
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    # Calculate total and percentages
    total = sum(row["count"] for row in rows)

    buckets = [
        StatusBucket(
            status=row["status"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
        )
        for row in rows
    ]

    return StatusSummaryResponse(
        buckets=buckets,
        total_runs=total,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# Internal Helper: Dimension Breakdown (Shared Logic)
# =============================================================================


async def _get_runs_by_dimension_internal(
    session: AsyncSession,
    tenant_id: str,
    dim: DimensionValue,
    state: RunState,
    limit: int = 20,
) -> DimensionBreakdownResponse:
    """
    Internal helper for dimension breakdown with HARDCODED state binding.

    This function is called by topic-scoped endpoints only.
    State is injected by the endpoint, never from caller.

    Policy: TOPIC-SCOPED-ENDPOINT-001
    """
    dimension_col = dim.value
    where_clause = "tenant_id = :tenant_id AND state = :state"
    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "state": state.value,
        "limit": limit,
    }

    sql = text(f"""
        SELECT
            COALESCE({dimension_col}::text, 'unknown') as value,
            COUNT(*) as count
        FROM v_runs_o2
        WHERE {where_clause}
        GROUP BY {dimension_col}
        ORDER BY count DESC
        LIMIT :limit
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    total = sum(row["count"] for row in rows)

    groups = [
        DimensionGroup(
            value=row["value"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
        )
        for row in rows
    ]

    return DimensionBreakdownResponse(
        dimension=dimension_col,
        groups=groups,
        total_runs=total,
        state_filter=state.value,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# GET /runs/live/by-dimension - LIVE Topic Distribution (LIVE-O5)
# =============================================================================


@router.get(
    "/runs/live/by-dimension",
    response_model=DimensionBreakdownResponse,
    summary="Live runs by dimension (LIVE-O5)",
    description="""
    Returns LIVE run counts grouped by a specified dimension.

    **Topic-Scoped Endpoint** - State filter is IMPLICIT (hardcoded to LIVE).
    This endpoint ONLY returns runs with state=LIVE.

    Policy: TOPIC-SCOPED-ENDPOINT-001
    Capability: activity.runs_by_dimension
    """,
)
async def get_live_runs_by_dimension(
    request: Request,
    dim: Annotated[DimensionValue, Query(description="Dimension to group by")],
    limit: Annotated[int, Query(ge=1, le=100, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DimensionBreakdownResponse:
    """Get LIVE runs grouped by dimension. State=LIVE is hardcoded."""
    tenant_id = get_tenant_id_from_auth(request)
    return await _get_runs_by_dimension_internal(
        session=session,
        tenant_id=tenant_id,
        dim=dim,
        state=RunState.LIVE,  # HARDCODED - cannot be overridden
        limit=limit,
    )


# =============================================================================
# GET /runs/completed/by-dimension - COMPLETED Topic Distribution
# =============================================================================


@router.get(
    "/runs/completed/by-dimension",
    response_model=DimensionBreakdownResponse,
    summary="Completed runs by dimension",
    description="""
    Returns COMPLETED run counts grouped by a specified dimension.

    **Topic-Scoped Endpoint** - State filter is IMPLICIT (hardcoded to COMPLETED).
    This endpoint ONLY returns runs with state=COMPLETED.

    Policy: TOPIC-SCOPED-ENDPOINT-001
    Capability: activity.runs_by_dimension
    """,
)
async def get_completed_runs_by_dimension(
    request: Request,
    dim: Annotated[DimensionValue, Query(description="Dimension to group by")],
    limit: Annotated[int, Query(ge=1, le=100, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DimensionBreakdownResponse:
    """Get COMPLETED runs grouped by dimension. State=COMPLETED is hardcoded."""
    tenant_id = get_tenant_id_from_auth(request)
    return await _get_runs_by_dimension_internal(
        session=session,
        tenant_id=tenant_id,
        dim=dim,
        state=RunState.COMPLETED,  # HARDCODED - cannot be overridden
        limit=limit,
    )


# =============================================================================
# GET /runs/by-dimension - INTERNAL/ADMIN ONLY (Deprecated for Panels)
# =============================================================================


@router.get(
    "/runs/by-dimension",
    response_model=DimensionBreakdownResponse,
    summary="[INTERNAL] Runs by dimension (admin only)",
    description="""
    **INTERNAL/ADMIN ENDPOINT - DO NOT USE FOR PANELS**

    This endpoint accepts an optional state filter and is NOT topic-scoped.
    For panel use, call the topic-scoped endpoints instead:
    - LIVE panels: /runs/live/by-dimension
    - COMPLETED panels: /runs/completed/by-dimension

    Policy: TOPIC-SCOPED-ENDPOINT-001 - Generic endpoints must not be panel-bound.
    """,
    deprecated=True,
)
async def get_runs_by_dimension(
    request: Request,
    dim: Annotated[DimensionValue, Query(description="Dimension to group by")],
    state: Annotated[RunState | None, Query(description="Filter by run state")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DimensionBreakdownResponse:
    """[INTERNAL] Get runs grouped by dimension with optional state. NOT FOR PANELS."""
    tenant_id = get_tenant_id_from_auth(request)

    dimension_col = dim.value
    where_clause = "tenant_id = :tenant_id"
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

    if state:
        where_clause += " AND state = :state"
        params["state"] = state.value

    sql = text(f"""
        SELECT
            COALESCE({dimension_col}::text, 'unknown') as value,
            COUNT(*) as count
        FROM v_runs_o2
        WHERE {where_clause}
        GROUP BY {dimension_col}
        ORDER BY count DESC
        LIMIT :limit
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    total = sum(row["count"] for row in rows)

    groups = [
        DimensionGroup(
            value=row["value"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
        )
        for row in rows
    ]

    return DimensionBreakdownResponse(
        dimension=dimension_col,
        groups=groups,
        total_runs=total,
        state_filter=state.value if state else None,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# GET /patterns - SIG-O3 Pattern Detection
# =============================================================================


@router.get(
    "/patterns",
    response_model=PatternDetectionResponse,
    summary="Detect patterns (SIG-O3)",
    description="""
    Detects instability patterns in trace steps:
    - retry_loop: Repeated retries (>3 in same run)
    - step_oscillation: Same skill called non-consecutively
    - tool_call_loop: Repeated skill within sliding window
    - timeout_cascade: Multiple slow steps
    """,
)
async def get_patterns(
    request: Request,
    window_hours: Annotated[int, Query(ge=1, le=168, description="Hours to look back")] = 24,
    limit: Annotated[int, Query(ge=1, le=50, description="Max patterns per type")] = 10,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PatternDetectionResponse:
    """Detect instability patterns (SIG-O3). READ-ONLY from aos_traces/aos_trace_steps."""

    tenant_id = get_tenant_id_from_auth(request)

    service = PatternDetectionService(session)
    result = await service.detect_patterns(
        tenant_id=tenant_id,
        window_hours=window_hours,
        limit=limit,
    )

    return PatternDetectionResponse(
        patterns=[
            PatternMatchResponse(
                pattern_type=p.pattern_type,
                run_id=p.run_id,
                confidence=p.confidence,
                details=p.details,
            )
            for p in result.patterns
        ],
        window_start=result.window_start,
        window_end=result.window_end,
        runs_analyzed=result.runs_analyzed,
    )


# =============================================================================
# GET /cost-analysis - SIG-O4 Cost Anomalies
# =============================================================================


@router.get(
    "/cost-analysis",
    response_model=CostAnalysisResponse,
    summary="Cost analysis (SIG-O4)",
    description="""
    Analyzes cost anomalies via Z-score comparison against baseline.
    Detects agents with unusual cost patterns.
    """,
)
async def get_cost_analysis(
    request: Request,
    baseline_days: Annotated[int, Query(ge=1, le=30, description="Days for baseline")] = 7,
    anomaly_threshold: Annotated[float, Query(ge=1.0, le=5.0, description="Z-score threshold")] = 2.0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostAnalysisResponse:
    """Analyze cost anomalies (SIG-O4). READ-ONLY from runs table."""

    tenant_id = get_tenant_id_from_auth(request)

    service = CostAnalysisService(session)
    result = await service.analyze_costs(
        tenant_id=tenant_id,
        baseline_days=baseline_days,
        anomaly_threshold=anomaly_threshold,
    )

    return CostAnalysisResponse(
        agents=[
            AgentCostResponse(
                agent_id=a.agent_id,
                current_cost_usd=a.current_cost_usd,
                run_count=a.run_count,
                baseline_avg_usd=a.baseline_avg_usd,
                baseline_p95_usd=a.baseline_p95_usd,
                z_score=a.z_score,
                is_anomaly=a.is_anomaly,
            )
            for a in result.agents
        ],
        total_anomalies=result.total_anomalies,
        total_cost_usd=result.total_cost_usd,
        window_current=result.window_current,
        window_baseline=result.window_baseline,
    )


# =============================================================================
# GET /attention-queue - SIG-O5 Attention Ranking
# =============================================================================


@router.get(
    "/attention-queue",
    response_model=AttentionQueueResponse,
    summary="Attention queue (SIG-O5)",
    description="""
    Returns runs ranked by composite attention score.
    Combines risk, impact, latency, recency, and evidence signals.

    Weight distribution (FROZEN):
    - risk: 35%
    - impact: 25%
    - latency: 15%
    - recency: 15%
    - evidence: 10%
    """,
)
async def get_attention_queue(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AttentionQueueResponse:
    """Get attention queue (SIG-O5). READ-ONLY from v_runs_o2."""

    tenant_id = get_tenant_id_from_auth(request)

    service = AttentionRankingService(session)
    result = await service.get_attention_queue(
        tenant_id=tenant_id,
        limit=limit,
    )

    return AttentionQueueResponse(
        queue=[
            AttentionItemResponse(
                run_id=item.run_id,
                attention_score=item.attention_score,
                reasons=item.reasons,
                state=item.state,
                status=item.status,
                started_at=item.started_at,
            )
            for item in result.queue
        ],
        total_attention_items=result.total_attention_items,
        weights_version=result.weights_version,
        generated_at=result.generated_at,
    )


# =============================================================================
# GET /risk-signals - Risk Signal Aggregates
# =============================================================================
# PURPOSE: Returns aggregated risk counts for Customer Console panels
# CAPABILITY: activity.risk_signals
# SIGNALS: at_risk_count, cost_risk_count, time_risk_count, token_risk_count
# =============================================================================


class RiskSignalsResponse(BaseModel):
    """GET /risk-signals response."""

    at_risk_count: int
    violated_count: int
    at_risk_level_count: int
    near_threshold_count: int
    total_at_risk: int
    generated_at: datetime


@router.get(
    "/risk-signals",
    response_model=RiskSignalsResponse,
    summary="Risk signal aggregates",
    description="""
    Returns aggregated counts of runs at various risk levels.

    Risk levels:
    - NORMAL: No risk signals
    - NEAR_THRESHOLD: Approaching limits (warning)
    - AT_RISK: Threshold breach imminent
    - VIOLATED: Threshold exceeded

    Capability: activity.risk_signals
    Consumers: Overview panels, Activity summary panels
    """,
)
async def get_risk_signals(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RiskSignalsResponse:
    """
    Returns aggregated risk signal counts.

    Supports: activity.risk_signals capability
    Consumers: Overview panels, Activity summary panels

    Only considers:
    - Live runs (state = 'LIVE')
    - Completed runs in the last 24 hours
    """
    tenant_id = get_tenant_id_from_auth(request)

    sql = text("""
        SELECT
            COUNT(*) FILTER (WHERE risk_level IN ('NEAR_THRESHOLD', 'AT_RISK', 'VIOLATED')) as at_risk_count,
            COUNT(*) FILTER (WHERE risk_level = 'VIOLATED') as violated_count,
            COUNT(*) FILTER (WHERE risk_level = 'AT_RISK') as at_risk_level_count,
            COUNT(*) FILTER (WHERE risk_level = 'NEAR_THRESHOLD') as near_threshold_count,
            COUNT(*) FILTER (WHERE risk_level != 'NORMAL') as total_at_risk
        FROM v_runs_o2
        WHERE tenant_id = :tenant_id
          AND (state = 'LIVE' OR completed_at >= NOW() - INTERVAL '24 hours')
    """)

    result = await session.execute(sql, {"tenant_id": tenant_id})
    row = result.mappings().first()

    return RiskSignalsResponse(
        at_risk_count=row["at_risk_count"] or 0 if row else 0,
        violated_count=row["violated_count"] or 0 if row else 0,
        at_risk_level_count=row["at_risk_level_count"] or 0 if row else 0,
        near_threshold_count=row["near_threshold_count"] or 0 if row else 0,
        total_at_risk=row["total_at_risk"] or 0 if row else 0,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# V2 Helpers
# =============================================================================


def _extract_policy_context(row: dict) -> PolicyContext:
    """
    Extract PolicyContext from a v_runs_o2 row (V2 schema).

    The v_runs_o2 view includes policy context fields from migration 107.
    This helper converts DB row to PolicyContext model.

    Cross-Domain Navigation (PIN-447):
    - facade_ref: Always populated if policy_id exists
    - threshold_ref: Populated if limit_id exists
    - violation_ref: Populated if violation_id exists
    """
    policy_id = row.get("policy_id") or "SYSTEM_DEFAULT"

    # Build cross-domain navigation refs (PIN-447 - Policy V2 Facade)
    facade_ref = f"/policy/active/{policy_id}" if policy_id != "SYSTEM_DEFAULT" else None
    threshold_ref = (
        f"/policy/thresholds/{row['limit_id']}" if row.get("limit_id") else None
    )
    violation_ref = (
        f"/policy/violations/{row['violation_id']}" if row.get("violation_id") else None
    )

    return PolicyContext(
        policy_id=policy_id,
        policy_name=row.get("policy_name") or "Default Safety Thresholds",
        policy_scope=row.get("policy_scope") or "GLOBAL",
        limit_type=row.get("limit_type"),
        threshold_value=float(row["threshold_value"]) if row.get("threshold_value") else None,
        threshold_unit=row.get("threshold_unit"),
        threshold_source=row.get("threshold_source") or "SYSTEM_DEFAULT",
        evaluation_outcome=row.get("evaluation_outcome") or "ADVISORY",
        actual_value=float(row["actual_value"]) if row.get("actual_value") else None,
        risk_type=row.get("risk_type"),
        proximity_pct=float(row["proximity_pct"]) if row.get("proximity_pct") else None,
        # Cross-domain navigation refs (PIN-447)
        facade_ref=facade_ref,
        threshold_ref=threshold_ref,
        violation_ref=violation_ref,
    )


def _row_to_run_summary_v2(row: dict) -> RunSummaryV2:
    """
    Convert a v_runs_o2 row to RunSummaryV2.

    Includes policy_context extraction.
    """
    return RunSummaryV2(
        run_id=row["run_id"],
        tenant_id=row["tenant_id"],
        project_id=row["project_id"],
        is_synthetic=row["is_synthetic"],
        source=row["source"],
        provider_type=row["provider_type"],
        state=row["state"],
        status=row["status"],
        started_at=row["started_at"],
        last_seen_at=row["last_seen_at"],
        completed_at=row["completed_at"],
        duration_ms=float(row["duration_ms"]) if row["duration_ms"] else None,
        risk_level=row["risk_level"],
        latency_bucket=row["latency_bucket"],
        evidence_health=row["evidence_health"],
        integrity_status=row["integrity_status"],
        incident_count=row["incident_count"] or 0,
        policy_draft_count=row["policy_draft_count"] or 0,
        policy_violation=row["policy_violation"] or False,
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        estimated_cost_usd=float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None,
        policy_context=_extract_policy_context(row),
    )


# =============================================================================
# V2 Endpoints: Topic-Scoped (Activity Domain V2)
# =============================================================================
# Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
# Design Principle: Topics are boundaries, not filters
# =============================================================================


@router.get(
    "/live",
    response_model=LiveRunsResponse,
    summary="List live runs (V2 - Topic-Scoped)",
    description="""
    Returns currently executing runs with policy context.

    **Topic-Scoped Endpoint** - State filter is HARDCODED to LIVE.
    Cannot be overridden by query parameters.

    Every run includes `policy_context` showing:
    - Which limit governs the run
    - Threshold proximity
    - Evaluation outcome (OK, NEAR_THRESHOLD, BREACH, etc.)

    Policy: TOPIC-SCOPED-ENDPOINT-001
    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    Panels: LIVE-O1, LIVE-O3, LIVE-O5
    """,
)
async def list_live_runs(
    request: Request,
    # Scope
    project_id: Annotated[str | None, Query(description="Project scope")] = None,
    # Risk filters
    risk_level: Annotated[list[RiskLevel] | None, Query(description="Filter by risk level")] = None,
    # Health filters
    evidence_health: Annotated[list[EvidenceHealth] | None, Query(description="Filter by evidence health")] = None,
    # Source filters
    source: Annotated[list[RunSource] | None, Query(description="Filter by run source")] = None,
    provider_type: Annotated[list[ProviderType] | None, Query(description="Filter by LLM provider")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=200, description="Max runs to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of runs to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> LiveRunsResponse:
    """
    List LIVE runs with policy context.

    State=LIVE is HARDCODED - cannot be overridden.
    This is the canonical endpoint for the LIVE topic.
    """

    tenant_id = get_tenant_id_from_auth(request)

    # Build query - state=LIVE is HARDCODED
    where_clauses = ["tenant_id = :tenant_id", "state = 'LIVE'"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Optional filters
    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if risk_level:
        values = [r.value for r in risk_level]
        where_clauses.append("risk_level = ANY(:risk_level)")
        params["risk_level"] = values

    if evidence_health:
        values = [e.value for e in evidence_health]
        where_clauses.append("evidence_health = ANY(:evidence_health)")
        params["evidence_health"] = values

    if source:
        values = [s.value for s in source]
        where_clauses.append("source = ANY(:source)")
        params["source"] = values

    if provider_type:
        values = [p.value for p in provider_type]
        where_clauses.append("provider_type = ANY(:provider_type)")
        params["provider_type"] = values

    where_sql = " AND ".join(where_clauses)

    # Count query
    count_sql = f"SELECT COUNT(*) as total FROM v_runs_o2 WHERE {where_sql}"

    # Data query - includes policy context fields from v_runs_o2
    data_sql = f"""
        SELECT
            run_id, tenant_id, project_id, is_synthetic, source, provider_type,
            state, status, started_at, last_seen_at, completed_at, duration_ms,
            risk_level, latency_bucket, evidence_health, integrity_status,
            incident_count, policy_draft_count, policy_violation,
            input_tokens, output_tokens, estimated_cost_usd,
            -- Policy context fields (V2)
            policy_id, policy_name, policy_scope, limit_type,
            threshold_value, threshold_unit, threshold_source,
            risk_type, actual_value, evaluation_outcome, proximity_pct
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY started_at DESC
        LIMIT :limit OFFSET :offset
    """

    params["limit"] = limit
    params["offset"] = offset

    try:
        count_result = await session.execute(text(count_sql), params)
        total = count_result.scalar() or 0

        data_result = await session.execute(text(data_sql), params)
        rows = data_result.mappings().all()

        items = [_row_to_run_summary_v2(dict(row)) for row in rows]

        has_more = offset + len(items) < total
        next_offset = offset + limit if has_more else None

        return LiveRunsResponse(
            items=items,
            total=total,
            has_more=has_more,
            pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


@router.get(
    "/completed",
    response_model=CompletedRunsResponse,
    summary="List completed runs (V2 - Topic-Scoped)",
    description="""
    Returns finished runs with policy context.

    **Topic-Scoped Endpoint** - State filter is HARDCODED to COMPLETED.
    Cannot be overridden by query parameters.

    Every run includes `policy_context` showing:
    - Which limit governed the run
    - Final threshold evaluation
    - Whether breach occurred

    Policy: TOPIC-SCOPED-ENDPOINT-001
    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    Panels: COMP-O2, COMP-O5
    """,
)
async def list_completed_runs(
    request: Request,
    # Scope
    project_id: Annotated[str | None, Query(description="Project scope")] = None,
    # Status filters
    status: Annotated[list[str] | None, Query(description="Run status (multiple)")] = None,
    # Risk filters
    risk_level: Annotated[list[RiskLevel] | None, Query(description="Filter by risk level")] = None,
    # Time filters
    completed_after: Annotated[datetime | None, Query(description="Filter runs completed after")] = None,
    completed_before: Annotated[datetime | None, Query(description="Filter runs completed before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=200, description="Max runs to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of runs to skip")] = 0,
    # Sort
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.COMPLETED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> CompletedRunsResponse:
    """
    List COMPLETED runs with policy context.

    State=COMPLETED is HARDCODED - cannot be overridden.
    This is the canonical endpoint for the COMPLETED topic.
    """

    tenant_id = get_tenant_id_from_auth(request)

    # Build query - state=COMPLETED is HARDCODED
    where_clauses = ["tenant_id = :tenant_id", "state = 'COMPLETED'"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Optional filters
    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if status:
        where_clauses.append("status = ANY(:status)")
        params["status"] = status

    if risk_level:
        values = [r.value for r in risk_level]
        where_clauses.append("risk_level = ANY(:risk_level)")
        params["risk_level"] = values

    if completed_after:
        where_clauses.append("completed_at >= :completed_after")
        params["completed_after"] = completed_after

    if completed_before:
        where_clauses.append("completed_at <= :completed_before")
        params["completed_before"] = completed_before

    where_sql = " AND ".join(where_clauses)
    sort_column = sort_by.value
    sort_dir = "DESC" if sort_order == SortOrder.DESC else "ASC"

    # Count query
    count_sql = f"SELECT COUNT(*) as total FROM v_runs_o2 WHERE {where_sql}"

    # Data query - includes policy context fields
    data_sql = f"""
        SELECT
            run_id, tenant_id, project_id, is_synthetic, source, provider_type,
            state, status, started_at, last_seen_at, completed_at, duration_ms,
            risk_level, latency_bucket, evidence_health, integrity_status,
            incident_count, policy_draft_count, policy_violation,
            input_tokens, output_tokens, estimated_cost_usd,
            -- Policy context fields (V2)
            policy_id, policy_name, policy_scope, limit_type,
            threshold_value, threshold_unit, threshold_source,
            risk_type, actual_value, evaluation_outcome, proximity_pct
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_dir}
        LIMIT :limit OFFSET :offset
    """

    params["limit"] = limit
    params["offset"] = offset

    try:
        count_result = await session.execute(text(count_sql), params)
        total = count_result.scalar() or 0

        data_result = await session.execute(text(data_sql), params)
        rows = data_result.mappings().all()

        items = [_row_to_run_summary_v2(dict(row)) for row in rows]

        has_more = offset + len(items) < total
        next_offset = offset + limit if has_more else None

        return CompletedRunsResponse(
            items=items,
            total=total,
            has_more=has_more,
            pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


@router.get(
    "/signals",
    response_model=SignalsResponse,
    summary="List activity signals (V2 - Projection)",
    description="""
    Returns synthesized attention signals across LIVE and COMPLETED runs.

    **SIGNALS is a projection layer, NOT a lifecycle state.**
    This endpoint synthesizes signals from runs with attention-worthy conditions.

    Signal types:
    - COST_RISK: Run approaching or exceeding cost threshold
    - TIME_RISK: Run approaching or exceeding time threshold
    - TOKEN_RISK: Run approaching or exceeding token threshold
    - EVIDENCE_DEGRADED: Evidence capture health issues
    - POLICY_BREACH: Policy threshold exceeded

    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    Panels: SIG-O1
    """,
)
async def list_signals(
    request: Request,
    # Scope
    project_id: Annotated[str | None, Query(description="Project scope")] = None,
    # Signal filters
    signal_type: Annotated[str | None, Query(description="Filter by signal type")] = None,
    severity: Annotated[str | None, Query(description="Filter by severity (HIGH, MEDIUM, LOW)")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max signals to return")] = 20,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> SignalsResponse:
    """
    List activity signals (V2 projection).

    Synthesizes signals from runs with attention-worthy conditions.
    SIGNALS is NOT a run state - it's a computed projection.
    """

    tenant_id = get_tenant_id_from_auth(request)

    # Build query for runs with signals (risk != NORMAL or evidence issues)
    where_clauses = [
        "tenant_id = :tenant_id",
        "(risk_level != 'NORMAL' OR evidence_health != 'FLOWING' OR evaluation_outcome IN ('BREACH', 'NEAR_THRESHOLD'))",
    ]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    # Filter by risk_type if signal_type specified
    if signal_type:
        if signal_type == "COST_RISK":
            where_clauses.append("risk_type = 'COST'")
        elif signal_type == "TIME_RISK":
            where_clauses.append("risk_type = 'TIME'")
        elif signal_type == "TOKEN_RISK":
            where_clauses.append("risk_type = 'TOKENS'")
        elif signal_type == "EVIDENCE_DEGRADED":
            where_clauses.append("evidence_health != 'FLOWING'")
        elif signal_type == "POLICY_BREACH":
            where_clauses.append("evaluation_outcome = 'BREACH'")

    if severity:
        if severity == "HIGH":
            where_clauses.append("(evaluation_outcome = 'BREACH' OR risk_level = 'VIOLATED')")
        elif severity == "MEDIUM":
            where_clauses.append("(evaluation_outcome = 'NEAR_THRESHOLD' OR risk_level = 'AT_RISK')")
        elif severity == "LOW":
            where_clauses.append("risk_level = 'NEAR_THRESHOLD'")

    where_sql = " AND ".join(where_clauses)

    # Query runs with signals
    sql = f"""
        SELECT
            run_id, state, started_at, risk_level, evidence_health,
            policy_id, policy_name, policy_scope, limit_type,
            threshold_value, threshold_unit, threshold_source,
            risk_type, actual_value, evaluation_outcome, proximity_pct
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY
            CASE evaluation_outcome
                WHEN 'BREACH' THEN 1
                WHEN 'NEAR_THRESHOLD' THEN 2
                ELSE 3
            END,
            started_at DESC
        LIMIT :limit
    """

    try:
        result = await session.execute(text(sql), params)
        rows = result.mappings().all()

        # Import fingerprint computation
        from app.services.activity.signal_identity import compute_signal_fingerprint_from_row
        from app.services.activity.signal_feedback_service import SignalFeedbackService

        # First pass: compute fingerprints and build signal data
        signal_data = []
        fingerprints: list[str] = []

        for row in rows:
            # Determine signal type and severity
            sig_type = "POLICY_BREACH" if row["evaluation_outcome"] == "BREACH" else \
                       f"{row['risk_type']}_RISK" if row.get("risk_type") else \
                       "EVIDENCE_DEGRADED" if row["evidence_health"] != "FLOWING" else "UNKNOWN"

            sev = "HIGH" if row["evaluation_outcome"] == "BREACH" or row["risk_level"] == "VIOLATED" else \
                  "MEDIUM" if row["evaluation_outcome"] == "NEAR_THRESHOLD" or row["risk_level"] == "AT_RISK" else \
                  "LOW"

            summary = f"Run {row['run_id'][:8]}... " + (
                f"breached {row.get('limit_type', 'limit')}" if row["evaluation_outcome"] == "BREACH" else
                f"at {row.get('proximity_pct', 0):.1f}% of threshold" if row["evaluation_outcome"] == "NEAR_THRESHOLD" else
                "requires attention"
            )

            # Compute canonical fingerprint
            signal_row = {
                "run_id": row["run_id"],
                "signal_type": sig_type,
                "risk_type": row.get("risk_type") or "UNKNOWN",
                "evaluation_outcome": row.get("evaluation_outcome") or "UNKNOWN",
            }
            fingerprint = compute_signal_fingerprint_from_row(signal_row)
            fingerprints.append(fingerprint)

            signal_data.append({
                "row": row,
                "sig_type": sig_type,
                "sev": sev,
                "summary": summary,
                "fingerprint": fingerprint,
            })

        # Fetch feedback for all signals in bulk
        feedback_service = SignalFeedbackService(session)
        feedback_map = await feedback_service.get_bulk_signal_feedback(tenant_id, fingerprints)

        # Second pass: build SignalProjection objects with feedback
        signals = []
        for data in signal_data:
            row = data["row"]
            fingerprint = data["fingerprint"]
            feedback = feedback_map.get(fingerprint)

            # Build feedback model if exists
            feedback_model = None
            if feedback:
                feedback_model = SignalFeedbackModel(
                    acknowledged=feedback.acknowledged,
                    acknowledged_by=feedback.acknowledged_by,
                    acknowledged_at=feedback.acknowledged_at,
                    suppressed_until=feedback.suppressed_until,
                )

            signals.append(SignalProjection(
                signal_id=f"sig-{row['run_id'][:8]}-{data['sig_type'].lower()}",
                signal_fingerprint=fingerprint,
                run_id=row["run_id"],
                signal_type=data["sig_type"],
                severity=data["sev"],
                summary=data["summary"],
                policy_context=_extract_policy_context(dict(row)),
                created_at=row["started_at"] or datetime.utcnow(),
                feedback=feedback_model,
            ))

        return SignalsResponse(
            signals=signals,
            total=len(signals),
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Activity metrics (V2)",
    description="""
    Returns aggregated activity metrics with topic-aware counts.

    Extends the /risk-signals endpoint with:
    - Live/Completed run counts
    - Evidence health breakdown
    - Risk type breakdown (COST, TIME, TOKENS, RATE)

    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    Panels: LIVE-O1, LIVE-O2, LIVE-O4, COMP-O1, COMP-O3
    """,
)
async def get_activity_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> MetricsResponse:
    """
    Get aggregated activity metrics (V2).

    Provides counts for:
    - Risk levels
    - Topic (LIVE vs COMPLETED)
    - Evidence health
    - Risk types
    """

    tenant_id = get_tenant_id_from_auth(request)

    sql = text("""
        SELECT
            -- Risk counts
            COUNT(*) FILTER (WHERE risk_level IN ('NEAR_THRESHOLD', 'AT_RISK', 'VIOLATED')) as at_risk_count,
            COUNT(*) FILTER (WHERE risk_level = 'VIOLATED') as violated_count,
            COUNT(*) FILTER (WHERE risk_level = 'NEAR_THRESHOLD') as near_threshold_count,
            COUNT(*) FILTER (WHERE risk_level != 'NORMAL') as total_at_risk,

            -- Topic counts
            COUNT(*) FILTER (WHERE state = 'LIVE') as live_count,
            COUNT(*) FILTER (WHERE state = 'COMPLETED') as completed_count,

            -- Evidence health
            COUNT(*) FILTER (WHERE evidence_health = 'FLOWING') as evidence_flowing_count,
            COUNT(*) FILTER (WHERE evidence_health = 'DEGRADED') as evidence_degraded_count,
            COUNT(*) FILTER (WHERE evidence_health = 'MISSING') as evidence_missing_count,

            -- Risk type counts (from evaluation_outcome != OK)
            COUNT(*) FILTER (WHERE risk_type = 'COST' AND evaluation_outcome != 'OK') as cost_risk_count,
            COUNT(*) FILTER (WHERE risk_type = 'TIME' AND evaluation_outcome != 'OK') as time_risk_count,
            COUNT(*) FILTER (WHERE risk_type = 'TOKENS' AND evaluation_outcome != 'OK') as token_risk_count,
            COUNT(*) FILTER (WHERE risk_type = 'RATE' AND evaluation_outcome != 'OK') as rate_risk_count
        FROM v_runs_o2
        WHERE tenant_id = :tenant_id
          AND (state = 'LIVE' OR completed_at >= NOW() - INTERVAL '24 hours')
    """)

    result = await session.execute(sql, {"tenant_id": tenant_id})
    row = result.mappings().first()

    if not row:
        return MetricsResponse(
            at_risk_count=0, violated_count=0, near_threshold_count=0, total_at_risk=0,
            live_count=0, completed_count=0,
            evidence_flowing_count=0, evidence_degraded_count=0, evidence_missing_count=0,
            cost_risk_count=0, time_risk_count=0, token_risk_count=0, rate_risk_count=0,
            generated_at=datetime.utcnow(),
        )

    return MetricsResponse(
        at_risk_count=row["at_risk_count"] or 0,
        violated_count=row["violated_count"] or 0,
        near_threshold_count=row["near_threshold_count"] or 0,
        total_at_risk=row["total_at_risk"] or 0,
        live_count=row["live_count"] or 0,
        completed_count=row["completed_count"] or 0,
        evidence_flowing_count=row["evidence_flowing_count"] or 0,
        evidence_degraded_count=row["evidence_degraded_count"] or 0,
        evidence_missing_count=row["evidence_missing_count"] or 0,
        cost_risk_count=row["cost_risk_count"] or 0,
        time_risk_count=row["time_risk_count"] or 0,
        token_risk_count=row["token_risk_count"] or 0,
        rate_risk_count=row["rate_risk_count"] or 0,
        generated_at=datetime.utcnow(),
    )


@router.get(
    "/threshold-signals",
    response_model=ThresholdSignalsResponse,
    summary="Threshold proximity signals (V2)",
    description="""
    Returns runs with typed threshold proximity information.

    Used for panels showing:
    - Runs approaching limits (NEAR_THRESHOLD)
    - Runs that breached limits (BREACH)
    - Typed by limit category (COST, TIME, TOKENS, RATE)

    Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    Panels: LIVE-O2, COMP-O4, SIG-O2
    """,
)
async def get_threshold_signals(
    request: Request,
    # Risk type filter
    risk_type: Annotated[RiskType | None, Query(description="Filter by risk type")] = None,
    # Evaluation filter
    evaluation_outcome: Annotated[EvaluationOutcome | None, Query(description="Filter by evaluation outcome")] = None,
    # State filter (optional - allows filtering to LIVE or COMPLETED)
    state: Annotated[RunState | None, Query(description="Filter by run state")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max signals to return")] = 20,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> ThresholdSignalsResponse:
    """
    Get threshold proximity signals (V2).

    Returns runs with threshold evaluation data.
    Can be filtered by risk_type (COST, TIME, TOKENS, RATE).
    """

    tenant_id = get_tenant_id_from_auth(request)

    # Build query - only runs with threshold data
    where_clauses = [
        "tenant_id = :tenant_id",
        "threshold_value IS NOT NULL",
        "evaluation_outcome IS NOT NULL",
        "evaluation_outcome != 'ADVISORY'",  # Exclude advisory (no actual limit)
    ]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

    if risk_type:
        where_clauses.append("risk_type = :risk_type")
        params["risk_type"] = risk_type.value

    if evaluation_outcome:
        where_clauses.append("evaluation_outcome = :evaluation_outcome")
        params["evaluation_outcome"] = evaluation_outcome.value

    if state:
        where_clauses.append("state = :state")
        params["state"] = state.value

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            run_id, limit_type, proximity_pct, evaluation_outcome,
            policy_id, policy_name, policy_scope,
            threshold_value, threshold_unit, threshold_source,
            risk_type, actual_value
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY
            CASE evaluation_outcome
                WHEN 'BREACH' THEN 1
                WHEN 'NEAR_THRESHOLD' THEN 2
                ELSE 3
            END,
            proximity_pct DESC NULLS LAST
        LIMIT :limit
    """

    try:
        result = await session.execute(text(sql), params)
        rows = result.mappings().all()

        signals = [
            ThresholdSignal(
                run_id=row["run_id"],
                limit_type=row["limit_type"] or "UNKNOWN",
                proximity_pct=float(row["proximity_pct"]) if row["proximity_pct"] else 0.0,
                evaluation_outcome=row["evaluation_outcome"],
                policy_context=_extract_policy_context(dict(row)),
            )
            for row in rows
        ]

        return ThresholdSignalsResponse(
            signals=signals,
            total=len(signals),
            risk_type_filter=risk_type.value if risk_type else None,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# Signal Feedback Endpoints (V2)
# =============================================================================


@router.post(
    "/signals/{signal_fingerprint}/ack",
    response_model=SignalAckResponse,
    summary="Acknowledge a signal",
    description="""
    Acknowledge a signal to record responsibility.

    INVARIANTS:
    - SIGNAL-ID-001: The signal_fingerprint MUST match the server-computed fingerprint
    - SIGNAL-ACK-001: Acknowledgement records responsibility but does not hide signals
    - ATTN-DAMP-001: Acknowledged signals receive 0.6x ranking dampener

    The server validates the signal exists before accepting acknowledgment.
    If the signal is not currently visible, returns 409 Conflict.

    Reference: Attention Feedback Loop Implementation Plan
    """,
    responses={
        200: {"description": "Signal acknowledged successfully"},
        409: {"description": "Signal not currently visible"},
    },
)
async def acknowledge_signal(
    request: Request,
    signal_fingerprint: Annotated[str, Path(description="Canonical signal fingerprint (sig-{hash})")],
    body: SignalAckRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SignalAckResponse:
    """
    Acknowledge a signal.

    Records acknowledgment in the audit_ledger.
    The signal remains visible but receives a ranking dampener (0.6x).
    """
    tenant_id = get_tenant_id_from_auth(request)
    actor_id = get_actor_id_from_auth(request)

    from app.services.activity.signal_feedback_service import SignalFeedbackService

    service = SignalFeedbackService(session)

    try:
        result = await service.acknowledge_signal(
            tenant_id=tenant_id,
            run_id=body.run_id,
            signal_type=body.signal_type,
            risk_type=body.risk_type,
            actor_id=actor_id,
            reason=body.comment,
        )

        return SignalAckResponse(
            signal_fingerprint=result.signal_fingerprint,
            acknowledged=result.acknowledged,
            acknowledged_by=result.acknowledged_by,
            acknowledged_at=result.acknowledged_at,
        )

    except ValueError as e:
        # Signal not currently visible
        raise HTTPException(
            status_code=409,
            detail={
                "error": "signal_not_visible",
                "message": str(e),
                "hint": "Signal may have resolved or is no longer meeting threshold criteria",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "acknowledge_failed", "message": str(e)},
        )


@router.post(
    "/signals/{signal_fingerprint}/suppress",
    response_model=SignalSuppressResponse,
    summary="Suppress a signal temporarily",
    description="""
    Suppress a signal for a specified duration.

    INVARIANTS:
    - SIGNAL-SUPPRESS-001: Suppression is temporary (15-1440 minutes, max 24 hours)
    - SIGNAL-SCOPE-001: Suppression applies tenant-wide (actor_id is for accountability)
    - No permanent silencing allowed

    Suppressed signals are excluded from the attention queue until the
    suppression expires. After expiry, the signal reappears if still active.

    Reference: Attention Feedback Loop Implementation Plan
    """,
    responses={
        200: {"description": "Signal suppressed successfully"},
        400: {"description": "Invalid duration (must be 15-1440 minutes)"},
        409: {"description": "Signal not currently visible"},
    },
)
async def suppress_signal(
    request: Request,
    signal_fingerprint: Annotated[str, Path(description="Canonical signal fingerprint (sig-{hash})")],
    body: SignalSuppressRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SignalSuppressResponse:
    """
    Suppress a signal temporarily.

    Records suppression in the audit_ledger with a suppress_until timestamp.
    The signal is excluded from the attention queue until expiry.
    """
    tenant_id = get_tenant_id_from_auth(request)
    actor_id = get_actor_id_from_auth(request)

    # Validate duration constraints
    if body.duration_minutes < 15 or body.duration_minutes > 1440:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_duration",
                "message": f"Duration must be 15-1440 minutes, got {body.duration_minutes}",
                "constraint": "SIGNAL-SUPPRESS-001",
            },
        )

    from app.services.activity.signal_feedback_service import SignalFeedbackService

    service = SignalFeedbackService(session)

    try:
        result = await service.suppress_signal(
            tenant_id=tenant_id,
            run_id=body.run_id,
            signal_type=body.signal_type,
            risk_type=body.risk_type,
            actor_id=actor_id,
            duration_minutes=body.duration_minutes,
            reason=body.reason,
        )

        return SignalSuppressResponse(
            signal_fingerprint=result.signal_fingerprint,
            suppressed_until=result.suppressed_until,
        )

    except ValueError as e:
        # Signal not currently visible or invalid duration
        if "duration" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_duration",
                    "message": str(e),
                    "constraint": "SIGNAL-SUPPRESS-001",
                },
            )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "signal_not_visible",
                "message": str(e),
                "hint": "Signal may have resolved or is no longer meeting threshold criteria",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "suppress_failed", "message": str(e)},
        )


def get_actor_id_from_auth(request: Request) -> str:
    """
    Extract actor ID from request auth context.

    Falls back to 'unknown' if not available (should not happen in production).
    """
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context:
        return getattr(auth_context, "user_id", None) or getattr(auth_context, "actor_id", "unknown")
    return "unknown"
