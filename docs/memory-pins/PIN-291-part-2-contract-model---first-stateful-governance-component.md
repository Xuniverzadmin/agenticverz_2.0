# PIN-291: Part-2 Contract Model - First Stateful Governance Component

**Status:** COMPLETE
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Implemented the Part-2 Contract Model (L4/L6), the first stateful component in the Part-2 CRM governance workflow. The Contract Model provides a state machine for System Contracts that consume validator and eligibility outputs.

---

## Key Design Decisions

### 1. Contract Creation Consumes Validator + Eligibility

Contracts can only be created with:
- A `ValidatorVerdict` (proof of validation)
- An `EligibilityVerdict` with decision = MAY (proof of eligibility)

### 2. MAY_NOT is Mechanically Un-overridable

The most critical constraint:

```python
if eligibility_verdict.decision == EligibilityDecision.MAY_NOT:
    raise MayNotVerdictError(eligibility_verdict.reason)
```

This check cannot be bypassed, overridden, or worked around. If eligibility says MAY_NOT, no contract can be created. Period.

### 3. Contracts are Immutable Post-Terminal

Terminal states (COMPLETED, FAILED, REJECTED, EXPIRED) cannot transition to any other state. This is enforced by `ContractImmutableError`.

### 4. No Execution Logic

The Contract Model manages state only. Execution logic is delegated to the Job Executor (future component).

---

## Contract Lifecycle

```
DRAFT ──────► VALIDATED ──────► ELIGIBLE ──────► APPROVED
  │              │                 │                │
  │              │                 │                ▼
  │              │                 │            ACTIVE
  │              │                 │                │
  │              │                 │          ┌────┴────┐
  │              │                 │          ▼         ▼
  ▼              ▼                 ▼      COMPLETED   FAILED
EXPIRED      REJECTED          REJECTED       │         │
                                              ▼         ▼
                                          AUDITED   AUDITED
```

---

## Invariants Implemented

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| CONTRACT-001 | Status transitions must follow state machine | `VALID_TRANSITIONS` map |
| CONTRACT-002 | APPROVED requires approved_by | State machine validation |
| CONTRACT-003 | ACTIVE requires job exists | State machine validation |
| CONTRACT-004 | COMPLETED requires audit_verdict = PASS | State machine validation |
| CONTRACT-005 | Terminal states are immutable | `ContractImmutableError` |
| CONTRACT-006 | proposed_changes must validate schema | Input validation |
| CONTRACT-007 | confidence_score range [0,1] | Input validation |

---

## Files Created

```
backend/app/models/contract.py (~450 lines)
  - L6 database model: SystemContract
  - Enums: ContractStatus, AuditVerdict, RiskLevel, ContractSource
  - Pydantic models: ContractCreate, ContractResponse, ContractApproval
  - Exceptions: InvalidTransitionError, ContractImmutableError, MayNotVerdictError
  - State transition map: VALID_TRANSITIONS

backend/app/services/governance/contract_service.py (~450 lines)
  - L4 domain service: ContractService
  - State machine: ContractStateMachine
  - State representation: ContractState
  - Methods: create_contract, approve, reject, activate, complete, fail, expire

backend/tests/governance/test_contract_invariants.py (~700 lines)
  - 43 invariant tests covering all 7 CONTRACT invariants
  - MAY_NOT enforcement tests
  - State machine completeness tests
  - Transition history tests
```

**Updated:**
```
backend/app/services/governance/__init__.py (added exports)
backend/app/models/__init__.py (added exports)
```

**Total:** ~1,600 lines (implementation + tests)

---

## Test Coverage

43 invariant tests covering:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestCONTRACT001ValidTransitions | 8 | State machine transitions |
| TestCONTRACT002ApprovedRequiresApprover | 2 | Approval constraints |
| TestCONTRACT003ActiveRequiresJob | 2 | Activation constraints |
| TestCONTRACT004CompletedRequiresPass | 3 | Completion constraints |
| TestCONTRACT005TerminalImmutable | 5 | Terminal state protection |
| TestCONTRACT006ProposedChangesSchema | 2 | Schema validation |
| TestCONTRACT007ConfidenceRange | 3 | Confidence bounds |
| TestMayNotEnforcement | 3 | MAY_NOT blocking |
| TestStateMachineCompleteness | 3 | State machine integrity |
| TestTransitionHistory | 3 | Audit trail recording |
| TestVersionAndConfig | 2 | Version tracking |
| TestInputValidation | 2 | Input constraints |
| TestQueryHelpers | 5 | Query methods |

All 43 tests passing.

---

## Combined Governance Tests

```
122 tests passing (31 validator + 48 eligibility + 43 contract)
```

---

## CI Guard Compliance

| Guard | Status |
|-------|--------|
| Backend Structure Guard | PASS (STRUCTURE INTACT) |
| Health Lifecycle Coherence Guard | PASS (COHERENT) |

No bypass patterns detected in governance services.

---

## What Contract Model Does NOT Do

| Action | Owner |
|--------|-------|
| Execute jobs | Job Executor (future) |
| Audit changes | Audit Service (future) |
| Create issues | Issue Ingestion (future) |
| Validate issues | Validator Service (PIN-288) |
| Check eligibility | Eligibility Engine (PIN-289) |
| Override MAY_NOT | (forbidden - mechanical) |

---

## Next Step

With Validator, Eligibility, and Contract implemented, proceed to:
- **Governance Services** (issue ingestion, etc.)

Implementation order from here:
1. ~~Validator (pure analysis)~~ DONE (PIN-288)
2. ~~Eligibility engine (pure rules)~~ DONE (PIN-289)
3. ~~Contract model (stateful)~~ DONE (PIN-291)
4. Governance services <- NEXT
5. Founder review surface
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
- SYSTEM_CONTRACT_OBJECT.md

---

## Related PINs

- [PIN-287](PIN-287-crm-event-schema---part-2-workflow-initiator-schema.md)
- [PIN-288](PIN-288-part-2-validator-service---pure-analysis-implementation.md)
- [PIN-289](PIN-289-part-2-eligibility-engine---pure-rules-implementation.md)
