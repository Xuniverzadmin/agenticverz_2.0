# PIN-196: S2 Hardening — Preventive Fixes

**Status:** COMPLETE
**Category:** Verification / Hardening / Preventive
**Created:** 2025-12-26
**Milestone:** Phase A.5 — Post-S2 Hardening
**Related:** PIN-194 (S2 Acceptance), PIN-193 (S1 Truth Propagation)

---

## Purpose

After S2 acceptance, implement preventive hardening to close predictable failure classes before they surface in S3–S6.

These are pattern-based fixes derived from common verification failures:
- Timestamp semantics drift
- NULL aggregation leakage
- Advisory idempotency violations
- Budget snapshot drift
- Tenant isolation gaps
- Verification mode inconsistency

---

## Hardening Checklist

### 1. Timestamp Semantics (TIMESTAMPTZ)

| Check | Result |
|-------|--------|
| Critical tables (`cost_records`, `cost_anomalies`, `worker_runs`) | ✅ All TIMESTAMPTZ |
| Legacy tables (18 columns) | ⏸️ Documented, not blocking |
| CI guard | Recommended (future) |

**Finding:** All S2-critical tables already use `TIMESTAMPTZ`. Legacy tables have `TIMESTAMP WITHOUT TIME ZONE` but are not in the verification path.

**Rule documented:**
> All persisted timestamps MUST be TIMESTAMPTZ. TIMESTAMP WITHOUT TIME ZONE is forbidden in new tables.

---

### 2. COALESCE Guards

| File | Fixes Applied |
|------|---------------|
| `cost_anomaly_detector.py:237` | ✅ `COALESCE(SUM(...), 0)` |
| `cost_anomaly_detector.py:262` | ✅ `COALESCE(SUM(...), 0)` |
| `cost_anomaly_detector.py:342` | ✅ `COALESCE(SUM(...), 0)` |
| `cost_anomaly_detector.py:975-978` | ✅ `COALESCE(SUM(...), 0)` |

**Rule documented:**
> Aggregations must never return NULL for numeric metrics. Use COALESCE(SUM(...), 0).

---

### 3. Advisory Idempotency

| Fix | Status |
|-----|--------|
| Unique index on `(metadata->>'run_id', anomaly_type)` | ✅ Created |
| Idempotency check before insert | ✅ Implemented |

**Index:**
```sql
CREATE UNIQUE INDEX uniq_cost_advisory_per_run
ON cost_anomalies ((metadata->>'run_id'), anomaly_type)
WHERE metadata->>'run_id' IS NOT NULL;
```

**Code change:**
```python
# Before inserting, check if advisory exists
existing = await session.execute(
    text("SELECT id FROM cost_anomalies WHERE ... AND metadata->>'run_id' = :run_id"),
    {"run_id": run_id},
).scalar_one_or_none()

if existing:
    # Idempotent — skip insert
else:
    # Insert new advisory
```

---

### 4. Budget Snapshot

| Fix | Status |
|-----|--------|
| Capture budget-at-run-time in advisory metadata | ✅ Implemented |

**Advisory now includes:**
```json
{
  "run_id": "...",
  "budget_snapshot": {
    "budget_id": "s2-test-budget",
    "daily_limit_cents": 50,
    "warn_threshold_pct": 50,
    "hard_limit_enabled": false
  }
}
```

**Rule documented:**
> Budget evaluation uses budget-at-run-time snapshot, not live budget.

---

### 5. Tenant Isolation

| Test | Result |
|------|--------|
| `cost_records` isolation | ✅ PASS |
| `cost_anomalies` isolation | ✅ PASS |
| `worker_runs` isolation | ✅ PASS |
| Cross-tenant join safety | ✅ PASS |

**Test script:** `scripts/verification/tenant_isolation_test.py`

---

### 6. VERIFICATION_MODE Consistency

| Check | Result |
|-------|--------|
| Single definition | ✅ `app/api/workers.py:187` |
| Consistent usage | ✅ All invariants use same flag |
| No shadow flags | ✅ Verified |

**Definition:**
```python
VERIFICATION_MODE = os.getenv("AOS_VERIFICATION_MODE", "false").lower() == "true"
```

---

## Meta-Pattern

Every issue fixed belongs to one family:

> **"System proceeds with classification or interpretation without first persisting authoritative facts."**

This hardening systematically closes that family.

---

## Files Modified

| File | Changes |
|------|---------|
| `app/api/workers.py` | Advisory idempotency check, budget snapshot |
| `app/services/cost_anomaly_detector.py` | COALESCE guards (5 locations) |
| `scripts/verification/tenant_isolation_test.py` | New test script |

---

## Verification

All tests pass:
```
✅ PASS cost_records isolation
✅ PASS cost_anomalies isolation
✅ PASS worker_runs isolation
✅ PASS cross-tenant join safety
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Completed all 6 hardening tasks |
| 2025-12-26 | Created PIN-196 — S2 Hardening |
