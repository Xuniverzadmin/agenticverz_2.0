# PIN-267: Test → System Protection Rule

**Status:** ACTIVE
**Created:** 2026-01-01
**Category:** CI Rediscovery / Governance
**Related PINs:** PIN-265 (M12 boundary), PIN-266 (test tracker)

---

## Executive Summary

Tests (L8) can damage the core product (L7 downward) if they encode false truths. This PIN establishes the classification system and protection rules discovered during CI rediscovery Slice-4.

---

## 1. The Damage Path

Tests influence reality through:

| Path | Mechanism | Risk |
|------|-----------|------|
| L8 → L7 | Engineers change prod code to satisfy wrong tests | Semantic drift |
| L8 → L6 | Tests hide race conditions, assume missing constraints | Data integrity holes |
| L8 → L5/L4 | Tests normalize unsafe retries, contradict intent | Recovery corruption |

**Most dangerous:** L8 → L7 (engineers believe tests are "correct")

---

## 2. Test Failure Classification (MANDATORY)

Every failing test **must** be classified into exactly one bucket:

### Bucket A — Test is Wrong (L8 defect)

Examples:
- Constructor vs factory mismatch
- Assertion drift
- Infra absent locally

**Response:**
- Fix test
- Add prevention (markers, helpers)

### Bucket B — Infra is Missing (L6 absence)

Examples:
- Missing agents schema
- Optional capability not present

**Response:**
- Add explicit capability markers
- Skip truthfully
- Document boundary (like M12)

### Bucket C — System Semantics are Wrong (L6/L5/L4 bug)

Examples:
- Missing uniqueness constraint
- Unsafe ON CONFLICT usage
- Race conditions under load

**Response:**
- **Must be fixed in core system**
- **Must get prevention**
- Tests may NOT be weakened

---

## 3. Protection Rule (NON-NEGOTIABLE)

> **If a test reveals a data-race or integrity issue, the fix must occur in the lowest possible layer (L6 > L5 > L4).**
> **Tests may not be weakened to hide correctness gaps.**

### What This Means

| If Test Reveals | Fix Layer | NOT Allowed |
|-----------------|-----------|-------------|
| Missing DB constraint | L6 (schema) | Skip test permanently |
| Race condition | L6/L5 (serialize or lock) | Add retry to hide race |
| Data integrity hole | L6 (constraint) | Mock it away |
| Intent contradiction | L4 (domain) | Weaken assertion |

---

## 4. Anti-Patterns (FORBIDDEN)

Do **not**:
- Permanently skip chaos tests that reveal races
- "Stabilize" by weakening assertions
- Add retries to hide races
- Push correctness issues up into workers or tests

---

## 5. Prevention Pattern

When a Bucket C issue is discovered:

1. **Fix the root cause** in the lowest layer
2. **Add schema invariant test** that asserts constraint presence
3. **Add concurrency invariant test** that must pass under load
4. **CI must fail** if invariant regresses

---

## 6. Slice-4 Example (Applied)

### Issue 1: Missing Constraint

- **Found:** `uq_work_queue_candidate_pending` not in local DB
- **Classification:** Bucket C (L6 bug)
- **Response:** Fix schema, add invariant test

### Issue 2: Race Conditions in Chaos Tests

- **Found:** ON CONFLICT doesn't cover all unique constraints
- **Classification:** Bucket C (L6 bug)
- **Response:** Fix upsert logic, keep chaos tests active

---

## 7. Test Classification Checklist

Before skipping or fixing any test:

```
TEST CLASSIFICATION CHECKLIST
- Bucket A (test wrong): Does test assume constructor vs factory? YES/NO
- Bucket A (test wrong): Is assertion stale? YES/NO
- Bucket B (infra missing): Is required schema/capability absent? YES/NO
- Bucket C (system bug): Does test reveal race condition? YES/NO
- Bucket C (system bug): Does test reveal data integrity gap? YES/NO
- If Bucket C → Fix must be in L6/L5/L4, not L8
```

---

## 8. SESSION_PLAYBOOK Addition

Add to SESSION_PLAYBOOK:

```yaml
test_system_protection:
  status: ENFORCED
  rule: |
    If a test reveals a data-race or integrity issue, the fix must occur
    in the lowest possible layer (L6 > L5 > L4).
    Tests may not be weakened to hide correctness gaps.
  classification_required: true
  buckets:
    A: "Test is wrong (L8 defect)"
    B: "Infra is missing (L6 absence)"
    C: "System semantics wrong (L6/L5/L4 bug)"
  bucket_c_response:
    - fix_in_lowest_layer
    - add_invariant_test
    - ci_must_fail_on_regression
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-01 | Establish test classification system | Prevent L8 → L6 damage |
| 2026-01-01 | Create protection rule | Tests may not hide correctness gaps |
| 2026-01-01 | Require invariant tests for Bucket C fixes | Prevent regression |

---

## References

- PIN-266 (Test Repair Execution Tracker)
- `docs/ci/CI_REDISCOVERY_MASTER_ROADMAP.md`
- Slice-4 findings (M10 recovery tests)
