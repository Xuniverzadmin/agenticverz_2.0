# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Signals Package Root
# Authority: None (observational only)
# Callers: semantic_auditor.correlation
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Signals Module

Detects semantic signals in the codebase:
- Affordance signals (missing/incomplete headers)
- Execution signals (async blocking calls, sync-over-async)
- Authority signals (DB writes outside write services)
- Layering signals (import graph violations)
"""

from .affordance import AffordanceSignalDetector
from .execution import ExecutionSignalDetector
from .authority import AuthoritySignalDetector
from .layering import LayeringSignalDetector

__all__ = [
    "AffordanceSignalDetector",
    "ExecutionSignalDetector",
    "AuthoritySignalDetector",
    "LayeringSignalDetector",
]
