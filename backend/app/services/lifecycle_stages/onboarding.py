# Layer: L4 — Domain Engine (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for onboarding stage handlers
# Allowed Imports: hoc_spine canonical onboarding engines

"""Compatibility shim.

Canonical onboarding stage handlers live at:
  app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding
"""

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding import (  # noqa: F401
    ActivateHandler,
    ClassifyHandler,
    GovernHandler,
    IndexHandler,
    IngestHandler,
    RegisterHandler,
    VerifyHandler,
)

__all__ = [
    "RegisterHandler",
    "VerifyHandler",
    "IngestHandler",
    "IndexHandler",
    "ClassifyHandler",
    "ActivateHandler",
    "GovernHandler",
]
