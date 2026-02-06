# TODO — Iteration 3.2

**Date:** 2026-02-06
**Status:** COMPLETE ✅
**Purpose:** Finish Iteration‑3 remaining items after strict L5 purity (Iter3.1).

---

## 1) P2‑Step4‑1 — L2 Non‑Registry Usage Cleanup ✅

**Goal:** Audit and convert remaining L2 endpoints that bypass `operation_registry`.

**Scope:** `backend/app/hoc/api/**` (all L2 APIRouter files)

**Acceptance Criteria**
- ✅ Identify all L2 endpoints that do not use `operation_registry`.
- ✅ For each, choose:
  - Convert to registry execution; or
  - Document a justified exception with evidence and owner.
- ✅ Update evidence report with before/after metrics.

**Results (Superseded Snapshot):**
The original breakdown below was based on a `get_operation_registry()`-string heuristic and is now stale.
Canonical live classification is in `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md`.

**Results (Live - Evidence Scan Verified):**
- 69 total L2 APIRouter files (string-scan: `APIRouter(`)
- 47 files dispatch via registry (`registry.execute(`)
- 22 files do not dispatch via registry (all classified + justified in the supplement)

**Compliance:** 100% (all 69 files compliant or have justified exceptions)

**Approved Patterns:**
Counts by pattern were tracked in earlier snapshots; use `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md` for canonical live classification lists.
1. `registry.execute(...)` dispatch — Registry pattern (canonical)
2. hoc_spine bridges — `get_*_bridge()` capability access (non-registry justified)
3. hoc_spine services facades — `app.hoc.cus.hoc_spine.services.*` delegation (non-registry justified)
4. Console/runtime adapters — `app.adapters.*` boundary pattern (non-registry justified)
5. Stateless/local endpoints — no DB access needed (non-registry justified)

**Evidence Outputs**
- ✅ `docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md` (READ-ONLY, corrected counts)
- ✅ `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md` (corrected by user)
- ✅ `docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_EXCEPTIONS.md` (final exceptions report)

---

## 2) P3 — Canonical Literature Refresh (Post Iter3.1) ✅

**Goal:** Update domain canonical literature to reflect new L4 injection patterns.

**Scope Domains**
- ✅ activity
- ✅ policies
- ✅ analytics
- ✅ incidents
- ✅ integrations

**Acceptance Criteria**
- ✅ Domain canonical literature mentions L4 injection pattern and removal of L5→L4 imports.
- ✅ hoc_spine bridge literature updated for any new bridge classes or capabilities.
- ✅ Changes are cited with file paths in literature.

**Evidence Outputs**
- ✅ `literature/hoc_domain/activity/ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md` - Section 12 added
- ✅ `literature/hoc_domain/policies/POLICIES_CANONICAL_SOFTWARE_LITERATURE.md` - PIN-520 section added
- ✅ `literature/hoc_domain/analytics/ANALYTICS_CANONICAL_SOFTWARE_LITERATURE.md` - PIN-520 section added
- ✅ `literature/hoc_domain/incidents/INCIDENT_CANONICAL_SOFTWARE_LITERATURE.md` - PIN-520 section added
- ✅ `literature/hoc_domain/integrations/INTEGRATIONS_CANONICAL_SOFTWARE_LITERATURE.md` - PIN-520 section added
- ✅ `literature/hoc_spine/orchestrator/analytics_bridge.md` - 4 capabilities added
- ✅ `literature/hoc_spine/orchestrator/policies_bridge.md` - 2 capabilities added
- ✅ `literature/hoc_spine/orchestrator/integrations_bridge.md` - IntegrationsEngineBridge section added
- ✅ `literature/hoc_spine/orchestrator/activity_bridge.md` - Created (4 capabilities)
- ✅ `literature/hoc_spine/orchestrator/incidents_bridge.md` - Created (7 capabilities)

---

## 3) First-Principles L2 DB Execution Removal ✅

**Goal:** Remove ALL `session.execute()` calls from 15 L2 files that had "L4 Session Helpers + DB Execution In L2".

**Scope:** Files previously classified as having DB execution despite using L4 session helpers.

**Acceptance Criteria:**
- ✅ All 15 files have 0 `execute` calls in L2
- ✅ DB execution moved to L6 drivers
- ✅ L4 handlers created for dispatch
- ✅ Evidence scan confirms compliance

**Files Refactored (all now 0 execute calls):**
1. ✅ `agent/discovery.py`
2. ✅ `agent/platform.py`
3. ✅ `analytics/feedback.py`
4. ✅ `analytics/predictions.py`
5. ✅ `general/agents.py`
6. ✅ `incidents/cost_guard.py`
7. ✅ `integrations/v1_proxy.py`
8. ✅ `logs/cost_intelligence.py`
9. ✅ `logs/traces.py`
10. ✅ `policies/M25_integrations.py`
11. ✅ `policies/customer_visibility.py`
12. ✅ `policies/policy_proposals.py`
13. ✅ `policies/replay.py`
14. ✅ `policies/v1_killswitch.py`
15. ✅ `recovery/recovery.py`

**Total execute calls removed from L2:** ~140

**L6 Drivers Created:**
- `agent/L6_drivers/discovery_stats_driver.py`
- `agent/L6_drivers/platform_driver.py`
- `agent/L6_drivers/routing_driver.py`
- `incidents/L6_drivers/cost_guard_driver.py`
- `integrations/L6_drivers/proxy_driver.py`
- `logs/L6_drivers/cost_intelligence_sync_driver.py`
- `policies/L6_drivers/m25_integration_read_driver.py`
- `policies/L6_drivers/m25_integration_write_driver.py`
- `policies/L6_drivers/replay_read_driver.py`
- `policies/L6_drivers/recovery_read_driver.py`
- `controls/L6_drivers/killswitch_ops_driver.py`

**L4 Handlers Created/Extended:**
- `agent_handler.py` — `agent.discovery_stats`, `agent.routing`, `agent.strategy`
- `traces_handler.py` — 6 trace operations
- `m25_integration_handler.py` — 10 M25 read/write operations

**Evidence Output:**
- ✅ `docs/architecture/hoc/P2_STEP4_1_L2_DB_EXECUTION_REMOVAL_EVIDENCE.md`

**Result:** First-principles L2 purity achieved. All DB execution now in L6 drivers.

---

## 4) Iter3.2.1 — Remove L4 Driver Factory Workaround ✅

**Goal:** Remove the L4 “service locator” pattern (`get_*_from_l4`) and force L2 to dispatch via `registry.execute(...)` only.

**Acceptance Criteria**
- ✅ `rg -n "get_\\w+_from_l4\\b" backend/app/hoc/api/cus` returns 0 matches
- ✅ `rg -n "^def get_\\w+_from_l4\\(" backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py` returns 0 matches
- ✅ AST scan across all 69 L2 APIRouter files finds 0 calls to `*.execute()` / `*.exec()` on any `*session*` variable

**Strict Registry Dispatch (5 L2 files):**
- ✅ `backend/app/hoc/api/cus/integrations/v1_proxy.py` → `registry.execute("proxy.ops", OperationContext(...))`
- ✅ `backend/app/hoc/api/cus/agent/platform.py` → `registry.execute("platform.health", OperationContext(...))`
- ✅ `backend/app/hoc/api/cus/policies/guard.py` → `registry.execute("policies.sync_guard_read", OperationContext(...))`
- ✅ `backend/app/hoc/api/cus/policies/v1_killswitch.py` → `registry.execute("killswitch.read|killswitch.write", OperationContext(...))`
- ✅ `backend/app/hoc/api/cus/policies/M25_integrations.py` → `registry.execute("m25.*", OperationContext(...))`

**L4 Handler Wiring Evidence**
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/proxy_handler.py` registers `proxy.ops`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/platform_handler.py` registers `platform.health`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/killswitch_handler.py` registers `killswitch.read`, `killswitch.write`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/m25_integration_handler.py` registers `m25.*`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` registers `policies.sync_guard_read`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py` wires all the above via `register_all_handlers(...)`

---

## 5) Iter3.2.2 — Remove DB Transaction Authority From L2 ✅

**Goal:** L2 must not own transaction authority. No `commit()` / `rollback()` and no ad-hoc DB execution under alternate variable names (e.g., `db.execute(...)`) inside L2.

**Result (as of 2026-02-06):** L2 no longer performs direct DB execution or owns transaction boundaries.

**Acceptance Criteria (Iter3.2.2)**
- ✅ `rg -n "\\bdb\\.(execute|exec)\\s*\\(" backend/app/hoc/api/cus` returns 0 matches
- ✅ `rg -n "\\b(db|session|db_session|sync_session|async_session)\\.(commit|rollback)\\s*\\(" backend/app/hoc/api/cus` returns 0 matches
- ✅ AST scan across all 69 L2 APIRouter files finds 0 calls to `execute/exec/commit/rollback` on DB/session-like variables (excluding `registry.execute`)

**Implementation Notes (What Changed)**
- `backend/app/hoc/api/cus/policies/rbac_api.py` now dispatches to `registry.execute("rbac.audit", OperationContext(...))` instead of calling `db.execute(...)` / `db.commit()` in L2.
- DB transaction boundaries for M25 write ops, policy approval/proposals, workers write ops, and recovery ingest are no longer in L2.

---

## 6) Iter3.2.3 — Remove Transaction Management From L6 Drivers ✅

**Goal:** Enforce Driver/Engine Pattern LOCKED: L6 drivers must not call `commit()` / `rollback()` (transaction boundary is owned by L4).

**Result:** COMPLETE. AST scan shows 0 files with commit/rollback in L6_drivers.

### 6.1) Iter3.2.3a — Driver Purity (RBAC Audit) ✅

**Result (as of 2026-02-06):**
- `backend/app/hoc/cus/policies/L6_drivers/rbac_audit_driver.py` has **0** `commit()`/`rollback()` calls.
- Commit/rollback for RBAC audit cleanup now lives in L4 handler: `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` (`RbacAuditHandler`).
- L2 remains transaction-free (`backend/app/hoc/api/cus/policies/rbac_api.py` has 0 `commit()`/`rollback()` calls).

**Acceptance Scans (RBAC only):**
- `rg -n "^[^#]*\\.(commit|rollback)\\s*\\(" backend/app/hoc/cus/policies/L6_drivers/rbac_audit_driver.py` → 0
- `rg -n "sync_session\\.(commit|rollback)\\(" backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` → expects matches for RBAC cleanup path
- `rg -n "\\.(commit|rollback)\\s*\\(" backend/app/hoc/api/cus/policies/rbac_api.py` → 0

### 6.2) Iter3.2.3 Remaining Work (Backlog)

### 6.2.1) Iter3.2.3b — Driver Purity (guard_read_driver RBAC cleanup) ✅

**Result (as of 2026-02-06):**
- Removed the last `await session.commit()` from `backend/app/hoc/cus/policies/L6_drivers/guard_read_driver.py` by deleting an unused RBAC cleanup helper.

### 6.2.2) Iter3.2.3c — Phase-2 Refactors Completed ✅

**Result (as of 2026-02-06):**
- `backend/app/hoc/cus/integrations/L6_drivers/cus_integration_driver.py`: session required (`__init__(session)`), `_get_session` removed, 0 commits/rollbacks.
- `backend/app/hoc/cus/activity/L6_drivers/cus_telemetry_driver.py`: session required (`__init__(session)`), `get_async_session` removed, 0 commits/rollbacks.
- `backend/app/hoc/cus/analytics/L6_drivers/canary_report_driver.py`: `write_canary_report(session, ...)` now requires session and does not commit/rollback. Read query helpers still create their own session (`async_session_context`) and are tracked as session-lifecycle backlog (see 6.3).

### 6.2.3) Remaining Commit/Rollback Violations (AST-Verified) ✅

**Before (2026-02-06 09:00):** L6 commit/rollback calls remained in exactly 2 files:
- `backend/app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py` (`conn.commit()` at 474; raw psycopg2 helper)
- `backend/app/hoc/cus/logs/L6_drivers/traces_store.py` (`conn.commit()` at 184,218,262,284,408,438,601; sqlite store)

**After (2026-02-06 12:00): ALL FIXED ✅**

**Fix 1 — `policy_violation_driver.py`:**
- Replaced `insert_policy_evaluation_sync()` with `insert_policy_evaluation_sync_with_cursor(cursor, ...)`
- Function now requires cursor (passed from L4), does NOT commit
- Created L4 transaction owner: `backend/app/services/policy_violation_service.py`
  - L4 creates psycopg2 connection
  - L4 passes cursor to L6 driver
  - L4 commits after L6 returns
- Fixed broken import in `run_governance_facade.py`

**Fix 2 — `traces_store.py`:**
- This SQLite store was RE-HOMED to infrastructure: `app/traces/store.py`
- Infrastructure store already existed with identical functionality
- Updated 3 callers to use infrastructure store:
  - `app/runtime/replay.py`
  - `app/hoc/int/platform/engines/replay.py`
  - `app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py`
- Deleted L6 file: `backend/app/hoc/cus/logs/L6_drivers/traces_store.py`

**Confirmed fixed (earlier):**
- `backend/app/hoc/cus/integrations/L6_drivers/bridges_driver.py` — UNFROZEN and refactored to accept injected `AsyncSession`; commit removed (L4 owns transaction boundary).
- `backend/app/hoc/cus/logs/L6_drivers/bridges_driver.py` — UNFROZEN and refactored to accept injected `AsyncSession`; commit removed (L4 owns transaction boundary).

**Final AST Scan (2026-02-06 12:00):**
```
=== L6 Driver Transaction Purity Scan (PIN-520 Phase 2/3) ===

PASS: 0 files with commit/rollback in L6_drivers

All L6 drivers now comply with PIN-520 transaction purity.
```

**Acceptance Criteria (Iter3.2.3) ✅**
- ✅ AST scan: 0 files with `commit()` / `rollback()` in L6_drivers
- ✅ L4 handlers own transaction boundaries

### 6.3) Separate Backlog: L6 Session Lifecycle (Strict Driver Purity)

Even where commit/rollback is removed, multiple L6 drivers still create/manage sessions internally (imports from `app.db*`, `get_session/get_engine/get_async_session`, `AsyncSessionLocal`, `async_session_context`, `create_engine`, `Session(...)`).
This is tracked separately from the commit/rollback authority rule and requires broader refactors.

### 6.4) Reality Note: Missing Legacy Module ✅

**Before:** `backend/app/services/governance/run_governance_facade.py` imported `app.services.policy_violation_service`, but `backend/app/services/policy_violation_service.py` did not exist (only a compiled `.pyc` existed).

**After (2026-02-06):** Created `backend/app/services/policy_violation_service.py` as L4 transaction owner:
- Exposes `create_policy_evaluation_sync(run_id, tenant_id, run_status, ...)`
- Owns psycopg2 connection lifecycle (L4 creates conn, passes cursor to L6, L4 commits)
- L6 driver now requires cursor parameter (no self-commit)

---

## Appendix — Reality Corrections

- `docs/memory-pins/TODO_ITER3.2.md` references `docs/architecture/hoc/P2_STEP4_1_L2_DB_EXECUTION_REMOVAL_EVIDENCE.md`, but the evidence artifact currently exists at `backend/docs/architecture/hoc/P2_STEP4_1_L2_DB_EXECUTION_REMOVAL_EVIDENCE.md` (canonical copy still missing).
- Live scan (string heuristic: `APIRouter` + `get_operation_registry`) currently shows 41/69 L2 router files using `get_operation_registry()`. The READ-ONLY audit artifacts still reflect the earlier 32/69 snapshot.
- Live scan (stronger heuristic: `APIRouter` + `registry.execute(`) currently shows 47/69 L2 router files dispatch via the registry. `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md` is the canonical live classification; `docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md` is a READ-ONLY snapshot.
