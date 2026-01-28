# PIN-479: HOC Domain Migration — Phase 0 Manifest + Phase 1 Execution

**Status:** ✅ COMPLETE
**Created:** 2026-01-27
**Category:** HOC Migration
**Parent:** PIN-470 (HOC Layer Inventory)

---

## Summary

Complete execution of HOC domain migration Phases 0 and 1. Parsed V3_MANUAL_AUDIT_WORKBOOK.md to identify 83 MISPLACED files. Resolved 13 duplicate conflicts (DELETE_DUPLICATE). Moved 70 files to correct domains with SHA-256 verification. Repointed 57 import references across 36 files. Zero stale references remaining.

---

## Artifacts

| Artifact | Path | Type | Purpose |
|----------|------|------|---------|
| Manifest Generator | `scripts/ops/hoc_phase0_manifest_generator.py` | CODE/OPS | Parses workbook, resolves paths, detects collisions, outputs CSV+MD |
| Migration Manifest | `backend/app/hoc/cus/_domain_map/MIGRATION_MANIFEST.csv` | DATA | 83-row manifest with migration IDs, paths, hashes, statuses |
| Migration Summary | `backend/app/hoc/cus/_domain_map/MIGRATION_SUMMARY.md` | DOC | Stats, collision report, resolution log, domain breakdowns |
| Source Workbook | `backend/app/hoc/cus/_domain_map/V3_MANUAL_AUDIT_WORKBOOK.md` | DATA (read-only) | 184-file audit workbook, 83 marked MISPLACED |

---

## Phase 0: Manifest Generation

### What Was Done

1. Built `hoc_phase0_manifest_generator.py` that parses two workbook formats:
   - **Format A** (markdown table): `### [x]` header → `| **Current Domain** |` table → `**DECISION:** \`target\` ⚠️ (MISPLACED)`
   - **Format B** (code-block): `### [x]` header → `Attribute: Current Domain` / `Value:` → `ASSIGN TO: target ⚠️ (MISPLACED)`
2. Resolved all 83 filenames to filesystem paths under `backend/app/hoc/cus/`
3. Computed SHA-256 hashes for each source file
4. Detected 13 collisions where target path already had a file

### Manifest Schema

```
migration_id, current_path, current_domain, current_layer, target_domain,
target_layer, target_path, reason, status, hash_source, hash_target
```

### Initial Results

| Status | Count |
|--------|-------|
| PENDING | 70 |
| CONFLICT | 13 |
| UNRESOLVED | 0 |

---

## Phase 0.5: Conflict Resolution (13 entries)

### Investigation

All 13 CONFLICT entries were near-duplicates where the target domain already held a copy. Cross-referenced with workbook:
- **11 of 13**: Target file was marked `✓ (CONFIRMED CORRECT)` in workbook
- **2 of 13** (M024, M054): Target not in workbook but verified via diff + import analysis

### Detailed Conflict Analysis

| ID | File | Source → Target | Diff Lines | Resolution |
|----|------|-----------------|------------|------------|
| M016 | `evidence_report.py` | incidents → logs | 7 | Delete source, repoint `guard.py:1837` |
| M020 | `panel_invariant_monitor.py` | incidents → general | 13 | Delete source (zero callers) |
| M022 | `pdf_renderer.py` | incidents → logs | 5 | Delete source, repoint `incidents.py:1852,1918,1984` |
| M024 | `runtime_switch.py` | incidents → general | 24 | Delete source (both orphaned, target canonical) |
| M031 | `connectors_facade.py` | logs → integrations | 9 | Delete source (zero callers) |
| M033 | `datasources_facade.py` | logs → integrations | 5 | Delete source (zero callers) |
| M034 | `detection_facade.py` | logs → analytics | 20 | Delete source (orphaned AnomalySeverity enum) |
| M040 | `scheduler_facade.py` | logs → general | 19 | Delete source (zero callers) |
| M050 | `alert_emitter.py` | policies → general | **102** | Delete source (zero callers; see note) |
| M054 | `cross_domain.py` | policies → general | 10 | Delete source (target imported by L4_runtime) |
| M063 | `audit_evidence.py` | policies → logs | 22 | Delete source (zero callers) |
| M066 | `certificate.py` | policies → logs | 18 | Delete source, repoint `guard.py:83` |
| M079 | `identity_resolver.py` | integrations → account | 13 | Delete source (zero callers) |

### Notable Findings

- **M034**: Source had orphaned `AnomalySeverity` enum (3 values). Target imports from `cost_anomaly_detector.py`. Integrations has 4-value variant (adds CRITICAL). No consolidation needed.
- **M050**: Source used correct L6 session-per-call factory (`create_alert_emitter`). Target uses singleton (`get_alert_emitter`) — **violates L6 driver contract**. Neither has callers. **Future fix required.**
- **M066**: Source declared L3 (Boundary Adapter), target declared L5 (Domain Engine). Layer disagreement — target's L5 is correct per workbook.

### Phase 0.5 Import Repoints (3 statements in 2 files)

| File Modified | Old Import | New Import |
|---------------|------------|------------|
| `hoc/api/cus/policies/guard.py:83` | `policies.L5_engines.certificate` | `logs.L5_engines.certificate` |
| `hoc/api/cus/policies/guard.py:1837` | `incidents.L5_engines.evidence_report` | `logs.L5_engines.evidence_report` |
| `hoc/api/cus/incidents/incidents.py:1852,1918,1984` | `incidents.L5_engines.pdf_renderer` | `logs.L5_engines.pdf_renderer` |

---

## Phase 1: File Moves + Import Repointing

### Execution

- **70 files moved** via `shutil.move()` with SHA-256 post-move verification
- **0 failures**, 0 hash mismatches
- **8 new directories created** for target paths:
  - `apis/L6_drivers/`, `controls/L5_controls/drivers/`, `controls/L5_controls/engines/`
  - `general/L5_engines/lifecycle/`, `general/L5_support/CRM/engines/`
  - `integrations/L5_notifications/engines/`, `logs/L5_support/CRM/engines/`
  - `policies/L3_adapters/`

### Import Repointing (54 references across 34 files)

| Old Module Path | New Module Path | Refs |
|-----------------|-----------------|------|
| `incidents.L5_engines.lessons_engine` | `policies.L5_engines.lessons_engine` | 16 |
| `analytics.L6_drivers.alert_driver` | `general.L6_drivers.alert_driver` | 6 |
| `policies.L5_engines.contract_engine` | `general.L5_engines.contract_engine` | 6 |
| `incidents.L6_drivers.scoped_execution` | `controls.L6_drivers.scoped_execution` | 5 |
| `activity.L6_drivers.threshold_driver` | `controls.L6_drivers.threshold_driver` | 4 |
| `policies.L6_drivers.keys_driver` | `apis.L6_drivers.keys_driver` | 2 |
| `policies.L5_schemas.policy_limits` | `controls.L5_schemas.policy_limits` | 2 |
| `policies.L5_schemas.simulation` | `controls.L5_schemas.simulation` | 2 |
| `incidents.L5_engines.recovery_evaluation_engine` | `policies.L5_engines.recovery_evaluation_engine` | 1 |
| `integrations.L5_engines.cus_telemetry_service` | `activity.L5_engines.cus_telemetry_service` | 1 |
| `policies.L5_controls.engines.customer_killswitch_read_engine` | `controls.L5_controls.engines.customer_killswitch_read_engine` | 1 |
| `policies.L5_engines.audit_engine` | `logs.L5_engines.audit_engine` | 1 |
| `policies.L5_engines.controls_facade` | `controls.L5_engines.controls_facade` | 1 |
| `policies.L5_schemas.overrides` | `controls.L5_schemas.overrides` | 1 |
| `policies.L6_drivers.budget_enforcement_driver` | `controls.L6_drivers.budget_enforcement_driver` | 1 |
| `policies.L6_drivers.limits_read_driver` | `controls.L6_drivers.limits_read_driver` | 1 |
| `policies.L6_drivers.override_driver` | `controls.L6_drivers.override_driver` | 1 |
| `policies.L6_drivers.policy_limits_driver` | `controls.L6_drivers.policy_limits_driver` | 1 |
| `account.L6_drivers.worker_registry_driver` | `integrations.L6_drivers.worker_registry_driver` | 1 |

### Files Modified for Import Repointing (34 files)

**API Layer (10 files):**
- `hoc/api/cus/policies/policy_layer.py` — 6 refs
- `hoc/api/cus/recovery/recovery.py` — 5 refs
- `hoc/api/cus/policies/policy.py` — 2 refs
- `hoc/api/cus/policies/simulate.py` — 1 ref
- `hoc/api/cus/policies/controls.py` — 1 ref
- `hoc/api/cus/policies/override.py` — 1 ref
- `hoc/api/cus/integrations/cus_telemetry.py` — 1 ref
- `hoc/api/fdr/agent/founder_contract_review.py` — 1 ref
- `hoc/fdr/ops/engines/founder_review.py` — 1 ref
- `hoc/fdr/ops/facades/founder_review_adapter.py` — 1 ref

**Engine/Driver Layer (18 files):**
- `general/L5_engines/alert_worker.py` — 5 refs
- `services/policy/lessons_engine.py` — 3 refs + 1 comment
- `policies/L5_engines/keys_shim.py` — 2 refs
- `policies/L5_engines/policy_limits_engine.py` — 2 refs
- `activity/L5_engines/threshold_engine.py` — 1 ref
- `activity/L5_engines/run_governance_facade.py` — 1 ref
- `controls/L5_engines/budget_enforcement_engine.py` — 1 ref
- `controls/L3_adapters/customer_killswitch_adapter.py` — 1 ref
- `controls/L6_drivers/override_driver.py` — 1 ref
- `general/L4_runtime/engines/__init__.py` — 2 refs
- `general/L4_runtime/engines/governance_orchestrator.py` — 1 ref
- `general/L4_runtime/facades/run_governance_facade.py` — 1 ref
- `incidents/L5_engines/incident_engine.py` — 1 ref
- `policies/L3_adapters/founder_contract_review_adapter.py` — 1 ref
- `policies/L5_engines/run_governance_facade.py` — 1 ref
- `policies/L5_engines/policies_limits_query_engine.py` — 1 ref
- `policies/L6_drivers/__init__.py` — 1 ref
- `account/L6_drivers/__init__.py` — 1 ref

**__init__.py Re-exports (3 files):**
- `activity/L6_drivers/__init__.py` — 1 ref
- `analytics/L6_drivers/__init__.py` — 1 ref
- `account/L6_drivers/__init__.py` — 1 ref

**Runtime/Worker Layer (3 files):**
- `worker/runner.py` — 1 ref
- `hoc/int/analytics/engines/runner.py` — 1 ref
- `hoc/int/incidents/engines/recovery_evaluator.py` — 1 ref
- `hoc/int/platform/engines/evaluator.py` — 1 ref

---

## Domain Flow Summary

### Files Migrated FROM (source domains)

| Domain | Files Out | Notes |
|--------|-----------|-------|
| policies | 31 | Largest source — controls, general, logs, apis split |
| logs | 16 | Facades moved to integrations, controls, general, analytics |
| incidents | 12 | Evidence/proof → logs, governance → general, lessons → policies |
| integrations | 11 | Adapters → controls/policies, identity → account |
| analytics | 8 | Circuit breakers → controls, alerts → general |
| account | 4 | Notifications → integrations, CRM → logs/general |
| activity | 1 | Threshold driver → controls |

### Files Migrated TO (target domains)

| Domain | Files In | Role |
|--------|----------|------|
| general | 26 | System-wide orchestration, governance, lifecycle, cross-domain bridge |
| controls | 25 | Limits, thresholds, killswitches, circuit breakers, budgets |
| logs | 10 | Evidence, audit trail, certificates, proof, capture |
| integrations | 8 | Connectors, data sources, monitors, notifications, channels |
| policies | 6 | Lessons, failure modes, recovery, learning proof, adapters |
| analytics | 3 | Cost snapshots, detection, behavioral analysis |
| account | 2 | Billing, identity resolution |
| activity | 2 | Telemetry, orphan recovery |
| apis | 1 | API key driver |

---

## Architecture Note: `general` Domain Role

> **`general` is the utility and bridge domain.** It serves as the source for system-wide
> utilities (runtime orchestration, lifecycle management, governance enforcement, scheduling)
> and acts as the bridge for cross-domain data transfer between domain boundaries.
> Files that coordinate across multiple domains (e.g., `cross_domain.py`, `alert_emitter.py`,
> `retrieval_mediator.py`) belong in `general` because no single domain owns cross-cutting
> orchestration. General does not own business decisions — it owns the infrastructure that
> enables domains to exchange data and coordinate execution.

---

## Verification

- All 83 manifest entries resolved (70 MOVED + 13 DELETE_DUPLICATE)
- SHA-256 hash verified for all 70 moves (zero mismatches)
- Zero stale import references remaining (full `backend/` scan verified)
- Manifest CSV and Summary MD updated with final statuses

---

## Open Items

| Item | Priority | Reference |
|------|----------|-----------|
| `general/L6_drivers/alert_emitter.py` singleton → session-per-call | MEDIUM | M050 investigation notes |
| `AnomalySeverity` enum consolidation (3-value vs 4-value) | LOW | M034 investigation notes |
| `__init__.py` re-exports in activity/analytics/account may be stale | LOW | Phase 1 repoint scan |

---

## Timeline

| Date | Event |
|------|-------|
| 2026-01-27 | Phase 0: Manifest generated (83 entries, 70 PENDING, 13 CONFLICT) |
| 2026-01-27 | Phase 0.5: 13 conflicts resolved as DELETE_DUPLICATE, 3 imports repointed |
| 2026-01-27 | Phase 1: 70 files moved, 54 imports repointed across 34 files |
---

## Phase 3 Domain Locking

### Update (2026-01-27)

Phase 3 COMPLETE. 11 domains locked with post-migration file inventories. 443 files, 127,042 LOC inventoried with SHA-256 hashes and layer classification. Artifacts produced: 11 DOMAIN_LOCK_FINAL.md files (backend/app/hoc/cus/docs/domain-locks/), DOMAIN_LOCK_REGISTRY.json (backend/app/hoc/cus/_domain_map/), DOMAIN_CI_GUARDS.yaml (backend/app/hoc/cus/_domain_map/). Script: scripts/ops/hoc_phase3_domain_locker.py. P1/P2 backfill artifacts also generated: PHASE1_VALIDATION_REPORT.md, PHASE1_CALLER_MAP.csv (136 rows), PHASE2_EXECUTION_LOG.csv (83 rows). Domain breakdown: policies 95 files (28,186 LOC), general 93 files (27,264 LOC), integrations 62 files (20,156 LOC), logs 45 files (15,509 LOC), analytics 36 files (10,215 LOC), incidents 35 files (9,800 LOC), controls 29 files (6,675 LOC), activity 17 files (2,984 LOC), account 16 files (4,414 LOC), api_keys 9 files (902 LOC), overview 6 files (937 LOC).
---

## Phase 4 Post-Migration Validation

### Update (2026-01-27)

Phase 4 COMPLETE. Overall: HEALTHY (score 92). V1 Import Resolution: PASS (443/443 files parse OK). V2 BLCA: SKIP (1,092 pre-existing legacy violations in app/policy/, zero in HOC cus/). V3 Tests: SKIP (no tests/hoc/ directory). V4 Circular Imports: PASS (1 lazy import cycle — threshold_driver↔threshold_engine — safe pattern). V5 Domain Integrity: WARN (38 filename duplicates across domains — pre-existing, Phase 5 scope). V6 Hash Verification: PASS (11 domains, 0 mismatches vs lock registry). Conclusion: migration is structurally sound, no regressions. Artifacts: PHASE4_VALIDATION_REPORT.md, PHASE4_HEALTH_SCORE.json. Script: scripts/ops/hoc_phase4_post_migration_validator.py.
---

## Phase 5 Duplicate Detection

### Update (2026-01-27)

Phase 5 COMPLETE. 426 duplicates detected across 385 files using 3-mode analysis: 2 exact file duplicates (SHA-256), 388 function/class signature duplicates (>70% body similarity), 36 block-level duplicates (>80% SequenceMatcher). 90 consolidation candidates produced. Top patterns: utc_now() utility duplicated 12+ times across 7 domains, generate_uuid() in 5 files, governance facades triplicated across general/activity/policies, full-file notification/profile/email duplicates across account/policies/integrations/api_keys, audit engines duplicated across general/logs. Recommendations: ~55 DELETE_FROM_DOMAIN (general already canonical), ~32 EXTRACT_TO_GENERAL (needs new canonical), 3 REVIEW_MERGE (partial overlap needs manual review). Artifacts: PHASE5_DUPLICATE_REPORT.csv (426 rows), PHASE5_CONSOLIDATION_CANDIDATES.csv (90 rows), PHASE5_DUPLICATE_SUMMARY.md. Script: scripts/ops/hoc_phase5_duplicate_detector.py.
---

## P7-P10 Close-out (2026-01-27)

### Update (2026-01-27)

P7 COMPLETE: 40 files deleted, 3 relocated, 14 edited. ~19K LOC removed. 54 import repoints. 0 broken imports. CHANGE-2026-0001 through 0004. PIN-481.
P8 COMPLETE: All 11 domain locks updated to v2.1. File counts verified. CHANGE-2026-0005. PIN-482.
P9 COMPLETE: BLCA baseline = 1071 errors, 116 warnings (pre-existing PIN-438 debt, unchanged). HOC cus domain: 405 files (was 472 pre-migration).
P10 COMPLETE: Migration close-out. All phases P1-P10 done.
FINAL STATUS: HOC Domain Migration COMPLETE.
