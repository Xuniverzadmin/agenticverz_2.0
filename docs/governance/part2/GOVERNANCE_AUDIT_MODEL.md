# Governance Audit Model Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** GOVERNANCE_JOB_MODEL.md
**Layer:** L8 Verification

---

## Purpose

The **Governance Auditor** verifies that job execution matched contract intent.

Audit is:
- **Post-execution** (runs after job completes)
- **Deterministic** (same job → same verdict)
- **Authoritative** (verdicts cannot be overridden)
- **Mandatory** (no rollout without audit)

---

## Audit Lifecycle

```
Job COMPLETED → AUDIT_PENDING → Auditor runs → AUDITED
                                     ↓
                              ┌──────┴──────┐
                              ↓             ↓
                           PASS          FAIL/INCONCLUSIVE
                              ↓             ↓
                          ROLLOUT       BLOCKED
```

---

## Audit Schema

```yaml
# governance_audits table
audit_id: UUID (PK)
job_id: UUID (FK → governance_jobs)
contract_id: UUID (FK → system_contracts)

# Verdict
verdict: ENUM(PENDING, PASS, FAIL, INCONCLUSIVE)
verdict_reason: TEXT
verdict_at: TIMESTAMP

# Checks
checks_performed: JSONB[]  # Array of check results
checks_passed: INTEGER
checks_failed: INTEGER
checks_inconclusive: INTEGER

# Evidence
evidence: JSONB  # Supporting data for verdict
health_snapshot_before: JSONB
health_snapshot_after: JSONB

# Metadata
auditor_version: TEXT
duration_ms: INTEGER
created_at: TIMESTAMP DEFAULT NOW()
```

---

## Audit Checks

### Check A-001: Scope Compliance

```yaml
check: A-001
name: Scope Compliance
question: Did job execute only within contract scope?
method: |
  Compare job steps against contract.affected_capabilities
  Verify no unauthorized targets
pass: All steps within scope
fail: Step targeted unauthorized capability
```

### Check A-002: Health Preservation

```yaml
check: A-002
name: Health Preservation
question: Did execution preserve system health?
method: |
  Compare health_snapshot_before vs health_snapshot_after
  Verify no health degradation
pass: Health maintained or improved
fail: Health degraded
inconclusive: Health service unavailable
```

### Check A-003: Execution Fidelity

```yaml
check: A-003
name: Execution Fidelity
question: Did execution match proposed changes?
method: |
  Compare job results against contract.proposed_changes
  Verify intended mutations occurred
pass: Results match proposal
fail: Results diverge from proposal
```

### Check A-004: Timing Compliance

```yaml
check: A-004
name: Timing Compliance
question: Did execution occur within activation window?
method: |
  Verify job.started_at >= contract.activation_window_start
  Verify job.completed_at <= contract.activation_window_end
pass: Execution within window
fail: Execution outside window
```

### Check A-005: Rollback Availability

```yaml
check: A-005
name: Rollback Availability
question: Can this execution be rolled back if needed?
method: |
  Verify all completed steps have rollback_action defined
  Verify rollback actions are valid
pass: Full rollback path available
fail: Incomplete rollback path
inconclusive: Some steps have no rollback (by design)
```

### Check A-006: Signal Consistency

```yaml
check: A-006
name: Signal Consistency
question: Are governance signals consistent post-execution?
method: |
  Query governance_signals for affected scope
  Verify no conflicting signals
pass: Signals consistent
fail: Conflicting signals detected
```

### Check A-007: No Unauthorized Mutations

```yaml
check: A-007
name: No Unauthorized Mutations
question: Were there any mutations outside job context?
method: |
  Compare system state before/after excluding expected changes
  Detect any unexpected mutations
pass: No unauthorized mutations
fail: Unauthorized mutations detected
```

---

## Verdict Logic

```python
def determine_verdict(checks: list[CheckResult]) -> AuditVerdict:
    failed = [c for c in checks if c.result == FAIL]
    inconclusive = [c for c in checks if c.result == INCONCLUSIVE]

    # Any failure → FAIL
    if failed:
        return AuditVerdict(
            verdict=FAIL,
            reason=f"Failed checks: {[c.name for c in failed]}"
        )

    # Any inconclusive → INCONCLUSIVE
    if inconclusive:
        return AuditVerdict(
            verdict=INCONCLUSIVE,
            reason=f"Inconclusive checks: {[c.name for c in inconclusive]}"
        )

    # All pass → PASS
    return AuditVerdict(
        verdict=PASS,
        reason="All checks passed"
    )
```

---

## Verdict Semantics

### PASS

> Execution was correct. Contract may proceed to COMPLETED.
> Rollout is authorized.

**Consequences:**
- Contract → COMPLETED
- Capability states finalized
- Audit trail preserved

### FAIL

> Execution violated contract or governance rules.
> Rollback is required.

**Consequences:**
- Contract → FAILED
- Rollback job created
- Incident created
- Human notification

### INCONCLUSIVE

> Cannot determine if execution was correct.
> Human review required.

**Consequences:**
- Contract remains in AUDIT_PENDING
- Human escalation triggered
- No automatic rollout or rollback

---

## Health Snapshots

Audit captures health state before and after:

```yaml
health_snapshot:
  captured_at: TIMESTAMP
  system_health: ENUM
  capability_health:
    - capability: TEXT
      status: ENUM
      lifecycle: ENUM
      qualifier: ENUM
  active_signals:
    - signal_type: TEXT
      scope: TEXT
      decision: TEXT
```

---

## Evidence Collection

Auditor collects evidence for traceability:

```yaml
evidence:
  job_execution_log: JSONB  # Step-by-step log
  state_before: JSONB       # Relevant state before
  state_after: JSONB        # Relevant state after
  signal_history: JSONB     # Signals during execution
  health_timeline: JSONB    # Health changes
  anomalies_detected: TEXT[] # Any anomalies
```

---

## Audit Boundaries

### What Auditor MAY Do

- Read job execution records
- Read contract details
- Read governance signals
- Read health status
- Produce verdicts

### What Auditor MUST NOT Do

- Modify job records
- Modify contract state
- Create/modify signals
- Trigger rollback directly
- Approve anything

---

## Audit Timing

```yaml
audit_timing:
  trigger: job.status = COMPLETED
  timeout: 5 minutes
  retry_on_inconclusive: 1 (max retries)
  escalation_delay: 10 minutes
```

If audit doesn't complete:
- Contract remains AUDIT_PENDING
- Human escalation triggered
- No timeout-based approval

---

## Audit Finality

**Audit verdicts are final.**

- PASS cannot be revoked
- FAIL cannot be overridden
- INCONCLUSIVE requires human resolution

Humans may:
- Resolve INCONCLUSIVE (by providing additional context)
- Acknowledge FAIL (but not overturn)

Humans may NOT:
- Override FAIL to PASS
- Bypass audit entirely
- Approve without audit

---

## Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| AUDIT-001 | All completed jobs require audit | State machine |
| AUDIT-002 | PASS required for COMPLETED | Contract state check |
| AUDIT-003 | FAIL triggers rollback | Job state machine |
| AUDIT-004 | Verdicts are immutable | DB constraint |
| AUDIT-005 | Evidence is preserved | Audit record |
| AUDIT-006 | Health snapshots required | Audit schema |

---

## API Surface

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/audits/{job_id}` | GET | Get audit for job |
| `/api/v1/audits/{id}/checks` | GET | Get check details |
| `/api/v1/audits/{id}/evidence` | GET | Get evidence |
| `/api/v1/audits/{id}/resolve` | POST | Resolve INCONCLUSIVE (human) |

**No CREATE endpoint.** Audits are created automatically by job completion.

---

## Attestation

This specification defines the Governance Audit model.
Audit is mandatory for all contract executions.
No rollout proceeds without PASS verdict.
Audit finality protects governance integrity.
