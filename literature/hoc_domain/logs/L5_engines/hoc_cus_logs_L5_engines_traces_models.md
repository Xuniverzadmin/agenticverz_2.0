# hoc_cus_logs_L5_engines_traces_models

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/traces_models.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace data models (dataclasses)

## Intent

**Role:** Trace data models (dataclasses)
**Reference:** PIN-470, Trace System
**Callers:** traces/*

## Purpose

Trace Models for AOS
M6 Deliverable: Run traces with correlation IDs

---

## Functions

### `_normalize_for_determinism(value: Any) -> Any`
- **Async:** No
- **Docstring:** Normalize a value for deterministic hashing.  Handles:
- **Calls:** _normalize_for_determinism, isinstance, items, round

### `compare_traces(original: TraceRecord, replay: TraceRecord) -> ParityResult`
- **Async:** No
- **Docstring:** Compare two traces to verify replay parity.  Checks:
- **Calls:** ParityResult, append, determinism_hash, determinism_signature, dumps, enumerate, join, len, min, zip

## Classes

### `TraceStatus(str, Enum)`
- **Docstring:** Status of a trace step.

### `TraceStep`
- **Docstring:** A single step in an execution trace.
- **Methods:** to_dict, from_dict, determinism_hash
- **Class Variables:** step_index: int, skill_name: str, params: dict[str, Any], status: TraceStatus, outcome_category: str, outcome_code: str | None, outcome_data: dict[str, Any] | None, cost_cents: float, duration_ms: float, retry_count: int, timestamp: datetime

### `TraceSummary`
- **Docstring:** Summary of a trace for listing purposes.
- **Methods:** to_dict
- **Class Variables:** run_id: str, correlation_id: str, tenant_id: str, agent_id: str | None, total_steps: int, success_count: int, failure_count: int, total_cost_cents: float, total_duration_ms: float, started_at: datetime, completed_at: datetime | None, status: str, violation_step_index: int | None, violation_timestamp: datetime | None, violation_policy_id: str | None, violation_reason: str | None

### `TraceRecord`
- **Docstring:** Complete trace record with all steps.
- **Methods:** total_cost_cents, total_duration_ms, success_count, failure_count, to_dict, from_dict, to_summary, determinism_signature
- **Class Variables:** SCHEMA_VERSION: ClassVar[str], run_id: str, correlation_id: str, tenant_id: str, agent_id: str | None, plan: list[dict[str, Any]], steps: list[TraceStep], started_at: datetime, completed_at: datetime | None, status: str, metadata: dict[str, Any], seed: int, frozen_timestamp: str | None, root_hash: str | None

### `ParityResult`
- **Docstring:** Result of comparing two traces for replay parity.
- **Methods:** to_dict
- **Class Variables:** is_parity: bool, original_signature: str, replay_signature: str, divergence_step: int | None, divergence_reason: str | None

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

traces/*

## Export Contract

```yaml
exports:
  functions:
    - name: compare_traces
      signature: "compare_traces(original: TraceRecord, replay: TraceRecord) -> ParityResult"
  classes:
    - name: TraceStatus
      methods: []
    - name: TraceStep
      methods: [to_dict, from_dict, determinism_hash]
    - name: TraceSummary
      methods: [to_dict]
    - name: TraceRecord
      methods: [total_cost_cents, total_duration_ms, success_count, failure_count, to_dict, from_dict, to_summary, determinism_signature]
    - name: ParityResult
      methods: [to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
