# PIN-547: Domain Linkage Implementation — Test Results & Issues

**Created:** 2026-02-09
**Status:** COMPLETE
**Commit:** `214513c8`
**Related:** PIN-546 (run linkage + governance log scoping), PIN-412 (domain design incidents/policies), PIN-545 (guardrail violations)

---

## Test & CI Results

| Suite | Count | Result |
|-------|-------|--------|
| hoc_spine | 41 | 41 passed |
| lifecycle | 59 | 59 passed |
| coordinator | 10 | 10 passed |
| CI hygiene | 30 checks | All passed, 0 blocking |
| Migration 124 | 1 | Applied — `prevention_records` created with all 15 columns + 7 indexes |
| Governance | 2170+ | 2170 passed, 1 pre-existing failure (not ours) |

---

## Bug Fixes (found during verification)

### 1. `::uuid` cast in SQL — `run_metrics_driver.py`

**Root Cause:** SQL used `WHERE id = :run_id::uuid` but `Run.id` is `VARCHAR`, not UUID. Would cause Postgres cast error at runtime.

**Fix:** Removed `::uuid` from all SQL statements.

### 2. Draft count hook in wrong handler — `policies_handler.py`

**Root Cause:** `convert_lesson_to_draft` hook was placed in `PoliciesGovernanceHandler` — but that operation is dispatched by `PoliciesLessonsHandler`. The code also referenced undefined variable `engine` (governance handler uses `facade`). Result: dead code that would never execute.

**Fix:** Moved hook to `PoliciesLessonsHandler.execute()`, used `ctx.session`.

### 3. `prevention_records` table missing — Migration 124

**Root Cause:** Local/staging DB was stamped at revision 123 without running intermediate migrations (043/044/077/079). `ALTER TABLE prevention_records ADD COLUMN run_id` fails because the table doesn't exist.

**Fix:** Made migration 124 resilient — inspects DB via `sqlalchemy.inspect()`, creates full table (15 columns from 4 migrations) if missing, otherwise just adds `run_id` column.

### 4. Test mock uses old API — `test_run_introspection_coordinators.py`

**Root Cause:** Test mocked `MagicMock.list_incidents()` (sync, old `IncidentReadService` API). Coordinator now calls `await reader.fetch_incidents_by_run_id()` (async, new `IncidentRunReadDriver` API). `MagicMock` can't be awaited → exception caught by coordinator's try/except → silent empty list.

**Fix:** Changed to `AsyncMock.fetch_incidents_by_run_id()`.

### 5. Test mock uses wrong dict keys — `test_run_introspection_coordinators.py`

**Root Cause:** Mock data had `"action_taken": "WARNED"` but coordinator reads `ev.get("outcome")` (matching `prevention_records` column name). `_derive_decisions()` got `outcome=None` → filtered out → `decisions_made` empty → assertion failed.

**Fix:** Changed mock key from `action_taken` → `outcome`, `rule_id` → `policy_id`.

---

## Pre-Existing Issues (not introduced by our changes)

### 6. `resolution_method` kwarg ignored

**Where:** `incident_write_engine.py:222` → `audit_ledger_engine.incident_resolved()`

Passes `resolution_method=resolution_method` but the method signature doesn't accept it. Would silently fail or raise `TypeError` depending on `**kwargs`. Pre-existing — not in our diff.

### 7. `isinstance` double-import failure

**Where:** `test_founder_review_invariants.py:775`

`isinstance(service, ContractService)` returns `False` due to module double-import (different module identities). Pre-existing.

### 8. Missing `billing_dependencies.py`

**Where:** `test_layer_boundaries.py:262`

Test asserts file exists but it was deleted. Pre-existing.

---

## Fixes Applied During Testing

1. **Migration 124 resilience** — Added `IF NOT EXISTS` logic: creates the full `prevention_records` table (with all columns from 043/044/077/079) when the table is missing on stamped DBs, otherwise just adds `run_id` column.
2. **Test mock update** — `test_run_introspection_coordinators.py`: changed incident mock from sync `MagicMock.list_incidents()` to async `AsyncMock.fetch_incidents_by_run_id()`, and updated policy mock dict keys from `action_taken` → `outcome` to match the new `prevention_records` schema.

---

## Lessons Learned

- **Stamped DBs miss tables:** When a staging DB is stamped forward (e.g., `alembic stamp head`), intermediate `CREATE TABLE` migrations are skipped. Always use `sqlalchemy.inspect()` to check table existence before `ADD COLUMN`.
- **Silent try/except swallows mock errors:** Coordinator's `try/except → return []` pattern makes sync/async mock mismatches invisible. Tests pass with empty results instead of failing loudly. Always verify positive assertions (e.g., `len > 0`), not just absence of errors.
- **Dict key mismatches after schema changes:** When switching from one data source to another (e.g., `policy_enforcements` → `prevention_records`), column names change. Test mocks must be updated to match the new schema's column names.
- **Check dispatch tables before adding hooks:** Before adding post-execution hooks to a handler, verify the operation is actually dispatched by that handler class's dispatch table — not a sibling handler.
