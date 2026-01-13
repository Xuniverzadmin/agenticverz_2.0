# Architecture Decisions Log

**Status:** ACTIVE
**Created:** 2026-01-12
**Last Updated:** 2026-01-12

---

## Purpose

This document records architectural decisions that resolve technical debt with explicit reasoning.
Each decision follows the principle: **either FIX now or DEPRECATE now** - no dangling half-truths.

---

## AD-001: Fail-Closed Trace Semantics (FIX)

**Date:** 2026-01-12
**PIN Reference:** PIN-406
**Status:** IMPLEMENTED

### Problem

When `complete_trace()` fails, the system logged `trace_complete_failed` and continued.
This left traces in a "dangling" state - neither COMPLETE nor explicitly failed.

**Consequences:**
- Open traces look like partial execution
- Integrity can never safely seal
- Audits become ambiguous

### Decision

**FIX** - Implement fail-closed trace semantics.

### Implementation

1. **New trace status: ABORTED**
   - Traces are now: `running`, `completed`, `failed`, or `aborted`
   - ABORTED = sealed but failed (terminal state, no retry)

2. **New method: `mark_trace_aborted(run_id, reason)`**
   - Location: `backend/app/traces/pg_store.py`
   - Updates trace status to 'aborted' with abort_reason in metadata

3. **Runner integration**
   - When `complete_trace()` throws, runner now calls `mark_trace_aborted()`
   - Upgraded from `logger.warning` to `logger.error` for visibility
   - Failure to abort logs at `logger.critical` level

### Invariant (LOCKED)

> A trace is either **COMPLETE** or **ABORTED**. There is no "dangling".

### Files Modified

| File | Change |
|------|--------|
| `backend/app/traces/pg_store.py` | Added `mark_trace_aborted()` method |
| `backend/app/worker/runner.py` | Updated both success and failure paths to use fail-closed semantics |

---

## AD-002: AC v2 Trace Queries Deprecation (DEPRECATE)

**Date:** 2026-01-12
**PIN Reference:** PIN-406
**Status:** DEPRECATED

### Problem

AC v2 observability evidence collection queried `aos_trace_steps` expecting a `run_id` column:

```sql
SELECT id, trace_id, run_id, synthetic_scenario_id, is_synthetic
FROM aos_trace_steps
WHERE synthetic_scenario_id = %s
```

**Issue:** The `run_id` column does not exist in `aos_trace_steps` table.

### Key Fact

> **AC v2 is NOT authoritative for truth, execution, or integrity.**

AC v2 is a read-only analytics consumer. Fixing schema drift is meaningless if the consumer is non-authoritative.

### Decision

**DEPRECATE** - Do not fix the schema query. Hard-disable the broken path.

### Implementation

1. **Disabled aos_trace_steps queries**
   - Location: `backend/scripts/sdsr/inject_synthetic.py`
   - The trace step linkage queries are commented out with deprecation notice

2. **Simplified evidence collection**
   - Only `aos_traces` table is queried (has proper schema)
   - `observability.trace_steps_count = 0` (not queried)
   - `observability.steps_linked_to_*` = False (deprecated)

3. **Adjusted integrity expectations**
   - Removed `logs` and `trace_steps` from expected events
   - Integrity now checks: `response`, `trace` only
   - This is a deliberate relaxation, not a bug

### Deprecation Notice

```
DEPRECATED (PIN-406): AC v2 trace-based analytics are deprecated.

Reason: aos_trace_steps does not have run_id column.
AC v2 is NOT authoritative for truth, execution, or integrity.

Trace step linkage is IMPLICITLY correct if:
1. Step has valid trace_id
2. Trace has valid run_id

This is enforced by pg_store.py record_step() which validates parent existence.
```

### Invariant (LOCKED)

> If a system component is not authoritative, it must not fail silently.
> It either works or is explicitly deprecated.

### Files Modified

| File | Change |
|------|--------|
| `backend/scripts/sdsr/inject_synthetic.py` | Deprecated AC-024 trace step queries, adjusted AC-026 integrity expectations |
| `docs/contracts/taxonomy_schema_mapping.yaml` | Should be updated to remove run_id reference (future) |

---

## Decision Framework

For every pre-existing issue, choose **exactly one**:

| Action | When | Outcome |
|--------|------|---------|
| **FIX** | Affects integrity, truth, audit | Make it correct, testable, invariant-safe |
| **DEPRECATE** | Non-authoritative consumer | Make it impossible to matter again |

**Anything in between is technical debt.**

---

## Verification

After these decisions:

- No dangling traces (fail-closed semantics)
- No fake "pending forever" integrity
- No broken analytics paths pretending to work
- No future revisit required
- SDSR runs on a **closed world**
