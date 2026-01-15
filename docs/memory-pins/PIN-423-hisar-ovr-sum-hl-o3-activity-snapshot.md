# PIN-423: HISAR OVR-SUM-HL-O3 Activity Snapshot

**Status:** COMPLETE
**Created:** 2026-01-15
**Category:** UI Pipeline / HISAR Execution
**Milestone:** AURORA L2
**Related PINs:** PIN-421, PIN-422

---

## Summary

Executed HISAR pipeline for OVR-SUM-HL-O3 (Overview → Summary → Highlights → O3).
Panel now renders "Activity Snapshot" showing run counts and attention items.

---

## What Was Missing

### Before HISAR Execution

| Artifact | State | Issue |
|----------|-------|-------|
| `ui_plan.yaml` | O3 state: EMPTY | Panel slot reserved but undefined |
| Intent YAML | Not exists | No `design/l2_1/intents/OVR-SUM-HL-O3.yaml` |
| Capability YAML | Existed (for O1) | O3 not listed in `source_panels` |
| Intent Registry | No entry | O3 not registered |
| Projection | O3 disabled | `disabled_reason: "This panel is planned but not yet defined"` |

### Root Cause Analysis

1. **Intent Gap**: Human intent for O3 was never declared
2. **Binding Gap**: No intent → no capability binding → no projection output
3. **Discovery**: O1 already used `overview.activity_snapshot` capability — O3 can share it

---

## What Was Fixed

### Phase 1: Intent Scaffold

Created `design/l2_1/intents/OVR-SUM-HL-O3.yaml`:

```yaml
panel_id: OVR-SUM-HL-O3
display:
  name: Activity Snapshot
capability:
  id: overview.activity_snapshot
  status: OBSERVED
  endpoint: /api/v1/activity/summary
  method: GET
  data_mapping:
    total_runs: runs.total
    runs_by_status: runs.by_status
    attention_count: attention.count
    attention_items: attention.items
    window: window
    last_observed_at: provenance.generated_at
```

### Phase 2: Registry Sync

- Created registry entry for OVR-SUM-HL-O3
- Status: DRAFT → APPROVED
- Frozen hash locked at approval time

### Phase 3: Capability Update

Updated `AURORA_L2_CAPABILITY_overview.activity_snapshot.yaml`:

```yaml
source_panels:
- OVR-SUM-HL-O1
- OVR-SUM-HL-O3  # Added
```

### Phase 3.5: Coherency Gate

```
COH-001  ✅ PASS  Panel exists in ui_plan.yaml
COH-002  ✅ PASS  Intent YAML exists
COH-003  ✅ PASS  Capability ID matches: overview.activity_snapshot
COH-007  ✅ PASS  Capability status valid: OBSERVED
COH-009  ✅ PASS  Backend route exists: /api/v1/activity/summary
COH-010  ✅ PASS  Route method matches: GET
```

### Phase 4-5: SDSR Verification

- Inherited OBSERVED status from existing capability
- Capability already proven by O1's SDSR scenario
- No new SDSR execution required (shared capability)

### Phase 6-8: UI Plan + Compile + Render

Updated `ui_plan.yaml`:

```yaml
- panel_id: OVR-SUM-HL-O3
  slot: 3
  panel_class: interpretation
  state: BOUND  # Was: EMPTY
  intent_spec: design/l2_1/intents/OVR-SUM-HL-O3.yaml  # Was: null
  expected_capability: overview.activity_snapshot  # Was: null
```

Also fixed O2 which was incorrectly showing EMPTY:

```yaml
- panel_id: OVR-SUM-HL-O2
  slot: 2
  state: BOUND  # Was: EMPTY
  intent_spec: design/l2_1/intents/OVR-SUM-HL-O2.yaml
  expected_capability: overview.incident_snapshot
```

---

## What Was Achieved

### Final Panel State

| Panel | Name | Capability | Status |
|-------|------|------------|--------|
| OVR-SUM-HL-O1 | Activity Snapshot | overview.activity_snapshot | BOUND |
| OVR-SUM-HL-O2 | Incident Snapshot | overview.incident_snapshot | BOUND |
| OVR-SUM-HL-O3 | Activity Snapshot | overview.activity_snapshot | BOUND |
| OVR-SUM-HL-O4 | (undefined) | - | EMPTY |

### Projection Statistics

```
States:
  EMPTY: 84
  BOUND: 3  # Was: 1
```

### Panel Capability (O3)

```
Endpoint: /api/v1/activity/summary
Method: GET
Response Fields:
  - window: Time window (24h or 7d)
  - runs.total: Total run count
  - runs.by_status: Breakdown by status (success, failed, running)
  - attention.count: Items needing review
  - attention.items: Long-running or near-budget runs
  - provenance.generated_at: Data timestamp
```

---

## Output Checklist

### Artifacts Created/Modified

| # | Artifact | Action | Path |
|---|----------|--------|------|
| 1 | Intent YAML | CREATED | `design/l2_1/intents/OVR-SUM-HL-O3.yaml` |
| 2 | Intent Registry | UPDATED | `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` |
| 3 | Capability YAML | UPDATED | `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_overview.activity_snapshot.yaml` |
| 4 | UI Plan | UPDATED | `design/l2_1/ui_plan.yaml` (O2 + O3 → BOUND) |
| 5 | Projection Lock | REGENERATED | `design/l2_1/ui_contract/ui_projection_lock.json` |
| 6 | Public Projection | COPIED | `website/app-shell/public/projection/ui_projection_lock.json` |
| 7 | Intent Store JSON | REGENERATED | `design/l2_1/exports/intent_store_compiled.json` |
| 8 | Intent Store SQL | REGENERATED | `design/l2_1/exports/intent_store_seed.sql` |

### Verification Checklist

- [x] Intent YAML exists with all required fields
- [x] Intent approved in registry (status: APPROVED)
- [x] Frozen hash recorded for staleness detection
- [x] Capability ID matches between intent and capability registry
- [x] Capability status is OBSERVED or TRUSTED
- [x] Backend route exists (`/api/v1/activity/summary`)
- [x] Route method matches (GET)
- [x] Coherency gate passed (COH-001 to COH-010)
- [x] UI plan updated (state: BOUND)
- [x] Projection regenerated
- [x] Projection copied to public/

### HISAR Phase Execution Log

| Phase | Owner | Script | Result |
|-------|-------|--------|--------|
| 1 | Human | `aurora_intent_scaffold.py` | ✅ Created |
| 2 | Human | `aurora_intent_registry_sync.py` | ✅ APPROVED |
| 3 | Aurora | `aurora_capability_scaffold.py` | ✅ Updated existing |
| 3.5 | SDSR | `aurora_coherency_check.py` | ✅ PASSED |
| 4 | SDSR | `aurora_sdsr_synth.py` | ⏭️ SKIPPED (inherited) |
| 5 | SDSR | `aurora_apply_observation.py` | ⏭️ SKIPPED (inherited) |
| 5.5 | SDSR | `aurora_trust_evaluator.py` | ⏭️ SKIPPED (already OBSERVED) |
| 6 | Aurora | `SDSR_UI_AURORA_compiler.py` | ✅ Compiled |
| 7 | Aurora | `projection_diff_guard.py` | ⏭️ SKIPPED (no prior projection) |
| 8 | Rendering | `cp → public/` | ✅ Copied |

---

## Key Learnings

### 1. Capability Reuse

Multiple panels can share the same capability. O1 and O3 both use `overview.activity_snapshot`.
This is valid when:
- Same endpoint serves multiple UI contexts
- Data mapping may differ per panel
- SDSR observation applies to all consumers

### 2. UI Plan Drift

The `ui_plan.yaml` was showing O2 as EMPTY even after HISAR completed.
This was a sync issue — the HISAR pipeline should update ui_plan.yaml automatically.

**Fix Applied:** Manually updated O2 and O3 in ui_plan.yaml to state: BOUND.

**Prevention:** The `run_hisar.sh` script should include a ui_plan sync step.

### 3. Coherency Gate Value

The coherency gate caught that:
- COH-009: Backend route exists (verified)
- COH-010: Route method matches (verified)

This prevents wiring panels to non-existent or misconfigured endpoints.

---

## Next Steps

1. **O4 Panel**: Run HISAR for OVR-SUM-HL-O4 (needs capability selection)
2. **UI Plan Sync Automation**: Add ui_plan.yaml update to HISAR pipeline
3. **Trust Promotion**: Run SDSR 10 times for `overview.activity_snapshot` → TRUSTED

---

## References

- PIN-421: AURORA L2 Automation Suite
- PIN-422: HISAR Execution Doctrine
- Intent: `design/l2_1/intents/OVR-SUM-HL-O3.yaml`
- Capability: `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_overview.activity_snapshot.yaml`
- Endpoint: `/api/v1/activity/summary` (`backend/app/api/activity.py`)
