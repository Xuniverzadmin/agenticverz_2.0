# hoc_cus_activity_L5_engines_cost_analysis_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/cost_analysis_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost analysis engine for activity signals

## Intent

**Role:** Cost analysis engine for activity signals
**Reference:** PIN-470, Activity Domain
**Callers:** activity_facade.py

## Purpose

Cost analysis engine for detecting cost anomalies.

---

## Classes

### `CostAnomaly`
- **Docstring:** A detected cost anomaly.
- **Class Variables:** anomaly_id: str, anomaly_type: str, dimension: str, description: str, severity: float, cost_delta_usd: float, cost_delta_pct: float, baseline_cost_usd: float, actual_cost_usd: float, detected_at: datetime, source_run_ids: list[str]

### `CostAnalysisResult`
- **Docstring:** Result of cost analysis.
- **Class Variables:** anomalies: list[CostAnomaly], total_cost_analyzed_usd: float, baseline_period_days: int, generated_at: datetime

### `CostAnalysisService`
- **Docstring:** Service for analyzing cost patterns and detecting anomalies.
- **Methods:** __init__, analyze_costs, get_cost_breakdown

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.services.time` |

## Callers

activity_facade.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CostAnomaly
      methods: []
    - name: CostAnalysisResult
      methods: []
    - name: CostAnalysisService
      methods: [analyze_costs, get_cost_breakdown]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
