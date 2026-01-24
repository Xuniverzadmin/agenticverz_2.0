# HOC Analytics Domain Analysis v1

**Date:** 2026-01-22
**Domain:** `app/hoc/cus/analytics/`
**Status:** Analysis Complete

---

## Directory Structure

```
app/hoc/cus/analytics/
├── __init__.py                           (12 LOC)
├── facades/
│   ├── __init__.py                       (11 LOC)
│   ├── analytics_facade.py               (829 LOC)
│   └── detection_facade.py               (552 LOC)
├── engines/
│   ├── __init__.py                       (11 LOC)
│   ├── cost_model_engine.py              (450 LOC)
│   ├── cost_anomaly_detector.py          (1184 LOC)
│   ├── cost_write_service.py             (225 LOC)
│   ├── pattern_detection.py              (394 LOC)
│   └── prediction.py                     (442 LOC)
├── drivers/
│   └── __init__.py                       (11 LOC)
└── schemas/
    └── __init__.py                       (11 LOC)
                                          ──────────
                              Total:      4,132 LOC
```

---

## File Analysis

### Domain Root

#### `analytics/__init__.py` (12 LOC)
```
# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Topics: usage, cost, trends
# Roles: facades, engines, schemas
```

**Exports:** None (domain root docstring only)

---

### Facades

#### `analytics/facades/analytics_facade.py` (829 LOC)
```
# Layer: L4 Domain Engine
# AUDIENCE: CUSTOMER
# Product: AI Console (usage/cost statistics)
```

**Enums:**
- `ResolutionType(HOUR, DAY)`
- `ScopeType(ORG, PROJECT, ENV)`

**DTOs (Dataclasses):**
- `TimeWindowResult`
- `UsageTotalsResult`
- `UsageDataPointResult`
- `SignalSourceResult`
- `UsageStatisticsResult`
- `CostTotalsResult`
- `CostDataPointResult`
- `CostByModelResult`
- `CostByFeatureResult`
- `CostStatisticsResult`
- `TopicStatusResult`
- `AnalyticsStatusResult`

**Classes:**
- `SignalAdapter` — fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, etc.
- `AnalyticsFacade` — get_usage_statistics, get_cost_statistics, get_status

**Exports:**
- `AnalyticsFacade`
- `get_analytics_facade()`

**Signal Sources:** cost_records, llm.usage, worker.execution, gateway.metrics

---

#### `analytics/facades/detection_facade.py` (552 LOC)
```
# Layer: L4 Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
```

**Enums:**
- `DetectionType(COST, BEHAVIORAL, DRIFT, POLICY)`
- `AnomalySeverity(LOW, MEDIUM, HIGH)`
- `AnomalyStatus(OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED)`

**DTOs:**
- `DetectionResult`
- `AnomalyInfo`
- `DetectionStatusInfo`

**Classes:**
- `DetectionFacade` — run_detection, list_anomalies, get_anomaly, resolve_anomaly, acknowledge_anomaly, get_detection_status

**Exports:**
- `DetectionFacade`
- `get_detection_facade()`

---

### Engines

#### `analytics/engines/cost_model_engine.py` (450 LOC)
```
# Layer: L4 Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# WARNING: If this logic is wrong, ALL products break.
```

**Constants:**
```python
SKILL_COST_COEFFICIENTS = {
    "http_call": {"base": 1.0, "variance": 0.2},
    "llm_invoke": {"base": 100.0, "variance": 0.3},
    "json_transform": {"base": 0.1, "variance": 0.05},
    # ... 10 skills total
}
```

**Enums:**
- `DriftVerdict(MATCH, MINOR_DRIFT, MAJOR_DRIFT, MISMATCH)`

**DTOs:**
- `StepCostEstimate`
- `FeasibilityResult`
- `DriftAnalysis`

**Functions (exports):**
- `get_skill_coefficients()`
- `estimate_step_cost()`
- `calculate_cumulative_risk()`
- `check_feasibility()`
- `classify_drift()` — MATCH ≤5%, MINOR ≤15%, MAJOR ≤30%, MISMATCH >30%
- `is_significant_risk()`

---

#### `analytics/engines/cost_anomaly_detector.py` (1184 LOC)
```
# Layer: L4 Domain Engine (System Truth)
# Product: system-wide
# Reference: M29 Cost Intelligence, GAP-081
```

**Thresholds:**
```python
ABSOLUTE_SPIKE_THRESHOLD = 1.40  # 40% above baseline for 2 intervals
SUSTAINED_DRIFT_THRESHOLD = 1.25  # 25% for 3+ consecutive days
```

**Enums:**
- `AnomalyType(ABSOLUTE_SPIKE, SUSTAINED_DRIFT, BUDGET_WARNING, BUDGET_EXCEEDED)`
- `AnomalySeverity(LOW, MEDIUM, HIGH)`
- `DerivedCause(RETRY_LOOP, PROMPT_GROWTH, FEATURE_SURGE, TRAFFIC_GROWTH, UNKNOWN)`

**Severity Bands:**
- LOW: +15-25%
- MEDIUM: +25-40%
- HIGH: >40%

**Classes:**
- `CostAnomalyDetector` — detect_all, detect_absolute_spikes, detect_sustained_drift, detect_budget_issues

**Entry Points:**
- `run_anomaly_detection()`
- `run_anomaly_detection_with_governance()`

**Cross-Domain Import:**
```python
from app.services.governance.cross_domain import create_incident_from_cost_anomaly_sync
```

**Governance Invariant:** "Every HIGH+ anomaly creates an incident or crashes"

---

#### `analytics/engines/cost_write_service.py` (225 LOC)
```
# Layer: L4 Domain Engine
# Product: system-wide (Cost Intelligence)
```

**Classes:**
- `CostWriteService` — create_feature_tag, update_feature_tag, create_cost_record, create_or_update_budget

---

#### `analytics/engines/pattern_detection.py` (394 LOC)
```
# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Callers: None (ORPHAN - pending integration)
# Reference: PIN-240
```

**Status:** ORPHAN — pending integration

**PB-S3 Contract:**
- Observe patterns → create feedback → do nothing else
- NO modification of worker_runs, traces, or costs
- Feedback stored SEPARATELY in pattern_feedback table

**Configuration (env vars):**
```python
FAILURE_PATTERN_THRESHOLD = 3
FAILURE_PATTERN_WINDOW_HOURS = 24
COST_SPIKE_THRESHOLD_PERCENT = 50
COST_SPIKE_MIN_RUNS = 5
```

**Functions:**
- `compute_error_signature()` — stable signature for error grouping
- `detect_failure_patterns()` — PB-S3 READ-ONLY
- `detect_cost_spikes()` — PB-S3 READ-ONLY
- `emit_feedback()` — creates PatternFeedback record
- `run_pattern_detection()` — full detection cycle
- `get_feedback_summary()` — read-only query

**Imports:**
- `app.db.get_async_session`
- `app.models.feedback.PatternFeedback, PatternFeedbackCreate`
- `app.models.tenant.WorkerRun`

---

#### `analytics/engines/prediction.py` (442 LOC)
```
# Layer: L3 — Boundary Adapter (Console → Platform)
# Product: AI Console
# Callers: predictions API (read-side)
# Reference: PIN-240
# NOTE: Advisory only. Predictions have zero side-effects.
```

**PB-S5 Contract:**
- Advise → Observe → Do Nothing
- Predictions are advisory only
- Predictions have zero side-effects
- Predictions never modify execution, scheduling, or history

**Configuration:**
```python
FAILURE_CONFIDENCE_THRESHOLD = 0.5
COST_OVERRUN_THRESHOLD_PERCENT = 30
PREDICTION_VALIDITY_HOURS = 24
```

**Functions:**
- `predict_failure_likelihood()` — PB-S5 READ-ONLY
- `predict_cost_overrun()` — PB-S5 READ-ONLY
- `emit_prediction()` — creates PredictionEvent (is_advisory=True enforced)
- `run_prediction_cycle()` — full prediction cycle
- `get_prediction_summary()` — read-only query

**Imports:**
- `app.db.get_async_session`
- `app.models.feedback.PatternFeedback`
- `app.models.prediction.PredictionEvent, PredictionEventCreate`
- `app.models.tenant.WorkerRun`

---

### Placeholder Files (11 LOC each)

- `analytics/facades/__init__.py`
- `analytics/engines/__init__.py`
- `analytics/drivers/__init__.py`
- `analytics/schemas/__init__.py`

---

## Layer Distribution

| Layer | Files | LOC |
|-------|-------|-----|
| L4 (Domain Engine) | 6 | 3,634 |
| L3 (Boundary Adapter) | 1 | 442 |
| Placeholders | 5 | 56 |
| **Total** | **12** | **4,132** |

---

## Cross-Domain Dependencies

| File | External Imports |
|------|------------------|
| cost_anomaly_detector.py | `app.services.governance.cross_domain` |
| pattern_detection.py | `app.db`, `app.models.feedback`, `app.models.tenant` |
| prediction.py | `app.db`, `app.models.feedback`, `app.models.prediction`, `app.models.tenant` |

---

## AUDIENCE/Layer Issues

| File | Issue | Severity |
|------|-------|----------|
| `prediction.py` | Declared as **L3 Boundary Adapter** but lives under `engines/` | LOW (naming) |
| `pattern_detection.py` | Marked **ORPHAN** — no callers | MEDIUM (dead code?) |

---

## Key Governance Contracts

1. **PB-S3 (Pattern Detection):** Observe → Feedback → No mutation
2. **PB-S5 (Prediction):** Advise → Observe → Zero side-effects
3. **Cost Anomaly:** HIGH+ severity → incident creation enforced

---

## Export Summary

### facades/analytics_facade.py
- `AnalyticsFacade`, `get_analytics_facade()`

### facades/detection_facade.py
- `DetectionFacade`, `get_detection_facade()`

### engines/cost_model_engine.py
- `get_skill_coefficients()`, `estimate_step_cost()`, `calculate_cumulative_risk()`, `check_feasibility()`, `classify_drift()`, `is_significant_risk()`
- `StepCostEstimate`, `FeasibilityResult`, `DriftAnalysis`, `DriftVerdict`

### engines/cost_anomaly_detector.py
- `run_anomaly_detection()`, `run_anomaly_detection_with_governance()`
- `CostAnomalyDetector`, `AnomalyType`, `AnomalySeverity`, `DerivedCause`

### engines/cost_write_service.py
- `CostWriteService`

### engines/pattern_detection.py
- `detect_failure_patterns()`, `detect_cost_spikes()`, `emit_feedback()`, `run_pattern_detection()`, `get_feedback_summary()`, `compute_error_signature()`

### engines/prediction.py
- `predict_failure_likelihood()`, `predict_cost_overrun()`, `emit_prediction()`, `run_prediction_cycle()`, `get_prediction_summary()`

---

## Recommendations

1. **prediction.py placement:** Consider moving to `drivers/` since it's declared L3 Boundary Adapter
2. **pattern_detection.py:** Resolve ORPHAN status — wire to caller or mark deprecated
3. **Add domain persona declaration** to `analytics/__init__.py` (similar to integrations domain)
