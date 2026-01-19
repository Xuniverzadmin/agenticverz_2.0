# Layer: L4 — Domain Engines
# Product: ai-console
# Role: Activity domain services exports
# Reference: docs/architecture/activity/ACTIVITY_CAPABILITY_REGISTRY.yaml

"""
Activity Domain Services

Provides:
- PatternDetectionService: Detect instability patterns in trace steps
- CostAnalysisService: Analyze cost anomalies via Z-score
- AttentionRankingService: Composite attention scoring
- RunSignalService: Update runs table with signals for Customer Console
- SignalFeedbackService: Signal acknowledge/suppress operations
- signal_identity: Canonical signal fingerprint computation
"""

from app.services.activity.pattern_detection_service import PatternDetectionService
from app.services.activity.cost_analysis_service import CostAnalysisService
from app.services.activity.attention_ranking_service import AttentionRankingService
from app.services.activity.run_signal_service import RunSignalService
from app.services.activity.signal_feedback_service import (
    SignalFeedbackService,
    SignalFeedback,
    SignalContext,
    AcknowledgeResult,
    SuppressResult,
)
from app.services.activity.signal_identity import (
    compute_signal_fingerprint_from_row,
    validate_signal_fingerprint,
)

__all__ = [
    "PatternDetectionService",
    "CostAnalysisService",
    "AttentionRankingService",
    "RunSignalService",
    "SignalFeedbackService",
    "SignalFeedback",
    "SignalContext",
    "AcknowledgeResult",
    "SuppressResult",
    "compute_signal_fingerprint_from_row",
    "validate_signal_fingerprint",
]
