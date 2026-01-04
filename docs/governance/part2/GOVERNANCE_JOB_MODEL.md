# Governance Job Model Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** SYSTEM_CONTRACT_OBJECT.md
**Layer:** L5 Execution

---

## Purpose

A **Governance Job** is the execution unit for an approved System Contract.

Jobs are:
- **Bounded** (execute within contract scope only)
- **Auditable** (every step recorded)
- **Reversible** (rollback plan required)
- **Health-aware** (cannot override platform health)

---

## Job Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                  GOVERNANCE JOB LIFECYCLE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PENDING ───────► RUNNING ───────► COMPLETED                │
│     │                │                 │                    │
│     │                │                 ▼                    │
│     │                │            AUDIT_PENDING             │
│     │                │                                      │
│     │                ▼                                      │
│     │             FAILED ───────► ROLLBACK_PENDING          │
│     │                │                 │                    │
│     ▼                ▼                 ▼                    │
│  CANCELLED      ROLLED_BACK       ROLLBACK_FAILED           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### State Definitions

| State | Entry Condition | Exit Condition | Terminal? |
|-------|-----------------|----------------|-----------|
| PENDING | Contract activated | Executor picks up | No |
| RUNNING | Execution starts | All steps complete or failure | No |
| COMPLETED | All steps succeed | Audit completes | No |
| FAILED | Any step fails | Rollback initiated | No |
| CANCELLED | Manual cancellation | None | Yes |
| AUDIT_PENDING | Job completed | Audit verdict | No |
| ROLLBACK_PENDING | Failure detected | Rollback completes | No |
| ROLLED_BACK | Rollback succeeds | None | Yes |
| ROLLBACK_FAILED | Rollback fails | Human escalation | Yes |

---

## Job Schema

```yaml
# governance_jobs table
job_id: UUID (PK)
contract_id: UUID (FK → system_contracts)
version: INTEGER (optimistic lock)

# State
status: ENUM(PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, AUDIT_PENDING, ROLLBACK_PENDING, ROLLED_BACK, ROLLBACK_FAILED)
status_reason: TEXT

# Execution
executor_id: TEXT (worker/node identifier)
started_at: TIMESTAMP (nullable)
completed_at: TIMESTAMP (nullable)
duration_ms: INTEGER (nullable)

# Steps
total_steps: INTEGER
completed_steps: INTEGER
current_step: INTEGER
steps: JSONB[]  # Array of step records

# Constraints
max_duration_ms: INTEGER (from contract)
scope_hash: TEXT (for verification)

# Rollback
rollback_job_id: UUID (nullable, FK → governance_jobs)
rollback_reason: TEXT (nullable)

# Audit link
audit_id: UUID (nullable, FK → governance_audits)

# Timestamps
created_at: TIMESTAMP DEFAULT NOW()
updated_at: TIMESTAMP DEFAULT NOW()
```

---

## Job Step Schema

```yaml
JobStep:
  step_number: INTEGER
  step_type: ENUM(capability_enable, capability_disable, config_update, signal_record)
  target: TEXT (capability name or config key)
  parameters: JSONB
  status: ENUM(PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
  started_at: TIMESTAMP (nullable)
  completed_at: TIMESTAMP (nullable)
  result: JSONB (nullable)
  error: TEXT (nullable)
  rollback_action: JSONB (how to undo this step)
```

---

## Execution Model

### Step Execution Order

1. Steps execute in order (step_number ascending)
2. No parallel step execution within a job
3. Failure at any step halts execution
4. Completed steps are recorded before continuing

### Step Execution Flow

```python
async def execute_job(job: GovernanceJob):
    job.status = RUNNING
    job.started_at = now()

    for step in job.steps:
        step.status = RUNNING
        step.started_at = now()

        try:
            result = await execute_step(step)
            step.status = COMPLETED
            step.result = result
            job.completed_steps += 1
        except Exception as e:
            step.status = FAILED
            step.error = str(e)
            job.status = FAILED
            job.status_reason = f"Step {step.step_number} failed: {e}"
            await initiate_rollback(job)
            return

        step.completed_at = now()

    job.status = COMPLETED
    job.completed_at = now()
    job.duration_ms = (job.completed_at - job.started_at).total_milliseconds()
```

---

## Step Types

### capability_enable

```yaml
step_type: capability_enable
target: "LOGS_LIST"
parameters:
  target_lifecycle: LAUNCHED
  qualifier_override: false
rollback_action:
  type: capability_disable
  target: "LOGS_LIST"
```

### capability_disable

```yaml
step_type: capability_disable
target: "INCIDENTS_DETAIL"
parameters:
  reason: "Contract execution"
rollback_action:
  type: capability_enable
  target: "INCIDENTS_DETAIL"
```

### config_update

```yaml
step_type: config_update
target: "system.rate_limit"
parameters:
  key: "max_requests_per_minute"
  old_value: 100
  new_value: 200
rollback_action:
  type: config_update
  target: "system.rate_limit"
  parameters:
    key: "max_requests_per_minute"
    new_value: 100  # Revert to old
```

### signal_record

```yaml
step_type: signal_record
target: "SYSTEM"
parameters:
  signal_type: "CONTRACT_EXECUTION"
  decision: "EXECUTING"
  reason: "Job {job_id} executing contract {contract_id}"
rollback_action: null  # Signals are not rolled back
```

---

## Health Supremacy Rule

**Jobs cannot override platform health.**

```python
async def execute_step(step: JobStep):
    # Check health before each step
    health = await platform_health_service.get_system_health()

    if health.status == "UNHEALTHY":
        raise HealthBlockException("System unhealthy - step blocked")

    if step.target in health.unhealthy_capabilities:
        raise HealthBlockException(f"Capability {step.target} unhealthy")

    # Execute step...
```

---

## Rollback Model

When a job fails, rollback is automatic:

```python
async def initiate_rollback(failed_job: GovernanceJob):
    rollback_steps = []

    # Reverse completed steps
    for step in reversed(failed_job.steps):
        if step.status == COMPLETED and step.rollback_action:
            rollback_steps.append(create_rollback_step(step))

    rollback_job = GovernanceJob(
        contract_id=failed_job.contract_id,
        status=PENDING,
        steps=rollback_steps,
        rollback_reason=failed_job.status_reason
    )

    failed_job.rollback_job_id = rollback_job.job_id
    failed_job.status = ROLLBACK_PENDING
```

---

## Constraints

### Scope Constraint

Jobs may only affect what the contract specifies:

```python
def verify_scope(job: GovernanceJob, contract: SystemContract):
    allowed_targets = set(contract.affected_capabilities)

    for step in job.steps:
        if step.target not in allowed_targets and step.target != "SYSTEM":
            raise ScopeViolation(f"Step targets {step.target} not in contract scope")
```

### Duration Constraint

Jobs have a maximum execution time:

```python
async def execute_with_timeout(job: GovernanceJob):
    try:
        async with timeout(job.max_duration_ms / 1000):
            await execute_job(job)
    except TimeoutError:
        job.status = FAILED
        job.status_reason = "Execution timeout"
        await initiate_rollback(job)
```

---

## Audit Integration

After completion, jobs enter AUDIT_PENDING:

```python
async def on_job_complete(job: GovernanceJob):
    job.status = AUDIT_PENDING

    audit = await create_audit(job)
    job.audit_id = audit.audit_id

    # Audit runs asynchronously
    # Job remains AUDIT_PENDING until audit completes
```

---

## Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| JOB-001 | Jobs execute contract scope only | Scope verification |
| JOB-002 | Health blocks execution | Health check per step |
| JOB-003 | Failed jobs trigger rollback | Automatic rollback |
| JOB-004 | Steps execute sequentially | No parallel steps |
| JOB-005 | Completed jobs require audit | State machine |
| JOB-006 | Rollback reverses completed steps | Rollback logic |

---

## API Surface

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/jobs` | GET | List jobs (filtered) |
| `/api/v1/jobs/{id}` | GET | Get job detail |
| `/api/v1/jobs/{id}/steps` | GET | Get step details |
| `/api/v1/jobs/{id}/cancel` | POST | Cancel pending job |

**No direct CREATE endpoint.** Jobs are created via contract activation only.

---

## Attestation

This specification defines the Governance Job execution model.
Implementation must enforce scope, health, and audit requirements.
Jobs are the only authorized execution path for contract changes.
