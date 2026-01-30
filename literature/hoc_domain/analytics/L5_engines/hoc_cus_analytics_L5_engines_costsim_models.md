# hoc_cus_analytics_L5_engines_costsim_models

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/costsim_models.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 data models (simulation status, results)

## Intent

**Role:** CostSim V2 data models (simulation status, results)
**Reference:** PIN-470
**Callers:** sandbox, canary, divergence engines

## Purpose

Data models for CostSim V2 sandbox evaluation.

---

## Classes

### `V2SimulationStatus(str, Enum)`
- **Docstring:** V2 simulation result status.

### `ComparisonVerdict(str, Enum)`
- **Docstring:** Verdict from V1 vs V2 comparison.

### `V2SimulationResult`
- **Docstring:** Result from CostSim V2 simulation.
- **Methods:** to_dict, compute_output_hash
- **Class Variables:** feasible: bool, status: V2SimulationStatus, estimated_cost_cents: int, estimated_duration_ms: int, budget_remaining_cents: int, confidence_score: float, model_version: str, step_estimates: List[Dict[str, Any]], risks: List[Dict[str, Any]], warnings: List[str], metadata: Dict[str, Any], runtime_ms: int

### `ComparisonResult`
- **Docstring:** Result of comparing V2 vs V1 simulation.
- **Methods:** to_dict
- **Class Variables:** verdict: ComparisonVerdict, v1_cost_cents: int, v2_cost_cents: int, cost_delta_cents: int, cost_delta_pct: float, v1_duration_ms: int, v2_duration_ms: int, duration_delta_ms: int, v1_feasible: bool, v2_feasible: bool, feasibility_match: bool, drift_score: float, details: Dict[str, Any]

### `DiffResult`
- **Docstring:** Detailed diff between two simulation results.
- **Methods:** to_dict
- **Class Variables:** input_hash: str, v1_output_hash: str, v2_output_hash: str, cost_diff: int, duration_diff: int, step_diffs: List[Dict[str, Any]], is_match: bool, diff_summary: str, timestamp: datetime

### `CanaryReport`
- **Docstring:** Report from daily canary run.
- **Methods:** to_dict
- **Class Variables:** run_id: str, timestamp: datetime, status: str, total_samples: int, matching_samples: int, minor_drift_samples: int, major_drift_samples: int, median_cost_diff: float, p90_cost_diff: float, kl_divergence: float, outlier_count: int, passed: bool, failure_reasons: List[str], artifact_paths: List[str], golden_comparison: Optional[Dict[str, Any]]

### `DivergenceReport`
- **Docstring:** Cost divergence report between V1 and V2.
- **Methods:** to_dict
- **Class Variables:** start_date: datetime, end_date: datetime, version: str, sample_count: int, delta_p50: float, delta_p90: float, kl_divergence: float, outlier_count: int, fail_ratio: float, matching_rate: float, detailed_samples: List[Dict[str, Any]]

### `ValidationResult`
- **Docstring:** Result of validating V2 against a reference dataset.
- **Methods:** to_dict
- **Class Variables:** dataset_id: str, dataset_name: str, sample_count: int, mean_error: float, median_error: float, std_deviation: float, outlier_pct: float, drift_score: float, verdict: str, details: Dict[str, Any], timestamp: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

sandbox, canary, divergence engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: V2SimulationStatus
      methods: []
    - name: ComparisonVerdict
      methods: []
    - name: V2SimulationResult
      methods: [to_dict, compute_output_hash]
    - name: ComparisonResult
      methods: [to_dict]
    - name: DiffResult
      methods: [to_dict]
    - name: CanaryReport
      methods: [to_dict]
    - name: DivergenceReport
      methods: [to_dict]
    - name: ValidationResult
      methods: [to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
