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
- attention_ranking_engine: Attention ranking engine (stub)
- pattern_detection_engine: Pattern detection engine (stub)
- cost_analysis_engine: Cost analysis engine (stub)
- signal_identity: Signal identity utilities
"""

from app.hoc.cus.controls.L5_engines.threshold_engine import (
    DEFAULT_LLM_RUN_PARAMS,
    LLMRunEvaluator,
    LLMRunEvaluatorSync,
    LLMRunThresholdResolver,
    LLMRunThresholdResolverSync,
    ThresholdEvaluationResult,
    ThresholdParams,
    ThresholdParamsUpdate,
    ThresholdSignal,
    ThresholdSignalRecord,
    collect_signals_from_evaluation,
    create_threshold_signal_record,
)
from app.hoc.cus.activity.L5_engines.activity_facade import (
    ActivityFacade,
    get_activity_facade,
)
from app.hoc.cus.general.L4_runtime.facades.run_governance_facade import (
    RunGovernanceFacade,
    get_run_governance_facade,
)

__all__ = [
    "DEFAULT_LLM_RUN_PARAMS",
    "LLMRunEvaluator",
    "LLMRunEvaluatorSync",
    "LLMRunThresholdResolver",
    "LLMRunThresholdResolverSync",
    "ThresholdEvaluationResult",
    "ThresholdParams",
    "ThresholdParamsUpdate",
    "ThresholdSignal",
    "ThresholdSignalRecord",
    "collect_signals_from_evaluation",
    "create_threshold_signal_record",
    # activity_facade
    "ActivityFacade",
    "get_activity_facade",
    # run_governance_facade
    "RunGovernanceFacade",
    "get_run_governance_facade",
]
