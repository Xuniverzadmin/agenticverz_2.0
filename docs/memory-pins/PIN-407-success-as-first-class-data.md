# PIN-407: Success as First-Class Data

**Status:** FOUNDATIONAL CORRECTION
**Created:** 2026-01-12
**Category:** Governance / Semantic Model / Layer 0
**Supersedes:** Previous "absence assertions" model

---

## Summary

This PIN documents a fundamental semantic correction to the execution capture model. The system is **EVENT-COMPLETE**, not event-sparse. Every run produces activity, incident, policy, and logs - regardless of outcome.

---

## The Core Correction

### Previous Model (INCORRECT)

> "Activity only when something external happens"
> "Incident/policy only on failure"

This framing was **wrong for our governance model**.

### Corrected Model (AUTHORITATIVE)

> **Every run produces a complete governance footprint.**
> **Success is data, not silence.**

A run is not "something that might produce activity/incident/policy".

A run **IS** a first-class activity that ALWAYS produces:
- Activity record
- Incident outcome
- Policy outcome
- Logs
- Traces

**What varies:** Classification and content
**What does NOT vary:** Existence

---

## Execution Capture Contract (v1.1)

### 1. Activity

- A run **is** an activity
- Activity MUST be recorded for ALL runs
- Activity types:
  - `EXECUTION_SUCCESS`
  - `EXECUTION_FAILURE`
  - `EXECUTION_BLOCKED`
  - `EXECUTION_ABORTED`

### 2. Incident

- Every run produces an **incident record**
- Incident outcome MUST be explicit:
  - `SUCCESS` - No harm, no violation (THIS IS EVIDENCE, not absence)
  - `FAILURE` - Something went wrong
  - `PARTIAL` - Partial completion
  - `BLOCKED` - Blocked by policy or auth

**A "success incident" is still an incident.**
It asserts NO harm, NO violation.
It is evidence, not absence.

### 3. Policy

- Every run produces a **policy evaluation result**
- Policy outcome MUST be explicit:
  - `NO_VIOLATION` - Run complied with all policies
  - `VIOLATION` - Run violated one or more policies
  - `ADVISORY` - Advisory only, no enforcement
  - `NOT_APPLICABLE` - No policies applied

On success runs, policy data MAY be stored as:
- Affirmation ("this run complied")
- Optional policy draft candidate for future runs

### 4. Logs

- Entry log
- Exit log
- Correlated by `run_id`
- **Non-optional**

### 5. Traces

- Trace created for every run
- Trace steps recorded
- Trace finalized as:
  - `COMPLETE` (successful finalization)
  - `ABORTED` (finalization failed - PIN-406)

---

## Orthogonality Rule (Still Valid, Clarified)

> Evidence **content** varies by run type.
> Evidence **existence** does not.

### Example: Pure Transform (json_transform)

| Evidence Type | Exists? | Content |
|--------------|---------|---------|
| Activity | YES | Execution occurred |
| Incident | YES | Outcome = SUCCESS |
| Policy | YES | Outcome = NO_VIOLATION / ADVISORY |
| External activity_evidence | NO | No external effects |
| Provider evidence | NO | No LLM provider called |
| Logs | YES | Entry + exit |
| Traces | YES | COMPLETE |

---

## Why This Matters

If you DON'T capture success as data:

1. **"Success" becomes indistinguishable from "nothing happened"**
2. **Cannot learn from success patterns**
3. **Cannot derive preventive policies**
4. **Cannot show regulators WHY something was safe**
5. **SDSR loses half its value**

> **Nothing happening is not a result.**
> **Something happening safely IS a result.**

---

## Impact on SDSR-E2E-006

Under the corrected contract, SDSR-E2E-006 (baseline success scenario) **should** produce:

| Category | Expected |
|----------|----------|
| Activity | Run activity record |
| Incident | Incident with outcome = SUCCESS |
| Policy | Policy evaluation = NO_VIOLATION |
| Logs | Entry + exit |
| Traces | Trace + steps (COMPLETE) |
| Integrity | Sealable once capture complete |

### Previous Expectations (INCORRECT)

```yaml
explicit_absence:
  incident_created: false     # WRONG
  policy_created: false       # WRONG
```

### Corrected Expectations (PIN-407)

```yaml
explicit_outcome:
  incident_created: true
  incident_outcome: SUCCESS
  policy_evaluated: true
  policy_outcome: NO_VIOLATION
  policy_proposal_created: false  # No proposal needed (no violation)
```

---

## Implementation Requirements

### Immediate TODO

1. **Update backend engines:**
   - Incident Engine: Create SUCCESS incidents for successful runs
   - Policy Engine: Create NO_VIOLATION records for compliant runs

2. **Ensure integrity treats:**
   - Missing success-records as **capture failure**
   - Not as "nothing to capture"

3. **UI classification:**
   - Remains **out of scope** for this PIN
   - UI observes backend truth

---

## Files Updated

| File | Change |
|------|--------|
| `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml` | Added `execution_capture_contract` v1.1 section |
| `docs/memory-pins/PIN-403-aos-execution-integrity-contract.md` | Added Execution Capture Contract section |
| `docs/memory-pins/PIN-405-evidence-architecture-v11---structural-authority-integrity-model.md` | Added Complete Governance Footprint section |
| `docs/memory-pins/PIN-370-sdsr-scenario-driven-system-realization.md` | Updated Cross-Domain Propagation Contract |
| `backend/scripts/sdsr/scenarios/SDSR-E2E-006.yaml` | Changed from absence assertions to outcome assertions |

---

## The Truth (No Sugar)

This was a **foundational semantic bug**.

> **Success is not nothing.**
> **Success is something that happened safely.**

Lock this now, and the system becomes **learning-capable**, not just **failure-detecting**.

---

## Related Documents

| Document | Location |
|----------|----------|
| AOS Execution Integrity Contract | `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml` |
| PIN-403 | `docs/memory-pins/PIN-403-aos-execution-integrity-contract.md` |
| PIN-405 | `docs/memory-pins/PIN-405-evidence-architecture-v11---structural-authority-integrity-model.md` |
| PIN-370 | `docs/memory-pins/PIN-370-sdsr-scenario-driven-system-realization.md` |
| PIN-406 | `docs/governance/ARCH_DECISIONS.md` (Fail-Closed Traces) |
| SDSR-E2E-006 | `backend/scripts/sdsr/scenarios/SDSR-E2E-006.yaml` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-12 | Initial creation - documenting fundamental semantic correction |
