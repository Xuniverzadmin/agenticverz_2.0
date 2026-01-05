# PIN-294: Part-2 Job Executor - Machine Execution Layer

**Status:** COMPLETE
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Implemented the Job Executor (L5) - a **pure machine** that executes governance job steps in order and emits evidence. This is "just physics" - it runs the plan and records what happened.

---

## Key Design Decisions

### 1. Executor is a Machine, Not a Brain

The Job Executor is intentionally simple:
- **Execute**: Run steps in declared order
- **Record**: Emit evidence per step
- **Stop**: Halt on first failure

That's it. No decisions. No retries. No interpretation.

```
JobStep[] ──► EXECUTOR ──► StepResult[]
                        └──► ExecutionResult
```

### 2. Six Core Invariants (EXEC-001 to EXEC-006)

| ID | Invariant | Description |
|----|-----------|-------------|
| EXEC-001 | Execute in order | Steps execute in declared order |
| EXEC-002 | Evidence per step | Each step produces a StepResult |
| EXEC-003 | Stop on failure | First failure halts execution |
| EXEC-004 | Health observed | Health is read-only, never modified |
| EXEC-005 | No contract mutation | Cannot modify eligibility or contracts |
| EXEC-006 | No retry logic | Failed = done |

### 3. Protocol-Based Dependency Injection

The Executor uses protocols (interfaces) for dependencies:

```python
class HealthObserver(Protocol):
    """Read-only health observation."""
    def observe_health(self) -> dict[str, Any]: ...

class StepHandler(Protocol):
    """Executes a specific step type."""
    def execute(self, step: JobStep, context: ExecutionContext) -> StepOutput: ...
```

This allows:
- Testing with mock handlers
- Production handlers injected at runtime
- No hardcoded dependencies

### 4. L5 Layer Placement

The Job Executor is placed at L5 (Execution & Workers):

| Layer | Component | Relationship |
|-------|-----------|--------------|
| L4 | GovernanceOrchestrator | Creates jobs, dispatches to L5 |
| L5 | **JobExecutor** | Executes steps, emits evidence |
| L6 | PlatformHealthService | Source for health observations |

L5 may only import from L6. It is forbidden from importing L1-L4.

---

## What the Executor IS

| Property | Description |
|----------|-------------|
| Plan Consumer | Executes JobSteps as declared |
| Evidence Emitter | Records output per step |
| Failure-Stop | Stops immediately on step failure |
| Health Observer | Captures health state (read-only) |

## What the Executor IS NOT

| Property | Description |
|----------|-------------|
| Decider | Does not interpret or classify |
| Retry Engine | Failed means done |
| Policy Interpreter | No severity or priority logic |
| Health Controller | Cannot modify health signals |
| Smart System | Just executes and records |

---

## Components Implemented

### 1. L5 Job Executor Service

`backend/app/services/governance/job_executor.py` (~400 lines)

**Data Types:**
- `StepOutput` - Raw output from step handler
- `ExecutionContext` - Context passed to handlers
- `ExecutionResult` - Final result of job execution

**Protocols:**
- `HealthObserver` - Read-only health observation
- `StepHandler` - Step type execution

**Main Class:**
- `JobExecutor` - Executes job steps in order

**Default Handlers:**
- `NoOpHandler` - Always succeeds (testing)
- `FailingHandler` - Always fails (testing)

**Factory:**
- `create_default_executor()` - Creates executor with default handlers

**Helper:**
- `execution_result_to_evidence()` - Converts result to audit format

### 2. Invariant Tests

`backend/tests/governance/test_executor_invariants.py` (~700 lines)

33 tests covering:
- EXEC-001: Steps execute in declared order
- EXEC-002: Evidence emitted per step
- EXEC-003: Stop on first failure
- EXEC-004: Health observed, never modified
- EXEC-005: No contract mutation
- EXEC-006: No retry logic

---

## Invariants Implemented

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| EXEC-001 | Execute steps in order | Loop in `execute_job()` |
| EXEC-002 | Evidence per step | `StepResult` appended per step |
| EXEC-003 | Stop on failure | `break` on first `FAILED` step |
| EXEC-004 | Health observed only | `HealthObserver` protocol (read-only) |
| EXEC-005 | No contract mutation | L5 cannot import L4 |
| EXEC-006 | No retry logic | No retry in executor code |

---

## Files Created

```
backend/app/services/governance/job_executor.py (~400 lines)
  - L5 Job Executor service
  - Data types: StepOutput, ExecutionContext, ExecutionResult
  - Protocols: HealthObserver, StepHandler
  - Class: JobExecutor
  - Handlers: NoOpHandler, FailingHandler
  - Factory: create_default_executor()
  - Helper: execution_result_to_evidence()

backend/tests/governance/test_executor_invariants.py (~700 lines)
  - 33 invariant tests
  - EXEC-001 to EXEC-006 coverage
  - Handler tests
  - Integration tests
```

**Updated:**
```
backend/app/services/governance/__init__.py (added exports)
```

**Total:** ~1,100 lines (implementation + tests)

---

## Test Coverage

33 invariant tests covering:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestEXEC001ExecutionOrder | 4 | Steps in declared order |
| TestEXEC002EvidenceEmission | 5 | Evidence per step |
| TestEXEC003StopOnFailure | 4 | Failure halts execution |
| TestEXEC004HealthObservation | 4 | Health read-only |
| TestEXEC005NoContractMutation | 3 | No contract changes |
| TestEXEC006NoRetryLogic | 3 | No retries |
| TestStepHandlers | 4 | Handler mechanics |
| TestExecutorMetadata | 3 | Version, properties |
| TestExecutorIntegration | 3 | Full execution flow |

All 33 tests passing.

---

## Combined Governance Tests

```
244 tests passing (31 validator + 48 eligibility + 43 contract + 51 orchestrator + 38 founder review + 33 executor)
```

---

## Execution Flow

```
execute_job(job_id, contract_id, steps, health_observer)
    │
    ├── Observe health before (EXEC-004)
    │
    ├── For each step (EXEC-001):
    │   │
    │   ├── Create ExecutionContext
    │   │
    │   ├── Find handler for step_type
    │   │
    │   ├── Execute handler
    │   │
    │   ├── Create StepResult (EXEC-002)
    │   │
    │   ├── If failed: stop (EXEC-003)
    │   │
    │   └── Observe health after step
    │
    └── Return ExecutionResult
```

---

## Handler Registration

```python
# Create executor with default handlers
executor = create_default_executor()

# Or create custom executor
executor = JobExecutor()
executor.register_handler("capability_enable", EnableHandler())
executor.register_handler("capability_disable", DisableHandler())
```

Default handlers are no-ops for testing. Production handlers should be registered separately.

---

## Evidence Format

The executor emits evidence in this format (via `execution_result_to_evidence`):

```json
{
  "job_id": "uuid",
  "final_status": "COMPLETED",
  "final_reason": "All steps completed successfully",
  "execution_summary": {
    "steps_executed": 3,
    "steps_succeeded": 3,
    "steps_failed": 0
  },
  "step_results": [
    {
      "step_index": 0,
      "status": "COMPLETED",
      "started_at": "2026-01-04T...",
      "completed_at": "2026-01-04T...",
      "output": {...},
      "error": null
    }
  ],
  "health_observations": {
    "before": {...},
    "after": {...}
  },
  "timing": {
    "started_at": "2026-01-04T...",
    "completed_at": "2026-01-04T...",
    "duration_seconds": 0.123
  },
  "executor_version": "1.0.0"
}
```

---

## Authority Chain (Updated)

```
CRM Event (no authority)
    ↓
Validator (machine, advisory) [PIN-288]
    ↓
Eligibility (machine, deterministic gate) [PIN-289]
    ↓
Contract (machine, state authority) [PIN-291]
    ↓
Founder Review (human, approval authority) [PIN-293]
    ↓
Governance Orchestrator (machine, coordination) [PIN-292]
    ↓
Job Executor (machine, execution authority) [PIN-294] ← THIS PIN
    ↓
Health Service (machine, truth authority) ← NEXT
    ↓
Auditor (machine, verification authority)
```

---

## Next Step

With Job Executor implemented, the execution layer is complete. Proceed to:
- **Audit Wiring** (connect executor output to audit system)

Implementation order from here:
1. ~~Validator (pure analysis)~~ DONE (PIN-288)
2. ~~Eligibility engine (pure rules)~~ DONE (PIN-289)
3. ~~Contract model (stateful)~~ DONE (PIN-291)
4. ~~Governance services~~ DONE (PIN-292)
5. ~~Founder review surface~~ DONE (PIN-293)
6. ~~Job execution~~ DONE (PIN-294)
7. Audit wiring <- NEXT
8. Rollout projection

---

## API Reference

### JobExecutor.execute_job()

```python
def execute_job(
    self,
    job_id: UUID,
    contract_id: UUID,
    steps: list[JobStep],
    health_observer: Optional[HealthObserver] = None,
    executed_by: str = "executor",
) -> ExecutionResult:
    """
    Execute a job's steps in order.

    EXEC-001: Steps execute in declared order
    EXEC-002: Evidence emitted per step
    EXEC-003: Stop on first failure
    EXEC-004: Health observed, never modified
    """
```

### StepHandler Protocol

```python
class StepHandler(Protocol):
    def execute(
        self,
        step: JobStep,
        context: ExecutionContext,
    ) -> StepOutput:
        """Execute a single step."""
        ...
```

### HealthObserver Protocol

```python
class HealthObserver(Protocol):
    def observe_health(self) -> dict[str, Any]:
        """Capture current health state (read-only)."""
        ...
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
- PIN-293: Founder Review
- PART2_CRM_WORKFLOW_CHARTER.md

---

## Related PINs

- [PIN-288](PIN-288-part-2-validator-service---pure-analysis-implementation.md)
- [PIN-289](PIN-289-part-2-eligibility-engine---pure-rules-implementation.md)
- [PIN-291](PIN-291-part-2-contract-model---first-stateful-governance-component.md)
- [PIN-292](PIN-292-part-2-governance-services---workflow-orchestration.md)
- [PIN-293](PIN-293-part-2-founder-review---last-human-authority-gate.md)
