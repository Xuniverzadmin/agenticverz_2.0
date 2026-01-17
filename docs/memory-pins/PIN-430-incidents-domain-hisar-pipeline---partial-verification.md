# PIN-430: INCIDENTS Domain HISAR Pipeline - Partial Verification

**Status:** 🏗️ IN_PROGRESS
**Created:** 2026-01-15
**Category:** HISAR / Domain Verification

---

## Summary

Ran HISAR pipeline for Incidents domain. 5/15 capabilities OBSERVED, remainder need endpoint discovery or backend patches.

---

## Details

## Overview

Executed the HISAR pipeline for the INCIDENTS domain. Added 15 panels with capability assignments and ran SDSR verification. Partial success - 5 capabilities verified, 10 need backend work.

## Work Completed

### 1. Intent Ledger Updates

Updated 15 INC-* panels from `State: EMPTY` to `State: DRAFT` with capability assignments:

| Topic | Panels | Capabilities Assigned |
|-------|--------|----------------------|
| ACTIVE | INC-EV-ACT-O1 to O5 | list, summary, metrics, patterns, infra_summary |
| RESOLVED | INC-EV-RES-O1 to O5 | resolved_list, recovery_actions, recovery_candidates, graduation_list, replay_summary |
| HISTORICAL | INC-EV-HIST-O1 to O5 | historical_list, guard_list, v1_list, ops_list, integration_stats |

### 2. Capability Entries Added

Added 15 capability entries to the Capabilities section with:
- Panel binding
- Implementation block (assumed endpoint)
- Data mapping
- Acceptance criteria
- SDSR scenario reference

### 3. Sync and SDSR Execution

- Ran `sync_from_intent_ledger.py` - generated 19 intent YAMLs
- Ran SDSR for all 15 incident scenarios

## SDSR Results

### ✅ OBSERVED (5 capabilities)

| Capability | Endpoint | Panel |
|------------|----------|-------|
| `incidents.list` | `/api/v1/incidents` | INC-EV-ACT-O1 |
| `incidents.summary` | `/api/v1/incidents/summary` | INC-EV-ACT-O2 |
| `incidents.metrics` | `/api/v1/incidents/metrics` | INC-EV-ACT-O3 |
| `incidents.resolved_list` | `/api/v1/incidents` | INC-EV-RES-O1 |
| `incidents.historical_list` | `/api/v1/incidents` | INC-EV-HIST-O1 |

### ❌ FAILED - Invariant Violations (4 capabilities)

Endpoints exist but returned non-200 status:

| Capability | Endpoint | Issue |
|------------|----------|-------|
| `incidents.patterns` | `/api/v1/ops/incidents/patterns` | 2/3 invariants |
| `incidents.infra_summary` | `/api/v1/ops/incidents/infra-summary` | 2/3 invariants |
| `incidents.guard_list` | `/api/v1/guard/incidents` | 2/3 invariants |
| `incidents.ops_list` | `/api/v1/ops/incidents` | 2/3 invariants |

**Action Required:** Investigate why these ops-level endpoints fail. May need auth fixes or endpoint implementation.

### ⚠️ MISSING ENDPOINTS (6 capabilities)

Endpoints do not exist or return errors:

| Capability | Assumed Endpoint | Action |
|------------|------------------|--------|
| `incidents.recovery_actions` | `/api/v1/recovery/actions` | Create endpoint or discover correct path |
| `incidents.recovery_candidates` | `/api/v1/recovery/candidates` | Create endpoint or discover correct path |
| `incidents.graduation_list` | `/integration/graduation` | Create endpoint or discover correct path |
| `incidents.replay_summary` | `/replay/{incident_id}/summary` | Create endpoint or discover correct path |
| `incidents.v1_list` | `/v1/incidents` | Legacy endpoint - may need discovery |
| `incidents.integration_stats` | `/integration/stats` | Create endpoint or discover correct path |

**Action Required:** Either:
1. **Discover** the correct existing endpoints in the backend
2. **Patch** the backend to implement the required capabilities

## Pipeline Results

```
✓ Semantic validation passed
✓ Compiler succeeded
✓ Generated canonical projection: 87 panels, 9 BOUND
✓ Diff guard passed
✓ Deployed to frontend
```

## Next Steps

1. **Endpoint Discovery:** Search backend for existing endpoints that match the capability requirements
2. **Backend Gaps:** For capabilities without existing endpoints, create implementation tickets
3. **Auth Investigation:** Check if ops-level endpoints need different auth context
4. **Re-run SDSR:** After fixes, re-run SDSR to verify and promote to OBSERVED

## Key Files Modified

| File | Changes |
|------|---------|
| `design/l2_1/INTENT_LEDGER.md` | 15 panels + 15 capabilities |
| `design/l2_1/intents/*.yaml` | 15 new intent YAMLs |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml` | 15 capability files |

## Observations Written

Observations saved for all 15 scenarios at:
`backend/scripts/sdsr/observations/SDSR_OBSERVATION_incidents.*.json`


---

## Related PINs

- [PIN-429](PIN-429-.md)
- [PIN-427](PIN-427-.md)
