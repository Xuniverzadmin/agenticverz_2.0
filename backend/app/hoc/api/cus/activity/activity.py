# capability_id: CAP-012
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
- GET /activity/live              → LIVE runs with policy context
- GET /activity/completed         → COMPLETED runs with policy context
- GET /activity/signals           → Synthesized attention signals
- GET /activity/metrics           → Aggregated activity metrics
- GET /activity/threshold-signals → Threshold proximity tracking

V1 Endpoints (Legacy):
- GET /activity/runs              → [DEPRECATED] O2 list with filters
- GET /activity/runs/{run_id}     → O3 detail
- GET /activity/runs/{run_id}/evidence → O4 context (preflight)
- GET /activity/runs/{run_id}/proof    → O5 raw (preflight)
- GET /activity/summary/by-status → COMP-O3 status summary
- GET /activity/runs/by-dimension → [DEPRECATED] dimension grouping
- GET /activity/patterns          → SIG-O3 pattern detection
- GET /activity/cost-analysis     → SIG-O4 cost anomalies
- GET /activity/attention-queue   → SIG-O5 attention ranking
- GET /activity/risk-signals      → Risk signal aggregates

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
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel
from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)

# =============================================================================
# Logging
# =============================================================================

logger = logging.getLogger(__name__)
from app.schemas.response import wrap_dict

# NOTE: All L5 engine access routed through L4 operation registry
# Direct L5 imports removed per PIN-491 construction plan

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
    prefix="/activity",
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
# UC-MON Determinism: as_of Contract
# =============================================================================


def _normalize_as_of(as_of: str | None) -> str:
    """
    Normalize as_of deterministic read watermark.

    UC-MON Contract:
    - If provided: validate ISO-8601 UTC format
    - If absent: generate once per request (server timestamp)
    - Same as_of + same filters = stable results
    """
    if as_of is not None:
        try:
            datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_as_of", "message": "as_of must be ISO-8601 UTC"},
            )
        return as_of
    return datetime.utcnow().isoformat() + "Z"


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
    session = Depends(get_session_dep),
) -> RunListResponse:
    """List runs with unified query filters. READ-ONLY from v_runs_o2 view."""

    tenant_id = get_tenant_id_from_auth(request)

    # DEPRECATION: Use /activity/live or /activity/completed instead
    user_agent = request.headers.get("user-agent", "unknown")
    logger.warning(
        "DEPRECATED_ENDPOINT_CALLED: /activity/runs | "
        f"tenant_id={tenant_id} | "
        f"state={state.value if state else 'none'} | "
        f"user_agent={user_agent[:100]} | "
        "migration_path=Use /activity/live or /activity/completed"
    )

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_runs",
                "project_id": project_id,
                "state": state.value if state else None,
                "status": status,
                "risk": risk,
                "risk_level": [r.value for r in risk_level] if risk_level else None,
                "latency_bucket": [lb.value for lb in latency_bucket] if latency_bucket else None,
                "evidence_health": [e.value for e in evidence_health] if evidence_health else None,
                "integrity_status": [i.value for i in integrity_status] if integrity_status else None,
                "source": [s.value for s in source] if source else None,
                "provider_type": [p.value for p in provider_type] if provider_type else None,
                "is_synthetic": is_synthetic,
                "started_after": started_after,
                "started_before": started_before,
                "completed_after": completed_after,
                "completed_before": completed_before,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by.value,
                "sort_order": sort_order.value,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    items = [
        RunSummary(
            run_id=item.run_id,
            tenant_id=item.tenant_id,
            project_id=item.project_id,
            is_synthetic=item.is_synthetic,
            source=item.source,
            provider_type=item.provider_type,
            state=item.state,
            status=item.status,
            started_at=item.started_at,
            last_seen_at=item.last_seen_at,
            completed_at=item.completed_at,
            duration_ms=item.duration_ms,
            risk_level=item.risk_level,
            latency_bucket=item.latency_bucket,
            evidence_health=item.evidence_health,
            integrity_status=item.integrity_status,
            incident_count=item.incident_count,
            policy_draft_count=item.policy_draft_count,
            policy_violation=item.policy_violation,
            input_tokens=item.input_tokens,
            output_tokens=item.output_tokens,
            estimated_cost_usd=item.estimated_cost_usd,
        )
        for item in result.items
    ]

    has_more = result.has_more
    next_offset = offset + limit if has_more else None

    return RunListResponse(
        items=items,
        total=result.total,
        has_more=has_more,
        filters_applied=result.filters_applied,
        pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
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
    session = Depends(get_session_dep),
) -> RunDetailResponse:
    """Get run detail (O3). Tenant isolation enforced."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_run_detail", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunDetailResponse(
        run_id=result.run_id,
        tenant_id=result.tenant_id,
        project_id=result.project_id,
        is_synthetic=result.is_synthetic,
        source=result.source,
        provider_type=result.provider_type,
        state=result.state,
        status=result.status,
        started_at=result.started_at,
        last_seen_at=result.last_seen_at,
        completed_at=result.completed_at,
        duration_ms=result.duration_ms,
        risk_level=result.risk_level,
        latency_bucket=result.latency_bucket,
        evidence_health=result.evidence_health,
        integrity_status=result.integrity_status,
        incident_count=result.incident_count,
        policy_draft_count=result.policy_draft_count,
        policy_violation=result.policy_violation,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=result.estimated_cost_usd,
        goal=result.goal,
        error_message=result.error_message,
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
    session = Depends(get_session_dep),
) -> StatusSummaryResponse:
    """Get run summary by status (COMP-O3). READ-ONLY from v_runs_o2."""

    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_status_summary",
                "state": state.value if state else None,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    total = result.total

    buckets = [
        StatusBucket(
            status=s.status,
            count=s.count,
            percentage=round((s.count / total * 100) if total > 0 else 0, 2),
        )
        for s in result.statuses
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
    session,
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
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_dimension_breakdown",
                "dimension": dim.value,
                "state": state.value,
                "limit": limit,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    groups = [
        DimensionGroup(
            value=g.value,
            count=g.count,
            percentage=g.percentage,
        )
        for g in result.groups
    ]

    return DimensionBreakdownResponse(
        dimension=result.dimension,
        groups=groups,
        total_runs=result.total_runs,
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
    session = Depends(get_session_dep),
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
    session = Depends(get_session_dep),
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
    session = Depends(get_session_dep),
) -> DimensionBreakdownResponse:
    """[INTERNAL] Get runs grouped by dimension with optional state. NOT FOR PANELS."""
    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_dimension_breakdown",
                "dimension": dim.value,
                "state": state.value if state else None,
                "limit": limit,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    groups = [
        DimensionGroup(value=g.value, count=g.count, percentage=g.percentage)
        for g in result.groups
    ]

    return DimensionBreakdownResponse(
        dimension=result.dimension,
        groups=groups,
        total_runs=result.total_runs,
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
    session = Depends(get_session_dep),
) -> PatternDetectionResponse:
    """Detect instability patterns (SIG-O3). READ-ONLY from aos_traces/aos_trace_steps."""

    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_patterns", "window_hours": window_hours, "limit": limit},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    # Map L4 PatternDetectionResult to L2 PatternDetectionResponse
    # Compute window times from generated_at and window_hours
    window_end = result.generated_at
    window_start = window_end - timedelta(hours=result.window_hours)

    return PatternDetectionResponse(
        patterns=[
            PatternMatchResponse(
                pattern_type=p.pattern_type,
                run_id=p.affected_run_ids[0] if p.affected_run_ids else "",
                confidence=p.confidence,
                details={
                    "title": p.title,
                    "description": p.description,
                    "dimension": p.dimension,
                    "occurrence_count": p.occurrence_count,
                    "severity": p.severity,
                    "first_seen": p.first_seen.isoformat() if p.first_seen else None,
                    "last_seen": p.last_seen.isoformat() if p.last_seen else None,
                },
            )
            for p in result.patterns
        ],
        window_start=window_start,
        window_end=window_end,
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
    anomaly_threshold: Annotated[float, Query(ge=1.0, le=5.0, description="Threshold percentage")] = 50.0,
    session = Depends(get_session_dep),
) -> CostAnalysisResponse:
    """Analyze cost anomalies (SIG-O4). READ-ONLY from runs table."""

    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_cost_analysis", "baseline_days": baseline_days, "threshold_pct": anomaly_threshold},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    # Map L4 CostAnalysisResult to L2 CostAnalysisResponse
    # Adapt anomalies to agent-style response for backwards compatibility
    return CostAnalysisResponse(
        agents=[
            AgentCostResponse(
                agent_id=a.anomaly_id,
                current_cost_usd=a.actual_cost_usd,
                run_count=len(a.source_run_ids),
                baseline_avg_usd=a.baseline_cost_usd,
                baseline_p95_usd=None,
                z_score=a.severity,  # Use severity as z-score proxy
                is_anomaly=True,  # All items in anomalies list are anomalies
            )
            for a in result.anomalies
        ],
        total_anomalies=len(result.anomalies),
        total_cost_usd=result.total_cost_analyzed_usd,
        window_current=f"last_{baseline_days}_days",
        window_baseline=f"baseline_{result.baseline_period_days}_days",
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
    session = Depends(get_session_dep),
) -> AttentionQueueResponse:
    """Get attention queue (SIG-O5). READ-ONLY from v_runs_o2."""

    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_attention_queue", "limit": limit},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    # Map L4 AttentionQueueResult to L2 AttentionQueueResponse
    return AttentionQueueResponse(
        queue=[
            AttentionItemResponse(
                run_id=item.source_run_id or item.signal_id,
                attention_score=item.attention_score,
                reasons=[item.attention_reason] if item.attention_reason else [],
                state="COMPLETED",  # Default state for signals
                status="ATTENTION",  # Signals are attention items
                started_at=item.created_at,
            )
            for item in result.items
        ],
        total_attention_items=result.total,
        weights_version="v1.0",  # Fixed version from L4 service
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
    session = Depends(get_session_dep),
) -> RiskSignalsResponse:
    """
    Returns aggregated risk signal counts.

    Supports: activity.risk_signals capability
    Consumers: Overview panels, Activity summary panels
    """
    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_risk_signals"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    return RiskSignalsResponse(
        at_risk_count=result.at_risk_count,
        violated_count=result.violated_count,
        at_risk_level_count=result.by_risk_type.get("AT_RISK", 0),
        near_threshold_count=result.near_threshold_count,
        total_at_risk=result.total_at_risk,
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


def _policy_context_from_l5(pc: Any) -> PolicyContext:
    """Convert L5 PolicyContextResult dataclass to L2 PolicyContext Pydantic model."""
    return PolicyContext(
        policy_id=pc.policy_id,
        policy_name=pc.policy_name,
        policy_scope=pc.policy_scope,
        limit_type=pc.limit_type,
        threshold_value=pc.threshold_value,
        threshold_unit=pc.threshold_unit,
        threshold_source=pc.threshold_source,
        evaluation_outcome=pc.evaluation_outcome,
        actual_value=pc.actual_value,
        risk_type=pc.risk_type,
        proximity_pct=pc.proximity_pct,
        facade_ref=getattr(pc, "facade_ref", None),
        threshold_ref=getattr(pc, "threshold_ref", None),
        violation_ref=getattr(pc, "violation_ref", None),
    )


def _run_summary_v2_from_l5(item: Any) -> RunSummaryV2:
    """Convert L5 RunSummaryV2Result dataclass to L2 RunSummaryV2 Pydantic model."""
    return RunSummaryV2(
        run_id=item.run_id,
        tenant_id=item.tenant_id,
        project_id=item.project_id,
        is_synthetic=item.is_synthetic,
        source=item.source,
        provider_type=item.provider_type,
        state=item.state,
        status=item.status,
        started_at=item.started_at,
        last_seen_at=item.last_seen_at,
        completed_at=item.completed_at,
        duration_ms=item.duration_ms,
        risk_level=item.risk_level,
        latency_bucket=item.latency_bucket,
        evidence_health=item.evidence_health,
        integrity_status=item.integrity_status,
        incident_count=item.incident_count,
        policy_draft_count=item.policy_draft_count,
        policy_violation=item.policy_violation,
        input_tokens=item.input_tokens,
        output_tokens=item.output_tokens,
        estimated_cost_usd=item.estimated_cost_usd,
        policy_context=_policy_context_from_l5(item.policy_context) if item.policy_context else _extract_policy_context({}),
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
    # UC-MON Determinism
    as_of: Annotated[str | None, Query(description="Deterministic read watermark (ISO-8601 UTC)")] = None,
    # Dependencies
    session = Depends(get_session_dep),
) -> LiveRunsResponse:
    """
    List LIVE runs with policy context.

    State=LIVE is HARDCODED - cannot be overridden.
    This is the canonical endpoint for the LIVE topic.
    """

    tenant_id = get_tenant_id_from_auth(request)
    effective_as_of = _normalize_as_of(as_of)

    # Route through L4 registry — state=LIVE hardcoded in L5 facade
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_live_runs",
                "as_of": effective_as_of,
                "project_id": project_id,
                "risk_level": [r.value for r in risk_level] if risk_level else None,
                "evidence_health": [e.value for e in evidence_health] if evidence_health else None,
                "source": [s.value for s in source] if source else None,
                "provider_type": [p.value for p in provider_type] if provider_type else None,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    items = [_run_summary_v2_from_l5(item) for item in result.items]

    has_more = result.has_more
    next_offset = offset + limit if has_more else None

    return LiveRunsResponse(
        items=items,
        total=result.total,
        has_more=has_more,
        pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=datetime.utcnow(),
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
    # UC-MON Determinism
    as_of: Annotated[str | None, Query(description="Deterministic read watermark (ISO-8601 UTC)")] = None,
    # Dependencies
    session = Depends(get_session_dep),
) -> CompletedRunsResponse:
    """
    List COMPLETED runs with policy context.

    State=COMPLETED is HARDCODED - cannot be overridden.
    This is the canonical endpoint for the COMPLETED topic.
    """

    tenant_id = get_tenant_id_from_auth(request)
    effective_as_of = _normalize_as_of(as_of)

    # Route through L4 registry — state=COMPLETED hardcoded in L5 facade
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_completed_runs",
                "as_of": effective_as_of,
                "project_id": project_id,
                "status": status,
                "risk_level": [r.value for r in risk_level] if risk_level else None,
                "completed_after": completed_after,
                "completed_before": completed_before,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by.value,
                "sort_order": sort_order.value,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    items = [_run_summary_v2_from_l5(item) for item in result.items]

    has_more = result.has_more
    next_offset = offset + limit if has_more else None

    return CompletedRunsResponse(
        items=items,
        total=result.total,
        has_more=has_more,
        pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=datetime.utcnow(),
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
    # UC-MON Determinism
    as_of: Annotated[str | None, Query(description="Deterministic read watermark (ISO-8601 UTC)")] = None,
    # Dependencies
    session = Depends(get_session_dep),
) -> SignalsResponse:
    """
    List activity signals (V2 projection).

    Synthesizes signals from runs with attention-worthy conditions.
    SIGNALS is NOT a run state - it's a computed projection.
    """

    tenant_id = get_tenant_id_from_auth(request)
    effective_as_of = _normalize_as_of(as_of)

    # Route through L4 registry — signal synthesis handled by L5 facade
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_signals",
                "as_of": effective_as_of,
                "project_id": project_id,
                "signal_type": signal_type,
                "severity": severity,
                "limit": limit,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    signals = []
    for sig in result.signals:
        feedback_model = None
        if sig.feedback:
            feedback_model = SignalFeedbackModel(
                acknowledged=sig.feedback.acknowledged,
                acknowledged_by=sig.feedback.acknowledged_by,
                acknowledged_at=sig.feedback.acknowledged_at,
                suppressed_until=sig.feedback.suppressed_until,
            )

        signals.append(SignalProjection(
            signal_id=sig.signal_id,
            signal_fingerprint=sig.signal_fingerprint,
            run_id=sig.run_id,
            signal_type=sig.signal_type,
            severity=sig.severity,
            summary=sig.summary,
            policy_context=_policy_context_from_l5(sig.policy_context),
            created_at=sig.created_at,
            feedback=feedback_model,
        ))

    return SignalsResponse(
        signals=signals,
        total=result.total,
        generated_at=datetime.utcnow(),
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
    session = Depends(get_session_dep),
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

    # Route through L4 registry
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_metrics"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    return MetricsResponse(
        at_risk_count=result.at_risk_count,
        violated_count=result.violated_count,
        near_threshold_count=result.near_threshold_count,
        total_at_risk=result.total_at_risk,
        live_count=result.live_count,
        completed_count=result.completed_count,
        evidence_flowing_count=result.evidence_flowing_count,
        evidence_degraded_count=result.evidence_degraded_count,
        evidence_missing_count=result.evidence_missing_count,
        cost_risk_count=result.cost_risk_count,
        time_risk_count=result.time_risk_count,
        token_risk_count=result.token_risk_count,
        rate_risk_count=result.rate_risk_count,
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
    session = Depends(get_session_dep),
) -> ThresholdSignalsResponse:
    """
    Get threshold proximity signals (V2).

    Returns runs with threshold evaluation data.
    Can be filtered by risk_type (COST, TIME, TOKENS, RATE).
    """

    tenant_id = get_tenant_id_from_auth(request)

    # Route through L4 registry
    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_threshold_signals",
                "risk_type": risk_type.value if risk_type else None,
                "evaluation_outcome": evaluation_outcome.value if evaluation_outcome else None,
                "state": state.value if state else None,
                "limit": limit,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    signals = [
        ThresholdSignal(
            run_id=sig.run_id,
            limit_type=sig.limit_type,
            proximity_pct=sig.proximity_pct,
            evaluation_outcome=sig.evaluation_outcome,
            policy_context=_policy_context_from_l5(sig.policy_context),
        )
        for sig in result.signals
    ]

    return ThresholdSignalsResponse(
        signals=signals,
        total=result.total,
        risk_type_filter=risk_type.value if risk_type else None,
        generated_at=datetime.utcnow(),
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
    session = Depends(get_session_dep),
) -> SignalAckResponse:
    """
    Acknowledge a signal.

    Records acknowledgment in the audit_ledger.
    The signal remains visible but receives a ranking dampener (0.6x).
    """
    tenant_id = get_tenant_id_from_auth(request)
    actor_id = get_actor_id_from_auth(request)

    # Use L4 registry for signal feedback
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "activity.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "acknowledge_signal",
                    "signal_id": signal_fingerprint,
                    "acknowledged_by": actor_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        # Map L4 AcknowledgeResult to L2 SignalAckResponse
        return SignalAckResponse(
            signal_fingerprint=result.signal_id,
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
    session = Depends(get_session_dep),
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

    # Use L4 registry for signal feedback
    registry = get_operation_registry()

    # Convert minutes to hours for facade
    duration_hours = max(1, body.duration_minutes // 60)

    try:
        op = await registry.execute(
            "activity.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "suppress_signal",
                    "signal_id": signal_fingerprint,
                    "suppressed_by": actor_id,
                    "duration_hours": duration_hours,
                    "reason": body.reason,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        # Map L4 SuppressResult to L2 SignalSuppressResponse
        return SignalSuppressResponse(
            signal_fingerprint=result.signal_id,
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
