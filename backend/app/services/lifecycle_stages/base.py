# Layer: L4 — Domain Engine (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for stage base types
# Allowed Imports: hoc_spine canonical base types

"""Compatibility shim.

Canonical base types live at:
  app.hoc.cus.hoc_spine.services.lifecycle_stages_base

This file exists only to preserve import paths while callers migrate.
"""

from app.hoc.cus.hoc_spine.services.lifecycle_stages_base import (  # noqa: F401
    BaseStageHandler,
    StageContext,
    StageHandler,
    StageRegistry,
    StageResult,
    StageStatus,
)

__all__ = [
    "BaseStageHandler",
    "StageContext",
    "StageHandler",
    "StageRegistry",
    "StageResult",
    "StageStatus",
]
