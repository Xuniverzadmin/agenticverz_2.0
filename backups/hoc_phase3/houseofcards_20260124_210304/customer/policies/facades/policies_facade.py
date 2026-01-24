# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB operations)
# Role: Policies domain facade - unified entry point for policy management operations
# Callers: L2 policies API (policies.py)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: POLICIES Domain - Customer Console v1 Constitution
#
"""
Policies Domain Facade (L4)

Unified facade for policy management operations.

Provides:
- Policy Rules: list, get detail
- Limits: list, get detail
- Lessons: list, get detail, stats
- Policy State: synthesized snapshot
- Policy Metrics: enforcement effectiveness
- Policy Conflicts: detect contradictions
- Policy Dependencies: structural relationships
- Policy Violations: unified violation view
- Budget Definitions: enforcement limits
- Policy Requests: pending approvals

All operations are tenant-scoped for isolation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.houseofcards.customer.general.utils.time import utc_now
from app.models.policy_control_plane import (
    Limit,
    LimitBreach,
    LimitIntegrity,
    PolicyEnforcement,
    PolicyRule,
    PolicyRuleIntegrity,
)


# =============================================================================
# Result Types - Policy Rules
# =============================================================================


@dataclass
class PolicyRuleSummaryResult:
    """Policy rule summary for list view (O2)."""

    rule_id: str
    name: str
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    source: str  # MANUAL, SYSTEM, LEARNED
    status: str  # ACTIVE, RETIRED
    created_at: datetime
    created_by: Optional[str]
    integrity_status: str  # VERIFIED, DEGRADED, FAILED
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
    limit_category: str  # BUDGET, RATE, THRESHOLD
    limit_type: str  # COST_USD, TOKENS_*, REQUESTS_*, etc.
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
    enforcement: str  # BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT
    status: str  # ACTIVE, DISABLED
    max_value: Decimal
    window_seconds: Optional[int]
    reset_period: Optional[str]  # DAILY, WEEKLY, MONTHLY, NONE
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
    conflict_type: str  # SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE
    severity: str  # BLOCKING, WARNING
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
    dependency_type: str  # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
    reason: str


@dataclass
class PolicyNodeResult:
    """A node in the dependency graph (DFT-O5)."""

    id: str
    name: str
    rule_type: str  # SYSTEM, SAFETY, ETHICAL, TEMPORAL
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
    violation_type: str  # cost, quota, rate, temporal, safety, ethical
    severity: float
    source: str  # guard, sim, runtime
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
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    max_value: Decimal
    reset_period: Optional[str]  # DAILY, WEEKLY, MONTHLY, NONE
    enforcement: str  # BLOCK, WARN
    status: str  # ACTIVE, DISABLED
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
# Policies Facade
# =============================================================================


class PoliciesFacade:
    """
    Unified facade for policy management.

    Provides:
    - Policy Rules: list, get detail
    - Limits: list, get detail
    - Lessons: list, get detail, stats
    - Policy State: synthesized snapshot
    - Policy Metrics: enforcement effectiveness
    - Policy Conflicts: detect contradictions
    - Policy Dependencies: structural relationships
    - Policy Violations: unified violation view
    - Budget Definitions: enforcement limits
    - Policy Requests: pending approvals

    All operations are tenant-scoped for isolation.
    """

    # -------------------------------------------------------------------------
    # Policy Rules Operations
    # -------------------------------------------------------------------------

    async def list_policy_rules(
        self,
        session: AsyncSession,
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
        thirty_days_ago = utc_now() - timedelta(days=30)

        # Subquery: enforcement aggregation
        enforcement_stats_subq = (
            select(
                PolicyEnforcement.rule_id.label("rule_id"),
                func.count(PolicyEnforcement.id).label("trigger_count_30d"),
                func.max(PolicyEnforcement.triggered_at).label("last_triggered_at"),
            )
            .where(PolicyEnforcement.triggered_at >= thirty_days_ago)
            .group_by(PolicyEnforcement.rule_id)
            .subquery()
        )

        # Main query
        stmt = (
            select(
                PolicyRule.id.label("rule_id"),
                PolicyRule.name,
                PolicyRule.enforcement_mode,
                PolicyRule.scope,
                PolicyRule.source,
                PolicyRule.status,
                PolicyRule.created_at,
                PolicyRule.created_by,
                PolicyRuleIntegrity.integrity_status,
                PolicyRuleIntegrity.integrity_score,
                func.coalesce(enforcement_stats_subq.c.trigger_count_30d, 0).label("trigger_count_30d"),
                enforcement_stats_subq.c.last_triggered_at,
            )
            .join(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
            .outerjoin(enforcement_stats_subq, enforcement_stats_subq.c.rule_id == PolicyRule.id)
            .where(
                and_(
                    PolicyRule.tenant_id == tenant_id,
                    PolicyRule.status == status,
                )
            )
            .order_by(
                enforcement_stats_subq.c.last_triggered_at.desc().nullslast(),
                PolicyRule.created_at.desc(),
            )
        )

        # Apply optional filters
        if enforcement_mode is not None:
            stmt = stmt.where(PolicyRule.enforcement_mode == enforcement_mode)
            filters_applied["enforcement_mode"] = enforcement_mode

        if scope is not None:
            stmt = stmt.where(PolicyRule.scope == scope)
            filters_applied["scope"] = scope

        if source is not None:
            stmt = stmt.where(PolicyRule.source == source)
            filters_applied["source"] = source

        if rule_type is not None:
            stmt = stmt.where(PolicyRule.rule_type == rule_type)
            filters_applied["rule_type"] = rule_type

        if created_after is not None:
            stmt = stmt.where(PolicyRule.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(PolicyRule.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count total
        count_stmt = (
            select(func.count(PolicyRule.id))
            .where(PolicyRule.tenant_id == tenant_id)
            .where(PolicyRule.status == status)
        )
        if enforcement_mode:
            count_stmt = count_stmt.where(PolicyRule.enforcement_mode == enforcement_mode)
        if scope:
            count_stmt = count_stmt.where(PolicyRule.scope == scope)
        if source:
            count_stmt = count_stmt.where(PolicyRule.source == source)
        if rule_type:
            count_stmt = count_stmt.where(PolicyRule.rule_type == rule_type)
        if created_after:
            count_stmt = count_stmt.where(PolicyRule.created_at >= created_after)
        if created_before:
            count_stmt = count_stmt.where(PolicyRule.created_at <= created_before)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

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
            for row in rows
        ]

        return PolicyRulesListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_policy_rule_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        rule_id: str,
    ) -> Optional[PolicyRuleDetailResult]:
        """Get policy rule detail. Tenant isolation enforced."""
        thirty_days_ago = utc_now() - timedelta(days=30)

        # Subquery for trigger stats
        enforcement_stats_subq = (
            select(
                PolicyEnforcement.rule_id.label("rule_id"),
                func.count(PolicyEnforcement.id).label("trigger_count_30d"),
                func.max(PolicyEnforcement.triggered_at).label("last_triggered_at"),
            )
            .where(
                PolicyEnforcement.rule_id == rule_id,
                PolicyEnforcement.triggered_at >= thirty_days_ago,
            )
            .group_by(PolicyEnforcement.rule_id)
            .subquery()
        )

        stmt = (
            select(
                PolicyRule,
                PolicyRuleIntegrity.integrity_status,
                PolicyRuleIntegrity.integrity_score,
                func.coalesce(enforcement_stats_subq.c.trigger_count_30d, 0).label("trigger_count_30d"),
                enforcement_stats_subq.c.last_triggered_at,
            )
            .join(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
            .outerjoin(enforcement_stats_subq, enforcement_stats_subq.c.rule_id == PolicyRule.id)
            .where(
                PolicyRule.id == rule_id,
                PolicyRule.tenant_id == tenant_id,
            )
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            return None

        rule = row[0]  # PolicyRule model

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
            integrity_status=row[1],
            integrity_score=row[2],
            trigger_count_30d=row[3],
            last_triggered_at=row[4],
            rule_definition=getattr(rule, "rule_definition", None),
            violation_count_total=0,
        )

    # -------------------------------------------------------------------------
    # Limits Operations
    # -------------------------------------------------------------------------

    async def list_limits(
        self,
        session: AsyncSession,
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
            "tenant_id": tenant_id,
            "category": category,
            "status": status,
        }

        thirty_days_ago = utc_now() - timedelta(days=30)

        # Subquery: breach aggregation
        breach_agg_subq = (
            select(
                LimitBreach.limit_id.label("limit_id"),
                func.count().label("breach_count_30d"),
                func.max(LimitBreach.breached_at).label("last_breached_at"),
            )
            .where(LimitBreach.breached_at >= thirty_days_ago)
            .group_by(LimitBreach.limit_id)
            .subquery()
        )

        # Main query
        stmt = (
            select(
                Limit.id.label("limit_id"),
                Limit.name,
                Limit.limit_category,
                Limit.limit_type,
                Limit.scope,
                Limit.enforcement,
                Limit.status,
                Limit.max_value,
                Limit.window_seconds,
                Limit.reset_period,
                LimitIntegrity.integrity_status,
                LimitIntegrity.integrity_score,
                func.coalesce(breach_agg_subq.c.breach_count_30d, 0).label("breach_count_30d"),
                breach_agg_subq.c.last_breached_at,
                Limit.created_at,
            )
            .select_from(Limit)
            .join(LimitIntegrity, LimitIntegrity.limit_id == Limit.id)
            .outerjoin(breach_agg_subq, breach_agg_subq.c.limit_id == Limit.id)
            .where(
                and_(
                    Limit.tenant_id == tenant_id,
                    Limit.limit_category == category,
                    Limit.status == status,
                )
            )
            .order_by(
                breach_agg_subq.c.last_breached_at.desc().nullslast(),
                Limit.created_at.desc(),
            )
        )

        # Apply optional filters
        if scope is not None:
            stmt = stmt.where(Limit.scope == scope)
            filters_applied["scope"] = scope

        if enforcement is not None:
            stmt = stmt.where(Limit.enforcement == enforcement)
            filters_applied["enforcement"] = enforcement

        if limit_type is not None:
            if limit_type.endswith("*"):
                prefix = limit_type[:-1]
                stmt = stmt.where(Limit.limit_type.startswith(prefix))
            else:
                stmt = stmt.where(Limit.limit_type == limit_type)
            filters_applied["limit_type"] = limit_type

        if created_after is not None:
            stmt = stmt.where(Limit.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(Limit.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count total
        count_stmt = (
            select(func.count(Limit.id))
            .where(Limit.tenant_id == tenant_id)
            .where(Limit.limit_category == category)
            .where(Limit.status == status)
        )
        if scope:
            count_stmt = count_stmt.where(Limit.scope == scope)
        if enforcement:
            count_stmt = count_stmt.where(Limit.enforcement == enforcement)
        if limit_type:
            if limit_type.endswith("*"):
                prefix = limit_type[:-1]
                count_stmt = count_stmt.where(Limit.limit_type.startswith(prefix))
            else:
                count_stmt = count_stmt.where(Limit.limit_type == limit_type)
        if created_after:
            count_stmt = count_stmt.where(Limit.created_at >= created_after)
        if created_before:
            count_stmt = count_stmt.where(Limit.created_at <= created_before)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

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
            for row in rows
        ]

        return LimitsListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_limit_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        limit_id: str,
    ) -> Optional[LimitDetailResult]:
        """Get limit detail. Tenant isolation enforced."""
        thirty_days_ago = utc_now() - timedelta(days=30)

        # Subquery for breach stats
        breach_agg_subq = (
            select(
                LimitBreach.limit_id.label("limit_id"),
                func.count().label("breach_count_30d"),
                func.max(LimitBreach.breached_at).label("last_breached_at"),
            )
            .where(
                LimitBreach.limit_id == limit_id,
                LimitBreach.breached_at >= thirty_days_ago,
            )
            .group_by(LimitBreach.limit_id)
            .subquery()
        )

        stmt = (
            select(
                Limit,
                LimitIntegrity.integrity_status,
                LimitIntegrity.integrity_score,
                func.coalesce(breach_agg_subq.c.breach_count_30d, 0).label("breach_count_30d"),
                breach_agg_subq.c.last_breached_at,
            )
            .join(LimitIntegrity, LimitIntegrity.limit_id == Limit.id)
            .outerjoin(breach_agg_subq, breach_agg_subq.c.limit_id == Limit.id)
            .where(
                Limit.id == limit_id,
                Limit.tenant_id == tenant_id,
            )
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            return None

        lim = row[0]

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
            integrity_status=row[1],
            integrity_score=row[2],
            breach_count_30d=row[3],
            last_breached_at=row[4],
            created_at=lim.created_at,
            updated_at=getattr(lim, "updated_at", None),
        )

    # -------------------------------------------------------------------------
    # Lessons Operations (delegates to LessonsLearnedEngine)
    # -------------------------------------------------------------------------

    async def list_lessons(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> LessonsListResult:
        """List lessons learned for the tenant."""
        from app.services.policy.lessons_engine import get_lessons_learned_engine

        _ = session  # Engine is sync, doesn't use session

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
                created_at=datetime.fromisoformat(lesson["created_at"]) if lesson["created_at"] else utc_now(),
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
        session: AsyncSession,
        tenant_id: str,
        lesson_id: str,
    ) -> Optional[LessonDetailResult]:
        """Get lesson detail."""
        from uuid import UUID
        from app.services.policy.lessons_engine import get_lessons_learned_engine

        _ = session  # Engine is sync

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
        session: AsyncSession,
        tenant_id: str,
    ) -> LessonStatsResult:
        """Get lesson statistics."""
        from app.services.policy.lessons_engine import get_lessons_learned_engine

        _ = session  # Engine is sync

        engine = get_lessons_learned_engine()
        stats = engine.get_lesson_stats(tenant_id=tenant_id)

        return LessonStatsResult(
            total=stats.get("total", 0),
            by_type=stats.get("by_type", {}),
            by_status=stats.get("by_status", {}),
        )

    # -------------------------------------------------------------------------
    # Policy State & Metrics (delegates to PolicyEngine)
    # -------------------------------------------------------------------------

    async def get_policy_state(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> PolicyStateResult:
        """Get policy layer state summary."""
        from app.policy.engine import get_policy_engine
        from app.services.policy.lessons_engine import get_lessons_learned_engine

        engine = get_policy_engine()
        state = await engine.get_state(session)

        # Get pending lessons count
        lessons_engine = get_lessons_learned_engine()
        lessons_stats = lessons_engine.get_lesson_stats(tenant_id=tenant_id)
        pending_lessons = lessons_stats.get("by_status", {}).get("pending", 0)

        # Get drafts pending
        drafts_count = 0
        try:
            from app.models.policy import PolicyProposal
            drafts_result = await session.execute(
                select(func.count(PolicyProposal.id)).where(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "pending",
                )
            )
            drafts_count = drafts_result.scalar() or 0
        except Exception:
            pass

        # Get conflicts count
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
            last_updated=utc_now(),
        )

    async def get_policy_metrics(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        hours: int = 24,
    ) -> PolicyMetricsResult:
        """Get policy enforcement metrics."""
        from app.policy.engine import get_policy_engine

        _ = tenant_id  # For future tenant-scoped metrics

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
        session: AsyncSession,
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
        from app.policy.engine import get_policy_engine
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

        # Map string violation_type to enum
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
            since=utc_now() - timedelta(hours=hours),
            limit=limit + 1,
        )

        # Apply filters
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
    # Policy Conflicts (delegates to PolicyConflictEngine)
    # -------------------------------------------------------------------------

    async def list_policy_conflicts(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        policy_id: Optional[str] = None,
        severity: Optional[str] = None,
        include_resolved: bool = False,
    ) -> ConflictsListResult:
        """Detect policy conflicts."""
        from app.services.policy_graph_engine import ConflictSeverity, get_conflict_engine

        engine = get_conflict_engine(tenant_id)

        severity_filter = None
        if severity:
            try:
                severity_filter = ConflictSeverity(severity.upper())
            except ValueError:
                pass

        result = await engine.detect_conflicts(
            session=session,
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
    # Policy Dependencies (delegates to PolicyDependencyEngine)
    # -------------------------------------------------------------------------

    async def get_policy_dependencies(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        policy_id: Optional[str] = None,
    ) -> DependencyGraphResult:
        """Get policy dependency graph."""
        from app.services.policy_graph_engine import get_dependency_engine

        engine = get_dependency_engine(tenant_id)
        result = await engine.compute_dependency_graph(session, policy_id=policy_id)

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
    # Policy Requests (Pending Approvals)
    # -------------------------------------------------------------------------

    async def list_policy_requests(
        self,
        session: AsyncSession,
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
        from datetime import timezone
        from app.models.policy import PolicyProposal

        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

        if proposal_type:
            filters_applied["proposal_type"] = proposal_type
        if days_old:
            filters_applied["days_old"] = days_old
        if include_synthetic:
            filters_applied["include_synthetic"] = True

        now = datetime.now(timezone.utc)

        # Build query
        stmt = select(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == status,
            )
        )

        if not include_synthetic:
            stmt = stmt.where(
                (PolicyProposal.is_synthetic == False) | (PolicyProposal.is_synthetic.is_(None))
            )

        if proposal_type:
            stmt = stmt.where(PolicyProposal.proposal_type == proposal_type)

        if days_old:
            cutoff = now - timedelta(days=days_old)
            stmt = stmt.where(PolicyProposal.created_at <= cutoff)

        # Count pending
        count_stmt = select(func.count()).select_from(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == "draft",
                (PolicyProposal.is_synthetic == False) | (PolicyProposal.is_synthetic.is_(None)),
            )
        )
        count_result = await session.execute(count_stmt)
        pending_count = count_result.scalar() or 0

        stmt = stmt.order_by(PolicyProposal.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        proposals = result.scalars().all()

        items = []
        for prop in proposals:
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
            pending_count=pending_count,
            filters_applied=filters_applied,
        )

    # -------------------------------------------------------------------------
    # Budget Definitions
    # -------------------------------------------------------------------------

    async def list_budgets(
        self,
        session: AsyncSession,
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

        stmt = (
            select(Limit)
            .where(
                and_(
                    Limit.tenant_id == tenant_id,
                    Limit.limit_category == "BUDGET",
                    Limit.status == status,
                )
            )
            .order_by(Limit.created_at.desc())
        )

        if scope:
            stmt = stmt.where(Limit.scope == scope)

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        limits = result.scalars().all()

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

_facade_instance: PoliciesFacade | None = None


def get_policies_facade() -> PoliciesFacade:
    """Get the singleton PoliciesFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = PoliciesFacade()
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
