# HOC Wiring Plan — hoc/cus/* Unused Code (DRAFT)

**Scope:** 155 UNWIRED entries in `hoc/cus/*` from `UNUSED_CODE_AUDIT.csv`
**Generated:** 2026-02-01
**Reference:** PIN-513 Phase 7 continuation
**Methodology:** Two-pass research. Pass 1: deep search per domain. Pass 2: skeptical cross-check.

---

## Critical Finding: Systematic Duplication

The skeptical pass revealed that most "HAS_CALLERS" reclassifications from Pass 1 were **incorrect**. The codebase contains systematic duplication:

```
Production code (app/api/, app/worker/)
  ↓ imports from
Legacy trees (app/billing/, app/costsim/, app/policy/, app/services/)
  ≠
HOC tree (app/hoc/cus/{domain}/L5_engines/)
```

**The HOC versions are copies of legacy code with identical function signatures but DIFFERENT import paths.** Production code imports the legacy version, not the HOC version. This means most HOC L5 engines are truly UNWIRED duplicates.

**Exception:** A few files ARE wired — via HOC-internal cross-imports (hoc_spine, other domains) or legacy shim re-exports.

---

## Classification Key

| Status | Meaning | Action |
|--------|---------|--------|
| DUPLICATE_OF_LEGACY | Identical to legacy file, zero HOC callers | DELETE when legacy deleted, or wire during cutover |
| WIRED_HOC_INTERNAL | Called by hoc_spine or other HOC domains | KEEP — already functional |
| WIRED_VIA_SHIM | Called through legacy re-export shim | Migrate callers to HOC path |
| CONFIRMED_UNWIRED | No callers anywhere, not a duplicate | Evaluate: delete or wire |
| BROKEN_IMPORT | Cannot even be imported (missing deps) | Fix or delete |
| FUTURE_SCAFFOLDING | Designed for planned feature, not yet integrated | Mark with PIN reference |

---

## Domain: account (8 entries)

| Symbol | File | Status | Evidence |
|--------|------|--------|----------|
| get_billing_provider | billing_provider_engine.py | DUPLICATE_OF_LEGACY | Identical to `app/billing/provider.py`. All production imports use `app.billing.provider`. Zero HOC imports. |
| set_billing_provider | billing_provider_engine.py | DUPLICATE_OF_LEGACY | Same as above. |
| create_default_identity_chain | identity_resolver_engine.py | CONFIRMED_UNWIRED | Zero callers. Active callers use renamed `create_identity_chain()` in `app/auth/`. |
| get_governance_config | profile_engine.py | DUPLICATE_OF_LEGACY | Identical to `app/services/governance/profile.py`. HOC callers use `hoc_spine/authority/profile_policy_mode.py` instead. |
| get_governance_profile | profile_engine.py | DUPLICATE_OF_LEGACY | Same file, same pattern. |
| load_governance_config | profile_engine.py | DUPLICATE_OF_LEGACY | Same. |
| reset_governance_config | profile_engine.py | DUPLICATE_OF_LEGACY | Same. |
| validate_governance_at_startup | profile_engine.py | DUPLICATE_OF_LEGACY | `app/main.py` calls from `app.services.governance.profile`. |
| validate_governance_config | profile_engine.py | DUPLICATE_OF_LEGACY | Same. |

**Wiring strategy:** When `app/services/` is deleted, rewire callers in `app/main.py`, `app/startup/boot_guard.py` to HOC paths. The account L5 engine OR hoc_spine authority file becomes canonical.

---

## Domain: activity (4 entries)

| Symbol | File | Status | Evidence |
|--------|------|--------|----------|
| detect_orphaned_runs | orphan_recovery_driver.py | DUPLICATE_OF_LEGACY | Internal helper called by `recover_orphaned_runs`. Legacy `app/services/orphan_recovery.py` is what `app/main.py:584` imports. |
| get_crash_recovery_summary | orphan_recovery_driver.py | CONFIRMED_UNWIRED | Zero callers in any version. Ops dashboard scaffolding never completed. |
| mark_run_as_crashed | orphan_recovery_driver.py | DUPLICATE_OF_LEGACY | Internal helper, same pattern as detect_orphaned_runs. |
| recover_orphaned_runs | orphan_recovery_driver.py | DUPLICATE_OF_LEGACY | `app/main.py:584` imports from `app.services.orphan_recovery`, not HOC. |

**Wiring strategy:** Rewire `app/main.py` startup to import from HOC L6 driver.

---

## Domain: analytics (48 entries)

### L5 Engines

| File | Status | Evidence |
|------|--------|----------|
| canary_engine.py | DUPLICATE_OF_LEGACY | All callers import `app.costsim.canary`. HOC file is separate copy. |
| config_engine.py | DUPLICATE_OF_LEGACY | All callers import `app.costsim.config`. |
| cost_snapshots_engine.py | DUPLICATE_OF_LEGACY | Script imports `app.integrations.cost_snapshots`. |
| datasets_engine.py | DUPLICATE_OF_LEGACY | API imports `app.costsim.datasets`. |
| divergence_engine.py | DUPLICATE_OF_LEGACY | API imports `app.costsim.divergence`. |
| envelope_engine.py | CONFIRMED_UNWIRED | Zero callers in any location. Future M10 utility. |
| metrics_engine.py | DUPLICATE_OF_LEGACY | All callers import `app.costsim.metrics`. |
| prediction_engine.py | DUPLICATE_OF_LEGACY | Tests import `app.services.prediction`. No scheduler. |
| provenance_engine.py | DUPLICATE_OF_LEGACY | Callers import `app.costsim.provenance`. |
| s1_retry_backoff_engine.py | DUPLICATE_OF_LEGACY | Callers import `app.optimization.envelopes`. |
| sandbox_engine.py | DUPLICATE_OF_LEGACY | API imports `app.costsim.sandbox`. |

### L6 Drivers

| File | Status | Evidence |
|------|--------|----------|
| coordination_audit_driver.py | DUPLICATE_OF_LEGACY | Callers import `app.optimization.audit_persistence`. |
| leader_driver.py | DUPLICATE_OF_LEGACY | 51 files reference it but via `app.costsim.leader`. |
| provenance_driver.py | DUPLICATE_OF_LEGACY | Callers import `app.costsim.provenance_async`. |

**Wiring strategy:** Massive — requires cutover of `app/costsim/` → HOC. 18 legacy files to redirect. Recommended: batch cutover with `app/costsim/__init__.py` re-export shim pointing to HOC, then delete legacy files.

---

## Domain: controls (34 entries)

### L5 Engines

| File | Status | Evidence |
|------|--------|----------|
| alert_fatigue_engine.py | DUPLICATE_OF_LEGACY | Superseded by `hoc_spine/services/fatigue_controller.py` (more complete). |
| cb_sync_wrapper_engine.py | DUPLICATE_OF_LEGACY | All callers import `app.costsim.cb_sync_wrapper`. |
| cost_safety_rails_engine.py | FUTURE_SCAFFOLDING | M27 cost safety. Zero callers anywhere. |
| decisions_engine.py | DUPLICATE_OF_LEGACY | Identical to `app/protection/decisions.py`. All callers use protection module. |
| killswitch_engine.py | FUTURE_SCAFFOLDING | C3 optimization killswitch. Zero callers. |
| s2_cost_smoothing_engine.py | FUTURE_SCAFFOLDING | C3-S2 envelope. Incomplete — imports from nonexistent `app.optimization.envelope`. |

### L6 Drivers

| File | Status | Evidence |
|------|--------|----------|
| circuit_breaker_async_driver.py | DUPLICATE_OF_LEGACY | All callers import `app.costsim.circuit_breaker_async`. |
| circuit_breaker_driver.py | DUPLICATE_OF_LEGACY | All callers import `app.costsim.circuit_breaker`. |
| scoped_execution_driver.py | DUPLICATE_OF_LEGACY | Identical to `app/services/scoped_execution.py`. Zero HOC imports. |

**Wiring strategy:** Delete 3 FUTURE_SCAFFOLDING files (or tag with PIN for later). For duplicates: cutover when legacy trees deleted. alert_fatigue_engine.py should be deleted (hoc_spine version is canonical).

---

## Domain: incidents (4 entries)

| Symbol | File | Status | Evidence |
|--------|------|--------|----------|
| create_policy_evaluation_record | policy_violation_engine.py | WIRED_VIA_SHIM | `app/services/policy_violation_service.py` re-exports from HOC. |
| create_policy_evaluation_sync | policy_violation_engine.py | WIRED_VIA_SHIM | Same shim. |
| handle_policy_evaluation_for_run | policy_violation_engine.py | WIRED_VIA_SHIM | Same shim. |
| handle_policy_violation | policy_violation_engine.py | WIRED_VIA_SHIM | Same shim. |

**Wiring strategy:** Already wired via shim. When `app/services/` deleted, update callers in `prevention_engine.py` to import directly from HOC.

---

## Domain: integrations (8 entries)

| Symbol | File | Status | Evidence |
|--------|------|--------|----------|
| create_bridges | bridges_engine.py | CONFIRMED_UNWIRED | Helper unused. Bridge classes are instantiated manually in `app/integrations/__init__.py`. |
| register_all_bridges | bridges_engine.py | CONFIRMED_UNWIRED | Same — convenience wrapper, bypassed. |
| check_channel_health | channel_engine.py | WIRED_HOC_INTERNAL | Imported by `hoc/api/cus/policies/notifications.py`, `hoc_spine/orchestrator/handlers/account_handler.py`. |
| get_channel_config | channel_engine.py | WIRED_HOC_INTERNAL | Same callers. |
| get_notify_service | channel_engine.py | WIRED_HOC_INTERNAL | Same callers. |
| send_notification | channel_engine.py | WIRED_HOC_INTERNAL | Same callers. |
| external_response_driver (all) | external_response_driver.py | CONFIRMED_UNWIRED | Zero callers in HOC or legacy. Dead code. |
| get_worker_registry_service | worker_registry_driver.py | DUPLICATE_OF_LEGACY | Legacy `app/services/worker_registry_service.py` is active. |

---

## Domain: logs (20 entries)

| File | Status | Evidence |
|------|--------|----------|
| traces_models.py | DUPLICATE_OF_LEGACY | Working alternative: `app/traces/models.py`. |
| capture_driver.py | DUPLICATE_OF_LEGACY | Working alternative: `app/evidence/capture.py`. |
| idempotency_driver.py | DUPLICATE_OF_LEGACY | Working alternative: `app/traces/idempotency.py`. |
| integrity_driver.py | DUPLICATE_OF_LEGACY | Working alternative: `app/evidence/integrity.py`. |
| job_execution_driver.py | DUPLICATE_OF_LEGACY | Working alternative: `app/services/scheduler/job_execution.py`. |
| replay_driver.py | DUPLICATE_OF_LEGACY | Working alternative: `app/traces/replay.py`. |
| traces_store.py | BROKEN_IMPORT | `from .models import TraceRecord` fails — `L6_drivers/models.py` MISSING. |

**Wiring strategy:** These require cutover of `app/traces/` and `app/evidence/` to HOC. Fix broken import in traces_store.py first. Major effort — recommend deferring to dedicated PIN.

---

## Domain: policies (27 entries)

### WIRED (via HOC-internal imports)

| Symbol | File | Status |
|--------|------|--------|
| get_limits_query_engine | policies_limits_query_engine.py | WIRED_HOC_INTERNAL |
| get_proposals_query_engine | policies_proposals_query_engine.py | WIRED_HOC_INTERNAL |
| get_policy_rules_query_engine | policies_rules_query_engine.py | WIRED_HOC_INTERNAL |
| resolve_policy_conflict + helpers | policy_conflict_resolver.py | WIRED_HOC_INTERNAL |
| policy_proposal_engine (all) | policy_proposal_engine.py | WIRED_HOC_INTERNAL |
| get/set_protection_provider | protection_provider.py | WIRED_HOC_INTERNAL |

### NOT WIRED

| Symbol | File | Status |
|--------|------|--------|
| determine_claim_status etc. | claim_decision_engine.py | CONFIRMED_UNWIRED |
| parse, parse_condition | dsl_parser.py | DUPLICATE_OF_LEGACY |
| snapshot_engine (all) | snapshot_engine.py | PARTIALLY_WIRED |

**Note on policies query engines:** The skeptical pass found zero imports of `from app.hoc.cus.policies.L5_engines` in production code. However, these engines are wired through the L4 operation registry pattern — the hoc_spine operation handlers call them. This is legitimate HOC-internal wiring.

---

## Summary Statistics

| Status | Count | Action |
|--------|-------|--------|
| DUPLICATE_OF_LEGACY | ~85 | Wire during legacy deletion cutover |
| WIRED_HOC_INTERNAL | ~25 | Already functional, no action |
| WIRED_VIA_SHIM | ~4 | Migrate callers when shim deleted |
| CONFIRMED_UNWIRED | ~15 | Evaluate: delete or wire |
| FUTURE_SCAFFOLDING | ~6 | Tag with PIN, defer |
| BROKEN_IMPORT | ~1 | Fix import path |
| PARTIALLY_WIRED | ~6 | Needs investigation |

---

## Recommended Execution Order

### Phase A: Quick Wins (zero-risk)
1. Delete `alert_fatigue_engine.py` (controls) — superseded by hoc_spine version
2. Delete `decisions_engine.py` (controls) — identical to `app/protection/decisions.py`
3. Delete `external_response_driver.py` (integrations) — zero callers everywhere
4. Delete `bridges_engine.py` helper functions or entire file (integrations)
5. Delete `claim_decision_engine.py` (policies) — Phase R-4 moved logic inline

### Phase B: Fix Broken Code
1. ~~Fix `traces_store.py` broken import~~ **DONE** — Changed `from .models import ...` to `from app.hoc.cus.logs.L5_engines.traces_models import ...`. Import verified working.

### Phase C: Legacy Cutover (by legacy tree)
This is the bulk work. Each legacy tree should be cut over as a unit:

| Legacy Tree | HOC Target | Files | Effort |
|-------------|-----------|-------|--------|
| `app/costsim/` | `hoc/cus/analytics/` + `controls/` | 18 files | ~~HIGH~~ **DONE** (5 TRANSITIONAL remain) |
| `app/traces/` | `hoc/cus/logs/` | 6 files | ~~MEDIUM~~ **DONE** |
| `app/evidence/` | `hoc/cus/logs/` | 3 files | ~~MEDIUM~~ **DONE** |
| `app/billing/provider.py` | `hoc/cus/account/` | 1 file | ~~LOW~~ **DONE** |
| `app/services/governance/profile.py` | `hoc_spine/authority/` | 1 file | ~~LOW~~ **DONE** |
| `app/services/orphan_recovery.py` | `hoc/cus/activity/` | 1 file | ~~LOW~~ **DONE** |

#### Phase C LOW Execution Log

| Legacy Source | HOC Target | Callers Updated | Files Modified |
|---------------|-----------|-----------------|----------------|
| `app.billing.provider` | `app.hoc.cus.account.L5_engines.billing_provider_engine` | 4 (skipped `app/billing/__init__.py` — legacy) | `api/billing_dependencies.py`, `api/middleware/billing_gate.py`, `hoc/api/int/policies/billing_gate.py`, `hoc/api/cus/policies/billing_dependencies.py` |
| `app.services.governance.profile` | `app.hoc.cus.hoc_spine.authority.profile_policy_mode` | 3 | `events/reactor_initializer.py`, `startup/boot_guard.py` (×2), `policy/failure_mode_handler.py` |
| `app.services.orphan_recovery` | `app.hoc.cus.activity.L6_drivers.orphan_recovery_driver` | 2 | `app/main.py`, `hoc/api/int/agent/main.py` |

#### Phase C MEDIUM Execution Log

| Legacy Source | HOC Target | Callers Updated | Files Modified |
|---------------|-----------|-----------------|----------------|
| `app.traces.models` | `app.hoc.cus.logs.L5_engines.traces_models` | 3 | `runtime/replay.py`, `hoc/int/platform/engines/replay.py`, `hoc/cus/logs/L5_engines/logs_read_engine.py` |
| `app.traces.store` | `app.hoc.cus.logs.L6_drivers.traces_store` | 3 | `runtime/replay.py`, `hoc/int/platform/engines/replay.py`, `hoc/cus/incidents/L6_drivers/export_bundle_driver.py` |
| `app.traces.pg_store` | `app.hoc.cus.logs.L6_drivers.pg_store` | 3 | `runtime/replay.py`, `hoc/int/platform/engines/replay.py`, `hoc/cus/logs/L5_engines/logs_read_engine.py` |
| `app.traces.idempotency` | `app.hoc.cus.logs.L6_drivers.idempotency_driver` | 1 | `stores/__init__.py` |
| `app.evidence.capture` | `app.hoc.cus.logs.L6_drivers.capture_driver` | 6 | `api/workers.py`, `hoc/api/cus/policies/workers.py`, `skills/executor.py` (×2), `worker/runner.py`, `hoc/int/agent/engines/executor.py` (×2), `hoc/int/analytics/engines/runner.py` |

**Remaining `app.traces` imports:** Only in `app/services/` (legacy, will be bulk-deleted).
**Remaining `app.evidence` imports:** Only in `app/evidence/` itself (legacy tree internal).

#### Phase C HIGH Execution Log (`app/costsim/`)

**13 files modified, 34 import statements rewired.**

| File | Imports Swapped | TRANSITIONAL Remaining |
|------|----------------|----------------------|
| `analytics/L5_engines/divergence_engine.py` | 3 (config, models, provenance) | 0 |
| `analytics/L5_engines/sandbox_engine.py` | 3 (cb_async, config, models) | 1 (`v2_adapter`) |
| `analytics/L5_engines/metrics_engine.py` | 1 (config) | 0 |
| `analytics/L5_engines/provenance_engine.py` | 1 (config) | 0 |
| `analytics/L5_engines/canary_engine.py` | 5 (cb_async, config, leader, models, provenance) | 2 (`circuit_breaker`, `v2_adapter`) |
| `analytics/L5_engines/datasets_engine.py` | 1 (models) | 1 (`v2_adapter`) |
| `controls/L6_drivers/circuit_breaker_driver.py` | 1 (config) | 0 |
| `controls/L6_drivers/circuit_breaker_async_driver.py` | 3 (config, metrics, cb_sync) | 0 |
| `controls/L5_engines/cb_sync_wrapper_engine.py` | 2 (cb_async ×2) | 0 |
| `api/costsim.py` | 6 (config, canary, sandbox, divergence, datasets ×2) | 1 (`circuit_breaker`) |
| `hoc/api/cus/analytics/costsim.py` | 6 (config, canary, sandbox, divergence, datasets ×2) | 1 (`circuit_breaker`) |

**TRANSITIONAL imports remaining (5 total, 2 root causes):**

| Root Cause | Files Affected | Sever When |
|------------|---------------|------------|
| `app.costsim.v2_adapter.CostSimV2Adapter` — no HOC engine exists | 3 (sandbox, datasets, canary) | Extract CostSimV2Adapter to HOC analytics L5 engine |
| `app.costsim.circuit_breaker.get_circuit_breaker()` — HOC `create_circuit_breaker(session)` has different signature (requires session) | 3 (api/costsim ×2, canary) | Refactor callers to pass session, or add backward-compat alias |

### Phase D: Future Scaffolding — DELETED (all 4 were duplicates)

All 4 files had zero callers and working production equivalents elsewhere. None were genuine future scaffolding.

| File | Production Equivalent | Reason |
|------|----------------------|--------|
| `controls/L5_engines/cost_safety_rails_engine.py` | `app/integrations/cost_safety_rails.py` | Duplicate with wrong imports |
| `controls/L5_engines/killswitch_engine.py` | `app/optimization/killswitch.py` | Duplicate, 58 files use production version |
| `controls/L5_engines/s2_cost_smoothing_engine.py` | `app/optimization/envelopes/s2_cost_smoothing.py` | Duplicate with broken imports |
| `analytics/L5_engines/envelope_engine.py` | `app/optimization/envelope.py` | Duplicate, even HOC files import from production |

---

## Decisions (Resolved)

1. **DUPLICATE_OF_LEGACY files:** Keep for cutover, mark with `MARKED_FOR_DELETION` header. Do NOT delete until callers are rewired.
2. **`app/costsim/` cutover strategy:** Update all callers at once (no re-export shims).
3. **Governance config:** Both files are **100% identical** (460 lines, same functions, same logger). `hoc_spine/authority/profile_policy_mode.py` is canonical (governance is cross-domain → L4 spine). `account/L5_engines/profile_engine.py` is DUPLICATE — marked for deletion during cutover.

## Phase A Execution Log

| # | File | Action | Status |
|---|------|--------|--------|
| 1 | `controls/L5_engines/alert_fatigue_engine.py` | MARKED_FOR_DELETION (superseded by hoc_spine) | DONE |
| 2 | `controls/L5_engines/decisions_engine.py` | MARKED_FOR_DELETION (duplicate of app/protection/) | DONE |
| 3 | `integrations/L6_drivers/external_response_driver.py` | DELETED (zero callers everywhere) | DONE |
| 4 | `integrations/L5_engines/_frozen/bridges_engine.py` | DELETED (helper functions unused, classes wired elsewhere) | DONE |
| 5 | `policies/L5_engines/claim_decision_engine.py` | DELETED (Phase R-4 moved logic inline) | DONE |

## Phase B Execution Log

| # | File | Action | Status |
|---|------|--------|--------|
| 1 | `logs/L6_drivers/traces_store.py:39` | Fixed broken relative import → absolute HOC import | DONE |

## Phase C Execution Log

### LOW effort

| # | Legacy Tree | Files Rewired | Status |
|---|------------|---------------|--------|
| 1 | `app/billing/provider.py` → `billing_provider_engine` | 4 files | DONE |
| 2 | `app/services/governance/profile.py` → `hoc_spine/authority/profile_policy_mode` | 3 files (4 imports) | DONE |
| 3 | `app/services/orphan_recovery.py` → `orphan_recovery_driver` | 2 files | DONE |

### MEDIUM effort

| # | Legacy Tree | Files Rewired | Status |
|---|------------|---------------|--------|
| 1 | `app/traces/` → `hoc/cus/logs/` | 5 files | DONE |
| 2 | `app/evidence/` → `hoc/cus/logs/L6_drivers/capture_driver` | 6 files | DONE |

### HIGH effort (costsim cutover)

| # | Action | Files | Status |
|---|--------|-------|--------|
| 1 | Rewired 34 import statements across 13 files | analytics, controls, api | DONE |
| 2 | 5 TRANSITIONAL imports tagged (v2_adapter ×3, circuit_breaker ×2) | — | Resolved in TRANSITIONAL phase |

## Phase D Execution Log

| # | File | Action | Status |
|---|------|--------|--------|
| 1 | `controls/L5_engines/cost_safety_rails_engine.py` | DELETED (duplicate of app/integrations/) | DONE |
| 2 | `controls/L5_engines/killswitch_engine.py` | DELETED (duplicate of app/optimization/) | DONE |
| 3 | `controls/L5_engines/s2_cost_smoothing_engine.py` | DELETED (duplicate, broken imports) | DONE |
| 4 | `analytics/L5_engines/envelope_engine.py` | DELETED (duplicate of app/optimization/) | DONE |

## TRANSITIONAL Resolution Log

| # | Import | File(s) | Resolution | Status |
|---|--------|---------|------------|--------|
| 1 | `from app.costsim.v2_adapter import CostSimV2Adapter` | sandbox_engine, datasets_engine, canary_engine | Created `v2_adapter_engine.py` (new HOC L5 engine, 375 lines). Rewired all 3 imports. | DONE |
| 2 | `from app.costsim.circuit_breaker import get_circuit_breaker` | api/costsim, hoc/api/cus/analytics/costsim, canary_engine | Added `get_circuit_breaker` alias to `circuit_breaker_async_driver.py` (maps to `get_async_circuit_breaker`). Rewired all 3 imports. | DONE |

**New file:** `app/hoc/cus/analytics/L5_engines/v2_adapter_engine.py` — HOC version of `app/costsim/v2_adapter.py`. Note: still has 2 lazy imports from `app.services.cost_model_engine` (L4 delegation, separate cutover scope).

**Alias added:** `circuit_breaker_async_driver.get_circuit_breaker = get_async_circuit_breaker`

**Result:** All 5 TRANSITIONAL imports fully severed. Zero `from app.costsim` imports remain in HOC callers or API layer.

## PIN-513 Phase 7: Reverse Boundary Severing — COMPLETE (2026-02-01)

**Goal:** Eliminate `from app.services` imports inside `app/hoc/`.

**Result:** All 8 planned steps were already resolved by Wiring Plan phases A–D and TRANSITIONAL resolution. Verification grep confirms zero `from app.services` code imports in `app/hoc/` — only docstring references remain in 4 hoc_spine facade files (false positives) and 3 lazy imports in `v2_adapter_engine.py` (deferred, separate PIN for cost_model_engine).

**Remaining `from app.services` in `app/hoc/` (non-actionable):**
- ~~`v2_adapter_engine.py` ×3~~ — RESOLVED: rewired to HOC `cost_model_engine.py` (copy already existed)
- ~~`hoc_spine/services/` ×4~~ — RESOLVED: docstring examples updated to HOC paths
- `hoc/duplicate/`, `.deprecated` files — dead code (not in scope)

**Final state:** Zero `from app.services` code imports in `app/hoc/` Python files. Only comment/docstring references and dead code remain.

## PIN-513 Phase 8: Zero-Caller Component Wiring — COMPLETE (2026-02-01)

**Goal:** Wire 9 DUPLICATE_OF_LEGACY files that had zero L4 callers. Root cause: pre-PIN-510 components implemented without L4 entrypoints.

**Principle:** Every executable capability must have exactly one L4 entrypoint (handler, coordinator, or utility).

| # | Component | Owner Created | Type | Status |
|---|-----------|--------------|------|--------|
| 1 | `cost_snapshots_engine` | `handlers/analytics_snapshot_handler.py` | NEW L4 handler | DONE |
| 2 | `prediction_engine` | `handlers/analytics_prediction_handler.py` | NEW L4 handler | DONE |
| 3 | `s1_retry_backoff_engine` | Moved to `hoc_spine/utilities/s1_retry_backoff.py` | Utility (SHARED) | DONE |
| 4 | `coordination_audit_driver` | Injected into `anomaly_incident_coordinator.py` | Method addition | DONE |
| 5 | `scoped_execution_driver` | `coordinators/execution_coordinator.py` | NEW L4 coordinator | DONE |
| 6 | `integrity_driver` | Injected into `incidents/L5_engines/export_engine.py` | Method addition | DONE |
| 7 | `job_execution_driver` | `coordinators/execution_coordinator.py` | NEW L4 coordinator (shared) | DONE |
| 8 | `replay_driver` | `coordinators/replay_coordinator.py` | NEW L4 coordinator | DONE |
| 9 | `worker_registry_driver` | `handlers/integrations_handler.py` (IntegrationsWorkersHandler) | Handler class addition | DONE |

**New files created (4):**
- `hoc_spine/orchestrator/handlers/analytics_snapshot_handler.py` — routes scheduled snapshot computation to CostSnapshotsEngine (L5)
- `hoc_spine/orchestrator/handlers/analytics_prediction_handler.py` — routes prediction queries to PredictionEngine (L5)
- `hoc_spine/orchestrator/coordinators/execution_coordinator.py` — binds ScopedExecutionDriver + JobExecutionDriver (L6)
- `hoc_spine/orchestrator/coordinators/replay_coordinator.py` — binds ReplayDriver (L6)

**Files modified (4):**
- `hoc_spine/utilities/s1_retry_backoff.py` — moved from `analytics/L5_engines/`, header updated to L4 Spine Utility / SHARED
- `hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py` — added `persist_coordination_audit()` method (delegates to coordination_audit_driver L6)
- `incidents/L5_engines/export_engine.py` — added `export_with_integrity()` method (delegates to integrity_driver L6)
- `hoc_spine/orchestrator/handlers/integrations_handler.py` — added `IntegrationsWorkersHandler` class (delegates to worker_registry_driver L6)

**Files deleted (1):**
- `analytics/L5_engines/s1_retry_backoff_engine.py` — moved to hoc_spine/utilities/

**Result:** All 9 zero-caller components now have L4 entrypoints. DUPLICATE_OF_LEGACY count reduced by 9.

### Phase 8 Signature Audit & Fix (2026-02-01)

Skeptical codebase audit found 13 critical signature mismatches in 3 of 4 skeleton files. All fixed:

| File | Issues Found | Fix Applied |
|------|-------------|-------------|
| `analytics_snapshot_handler.py` | `evaluate_snapshot` passed spurious `tenant_id` | Removed `tenant_id` (actual sig: `snapshot_id, threshold_pct`) |
| `analytics_prediction_handler.py` | All 4 methods passed `session` instead of `driver` | Added `get_prediction_driver(session)` for driver-requiring methods; removed `session` from session-less methods |
| `execution_coordinator.py` | `create_scope` used `allowed_actions: List` (actual: `action: str`); `execute_with_scope` used wrong param names; `JobRetryManager/ProgressTracker/AuditEmitter` constructors wrong | Matched all signatures to actual L6 driver APIs; split generic `emit_audit` into `emit_audit_created/completed/failed` |
| `replay_coordinator.py` | `enforce_step` passed individual params (actual: `step: dict`); `enforce_trace` passed `steps` (actual: `trace: dict, step_executor`) | Matched signatures to `ReplayEnforcer` API |

**Method injections (3) verified clean — no fixes needed:**
- `anomaly_incident_coordinator.persist_coordination_audit` — exact match
- `export_engine.export_with_integrity` — exact match
- `integrations_handler.IntegrationsWorkersHandler` — all 7 methods match

### Phase 8 "Zero-Caller" Premise Clarification

The "zero-caller" label refers to callers of the **HOC copy** (`app/hoc/cus/...` path), not the legacy original. Audit confirmed 7/9 HOC copies genuinely had zero HOC-path callers. Exception: `coordination_audit_driver` had 1 pre-existing HOC caller (`coordinator_engine.py`). Legacy originals at `app/services/`, `app/traces/`, etc. retain their active callers — expected until legacy bulk-deletion.

---

## Phase 9: Batch 1 Wiring (PIN-513, 2026-02-01)

**Scope:** 24 symbols across 4 domains (activity, incidents, account, integrations).

### Batch 1A — Activity (4 symbols)

**Root cause:** L6 driver violated "no implicit execution" — created own sessions, scheduled itself.

| Action | Detail |
|--------|--------|
| Created | `hoc_spine/orchestrator/handlers/orphan_recovery_handler.py` |
| Stripped | `recover_orphaned_runs()` + `get_crash_recovery_summary()` from L6 driver |
| Rewired | `main.py:584` now calls `OrphanRecoveryHandler().execute()` (was direct L6 import) |
| Result | L6 is pure data access; L4 owns session + commit + scheduling |

### Batch 1B — Incidents (4 symbols)

**Root cause:** Run-lifecycle side effects had no L4 owner.

| Action | Detail |
|--------|--------|
| Created | `hoc_spine/orchestrator/handlers/run_governance_handler.py` |
| Wired | `handle_policy_evaluation_for_run` → `RunGovernanceHandler.evaluate_run()` |
| Wired | `handle_policy_violation` → `RunGovernanceHandler.report_violation()` |
| Wired | `create_policy_evaluation_record` → `RunGovernanceHandler.create_evaluation()` |
| Reclassified | `create_policy_evaluation_sync` — already wired via `RunGovernanceFacade` |

### Batch 1C — Account (9 symbols)

**First-principles decision:** Identity resolution and governance profile are authority-level, not domain-level.

| Action | Detail |
|--------|--------|
| Tombstoned | `identity_resolver_engine.py` — marked `TOPOLOGY_DEAD` |
| Tombstoned | `profile_engine.py` (6 symbols) — marked `TOPOLOGY_DEAD` |
| Canonical | `hoc_spine/authority/profile_policy_mode.py` (governance) |
| Canonical | `hoc_spine/authority/` (identity — separate PIN) |
| Reclassified | `billing_provider_engine.py` (2 symbols) — already wired, CSV stale |

### Batch 1D — Integrations (10 symbols)

| Action | Detail |
|--------|--------|
| Created | `hoc_spine/orchestrator/handlers/integration_bootstrap_handler.py` |
| Wired | `get_notify_service` → `IntegrationBootstrapHandler.initialize()` |
| Wired | `send_notification` → `IntegrationBootstrapHandler.send_notification()` |
| Wired | `check_channel_health` → `IntegrationBootstrapHandler.check_health()` |
| Wired | `get_channel_config` → `IntegrationBootstrapHandler.get_channel_config()` |
| Reclassified | `worker_registry_driver` — already wired via Phase 8 `IntegrationsWorkersHandler` |
| Out of scope | `bridges_engine` (2) — lives in legacy `app/integrations/`, not HOC |
| Out of scope | `external_response_driver` (3) — lives in `hoc/int/`, not `hoc/cus/` |

### Batch 1 Tally

| Category | Count |
|----------|-------|
| Newly wired (L4 handler created) | 11 |
| Already wired (CSV stale) | 4 |
| TOPOLOGY_DEAD (tombstoned) | 7 |
| OUT_OF_SCOPE (wrong tree) | 5 |
| REMOVED from L6 (moved to L4) | 1 |
| **Total resolved** | **24** (was 24) |

Remaining UNWIRED after Batch 1: **131** (was 155, minus 24 resolved).

---

## Phase 9 Batch 2: Controls + Policies (2026-02-01)

**Scope:** 59 symbols (33 controls + 26 policies).

### Controls (Batch 2A)

| Action | Count | Handler/Resolution |
|--------|-------|--------------------|
| PHANTOM_NO_HOC_COPY | 13 | cost_safety_rails_engine, killswitch_engine, s2_cost_smoothing_engine |
| TOPOLOGY_DEAD | 7 | alert_fatigue_engine, decisions_engine (tombstoned) |
| WIRED | 11 | circuit_breaker_handler.py |
| Already wired | 2 | scoped_execution_driver (Phase 8) |

### Policies (Batch 2B)

| Action | Count | Handler/Resolution |
|--------|-------|--------------------|
| PHANTOM_NO_HOC_COPY | 3 | claim_decision_engine |
| WIRED query handlers | 3 | policies_handler.py (3 new handler classes) |
| WIRED pure import | 6 | dsl_parser (2), conflict_resolver (4) |
| WIRED governance | 13 | policy_governance_handler.py |
| WIRED middleware | 2 | protection_provider |

### Tally Update

| Metric | Before Batch 2 | After Batch 2 |
|--------|----------------|---------------|
| Total UNWIRED | 131 | 72 |
| Newly wired | — | 36 |
| PHANTOM reclassified | — | 16 |
| TOPOLOGY_DEAD | — | 7 |
| Remaining UNWIRED | 131 | 72 |

---

## Phase 9 Batch 3: Analytics + Logs (2026-02-01)

**Scope:** 66 symbols (46 analytics + 20 logs).

### Analytics (Batch 3A)

| Action | Count | Handler/Resolution |
|--------|-------|--------------------|
| PHANTOM_NO_HOC_COPY | 5 | envelope_engine (source deleted) |
| CSV stale | 6 | cost_snapshots, prediction, s1_retry_backoff, coordination_audit |
| WIRED_VIA_PARENT | 3 | prediction sub-functions |
| PURE_INFRA_UTILITY | 3 | provenance_engine |
| WIRED (new handlers) | 29 | canary_coordinator, analytics_config_handler, analytics_validation_handler, analytics_metrics_handler, analytics_sandbox_handler, leadership_coordinator, provenance_coordinator |

### Logs (Batch 3B)

| Action | Count | Handler/Resolution |
|--------|-------|--------------------|
| CSV stale | 6 | job_execution_driver, replay_driver |
| PURE_UTILITY | 3 | traces_models, traces_store |
| WIRED (new handlers) | 11 | evidence_coordinator, integrity_handler, idempotency_handler |

### Tally Update

| Metric | Before Batch 3 | After Batch 3 |
|--------|----------------|---------------|
| Total UNWIRED | 72 | 6 |
| Newly wired (analytics) | — | 29 |
| Newly wired (logs) | — | 11 |
| PHANTOM reclassified | — | 5 |
| CSV stale fixed | — | 12 |
| PURE_UTILITY | — | 6 |
| Remaining UNWIRED | 72 | **6** |

---

## Phase 9 Batch 4: Deletion & Final Hygiene (2026-02-01)

**Scope:** 53 deletions + 1 new coordinator + 2 final UNWIRED resolved.

### Phase 1: Orphaned .pyc Cleanup
- **26 orphaned .pyc files deleted** across 8 domains (19 initial + 7 from Phase 2-5 deletions)

### Phase 2: TOPOLOGY_DEAD Source Deletion
- `account/L5_engines/identity_resolver_engine.py` — canonical: hoc_spine/authority/
- `account/L5_engines/profile_engine.py` — canonical: hoc_spine/authority/profile_policy_mode.py
- `controls/L5_engines/alert_fatigue_engine.py` — canonical: hoc_spine/services/fatigue_controller.py
- `controls/L5_engines/decisions_engine.py` — canonical: app/protection/decisions.py

### Phase 3: hoc/duplicate/ Bulk Deletion
- **26 files deleted** (entire deprecated staging tree)

### Phase 4: REDUNDANT Deletion
- `controls/L5_engines/customer_killswitch_read_engine.py` — zero callers, zero logic
- `controls/adapters/customer_killswitch_adapter.py` — zero callers

### Phase 5: REDUNDANT_DEBATABLE Resolution
- `analytics/L5_engines/cost_write_engine.py` — **DELETED** (zero-logic passthrough, no decision boundary, zero callers)
- Decision: topology does NOT mandate zero-logic L5 wrappers

### Final Wiring
- Created `hoc_spine/orchestrator/coordinators/snapshot_scheduler.py` — L4: multi-tenant scheduled snapshot batch execution
- Wired last 2 UNWIRED symbols: `run_hourly_snapshot_job`, `run_daily_snapshot_and_baseline_job`

### Acceptance Criteria Verified
- `grep UNWIRED CSV` → **0 data rows**
- `grep TOPOLOGY_DEAD source` → **0 files**
- Orphaned `.pyc` → **0**
- `hoc/duplicate/` → **deleted**
- Zero-logic L5 wrappers → **0**

### Final Tally

| Metric | Value |
|--------|-------|
| Total UNWIRED at start (PIN-513) | 155 |
| **Remaining UNWIRED** | **0** |
| Files deleted (Batch 4) | 33 (4 source + 3 redundant + 26 duplicate/) |
| .pyc orphans cleaned | 26 |
| New coordinators | 1 (snapshot_scheduler) |

---

## Batch 5: Invariant Hardening (2026-02-01) — COMPLETE

**Scope:** 4 new CI checks (27-30) in `scripts/ci/check_init_hygiene.py`.

### Checks Implemented

| Check | Function | Rule | Allowlist |
|-------|----------|------|-----------|
| 27 | `check_l2_no_direct_l5_l6_imports` | L2 API files must not import L5_engines/L6_drivers directly — must route through L4 | 8 files frozen |
| 28 | `check_l5_no_cross_domain_l5_imports` | L5 engines must not import cross-domain L5_engines | 2 files frozen |
| 29 | `check_driver_no_l5_engine_imports_extended` | int/fdr driver files must not import L5_engines | 3 files frozen |
| 30 | `check_facade_logic_minimum` | Zero-logic facade detection | Advisory (non-blocking) |

### Frozen Allowlists

**Check 27 (L2→L5/L6 bypass):**
`recovery.py`, `recovery_ingest.py`, `billing_dependencies.py`, `workers.py`, `costsim.py`, `cost_intelligence.py`, `billing_gate.py`, `main.py`

**Check 28 (L5→L5 cross-domain):**
`recovery_evaluation_engine.py`, `cost_anomaly_detector_engine.py`

**Check 29 (driver→L5 extended):**
`tenant_config.py`, `hallucination_hook.py`, `failure_classification_engine.py`

### Verification

CI run: 16 blocking violations (all pre-existing from checks 4, 5, 10, 12, 13, 21). Zero new violations from checks 27-30. All allowlists are `frozenset[str]` — any NEW file introducing these violations will fail CI.

### Tally

| Metric | Value |
|--------|-------|
| New CI checks | 4 (27-30) |
| Total CI checks | 30 |
| Pre-existing violations frozen | 13 (8+2+3) |
| New blocking violations | 0 |
