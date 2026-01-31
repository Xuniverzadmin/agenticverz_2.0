# Layer: L5 — Domain Engine (Facade)
# AUDIENCE: CUSTOMER
# Role: Policies facade - unified entry point for policy management
# NOTE: Legacy import disconnected (2026-01-31) — was re-exporting from
#       app.services.policies_facade. Stubbed pending HOC rewiring.
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: policies.py (L2 API)
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 3, PIN-470

"""
PoliciesFacade (SWEEP-03 Batch 3)

PURPOSE:
    HOC wrapper for policies facade - unified policy management.
    Called by L2 policies API.

INTERFACE:
    - PoliciesFacade
    - get_policies_facade() -> PoliciesFacade

IMPLEMENTATION STATUS:
    Legacy import from app.services.policies_facade DISCONNECTED.
    Stubbed with placeholder classes pending HOC rewiring phase.
    TODO: Rewire to HOC equivalent candidate during rewiring phase.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# =============================================================================
# Stub result types — TODO: rewire to HOC equivalent candidate during rewiring phase
# =============================================================================


@dataclass
class PolicyRuleSummaryResult:
    """Policy rule summary — stub."""
    id: str = ""
    name: str = ""
    status: str = ""


@dataclass
class PolicyRulesListResult:
    """Policy rules list — stub."""
    items: list[PolicyRuleSummaryResult] = field(default_factory=list)
    total: int = 0


@dataclass
class PolicyRuleDetailResult(PolicyRuleSummaryResult):
    """Policy rule detail — stub."""
    description: str = ""


@dataclass
class LimitSummaryResult:
    """Limit summary — stub."""
    id: str = ""
    name: str = ""


@dataclass
class LimitsListResult:
    """Limits list — stub."""
    items: list[LimitSummaryResult] = field(default_factory=list)
    total: int = 0


@dataclass
class LimitDetailResult(LimitSummaryResult):
    """Limit detail — stub."""
    pass


@dataclass
class PolicyStateResult:
    """Policy state — stub."""
    state: str = "active"


@dataclass
class PolicyMetricsResult:
    """Policy metrics — stub."""
    total_policies: int = 0
    active_policies: int = 0


@dataclass
class PolicyConflictResult:
    """Policy conflict — stub."""
    id: str = ""


@dataclass
class ConflictsListResult:
    """Conflicts list — stub."""
    items: list[PolicyConflictResult] = field(default_factory=list)
    total: int = 0


@dataclass
class PolicyDependencyRelation:
    """Policy dependency relation — stub."""
    source: str = ""
    target: str = ""


@dataclass
class PolicyNodeResult:
    """Policy node — stub."""
    id: str = ""


@dataclass
class PolicyDependencyEdge:
    """Policy dependency edge — stub."""
    source: str = ""
    target: str = ""


@dataclass
class DependencyGraphResult:
    """Dependency graph — stub."""
    nodes: list[PolicyNodeResult] = field(default_factory=list)
    edges: list[PolicyDependencyEdge] = field(default_factory=list)


@dataclass
class PolicyViolationResult:
    """Policy violation — stub."""
    id: str = ""


@dataclass
class ViolationsListResult:
    """Violations list — stub."""
    items: list[PolicyViolationResult] = field(default_factory=list)
    total: int = 0


@dataclass
class BudgetDefinitionResult:
    """Budget definition — stub."""
    id: str = ""


@dataclass
class BudgetsListResult:
    """Budgets list — stub."""
    items: list[BudgetDefinitionResult] = field(default_factory=list)
    total: int = 0


@dataclass
class PolicyRequestResult:
    """Policy request — stub."""
    id: str = ""


@dataclass
class PolicyRequestsListResult:
    """Policy requests list — stub."""
    items: list[PolicyRequestResult] = field(default_factory=list)
    total: int = 0


@dataclass
class LessonSummaryResult:
    """Lesson summary — stub."""
    id: str = ""


@dataclass
class LessonsListResult:
    """Lessons list — stub."""
    items: list[LessonSummaryResult] = field(default_factory=list)
    total: int = 0


@dataclass
class LessonDetailResult(LessonSummaryResult):
    """Lesson detail — stub."""
    pass


@dataclass
class LessonStatsResult:
    """Lesson stats — stub."""
    total: int = 0


class PoliciesFacade:
    """Policies facade — stub.

    TODO: Rewire to HOC equivalent candidate during rewiring phase.
    Previously re-exported from app.services.policies_facade (legacy, now disconnected).
    """

    async def list_policy_rules(self, **kwargs: Any) -> PolicyRulesListResult:
        return PolicyRulesListResult()

    async def get_policy_rule_detail(self, **kwargs: Any) -> Optional[PolicyRuleDetailResult]:
        return None

    async def list_limits(self, **kwargs: Any) -> LimitsListResult:
        return LimitsListResult()

    async def get_limit_detail(self, **kwargs: Any) -> Optional[LimitDetailResult]:
        return None

    async def get_policy_state(self, **kwargs: Any) -> PolicyStateResult:
        return PolicyStateResult()

    async def get_policy_metrics(self, **kwargs: Any) -> PolicyMetricsResult:
        return PolicyMetricsResult()

    async def list_conflicts(self, **kwargs: Any) -> ConflictsListResult:
        return ConflictsListResult()

    async def get_dependency_graph(self, **kwargs: Any) -> DependencyGraphResult:
        return DependencyGraphResult()

    async def list_violations(self, **kwargs: Any) -> ViolationsListResult:
        return ViolationsListResult()

    async def list_budgets(self, **kwargs: Any) -> BudgetsListResult:
        return BudgetsListResult()

    async def list_requests(self, **kwargs: Any) -> PolicyRequestsListResult:
        return PolicyRequestsListResult()

    async def list_lessons(self, **kwargs: Any) -> LessonsListResult:
        return LessonsListResult()

    async def get_lesson_stats(self, **kwargs: Any) -> LessonStatsResult:
        return LessonStatsResult()


_facade_instance: Optional[PoliciesFacade] = None


def get_policies_facade() -> PoliciesFacade:
    """Get the PoliciesFacade singleton instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = PoliciesFacade()
    return _facade_instance


__all__ = [
    # Facade
    "PoliciesFacade",
    "get_policies_facade",
    # Result types
    "PolicyRuleSummaryResult",
    "PolicyRulesListResult",
    "PolicyRuleDetailResult",
    "LimitSummaryResult",
    "LimitsListResult",
    "LimitDetailResult",
    "PolicyStateResult",
    "PolicyMetricsResult",
    "PolicyConflictResult",
    "ConflictsListResult",
    "PolicyDependencyRelation",
    "PolicyNodeResult",
    "PolicyDependencyEdge",
    "DependencyGraphResult",
    "PolicyViolationResult",
    "ViolationsListResult",
    "BudgetDefinitionResult",
    "BudgetsListResult",
    "PolicyRequestResult",
    "PolicyRequestsListResult",
    "LessonSummaryResult",
    "LessonsListResult",
    "LessonDetailResult",
    "LessonStatsResult",
]
