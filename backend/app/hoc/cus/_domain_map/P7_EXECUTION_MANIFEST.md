# P7 Execution Manifest — HOC Domain Consolidation

**Status:** READY FOR EXECUTION
**Created:** 2026-01-27
**Reference:** PIN-470, PIN-479, PIN-480, V4_DOMAIN_WORKBOOK_CANONICAL_FINAL.md
**Input:** 63 approved decisions from P6 review (90 candidates, 18 batches)

---

## Execution Order

| Group | Type | Count | Risk | Execute |
|-------|------|-------|------|---------|
| **A** | Inline utility deletions (utc_now/generate_uuid) | 15 unique files | LOW | FIRST |
| **B** | Full file deletions (0 importers) | 20 files | LOW | SECOND |
| **C** | Full file deletions (repoints required) | 14 files | MEDIUM | THIRD |
| **D** | Renames + relocations | 4 files | HIGH | FOURTH |

---

## GROUP A — Inline Utility Deletions (15 unique files)

> Delete inline `utc_now()` and/or `generate_uuid()` functions. Add import from canonical.
> Canonical utc_now: `from app.hoc.hoc_spine.services.time import utc_now`
> Canonical generate_uuid: `from app.hoc.cus.general.L6_drivers.cross_domain import generate_uuid`

| # | File | Delete Functions | Candidate IDs | Status |
|---|------|-----------------|---------------|--------|
| A01 | `account/L6_drivers/user_write_driver.py` | `utc_now()` | C006-C009 | ☑ DONE |
| A02 | `general/L5_controls/drivers/guard_write_driver.py` | `utc_now()` ~line 64 | C013 | ☑ DONE |
| A03 | `analytics/L6_drivers/cost_write_driver.py` | `utc_now()` ~line 52 | C013 | ☑ DONE |
| A04 | `general/L5_engines/knowledge_lifecycle_manager.py` | `utc_now()` | C040 | ☑ DONE |
| A05 | `incidents/L5_engines/incident_engine.py` | `utc_now()` lines 93-95 | C041 | ☑ DONE |
| A06 | `logs/L5_engines/mapper.py` | `utc_now()` lines 43-45 | C042 | ☑ DONE |
| A07 | `policies/L5_engines/lessons_engine.py` | `utc_now()` lines 85-87 | C043 | ☑ DONE |
| A08 | `policies/L5_engines/mapper.py` | `utc_now()` lines 43-45 | C044 | ☑ DONE |
| A09 | `general/L5_schemas/artifact.py` | `_utc_now()` ~line 30-32 | C056 | ☑ DONE (imported as `_utc_now` alias) |
| A10 | `general/L5_schemas/plan.py` | `_utc_now()` ~line 30-32 | C056 | ☑ DONE (imported as `_utc_now` alias) |
| A11 | `incidents/L6_drivers/guard_write_driver.py` | `utc_now()` lines 66-68 | C062 | ☑ DONE |
| A12 | `controls/L6_drivers/override_driver.py` | `utc_now()` + `generate_uuid()` | C019, C020 | ☑ DONE |
| A13 | `policies/L5_engines/policy_limits_engine.py` | `utc_now()` lines 78-80 + `generate_uuid()` lines 83-85 | C067 | ☑ DONE |
| A14 | `policies/L5_engines/policy_rules_engine.py` | `utc_now()` lines 79-81 + `generate_uuid()` lines 84-86 | C068 | ☑ DONE |
| A15 | `general/L5_engines/plan_generation_engine.py` | `utc_now()` | C024 | ⊘ SKIP (file does not exist) |

---

## GROUP B — Full File Deletions (0 Importers, 20 files)

> These files have ZERO active importers. Safe to delete without repointing.

| # | File to Delete | Lines | Canonical Location | Candidate ID | Status |
|---|---------------|-------|-------------------|--------------|--------|
| B01 | `api_keys/L5_engines/email_verification.py` | ~600 | `account/L5_engines/email_verification.py` | C001 | ☑ DELETED |
| B02 | `integrations/L5_engines/notifications_facade.py` | ~500 | `account/L5_engines/notifications_facade.py` | C003 | ☑ DELETED |
| B03 | `activity/L5_engines/run_governance_facade.py` | ~400 | `general/L4_runtime/facades/run_governance_facade.py` | C010 | ⊘ DEFERRED → Group C (has importers: activity/__init__.py) |
| B04 | `controls/L5_engines/alerts_facade.py` | 677 | `general/L5_engines/alerts_facade.py` | C016 | ☑ DELETED |
| B05 | `controls/L6_drivers/llm_threshold_driver.py` | 823 | SUPERSEDED by `threshold_driver.py` | C018 | ☑ DELETED |
| B06 | `policies/L5_engines/run_governance_facade.py` | ~400 | `general/L4_runtime/facades/run_governance_facade.py` | C011 | ⊘ DEFERRED → Group C (has importers: transaction_coordinator, engines/__init__) |
| B07 | `incidents/L5_engines/alert_log_linker.py` | 758 | `general/L5_engines/alert_log_linker.py` | C031 | ☑ DELETED |
| B08 | `general/L5_engines/durability.py` | ~325 | `general/L5_engines/audit_durability.py` | C032 | ☑ DELETED |
| B09 | `logs/L6_drivers/audit_store.py` | 455 | `general/L5_engines/audit_store.py` | C033 | ☑ DELETED |
| B10 | `logs/L6_drivers/store.py` | 454 | `general/L5_engines/audit_store.py` | C034 | ☑ DELETED |
| B11 | `logs/L5_engines/compliance_facade.py` | 515 | `general/L5_engines/compliance_facade.py` | C035 | ☑ DELETED |
| B12 | `logs/L5_engines/control_registry.py` | 454 | `general/L5_engines/control_registry.py` | C037 | ☑ DELETED |
| B13 | `integrations/L5_vault/engines/cus_credential_engine.py` | 480 | `general/L5_engines/cus_credential_service.py` | C038 | ☑ DELETED |
| B14 | `policies/L5_engines/fatigue_controller.py` | 749 | `general/L5_engines/fatigue_controller.py` | C039 | ☑ DELETED |
| B15 | `general/L5_engines/lifecycle/lifecycle_facade.py` | 704 | `general/L5_engines/lifecycle_facade.py` | C045 | ☑ DELETED |
| B16 | `integrations/L5_engines/monitors_facade.py` | 538 | `general/L5_engines/monitors_facade.py` | C047 | ☑ DELETED |
| B17 | `integrations/L6_drivers/execution.py` | 1323 | `general/L5_lifecycle/drivers/execution.py` | C050 | ☑ DELETED |
| B18 | `integrations/L3_adapters/notifications_base.py` | ~300 | `account/L5_engines/notifications_facade.py` | C075 | ☑ DELETED |
| B19 | `logs/L5_engines/export_completeness_checker.py` | 518 | `logs/L5_engines/completeness_checker.py` | C083 | ☑ DELETED |
| B20 | `integrations/L5_engines/channel_engine.py` | 1107 | `integrations/L5_notifications/engines/channel_engine.py` | C076 | ☑ DELETED |

---

## GROUP C — Full File Deletions + Repoints (14 files)

> These files have active importers that must be redirected before deletion.

| # | File to Delete | Repoint Count | Importers to Fix | New Import Path | Candidate ID | Status |
|---|---------------|---------------|-----------------|-----------------|--------------|--------|
| C01 | `incidents/L6_drivers/guard_write_driver.py` | 1 | `hoc/api/cus/policies/guard.py` | `general/L5_controls/drivers/guard_write_driver.py` (class: GuardWriteService→GuardWriteDriver) | C028 | ☑ REPOINTED+DELETED |
| C02 | `general/L5_engines/runtime_switch.py` | 4 | `step_enforcement.py`, `kill_switch_guard.py`, `boot_guard.py`, `governance_facade.py` | `general/L5_controls/drivers/runtime_switch.py` | C029 | ☑ REPOINTED+DELETED |
| C03 | `general/L5_engines/degraded_mode_checker.py` | 0 | — | `general/L5_controls/engines/degraded_mode_checker.py` | C030 | ☑ DELETED |
| C04 | `general/L5_engines/contract_engine.py` | 6 | `__init__.py`, `governance_orchestrator.py`, `founder_*` (×4) | `general/L5_workflow/contracts/engines/contract_engine.py` | C036 | ☑ REPOINTED+DELETED |
| C05 | `policies/L5_engines/hallucination_detector.py` | 0 | — | `incidents/L5_engines/hallucination_detector.py` | C071 | ☑ DELETED |
| C06 | `policies/L5_engines/mcp_connector.py` | 0 | — | `integrations/L5_engines/mcp_connector.py` | C077 | ☑ DELETED |
| C07 | `integrations/L5_engines/service.py` | 0 | — | `integrations/L5_vault/engines/service.py` | C078 | ☑ DELETED |
| C08 | `logs/L5_engines/audit_engine.py` | 0 | — | `logs/L5_support/CRM/engines/audit_engine.py` | C080 | ☑ DELETED (+ repointed __init__.py) |
| C09 | `logs/L5_engines/reconciler.py` | 0 | — | `logs/L5_engines/audit_reconciler.py` | C082 | ☑ DELETED |
| C10 | `policies/L5_engines/rollout_projection.py` | 0 | — | `general/L5_ui/engines/rollout_projection.py` | C061 | ☑ DELETED (+ repointed __init__.py) |
| C11 | `policies/L5_engines/job_executor.py` | 0 | — | `general/L5_support/CRM/engines/job_executor.py` | C060 | ☑ DELETED (+ repointed __init__.py) |
| C12 | `integrations/L5_engines/retrieval_facade.py` | 1 | `policies/retrieval.py` | `general/L5_engines/retrieval_facade.py` | C048 | ☑ REPOINTED+DELETED |
| C13 | `integrations/L5_engines/retrieval_mediator.py` | 2 | `retrieval_facade.py`, `retrieval_hook.py` | `general/L5_engines/retrieval_mediator.py` | C049 | ☑ REPOINTED+DELETED |
| C14 | `logs/L5_schemas/audit_models.py` | 6 | `audit_store`, `audit_reconciler`, `run_governance_facade`, `incident_driver` (×2), `run_orchestration_kernel` | `general/L5_schemas/rac_models.py` | C057 | ☑ REPOINTED+DELETED |
| C15 | `logs/L5_schemas/models.py` | 0 | — | `general/L5_schemas/rac_models.py` | C058 | ☑ DELETED |
| C16 | `policies/L5_engines/mapper.py` | 0 | — | `logs/L5_engines/mapper.py` | C085 | ☑ DELETED |
| C17 | `policies/L5_engines/replay_determinism.py` | 1 | `policies/guard.py` | `logs/L5_engines/replay_determinism.py` | C086 | ☑ REPOINTED+DELETED |
| C18 | `general/L5_lifecycle/engines/base.py` | 1 | `lifecycle_worker.py` | `general/L5_engines/lifecycle_stages_base.py` | C046 | ☑ REPOINTED+DELETED |
| C19 | `general/L6_drivers/knowledge_plane.py` | 0 | — | `general/L5_lifecycle/drivers/knowledge_plane.py` | C051 | ☑ DELETED |
| C20 | `policies/L5_engines/governance_orchestrator.py` | 0 | — | `general/L4_runtime/engines/governance_orchestrator.py` | C023 | ☑ DELETED |

---

## GROUP D — Renames + Relocations (4 files)

> Highest risk. Create new file at target path, repoint importers, then delete source.

| # | Source Path | Target Path | Rename | Importers to Update | Candidate ID | Status |
|---|------------|------------|--------|-------------------|--------------|--------|
| D01 | `policies/L5_engines/profile.py` | `general/L5_engines/profile_policy_mode.py` | YES: profile.py → profile_policy_mode.py | 3: `boot_guard.py:87,101`, `failure_mode_handler.py:97` | C004 | ☑ MOVED+REPOINTED |
| D02 | `policies/L5_engines/validator_engine.py` | `account/L5_support/CRM/engines/crm_validator_engine.py` | YES: validator_engine.py → crm_validator_engine.py | 2: `contract_engine.py:102`, `L4_runtime/__init__.py:113` | C005 | ☑ MOVED+REPOINTED |
| D03 | `activity/L5_engines/threshold_engine.py` | `controls/L5_engines/threshold_engine.py` | NO (same name) | 6: `runner.py`, `policy_limits_crud` (×3), `threshold_driver`, `activity/__init__` | C012 | ☑ MOVED+REPOINTED |
| D04 | `general/L5_engines/phase_status_invariants.py` | (keep, fix header) | NO | — | C025 | ⊘ SKIP (file does not exist) |

---

## Pre-Execution Checklist

- [x] Verify all canonical files exist before deleting copies
- [x] Execute Group A (inline deletions) — 14/15 done, A15 skipped
- [x] Verify: 0 non-canonical `def utc_now` remaining
- [x] Execute Group B (0-importer file deletions) — 18/20 done, B03+B06 deferred→C
- [x] Verify: 0 broken imports
- [x] Execute Group C (repoints + deletions) — 22/22 done (~30 repoints)
- [x] Verify: 0 broken imports
- [x] Execute Group D (renames + relocations) — 3/4 done, D04 skipped
- [x] Final BLCA: 1071 errors, 116 warnings (unchanged from pre-P7)
- [x] Update domain locks — all 11 updated to v2.1 (PIN-482)

---

## Totals

| Metric | Value |
|--------|-------|
| Files to delete (full) | ~37 |
| Inline functions to remove | ~20 across 15 files |
| Import repoints | ~30 |
| Renames | 2 (C004, C005) |
| Relocations | 2 (C012, C051) |
| Estimated LOC removed | ~15,000+ |
