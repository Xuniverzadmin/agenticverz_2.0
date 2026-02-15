# UC Script Coverage Wave-3: controls + account — Implementation Evidence

- Date: 2026-02-12
- Scope: Classify 52 unlinked scripts in account (31) + controls (21) domains
- Sources: `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_WAVE3_TARGET_UNLINKED_2026-02-12.txt`
- Result: 19 UC_LINKED + 33 NON_UC_SUPPORT + 0 DEPRECATED

## 1) Before/After Counts

### Before Wave-3
| Domain | Total Scripts | UC_LINKED | Unlinked | Coverage |
|--------|-------------|-----------|----------|----------|
| account | 31 | 0 | 31 | 0.0% |
| controls | 23 | 2 | 21 | 8.7% |
| **Total** | **54** | **2** | **52** | **3.7%** |

### After Wave-3
| Domain | Total Scripts | UC_LINKED | NON_UC_SUPPORT | Unclassified | Coverage |
|--------|-------------|-----------|----------------|--------------|----------|
| account | 31 | 13 | 18 | 0 | 100% classified |
| controls | 23 | 8 | 15 | 0 | 100% classified |
| **Total** | **54** | **21** | **33** | **0** | **100% classified** |

### Delta
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Account UC_LINKED | 0 | 13 | +13 |
| Controls UC_LINKED | 2 | 8 | +6 |
| Total UC_LINKED | 2 | 21 | +19 |
| Unclassified | 52 | 0 | -52 |

## 2) Classification Breakdown

### Account Domain (31 unlinked scripts)

**UC_LINKED (13 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/accounts_facade.py` | UC-002 | Account queries via L4 AccountQueryHandler dispatch |
| `L5_engines/memory_pins_engine.py` | UC-002 | Memory pin persistence for onboarding/lifecycle audit |
| `L5_engines/notifications_facade.py` | UC-002 | Onboarding notifications and account alerts delivery |
| `L5_engines/onboarding_engine.py` | UC-002 | Core state-machine (5 states, monotonic transitions) |
| `L5_engines/tenant_engine.py` | UC-001, UC-002 | Tenant operations (quota enforcement, bootstrap) |
| `L5_engines/tenant_lifecycle_engine.py` | UC-002 | Offboarding lifecycle transitions (ACTIVE→ARCHIVED) |
| `L6_drivers/accounts_facade_driver.py` | UC-002 | Account query persistence (tenants, users, memberships) |
| `L6_drivers/memory_pins_driver.py` | UC-002 | Memory pin data access |
| `L6_drivers/onboarding_driver.py` | UC-002 | Onboarding state CRUD (fetch/write state) |
| `L6_drivers/sdk_attestation_driver.py` | UC-002 | SDK attestation verification persistence |
| `L6_drivers/tenant_driver.py` | UC-001, UC-002 | Tenant quota/plan persistence |
| `L6_drivers/tenant_lifecycle_driver.py` | UC-002 | Lifecycle status mutations |
| `L6_drivers/user_write_driver.py` | UC-002 | User creation during onboarding |

**NON_UC_SUPPORT (18 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 5 | `__init__.py` across L5_engines, L5_schemas, L6_drivers, auth/L5_engines, auth/L6_drivers |
| L5 schemas | 8 | `crm_validator_types.py`, `lifecycle_dtos.py`, `onboarding_dtos.py`, `onboarding_state.py`, `plan_quotas.py`, `result_types.py`, `sdk_attestation.py`, `tenant_lifecycle_enums.py`, `tenant_lifecycle_state.py` |
| Platform auth infrastructure | 3 | `identity_adapter.py` (request identity), `invocation_safety.py` (PIN-332), `rbac_engine.py` (legacy M7 RBAC) |
| Infrastructure | 1 | `billing_provider_engine.py` (Phase-6 protocol/mock provider) |

### Controls Domain (21 unlinked scripts)

**UC_LINKED (6 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/controls_facade.py` | UC-021 | Centralized control operations facade (L2 dispatch entry) |
| `L5_engines/threshold_engine.py` | UC-001 | Threshold evaluation decision logic during LLM runs |
| `L6_drivers/override_driver.py` | UC-021 | Limit override lifecycle persistence (PENDING→APPROVED→ACTIVE→EXPIRED) |
| `L6_drivers/policy_limits_driver.py` | UC-021 | Policy limits CRUD data access |
| `L6_drivers/scoped_execution_driver.py` | UC-029 | Pre-execution gate for recovery actions (scope creation/validation) |
| `L6_drivers/threshold_driver.py` | UC-001 | Threshold limit data access (active limits, signal emission) |

**NON_UC_SUPPORT (15 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 3 | `__init__.py` across L5_engines, L5_schemas, L6_drivers |
| L5 schemas | 5 | `override_types.py`, `overrides.py`, `policy_limits.py`, `simulation.py`, `threshold_signals.py` |
| Circuit breaker infrastructure | 3 | `cb_sync_wrapper_engine.py` (sync wrapper), `circuit_breaker_async_driver.py`, `circuit_breaker_driver.py` |
| Kill switch infrastructure | 2 | `killswitch_ops_driver.py`, `killswitch_read_driver.py` |
| Budget enforcement | 1 | `budget_enforcement_driver.py` (helper for halted run queries) |
| Adapters | 1 | `adapters/__init__.py` |

## 3) Fixes Applied

No architecture violations found in Wave-3 scope. All newly-classified UC_LINKED L5 engines pass purity checks (0 runtime DB imports). No code changes were required.

## 4) Test Changes

| File | Before | After | Delta |
|------|--------|-------|-------|
| `test_uc018_uc032_expansion.py` | 219 tests | 250 tests | +31 |

New test class: `TestWave3ScriptCoverage`
- 8 L5 existence checks for UC_LINKED engines
- 11 L6 existence checks for UC_LINKED drivers
- 8 L5 purity checks for UC_LINKED engines
- 1 account NON_UC_SUPPORT schemas existence check
- 1 account NON_UC_SUPPORT auth existence check
- 1 controls NON_UC_SUPPORT safety existence check
- 1 total classification count validation

## 5) Gate Results

| # | Gate | Result |
|---|------|--------|
| 1 | Cross-domain validator | `status=CLEAN, count=0` |
| 2 | Layer boundaries | `CLEAN: No layer boundary violations found` |
| 3 | CI hygiene (--ci) | `All checks passed. 0 blocking violations` |
| 4 | Pairing gap detector | `wired=70, orphaned=0, direct=0` |
| 5 | UC-MON strict | `Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0` |
| 6 | Governance tests | `250 passed in 1.77s` |

**All 6 gates PASS.**

## 6) Cumulative Coverage (Wave-1 + Wave-2 + Wave-3)

| Wave | Domains | Scripts Classified | UC_LINKED | NON_UC_SUPPORT |
|------|---------|-------------------|-----------|----------------|
| Wave-1 | policies, logs | 130 | 33 | 97 |
| Wave-2 | analytics, incidents, activity | 80 | 35 | 45 |
| Wave-3 | controls, account | 52 | 19 | 33 |
| **Total** | **7 domains** | **262** | **87** | **175** |

## 7) Residual Gap List

### Remaining Wave-4 domains (unlinked scripts not yet classified):

| Domain | Unlinked Count | Wave |
|--------|---------------|------|
| hoc_spine | 170+ | Wave-4 |
| integrations | 58 | Wave-4 |
| agent | 4 | Wave-4 |
| api_keys | 8 | Wave-4 |
| apis | 2 | Wave-4 |
| ops | 3 | Wave-4 |
| overview | 5 | Wave-4 |

### Known pre-existing violations (not Wave-3 scope):
- `logs/L6_drivers/trace_store.py`: 7 L6_TRANSACTION_CONTROL violations (`.commit()` calls in L6 driver)
- These pre-date Wave-3 and are tracked separately

## 8) Documents Updated

| Document | Change |
|----------|--------|
| `HOC_USECASE_CODE_LINKAGE.md` | Added Script Coverage Wave-3 section with classification summary, UC_LINKED expansions for account (UC-002, UC-001) and controls (UC-001, UC-021, UC-029), NON_UC_SUPPORT groups |
| `test_uc018_uc032_expansion.py` | Added `TestWave3ScriptCoverage` class (31 tests, total now 250) |
| `UC_SCRIPT_COVERAGE_WAVE_3_implemented.md` | Created (this file) |

## 9) Audit Reconciliation Note (2026-02-12)

- Independent Codex audit re-ran all deterministic gates and confirmed `250` governance tests passing.
- Canonical classification and residual gap artifacts were reconciled to avoid stale post-Wave-2 counts.
- Canonical residual snapshot after reconciliation:
- `UNLINKED` (all scripts): `269`
- core-6 residual (core-layer scope): `0`
- Canonical reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_AUDIT_2026-02-12.md`
