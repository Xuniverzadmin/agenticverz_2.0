# UC Script Coverage Wave-1: Policies + Logs — Implementation Evidence

- Date: 2026-02-12
- Scope: Classify 130 unlinked scripts in policies (91) + logs (39) domains
- Sources: `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`
- Result: 33 UC_LINKED + 97 NON_UC_SUPPORT + 0 DEPRECATED

## 1) Before/After Counts

### Before Wave-1
| Domain | Total Scripts | UC_LINKED | Unlinked | Coverage |
|--------|-------------|-----------|----------|----------|
| policies | 100 | 9 | 91 | 9.0% |
| logs | 44 | 5 | 39 | 11.4% |
| **Total** | **144** | **14** | **130** | **9.7%** |

### After Wave-1
| Domain | Total Scripts | UC_LINKED | NON_UC_SUPPORT | Unclassified | Coverage |
|--------|-------------|-----------|----------------|--------------|----------|
| policies | 100 | 25 | 75 | 0 | 100% classified |
| logs | 44 | 22 | 22 | 0 | 100% classified |
| **Total** | **144** | **47** | **97** | **0** | **100% classified** |

### Delta
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Policies UC_LINKED | 9 | 25 | +16 |
| Logs UC_LINKED | 5 | 22 | +17 |
| Total UC_LINKED | 14 | 47 | +33 |
| Unclassified | 130 | 0 | -130 |

## 2) Classification Breakdown

### Policies Domain (91 scripts)

**UC_LINKED (16 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/engine.py` | UC-009 | Policy rule evaluation engine, emits policy_evaluation_complete |
| `L5_engines/cus_enforcement_engine.py` | UC-009 | Enforcement decisions (HARD_BLOCKED→ALLOWED hierarchy) |
| `L5_engines/policy_proposal_engine.py` | UC-009 | Proposal state machine (Propose→Review→Decide) |
| `L5_engines/deterministic_engine.py` | UC-018 | Reproducible policy execution (M20/PLang v2.0) |
| `L5_engines/recovery_evaluation_engine.py` | UC-029 | Recovery decision generation (M9/M10 pattern) |
| `L5_engines/lessons_engine.py` | UC-023 | Lessons learned creation (SDSR pattern) |
| `L6_drivers/policy_engine_driver.py` | UC-009 | Evaluation/violation persistence |
| `L6_drivers/cus_enforcement_driver.py` | UC-009 | Enforcement data persistence |
| `L6_drivers/policy_proposal_read_driver.py` | UC-019 | Proposal read operations |
| `L6_drivers/policy_proposal_write_driver.py` | UC-019 | Proposal write operations |
| `L6_drivers/prevention_records_read_driver.py` | UC-009 | Run-scoped evaluation ledger |
| `L6_drivers/policy_enforcement_driver.py` | UC-009 | Enforcement persistence |
| `L6_drivers/policy_enforcement_write_driver.py` | UC-009 | Enforcement write persistence |
| `L6_drivers/recovery_read_driver.py` | UC-029 | Recovery candidate reads |
| `L6_drivers/recovery_write_driver.py` | UC-029 | Recovery pattern writes |
| `L6_drivers/recovery_matcher.py` | UC-029 | Recovery matching logic |

**NON_UC_SUPPORT (75 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 7 | `__init__.py` across all subdirs |
| L5 schemas | 4 | `domain_bridge_capabilities.py`, `intent_validation.py`, `policy_check.py`, `policy_rules.py` |
| Adapters | 3 | `customer_policies_adapter.py`, `founder_contract_review_adapter.py`, `policy_adapter.py` |
| DSL compiler pipeline | 14 | `ast.py`, `compiler_parser.py`, `dsl_parser.py`, `grammar.py`, `interpreter.py`, `ir_builder.py`, `ir_compiler.py`, `ir_nodes.py`, `kernel.py`, `nodes.py`, `tokenizer.py`, `folds.py`, `visitors.py`, `decorator.py` |
| Policy infrastructure engines | 23 | `authority_checker.py`, `binding_moment_enforcer.py`, `content_accuracy.py`, `customer_policy_read_engine.py`, `dag_executor.py`, `degraded_mode.py`, `failure_mode_handler.py`, `governance_facade.py`, `intent.py`, `kill_switch.py`, `limits.py`, `limits_facade.py`, `limits_simulation_engine.py`, `llm_policy.py`, `phase_status_invariants.py`, `plan.py`, `plan_generation.py`, `policies_facade.py`, `policy_command.py`, `policy_driver.py`, `policy_graph.py`, `policy_limits_engine.py`, `policy_mapper.py`, `policy_models.py`, `policy_rules_engine.py`, `prevention_hook.py`, `protection_provider.py`, `runtime_command.py`, `sandbox_executor.py`, `state.py`, `validator.py`, `worker_execution_command.py` |
| L5_controls | 2 | `L5_controls/KillSwitch/engines/__init__.py`, `L5_controls/drivers/__init__.py` |
| Read/persistence drivers | 15 | `arbitrator.py`, `guard_read_driver.py`, `limits_simulation_driver.py`, `m25_integration_read_driver.py`, `m25_integration_write_driver.py`, `policies_facade_driver.py`, `policy_approval_driver.py`, `policy_graph_driver.py`, `policy_read_driver.py`, `policy_rules_driver.py`, `rbac_audit_driver.py`, `replay_read_driver.py`, `scope_resolver.py`, `symbol_table.py`, `workers_read_driver.py` |

### Logs Domain (39 scripts)

**UC_LINKED (17 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/certificate.py` | UC-017 | Cryptographic certificate for deterministic replay |
| `L5_engines/completeness_checker.py` | UC-017 | Evidence PDF completeness validation (SOC2) |
| `L5_engines/evidence_facade.py` | UC-017 | Centralized evidence/export access |
| `L5_engines/evidence_report.py` | UC-017 | Legal-grade PDF export for incidents |
| `L5_engines/logs_read_engine.py` | UC-003 | Logs/Traces domain read operations |
| `L5_engines/mapper.py` | UC-017 | Map incidents to SOC2 controls |
| `L5_engines/pdf_renderer.py` | UC-017 | Render export bundles to PDF |
| `L5_engines/replay_determinism.py` | UC-017 | Replay determinism validation definitions |
| `L5_engines/trace_mismatch_engine.py` | UC-003 | Trace mismatch detection and notifications |
| `L6_drivers/export_bundle_store.py` | UC-017 | Export bundle persistence |
| `L6_drivers/idempotency_driver.py` | UC-003 | Trace idempotency enforcement (Redis+Lua) |
| `L6_drivers/integrity_driver.py` | UC-017 | Integrity computation persistence |
| `L6_drivers/replay_driver.py` | UC-017 | Trace replay execution |
| `L6_drivers/trace_mismatch_driver.py` | UC-003 | Trace mismatch data access |
| `L5_schemas/determinism_types.py` | UC-017 | Determinism level definitions |
| `L5_schemas/traces_models.py` | UC-003 | Trace data models (dataclasses) |
| `adapters/customer_logs_adapter.py` | UC-003 | Customer logs boundary adapter |

**NON_UC_SUPPORT (22 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 5 | `__init__.py` across all subdirs |
| L5_support | 1 | `L5_support/CRM/engines/__init__.py` |
| Audit infrastructure | 6 | `audit_evidence.py`, `audit_ledger_engine.py`, `audit_reconciler.py`, `audit_ledger_driver.py`, `audit_ledger_read_driver.py`, `audit_ledger_write_driver_sync.py` |
| Cost intelligence | 3 | `cost_intelligence_engine.py`, `cost_intelligence_driver.py`, `cost_intelligence_sync_driver.py` |
| Logs infrastructure | 4 | `logs_facade.py`, `traces_models.py` (L5 re-export), `logs_domain_store.py`, `panel_consistency_driver.py` |
| Other drivers | 3 | `bridges_driver.py`, `capture_driver.py`, `job_execution_driver.py` |

## 3) Fixes Applied

No architecture violations found in Wave-1 scope. All newly-classified UC_LINKED L5 engines pass purity checks (0 runtime DB imports). No code changes were required.

## 4) Test Changes

| File | Before | After | Delta |
|------|--------|-------|-------|
| `test_uc018_uc032_expansion.py` | 115 tests | 163 tests | +48 |

New test class: `TestWave1ScriptCoverage`
- 15 L5 existence checks for UC_LINKED engines
- 15 L6 existence checks for UC_LINKED drivers
- 15 L5 purity checks for UC_LINKED engines
- 1 DSL compiler NON_UC_SUPPORT existence check
- 1 audit ledger NON_UC_SUPPORT existence check
- 1 total classification count validation

## 5) Gate Results

| # | Gate | Result |
|---|------|--------|
| 1 | Cross-domain validator | `status=CLEAN, count=0` |
| 2 | Layer boundaries | `CLEAN: No layer boundary violations found` |
| 3 | CI hygiene (--ci) | `All checks passed. 0 blocking violations` |
| 4 | Pairing gap detector | `wired=70, orphaned=0, direct=0` |
| 5 | UC-MON strict | `Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0` |
| 6 | Governance tests | `163 passed in 1.53s` |

**All 6 gates PASS.**

## 6) Residual Gap List

### Classified but remaining Wave-2+ domains (unlinked scripts not yet classified):

| Domain | Unlinked Count | Wave |
|--------|---------------|------|
| activity | 18 | Wave-2 |
| incidents | 35 | Wave-2 |
| analytics | 40 | Wave-2 |
| controls | 21 | Wave-3 |
| account | 28 | Wave-3 |
| hoc_spine | 170+ | Wave-4 |
| integrations | 58 | Wave-4 |
| agent | 4 | Wave-4 |
| api_keys | 8 | Wave-4 |
| apis | 2 | Wave-4 |
| ops | 3 | Wave-4 |
| overview | 5 | Wave-4 |

### Known pre-existing violations (not Wave-1 scope):
- `logs/L6_drivers/trace_store.py`: 7 L6_TRANSACTION_CONTROL violations (`.commit()` calls in L6 driver)
- These pre-date Wave-1 and are tracked separately

## 7) Documents Updated

| Document | Change |
|----------|--------|
| `HOC_USECASE_CODE_LINKAGE.md` | Added Script Coverage Wave-1 section with classification summary, UC_LINKED expansions, NON_UC_SUPPORT groups |
| `test_uc018_uc032_expansion.py` | Added `TestWave1ScriptCoverage` class (48 tests) |
| `UC_SCRIPT_COVERAGE_WAVE_1_implemented.md` | Created (this file) |

## 8) Audit Reconciliation Note (2026-02-12)

- Independent Codex audit re-ran all deterministic gates and confirmed `163` governance tests passing.
- Canonical classification and residual gap artifacts were reconciled to avoid stale pre-wave counts.
- Canonical reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_1_AUDIT_2026-02-12.md`
