# hoc_cus_controls_L5_engines_threshold_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/threshold_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Threshold resolution and evaluation logic (decision engine)

## Intent

**Role:** Threshold resolution and evaluation logic (decision engine)
**Reference:** PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** L3 Adapters, API routes

## Purpose

Threshold Decision Engine (L5)

---

## Functions

### `create_threshold_signal_record(tenant_id: str, run_id: str, state: str, signal: ThresholdSignal, params_used: dict) -> ThresholdSignalRecord`
- **Async:** No
- **Docstring:** Create a threshold signal record for activity domain.  This creates a record that surfaces in:
- **Calls:** ThresholdSignalRecord, info, now

### `collect_signals_from_evaluation(evaluation: ThresholdEvaluationResult, tenant_id: str, state: str) -> list[ThresholdSignalRecord]`
- **Async:** No
- **Docstring:** Collect all signals from an evaluation result into records.  Args:
- **Calls:** append, create_threshold_signal_record

## Classes

### `ThresholdParams(BaseModel)`
- **Docstring:** Validated threshold parameters for LLM run governance.
- **Methods:** coerce_decimal_to_float
- **Class Variables:** max_execution_time_ms: int, max_tokens: int, max_cost_usd: float, failure_signal: bool

### `ThresholdParamsUpdate(BaseModel)`
- **Docstring:** Partial update for threshold params.
- **Class Variables:** max_execution_time_ms: Optional[int], max_tokens: Optional[int], max_cost_usd: Optional[float], failure_signal: Optional[bool]

### ~~`ThresholdSignal(str, Enum)`~~ — MOVED (PIN-507 Law 1, 2026-02-01)
- **Canonical home:** `controls/L5_schemas/threshold_signals.py`
- **Re-exported here** for backward compatibility (tombstone)

### ~~`ThresholdEvaluationResult`~~ — MOVED (PIN-507 Law 1, 2026-02-01)
- **Canonical home:** `controls/L5_schemas/threshold_signals.py`
- **Re-exported here** for backward compatibility (tombstone)

### `ThresholdDriverProtocol(Protocol)`
- **Docstring:** Protocol defining the interface for threshold drivers.
- **Methods:** get_active_threshold_limits

### `ThresholdDriverSyncProtocol(Protocol)`
- **Docstring:** Protocol defining the interface for sync threshold drivers.
- **Methods:** get_active_threshold_limits

### `LLMRunThresholdResolver`
- **Docstring:** Resolves effective threshold params for an LLM run
- **Methods:** __init__, resolve

### `LLMRunEvaluator`
- **Docstring:** Evaluates LLM runs against threshold params.
- **Methods:** __init__, evaluate_live_run, evaluate_completed_run

### `LLMRunThresholdResolverSync`
- **Docstring:** Sync version of LLMRunThresholdResolver for worker context.
- **Methods:** __init__, resolve

### `LLMRunEvaluatorSync`
- **Docstring:** Sync version of LLMRunEvaluator for worker context.
- **Methods:** __init__, evaluate_completed_run

### `ThresholdSignalRecord`
- **Docstring:** Record of a threshold signal for activity domain.
- **Class Variables:** tenant_id: str, run_id: str, state: str, signal: ThresholdSignal, params_used: dict, emitted_at: datetime

## Attributes

- `logger` (line 65)
- `DEFAULT_LLM_RUN_PARAMS` (line 72)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.controls.L6_drivers.threshold_driver` |
| External | `pydantic` |

## Callers

L3 Adapters, API routes

## Export Contract

```yaml
exports:
  functions:
    - name: create_threshold_signal_record
      signature: "create_threshold_signal_record(tenant_id: str, run_id: str, state: str, signal: ThresholdSignal, params_used: dict) -> ThresholdSignalRecord"
    - name: collect_signals_from_evaluation
      signature: "collect_signals_from_evaluation(evaluation: ThresholdEvaluationResult, tenant_id: str, state: str) -> list[ThresholdSignalRecord]"
  classes:
    - name: ThresholdParams
      methods: [coerce_decimal_to_float]
    - name: ThresholdParamsUpdate
      methods: []
    - name: ThresholdSignal
      methods: []
    - name: ThresholdEvaluationResult
      methods: []
    - name: ThresholdDriverProtocol
      methods: [get_active_threshold_limits]
    - name: ThresholdDriverSyncProtocol
      methods: [get_active_threshold_limits]
    - name: LLMRunThresholdResolver
      methods: [resolve]
    - name: LLMRunEvaluator
      methods: [evaluate_live_run, evaluate_completed_run]
    - name: LLMRunThresholdResolverSync
      methods: [resolve]
    - name: LLMRunEvaluatorSync
      methods: [evaluate_completed_run]
    - name: ThresholdSignalRecord
      methods: []
```

## PIN-507 Law 1 Amendment (2026-02-01)

`ThresholdSignal` and `ThresholdEvaluationResult` extracted to `controls/L5_schemas/threshold_signals.py`. This file retains tombstone re-exports for backward compatibility. Canonical import: `app.hoc.cus.controls.L5_schemas.threshold_signals`. Unused `from enum import Enum` removed.

## Evaluation Notes

- **Disposition:** KEEP
- **Rationale:** Core L5 engine for threshold decisions. Signal types moved to L5_schemas per PIN-507 Law 1.
