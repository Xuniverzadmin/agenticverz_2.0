# LOGS Domain API Audit

**Created:** 2026-01-16
**Domain:** LOGS
**Subdomain:** RECORDS
**Topics:** AUDIT, LLM_RUNS, SYSTEM_LOGS

---

## Available Endpoints (Customer-Facing)

| Endpoint | File | Full Path | Auth |
|----------|------|-----------|------|
| traces.py | `/traces/*` | `/api/v1/traces/*` | No explicit auth |
| rbac_api.py | `/api/v1/rbac/audit` | `/api/v1/rbac/audit` | No explicit auth |
| status_history.py | `/status_history/*` | `/status_history/*` | No explicit auth |
| runtime.py | `/api/v1/runtime/traces` | `/api/v1/runtime/traces` | No explicit auth |
| guard_logs.py | `/guard/logs/*` | `/guard/logs/*` | Console auth |
| health.py | `/health/*` | `/health/*` | Public |

---

## Panel → Endpoint Mapping

### Topic: AUDIT (LOG-REC-AUD-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| LOG-REC-AUD-O1 | `/api/v1/traces` | ✅ CORRECT | traces.py |
| LOG-REC-AUD-O2 | `/api/v1/rbac/audit` | ✅ CORRECT | rbac_api.py |
| LOG-REC-AUD-O3 | `/ops/actions/audit` | ⛔ SCOPE VIOLATION | Points to founder_actions.py (FOPS auth) |
| LOG-REC-AUD-O4 | `/status_history` | ✅ CORRECT | status_history.py |
| LOG-REC-AUD-O5 | (no endpoint) | ⚠️ MISSING | No assumed_endpoint in YAML |

### Topic: LLM_RUNS (LOG-REC-LLM-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| LOG-REC-LLM-O1 | `/api/v1/runtime/traces` | ✅ CORRECT | runtime.py |
| LOG-REC-LLM-O2 | `/api/v1/activity/runs` | ✅ CORRECT | activity.py |
| LOG-REC-LLM-O3 | `/api/v1/customer/activity` | ✅ CORRECT | customer_activity.py |
| LOG-REC-LLM-O4 | `/api/v1/tenants/runs` | ⚠️ NEEDS VERIFY | Check if endpoint exists |
| LOG-REC-LLM-O5 | `/api/v1/traces/mismatches` | ⚠️ NEEDS VERIFY | Check if endpoint exists |

### Topic: SYSTEM_LOGS (LOG-REC-SYS-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| LOG-REC-SYS-O1 | `/guard/logs` | ✅ CORRECT | guard_logs.py |
| LOG-REC-SYS-O2 | `/health` | ✅ CORRECT | health.py |
| LOG-REC-SYS-O3 | `/health/ready` | ✅ CORRECT | health.py |
| LOG-REC-SYS-O4 | `/health/adapters` | ✅ CORRECT | health.py |
| LOG-REC-SYS-O5 | `/health/skills` | ✅ CORRECT | health.py |

---

## Summary

| Category | Count | Details |
|----------|-------|---------|
| ✅ Correct | 11 | Paths match actual endpoints |
| ⚠️ Needs Verify | 2 | LOG-REC-LLM-O4, O5 |
| ⚠️ Missing | 1 | LOG-REC-AUD-O5 (no endpoint) |
| ⛔ Scope Violation | 1 | LOG-REC-AUD-O3 (founder-only) |

**Total Panels:** 15
**Issues:** 4

---

## Key Findings

### 1. LOG-REC-AUD-O3 Points to Founder-Only Endpoint

The panel expects `/ops/actions/audit` which is a founder-only endpoint (FOPS auth required).

**Options:**
- A) Create customer-facing audit endpoint at `/guard/actions/audit`
- B) Remove panel from customer console
- C) This panel may be intended for Ops Console only

### 2. LOG-REC-AUD-O5 Has No Endpoint

The intent YAML has no `assumed_endpoint` value. Need to determine:
- What data this panel should display
- Create appropriate endpoint

### 3. Endpoints Needing Verification

| Endpoint | Check |
|----------|-------|
| `/api/v1/tenants/runs` | Verify in tenants.py |
| `/api/v1/traces/mismatches` | Verify in traces.py |

---

## Recommended Actions

### 1. Fix Scope Violation

| Panel | Current (Founder-Only) | Customer Alternative |
|-------|------------------------|----------------------|
| LOG-REC-AUD-O3 | `/ops/actions/audit` | Create `/guard/actions/audit` |

### 2. Define Missing Endpoint

LOG-REC-AUD-O5 needs:
- Endpoint definition
- Data shape specification
- Intent YAML update

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial audit created |
