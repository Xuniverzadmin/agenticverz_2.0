# PIN-454: Cross-Domain Orchestration Audit — Implementation Plan Approved

**Status:** ✅ PLAN APPROVED
**Created:** 2026-01-20
**Updated:** 2026-01-20
**Category:** Architecture / Orchestration

---

## Summary

Systems architect audit of cross-domain orchestration (Activity, Policies, Incidents, Logs). Identified 5 critical gaps. Two major architectural proposals (ROK, RAC) validated and APPROVED. 5-phase implementation plan created.

---

## Audit Findings

### Execution Model
- **Trigger:** Polling-based worker pool (2s interval)
- **Execution:** Sync-over-async in ThreadPoolExecutor
- **Cross-Domain:** All calls are sync but fail-soft (errors logged, not propagated)

### Critical Gaps Identified

| ID | Gap | Risk |
|----|-----|------|
| G-001 | No policy re-evaluation during execution | HIGH |
| G-002 | Incident creation failure is silent | HIGH |
| G-003 | Trace failure runs in 'dark mode' | HIGH |
| G-004 | No event subscribers in backend | MEDIUM |
| G-005 | L5→L4 layer violations | MEDIUM |

---

## Approved Proposals

### Run Orchestration Kernel (ROK) — APPROVED

Single authority for run lifecycle with phase state machine:

```
CREATED → AUTHORIZED → EXECUTING → GOVERNANCE_CHECK → FINALIZING → COMPLETED/FAILED
```

**Key Invariants:**
- Every run transition emits AuditExpectation
- GOVERNANCE_CHECK is mandatory before FINALIZING
- No direct engine calls — facades only
- run_id is the correlation key across all domains

### Runtime Audit Contract (RAC) — APPROVED

Expectations declared at run start, reconciled after completion:

```
AuditReconciler
 ├─ expected − acked → missing
 ├─ acked − expected → drift
 └─ missing finalization → stale run
```

**Completeness Guarantees:**
1. **Run Liveness Expectation:** At T0, add `finalize_run` meta-expectation
2. **Unexpected Action Detection:** `acks - expectations = drift_actions`

---

## Implementation Plan (4 weeks)

### Phase 1: Foundation (Week 1)
- GovernanceFacade (FIX-002)
- Observability Guard (FIX-004)
- Runner imports update
- DEGRADED status column

### Phase 2: Audit Infrastructure (Week 2)
- AuditExpectation model
- DomainAck model
- AuditStore (in-memory + Redis)
- AuditReconciler
- Facade ack emission

### Phase 3: ROK (Week 3)
- Phase state machine
- Expectation declaration
- Governance checkpoint
- WorkerPool integration
- finalize_run meta-expectation

### Phase 4: Transaction + Enhancements (Week 4)
- Transaction coordinator (FIX-001)
- EventReactor (FIX-003)
- MidExecutionPolicyChecker (FIX-005)
- Alert handlers

---

## Validation Checkpoints

| Checkpoint | Validation | Blocking? |
|------------|------------|-----------|
| Post-Phase 1 | BLCA clean, no layer violations | YES |
| Post-Phase 2 | Unit tests: reconciler detects missing/drift | YES |
| Post-Phase 3 | Integration test: run lifecycle through ROK | YES |
| Post-Phase 4 | E2E test: partial failure = full rollback | YES |
| Post-Phase 5 | Smoke test: mid-execution policy halt | NO |

---

## Reference

- Document: `docs/architecture/CROSS_DOMAIN_ORCHESTRATION_AUDIT.md`
- Related: PIN-370 (SDSR System Contract), PIN-407 (Success as First-Class Data)

---

## Related PINs

- [PIN-370](PIN-370-.md)
- [PIN-407](PIN-407-.md)
- [PIN-453](PIN-453-policies-domain-topic-rename-thresholds-to-controls.md)
