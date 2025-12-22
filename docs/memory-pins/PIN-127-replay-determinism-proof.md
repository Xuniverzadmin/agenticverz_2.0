# PIN-127: Replay Determinism Proof

**Status:** COMPLETE
**Category:** Core Infrastructure / Determinism
**Created:** 2025-12-22
**Tag:** `v1.0.0-determinism-proof`
**Related PINs:** PIN-126, PIN-120

---

## The Invariant

> **Given a frozen execution trace, the system must produce identical determinism signature, or fail loudly with a classified reason.**

This is a verifiable engineering guarantee, not marketing language.

---

## What This Proves

| Claim | Test |
|-------|------|
| Same trace → same hash | `test_determinism_invariant_same_trace_same_hash` |
| Reload from disk → same hash | `test_determinism_invariant_reload_same_hash` |
| Self-comparison → parity | `test_compare_traces_identical` |
| Float normalization → stable | `test_float_normalization_prevents_drift` |
| Different step count → detected | `test_detect_step_count_divergence` |
| Different status → detected | `test_detect_status_divergence` |
| Different params → detected | `test_detect_params_divergence` |
| Schema version enforced | `test_schema_version_is_set` |

---

## Implementation

### Gap 1: Schema Versioning

```python
# backend/app/traces/models.py
class TraceRecord:
    SCHEMA_VERSION: ClassVar[str] = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "checksum": self.determinism_signature(),
            # ... other fields
        }
```

**Why:** Traces must be versioned for future compatibility. Without versioning, format changes silently break replay.

### Gap 2: Float Normalization

```python
def _normalize_for_determinism(value: Any) -> Any:
    """Round floats to 6 decimals, recurse into dicts/lists."""
    if isinstance(value, float):
        return round(value, 6)
    elif isinstance(value, dict):
        return {k: _normalize_for_determinism(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_normalize_for_determinism(v) for v in value]
    return value
```

**Why:** Floating-point representation varies across platforms. Without normalization, `3.14159265` and `3.141592650000001` produce different hashes despite being semantically identical.

**Scope:** Applied only inside `determinism_hash()`. No runtime pollution.

### Gap 3: Invariant Test Suite

```
backend/tests/test_determinism_invariant.py
├── TestDeterminismInvariant (7 tests)
│   ├── test_frozen_trace_has_schema_version
│   ├── test_frozen_trace_has_checksum
│   ├── test_determinism_invariant_same_trace_same_hash  ← THE CROWN JEWEL
│   ├── test_determinism_invariant_reload_same_hash
│   ├── test_compare_traces_identical
│   ├── test_float_normalization_prevents_drift
│   └── test_signature_is_stable_across_step_order
├── TestDeterminismDriftDetection (3 tests)
│   ├── test_detect_step_count_divergence
│   ├── test_detect_status_divergence
│   └── test_detect_params_divergence
└── TestSchemaVersioning (3 tests)
    ├── test_schema_version_is_set
    ├── test_to_dict_includes_schema_version
    └── test_to_dict_includes_checksum
```

**Runtime:** 0.25s
**Status:** CI-blocking

---

## Files

| File | Purpose |
|------|---------|
| `backend/app/traces/models.py` | Schema version, float normalization, checksum |
| `backend/tests/test_determinism_invariant.py` | 13-test invariant suite |
| `backend/tests/fixtures/golden_trace.json` | Frozen trace fixture |

---

## What This Unlocks

- **Incident post-mortems:** Replay with proof of fidelity
- **Ops console:** "Replay verified" badge/state
- **Recovery workflows:** Trust that suggestions match original behavior
- **Governance claims:** Auditable execution traces
- **Enterprise trust:** Determinism as a hard technical moat

---

## What NOT To Do

- ❌ Do not generalize to all agents yet
- ❌ Do not add replay configuration options
- ❌ Do not touch performance
- ❌ Do not "clean up" replay code

This proof is complete. Consume it, don't extend it.

---

## Correct Next Steps (When Ready)

1. Show drift reports in ops UI
2. Attach replay hashes to incidents
3. Expose "replay verified" as a badge/state
4. Surface divergence reasons in incident timeline

---

## Verification

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 -m pytest tests/test_determinism_invariant.py -v
# 13 passed in 0.25s
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Created PIN-127 with determinism proof documentation |
| 2025-12-22 | Tagged `v1.0.0-determinism-proof` |
