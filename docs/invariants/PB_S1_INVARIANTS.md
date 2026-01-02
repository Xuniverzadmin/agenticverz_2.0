# PB-S1 Immutability Invariants

**Status:** FROZEN (Constitutional)
**Tests:**
- `tests/test_pb_s1_invariants.py`
- `tests/test_pb_s1_behavioral_invariants.py`
- `tests/test_pb_s1_bypass_detection.py`
**Reference:** PIN-199 (PB-S1 Retry Immutability)

---

## Overview

PB-S1 is a truth guarantee: **Retry creates NEW execution, not mutation.**

This guarantee ensures that:
- Completed/failed worker_runs cannot be mutated
- Retry operations create new rows with parent linkage
- Cost and attempt chains are preserved, never overwritten

**Constitutional Status:** These invariants are frozen. Tests must NEVER be modified to pass by changing behavior. If a test fails, the FIX must be in the application code, not the test.

---

## Structural Invariants

### 1. Immutability Trigger Exists

**What Must Be True:**
- Database trigger `worker_runs_immutable_guard` must exist
- Trigger function `prevent_worker_run_mutation()` must exist
- Trigger must fire on UPDATE of worker_runs table

**Why It Exists:**
- Prevents ANY mutation of completed/failed runs
- Enforces truth guarantee at database level (cannot be bypassed by code)

**Where Enforced:**
- `tests/test_pb_s1_invariants.py:TestPBS1ImmutabilityTrigger.test_immutability_trigger_exists`
- `tests/test_pb_s1_bypass_detection.py:TestPBS1BypassDetection.test_worker_runs_trigger_exists_in_migrations`

**What Breaks If Violated:**
- Completed runs could be silently mutated
- Historical execution data becomes unreliable
- Cost and timing data could be retroactively changed

---

### 2. Retry Schema Columns

**What Must Be True:**
- Column `parent_run_id` exists (links retry to original)
- Column `attempt` exists (monotonically increasing)
- Column `is_retry` exists (boolean flag)

**Why It Exists:**
- Enables lineage tracking
- Preserves original run while creating retry
- Allows audit of retry chains

**Where Enforced:**
- `tests/test_pb_s1_invariants.py:TestPBS1RetryCreatesNewRow.test_retry_schema_has_required_columns`

**What Breaks If Violated:**
- Retries cannot be linked to originals
- Attempt tracking fails
- Retry chains become unauditable

---

### 3. retry_history View Exists

**What Must Be True:**
- View `retry_history` must exist in database
- View provides audit trail of retry chains

**Why It Exists:**
- Enables querying complete retry lineages
- Provides compliance/audit evidence

**Where Enforced:**
- `tests/test_pb_s1_invariants.py:TestPBS1RetryCreatesNewRow.test_retry_history_view_exists`

**What Breaks If Violated:**
- Audit queries fail
- Lineage tracking requires manual joins

---

## Behavioral Invariants

### 4. Mutation of Terminal Runs is Rejected

**What Must Be True:**
- UPDATE on worker_runs WHERE status IN ('completed', 'failed') raises `RestrictViolation`
- Error message contains `TRUTH_VIOLATION`

**Why It Exists:**
- Core PB-S1 guarantee: completed runs are immutable
- Prevents "fixing" historical data
- Ensures replay fidelity

**Where Enforced:**
- `tests/test_pb_s1_invariants.py:TestPBS1ImmutabilityTrigger.test_mutation_of_failed_run_is_rejected`
- `tests/test_pb_s1_invariants.py:TestPBS1ImmutabilityTrigger.test_mutation_of_completed_run_is_rejected`

**What Breaks If Violated:**
- Historical executions can be silently altered
- Audit trail becomes unreliable
- Cost/timing data can be retroactively changed

**Forbidden Actions:**
```sql
-- These MUST fail with TRUTH_VIOLATION
UPDATE worker_runs SET status = 'queued' WHERE status = 'failed';
UPDATE worker_runs SET status = 'running' WHERE status = 'completed';
UPDATE worker_runs SET completed_at = NULL WHERE status = 'completed';
```

---

### 5. Retry Creates New Row (Not Mutation)

**What Must Be True:**
- All retries have `is_retry = true`
- All retries have `parent_run_id` set (non-NULL)
- No orphan retries exist (is_retry=true AND parent_run_id IS NULL)

**Why It Exists:**
- Retries are NEW executions, not rewrites
- Original run data is preserved
- Lineage is traceable

**Where Enforced:**
- `tests/test_pb_s1_invariants.py:TestPBS1RetryCreatesNewRow.test_retry_creates_new_row_not_mutation`
- `tests/test_pb_s1_bypass_detection.py:TestPBS1BypassDetection.test_retry_endpoint_uses_new_row`

**What Breaks If Violated:**
- Retry might overwrite original (loses history)
- Parent linkage broken
- Lineage queries fail

---

### 6. Cost Chain Invariant

**What Must Be True:**
- Original run cost is preserved after retry is created
- Retry has independent cost (not copied from parent)
- Lineage total = sum of all execution costs in chain

**Why It Exists:**
- Costs are facts, not estimates
- Each execution has its own cost (immutable)
- Total spend is computable by summing

**Where Enforced:**
- `tests/test_pb_s1_behavioral_invariants.py:TestCostChainInvariant`
  - `test_original_run_cost_preserved_after_retry`
  - `test_retry_has_independent_cost`
  - `test_lineage_cost_sum_computable`
  - `test_cost_not_zeroed_on_retry_creation`

**What Breaks If Violated:**
- Cost reporting becomes inaccurate
- Billing disputes impossible to resolve
- Historical cost data unreliable

---

### 7. Attempt Monotonicity Invariant

**What Must Be True:**
- Original runs have `attempt = 1`
- Retry attempt > parent attempt
- No duplicate attempts in a lineage
- Attempt increments by exactly 1

**Why It Exists:**
- Attempt number is canonical ordering
- Enables "which retry is this?" queries
- Prevents attempt number reuse

**Where Enforced:**
- `tests/test_pb_s1_behavioral_invariants.py:TestAttemptMonotonicityInvariant`
  - `test_original_runs_have_attempt_1`
  - `test_retry_attempt_greater_than_parent`
  - `test_no_duplicate_attempts_in_lineage`
  - `test_attempt_increments_by_one`
  - `test_attempt_sequence_integrity`

**What Breaks If Violated:**
- Attempt sequence has gaps or duplicates
- Ordering queries return wrong results
- Lineage reconstruction fails

---

### 8. /admin/rerun is Permanently Disabled

**What Must Be True:**
- Endpoint `/admin/rerun` returns HTTP 410 Gone
- Response includes `error: endpoint_removed`

**Why It Exists:**
- Rerun implies mutation (forbidden by PB-S1)
- Only retry (new row) is allowed
- Historical endpoint must remain disabled

**Where Enforced:**
- `tests/test_pb_s1_invariants.py:TestPBS1EndpointBehavior.test_rerun_endpoint_returns_410_gone`
- `tests/test_pb_s1_bypass_detection.py:TestPBS1BypassDetection.test_rerun_endpoint_returns_410`

**What Breaks If Violated:**
- Rerun could mutate historical runs
- PB-S1 guarantee violated

---

## Bypass Detection

### 9. No Raw SQL Bypass Patterns

**What Must Be True:**
- No code outside allowed paths contains dangerous UPDATE patterns:
  - `UPDATE worker_runs SET status = 'queued'`
  - `UPDATE worker_runs SET status = 'running'`
  - `UPDATE worker_runs SET completed_at = NULL`

**Allowed Paths:**
- `alembic/versions/` (migrations)
- `tests/test_pb_s1*` (tests that verify trigger rejection)
- `tests/test_pb_s2*` (crash recovery tests)

**Where Enforced:**
- `tests/test_pb_s1_bypass_detection.py:TestPBS1BypassDetection.test_no_raw_update_worker_runs_status`

**What Breaks If Violated:**
- Code could bypass trigger via raw SQL
- PB-S1 guarantee undermined

---

## Quick Reference

| Invariant | Type | What Happens If Broken |
|-----------|------|------------------------|
| Immutability trigger | Structural | Terminal runs can be mutated |
| Retry schema columns | Structural | Lineage tracking fails |
| retry_history view | Structural | Audit queries fail |
| Mutation rejection | Behavioral | History becomes mutable |
| Retry creates new row | Behavioral | Retries overwrite originals |
| Cost chain | Behavioral | Cost data unreliable |
| Attempt monotonicity | Behavioral | Attempt ordering breaks |
| /admin/rerun disabled | Behavioral | Mutation endpoint exposed |
| No raw SQL bypass | Security | Trigger can be circumvented |

---

## References

- PIN-199 (PB-S1 Retry Immutability)
- PIN-201 (Trigger Implementation)
- `tests/test_pb_s1_invariants.py`
- `tests/test_pb_s1_behavioral_invariants.py`
- `tests/test_pb_s1_bypass_detection.py`
