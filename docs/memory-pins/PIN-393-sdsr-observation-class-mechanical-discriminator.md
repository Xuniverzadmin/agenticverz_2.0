# PIN-393: SDSR Observation Class Mechanical Discriminator

**Status:** ✅ COMPLETE
**Created:** 2026-01-11
**Category:** SDSR / Architecture

---

## Summary

Implemented observation_class mechanical discriminator to distinguish INFRASTRUCTURE vs EFFECT scenarios, enabling Aurora to correctly handle empty capabilities_observed

---

## Details

## Problem

SDSR-E2E-005 (infrastructure scenario) produced `capabilities_observed: []` and Aurora applier rejected it as invalid, blocking the pipeline.

The root cause: nothing in code stated whether empty capabilities was valid. Claude and downstream systems had to **infer** intent from prose.

## Solution: observation_class Mechanical Discriminator

Added `observation_class: Literal['INFRASTRUCTURE', 'EFFECT']` to `ScenarioSDSROutput`.

### Classification Rule (Mechanical)
```python
if observed_effects:
    observation_class = 'EFFECT'
else:
    observation_class = 'INFRASTRUCTURE'
```

No YAML flags. No Aurora knowledge. Pure truth.

## Files Modified

### 1. Scenario_SDSR_output.py (Truth Source)
- Added `observation_class` field
- Added `observed_effects` field
- Added `CAPABILITY_ACCEPTANCE_CRITERIA` mapping
- Added `infer_capabilities_from_effects()` function
- Added architectural invariant docstring

### 2. inject_synthetic.py (Effect Observer)
- Now queries actual state transitions from database
- Passes `observed_effects` to builder (not capabilities from YAML)
- Builder infers capabilities using acceptance criteria

### 3. SDSR_output_emit_AURORA_L2.py (Serializer)
- Serializes `observation_class` and `observed_effects`
- Updated validation to require `observation_class`

### 4. AURORA_L2_apply_sdsr_observations.py (Consumer)
- Gates on `observation_class`
- INFRASTRUCTURE: returns success with no capability updates
- EFFECT: requires non-empty capabilities

### 5. SDSR_PIPELINE_CONTRACT.md (Governance)
- Added Section 15: Observation Classification
- Added Section 16: Four Locked Invariants
- Added Section 17: Capability Inference
- Added Section 18: Updated JSON Schema

## Four Locked Invariants (Constitutional)

| ID | Invariant |
|----|-----------|
| INV-SDSR-001 | SDSR_output is the sole authority for naming observed capabilities |
| INV-SDSR-002 | SDSR never updates capability registry or belief state |
| INV-SDSR-003 | Aurora never infers capabilities — it only applies belief transitions |
| INV-SDSR-004 | Empty capabilities_observed is valid for INFRASTRUCTURE observations |

## Observation JSON Schema (Updated)

```json
{
  "scenario_id": "SDSR-E2E-005",
  "status": "PASSED",
  "observation_class": "INFRASTRUCTURE",
  "observed_at": "2026-01-11T14:20:52Z",
  "observed_effects": [],
  "capabilities_observed": [],
  "metadata": { ... }
}
```

## Acceptance Criteria Mapping

```python
CAPABILITY_ACCEPTANCE_CRITERIA = {
    ("policy_proposal", "status", "PENDING", "APPROVED"): "APPROVE",
    ("policy_proposal", "status", "PENDING", "REJECTED"): "REJECT",
}
```

## Layer Separation (Final)

| Layer | Responsibility |
|-------|----------------|
| SDSR | What happened (observe effects) |
| SDSR_output | What behavior was proven (name capabilities) |
| Aurora | What beliefs to update (registry transitions) |
| UI | Reflect beliefs |

## Testing

Re-run SDSR-E2E-005 to verify:
1. `observation_class: INFRASTRUCTURE` in observation JSON
2. Aurora applier accepts empty capabilities
3. Pipeline completes successfully

---

## Related PINs

- [PIN-391](PIN-391-.md)
- [PIN-392](PIN-392-.md)
- [PIN-370](PIN-370-.md)
- [PIN-379](PIN-379-.md)
