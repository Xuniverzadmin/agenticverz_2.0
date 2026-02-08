# Layer: L4 — Domain Engine (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for knowledge lifecycle stage handlers
# Callers: legacy imports, tests
# Allowed Imports: hoc_spine canonical stage surface

"""Compatibility shim.

Canonical implementation lives at:
  app.hoc.cus.hoc_spine.orchestrator.lifecycle.stages

This package exists only to preserve import paths while callers migrate.
"""

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.stages import *  # noqa: F401,F403
