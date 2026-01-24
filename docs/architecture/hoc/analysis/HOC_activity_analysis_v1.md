# HOC Activity Domain Analysis v1

**Domain:** `app/houseofcards/customer/activity/`
**Audience:** CUSTOMER
**Date:** 2026-01-22
**Status:** CLEANUP COMPLETE
**Last Updated:** 2026-01-22

---

## 1. Final Structure (Post-Cleanup)

```
app/houseofcards/customer/activity/
├── __init__.py
├── drivers/
│   └── __init__.py           (EMPTY - reserved for L3 adapters)
├── engines/
│   ├── __init__.py
│   ├── attention_ranking_service.py   # Signal prioritization
│   ├── cost_analysis_service.py       # Cost anomaly detection
│   ├── pattern_detection_service.py   # Pattern recognition
│   ├── signal_feedback_service.py     # Acknowledge/suppress
│   └── signal_identity.py             # Fingerprint utility
├── facades/
│   ├── __init__.py
│   └── activity_facade.py             # Domain entry point
└── schemas/
    └── __init__.py           (EMPTY - reserved for DTOs)
```

**File Count:** 6 files (excluding __init__.py)

---

## 2. Completed Actions

### 2.1 Files Moved Out (COMPLETED 2026-01-22)

| File | From | To | Reason |
|------|------|-----|--------|
| `plan_generation_engine.py` | activity/engines/ | `general/runtime/engines/` | System-wide, handles planning (pre-execution) |
| `llm_failure_service.py` | activity/engines/ | `incidents/engines/` | System-wide, S4 failure truth model |

**Decision Rationale:**
- **plan_generation_engine.py**: Header marked "system-wide (NOT console-owned)". Handles plan generation BEFORE runs start (memory retrieval, planner calls). Activity domain observes execution history; this file creates the plan before execution happens.
- **llm_failure_service.py**: Header marked "system-wide". Implements S4 failure truth model (PIN-196). Persists authoritative failure facts. Incidents domain owns "what went wrong?" - this file creates those facts.

### 2.2 Empty Folders (KEPT)

| Folder | Status | Reason |
|--------|--------|--------|
| `drivers/` | EMPTY | Reserved for future L3 adapters |
| `schemas/` | EMPTY | Reserved for future DTOs |

---

## 3. Import Inventory

### 3.1 External Imports (FROM activity domain)

| File | Imports From |
|------|--------------|
| `activity_facade.py` | `app.services.activity.attention_ranking_service` |
| `activity_facade.py` | `app.services.activity.cost_analysis_service` |
| `activity_facade.py` | `app.services.activity.pattern_detection_service` |
| `activity_facade.py` | `app.services.activity.signal_feedback_service` |
| `activity_facade.py` | `app.services.activity.signal_identity` |

**Note:** Import paths need update from `app.services.activity.*` to `app.houseofcards.customer.activity.engines.*`

### 3.2 Standard Library Imports

| File | Stdlib Imports |
|------|----------------|
| All engines | `dataclasses`, `datetime`, `typing` |
| `signal_identity.py` | `hashlib`, `json` |
| `activity_facade.py` | `logging` |

### 3.3 Database Imports

| File | DB Import |
|------|-----------|
| All services | `sqlalchemy.ext.asyncio.AsyncSession` |
| `activity_facade.py` | `sqlalchemy.text` |

---

## 4. Export Inventory

### 4.1 Facade Exports (Public API)

**File:** `activity_facade.py`

| Export | Type | Description |
|--------|------|-------------|
| `ActivityFacade` | class | Main facade class |
| `PolicyContextResult` | dataclass | Policy context for runs |
| `RunSummaryResult` | dataclass | Run summary for list view |

**Facade Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_runs()` | List[RunSummaryResult] | List runs with filters |
| `get_run_detail()` | RunDetailResult | Get run details (O3) |
| `get_run_evidence()` | EvidenceResult | Get run evidence context (O4) |
| `get_run_proof()` | ProofResult | Get run integrity proof (O5) |
| `get_status_summary()` | dict | Runs grouped by status |
| `get_patterns()` | PatternDetectionResult | Pattern detection (SIG-O3) |
| `get_cost_analysis()` | CostAnalysisResult | Cost anomalies (SIG-O4) |
| `get_attention_queue()` | AttentionQueueResult | Attention ranking (SIG-O5) |
| `get_live_runs()` | List[LiveRunResult] | V2 live runs with policy |
| `get_completed_runs()` | List[CompletedRunResult] | V2 completed runs |
| `get_signals()` | SignalsResult | V2 synthesized signals |
| `get_metrics()` | MetricsResult | V2 activity metrics |
| `get_threshold_signals()` | ThresholdSignalsResult | V2 threshold proximity |
| `get_risk_signals()` | RiskSignalsResult | Risk signal aggregates |
| `acknowledge_signal()` | AcknowledgeResult | Acknowledge a signal |
| `suppress_signal()` | SuppressResult | Suppress a signal |

### 4.2 Engine Exports

**File:** `attention_ranking_service.py`

| Export | Type | Description |
|--------|------|-------------|
| `AttentionRankingService` | class | Attention score computation |
| `AttentionSignal` | dataclass | Signal in attention queue |
| `AttentionQueueResult` | dataclass | Attention queue query result |

**Methods:**
- `get_attention_queue(tenant_id, limit, offset, min_score)` → AttentionQueueResult
- `compute_attention_score(signal_type, severity, recency_hours, pattern_frequency)` → float

---

**File:** `cost_analysis_service.py`

| Export | Type | Description |
|--------|------|-------------|
| `CostAnalysisService` | class | Cost anomaly detection |
| `CostAnomaly` | dataclass | Detected cost anomaly |
| `CostAnalysisResult` | dataclass | Cost analysis result |

**Methods:**
- `analyze_costs(tenant_id, baseline_days, threshold_pct)` → CostAnalysisResult
- `get_cost_breakdown(tenant_id, group_by, period_days)` → dict[str, float]

---

**File:** `pattern_detection_service.py`

| Export | Type | Description |
|--------|------|-------------|
| `PatternDetectionService` | class | Activity pattern detection |
| `DetectedPattern` | dataclass | Detected pattern |
| `PatternDetectionResult` | dataclass | Pattern detection result |

**Methods:**
- `detect_patterns(tenant_id, window_hours, min_confidence, limit)` → PatternDetectionResult
- `get_pattern_detail(tenant_id, pattern_id)` → Optional[DetectedPattern]

---

**File:** `signal_feedback_service.py`

| Export | Type | Description |
|--------|------|-------------|
| `SignalFeedbackService` | class | Signal acknowledgment/suppression |
| `AcknowledgeResult` | dataclass | Acknowledge result |
| `SuppressResult` | dataclass | Suppress result |
| `SignalFeedbackStatus` | dataclass | Feedback status |

**Methods:**
- `acknowledge_signal(tenant_id, signal_id, acknowledged_by)` → AcknowledgeResult
- `suppress_signal(tenant_id, signal_id, suppress_hours, reason, suppressed_by)` → SuppressResult
- `get_feedback_status(tenant_id, signal_id)` → SignalFeedbackStatus

---

**File:** `signal_identity.py`

| Export | Type | Description |
|--------|------|-------------|
| `compute_signal_fingerprint_from_row` | function | Compute fingerprint from row dict |
| `compute_signal_fingerprint` | function | Compute fingerprint from fields |

---

## 5. Function/Task Inventory

### 5.1 Core Business Functions

| Function | Owner | Layer | Description |
|----------|-------|-------|-------------|
| Run listing | ActivityFacade | L4 | List runs with filters, pagination |
| Run detail | ActivityFacade | L4 | Get detailed run information |
| Run evidence | ActivityFacade | L4 | Get run evidence/context |
| Run proof | ActivityFacade | L4 | Get integrity proof |
| Status aggregation | ActivityFacade | L4 | Group runs by status |

### 5.2 Signal Functions

| Function | Owner | Layer | Description |
|----------|-------|-------|-------------|
| Pattern detection | PatternDetectionService | L4 | Detect recurring patterns |
| Cost analysis | CostAnalysisService | L4 | Detect cost anomalies |
| Attention ranking | AttentionRankingService | L4 | Prioritize signals by score |
| Signal acknowledge | SignalFeedbackService | L4 | Mark signal as reviewed |
| Signal suppress | SignalFeedbackService | L4 | Temporarily hide signal |
| Signal fingerprint | signal_identity | L4 | Compute signal identity |

### 5.3 V2 API Functions

| Function | Owner | Layer | Description |
|----------|-------|-------|-------------|
| Live runs | ActivityFacade | L4 | V2 live runs with policy context |
| Completed runs | ActivityFacade | L4 | V2 completed runs with policy |
| Signals | ActivityFacade | L4 | V2 synthesized signals |
| Metrics | ActivityFacade | L4 | V2 activity metrics |
| Threshold signals | ActivityFacade | L4 | V2 threshold proximity |
| Risk signals | ActivityFacade | L4 | Risk signal aggregates |

---

## 6. Dependency Graph

```
activity_facade.py
├── attention_ranking_service.py
├── cost_analysis_service.py
├── pattern_detection_service.py
├── signal_feedback_service.py
└── signal_identity.py

External Dependencies:
├── app.services.activity.* (OLD PATH - needs update to houseofcards)
├── sqlalchemy.ext.asyncio.AsyncSession
└── sqlalchemy.text
```

---

## 7. Remaining Action Items

### 7.1 Import Path Updates (Priority: MEDIUM)

| File | Old Import | New Import |
|------|------------|------------|
| `activity_facade.py` | `app.services.activity.*` | `app.houseofcards.customer.activity.engines.*` |

### 7.2 Documentation (Priority: LOW)

- Add `__init__.py` exports for each subpackage
- Add module docstrings to empty `__init__.py` files

---

## 8. Domain Summary

| Metric | Value |
|--------|-------|
| **Purpose** | Runs, traces, execution history, signals |
| **Files** | 6 |
| **Facade** | 1 (activity_facade.py) |
| **Engines** | 5 |
| **Drivers** | 0 (reserved) |
| **Schemas** | 0 (reserved) |
| **External Dependencies** | sqlalchemy, app.services (to be updated) |
| **Callers** | app.api.activity (L2) |

---

## 9. Change Log

| Date | Action | Details |
|------|--------|---------|
| 2026-01-22 | Initial analysis | Structure, imports, exports documented |
| 2026-01-22 | Files moved | `plan_generation_engine.py` → general/runtime/engines/, `llm_failure_service.py` → incidents/engines/ |
| 2026-01-22 | Status updated | CLEANUP COMPLETE |

---

*Generated: 2026-01-22*
*Version: v1.1*
