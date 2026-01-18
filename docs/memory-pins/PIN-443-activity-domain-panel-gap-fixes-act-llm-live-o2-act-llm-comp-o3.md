# PIN-443: Activity Domain Panel Gap Fixes (ACT-LLM-LIVE-O2, ACT-LLM-COMP-O3)

**Status:** ✅ COMPLETE
**Created:** 2026-01-18
**Category:** Activity Domain / Capability Wiring

---

## Summary

Wired two previously EMPTY Activity domain panels to their capabilities

---

## Details

## Summary

Fixed two Activity domain panels that were in EMPTY state (no capability binding):

### ACT-LLM-LIVE-O2: Live Runs Exceeding Time

- **Previous State:** EMPTY
- **New State:** DRAFT
- **Capability:** `activity.risk_signals`
- **Endpoint:** `/api/v1/activity/risk-signals`
- **Purpose:** Surface live runs exceeding expected execution time (AT_RISK, VIOLATED)

### ACT-LLM-COMP-O3: Failed Completed Runs

- **Previous State:** EMPTY  
- **New State:** DRAFT
- **Capability:** `activity.summary_by_status` (shared with COMP-O2, LIVE-O5)
- **Endpoint:** `/api/v1/activity/summary/by-status`
- **Purpose:** Shows failed run count from FAILED bucket in status breakdown

## Files Changed

| File | Change |
|------|--------|
| `design/l2_1/INTENT_LEDGER.md` | Updated panel definitions EMPTY→DRAFT |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_activity.risk_signals.yaml` | NEW - capability for LIVE-O2 |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_activity.summary_by_status.yaml` | Added ACT-LLM-COMP-O3 to source_panels |
| `design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-LIVE-O2.yaml` | NEW - generated intent |
| `design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-COMP-O3.yaml` | NEW - generated intent |
| `docs/architecture/activity/ACTIVITY_DOMAIN_CONTRACT.md` | Updated Section 7 panel binding table |

## Capability Status

- `activity.risk_signals`: DECLARED (needs SDSR validation for OBSERVED)
- `activity.summary_by_status`: OBSERVED (already validated via SDSR)

## Next Steps

1. Create SDSR scenario for `activity.risk_signals` to promote DECLARED→OBSERVED
2. Run SDSR validation for ACT-LLM-LIVE-O2

## References

- ACTIVITY_DOMAIN_CONTRACT.md Section 7
- Commit: 51d27375
---

## Updates

### Update (2026-01-18)

## 2026-01-18: SDSR Attribution Compliance Added

inject_synthetic.py now complies with migration 105 attribution constraints:

### Changes
- Added `SDSR_ORIGIN_SYSTEM_ID = 'sdsr-inject-synthetic'` (replaces legacy-migration)
- Added `SDSR_DEFAULT_ACTOR_TYPE = 'SYSTEM'` with logging when defaulting
- Added `validate_sdsr_attribution()` for early validation
- Scenario YAML now supports: `actor_type`, `actor_id`, `origin_system_id`
- Optional metadata fields: `authorization_*`, `project_id`, `source`

### Tightenings Implemented
1. **Visibility**: Logs when actor_type defaults to SYSTEM
2. **Namespace Reservation**: 'sdsr-' prefix reserved for SDSR

### Result
> Every run in the system — real or synthetic — obeys the same attribution law.

Commit: c155d138
