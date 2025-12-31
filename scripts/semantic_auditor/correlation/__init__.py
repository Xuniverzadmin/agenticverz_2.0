# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Correlation Package Root
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Correlation Module

Correlates declared semantics with observed behavior:
- Loads semantic contracts and coordinate maps
- Aggregates signals per file
- Computes semantic deltas
"""

from .declared_semantics import DeclaredSemantics
from .observed_behavior import ObservedBehavior
from .delta_engine import DeltaEngine

__all__ = ["DeclaredSemantics", "ObservedBehavior", "DeltaEngine"]
