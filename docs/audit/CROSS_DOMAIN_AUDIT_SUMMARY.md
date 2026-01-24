# Cross-Domain API Audit Summary

**Created:** 2026-01-16
**Scope:** All 5 Customer Console Domains
**Audit Files:**
- `DOMAIN_AUDIT_ACTIVITY.md`
- `DOMAIN_AUDIT_INCIDENTS.md`
- `DOMAIN_AUDIT_POLICIES.md`
- `DOMAIN_AUDIT_LOGS.md`
- `DOMAIN_AUDIT_OVERVIEW.md`

---

## Executive Summary

| Domain | Total Panels | Correct | Issues | Issue Rate |
|--------|-------------|---------|--------|------------|
| ACTIVITY | 13 | 3 | 10 | 77% |
| INCIDENTS | 15 | 5 | 10 | 67% |
| POLICIES | 25 | 11 | 14 | 56% |
| LOGS | 15 | 11 | 4 | 27% |
| OVERVIEW | 11 | 0 | 11 | 100% |
| **TOTAL** | **79** | **30** | **49** | **62%** |

---

## Issue Breakdown by Category

### 1. Needs Binding (null endpoints) — 24 panels

Panels with `assumed_endpoint: null` that need to be wired to appropriate endpoints.

| Domain | Count | Recommended Endpoint |
|--------|-------|---------------------|
| ACTIVITY | 10 | `/api/v1/runtime/activity/runs` |
| OVERVIEW | 10 | `/api/v1/runtime/overview/*` (varies by topic) |
| INCIDENTS | 0 | — |
| POLICIES | 2 | Need verification |
| LOGS | 1 | Need definition |

### 2. Path Mismatch — 15 panels

Panels where the intent YAML has an incorrect path vs actual backend endpoint.

| Domain | Count | Primary Issue |
|--------|-------|---------------|
| POLICIES | 13 | Missing `/api/v1` prefix for `/policy-layer/*` |
| INCIDENTS | 2 | Wrong prefix (e.g., `/api/v1/guard/*` vs `/guard/*`) |
| LOGS | 0 | — |
| ACTIVITY | 0 | — |
| OVERVIEW | 1 | Points to `/api/v1/activity/summary` instead of runtime projection |

### 3. Scope/Auth Violations — 8 panels

Panels pointing to founder-only (FOPS auth) endpoints that should NOT be in Customer Console.

| Domain | Count | Offending Endpoints |
|--------|-------|---------------------|
| INCIDENTS | 7 | `/ops/*`, `/api/v1/recovery/*`, `/integration/*` |
| LOGS | 1 | `/ops/actions/audit` |
| POLICIES | 0 | — |
| ACTIVITY | 0 | — |
| OVERVIEW | 0 | — |

### 4. Needs Verification — 2 panels

Endpoints referenced in intent YAMLs that need backend verification.

| Domain | Panel | Endpoint |
|--------|-------|----------|
| POLICIES | POL-LIM-THR-O3 | `/api/v1/tenants/tenant/quota/runs` |
| POLICIES | POL-LIM-THR-O4 | `/api/v1/tenants/tenant/quota/tokens` |

---

## Critical Findings

### 1. INCIDENTS Domain Has Major Auth Issues

**7 of 15 INCIDENTS panels point to founder-only endpoints:**

| Panel | Current Endpoint | Auth Required |
|-------|------------------|---------------|
| INC-EV-ACT-O4 | `/api/v1/ops/incidents/patterns` | FOPS |
| INC-EV-ACT-O5 | `/api/v1/ops/incidents/infra-summary` | FOPS |
| INC-EV-HIST-O4 | `/api/v1/ops/incidents` | FOPS |
| INC-EV-HIST-O5 | `/integration/stats` | FOPS |
| INC-EV-RES-O2 | `/api/v1/recovery/actions` | FOPS |
| INC-EV-RES-O3 | `/api/v1/recovery/candidates` | FOPS |
| INC-EV-RES-O4 | `/integration/graduation` | FOPS |

**Action Required:** Either create customer-safe adapter endpoints or remove these panels from Customer Console.

### 2. POLICIES Domain Has Systematic Path Issue

**13 panels missing `/api/v1` prefix:**

The `policy_layer.py` router has `prefix="/policy-layer"` but is mounted with `prefix="/api/v1"` in main.py. All intent YAMLs reference `/policy-layer/*` but actual paths are `/api/v1/policy-layer/*`.

**Fix:** Bulk update all `/policy-layer/*` references to `/api/v1/policy-layer/*`.

### 3. OVERVIEW Domain Completely Unwired

**All 11 OVERVIEW panels have issues:**
- 1 panel points to wrong endpoint
- 10 panels have `null` endpoints

The Overview runtime projection (`/api/v1/runtime/overview/*`) exists and has proper endpoints, but no intent YAMLs point to it.

### 4. ACTIVITY O2+ Panels Need Runtime Projection Binding

**10 of 13 ACTIVITY panels have null endpoints:**
- O1 panels correctly use `/api/v1/activity/runs`
- O2+ panels need `/api/v1/runtime/activity/runs` for enhanced schema

---

## Recommended Fix Prioritization

### Priority 1: Auth Violations (BLOCKING)

Customer Console must NOT call founder-only endpoints. These panels are security risks.

| Action | Panels Affected |
|--------|-----------------|
| Create customer-safe adapters OR remove from console | 8 panels (7 INCIDENTS + 1 LOGS) |

### Priority 2: Path Mismatches (FUNCTIONAL)

Panels with wrong paths will fail at runtime.

| Action | Panels Affected |
|--------|-----------------|
| Add `/api/v1` prefix to `/policy-layer/*` paths | 13 POLICIES panels |
| Fix INC-EV-HIST-O2: `/api/v1/guard/incidents` → `/guard/incidents` | 1 panel |
| Fix INC-EV-RES-O5: `/replay/{id}/summary` → `/api/v1/replay/{id}/summary` | 1 panel |
| Fix POL-GOV-ACT-O3: `/api/v1/policies/requests` → `/api/v1/policy/requests` | 1 panel |
| Fix OVR-SUM-HL-O1: `/api/v1/activity/summary` → `/api/v1/runtime/overview/highlights` | 1 panel |

### Priority 3: Null Bindings (ENHANCEMENT)

Panels with null endpoints are non-functional but not broken.

| Action | Panels Affected |
|--------|-----------------|
| Bind ACTIVITY O2+ panels to `/api/v1/runtime/activity/runs` | 10 panels |
| Bind OVERVIEW panels to runtime projection | 10 panels |
| Verify and bind POLICIES quota endpoints | 2 panels |
| Define LOG-REC-AUD-O5 endpoint | 1 panel |

---

## Scope Exclusions

Per user directive, the following are OUT OF SCOPE for Customer Console:

| Router | Path Prefix | Reason |
|--------|-------------|--------|
| `ops.py` | `/ops/*` | Founder/Backend only |
| `founder_actions.py` | `/ops/actions/*` | Founder/Backend only |
| `cost_ops.py` | `/ops/cost/*` | Founder/Backend only |
| `recovery.py` | `/api/v1/recovery/*` | FOPS auth required |
| `integration.py` | `/integration/*` | FOPS auth required |

Any panel pointing to these endpoints is a **scope violation**.

---

## Customer-Facing Route Prefixes

The following prefixes are SAFE for Customer Console:

| Prefix | Router(s) | Auth |
|--------|-----------|------|
| `/guard/*` | guard.py, guard_policies.py, guard_logs.py, cost_guard.py | Console auth |
| `/api/v1/cus/*` | customer_activity.py | Customer-safe |
| `/api/v1/runtime/*` | runtime_projections/* | Tenant auth |
| `/api/v1/policy-layer/*` | policy_layer.py | No explicit auth |
| `/api/v1/policy-proposals/*` | policy_proposals.py | No explicit auth |
| `/api/v1/incidents/*` | incidents.py | Customer |
| `/api/v1/activity/*` | activity.py | No explicit auth |
| `/api/v1/traces/*` | traces.py | No explicit auth |
| `/health/*` | health.py | Public |

---

## Next Steps

1. **Review this summary with stakeholders**
2. **Decide on auth violation remediation** (adapters vs removal)
3. **Execute bulk path fixes** for POLICIES domain
4. **Wire OVERVIEW runtime projection** endpoints
5. **Bind ACTIVITY O2+ panels** to runtime projection
6. **Verify tenant quota endpoints** exist

---

## Audit Files Location

```
docs/audit/
├── API_FIX_PLAN.md                    # Original fix plan (updated)
├── CROSS_DOMAIN_AUDIT_SUMMARY.md      # This file
├── DOMAIN_AUDIT_ACTIVITY.md           # ACTIVITY domain details
├── DOMAIN_AUDIT_INCIDENTS.md          # INCIDENTS domain details
├── DOMAIN_AUDIT_POLICIES.md           # POLICIES domain details
├── DOMAIN_AUDIT_LOGS.md               # LOGS domain details
└── DOMAIN_AUDIT_OVERVIEW.md           # OVERVIEW domain details
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial cross-domain summary created |
