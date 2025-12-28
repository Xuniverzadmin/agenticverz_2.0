"""
C5 Learning Module - Advisory Learning from Historical Outcomes.

This module MUST NOT be imported by:
- app/optimization/killswitch.py
- app/optimization/coordinator.py (core paths)

It MAY be imported by:
- app/api/learning.py (for approval endpoints)
- app/optimization/metrics.py (for learning metrics)

Core Principle:
    Learning observes rollbacks. Humans interpret. Existing envelopes apply.

Reference: PIN-232, C5_S1_LEARNING_SCENARIO.md
"""

from app.learning.config import learning_enabled, require_learning_enabled
from app.learning.suggestions import LearningSuggestion, SuggestionConfidence, SuggestionStatus
from app.learning.tables import LEARNING_ALLOWED_TABLES, LEARNING_FORBIDDEN_TABLES

__all__ = [
    "learning_enabled",
    "require_learning_enabled",
    "LearningSuggestion",
    "SuggestionConfidence",
    "SuggestionStatus",
    "LEARNING_ALLOWED_TABLES",
    "LEARNING_FORBIDDEN_TABLES",
]
