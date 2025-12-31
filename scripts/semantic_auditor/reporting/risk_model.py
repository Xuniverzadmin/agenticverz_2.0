# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Risk Model Definitions
# Authority: None (observational only)
# Callers: semantic_auditor.reporting.report_builder
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Risk Model

Defines risk levels and assessment logic for semantic deltas.
This is observational - it produces risk assessments, not verdicts.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..correlation.delta_engine import SemanticDelta, DeltaReport


class RiskLevel(Enum):
    """Risk levels for semantic deltas."""

    INFO = "INFO"           # Informational, no action needed
    WARNING = "WARNING"     # Potential issue, should review
    HIGH_RISK = "HIGH_RISK"  # Likely issue, should address
    CRITICAL = "CRITICAL"   # Severe issue, priority fix


@dataclass
class RiskAssessment:
    """Risk assessment for a delta or group of deltas."""

    level: RiskLevel
    score: int  # Numeric score for sorting/comparison
    reason: str
    recommendations: List[str]


class RiskModel:
    """Defines and applies risk assessments."""

    # Base scores for each risk level
    LEVEL_SCORES: Dict[RiskLevel, int] = {
        RiskLevel.INFO: 1,
        RiskLevel.WARNING: 5,
        RiskLevel.HIGH_RISK: 25,
        RiskLevel.CRITICAL: 100,
    }

    # Risk descriptions and recommendations by delta type
    RISK_DEFINITIONS: Dict[str, Dict] = {
        "MISSING_SEMANTIC_HEADER": {
            "level": RiskLevel.WARNING,
            "reason": "Boundary file lacks semantic contract declaration",
            "recommendations": [
                "Add semantic header with Layer, Role, Authority fields",
                "Reference the appropriate contract document",
                "Ensure callers and execution context are documented",
            ],
        },
        "INCOMPLETE_SEMANTIC_HEADER": {
            "level": RiskLevel.INFO,
            "reason": "Semantic header exists but is incomplete",
            "recommendations": [
                "Add missing required fields to header",
                "Review and complete optional fields",
            ],
        },
        "ASYNC_BLOCKING_CALL": {
            "level": RiskLevel.HIGH_RISK,
            "reason": "Blocking I/O in async context can cause event loop starvation",
            "recommendations": [
                "Replace blocking call with async equivalent",
                "Use asyncio.to_thread() for unavoidable blocking calls",
                "Consider if function should be sync instead",
            ],
        },
        "WRITE_OUTSIDE_WRITE_SERVICE": {
            "level": RiskLevel.HIGH_RISK,
            "reason": "Database writes outside designated write services violate authority boundaries",
            "recommendations": [
                "Move write operation to appropriate *_write_service.py",
                "If intentional, document the authority exception",
                "Review transaction boundaries",
            ],
        },
        "LAYER_IMPORT_VIOLATION": {
            "level": RiskLevel.WARNING,
            "reason": "Import violates layered architecture constraints",
            "recommendations": [
                "Refactor to respect layer boundaries",
                "Use dependency injection instead of direct import",
                "Consider if the layer assignment is correct",
            ],
        },
    }

    def __init__(self):
        """Initialize the risk model."""
        pass

    def assess_delta(self, delta: SemanticDelta) -> RiskAssessment:
        """
        Assess the risk of a single delta.

        Args:
            delta: The semantic delta to assess

        Returns:
            RiskAssessment with level, score, and recommendations
        """
        definition = self.RISK_DEFINITIONS.get(delta.delta_type)

        if definition:
            level = definition["level"]
            return RiskAssessment(
                level=level,
                score=self.LEVEL_SCORES[level],
                reason=definition["reason"],
                recommendations=definition["recommendations"],
            )

        # Unknown delta type - default to INFO
        return RiskAssessment(
            level=RiskLevel.INFO,
            score=self.LEVEL_SCORES[RiskLevel.INFO],
            reason="Unknown delta type",
            recommendations=["Review this finding manually"],
        )

    def assess_report(self, report: DeltaReport) -> Dict[str, int]:
        """
        Compute overall risk scores for a report.

        Args:
            report: The delta report to assess

        Returns:
            Dict with total_score and counts per level
        """
        total_score = 0
        level_counts = {level.value: 0 for level in RiskLevel}

        for delta in report.deltas:
            assessment = self.assess_delta(delta)
            total_score += assessment.score
            level_counts[assessment.level.value] += 1

        return {
            "total_score": total_score,
            **level_counts,
        }

    def get_severity_from_string(self, severity: str) -> RiskLevel:
        """Convert a severity string to RiskLevel."""
        try:
            return RiskLevel(severity)
        except ValueError:
            return RiskLevel.INFO

    def get_recommendations(self, delta_type: str) -> List[str]:
        """Get recommendations for a delta type."""
        definition = self.RISK_DEFINITIONS.get(delta_type, {})
        return definition.get("recommendations", [])
