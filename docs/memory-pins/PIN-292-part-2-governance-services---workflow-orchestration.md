# PIN-292: Part-2 Governance Services - Workflow Orchestration

**Status:** COMPLETE
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Implemented the Part-2 Governance Services (L4), the workflow orchestration layer that bridges contracts to job execution. These services coordinate the governance workflow without executing jobs or making audit decisions.

---

## Key Design Decisions

### 1. Orchestrates Only - Does NOT Execute

The Governance Orchestrator is a "traffic controller":
- Creates job plans from contracts
- Tracks job state transitions
- Prepares evidence for audit

It does NOT:
- Execute job steps (that's L5 Job Executor)
- Modify health signals
- Make audit decisions (that's L8 Audit Service)

### 2. Contract is Sole Source of Execution Intent

All job plans derive from contract `proposed_changes`. No job can exist without a contract, and no execution can happen without going through the contract state machine.

```python
def activate_contract(self, contract_state: ContractState, ...) -> tuple[ContractState, JobState]:
    # Validates contract is APPROVED
    if contract_state.status != ContractStatus.APPROVED:
        raise ContractActivationError(...)

    # Creates job plan FROM contract
    steps = ExecutionOrchestrator.create_job_plan(contract_state)

    # Creates job in PENDING state
    job_state = JobState(...)

    # Transitions contract to ACTIVE
    updated_contract = self._contract_service.activate(contract_state, job_id)
```

### 3. Job State Machine with Terminal Immutability

Jobs follow a strict state machine:

```
PENDING ──────► RUNNING ──────► COMPLETED
    │              │
    │              ├──────────► FAILED
    │              │
    ▼              ▼
CANCELLED     CANCELLED
```

Terminal states (COMPLETED, FAILED, CANCELLED) are immutable.

### 4. Audit Trigger - Prepares Evidence, Doesn't Decide

The Audit Trigger prepares evidence packages but makes no verdicts:

```python
evidence = AuditEvidence(
    job_id=job_state.job_id,
    contract_id=job_state.contract_id,
    job_status=job_state.status,
    steps=job_state.steps,
    step_results=job_state.step_results,
    health_before=job_state.health_snapshot_before,
    health_after=job_state.health_snapshot_after,
    execution_duration_seconds=duration,
    collected_at=datetime.now(timezone.utc),
)
```

The Audit Service (L8) receives this and makes the verdict.

---

## Components Implemented

### 1. Contract Activation Service

Bridges APPROVED contracts to ACTIVE + PENDING job:
- Validates contract is APPROVED
- Creates job plan from proposed_changes
- Creates JobState in PENDING
- Transitions contract to ACTIVE

### 2. Execution Orchestrator

Translates contract proposed_changes into JobSteps:
- Parses change lists
- Validates step structure
- Calculates timeouts

### 3. Job State Tracker

Observes job execution (does NOT control):
- Records step results
- Calculates completion status
- Tracks step progress

### 4. Audit Trigger

Prepares evidence for audit layer:
- Packages job state
- Captures health snapshots
- Calculates execution duration

---

## Invariants Implemented

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| JOB-001 | Jobs require contract_id | `contract_id` required, unique |
| JOB-002 | Job steps execute in order | `step_index` sequential |
| JOB-003 | Terminal states are immutable | `JobImmutableError` |
| JOB-004 | Evidence is recorded per step | `StepResult` per step |
| JOB-005 | Health snapshots are read-only | `HealthSnapshot` observations |

---

## Files Created

```
backend/app/models/governance_job.py (~350 lines)
  - L6 database model: GovernanceJob
  - Enums: JobStatus, StepStatus
  - Pydantic models: JobStep, StepResult, HealthSnapshot, JobCreate, JobResponse
  - Exceptions: InvalidJobTransitionError, JobImmutableError, OrphanJobError
  - State transition map: JOB_VALID_TRANSITIONS

backend/app/services/governance/governance_orchestrator.py (~600 lines)
  - L4 domain service: GovernanceOrchestrator
  - State machine: JobStateMachine
  - State representation: JobState
  - Components: ContractActivationService, ExecutionOrchestrator, JobStateTracker, AuditTrigger
  - Evidence: AuditEvidence

backend/tests/governance/test_orchestrator_invariants.py (~750 lines)
  - 51 invariant tests covering all 5 JOB invariants
  - Contract activation tests
  - Job state machine tests
  - Audit trigger tests
  - Orchestrator boundary tests
```

**Updated:**
```
backend/app/services/governance/__init__.py (added exports)
backend/app/models/__init__.py (added exports)
```

**Total:** ~1,700 lines (implementation + tests)

---

## Test Coverage

51 invariant tests covering:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestJOB001JobsRequireContract | 3 | Contract-job linking |
| TestJOB002StepsInOrder | 4 | Step sequencing |
| TestJOB003TerminalImmutable | 7 | Terminal state protection |
| TestJOB004EvidencePerStep | 3 | Evidence recording |
| TestJOB005HealthReadOnly | 3 | Health observation |
| TestJobStateMachine | 6 | State machine transitions |
| TestExecutionOrchestrator | 3 | Job plan creation |
| TestJobStateTracker | 2 | Completion calculation |
| TestAuditTrigger | 6 | Audit triggering |
| TestContractActivationService | 4 | Activation workflow |
| TestGovernanceOrchestratorFacade | 3 | Full workflow |
| TestOrchestratorBoundaries | 3 | Authority boundaries |
| TestJobStateMachineCompleteness | 4 | State machine integrity |

All 51 tests passing.

---

## Combined Governance Tests

```
173 tests passing (31 validator + 48 eligibility + 43 contract + 51 orchestrator)
```

---

## CI Guard Compliance

| Guard | Status |
|-------|--------|
| Backend Structure Guard | PASS (STRUCTURE INTACT) |
| Health Lifecycle Coherence Guard | PASS (COHERENT) |

No bypass patterns detected in governance services.

---

## What Governance Services Do NOT Do

| Action | Owner |
|--------|-------|
| Execute job steps | Job Executor (L5 - future) |
| Modify health signals | PlatformHealthService |
| Make audit decisions | Audit Service (L8 - future) |
| Create contracts | Contract Service (PIN-291) |
| Check eligibility | Eligibility Engine (PIN-289) |
| Validate issues | Validator Service (PIN-288) |
| Override MAY_NOT | (forbidden - mechanical) |

---

## Authority Chain (Complete)

```
CRM Event (no authority)
    ↓
Validator (machine, advisory) [PIN-288]
    ↓
Eligibility (machine, deterministic gate) [PIN-289]
    ↓
Contract (machine, state authority) [PIN-291]
    ↓
Founder Review (human, approval authority)
    ↓
Governance Orchestrator (machine, coordination) [PIN-292]
    ↓
Job Executor (machine, execution authority) ← NEXT
    ↓
Health Service (machine, truth authority)
    ↓
Auditor (machine, verification authority)
```

---

## Next Step

With Validator, Eligibility, Contract, and Governance Services implemented, proceed to:
- **Founder Review Surface** (human approval gate)

Implementation order from here:
1. ~~Validator (pure analysis)~~ DONE (PIN-288)
2. ~~Eligibility engine (pure rules)~~ DONE (PIN-289)
3. ~~Contract model (stateful)~~ DONE (PIN-291)
4. ~~Governance services~~ DONE (PIN-292)
5. Founder review surface <- NEXT
6. Job execution
7. Audit wiring
8. Rollout projection

---

## References

- Tag: `part2-design-v1`
- PIN-284: Part-2 Design Documentation
- PIN-285: Pass 1 Static CI Guards
- PIN-286: Pass 2 Bootstrap + Semantic Guards
- PIN-287: CRM Event Schema
- PIN-288: Validator Service
- PIN-289: Eligibility Engine
- PIN-291: Contract Model
- PART2_CRM_WORKFLOW_CHARTER.md

---

## Related PINs

- [PIN-287](PIN-287-crm-event-schema---part-2-workflow-initiator-schema.md)
- [PIN-288](PIN-288-part-2-validator-service---pure-analysis-implementation.md)
- [PIN-289](PIN-289-part-2-eligibility-engine---pure-rules-implementation.md)
- [PIN-291](PIN-291-part-2-contract-model---first-stateful-governance-component.md)
