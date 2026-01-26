# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Policies facade - unified entry point for policy management
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

IMPLEMENTATION NOTES:
    Re-exports from existing app.services.policies_facade which is
    already properly structured as an L4/L5 facade.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# Re-export from existing facade
# =============================================================================

from app.services.policies_facade import (
    # Facade
    PoliciesFacade,
    get_policies_facade,
    # Result types - Policy Rules
    PolicyRuleSummaryResult,
    PolicyRulesListResult,
    PolicyRuleDetailResult,
    # Result types - Limits
    LimitSummaryResult,
    LimitsListResult,
    LimitDetailResult,
    # Result types - State & Metrics
    PolicyStateResult,
    PolicyMetricsResult,
    # Result types - Conflicts & Dependencies
    PolicyConflictResult,
    ConflictsListResult,
    PolicyDependencyRelation,
    PolicyNodeResult,
    PolicyDependencyEdge,
    DependencyGraphResult,
    # Result types - Violations
    PolicyViolationResult,
    ViolationsListResult,
    # Result types - Budgets
    BudgetDefinitionResult,
    BudgetsListResult,
    # Result types - Requests
    PolicyRequestResult,
    PolicyRequestsListResult,
    # Result types - Lessons
    LessonSummaryResult,
    LessonsListResult,
    LessonDetailResult,
    LessonStatsResult,
)

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
