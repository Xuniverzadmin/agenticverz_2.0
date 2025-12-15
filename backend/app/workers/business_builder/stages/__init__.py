# Stage implementations for Business Builder Worker
# Each stage can have custom logic beyond agent execution
"""
Stages provide:
1. Input validation
2. Output transformation
3. Integration with external services
4. Custom failure patterns
"""

from .research import ResearchStage
from .strategy import StrategyStage
from .copy import CopyStage
from .ux import UXStage

__all__ = [
    "ResearchStage",
    "StrategyStage",
    "CopyStage",
    "UXStage",
]
