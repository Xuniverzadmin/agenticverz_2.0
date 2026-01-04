# PIN-287: CRM Event Schema - Part-2 Workflow Initiator Schema

**Status:** RATIFIED
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Designed and ratified the CRM Event Schema (L8), the canonical input format for Part-2 workflow initiation. Schema defines event envelope, source attribution, payload structure, and input hints with explicit NON_AUTHORITATIVE semantics.

---

## Details

### Schema Purpose

The CRM Event Schema is a **workflow initiator schema** - it captures input data, not authority. CRM events enter the system through this schema and are subsequently processed by:
1. Validator (L4) - issue type classification
2. Eligibility Engine (L4) - contract gating
3. Founder Review (Human) - approval authority

### Schema Components

| Component | Purpose | Authority |
|-----------|---------|-----------|
| Event Envelope | Identity, timing, deduplication | None (metadata) |
| Source Attribution | Submitter tracking | None (audit) |
| Payload | Issue content | None (input) |
| Input Hints | Suggestions from source | NON_AUTHORITATIVE |

### Constitutional Constraints Applied

Four mandatory amendments were applied before ratification:

#### A. Hints NON_AUTHORITATIVE (Structural)

```yaml
hints:
  _semantics: NON_AUTHORITATIVE  # Explicit marker
```

> Any downstream component that treats hints as decisions is in violation of Part-2 governance and must fail CI.

#### B. Event Type Authority Constraint

| event_type | Allowed Effect |
|------------|----------------|
| issue | Normal flow |
| feedback | Normal flow |
| alert | Prioritization hint only |
| escalation | Prioritization hint only |

> `event_type` affects routing and urgency only, never eligibility, approval, or execution scope.

#### C. Contract Creation Forbidden

| Forbidden Action | Reason |
|------------------|--------|
| Contract instantiation | Requires validation + eligibility |
| Contract state transitions | State machine belongs to Contract Service |
| Eligibility pre-evaluation | Must go through Validator first |

> CRM ingestion MUST NOT create or mutate contracts directly.

#### D. Idempotency Window Semantics

- Within 24h: Same idempotency_key = duplicate, return existing
- After 24h: Same idempotency_key = new issue with `recurrence_of` link

### Database Schema

```sql
CREATE TABLE issue_events (
    issue_id UUID PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    -- ... full schema in CRM_EVENT_SCHEMA.md
    recurrence_of UUID REFERENCES issue_events(issue_id)
);
```

### Alignment with part2-design-v1

| Design Reference | Schema Alignment |
|------------------|------------------|
| PART2_CRM_WORKFLOW_CHARTER.md Step 1 | Fields match `issue_events` definition |
| VALIDATOR_LOGIC.md `ValidatorInput` | Schema produces valid input |
| SYSTEM_CONTRACT_OBJECT.md `issue_id` FK | `issue_id` generated at ingestion |

---

## Files Created

```
docs/governance/part2/CRM_EVENT_SCHEMA.md  (522 lines)
```

---

## What This Schema Does NOT Define

| Item | Owner |
|------|-------|
| Issue type classification | Validator |
| Severity determination | Validator |
| Eligibility decisions | Eligibility Engine |
| Contract creation | Contract Service |
| Approval authority | Founder Review |

---

## Next Step

With CRM Event Schema ratified, proceed to:
- **Validator implementation** (pure analysis, L4)

Implementation order from here:
1. Validator (pure analysis)
2. Eligibility engine (pure rules)
3. Contract model (stateful)
4. Governance services
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
- PART2_CRM_WORKFLOW_CHARTER.md
- VALIDATOR_LOGIC.md

---

## Commits

- `55ddb3fc`

---

## Related PINs

- [PIN-284](PIN-284-.md)
- [PIN-285](PIN-285-part-2-crm-workflow-enforcement---static-ci-guards.md)
- [PIN-286](PIN-286-part-2-enforcement-pass-2---bootstrap-and-semantic-guards.md)
