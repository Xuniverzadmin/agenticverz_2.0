# hoc_cus_analytics_L5_engines_pattern_detection

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/pattern_detection.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Pattern detection (PB-S3) - observe → feedback → no mutation (System Truth)

## Intent

**Role:** Pattern detection (PB-S3) - observe → feedback → no mutation (System Truth)
**Reference:** PIN-470, PIN-240
**Callers:** None (DORMANT BY DESIGN)

## Purpose

Pattern Detection Service (PB-S3)

---

## Functions

### `compute_error_signature(error: str) -> str`
- **Async:** No
- **Docstring:** Compute a stable signature for an error message.  Strips variable parts (IDs, timestamps) to group similar errors.
- **Calls:** encode, hexdigest, lower, sha256, strip, sub

### `async detect_failure_patterns(driver: PatternDetectionDriver, tenant_id: Optional[UUID], threshold: int, window_hours: int) -> list[dict]`
- **Async:** Yes
- **Docstring:** Detect repeated failure patterns.  PB-S3: This function READS execution data only. No modifications.
- **Calls:** append, compute_error_signature, fetch_failed_runs, info, items, len, str, timedelta, utc_now

### `async detect_cost_spikes(driver: PatternDetectionDriver, tenant_id: Optional[UUID], spike_threshold_percent: float, min_runs: int) -> list[dict]`
- **Async:** Yes
- **Docstring:** Detect abnormal cost increases.  PB-S3: This function READS cost data only. No modifications.
- **Calls:** append, fetch_completed_runs_with_costs, info, items, len, round, str, sum

### `async emit_feedback(driver: PatternDetectionDriver, feedback: PatternFeedbackCreate) -> dict`
- **Async:** Yes
- **Docstring:** Emit a feedback record.  PB-S3: This creates a NEW record in pattern_feedback.
- **Calls:** UUID, info, insert_feedback, isinstance, len, str, utc_now

### `async run_pattern_detection(tenant_id: Optional[UUID]) -> dict`
- **Async:** Yes
- **Docstring:** Run full pattern detection cycle.  PB-S3: Detects patterns and emits feedback. No execution modifications.
- **Calls:** PatternFeedbackCreate, append, detect_cost_spikes, detect_failure_patterns, emit_feedback, error, get_async_session, get_pattern_detection_driver, str

### `async get_feedback_summary(tenant_id: Optional[UUID], acknowledged: Optional[bool], limit: int) -> dict`
- **Async:** Yes
- **Docstring:** Get feedback summary for ops visibility.  PB-S3: Read-only query of feedback table.
- **Calls:** fetch_feedback_records, get, get_async_session, get_pattern_detection_driver, isoformat, len, str

## Attributes

- `logger` (line 64)
- `FAILURE_PATTERN_THRESHOLD` (line 67)
- `FAILURE_PATTERN_WINDOW_HOURS` (line 68)
- `COST_SPIKE_THRESHOLD_PERCENT` (line 69)
- `COST_SPIKE_MIN_RUNS` (line 70)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.analytics.L6_drivers.pattern_detection_driver` |
| L7 Model | `app.models.feedback` |
| External | `app.db`, `app.hoc.cus.hoc_spine.services.time` |

## Callers

None (DORMANT BY DESIGN)

## Export Contract

```yaml
exports:
  functions:
    - name: compute_error_signature
      signature: "compute_error_signature(error: str) -> str"
    - name: detect_failure_patterns
      signature: "async detect_failure_patterns(driver: PatternDetectionDriver, tenant_id: Optional[UUID], threshold: int, window_hours: int) -> list[dict]"
    - name: detect_cost_spikes
      signature: "async detect_cost_spikes(driver: PatternDetectionDriver, tenant_id: Optional[UUID], spike_threshold_percent: float, min_runs: int) -> list[dict]"
    - name: emit_feedback
      signature: "async emit_feedback(driver: PatternDetectionDriver, feedback: PatternFeedbackCreate) -> dict"
    - name: run_pattern_detection
      signature: "async run_pattern_detection(tenant_id: Optional[UUID]) -> dict"
    - name: get_feedback_summary
      signature: "async get_feedback_summary(tenant_id: Optional[UUID], acknowledged: Optional[bool], limit: int) -> dict"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
