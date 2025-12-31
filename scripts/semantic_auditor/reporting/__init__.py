# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Reporting Package Root
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Reporting Module

Generates risk reports from semantic deltas:
- Risk model definitions
- Report building and grouping
- Multiple output formats (markdown, JSON)
"""

from .risk_model import RiskLevel, RiskAssessment
from .report_builder import ReportBuilder

__all__ = ["RiskLevel", "RiskAssessment", "ReportBuilder"]
