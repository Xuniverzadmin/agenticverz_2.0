# PIN-404: SDSR-E2E-006 Baseline Trust Scenario

**Status:** PROPOSED
**Created:** 2026-01-12
**Category:** SDSR / E2E Testing / Baseline
**Milestone:** SDSR Foundation
**Foundation:** AOS Execution Integrity Contract v1.0 (PIN-403)

---

## Summary

SDSR-E2E-006 is the **canonical baseline scenario** for all SDSR and Aurora behavior. It proves governance-grade capture and integrity evaluation on the success path, establishing the bedrock trust layer.

**If this scenario is invalid, no other scenario is trustworthy.**

---

## Scenario Classification

| Field | Value |
|-------|-------|
| **Scenario ID** | SDSR-E2E-006 |
| **Name** | Successful Activity → Run Record + Integrity (Baseline Trust) |
| **Class** | SC-EX-S (Execution — Success) |
| **Execution Mode** | executable |
| **Conceptually Supersedes** | SDSR-E2E-002 |

---

## Purpose (Non-Negotiable)

This scenario proves, in production-real terms, that:

1. **All successful executions are captured as Runs**
2. **Success produces evidence, not silence**
3. **Integrity is evaluated even when nothing goes wrong**
4. **Absence of incidents/policies is an explicit, verified outcome**
5. **Future governance can safely build on this baseline**

---

## Foundation Compliance

| Foundation Principle | E2E-006 Compliance |
|----------------------|-------------------|
| P1_CAPTURE_ALL | Run Record created with all required fields |
| P2_INTEGRITY_OVER_COMPLETENESS | Integrity score computed and verified |
| P3_NO_FABRICATED_CERTAINTY | Absence explicitly asserted, not inferred |

---

## Injection Boundary (Strict)

### Injected (Synthetic)

- Valid execution intent
- Schema-compliant inputs
- Policy-compliant inputs
- Within-threshold inputs

### Explicitly NOT Injected

- Logs
- Traces
- Incidents
- Policies
- Metrics
- Integrity results

**Invariant:** All downstream artifacts MUST be produced by real backend execution paths.

---

## Run Record Requirements

### Required Fields (Hard Requirements)

| Field | Must Exist | Expected Value |
|-------|------------|----------------|
| run_id | YES | — |
| actor_type | YES | human/agent/system |
| timestamp_start | YES | — |
| operation_type | YES | — |
| model_provider | YES | — |
| run_status | YES | `success` |
| response_expected | YES | `true` |
| response_received | YES | `true` |

### Missing any required field → **SCENARIO FAILS**

---

## Observability Requirements

### Logs

| Requirement | Status |
|-------------|--------|
| Entry log recorded | Required |
| Exit log recorded | Required |
| Logs correlated to run_id | Required |
| Silence is failure | YES |

### Traces

| Requirement | Status |
|-------------|--------|
| trace_expected = true | Required |
| trace_received = true | Required |
| Single root trace_id | Required |
| All spans linked | Required |
| Queryable after completion | Required |

---

## Explicit Absence Assertions

| Field | Expected | Inference Forbidden |
|-------|----------|---------------------|
| incident_created | `false` | YES |
| policy_created | `false` | YES |
| policy_proposal_created | `false` | YES |

**If absence is inferred rather than asserted → SCENARIO FAILS**

---

## Integrity Evaluation

### Expectations

| Condition | Result | Status |
|-----------|--------|--------|
| Response expected | Response received | PASS |
| Trace expected | Trace present | PASS |
| Logs expected | Logs present | PASS |

### Computation

| Metric | Value |
|--------|-------|
| expected_events | 3 |
| observed_events | 3 |
| missing_events | 0 |
| integrity_score | **1.0** |

**If integrity_score < 1.0 → SCENARIO FAILS**

---

## SDSR Observation Output

### Observation Class: `EFFECT`

**Reason:** Real execution occurred. Real system artifacts observed. Integrity verified.

### Capabilities Allowed

- EXECUTE
- TRACE
- VIEW_EXECUTION_GRAPH

### Capabilities Forbidden

- ACKNOWLEDGE
- RESOLVE
- APPROVE
- REJECT
- ACTIVATE
- DEACTIVATE

**Any forbidden capability inferred → reject observation**

---

## Acceptance Criteria

| AC | Criterion | Expected |
|----|-----------|----------|
| AC-001 | Run Record created with all required fields | true |
| AC-002 | run_status = success | success |
| AC-003 | response_expected AND response_received = true | true |
| AC-004 | Entry and exit logs recorded | true |
| AC-005 | Trace created with single root trace_id | true |
| AC-006 | All trace spans linked | true |
| AC-007 | policies_evaluated field exists | true |
| AC-008 | policy_results = pass | pass |
| AC-009 | incident_created explicitly = false | false |
| AC-010 | policy_created explicitly = false | false |
| AC-011 | policy_proposal_created explicitly = false | false |
| AC-012 | integrity_score = 1.0 | 1.0 |
| AC-013 | missing_events = 0 | 0 |
| AC-014 | incidents count for scenario = 0 | 0 |
| AC-015 | policy_proposals count for scenario = 0 | 0 |
| AC-016 | policy_rules count for scenario = 0 | 0 |

---

## Hard Failure Conditions

| Condition | Scenario Result |
|-----------|-----------------|
| No Run Record exists | FAIL |
| Logs or traces missing | FAIL |
| Integrity expectations violated | FAIL |
| Incident created | FAIL |
| Policy or proposal created | FAIL |
| Absence asserted implicitly | FAIL |
| Execution shortcuts governance layer | FAIL |

**Note:** Failure here is CORRECT behavior.

---

## Value Proven

After SDSR-E2E-006 is certified, the system can truthfully claim:

- All executions are observed
- Success paths are governed, not ignored
- Integrity is measurable
- Governance does not interfere with normal operation
- Future incidents and policies have a trusted baseline

**This is the BEDROCK scenario.**

---

## Relationship to Existing Scenarios

| Scenario | Relationship |
|----------|--------------|
| SDSR-E2E-005 | Proves worker execution + trace mechanics |
| SDSR-E2E-006 | Proves governance-grade capture + integrity on success |
| SDSR-E2E-001 | Builds on this baseline (failure path) |
| SDSR-E2E-003 | Builds on this baseline (threshold breach) |
| SDSR-E2E-004 | Builds on this baseline (HITL policy) |

**No conflicts. No rewrites. Clean layering.**

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Scenario YAML | `backend/scripts/sdsr/scenarios/SDSR-E2E-006.yaml` |
| Foundation Contract | `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml` |
| Scenario Coverage Matrix | `docs/governance/SDSR_SCENARIO_COVERAGE_MATRIX.md` |

---

## Related PINs

- [PIN-403](PIN-403-aos-execution-integrity-contract.md) - AOS Execution Integrity Contract (Foundation)
- [PIN-396](PIN-396-sdsr-scenario-coverage-matrix-locked.md) - SDSR Scenario Coverage Matrix
- [PIN-381](PIN-381-sdsr-e2e-testing-protocol-implementation.md) - SDSR E2E Testing Protocol
- [PIN-380](PIN-380-sdsr-e2e-001-stability-fixes.md) - SDSR-E2E-001 Stability Fixes

---

*This PIN establishes a foundational scenario. Certification validates the bedrock trust layer.*
