# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (metrics from prometheus)
#   Writes: none (metrics export only)
# Role: Trace metrics collection (Prometheus)
# Callers: trace store
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Trace System
# NOTE: Reclassified L6→L5 (2026-01-24) - Prometheus utilities, not SQL driver
#       Remains in drivers/ per Layer ≠ Directory principle

"""
Prometheus Metrics for AOS Traces API

M8 Deliverable: Comprehensive observability for trace operations.

Metrics:
- aos_trace_request_duration_seconds: Histogram of trace API latencies
- aos_trace_requests_total: Counter of trace requests by operation/status
- aos_trace_parity_status: Gauge for parity check results (1=pass, 0=fail)
- aos_replay_enforcement_total: Counter of replay enforcement outcomes
- aos_idempotency_total: Counter of idempotency check outcomes
"""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Try to import prometheus_client
try:
    from prometheus_client import (
        REGISTRY,
        Counter,
        Gauge,
        Histogram,
        Info,
    )

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

    # Create stub classes for when prometheus_client is not installed
    class StubMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def time(self):
            return contextmanager(lambda: iter([None]))()

    Counter = Histogram = Gauge = Summary = Info = StubMetric
    REGISTRY = None


# Metric definitions
TRACE_LATENCY_HISTOGRAM = (
    Histogram(
        "aos_trace_request_duration_seconds",
        "Duration of trace API requests in seconds",
        labelnames=["operation", "status", "tenant_id"],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )
    if HAS_PROMETHEUS
    else StubMetric()
)

TRACE_REQUESTS_COUNTER = (
    Counter(
        "aos_trace_requests_total",
        "Total number of trace API requests",
        labelnames=["operation", "status", "tenant_id"],
    )
    if HAS_PROMETHEUS
    else StubMetric()
)

TRACE_PARITY_GAUGE = (
    Gauge("aos_trace_parity_status", "Status of parity checks (1=pass, 0=fail)", labelnames=["trace_id", "check_type"])
    if HAS_PROMETHEUS
    else StubMetric()
)

REPLAY_ENFORCEMENT_COUNTER = (
    Counter(
        "aos_replay_enforcement_total",
        "Total replay enforcement actions",
        labelnames=["behavior", "outcome", "tenant_id"],
    )
    if HAS_PROMETHEUS
    else StubMetric()
)

IDEMPOTENCY_COUNTER = (
    Counter("aos_idempotency_total", "Total idempotency check results", labelnames=["result", "tenant_id"])
    if HAS_PROMETHEUS
    else StubMetric()
)

TRACE_STEPS_HISTOGRAM = (
    Histogram(
        "aos_trace_steps_count",
        "Number of steps per trace",
        labelnames=["tenant_id"],
        buckets=[1, 5, 10, 25, 50, 100, 250, 500],
    )
    if HAS_PROMETHEUS
    else StubMetric()
)

TRACE_SIZE_HISTOGRAM = (
    Histogram(
        "aos_trace_size_bytes",
        "Size of traces in bytes",
        labelnames=["tenant_id"],
        buckets=[1024, 10240, 102400, 1048576, 10485760],  # 1KB to 10MB
    )
    if HAS_PROMETHEUS
    else StubMetric()
)

PARITY_FAILURES_COUNTER = (
    Counter("aos_parity_failures_total", "Total parity check failures", labelnames=["failure_type", "tenant_id"])
    if HAS_PROMETHEUS
    else StubMetric()
)

# Trace storage metrics
TRACE_STORAGE_LATENCY = (
    Histogram(
        "aos_trace_storage_duration_seconds",
        "Duration of trace storage operations",
        labelnames=["operation", "backend"],
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    )
    if HAS_PROMETHEUS
    else StubMetric()
)

# Build info
if HAS_PROMETHEUS:
    TRACE_BUILD_INFO = Info("aos_traces_build", "Build information for traces module")
    TRACE_BUILD_INFO.info({"version": "1.1", "schema_version": "1.1", "determinism": "enabled"})


class TracesMetrics:
    """Centralized metrics manager for traces API."""

    def __init__(self):
        self._start_times: dict = {}

    @contextmanager
    def measure_request(self, operation: str, tenant_id: str = "default"):
        """Context manager to measure request duration."""
        start = time.perf_counter()
        status = "success"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.perf_counter() - start
            TRACE_LATENCY_HISTOGRAM.labels(operation=operation, status=status, tenant_id=tenant_id).observe(duration)
            TRACE_REQUESTS_COUNTER.labels(operation=operation, status=status, tenant_id=tenant_id).inc()

    def record_trace_stored(self, trace_id: str, step_count: int, size_bytes: int, tenant_id: str = "default"):
        """Record trace storage metrics."""
        TRACE_STEPS_HISTOGRAM.labels(tenant_id=tenant_id).observe(step_count)
        TRACE_SIZE_HISTOGRAM.labels(tenant_id=tenant_id).observe(size_bytes)

    def record_replay_enforcement(self, behavior: str, outcome: str, tenant_id: str = "default"):
        """Record replay enforcement outcome."""
        REPLAY_ENFORCEMENT_COUNTER.labels(behavior=behavior, outcome=outcome, tenant_id=tenant_id).inc()

    def record_idempotency_check(self, result: str, tenant_id: str = "default"):
        """Record idempotency check result."""
        IDEMPOTENCY_COUNTER.labels(result=result, tenant_id=tenant_id).inc()

    def record_parity_check(self, trace_id: str, check_type: str, passed: bool):
        """Record parity check result."""
        TRACE_PARITY_GAUGE.labels(
            trace_id=trace_id[:16],  # Truncate for cardinality
            check_type=check_type,
        ).set(1 if passed else 0)

        if not passed:
            PARITY_FAILURES_COUNTER.labels(failure_type=check_type, tenant_id="default").inc()

    @contextmanager
    def measure_storage(self, operation: str, backend: str = "postgres"):
        """Context manager to measure storage operation duration."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            TRACE_STORAGE_LATENCY.labels(operation=operation, backend=backend).observe(duration)


# Global instance
_traces_metrics: Optional[TracesMetrics] = None


def get_traces_metrics() -> TracesMetrics:
    """Get or create global traces metrics instance."""
    global _traces_metrics
    if _traces_metrics is None:
        _traces_metrics = TracesMetrics()
    return _traces_metrics


def instrument_trace_request(operation: str):
    """Decorator to instrument trace API endpoints."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to extract tenant_id from kwargs or request
            tenant_id = kwargs.get("tenant_id", "default")

            metrics = get_traces_metrics()
            with metrics.measure_request(operation, tenant_id):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def instrument_replay_check(func: Callable) -> Callable:
    """Decorator to instrument replay enforcement."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        # Record metrics based on result
        metrics = get_traces_metrics()
        behavior = getattr(result, "behavior", "unknown")
        outcome = getattr(result, "outcome", "unknown")
        tenant_id = kwargs.get("tenant_id", "default")

        metrics.record_replay_enforcement(behavior=str(behavior), outcome=str(outcome), tenant_id=tenant_id)

        return result

    return wrapper


def instrument_parity_check(func: Callable) -> Callable:
    """Decorator to instrument parity checks."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # Record metrics based on result
        metrics = get_traces_metrics()
        trace_id = kwargs.get("trace_id", "unknown")
        passed = getattr(result, "passed", False) if result else False

        metrics.record_parity_check(trace_id=trace_id, check_type="cross_language", passed=passed)

        return result

    return wrapper
