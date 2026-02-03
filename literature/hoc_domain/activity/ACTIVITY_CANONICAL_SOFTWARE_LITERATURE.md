# Activity Domain — Canonical Software Literature

**Domain:** activity
**Physical Files:** 16 (9 L5_engines + 4 L6_drivers + 2 `__init__.py` + 1 deprecated)
**Traced Scripts:** 13 (in call graph)
**Total LOC:** ~2,800
**Consolidation Date:** 2026-01-31
**Generator:** Manual analysis + domain inventory
**Status:** CONSOLIDATED — naming violations fixed, wiring violations deferred

---

## Table of Contents

1. [Domain Architecture](#1-domain-architecture)
2. [Script Inventory (16 files)](#2-script-inventory-16-files)
3. [Canonical Function Registry](#3-canonical-function-registry)
4. [Naming Violations Fixed](#4-naming-violations-fixed)
5. [Architecture Violations](#5-architecture-violations)
6. [Stub Engines](#6-stub-engines)
7. [Cross-Domain Dependencies](#7-cross-domain-dependencies)
8. [Legacy Dependencies](#8-legacy-dependencies)
9. [L4 Wiring](#9-l4-wiring)
10. [External Callers](#10-external-callers)
11. [Lessons Learned](#11-lessons-learned)

---

## 1. Domain Architecture

```
                    ┌──────────────────────────┐
                    │  L2 API (activity.py)     │
                    │  (via facades)            │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  L4 hoc_spine             │
                    │  activity_handler.py      │
                    │  5 operation types        │
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │            L5 ENGINES (9 files)              │
          │                                              │
          │  FACADE         │ activity_facade (main)    │
          │  ORCHESTRATION  │ run_governance_facade     │
          │  ENUMS          │ activity_enums            │
          │  SIGNAL         │ signal_identity           │
          │  STUB ENGINES   │ attention_ranking_engine  │
          │                 │ cost_analysis_engine      │
          │                 │ pattern_detection_engine  │
          │                 │ signal_feedback_engine    │
          │  RE-EXPORT      │ cus_telemetry_engine      │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │            L6 DRIVERS (4 files)              │
          │                                              │
          │  activity_read_driver        (READ)         │
          │  run_signal_driver           (WRITE)        │
          │  orphan_recovery_driver      (READ+WRITE)   │
          │  llm_threshold_service.py.deprecated (DEP)  │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │  CROSS-DOMAIN IMPORTS (controls)             │
          │  threshold_engine        (L5 controls)       │
          │  threshold_driver        (L6 controls)       │
          └─────────────────────────────────────────────┘
```

**Key Characteristics:**
- **Main Entry Point:** `activity_facade.py` — 15+ async methods, 18 dataclasses
- **5 L4 Operations:** activity.query, activity.signal_fingerprint, activity.signal_feedback, activity.telemetry, activity.discovery (PIN-520)
- **Cross-Domain Pattern:** L6 control → L5 control → L4 runtime → L5 activity → L6 activity
- **4 Stub Engines:** Attention ranking, cost analysis, pattern detection, signal feedback (all need ideal contractor)

---

## 2. Script Inventory (16 files)

### L5 Engines (9 files)

| # | File | Class/Functions | Role | LOC | Methods | Dependencies |
|---|------|-----------------|------|-----|---------|--------------|
| 1 | `__init__.py` | — (package init) | SUPPORT | ~15 | — | Re-exports from threshold_engine, activity_facade, run_governance_facade |
| 2 | `activity_enums.py` | SignalType, SeverityLevel, RunState, RiskType, EvidenceHealth | ENUMS | ~120 | Converters: severity_from_string, severity_to_int | None (pure data) |
| 3 | `activity_facade.py` | ActivityFacade (singleton) | FACADE | ~850 | 15+ async methods: get_runs, get_run_detail, get_run_evidence, get_run_proof, get_status_summary, get_live_runs, get_completed_runs, get_signals, get_metrics, get_threshold_signals, get_risk_signals, get_patterns, get_cost_analysis, get_attention_queue, acknowledge_signal, suppress_signal | ActivityReadDriver (L6), PatternDetectionService, CostAnalysisService, AttentionRankingService, SignalFeedbackService, signal_identity |
| 4 | `attention_ranking_engine.py` | AttentionRankingService | STUB_ENGINE | ~80 | get_attention_queue (stub), compute_attention_score (formula: severity*0.4 + recency*0.3 + frequency*0.3) | None (pure logic) |
| 5 | `cost_analysis_engine.py` | CostAnalysisService | STUB_ENGINE | ~95 | analyze_costs (stub), get_cost_breakdown (stub) | None (pure logic) |
| 6 | `cus_telemetry_engine.py` | CusTelemetryEngine: telemetry ingestion, queries, aggregation (384 lines). Rewired from legacy 2026-02-02 (PIN-512 Cat-B). | CANONICAL | ~384 | ingest, batch_ingest, query_telemetry, aggregate, get_summary | CusTelemetryDriver (L6) |
| 7 | `pattern_detection_engine.py` | PatternDetectionService | STUB_ENGINE | ~110 | detect_patterns (stub), get_pattern_detail (stub) | None (pure logic) |
| 8 | `signal_feedback_engine.py` | SignalFeedbackService | STUB_ENGINE | ~130 | acknowledge_signal, suppress_signal, get_signal_feedback_status, get_bulk_signal_feedback (all stubs) | None (pure logic) |
| 9 | `signal_identity.py` | compute_signal_fingerprint_from_row, compute_signal_fingerprint | PURE_COMPUTATION | ~45 | sha256[:32] fingerprinting | None (hashlib only) |

**18 Dataclasses in activity_facade.py:**
PolicyContextResult, RunSummaryResult, RunSummaryV2Result, RunListResult, RunsResult, RunDetailResult, RunEvidenceResult, RunProofResult, StatusCount, StatusSummaryResult, SignalProjectionResult, SignalsResult, MetricsResult, ThresholdSignalResult, ThresholdSignalsResult, RiskSignalsResult, LiveRunsResult (alias), CompletedRunsResult (alias)

### L6 Drivers (4 files + 1 deprecated)

| # | File | Class | Tables | LOC | Methods |
|---|------|-------|--------|-----|---------|
| 10 | `__init__.py` | — (package init) | — | ~15 | Re-exports from controls/threshold_driver: LimitSnapshot, ThresholdDriver, ThresholdDriverSync, emit_and_persist_threshold_signal, emit_threshold_signal_sync |
| 11 | `activity_read_driver.py` | ActivityReadDriver(session) | v_runs_o2 (READ) | ~380 | count_runs, fetch_runs, fetch_run_detail, fetch_status_summary, fetch_runs_with_policy_context, fetch_at_risk_runs, fetch_metrics, fetch_threshold_signals |
| 12 | `orphan_recovery_driver.py` | detect_orphaned_runs, mark_run_as_crashed, recover_orphaned_runs, get_crash_recovery_summary | WorkerRun (READ+WRITE) | ~280 | PB-S2 truth guarantee. Renamed from orphan_recovery.py (2026-01-31) |
| 13 | `run_signal_driver.py` | RunSignalDriver(session) | WorkerRun (WRITE) | ~150 | update_risk_level(run_id, signals), get_risk_level(run_id). SIGNAL_TO_RISK_LEVEL mapping. Backward alias: RunSignalService |
| 14 | `llm_threshold_service.py.deprecated` | — (deprecated) | — | — | DEPRECATED file, not active |

_Tables: v_runs_o2 is a view; WorkerRun owned by activity domain._

---

## 3. Canonical Function Registry

Each script's identity-defining function — the one that makes this script uniquely necessary.

| # | Script | Canonical Function | Status |
|---|--------|--------------------|--------|
| 1 | activity_enums | SignalType, SeverityLevel enums | CANONICAL (domain vocabulary) |
| 2 | activity_facade | `ActivityFacade.get_runs` | CANONICAL (main facade) |
| 3 | attention_ranking_engine | `AttentionRankingService.compute_attention_score` | STUB (needs ideal contractor) |
| 4 | cost_analysis_engine | `CostAnalysisService.analyze_costs` | STUB (needs ideal contractor) |
| 5 | cus_telemetry_engine | `CusTelemetryEngine.ingest` | CANONICAL (rewired from legacy, PIN-512 Cat-B) |
| 6 | pattern_detection_engine | `PatternDetectionService.detect_patterns` | STUB (needs ideal contractor) |
| 7 | signal_feedback_engine | `SignalFeedbackService.acknowledge_signal` | STUB (needs ideal contractor) |
| 8 | signal_identity | `compute_signal_fingerprint` | CANONICAL (pure computation) |
| 9 | activity_read_driver | `ActivityReadDriver.fetch_runs` | CANONICAL (persistence) |
| 10 | orphan_recovery_driver | `detect_orphaned_runs` | CANONICAL (PB-S2 truth) |
| 11 | run_signal_driver | `RunSignalDriver.update_risk_level` | CANONICAL (signal→risk mapping) |

---

## 4. Naming Violations Fixed

**Consolidation Date:** 2026-01-31

| # | Violation | Was | Fixed To | Backward Compatibility |
|---|-----------|-----|----------|------------------------|
| N1 | L6 class named `*Service` | `run_signal_service.py` → class `RunSignalService` | `run_signal_driver.py` → class `RunSignalDriver` + alias `RunSignalService = RunSignalDriver` | YES (alias preserved) |
| N2 | L5 file named `*_service.py` | `cus_telemetry_service.py` | `cus_telemetry_engine.py` (header updated, L4 handler import updated) | YES (re-export maintained) |
| N3 | L6 file missing `_driver` suffix | `orphan_recovery.py` | `orphan_recovery_driver.py` (header updated) | YES (function names unchanged) |

**Verification Status:** All naming violations resolved. File headers updated. L4 handler imports verified.

---

## 5. Architecture Violations

### V1: Cross-domain L6→L6 import (MEDIUM)

**Location:** `controls/L6_drivers/threshold_driver.py` → `activity/L6_drivers/run_signal_driver.py`
**Violation:** Controls L6 driver imports activity L6 driver directly.
**Topology Rule:** Cross-domain access MUST go through L4 spine, never direct L6→L6.

```
CURRENT (WRONG):                    CORRECT (per HOC Topology V2.0.0):
controls/L6 threshold_driver         controls/L6 threshold_driver
    │                                    │
    ▼ VIOLATION                          ▼
activity/L6 run_signal_driver        controls/L5 threshold_engine
                                         │
                                         ▼
                                     L4 hoc_spine (activity.signal_risk)
                                         │
                                         ▼
                                     activity/L5 signal_risk_engine (NEW)
                                         │
                                         ▼
                                     activity/L6 run_signal_driver
```

**Fix:** Controls domain should call through L4 spine, which routes to activity L5 engine, which delegates to L6 driver. This maintains the layer topology: L6 control → L5 control → L4 → L5 activity → L6 activity.

**Status:** DEFERRED — wiring exercise post-all-domain consolidation.

### V2: Legacy dependency (LOW)

**Location:** `cus_telemetry_engine.py` imports from `app.services.cus_telemetry_engine`
**Issue:** HOC layer importing from legacy `app.services` location.
**Topology Rule:** HOC layer should not depend on legacy service layer.

**Fix:** Post-all-domain, perform ideal contractor analysis: Does telemetry belong in activity domain, or does it need its own domain? Currently a re-export stub maintaining backward compatibility.

**Status:** DEFERRED — ideal contractor analysis post-all-domain.

---

## 6. Stub Engines

**4 Stub Engines** — all return mock/empty data, need ideal contractor analysis:

| # | Engine | Dataclasses | Methods | Current Behavior | Ideal State |
|---|--------|-------------|---------|------------------|-------------|
| 1 | `attention_ranking_engine.py` | AttentionSignal, AttentionQueueResult | get_attention_queue (stub → empty), compute_attention_score (formula) | Returns empty queue | Real attention ranking based on severity, recency, frequency |
| 2 | `cost_analysis_engine.py` | CostAnomaly, CostAnalysisResult | analyze_costs (stub), get_cost_breakdown (stub) | Returns empty results | Real cost analysis from analytics domain |
| 3 | `pattern_detection_engine.py` | DetectedPattern, PatternDetectionResult | detect_patterns (stub), get_pattern_detail (stub) | Returns empty patterns | Real pattern detection across runs |
| 4 | `signal_feedback_engine.py` | AcknowledgeResult, SuppressResult, SignalFeedbackStatus | acknowledge_signal, suppress_signal, get_signal_feedback_status, get_bulk_signal_feedback | Returns mock success | Real signal acknowledgment persistence |

**Ideal Contractor Questions:**
1. Should attention ranking call analytics domain for real-time metrics?
2. Should cost analysis be a cross-domain query to analytics + activity?
3. Should pattern detection use ML models or rule-based heuristics?
4. Should signal feedback persist to a dedicated `signal_feedback` table?

**Wiring Impact:** All 4 stubs are called only by `activity_facade.py`. Facade already has delegation pattern in place. Upgrading stubs to real engines requires only L6 driver creation + L5 engine implementation, no L4 changes.

---

## 7. Cross-Domain Dependencies

### Activity imports from controls domain

| # | Activity File | Imports From Controls | Purpose |
|---|---------------|----------------------|---------|
| 1 | ~~`L5_engines/__init__.py`~~ | ~~`controls/L5_engines/threshold_engine`~~ | **RESOLVED** (PIN-504 Phase 6): Re-export block deleted, zero callers |
| 2 | `L6_drivers/__init__.py` | `controls/L6_drivers/threshold_driver` | LimitSnapshot, ThresholdDriver, ThresholdDriverSync, emit_and_persist_threshold_signal, emit_threshold_signal_sync |

### Controls imports from activity domain

| # | Controls File | Imports From Activity | Purpose |
|---|---------------|----------------------|---------|
| 1 | `controls/L6_drivers/threshold_driver.py` | `activity/L6_drivers/run_signal_driver` | RunSignalDriver.update_risk_level (VIOLATION V1) |

**Cross-Domain Pattern:** L6 control → L5 control → L4 runtime → L5 activity → L6 activity

**Violation:** Controls L6 bypasses this pattern and imports activity L6 directly (V1).

---

## 8. Legacy Dependencies

| # | File | Legacy Import | Purpose | Status |
|---|------|---------------|---------|--------|
| 1 | `cus_telemetry_engine.py` | `from app.services.cus_telemetry_engine import ...` | Re-export HOC aliases for telemetry service | DEFERRED — ideal contractor post-all-domain |

**Analysis:** `cus_telemetry_engine.py` is a re-export bridge. The real implementation lives in `app/services/cus_telemetry_engine.py` (legacy location). Post-all-domain, ideal contractor analysis should determine:
1. Does telemetry belong in activity domain?
2. Should it be a separate telemetry domain?
3. Should it be platform infrastructure?

---

## 9. L4 Wiring

### L4 Handler: `hoc_spine/orchestrator/handlers/activity_handler.py`

**5 Handler Classes:**

| # | Operation Name | Handler Class | Target | Status |
|---|----------------|---------------|--------|--------|
| 1 | `activity.query` | ActivityQueryHandler | ActivityFacade (L5) | WIRED |
| 2 | `activity.signal_fingerprint` | ActivitySignalFingerprintHandler | signal_identity (L5) | WIRED |
| 3 | `activity.signal_feedback` | ActivitySignalFeedbackHandler | SignalFeedbackService (L5) | WIRED (stub) |
| 4 | `activity.telemetry` | ActivityTelemetryHandler | CusTelemetryService (L5) | WIRED (re-export) |
| 5 | `activity.discovery` | ActivityDiscoveryHandler | Discovery Ledger (hoc_spine driver) | WIRED (PIN-520) |

### activity.discovery Methods (PIN-520)

| Method | Purpose |
|--------|---------|
| `emit_signal` | Record a discovery signal (aggregates duplicates by artifact+field+signal_type) |
| `get_signals` | Query discovery signals from the ledger |

**Call Pattern:**
```
L2 API → L4 handler.handle(operation, args)
       → L5 facade/engine method(args)
       → L6 driver.fetch/persist
       → L7 model (ORM)
```

**Verification Status:** All 5 operations registered and callable. L4→L5 delegation confirmed.

### External Callers

| # | Caller File | Imports From Activity | Purpose | Status |
|---|-------------|----------------------|---------|--------|
| 1 | `int/agent/main.py` | `from .services.orphan_recovery import recover_orphaned_runs` | Orphan run recovery (legacy path) | LEGACY PATH (should route through L4) |
| 2 | `hoc/api/cus/activity/activity.py` | ActivityFacade | L2 API endpoints | WIRED |
| 3 | Various L5 engines | activity_enums (SignalType, SeverityLevel) | Shared domain vocabulary | WIRED |

**Legacy Path Issue:** `int/agent/main.py` imports from `.services.orphan_recovery` (legacy path). Should be updated to call through L4 spine: `hoc_spine.orchestrate("activity.orphan_recovery", args)`.

**Status:** DEFERRED — wiring exercise post-all-domain.

### L4 Coordinators: Run Introspection (PIN-519)

**New L4 Coordinators:** 3 coordinators added for cross-domain run queries.

| Coordinator | File | Purpose | Bridges Used |
|-------------|------|---------|--------------|
| RunEvidenceCoordinator | `run_evidence_coordinator.py` | Cross-domain impact (incidents, policies, limits) | IncidentsBridge, PoliciesBridge, ControlsBridge |
| RunProofCoordinator | `run_proof_coordinator.py` | Integrity verification (HASH_CHAIN) | LogsBridge |
| SignalFeedbackCoordinator | `signal_feedback_coordinator.py` | Audit ledger feedback queries | LogsBridge |

**Activity Facade Delegation (PIN-519):**

| Method | Coordinator | Status |
|--------|-------------|--------|
| `get_run_evidence()` | RunEvidenceCoordinator | WIRED |
| `get_run_proof()` | RunProofCoordinator | WIRED |
| `_get_signal_feedback()` | SignalFeedbackCoordinator | WIRED |

**Red-Line Compliance:**
- Activity L5 delegates cross-domain queries to L4 coordinators (no direct imports)
- Integrity computation happens in L4, not L5
- All verification states explicit (VERIFIED | FAILED | UNSUPPORTED)

---

## 10. External Callers

Complete map of all files outside activity domain that call into it.

| # | Layer | File | Imports From Activity | Status |
|---|-------|------|----------------------|--------|
| 1 | L4 spine | `activity_handler.py` | `activity_facade`, `signal_identity`, etc. | WIRED |
| 2 | L2 HOC API | `hoc/api/cus/activity/activity.py` | `ActivityFacade` | WIRED |
| 3 | L5 controls | `threshold_engine.py` | activity_enums (SignalType, SeverityLevel) | WIRED (enums) |
| 4 | L6 controls | `threshold_driver.py` | `run_signal_driver` (RunSignalDriver) | VIOLATION V1 |
| 5 | int/agent | `main.py` | orphan_recovery (legacy path) | LEGACY PATH |
| 6 | Various | Multiple | activity_enums (shared vocabulary) | WIRED |

---

## 11. Lessons Learned

Patterns to apply when consolidating subsequent domains:

### L1: Re-export stubs are valid transition artifacts

`cus_telemetry_engine.py` is a re-export stub that bridges HOC layer to legacy `app.services`. This is a valid architectural pattern during migration. Re-export stubs should be:
1. Clearly documented as "RE-EXPORT" in role classification
2. Marked with legacy dependency comments
3. Scheduled for ideal contractor analysis post-all-domain

### L2: Stub engines need clear dataclass definitions

All 4 stub engines define dataclasses even though they return mock data. This is CORRECT — dataclasses define the contract for future real implementations. Upgrading a stub to a real engine should only require:
1. Create L6 driver (if persistence needed)
2. Implement L5 engine methods (replace stub logic)
3. No L4 handler changes (delegation already in place)

### L3: Cross-domain L6→L6 is the most common violation

Controls L6 importing activity L6 directly (V1) is a common pattern that violates HOC Topology V2.0.0. The correct fix is always:
```
SOURCE DOMAIN L6 → SOURCE DOMAIN L5 → L4 spine → TARGET DOMAIN L5 → TARGET DOMAIN L6
```

### L4: Naming conventions enforce layer discipline

Renaming `run_signal_service.py` → `run_signal_driver.py` (N1) makes layer membership explicit. File name patterns (`*_driver`, `*_engine`, `*_facade`) are not just conventions — they enforce layer topology and prevent misclassification.

### L5: Pure computation functions belong in separate files

`signal_identity.py` is a perfect example: pure functions (no dependencies, no state, no I/O) in a separate file. This makes the computation reusable across L4 handlers, L5 engines, and even L6 drivers without circular dependencies.

### L6: Enums are domain vocabulary, not infrastructure

`activity_enums.py` defines `SignalType`, `SeverityLevel`, `RunState`, etc. These are imported by controls domain, analytics domain, and others. Enums are CANONICAL domain vocabulary, not shared infrastructure. Each domain owns its enums; other domains import them as cross-domain dependencies (allowed).

### L7: Backward compatibility aliases prevent wiring breaks

`RunSignalService = RunSignalDriver` (N1 fix) preserves backward compatibility. When renaming classes for layer compliance, always add an alias for the old name. Remove alias only after confirming no external callers remain.

---

## Verification

```bash
# File count verification
ls -1 backend/app/hoc/cus/activity/L5_engines/*.py | wc -l
# Expected: 9 (including __init__.py)

ls -1 backend/app/hoc/cus/activity/L6_drivers/*.py | wc -l
# Expected: 5 (including __init__.py and deprecated file)

# Naming violation check (should return 0 matches)
grep -r "class.*Service" backend/app/hoc/cus/activity/L6_drivers/*.py | grep -v "# Backward"
# Expected: 0 matches (all L6 classes use "Driver" suffix)

# Cross-domain L6→L6 violation check
grep -r "from.*activity.*L6_drivers" backend/app/hoc/cus/controls/
# Expected: 1 match (threshold_driver.py → run_signal_driver, known V1)

# Stub engine verification
grep -A 3 "def get_attention_queue" backend/app/hoc/cus/activity/L5_engines/attention_ranking_engine.py
# Expected: Returns empty list (stub behavior)
```

**Status:** CONSOLIDATED — All naming violations fixed. Architecture violations documented and deferred.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat B: Legacy Import Disconnected (1)

| File | Old Import | New State |
|------|-----------|-----------|
| `L5_engines/cus_telemetry_engine.py` line 44 | `from app.services.cus_telemetry_engine import BatchIngestResult, CusTelemetryEngine, IngestResult, get_cus_telemetry_engine` | DISCONNECTED — stub classes with NotImplementedError, TODO rewire |

Re-export bridge replaced with stub dataclasses (`IngestResult`, `BatchIngestResult`) and stub `CusTelemetryEngine` class. Methods raise `NotImplementedError` until HOC-native implementation is wired. Factory `get_cus_telemetry_engine()` returns stub instance.

### Cat B: Stale Docstring References Corrected (1)

| File | Old Docstring Reference | New Docstring Reference |
|------|------------------------|------------------------|
| `L5_engines/cus_telemetry_engine.py` | `Re-exports from existing cus_telemetry_engine.py` | `Legacy import disconnected (PIN-503)` |

### Cat D: L2→L5 Bypass Violations (0)

No L2→L5 bypasses in activity domain.

### Cat E: Cross-Domain L5→L5/L6 Violations (Inbound — 1 — DOCUMENT ONLY)

| Source File | Source Domain | Import Target |
|------------|--------------|--------------|
| `controls/L6_drivers/threshold_driver.py` | controls | `activity.L6_drivers.run_signal_driver` |

**Deferred:** Requires L4 Coordinator to mediate cross-domain signal writes.

### Cat E: Cross-Domain L5→L5/L6 Violations (Outbound — 1 → 0 — RESOLVED)

| Source File | Old Import | Resolution |
|------------|-----------|-----------|
| `activity/L5_engines/__init__.py` | 12 symbols from `controls.L5_engines.threshold_engine` | **RESOLVED** (PIN-504 Phase 6): Deleted re-export block. Zero callers used this path. |

**Note:** `activity/L6_drivers/__init__.py` re-export of controls threshold types was resolved in PIN-504 Phase 3 (SignalCoordinator).

### Tally

31/31 checks PASS (27 consolidation + 4 cleansing).


---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-508 Stub Classification (2026-02-01)

### STUB_ENGINE Marker Added (Phase 5)

| # | File | Marker | Purpose |
|---|------|--------|---------|
| 1 | `L5_engines/cus_telemetry_engine.py` | STUB_ENGINE | Legacy bridge to app.services.cus_telemetry_engine. Stub data classes (IngestResult, BatchIngestResult) with NotImplementedError. Scheduled for ideal contractor analysis post-all-domain consolidation. |

**Clarification:** `cus_telemetry_engine` is both a RE-EXPORT stub and a STUB_ENGINE. The distinction: RE-EXPORT indicates it bridges legacy code; STUB_ENGINE indicates the internal implementation is stubbed pending HOC-native replacement.

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-520 Wiring Audit (2026-02-03)

### Discovery Ledger Wiring

**Problem:** Discovery Ledger in `hoc_spine/drivers/ledger.py` had zero callers.

**Solution:** Wired to activity domain via `activity.discovery` operation.

| Component | Layer | Wired To | Purpose |
|-----------|-------|----------|---------|
| `emit_signal` | hoc_spine Driver | `activity.discovery` (method=emit_signal) | Record curiosity signals |
| `get_signals` | hoc_spine Driver | `activity.discovery` (method=get_signals) | Query discovery signals |

**Call Pattern:**
```
L2 API → registry.execute("activity.discovery", ctx)
       → ActivityDiscoveryHandler.execute(ctx)
       → emit_signal() or get_signals() from hoc_spine/drivers
       → DiscoverySignal model (ledger.py)
```

**Semantic Note:** Discovery Ledger records "curiosity, not decisions." Signals are aggregated: same (artifact, field, signal_type) updates `seen_count` instead of creating duplicates.

**Export Path:** `from app.hoc.cus.hoc_spine.drivers import emit_signal, get_signals`

## PIN-519 System Run Introspection (2026-02-03)

### Problem Solved

Three TODOs in `activity_facade.py` returned empty/stub data:
1. `get_run_evidence()` — returned empty shell
2. `get_run_proof()` — returned UNKNOWN integrity
3. Signal feedback in `get_signals()` — `feedback=None`

**Root Cause:** Activity L5 cannot answer cross-domain questions. These require L4 coordinators.

### Solution: L4 Coordinator Delegation

Activity facade now delegates to L4 coordinators for cross-domain queries:

| Facade Method | L4 Coordinator | Cross-Domain Sources |
|---------------|----------------|---------------------|
| `get_run_evidence()` | `RunEvidenceCoordinator` | incidents, policies, controls |
| `get_run_proof()` | `RunProofCoordinator` | logs (traces_store) |
| `_get_signal_feedback()` | `SignalFeedbackCoordinator` | logs (audit_ledger) |

### Call Pattern

```
ActivityFacade.get_run_evidence(session, tenant_id, run_id)
    → get_run_evidence_coordinator()
    → RunEvidenceCoordinator.get_run_evidence()
        → IncidentsBridge.incidents_for_run_capability()
        → PoliciesBridge.policy_evaluations_capability()
        → ControlsBridge.limit_breaches_capability()
    → RunEvidenceResult
```

### Result Types (from run_introspection_protocols.py)

| Type | Fields |
|------|--------|
| `RunEvidenceResult` | run_id, incidents_caused, policies_evaluated, limits_hit, decisions_made, computed_at |
| `RunProofResult` | run_id, integrity, aos_traces, aos_trace_steps, raw_logs, verified_at |
| `SignalFeedbackResult` | acknowledged, acknowledged_by, acknowledged_at, suppressed, suppressed_until, escalated, escalated_at |
| `IntegrityVerificationResult` | model, root_hash, chain_length, verification_status, failure_reason |

### Integrity Model

**Phase 1:** HASH_CHAIN — sequential SHA-256 hash of trace steps
**Future:** MERKLE_TREE — Merkle tree of trace evidence

```python
INTEGRITY_CONFIG = {
    "model": "HASH_CHAIN",
    "trust_boundary": "SYSTEM",
    "storage": "POSTGRES",
}
```

### Red-Line Compliance

- ✅ Activity L5 does not import other domains
- ✅ Activity L5 does not write data
- ✅ Activity L5 does not evaluate policy
- ✅ Activity L5 does not compute integrity (delegated to coordinator)
- ✅ All cross-domain queries go through L4 coordinators
