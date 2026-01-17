# POLICIES Domain API Audit

**Created:** 2026-01-16
**Updated:** 2026-01-17
**Domain:** POLICIES
**Subdomains:** GOVERNANCE, LIMITS
**Topics:** ACTIVE, DRAFTS, POLICY_LIBRARY, THRESHOLDS, VIOLATIONS

---

## Facade Architecture

The **policy-layer facade** (`/api/v1/policy-layer/*`) provides a unified interface for all policy-related operations. All POLICIES domain panels MUST route through this facade rather than directly to underlying endpoints.

### Facade Endpoints (Canonical)

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/policy-layer/state` | Policy state overview |
| `/api/v1/policy-layer/metrics` | Policy engine metrics |
| `/api/v1/policy-layer/versions` | Policy version history |
| `/api/v1/policy-layer/versions/current` | Current active version |
| `/api/v1/policy-layer/violations` | Policy violations list |
| `/api/v1/policy-layer/safety-rules` | Safety rules |
| `/api/v1/policy-layer/ethical-constraints` | Ethical constraints |
| `/api/v1/policy-layer/risk-ceilings` | Risk ceilings / budgets |
| `/api/v1/policy-layer/cooldowns` | Active cooldowns |
| `/api/v1/policy-layer/temporal-policies` | Temporal policies |
| `/api/v1/policy-layer/conflicts` | Policy conflicts |
| `/api/v1/policy-layer/dependencies` | Policy dependencies |

---

## Panel → Endpoint Mapping (POST-FIX)

### Subdomain: GOVERNANCE

#### Topic: ACTIVE (POL-GOV-ACT-*)

| Panel | Facade Endpoint | Status | Notes |
|-------|-----------------|--------|-------|
| POL-GOV-ACT-O1 | `/api/v1/policy-layer/state` | ✅ FIXED | Was: `/api/v1/policy-proposals` |
| POL-GOV-ACT-O2 | `/api/v1/policy-layer/metrics` | ✅ FIXED | Was: `/api/v1/policy-proposals/stats/summary` |
| POL-GOV-ACT-O3 | `/api/v1/policy-layer/state` | ✅ FIXED | Was: `/api/v1/policies/requests` (wrong path + bypassed facade) |
| POL-GOV-ACT-O4 | `/api/v1/policy-layer/state` | ✅ CORRECT | Already using facade |
| POL-GOV-ACT-O5 | `/api/v1/policy-layer/metrics` | ✅ CORRECT | Already using facade |

#### Topic: DRAFTS (POL-GOV-DFT-*)

| Panel | Facade Endpoint | Status | Notes |
|-------|-----------------|--------|-------|
| POL-GOV-DFT-O1 | `/api/v1/policy-layer/versions` | ✅ FIXED | Was: `/api/v1/policy-proposals` |
| POL-GOV-DFT-O2 | `/api/v1/policy-layer/versions` | ✅ CORRECT | Already using facade |
| POL-GOV-DFT-O3 | `/api/v1/policy-layer/versions/current` | ✅ CORRECT | Already using facade |
| POL-GOV-DFT-O4 | `/api/v1/policy-layer/conflicts` | ✅ CORRECT | Already using facade |
| POL-GOV-DFT-O5 | `/api/v1/policy-layer/dependencies` | ✅ CORRECT | Already using facade |

#### Topic: POLICY_LIBRARY (POL-GOV-LIB-*)

| Panel | Facade Endpoint | Status | Notes |
|-------|-----------------|--------|-------|
| POL-GOV-LIB-O1 | `/api/v1/policy-layer/safety-rules` | ✅ CORRECT | Already using facade |
| POL-GOV-LIB-O2 | `/api/v1/policy-layer/ethical-constraints` | ✅ CORRECT | Already using facade |
| POL-GOV-LIB-O3 | `/api/v1/policy-layer/state` | ✅ FIXED | Was: `/v1/policies/active` (bypassed facade) |
| POL-GOV-LIB-O4 | `/api/v1/policy-layer/safety-rules` | ✅ FIXED | Was: `/guard/policies` (bypassed facade) |
| POL-GOV-LIB-O5 | `/api/v1/policy-layer/temporal-policies` | ✅ CORRECT | Already using facade |

### Subdomain: LIMITS

#### Topic: THRESHOLDS (POL-LIM-THR-*)

| Panel | Facade Endpoint | Status | Notes |
|-------|-----------------|--------|-------|
| POL-LIM-THR-O1 | `/api/v1/policy-layer/risk-ceilings` | ✅ CORRECT | Already using facade |
| POL-LIM-THR-O2 | `/api/v1/policy-layer/risk-ceilings` | ✅ FIXED | Was: `/cost/budgets` (bypassed facade) |
| POL-LIM-THR-O3 | `/api/v1/policy-layer/risk-ceilings` | ✅ FIXED | Was: `/api/v1/tenants/tenant/quota/runs` (bypassed facade) |
| POL-LIM-THR-O4 | `/api/v1/policy-layer/simulate` | ✅ FIXED | Was: `/api/v1/tenants/tenant/quota/tokens` (bypassed facade) |
| POL-LIM-THR-O5 | `/api/v1/policy-layer/cooldowns` | ✅ CORRECT | Already using facade |

#### Topic: VIOLATIONS (POL-LIM-VIO-*)

| Panel | Facade Endpoint | Status | Notes |
|-------|-----------------|--------|-------|
| POL-LIM-VIO-O1 | `/api/v1/policy-layer/violations` | ✅ CORRECT | Already using facade |
| POL-LIM-VIO-O2 | `/api/v1/policy-layer/violations` | ✅ FIXED | Was: `/guard/costs/incidents` (bypassed facade) |
| POL-LIM-VIO-O3 | `/api/v1/policy-layer/violations` | ✅ FIXED | Was: `/costsim/v2/incidents` (bypassed facade) |
| POL-LIM-VIO-O4 | `/api/v1/policy-layer/violations` | ✅ FIXED | Was: `/cost/anomalies` (bypassed facade) |
| POL-LIM-VIO-O5 | `/api/v1/policy-layer/temporal-policies` | ✅ FIXED | Was: `/costsim/divergence` (bypassed facade) |

---

## Summary (POST-FIX)

| Category | Count | Details |
|----------|-------|---------|
| ✅ Correct (facade) | 12 | Already using unified policy-layer facade |
| ✅ FIXED | 13 | Redirected from direct endpoints to facade |
| ⚠️ Issues | 0 | All resolved |

**Total Panels:** 25
**Facade Coverage:** 25/25 (100%)
**Remaining Issues:** 0

---

## Fixes Applied (2026-01-17)

### Panels Redirected to Facade

| Panel | Old (Direct) | New (Facade) |
|-------|--------------|--------------|
| POL-GOV-ACT-O1 | `/api/v1/policy-proposals` | `/api/v1/policy-layer/state` |
| POL-GOV-ACT-O2 | `/api/v1/policy-proposals/stats/summary` | `/api/v1/policy-layer/metrics` |
| POL-GOV-ACT-O3 | `/api/v1/policies/requests` | `/api/v1/policy-layer/state` |
| POL-GOV-DFT-O1 | `/api/v1/policy-proposals` | `/api/v1/policy-layer/versions` |
| POL-GOV-LIB-O3 | `/v1/policies/active` | `/api/v1/policy-layer/state` |
| POL-GOV-LIB-O4 | `/guard/policies` | `/api/v1/policy-layer/safety-rules` |
| POL-LIM-THR-O2 | `/cost/budgets` | `/api/v1/policy-layer/risk-ceilings` |
| POL-LIM-THR-O3 | `/api/v1/tenants/tenant/quota/runs` | `/api/v1/policy-layer/risk-ceilings` |
| POL-LIM-THR-O4 | `/api/v1/tenants/tenant/quota/tokens` | `/api/v1/policy-layer/simulate` |
| POL-LIM-VIO-O2 | `/guard/costs/incidents` | `/api/v1/policy-layer/violations` |
| POL-LIM-VIO-O3 | `/costsim/v2/incidents` | `/api/v1/policy-layer/violations` |
| POL-LIM-VIO-O4 | `/cost/anomalies` | `/api/v1/policy-layer/violations` |
| POL-LIM-VIO-O5 | `/costsim/divergence` | `/api/v1/policy-layer/temporal-policies` |

### Intent YAML Files Updated

- `AURORA_L2_INTENT_POL-GOV-ACT-O1.yaml`
- `AURORA_L2_INTENT_POL-GOV-ACT-O2.yaml`
- `AURORA_L2_INTENT_POL-GOV-ACT-O3.yaml`
- `AURORA_L2_INTENT_POL-GOV-DFT-O1.yaml`
- `AURORA_L2_INTENT_POL-GOV-LIB-O3.yaml`
- `AURORA_L2_INTENT_POL-GOV-LIB-O4.yaml`
- `AURORA_L2_INTENT_POL-LIM-THR-O2.yaml`
- `AURORA_L2_INTENT_POL-LIM-THR-O3.yaml`
- `AURORA_L2_INTENT_POL-LIM-THR-O4.yaml`
- `AURORA_L2_INTENT_POL-LIM-VIO-O2.yaml`
- `AURORA_L2_INTENT_POL-LIM-VIO-O3.yaml`
- `AURORA_L2_INTENT_POL-LIM-VIO-O4.yaml`
- `AURORA_L2_INTENT_POL-LIM-VIO-O5.yaml`

---

## Remaining Actions

**None** - All 25 panels now use the unified policy-layer facade.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-17 | **COMPLETE** - Fixed remaining 3 panels (POL-GOV-ACT-O3, POL-LIM-THR-O3, POL-LIM-THR-O4) |
| 2026-01-17 | Facade coverage increased to 100% (25/25 panels) |
| 2026-01-17 | **FACADE UNIFORMITY FIX** - 13 panels redirected to policy-layer facade |
| 2026-01-17 | Updated intent YAMLs with `facade_note` tracking original endpoints |
| 2026-01-16 | Initial audit created |
