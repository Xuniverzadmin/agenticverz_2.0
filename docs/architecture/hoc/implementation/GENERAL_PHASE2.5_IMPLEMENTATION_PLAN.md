# General Domain — Phase 2.5 Implementation Plan

**Status:** ANALYSIS COMPLETE
**Created:** 2026-01-24
**Reference:** HOC_LAYER_TOPOLOGY_V1.md, HOC_general_analysis_v1.md

---

## Executive Summary

The general domain has **68 files** across 12 subdirectories. BLCA analysis reveals:
- **63 violations** (61 errors, 2 warnings)
- **3 files** with banned `*_service.py` naming
- **22 files** with layer boundary violations
- **35 files** with legacy imports from `app.services.*`
- **1 file** with sqlalchemy runtime import in L4
- **2 files** with missing headers
- **1 file** with critical layer misclassification (knowledge_sdk.py)

**Domain Constitution Note:** The domain `__init__.py` explicitly documents known issues with Phase 3+ deadlines.

---

## Canonical Layer Reference

```
L2 = Product APIs (api/ routes)
L3 = Adapters (translation layer)
L4 = Runtime (general/runtime/ ONLY per HOC Topology)
L5 = Engines / Workers / Schemas (per-domain)
L6 = Drivers (per-domain)
L7 = Models (ORM)
```

**Critical HOC Topology Rules:**
- L4 = `general/runtime/` ONLY (Governed Runtime)
- Engines in `engines/` are L5, NOT L4
- Facades should be L3 (Adapters) or L2.1
- `*_service.py` naming is BANNED

---

## BLCA Results (2026-01-24)

**Command:** `python3 scripts/ops/layer_validator.py --path backend/app/hoc/cus/general --ci`

| Category | Count | Details |
|----------|-------|---------|
| BANNED_NAMING | 3 | `*_service.py` files |
| LAYER_BOUNDARY | 22 | L4→L7, L6→L4, L2→L7 violations |
| LEGACY_IMPORT | 35 | `app.services.*` imports |
| SQLALCHEMY_RUNTIME | 1 | L4 with sqlmodel import |
| MISSING_HEADER | 2 | Empty init files |
| **TOTAL** | **63** | |

---

## Phase I: Header Corrections

Fix layer declarations in `__init__.py` files.

| # | File | Current Header | Correct Header | Status |
|---|------|----------------|----------------|--------|
| 1 | `__init__.py` | L4 — Domain Services | L5 — Domain Engines (general cross-domain) | ⬜ TODO |
| 2 | `drivers/__init__.py` | L4 — Domain Services | L6 — Drivers | ⬜ TODO |
| 3 | `engines/__init__.py` | L4 — Domain Services | L5 — Domain Engines | ⬜ TODO |
| 4 | `schemas/__init__.py` | L4 — Domain Services | L5 — Domain Schemas | ⬜ TODO |
| 5 | `facades/__init__.py` | L4 — Domain Services | L3 — Adapters | ⬜ TODO |
| 6 | `controls/__init__.py` | (empty) | L5 — Domain Engines | ⬜ TODO |
| 7 | `controls/engines/__init__.py` | (empty) | L5 — Domain Engines | ⬜ TODO |
| 8 | `controls/drivers/__init__.py` | L6 — Driver | ✅ CORRECT | ✅ DONE |
| 9 | `utils/__init__.py` | L6 — Platform Substrate | ✅ CORRECT | ✅ DONE |

---

## Phase II: Banned Naming Fixes

Rename `*_service.py` files to `*_engine.py`.

| # | Current Name | New Name | Layer | Status |
|---|--------------|----------|-------|--------|
| 1 | `engines/cus_health_service.py` | `engines/cus_health_engine.py` | L5 | ⬜ TODO |
| 2 | `workflow/contracts/engines/contract_service.py` | `workflow/contracts/engines/contract_engine.py` | L5 | ⬜ TODO |
| 3 | `controls/engines/guard_write_service.py` | `controls/engines/guard_write_engine.py` | L5 | ⬜ TODO |

---

## Phase III: Layer Reclassification

Fix files with incorrect layer declarations.

### 3.1 Knowledge SDK (CRITICAL - Evidence-Based Analysis)

| File | Current | Evidence-Based Assessment | Status |
|------|---------|---------------------------|--------|
| `engines/knowledge_sdk.py` | L2 — Product APIs | **HEADER IS WRONG** (see evidence below) | ⬜ DEFERRED (Phase 3) |

#### Evidence-Based Analysis (2026-01-24)

**Location:** `backend/app/hoc/cus/general/L5_engines/knowledge_sdk.py`

**Header Claims:**
```python
# Layer: L2 — Product APIs
# Role: GAP-083-085 Knowledge SDK Façade
# Callers: External SDK consumers, API endpoints
```

**Imports (lines 46-57):**
```python
from app.models.knowledge_lifecycle import (...)     # L7 import
from app.services.knowledge_lifecycle_manager import (...) # LEGACY (banned)
```

**Code Function Analysis:**

| Class | Lines | Type | Purpose |
|-------|-------|------|---------|
| `KnowledgePlaneConfig` | 65-73 | dataclass | Configuration schema |
| `WaitOptions` | 75-80 | dataclass | Wait options schema |
| `SDKResult` | 88-154 | dataclass | Result schema |
| `PlaneInfo` | 157-230 | dataclass | Info schema |
| `KnowledgeSDK` | 238-939 | class | **Thin wrapper** over manager |

**KnowledgeSDK Method Behavior:**
- `register()`, `verify()`, `ingest()`, etc. → All delegate to `self._manager.handle_transition()`
- `get_state()`, `get_plane()`, etc. → Query methods delegating to `_manager`
- `wait_until()` → Polling loop calling `_manager.get_state()`

**Design Invariants (from docstring):**
```
SDK-001: SDK does NOT force transitions — it requests them
SDK-002: SDK does NOT manage state — orchestrator does
SDK-003: SDK does NOT bypass policy gates — gates are mandatory
```

#### Evidence vs HOC Topology

| Check | L2 Requires | L5 Engine Requires | Actual Behavior |
|-------|-------------|-------------------|-----------------|
| Handles HTTP? | ✅ Required | N/A | ❌ NO |
| Route handlers? | ✅ Required | N/A | ❌ NO |
| Input validation? | ✅ Required | N/A | ❌ NO |
| Business logic? | ❌ Forbidden | ✅ Required | ❌ NO (thin delegation) |
| Pattern detection? | N/A | ✅ Required | ❌ NO |
| Dataclasses/schemas? | N/A | ✅ Allowed | ✅ YES |

#### Verdict

**The L2 header is WRONG:**
1. L2 is for HTTP route handlers at `hoc/api/{audience}/*.py`
2. This file is NOT at that location
3. This file does NOT handle HTTP
4. This file does NOT validate HTTP input
5. This file does NOT call L3 adapters

**The engines/ location is ALSO QUESTIONABLE:**
1. L5 Engines should contain "business rules, pattern detection, decisions"
2. This file contains **thin delegation** (every method calls `_manager.*`)
3. The actual business logic is in `KnowledgeLifecycleManager` (legacy)

**What this file actually is:**
- **SDK Facade/Wrapper** providing clean interface over `KnowledgeLifecycleManager`
- Contains **L5 Schemas** (dataclasses: `KnowledgePlaneConfig`, `SDKResult`, `PlaneInfo`)
- NOT an L2 API (no HTTP), NOT purely an L5 Engine (no business logic)

#### Correct Classification Options

| Option | Classification | Rationale | Action Required |
|--------|----------------|-----------|-----------------|
| A | L3 — Adapter | Translation layer pattern, delegates to service | Change header + move to adapters/ |
| B | L5 — Engine | Keep in engines/, behavior is SDK wrapper | Change header only |
| C | Split | Extract schemas to `schemas/knowledge_sdk_schemas.py`, keep wrapper | Split file |

**Recommended:** Option B (change header to L5) for Phase 2.5, with note that full refactor depends on `KnowledgeLifecycleManager` migration.

#### Violations Found

| Violation | Evidence | Severity |
|-----------|----------|----------|
| Wrong Layer Header | L2 claimed but no HTTP handling | HIGH |
| Legacy Import | `app.services.knowledge_lifecycle_manager` | MEDIUM (blocked until migration) |
| L7 Import | `app.models.knowledge_lifecycle` | LOW (acceptable for L5/L6) |

**Note:** Domain constitution documents this as "Phase 3 deadline" issue. Full remediation blocked until `KnowledgeLifecycleManager` migrates to HOC.

### 3.2 Facade Layer Fixes

Facades are currently declared as L6 or L4 but should be L3 (Adapters).

| File | Current | Correct | Status |
|------|---------|---------|--------|
| `facades/alerts_facade.py` | L6 — Driver | L3 — Adapter | ⬜ TODO |
| `facades/monitors_facade.py` | L4 — Domain Engine | L3 — Adapter | ⬜ TODO |
| `facades/compliance_facade.py` | (check) | L3 — Adapter | ⬜ TODO |
| `facades/lifecycle_facade.py` | (check) | L3 — Adapter | ⬜ TODO |
| `facades/scheduler_facade.py` | (check) | L3 — Adapter | ⬜ TODO |

### 3.3 Runtime Facade Fix

| File | Current | Correct | Status |
|------|---------|---------|--------|
| `runtime/facades/run_governance_facade.py` | L3 — Adapter | ✅ CORRECT | ✅ DONE |

---

## Phase IV: SQLAlchemy Runtime Fix

Split files with sqlalchemy imports in L5.

| # | File | Issue | Resolution | Status |
|---|------|-------|------------|--------|
| 1 | `engines/cus_health_service.py` | `from sqlmodel import Session, select` at runtime | Extract DB ops to driver | ⬜ TODO |

**Split Plan:**
- Create `drivers/cus_health_driver.py` (L6) with DB operations
- Keep `engines/cus_health_engine.py` (L5) with business logic only

---

## Phase V: Legacy Import Audit

Files importing from banned `app.services.*` namespace.

### 5.1 Facades (5 files - All importing legacy services)

| File | Legacy Import | HOC Import | Status |
|------|---------------|------------|--------|
| `facades/monitors_facade.py` | `app.services.monitors.facade` | TBD (when monitors migrated) | ⬜ DEFERRED |
| `facades/alerts_facade.py` | `app.services.alerts.facade` | TBD (when alerts migrated) | ⬜ DEFERRED |
| `facades/scheduler_facade.py` | `app.services.scheduler.facade` | TBD (when scheduler migrated) | ⬜ DEFERRED |
| `facades/compliance_facade.py` | `app.services.compliance.facade` | TBD (when compliance migrated) | ⬜ DEFERRED |
| `facades/lifecycle_facade.py` | `app.services.lifecycle.facade` | TBD (when lifecycle migrated) | ⬜ DEFERRED |

### 5.2 Engines (3 files)

| File | Legacy Import | Status |
|------|---------------|--------|
| `engines/cus_health_service.py` | `app.services.cus_credential_service` | ⬜ DEFERRED |
| `engines/knowledge_sdk.py` | `app.services.knowledge_lifecycle_manager` | ⬜ DEFERRED (Phase 3) |
| `engines/knowledge_lifecycle_manager.py` | `app.models.*` | ⬜ CHECK |

### 5.3 Workflow (1 file)

| File | Legacy Imports | Status |
|------|----------------|--------|
| `workflow/contracts/engines/contract_service.py` | `app.services.governance.eligibility_engine`, `app.services.governance.validator_service` | ⬜ DEFERRED |

### 5.4 Lifecycle (1 file)

| File | Legacy Import | Status |
|------|---------------|--------|
| `lifecycle/drivers/execution.py` | `app.services.connectors` | ⬜ DEFERRED |

### 5.5 Runtime (Multiple files)

| File | Legacy Import | Status |
|------|---------------|--------|
| `runtime/engines/governance_orchestrator.py` | `app.models.contract.*` | ⬜ CHECK (L7 import) |
| `runtime/drivers/transaction_coordinator.py` | Various facades | ⬜ CHECK |

---

## Phase VI: Layer Boundary Violations Detail

### 6.1 L4/L5 importing L7 (Model imports)

Per HOC Topology, L4/L5 should not import L7 directly. These need driver extraction.

| File | Import | Resolution | Status |
|------|--------|------------|--------|
| `engines/cus_health_service.py` | `app.models.cus_models` | Move to driver | ⬜ TODO |
| `engines/knowledge_lifecycle_manager.py` | `app.models.knowledge_lifecycle` | Move to driver | ⬜ ASSESS |
| `engines/lifecycle_stages_base.py` | `app.models.knowledge_lifecycle` | TYPE_CHECKING block | ⬜ TODO |
| `workflow/contracts/engines/contract_service.py` | `app.models.contract` | TYPE_CHECKING block | ⬜ TODO |
| `runtime/engines/governance_orchestrator.py` | `app.models.contract` | TYPE_CHECKING block | ⬜ TODO |

### 6.2 L6 importing L4 (Drivers importing engines)

| File | Import | Resolution | Status |
|------|--------|------------|--------|
| `lifecycle/drivers/execution.py` | `app.services.connectors` | DEFERRED (connectors migration) | ⬜ DEFERRED |
| `facades/*` | `app.services.*` | DEFERRED (service migration) | ⬜ DEFERRED |

### 6.3 L2 in engines/ (Misplacement)

| File | Issue | Resolution | Status |
|------|-------|------------|--------|
| `engines/knowledge_sdk.py` | L2 declared but in engines/ | Reclassify to L5 or move | ⬜ DEFERRED (Phase 3) |

---

## Files by Subdirectory Analysis

### Root Level
| File | Layer (Header) | Layer (Actual) | Issues |
|------|----------------|----------------|--------|
| `__init__.py` | L4 | L5 | Header wrong |

### drivers/ (23 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `__init__.py` | L4 | Should be L6 |
| `alert_emitter.py` | L6 | ✅ CLEAN |
| `budget_tracker.py` | L6 | ✅ CLEAN |
| `canonical_json.py` | L6 | ✅ CLEAN |
| `concurrent_runs.py` | L6 | ✅ CLEAN |
| `db_helpers.py` | L6 | ✅ CLEAN |
| `decisions.py` | L6 | ✅ CLEAN |
| `deterministic.py` | L6 | ✅ CLEAN |
| `fatigue_controller.py` | L6 | ✅ CLEAN |
| `guard.py` | L6 | ✅ CLEAN |
| `guard_cache.py` | L6 | ✅ CLEAN |
| `idempotency.py` | L6 | ✅ CLEAN |
| `input_sanitizer.py` | L6 | ✅ CLEAN |
| `ledger.py` | L6 | ✅ CLEAN |
| `metrics_helpers.py` | L6 | ✅ CLEAN |
| `panel_invariant_monitor.py` | L6 | ✅ CLEAN |
| `plan_inspector.py` | L6 | ✅ CLEAN |
| `rate_limiter.py` | L6 | ✅ CLEAN |
| `runtime.py` | L6 | ✅ CLEAN |
| `schema_parity.py` | L6 | ✅ CLEAN |
| `webhook_verify.py` | L6 | ✅ CLEAN |
| `worker_write_service_async.py` | L6 | ⚠️ Naming (async driver) |

### engines/ (7 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `__init__.py` | L4 | Should be L5 |
| `alert_log_linker.py` | L5 | ✅ CLEAN |
| `control_registry.py` | L5 | ✅ CLEAN |
| `cus_health_service.py` | L4 | BANNED_NAMING, SQLALCHEMY_RUNTIME, L7 imports |
| `knowledge_lifecycle_manager.py` | L4 | L7 imports |
| `knowledge_sdk.py` | L2 | **CRITICAL**: L2 in engines/ |
| `lifecycle_stages_base.py` | L4 | L7 imports |

### facades/ (6 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `__init__.py` | L4 | Should be L3 |
| `alerts_facade.py` | L6 | Should be L3, legacy imports |
| `compliance_facade.py` | ? | Legacy imports |
| `lifecycle_facade.py` | ? | Legacy imports |
| `monitors_facade.py` | L4 | Should be L3, legacy imports |
| `scheduler_facade.py` | ? | Legacy imports |

### schemas/ (7 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `__init__.py` | L4 | Should be L5 |
| `agent.py` | L6 | Should be L5 |
| `artifact.py` | ? | Check header |
| `common.py` | ? | Check header |
| `plan.py` | ? | Check header |
| `response.py` | L2 | ⚠️ L2 in schemas/ |
| `skill.py` | ? | Check header |

### controls/ (4 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `__init__.py` | (empty) | MISSING_HEADER |
| `engines/__init__.py` | (empty) | MISSING_HEADER |
| `engines/guard_write_service.py` | L4 | BANNED_NAMING (already split) |
| `drivers/__init__.py` | L6 | ✅ CORRECT |
| `drivers/guard_write_driver.py` | L6 | ✅ CLEAN |

### lifecycle/ (6 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `engines/base.py` | L4 | L7 imports |
| `engines/onboarding.py` | L4 | L7 imports |
| `engines/offboarding.py` | L4 | Check |
| `engines/pool_manager.py` | L4 | ✅ CLEAN |
| `drivers/execution.py` | L6 | Legacy imports (connectors) |
| `drivers/knowledge_plane.py` | L6 | ✅ CLEAN |

### runtime/ (6 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `engines/__init__.py` | ? | Check |
| `engines/governance_orchestrator.py` | L4 | L7 imports (contract models) |
| `engines/plan_generation_engine.py` | L4 | ✅ CLEAN |
| `engines/constraint_checker.py` | L4 | ✅ CLEAN |
| `engines/phase_status_invariants.py` | ? | Check |
| `facades/run_governance_facade.py` | L3 | ✅ CORRECT |
| `drivers/transaction_coordinator.py` | L6 | ✅ CLEAN |

### ui/ (1 file)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `engines/rollout_projection.py` | L4 | ✅ CLEAN (projection) |

### workflow/ (1 file)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `contracts/engines/contract_service.py` | L4 | BANNED_NAMING, L7 imports, legacy imports |

### cross-domain/ (1 file)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `drivers/cross_domain.py` | L6 | ✅ CLEAN |

### mcp/ (2 files)
| File | Layer (Header) | Issues |
|------|----------------|--------|
| `__init__.py` | L5 | ✅ CLEAN (added in integrations phase) |
| `server_registry.py` | L6 | ✅ CLEAN (added in integrations phase) |

---

## Remediation Priority

### P1 - Critical (Blocks other work)
| Item | Issue | Action |
|------|-------|--------|
| 1 | `controls/__init__.py` missing header | Add L5 header |
| 2 | `controls/engines/__init__.py` missing header | Add L5 header |
| 3 | Init file headers wrong | Fix L4 → correct layer |

### P2 - High (Naming violations)
| Item | Issue | Action |
|------|-------|--------|
| 1 | `cus_health_service.py` | Rename to `cus_health_engine.py` |
| 2 | `contract_service.py` | Rename to `contract_engine.py` |
| 3 | `guard_write_service.py` | Rename to `guard_write_engine.py` |

### P3 - Medium (SQLAlchemy/L7 violations in L5)
| Item | Issue | Action |
|------|-------|--------|
| 1 | `cus_health_engine.py` sqlalchemy | Extract to driver |
| 2 | L7 model imports in engines | Use TYPE_CHECKING |

### P4 - Deferred (Dependency on other migrations)
| Item | Issue | Waiting On |
|------|-------|------------|
| 1 | Facades legacy imports | Service migrations |
| 2 | `knowledge_sdk.py` L2 issue | Phase 3 governance |
| 3 | `execution.py` connectors import | Connectors migration |

---

## Implementation Order

1. **Phase I** — Fix init file headers (non-breaking)
2. **Phase II** — Rename `*_service.py` files
3. **Phase III** — Reclassify facade layers (header only)
4. **Phase IV** — Extract sqlalchemy from cus_health_engine
5. **Phase V** — Add TYPE_CHECKING blocks for L7 imports
6. **Phase VI** — Deferred items (post-dependency migration)

---

## Post-Remediation Checklist

- [ ] All `__init__.py` files have correct layer headers
- [ ] No `*_service.py` files in engines/
- [ ] controls/ has proper headers
- [ ] Facades declared as L3
- [ ] No sqlalchemy runtime imports in L5
- [ ] L7 model imports use TYPE_CHECKING where possible
- [ ] BLCA reports reduced violations

---

## Known Technical Debt (Documented)

Per domain constitution (`general/__init__.py`):

1. **knowledge_sdk.py** - L2 in engines/ (Phase 3 deadline)
2. **guard_write_service.py** - Temporary name (split done, rename pending)
3. **Facades** - Extraction candidates (Phase 4+)
4. **Legacy imports** - Waiting on service migrations

---

## Changelog

| Date | Phase | Action | Result |
|------|-------|--------|--------|
| 2026-01-24 | Analysis | Full domain analysis | 68 files, 63 violations identified |

---

**END OF PLAN**
