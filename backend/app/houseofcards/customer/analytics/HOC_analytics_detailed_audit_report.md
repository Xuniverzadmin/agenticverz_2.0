# HOC ANALYTICS DOMAIN DEEP AUDIT REPORT (RIGOROUS)

**Date:** 2026-01-23
**Scope:** `houseofcards/customer/analytics/` (ANALYTICS domain only)
**Auditor:** Claude
**Methodology:** Line-by-line extraction, no assumptions, facts only

---

## 1. FILE INVENTORY

### 1.1 Files Audited (Exact Line Counts)

| File | Path | Lines |
|------|------|-------|
| analytics_facade.py | facades/ | 828 |
| detection_facade.py | facades/ | 551 |
| cost_anomaly_detector.py | engines/ | 1183 |
| cost_model_engine.py | engines/ | 449 |
| cost_write_service.py | engines/ | 224 |
| pattern_detection.py | engines/ | 405 |
| prediction.py | engines/ | 452 |
| **TOTAL** | | **4092** |

### 1.2 Empty Folders

- `schemas/` - contains only `__init__.py`
- `drivers/` - contains only `__init__.py`

---

## 2. LINE-BY-LINE ARTIFACT EXTRACTION

### 2.1 detection_facade.py (551 lines)

**HEADER (Lines 1-10):**
```
Line 1: # Layer: L4 — Domain Engine
Line 2: # Product: system-wide
Line 6: # Role: Detection Facade - Centralized access to anomaly detection operations
Line 7: # Callers: L2 detection.py API, SDK, Worker
Line 10: # Reference: GAP-102 (Anomaly Detection API)
```

**IMPORTS (Lines 49-54):**
```python
Line 49: import logging
Line 50: from dataclasses import dataclass, field
Line 51: from datetime import datetime, timezone
Line 52: from enum import Enum
Line 53: from typing import Any, Dict, List, Optional
Line 54: import uuid
```

**ENUMS:**

| Enum | Line Start | Line End | Values |
|------|------------|----------|--------|
| `DetectionType(str, Enum)` | 59 | 64 | COST="cost", BEHAVIORAL="behavioral", DRIFT="drift", POLICY="policy" |
| `AnomalySeverity(str, Enum)` | 67 | 71 | LOW="LOW", MEDIUM="MEDIUM", HIGH="HIGH" |
| `AnomalyStatus(str, Enum)` | 74 | 79 | OPEN="open", ACKNOWLEDGED="acknowledged", RESOLVED="resolved", DISMISSED="dismissed" |

**DATACLASSES:**

| Dataclass | Line Start | Line End | Fields |
|-----------|------------|----------|--------|
| `DetectionResult` | 82 | 105 | success, detection_type, anomalies_detected, anomalies_created, incidents_created, tenant_id, run_at, error |
| `AnomalyInfo` | 108 | 149 | id, tenant_id, detection_type, anomaly_type, severity, status, entity_type, entity_id, current_value, expected_value, deviation_pct, message, derived_cause, incident_id, detected_at, resolved_at, metadata |
| `DetectionStatusInfo` | 152 | 167 | healthy, engines, last_run, next_scheduled_run |

**CLASSES:**

| Class | Line Start | Line End | Methods |
|-------|------------|----------|---------|
| `DetectionFacade` | 170 | 528 | __init__(181), cost_detector(189), run_detection(205), _run_cost_detection(262), list_anomalies(356), get_anomaly(403), resolve_anomaly(423), acknowledge_anomaly(467), get_detection_status(499) |

**SINGLETON:**
- Line 535: `_facade_instance: Optional[DetectionFacade] = None`
- Lines 538-551: `def get_detection_facade() -> DetectionFacade`

---

### 2.2 analytics_facade.py (828 lines)

**HEADER (Lines 1-11):**
```
Line 1: # Layer: L4 — Domain Engine
Line 2: # AUDIENCE: CUSTOMER
Line 3: # Product: ai-console
Line 7: # Role: Analytics Facade - Centralized access to analytics domain operations
Line 8: # Callers: app.api.analytics (L2)
Line 11: # Reference: Analytics Domain Declaration v1, PIN-411, W4 Pattern
```

**IMPORTS (Lines 33-43):**
```python
Line 33: from __future__ import annotations
Line 35: import logging
Line 36: from dataclasses import dataclass, field
Line 37: from datetime import datetime, timezone, timedelta
Line 38: from enum import Enum
Line 39: from typing import Any
Line 41: from sqlalchemy import text
Line 42: from sqlalchemy.ext.asyncio import AsyncSession
```

**ENUMS:**

| Enum | Line Start | Line End | Values |
|------|------------|----------|--------|
| `ResolutionType(str, Enum)` | 52 | 56 | HOUR="hour", DAY="day" |
| `ScopeType(str, Enum)` | 59 | 64 | ORG="org", PROJECT="project", ENV="env" |

**DATACLASSES:**

| Dataclass | Line Start | Line End | Fields |
|-----------|------------|----------|--------|
| `TimeWindowResult` | 72 | 78 | from_ts, to_ts, resolution |
| `UsageTotalsResult` | 81 | 87 | requests, compute_units, tokens |
| `UsageDataPointResult` | 90 | 97 | ts, requests, compute_units, tokens |
| `SignalSourceResult` | 100 | 105 | sources, freshness_sec |
| `UsageStatisticsResult` | 108 | 115 | window, totals, series, signals |
| `CostTotalsResult` | 118 | 126 | spend_cents, spend_usd, requests, input_tokens, output_tokens |
| `CostDataPointResult` | 129 | 137 | ts, spend_cents, requests, input_tokens, output_tokens |
| `CostByModelResult` | 140 | 149 | model, spend_cents, requests, input_tokens, output_tokens, pct_of_total |
| `CostByFeatureResult` | 152 | 159 | feature_tag, spend_cents, requests, pct_of_total |
| `CostStatisticsResult` | 162 | 171 | window, totals, series, by_model, by_feature, signals |
| `TopicStatusResult` | 174 | 180 | read, write, signals_bound |
| `AnalyticsStatusResult` | 183 | 189 | domain, subdomains, topics |

**CLASSES:**

| Class | Line Start | Line End | Methods |
|-------|------------|----------|---------|
| `SignalAdapter` | 197 | 510 | fetch_cost_metrics(208), fetch_llm_usage(259), fetch_worker_execution(310), fetch_cost_spend(359), fetch_cost_by_model(414), fetch_cost_by_feature(465) |
| `AnalyticsFacade` | 518 | 813 | __init__(525), get_usage_statistics(529), get_cost_statistics(647), get_status(763), _calculate_freshness(787), _calculate_freshness_from_cost(801) |

**SINGLETON:**
- Line 820: `_facade_instance: AnalyticsFacade | None = None`
- Lines 823-828: `def get_analytics_facade() -> AnalyticsFacade`

---

### 2.3 cost_anomaly_detector.py (1183 lines)

**HEADER (Lines 1-5):**
```
Line 1: # Layer: L4 — Domain Engine (System Truth)
Line 2: # Product: system-wide (NOT console-owned)
Line 3: # Callers: tests, future background job
Line 4: # Reference: PIN-240
Line 5: # WARNING: If this logic is wrong, ALL products break.
```

**IMPORTS (Lines 24-41):**
```python
Line 24: from __future__ import annotations
Line 26: import logging
Line 27: import uuid
Line 28: from dataclasses import dataclass, field
Line 29: from datetime import date, datetime, timedelta
Line 30: from enum import Enum
Line 31: from typing import List, Optional
Line 33: from sqlalchemy import text
Line 34: from sqlmodel import Session, select
Line 36-40: from app.db import (CostAnomaly, CostBudget, utc_now)
Line 41: from app.services.governance.cross_domain import create_incident_from_cost_anomaly_sync
```

**ENUMS:**

| Enum | Line Start | Line End | Values |
|------|------------|----------|--------|
| `AnomalyType(str, Enum)` | 51 | 57 | ABSOLUTE_SPIKE="ABSOLUTE_SPIKE", SUSTAINED_DRIFT="SUSTAINED_DRIFT", BUDGET_WARNING="BUDGET_WARNING", BUDGET_EXCEEDED="BUDGET_EXCEEDED" |
| `AnomalySeverity(str, Enum)` | 60 | 65 | LOW="LOW", MEDIUM="MEDIUM", HIGH="HIGH" |
| `DerivedCause(str, Enum)` | 68 | 75 | RETRY_LOOP="RETRY_LOOP", PROMPT_GROWTH="PROMPT_GROWTH", FEATURE_SURGE="FEATURE_SURGE", TRAFFIC_GROWTH="TRAFFIC_GROWTH", UNKNOWN="UNKNOWN" |

**CONSTANTS (Lines 84-100):**
```python
Line 84: ABSOLUTE_SPIKE_THRESHOLD = 1.40
Line 87: CONSECUTIVE_INTERVALS_REQUIRED = 2
Line 90: SUSTAINED_DRIFT_THRESHOLD = 1.25
Line 93: DRIFT_DAYS_REQUIRED = 3
Lines 96-100: SEVERITY_BANDS = {"LOW": (15, 25), "MEDIUM": (25, 40), "HIGH": (40, float("inf"))}
```

**DATACLASSES:**

| Dataclass | Line Start | Line End | Fields |
|-----------|------------|----------|--------|
| `DetectedAnomaly` | 108 | 122 | anomaly_type, severity, entity_type, entity_id, current_value_cents, expected_value_cents, deviation_pct, message, breach_count, derived_cause, metadata |

**FUNCTIONS (Module-Level):**

| Function | Line Start | Line End | Signature |
|----------|------------|----------|-----------|
| `classify_severity` | 130 | 149 | `def classify_severity(deviation_pct: float) -> AnomalySeverity` |
| `run_anomaly_detection` | 1110 | 1123 | `async def run_anomaly_detection(session: Session, tenant_id: str) -> List[CostAnomaly]` |
| `run_anomaly_detection_with_governance` | 1126 | 1183 | `async def run_anomaly_detection_with_governance(session: Session, tenant_id: str) -> dict` |

**CLASSES:**

| Class | Line Start | Line End | Methods |
|-------|------------|----------|---------|
| `CostAnomalyDetector` | 157 | 1102 | __init__(168), detect_all(172), detect_absolute_spikes(194), _detect_entity_spikes(224), _detect_tenant_spike(334), detect_sustained_drift(429), detect_budget_issues(546), _check_budget_threshold(625), _record_breach_and_get_consecutive_count(677), _reset_breach_history(773), _update_drift_tracking(785), _reset_drift_tracking(879), _derive_cause(906), _format_spike_message(1022), persist_anomalies(1040) |

---

### 2.4 cost_model_engine.py (449 lines)

**HEADER (Lines 1-10):**
```
Line 1: # Layer: L4 — Domain Engine (System Truth)
Line 2: # Product: system-wide (NOT console-owned)
Line 6: # Role: Cost modeling and risk estimation domain authority
Line 7: # Callers: CostSimV2Adapter (L3), simulation endpoints
Line 10: # Reference: PIN-254 Phase B Fix
```

**IMPORTS (Lines 25-28):**
```python
Line 25: import logging
Line 26: from dataclasses import dataclass, field
Line 27: from enum import Enum
Line 28: from typing import Any, Dict, List, Optional
```

**CONSTANTS:**
- Lines 41-106: `SKILL_COST_COEFFICIENTS` dictionary
- Lines 109-114: `UNKNOWN_SKILL_COEFFICIENTS` dictionary
- Line 132: `DRIFT_THRESHOLD_MATCH = 0.05`
- Line 133: `DRIFT_THRESHOLD_MINOR = 0.15`
- Line 134: `DRIFT_THRESHOLD_MAJOR = 0.30`
- Line 142: `DEFAULT_RISK_THRESHOLD = 0.5`
- Line 145: `SIGNIFICANT_RISK_THRESHOLD = 0.02`
- Line 148: `CONFIDENCE_DEGRADATION_LONG_PROMPT = 2000`
- Line 149: `CONFIDENCE_DEGRADATION_VERY_LONG_PROMPT = 4000`

**ENUMS:**

| Enum | Line Start | Line End | Values |
|------|------------|----------|--------|
| `DriftVerdict(str, Enum)` | 122 | 128 | MATCH="MATCH", MINOR_DRIFT="MINOR_DRIFT", MAJOR_DRIFT="MAJOR_DRIFT", MISMATCH="MISMATCH" |

**DATACLASSES:**

| Dataclass | Line Start | Line End | Fields |
|-----------|------------|----------|--------|
| `StepCostEstimate` | 152 | 161 | step_index, skill_id, cost_cents, latency_ms, confidence, risk_factors |
| `FeasibilityResult` | 164 | 173 | feasible, budget_sufficient, has_permissions, risk_acceptable, cumulative_risk, reason |
| `DriftAnalysis` | 176 | 184 | verdict, drift_score, cost_delta_pct, feasibility_match, details |

**FUNCTIONS:**

| Function | Line Start | Line End | Signature |
|----------|------------|----------|-----------|
| `get_skill_coefficients` | 187 | 197 | `def get_skill_coefficients(skill_id: str) -> Dict[str, float]` |
| `estimate_step_cost` | 200 | 292 | `def estimate_step_cost(step_index: int, skill_id: str, params: Dict[str, Any]) -> StepCostEstimate` |
| `calculate_cumulative_risk` | 295 | 311 | `def calculate_cumulative_risk(risks: List[Dict[str, float]]) -> float` |
| `check_feasibility` | 314 | 357 | `def check_feasibility(...) -> FeasibilityResult` |
| `classify_drift` | 360 | 415 | `def classify_drift(...) -> DriftAnalysis` |
| `is_significant_risk` | 418 | 420 | `def is_significant_risk(probability: float) -> bool` |

---

### 2.5 cost_write_service.py (224 lines)

**HEADER (Lines 1-10):**
```
Line 1: # Layer: L4 — Domain Engine
Line 2: # Product: system-wide (Cost Intelligence)
Line 6: # Role: DB write delegation for Cost Intelligence API (Phase 2B extraction)
Line 7: # Callers: api/cost_intelligence.py
Line 10: # Reference: PIN-250 Phase 2B Batch 2
```

**IMPORTS (Lines 24-29):**
```python
Line 24: from datetime import datetime, timezone
Line 25: from typing import Optional
Line 27: from sqlmodel import Session
Line 29: from app.db import CostBudget, CostRecord, FeatureTag
```

**FUNCTIONS:**

| Function | Line Start | Line End | Signature |
|----------|------------|----------|-----------|
| `utc_now` | 32 | 34 | `def utc_now() -> datetime` |

**CLASSES:**

| Class | Line Start | Line End | Methods |
|-------|------------|----------|---------|
| `CostWriteService` | 37 | 224 | __init__(44), create_feature_tag(51), update_feature_tag(84), create_cost_record(125), create_or_update_budget(176) |

---

### 2.6 pattern_detection.py (405 lines)

**HEADER (Lines 1-17):**
```
Line 1: # Layer: L4 — Domain Engine (System Truth)
Line 2: # Product: system-wide (NOT console-owned)
Line 3: # Callers: None
Line 4: # Reference: PIN-240
Line 6: # STATUS: DORMANT BY DESIGN
```

**IMPORTS (Lines 34-46):**
```python
Line 34: import hashlib
Line 35: import logging
Line 36: import os
Line 37: from datetime import datetime, timedelta
Line 38: from typing import Optional
Line 39: from uuid import UUID
Line 41: from sqlalchemy import select
Line 42: from sqlalchemy.ext.asyncio import AsyncSession
Line 44: from app.db import get_async_session
Line 45: from app.models.feedback import PatternFeedback, PatternFeedbackCreate
Line 46: from app.models.tenant import WorkerRun
```

**CONSTANTS:**
- Line 51: `FAILURE_PATTERN_THRESHOLD = int(os.getenv("FAILURE_PATTERN_THRESHOLD", "3"))`
- Line 52: `FAILURE_PATTERN_WINDOW_HOURS = int(os.getenv("FAILURE_PATTERN_WINDOW_HOURS", "24"))`
- Line 53: `COST_SPIKE_THRESHOLD_PERCENT = float(os.getenv("COST_SPIKE_THRESHOLD_PERCENT", "50"))`
- Line 54: `COST_SPIKE_MIN_RUNS = int(os.getenv("COST_SPIKE_MIN_RUNS", "5"))`

**FUNCTIONS:**

| Function | Line Start | Line End | Signature |
|----------|------------|----------|-----------|
| `compute_error_signature` | 57 | 77 | `def compute_error_signature(error: str) -> str` |
| `detect_failure_patterns` | 80 | 148 | `async def detect_failure_patterns(session: AsyncSession, ...)` |
| `detect_cost_spikes` | 151 | 236 | `async def detect_cost_spikes(session: AsyncSession, ...)` |
| `emit_feedback` | 239 | 277 | `async def emit_feedback(session: AsyncSession, feedback: PatternFeedbackCreate)` |
| `run_pattern_detection` | 280 | 357 | `async def run_pattern_detection(tenant_id: Optional[UUID] = None)` |
| `get_feedback_summary` | 360 | 405 | `async def get_feedback_summary(...)` |

---

### 2.7 prediction.py (452 lines)

**HEADER (Lines 1-16):**
```
Line 1: # Layer: L4 — Domain Engine (Advisory)
Line 2: # Product: AI Console
Line 3: # Callers: predictions API (read-side)
Line 4: # Reference: PIN-240
Line 6: # CLASSIFICATION: Advisory Engine (not Boundary Adapter)
```

**IMPORTS (Lines 32-43):**
```python
Line 32: import logging
Line 33: from datetime import datetime, timedelta
Line 34: from typing import Optional
Line 35: from uuid import UUID
Line 37: from sqlalchemy import func, select
Line 38: from sqlalchemy.ext.asyncio import AsyncSession
Line 40: from app.db import get_async_session
Line 41: from app.models.feedback import PatternFeedback
Line 42: from app.models.prediction import PredictionEvent, PredictionEventCreate
Line 43: from app.models.tenant import WorkerRun
```

**CONSTANTS:**
- Line 48: `FAILURE_CONFIDENCE_THRESHOLD = 0.5`
- Line 49: `COST_OVERRUN_THRESHOLD_PERCENT = 30`
- Line 50: `PREDICTION_VALIDITY_HOURS = 24`

**FUNCTIONS:**

| Function | Line Start | Line End | Signature |
|----------|------------|----------|-----------|
| `predict_failure_likelihood` | 53 | 176 | `async def predict_failure_likelihood(session: AsyncSession, ...)` |
| `predict_cost_overrun` | 179 | 284 | `async def predict_cost_overrun(session: AsyncSession, ...)` |
| `emit_prediction` | 287 | 326 | `async def emit_prediction(session: AsyncSession, prediction: PredictionEventCreate)` |
| `run_prediction_cycle` | 329 | 398 | `async def run_prediction_cycle(tenant_id: Optional[UUID] = None)` |
| `get_prediction_summary` | 401 | 452 | `async def get_prediction_summary(...)` |

---

## 3. CROSS-COMPARISON: ENUM ANALYSIS

### 3.1 All Enums in Analytics Domain

| # | Enum Name | File | Line | Values |
|---|-----------|------|------|--------|
| 1 | `DetectionType` | detection_facade.py | 59-64 | COST, BEHAVIORAL, DRIFT, POLICY |
| 2 | `AnomalySeverity` | detection_facade.py | 67-71 | LOW, MEDIUM, HIGH |
| 3 | `AnomalyStatus` | detection_facade.py | 74-79 | OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED |
| 4 | `ResolutionType` | analytics_facade.py | 52-56 | HOUR, DAY |
| 5 | `ScopeType` | analytics_facade.py | 59-64 | ORG, PROJECT, ENV |
| 6 | `AnomalyType` | cost_anomaly_detector.py | 51-57 | ABSOLUTE_SPIKE, SUSTAINED_DRIFT, BUDGET_WARNING, BUDGET_EXCEEDED |
| 7 | `AnomalySeverity` | cost_anomaly_detector.py | 60-65 | LOW, MEDIUM, HIGH |
| 8 | `DerivedCause` | cost_anomaly_detector.py | 68-75 | RETRY_LOOP, PROMPT_GROWTH, FEATURE_SURGE, TRAFFIC_GROWTH, UNKNOWN |
| 9 | `DriftVerdict` | cost_model_engine.py | 122-128 | MATCH, MINOR_DRIFT, MAJOR_DRIFT, MISMATCH |

### 3.2 FACT: AnomalySeverity Enum Comparison

**Location 1: detection_facade.py lines 67-71**
```python
class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    LOW = "LOW"  # +15% to +25%
    MEDIUM = "MEDIUM"  # +25% to +40%
    HIGH = "HIGH"  # >40%
```

**Location 2: cost_anomaly_detector.py lines 60-65**
```python
class AnomalySeverity(str, Enum):
    """Aligned severity bands per plan."""

    LOW = "LOW"  # +15% to +25%
    MEDIUM = "MEDIUM"  # +25% to +40%
    HIGH = "HIGH"  # >40%
```

**FACT:** Both files define an enum named `AnomalySeverity` that:
- Inherits from `(str, Enum)`
- Has exactly 3 members: `LOW`, `MEDIUM`, `HIGH`
- Assigns identical string values: `"LOW"`, `"MEDIUM"`, `"HIGH"`
- Has identical comment annotations for thresholds

**OBSERVATION:** This is the same enum definition appearing in two different files.

---

## 4. CROSS-COMPARISON: DATACLASS ANALYSIS

### 4.1 All Dataclasses in Analytics Domain

| File | Dataclass Count | Names |
|------|----------------|-------|
| detection_facade.py | 3 | DetectionResult, AnomalyInfo, DetectionStatusInfo |
| analytics_facade.py | 12 | TimeWindowResult, UsageTotalsResult, UsageDataPointResult, SignalSourceResult, UsageStatisticsResult, CostTotalsResult, CostDataPointResult, CostByModelResult, CostByFeatureResult, CostStatisticsResult, TopicStatusResult, AnalyticsStatusResult |
| cost_anomaly_detector.py | 1 | DetectedAnomaly |
| cost_model_engine.py | 3 | StepCostEstimate, FeasibilityResult, DriftAnalysis |
| **TOTAL** | **19** | |

### 4.2 Dataclass Field Comparison

**detection_facade.py::AnomalyInfo (Line 108)**
Fields: id, tenant_id, detection_type, anomaly_type, severity, status, entity_type, entity_id, current_value, expected_value, deviation_pct, message, derived_cause, incident_id, detected_at, resolved_at, metadata

**cost_anomaly_detector.py::DetectedAnomaly (Line 108)**
Fields: anomaly_type, severity, entity_type, entity_id, current_value_cents, expected_value_cents, deviation_pct, message, breach_count, derived_cause, metadata

**FACT:** These dataclasses have different names and different field sets. They are NOT duplicates.

---

## 5. CROSS-COMPARISON: FUNCTION ANALYSIS

### 5.1 utc_now() Function

**Location 1: cost_write_service.py lines 32-34**
```python
def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)
```

**Location 2: cost_anomaly_detector.py line 39**
```python
from app.db import (
    CostAnomaly,
    CostBudget,
    utc_now,
)
```

**FACT:**
- `cost_write_service.py` DEFINES a local `utc_now()` function at line 32
- `cost_anomaly_detector.py` IMPORTS `utc_now` from `app.db` at line 39

**OBSERVATION:** Two different sources for the same function name. One is a local definition, one is an import from a shared module (`app.db`).

---

## 6. HEADER COMPLIANCE ANALYSIS

| File | Layer Header | AUDIENCE Header | Product Header | Reference |
|------|--------------|-----------------|----------------|-----------|
| analytics_facade.py | L4 (Line 1) | CUSTOMER (Line 2) | ai-console (Line 3) | PIN-411 (Line 11) |
| detection_facade.py | L4 (Line 1) | None | system-wide (Line 2) | GAP-102 (Line 10) |
| cost_anomaly_detector.py | L4 (Line 1) | None | system-wide (Line 2) | PIN-240 (Line 4) |
| cost_model_engine.py | L4 (Line 1) | None | system-wide (Line 2) | PIN-254 (Line 10) |
| cost_write_service.py | L4 (Line 1) | None | system-wide (Line 2) | PIN-250 (Line 10) |
| pattern_detection.py | L4 (Line 1) | None | system-wide (Line 2) | PIN-240 (Line 4) |
| prediction.py | L4 (Line 1) | None | AI Console (Line 2) | PIN-240 (Line 4) |

**FACT:** Only `analytics_facade.py` has an `AUDIENCE:` header.

---

## 7. IMPORT RELATIONSHIPS

### 7.1 detection_facade.py Imports from cost_anomaly_detector.py

**Line 195-196:**
```python
from app.services.cost_anomaly_detector import CostAnomalyDetector
```

**Line 295-297:**
```python
from app.services.cost_anomaly_detector import (
    run_anomaly_detection_with_governance,
)
```

**FACT:** detection_facade.py imports from `app.services.cost_anomaly_detector`, NOT from the `houseofcards` path.

---

## 8. CONTRACT/STATUS MARKERS

| File | Marker | Line | Description |
|------|--------|------|-------------|
| cost_anomaly_detector.py | M29 | 8 | M29 Cost Anomaly Detector - Aligned Rules |
| pattern_detection.py | DORMANT BY DESIGN | 6 | Intentionally unwired |
| pattern_detection.py | PB-S3 | 8,24 | observe → feedback → no mutation |
| prediction.py | PB-S5 | 11,23 | Predictions are advisory only |

---

## 9. FINDINGS AND RESOLUTIONS

### 9.1 ANA-DUP-001: AnomalySeverity Enum Duplication

**Type:** Exact duplicate enum
**Severity:** CRITICAL
**Status:** RESOLVED — QUARANTINED

**Evidence:**
- File 1: `detection_facade.py` lines 67-71 (DUPLICATE)
- File 2: `cost_anomaly_detector.py` lines 60-65 (CANONICAL)
- Both defined: `class AnomalySeverity(str, Enum)` with identical values LOW, MEDIUM, HIGH

**Resolution (2026-01-23):**
1. Created quarantine folder: `houseofcards/duplicate/analytics/`
2. Created frozen copy: `duplicate/analytics/anomaly_severity.py`
3. Updated `detection_facade.py` to import from canonical source:
   ```python
   # AnomalySeverity enum removed — ANA-DUP-001 quarantine
   # Import from canonical source: cost_anomaly_detector.py
   from app.houseofcards.customer.analytics.engines.cost_anomaly_detector import (
       AnomalySeverity,
   )
   ```

**Canonical Authority:**
```
houseofcards/customer/analytics/engines/cost_anomaly_detector.py::AnomalySeverity
```

---

### 9.2 ANA-FIND-002: Local utc_now() Definition

**Type:** Local function shadows shared utility
**Severity:** LOW
**Status:** TOLERATED — Utility drift

**Evidence:**
- File: `cost_write_service.py` line 32-34
- Defines: `def utc_now() -> datetime`
- Meanwhile: `cost_anomaly_detector.py` imports `utc_now` from `app.db`

**Decision:** No action. Utility drift is tolerated per architectural guidance. Consolidation would create inappropriate cross-domain coupling.

---

### 9.3 ANA-FIND-003: Missing AUDIENCE Headers

**Type:** Missing governance marker
**Severity:** INFORMATIONAL
**Status:** DEFERRED — Hygiene sweep

**Evidence:**
6 of 7 files lack `AUDIENCE:` header. Only `analytics_facade.py` has it.

**Decision:** Deferred to separate hygiene sweep. Not a duplication concern.

---

## 10. SUMMARY TABLE

| Category | Count |
|----------|-------|
| Files audited | 7 |
| Total lines | 4092 |
| Enums defined | 9 |
| Dataclasses defined | 19 |
| Classes defined | 6 |
| Module-level functions | 16 |
| Singletons | 2 |

---

## 11. RESOLUTION SUMMARY

| Issue ID | Type | Status | Action |
|----------|------|--------|--------|
| ANA-DUP-001 | AnomalySeverity enum duplication | **QUARANTINED** | Frozen copy + import fix |
| ANA-FIND-002 | utc_now() utility drift | TOLERATED | No action |
| ANA-FIND-003 | Missing AUDIENCE headers | DEFERRED | Hygiene sweep |

### Quarantine Artifacts Created

| File | Purpose |
|------|---------|
| `duplicate/analytics/__init__.py` | Package marker (no exports) |
| `duplicate/analytics/anomaly_severity.py` | Frozen facade enum copy |
| `duplicate/analytics/README.md` | Quarantine documentation |

### Files Modified

| File | Change |
|------|--------|
| `detection_facade.py` | Removed local AnomalySeverity, imports from canonical engine |

---

## 12. CROSS-DOMAIN QUARANTINE STATUS

| Domain | Quarantine Count | Status |
|--------|------------------|--------|
| Policies | 4 | QUARANTINED |
| Incidents | TBD | — |
| Logs | 0 | CLEAN |
| **Analytics** | **1** | **QUARANTINED** |

---

## 13. AUDIT TRAIL

| Date | Action | Method |
|------|--------|--------|
| 2026-01-23 | Line-by-line read of all 7 files | Read tool with full content |
| 2026-01-23 | Extracted all artifacts with exact line numbers | Manual extraction |
| 2026-01-23 | Cross-compared all enums | Direct string comparison |
| 2026-01-23 | Initial report generated | Facts only, no assumptions |
| 2026-01-23 | ANA-DUP-001 quarantine executed | Folder + files created |
| 2026-01-23 | detection_facade.py updated | Import from canonical |
| 2026-01-23 | Audit report updated with resolutions | Final status |

---

**End of Rigorous Audit Report**
