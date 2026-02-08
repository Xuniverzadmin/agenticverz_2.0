# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Location: hoc/cus/activity/L5_engines/activity_facade.py
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: WorkerRun, AuditLedger (via driver)
#   Writes: none (read-only facade)
# Role: Activity Facade - Centralized access to activity domain operations
# Callers: app.api.activity (L2)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# ============================================================================
# ARCHITECTURAL LOCK (PIN-519)
# ============================================================================
# This is the ONLY Activity Facade in the HOC tree.
#
# RED-LINE CONSTRAINTS:
#   - Cross-domain access is FORBIDDEN here
#   - All aggregation must go through L4 coordinators
#   - No persistence (read-only via L6 drivers)
#   - No policy evaluation (delegated to L4)
#   - No integrity computation (delegated to L4)
#
# ENFORCEMENT:
#   - CI check 31: check_single_activity_facade()
#   - Test: test_single_activity_facade_exists()
#
# Any duplicate ActivityFacade in app/hoc/ is a CI-blocking violation.
# The legacy app/services/activity_facade.py is scheduled for deletion (PIN-511).
# ============================================================================

"""
Activity Facade (L5)

Provides unified access to activity domain operations.
This is the single entry point for all activity business logic.

Operations:
- get_runs: List runs with filters
- get_run_detail: Get run details (O3)
- get_run_evidence: Get run evidence context (O4)
- get_run_proof: Get run integrity proof (O5)
- get_status_summary: Get runs grouped by status
- get_patterns: Pattern detection (SIG-O3)
- get_cost_analysis: Cost anomalies (SIG-O4)
- get_attention_queue: Attention ranking (SIG-O5)
- get_live_runs: V2 live runs with policy context
- get_completed_runs: V2 completed runs with policy context
- get_signals: V2 synthesized signals
- get_metrics: V2 activity metrics
- get_threshold_signals: V2 threshold proximity signals
- get_risk_signals: Risk signal aggregates
- acknowledge_signal: Acknowledge a signal
- suppress_signal: Suppress a signal

Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Protocol

from app.hoc.cus.activity.L6_drivers.activity_read_driver import (
    get_activity_read_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.hoc.cus.activity.L6_drivers.activity_read_driver import ActivityReadDriver
from app.hoc.cus.activity.L5_engines.attention_ranking import AttentionRankingService
from app.hoc.cus.activity.L5_engines.cost_analysis import CostAnalysisService
from app.hoc.cus.activity.L5_engines.pattern_detection import PatternDetectionService
from app.hoc.cus.activity.L5_engines.signal_feedback_engine import (
    SignalFeedbackService,
    AcknowledgeResult,
    SuppressResult,
    SignalFeedbackStatus,  # Canonical feedback state - engines own state DTOs
)
from app.hoc.cus.activity.L5_engines.signal_identity import compute_signal_fingerprint_from_row

# Import canonical enums from engines (engines own enums, facades import)
from app.hoc.cus.activity.L5_engines.activity_enums import (
    SignalType,
    SeverityLevel,
    RunState,
)

logger = logging.getLogger("nova.services.activity.facade")


# =============================================================================
# PIN-520: Protocols for coordinator injection (L5 purity)
# =============================================================================


class RunEvidenceCoordinatorPort(Protocol):
    """Protocol for run evidence coordinator (PIN-520 L5 purity)."""

    async def get_run_evidence(
        self, session: Any, tenant_id: str, run_id: str
    ) -> Any:
        """Get cross-domain evidence for a run."""
        ...


class RunProofCoordinatorPort(Protocol):
    """Protocol for run proof coordinator (PIN-520 L5 purity)."""

    async def get_run_proof(
        self, session: Any, tenant_id: str, run_id: str, include_payloads: bool
    ) -> Any:
        """Get integrity proof for a run."""
        ...


class SignalFeedbackCoordinatorPort(Protocol):
    """Protocol for signal feedback coordinator (PIN-520 L5 purity)."""

    async def get_signal_feedback(
        self, session: Any, tenant_id: str, fingerprint: str
    ) -> Any:
        """Get feedback status for a signal."""
        ...


# =============================================================================
# Result Dataclasses
# =============================================================================


@dataclass
class PolicyContextResult:
    """Policy context for a run."""

    policy_id: str
    policy_name: str
    policy_scope: str
    limit_type: str | None
    threshold_value: float | None
    threshold_unit: str | None
    threshold_source: str
    evaluation_outcome: str
    actual_value: float | None = None
    risk_type: str | None = None
    proximity_pct: float | None = None
    facade_ref: str | None = None
    threshold_ref: str | None = None
    violation_ref: str | None = None


@dataclass
class RunSummaryResult:
    """Run summary for list view."""

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
    incident_count: int = 0
    policy_draft_count: int = 0
    policy_violation: bool = False
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None


@dataclass
class RunSummaryV2Result(RunSummaryResult):
    """Run summary with policy context (V2)."""

    policy_context: PolicyContextResult | None = None


@dataclass
class RunListResult:
    """Result of listing runs."""

    items: list[RunSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunsResult:
    """
    Unified result for getting runs (V2).

    Consolidates LiveRunsResult and CompletedRunsResult per ACT-DUP-003.
    These were 100% structurally identical - only the name differed.

    Rule: If structures are identical today, they will diverge accidentally tomorrow.
    """

    state: str  # "LIVE" or "COMPLETED"
    items: list[RunSummaryV2Result]
    total: int
    has_more: bool
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Type aliases for backward compatibility during migration
LiveRunsResult = RunsResult
CompletedRunsResult = RunsResult


@dataclass
class RunDetailResult(RunSummaryResult):
    """
    Run detail (O3) - extends summary with additional fields.

    Refactored per ACT-DUP-002: Detail DTOs must extend summary DTOs,
    never re-declare shared fields. This prevents field drift and
    guarantees backward compatibility.
    """

    goal: str | None = None
    error_message: str | None = None


@dataclass
class RunEvidenceResult:
    """Run evidence context (O4)."""

    run_id: str
    incidents_caused: list[dict[str, Any]] = field(default_factory=list)
    policies_triggered: list[dict[str, Any]] = field(default_factory=list)
    decisions_made: list[dict[str, Any]] = field(default_factory=list)
    traces_linked: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RunProofResult:
    """Run integrity proof (O5)."""

    run_id: str
    integrity: dict[str, Any] = field(default_factory=dict)
    aos_traces: list[dict[str, Any]] = field(default_factory=list)
    aos_trace_steps: list[dict[str, Any]] = field(default_factory=list)
    raw_logs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class StatusCount:
    """Status count item."""

    status: str
    count: int


@dataclass
class StatusSummaryResult:
    """Summary by status."""

    statuses: list[StatusCount]
    total: int


# SignalFeedbackResult DELETED (ACT-DUP-001)
# Canonical feedback state is SignalFeedbackStatus from signal_feedback_service.py
# Rule: Feedback state is owned by engines, never redefined by facades


@dataclass
class SignalProjectionResult:
    """A signal projection."""

    signal_id: str
    signal_fingerprint: str
    run_id: str
    signal_type: str
    severity: str
    summary: str
    policy_context: PolicyContextResult
    created_at: datetime
    feedback: SignalFeedbackStatus | None = None  # Uses canonical engine DTO


@dataclass
class SignalsResult:
    """Result of getting signals (V2)."""

    signals: list[SignalProjectionResult]
    total: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetricsResult:
    """Activity metrics (V2)."""

    at_risk_count: int
    violated_count: int
    near_threshold_count: int
    total_at_risk: int
    live_count: int
    completed_count: int
    evidence_flowing_count: int
    evidence_degraded_count: int
    evidence_missing_count: int
    cost_risk_count: int
    time_risk_count: int
    token_risk_count: int
    rate_risk_count: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ThresholdSignalResult:
    """A threshold proximity signal."""

    run_id: str
    limit_type: str
    proximity_pct: float
    evaluation_outcome: str
    policy_context: PolicyContextResult


@dataclass
class ThresholdSignalsResult:
    """Result of getting threshold signals (V2)."""

    signals: list[ThresholdSignalResult]
    total: int
    risk_type_filter: str | None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RiskSignalsResult:
    """
    Risk signal aggregates.

    NOTE (ACT-DUP-004): This is a DERIVED PROJECTION of MetricsResult.
    The get_risk_signals() method extracts a subset from get_metrics().
    If you need full metrics, use MetricsResult directly.

    Rule: Derived views must be explicitly labeled as such.
    """

    at_risk_count: int
    violated_count: int
    near_threshold_count: int
    total_at_risk: int
    by_risk_type: dict[str, int] = field(default_factory=dict)


@dataclass
class DimensionGroupResult:
    """A dimension group with count and percentage."""

    value: str
    count: int
    percentage: float


@dataclass
class DimensionBreakdownResult:
    """Dimension breakdown result."""

    dimension: str
    groups: list[DimensionGroupResult]
    total_runs: int
    state_filter: str | None


# Import service result types for pass-through
from app.hoc.cus.activity.L5_engines.pattern_detection import (
    PatternDetectionResult,
    DetectedPattern,
)
from app.hoc.cus.activity.L5_engines.cost_analysis import (
    CostAnalysisResult,
    CostAnomaly,
)
from app.hoc.cus.activity.L5_engines.attention_ranking import (
    AttentionQueueResult,
    AttentionSignal,
)


# =============================================================================
# Facade Class
# =============================================================================


class ActivityFacade:
    """
    Unified facade for Activity domain operations.

    This class provides a single entry point for all activity business logic,
    delegating to specialized services where appropriate.

    Note: Services are instantiated per-request with the session, as they
    require the session in their constructors.

    PIN-520: Coordinators are now injected via L4 bridge instead of being
    imported directly from L4 orchestrator.
    """

    def __init__(
        self,
        run_evidence_coordinator: RunEvidenceCoordinatorPort | None = None,
        run_proof_coordinator: RunProofCoordinatorPort | None = None,
        signal_feedback_coordinator: SignalFeedbackCoordinatorPort | None = None,
    ) -> None:
        """Initialize facade with optional coordinator injection.

        Args:
            run_evidence_coordinator: Coordinator for cross-domain evidence queries (injected by L4 caller).
            run_proof_coordinator: Coordinator for integrity proof queries (injected by L4 caller).
            signal_feedback_coordinator: Coordinator for signal feedback queries (injected by L4 caller).

        PIN-520: L4 callers must inject coordinators. L5 must not import from hoc_spine.
        """
        self._run_evidence_coordinator = run_evidence_coordinator
        self._run_proof_coordinator = run_proof_coordinator
        self._signal_feedback_coordinator = signal_feedback_coordinator

    def _get_driver(self, session: AsyncSession) -> ActivityReadDriver:
        """Get activity read driver for this session."""
        return get_activity_read_driver(session)

    def _get_pattern_service(self, session: AsyncSession) -> PatternDetectionService:
        """Get pattern detection service for this session."""
        return PatternDetectionService(session)

    def _get_cost_service(self, session: AsyncSession) -> CostAnalysisService:
        """Get cost analysis service for this session."""
        return CostAnalysisService(session)

    def _get_attention_service(self, session: AsyncSession) -> AttentionRankingService:
        """Get attention ranking service for this session."""
        return AttentionRankingService(session)

    def _get_feedback_service(self, session: AsyncSession) -> SignalFeedbackService:
        """Get signal feedback service for this session."""
        return SignalFeedbackService(session)

    # =========================================================================
    # V1 Run Operations
    # =========================================================================

    async def get_runs(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
        state: str | None = None,
        status: list[str] | None = None,
        risk: bool = False,
        risk_level: list[str] | None = None,
        latency_bucket: list[str] | None = None,
        evidence_health: list[str] | None = None,
        integrity_status: list[str] | None = None,
        source: list[str] | None = None,
        provider_type: list[str] | None = None,
        is_synthetic: bool | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
        completed_after: datetime | None = None,
        completed_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "started_at",
        sort_order: str = "desc",
    ) -> RunListResult:
        """
        List runs with filters.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter
            state: LIVE or COMPLETED
            status: List of statuses to filter
            risk: If True, return only at-risk runs
            risk_level: Filter by risk levels
            latency_bucket: Filter by latency buckets
            evidence_health: Filter by evidence health
            integrity_status: Filter by integrity status
            source: Filter by run source
            provider_type: Filter by provider type
            is_synthetic: Filter by synthetic flag
            started_after: Filter by start time
            started_before: Filter by start time
            completed_after: Filter by completion time
            completed_before: Filter by completion time
            limit: Max items to return
            offset: Items to skip
            sort_by: Field to sort by
            sort_order: asc or desc

        Returns:
            RunListResult with items and pagination info
        """
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}
        where_clauses = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id}

        # Build filter clauses
        if project_id:
            where_clauses.append("project_id = :project_id")
            params["project_id"] = project_id
            filters_applied["project_id"] = project_id

        if state:
            where_clauses.append("state = :state")
            params["state"] = state
            filters_applied["state"] = state

        if status:
            where_clauses.append("status = ANY(:status)")
            params["status"] = status
            filters_applied["status"] = status

        if risk:
            where_clauses.append(
                "(risk_level != 'NORMAL' OR incident_count > 0 OR policy_violation = true)"
            )
            filters_applied["risk"] = True

        if risk_level:
            where_clauses.append("risk_level = ANY(:risk_level)")
            params["risk_level"] = risk_level
            filters_applied["risk_level"] = risk_level

        if latency_bucket:
            where_clauses.append("latency_bucket = ANY(:latency_bucket)")
            params["latency_bucket"] = latency_bucket
            filters_applied["latency_bucket"] = latency_bucket

        if evidence_health:
            where_clauses.append("evidence_health = ANY(:evidence_health)")
            params["evidence_health"] = evidence_health
            filters_applied["evidence_health"] = evidence_health

        if integrity_status:
            where_clauses.append("integrity_status = ANY(:integrity_status)")
            params["integrity_status"] = integrity_status
            filters_applied["integrity_status"] = integrity_status

        if source:
            where_clauses.append("source = ANY(:source)")
            params["source"] = source
            filters_applied["source"] = source

        if provider_type:
            where_clauses.append("provider_type = ANY(:provider_type)")
            params["provider_type"] = provider_type
            filters_applied["provider_type"] = provider_type

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
        sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        total = await driver.count_runs(where_sql, params)
        rows = await driver.fetch_runs(where_sql, params, sort_by, sort_dir, limit, offset)

        items = [
            RunSummaryResult(
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
                estimated_cost_usd=(
                    float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None
                ),
            )
            for row in rows
        ]

        has_more = offset + len(items) < total

        return RunListResult(
            items=items,
            total=total,
            has_more=has_more,
            filters_applied=filters_applied,
        )

    async def get_run_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> RunDetailResult | None:
        """
        Get run detail (O3).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            run_id: Run ID to fetch

        Returns:
            RunDetailResult or None if not found
        """
        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        row = await driver.fetch_run_detail(tenant_id, run_id)

        if not row:
            return None

        return RunDetailResult(
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
            estimated_cost_usd=(
                float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None
            ),
            goal=row.get("goal"),
            error_message=row.get("error_message"),
        )

    async def get_run_evidence(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> RunEvidenceResult:
        """
        Get run evidence context (O4).

        Delegates to L4 RunEvidenceCoordinator for cross-domain queries (PIN-519).

        PIN-520: Uses injected coordinator instead of importing from L4 orchestrator.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            run_id: Run ID to fetch

        Returns:
            RunEvidenceResult with cross-domain impact
        """
        # PIN-520: Coordinator must be injected via L4 bridge
        if self._run_evidence_coordinator is None:
            raise RuntimeError(
                "RunEvidenceCoordinator not available - inject via L4 ActivityEngineBridge"
            )

        result = await self._run_evidence_coordinator.get_run_evidence(session, tenant_id, run_id)

        # Convert L4 result to L5 result type (they should be compatible)
        return RunEvidenceResult(
            run_id=result.run_id,
            incidents_caused=[
                {"incident_id": i.incident_id, "severity": i.severity, "title": i.title}
                for i in result.incidents_caused
            ],
            policies_triggered=[
                {"policy_id": p.policy_id, "policy_name": p.policy_name, "outcome": p.outcome}
                for p in result.policies_evaluated
            ],
            decisions_made=[
                {"decision_id": d.decision_id, "decision_type": d.decision_type, "outcome": d.outcome}
                for d in result.decisions_made
            ],
            traces_linked=[
                {"limit_id": lh.limit_id, "limit_name": lh.limit_name}
                for lh in result.limits_hit
            ],
        )

    async def get_run_proof(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
        include_payloads: bool = False,
    ) -> RunProofResult:
        """
        Get run integrity proof (O5).

        Delegates to L4 RunProofCoordinator for trace/proof queries (PIN-519).

        PIN-520: Uses injected coordinator instead of importing from L4 orchestrator.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            run_id: Run ID to fetch
            include_payloads: Include raw payloads

        Returns:
            RunProofResult with integrity proof
        """
        # PIN-520: Coordinator must be injected via L4 bridge
        if self._run_proof_coordinator is None:
            raise RuntimeError(
                "RunProofCoordinator not available - inject via L4 ActivityEngineBridge"
            )

        result = await self._run_proof_coordinator.get_run_proof(
            session, tenant_id, run_id, include_payloads
        )

        # Convert L4 result to L5 result type
        return RunProofResult(
            run_id=result.run_id,
            integrity={
                "model": result.integrity.model,
                "root_hash": result.integrity.root_hash,
                "verification_status": result.integrity.verification_status,
                "chain_length": result.integrity.chain_length,
                "failure_reason": result.integrity.failure_reason,
            },
            aos_traces=[
                {"trace_id": t.trace_id, "status": t.status, "step_count": t.step_count}
                for t in result.aos_traces
            ],
            aos_trace_steps=[
                {"step_index": s.step_index, "skill_name": s.skill_name, "status": s.status}
                for s in result.aos_trace_steps
            ],
            raw_logs=[{"log": log} for log in (result.raw_logs or [])],
        )

    async def get_status_summary(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str | None = None,
        state: str | None = None,
    ) -> StatusSummaryResult:
        """
        Get summary by status (COMP-O3).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter
            state: Optional state filter (LIVE, COMPLETED)

        Returns:
            StatusSummaryResult with counts by status
        """
        where_clauses = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id}

        if project_id:
            where_clauses.append("project_id = :project_id")
            params["project_id"] = project_id

        if state:
            where_clauses.append("state = :state")
            params["state"] = state

        where_sql = " AND ".join(where_clauses)

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        rows = await driver.fetch_status_summary(where_sql, params)

        statuses = [
            StatusCount(status=row["status"], count=row["count"]) for row in rows
        ]
        total = sum(s.count for s in statuses)

        return StatusSummaryResult(statuses=statuses, total=total)

    # =========================================================================
    # V2 Topic-Scoped Operations
    # =========================================================================

    async def get_live_runs(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
        risk_level: list[str] | None = None,
        evidence_health: list[str] | None = None,
        source: list[str] | None = None,
        provider_type: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "started_at",
        sort_order: str = "desc",
    ) -> LiveRunsResult:
        """
        Get live runs with policy context (V2).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter
            risk_level: Filter by risk levels
            evidence_health: Filter by evidence health
            source: Filter by run source
            provider_type: Filter by LLM provider
            limit: Max items to return
            offset: Items to skip
            sort_by: Field to sort by
            sort_order: asc or desc

        Returns:
            LiveRunsResult with items and pagination
        """
        result = await self._get_runs_with_policy_context(
            session=session,
            tenant_id=tenant_id,
            state="LIVE",
            project_id=project_id,
            risk_level=risk_level,
            evidence_health=evidence_health,
            source=source,
            provider_type=provider_type,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return RunsResult(
            state="LIVE",
            items=result["items"],
            total=result["total"],
            has_more=result["has_more"],
        )

    async def get_completed_runs(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
        status: list[str] | None = None,
        risk_level: list[str] | None = None,
        completed_after: datetime | None = None,
        completed_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "started_at",
        sort_order: str = "desc",
    ) -> CompletedRunsResult:
        """
        Get completed runs with policy context (V2).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter
            status: Filter by run statuses
            risk_level: Filter by risk levels
            completed_after: Filter by completion time
            completed_before: Filter by completion time
            limit: Max items to return
            offset: Items to skip
            sort_by: Field to sort by
            sort_order: asc or desc

        Returns:
            CompletedRunsResult with items and pagination
        """
        result = await self._get_runs_with_policy_context(
            session=session,
            tenant_id=tenant_id,
            state="COMPLETED",
            project_id=project_id,
            status=status,
            risk_level=risk_level,
            completed_after=completed_after,
            completed_before=completed_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return RunsResult(
            state="COMPLETED",
            items=result["items"],
            total=result["total"],
            has_more=result["has_more"],
        )

    async def _get_runs_with_policy_context(
        self,
        session: AsyncSession,
        tenant_id: str,
        state: str,
        *,
        project_id: str | None = None,
        status: list[str] | None = None,
        risk_level: list[str] | None = None,
        evidence_health: list[str] | None = None,
        source: list[str] | None = None,
        provider_type: list[str] | None = None,
        completed_after: datetime | None = None,
        completed_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "started_at",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """Internal helper to get runs with policy context."""
        where_clauses = ["tenant_id = :tenant_id", "state = :state"]
        params: dict[str, Any] = {"tenant_id": tenant_id, "state": state}

        if project_id:
            where_clauses.append("project_id = :project_id")
            params["project_id"] = project_id

        if status:
            where_clauses.append("status = ANY(:status)")
            params["status"] = status

        if risk_level:
            where_clauses.append("risk_level = ANY(:risk_level)")
            params["risk_level"] = risk_level

        if evidence_health:
            where_clauses.append("evidence_health = ANY(:evidence_health)")
            params["evidence_health"] = evidence_health

        if source:
            where_clauses.append("source = ANY(:source)")
            params["source"] = source

        if provider_type:
            where_clauses.append("provider_type = ANY(:provider_type)")
            params["provider_type"] = provider_type

        if completed_after:
            where_clauses.append("completed_at >= :completed_after")
            params["completed_after"] = completed_after

        if completed_before:
            where_clauses.append("completed_at <= :completed_before")
            params["completed_before"] = completed_before

        where_sql = " AND ".join(where_clauses)
        sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        total = await driver.count_runs(where_sql, params)
        rows = await driver.fetch_runs_with_policy_context(
            where_sql, params, sort_by, sort_dir, limit, offset
        )

        items = []
        for row in rows:
            policy_context = PolicyContextResult(
                policy_id=row["policy_id"],
                policy_name=row["policy_name"],
                policy_scope=row["policy_scope"],
                limit_type=row.get("limit_type"),
                threshold_value=(
                    float(row["threshold_value"]) if row.get("threshold_value") else None
                ),
                threshold_unit=row.get("threshold_unit"),
                threshold_source=row["threshold_source"],
                evaluation_outcome=row["evaluation_outcome"],
                actual_value=(
                    float(row["actual_value"]) if row.get("actual_value") else None
                ),
                risk_type=row.get("risk_type"),
                proximity_pct=(
                    float(row["proximity_pct"]) if row.get("proximity_pct") else None
                ),
            )

            items.append(
                RunSummaryV2Result(
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
                    estimated_cost_usd=(
                        float(row["estimated_cost_usd"])
                        if row["estimated_cost_usd"]
                        else None
                    ),
                    policy_context=policy_context,
                )
            )

        has_more = offset + len(items) < total

        return {"items": items, "total": total, "has_more": has_more}

    async def get_signals(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
        signal_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SignalsResult:
        """
        Get synthesized attention signals (V2).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter
            signal_type: Filter by signal type (COST_RISK, TIME_RISK, etc.)
            severity: Filter by severity (HIGH, MEDIUM, LOW)
            limit: Max items to return
            offset: Items to skip

        Returns:
            SignalsResult with synthesized signals
        """
        # Build query for at-risk runs to synthesize signals
        where_clauses = [
            "tenant_id = :tenant_id",
            "(risk_level != 'NORMAL' OR incident_count > 0 OR policy_violation = true)",
        ]
        params: dict[str, Any] = {"tenant_id": tenant_id}

        if project_id:
            where_clauses.append("project_id = :project_id")
            params["project_id"] = project_id

        where_sql = " AND ".join(where_clauses)

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        rows = await driver.fetch_at_risk_runs(where_sql, params, limit, offset)

        # Count total
        count_params = {k: v for k, v in params.items()}
        total = await driver.count_runs(where_sql, count_params)

        signals = []
        for row_mapping in rows:
            # Convert RowMapping to dict for type safety
            row = dict(row_mapping)

            # Compute signal type from run data
            computed_signal_type = self._compute_signal_type(row)
            severity_val = self._compute_severity(row)

            # Apply signal_type filter if specified
            if signal_type and computed_signal_type != signal_type:
                continue

            # Apply severity filter if specified
            if severity and severity_val != severity:
                continue

            policy_context = PolicyContextResult(
                policy_id=row["policy_id"],
                policy_name=row["policy_name"],
                policy_scope=row["policy_scope"],
                limit_type=row.get("limit_type"),
                threshold_value=(
                    float(row["threshold_value"]) if row.get("threshold_value") else None
                ),
                threshold_unit=row.get("threshold_unit"),
                threshold_source=row["threshold_source"],
                evaluation_outcome=row["evaluation_outcome"],
                actual_value=(
                    float(row["actual_value"]) if row.get("actual_value") else None
                ),
                risk_type=row.get("risk_type"),
                proximity_pct=(
                    float(row["proximity_pct"]) if row.get("proximity_pct") else None
                ),
            )

            # Compute fingerprint
            fingerprint = compute_signal_fingerprint_from_row(row)

            # Fetch feedback from audit ledger via L4 coordinator (PIN-519)
            feedback = await self._get_signal_feedback(session, tenant_id, fingerprint)

            signals.append(
                SignalProjectionResult(
                    signal_id=f"sig-{row['run_id'][:8]}",
                    signal_fingerprint=fingerprint,
                    run_id=row["run_id"],
                    signal_type=computed_signal_type,
                    severity=severity_val,
                    summary=self._compute_signal_summary(row, computed_signal_type),
                    policy_context=policy_context,
                    created_at=row["started_at"] or datetime.now(timezone.utc),
                    feedback=feedback,
                )
            )

        return SignalsResult(signals=signals, total=total)

    async def _get_signal_feedback(
        self,
        session: AsyncSession,
        tenant_id: str,
        fingerprint: str,
    ) -> SignalFeedbackStatus | None:
        """
        Get signal feedback from audit ledger via L4 coordinator (PIN-519).

        PIN-520: Uses injected coordinator instead of importing from L4 orchestrator.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            fingerprint: Signal fingerprint

        Returns:
            SignalFeedbackStatus if feedback exists, None otherwise
        """
        # PIN-520: Coordinator must be injected via L4 bridge
        if self._signal_feedback_coordinator is None:
            # Graceful degradation - return None if coordinator not available
            logger.debug("SignalFeedbackCoordinator not injected, skipping feedback lookup")
            return None

        try:
            result = await self._signal_feedback_coordinator.get_signal_feedback(
                session, tenant_id, fingerprint
            )

            if result is None:
                return None

            # Convert L4 result to L5 SignalFeedbackStatus
            return SignalFeedbackStatus(
                acknowledged=result.acknowledged,
                acknowledged_by=result.acknowledged_by,
                acknowledged_at=result.acknowledged_at,
                suppressed=result.suppressed,
                suppressed_until=result.suppressed_until,
            )
        except Exception as e:
            logger.warning(f"Failed to fetch signal feedback for {fingerprint}: {e}")
            return None

    def _compute_signal_type(self, row: dict[str, Any]) -> str:
        """
        Compute signal type from run data.

        Uses canonical SignalType enum values (ACT-DUP-006).
        Rule: No free-text categorical fields in Activity.
        """
        risk_type = row.get("risk_type")
        if risk_type:
            # Map risk types to SignalType enum
            type_map = {
                "COST": SignalType.COST_RISK,
                "TIME": SignalType.TIME_RISK,
                "TOKENS": SignalType.TOKEN_RISK,
                "RATE": SignalType.RATE_RISK,
            }
            return type_map.get(risk_type, SignalType.COST_RISK).value

        risk_level = row.get("risk_level", "NORMAL")
        if risk_level == "VIOLATED":
            return SignalType.POLICY_BREACH.value
        if row.get("evidence_health") in ("DEGRADED", "MISSING"):
            return SignalType.EVIDENCE_DEGRADED.value

        return SignalType.COST_RISK.value

    def _compute_severity(self, row: dict[str, Any]) -> str:
        """
        Compute severity level from run data.

        Rule (ACT-DUP-005): Engines speak numbers, facades speak labels.
        Uses SeverityLevel.from_risk_level() for conversion.
        """
        risk_level = row.get("risk_level", "NORMAL")
        return SeverityLevel.from_risk_level(risk_level).value.upper()

    def _compute_signal_summary(self, row: dict[str, Any], signal_type: str) -> str:
        """Compute signal summary from run data."""
        run_id = row.get("run_id", "unknown")[:8]
        risk_level = row.get("risk_level", "NORMAL")
        return f"Run {run_id} has {signal_type} signal ({risk_level})"

    async def get_metrics(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
    ) -> MetricsResult:
        """
        Get activity metrics (V2).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter

        Returns:
            MetricsResult with aggregated metrics
        """
        where_clauses = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id}

        if project_id:
            where_clauses.append("project_id = :project_id")
            params["project_id"] = project_id

        where_sql = " AND ".join(where_clauses)

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        row = await driver.fetch_metrics(where_sql, params)

        if not row:
            return MetricsResult(
                at_risk_count=0,
                violated_count=0,
                near_threshold_count=0,
                total_at_risk=0,
                live_count=0,
                completed_count=0,
                evidence_flowing_count=0,
                evidence_degraded_count=0,
                evidence_missing_count=0,
                cost_risk_count=0,
                time_risk_count=0,
                token_risk_count=0,
                rate_risk_count=0,
            )

        return MetricsResult(
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
        )

    async def get_threshold_signals(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
        risk_type: str | None = None,
        evaluation_outcome: str | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ThresholdSignalsResult:
        """
        Get threshold proximity signals (V2).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter
            risk_type: Filter by risk type (COST, TIME, TOKENS, RATE)
            evaluation_outcome: Filter by evaluation outcome
            state: Filter by run state (LIVE, COMPLETED)
            limit: Max items to return
            offset: Items to skip

        Returns:
            ThresholdSignalsResult with threshold signals
        """
        where_clauses = [
            "tenant_id = :tenant_id",
            "threshold_value IS NOT NULL",
            "evaluation_outcome IS NOT NULL",
            "evaluation_outcome != 'ADVISORY'",
        ]
        params: dict[str, Any] = {"tenant_id": tenant_id}

        if project_id:
            where_clauses.append("project_id = :project_id")
            params["project_id"] = project_id

        if risk_type:
            where_clauses.append("risk_type = :risk_type")
            params["risk_type"] = risk_type

        if evaluation_outcome:
            where_clauses.append("evaluation_outcome = :evaluation_outcome")
            params["evaluation_outcome"] = evaluation_outcome

        if state:
            where_clauses.append("state = :state")
            params["state"] = state

        where_sql = " AND ".join(where_clauses)

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        rows = await driver.fetch_threshold_signals(where_sql, params, limit, offset)

        # Count total
        count_params = {k: v for k, v in params.items()}
        total = await driver.count_runs(where_sql, count_params)

        signals = []
        for row in rows:
            policy_context = PolicyContextResult(
                policy_id=row["policy_id"],
                policy_name=row["policy_name"],
                policy_scope=row["policy_scope"],
                limit_type=row.get("limit_type"),
                threshold_value=(
                    float(row["threshold_value"]) if row.get("threshold_value") else None
                ),
                threshold_unit=row.get("threshold_unit"),
                threshold_source=row["threshold_source"],
                evaluation_outcome=row["evaluation_outcome"],
                actual_value=(
                    float(row["actual_value"]) if row.get("actual_value") else None
                ),
                risk_type=row.get("risk_type"),
                proximity_pct=float(row["proximity_pct"]),
            )

            signals.append(
                ThresholdSignalResult(
                    run_id=row["run_id"],
                    limit_type=row["limit_type"],
                    proximity_pct=float(row["proximity_pct"]),
                    evaluation_outcome=row["evaluation_outcome"],
                    policy_context=policy_context,
                )
            )

        return ThresholdSignalsResult(
            signals=signals,
            total=total,
            risk_type_filter=risk_type,
        )

    async def get_risk_signals(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        project_id: str | None = None,
    ) -> RiskSignalsResult:
        """
        Get risk signal aggregates.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            project_id: Optional project filter

        Returns:
            RiskSignalsResult with aggregated risk counts
        """
        metrics = await self.get_metrics(session, tenant_id, project_id=project_id)

        return RiskSignalsResult(
            at_risk_count=metrics.at_risk_count,
            violated_count=metrics.violated_count,
            near_threshold_count=metrics.near_threshold_count,
            total_at_risk=metrics.total_at_risk,
            by_risk_type={
                "COST": metrics.cost_risk_count,
                "TIME": metrics.time_risk_count,
                "TOKENS": metrics.token_risk_count,
                "RATE": metrics.rate_risk_count,
            },
        )

    async def get_dimension_breakdown(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        dimension: str,
        state: str | None = None,
        limit: int = 20,
    ) -> DimensionBreakdownResult:
        """
        Get runs grouped by dimension.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            dimension: Column to group by
            state: Optional state filter (LIVE, COMPLETED)
            limit: Max groups to return

        Returns:
            DimensionBreakdownResult with groups
        """
        where_clauses = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

        if state:
            where_clauses.append("state = :state")
            params["state"] = state

        where_sql = " AND ".join(where_clauses)

        # L6: Delegate data access to driver
        driver = self._get_driver(session)
        rows = await driver.fetch_dimension_breakdown(
            dimension, where_sql, params, limit
        )

        total = sum(row["count"] for row in rows)
        groups = [
            DimensionGroupResult(
                value=row["value"],
                count=row["count"],
                percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
            )
            for row in rows
        ]

        return DimensionBreakdownResult(
            dimension=dimension,
            groups=groups,
            total_runs=total,
            state_filter=state,
        )

    # =========================================================================
    # Signal Analysis Operations (Delegate to Existing Services)
    # =========================================================================

    async def get_patterns(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        window_hours: int = 24,
        limit: int = 20,
        project_id: str | None = None,
    ) -> PatternDetectionResult:
        """
        Detect instability patterns (SIG-O3).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            window_hours: Analysis window in hours
            limit: Maximum patterns per type
            project_id: Optional project filter

        Returns:
            PatternDetectionResult with detected patterns
        """
        service = self._get_pattern_service(session)
        result = await service.detect_patterns(
            tenant_id=tenant_id,
            window_hours=window_hours,
            limit=limit,
        )
        # project_id filtering not supported by service yet
        _ = project_id
        return result

    async def get_cost_analysis(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        baseline_days: int = 7,
        threshold_pct: float = 50.0,
        project_id: str | None = None,
    ) -> CostAnalysisResult:
        """
        Analyze cost anomalies (SIG-O4).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            baseline_days: Days for baseline calculation
            threshold_pct: Percentage threshold for anomaly detection
            project_id: Optional project filter

        Returns:
            CostAnalysisResult with detected anomalies
        """
        service = self._get_cost_service(session)
        result = await service.analyze_costs(
            tenant_id=tenant_id,
            baseline_days=baseline_days,
            threshold_pct=threshold_pct,
        )
        # project_id filtering not supported by service yet
        _ = project_id
        return result

    async def get_attention_queue(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 20,
        project_id: str | None = None,
    ) -> AttentionQueueResult:
        """
        Get attention ranking (SIG-O5).

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            limit: Max items to return
            project_id: Optional project filter

        Returns:
            AttentionQueueResult with ranked items
        """
        service = self._get_attention_service(session)
        result = await service.get_attention_queue(
            tenant_id=tenant_id,
            limit=limit,
        )
        # project_id filtering not supported by service yet
        _ = project_id
        return result

    # =========================================================================
    # Signal Feedback Operations
    # =========================================================================

    async def acknowledge_signal(
        self,
        session: AsyncSession,
        tenant_id: str,
        signal_id: str,
        acknowledged_by: str | None = None,
    ) -> AcknowledgeResult:
        """
        Acknowledge a signal.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            signal_id: Signal ID (fingerprint)
            acknowledged_by: User ID

        Returns:
            AcknowledgeResult from feedback service
        """
        service = self._get_feedback_service(session)
        return await service.acknowledge_signal(
            tenant_id=tenant_id,
            signal_id=signal_id,
            acknowledged_by=acknowledged_by,
        )

    async def suppress_signal(
        self,
        session: AsyncSession,
        tenant_id: str,
        signal_id: str,
        suppressed_by: str | None = None,
        duration_hours: int = 24,
        reason: str | None = None,
    ) -> SuppressResult:
        """
        Suppress a signal.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            signal_id: Signal ID (fingerprint)
            suppressed_by: User ID
            duration_hours: Suppression duration in hours
            reason: Optional reason

        Returns:
            SuppressResult from feedback service
        """
        service = self._get_feedback_service(session)
        return await service.suppress_signal(
            tenant_id=tenant_id,
            signal_id=signal_id,
            suppressed_by=suppressed_by,
            duration_hours=duration_hours,
            reason=reason,
        )


# =============================================================================
# Singleton Instance
# =============================================================================

_facade_instance: ActivityFacade | None = None


def get_activity_facade(
    run_evidence_coordinator: RunEvidenceCoordinatorPort | None = None,
    run_proof_coordinator: RunProofCoordinatorPort | None = None,
    signal_feedback_coordinator: SignalFeedbackCoordinatorPort | None = None,
) -> ActivityFacade:
    """Get the singleton ActivityFacade instance.

    PIN-520: L4 callers must inject coordinators. L5 must not import from hoc_spine.

    Args:
        run_evidence_coordinator: Coordinator for cross-domain evidence queries (injected by L4 caller).
        run_proof_coordinator: Coordinator for integrity proof queries (injected by L4 caller).
        signal_feedback_coordinator: Coordinator for signal feedback queries (injected by L4 caller).

    Returns:
        ActivityFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = ActivityFacade(
            run_evidence_coordinator=run_evidence_coordinator,
            run_proof_coordinator=run_proof_coordinator,
            signal_feedback_coordinator=signal_feedback_coordinator,
        )
    else:
        # Allow late injection if coordinators weren't provided initially
        if run_evidence_coordinator and _facade_instance._run_evidence_coordinator is None:
            _facade_instance._run_evidence_coordinator = run_evidence_coordinator
        if run_proof_coordinator and _facade_instance._run_proof_coordinator is None:
            _facade_instance._run_proof_coordinator = run_proof_coordinator
        if signal_feedback_coordinator and _facade_instance._signal_feedback_coordinator is None:
            _facade_instance._signal_feedback_coordinator = signal_feedback_coordinator
    return _facade_instance
