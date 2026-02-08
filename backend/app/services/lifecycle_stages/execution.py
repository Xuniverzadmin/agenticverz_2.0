# Layer: L4 — Domain Engine (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Compatibility shim for stage execution implementations
# Allowed Imports: hoc_spine canonical execution drivers

"""Compatibility shim.

Canonical execution implementations live at:
  app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution
"""

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution import *  # noqa: F401,F403
