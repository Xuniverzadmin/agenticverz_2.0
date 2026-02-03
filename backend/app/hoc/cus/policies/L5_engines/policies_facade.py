# Layer: L5 — Domain Engine (Facade)
# AUDIENCE: CUSTOMER
# Role: Policies facade - unified entry point for policy management
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: policies.py (L2 API)
# Allowed Imports: L5 (same domain), L6 (drivers)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: PIN-512 Category B — rewired from legacy app.services.policies_facade

"""
PoliciesFacade (L5)

Unified facade for policy management operations.

Provides:
- Policy Rules: list, get detail (via L6 driver)
- Limits: list, get detail (via L6 driver)
- Lessons: list, get detail, stats (delegates to LessonsLearnedEngine)
- Policy State: synthesized snapshot (mixed: driver + engine delegation)
- Policy Metrics: enforcement effectiveness (delegates to PolicyEngine)
- Policy Conflicts: detect contradictions (delegates to PolicyConflictEngine)
- Policy Dependencies: structural relationships (delegates to PolicyDependencyEngine)
- Policy Violations: unified violation view (delegates to PolicyEngine)
- Budget Definitions: enforcement limits (via L6 driver)
- Policy Requests: pending approvals (via L6 driver)

All operations are tenant-scoped for isolation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app.hoc.cus.policies.L6_drivers.policies_facade_driver import PoliciesFacadeDriver


# =============================================================================
# Result Types - Policy Rules
# =============================================================================


@dataclass
class PolicyRuleSummaryResult:
    """Policy rule summary for list view (O2)."""

    rule_id: str
    name: str
    enforcement_mode: str
    scope: str
    source: str
    status: str
    created_at: datetime
    created_by: Optional[str]
    integrity_status: str
    integrity_score: Decimal
    trigger_count_30d: int
    last_triggered_at: Optional[datetime]


@dataclass
class PolicyRulesListResult:
    """Policy rules list response."""

    items: list[PolicyRuleSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class PolicyRuleDetailResult:
    """Policy rule detail response (O3)."""

    rule_id: str
    name: str
    description: Optional[str]
    enforcement_mode: str
    scope: str
    source: str
    status: str
    created_at: datetime
    created_by: Optional[str]
    updated_at: Optional[datetime]
    integrity_status: str
    integrity_score: Decimal
    trigger_count_30d: int
    last_triggered_at: Optional[datetime]
    rule_definition: Optional[dict] = None
    violation_count_total: int = 0


# =============================================================================
# Result Types - Limits
# =============================================================================


@dataclass
class LimitSummaryResult:
    """Limit summary for list view (O2)."""

    limit_id: str
    name: str
    limit_category: str
    limit_type: str
    scope: str
    enforcement: str
    status: str
    max_value: Decimal
    window_seconds: Optional[int]
    reset_period: Optional[str]
    integrity_status: str
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime


@dataclass
class LimitsListResult:
    """Limits list response."""

    items: list[LimitSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class LimitDetailResult:
    """Limit detail response (O3)."""

    limit_id: str
    name: str
    description: Optional[str]
    limit_category: str
    limit_type: str
    scope: str
    enforcement: str
    status: str
    max_value: Decimal
    window_seconds: Optional[int]
    reset_period: Optional[str]
    integrity_status: str
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    current_value: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


# =============================================================================
# Result Types - Policy State & Metrics
# =============================================================================


@dataclass
class PolicyStateResult:
    """Policy layer state summary (ACT-O4)."""

    total_policies: int
    active_policies: int
    drafts_pending_review: int
    conflicts_detected: int
    violations_24h: int
    lessons_pending_action: int
    last_updated: datetime


@dataclass
class PolicyMetricsResult:
    """Policy enforcement metrics (ACT-O5)."""

    total_evaluations: int
    total_blocks: int
    total_allows: int
    block_rate: float
    avg_evaluation_ms: float
    violations_by_type: dict[str, int]
    evaluations_by_action: dict[str, int]
    window_hours: int


# =============================================================================
# Result Types - Conflicts & Dependencies
# =============================================================================


@dataclass
class PolicyConflictResult:
    """Policy conflict summary (DFT-O4)."""

    policy_a_id: str
    policy_b_id: str
    policy_a_name: str
    policy_b_name: str
    conflict_type: str
    severity: str
    explanation: str
    recommended_action: str
    detected_at: datetime


@dataclass
class ConflictsListResult:
    """Policy conflicts list response."""

    items: list[PolicyConflictResult]
    total: int
    unresolved_count: int
    computed_at: datetime


@dataclass
class PolicyDependencyRelation:
    """A dependency relationship."""

    policy_id: str
    policy_name: str
    dependency_type: str
    reason: str


@dataclass
class PolicyNodeResult:
    """A node in the dependency graph (DFT-O5)."""

    id: str
    name: str
    rule_type: str
    scope: str
    status: str
    enforcement_mode: str
    depends_on: list[PolicyDependencyRelation]
    required_by: list[PolicyDependencyRelation]


@dataclass
class PolicyDependencyEdge:
    """A dependency edge in the graph."""

    policy_id: str
    depends_on_id: str
    policy_name: str
    depends_on_name: str
    dependency_type: str
    reason: str


@dataclass
class DependencyGraphResult:
    """Policy dependency graph response."""

    nodes: list[PolicyNodeResult]
    edges: list[PolicyDependencyEdge]
    nodes_count: int
    edges_count: int
    computed_at: datetime


# =============================================================================
# Result Types - Violations
# =============================================================================


@dataclass
class PolicyViolationResult:
    """Policy violation summary (VIO-O1)."""

    id: str
    policy_id: Optional[str]
    policy_name: Optional[str]
    violation_type: str
    severity: float
    source: str
    agent_id: Optional[str]
    description: Optional[str]
    occurred_at: datetime
    is_synthetic: bool = False


@dataclass
class ViolationsListResult:
    """Policy violations list response."""

    items: list[PolicyViolationResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


# =============================================================================
# Result Types - Budgets
# =============================================================================


@dataclass
class BudgetDefinitionResult:
    """Budget definition summary (THR-O2)."""

    id: str
    name: str
    scope: str
    max_value: Decimal
    reset_period: Optional[str]
    enforcement: str
    status: str
    current_usage: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


@dataclass
class BudgetsListResult:
    """Budget definitions list response."""

    items: list[BudgetDefinitionResult]
    total: int
    filters_applied: dict[str, Any]


# =============================================================================
# Result Types - Policy Requests
# =============================================================================


@dataclass
class PolicyRequestResult:
    """Pending policy request summary (ACT-O3)."""

    id: str
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict[str, Any]
    status: str
    created_at: datetime
    triggering_feedback_count: int
    days_pending: int


@dataclass
class PolicyRequestsListResult:
    """Policy requests list response."""

    items: list[PolicyRequestResult]
    total: int
    pending_count: int
    filters_applied: dict[str, Any]


# =============================================================================
# Result Types - Lessons
# =============================================================================


@dataclass
class LessonSummaryResult:
    """Lesson summary for list view (O2)."""

    id: str
    lesson_type: str
    severity: Optional[str]
    title: str
    status: str
    source_event_type: str
    created_at: datetime
    has_proposed_action: bool


@dataclass
class LessonsListResult:
    """Lessons list response."""

    items: list[LessonSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class LessonDetailResult:
    """Lesson detail response (O3)."""

    id: str
    lesson_type: str
    severity: Optional[str]
    source_event_id: Optional[str]
    source_event_type: str
    source_run_id: Optional[str]
    title: str
    description: str
    proposed_action: Optional[str]
    detected_pattern: Optional[dict[str, Any]]
    status: str
    draft_proposal_id: Optional[str]
    created_at: str
    converted_at: Optional[str]
    deferred_until: Optional[str]


@dataclass
class LessonStatsResult:
    """Lesson statistics response."""

    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]


# =============================================================================
# Policies Facade (L5)
# =============================================================================


class PoliciesFacade:
    """
    Unified facade for policy management.

    SQL operations delegate to PoliciesFacadeDriver (L6).
    Domain operations delegate to same-domain L5 engines.
    """

    def __init__(self, driver: Optional[PoliciesFacadeDriver] = None) -> None:
        self._driver = driver or PoliciesFacadeDriver()

    # -------------------------------------------------------------------------
    # Policy Rules Operations (L6 driver)
    # -------------------------------------------------------------------------

    async def list_policy_rules(
        self,
        session: Any,
        tenant_id: str,
        *,
        status: str = "ACTIVE",
        enforcement_mode: Optional[str] = None,
        scope: Optional[str] = None,
        source: Optional[str] = None,
        rule_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PolicyRulesListResult:
        """List policy rules for the tenant."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}
        if enforcement_mode:
            filters_applied["enforcement_mode"] = enforcement_mode
        if scope:
            filters_applied["scope"] = scope
        if source:
            filters_applied["source"] = source
        if rule_type:
            filters_applied["rule_type"] = rule_type
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        data = await self._driver.fetch_policy_rules(
            session, tenant_id,
            status=status,
            enforcement_mode=enforcement_mode,
            scope=scope,
            source=source,
            rule_type=rule_type,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        items = [
            PolicyRuleSummaryResult(
                rule_id=row["rule_id"],
                name=row["name"],
                enforcement_mode=row["enforcement_mode"],
                scope=row["scope"],
                source=row["source"],
                status=row["status"],
                created_at=row["created_at"],
                created_by=row["created_by"],
                integrity_status=row["integrity_status"],
                integrity_score=row["integrity_score"],
                trigger_count_30d=row["trigger_count_30d"],
                last_triggered_at=row["last_triggered_at"],
            )
            for row in data["items"]
        ]

        return PolicyRulesListResult(
            items=items,
            total=data["total"],
            has_more=(offset + len(items)) < data["total"],
            filters_applied=filters_applied,
        )

    async def get_policy_rule_detail(
        self,
        session: Any,
        tenant_id: str,
        rule_id: str,
    ) -> Optional[PolicyRuleDetailResult]:
        """Get policy rule detail."""
        data = await self._driver.fetch_policy_rule_detail(session, tenant_id, rule_id)
        if not data:
            return None

        rule = data["rule"]
        return PolicyRuleDetailResult(
            rule_id=rule.id,
            name=rule.name,
            description=getattr(rule, "description", None),
            enforcement_mode=rule.enforcement_mode,
            scope=rule.scope,
            source=rule.source,
            status=rule.status,
            created_at=rule.created_at,
            created_by=rule.created_by,
            updated_at=getattr(rule, "updated_at", None),
            integrity_status=data["integrity_status"],
            integrity_score=data["integrity_score"],
            trigger_count_30d=data["trigger_count_30d"],
            last_triggered_at=data["last_triggered_at"],
            rule_definition=getattr(rule, "rule_definition", None),
            violation_count_total=0,
        )

    # -------------------------------------------------------------------------
    # Limits Operations (L6 driver)
    # -------------------------------------------------------------------------

    async def list_limits(
        self,
        session: Any,
        tenant_id: str,
        *,
        category: str = "BUDGET",
        status: str = "ACTIVE",
        scope: Optional[str] = None,
        enforcement: Optional[str] = None,
        limit_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> LimitsListResult:
        """List limits for the tenant."""
        filters_applied: dict[str, Any] = {
            "tenant_id": tenant_id, "category": category, "status": status,
        }
        if scope:
            filters_applied["scope"] = scope
        if enforcement:
            filters_applied["enforcement"] = enforcement
        if limit_type:
            filters_applied["limit_type"] = limit_type
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        data = await self._driver.fetch_limits(
            session, tenant_id,
            category=category,
            status=status,
            scope=scope,
            enforcement=enforcement,
            limit_type=limit_type,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        items = [
            LimitSummaryResult(
                limit_id=row["limit_id"],
                name=row["name"],
                limit_category=row["limit_category"],
                limit_type=row["limit_type"],
                scope=row["scope"],
                enforcement=row["enforcement"],
                status=row["status"],
                max_value=row["max_value"],
                window_seconds=row["window_seconds"],
                reset_period=row["reset_period"],
                integrity_status=row["integrity_status"],
                integrity_score=row["integrity_score"],
                breach_count_30d=row["breach_count_30d"],
                last_breached_at=row["last_breached_at"],
                created_at=row["created_at"],
            )
            for row in data["items"]
        ]

        return LimitsListResult(
            items=items,
            total=data["total"],
            has_more=(offset + len(items)) < data["total"],
            filters_applied=filters_applied,
        )

    async def get_limit_detail(
        self,
        session: Any,
        tenant_id: str,
        limit_id: str,
    ) -> Optional[LimitDetailResult]:
        """Get limit detail."""
        data = await self._driver.fetch_limit_detail(session, tenant_id, limit_id)
        if not data:
            return None

        lim = data["limit"]
        return LimitDetailResult(
            limit_id=lim.id,
            name=lim.name,
            description=getattr(lim, "description", None),
            limit_category=lim.limit_category,
            limit_type=lim.limit_type,
            scope=lim.scope,
            enforcement=lim.enforcement,
            status=lim.status,
            max_value=lim.max_value,
            window_seconds=lim.window_seconds,
            reset_period=lim.reset_period,
            integrity_status=data["integrity_status"],
            integrity_score=data["integrity_score"],
            breach_count_30d=data["breach_count_30d"],
            last_breached_at=data["last_breached_at"],
            created_at=lim.created_at,
            updated_at=getattr(lim, "updated_at", None),
        )

    # -------------------------------------------------------------------------
    # Lessons Operations (delegates to LessonsLearnedEngine — same domain L5)
    # -------------------------------------------------------------------------

    async def list_lessons(
        self,
        session: Any,
        tenant_id: str,
        *,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> LessonsListResult:
        """List lessons learned for the tenant."""
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine

        engine = get_lessons_learned_engine()
        lessons = engine.list_lessons(
            tenant_id=tenant_id,
            lesson_type=lesson_type,
            status=status,
            severity=severity,
            limit=limit,
            offset=offset,
        )

        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}
        if lesson_type:
            filters_applied["lesson_type"] = lesson_type
        if status:
            filters_applied["status"] = status
        if severity:
            filters_applied["severity"] = severity

        items = [
            LessonSummaryResult(
                id=lesson["id"],
                lesson_type=lesson["lesson_type"],
                severity=lesson["severity"],
                title=lesson["title"],
                status=lesson["status"],
                source_event_type=lesson["source_event_type"],
                created_at=datetime.fromisoformat(lesson["created_at"]) if lesson["created_at"] else datetime.utcnow(),
                has_proposed_action=lesson["has_proposed_action"],
            )
            for lesson in lessons
        ]

        return LessonsListResult(
            items=items,
            total=len(items),
            has_more=len(items) == limit,
            filters_applied=filters_applied,
        )

    async def get_lesson_detail(
        self,
        session: Any,
        tenant_id: str,
        lesson_id: str,
    ) -> Optional[LessonDetailResult]:
        """Get lesson detail."""
        from uuid import UUID
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine

        engine = get_lessons_learned_engine()
        lesson = engine.get_lesson(lesson_id=UUID(lesson_id), tenant_id=tenant_id)

        if not lesson:
            return None

        return LessonDetailResult(
            id=lesson["id"],
            lesson_type=lesson["lesson_type"],
            severity=lesson["severity"],
            source_event_id=lesson["source_event_id"],
            source_event_type=lesson["source_event_type"],
            source_run_id=lesson["source_run_id"],
            title=lesson["title"],
            description=lesson["description"],
            proposed_action=lesson["proposed_action"],
            detected_pattern=lesson["detected_pattern"],
            status=lesson["status"],
            draft_proposal_id=lesson["draft_proposal_id"],
            created_at=lesson["created_at"],
            converted_at=lesson["converted_at"],
            deferred_until=lesson["deferred_until"],
        )

    async def get_lesson_stats(
        self,
        session: Any,
        tenant_id: str,
    ) -> LessonStatsResult:
        """Get lesson statistics."""
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine

        engine = get_lessons_learned_engine()
        stats = engine.get_lesson_stats(tenant_id=tenant_id)

        return LessonStatsResult(
            total=stats.get("total", 0),
            by_type=stats.get("by_type", {}),
            by_status=stats.get("by_status", {}),
        )

    # -------------------------------------------------------------------------
    # Policy State & Metrics (mixed: driver + engine delegation)
    # -------------------------------------------------------------------------

    async def get_policy_state(
        self,
        session: Any,
        tenant_id: str,
    ) -> PolicyStateResult:
        """Get policy layer state summary."""
        from app.hoc.cus.policies.L5_engines.engine import get_policy_engine
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine

        engine = get_policy_engine()
        state = await engine.get_state(session)

        lessons_engine = get_lessons_learned_engine()
        lessons_stats = lessons_engine.get_lesson_stats(tenant_id=tenant_id)
        pending_lessons = lessons_stats.get("by_status", {}).get("pending", 0)

        drafts_count = await self._driver.count_pending_drafts(session, tenant_id)

        conflicts_count = 0
        try:
            conflicts = await engine.get_policy_conflicts(session, include_resolved=False)
            conflicts_count = len(conflicts)
        except Exception:
            pass

        return PolicyStateResult(
            total_policies=state.total_policies,
            active_policies=state.active_policies,
            drafts_pending_review=drafts_count,
            conflicts_detected=conflicts_count,
            violations_24h=state.total_violations_today,
            lessons_pending_action=pending_lessons,
            last_updated=datetime.utcnow(),
        )

    async def get_policy_metrics(
        self,
        session: Any,
        tenant_id: str,
        *,
        hours: int = 24,
    ) -> PolicyMetricsResult:
        """Get policy enforcement metrics."""
        from app.hoc.cus.policies.L5_engines.engine import get_policy_engine

        engine = get_policy_engine()
        metrics = await engine.get_metrics(session, hours=hours)

        return PolicyMetricsResult(
            total_evaluations=metrics.get("total_evaluations", 0),
            total_blocks=metrics.get("total_blocks", 0),
            total_allows=metrics.get("total_allows", 0),
            block_rate=metrics.get("block_rate", 0.0),
            avg_evaluation_ms=metrics.get("avg_evaluation_ms", 0.0),
            violations_by_type=metrics.get("violations_by_type", {}),
            evaluations_by_action=metrics.get("evaluations_by_action", {}),
            window_hours=hours,
        )

    # -------------------------------------------------------------------------
    # Policy Violations (delegates to PolicyEngine)
    # -------------------------------------------------------------------------

    async def list_policy_violations(
        self,
        session: Any,
        tenant_id: str,
        *,
        violation_type: Optional[str] = None,
        source: Optional[str] = None,
        severity_min: Optional[float] = None,
        violation_kind: Optional[str] = None,
        hours: int = 24,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> ViolationsListResult:
        """List policy violations."""
        from app.hoc.cus.policies.L5_engines.engine import get_policy_engine
        from app.policy.models import ViolationType as ViolationTypeEnum

        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "hours": hours}
        if violation_type:
            filters_applied["violation_type"] = violation_type
        if source:
            filters_applied["source"] = source
        if severity_min:
            filters_applied["severity_min"] = severity_min
        if violation_kind:
            filters_applied["violation_kind"] = violation_kind

        engine = get_policy_engine()

        violation_type_enum = None
        if violation_type:
            type_mapping = {
                "cost": ViolationTypeEnum.RISK_CEILING_BREACH,
                "quota": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "rate": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "temporal": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "safety": ViolationTypeEnum.SAFETY_RULE_TRIGGERED,
                "ethical": ViolationTypeEnum.ETHICAL_VIOLATION,
            }
            violation_type_enum = type_mapping.get(violation_type)

        violations = await engine.get_violations(
            session,
            tenant_id=tenant_id,
            violation_type=violation_type_enum,
            severity_min=severity_min,
            since=datetime.utcnow() - timedelta(hours=hours),
            limit=limit + 1,
        )

        if source:
            violations = [v for v in violations if getattr(v, "source", "runtime") == source]
        if violation_kind:
            violations = [v for v in violations if getattr(v, "violation_kind", "STANDARD") == violation_kind]
        if not include_synthetic:
            violations = [v for v in violations if not getattr(v, "is_synthetic", False)]

        has_more = len(violations) > limit
        violations = violations[:limit]

        items = [
            PolicyViolationResult(
                id=str(v.id),
                policy_id=getattr(v, "policy_id", None),
                policy_name=getattr(v, "policy_name", None),
                violation_type=str(v.violation_type.value) if hasattr(v.violation_type, "value") else str(v.violation_type),
                severity=v.severity,
                source=getattr(v, "source", "runtime"),
                agent_id=v.agent_id,
                description=getattr(v, "description", None),
                occurred_at=v.detected_at,
                is_synthetic=getattr(v, "is_synthetic", False),
            )
            for v in violations
        ]

        return ViolationsListResult(
            items=items,
            total=len(items),
            has_more=has_more,
            filters_applied=filters_applied,
        )

    # -------------------------------------------------------------------------
    # Policy Conflicts (delegates to PolicyConflictEngine — same domain L5)
    # -------------------------------------------------------------------------

    async def list_policy_conflicts(
        self,
        session: Any,
        tenant_id: str,
        *,
        policy_id: Optional[str] = None,
        severity: Optional[str] = None,
        include_resolved: bool = False,
    ) -> ConflictsListResult:
        """Detect policy conflicts."""
        from app.hoc.cus.policies.L5_engines.policy_graph_engine import (
            ConflictSeverity,
            get_conflict_engine,
        )
        from app.hoc.cus.policies.L6_drivers.policy_graph_driver import (
            get_policy_graph_driver,
        )

        engine = get_conflict_engine(tenant_id)
        driver = get_policy_graph_driver(session)

        severity_filter = None
        if severity:
            try:
                severity_filter = ConflictSeverity(severity.upper())
            except ValueError:
                pass

        result = await engine.detect_conflicts(
            driver=driver,
            policy_id=policy_id,
            severity_filter=severity_filter,
            include_resolved=include_resolved,
        )

        items = [
            PolicyConflictResult(
                policy_a_id=c.policy_a_id,
                policy_b_id=c.policy_b_id,
                policy_a_name=c.policy_a_name,
                policy_b_name=c.policy_b_name,
                conflict_type=c.conflict_type.value,
                severity=c.severity.value,
                explanation=c.explanation,
                recommended_action=c.recommended_action,
                detected_at=c.detected_at,
            )
            for c in result.conflicts
        ]

        return ConflictsListResult(
            items=items,
            total=len(items),
            unresolved_count=result.unresolved_count,
            computed_at=result.computed_at,
        )

    # -------------------------------------------------------------------------
    # Policy Dependencies (delegates to PolicyDependencyEngine — same domain L5)
    # -------------------------------------------------------------------------

    async def get_policy_dependencies(
        self,
        session: Any,
        tenant_id: str,
        *,
        policy_id: Optional[str] = None,
    ) -> DependencyGraphResult:
        """Get policy dependency graph."""
        from app.hoc.cus.policies.L5_engines.policy_graph_engine import get_dependency_engine
        from app.hoc.cus.policies.L6_drivers.policy_graph_driver import (
            get_policy_graph_driver,
        )

        engine = get_dependency_engine(tenant_id)
        driver = get_policy_graph_driver(session)
        result = await engine.compute_dependency_graph(driver, policy_id=policy_id)

        nodes = [
            PolicyNodeResult(
                id=n.id,
                name=n.name,
                rule_type=n.rule_type,
                scope=n.scope,
                status=n.status,
                enforcement_mode=n.enforcement_mode,
                depends_on=[
                    PolicyDependencyRelation(
                        policy_id=d["policy_id"],
                        policy_name=d["policy_name"],
                        dependency_type=d["type"],
                        reason=d["reason"],
                    )
                    for d in n.depends_on
                ],
                required_by=[
                    PolicyDependencyRelation(
                        policy_id=d["policy_id"],
                        policy_name=d["policy_name"],
                        dependency_type=d["type"],
                        reason=d["reason"],
                    )
                    for d in n.required_by
                ],
            )
            for n in result.nodes
        ]

        edges = [
            PolicyDependencyEdge(
                policy_id=e.policy_id,
                depends_on_id=e.depends_on_id,
                policy_name=e.policy_name,
                depends_on_name=e.depends_on_name,
                dependency_type=e.dependency_type.value,
                reason=e.reason,
            )
            for e in result.edges
        ]

        return DependencyGraphResult(
            nodes=nodes,
            edges=edges,
            nodes_count=len(nodes),
            edges_count=len(edges),
            computed_at=result.computed_at,
        )

    # -------------------------------------------------------------------------
    # Policy Requests (L6 driver)
    # -------------------------------------------------------------------------

    async def list_policy_requests(
        self,
        session: Any,
        tenant_id: str,
        *,
        status: str = "draft",
        proposal_type: Optional[str] = None,
        days_old: Optional[int] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> PolicyRequestsListResult:
        """List pending policy requests."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}
        if proposal_type:
            filters_applied["proposal_type"] = proposal_type
        if days_old:
            filters_applied["days_old"] = days_old
        if include_synthetic:
            filters_applied["include_synthetic"] = True

        now = datetime.now(timezone.utc)

        data = await self._driver.fetch_policy_requests(
            session, tenant_id,
            status=status,
            proposal_type=proposal_type,
            days_old=days_old,
            include_synthetic=include_synthetic,
            limit=limit,
            offset=offset,
        )

        items = []
        for prop in data["items"]:
            created = prop.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            days_pending = (now - created).days

            feedback_ids = prop.triggering_feedback_ids or []
            feedback_count = len(feedback_ids) if isinstance(feedback_ids, list) else 0

            items.append(
                PolicyRequestResult(
                    id=str(prop.id),
                    proposal_name=prop.proposal_name,
                    proposal_type=prop.proposal_type,
                    rationale=prop.rationale,
                    proposed_rule=prop.proposed_rule or {},
                    status=prop.status,
                    created_at=prop.created_at,
                    triggering_feedback_count=feedback_count,
                    days_pending=days_pending,
                )
            )

        return PolicyRequestsListResult(
            items=items,
            total=len(items),
            pending_count=data["pending_count"],
            filters_applied=filters_applied,
        )

    # -------------------------------------------------------------------------
    # Budget Definitions (L6 driver)
    # -------------------------------------------------------------------------

    async def list_budgets(
        self,
        session: Any,
        tenant_id: str,
        *,
        scope: Optional[str] = None,
        status: str = "ACTIVE",
        limit: int = 20,
        offset: int = 0,
    ) -> BudgetsListResult:
        """List budget definitions for the tenant."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}
        if scope:
            filters_applied["scope"] = scope

        limits = await self._driver.fetch_budgets(
            session, tenant_id, scope=scope, status=status, limit=limit, offset=offset,
        )

        items = [
            BudgetDefinitionResult(
                id=str(lim.id),
                name=lim.name,
                scope=lim.scope,
                max_value=lim.max_value,
                reset_period=lim.reset_period,
                enforcement=lim.enforcement,
                status=lim.status,
            )
            for lim in limits
        ]

        return BudgetsListResult(
            items=items,
            total=len(items),
            filters_applied=filters_applied,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_facade_instance: Optional[PoliciesFacade] = None


def get_policies_facade(driver: Optional[PoliciesFacadeDriver] = None) -> PoliciesFacade:
    """Get the singleton PoliciesFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = PoliciesFacade(driver=driver)
    return _facade_instance


__all__ = [
    # Facade
    "PoliciesFacade",
    "get_policies_facade",
    # Result types - Policy Rules
    "PolicyRuleSummaryResult",
    "PolicyRulesListResult",
    "PolicyRuleDetailResult",
    # Result types - Limits
    "LimitSummaryResult",
    "LimitsListResult",
    "LimitDetailResult",
    # Result types - State & Metrics
    "PolicyStateResult",
    "PolicyMetricsResult",
    # Result types - Conflicts & Dependencies
    "PolicyConflictResult",
    "ConflictsListResult",
    "PolicyDependencyRelation",
    "PolicyNodeResult",
    "PolicyDependencyEdge",
    "DependencyGraphResult",
    # Result types - Violations
    "PolicyViolationResult",
    "ViolationsListResult",
    # Result types - Budgets
    "BudgetDefinitionResult",
    "BudgetsListResult",
    # Result types - Requests
    "PolicyRequestResult",
    "PolicyRequestsListResult",
    # Result types - Lessons
    "LessonSummaryResult",
    "LessonsListResult",
    "LessonDetailResult",
    "LessonStatsResult",
]
