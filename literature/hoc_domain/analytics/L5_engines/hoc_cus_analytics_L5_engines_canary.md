# hoc_cus_analytics_L5_engines_canary

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/canary.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 canary runner (daily validation, drift detection)

## Intent

**Role:** CostSim V2 canary runner (daily validation, drift detection)
**Reference:** PIN-470
**Callers:** systemd timer, cron

## Purpose

Daily canary runner for CostSim V2 validation.

---

## Functions

### `async run_canary(sample_count: int, drift_threshold: float) -> CanaryReport`
- **Async:** Yes
- **Docstring:** Convenience function to run canary.  Args:
- **Calls:** CanaryRunConfig, CanaryRunner, run

## Classes

### `CanarySample`
- **Docstring:** A single canary test sample.
- **Class Variables:** id: str, plan: List[Dict[str, Any]], budget_cents: int, expected_cost_cents: Optional[int], expected_feasible: Optional[bool]

### `CanaryRunConfig`
- **Docstring:** Configuration for a canary run.
- **Class Variables:** sample_count: int, max_runtime_seconds: int, parallel_workers: int, drift_threshold: float, outlier_threshold: float, outlier_max_pct: float, golden_dir: Optional[str], save_artifacts: bool, artifacts_dir: Optional[str], require_leader_lock: bool, leader_lock_timeout: float, use_async_circuit_breaker: bool

### `CanaryRunner`
- **Docstring:** Daily canary runner for V2 validation.
- **Methods:** __init__, run, _run_internal, _load_samples, _generate_synthetic_samples, _run_single, _calculate_metrics, _approximate_kl_divergence, _compare_with_golden, _evaluate_results, _save_artifacts

## Attributes

- `logger` (line 71)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.circuit_breaker`, `app.costsim.circuit_breaker_async`, `app.costsim.config`, `app.costsim.leader`, `app.costsim.models`, `app.costsim.provenance`, `app.costsim.v2_adapter`, `app.worker.simulate` |

## Callers

systemd timer, cron

## Export Contract

```yaml
exports:
  functions:
    - name: run_canary
      signature: "async run_canary(sample_count: int, drift_threshold: float) -> CanaryReport"
  classes:
    - name: CanarySample
      methods: []
    - name: CanaryRunConfig
      methods: []
    - name: CanaryRunner
      methods: [run]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
