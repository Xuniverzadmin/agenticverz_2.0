# System Contract Object Design Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** PART2_CRM_WORKFLOW_CHARTER.md
**Layer:** L4 Domain Model

---

## Definition

> A **System Contract** is a formal, machine-enforced agreement between
> human intent and governance authority.

It is NOT:
- A simple record
- A request queue item
- An event log entry

It IS:
- A state machine with explicit transitions
- An authorization boundary
- An audit trail anchor
- A rollback reference

---

## Contract Lifecycle States

```
┌─────────────────────────────────────────────────────────────┐
│                  SYSTEM CONTRACT LIFECYCLE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DRAFT ──────► VALIDATED ──────► ELIGIBLE ──────► APPROVED  │
│    │              │                 │                │      │
│    │              │                 │                ▼      │
│    │              │                 │            ACTIVE     │
│    │              │                 │                │      │
│    │              │                 │          ┌────┴────┐  │
│    │              │                 │          ▼         ▼  │
│    ▼              ▼                 ▼      COMPLETED   FAILED│
│  EXPIRED      REJECTED          REJECTED       │         │  │
│                                                ▼         ▼  │
│                                            AUDITED   AUDITED │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### State Definitions

| State | Entry Condition | Exit Condition | Terminal? |
|-------|-----------------|----------------|-----------|
| DRAFT | Issue passes initial filter | Validation completes | No |
| VALIDATED | Validator produces verdict | Eligibility check runs | No |
| ELIGIBLE | Eligibility returns MAY | Founder reviews | No |
| APPROVED | Founder approves | Activation window starts | No |
| ACTIVE | Activation window begins | Job completes or window expires | No |
| COMPLETED | Job succeeds + audit passes | None | Yes |
| FAILED | Job fails OR audit fails | None | Yes |
| REJECTED | Any gate rejects | None | Yes |
| EXPIRED | TTL exceeded | None | Yes |
| AUDITED | Audit verdict recorded | None | Yes (meta) |

---

## Contract Schema

```yaml
# system_contracts table
contract_id: UUID (PK)
version: INTEGER (optimistic lock)

# Origin
issue_id: UUID (FK → issue_events)
source: ENUM(crm_feedback, support_ticket, ops_alert, manual)

# State
status: ENUM(DRAFT, VALIDATED, ELIGIBLE, APPROVED, ACTIVE, COMPLETED, FAILED, REJECTED, EXPIRED)
status_reason: TEXT (human-readable)

# Content
title: TEXT (required, <= 200 chars)
description: TEXT (optional, <= 4000 chars)
proposed_changes: JSONB (schema-validated)
affected_capabilities: TEXT[] (capability names)
risk_level: ENUM(critical, high, medium, low)

# Validation
validator_verdict: JSONB (nullable until validated)
eligibility_verdict: JSONB (nullable until eligible)
confidence_score: DECIMAL(3,2) (0.00-1.00)

# Authorization
created_by: TEXT (system or user_id)
approved_by: TEXT (nullable until approved)
approved_at: TIMESTAMP (nullable)

# Execution
activation_window_start: TIMESTAMP (nullable)
activation_window_end: TIMESTAMP (nullable)
execution_constraints: JSONB (rate limits, scope limits)

# Audit
audit_verdict: ENUM(PENDING, PASS, FAIL, INCONCLUSIVE) DEFAULT PENDING
audit_reason: TEXT (nullable)
audit_completed_at: TIMESTAMP (nullable)

# Timestamps
created_at: TIMESTAMP DEFAULT NOW()
updated_at: TIMESTAMP DEFAULT NOW()
expires_at: TIMESTAMP (TTL for DRAFT contracts)
```

---

## Proposed Changes Schema

The `proposed_changes` field must conform to:

```yaml
proposed_changes:
  type: ENUM(capability_enable, capability_disable, configuration_update, parameter_change)

  capability_enable:
    capability_name: TEXT
    target_lifecycle: ENUM(PREVIEW, LAUNCHED, DEPRECATED)

  capability_disable:
    capability_name: TEXT
    reason: TEXT

  configuration_update:
    scope: ENUM(SYSTEM, capability_name)
    key: TEXT
    old_value: ANY (for verification)
    new_value: ANY

  parameter_change:
    scope: ENUM(SYSTEM, capability_name)
    parameters: JSONB
```

---

## Validator Verdict Schema

```yaml
validator_verdict:
  issue_type: ENUM(capability_request, bug_report, configuration_change, escalation)
  severity: ENUM(critical, high, medium, low)
  affected_capabilities: TEXT[]
  recommended_action: ENUM(create_contract, defer, reject, escalate)
  confidence_score: DECIMAL(3,2)
  reason: TEXT
  analyzed_at: TIMESTAMP
  validator_version: TEXT
```

---

## Eligibility Verdict Schema

```yaml
eligibility_verdict:
  decision: ENUM(MAY, MAY_NOT)
  reason: TEXT
  blocking_signals: TEXT[] (if any)
  missing_prerequisites: TEXT[] (if any)
  evaluated_at: TIMESTAMP
  rules_version: TEXT
```

---

## State Transition Rules

### DRAFT → VALIDATED

**Trigger:** Validator analysis completes
**Guard:** Validator produces verdict
**Action:** Record `validator_verdict`, update `confidence_score`
**On failure:** → REJECTED (invalid issue)

### VALIDATED → ELIGIBLE

**Trigger:** Eligibility check runs
**Guard:** `eligibility_verdict.decision = MAY`
**Action:** Record `eligibility_verdict`
**On failure:** → REJECTED (ineligible)

### ELIGIBLE → APPROVED

**Trigger:** Founder approves
**Guard:** Founder has authority, contract not expired
**Action:** Set `approved_by`, `approved_at`
**On failure:** → REJECTED (denied)

### APPROVED → ACTIVE

**Trigger:** Activation window begins
**Guard:** `NOW() >= activation_window_start`
**Action:** Create governance job
**On failure:** → FAILED (activation error)

### ACTIVE → COMPLETED

**Trigger:** Job completes successfully
**Guard:** `job.status = COMPLETED`, `audit_verdict = PASS`
**Action:** Finalize contract
**On failure:** → FAILED (job or audit failed)

### ACTIVE → FAILED

**Trigger:** Job fails OR audit fails
**Guard:** `job.status = FAILED` OR `audit_verdict = FAIL`
**Action:** Create rollback job, create incident
**On failure:** Escalate to human

### * → EXPIRED

**Trigger:** TTL exceeded
**Guard:** `NOW() > expires_at` AND status in (DRAFT, VALIDATED, ELIGIBLE)
**Action:** Mark expired, notify creator
**On failure:** N/A

---

## Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| CONTRACT-001 | Status transitions must follow state machine | DB trigger |
| CONTRACT-002 | APPROVED requires `approved_by` | NOT NULL constraint |
| CONTRACT-003 | ACTIVE requires job exists | FK constraint |
| CONTRACT-004 | COMPLETED requires `audit_verdict = PASS` | Check constraint |
| CONTRACT-005 | Terminal states are immutable | Trigger |
| CONTRACT-006 | `proposed_changes` must validate schema | Check constraint |
| CONTRACT-007 | `confidence_score` range [0,1] | Check constraint |

---

## Indexes

```sql
-- Primary queries
CREATE INDEX idx_contracts_status ON system_contracts(status);
CREATE INDEX idx_contracts_issue ON system_contracts(issue_id);
CREATE INDEX idx_contracts_capability ON system_contracts USING GIN(affected_capabilities);
CREATE INDEX idx_contracts_expires ON system_contracts(expires_at) WHERE status IN ('DRAFT', 'VALIDATED', 'ELIGIBLE');

-- Audit queries
CREATE INDEX idx_contracts_audit ON system_contracts(audit_verdict, audit_completed_at);
CREATE INDEX idx_contracts_approved ON system_contracts(approved_by, approved_at);
```

---

## API Surface

Contracts are accessed via:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/contracts` | GET | List contracts (filtered) |
| `/api/v1/contracts/{id}` | GET | Get contract detail |
| `/api/v1/contracts/{id}/approve` | POST | Founder approval |
| `/api/v1/contracts/{id}/reject` | POST | Founder rejection |
| `/api/v1/contracts/{id}/history` | GET | State transition history |

**No direct CREATE endpoint.** Contracts are created via validated proposals only.

---

## Attestation

This specification defines the System Contract object model.
Implementation must conform to this schema and state machine.
Changes require amendment to this specification.
