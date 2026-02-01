# deterministic.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/deterministic.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            deterministic.py
Lives in:        services/
Role:            Services
Inbound:         runtime, workers
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Deterministic execution utilities (pure computation, no boundary crossing)
Violations:      none
```

## Purpose

Deterministic execution utilities (pure computation, no boundary crossing)

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `seeded_jitter(workflow_run_id: str, attempt: int) -> float`

Generate deterministic jitter value from workflow ID and attempt number.

Uses HMAC-SHA256 to produce a consistent float between 0 and 1
that is reproducible given the same inputs.

Args:
    workflow_run_id: Unique workflow run identifier
    attempt: Current attempt number (1-based)

Returns:
    Float between 0.0 and 1.0

### `deterministic_backoff_ms(workflow_run_id: str, attempt: int, initial_ms: int, multiplier: float, jitter_pct: float, max_ms: int) -> int`

Calculate exponential backoff with deterministic jitter.

The jitter is derived from the workflow_run_id and attempt number,
making the backoff sequence reproducible for replay verification.

Args:
    workflow_run_id: Unique workflow run identifier
    attempt: Current attempt number (1-based)
    initial_ms: Initial backoff in milliseconds
    multiplier: Exponential multiplier per attempt
    jitter_pct: Jitter percentage (0.1 = +/- 10%)
    max_ms: Maximum backoff in milliseconds

Returns:
    Backoff duration in milliseconds

### `deterministic_timestamp(workflow_run_id: str, step_index: int, base_time: Optional[float]) -> int`

Generate a deterministic timestamp for replay scenarios.

In production, returns current time. In replay mode with base_time,
returns a reproducible offset from base_time.

Args:
    workflow_run_id: Unique workflow run identifier
    step_index: Step index within workflow
    base_time: Base timestamp for replay (None = use current time)

Returns:
    Unix timestamp in seconds

### `generate_idempotency_key(workflow_run_id: str, skill_name: str, step_index: int) -> str`

Generate a deterministic idempotency key for a skill execution.

Args:
    workflow_run_id: Unique workflow run identifier
    skill_name: Name of the skill being executed
    step_index: Step index within workflow

Returns:
    Idempotency key string

### `hash_params(params: dict) -> str`

Generate a hash of skill parameters for idempotency comparison.

Args:
    params: Skill input parameters

Returns:
    SHA256 hash prefix (16 chars)

## Domain Usage

**Callers:** runtime, workers

## Export Contract

```yaml
exports:
  functions:
    - name: seeded_jitter
      signature: "seeded_jitter(workflow_run_id: str, attempt: int) -> float"
      consumers: ["orchestrator"]
    - name: deterministic_backoff_ms
      signature: "deterministic_backoff_ms(workflow_run_id: str, attempt: int, initial_ms: int, multiplier: float, jitter_pct: float, max_ms: int) -> int"
      consumers: ["orchestrator"]
    - name: deterministic_timestamp
      signature: "deterministic_timestamp(workflow_run_id: str, step_index: int, base_time: Optional[float]) -> int"
      consumers: ["orchestrator"]
    - name: generate_idempotency_key
      signature: "generate_idempotency_key(workflow_run_id: str, skill_name: str, step_index: int) -> str"
      consumers: ["orchestrator"]
    - name: hash_params
      signature: "hash_params(params: dict) -> str"
      consumers: ["orchestrator"]
  classes: []
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

