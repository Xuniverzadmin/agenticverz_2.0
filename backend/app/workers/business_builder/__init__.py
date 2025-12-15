# Business Builder Worker v0.2
# The first worker that demonstrates M0-M20 moats
"""
Business Builder: Idea -> Research -> Strategy -> Build -> Launch

Uses:
- M4: Deterministic execution engine
- M9: Failure pattern catalog
- M10: Recovery suggestion engine
- M11: Skills (webhook, embed, kv_store)
- M12: Multi-agent coordination
- M15: Strategy-Bound Agents (SBA)
- M17: CARE routing engine
- M18: Drift detection & reputation
- M19: Policy constitutional
- M20: PLang compiler & runtime
"""

from .worker import BusinessBuilderWorker
from .execution_plan import ExecutionPlan, ExecutionStage
from .schemas.brand import BrandSchema

__all__ = [
    "BusinessBuilderWorker",
    "ExecutionPlan",
    "ExecutionStage",
    "BrandSchema",
]
