# hoc_cus_analytics_L5_engines_divergence

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/divergence.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 divergence reporting (delta metrics, KL divergence)

## Intent

**Role:** CostSim V2 divergence reporting (delta metrics, KL divergence)
**Reference:** PIN-470
**Callers:** canary runner, sandbox API

## Purpose

Cost divergence reporting between V1 and V2.

---

## Functions

### `async generate_divergence_report(start_date: Optional[datetime], end_date: Optional[datetime], tenant_id: Optional[str]) -> DivergenceReport`
- **Async:** Yes
- **Docstring:** Convenience function to generate a divergence report.  Args:
- **Calls:** DivergenceAnalyzer, generate_report

## Classes

### `DivergenceSample`
- **Docstring:** A single sample for divergence analysis.
- **Class Variables:** timestamp: datetime, input_hash: str, v1_cost_cents: int, v2_cost_cents: int, cost_delta_cents: int, drift_score: float, verdict: str, tenant_id: Optional[str]

### `DivergenceAnalyzer`
- **Docstring:** Analyzer for V1 vs V2 cost divergence.
- **Methods:** __init__, generate_report, _load_samples, _parse_provenance_log, _calculate_metrics, _calculate_kl_divergence

## Attributes

- `logger` (line 48)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.config`, `app.costsim.models`, `app.costsim.provenance` |

## Callers

canary runner, sandbox API

## Export Contract

```yaml
exports:
  functions:
    - name: generate_divergence_report
      signature: "async generate_divergence_report(start_date: Optional[datetime], end_date: Optional[datetime], tenant_id: Optional[str]) -> DivergenceReport"
  classes:
    - name: DivergenceSample
      methods: []
    - name: DivergenceAnalyzer
      methods: [generate_report]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
