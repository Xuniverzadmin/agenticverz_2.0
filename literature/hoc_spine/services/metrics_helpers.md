# metrics_helpers.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/metrics_helpers.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            metrics_helpers.py
Lives in:        services/
Role:            Services
Inbound:         all modules
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Prometheus Metrics Helpers - Idempotent Registration
Violations:      none
```

## Purpose

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

## Import Analysis

**External:**
- `prometheus_client`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `_find_existing_metric(name: str)`

Find an existing metric in the registry by name.

Prometheus registers metrics under multiple keys (base name, _total, _created).
The collector's _name attribute contains the base name.

Args:
    name: The base metric name (without _total suffix for counters)

Returns:
    The existing metric collector if found, None otherwise

### `get_or_create_counter(name: str, documentation: str, labelnames: Optional[List[str]]) -> Counter`

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

### `get_or_create_gauge(name: str, documentation: str, labelnames: Optional[List[str]]) -> Gauge`

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

### `get_or_create_histogram(name: str, documentation: str, labelnames: Optional[List[str]], buckets: Optional[List[float]]) -> Histogram`

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

### `validate_metric_name(name: str) -> bool`

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

### `reset_metrics_registry()`

Reset the Prometheus registry for test isolation.

WARNING: Only use in test fixtures, never in production code.

## Domain Usage

**Callers:** all modules

## Export Contract

```yaml
exports:
  functions:
    - name: _find_existing_metric
      signature: "_find_existing_metric(name: str)"
      consumers: ["orchestrator"]
    - name: get_or_create_counter
      signature: "get_or_create_counter(name: str, documentation: str, labelnames: Optional[List[str]]) -> Counter"
      consumers: ["orchestrator"]
    - name: get_or_create_gauge
      signature: "get_or_create_gauge(name: str, documentation: str, labelnames: Optional[List[str]]) -> Gauge"
      consumers: ["orchestrator"]
    - name: get_or_create_histogram
      signature: "get_or_create_histogram(name: str, documentation: str, labelnames: Optional[List[str]], buckets: Optional[List[float]]) -> Histogram"
      consumers: ["orchestrator"]
    - name: validate_metric_name
      signature: "validate_metric_name(name: str) -> bool"
      consumers: ["orchestrator"]
    - name: reset_metrics_registry
      signature: "reset_metrics_registry()"
      consumers: ["orchestrator"]
  classes: []
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['prometheus_client']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

