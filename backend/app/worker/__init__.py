# NOVA Worker Package
# Worker pool and runner for async run execution
#
# TECH-001: Lazy imports to avoid sqlmodel dependency in lightweight tests
# Heavy imports (pool.py, runner.py) require sqlmodel which breaks test isolation.
# Use lazy getters to defer import until actual usage.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pool import WorkerPool
    from .runner import RunRunner

__all__ = ["WorkerPool", "RunRunner", "get_worker_pool", "get_run_runner"]

# Lazy import cache
_worker_pool_class = None
_run_runner_class = None


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


# For backwards compatibility, provide lazy property-like access
class _LazyModule:
    """Lazy module wrapper for backwards compatibility."""

    @property
    def WorkerPool(self):
        return get_worker_pool()

    @property
    def RunRunner(self):
        return get_run_runner()


# Note: Direct imports like `from app.worker import WorkerPool` will still fail
# Use `from app.worker import get_worker_pool; WorkerPool = get_worker_pool()` instead
# Or import directly: `from app.worker.pool import WorkerPool`
