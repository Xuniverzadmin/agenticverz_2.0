# AOS Replay Scope & Semantics

**Status:** v1 Definition
**Milestone:** M6

---

## What is Replay?

**Replay** in AOS means re-executing a stored plan (list of skill calls + inputs + skill versions) **without re-calling the planner**.

Replay is used for:
1. **Debugging** - Reproduce an issue with same inputs
2. **Testing** - Verify runtime behavior is deterministic
3. **Validation** - Ensure changes don't break existing behavior
4. **Auditing** - Prove execution path for compliance

---

## What Replay Guarantees

### Guaranteed (Deterministic)

| Aspect | Description |
|--------|-------------|
| **Same skill calls** | Same skills invoked in same order |
| **Same parameters** | Exact same inputs to each skill |
| **Same retry behavior** | Same retry/backoff decisions |
| **Same error classification** | Same errors classified the same way |
| **Same side-effect sequence** | Side effects logged in same order |

### NOT Guaranteed (Non-Deterministic)

| Aspect | Reason |
|--------|--------|
| **External API responses** | Remote services may return different data |
| **LLM output content** | Language models are inherently non-deterministic |
| **Timestamps** | Wall clock time always differs |
| **Execution duration** | Network latency, system load vary |
| **Actual costs** | Pricing may change between runs |

---

## Parity Check Definition

When comparing an original trace with a replayed trace, **parity** means:

```
Original Trace             Replayed Trace
--------------             --------------
Step 0: http_call(url=X)   Step 0: http_call(url=X)     ✓ Same
Step 1: json_transform(q)  Step 1: json_transform(q)    ✓ Same
Step 2: llm_invoke(p)      Step 2: llm_invoke(p)        ✓ Same
Status: SUCCESS            Status: SUCCESS              ✓ Same
Retries: [1, 0, 0]         Retries: [1, 0, 0]           ✓ Same
```

Parity is verified by computing a **determinism signature** from:
- Skill names in order
- Parameters (canonicalized JSON)
- Status of each step
- Retry counts

**Parity does NOT require:**
- Same response data
- Same timing
- Same cost values

---

## Replay API

### Starting a Replay

```python
from app.runtime.replay import replay_run

result = await replay_run(
    run_id="run_abc123",      # Original run to replay
    verify_parity=True,        # Compare with original
    dry_run=False,             # Actually execute skills
)
```

### Replay Result

```python
@dataclass
class ReplayResult:
    success: bool              # Did replay complete?
    parity_check: ParityResult # Comparison with original
    trace: TraceRecord         # New trace from replay
    divergence_point: int | None  # Step where behavior differed
```

### Parity Result

```python
@dataclass
class ParityResult:
    is_parity: bool            # True if determinism holds
    original_signature: str    # Hash of original trace
    replay_signature: str      # Hash of replayed trace
    divergence_step: int | None
    divergence_reason: str | None
```

---

## Use Cases

### 1. Debugging a Failed Run

```bash
# Get the original trace
aos trace get run_abc123

# Replay to reproduce
aos replay run_abc123 --verbose

# Compare traces
aos trace diff run_abc123 run_xyz789
```

### 2. Regression Testing

```python
# In CI: replay golden runs and verify parity
async def test_regression():
    golden_runs = ["run_golden_1", "run_golden_2"]
    for run_id in golden_runs:
        result = await replay_run(run_id, verify_parity=True)
        assert result.parity_check.is_parity, f"Regression in {run_id}"
```

### 3. Determinism Validation

```python
# Verify same inputs produce same behavior
async def test_determinism():
    # Run twice with same inputs
    result1 = await runtime.execute(plan, tenant_id="test")
    result2 = await runtime.execute(plan, tenant_id="test")

    # Compare determinism signatures
    trace1 = await trace_store.get_trace(result1.run_id)
    trace2 = await trace_store.get_trace(result2.run_id)

    assert trace1.determinism_signature() == trace2.determinism_signature()
```

---

## Limitations

### 1. External State Changes

Replay cannot account for external state changes:

```
Original Run (T=0):
  http_call("api.example.com/item/123") → {"status": "available"}

Replay (T=1):
  http_call("api.example.com/item/123") → {"status": "sold"}

Parity: ✓ (same call made, different response is expected)
```

### 2. Time-Dependent Logic

If skills have time-dependent behavior, replay may diverge:

```python
# BAD: Time-dependent parameter
params = {"timestamp": datetime.now()}  # Different each run

# GOOD: Fixed or relative time
params = {"timestamp": "2025-01-01T00:00:00Z"}
```

### 3. Non-Idempotent Operations

Replaying non-idempotent operations may have side effects:

```
Original: POST /api/orders → {"order_id": 123}
Replay:   POST /api/orders → {"order_id": 456}  # Creates another order!
```

**Recommendation:** Use dry-run mode for non-idempotent replays.

### 4. Skill Version Changes

If skill version changes between original and replay:

```
Original: http_call v0.1.0 (no timeout)
Replay:   http_call v0.2.0 (30s timeout)

Behavior may differ due to version change.
```

**Recommendation:** Pin skill versions in plans for replay consistency.

---

## Best Practices

### For Replay-Safe Plans

1. **Use fixed timestamps** instead of `now()`
2. **Avoid randomness** in parameters
3. **Pin skill versions** when creating plans
4. **Use dry-run mode** for non-idempotent operations
5. **Store external responses** if content matters

### For Determinism Testing

1. **Mock external services** to ensure consistent responses
2. **Fix random seeds** if any randomness is used
3. **Compare signatures** not raw outputs
4. **Test retry paths** by injecting failures

---

## Replay vs Re-Run

| Aspect | Replay | Re-Run |
|--------|--------|--------|
| Planner called | No | Yes |
| Uses stored plan | Yes | No (generates new plan) |
| Deterministic path | Yes | No (planner may choose differently) |
| Use case | Debugging, testing | Fresh execution |

---

## Trace Storage

Traces are stored in SQLite by default:

```
/var/lib/aos/traces.db

Tables:
- traces: Run metadata
- trace_steps: Individual step records

Retention: 30 days default (configurable)
```

---

## Configuration

```bash
# Trace storage location
TRACE_STORAGE_PATH=/var/lib/aos/traces.db

# Retention period
TRACE_RETENTION_DAYS=30

# Enable/disable tracing
TRACING_ENABLED=true
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-04 | Initial replay scope definition |
