# Layer: L4 — Domain Engine (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for offboarding stage handlers
# Allowed Imports: hoc_spine canonical offboarding engines

"""Compatibility shim.

Canonical offboarding stage handlers live at:
  app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding
"""

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding import (  # noqa: F401
    ArchiveHandler,
    DeactivateHandler,
    DeregisterHandler,
    PurgeHandler,
    VerifyDeactivateHandler,
)

__all__ = [
    "DeregisterHandler",
    "VerifyDeactivateHandler",
    "DeactivateHandler",
    "ArchiveHandler",
    "PurgeHandler",
]
