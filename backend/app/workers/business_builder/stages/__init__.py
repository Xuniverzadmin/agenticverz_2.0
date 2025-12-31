# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Business builder stages package marker
# Callers: Stage imports
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: Package Structure

# Stage implementations for Business Builder Worker
# Each stage can have custom logic beyond agent execution
"""
Stages provide:
1. Input validation
2. Output transformation
3. Integration with external services
4. Custom failure patterns
"""

from .copy import CopyStage
from .research import ResearchStage
from .strategy import StrategyStage
from .ux import UXStage

__all__ = [
    "ResearchStage",
    "StrategyStage",
    "CopyStage",
    "UXStage",
]
