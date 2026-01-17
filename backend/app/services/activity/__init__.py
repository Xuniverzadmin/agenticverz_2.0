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
"""

from app.services.activity.pattern_detection_service import PatternDetectionService
from app.services.activity.cost_analysis_service import CostAnalysisService
from app.services.activity.attention_ranking_service import AttentionRankingService

__all__ = [
    "PatternDetectionService",
    "CostAnalysisService",
    "AttentionRankingService",
]
