# Part-2 CRM Workflow System - Specification Index

**Status:** DESIGN COMPLETE
**Effective:** 2026-01-04
**Reference:** PIN-284 (Platform Monitoring System)

---

## Overview

Part-2 defines a **governed workflow system** that allows CRM feedback
to result in controlled, auditable system changes without violating
Phase-1 invariants.

**Key Principle:**
> CRM is a workflow **initiator**, not an authority **source**.
> Authority is explicitly staged: machine validation → eligibility gating → human approval → governance automation.

---

## Specification Documents

| # | Document | Purpose | Layer |
|---|----------|---------|-------|
| 1 | [CRM Workflow Charter](PART2_CRM_WORKFLOW_CHARTER.md) | 10-step canonical workflow | Cross-cutting |
| 2 | [System Contract Object](SYSTEM_CONTRACT_OBJECT.md) | Contract states, fields, lifecycle | L4 Model |
| 3 | [Eligibility Rules](ELIGIBILITY_RULES.md) | What may/may not become contract | L4 Logic |
| 4 | [Validator Logic](VALIDATOR_LOGIC.md) | Issue analysis semantics | L4 Service |
| 5 | [Governance Job Model](GOVERNANCE_JOB_MODEL.md) | How contracts execute safely | L5 Execution |
| 6 | [Founder Review Semantics](FOUNDER_REVIEW_SEMANTICS.md) | Human approval gate | Human Authority |
| 7 | [Governance Audit Model](GOVERNANCE_AUDIT_MODEL.md) | Post-execution verification | L8 Verification |
| 8 | [End-to-End State Machine](END_TO_END_STATE_MACHINE.md) | Contract → Job → Audit → Rollout | Cross-cutting |
| 9 | [Closure Criteria](PART2_CLOSURE_CRITERIA.md) | What "done" means for Part-2 | Governance |

---

## Reading Order

For implementers, read in this order:

1. **CRM Workflow Charter** - Understand the 10-step flow
2. **System Contract Object** - Core data model
3. **Validator Logic** - How issues become proposals
4. **Eligibility Rules** - Gate between proposals and contracts
5. **Founder Review Semantics** - Human authority gate
6. **Governance Job Model** - Execution semantics
7. **Governance Audit Model** - Verification semantics
8. **End-to-End State Machine** - How everything connects
9. **Closure Criteria** - What "done" means

---

## Authority Chain

```
CRM Event (no authority)
    ↓
Validator (machine, advisory)
    ↓
Eligibility (machine, deterministic gate)
    ↓
Founder Review (human, approval authority)
    ↓
Job Executor (machine, execution authority)
    ↓
Health Service (machine, truth authority)
    ↓
Auditor (machine, verification authority)
```

---

## Relationship to Phase-1

Part-2 is **layered on top of** Phase-1:

| Phase-1 Invariant | Part-2 Preservation |
|-------------------|---------------------|
| HEALTH-IS-AUTHORITY | Jobs cannot override health |
| HEALTH-LIFECYCLE-COHERENCE | Contract changes respect lifecycle |
| HEALTH-DETERMINISM | Audit verifies determinism |
| NO-PHANTOM-HEALTH | Health snapshots captured |
| DOMINANCE-ORDER | Health > Lifecycle > Qualifier |

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Specifications | COMPLETE |
| Database Schema | NOT STARTED |
| L4 Services | NOT STARTED |
| L5 Executor | NOT STARTED |
| L8 Auditor | NOT STARTED |
| API Endpoints | NOT STARTED |
| Founder Dashboard | NOT STARTED |
| CI Guards | NOT STARTED |

---

## Next Steps

1. **Draft Part-2 Closure Note** - Like Phase-1 closure note
2. **Map Part-2 gates to CI** - Enforcement automation
3. **Design CRM Event Schema (L8)** - Ingestion schema
4. **Begin implementation** - Following specs exactly

---

## Constitutional Notes

- These specifications are **constitutional** - deviations require amendment
- Implementation must conform to specs, not vice versa
- All 10 closure gates must pass before Part-2 is declared CLOSED
- Phase-1 invariants must be preserved throughout
