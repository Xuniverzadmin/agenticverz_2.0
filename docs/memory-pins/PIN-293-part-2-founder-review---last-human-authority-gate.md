# PIN-293: Part-2 Founder Review - Last Human Authority Gate

**Status:** COMPLETE
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Implemented the Founder Review surface - the **LAST human authority insertion point** in the entire Part-2 governance workflow. This is a "narrow valve" that allows founders to APPROVE or REJECT ELIGIBLE contracts, with no other actions permitted.

---

## Key Design Decisions

### 1. Binary Decision Gate

Founder Review is intentionally constrained:
- **Read**: Queue of ELIGIBLE contracts, contract details
- **Write**: APPROVE or REJECT (binary decision)

That's it. No 'update'. No 'edit'. No 'retry'. No 'override'.

```
ELIGIBLE ──► FOUNDER REVIEW ──► APPROVED
                              └──► REJECTED (terminal)
```

### 2. MAY_NOT is Mechanically Un-Approvable

MAY_NOT contracts **never appear** in the Founder Review queue because:
- ContractService refuses to create contracts from MAY_NOT verdicts
- This is enforced at L4, not L2
- Founders cannot override this - it's a system invariant

```python
# L4 ContractService - MAY_NOT enforcement (absolute)
if eligibility_verdict.decision == EligibilityDecision.MAY_NOT:
    raise MayNotVerdictError(eligibility_verdict.reason)
```

### 3. L2/L3/L4 Layer Separation

The implementation strictly follows layer boundaries:

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| L2 | `founder_review.py` | HTTP handling, thin layer |
| L3 | `founder_review_adapter.py` | Translation only |
| L4 | `ContractService` | Business logic, state machine |

### 4. Adapter is Translation-Only

The L3 adapter (`FounderReviewAdapter`) performs **no business logic**:
- Translates `ContractState` (L4) → `FounderContractSummaryView` (L3)
- Translates `ContractState` (L4) → `FounderContractDetailView` (L3)
- Formats queue responses
- Formats review results

It cannot approve, reject, or modify contracts.

---

## Components Implemented

### 1. L3 Founder Review Adapter

`backend/app/adapters/founder_review_adapter.py` (~310 lines)

View DTOs:
- `FounderContractSummaryView` - Queue item view
- `FounderContractDetailView` - Full review context
- `FounderReviewQueueResponse` - Queue endpoint response
- `FounderReviewDecision` - Input for APPROVE/REJECT
- `FounderReviewResult` - Result after review

Adapter methods:
- `to_summary_view()` - Contract → Summary
- `to_detail_view()` - Contract → Detail
- `to_queue_response()` - List → Queue response
- `to_review_result()` - Review action → Result

### 2. L2 Founder Review API

`backend/app/api/founder_review.py` (~330 lines)

Endpoints:
- `GET /fdr/contracts/review-queue` - List ELIGIBLE contracts
- `GET /fdr/contracts/{contract_id}` - Get contract details
- `POST /fdr/contracts/{contract_id}/review` - Submit APPROVE/REJECT

Features:
- Uses L3 adapter for all response translation
- Delegates all business logic to L4 ContractService
- Proper error handling (404, 400, 409)
- Pydantic request validation

### 3. Invariant Tests

`backend/tests/governance/test_founder_review_invariants.py` (~600 lines)

38 tests covering:
- REVIEW-001: Only operates on ELIGIBLE contracts
- REVIEW-002: APPROVE transitions to APPROVED
- REVIEW-003: REJECT transitions to REJECTED (terminal)
- REVIEW-004: MAY_NOT never appears in queue
- REVIEW-005: Queue only shows ELIGIBLE contracts
- REVIEW-006: Cannot approve/reject non-ELIGIBLE contracts
- REVIEW-007: L3 adapter performs translation only

---

## Invariants Implemented

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| REVIEW-001 | Founder Review only on ELIGIBLE | L4 state machine |
| REVIEW-002 | APPROVE → APPROVED | L4 `approve()` |
| REVIEW-003 | REJECT → REJECTED (terminal) | L4 `reject()` |
| REVIEW-004 | MAY_NOT never in queue | L4 `create_contract()` |
| REVIEW-005 | Queue = ELIGIBLE only | L2 filtering |
| REVIEW-006 | Non-ELIGIBLE = error | L4 state machine |
| REVIEW-007 | Adapter = translation | L3 design |

---

## Files Created

```
backend/app/adapters/founder_review_adapter.py (~310 lines)
  - L3 boundary adapter
  - View DTOs: FounderContractSummaryView, FounderContractDetailView, etc.
  - Translation methods: to_summary_view, to_detail_view, etc.

backend/app/api/founder_review.py (~330 lines)
  - L2 REST API
  - Endpoints: /review-queue, /{id}, /{id}/review
  - Request models: ReviewDecisionRequest

backend/tests/governance/test_founder_review_invariants.py (~600 lines)
  - 38 invariant tests
  - REVIEW-001 to REVIEW-007 coverage
  - L2/L3/L4 integration tests
```

**Updated:**
```
backend/app/adapters/__init__.py (added exports)
```

**Total:** ~1,240 lines (implementation + tests)

---

## Test Coverage

38 invariant tests covering:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestREVIEW001EligibleOnly | 4 | Only ELIGIBLE contracts |
| TestREVIEW002ApproveTransition | 6 | APPROVE behavior |
| TestREVIEW003RejectTransition | 5 | REJECT behavior |
| TestREVIEW004MayNotExclusion | 2 | MAY_NOT enforcement |
| TestREVIEW005QueueFiltering | 2 | Queue filtering |
| TestREVIEW006NonEligibleRejection | 3 | Non-ELIGIBLE errors |
| TestREVIEW007AdapterTranslation | 5 | L3 adapter purity |
| TestFounderContractSummaryView | 2 | Summary DTO |
| TestFounderContractDetailView | 3 | Detail DTO |
| TestL2APIThinLayer | 3 | L2 API structure |
| TestFounderReviewIntegration | 3 | Full flow |

All 38 tests passing.

---

## Combined Governance Tests

```
211 tests passing (31 validator + 48 eligibility + 43 contract + 51 orchestrator + 38 founder review)
```

---

## What Founder Review Does NOT Do

| Action | Why Not |
|--------|---------|
| Execute contracts | That's Job Executor (future) |
| Modify health signals | That's PlatformHealthService |
| Override MAY_NOT | Mechanically impossible |
| Edit contracts | Contracts are immutable after creation |
| Create contracts | That's ContractService |
| Retry rejected contracts | REJECTED is terminal |

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
Founder Review (human, approval authority) [PIN-293] ← THIS PIN
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

With Founder Review implemented, the human authority gate is complete. Proceed to:
- **Job Executor** (machine execution layer)

Implementation order from here:
1. ~~Validator (pure analysis)~~ DONE (PIN-288)
2. ~~Eligibility engine (pure rules)~~ DONE (PIN-289)
3. ~~Contract model (stateful)~~ DONE (PIN-291)
4. ~~Governance services~~ DONE (PIN-292)
5. ~~Founder review surface~~ DONE (PIN-293)
6. Job execution <- NEXT
7. Audit wiring
8. Rollout projection

---

## API Reference

### GET /fdr/contracts/review-queue

Returns all contracts in ELIGIBLE status awaiting founder review.

**Response:**
```json
{
  "total": 1,
  "contracts": [
    {
      "contract_id": "uuid",
      "title": "string",
      "status": "ELIGIBLE",
      "risk_level": "MEDIUM",
      "source": "crm_feedback",
      "affected_capabilities": ["cap1", "cap2"],
      "confidence_score": 0.85,
      "created_at": "2026-01-04T20:00:00Z",
      "expires_at": "2026-01-07T20:00:00Z",
      "issue_type": "capability_request",
      "severity": "medium"
    }
  ],
  "as_of": "2026-01-04T20:00:00Z"
}
```

### GET /fdr/contracts/{contract_id}

Returns full contract context for review decision.

### POST /fdr/contracts/{contract_id}/review

Submit APPROVE or REJECT decision.

**Request:**
```json
{
  "decision": "APPROVE",  // or "REJECT"
  "comment": "Approved for deployment",
  "activation_window_hours": 24
}
```

**Response:**
```json
{
  "contract_id": "uuid",
  "previous_status": "ELIGIBLE",
  "new_status": "APPROVED",
  "reviewed_by": "founder_id",
  "reviewed_at": "2026-01-04T20:00:00Z",
  "comment": "Approved for deployment"
}
```

---

## References

- Tag: `part2-design-v1`
- PIN-284: Part-2 Design Documentation
- PIN-287: CRM Event Schema
- PIN-288: Validator Service
- PIN-289: Eligibility Engine
- PIN-291: Contract Model
- PIN-292: Governance Services
- PART2_CRM_WORKFLOW_CHARTER.md

---

## Related PINs

- [PIN-288](PIN-288-part-2-validator-service---pure-analysis-implementation.md)
- [PIN-289](PIN-289-part-2-eligibility-engine---pure-rules-implementation.md)
- [PIN-291](PIN-291-part-2-contract-model---first-stateful-governance-component.md)
- [PIN-292](PIN-292-part-2-governance-services---workflow-orchestration.md)
