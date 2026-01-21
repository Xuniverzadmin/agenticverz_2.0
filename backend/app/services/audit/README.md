# Runtime Audit Contract (RAC) Module

**Layer:** L4 — Domain Engine
**Reference:** PIN-454 (Cross-Domain Orchestration Audit)
**Status:** IMPLEMENTED (Phase 2)

---

## Overview

The Runtime Audit Contract (RAC) module provides audit infrastructure for cross-domain operations during run execution. It ensures that all expected actions are tracked and reconciled.

## Problem Solved

Without RAC, cross-domain operations can fail silently:
- Incident creation fails → run "succeeds" but incident is missing
- Policy evaluation fails → no policy record exists
- Trace creation fails → run executes in "dark mode" without observability

RAC provides:
1. **Expectations** — What MUST happen during a run
2. **Acknowledgments** — What actually happened
3. **Reconciliation** — Comparison of expected vs actual

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               Runtime Audit Contract (RAC)                        │
│                      L4: Domain Logic                             │
├──────────────────────────────────────────────────────────────────┤
│  EXPECTATION MODEL:                                               │
│                                                                   │
│  At run start (T0), declare what MUST happen:                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ AuditExpectation                                             │ │
│  │   run_id: uuid                                               │ │
│  │   domain: "incidents" | "policies" | "logs" | "orchestrator" │ │
│  │   action: "create_incident" | "evaluate_policy" | ...        │ │
│  │   status: PENDING | ACKED | MISSING | FAILED                 │ │
│  │   deadline_ms: 5000                                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ACKNOWLEDGMENT MODEL:                                            │
│                                                                   │
│  Each domain reports completion:                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ DomainAck                                                    │ │
│  │   run_id: uuid                                               │ │
│  │   domain: "incidents"                                        │ │
│  │   action: "create_incident"                                  │ │
│  │   result_id: uuid | null                                     │ │
│  │   error: string | null                                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  RECONCILIATION:                                                  │
│  • expected − acked → missing_actions (audit alert)               │
│  • acked − expected → drift_actions (unexpected behavior)         │
│  • missing finalization → stale_run (liveness violation)          │
└──────────────────────────────────────────────────────────────────┘
```

## Components

### models.py

Core data models for the audit system:

- `AuditExpectation` — Declares what action MUST happen for a run
- `DomainAck` — Reports that an action has completed
- `ReconciliationResult` — Result of comparing expectations vs acks
- `AuditStatus` — PENDING, ACKED, MISSING, FAILED
- `AuditDomain` — INCIDENTS, POLICIES, LOGS, ORCHESTRATOR
- `AuditAction` — CREATE_INCIDENT, EVALUATE_POLICY, START_TRACE, etc.

### store.py

Thread-safe storage for expectations and acknowledgments:

- In-memory dictionary (fast, per-process)
- Optional Redis backing (for cross-process coordination)
- 1-hour TTL for Redis keys (runs should complete within this time)

### reconciler.py

Four-way validation of expectations vs acknowledgments:

1. `expected − acked → missing` (audit alert)
2. `acked − expected → drift` (unexpected action)
3. `missing finalization → stale run` (liveness violation)
4. `expectations without deadline → invalid contract`

## Usage

### Creating Expectations (at T0)

```python
from app.services.audit.models import create_run_expectations
from app.services.audit.store import get_audit_store

# At run creation (T0)
expectations = create_run_expectations(
    run_id=run_id,
    run_timeout_ms=30000,
    grace_period_ms=5000,
)

store = get_audit_store()
store.add_expectations(run_id, expectations)
```

### Emitting Acknowledgments (facades)

Facades emit acks after domain operations. This is handled automatically by:
- `IncidentFacade.create_incident_for_run()` → emits INCIDENTS/CREATE_INCIDENT ack
- `RunGovernanceFacade.create_policy_evaluation()` → emits POLICIES/EVALUATE_POLICY ack
- `TraceFacade.start_trace()` → emits LOGS/START_TRACE ack

### Reconciliation

```python
from app.services.audit.reconciler import get_audit_reconciler

reconciler = get_audit_reconciler()
result = reconciler.reconcile(run_id)

if not result.is_clean:
    if result.has_missing:
        # Handle missing actions
        alert_missing_actions(result.missing_actions)
    if result.has_drift:
        # Handle unexpected actions
        investigate_drift(result.drift_actions)
    if result.stale_run:
        # Handle stale run
        alert_stale_run(run_id)
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `RAC_ENABLED` | `true` | Enable RAC ack emission |
| `AUDIT_REDIS_ENABLED` | `false` | Enable Redis backing for cross-process coordination |

## Metrics (Prometheus)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `rac_reconciliation_total` | Counter | status | Total reconciliations performed |
| `rac_missing_actions_total` | Counter | domain, action | Total missing actions detected |
| `rac_drift_actions_total` | Counter | domain, action | Total drift actions detected |
| `rac_stale_runs_total` | Counter | — | Total stale runs detected |
| `rac_reconciliation_duration_seconds` | Histogram | — | Time spent reconciling |

## Domain Mapping

| Domain | Action | Emitting Facade |
|--------|--------|-----------------|
| `incidents` | `create_incident` | IncidentFacade |
| `policies` | `evaluate_policy` | RunGovernanceFacade |
| `logs` | `start_trace` | TraceFacade |
| `logs` | `complete_trace` | TraceFacade |
| `orchestrator` | `finalize_run` | ROK (Phase 3) |

## Files

| File | Role |
|------|------|
| `__init__.py` | Module exports |
| `models.py` | AuditExpectation, DomainAck, ReconciliationResult |
| `store.py` | AuditStore (in-memory + Redis) |
| `reconciler.py` | AuditReconciler (four-way validation) |

## Related Documents

- `docs/architecture/CROSS_DOMAIN_ORCHESTRATION_AUDIT.md` — Full audit and implementation plan
- PIN-454 — Cross-Domain Orchestration Audit PIN
- `docs/memory-pins/PIN-455-phase-2-rac-infrastructure.md` — Phase 2 completion PIN
