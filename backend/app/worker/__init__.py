# NOVA Worker Package
# Worker pool and runner for async run execution
#
# TECH-001: Lazy imports to avoid sqlmodel dependency in lightweight tests
# Heavy imports (pool.py, runner.py) require sqlmodel which breaks test isolation.
# Use lazy getters to defer import until actual usage.
#
# Reference: GAP-155 (Job Queue Worker), GAP-162-164 (Lifecycle Worker)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pool import WorkerPool
    from .runner import RunRunner
    from .job_queue_worker import JobQueueWorker
    from .lifecycle_worker import LifecycleWorker

__all__ = [
    # Core worker
    "WorkerPool",
    "RunRunner",
    "get_worker_pool",
    "get_run_runner",
    # GAP-155: Job Queue Worker
    "JobQueueWorker",
    "get_job_queue_worker",
    # GAP-162-164: Lifecycle Worker
    "LifecycleWorker",
    "get_lifecycle_worker",
    "get_lifecycle_progress_manager",
    "get_lifecycle_recovery_manager",
]

# Lazy import cache
_worker_pool_class = None
_run_runner_class = None
_job_queue_worker = None
_lifecycle_worker = None


def get_worker_pool():
    """Lazy getter for WorkerPool class to avoid early sqlmodel import."""
    global _worker_pool_class
    if _worker_pool_class is None:
        from .pool import WorkerPool

        _worker_pool_class = WorkerPool
    return _worker_pool_class


def get_run_runner():
    """Lazy getter for RunRunner class to avoid early sqlmodel import."""
    global _run_runner_class
    if _run_runner_class is None:
        from .runner import RunRunner

        _run_runner_class = RunRunner
    return _run_runner_class


def get_job_queue_worker():
    """Lazy getter for JobQueueWorker singleton."""
    global _job_queue_worker
    if _job_queue_worker is None:
        from .job_queue_worker import get_job_queue_worker as _get_jqw
        _job_queue_worker = _get_jqw()
    return _job_queue_worker


def get_lifecycle_worker():
    """Lazy getter for LifecycleWorker singleton."""
    global _lifecycle_worker
    if _lifecycle_worker is None:
        from .lifecycle_worker import get_lifecycle_worker as _get_lw
        _lifecycle_worker = _get_lw()
    return _lifecycle_worker


def get_lifecycle_progress_manager():
    """Lazy getter for LifecycleProgressManager singleton."""
    from .lifecycle_worker import get_lifecycle_progress_manager as _get_lpm
    return _get_lpm()


def get_lifecycle_recovery_manager():
    """Lazy getter for LifecycleRecoveryManager singleton."""
    from .lifecycle_worker import get_lifecycle_recovery_manager as _get_lrm
    return _get_lrm()


# For backwards compatibility, provide lazy property-like access
class _LazyModule:
    """Lazy module wrapper for backwards compatibility."""

    @property
    def WorkerPool(self):
        return get_worker_pool()

    @property
    def RunRunner(self):
        return get_run_runner()

    @property
    def JobQueueWorker(self):
        return get_job_queue_worker()

    @property
    def LifecycleWorker(self):
        return get_lifecycle_worker()


# Note: Direct imports like `from app.worker import WorkerPool` will still fail
# Use `from app.worker import get_worker_pool; WorkerPool = get_worker_pool()` instead
# Or import directly: `from app.worker.pool import WorkerPool`
