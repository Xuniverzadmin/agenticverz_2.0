# hoc_cus_activity_L5_engines_activity_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/activity_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Activity Facade - Centralized access to activity domain operations

## Intent

**Role:** Activity Facade - Centralized access to activity domain operations
**Reference:** PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** app.api.activity (L2)

## Purpose

Activity Facade (L5)

---

## Functions

### `get_activity_facade() -> ActivityFacade`
- **Async:** No
- **Docstring:** Get the singleton ActivityFacade instance.
- **Calls:** ActivityFacade

## Classes

### `PolicyContextResult`
- **Docstring:** Policy context for a run.
- **Class Variables:** policy_id: str, policy_name: str, policy_scope: str, limit_type: str | None, threshold_value: float | None, threshold_unit: str | None, threshold_source: str, evaluation_outcome: str, actual_value: float | None, risk_type: str | None, proximity_pct: float | None, facade_ref: str | None, threshold_ref: str | None, violation_ref: str | None

### `RunSummaryResult`
- **Docstring:** Run summary for list view.
- **Class Variables:** run_id: str, tenant_id: str | None, project_id: str | None, is_synthetic: bool, source: str, provider_type: str, state: str, status: str, started_at: datetime | None, last_seen_at: datetime | None, completed_at: datetime | None, duration_ms: float | None, risk_level: str, latency_bucket: str, evidence_health: str, integrity_status: str, incident_count: int, policy_draft_count: int, policy_violation: bool, input_tokens: int | None, output_tokens: int | None, estimated_cost_usd: float | None

### `RunSummaryV2Result(RunSummaryResult)`
- **Docstring:** Run summary with policy context (V2).
- **Class Variables:** policy_context: PolicyContextResult | None

### `RunListResult`
- **Docstring:** Result of listing runs.
- **Class Variables:** items: list[RunSummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `RunsResult`
- **Docstring:** Unified result for getting runs (V2).
- **Class Variables:** state: str, items: list[RunSummaryV2Result], total: int, has_more: bool, generated_at: datetime

### `RunDetailResult(RunSummaryResult)`
- **Docstring:** Run detail (O3) - extends summary with additional fields.
- **Class Variables:** goal: str | None, error_message: str | None

### `RunEvidenceResult`
- **Docstring:** Run evidence context (O4).
- **Class Variables:** run_id: str, incidents_caused: list[dict[str, Any]], policies_triggered: list[dict[str, Any]], decisions_made: list[dict[str, Any]], traces_linked: list[dict[str, Any]]

### `RunProofResult`
- **Docstring:** Run integrity proof (O5).
- **Class Variables:** run_id: str, integrity: dict[str, Any], aos_traces: list[dict[str, Any]], aos_trace_steps: list[dict[str, Any]], raw_logs: list[dict[str, Any]]

### `StatusCount`
- **Docstring:** Status count item.
- **Class Variables:** status: str, count: int

### `StatusSummaryResult`
- **Docstring:** Summary by status.
- **Class Variables:** statuses: list[StatusCount], total: int

### `SignalProjectionResult`
- **Docstring:** A signal projection.
- **Class Variables:** signal_id: str, signal_fingerprint: str, run_id: str, signal_type: str, severity: str, summary: str, policy_context: PolicyContextResult, created_at: datetime, feedback: SignalFeedbackStatus | None

### `SignalsResult`
- **Docstring:** Result of getting signals (V2).
- **Class Variables:** signals: list[SignalProjectionResult], total: int, generated_at: datetime

### `MetricsResult`
- **Docstring:** Activity metrics (V2).
- **Class Variables:** at_risk_count: int, violated_count: int, near_threshold_count: int, total_at_risk: int, live_count: int, completed_count: int, evidence_flowing_count: int, evidence_degraded_count: int, evidence_missing_count: int, cost_risk_count: int, time_risk_count: int, token_risk_count: int, rate_risk_count: int, generated_at: datetime

### `ThresholdSignalResult`
- **Docstring:** A threshold proximity signal.
- **Class Variables:** run_id: str, limit_type: str, proximity_pct: float, evaluation_outcome: str, policy_context: PolicyContextResult

### `ThresholdSignalsResult`
- **Docstring:** Result of getting threshold signals (V2).
- **Class Variables:** signals: list[ThresholdSignalResult], total: int, risk_type_filter: str | None, generated_at: datetime

### `RiskSignalsResult`
- **Docstring:** Risk signal aggregates.
- **Class Variables:** at_risk_count: int, violated_count: int, near_threshold_count: int, total_at_risk: int, by_risk_type: dict[str, int]

### `ActivityFacade`
- **Docstring:** Unified facade for Activity domain operations.
- **Methods:** __init__, _get_driver, _get_pattern_service, _get_cost_service, _get_attention_service, _get_feedback_service, get_runs, get_run_detail, get_run_evidence, get_run_proof, get_status_summary, get_live_runs, get_completed_runs, _get_runs_with_policy_context, get_signals, _compute_signal_type, _compute_severity, _compute_signal_summary, get_metrics, get_threshold_signals, get_risk_signals, get_patterns, get_cost_analysis, get_attention_queue, acknowledge_signal, suppress_signal

## Attributes

- `logger` (line 81)
- `LiveRunsResult` (line 173)
- `CompletedRunsResult` (line 174)
- `_facade_instance: ActivityFacade | None` (line 1379)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.activity.L5_engines.activity_enums`, `app.hoc.cus.activity.L5_engines.attention_ranking_engine`, `app.hoc.cus.activity.L5_engines.cost_analysis_engine`, `app.hoc.cus.activity.L5_engines.pattern_detection_engine`, `app.hoc.cus.activity.L5_engines.signal_feedback_engine`, `app.hoc.cus.activity.L5_engines.signal_identity` |
| L6 Driver | `app.hoc.cus.activity.L6_drivers.activity_read_driver` |
| External | `__future__`, `sqlalchemy.ext.asyncio` |

## Callers

app.api.activity (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_activity_facade
      signature: "get_activity_facade() -> ActivityFacade"
  classes:
    - name: PolicyContextResult
      methods: []
    - name: RunSummaryResult
      methods: []
    - name: RunSummaryV2Result
      methods: []
    - name: RunListResult
      methods: []
    - name: RunsResult
      methods: []
    - name: RunDetailResult
      methods: []
    - name: RunEvidenceResult
      methods: []
    - name: RunProofResult
      methods: []
    - name: StatusCount
      methods: []
    - name: StatusSummaryResult
      methods: []
    - name: SignalProjectionResult
      methods: []
    - name: SignalsResult
      methods: []
    - name: MetricsResult
      methods: []
    - name: ThresholdSignalResult
      methods: []
    - name: ThresholdSignalsResult
      methods: []
    - name: RiskSignalsResult
      methods: []
    - name: ActivityFacade
      methods: [get_runs, get_run_detail, get_run_evidence, get_run_proof, get_status_summary, get_live_runs, get_completed_runs, get_signals, get_metrics, get_threshold_signals, get_risk_signals, get_patterns, get_cost_analysis, get_attention_queue, acknowledge_signal, suppress_signal]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
