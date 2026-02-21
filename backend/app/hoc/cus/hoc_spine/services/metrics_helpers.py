# capability_id: CAP-012
# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none (Prometheus metrics are in-memory)
# Role: Metrics helper functions (Prometheus)
# Callers: all modules
# Allowed Imports: L6, L7 (stdlib, prometheus_client)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-470, Observability
# NOTE: Reclassified L6→L5 (2026-01-24) - Prometheus utilities, not SQL driver
#       Remains in drivers/ per Layer ≠ Directory principle

"""
Prometheus Metrics Helpers - Idempotent Registration

This module provides helper functions for creating Prometheus metrics
that are safe to use in modules that may be reimported during testing.

Usage:
    from app.utils.metrics_helpers import get_or_create_counter, get_or_create_gauge

    MY_COUNTER = get_or_create_counter(
        "mymodule_operations_total",
        "Total operations",
        ["status", "type"]
    )

Prevention: PIN-120 / PREV-1 - Prevents duplicate timeseries errors in tests.
"""

from typing import List, Optional

from prometheus_client import REGISTRY, Counter, Gauge, Histogram


def _find_existing_metric(name: str):
    """
    Find an existing metric in the registry by name.

    Prometheus registers metrics under multiple keys (base name, _total, _created).
    The collector's _name attribute contains the base name.

    Args:
        name: The base metric name (without _total suffix for counters)

    Returns:
        The existing metric collector if found, None otherwise
    """
    # Check direct registry lookup
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]

    # Check collector's _name attribute (handles suffixed names)
    for collector in list(REGISTRY._names_to_collectors.values()):
        if hasattr(collector, "_name") and collector._name == name:
            return collector

    return None


def get_or_create_counter(name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Counter:
    """
    Get existing counter or create new one - idempotent.

    Args:
        name: Metric name (should follow naming convention: {module}_{metric}_total)
        documentation: Help text for the metric
        labelnames: List of label names

    Returns:
        Counter metric (existing or new)

    Example:
        MY_COUNTER = get_or_create_counter(
            "drift_detector_comparisons_total",
            "Total drift comparisons performed",
            ["status"]
        )
    """
    existing = _find_existing_metric(name)
    if existing is not None:
        return existing
    return Counter(name, documentation, labelnames or [])


def get_or_create_gauge(name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Gauge:
    """
    Get existing gauge or create new one - idempotent.

    Args:
        name: Metric name (should follow naming convention: {module}_{metric})
        documentation: Help text for the metric
        labelnames: List of label names

    Returns:
        Gauge metric (existing or new)

    Example:
        MY_GAUGE = get_or_create_gauge(
            "policy_cache_size",
            "Current policy cache size",
            ["tenant_id"]
        )
    """
    existing = _find_existing_metric(name)
    if existing is not None:
        return existing
    return Gauge(name, documentation, labelnames or [])


def get_or_create_histogram(
    name: str, documentation: str, labelnames: Optional[List[str]] = None, buckets: Optional[List[float]] = None
) -> Histogram:
    """
    Get existing histogram or create new one - idempotent.

    Args:
        name: Metric name (should follow naming convention: {module}_{metric}_seconds)
        documentation: Help text for the metric
        labelnames: List of label names
        buckets: Histogram bucket boundaries

    Returns:
        Histogram metric (existing or new)

    Example:
        MY_HISTOGRAM = get_or_create_histogram(
            "outbox_processing_seconds",
            "Time to process outbox events",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
    """
    existing = _find_existing_metric(name)
    if existing is not None:
        return existing

    kwargs = {"labelnames": labelnames or []}
    if buckets:
        kwargs["buckets"] = buckets

    return Histogram(name, documentation, **kwargs)


# =============================================================================
# Naming Convention Validation
# =============================================================================

VALID_SUFFIXES = {"_total", "_seconds", "_bytes", "_count", "_ratio", "_info"}


def validate_metric_name(name: str) -> bool:
    """
    Validate metric name follows conventions.

    Convention (PIN-120 / PREV-2):
    - Counter: {module}_{metric}_total
    - Histogram: {module}_{metric}_seconds
    - Gauge: {module}_{metric} (no required suffix)
    - Info: {module}_{metric}_info

    Args:
        name: Metric name to validate

    Returns:
        True if valid, False otherwise
    """
    # Must have at least one underscore (module prefix)
    if "_" not in name:
        return False

    # Check for standard suffix (recommended but not required for gauges)
    has_standard_suffix = any(name.endswith(suffix) for suffix in VALID_SUFFIXES)

    # At minimum, should have module prefix
    parts = name.split("_")
    return len(parts) >= 2 and len(parts[0]) > 0


# =============================================================================
# Test Isolation Helpers
# =============================================================================


def reset_metrics_registry():
    """
    Reset the Prometheus registry for test isolation.

    WARNING: Only use in test fixtures, never in production code.
    """
    # Get all collector names
    collectors_to_remove = []
    for name, collector in list(REGISTRY._names_to_collectors.items()):
        # Only remove our custom metrics, not default Python/process metrics
        if not name.startswith(("python_", "process_", "gc_")):
            collectors_to_remove.append(collector)

    # Unregister collectors
    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass  # Already unregistered
