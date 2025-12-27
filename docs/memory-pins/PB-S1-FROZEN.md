# PB-S1 — FROZEN

**Status:** FROZEN (Constitutional)
**Effective:** 2025-12-27
**Reference:** PIN-199

---

## Invariant Statement

> **Retry creates NEW execution. Original runs are IMMUTABLE.**

This invariant is **FROZEN** — it cannot be relaxed, bypassed, or reinterpreted.

---

## Enforcement Layers

| Layer | Mechanism | Error Code |
|-------|-----------|------------|
| **Database** | Trigger `prevent_worker_run_mutation()` | `PB-S1 VIOLATION` |
| **API** | `POST /admin/retry` creates new row | N/A |
| **API** | `POST /admin/rerun` returns HTTP 410 Gone | `endpoint_removed` |
| **Schema** | `parent_run_id`, `attempt`, `is_retry` columns | N/A |
| **CI** | `test_pb_s1_invariants.py` | Test failure |

---

## What This Means

1. **Completed/failed worker_runs cannot be modified** — Database trigger rejects all mutations
2. **Retry creates a NEW row** — With `parent_run_id` linking to original
3. **Legacy rerun endpoint is DEAD** — Returns HTTP 410 Gone
4. **Immutability is physics, not policy** — Enforced at database level

---

## Cross-Table Immutability Status

| Table | Protected | Trigger |
|-------|-----------|---------|
| `worker_runs` | ✅ YES | `prevent_worker_run_mutation()` |
| `aos_traces` | ✅ YES | `restrict_trace_update()` |
| `aos_trace_steps` | ✅ YES | `enforce_trace_step_immutability()` |

---

## Forbidden Actions (PERMANENT)

These are **NEVER allowed**, regardless of business need:

| Action | Why Forbidden |
|--------|---------------|
| UPDATE status of failed/completed run | Rewrites history |
| UPDATE timestamps of terminal run | Erases evidence |
| UPDATE error fields of terminal run | Hides truth |
| Direct UPDATE bypassing API | Violates architecture |
| Silent retry (no parent linkage) | Breaks audit trail |

---

## What Phase B CAN Do

Phase B may add:
- Crash & resume semantics (creates new execution)
- Cost attribution (reads only)
- Incident lineage (reads only)
- Advisory predictions (no writes)

Phase B **CANNOT**:
- Auto-retry (must be explicit, creates new run)
- Self-healing (cannot mutate history)
- Silent recovery (all recovery is logged)
- Outcome rewriting (facts are facts)

---

## Behavioral Invariants (Risk 2 Coverage)

In addition to immutability enforcement, PB-S1 requires these behavioral invariants:

### 1. Cost Chain Invariant

> **For any retry lineage, total_cost = sum(costs of all executions in the chain)**

| Rule | Enforcement |
|------|-------------|
| Original run cost preserved | Trigger blocks cost_cents mutation |
| Retry has independent cost | Computed at execution time |
| Lineage total = sum of parts | Computed by aggregation, never inferred |

**Anti-patterns blocked:**
- Zeroing parent cost on retry
- Copying parent cost to retry
- Inferring costs from lineage

### 2. Attempt Monotonicity Invariant

> **For a given lineage, attempt strictly increases and is never reused**

| Rule | Enforcement |
|------|-------------|
| Original run: attempt = 1 | Schema default |
| Retry: attempt = parent.attempt + 1 | Application logic |
| No duplicates in lineage | CI test verification |
| No gaps in sequence | CI test verification |

**Sequence must be:** 1 → 2 → 3 → ... (no skips, no repeats)

### CI Enforcement (Behavioral)

```bash
# Run behavioral invariant tests
cd backend && pytest tests/test_pb_s1_behavioral_invariants.py -v

# Tests that MUST pass:
# - test_original_run_cost_preserved_after_retry
# - test_retry_has_independent_cost
# - test_lineage_cost_sum_computable
# - test_original_runs_have_attempt_1
# - test_retry_attempt_greater_than_parent
# - test_no_duplicate_attempts_in_lineage
# - test_attempt_increments_by_one
```

---

## Table Scope Clarification

**IMPORTANT:** PB-S1 invariants apply ONLY to the `worker_runs` table.

| Table | PB-S1 Protected | Notes |
|-------|-----------------|-------|
| `worker_runs` | ✅ YES | Primary execution table, immutability enforced |
| `runs` | ❌ NO | Legacy table in `db.py`, excluded by design |

The `runs` table (defined in `app/db.py`) is a legacy table from earlier architecture.
PB-S1 enforcement targets `worker_runs` (defined in `app/models/tenant.py`) which is the
canonical execution table for tenant-isolated worker runs.

**Why this distinction matters:**
- `worker_runs` has tenant isolation, retry linkage, and immutability triggers
- `runs` predates the current architecture and may be deprecated
- CI bypass detection tests specifically scan for `worker_runs` mutations

---

## CI Enforcement

```bash
# Run ALL PB-S1 tests
cd backend && pytest tests/test_pb_s1_*.py -v

# 1. Immutability tests (test_pb_s1_invariants.py)
# - test_mutation_of_failed_run_is_rejected
# - test_mutation_of_completed_run_is_rejected
# - test_immutability_trigger_exists
# - test_retry_creates_new_row_not_mutation
# - test_rerun_endpoint_returns_410_gone

# 2. Behavioral invariant tests (test_pb_s1_behavioral_invariants.py)
# - Cost Chain: test_original_run_cost_preserved_after_retry
# - Cost Chain: test_lineage_cost_sum_computable
# - Attempt: test_original_runs_have_attempt_1
# - Attempt: test_no_duplicate_attempts_in_lineage

# 3. Bypass detection tests (test_pb_s1_bypass_detection.py)
# - test_no_raw_update_worker_runs_status
# - test_worker_runs_trigger_exists_in_migrations
# - test_retry_endpoint_uses_new_row
# - test_no_cross_table_confusion_in_retry
```

---

## Trigger Definition (Reference)

```sql
CREATE OR REPLACE FUNCTION prevent_worker_run_mutation()
RETURNS trigger AS $$
BEGIN
    IF OLD.status IN ('completed', 'failed') THEN
        IF (
            NEW.status != OLD.status OR
            NEW.success IS DISTINCT FROM OLD.success OR
            NEW.error IS DISTINCT FROM OLD.error OR
            NEW.output_json IS DISTINCT FROM OLD.output_json OR
            NEW.total_tokens IS DISTINCT FROM OLD.total_tokens OR
            NEW.cost_cents IS DISTINCT FROM OLD.cost_cents OR
            NEW.started_at IS DISTINCT FROM OLD.started_at OR
            NEW.completed_at IS DISTINCT FROM OLD.completed_at
        ) THEN
            RAISE EXCEPTION 'PB-S1 VIOLATION: Cannot mutate completed/failed worker_run (id=%)', OLD.id
                USING ERRCODE = 'restrict_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## Amendment Process

To modify PB-S1:

1. **STOP** — This is a constitutional invariant
2. **Escalate** — Requires explicit founder approval
3. **Document** — Full rationale in new PIN
4. **Migrate** — Schema migration with evidence
5. **Verify** — All CI tests updated and passing

**Default answer: NO.**

---

*This document is machine-referenced. Do not delete.*
