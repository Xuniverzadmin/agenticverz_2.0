# PIN-512: PIN-514: Boundary Severance — Items 1-5 Cleanup

**Status:** ✅ COMPLETE
**Created:** 2026-02-02
**Category:** Architecture

---

## Summary

Severed all services-HOC boundary violations (Items 1-5 from audit tally). DELETED: (1) incidents/L5_engines/incident_driver.py tombstone (0 importers), (2) services/_audit_shim.py no-op shim (4 legacy callers in services/), (3) services/policy_violation_service.py re-export shim. MIGRATED: prevention_engine.py and s3_policy_violation_verification.py to direct HOC imports. SEVERED: detection/facade.py:296 transitional HOC import replaced with NotImplementedError. AUDIT FIX: docstring false-positive bug fixed in tally script (7 FPs eliminated). POST-CLEANUP: Items 1-5 = 0. Remaining 67 = 25 BANNED_NAMING + 42 MISSING_HEADER.

---

## Details

[Add details here]

### Update (2026-02-02)

## Actions Taken

### Deleted (3 files)
1. `app/hoc/cus/incidents/L5_engines/incident_driver.py` — TOMBSTONE re-export with 0 importers. Canonical code lives at L6_drivers. Created during PIN-511 Phase 0.1, expiry 2026-03-01 but zero-dependent.
2. `app/services/_audit_shim.py` — No-op AuditLedgerShim (23 lines). 4 legacy callers all inside app/services/ (dies with bulk deletion).
3. `app/services/policy_violation_service.py` — Re-export shim for PolicyViolationService. 10+ symbols re-exported from HOC incidents engine.

### Migrated (2 non-legacy callers)
- `app/policy/validators/prevention_engine.py:812,841` — now imports directly from `app.hoc.cus.incidents.L5_engines.policy_violation_service`
- `scripts/verification/s3_policy_violation_verification.py:116,348` — same direct HOC import

### Severed (1 import)
- `app/services/detection/facade.py:296` — Replaced `from app.hoc.cus.hoc_spine.orchestrator.coordinators.anomaly_incident_coordinator import ...` with `raise NotImplementedError`. Detection domain must migrate to HOC.

### Audit Script Fix
- `audit_cleanup_tally.py` — Added `is_code_line()` and `iter_code_lines()` helpers that track triple-quote state. Eliminated 7 false positives (1 in Item 3, 5 in Item 4, 1 in Item 5).

## Tally Change
- Before: 78 total (11 in Items 1-5)
- After docstring fix: 71 (4 real in Items 1-5)
- After deletions: 67 (0 in Items 1-5)
- Remaining: 25 BANNED_NAMING + 42 MISSING_HEADER
---

## Item 6 Renames

### Update (2026-02-02)

Renamed 25 BANNED_NAMING files (*_service.py -> *_engine.py/*_driver.py) in HOC. Updated 57 import references across 18 files. Migrated 48 legacy imports (app.agents.services.*, app.services.*) to HOC paths. Updated 9 CI allowlist entries in check_init_hygiene.py. Reverted 1 false migration in app/services/ops/facade.py (legacy file should not import HOC). Post-rename tally: Items 1-6 = 0, Item 7 = 42 MISSING_HEADER. Total: 42.
---

## Item 7 Headers

### Update (2026-02-02)

Added # Layer: / # AUDIENCE: / # Role: headers to 42 HOC files missing them. Breakdown: 2 L2 API (fdr/ops, fdr/logs), 1 L2.1 Facade (int/agent/claude_adapter), 9 L6 Drivers (int/platform), 28 L5 Engines (int/agent), 1 L5 Engine (int/platform/replay), 1 L5 Engine (int/general/contracts). Automated via fix_missing_headers.py which reads audit_tally.json and infers layer/audience/role from path + first docstring. FINAL TALLY: All 7 items = 0. Total violations = 0. Cleanup complete from 78 -> 0.
---

## Stub Deduplication

### Update (2026-02-02)

Deduplicated 5 Category A test stubs. Deleted legacy copies: app/skills/stubs/{http_call_stub,llm_invoke_stub,json_transform_stub}.py, app/planners/stub_adapter.py, app/planner/stub_planner.py. Migrated 48 import lines across 29 files to HOC canonical paths. Verified: 0 legacy stub references remain outside app/services/.
---

## Category B Stub Rewiring (Phase 1)

### Update (2026-02-02)

Rewired 4 of 5 Category B stub engines with real implementations from legacy. Copied 4 legacy drivers to HOC L6: cus_enforcement_driver → policies/L6_drivers, cus_telemetry_driver → activity/L6_drivers, cus_integration_driver → integrations/L6_drivers, limits/simulation_driver → policies/L6_drivers. Replaced 4 HOC stubs with legacy engine logic (total: 117+125+103+95 → 559+384+472+275 lines). Migrated 6 external callers (L2 APIs + L4 handlers) to HOC import paths. Deleted backward *Service aliases. Verified: 0 legacy imports remain outside app/services/.

## Category B Stub Rewiring (Phase 2 — policies_facade)

### Update (2026-02-02)

Manually extracted policies_facade.py L6 driver. Created policies/L6_drivers/policies_facade_driver.py (478 LOC) with 7 SQL methods: fetch_policy_rules, fetch_policy_rule_detail, fetch_limits, fetch_limit_detail, fetch_policy_requests, fetch_budgets, count_pending_drafts. Rewrote L5 policies_facade.py (286→1185 LOC): 20 rich result dataclasses from legacy, 14 async methods (6 via L6 driver, 5 delegate to same-domain L5 engines, 3 mixed). Rewired delegation imports: lessons_engine→HOC, engine→HOC, policy_graph_engine→HOC. Migrated 1 L2 API caller (app/api/policies.py:51). FINAL TALLY: Category B = 5/5 rewired, 5/5 L6 drivers present, 0 STUB_ENGINE markers remaining. Boundary leaks: 2 (ops_facade fdr/ops = out-of-scope, services/policy/lessons_engine reverse = legacy).

## Category C: Unwired L6 Driver Wiring

### Update (2026-02-02)

Wired 7 files with unwired/improperly-wired L6 drivers across 3 priority tiers.

### P0: override_driver.py (controls/L6_drivers)
- Created `LimitOverride` SQLModel in `app/models/policy_control_plane.py` matching migration 094 schema (16 columns, 4 indexes including no-stacking unique partial)
- Added `LimitOverride` to `app/models/__init__.py` exports
- Rewrote `override_driver.py`: deleted `_OVERRIDE_STORE` global dict, replaced all in-memory dict operations with SQLAlchemy queries against `LimitOverride` model. Uses `session.flush()` (L6 never commits). 252→297 LOC.

### P1: decisions.py (hoc_spine/drivers)
- Added `_get_engine()` method — lazily creates shared engine once (was creating+disposing per method call)
- Replaced all 8 `create_engine(db_url)` calls with `self._get_engine()` / `svc._get_engine()`
- Replaced all 4 explicit `conn.commit()` with `engine.begin()` context manager (auto-commits on exit)
- Eliminated all `engine.dispose()` calls (shared engine persists)

### P1: limit_enforcer.py (int/policies/L5_engines)
- Rewired from allow-all stub to real enforcement via LimitsReadDriver (L6) + RateLimiter (Redis token bucket)
- Cost checks: queries BUDGET limits, blocks if exceeded
- Token checks: queries RATE/TOKENS_* limits, blocks if exceeded
- Rate checks: uses Redis token bucket via `rate_limiter.allow()`
- Fail-closed: if session unavailable or driver errors → DENY. 174→286 LOC.

### P2: usage_monitor.py (int/policies/L5_engines) + usage_record_driver.py (NEW)
- Created `int/policies/drivers/usage_record_driver.py` (L6, 88 LOC) — `insert_usage()` persists to `usage_records` table via existing `UsageRecord` model
- Rewired `usage_monitor.py` to persist 3 meters per step (cost_cents, tokens_used, step_latency_ms) via driver. Falls back to log-only if no session factory. 141→177 LOC.

### P2: alert_emitter.py (hoc_spine/drivers)
- Wired `_send_email` to `SMTPAdapter` with graceful ImportError fallback (base notification types module pending)
- Builds NotificationMessage with proper subject/body from signal data

### P3: alert_driver.py (hoc_spine/drivers) + transaction_coordinator.py
- Fixed stale inventory comments: all 9 methods marked [DONE] (was 7 [TODO])
- Added `RollbackNotSupportedError` exception class to transaction_coordinator.py
- Replaced rollback TODO stubs with explicit `raise RollbackNotSupportedError` (fail-loud fencing)

### Files Changed (10)
1. `app/models/policy_control_plane.py` — +LimitOverride model
2. `app/models/__init__.py` — +LimitOverride export
3. `app/hoc/cus/controls/L6_drivers/override_driver.py` — DB persistence rewrite
4. `app/hoc/cus/hoc_spine/drivers/decisions.py` — shared engine + no commit
5. `app/hoc/int/policies/L5_engines/limit_enforcer.py` — real enforcement
6. `app/hoc/int/policies/L5_engines/usage_monitor.py` — DB persistence
7. `app/hoc/int/policies/drivers/usage_record_driver.py` — NEW L6 driver
8. `app/hoc/cus/hoc_spine/drivers/alert_emitter.py` — email wired to SMTP
9. `app/hoc/cus/hoc_spine/drivers/alert_driver.py` — inventory comments fixed
10. `app/hoc/cus/hoc_spine/drivers/transaction_coordinator.py` — rollback fencing
