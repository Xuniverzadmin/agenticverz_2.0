# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: Overview domain engines - business logic composition
# Location: hoc/cus/overview/L5_engines/
# Reference: PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md

"""
Overview L5 Engines

Business logic for overview domain aggregation and composition.
"""

from app.hoc.cus.overview.L5_engines.overview_facade import (
    CostPeriod,
    CostsResult,
    DecisionItem,
    DecisionsCountResult,
    DecisionsResult,
    DomainCount,
    get_overview_facade,
    HighlightsResult,
    LimitCostItem,
    OverviewFacade,
    RecoveryStatsResult,
    SystemPulse,
)

__all__ = [
    # Facade
    "OverviewFacade",
    "get_overview_facade",
    # Result types
    "SystemPulse",
    "DomainCount",
    "HighlightsResult",
    "DecisionItem",
    "DecisionsResult",
    "CostPeriod",
    "LimitCostItem",
    "CostsResult",
    "DecisionsCountResult",
    "RecoveryStatsResult",
]
