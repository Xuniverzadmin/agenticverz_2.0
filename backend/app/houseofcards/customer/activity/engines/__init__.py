# Layer: L4 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: activity domain - decision engines (business logic only)
# Reference: ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
activity / engines (L4)

Decision engines for activity domain. Pure business logic, no DB access.

Exports:
- threshold_engine: Threshold resolution and evaluation logic
- signal_feedback_service: Signal feedback service (stub)
- attention_ranking_service: Attention ranking service (stub)
- pattern_detection_service: Pattern detection service (stub)
- cost_analysis_service: Cost analysis service (stub)
- signal_identity: Signal identity utilities
"""

from app.houseofcards.customer.activity.engines.threshold_engine import (
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
]
