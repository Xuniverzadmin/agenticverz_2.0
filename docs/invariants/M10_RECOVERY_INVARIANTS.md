# M10 Recovery Module Invariants

**Status:** ACTIVE
**Tests:** `tests/invariants/test_m10_invariants.py`
**Reference:** PIN-267 (Test System Protection Rule)

---

## Overview

The M10 recovery module handles failure detection, recovery candidate tracking, and work queue management. These invariants ensure the recovery system functions correctly under concurrent access.

---

## Schema Invariants

### 1. m10_recovery Schema Exists

**What Must Be True:**
- A PostgreSQL schema named `m10_recovery` must exist
- This schema contains recovery-specific tables (e.g., `work_queue`)

**Why It Exists:**
- Logical separation of recovery infrastructure from main application tables
- Allows independent permission and backup management

**Where Enforced:**
- `tests/invariants/test_m10_invariants.py:TestM10SchemaInvariants.test_m10_recovery_schema_exists`

**What Breaks If Violated:**
- Work queue operations fail with "schema does not exist" errors
- DB fallback for Redis unavailability fails

---

### 2. recovery_candidates Table in Public Schema

**What Must Be True:**
- Table `recovery_candidates` must exist in `public` schema (not `m10_recovery`)

**Why It Exists:**
- Historical: table predates schema separation
- Used by multiple modules beyond M10

**Where Enforced:**
- `tests/invariants/test_m10_invariants.py:TestM10SchemaInvariants.test_recovery_candidates_table_exists`

**What Breaks If Violated:**
- `enqueue_work` function fails
- Recovery candidate upserts fail

---

### 3. failure_match_id Unique Constraint

**What Must Be True:**
- Unique constraint `recovery_candidates_failure_match_id_key` must exist on `failure_match_id` column

**Why It Exists:**
- Enables `ON CONFLICT (failure_match_id) DO UPDATE` upsert pattern
- Prevents duplicate candidates for the same failure

**Where Enforced:**
- `tests/invariants/test_m10_invariants.py:TestM10SchemaInvariants.test_failure_match_id_unique_constraint_exists`

**What Breaks If Violated:**
- Concurrent upserts fail with duplicate key errors
- Recovery candidates accumulate duplicates

**Correct Pattern:**
```sql
INSERT INTO recovery_candidates (...)
ON CONFLICT (failure_match_id) DO UPDATE
SET occurrence_count = recovery_candidates.occurrence_count + 1,
    updated_at = now();
```

---

### 4. Partial Unique Index uq_rc_fmid_sig

**What Must Be True:**
- Partial unique index `uq_rc_fmid_sig` exists on `(failure_match_id, error_signature)`
- Index has `WHERE error_signature IS NOT NULL` clause

**Why It Exists:**
- Provides additional uniqueness for candidates with signatures
- Allows NULL signatures to coexist

**Where Enforced:**
- `tests/invariants/test_m10_invariants.py:TestM10SchemaInvariants.test_partial_unique_index_fmid_sig_exists`

**What Breaks If Violated:**
- Candidates with same failure_match_id but different signatures become duplicates

**CRITICAL WARNING:**
```
ON CONFLICT (failure_match_id, error_signature) WILL NOT WORK
because uq_rc_fmid_sig is a PARTIAL index.
Use ON CONFLICT (failure_match_id) instead.
```

---

### 5. work_queue Table Exists

**What Must Be True:**
- Table `work_queue` must exist in `m10_recovery` schema

**Why It Exists:**
- Provides DB fallback when Redis is unavailable
- Ensures recovery work can be enqueued even during Redis outages

**Where Enforced:**
- `tests/invariants/test_m10_invariants.py:TestM10SchemaInvariants.test_work_queue_table_exists`

**What Breaks If Violated:**
- Redis fallback fails completely
- Recovery work is lost during Redis outages

---

## Concurrency Invariants

### 1. Dual-Constraint Race Condition (Bucket C)

**Root Cause:**
- `recovery_candidates` has TWO unique constraints on failure_match_id:
  1. `recovery_candidates_failure_match_id_key` (full constraint)
  2. `uq_rc_fmid_sig` partial index (failure_match_id, error_signature WHERE NOT NULL)
- `ON CONFLICT (failure_match_id)` only handles constraint #1
- Under high concurrency, constraint #2 can trigger first

**Symptoms:**
- `UniqueViolation` in concurrent upserts
- Intermittent failures under load
- Test `test_100_concurrent_upserts_single_candidate` fails probabilistically

**Correct L6 Fixes (choose one):**
1. Remove partial index and use full unique constraint
2. Change upsert to `ON CONFLICT ON CONSTRAINT recovery_candidates_failure_match_id_key`
3. Use SERIALIZABLE isolation for critical paths

**Forbidden "Fixes" (per PIN-267):**
- Adding retry loop in tests (hides race)
- Reducing test concurrency (hides race)
- Catching and ignoring UniqueViolation (hides race)
- Marking test as skip/xfail to avoid CI failure without documentation

**Reference:**
- `tests/invariants/test_m10_invariants.py:TestM10ConcurrencyInvariants.test_dual_constraint_race_documented`
- PIN-267 Section 3

---

### 2. Connection Pool Exhaustion (Bucket B)

**Root Cause:**
- Local PostgreSQL has `max_connections` limit
- 1000+ concurrent threads opening connections exhausts pool
- Results in "too many clients already" error

**Classification:** Bucket B (Infrastructure)
- Not a code bug but an infrastructure capacity limit
- Production uses PgBouncer which handles this
- Test documents the limitation

**Correct Fixes:**
- Use connection pooling in tests (SQLAlchemy pool)
- Reduce test concurrency to match local capacity
- Skip test in environments without pooling

**Reference:**
- `tests/invariants/test_m10_invariants.py:TestM10ConcurrencyInvariants.test_connection_pool_limit_documented`

---

## Quick Reference

| Invariant | Type | What Happens If Broken |
|-----------|------|------------------------|
| m10_recovery schema | Schema | Work queue operations fail |
| recovery_candidates table | Schema | Upserts fail |
| failure_match_id unique | Schema | Duplicate candidates, race errors |
| uq_rc_fmid_sig partial index | Schema | Signature uniqueness lost |
| work_queue table | Schema | Redis fallback fails |
| Dual-constraint race | Concurrency | Intermittent UniqueViolation |
| Connection pool limit | Concurrency | "too many clients" under load |

---

## References

- PIN-267 (Test System Protection Rule)
- `tests/invariants/test_m10_invariants.py`
- `tests/test_m10_recovery_enhanced.py` (chaos tests)
