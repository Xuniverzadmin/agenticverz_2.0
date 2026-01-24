# Tasks module
"""
Task definitions for background processing.

Phase 2A: Wired exports for modules that are imported directly.
"""

# Memory update tasks
# M10 Metrics collection
from .m10_metrics_collector import collect_m10_metrics, run_metrics_collector
from .memory_update import apply_update_rules, apply_update_rules_sync

# Recovery queue tasks
from .recovery_queue_stream import enqueue_stream, get_dead_letter_count, get_stream_info

__all__ = [
    # memory_update
    "apply_update_rules",
    "apply_update_rules_sync",
    # recovery_queue_stream
    "enqueue_stream",
    "get_dead_letter_count",
    "get_stream_info",
    # m10_metrics_collector
    "collect_m10_metrics",
    "run_metrics_collector",
]
