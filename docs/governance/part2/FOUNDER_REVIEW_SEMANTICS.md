# Founder Review Semantics Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** PART2_CRM_WORKFLOW_CHARTER.md
**Layer:** Human Authority Gate

---

## Purpose

**Founder Review** is the human-in-the-loop authority gate.

It is:
- The ONLY point where human judgment enters the workflow
- A deliberate friction point (this is a feature)
- An approval, NOT a rubber stamp
- Auditable and traceable

---

## Review Authority

### Who May Review

| Role | Authority | Scope |
|------|-----------|-------|
| Founder | Full approval/reject | All contracts |
| Delegate (future) | Limited approval | Assigned capabilities |

**Phase-1:** Only Founder role exists.

---

## Review Actions

### APPROVE

```yaml
action: APPROVE
effect: Contract advances to APPROVED
fields_set:
  - approved_by: founder_id
  - approved_at: timestamp
  - activation_window_start: (founder sets or accepts default)
  - activation_window_end: (founder sets or accepts default)
constraints:
  - Cannot approve expired contract
  - Cannot approve if health degraded
  - Cannot approve frozen capability changes
```

### REJECT

```yaml
action: REJECT
effect: Contract terminates with REJECTED
fields_set:
  - status: REJECTED
  - status_reason: (founder provides reason)
constraints:
  - Rejection reason required (> 10 chars)
  - Rejection is final for this contract
```

### REQUEST_CLARIFICATION

```yaml
action: REQUEST_CLARIFICATION
effect: Contract remains ELIGIBLE, notification sent
fields_set:
  - clarification_request: TEXT
  - clarification_requested_at: timestamp
constraints:
  - Does not advance or terminate contract
  - Original proposal creator notified
  - Contract TTL paused while awaiting clarification
```

### MODIFY_SCOPE

```yaml
action: MODIFY_SCOPE
effect: Creates new contract version (DRAFT)
fields_set:
  - Creates new contract with modified proposed_changes
  - Original contract linked via parent_contract_id
  - Original contract marked SUPERSEDED
constraints:
  - Founder must explicitly define modifications
  - Modified contract restarts at DRAFT
  - Original validator/eligibility verdicts do not transfer
```

---

## Review Interface

The Founder Review Dashboard presents:

```
┌─────────────────────────────────────────────────────────────┐
│ CONTRACT REVIEW: {contract_id}                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ORIGIN                                                      │
│   Issue: {issue_id}                                         │
│   Source: {source}                                          │
│   Received: {received_at}                                   │
│                                                             │
│ VALIDATOR VERDICT                                           │
│   Type: {issue_type}                                        │
│   Severity: {severity}                                      │
│   Confidence: {confidence_score}                            │
│   Recommendation: {recommended_action}                      │
│   Reason: {reason}                                          │
│                                                             │
│ PROPOSED CHANGES                                            │
│   {formatted proposed_changes}                              │
│                                                             │
│ AFFECTED CAPABILITIES                                       │
│   {capability list with current status}                     │
│                                                             │
│ RISK ASSESSMENT                                             │
│   Risk Level: {risk_level}                                  │
│   Health Impact: {estimated}                                │
│                                                             │
│ ELIGIBILITY                                                 │
│   Decision: {MAY/MAY_NOT}                                   │
│   Rules Passed: {count}                                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ ACTIVATION WINDOW                                           │
│   Start: [__________] (default: immediate)                  │
│   End:   [__________] (default: +24h)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [APPROVE]  [REJECT]  [REQUEST CLARIFICATION]  [MODIFY]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Review Constraints

### What Founder CAN Do

- Approve eligible contracts
- Reject any contract (with reason)
- Request clarification
- Modify scope (creates new version)
- Set activation window
- Add notes/comments

### What Founder CANNOT Do

- Approve ineligible contracts
- Skip validation step
- Override eligibility rules
- Bypass audit after execution
- Create contracts without proposals
- Approve during health degradation

---

## Approval Semantics

Approval is NOT just "I agree this should happen."

Approval means:

> "I have reviewed this contract, understand its scope and risk,
> and authorize its execution within the specified window.
> I accept responsibility for this decision."

---

## Rejection Semantics

Rejection is NOT just "No."

Rejection means:

> "This contract should not proceed. The reason is recorded.
> A new proposal with different scope may be submitted."

Rejection reason is:
- Required (not optional)
- Auditable
- Visible to original requestor
- Permanent record

---

## Clarification Flow

```
ELIGIBLE → Founder requests clarification → (paused)
                      ↓
            Clarification provided
                      ↓
        Founder reviews again → APPROVE/REJECT
```

Clarification does not:
- Re-run validation
- Re-check eligibility
- Reset contract TTL

Clarification does:
- Pause TTL expiration
- Notify requestor
- Record in audit trail

---

## Review Timeout

Contracts awaiting review have a timeout:

```yaml
review_timeout:
  default: 7 days
  warning_at: 5 days
  escalation_at: 6 days
  expiration: 7 days
```

On expiration:
- Contract → EXPIRED
- Notification to Founder
- No automatic approval

---

## Audit Trail

Every review action is recorded:

```yaml
review_event:
  contract_id: UUID
  action: ENUM
  actor: founder_id
  timestamp: TIMESTAMP
  reason: TEXT (for reject)
  modifications: JSONB (for modify)
  session_id: TEXT (for traceability)
```

---

## Delegation (Future)

In future versions, Founders may delegate review authority:

```yaml
delegation:
  delegate_id: TEXT
  delegated_by: founder_id
  scope:
    capabilities: [list]
    max_risk_level: medium
    valid_until: TIMESTAMP
```

**Not implemented in Part-2 Phase-1.**

---

## Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| REVIEW-001 | Only ELIGIBLE contracts can be approved | State check |
| REVIEW-002 | Rejection requires reason | Validation |
| REVIEW-003 | Approval sets activation window | Required fields |
| REVIEW-004 | All actions are audited | Event recording |
| REVIEW-005 | Modification creates new version | Version control |
| REVIEW-006 | Timeout leads to expiration | TTL enforcement |

---

## Attestation

This specification defines the Founder Review semantics.
Review is the human authority gate in Part-2 workflow.
No contract may execute without explicit Founder approval.
