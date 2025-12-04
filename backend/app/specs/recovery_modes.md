# Recovery Mode Taxonomy

**Version:** 0.1.0
**Status:** DRAFT (M5 Preparation)
**Last Updated:** 2025-12-02

---

## Overview

Recovery modes define how the AOS runtime responds to errors. Each error code maps to a recovery mode that specifies the strategy for handling the failure.

---

## Recovery Strategies

### 1. RETRY_IMMEDIATE

**Description:** Retry the operation immediately without delay.

**Use Case:** Transient failures likely to succeed on immediate retry (e.g., brief network glitch).

**Configuration:**
```json
{
  "strategy": "RETRY_IMMEDIATE",
  "config": {
    "max_retries": 1,
    "delay_ms": 0
  }
}
```

**Behavior:**
1. Catch error
2. Increment retry counter
3. If retries < max_retries: retry immediately
4. Else: escalate to fallback or abort

---

### 2. RETRY_EXPONENTIAL

**Description:** Retry with exponential backoff.

**Use Case:** Rate limits, temporary overload, or service recovery.

**Configuration:**
```json
{
  "strategy": "RETRY_EXPONENTIAL",
  "config": {
    "max_retries": 3,
    "base_delay_ms": 1000,
    "max_delay_ms": 30000,
    "multiplier": 2.0
  }
}
```

**Delay Calculation:**
```
delay = min(base_delay * (multiplier ^ attempt), max_delay)
```

**Example Delays (base=1000, multiplier=2):**
- Attempt 1: 1000ms
- Attempt 2: 2000ms
- Attempt 3: 4000ms

---

### 3. RETRY_WITH_JITTER

**Description:** Exponential backoff with random jitter to prevent thundering herd.

**Use Case:** Shared resources, distributed systems, rate-limited APIs.

**Configuration:**
```json
{
  "strategy": "RETRY_WITH_JITTER",
  "config": {
    "max_retries": 3,
    "base_delay_ms": 1000,
    "max_delay_ms": 30000,
    "multiplier": 2.0,
    "jitter_factor": 0.25
  }
}
```

**Delay Calculation:**
```
base = min(base_delay * (multiplier ^ attempt), max_delay)
jitter = base * random(-jitter_factor, +jitter_factor)
delay = base + jitter
```

**Important:** Jitter MUST be seeded deterministically for replay.

---

### 4. FALLBACK

**Description:** Use a fallback value or alternative execution path.

**Use Case:** Non-critical operations where a default is acceptable.

**Configuration:**
```json
{
  "strategy": "FALLBACK",
  "config": {
    "fallback_value": null,
    "fallback_skill": "alternative_skill",
    "log_original_error": true
  }
}
```

**Behavior:**
1. Catch error
2. Log original error (if configured)
3. Return fallback_value OR invoke fallback_skill
4. Continue workflow

---

### 5. CIRCUIT_BREAKER

**Description:** Open circuit after threshold failures to prevent cascade.

**Use Case:** External services with known instability.

**Configuration:**
```json
{
  "strategy": "CIRCUIT_BREAKER",
  "config": {
    "failure_threshold": 5,
    "reset_timeout_ms": 60000,
    "half_open_requests": 1
  }
}
```

**States:**
- **CLOSED:** Normal operation, track failures
- **OPEN:** Reject all requests immediately
- **HALF_OPEN:** Allow limited requests to test recovery

**State Transitions:**
```
CLOSED --[failures >= threshold]--> OPEN
OPEN --[timeout elapsed]--> HALF_OPEN
HALF_OPEN --[request succeeds]--> CLOSED
HALF_OPEN --[request fails]--> OPEN
```

---

### 6. SKIP

**Description:** Skip the failed step and continue workflow.

**Use Case:** Optional enrichment steps, non-critical data.

**Configuration:**
```json
{
  "strategy": "SKIP",
  "config": {
    "log_level": "WARNING",
    "emit_metric": true,
    "substitute_value": null
  }
}
```

**Behavior:**
1. Catch error
2. Log at configured level
3. Emit skip metric (if configured)
4. Set step result to substitute_value
5. Continue to next step

---

### 7. ABORT

**Description:** Abort the workflow immediately.

**Use Case:** Critical errors, security violations, budget exceeded.

**Configuration:**
```json
{
  "strategy": "ABORT",
  "config": {
    "cleanup": true,
    "save_checkpoint": true,
    "notify": true,
    "notification_channel": "critical"
  }
}
```

**Behavior:**
1. Catch error
2. Save checkpoint (if configured)
3. Run cleanup handlers
4. Send notification (if configured)
5. Return error result to caller

---

### 8. ESCALATE

**Description:** Escalate to manual intervention.

**Use Case:** Errors requiring human decision.

**Configuration:**
```json
{
  "strategy": "ESCALATE",
  "config": {
    "alert_channel": "critical",
    "timeout_ms": 3600000,
    "timeout_action": "ABORT"
  }
}
```

**Behavior:**
1. Catch error
2. Send alert to configured channel
3. Pause workflow execution
4. Wait for manual resolution OR timeout
5. If resolved: continue with provided input
6. If timeout: execute timeout_action

---

### 9. CHECKPOINT_RESTORE

**Description:** Restore from last checkpoint and retry.

**Use Case:** State corruption, partial failures.

**Configuration:**
```json
{
  "strategy": "CHECKPOINT_RESTORE",
  "config": {
    "max_restore_attempts": 1,
    "checkpoint_age_limit_ms": 300000,
    "restore_to": "LAST_SUCCESSFUL"
  }
}
```

**Restore Targets:**
- `LAST_SUCCESSFUL` - Most recent successful checkpoint
- `STEP_START` - Beginning of failed step
- `WORKFLOW_START` - Beginning of workflow

**Behavior:**
1. Catch error
2. Load checkpoint
3. Validate checkpoint age
4. Restore state
5. Retry from restore point

---

### 10. MANUAL_INTERVENTION

**Description:** Pause and wait for explicit manual action.

**Use Case:** Security-sensitive operations, data reconciliation.

**Configuration:**
```json
{
  "strategy": "MANUAL_INTERVENTION",
  "config": {
    "prompt": "Approve data deletion?",
    "options": ["approve", "reject", "modify"],
    "timeout_ms": 86400000,
    "timeout_action": "ABORT"
  }
}
```

**Behavior:**
1. Pause workflow
2. Present prompt with options
3. Wait for user selection OR timeout
4. Execute based on selection

---

## Recovery Mode Selection

### Priority Order

1. **Error-specific override** - Error definition specifies recovery mode
2. **Category default** - Category specifies default recovery mode
3. **Global default** - System-wide default (typically ABORT)

### Decision Tree

```
Error Occurred
    │
    ├── Is error code in catalog?
    │   ├── Yes → Use error-specific recovery mode
    │   └── No → Continue to category match
    │
    ├── Is error category known?
    │   ├── TRANSIENT → RETRY_WITH_JITTER
    │   ├── PERMANENT → ABORT
    │   ├── RESOURCE → RETRY_EXPONENTIAL (if rate limit) or ABORT
    │   ├── PERMISSION → ABORT
    │   ├── VALIDATION → ABORT
    │   └── INTERNAL → ABORT + ALERT
    │
    └── Unknown → ABORT + LOG_CRITICAL
```

---

## Determinism Requirements

For replay compatibility, recovery modes MUST be deterministic:

1. **Seeded Jitter:** All random jitter must use seeded RNG
2. **Deterministic Delays:** Delay calculations must be reproducible
3. **Consistent State:** Circuit breaker state must be checkpointed
4. **Fallback Values:** Static fallback values only

### Non-Deterministic Elements (Quarantined)

These must be isolated from determinism-critical paths:
- Wall clock time (use logical time)
- External service responses
- User input timing
- System load variations

---

## Metrics

Each recovery mode emits standard metrics:

| Metric | Labels | Description |
|--------|--------|-------------|
| `aos_recovery_attempt_total` | `mode`, `error_code` | Total recovery attempts |
| `aos_recovery_success_total` | `mode`, `error_code` | Successful recoveries |
| `aos_recovery_failure_total` | `mode`, `error_code` | Failed recoveries |
| `aos_recovery_duration_seconds` | `mode` | Time spent in recovery |
| `aos_circuit_breaker_state` | `service` | Current circuit state |

---

## Related Documents

- [M5 Specification](../../docs/milestones/M5-SPEC.md)
- [Error Taxonomy](error_taxonomy.md)
- [Failure Catalog Schema](../schemas/failure_catalog.schema.json)
