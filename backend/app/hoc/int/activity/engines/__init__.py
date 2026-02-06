# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: Activity engines package (internal audience)

"""
Activity engines package.

Stale re-exports removed — m10_metrics_collector, memory_update, and recovery_queue_stream
live in other packages (app/tasks/, app/hoc/int/platform/engines/, etc.).
No consumers import from app.hoc.int.activity.engines (verified 2026-02-06).
"""

__all__: list[str] = []
