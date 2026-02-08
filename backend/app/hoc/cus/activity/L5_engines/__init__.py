# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: activity domain - decision engines (business logic only)
# Callers: facades/activity_facade.py, API routes
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md
# NOTE: Layer reclassified L4→L5 (2026-01-24) per HOC Layer Topology V1
#       *_service.py files renamed to *_engine.py per BANNED_NAMING

"""
activity / engines (L5)

Decision engines for activity domain. Pure business logic, no DB access.

Exports:
- threshold_engine: Threshold resolution and evaluation logic
- signal_feedback_engine: Signal feedback engine (stub)
- attention_ranking: Attention ranking (stub, demoted from _engine 2026-02-08)
- pattern_detection: Pattern detection (stub, demoted from _engine 2026-02-08)
- cost_analysis: Cost analysis (stub, demoted from _engine 2026-02-08)
- signal_identity: Signal identity utilities
"""

from app.hoc.cus.activity.L5_engines.activity_facade import (
    ActivityFacade,
    get_activity_facade,
)

# NOTE: RunGovernanceFacade removed (PIN-520 L5 purity)
# Callers should import directly from hoc_spine if needed:
#   from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import get_run_governance_facade

__all__ = [
    # activity_facade
    "ActivityFacade",
    "get_activity_facade",
]
