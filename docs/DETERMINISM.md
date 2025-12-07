# AOS Determinism Guide

Deterministic simulation and replay is a core principle of AOS. This guide covers how to use deterministic features for reproducible agent execution.

## Overview

AOS guarantees that:

1. **Same input + same seed = identical output** (always)
2. **Traces capture everything needed for replay** (verifiable)
3. **Time is frozen during simulation** (predictable)
4. **RNG state is captured at each step** (auditable)

## Why Determinism Matters

| Scenario | Without Determinism | With Determinism |
|----------|--------------------|--------------------|
| Debugging | "It worked yesterday..." | Replay exact trace |
| Testing | Flaky tests | Reproducible assertions |
| Auditing | Log parsing | Verifiable trace chain |
| Compliance | "Trust me" | Cryptographic proof |

## Quick Start

### CLI Usage

```bash
# Simulate with explicit seed
aos simulate '[{"skill":"transform","params":{}}]' --seed 42

# Save trace for replay
aos simulate '[...]' --seed 42 --save-trace run001.trace.json

# Replay and verify
aos replay run001.trace.json --execute

# Compare two traces
aos diff run001.trace.json run002.trace.json

# Dry run (no execution)
aos simulate '[...]' --dry-run
```

### Python SDK

```python
from aos_sdk import AOSClient, RuntimeContext, Trace

# Create deterministic context
ctx = RuntimeContext(
    seed=42,
    now="2025-01-01T00:00:00Z"  # Frozen time
)

# Deterministic random values
value = ctx.randint(1, 100)    # Always 82 for seed=42
uuid = ctx.uuid()               # Deterministic UUID

# Create client and trace
client = AOSClient()
trace = Trace(seed=ctx.seed, timestamp=ctx.timestamp(), plan=my_plan)

# Simulate
result = client.simulate(my_plan, seed=ctx.seed)

# Record step
trace.add_step(
    skill_id="simulate",
    input_data=my_plan,
    output_data=result,
    rng_state=ctx.rng_state,
    duration_ms=150,
    outcome="success"
)

# Finalize and save
trace.finalize()
trace.save("run.trace.json")
print(f"Root hash: {trace.root_hash}")
```

## Core Components

### RuntimeContext

Provides deterministic primitives for simulation:

```python
from aos_sdk import RuntimeContext

ctx = RuntimeContext(
    seed=42,                          # Random seed
    now="2025-01-01T12:00:00Z",       # Frozen timestamp
    tenant_id="tenant-001"            # Isolation
)

# Deterministic operations
ctx.randint(1, 100)     # Random integer
ctx.random()            # Random float [0, 1)
ctx.choice([1, 2, 3])   # Random choice
ctx.uuid()              # Deterministic UUID
ctx.timestamp()         # Frozen ISO8601 string

# Capture state for trace
ctx.rng_state           # SHA256 of RNG state (16 chars)
ctx.to_dict()           # Serialize for trace
```

### Trace

Records execution for replay verification:

```python
from aos_sdk import Trace

# Create trace
trace = Trace(
    seed=42,
    plan=[{"skill": "transform", "params": {}}],
    timestamp="2025-01-01T00:00:00Z"
)

# Add steps as execution progresses
trace.add_step(
    skill_id="transform",
    input_data={"x": 1},
    output_data={"y": 2},
    rng_state="abc123def456",
    duration_ms=100,
    outcome="success"  # or "failure" or "skipped"
)

# Finalize (computes Merkle root hash)
trace.finalize()

# Save/load
trace.save("run.trace.json")
loaded = Trace.load("run.trace.json")

# Verify integrity
assert loaded.verify()  # Recomputes hash
```

### Trace Diffing

Compare traces to detect non-determinism:

```python
from aos_sdk import diff_traces, Trace

trace1 = Trace.load("original.trace.json")
trace2 = Trace.load("replay.trace.json")

result = diff_traces(trace1, trace2)

if result["match"]:
    print("Traces are identical")
else:
    print(f"Differences: {result['summary']}")
    for diff in result["differences"]:
        print(f"  {diff['field']}: {diff['trace1']} != {diff['trace2']}")
```

## Trace Schema v1

Traces follow a canonical JSON schema:

```json
{
  "version": "1.0.0",
  "seed": 42,
  "timestamp": "2025-01-01T00:00:00+00:00",
  "tenant_id": "default",
  "plan": [
    {"skill": "transform", "params": {"query": "..."}}
  ],
  "steps": [
    {
      "step_index": 0,
      "skill_id": "transform",
      "input_hash": "a1b2c3d4e5f6...",
      "output_hash": "f6e5d4c3b2a1...",
      "rng_state_before": "0123456789ab",
      "duration_ms": 150,
      "outcome": "success",
      "error_code": null,
      "timestamp": "2025-01-01T00:00:00+00:00"
    }
  ],
  "root_hash": "deadbeef...",
  "finalized": true,
  "metadata": {}
}
```

### Root Hash Computation

The `root_hash` is computed as a Merkle chain:

```
chain = SHA256(seed:timestamp)
for each step:
    step_json = canonical_json(step)
    chain = SHA256(chain:step_json)
root_hash = chain
```

This ensures:
- Any modification invalidates the hash
- Steps cannot be reordered
- Truncation is detected

## Best Practices

### 1. Always Specify Seed

```python
# Bad - non-deterministic
result = client.simulate(plan)

# Good - deterministic
result = client.simulate(plan, seed=42)
```

### 2. Use Frozen Time

```python
# Bad - time-dependent
ctx = RuntimeContext(seed=42)

# Good - reproducible
ctx = RuntimeContext(seed=42, now="2025-01-01T00:00:00Z")
```

### 3. Capture Traces for Debugging

```python
# Always save traces in development
trace = Trace(seed=ctx.seed, plan=plan)
try:
    result = execute(plan)
    trace.add_step(...)
finally:
    trace.finalize()
    trace.save(f"traces/{run_id}.trace.json")
```

### 4. Verify Replay in CI

```yaml
# .github/workflows/determinism-check.yml
- name: Verify determinism
  run: |
    aos simulate '...' --seed 42 --save-trace t1.json
    aos simulate '...' --seed 42 --save-trace t2.json
    aos diff t1.json t2.json
```

### 5. Use Canonical JSON

```python
from aos_sdk import canonical_json, hash_data

# Identical data, different order
data1 = {"b": 2, "a": 1}
data2 = {"a": 1, "b": 2}

# Canonical form is identical
assert canonical_json(data1) == canonical_json(data2)
assert hash_data(data1) == hash_data(data2)
```

## Non-Deterministic Operations

Some operations are inherently non-deterministic:

| Operation | Issue | Solution |
|-----------|-------|----------|
| HTTP requests | Network timing | Mock in tests |
| Current time | Time changes | Use `ctx.timestamp()` |
| `random.random()` | Global state | Use `ctx.random()` |
| `uuid.uuid4()` | Random | Use `ctx.uuid()` |
| Database IDs | Auto-increment | Use deterministic IDs |

### Handling External Calls

For skills that make external calls, the trace captures:
- Input hash (what was sent)
- Output hash (what was received)
- RNG state (for replay without network)

In replay mode, AOS can optionally:
1. **Skip external calls** - use recorded output hash
2. **Re-execute** - verify output matches recorded hash
3. **Fail fast** - if external response differs

## Debugging Non-Determinism

If `aos diff` reports differences:

```bash
$ aos diff trace1.json trace2.json
Comparing:
  Trace 1: trace1.json (hash: abc123...)
  Trace 2: trace2.json (hash: def456...)

Result: DIFFERENT (2 differences)

  step[0].output_hash:
    Trace 1: a1b2c3d4
    Trace 2: e5f6g7h8

  root_hash:
    Trace 1: abc123...
    Trace 2: def456...
```

**Common causes:**

1. **Different seeds** - Check `seed` field
2. **Time-dependent code** - Check for `datetime.now()` calls
3. **Uncontrolled RNG** - Use `ctx.random()` instead of `random.random()`
4. **External API changes** - Mock or record responses
5. **Floating point** - Use `decimal` or round consistently

## CI Integration

The `determinism-check.yml` workflow runs:

1. **Unit tests** - RuntimeContext and Trace classes
2. **Multi-seed verification** - Seeds 1, 42, 1337, 999999
3. **Trace schema validation** - Serialize/deserialize roundtrip
4. **Canonical JSON stability** - Key ordering independence

Triggered on:
- Pull requests touching SDK or worker
- Push to main/develop
- Nightly schedule (2 AM UTC)
- Manual dispatch with custom seed

## API Reference

### RuntimeContext

| Method | Description |
|--------|-------------|
| `randint(a, b)` | Deterministic integer in [a, b] |
| `random()` | Deterministic float in [0, 1) |
| `choice(seq)` | Deterministic choice from sequence |
| `shuffle(seq)` | In-place deterministic shuffle |
| `uuid()` | Deterministic UUID |
| `timestamp()` | Frozen ISO8601 string |
| `to_dict()` | Serialize to dict |
| `from_dict(d)` | Deserialize from dict |

### Trace

| Method | Description |
|--------|-------------|
| `add_step(...)` | Record execution step |
| `finalize()` | Compute root hash |
| `verify()` | Check integrity |
| `to_json()` | Canonical JSON string |
| `save(path)` | Write to file |
| `load(path)` | Read from file |

### Utilities

| Function | Description |
|----------|-------------|
| `canonical_json(obj)` | Sorted keys, compact JSON |
| `hash_data(obj)` | SHA256 of canonical JSON |
| `diff_traces(t1, t2)` | Compare two traces |
| `freeze_time(iso)` | Parse ISO8601 string |

## Summary

AOS determinism provides:

- **Reproducibility**: Same seed = same output
- **Auditability**: Cryptographic trace chain
- **Debuggability**: Replay any execution
- **Testability**: No flaky tests

Use these primitives to build agents that are predictable, verifiable, and machine-native.
