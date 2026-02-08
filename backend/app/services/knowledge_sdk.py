# Layer: L2 — Product APIs (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for Knowledge SDK facade
# Callers: legacy imports, tests
# Allowed Imports: hoc_spine canonical implementation

"""Compatibility shim.

Canonical implementation lives at:
  app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_sdk

This file exists only to preserve import paths while callers migrate.
"""

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_sdk import (
    KnowledgePlaneConfig,
    KnowledgeSDK,
    PlaneInfo,
    SDKResult,
    WaitOptions,
    create_knowledge_sdk,
)

__all__ = [
    "KnowledgeSDK",
    "KnowledgePlaneConfig",
    "WaitOptions",
    "SDKResult",
    "PlaneInfo",
    "create_knowledge_sdk",
]
