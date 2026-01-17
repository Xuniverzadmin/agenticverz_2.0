# PIN-431: Policies Domain HISAR and Analytics Domain Creation

**Status:** COMPLETE
**Created:** 2026-01-15
**Category:** HISAR / Schema Architecture

---

## Summary

Completed HISAR pipeline for Policies domain (20 panels, 9 BOUND) and created new ANALYTICS domain by splitting USAGE topic from LIMITS subdomain.

---

## Overview

This session extended the HISAR pipeline to the Policies domain and restructured the UI topology to add a new ANALYTICS domain.

## Topology Change: ANALYTICS Domain

### Problem
The USAGE topic under LIMITS subdomain was semantically about cost/usage analytics, not policy limits management. This created conceptual drift.

### Solution
Created a new ANALYTICS domain and moved USAGE topic there:

**Before:**
```
POLICIES → LIMITS → USAGE (5 panels)
```

**After:**
```
ANALYTICS → COST → USAGE (5 panels)
```

### Files Modified

1. **UI_TOPOLOGY_TEMPLATE.yaml**
   - Removed USAGE topic from LIMITS subdomain
   - Added new ANALYTICS domain with COST subdomain and USAGE/PROJECTIONS/BUDGETS topics

2. **INTENT_LEDGER.md**
   - Renamed POL-LIM-USG-O1 through O5 → ANA-CST-USG-O1 through O5
   - Updated Location blocks to ANALYTICS/COST/USAGE

3. **SDSR Scenarios**
   - Renamed SDSR-POL-LIM-USG-*.yaml → SDSR-ANA-CST-USG-*.yaml
   - Updated domain, panel_id, capability names in scenarios

4. **PDG Allowlist**
   - Created `backend/aurora_l2/tools/projection_diff_allowlist.json`
   - Allowlisted USG panel deletions (renamed to ANA)

## Policies Domain SDSR Verification

### Capabilities Verified

**PASSED (9 capabilities → BOUND):**

| Panel | Capability | Endpoint | Status |
|-------|------------|----------|--------|
| POL-GOV-ACT-O1 | policies.proposals_list | /api/v1/policy-proposals | OBSERVED |
| POL-GOV-ACT-O2 | policies.proposals_summary | /api/v1/policy-proposals/stats/summary | OBSERVED |
| POL-GOV-ACT-O3 | policies.requests_list | /api/v1/policies/requests | OBSERVED |
| POL-GOV-DFT-O1 | policies.drafts_list | /api/v1/policy-proposals | OBSERVED |
| POL-GOV-LIB-O3 | policies.active_policies | /v1/policies/active | OBSERVED |
| POL-GOV-LIB-O4 | policies.guard_policies | /guard/policies | OBSERVED |
| POL-LIM-VIO-O2 | policies.cost_incidents | /guard/costs/incidents | OBSERVED |
| POL-LIM-VIO-O3 | policies.simulated_incidents | /costsim/v2/incidents | OBSERVED |
| POL-LIM-VIO-O5 | policies.divergence_report | /costsim/divergence | OBSERVED |

**FAILED (11 capabilities - endpoints don't exist):**
- policies.layer_state (/policy-layer/state)
- policies.layer_metrics (/policy-layer/metrics)
- policies.versions_list (/policy-layer/versions)
- policies.current_version (/policy-layer/versions/current)
- policies.conflicts_list (/policy-layer/conflicts)
- policies.dependencies_list (/policy-layer/dependencies)
- policies.safety_rules (/policy-layer/safety-rules)
- policies.ethical_constraints (/policy-layer/ethical-constraints)
- policies.temporal_policies (/policy-layer/temporal-policies)
- policies.risk_ceilings (/policy-layer/risk-ceilings)
- policies.budgets_list (/cost/budgets)
- policies.cooldowns_list (/policy-layer/cooldowns)
- policies.violations_list (/policy-layer/violations)
- policies.anomalies_list (/cost/anomalies)

**BLOCKED (2 - coherency issues):**
- policies.quota_runs (endpoint format)
- policies.quota_tokens (endpoint format)

## Pipeline Results

```
Semantic validation passed (0 errors, 0 warnings)
Compiler succeeded
Generated canonical projection: 82 panels, 18 BOUND
Diff guard passed
Deployed to frontend
```

### Panel Summary

| Domain | Total Panels | BOUND | UNBOUND | EMPTY |
|--------|--------------|-------|---------|-------|
| POLICIES | 20 | 9 | 11 | 0 |
| ACTIVITY | 4 | 3 | 1 | 0 |
| INCIDENTS | 15 | 5 | 10 | 0 |
| OVERVIEW | 1 | 1 | 0 | 0 |
| LOGS | 15 | 0 | 4 | 11 |
| ACCOUNT | 9 | 0 | 0 | 9 |
| CONNECTIVITY | 8 | 0 | 0 | 8 |
| ANALYTICS | 5 | 0 | 0 | 5 |

## Key Artifacts

| Artifact | Location |
|----------|----------|
| UI Topology | `design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml` |
| Intent Ledger | `design/l2_1/INTENT_LEDGER.md` |
| PDG Allowlist | `backend/aurora_l2/tools/projection_diff_allowlist.json` |
| Semantic Registry | `design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml` (8 domains) |
| Compile Report | `design/l2_1/exports/AURORA_L2_COMPILE_REPORT.json` |

## Backend Gaps Identified

The failed SDSR verifications reveal backend endpoints that need implementation:

1. **Policy Layer endpoints** (/policy-layer/*) - 9 endpoints
2. **Cost endpoints** (/cost/*) - 2 endpoints
3. **Quota endpoints** - need format correction

These represent backend work required to enable full Policies domain capabilities.

## Lessons Learned

1. **Domain restructuring**: When splitting domains, update topology first, then rename panels and scenarios
2. **PDG Allowlist**: Panel renames require PDG allowlist entries for deletions
3. **Observation persistence**: Sync resets capability status - re-apply observations after sync
4. **Domain scope**: ANALYTICS domain captures cost/usage analytics distinct from governance policies

---

## Related PINs

- [PIN-429](PIN-429-hisar-schema-split-and-activity-domain-sdsr-verification.md) - Schema Split and Activity Domain
- [PIN-430](PIN-430-incidents-domain-hisar-partial-verification.md) - Incidents Domain HISAR

