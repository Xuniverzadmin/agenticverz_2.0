# capability_id: CAP-012
# Layer: L5 — Execution & Workers
# Product: system-wide
# Role: Worker hooks package
# Reference: GAP-137, GAP-138, GAP-139, GAP-140

"""
Worker hooks for governance enforcement in the runner execution path.

These hooks intercept execution at critical points to enforce:
- Retrieval mediation (GAP-137)
- Hallucination detection (GAP-138)
- Monitor/limit enforcement (GAP-139)
- Step enforcement event bus (GAP-140)
"""

from app.hoc.int.worker.hooks.retrieval_hook import (
    RetrievalHook,
    RetrievalRequest,
    RetrievalResponse,
    get_retrieval_hook,
    configure_retrieval_hook,
)

from app.hoc.int.worker.hooks.hallucination_hook import (
    HallucinationHook,
    HallucinationAnnotation,
    get_hallucination_hook,
    configure_hallucination_hook,
)

from app.hoc.int.worker.hooks.limit_hook import (
    LimitHook,
    LimitCheckResult,
    LimitDecision,
    UsageRecord,
    get_limit_hook,
    configure_limit_hook,
)

from app.hoc.int.worker.hooks.step_enforcement_hook import (
    StepEnforcementHook,
    StepEnforcementEvent,
    get_step_enforcement_hook,
    configure_step_enforcement_hook,
)

__all__ = [
    # GAP-137: Retrieval Hook
    "RetrievalHook",
    "RetrievalRequest",
    "RetrievalResponse",
    "get_retrieval_hook",
    "configure_retrieval_hook",
    # GAP-138: Hallucination Hook
    "HallucinationHook",
    "HallucinationAnnotation",
    "get_hallucination_hook",
    "configure_hallucination_hook",
    # GAP-139: Limit Hook
    "LimitHook",
    "LimitCheckResult",
    "LimitDecision",
    "UsageRecord",
    "get_limit_hook",
    "configure_limit_hook",
    # GAP-140: Step Enforcement Hook
    "StepEnforcementHook",
    "StepEnforcementEvent",
    "get_step_enforcement_hook",
    "configure_step_enforcement_hook",
]
