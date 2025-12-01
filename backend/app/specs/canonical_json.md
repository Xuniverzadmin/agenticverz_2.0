# Canonical JSON Rules (AOS)

**Version:** 1.0.0
**Status:** Active
**Last Updated:** 2025-12-01

---

## Purpose

This specification defines canonical JSON serialization rules for AOS to ensure:
1. **Determinism**: Same data produces identical JSON bytes
2. **Replay**: Golden files can be compared byte-for-byte
3. **Hashing**: Content hashes are stable across runs

---

## Core Rules

### 1. Key Ordering

All JSON objects MUST have keys sorted alphabetically (ASCII order).

```python
# CORRECT
{"a": 1, "b": 2, "z": 3}

# INCORRECT
{"z": 3, "a": 1, "b": 2}
```

### 2. Numeric Formatting

- **Integers**: No leading zeros, no unnecessary decimal points
- **Floats**: Use minimal representation, no trailing zeros after decimal
- **Scientific notation**: Avoid unless necessary for precision

```python
# CORRECT
42
3.14
0.001

# INCORRECT
042
3.140000
1.0e-3
```

### 3. String Escaping

Use minimal escaping. Only escape:
- `"` (double quote) → `\"`
- `\` (backslash) → `\\`
- Control characters (0x00-0x1F) → `\uXXXX`

Do NOT escape:
- Forward slash `/`
- Unicode characters (use UTF-8 directly)

### 4. Whitespace

- **No** extra whitespace between elements
- **No** trailing whitespace
- **No** leading whitespace
- **No** newlines in serialized output (single line)

```python
# CORRECT
{"key":"value","array":[1,2,3]}

# INCORRECT
{ "key" : "value" , "array" : [ 1, 2, 3 ] }
```

### 5. Null Handling

- Explicit `null` values MUST be serialized (not omitted)
- Empty strings `""` are NOT equivalent to `null`

```python
# CORRECT - null is explicit
{"name": "Alice", "middle_name": null}

# INCORRECT - omitting null
{"name": "Alice"}
```

### 6. Boolean Values

Always lowercase: `true`, `false`

### 7. Array Ordering

Arrays MUST maintain insertion order. Do NOT sort array elements unless the schema explicitly defines the array as an unordered set.

---

## Implementation

### Python Canonical Serialization

```python
import json
from typing import Any

def canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON format."""
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':'),
        default=str  # Handle non-serializable types
    )

def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize to canonical JSON bytes (UTF-8)."""
    return canonical_json(obj).encode('utf-8')
```

### Content Hashing

```python
import hashlib

def content_hash(obj: Any) -> str:
    """Compute deterministic content hash."""
    canonical = canonical_json_bytes(obj)
    return hashlib.sha256(canonical).hexdigest()[:16]
```

---

## Field Stability Categories

From `determinism_and_replay.md`, fields are categorized as:

| Category | Serialization Rule |
|----------|-------------------|
| `DETERMINISTIC` | Must produce identical bytes across runs |
| `STABLE_AFTER_COMMIT` | Fixed once recorded, may vary during execution |
| `ALLOWED_VARIANCE` | May differ between runs (timestamps, UUIDs) |

### Fields with ALLOWED_VARIANCE

These fields are excluded from content hash comparisons:
- `id` (generated UUIDs)
- `created_at`, `started_at`, `completed_at` (timestamps)
- `duration_ms` (timing data)
- `trace_id`, `span_id` (telemetry)

---

## Golden File Format

Golden files for replay tests use this structure:

```json
{
  "_meta": {
    "version": "1.0.0",
    "created_at": "2025-12-01T00:00:00Z",
    "description": "Test case description"
  },
  "input": { ... },
  "expected_output": { ... },
  "deterministic_fields": ["skill_id", "version", "output_hash"],
  "ignored_fields": ["id", "created_at", "duration_ms"]
}
```

---

## Verification

### CI Check: `canonical-json-check`

```bash
#!/bin/bash
# Verify all golden files are canonical

for file in backend/tests/golden/*.json; do
    # Re-serialize and compare
    python3 -c "
import json
import sys

with open('$file') as f:
    data = json.load(f)

canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
original = open('$file').read().strip()

if canonical != original:
    print(f'Non-canonical: $file')
    sys.exit(1)
"
done
```

### Test Helper

```python
def assert_canonical_json(filepath: str) -> None:
    """Assert that a JSON file is in canonical format."""
    import json

    with open(filepath) as f:
        data = json.load(f)

    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))

    with open(filepath) as f:
        original = f.read().strip()

    assert canonical == original, f"File {filepath} is not in canonical format"
```

---

## Exceptions

### Pretty-Printed Files

Documentation and human-readable config files MAY use pretty printing:
- `docs/**/*.json`
- `*.schema.json` (for readability)
- Files with `.pretty.json` suffix

### Excluded from Determinism

Files that inherently vary:
- Log files
- Temporary files
- Cache files

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Initial specification |
