# PIN-408: Aurora Projection Pipeline - PIN-407 Compliance Fix

**Status:** VERIFIED (Static) - PENDING RUNTIME VALIDATION
**Created:** 2026-01-12
**Updated:** 2026-01-12
**Category:** Architecture / SDSR / Aurora Pipeline
**Related:** PIN-407, PIN-406, PIN-405, PIN-403, PIN-370
**Proof Artifact:** `artifacts/proofs/SDSR_AURORA_ACCEPTANCE_VERIFIED.yaml`

---

## Summary

Full implementation of PIN-407 "Success as First-Class Data" semantic correction across:
1. **Backend Services** - Incident engine and policy service now create records for ALL runs
2. **SDSR Evidence Collection** - Updated to recognize SUCCESS incidents and NO_VIOLATION policies
3. **Aurora UI Projection** - Data model and serialization updated for outcome-based records
4. **Integrity Enforcement** - Now requires incident + policy records for SEALED status

Every SDSR run now produces a complete governance footprint with explicit outcome records.

---

## Backend Service Changes (Core Implementation)

### 1. incident_engine.py - SUCCESS Incident Creation

**New Method:** `create_incident_for_run()`

Creates an incident for ANY run, not just failures. This is the core PIN-407 fix.

```python
# PIN-407: Incident Outcome Model
INCIDENT_OUTCOME_SUCCESS = "SUCCESS"
INCIDENT_OUTCOME_FAILURE = "FAILURE"
INCIDENT_OUTCOME_BLOCKED = "BLOCKED"
INCIDENT_OUTCOME_ABORTED = "ABORTED"
SEVERITY_NONE = "NONE"  # New severity for success incidents

def create_incident_for_run(
    self,
    run_id: str,
    tenant_id: str,
    run_status: str,  # SUCCESS, FAILURE, BLOCKED, ABORTED
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    agent_id: Optional[str] = None,
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
) -> Optional[str]:
    """Create an incident for ANY run (PIN-407: Success as First-Class Data)."""
```

**Outcome Mapping:**

| Run Status | Incident Outcome | Severity | Category | Status |
|------------|------------------|----------|----------|--------|
| SUCCESS | SUCCESS | NONE | EXECUTION_SUCCESS | CLOSED |
| FAILURE | FAILURE | ERROR | EXECUTION_FAILURE | OPEN |
| BLOCKED | BLOCKED | WARNING | EXECUTION_BLOCKED | OPEN |
| ABORTED | ABORTED | INFO | EXECUTION_ABORTED | CLOSED |

### 2. policy_violation_service.py - NO_VIOLATION Policy Records

**New Functions:**
- `create_policy_evaluation_record()` - Creates policy record for any run
- `handle_policy_evaluation_for_run()` - Maps run status to policy outcome

```python
# PIN-407: Policy Outcome Model
POLICY_OUTCOME_NO_VIOLATION = "no_violation"
POLICY_OUTCOME_VIOLATION = "violation_incident"
POLICY_OUTCOME_ADVISORY = "advisory"
POLICY_OUTCOME_NOT_APPLICABLE = "not_applicable"

async def handle_policy_evaluation_for_run(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
    run_status: str,  # SUCCESS, FAILURE, BLOCKED, ABORTED
    ...
) -> str:
    """Create a policy evaluation record for ANY run (PIN-407)."""
```

**Outcome Mapping:**

| Run Status | Policy Outcome | Reason |
|------------|----------------|--------|
| SUCCESS | no_violation | Clean execution |
| FAILURE | violation_incident | Execution failure |
| BLOCKED | advisory | Policy intervened |
| ABORTED | not_applicable | Run aborted |

**Table Used:** `prevention_records` (existing table, no new tables created)

---

## SDSR Pipeline Changes

### 1. Scenario_SDSR_output.py - Data Model Update

**Class Renamed:** `ExplicitAbsenceEvidence` -> `ExplicitOutcomeEvidence`

**Old Model (INCORRECT):**
```python
@dataclass
class ExplicitAbsenceEvidence:
    incident_created_explicit: bool = False
    incident_created_value: Optional[bool] = None  # Expected: False
    policy_created_explicit: bool = False
    policy_created_value: Optional[bool] = None  # Expected: False
```

**New Model (PIN-407 COMPLIANT):**
```python
@dataclass
class ExplicitOutcomeEvidence:
    # Incident outcome (MANDATORY for all runs)
    incident_created: bool = False  # Must be True for all runs
    incident_outcome: Optional[str] = None  # SUCCESS, FAILURE, PARTIAL, BLOCKED

    # Policy outcome (MANDATORY for all runs)
    policy_evaluated: bool = False  # Must be True for all runs
    policy_outcome: Optional[str] = None  # NO_VIOLATION, VIOLATION, etc.

    # Capture validation
    capture_complete: bool = False
    capture_failures: List[str] = field(default_factory=list)
```

### 2. ACv2Evidence Class Update

**Field Renamed:** `explicit_absence` -> `explicit_outcome`

Backward compatibility property added for migration safety.

### 3. inject_synthetic.py - Evidence Collection Update

**AC-025 Evidence Collection:**

Old logic (line 1117-1150):
- Checked if incidents/policies were NOT created
- Expected `incident_created = false` for success

New logic:
- Checks if SUCCESS incident was created
- Expects `incident_created = true` with `outcome = SUCCESS`
- Expects `policy_evaluated = true` with `outcome = NO_VIOLATION`
- Tracks capture completeness

**AC-026 Integrity Computation:**

Old expected_events: `["response", "trace"]`

New expected_events (PIN-407): `["response", "trace", "incident", "policy"]`

### 4. SDSR_output_emit_AURORA_L2.py - Serialization Update

Updated serialization to emit new outcome-based fields:
```python
result["explicit_outcome"] = {
    "incident_created": explicit_outcome.incident_created,
    "incident_outcome": explicit_outcome.incident_outcome,
    "policy_evaluated": explicit_outcome.policy_evaluated,
    "policy_outcome": explicit_outcome.policy_outcome,
    "capture_complete": explicit_outcome.capture_complete,
    "capture_failures": explicit_outcome.capture_failures,
}
```

### 5. SDSR-E2E-006.yaml - Expectations Update

**Hard Failure Conditions:** Updated to expect SUCCESS incident creation

**AC-009:** Changed from `incident_created = false` to `incident_created = true, outcome = SUCCESS`

**AC-010:** Changed from `policy_created = false` to `policy_evaluated = true, outcome = NO_VIOLATION`

**AC-025:** Changed from "Absence assertions" to "Outcome assertions"

---

## Verification

### Static Verification (PASSED)

| Check | Status |
|-------|--------|
| incident_engine.py syntax | PASSED |
| policy_violation_service.py syntax | PASSED |
| Scenario_SDSR_output.py syntax | PASSED |
| inject_synthetic.py syntax | PASSED |
| SDSR_output_emit_AURORA_L2.py syntax | PASSED |
| SDSR-E2E-006.yaml validity | PASSED |

### Runtime Verification (PENDING)

| Check | Status |
|-------|--------|
| SDSR-E2E-006 scenario execution | PENDING |
| Aurora L2 observation file inspection | PENDING |
| UI displays SUCCESS incidents | PENDING |
| UI displays NO_VIOLATION policies | PENDING |

---

## Contract Compliance

### PIN-407 Requirements

| Requirement | Implementation |
|-------------|----------------|
| Every run produces Activity | Already captured (run is activity) |
| Every run produces Incident | `incident_created = true` with outcome |
| Every run produces Policy | `policy_evaluated = true` with outcome |
| Every run produces Logs | Captured in ObservabilityEvidence |
| Every run produces Traces | Captured in ObservabilityEvidence |
| Missing success records = capture failure | `capture_complete` and `capture_failures` fields |

### Integrity Check

Under PIN-407, integrity now validates:
1. Response received (execution completed)
2. Trace exists (observability)
3. SUCCESS incident created (governance footprint)
4. NO_VIOLATION policy evaluated (compliance record)

---

## Files Modified

### Backend Services (Core Implementation)

| File | Change |
|------|--------|
| `backend/app/services/incident_engine.py` | Added `create_incident_for_run()` method + outcome constants |
| `backend/app/services/policy_violation_service.py` | Added `handle_policy_evaluation_for_run()` + outcome constants |

### SDSR Pipeline

| File | Change |
|------|--------|
| `backend/scripts/sdsr/Scenario_SDSR_output.py` | Renamed ExplicitAbsenceEvidence -> ExplicitOutcomeEvidence |
| `backend/scripts/sdsr/inject_synthetic.py` | Updated AC-025 and AC-026 evidence collection |
| `backend/scripts/sdsr/SDSR_output_emit_AURORA_L2.py` | Updated serialization for new fields |
| `backend/scripts/sdsr/scenarios/SDSR-E2E-006.yaml` | Updated expectations and acceptance criteria |

### Proof Artifacts

| File | Purpose |
|------|---------|
| `artifacts/proofs/SDSR_AURORA_ACCEPTANCE_VERIFIED.yaml` | Static verification proof |

---

## Backward Compatibility

- `ExplicitAbsenceEvidence` alias preserved for migration
- `explicit_absence` property on `ACv2Evidence` delegates to `explicit_outcome`
- Serialization checks both old and new field names

---

## The Truth (No Sugar)

This fix ensures the Aurora UI projection pipeline correctly represents success as data, not silence.

> **Before:** Success runs produced empty incident/policy records (interpreted as "nothing happened")
> **After:** Success runs produce explicit SUCCESS incident and NO_VIOLATION policy records

The system is now **EVENT-COMPLETE**, not event-sparse.

---

## Next Steps

1. Runtime validation with SDSR-E2E-006 (requires running backend)
2. Verify Aurora L2 observation files contain correct outcome data
3. UI should display success records (not "no incidents")

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-12 | Initial creation - PIN-407 compliance fix |
| 2026-01-12 | Added backend service implementations (incident_engine.py, policy_violation_service.py) |
| 2026-01-12 | Created acceptance proof artifact |
| 2026-01-12 | All static verification checks passed |

