# PIN-415: Frontend Simulation Removal - RealControl Migration

**Status:** ✅ COMPLETE
**Created:** 2026-01-14
**Category:** Frontend / Architecture

---

## Summary

Surgically removed all frontend simulation components (SimulationContext, SimulatedControl, SimulationLog) and replaced with projection-driven RealControl component. AURORA pipeline and RETRY functionality preserved.

---

## Details

## Context

The frontend had a simulation layer that provided fake action acknowledgements for controls.
This was creating confusion about what was real vs simulated. Per AURORA L2.1 principles,
the UI should be "brutally honest" - if a control is clickable, it must call real backend.

## What Was Removed

### Files Deleted:
- `src/components/simulation/SimulatedControl.tsx`
- `src/components/simulation/SimulationLog.tsx`
- `src/components/simulation/ConfirmationModal.tsx`
- `src/components/simulation/index.ts`
- `src/contexts/SimulationContext.tsx`

### Files Modified:
- `App.tsx` - Removed SimulationProvider wrapper and SimulationLog
- `DomainPage.tsx` - Replaced SimulatedControl with RealControl
- `PanelView.tsx` - Replaced SimulatedControl with RealControl

## What Was Created

### `src/components/controls/RealControl.tsx`
Projection-driven control component with rules:
- If `control.enabled === false` → Disabled, no click handler
- If `control.enabled === true` → Click calls real backend
- No simulation, no preview, no fake acknowledgement
- RETRY action calls `retryRun()` from `api/worker.ts`

### `src/components/controls/index.ts`
Export barrel for controls module.

## Acceptance Verification

| Check | Result |
|-------|--------|
| SimulationContext refs | 0 hits |
| SimulatedControl refs | 0 hits |
| SimulationLog refs | 0 hits |
| ui_projection_loader.ts | Unchanged |
| AURORA L2.1 files | Unchanged |
| RETRY calls real backend | ✅ |
| Disabled controls via projection | ✅ |
| No frontend inference | ✅ |

## Key Principles Preserved

1. **Projection Authority**: Control enabled state comes from AURORA projection only
2. **No Frontend Inference**: UI does not decide what should be enabled
3. **Real Backend Calls**: Enabled action controls execute real API calls
4. **Binding Status Gate**: Controls disabled when binding_status \!== BOUND

## Related Work

- AURORA L2.1 UI Projection Pipeline
- Capability Status Model (DISCOVERED → DECLARED → OBSERVED → TRUSTED)
- SDSR system for capability verification

## Future Updates

Track any follow-up work related to:
- Additional action control implementations (beyond RETRY)
- Control binding status changes
- Projection-driven UI enhancements
---

## Updates

### Update (2026-01-14)

## 2026-01-14: Hostile Audit Completed

### Audit Scope
8 attack vectors probed for any residual simulation, inference, or truth fabrication.

### Vectors Tested
| Vector | Target | Verdict |
|--------|--------|---------|
| V1 | Projection Authority Leakage | ✅ PASS |
| V2 | Control Enablement Drift | ✅ PASS |
| V3 | Backend Failure Masking | ✅ PASS |
| V4 | Residual Simulation Semantics | ✅ PASS |
| V5 | Projection Loader Side Inference | ✅ PASS |
| V6 | UI/API Capability Mismatch | ✅ PASS (Correct Failure Mode) |
| V7 | Temporal Inference (Race Conditions) | ✅ PASS |
| V8 | Developer Convenience Regressions | ✅ PASS |

### Watchpoint Identified
⚠️ No runtime assertion that "if control.enabled === true, backend handler must exist."
Currently enforced by process (AURORA + SDSR), not code.
**Status:** Acceptable by design. Optional dev-only assertion deferred.

### Final Verdict
**UI reflects compiled truth and nothing else.**
Frontend cannot fabricate truth. No simulation residue remains.
