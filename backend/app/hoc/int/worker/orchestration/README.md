# Run Orchestration Module

**Layer:** L5 — Execution & Workers
**Reference:** PIN-454 (Cross-Domain Orchestration Audit), Section 8.1

## Overview

The Run Orchestration module provides the **Run Orchestration Kernel (ROK)** — the single authority for run lifecycle management. ROK coordinates phase transitions, audit expectations, and governance checks across domains.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Run Orchestration Kernel (ROK)                │
│                         L5: Execution                            │
├──────────────────────────────────────────────────────────────────┤
│  STATE MACHINE:                                                  │
│  CREATED → AUTHORIZED → EXECUTING → GOVERNANCE_CHECK             │
│                                    → FINALIZING → COMPLETED/FAILED│
│                                                                  │
│  DOMAIN COORDINATION (via L4 Facades):                           │
│  ├─ IncidentFacade    → incident creation                        │
│  ├─ GovernanceFacade  → policy evaluation, lessons               │
│  └─ TraceFacade       → observability                            │
│                                                                  │
│  INVARIANTS:                                                     │
│  • Every run transition emits AuditExpectation                   │
│  • GOVERNANCE_CHECK is mandatory before FINALIZING               │
│  • No direct engine calls — facades only                         │
│  • run_id is the correlation key across all domains              │
└──────────────────────────────────────────────────────────────────┘
```

## Components

### phases.py

Defines the phase state machine:

- **RunPhase** — Enum of run phases (CREATED, AUTHORIZED, EXECUTING, GOVERNANCE_CHECK, FINALIZING, COMPLETED, FAILED)
- **PhaseTransition** — Immutable record of a phase transition
- **PhaseContext** — Context for current phase including governance check results
- **PhaseStateMachine** — Enforces valid transitions and records history
- **VALID_TRANSITIONS** — Maps which transitions are allowed

### run_orchestration_kernel.py

The main ROK class:

- **RunOrchestrationKernel** — Single authority for run lifecycle
  - `declare_expectations()` — Declares audit expectations at T0
  - `authorize()` — Transitions to AUTHORIZED phase
  - `begin_execution()` — Transitions to EXECUTING phase
  - `execution_complete()` — Transitions to GOVERNANCE_CHECK phase
  - `governance_check()` — Reconciles expectations vs acknowledgments
  - `begin_finalization()` — Transitions to FINALIZING phase
  - `finalize()` — Terminal operation, emits finalize_run ack
  - `fail()` — Fail from any non-terminal phase

- **create_rok()** — Factory function for creating ROK instances

## Usage

```python
from app.hoc.int.worker.orchestration import create_rok, RunPhase

# Create ROK instance
kernel = create_rok(run_id)

# Declare expectations at T0 (run start)
kernel.declare_expectations()

# Execute through phases
if kernel.authorize():
    kernel.begin_execution()

    # ... runner executes skills ...

    kernel.execution_complete(success=True)
    kernel.governance_check()
    kernel.begin_finalization()
    kernel.finalize()
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ROK_ENABLED` | `true` | Enable/disable ROK integration |
| `RAC_ENABLED` | `true` | Enable/disable Runtime Audit Contract |
| `ROK_GOVERNANCE_TIMEOUT_MS` | `5000` | Timeout for governance checks |
| `ROK_DEFAULT_RUN_TIMEOUT_MS` | `30000` | Default run timeout for deadline calculation |
| `ROK_GRACE_PERIOD_MS` | `5000` | Grace period for audit reconciliation |

## Phase Transitions

```
CREATED ─────────────────────────► AUTHORIZED ─────► EXECUTING
    │                                    │                │
    │                                    │                │
    └─► FAILED ◄─────────────────────────┴────────────────┤
                                                          │
                                                          ▼
                                               GOVERNANCE_CHECK
                                                          │
                                    FAILED ◄──────────────┤
                                       ▲                  │
                                       │                  ▼
                                       └────────── FINALIZING
                                                          │
                                                          ▼
                                                     COMPLETED
```

### Transition Rules

- CREATED → AUTHORIZED: Authorization granted
- CREATED → FAILED: Authorization denied or system error
- AUTHORIZED → EXECUTING: Worker claims run
- AUTHORIZED → FAILED: System error
- EXECUTING → GOVERNANCE_CHECK: Execution complete (success or failure)
- EXECUTING → FAILED: Critical execution error
- GOVERNANCE_CHECK → FINALIZING: All governance checks passed
- GOVERNANCE_CHECK → FAILED: Governance timeout or missing acks (strict mode)
- FINALIZING → COMPLETED: DB commit + events published
- FINALIZING → FAILED: Commit or event publish error

## Governance Check

During GOVERNANCE_CHECK phase, ROK reconciles:

1. **Expected operations** (declared at T0):
   - INCIDENTS / create_incident
   - POLICIES / evaluate_policy
   - LOGS / start_trace
   - ORCHESTRATOR / finalize_run

2. **Received acknowledgments** (from domain facades):
   - IncidentFacade emits INCIDENTS/create_incident ack
   - GovernanceFacade emits POLICIES/evaluate_policy ack
   - TraceFacade emits LOGS/start_trace ack
   - ROK emits ORCHESTRATOR/finalize_run ack

3. **Reconciliation result**:
   - `missing = expected - acked` (operations not performed)
   - `drift = acked - expected` (unexpected operations)
   - `is_clean = (missing == 0) && (drift == 0)`

## Integration with WorkerPool

WorkerPool uses ROK for lifecycle management in `_execute_run()`:

```python
def _execute_run(self, run_id: str):
    rok = None
    success = False
    error = None

    try:
        if ROK_ENABLED:
            rok = create_rok(run_id)
            rok.declare_expectations()  # T0

        runner = RunRunner(run_id=run_id, publisher=self.publisher)
        runner.run()
        success = True

    except Exception as e:
        error = str(e)
        raise

    finally:
        if rok is not None:
            rok.finalize(success=success, error=error)
```

## Layer Compliance

- **Layer:** L5 (Execution & Workers)
- **Allowed Imports:** L4 (via facades only), L6
- **Forbidden Imports:** L1, L2, L3, L4 engines directly
- **Callers:** WorkerPool (L5), RunRunner (L5)

## Related Documentation

- `docs/architecture/CROSS_DOMAIN_ORCHESTRATION_AUDIT.md` — Full audit document
- `backend/app/services/audit/README.md` — RAC module documentation
- `backend/app/services/observability/README.md` — TraceFacade documentation
