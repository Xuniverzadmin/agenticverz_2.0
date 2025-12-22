# PIN-125: SDK Cross-Language Parity - CI Fix & Prevention

**Status:** COMPLETE
**Created:** 2025-12-22
**Category:** Infrastructure / CI / SDK
**Author:** Claude Opus 4.5
**Milestone:** M8 (SDK Packaging)

---

## Executive Summary

This PIN documents the root cause analysis and fix for CI failures in the Determinism Check workflow, specifically the cross-language parity tests between Python and JavaScript SDKs.

---

## Issue Description

### Failing CI Jobs

| Job Name | Exit Code | Impact |
|----------|-----------|--------|
| Cross-Language Parity (Python vs JS) | 1 | Blocking |
| Cross-Language Parity (Script) | 1 | Blocking |
| Determinism Summary | 1 | Cascade failure |
| Replay Verification | Warning | Non-blocking |

### Symptoms

1. Root hash mismatch between Python and JS SDKs
2. ES module syntax error in CI environment
3. Determinism verification failing despite correct Python implementation

---

## Root Cause Analysis

### Issue 1: Missing SDK Exports

**File:** `sdk/js/aos-sdk/dist/index.js`

**Problem:** The compiled JS SDK was only exporting 4 items instead of all 19.

```javascript
// Before (incorrect):
module.exports = { AOSClient, AOSError, NovaClient, VERSION };

// After (correct):
module.exports = {
  AOSClient, AOSError, NovaClient, VERSION,
  RuntimeContext, Trace, TraceStep, canonicalJson, hashData, hashTrace,
  freezeTime, diffTraces, createTraceFromContext, TRACE_SCHEMA_VERSION,
  resetIdempotencyState, markIdempotencyKeyExecuted, isIdempotencyKeyExecuted,
  replayStep, generateIdempotencyKey
};
```

**Root Cause:** The `dist/` folder was rebuilt but the source `src/index.ts` correctly exported everything. The issue was stale build artifacts in the repository.

### Issue 2: ES Module vs CommonJS Mismatch

**File:** `sdk/js/aos-sdk/scripts/compare_with_python.js`

**Problem:** Script used ES module syntax but package.json doesn't have `"type": "module"`.

```javascript
// Before (ES modules - fails in CI):
import fs from "fs";
import crypto from "crypto";

// After (CommonJS - works in CI):
const fs = require("fs");
const crypto = require("crypto");
```

### Issue 3: Hash Chain Separator Mismatch

**File:** `sdk/js/aos-sdk/scripts/compare_with_python.js`

**Problem:** Hash chain computation used different separator than Python.

```javascript
// Before (JS - incorrect):
const combined = currentHash + stepHash;  // Direct concatenation

// After (JS - matches Python):
const combined = `${currentHash}:${stepHash}`;  // Colon separator
```

```python
# Python implementation (reference):
combined = f"{chain_hash}:{step_det_hash}"  # Colon separator
```

---

## Fix Applied

### Commit: `c6ab777`

```
fix(sdk): Fix cross-language parity failures in CI

JS SDK Fixes:
- Rebuild dist with all exports (Trace, canonicalJson, hashData, etc.)
- Fix compare_with_python.js: convert ES modules to CommonJS
- Fix hash chaining: add colon separator to match Python implementation
```

### Files Changed

| File | Change |
|------|--------|
| `sdk/js/aos-sdk/dist/index.js` | Rebuilt with all 19 exports |
| `sdk/js/aos-sdk/dist/index.mjs` | Rebuilt with all 19 exports |
| `sdk/js/aos-sdk/dist/index.d.ts` | Type definitions updated |
| `sdk/js/aos-sdk/dist/index.d.mts` | Type definitions updated |
| `sdk/js/aos-sdk/scripts/compare_with_python.js` | ES→CommonJS, fixed colon separator |

---

## Prevention Mechanisms

### PREV-16: SDK Export Verification

**Location:** `scripts/ops/postflight.py`

**Rule:** Verify JS SDK exports match expected list after build.

```python
# Check: JS SDK exports all required items
required_exports = [
    'AOSClient', 'Trace', 'canonicalJson', 'hashData',
    'RuntimeContext', 'TraceStep', 'TRACE_SCHEMA_VERSION'
]
```

### PREV-17: Cross-Language Parity Pre-Commit

**Location:** `scripts/ops/preflight.py`

**Rule:** Run parity check before commits touching SDK files.

```python
# Trigger: Changes to sdk/python/** or sdk/js/**
# Check: Generate Python trace, verify JS can compute same root_hash
```

### PREV-18: SDK Build Freshness

**Location:** `.github/workflows/ci.yml`

**Rule:** Always rebuild JS SDK before parity tests.

```yaml
- name: Build JS SDK (ensure fresh)
  run: |
    cd sdk/js/aos-sdk
    npm ci
    npm run build
```

### PREV-19: Hash Algorithm Parity Test

**Location:** `sdk/js/aos-sdk/test/parity.test.js`

**Rule:** Unit test verifying hash algorithm matches Python exactly.

```javascript
test('hash chain uses colon separator', () => {
  // Verify: combined = `${hash1}:${hash2}` not hash1 + hash2
});
```

---

## Verification Checklist

### Local Verification

```bash
# 1. Generate Python trace
python3 -c "
from aos_sdk import Trace, RuntimeContext
ctx = RuntimeContext(seed=1337, now='2025-12-01T00:00:00Z')
trace = Trace(seed=ctx.seed, timestamp=ctx.timestamp(), plan=[{'skill': 'test'}])
trace.add_step(skill_id='test', input_data={'x': 1}, output_data={'y': 2},
               rng_state=ctx.rng_state, duration_ms=50, outcome='success')
trace.finalize()
trace.save('/tmp/test_trace.json')
print(f'Python: {trace.root_hash}')
"

# 2. Verify JS computes same hash
node sdk/js/aos-sdk/scripts/compare_with_python.js /tmp/test_trace.json

# Expected output: PARITY CHECK: PASSED
```

### CI Verification

1. Push changes to trigger CI
2. Verify "Determinism Check" workflow passes
3. Verify all parity jobs show green

---

## Cross-Language Parity Contract

### Deterministic Fields (MUST match)

| Field | Python | JS |
|-------|--------|-----|
| `seed` | `int` | `number` |
| `timestamp` | `str` (ISO 8601) | `string` (ISO 8601) |
| `tenant_id` | `str` | `string` |
| `step_index` | `int` | `number` |
| `skill_id` | `str` | `string` |
| `input_hash` | `str` (16 char hex) | `string` (16 char hex) |
| `output_hash` | `str` (16 char hex) | `string` (16 char hex) |
| `rng_state_before` | `str` | `string` |
| `outcome` | `str` | `string` |
| `idempotency_key` | `str | None` | `string | null` |
| `replay_behavior` | `str` | `string` |

### Hash Algorithm (MUST match)

```
1. base_string = f"{seed}:{timestamp}:{tenant_id}"
2. chain_hash = SHA256(base_string).hexdigest()
3. For each step:
   a. step_payload = canonical_json(deterministic_payload)
   b. step_hash = SHA256(step_payload).hexdigest()
   c. combined = f"{chain_hash}:{step_hash}"  # COLON SEPARATOR
   d. chain_hash = SHA256(combined).hexdigest()
4. root_hash = chain_hash
```

### Canonical JSON Rules

1. Keys sorted alphabetically
2. No whitespace between elements
3. Separators: `","` and `":"`
4. `null` for None/null values

---

## Related PINs

- PIN-120: Test Suite Stabilization & Prevention (PREV-1 to PREV-12)
- PIN-121: Mypy Technical Debt Remediation (PREV-13 to PREV-15)
- PIN-033: M8-M14 Machine-Native Realignment

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Initial PIN created, fix applied, prevention mechanisms defined |

---

*PIN-125: SDK Cross-Language Parity - Ensuring Python and JS SDKs produce identical deterministic hashes.*
