# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Activity domain services package
"""Activity domain services."""

from app.services.activity.attention_ranking_service import AttentionRankingService
from app.services.activity.cost_analysis_service import CostAnalysisService
from app.services.activity.pattern_detection_service import PatternDetectionService
from app.services.activity.signal_feedback_service import (
    AcknowledgeResult,
    SignalFeedbackService,
    SuppressResult,
)
from app.services.activity.signal_identity import compute_signal_fingerprint_from_row

__all__ = [
    "AttentionRankingService",
    "CostAnalysisService",
    "PatternDetectionService",
    "SignalFeedbackService",
    "AcknowledgeResult",
    "SuppressResult",
    "compute_signal_fingerprint_from_row",
]
