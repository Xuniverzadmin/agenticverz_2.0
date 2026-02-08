# Layer: L4 — Domain Engine (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for KnowledgeLifecycleManager
# Callers: legacy imports, tests
# Allowed Imports: hoc_spine canonical implementation

"""Compatibility shim.

Canonical implementation lives at:
  app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager

This file exists only to preserve import paths while callers migrate.
"""

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager import (
    GateDecision,
    GateResult,
    KnowledgeLifecycleManager,
    KnowledgePlane,
    TransitionRequest,
    TransitionResponse,
    get_knowledge_lifecycle_manager,
    reset_manager,
)

__all__ = [
    "GateDecision",
    "GateResult",
    "KnowledgeLifecycleManager",
    "KnowledgePlane",
    "TransitionRequest",
    "TransitionResponse",
    "get_knowledge_lifecycle_manager",
    "reset_manager",
]
