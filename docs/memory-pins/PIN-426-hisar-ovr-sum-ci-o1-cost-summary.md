# PIN-426: HISAR OVR-SUM-CI-O1 Cost Summary

**Status:** BLOCKED (Backend Gap)
**Created:** 2026-01-15
**Category:** UI Pipeline / HISAR Execution
**Milestone:** AURORA L2
**Related PINs:** PIN-422, PIN-425

---

## Summary

Executed HISAR pipeline for OVR-SUM-CI-O1 (Overview → Summary → Cost Intelligence → O1).
SDSR revealed a backend gap: `/cost/summary` endpoint returns 401 (AUTH_FAILURE).
Panel remains EMPTY until backend gap is resolved.

---

## Human Intent

**Panel:** OVR-SUM-CI-O1
**Name:** Cost Summary
**Purpose:** Provides a glanceable snapshot of cost metrics for the current period.

**What It Shows:**
- Total cost in cents
- Token usage (input/output)
- Request count
- Budget utilization percentage
- Days remaining at current spend rate

**What It Does NOT Show:**
- Per-feature breakdown
- Anomalies
- Historical trends

---

## HISAR Execution Log

| Phase | Status | Result |
|-------|--------|--------|
| 1. Intent Scaffold | DONE | Created `design/l2_1/intents/OVR-SUM-CI-O1.yaml` |
| 2. Registry Sync | DONE | APPROVED in registry |
| 3. Capability Scaffold | DONE | Created `overview.cost_summary` capability |
| 3.5 Coherency Gate | PASS | COH-001 to COH-010 all passed |
| 4. SDSR Verification | **FAIL** | AUTH_FAILURE (HTTP 401) |
| 5. Observation | BLOCKED | Cannot apply failed observation |
| 6-8. Compile/Bind/Render | BLOCKED | Waiting for SDSR pass |

---

## Backend Gap Report

### SDSR Observation

```
Scenario:    SDSR-OVR-SUM-CI-O1-001
Capability:  overview.cost_summary
Endpoint:    /cost/summary
Method:      GET

Status:      FAIL
HTTP Code:   401 (Unauthorized)
Taxonomy:    AUTH_FAILURE

Invariants:  0/5 passed
  INV-001 response_shape:        NOT EVALUATED (auth failed)
  INV-002 status_code:           FAIL (expected 200, got 401)
  INV-003 auth_works:            FAIL (401 is auth failure)
  INV-004 provenance_present:    NOT EVALUATED
  INV-005 aggregation_type:      NOT EVALUATED
```

### Root Cause

The `/cost/summary` endpoint requires:
1. Valid authentication token
2. `tenant_id` query parameter

SDSR runner attempted to call the endpoint but received 401 Unauthorized.

### Required Backend Fix

| Option | Description | Effort |
|--------|-------------|--------|
| A | Add SDSR service account with read-only access | Medium |
| B | Configure SDSR runner with test tenant credentials | Low |
| C | Add `/cost/summary` to public paths (if safe) | Low |

---

## Invariant Immutability Law

During this execution, the correct HISAR doctrine was reinforced:

> **SDSR's job is to REVEAL backend gaps, not work around them.**

### What Was NOT Done (Correctly)

| Forbidden Action | Why It Was Avoided |
|------------------|-------------------|
| Change invariants to skip auth check | Would hide the real gap |
| Mark endpoint as "legacy exception" | Creates two classes of truth |
| Force OBSERVED status | Violates trust model |

### What Was Done (Correctly)

| Required Action | What Happened |
|-----------------|---------------|
| Run SDSR with standard invariants | Yes - ran with HIL v1 invariants |
| Report failure as backend gap | Yes - documented AUTH_FAILURE |
| Stop execution at failure | Yes - did not proceed to Phase 5+ |
| Document gap for backend team | Yes - this PIN |

---

## Artifacts Created

| # | Artifact | Path | Status |
|---|----------|------|--------|
| 1 | Intent YAML | `design/l2_1/intents/OVR-SUM-CI-O1.yaml` | Created |
| 2 | Intent Registry | `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` | APPROVED |
| 3 | Capability YAML | `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_overview.cost_summary.yaml` | DECLARED |
| 4 | SDSR Scenario | `backend/scripts/sdsr/scenarios/SDSR-OVR-SUM-CI-O1-001.yaml` | Created |
| 5 | SDSR Observation | `backend/scripts/sdsr/observations/SDSR_OBSERVATION_overview.cost_summary.json` | FAIL |

---

## Panel State

| Field | Value |
|-------|-------|
| Panel ID | OVR-SUM-CI-O1 |
| State | EMPTY (unchanged) |
| Capability | overview.cost_summary |
| Capability Status | DECLARED (not OBSERVED) |
| Blocking Issue | AUTH_FAILURE |

---

## Documentation Updates

This session also updated HISAR governance documentation:

1. **PIN-422** - Added "Invariant Immutability Law" section
2. **run_hisar.sh** - Added invariant immutability rules to header

### The Law (Now Documented)

```
INVARIANT IMMUTABILITY LAW

Human Intent is the constraint.
Backend is the implementation.
SDSR is the verifier.

When SDSR fails:
  - The backend is wrong, not the invariant.
  - The gap is real, not a false positive.
  - The fix goes in backend, not SDSR.

Changing invariants to "make tests pass" is a governance violation.
```

---

## Next Steps

1. **Backend Team:** Resolve AUTH_FAILURE for `/cost/summary`
2. **Re-run SDSR:** `python3 aurora_sdsr_runner.py --panel OVR-SUM-CI-O1`
3. **If PASS:** Continue to Phase 5-8
4. **Expected Outcome:** Additional gaps likely (provenance_present may fail)

---

## References

- Intent: `design/l2_1/intents/OVR-SUM-CI-O1.yaml`
- Capability: `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_overview.cost_summary.yaml`
- SDSR Scenario: `backend/scripts/sdsr/scenarios/SDSR-OVR-SUM-CI-O1-001.yaml`
- Endpoint: `/cost/summary` (`backend/app/api/cost_intelligence.py`)
- PIN-422: HISAR Execution Doctrine (Invariant Immutability Law)
