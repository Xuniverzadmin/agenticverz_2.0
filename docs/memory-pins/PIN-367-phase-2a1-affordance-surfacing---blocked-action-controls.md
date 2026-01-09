# PIN-367: Phase-2A.1 Affordance Surfacing - Blocked Action Controls

**Status:** ✅ COMPLETE
**Created:** 2026-01-09
**Category:** UI Pipeline / Phase-2A.1

---

## Summary

Added 14 blocked action controls to ui_projection_lock.json across all 4 domains. Controls are visible but disabled on read-only surfaces.

---

## Details

## Definition

Phase-2A.1 Affordance Surfacing adds **blocked action controls** to the UI projection so users can see what actions exist but understand why they're unavailable on read-only surfaces.

---

## Problem Statement

The STEP-3 negative scenarios reference action controls that should exist in the UI but were missing from ui_projection_lock.json:

| Domain | Missing Actions |
|--------|-----------------|
| Activity | STOP, RETRY, REPLAY_EXPORT |
| Incidents | MITIGATE, CLOSE, ESCALATE |
| Policies | TOGGLE, EDIT |
| Logs | ARCHIVE, DELETE |

Without these controls, users have no visibility into what actions are available when surfaces are upgraded.

---

## Solution

Add all action controls to the projection in **blocked state**:

```json
{
  "type": "STOP",
  "order": 4,
  "icon": "stop-circle",
  "category": "action",
  "enabled": false,
  "visibility": "ALWAYS",
  "disabled_reason": "Action unavailable on read-only surface L21-EVD-R"
}
```

---

## Artifacts Created

| Artifact | Path | Purpose |
|----------|------|---------|
| Affordance Spec | design/l2_1/step_3/phase_2a1_affordance_spec.yaml | Control definitions |
| Apply Script | scripts/ops/apply_phase2a1_affordances.py | Applies controls to projection |

---

## Controls Added (14 Total)

### Activity Domain (3 controls, 2 panels)

| Panel | Controls Added |
|-------|---------------|
| ACT-EX-AR-O2 (Active Runs List) | STOP, RETRY |
| ACT-EX-RD-O5 (Run Proof) | REPLAY_EXPORT |

### Incidents Domain (3 controls, 2 panels)

| Panel | Controls Added |
|-------|---------------|
| INC-AI-OI-O2 (Open Incidents List) | MITIGATE, CLOSE |
| INC-AI-ID-O3 (Incident Detail) | ESCALATE |

### Policies Domain (4 controls, 4 panels)

| Panel | Controls Added |
|-------|---------------|
| POL-AP-BP-O2 (Budget Policies List) | TOGGLE |
| POL-AP-RL-O2 (Rate Limits List) | TOGGLE |
| POL-AP-AR-O2 (Approval Rules List) | TOGGLE |
| POL-AP-BP-O3 (Budget Policy Detail) | EDIT |

### Logs Domain (4 controls, 3 panels)

| Panel | Controls Added |
|-------|---------------|
| LOG-ET-TD-O2 (Trace List) | ARCHIVE, DELETE |
| LOG-AL-SA-O2 (System Audit List) | ARCHIVE |
| LOG-AL-UA-O2 (User Audit List) | ARCHIVE |

---

## Projection Statistics

| Metric | Before | After |
|--------|--------|-------|
| Total Controls | 95 | 109 |
| Processing Stage | LOCKED | PHASE_2A1_APPLIED |

---

## Blocked State Properties

| Property | Value | Meaning |
|----------|-------|---------|
| enabled | false | Control visible but non-interactive |
| visibility | ALWAYS | Control appears even when blocked |
| disabled_reason | Surface-specific | Explains why unavailable |

---

## Graduation Path (Phase-3 Preview)

When surfaces upgrade from L21-EVD-R to L21-CTL-RW:

1. **Phase-3 Simulation**: Controls enter SIMULATED state
   - onClick logs intent but doesn't execute
   - Allows UX validation without backend changes

2. **Phase-4 Activation**: Controls become fully enabled
   - enabled: true
   - disabled_reason: removed
   - Backend handlers wired

---

## Validation

STEP-3 scenarios verified after Phase-2A.1 application:

| Type | Count | Status |
|------|-------|--------|
| Baseline | 4 | PASS |
| Negative | 4 | FAIL (SL-04) |

All scenarios continue to work correctly.

---

## Commands

```bash
# Apply affordances (modifies ui_projection_lock.json)
python3 scripts/ops/apply_phase2a1_affordances.py

# Preview changes without modifying
python3 scripts/ops/apply_phase2a1_affordances.py --dry-run

# JSON output
python3 scripts/ops/apply_phase2a1_affordances.py --json
```

---

## Invariants

1. **Controls never auto-enable** — graduation requires explicit surface upgrade
2. **disabled_reason is mandatory** — blocked controls must explain why
3. **visibility: ALWAYS** — users must see what's possible
4. **Scenarios unaffected** — Phase-2A.1 is additive, not mutating

---

## Related PINs

- [PIN-366](PIN-366-.md)
- [PIN-365](PIN-365-.md)
- [PIN-363](PIN-363-.md)
