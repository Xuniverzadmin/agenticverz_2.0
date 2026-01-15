# PIN-428: ANALYTICS Domain Promoted to OBSERVED via SDSR

**Status:** ✅ COMPLETE
**Created:** 2026-01-15
**Category:** AURORA L2 / Capability Observation

---

## Summary

All 5 ANALYTICS capabilities promoted from DECLARED to OBSERVED via SDSR pipeline. Domain is now fully observable with provenance-verified interpretation panels.

---

## Details

## Overview

The ANALYTICS domain has been fully promoted to OBSERVED status through the SDSR (Synthetic Data Scenario Runner) pipeline. This makes the domain observable in the HISAR projection.

## Capabilities Promoted

| Capability | Endpoint | Panel ID | Status |
|------------|----------|----------|--------|
| analytics.tenant_usage | `/api/v1/tenant/usage` | ANL-USG-SUM-O1 | OBSERVED |
| analytics.cost_summary | `/cost/dashboard` | ANL-CST-SUM-O1 | OBSERVED |
| analytics.cost_by_actor | `/cost/by-user` | ANL-CST-ACT-O1 | OBSERVED |
| analytics.cost_by_model | `/cost/by-model` | ANL-CST-MOD-O1 | OBSERVED |
| analytics.anomaly_detection | `/cost/anomalies` | ANL-CST-ANM-O1 | OBSERVED |

## Invariants Verified (5/5 per capability)

1. Endpoint exists and responds with HTTP 200
2. Response includes provenance envelope
3. Provenance has required fields: sources, window, aggregation, generated_at
4. Data aggregation matches capability contract
5. Coherency gate passes (UI Intent → Capability → Backend route)

## Artifacts Created

### Capability YAMLs
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.tenant_usage.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.cost_summary.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.cost_by_actor.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.cost_by_model.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.anomaly_detection.yaml`

### SDSR Scenarios
- `backend/scripts/sdsr/scenarios/SDSR_ANL_USG_SUM_O1.yaml`
- `backend/scripts/sdsr/scenarios/SDSR_ANL_CST_SUM_O1.yaml`
- `backend/scripts/sdsr/scenarios/SDSR_ANL_CST_ACT_O1.yaml`
- `backend/scripts/sdsr/scenarios/SDSR_ANL_CST_MOD_O1.yaml`
- `backend/scripts/sdsr/scenarios/SDSR_ANL_CST_ANM_O1.yaml`

## Bug Fixes During Implementation

### Routes Cache Prefix Bug (COH-009)
- **Issue**: Coherency gate failing with "Backend route not found"
- **Root Cause**: `aurora_coherency_check.py` had wrong prefix for `tenants.py`
- **Fix**: Changed `known_prefixes` from `/api/v1/tenants` to `/api/v1`
- **Location**: `backend/aurora_l2/tools/aurora_coherency_check.py:164`

## Provenance Envelope Structure

All ANALYTICS endpoints return responses with provenance:

```json
{
  "data": { ... },
  "provenance": {
    "sources": ["cost_records", "runs"],
    "window": { "start": "...", "end": "..." },
    "aggregation": "SUM" | "GROUP_BY:model" | "GROUP_BY:user",
    "generated_at": "2026-01-15T12:00:00Z"
  }
}
```

## Capability Status FSM

```
DECLARED → OBSERVED → TRUSTED
   ↓          ↓          ↓
 claim    demonstrated  stable
```

All ANALYTICS capabilities are now at OBSERVED (demonstrated via SDSR).

## Next Steps

- Run full HISAR pipeline (not dry-run) to regenerate projection with ANALYTICS domain
- Consider promoting to TRUSTED after stability period

## Related Work

- HISAR Phase 0 Snapshot Gate added (prevents 0-byte snapshot thrash)
- CI guard for OpenAPI snapshot validation
