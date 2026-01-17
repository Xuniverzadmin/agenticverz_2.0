# INCIDENTS Domain API Audit

**Created:** 2026-01-16
**Domain:** INCIDENTS
**Subdomain:** EVENTS
**Topics:** ACTIVE, HISTORICAL, RESOLVED

---

## Available Endpoints (Customer-Facing)

| Endpoint | File | Auth | Purpose |
|----------|------|------|---------|
| `/api/v1/incidents` | `incidents.py:293` | Customer | Incident list |
| `/api/v1/incidents/summary` | `incidents.py:182` | Customer | Incident summary |
| `/api/v1/incidents/metrics` | `incidents.py:381` | Customer | Incident metrics |
| `/api/v1/incidents/{id}` | `incidents.py:423` | Customer | Incident detail |
| `/guard/incidents` | `guard.py:494` | Customer | Guard incidents |
| `/guard/incidents/{id}` | `guard.py:540` | Customer | Guard incident detail |
| `/v1/incidents` | `v1_killswitch.py:384` | Tenant SDK | Killswitch incidents |

---

## ⚠️ FOUNDER-ONLY Endpoints (NOT Customer-Facing)

The following endpoints require `verify_fops_token` and are **NOT for Customer Console**:

| Endpoint | File | Auth Requirement |
|----------|------|------------------|
| `/api/v1/recovery/actions` | `recovery.py:695` | **FOPS (Founder)** |
| `/api/v1/recovery/candidates` | `recovery.py:240` | **FOPS (Founder)** |
| `/integration/stats` | `integration.py:488` | **FOPS (Founder)** |
| `/integration/graduation` | `integration.py:747` | **FOPS (Founder)** |
| `/ops/incidents/*` | `ops.py` | **FOPS (Founder)** |

---

## Panel → Endpoint Mapping

### Topic: ACTIVE (INC-EV-ACT-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| INC-EV-ACT-O1 | `/api/v1/incidents` | ✅ CORRECT | None |
| INC-EV-ACT-O2 | `/api/v1/incidents/summary` | ✅ CORRECT | None |
| INC-EV-ACT-O3 | `/api/v1/incidents/metrics` | ✅ CORRECT | None |
| INC-EV-ACT-O4 | `/api/v1/ops/incidents/patterns` | ⛔ SCOPE VIOLATION | Points to ops.py (founder-only) |
| INC-EV-ACT-O5 | `/api/v1/ops/incidents/infra-summary` | ⛔ SCOPE VIOLATION | Points to ops.py (founder-only) |

### Topic: HISTORICAL (INC-EV-HIST-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| INC-EV-HIST-O1 | `/api/v1/incidents` | ✅ CORRECT | None |
| INC-EV-HIST-O2 | `/api/v1/guard/incidents` | ⚠️ PATH MISMATCH | Actual: `/guard/incidents` (no /api/v1) |
| INC-EV-HIST-O3 | `/v1/incidents` | ✅ CORRECT | v1_killswitch.py |
| INC-EV-HIST-O4 | `/api/v1/ops/incidents` | ⛔ SCOPE VIOLATION | Points to ops.py (founder-only) |
| INC-EV-HIST-O5 | `/integration/stats` | ⛔ AUTH VIOLATION | Requires FOPS token (founder-only) |

### Topic: RESOLVED (INC-EV-RES-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| INC-EV-RES-O1 | `/api/v1/incidents` | ✅ CORRECT | None |
| INC-EV-RES-O2 | `/api/v1/recovery/actions` | ⛔ AUTH VIOLATION | Requires FOPS token (founder-only) |
| INC-EV-RES-O3 | `/api/v1/recovery/candidates` | ⛔ AUTH VIOLATION | Requires FOPS token (founder-only) |
| INC-EV-RES-O4 | `/integration/graduation` | ⛔ AUTH VIOLATION | Requires FOPS token (founder-only) |
| INC-EV-RES-O5 | `/replay/{incident_id}/summary` | ⚠️ PATH MISMATCH | Actual: `/api/v1/replay/{incident_id}/summary` |

---

## Summary

| Category | Count | Panels |
|----------|-------|--------|
| ✅ Correct | 5 | O1, O2, O3 for ACT; O1, O3 for HIST; O1 for RES |
| ⚠️ Path Mismatch | 2 | INC-EV-HIST-O2, INC-EV-RES-O5 |
| ⛔ Scope Violation (ops.py) | 3 | INC-EV-ACT-O4, INC-EV-ACT-O5, INC-EV-HIST-O4 |
| ⛔ Auth Violation (FOPS) | 4 | INC-EV-HIST-O5, INC-EV-RES-O2, O3, O4 |

**Total Issues:** 9 out of 15 panels have problems

---

## Recommended Actions

### 1. Fix Path Mismatches (2 panels)

| Panel | Current | Fix To |
|-------|---------|--------|
| INC-EV-HIST-O2 | `/api/v1/guard/incidents` | `/guard/incidents` |
| INC-EV-RES-O5 | `/replay/{incident_id}/summary` | `/api/v1/replay/{incident_id}/summary` |

### 2. Reassess Scope Violations (3 panels)

These panels point to `/ops/*` which is founder-only. Options:

| Panel | Current (Founder-Only) | Customer Alternative |
|-------|------------------------|----------------------|
| INC-EV-ACT-O4 | `/api/v1/ops/incidents/patterns` | Need customer-facing pattern endpoint |
| INC-EV-ACT-O5 | `/api/v1/ops/incidents/infra-summary` | Need customer-facing infra summary |
| INC-EV-HIST-O4 | `/api/v1/ops/incidents` | Use `/api/v1/incidents` or `/guard/incidents` |

### 3. Reassess Auth Violations (4 panels)

These panels point to FOPS-auth endpoints. Either:
- A) Create customer-facing equivalents
- B) Remove panels from customer console
- C) Create adapters that proxy with appropriate auth

| Panel | Current (FOPS Required) | Action Needed |
|-------|-------------------------|---------------|
| INC-EV-HIST-O5 | `/integration/stats` | Create `/guard/integration/stats` |
| INC-EV-RES-O2 | `/api/v1/recovery/actions` | Create `/guard/recovery/actions` |
| INC-EV-RES-O3 | `/api/v1/recovery/candidates` | Create `/guard/recovery/candidates` |
| INC-EV-RES-O4 | `/integration/graduation` | Create `/guard/graduation` |

---

## Critical Finding

**7 out of 15 INCIDENTS panels point to founder-only endpoints.**

These panels should NOT be in the Customer Console without:
1. Creating customer-safe adapter endpoints
2. Proper tenant isolation
3. Removing founder-sensitive data from responses

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial audit created |
