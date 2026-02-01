# Incidents Domain — Canonical Software Literature

**Domain:** incidents
**Physical Files:** 30 (17 L5_engines + 11 L6_drivers + 2 adapters)
**Traced Scripts:** 27 (in call graph)
**Total LOC:** ~8,200
**Consolidation Date:** 2026-01-31
**Generator:** Manual analysis + `hoc_software_bible_generator.py` + `hoc_incidents_tally.py`
**Status:** CONSOLIDATED — pending freeze

---

## Table of Contents

1. [Domain Architecture](#1-domain-architecture)
2. [Script Inventory (30 files)](#2-script-inventory-30-files)
3. [Canonical Function Registry](#3-canonical-function-registry)
4. [Duplicate Analysis](#4-duplicate-analysis)
5. [Uncalled Functions](#5-uncalled-functions)
6. [Architecture Violations](#6-architecture-violations)
7. [Missing L4 Wiring](#7-missing-l4-wiring)
8. [Cross-Domain Dependencies](#8-cross-domain-dependencies)
9. [External Callers](#9-external-callers)
10. [Lessons Learned](#10-lessons-learned)

---

## 1. Domain Architecture

```
                    ┌──────────────────────────┐
                    │  L2 API (incidents.py)    │
                    │  22 endpoints             │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  L4 hoc_spine             │
                    │  incidents_handler.py     │
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │            L5 ENGINES (17 files)             │
          │                                              │
          │  FACADE         │ incidents_facade           │
          │  ORCHESTRATION  │ incident_driver            │
          │  DECISION       │ incident_engine            │
          │                 │ incident_severity_engine    │
          │  POLICY         │ prevention_engine           │
          │                 │ policy_violation_engine     │
          │  RECOVERY       │ recovery_rule_engine        │
          │  DETECTION      │ hallucination_detector      │
          │                 │ llm_failure_engine           │
          │                 │ semantic_failures            │
          │  ANALYSIS       │ postmortem_engine            │
          │                 │ incident_pattern_engine      │
          │                 │ recurrence_analysis_engine   │
          │  BRIDGE         │ anomaly_bridge               │
          │  READ/WRITE     │ incident_read_engine         │
          │                 │ incident_write_engine         │
          │  SUPPORT        │ incidents_types               │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │            L6 DRIVERS (11 files)             │
          │                                              │
          │  incident_read_driver        (READ)          │
          │  incident_write_driver       (WRITE)         │
          │  incidents_facade_driver     (READ)          │
          │  incident_aggregator         (READ+WRITE)    │
          │  incident_pattern_driver     (READ)          │
          │  postmortem_driver           (READ)          │
          │  recurrence_analysis_driver  (READ)          │
          │  export_bundle_driver        (READ)          │
          │  lessons_driver              (READ+WRITE)    │
          │  llm_failure_driver          (READ+WRITE)    │
          │  policy_violation_driver     (READ+WRITE)    │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │  ADAPTERS (2 files)                          │
          │  customer_incidents_adapter (CUSTOMER)       │
          │  founder_ops_adapter        (FOUNDER)        │
          └─────────────────────────────────────────────┘
```

---

## 2. Script Inventory (30 files)

### L5 Engines (17 files)

| # | File | Class | Role | LOC | Decisions | Methods | DB Access |
|---|------|-------|------|-----|-----------|---------|-----------|
| 1 | `anomaly_bridge.py` | AnomalyIncidentBridge | PATTERN_ANALYSIS | ~280 | 3 | ingest, _meets_severity_threshold, _is_suppressed, _check_existing_incident | Delegates to incident_write_driver (PIN-508 Phase 1B) |
| 2 | `hallucination_detector.py` | HallucinationDetector | DETECTION | ~468 | 6 | detect, _detect_suspicious_urls, _detect_suspicious_citations, _detect_contradictions, _detect_temporal_issues, _hash_content | None (pure logic) |
| 3 | `incident_driver.py` | IncidentDriver | ORCHESTRATION | ~280 | 1 | create_incident_for_run, check_and_create_incident, get_incidents_for_run, _emit_ack | Delegates to incident_engine |
| 4 | `incident_engine.py` | IncidentEngine | DECISION_ENGINE | ~906 | 6 | create_incident_for_run, create_incident_for_failed_run, check_and_create_incident, create_incident_for_all_runs, _check_policy_suppression, _write_prevention_record, _maybe_create_policy_proposal, _generate_title, _extract_error_code, get_incidents_for_run | Delegates to incident_write_driver |
| 5 | `incident_pattern_engine.py` | IncidentPatternService | PATTERN_ANALYSIS | ~280 | 0 | detect_patterns, _detect_category_clusters, _detect_severity_spikes, _detect_cascade_failures | Delegates to incident_pattern_driver |
| 6 | `incident_read_engine.py` | IncidentReadService | READ_SERVICE | ~154 | 0 | list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident | Delegates to incident_read_driver |
| 7 | `incident_severity_engine.py` | — (TOMBSTONE) | DELETED | — | — | — | DELETED per PIN-508 Phase 4B (logic moved to L5_schemas/severity_policy.py, zero dependents) |
| 8 | `incident_write_engine.py` | IncidentWriteService | WRITE_SERVICE | ~304 | 2 | acknowledge_incident, resolve_incident, manual_close_incident | Delegates to incident_write_driver + audit_ledger |
| 9 | `incidents_facade.py` | IncidentsFacade | FACADE | ~984 | 6 | list_active_incidents, list_resolved_incidents, list_historical_incidents, get_incident_detail, get_incidents_for_run, get_metrics, analyze_cost_impact, detect_patterns, analyze_recurrence, get_incident_learnings, _snapshot_to_summary | Delegates to incidents_facade_driver + sub-engines |
| 10 | `incidents_types.py` | — (type aliases) | SUPPORT | ~45 | 0 | — | None |
| 11 | `llm_failure_engine.py` | LLMFailureService | DETECTION | ~349 | 1 | persist_failure_and_mark_run, _persist_failure, _capture_evidence, _mark_run_failed, _verify_no_contamination, get_failure_by_run_id | Delegates to llm_failure_driver |
| 12 | `policy_violation_engine.py` | PolicyViolationService | POLICY | ~714 | 5 | persist_violation_fact, check_violation_persisted, check_policy_enabled, persist_evidence, check_incident_exists, create_incident_from_violation, persist_violation_and_create_incident, verify_violation_truth | Delegates to policy_violation_driver |
| 13 | `postmortem_engine.py` | PostMortemService | ANALYSIS | ~445 | 1 | get_incident_learnings, get_category_learnings, _get_resolution_summary, _find_similar_incidents, _extract_insights, _generate_category_insights | Delegates to postmortem_driver |
| 14 | `prevention_engine.py` | PreventionEngine + 5 validators | POLICY | ~891 | 6 | evaluate, _generate_safe_response, _emit_metrics; Validators: ContentAccuracyValidatorV2, PIIValidator, SafetyValidator, HallucinationValidator, BudgetValidator | Delegates to policy_violation_engine |
| 15 | `recovery_rule_engine.py` | RecoveryRuleEngine + 5 rule types | RECOVERY | ~803 | 4 | evaluate, add_rule, remove_rule; Rules: ErrorCodeRule, HistoricalPatternRule, SkillSpecificRule, OccurrenceThresholdRule, CompositeRule | None (pure logic) |
| 16 | `recurrence_analysis_engine.py` | RecurrenceAnalysisService | PATTERN_ANALYSIS | ~190 | 0 | analyze_recurrence, get_recurrence_for_category, _snapshot_to_group | Delegates to recurrence_analysis_driver |
| 17 | `semantic_failures.py` | — (functions + constants) | SUPPORT | ~299 | 0 | get_failure_info, get_fix_owner, get_fix_action, get_violation_class, format_violation_message | None (pure data) |

### L6 Drivers (11 files)

| # | File | Class | Tables | LOC | Methods |
|---|------|-------|--------|-----|---------|
| 18 | `incident_read_driver.py` | IncidentReadDriver | Incident, IncidentEvent (READ) | ~180 | list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident |
| 19 | `incident_write_driver.py` | IncidentWriteDriver | Incident, IncidentEvent, runs*, aos_traces*, prevention_records*, policy_proposals*, policy_rules* (READ+WRITE) | ~480 | insert_incident, insert_incident_from_anomaly, update_incident_acknowledged, update_incident_resolved, create_incident_event, refresh_incident, update_run_incident_count, update_trace_incident_id, insert_prevention_record, insert_policy_proposal, fetch_suppressing_policy, fetch_incidents_by_run_id |
| 20 | `incidents_facade_driver.py` | IncidentsFacadeDriver | Incident (READ) | ~400 | fetch_active_incidents, fetch_resolved_incidents, fetch_historical_incidents, fetch_incident_by_id, fetch_incidents_by_run, fetch_metrics_aggregates, fetch_cost_impact_data, _to_snapshot |
| 21 | `incident_aggregator.py` | IncidentAggregator | Incident, IncidentEvent (READ+WRITE) | ~380 | get_or_create_incident, resolve_stale_incidents, get_incident_stats, _find_open_incident, _can_create_incident, _get_rate_limit_incident, _create_incident, _add_call_to_incident, _add_incident_event |
| 22 | `incident_pattern_driver.py` | IncidentPatternDriver | incidents (READ) | ~200 | fetch_incidents_count, fetch_category_clusters, fetch_severity_spikes, fetch_cascade_failures |
| 23 | `postmortem_driver.py` | PostMortemDriver | incidents, incident_evidence (READ) | ~250 | fetch_category_stats, fetch_resolution_methods, fetch_recurrence_data, fetch_resolution_summary, fetch_similar_incidents |
| 24 | `recurrence_analysis_driver.py` | RecurrenceAnalysisDriver | incidents (READ) | ~150 | fetch_recurrence_groups, fetch_recurrence_for_category |
| 25 | `export_bundle_driver.py` | ExportBundleDriver | Incident, Run*, AosTrace* (READ) | ~430 | create_evidence_bundle, create_soc2_bundle, create_executive_debrief, _compute_bundle_hash, _generate_attestation, _assess_risk_level, _generate_incident_summary, _assess_business_impact, _generate_recommendations |
| 26 | `lessons_driver.py` | LessonsDriver | lessons_learned*, policy_proposals* (READ+WRITE) | ~350 | insert_lesson, fetch_lesson_by_id, fetch_lessons_list, fetch_lesson_stats, update_lesson_deferred, update_lesson_dismissed, update_lesson_converted, update_lesson_reactivated, fetch_debounce_count, fetch_expired_deferred, insert_policy_proposal_from_lesson |
| 27 | `llm_failure_driver.py` | LLMFailureDriver | run_failures, failure_evidence, worker_runs*, cost_records*, cost_anomalies* (READ+WRITE) | ~250 | insert_failure, insert_evidence, update_run_failed, fetch_failure_by_run_id, fetch_contamination_check |
| 28 | `policy_violation_driver.py` | PolicyViolationDriver | prevention_records*, policy_rules*, incidents, incident_events (READ+WRITE) | ~300 | insert_violation_record, fetch_violation_exists, fetch_policy_enabled, insert_evidence_event, fetch_incident_by_violation, fetch_violation_truth_check, insert_policy_evaluation; sync: insert_policy_evaluation_sync |

_Tables marked with * are owned by other domains (see Section 8)._

### Adapters (2 files)

| # | File | Class | Audience | LOC |
|---|------|-------|----------|-----|
| 29 | `customer_incidents_adapter.py` | CustomerIncidentsAdapter | CUSTOMER | ~399 |
| 30 | `founder_ops_adapter.py` | FounderOpsAdapter | FOUNDER | ~146 |

---

## 3. Canonical Function Registry

Each script's identity-defining function — the one that makes this script uniquely necessary.

| # | Script | Canonical Function | Status |
|---|--------|--------------------|--------|
| 1 | anomaly_bridge | `AnomalyIncidentBridge.ingest` | CANONICAL |
| 2 | hallucination_detector | `HallucinationDetector.detect` | CANONICAL |
| 3 | incident_driver | `IncidentDriver.create_incident_for_run` | CANONICAL (facade) |
| 4 | incident_engine | `IncidentEngine.create_incident_for_run` | CANONICAL (authority) |
| 5 | incident_pattern_engine | `IncidentPatternService.detect_patterns` | CANONICAL |
| 6 | incident_read_engine | `IncidentReadService.list_incidents` | INTERFACE |
| 7 | incident_severity_engine | — (DELETED) | TOMBSTONE (PIN-508 Phase 4B) |
| 8 | incident_write_engine | `IncidentWriteService.resolve_incident` | CANONICAL |
| 9 | incidents_facade | `IncidentsFacade.list_active_incidents` | CANONICAL |
| 10 | incidents_types | — (type aliases) | SUPPORT |
| 11 | llm_failure_engine | `LLMFailureService.persist_failure_and_mark_run` | CANONICAL |
| 12 | policy_violation_engine | `PolicyViolationService.persist_violation_and_create_incident` | CANONICAL |
| 13 | postmortem_engine | `PostMortemService.get_category_learnings` | CANONICAL |
| 14 | prevention_engine | `PreventionEngine.evaluate` | CANONICAL |
| 15 | recovery_rule_engine | `RecoveryRuleEngine.evaluate` | CANONICAL |
| 16 | recurrence_analysis_engine | `RecurrenceAnalysisService.analyze_recurrence` | CANONICAL |
| 17 | semantic_failures | `get_failure_info` | SUPPORT |
| 18 | incident_read_driver | `IncidentReadDriver.list_incidents` | CANONICAL |
| 19 | incident_write_driver | `IncidentWriteDriver.insert_incident` | CANONICAL; `insert_incident_from_anomaly` added (PIN-508 Phase 1B) |
| 20 | incidents_facade_driver | `IncidentsFacadeDriver.fetch_active_incidents` | CANONICAL |
| 21 | incident_aggregator | `IncidentAggregator.get_or_create_incident` | CANONICAL |
| 22 | incident_pattern_driver | `IncidentPatternDriver.fetch_cascade_failures` | CANONICAL |
| 23 | postmortem_driver | `PostMortemDriver.fetch_category_stats` | CANONICAL |
| 24 | recurrence_analysis_driver | `RecurrenceAnalysisDriver.fetch_recurrence_groups` | CANONICAL |
| 25 | export_bundle_driver | `ExportBundleDriver.create_evidence_bundle` | CANONICAL |
| 26 | lessons_driver | `LessonsDriver.insert_lesson` | CANONICAL |
| 27 | llm_failure_driver | `LLMFailureDriver.insert_failure` | CANONICAL |
| 28 | policy_violation_driver | `PolicyViolationDriver.insert_violation_record` | CANONICAL |
| 29 | customer_incidents_adapter | `CustomerIncidentsAdapter.list_incidents` | CANONICAL |
| 30 | founder_ops_adapter | `FounderOpsAdapter.to_summary_response` | CANONICAL |

---

## 4. Duplicate Analysis

**Result: ZERO true duplicates.**

### Previously Flagged Overlaps — Reclassified

| Pair | Verdict | Evidence |
|------|---------|----------|
| `incident_driver` vs `incident_engine` | **FACADE_PATTERN** | Driver = orchestration facade (1 decision, RAC ack, delegates to engine). Engine = SDSR decision logic (6 decisions: severity, category, suppression, title, proposal). Driver.create_incident_for_run() → Engine.create_incident_for_run(). |
| `prevention_engine` vs `recovery_rule_engine` | **FALSE_POSITIVE** | Prevention = before-incident (5 validators: content accuracy, PII, safety, hallucination, budget). Recovery = after-incident (5 rule types: error code, historical, skill-specific, threshold, composite). Zero shared algorithm code. |

---

## 5. Uncalled Functions

5 functions in `policy_violation_engine.py` with no detected callers:

| Function | Classification | Reason | Action |
|----------|---------------|--------|--------|
| `PolicyViolationService.check_policy_enabled` | INTERNAL | Self-contained check method, called indirectly via driver delegation | Keep |
| `PolicyViolationService.verify_violation_truth` | PENDING-PIN-195 | S3 truth verification, not yet wired from L4 | Keep for PIN-195 |
| `create_policy_evaluation_sync` | WIRED (false positive) | Called by `policy_violation_driver.insert_policy_evaluation_sync` | Keep — detection missed cross-file sync call |
| `handle_policy_evaluation_for_run` | PENDING-PIN-407 | Success-as-First-Class-Data entry point | Keep for PIN-407 |
| `handle_policy_violation` | PENDING-PIN-195 | S3 violation handling entry point, not yet wired from L4 | Keep for PIN-195 |

---

## 6. Architecture Violations

### V1: L6 imports L5 (HIGH)

**Location:** `L6_drivers/incident_aggregator.py`
**Violation:** Imports `IncidentSeverityEngine` from `L5_engines/incident_severity_engine.py`
**Topology Rule:** L6 drivers MUST NOT import L5 engines. Flow is L5→L6, never L6→L5.

```
CURRENT (WRONG):                    CORRECT (per HOC Topology V2.0.0):
L5 policy_violation_engine           L5 policy_violation_engine
    │                                    │
    ▼                                    ├──▶ L5 incident_severity_engine
L6 incident_aggregator                   │       (calculate severity)
    │                                    │
    ▼ VIOLATION                          ▼
L5 incident_severity_engine          L6 incident_aggregator
                                         (receives severity as parameter)
```

**Fix:** The L5 caller (policy_violation_engine or its callers) should call `IncidentSeverityEngine` first, then pass the computed severity to `incident_aggregator.get_or_create_incident()`.
**Status:** DEFERRED — wiring exercise post-domain-completion.

### V2: Cross-domain L5→L6 (MEDIUM)

**Location:** `policies/L5_engines/lessons_engine.py`
**Violation:** Policies domain L5 engine imports incidents domain L6 driver directly.
**Topology Rule:** Cross-domain access MUST go through the target domain's L5 engine, not directly to L6.

```
CURRENT (WRONG):                    CORRECT (per HOC Topology V2.0.0):
policies/L5 lessons_engine           policies/L5 lessons_engine
    │                                    │
    ▼ VIOLATION                          ▼
incidents/L6 lessons_driver          incidents/L5 lessons_engine (NEW or existing)
                                         │
                                         ▼
                                     incidents/L6 lessons_driver
```

**Fix:** Either (a) create an L5 `lessons_engine.py` in incidents domain that wraps the driver, or (b) move `lessons_driver` to policies domain since it manages `lessons_learned` + `policy_proposals` tables.
**Status:** DEFERRED — ownership decision needed during policies domain consolidation.

### V3: Stale import path (HIGH)

**Location:** `analytics/L5_engines/cost_anomaly_detector.py`
**Violation:** Imports from `app.hoc.cus.incidents.L3_adapters.anomaly_bridge` — path does not exist.
**Correct path:** `app.hoc.cus.incidents.L5_engines.anomaly_bridge`

```
CURRENT (WRONG):                    CORRECT:
from app.hoc.cus.incidents          from app.hoc.cus.incidents
    .L3_adapters                        .L5_engines
    .anomaly_bridge                     .anomaly_bridge
    import ...                          import ...
```

**Status:** DEFERRED — wiring exercise post-domain-completion.

### N1: Naming violation (FIXED)

**Location:** `L6_drivers/export_bundle_driver.py`
**Was:** Class named `ExportBundleService`
**Fixed:** Class renamed to `ExportBundleDriver` with backward-compatible alias `ExportBundleService = ExportBundleDriver`
**Callers updated:** `hoc/api/cus/incidents/incidents.py` now uses `get_export_bundle_driver()`
**Verified by:** `scripts/ops/hoc_incidents_tally.py` — ALL PASS

### E1: DB extraction completed (PIN-508 Phase 1B)

**Location:** `L5_engines/anomaly_bridge.py` → `_create_incident()` method
**Refactor:** Removed `_build_incident_insert_sql()` method. SQL construction moved entirely to `incident_write_driver.insert_incident_from_anomaly()`.
**Status:** RESOLVED — anomaly_bridge now passes normalized incident dict to driver. Constructor now accepts IncidentWriteDriver instance. Factory `get_anomaly_incident_bridge(session)` creates both driver and bridge.

---

## 7. Missing L4 Wiring

### W1: export_bundle_driver bypasses L4

**Current wiring:**
```
L2 incidents.py → L6 export_bundle_driver.get_export_bundle_driver()
```

**Expected wiring (per HOC Topology V2.0.0):**
```
L2 incidents.py → L4 hoc_spine/incidents_handler.py → L5 export_engine (NEW) → L6 export_bundle_driver
```

**Recommendation:** Create a thin L5 `export_engine.py` that wraps the driver, then register an `"incidents.export"` operation in the L4 incidents_handler. The L5 engine would add tenant scoping and audit logging before delegating to the driver.

### W2: lessons_driver has no incidents-domain L5 caller

**Current wiring:**
```
policies/L5 lessons_engine.py → incidents/L6 lessons_driver
```

**Expected wiring options:**

**Option A — Keep in incidents, add L5 wrapper:**
```
policies/L5 lessons_engine → incidents/L5 lessons_engine (NEW) → incidents/L6 lessons_driver
```

**Option B — Move to policies domain (recommended):**
```
policies/L5 lessons_engine → policies/L6 lessons_driver (MOVED)
```

**Recommendation:** Option B. The `lessons_driver` manages `lessons_learned` and `policy_proposals` tables, which are policy-domain concepts. The driver should live where its data authority lives. Decision deferred to policies domain consolidation.

---

## 8. Cross-Domain Dependencies

### Incidents L6 drivers accessing foreign tables

| # | Driver | Foreign Table | Owner Domain | Access | Justification |
|---|--------|---------------|--------------|--------|---------------|
| 1 | incident_write_driver | `runs` | activity | UPDATE (incident_count) | Incident count on run is denormalized counter |
| 2 | incident_write_driver | `aos_traces` | activity | UPDATE (incident_id) | Links trace to incident for evidence chain |
| 3 | incident_write_driver | `prevention_records` | policies | INSERT | Prevention record is co-owned (incident creates, policy reads) |
| 4 | incident_write_driver | `policy_proposals` | policies | INSERT | Incident engine proposes policies from patterns |
| 5 | incident_write_driver | `policy_rules` | policies | SELECT | Checks policy suppression rules |
| 6 | llm_failure_driver | `worker_runs` | activity | UPDATE (status=failed) | Marks run as failed when LLM failure detected |
| 7 | llm_failure_driver | `cost_records` | analytics | SELECT | Contamination check: was cost already recorded? |
| 8 | llm_failure_driver | `cost_anomalies` | analytics | SELECT | Contamination check: was anomaly already flagged? |
| 9 | lessons_driver | `lessons_learned` | unclear | READ+WRITE | Ownership contested (see W2) |
| 10 | lessons_driver | `policy_proposals` | policies | INSERT | Lesson→proposal conversion |
| 11 | policy_violation_driver | `prevention_records` | policies | READ+WRITE | Violation→prevention linkage |
| 12 | policy_violation_driver | `policy_rules` | policies | SELECT | Checks if policy is enabled |

### External domains importing from incidents

| # | Caller Domain | File | Imports | Purpose |
|---|---------------|------|---------|---------|
| 1 | policies | recovery_evaluation_engine.py | recovery_rule_engine (4 fns) | Recovery decision logic |
| 2 | policies | lessons_engine.py | lessons_driver (L6 direct) | Lesson persistence (VIOLATION V2) |
| 3 | analytics | cost_anomaly_detector.py | anomaly_bridge (stale path) | Anomaly→incident bridge |
| 4 | integrations | customer_incidents_adapter.py | incident_read_engine, incident_write_engine | Customer incident operations |

---

## 9. External Callers

Complete map of all files outside incidents domain that call into it.

| # | Layer | File | Imports From Incidents | Status |
|---|-------|------|------------------------|--------|
| 1 | L4 spine | `incidents_handler.py` | `incidents_facade` | WIRED |
| 2 | L4 spine | `transaction_coordinator.py` | `incident_driver` | COMMENTED OUT |
| 3 | L4 spine | `run_governance_facade.py` | `policy_violation_service` | COMMENTED OUT |
| 4 | L2 HOC API | `hoc/api/cus/incidents/incidents.py` | `incidents.export` (L4 handler) | WIRED (PIN-504 Phase 6) |
| 5 | L2 HOC API | `hoc/api/cus/recovery/recovery.py` | `recovery_rule_engine` | WIRED |
| 6 | L2 Legacy | `app/api/incidents.py` | `incidents_facade` (via shim) | LEGACY |
| 7 | L5 policies | `recovery_evaluation_engine.py` | `hoc_spine/schemas/recovery_decisions` (pure fns extracted) | RESOLVED (PIN-504 Phase 6) |
| 8 | L5 policies | `lessons_engine.py` | `lessons_driver` (lazy import) | RESOLVED (PIN-504 Phase 6) |
| 9 | L5 analytics | `cost_anomaly_detector.py` | `anomaly_bridge` | STALE PATH V3 |
| 10 | L5 integrations | `customer_incidents_adapter.py` | `incident_read_engine`, `incident_write_engine` | WIRED |
| 11 | int/general | `hallucination_hook.py` | `hallucination_detector` | WIRED |
| 12 | int/incidents | `failure_classification_engine.py` | `recovery_rule_engine` | WIRED |
| 13 | int/platform | `failure_intelligence.py` | `recovery_rule_engine` | WIRED |
| 14 | int/recovery | `incident_driver.py` | `incident_engine` | WIRED |

---

## 10. Lessons Learned

Patterns to apply when consolidating subsequent domains:

### L1: Overlap detection must consider role, not just noun
The original bible generator grouped scripts by canonical function noun (e.g., `create_incident_for_run`). Two scripts sharing a noun but serving different roles (ORCHESTRATION vs DECISION_ENGINE) are FACADE_PATTERN, not duplicates. The generator was updated to classify by role category (FACADE, ALGORITHM, PERSISTENCE).

### L2: Uncalled detection misses self.method() and cross-file sync calls
The simple "no callers" check produced false positives for:
- Methods called via `self._driver.method()` delegation (indirect call)
- Sync functions called from driver files (cross-file wiring)
- Design-ahead infrastructure for future PINs
Updated generator now checks `self.method()` calls in source files and PIN references.

### L3: L6→L5 imports are a common violation
When L6 drivers need business logic (severity calculation, etc.), they tend to import L5 engines. The correct pattern is for the L5 caller to compute the value and pass it as a parameter to the L6 driver.

### L4: Cross-domain L5→L6 is a domain ownership signal
When one domain's L5 engine imports another domain's L6 driver directly, it usually means either (a) the driver should be moved to the calling domain, or (b) a thin L5 interface is missing in the target domain.

### L5: Physical file count ≠ traced script count
The call chain tracer tracks 27 scripts (files with functions in the call graph). The actual directory has 30 .py files (including `__init__.py`, `incidents_types.py`, and files with only type definitions). Both counts are correct — use the tally script for physical verification and the bible for call graph analysis.

### L6: Naming conventions matter for automated detection
The script role classifier relies on file name patterns (`*_driver` = PERSISTENCE, `*_engine` = DECISION, `*_facade` = FACADE). Files that violate naming conventions (like `ExportBundleService` in a `*_driver.py` file) cause classification errors. Fix naming first, then run analysis.

---

## Verification

```bash
# Tally verification (deterministic)
python3 scripts/ops/hoc_incidents_tally.py
# Expected: ALL PASS (30 files, class/method counts, N1 fix verified)

# Software Bible regeneration
python3 scripts/ops/hoc_software_bible_generator.py --domain incidents
# Expected: 0 overlaps, 5 uncalled (classified), 27 traced scripts, 22 L2 features
```

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat A/B: No Actions Required

Domain has zero `app.services` imports (active or docstring) and zero `cus.general` imports.

### Cat D: L2→L5 Bypass Violations (3 → 0 — RESOLVED PIN-504 Phase 6)

| L2 File | Resolution |
|---------|-----------|
| `incidents/incidents.py` (3 export endpoints) | Routed through L4 `incidents.export` handler via `IncidentsExportHandler` |

### Cat E: Cross-Domain L5→L5/L6 Violations (Outbound — 1 → 0 — RESOLVED PIN-504 Phase 6)

| Source File | Old Import | Resolution |
|------------|-----------|-----------|
| `incident_engine.py` | `policies.L5_engines.lessons_engine` | LessonsCoordinator (L4) injected as `evidence_recorder` |
| `incident_write_engine.py` | `logs.L5_engines.audit_ledger_engine` | AuditCoordinator (L4) injected (PIN-504 Phase 2) |

### Tally

12/12 checks PASS (9 consolidation + 3 cleansing).

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-507 Law 0 Remediation (2026-02-01)

**Legacy `app/services/incident_write_engine.py`:** Import of `AuditLedgerService` rewired from abolished `app.services.logs.audit_ledger_service` → `app.hoc.cus.logs.L5_engines.audit_ledger_engine`. This is a transitional `services→hoc` dependency (comment added at import site). Permanent fix: migrate entire `incident_write_engine.py` to `hoc/cus/incidents/L5_engines/`.

**Legacy `app/worker/runner.py`:** Import of `get_incident_facade` rewired from non-existent `..services.incidents.facade` submodule → `..services.incidents` (package-level `__init__` export). Unblocks `test_phase5a_governance.py`.

**`hoc/cus/incidents/L6_drivers/export_bundle_driver.py` (line 45):** L6→L7 boundary fix. `Incident` model import moved from `app.db` → `app.models.killswitch`. L6 drivers must not import L7 models via `app.db` per HOC Topology V2.0.0. Detected by `scripts/ci/check_init_hygiene.py` L6_L7_BOUNDARY check.

## PIN-508 Refactoring (2026-02-01)

### Phase 1B: anomaly_bridge → incident_write_driver Extraction

**Files Modified:**
- `L5_engines/anomaly_bridge.py`
- `L6_drivers/incident_write_driver.py`

**Changes:**

1. **anomaly_bridge.py:**
   - `__init__` now accepts `IncidentWriteDriver` instance via constructor instead of `SQLAlchemy session`
   - Removed `_build_incident_insert_sql()` method — SQL construction moved to driver
   - Removed `_create_incident()` method — delegated to driver's new `insert_incident_from_anomaly()` method
   - Factory function `get_anomaly_incident_bridge(session)` creates driver internally

2. **incident_write_driver.py:**
   - Added `insert_incident_from_anomaly(incident_dict: Dict)` method (Phase 1B)
   - Accepts normalized incident data (severity, category, title, etc.) from anomaly_bridge
   - Handles full SQL INSERT + IncidentEvent creation + audit logging
   - Eliminates direct SQL in L5 engines

**Impact:**
- Zero L5→L6 method signature changes (wrapper interface preserved)
- Pure extraction (no business logic moved, no behavior change)
- incident_aggregator and other L5 callers unaffected

### Phase 4B: incident_severity_engine Deletion

**Files Deleted:**
- `L5_engines/incident_severity_engine.py` (TOMBSTONE)

**Rationale:**
- Logic previously in `IncidentSeverityEngine` extracted to `L5_schemas/severity_policy.py` (see PIN-507 Law 1)
- Zero current dependents (incident_aggregator rewired to import from `L5_schemas`)
- Tombstone placeholder left for historical reference; not imported by any file

**Impact:**
- No breakage (precursor moved by PIN-507)
- Cleanup only; severity policy now canonical at schema layer

## PIN-510 Phase 1C — CostAnomalyFact Extraction (2026-02-01)

- `CostAnomalyFact` dataclass extracted from `anomaly_bridge.py` to `hoc_spine/schemas/anomaly_types.py`
- Backward-compat re-export remains in `anomaly_bridge.py` (TOMBSTONE)
- New L4 coordinator `anomaly_incident_coordinator.py` owns analytics→incidents sequencing
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

**`fdr/incidents/engines/ops_incident_service.py`:** Import swapped from `app.services.ops_domain_models` → `app.hoc.fdr.ops.schemas.ops_domain_models`. HOC schemas copy has identical `OpsIncident`, `OpsIncidentCategory`, `OpsSeverity` dataclasses.

**`api/fdr/incidents/ops.py:1482`:** Import swapped from `app.services.ops.get_ops_facade` → `app.hoc.fdr.ops.facades.ops_facade.get_ops_facade`. HOC ops facade now self-contained (its own legacy imports were severed in the same phase). Fully severed.
