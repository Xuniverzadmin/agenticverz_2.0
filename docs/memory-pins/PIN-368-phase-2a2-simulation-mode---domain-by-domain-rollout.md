# PIN-368: Phase-2A.2 Simulation Mode - Domain-by-Domain Rollout

**Status:** 🏗️ IN_PROGRESS
**Created:** 2026-01-09
**Category:** UI Pipeline / Phase-2A.2

---

## Summary

Simulation mode for blocked action controls. Controls respond to clicks but don't mutate state. Rolling out domain-by-domain: Activity → Incidents → Policies → Logs.

---

## Details

## Definition

Phase-2A.2 moves controls from **BLOCKED** to **SIMULATED** state.

- **BLOCKED**: Control visible but disabled
- **SIMULATED**: Control enabled, responds to clicks, but NO backend mutation

---

## Purpose

Answer these questions through UX validation:

1. "If I *could* act, would this UI make sense?"
2. "Does the feedback explain what would happen?"
3. "Is the authority boundary clear?"

---

## Domain Rollout Order

| Order | Domain | Status | Controls |
|-------|--------|--------|----------|
| 1 | Activity | **🔒 FROZEN** | RETRY, STOP, REPLAY_EXPORT |
| 2 | Incidents | **🏗️ IMPLEMENTED** | MITIGATE, CLOSE, ESCALATE |
| 3 | Policies | PENDING | TOGGLE, EDIT |
| 4 | Logs | PENDING | ARCHIVE, DELETE |

> **ACTIVITY Phase-2A.2 simulation complete and frozen.**
> No further affordances to be added without cross-domain review.

---

## Simulation Rules (Non-Negotiable)

| Rule | Enforcement |
|------|-------------|
| No backend API calls | BLOCKING |
| No state mutation | BLOCKING |
| No DB writes | BLOCKING |
| Immediate UI feedback | REQUIRED |
| Self-explanatory action | REQUIRED |

---

## Required Feedback Pattern

Every simulated action MUST show:

```
Toast: "{Action} requested (simulation only)"
Inline: "No actual change occurred. This is a preview."
```

---

## ACTIVITY Domain Scenarios (Ready)

| ID | Name | Control | Purpose |
|----|------|---------|---------|
| ACT-SIM-001 | Retry completed run | RETRY | Can I rerun a failed/completed run? |
| ACT-SIM-002 | Stop running run | STOP | Do I have control over something running? |
| ACT-SIM-003 | Replay evidence | REPLAY_EXPORT | What actually happened inside this run? |

---

## Freeze Criteria Per Domain

- All simulation scenarios work
- No new controls requested
- No confusion about state
- No verbal explanation needed

---

## What This Is NOT

- NOT wiring backend
- NOT adding real execution
- NOT connecting to DB
- NOT Phase-3

---

## Artifacts

| Artifact | Path |
|----------|------|
| Simulation Spec | design/l2_1/step_3/phase_2a2_simulation_spec.yaml |
| SimulationContext | website/app-shell/src/contexts/SimulationContext.tsx |
| SimulatedControl | website/app-shell/src/components/simulation/SimulatedControl.tsx |
| ConfirmationModal | website/app-shell/src/components/simulation/ConfirmationModal.tsx |
| SimulationLog | website/app-shell/src/components/simulation/SimulationLog.tsx |

---

## Next Steps

1. ~~Implement ACTIVITY simulation (3 scenarios)~~ **DONE**
2. Manual UX walkthrough (verify ACT-SIM-001, 002, 003)
3. Freeze ACTIVITY
4. Proceed to INCIDENTS domain simulation

---


---

## Updates

### Update (2026-01-09)

## 2026-01-09: ACTIVITY Domain Simulation Implemented

### Files Created

| File | Purpose |
|------|---------|
| src/contexts/SimulationContext.tsx | Simulation state management and action handling |
| src/components/simulation/SimulatedControl.tsx | Interactive control with simulation feedback |
| src/components/simulation/ConfirmationModal.tsx | Confirmation dialog for destructive actions |
| src/components/simulation/SimulationLog.tsx | Debug panel showing action log |
| src/components/simulation/index.ts | Component exports |

### Features Implemented

1. **SimulationContext** - Global state for simulation mode
   - Modes: BLOCKED, SIMULATED, LIVE
   - Action log tracking
   - Per-control message templates

2. **SimulatedControl** - Interactive control component
   - Shows SIMULATED badge on action controls
   - Inline message after click
   - Toast notification
   - Confirmation modal for destructive actions

3. **SimulationLog** - Debug panel (bottom-left)
   - Expandable action log
   - Shows all simulated actions
   - Timestamps and results

4. **PanelView Integration**
   - All controls now use SimulatedControl
   - SIMULATION badge in controls header
   - Action count indicator

### Activity Domain Controls

| Control | Behavior | Message |
|---------|----------|---------|
| RETRY | Toast + inline | No execution was triggered. This is a preview. |
| STOP | Confirm modal + toast | Execution continues. No stop signal sent. |
| REPLAY_EXPORT | Toast + inline | No file was created. This is a preview. |

### Build Status: SUCCESS

### Next: Manual UX Walkthrough

Test checklist:
- Navigate to Activity panel
- Click RETRY on a run
- Click STOP on a running run (confirm modal appears)
- Click REPLAY_EXPORT
- Verify toasts appear
- Verify inline messages appear
- Verify SimulationLog captures actions

## 2026-01-09: Pipeline Hardening & UX Fixes

### Issues Fixed

1. **Projection Stage Validation** - Loader rejected `PHASE_2A1_APPLIED` stage
   - Updated `ui_projection_loader.ts` to accept Phase-2A stages
   - Added `projection-stage-check.cjs` to prebuild pipeline

2. **Controls Not Visible in DomainPage** - `FullPanelSurface` didn't render controls
   - Added `SimulatedControl` rendering to `DomainPage.tsx`
   - Added `simulation-render-check.cjs` to enforce both render paths

3. **SimulationLog Copy Button** - Added copy functionality for log export

### Pipeline Checks Added

| Check | Purpose |
|-------|---------|
| `projection-stage-check.cjs` | Validates projection stage + design sync |
| `simulation-render-check.cjs` | Ensures SimulatedControl in all render paths |

### Commands Added

```bash
npm run projection      # Check projection stage
npm run projection:sync # Sync from design file
npm run simulation      # Check simulation rendering
```

### Prebuild Pipeline (Mandatory)

```
ui-hygiene-check → import-boundary-check → projection-stage-check → simulation-render-check → build
```

### UX Walkthrough Status

| Scenario | Status |
|----------|--------|
| ACT-SIM-001 (RETRY) | VERIFIED |
| ACT-SIM-002 (STOP) | VERIFIED |
| ACT-SIM-003 (REPLAY_EXPORT) | VERIFIED |
| SimulationLog | VERIFIED (with copy) |

### ACTIVITY Domain: FROZEN

---

## 2026-01-09: INCIDENTS Domain Simulation Implemented

### Changes Made

1. **SimulationContext** - Updated INCIDENTS messages (careful tone)
   - MITIGATE: "Mitigation request recorded (simulation only)"
   - CLOSE: "Incident closure acknowledged (simulation only)"
   - ESCALATE: "Escalation recorded (simulation only)"

2. **SimulatedControl** - Added modal configurations per control type
   - Domain-appropriate wording for incidents
   - All 3 controls require confirmation modal

3. **Confirmation Required** - MITIGATE, CLOSE, ESCALATE added

### INCIDENTS Domain Controls

| Control | Panel | Confirmation | Message |
|---------|-------|--------------|---------|
| MITIGATE | Open Incidents List | YES | No mitigation action was executed. Incident state unchanged. |
| CLOSE | Open Incidents List | YES | Incident remains visible for audit purposes. |
| ESCALATE | Incident Detail | YES | No ownership transfer occurred. Escalation path shown for reference. |

### UX Walkthrough Checklist

Navigate to: `https://preflight-console.agenticverz.com/precus/incidents`

| ID | Scenario | Verify |
|----|----------|--------|
| INC-SIM-001 | Click MITIGATE on Open Incidents | Modal appears, toast + inline after confirm |
| INC-SIM-002 | Click CLOSE on any incident | Modal appears, toast + inline after confirm |
| INC-SIM-003 | Click ESCALATE on Incident Detail | Modal appears, toast + inline after confirm |

### Severity Perception Check

- [ ] Does severity still feel "serious" after clicking actions?
- [ ] Do actions feel acknowledged but constrained?
- [ ] Is it obvious incidents are not "closed away"?
- [ ] Does escalation feel procedural, not magical?

---

## Related PINs

- [PIN-367](PIN-367-.md)
- [PIN-366](PIN-366-.md)
- [PIN-365](PIN-365-.md)
