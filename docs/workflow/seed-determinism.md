# AOS Seed Determinism Timeline

**Version:** 1.0
**Created:** 2025-12-02
**Last Updated:** 2025-12-02

---

## Executive Summary

This document provides a permanent historical record of determinism validation for the AOS Workflow Engine. These results establish the baseline determinism guarantees before M5 introduces failure recovery loops.

---

## Determinism Architecture

### Seed Propagation

AOS uses SHA256-based deterministic seed derivation:

```
workflow_seed = SHA256(base_seed || workflow_id)
step_seed = SHA256(workflow_seed || step_index)
```

This ensures:
1. Same base seed → same workflow behavior
2. Step ordering is deterministic
3. Parallel workers produce identical results

### Deterministic Components

| Component | Seeded | Method |
|-----------|--------|--------|
| Workflow execution order | Yes | Seed-derived priority |
| Step execution order | Yes | Sequential within workflow |
| Random values in steps | Yes | Seeded RNG per step |
| Retry delays (jitter) | Yes | Seeded jitter calculation |
| Hash computation | N/A | Deterministic by design |

### Non-Deterministic Components (Isolated)

| Component | Isolation Method |
|-----------|------------------|
| Wall clock time | Excluded from golden hash |
| Duration measurements | Excluded from golden hash |
| External API responses | Mocked in shadow mode |
| LLM outputs | Stubbed with seeded responses |

---

## Validation Timeline

### Phase B: Multi-Worker Determinism (2025-12-02)

**Test Configuration:**
| Parameter | Value |
|-----------|-------|
| Workers | 3 |
| Iterations per worker | 500 |
| Seeds per iteration | 5 |
| Workflow types | 3 (compute, io, llm) |
| **Total iterations** | **22,500** |

**Results:**
| Metric | Value |
|--------|-------|
| Mismatches | **0** |
| Duration | 11.23 seconds |
| Throughput | 2,004 iterations/sec |

**Evidence:**
- Test Script: `/tmp/multi_worker_500.py`
- Verification: Step-level hash comparison across workers

### Phase D: CPU Stress Determinism (2025-12-02)

**Test Configuration:**
| Parameter | Value |
|-----------|-------|
| CPU stress workers | 4 |
| Replay workers | 4 |
| Workflows | 100 |
| Replays | 100 |

**Results:**
| Metric | Value |
|--------|-------|
| Mismatches under load | **0** |

**Evidence:**
- Test Script: `/tmp/cpu_stress_replay.py`
- Verification: Golden hash match under CPU contention

### Phase E: 24-Hour Shadow Simulation (2025-12-02 - 2025-12-03)

**Test Configuration:**
| Parameter | Value |
|-----------|-------|
| Start Time | 2025-12-02 13:12:19 CET |
| Duration | 24 hours |
| Workers | 3 |
| Cycle Interval | 30 seconds |
| Workflows per cycle | ~9 |
| Expected cycles | ~2,880 |
| Expected workflows | ~26,000 |

**Running Status (T+1h 15min):**
| Metric | Value |
|--------|-------|
| Cycles completed | 138 |
| Workflows executed | ~1,242 |
| Replays verified | ~1,242 |
| Mismatches | **0** |
| Golden files created | 1,242 |

**Evidence:**
- Log: `/var/lib/aos/shadow_24h_20251202_131219.log`
- Golden Dir: `/tmp/shadow_simulation_20251202_131219/golden/`
- Monitor Log: `/var/lib/aos/shadow_monitor.log`

---

## Cumulative Determinism Statistics

| Metric | Value | Date |
|--------|-------|------|
| Total determinism iterations | 22,500+ | 2025-12-02 |
| Total shadow cycles | 138+ (ongoing) | 2025-12-02 |
| Total workflows replayed | 1,242+ (ongoing) | 2025-12-02 |
| Total mismatches | **0** | 2025-12-02 |
| CPU stress iterations | 100 | 2025-12-02 |
| Fault injection iterations | 12 types | 2025-12-02 |

---

## Determinism Guarantees

Based on the validation results, AOS provides the following guarantees:

### G1: Cross-Worker Determinism
> Given the same seed, any worker will produce identical workflow_hash values.

**Evidence:** 22,500 iterations across 3 workers, 0 mismatches.

### G2: Replay Determinism
> A workflow can be replayed from a checkpoint and produce identical results.

**Evidence:** 1,242+ shadow replays, 0 mismatches.

### G3: Stress Resilience
> Determinism is maintained under CPU stress conditions.

**Evidence:** 100 workflows replayed under 4-core CPU stress, 0 mismatches.

### G4: Step-Level Determinism
> Individual step hashes are deterministic and reproducible.

**Evidence:** Step hash arrays match in all 22,500+ iterations.

---

## Hash Computation

### Workflow Hash
```python
workflow_hash = SHA256(
    canonical_json({
        "run_id": run_id,
        "workflow_type": workflow_type,
        "seed": seed,
        "step_hashes": step_hashes,  # Ordered list
        "success": success,
        "error": error_code  # Not error message
    })
)
```

### Step Hash
```python
step_hash = SHA256(
    canonical_json({
        "skill_name": skill_name,
        "skill_version": skill_version,
        "input_hash": SHA256(canonical_json(inputs)),
        "output_hash": SHA256(canonical_json(outputs)),
        "seed": step_seed
    })
)
```

### Canonical JSON Rules
- Keys sorted alphabetically
- No whitespace
- Unicode normalized (NFC)
- Numbers without trailing zeros
- Null represented as `null`

---

## Golden File Format

```json
{
  "run_id": "primary-w1-280cfdcd",
  "workflow_type": "io",
  "seed": 74439,
  "step_hashes": [
    "mock_io:87bec47e62613a99",
    "mock_io:3e5aaa8c6e78b91a",
    "transform_json:41ef8a685e35feaf",
    "compute_hash:c3e33927cf3b2683"
  ],
  "workflow_hash": "85046808c4908b85a2b0ad5efdc3f9edc5434ca2c0581e1a7cbaadfef8dacbc5",
  "duration_ms": 0,
  "success": true,
  "error": null
}
```

**Note:** `duration_ms` is excluded from workflow_hash computation (volatile field).

---

## Verification Commands

### Quick Verification
```bash
# Check shadow status
./scripts/stress/check_shadow_status.sh

# Verify no mismatches in log
grep -E "[1-9][0-9]* mismatches" /var/lib/aos/shadow_24h_*.log | grep -v ", 0 mismatches"
# Expected: no output
```

### Full Verification
```bash
# Run determinism stress test
./scripts/stress/run_multi_worker_determinism.sh

# Run shadow simulation
./scripts/stress/run_shadow_simulation.sh --hours 1 --workers 3

# Analyze golden files
python3 scripts/stress/golden_diff_debug.py --summary-dir /tmp/shadow_simulation_*/golden
```

---

## Pre-M5 Baseline

This document establishes the determinism baseline before M5 introduces:
- Failure recovery loops
- Retry with jitter
- Circuit breaker state
- Checkpoint restore paths

Any regression in determinism after M5 must be investigated against this baseline.

---

## Related Documents

- [PIN-015](../memory-pins/PIN-015-m4-validation-maturity-gates.md) - M4 Validation Gates
- [Determinism & Replay Spec](../backend/app/specs/determinism_and_replay.md) - Technical Spec
- [M4 Summary](../release-notes/M4-summary.md) - Milestone Summary
