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
"""

from app.services.activity.pattern_detection_service import PatternDetectionService
from app.services.activity.cost_analysis_service import CostAnalysisService
from app.services.activity.attention_ranking_service import AttentionRankingService
from app.services.activity.run_signal_service import RunSignalService

__all__ = [
    "PatternDetectionService",
    "CostAnalysisService",
    "AttentionRankingService",
    "RunSignalService",
]
