# Tenant ID Enforcement Audit Report

**Date:** 2025-12-30
**Reference:** PIN-052
**Status:** REMEDIATION IN PROGRESS

---

## Summary

Audit of tenant_id enforcement across all SQL queries in the AOS backend.

---

## Critical Findings Fixed

### 1. customer_visibility.py (FIXED)

**Issue:** `fetch_run_outcome()` and `fetch_decision_summary()` queried by `run_id` only, without `tenant_id` filtering.

**Risk Level:** HIGH - Could allow cross-tenant data access if run_id is guessed or leaked.

**Fix Applied:**
- Added `tenant_id` parameter to both functions
- Updated SQL queries to include `AND tenant_id = :tenant_id`
- Updated `get_outcome_reconciliation()` endpoint to pass tenant_id from request context

---

## Audit Methodology

1. Searched for all files containing `SELECT.*FROM` patterns
2. Cross-referenced with files containing `tenant_id`
3. Verified each query includes tenant_id filtering where applicable

---

## Files Reviewed

### Properly Enforced (No Action Needed)

| File | Notes |
|------|-------|
| `middleware/tenancy.py` | Middleware correctly extracts and enforces tenant_id |
| `traces/pg_store.py` | Includes tenant_id in all trace queries |
| `policy/engine.py` | Policies scoped to tenant |
| `api/ops.py` | Ops endpoints properly filtered |
| `api/traces.py` | Trace queries include tenant_id |

### Fixed in This Audit

| File | Issue | Fix |
|------|-------|-----|
| `api/customer_visibility.py` | Missing tenant_id in run/decision queries | Added tenant_id filtering |

### Remaining Review Needed

| File | Priority | Notes |
|------|----------|-------|
| `services/recovery_matcher.py` | P2 | Check failure_matches queries |
| `memory/vector_store.py` | P2 | Memory queries use agent_id (may need tenant scope) |
| `integrations/dispatcher.py` | P3 | Integration dispatch queries |

---

## Tenancy Enforcement Pattern

All customer-facing queries MUST follow this pattern:

```sql
-- CORRECT
SELECT * FROM table
WHERE id = :id AND tenant_id = :tenant_id

-- INCORRECT (security gap)
SELECT * FROM table
WHERE id = :id
```

---

## Recommendations

1. **Pre-commit Hook:** Add sqlfluff rule to detect queries missing tenant_id
2. **Integration Test:** Add cross-tenant access tests to CI
3. **Query Builder:** Consider abstraction layer that auto-injects tenant_id

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial audit, fixed customer_visibility.py |
