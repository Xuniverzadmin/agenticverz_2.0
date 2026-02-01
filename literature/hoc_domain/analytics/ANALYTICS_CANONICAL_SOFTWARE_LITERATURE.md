# Analytics Domain — Canonical Software Literature

**Domain:** analytics
**Generated:** 2026-01-31
**Reference:** PIN-497
**Total Files:** 46 (21 L5_engines, 9 L6_drivers, 2 L5_schemas, 2 adapters, __init__.py files)

---

## Consolidation Actions (2026-01-31)

### Naming Violations Fixed (18 renames)

**L5 (15):**

| # | Old Name | New Name |
|---|----------|----------|
| N1 | canary.py | canary_engine.py |
| N2 | config.py | config_engine.py |
| N3 | coordinator.py | coordinator_engine.py |
| N4 | cost_anomaly_detector.py | cost_anomaly_detector_engine.py |
| N5 | cost_snapshots.py | cost_snapshots_engine.py |
| N6 | costsim_models.py | costsim_models_engine.py |
| N7 | datasets.py | datasets_engine.py |
| N8 | divergence.py | divergence_engine.py |
| N9 | envelope.py | envelope_engine.py |
| N10 | metrics.py | metrics_engine.py |
| N11 | pattern_detection.py | pattern_detection_engine.py |
| N12 | prediction.py | prediction_engine.py |
| N13 | provenance.py | provenance_engine.py |
| N14 | s1_retry_backoff.py | s1_retry_backoff_engine.py |
| N15 | sandbox.py | sandbox_engine.py |

**L6 (3):**

| # | Old Name | New Name |
|---|----------|----------|
| N16 | audit_persistence.py | coordination_audit_driver.py |
| N17 | leader.py | leader_driver.py |
| N18 | provenance_async.py | provenance_driver.py |

### Header Correction (1)

| File | Old Header | New Header |
|------|-----------|------------|
| analytics/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain (Analytics)` |

### Class Rename (1)

| File | Old Class | New Class | Alias |
|------|----------|-----------|-------|
| cost_write_engine.py | CostWriteService | CostWriteEngine | CostWriteService = CostWriteEngine |

### Import Path Fix (1)

| File | Old Import | New Import |
|------|-----------|------------|
| detection_facade.py | `...cost_anomaly_detector import` | `...cost_anomaly_detector_engine import` |

### Legacy Connections

**None.** The `from app.services.detection.facade` reference in `detection_facade.py` is inside a docstring (Usage example), not an active import.

### New L5_schemas File (PIN-504 Phase 6)

| File | Contents | Purpose |
|------|----------|---------|
| `L5_schemas/query_types.py` | `ResolutionType`, `ScopeType` enums | Type enums extracted from `analytics_facade.py` so L2 can import without L5_engines dependency |

### Cross-Domain Imports (Documented — Deferred to Rewiring)

`cost_anomaly_detector_engine.py` has 3 lazy (function-scoped) imports from `app.hoc.cus.incidents.L3_adapters`:
- `AnomalyIncidentBridge` (line ~975)
- `CostAnomalyFact` (line ~981)
- Bridge components (line ~1047)

**Purpose:** Analytics detects anomalies and emits facts. Incidents domain (via bridge) decides whether to create incidents. This is the authority-model separation.

**Correct architecture:** L5 analytics engine → L4 orchestrator → L5 incidents engine. Currently L5→L5 cross-domain. Deferred to rewiring phase.

### Hybrid File (Documented — Deferred to Refactor)

`cost_snapshots_engine.py` declares `# Layer: L5/L6 — HYBRID (pending refactor)`. Contains mixed business logic and database operations. Schemas already extracted to `L5_schemas/cost_snapshot_schemas.py`. DB operations should be extracted to an L6 driver during refactor phase.

### Duplicates

None identified.

---

## Conceptual Domain Split (from __init__.py)

| Layer | Purpose | Files |
|-------|---------|-------|
| INSIGHT (Console) | Aggregations, statistics, trends | analytics_facade.py, detection_facade.py |
| TRUTH (System-wide) | System truth, governance-adjacent | cost_model_engine.py, cost_anomaly_detector_engine.py, cost_write_engine.py |
| ADVISORY (Zero side-effects) | Predictions, advisory only | prediction_engine.py |
| DORMANT (Quarantined) | Complete but unwired | pattern_detection_engine.py |

---

## L5_engines (21 files)

### __init__.py
- **Role:** Package init (empty exports)

### ai_console_panel_engine.py
- **Role:** AI console panel rendering engine

### analytics_facade.py
- **Role:** Main analytics facade (aggregations, statistics, trends)
- **Classes:** 16 dataclasses + AnalyticsFacade
- **Factory:** `get_analytics_facade()`
- **Callers:** L4 analytics_handler (analytics.query)

### canary_engine.py *(renamed from canary.py)*
- **Role:** Canary deployment monitoring

### config_engine.py *(renamed from config.py)*
- **Role:** Analytics configuration
- **Factory:** `get_config()`, `get_commit_sha()`

### coordinator_engine.py *(renamed from coordinator.py)*
- **Role:** Analytics coordination engine

### cost_anomaly_detector_engine.py *(renamed from cost_anomaly_detector.py)*
- **Role:** Cost anomaly detection (system truth, incident escalation)
- **Classes:** `CostAnomalyDetector`, `AnomalySeverity`, + 3 others
- **Cross-domain:** Imports incidents bridge (deferred to rewiring)

### cost_model_engine.py
- **Role:** Cost model (system truth, all products depend)
- **Factory:** `get_skill_coefficients()`

### cost_snapshots_engine.py *(renamed from cost_snapshots.py)*
- **Layer:** L5 — Domain Engine
- **Role:** Cost snapshot business logic (database operations extracted to L6)
- **Classes:** `SnapshotAnomalyDetector`, `SnapshotComputer`, `BaselineComputer`
- **Dependencies:** Accepts `CostSnapshotsDriverProtocol` via constructor injection
- **Reference:** PIN-508 Phase 1A

### cost_write_engine.py
- **Role:** Cost write operations (L5 facade over L6 driver)
- **Classes:** `CostWriteEngine` (renamed from CostWriteService)
- **Alias:** `CostWriteService = CostWriteEngine`

### costsim_models_engine.py *(renamed from costsim_models.py)*
- **Role:** Cost simulation models/types

### datasets_engine.py *(renamed from datasets.py)*
- **Role:** Dataset management
- **Factory:** `get_dataset_validator()`

### detection_facade.py
- **Role:** Detection facade — anomaly lifecycle, read models
- **Classes:** `DetectionFacade`, `DetectionType`, `AnomalyStatus`, + 4 others
- **Factory:** `get_detection_facade()`
- **Callers:** L4 analytics_handler (analytics.detection)

### divergence_engine.py *(renamed from divergence.py)*
- **Role:** Model/data divergence detection

### envelope_engine.py *(renamed from envelope.py)*
- **Role:** Envelope/optimization calculations
- **Factory:** `get_envelope_priority()`

### metrics_engine.py *(renamed from metrics.py)*
- **Role:** Metrics collection/computation
- **Factory:** `get_metrics()`, `get_alert_rules()`

### pattern_detection_engine.py *(renamed from pattern_detection.py)*
- **Role:** Pattern detection — **DORMANT (quarantined, complete but unwired)**

### prediction_engine.py *(renamed from prediction.py)*
- **Role:** Failure/cost predictions — **ADVISORY (zero side-effects per PB-S5)**

### provenance_engine.py *(renamed from provenance.py)*
- **Role:** Data provenance logging
- **Factory:** `get_provenance_logger()`

### s1_retry_backoff_engine.py *(renamed from s1_retry_backoff.py)*
- **Role:** S1 retry backoff logic

### sandbox_engine.py *(renamed from sandbox.py)*
- **Role:** Sandbox execution environment
- **Factory:** `get_sandbox()`

---

## L6_drivers (9 files)

### __init__.py
- **Role:** Package init, re-exports AlertDriver, CostAnomalyDriver, PredictionDriver

### analytics_read_driver.py
- **Role:** Analytics read operations
- **Classes:** `AnalyticsReadDriver`

### coordination_audit_driver.py *(renamed from audit_persistence.py)*
- **Role:** Coordination audit record persistence
- **Classes:** `CoordinationAuditRecordDB` (SQLModel table)

### cost_anomaly_driver.py
- **Role:** Cost anomaly detection DB operations
- **Classes:** `CostAnomalyDriver`

### cost_snapshots_driver.py *(NEW — PIN-508 Phase 1A)*
- **Layer:** L6 — Domain Driver
- **Role:** Database operations for cost snapshots (extracted from cost_snapshots_engine.py)
- **Classes:** `CostSnapshotsDriver`
- **Reference:** PIN-508 Phase 1A

### cost_write_driver.py
- **Role:** Cost write DB operations
- **Classes:** `CostWriteDriver`

### leader_driver.py *(renamed from leader.py)*
- **Role:** Leader election driver
- **Classes:** `LeaderContext`

### pattern_detection_driver.py
- **Role:** Pattern detection DB operations
- **Classes:** `PatternDetectionDriver`

### prediction_driver.py
- **Role:** Prediction event DB operations
- **Classes:** `PredictionDriver`

### provenance_driver.py *(renamed from provenance_async.py)*
- **Role:** Async provenance logging driver

---

## L5_schemas (2 files)

### __init__.py
- **Role:** Schemas package init

### cost_snapshot_schemas.py
- **Role:** Cost snapshot schema definitions (extracted from cost_snapshots hybrid)

---

## Adapters (2 files)

### __init__.py
- **Role:** Package init (empty)

### v2_adapter.py
- **Role:** V2 API adapter (L2 boundary)

---

## L4 Handler

**File:** `hoc/cus/hoc_spine/orchestrator/handlers/analytics_handler.py`
**Operations:** 2

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| analytics.query | AnalyticsQueryHandler | AnalyticsFacade |
| analytics.detection | AnalyticsDetectionHandler | DetectionFacade |

No L4 handler import updates required — handler imports `analytics_facade` and `detection_facade` which were not renamed.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat B: Stale Docstring References Corrected (1)

| File | Old Docstring Reference | New Docstring Reference |
|------|------------------------|------------------------|
| `L5_engines/detection_facade.py` | `from app.services.detection.facade import get_detection_facade` | `from app.hoc.cus.analytics.L5_engines.detection_facade import get_detection_facade` |

### Cat B: Active Legacy Imports

**None.** Domain has zero active `app.services` imports.

### Legacy Connections

**None.** Domain is clean — no HOC→legacy or legacy→HOC active imports.

### Cross-Domain Imports

**None.** Domain is clean.

### Tally

62/62 checks PASS (59 consolidation + 3 cleansing).

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-510 Phase 1C — Analytics→Incidents L4 Coordinator (2026-02-01)

- `CostAnomalyFact` moved from `incidents/L5_engines/anomaly_bridge.py` to `hoc_spine/schemas/anomaly_types.py` (schema admission compliant: consumers = analytics, incidents)
- New L4 coordinator: `hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py`
- Stale `L3_adapters` import paths in `cost_anomaly_detector_engine.py` fixed to canonical paths
- Backward-compat re-export left in `anomaly_bridge.py`
- Reference: `docs/memory-pins/PIN-510-domain-remediation-queue.md`

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

**`cost_write_engine.py` (L5):** Now the canonical import source for `CostWriteService` in `api/cus/logs/cost_intelligence.py`. Previous legacy path `app.services.cost_write_service` severed. Alias `CostWriteService = CostWriteEngine` provides backward compat.

**`cost_anomaly_detector_engine.py` (L5):** Now the canonical import source for `run_anomaly_detection` in `api/cus/logs/cost_intelligence.py`. Previous legacy path `app.services.cost_anomaly_detector` severed. Identical `run_anomaly_detection(session, tenant_id)` signature.
