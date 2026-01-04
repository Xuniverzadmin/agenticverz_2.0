# End-to-End State Machine Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** All Part-2 Specifications
**Layer:** Cross-cutting

---

## Purpose

This document defines the complete state machine for Part-2 governance,
showing how Contract, Job, Audit, and Rollout states interact.

---

## The Four Coupled State Machines

Part-2 consists of four interconnected state machines:

1. **Contract State Machine** - Authorization lifecycle
2. **Job State Machine** - Execution lifecycle
3. **Audit State Machine** - Verification lifecycle
4. **Rollout State Machine** - Deployment lifecycle

Each machine has strict hand-off points to the next.

---

## Complete State Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PART-2 END-TO-END STATE MACHINE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ISSUE                                                                      │
│    ↓                                                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║  CONTRACT STATE MACHINE                                                ║  │
│  ║                                                                        ║  │
│  ║  DRAFT ─────► VALIDATED ─────► ELIGIBLE ─────► APPROVED               ║  │
│  ║    │              │                │               │                   ║  │
│  ║    ▼              ▼                ▼               │                   ║  │
│  ║  EXPIRED       REJECTED         REJECTED          │                   ║  │
│  ║                                                    │                   ║  │
│  ╚════════════════════════════════════════════════════╪═══════════════════╝  │
│                                                       │                      │
│                                                       ▼                      │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║  JOB STATE MACHINE                                 │                   ║  │
│  ║                                                    │                   ║  │
│  ║                    ACTIVE (contract) ──────────────┘                   ║  │
│  ║                         │                                              ║  │
│  ║                         ▼                                              ║  │
│  ║  PENDING ─────► RUNNING ─────► COMPLETED ─────► AUDIT_PENDING         ║  │
│  ║      │             │                                    │              ║  │
│  ║      ▼             ▼                                    │              ║  │
│  ║  CANCELLED      FAILED ──────────────────┐              │              ║  │
│  ║                    │                     │              │              ║  │
│  ║                    ▼                     │              │              ║  │
│  ║              ROLLBACK_PENDING            │              │              ║  │
│  ║                    │                     │              │              ║  │
│  ║              ┌─────┴─────┐               │              │              ║  │
│  ║              ▼           ▼               │              │              ║  │
│  ║        ROLLED_BACK  ROLLBACK_FAILED      │              │              ║  │
│  ║                                          │              │              ║  │
│  ╚══════════════════════════════════════════╪══════════════╪══════════════╝  │
│                                             │              │                 │
│                                             │              ▼                 │
│  ╔══════════════════════════════════════════╪══════════════════════════════╗ │
│  ║  AUDIT STATE MACHINE                     │                              ║ │
│  ║                                          │                              ║ │
│  ║  PENDING ─────────────────────────────────────────► PASS               ║ │
│  ║      │                                              │                  ║ │
│  ║      ├───────────────────────────────────────────► FAIL ────┐          ║ │
│  ║      │                                              │       │          ║ │
│  ║      └───────────────────────────────────────────► INCONCLUSIVE       ║ │
│  ║                                                             │          ║ │
│  ╚═════════════════════════════════════════════════════════════╪══════════╝ │
│                                                                │            │
│                                             ┌──────────────────┘            │
│                                             │                               │
│                                             ▼                               │
│  ╔══════════════════════════════════════════════════════════════════════╗  │
│  ║  ROLLOUT STATE MACHINE                                               ║  │
│  ║                                                                      ║  │
│  ║  PENDING ─────► (PASS) ─────► DEPLOYED ─────► VERIFIED              ║  │
│  ║      │                                                               ║  │
│  ║      │                                                               ║  │
│  ║      └──────► (FAIL) ──────► ROLLED_BACK ─────► INCIDENT            ║  │
│  ║      │                                                               ║  │
│  ║      └──────► (INCONCLUSIVE) ─────► ESCALATED                       ║  │
│  ║                                                                      ║  │
│  ╚══════════════════════════════════════════════════════════════════════╝  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## State Transition Table

### Contract Transitions

| From | To | Trigger | Guard | Action |
|------|----|---------|-------|--------|
| (issue) | DRAFT | Issue received | Source valid | Create contract |
| DRAFT | VALIDATED | Validator completes | Verdict produced | Record verdict |
| DRAFT | EXPIRED | TTL exceeded | Now > expires_at | Mark expired |
| VALIDATED | ELIGIBLE | Eligibility passes | Decision = MAY | Record eligibility |
| VALIDATED | REJECTED | Eligibility fails | Decision = MAY_NOT | Record rejection |
| ELIGIBLE | APPROVED | Founder approves | Has authority | Set approval |
| ELIGIBLE | REJECTED | Founder rejects | Reason provided | Record rejection |
| ELIGIBLE | EXPIRED | Review timeout | Now > review_deadline | Mark expired |
| APPROVED | ACTIVE | Window starts | Now >= window_start | Create job |
| ACTIVE | COMPLETED | Audit passes | Verdict = PASS | Finalize |
| ACTIVE | FAILED | Job/audit fails | Verdict = FAIL | Rollback |

---

### Job Transitions

| From | To | Trigger | Guard | Action |
|------|----|---------|-------|--------|
| (contract) | PENDING | Contract activates | Contract = ACTIVE | Create job |
| PENDING | RUNNING | Executor picks up | Executor available | Start execution |
| PENDING | CANCELLED | Manual cancel | Before execution | Mark cancelled |
| RUNNING | COMPLETED | All steps succeed | All steps done | Complete job |
| RUNNING | FAILED | Any step fails | Error occurred | Initiate rollback |
| COMPLETED | AUDIT_PENDING | Job done | Auto-trigger | Create audit |
| FAILED | ROLLBACK_PENDING | Failure confirmed | Rollback defined | Create rollback job |
| ROLLBACK_PENDING | ROLLED_BACK | Rollback succeeds | All reverted | Complete rollback |
| ROLLBACK_PENDING | ROLLBACK_FAILED | Rollback fails | Error occurred | Escalate |

---

### Audit Transitions

| From | To | Trigger | Guard | Action |
|------|----|---------|-------|--------|
| (job) | PENDING | Job completes | Job = COMPLETED | Create audit |
| PENDING | PASS | All checks pass | No failures | Record verdict |
| PENDING | FAIL | Any check fails | Failure detected | Record verdict |
| PENDING | INCONCLUSIVE | Check inconclusive | Cannot determine | Record verdict |

---

### Rollout Transitions

| From | To | Trigger | Guard | Action |
|------|----|---------|-------|--------|
| (audit) | PENDING | Audit completes | Any verdict | Enter rollout |
| PENDING | DEPLOYED | Audit = PASS | PASS verdict | Apply changes |
| PENDING | ROLLED_BACK | Audit = FAIL | FAIL verdict | Execute rollback |
| PENDING | ESCALATED | Audit = INCONCLUSIVE | Inconclusive | Human escalation |
| DEPLOYED | VERIFIED | Health confirmed | Health stable | Complete rollout |
| ROLLED_BACK | INCIDENT | Rollback done | Always | Create incident |

---

## Hand-off Points

### Contract → Job

```yaml
hand_off: CONTRACT_TO_JOB
trigger: Contract enters ACTIVE
guard:
  - contract.status = APPROVED
  - NOW() >= activation_window_start
action:
  - Create GovernanceJob
  - Job.contract_id = contract.contract_id
  - Contract.status = ACTIVE
```

### Job → Audit

```yaml
hand_off: JOB_TO_AUDIT
trigger: Job enters COMPLETED
guard:
  - job.status = COMPLETED
  - All steps finished
action:
  - Create GovernanceAudit
  - Audit.job_id = job.job_id
  - Job.status = AUDIT_PENDING
```

### Audit → Contract

```yaml
hand_off: AUDIT_TO_CONTRACT
trigger: Audit verdict produced
guard:
  - audit.verdict IN (PASS, FAIL)
action:
  - If PASS: Contract.status = COMPLETED
  - If FAIL: Contract.status = FAILED
```

### Audit → Rollout

```yaml
hand_off: AUDIT_TO_ROLLOUT
trigger: Audit complete
guard:
  - audit.verdict produced
action:
  - If PASS: Initiate deployment
  - If FAIL: Initiate rollback
  - If INCONCLUSIVE: Escalate to human
```

---

## Terminal States

### Success Path

```
DRAFT → VALIDATED → ELIGIBLE → APPROVED → ACTIVE → COMPLETED (AUDITED:PASS)
```

Final state: **Contract.COMPLETED**, **Job.COMPLETED**, **Audit.PASS**

### Failure Path

```
DRAFT → VALIDATED → ELIGIBLE → APPROVED → ACTIVE → FAILED → ROLLED_BACK
```

Final state: **Contract.FAILED**, **Job.ROLLED_BACK**, **Audit.FAIL**

### Early Termination Paths

```
DRAFT → EXPIRED
DRAFT → VALIDATED → REJECTED (ineligible)
DRAFT → VALIDATED → ELIGIBLE → REJECTED (founder denied)
DRAFT → VALIDATED → ELIGIBLE → EXPIRED (review timeout)
```

---

## Cross-Machine Invariants

| ID | Invariant | Machines | Enforcement |
|----|-----------|----------|-------------|
| SM-001 | Job only exists for ACTIVE contract | Contract, Job | FK + state check |
| SM-002 | Audit only exists for COMPLETED job | Job, Audit | FK + state check |
| SM-003 | Contract COMPLETED requires Audit PASS | Contract, Audit | State check |
| SM-004 | Contract FAILED requires Rollback | Contract, Job | State machine |
| SM-005 | Rollout requires Audit verdict | Audit, Rollout | State check |
| SM-006 | No parallel jobs for same contract | Job | Unique constraint |

---

## Health Authority

**Health evaluates; contracts do not override.**

At every transition point, health may block:

```python
def check_health_gate(transition):
    health = platform_health_service.get_system_health()

    if health.status == "UNHEALTHY":
        raise HealthBlockException("System unhealthy")

    if affected_capability in health.unhealthy_capabilities:
        raise HealthBlockException(f"Capability unhealthy")
```

---

## Monitoring Points

| Point | Metric | Alert Threshold |
|-------|--------|-----------------|
| Contract queue depth | contracts_pending | > 100 |
| Validation latency | validator_duration_ms | > 5000ms |
| Review aging | contracts_awaiting_review | age > 3 days |
| Job execution time | job_duration_ms | > 60000ms |
| Audit latency | audit_duration_ms | > 30000ms |
| Rollback rate | rollbacks_per_hour | > 5 |

---

## Attestation

This specification defines the complete end-to-end state machine.
All four sub-machines must remain synchronized.
Hand-off points are mandatory checkpoints.
Health authority applies at all transitions.
