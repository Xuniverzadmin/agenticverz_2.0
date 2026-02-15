# PIN-553: RunProof Gap Validation v1 — Postgres Trace Proof Closed

**Status:** ✅ COMPLETE
**Created:** 2026-02-10
**Category:** HOC Governance / Validation

---

## Summary

Executed runproof_gap_validation_plan_v1.md: all 4 acceptance criteria PASS. Found and fixed S6 immutability trigger (reject_trace_update_lifecycle) that blocked trace completion — every trace was stuck at status=running. Trigger now allows status/completed_at/metadata updates while preserving content immutability. RunProofCoordinator returns HASH_CHAIN + VERIFIED with full Postgres trace (aos_traces=completed, aos_trace_steps=1). Report: docs/architecture/hoc/runproof_gap_validation_plan_v1_executed.md

---

## Acceptance Criteria Results

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Postgres traces created (`aos_traces` row exists) | **PASS** — status=`completed` |
| 2 | Postgres trace steps exist (`aos_trace_steps` >= 1) | **PASS** — 1 step (http_call) |
| 3 | RunProofCoordinator returns `HASH_CHAIN` + `VERIFIED` | **PASS** |
| 4 | Fixes documented with file references | **PASS** |

## Run Evidence

| Field | Value |
|-------|-------|
| Run ID | `89ceeaba-1aa4-42ad-b93e-4bdcd72d75b6` |
| Tenant ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Status | `succeeded` |
| Trace Status | `completed` (previously stuck at `running`) |
| Integrity Model | `HASH_CHAIN` |
| Verification Status | `VERIFIED` |
| Root Hash | `d4ce6cf4a8984214901e97b1635ecec3a7562e401b1015680535b18ab35b35b8` |

## Bug Found and Fixed

### S6 Immutability Trigger Blocking Trace Completion (BLOCKING)

**Trigger:** `prevent_trace_update` on `aos_traces` → `reject_trace_update_lifecycle()`

**Problem:** The trigger only allowed archival UPDATEs (`archived_at: NULL → timestamp`) but blocked ALL other UPDATEs — including trace lifecycle transitions (`status`, `completed_at`, `metadata`). Every trace in the system was permanently stuck at `status=running`.

**Two conflicting functions existed:**

| Function | Logic | Had Trigger? |
|----------|-------|-------------|
| `restrict_trace_update` (old) | Allows status/completed_at/metadata changes | No (orphaned) |
| `reject_trace_update_lifecycle` (active) | Blocks all except archival | Yes |

**Fix:** Updated `reject_trace_update_lifecycle()` with two exceptions:
1. Archival — `archived_at` NULL → timestamp (existing)
2. Trace completion — `status`/`completed_at`/`metadata` may change, all content fields must be unchanged (new)

**Verification:** Full lifecycle test: `start_trace` → `record_step` → `complete_trace` → `get_trace` (status=`completed`, steps=1).


---

## Updates

### Update (2026-02-10)

Codified the S6 trace completion exception in new Alembic migration backend/alembic/versions/126_s6_trace_completion_allowed.py so clean environments allow status/completed_at/metadata updates while preserving content immutability. Re-homed tracing to HOC canonical locations: added backend/app/hoc/cus/logs/L6_drivers/trace_store.py, backend/app/hoc/cus/logs/L6_drivers/redact.py, and backend/app/hoc/cus/logs/L6_drivers/idempotency.lua, updated imports across runtime/services/tests/CLI to use HOC paths, and deleted legacy backend/app/traces/ to remove duplication. Note: docs still reference app/traces/* and should be updated.


## Related PINs

| PIN | Relationship |
|-----|-------------|
| PIN-552 | Test Plan v4 execution — pre-requisite fixes (imports, enforcement guard) |
| PIN-193/194 | S6 Trace Integrity Truth — immutability semantics |
| PIN-378 | SDSR Canonical Logs System — trace source/level |
| PIN-404 | Trace identity propagation — `trace_id` passed not derived |
| PIN-406 | Fail-closed trace semantics — COMPLETE or ABORTED |

## Artifacts

| Artifact | Path |
|----------|------|
| Validation Plan | `docs/architecture/hoc/runproof_gap_validation_plan_v1.md` |
| Execution Report | `docs/architecture/hoc/runproof_gap_validation_plan_v1_executed.md` |
| Trigger Function | `reject_trace_update_lifecycle()` (in-DB, updated via DDL) |
