# Analytics Domain — Canonical Software Literature

**Domain:** analytics
**Generated:** 2026-01-31
**Reference:** PIN-497
**Total Files:** 47 (22 L5_engines, 9 L6_drivers, 2 L5_schemas, 2 adapters, __init__.py files)

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

### alert_worker_engine.py *(NEW — PIN-520)*
- **Layer:** L5 — Analytics (Engine)
- **Role:** Alert worker engine - orchestrates alert delivery
- **Classes:** `AlertWorkerEngine`
- **Factory:** `get_alert_worker(alertmanager_url, max_backoff_seconds, timeout_seconds)`
- **Wires:** `AlertDriver` (L6 via context manager), `AlertDeliveryAdapter` (hoc_spine service)
- **PIN-512 Compliant:** No session parameters — driver manages own session via context manager
- **Methods:**
  - `process_batch(batch_size)` — Process pending alerts
  - `get_queue_stats()` — Get queue statistics
  - `retry_failed_alerts(max_retries)` — Reset failed alerts
  - `purge_old_alerts(days, statuses)` — Delete old alerts
- **Business Logic:**
  - Exponential backoff calculation (2^attempts, capped at max_backoff)
  - Retry decision logic (max attempts check)
  - Dead letter handling (mark as failed after max attempts)

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

## PIN-518 Analytics Storage Follow-ups (2026-02-03)

Audit of analytics storage wiring revealed 3 authority gaps. All fixed.

### Gap 1: L2→L6 Bypass Fixed

**Problem:** `api/cus/analytics/costsim.py` `/canary/reports` endpoint was calling `provenance_driver` directly (L2→L6 bypass, violates layer topology).

**Fix:** Route through L4 handler via OperationRegistry.

| Layer | File | Change |
|-------|------|--------|
| L2 | `api/cus/analytics/costsim.py` | Now calls `registry.execute("analytics.canary_reports", ctx)` |
| L4 | `hoc_spine/orchestrator/handlers/analytics_handler.py` | Added `CanaryReportHandler` class |

**L4 Handler Registration:**
```python
class CanaryReportHandler:
    """L4 handler for canary report operations."""
    async def execute(self, ctx: OperationContext) -> OperationResult:
        # Routes list and get methods to canary_report_driver
```

### Gap 2: Provenance/Canary Authority Split

**Problem:** `provenance_driver.py` handled both provenance and canary reports (authority blur — two distinct concerns in single driver).

**Fix:** Split into separate drivers with single responsibility.

| Layer | File | Purpose |
|-------|------|---------|
| L6 | `L6_drivers/provenance_driver.py` | Provenance logging only |
| L6 | `L6_drivers/canary_report_driver.py` *(NEW)* | Canary report persistence |

**canary_report_driver.py Methods:**
- `write_canary_report(session, report)` — Persist canary report
- `query_canary_reports(session, tenant_id, filters)` — Query with filters
- `get_canary_report_by_run_id(session, tenant_id, run_id)` — Get by run ID

### Gap 3: Artifact-Before-DB Invariant Guard

**Problem:** `canary_engine.py` could persist reports to DB without artifacts being written first (missing invariant guard).

**Fix:** Added explicit invariant check in `_persist_report_to_db()`.

| Layer | File | Change |
|-------|------|--------|
| L5 | `L5_engines/canary_engine.py` | Added artifact-before-DB guard |

**Guard Implementation:**
```python
async def _persist_report_to_db(self, report: CanaryReport) -> None:
    if self.config.save_artifacts and not report.artifact_paths:
        raise RuntimeError(
            "Canary artifacts missing; refusing DB write. "
            "Write artifacts first via _write_artifacts()."
        )
```

### Updated L4 Handler Operations

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| analytics.query | AnalyticsQueryHandler | AnalyticsFacade |
| analytics.detection | AnalyticsDetectionHandler | DetectionFacade |
| analytics.canary_reports | CanaryReportHandler | canary_report_driver |
| analytics.canary | CanaryRunHandler | CanaryCoordinator *(PIN-520)* |
| analytics.prediction | AnalyticsPredictionHandler | prediction_engine *(PIN-520)* |
| analytics.snapshot | AnalyticsSnapshotHandler | cost_snapshots_engine *(PIN-520)* |

---

## PIN-520 Wiring Audit (2026-02-03)

### Zero-Caller Components Wired

**Problem:** 5 orphaned components with zero callers identified during wiring audit.

**Solution:** All 5 components wired to proper export/import paths.

| Component | Type | Wired To | Status |
|-----------|------|----------|--------|
| CanaryCoordinator | L4 Coordinator | `analytics.canary` operation via `CanaryRunHandler` | WIRED |
| ExecutionCoordinator | L4 Coordinator | `CoordinatedJobExecutor` via `job_executor.py` | WIRED |
| ReplayCoordinator | L4 Coordinator | `logs.replay` operation via `LogsReplayHandler` | WIRED |
| AlertDeliveryAdapter | hoc_spine Service | `alert_worker_engine.py` via factory | WIRED |
| DiscoveryLedger | hoc_spine Driver | `activity.discovery` operation via `ActivityDiscoveryHandler` | WIRED |

### Alert Worker L5→L6→Service Wiring

```
AlertWorkerEngine (L5)
    ├── AlertDriver (L6) — DB operations via context manager
    │       ├── fetch_pending_alerts()
    │       ├── update_alert_sent()
    │       ├── update_alert_failed()
    │       ├── update_alert_retry()
    │       ├── mark_incident_alert_sent()
    │       ├── fetch_queue_stats()
    │       ├── retry_failed_alerts()
    │       └── purge_old_alerts()
    └── AlertDeliveryAdapter (Service) — HTTP delivery
            └── send_alert(payload) → DeliveryResult
```

### Operation Registry Total

**Total operations:** 44 (up from 42 pre-PIN-520)

## PIN-521 Config/Metrics Extraction (2026-02-03)

### Extracted to hoc_spine/services

**Problem:** `controls/L6_drivers/circuit_breaker_async_driver.py` imported from `analytics/L5_engines/config_engine.py` and `metrics_engine.py`, violating L6→L5_engines ban and cross-domain rules.

**Solution:** CostSimConfig and CostSimMetrics moved to `hoc_spine/services/` as domain-agnostic shared services.

| Component | Old Location | New Location |
|-----------|--------------|--------------|
| `CostSimConfig` | `analytics/L5_engines/config_engine.py` | `hoc_spine/services/costsim_config.py` |
| `get_config()` | `analytics/L5_engines/config_engine.py` | `hoc_spine/services/costsim_config.py` |
| `CostSimMetrics` | `analytics/L5_engines/metrics_engine.py` | `hoc_spine/services/costsim_metrics.py` |
| `get_metrics()` | `analytics/L5_engines/metrics_engine.py` | `hoc_spine/services/costsim_metrics.py` |

**Migration:**
```python
# OLD (violates L6→L5_engines ban)
from app.hoc.cus.analytics.L5_engines.config_engine import get_config
from app.hoc.cus.analytics.L5_engines.metrics_engine import get_metrics

# NEW (compliant)
from app.hoc.cus.hoc_spine.services.costsim_config import get_config
from app.hoc.cus.hoc_spine.services.costsim_metrics import get_metrics
```

**Backward Compatibility:** Original files in `analytics/L5_engines/` re-export from `hoc_spine/services/` for existing callers.

### Updated: L5_engines/config_engine.py

Now a backward-compatibility re-export file. Canonical home: `hoc_spine/services/costsim_config.py`.

### Updated: L5_engines/metrics_engine.py

Now a backward-compatibility re-export file. Canonical home: `hoc_spine/services/costsim_metrics.py`. Alert rules YAML kept in analytics for domain specificity.
