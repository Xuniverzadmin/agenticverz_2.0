# PIN-456: PIN-454 Phase 3: Run Orchestration Kernel (ROK) Implementation

**Status:** ✅ COMPLETE
**Created:** 2026-01-20
**Category:** Architecture / Cross-Domain Orchestration
**Milestone:** PIN-454 Phase 3

---

## Summary

Implemented Run Orchestration Kernel (ROK) as the single authority for run lifecycle management, including phase state machine, expectation declaration, governance checkpoint, and WorkerPool integration.

---

## Details

## Overview

Phase 3 of PIN-454 Cross-Domain Orchestration Audit implements the Run Orchestration Kernel (ROK), the single authority for run lifecycle management at L5.

## Deliverables

### 1. Phase State Machine (`phases.py`)

- **RunPhase** enum: CREATED → AUTHORIZED → EXECUTING → GOVERNANCE_CHECK → FINALIZING → COMPLETED/FAILED
- **PhaseStateMachine** class: Enforces valid transitions, records history
- **PhaseContext** dataclass: Tracks governance check status (incident_created, policy_evaluated, trace_completed)
- **VALID_TRANSITIONS** mapping: Defines allowed phase transitions

### 2. Run Orchestration Kernel (`run_orchestration_kernel.py`)

- **RunOrchestrationKernel** class with lifecycle methods:
  - `declare_expectations()` — T0 expectation declaration using RAC
  - `authorize()` — Transition to AUTHORIZED phase
  - `begin_execution()` — Transition to EXECUTING phase
  - `execution_complete()` — Transition to GOVERNANCE_CHECK phase
  - `governance_check()` — Reconcile expectations vs acknowledgments
  - `begin_finalization()` — Transition to FINALIZING phase
  - `finalize()` — Terminal operation, emits finalize_run ack
  - `fail()` — Fail from any non-terminal phase
- **create_rok()** factory function

### 3. WorkerPool Integration (`pool.py`)

- Added ROK_ENABLED flag (default: true)
- Updated `_execute_run()` to use ROK:
  - Create ROK at dispatch time
  - Declare expectations at T0
  - Finalize ROK after run completion (success or failure)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| ROK_ENABLED | true | Enable/disable ROK |
| RAC_ENABLED | true | Enable/disable RAC |
| ROK_GOVERNANCE_TIMEOUT_MS | 5000 | Governance check timeout |
| ROK_DEFAULT_RUN_TIMEOUT_MS | 30000 | Default run timeout |
| ROK_GRACE_PERIOD_MS | 5000 | Grace period for audit |

## Files Created

- `backend/app/worker/orchestration/__init__.py`
- `backend/app/worker/orchestration/phases.py`
- `backend/app/worker/orchestration/run_orchestration_kernel.py`
- `backend/app/worker/orchestration/README.md`

## Files Modified

- `backend/app/worker/pool.py` — ROK integration

## Verification

- BLCA: 0 violations, 1003 files scanned
- All layer compliance rules satisfied

## Next Steps

- Phase 4: RunRunner integration (full ROK lifecycle in runner)
- Phase 5: Integration testing

---

## Related PINs

- [PIN-454](PIN-454-.md)
- [PIN-455](PIN-455-.md)
