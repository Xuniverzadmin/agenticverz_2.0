# Part-2 Closure Criteria

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** All Part-2 Specifications
**Purpose:** Define what "done" means for Part-2

---

## Prime Criterion

> Part-2 is **CLOSED** when a CRM event can safely become a deployed change
> through a fully governed, human-approved, machine-audited workflow.

---

## The 10 Mandatory Closure Gates

All gates must pass. No partial closure.

---

### Gate 1: Issue Ingestion (L8 → DB)

**Requirement:** CRM events are captured and stored correctly.

**Verification:**
- [ ] `issue_events` table exists with correct schema
- [ ] Ingestion endpoint receives CRM payloads
- [ ] Events are stored with source, timestamp, raw_payload
- [ ] No data loss in ingestion path

**Evidence:** Integration test showing CRM → DB flow

---

### Gate 2: Validator Service (L4)

**Requirement:** Validator produces structured verdicts.

**Verification:**
- [ ] ValidatorService exists as L4 domain service
- [ ] Produces ValidatorVerdict with all required fields
- [ ] Classification logic implemented per spec
- [ ] Confidence calculation follows formula
- [ ] Is stateless and deterministic

**Evidence:** Unit tests with various issue types

---

### Gate 3: Eligibility Engine (L4)

**Requirement:** Eligibility rules produce correct verdicts.

**Verification:**
- [ ] EligibilityEngine exists as L4 domain service
- [ ] All E-001 to E-006 rules implemented
- [ ] All E-100 to E-104 rules implemented
- [ ] Correct evaluation order (MAY_NOT first)
- [ ] Deterministic output

**Evidence:** Unit tests for each rule

---

### Gate 4: Contract State Machine

**Requirement:** Contracts follow defined lifecycle.

**Verification:**
- [ ] `system_contracts` table exists with correct schema
- [ ] All states implemented (DRAFT through AUDITED)
- [ ] State transitions enforced by DB triggers
- [ ] Invalid transitions rejected
- [ ] Terminal states are immutable

**Evidence:** State transition tests

---

### Gate 5: Founder Review Gate (Human)

**Requirement:** Human approval gate works correctly.

**Verification:**
- [ ] Review dashboard shows contract details
- [ ] APPROVE action sets correct fields
- [ ] REJECT action requires reason
- [ ] REQUEST_CLARIFICATION pauses TTL
- [ ] MODIFY_SCOPE creates new version
- [ ] Review actions are audited

**Evidence:** Manual review flow demonstration

---

### Gate 6: Job Execution (L5)

**Requirement:** Jobs execute contracts correctly.

**Verification:**
- [ ] `governance_jobs` table exists with correct schema
- [ ] Jobs execute steps in order
- [ ] Scope constraint enforced
- [ ] Health check per step
- [ ] Failure triggers rollback
- [ ] Duration timeout enforced

**Evidence:** Job execution tests with various scenarios

---

### Gate 7: Audit Verification (L8)

**Requirement:** Audit produces correct verdicts.

**Verification:**
- [ ] `governance_audits` table exists with correct schema
- [ ] All A-001 to A-007 checks implemented
- [ ] Health snapshots captured
- [ ] Evidence collected
- [ ] PASS/FAIL/INCONCLUSIVE logic correct
- [ ] Verdicts are immutable

**Evidence:** Audit tests with pass/fail scenarios

---

### Gate 8: Rollout/Rollback Flow

**Requirement:** Audit results lead to correct outcomes.

**Verification:**
- [ ] PASS → Contract COMPLETED, changes deployed
- [ ] FAIL → Contract FAILED, rollback executed
- [ ] INCONCLUSIVE → Human escalation
- [ ] Rollback reverses all completed steps
- [ ] Incidents created on failure

**Evidence:** End-to-end tests for all paths

---

### Gate 9: Phase-1 Preservation

**Requirement:** Part-2 does not violate Phase-1 invariants.

**Verification:**
- [ ] HEALTH-IS-AUTHORITY preserved
- [ ] HEALTH-LIFECYCLE-COHERENCE preserved
- [ ] HEALTH-DETERMINISM preserved
- [ ] NO-PHANTOM-HEALTH preserved
- [ ] DOMINANCE-ORDER preserved
- [ ] Frozen files unmodified
- [ ] PlatformHealthService unchanged

**Evidence:** Phase-1 invariant tests still pass

---

### Gate 10: Constitutional Compliance

**Requirement:** Implementation matches these specifications.

**Verification:**
- [ ] CRM Workflow Charter followed
- [ ] System Contract schema matches spec
- [ ] Eligibility rules match spec
- [ ] Validator logic matches spec
- [ ] Job model matches spec
- [ ] Founder review matches spec
- [ ] Audit model matches spec
- [ ] State machine matches spec

**Evidence:** Spec-to-code traceability matrix

---

## Closure Declaration Format

When all gates pass:

```yaml
PART2_CLOSURE_DECLARATION:
  status: CLOSED
  closed_at: TIMESTAMP
  closed_by: founder_id

  gates:
    issue_ingestion: PASS
    validator_service: PASS
    eligibility_engine: PASS
    contract_state_machine: PASS
    founder_review_gate: PASS
    job_execution: PASS
    audit_verification: PASS
    rollout_flow: PASS
    phase1_preservation: PASS
    constitutional_compliance: PASS

  evidence:
    test_report: TR-XXX
    spec_matrix: docs/governance/part2/SPEC_MATRIX.md
    demo_recording: (optional)

  frozen_files:
    - backend/app/models/contract.py
    - backend/app/services/governance/validator_service.py
    - backend/app/services/governance/eligibility_engine.py
    - backend/app/services/governance/contract_service.py
    - backend/app/services/governance/job_executor.py
    - backend/app/services/governance/audit_service.py
    - scripts/ci/part2_invariant_guard.py

  tag: part2-crm-workflow-v1
```

---

## What Part-2 Closure Enables

After Part-2 closure:

1. **CRM feedback can become contracts** - Structured change proposals
2. **Founder can approve changes** - Human-in-the-loop authority
3. **Changes execute safely** - Bounded, audited, reversible
4. **Health is preserved** - Phase-1 guarantees maintained
5. **Audit trail exists** - Every decision traceable

---

## What Part-2 Closure Does NOT Enable

Part-2 closure does NOT:

- Remove Founder from approval path
- Allow CRM to directly mutate system
- Bypass audit for any execution
- Override health signals
- Modify Phase-1 invariants

---

## Post-Closure Evolution

After Part-2 closure, future work may:

1. **Add capability types** - New change types in contracts
2. **Add eligibility rules** - New rules with version increment
3. **Add audit checks** - New checks with version increment
4. **Delegate authority** - (Future Part-3)

All evolution must preserve Part-2 invariants.

---

## Attestation

This specification defines the closure criteria for Part-2.
All 10 gates must pass before closure declaration.
Partial closure is not permitted.
Phase-1 invariants must be preserved throughout.
