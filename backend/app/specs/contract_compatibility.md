# Contract Compatibility Matrix

**Version:** 1.0.0
**Last Updated:** 2025-12-01

---

## Overview

This document defines compatibility rules for AOS contracts (skills, planners, resources).
These rules determine when version bumps are required and when changes are breaking.

---

## Semantic Versioning Rules

### MAJOR (Breaking)
Increment MAJOR when making incompatible changes:

| Change Type | Example | Breaking? |
|------------|---------|-----------|
| Remove required input field | Remove `url` from http_call inputs | YES |
| Remove output field that callers depend on | Remove `status_code` from response | YES |
| Change field type | `status_code` from int to string | YES |
| Narrow input validation | Previously allowed null, now required | YES |
| Change error code semantics | `ERR_TIMEOUT` now means something different | YES |
| Remove skill from registry | Skill completely unavailable | YES |
| Change determinism mode | FULL → STRUCTURAL or NONE | YES |

### MINOR (Backwards Compatible)
Increment MINOR when adding functionality:

| Change Type | Example | Breaking? |
|------------|---------|-----------|
| Add optional input field | New `timeout_ms` param with default | NO |
| Add new output field | New `latency_ms` in response | NO |
| Widen input validation | Now accepts both string and int | NO |
| Add new error codes | New `ERR_DNS_FAILURE` | NO |
| Add new skill | Register new skill in registry | NO |
| Improve error messages | More descriptive error text | NO |

### PATCH (Bug Fixes)
Increment PATCH for backwards-compatible bug fixes:

| Change Type | Example | Breaking? |
|------------|---------|-----------|
| Fix incorrect output | Was returning wrong status code | NO |
| Fix crash/exception | Handler no longer throws | NO |
| Performance improvement | Faster execution | NO |
| Documentation update | Better docstrings | NO |

---

## Skill Contract Compatibility

### Input Schema Changes

```
BREAKING:
- Remove field from required inputs
- Change required field type
- Add new required field without default

NON-BREAKING:
- Add optional field with default
- Widen accepted types (str → str|int)
- Change validation to be more permissive
```

### Output Schema Changes

```
BREAKING:
- Remove field from output
- Change field type
- Change field semantics

NON-BREAKING:
- Add new field to output
- Add nested fields
- Add to enum values
```

### Stable Fields Changes

```
BREAKING:
- Change stable field from DETERMINISTIC to NON-DETERMINISTIC
- Remove stable field declaration

NON-BREAKING:
- Add new stable field
- Document existing behavior
```

---

## Planner Contract Compatibility

### Determinism Mode Changes

```
BREAKING:
- FULL → STRUCTURAL (loses byte-identical guarantee)
- FULL → NONE (loses all guarantees)
- STRUCTURAL → NONE (loses structure guarantee)

NON-BREAKING:
- STRUCTURAL → FULL (stricter guarantee)
- NONE → STRUCTURAL (adds guarantee)
- NONE → FULL (adds strictest guarantee)
```

### Plan Output Changes

```
BREAKING:
- Remove step fields (step_id, skill, params)
- Change step_id generation algorithm
- Change dependency resolution

NON-BREAKING:
- Add optional step fields
- Add metadata fields
- Add warnings
```

---

## Version Gating Rules

### Strict Mode
When `strict=True` in skill resolution:
- Required version MUST match exactly
- `1.2.3` only matches `1.2.3`

### Default Mode
When `strict=False` (default):
- Allows compatible versions
- `1.2.0` matches `1.2.x` and `1.x.x` where x >= 2
- Major version must match
- Minor version must be >= required

### Version Compatibility Check

```python
def is_version_compatible(required: str, actual: str, strict: bool = False) -> bool:
    """
    Check version compatibility.

    Args:
        required: Required version (e.g., "1.2.0")
        actual: Actual version available (e.g., "1.3.0")
        strict: If True, require exact match

    Returns:
        True if compatible
    """
    if strict:
        return required == actual

    req_parts = required.split(".")
    act_parts = actual.split(".")

    # Major must match exactly
    if req_parts[0] != act_parts[0]:
        return False

    # Minor must be >= required
    if int(act_parts[1]) < int(req_parts[1]):
        return False

    return True
```

---

## Contract Diffing

### Diff Categories

| Category | Severity | Action |
|----------|----------|--------|
| `added_fields` | INFO | Log for awareness |
| `removed_fields` | ERROR | Block deployment |
| `type_changed` | ERROR | Block deployment |
| `validation_narrowed` | WARNING | Review required |
| `validation_widened` | INFO | Log for awareness |
| `default_changed` | WARNING | Review required |

### Diff Output Format

```json
{
  "skill_id": "skill.http_call",
  "old_version": "1.0.0",
  "new_version": "1.1.0",
  "breaking_changes": [],
  "non_breaking_changes": [
    {
      "type": "field_added",
      "path": "inputs.timeout_ms",
      "description": "Added optional timeout_ms input"
    }
  ],
  "warnings": [],
  "compatible": true,
  "recommended_bump": "MINOR"
}
```

---

## CI Integration

### Pre-Commit Checks

```yaml
# .github/workflows/ci.yml
schema-compatibility:
  runs-on: ubuntu-latest
  steps:
    - name: Check contract compatibility
      run: |
        python -m app.skills.registry_v2 diff-contracts \
          --old-version ${{ github.event.before }} \
          --new-version ${{ github.sha }}

    - name: Fail on breaking changes
      if: ${{ steps.diff.outputs.breaking == 'true' }}
      run: exit 1
```

### Version Bump Enforcement

```yaml
changelog-check:
  runs-on: ubuntu-latest
  steps:
    - name: Check version bump
      run: |
        # If contracts changed, version must be bumped
        python -c "
        import json
        diff = json.load(open('contract_diff.json'))
        if diff['breaking_changes']:
            assert diff['new_version'].split('.')[0] > diff['old_version'].split('.')[0], \
                'Breaking change requires MAJOR bump'
        "
```

---

## Examples

### Example 1: Adding Optional Field (MINOR)

```python
# Before (v1.0.0)
inputs_schema = {
    "url": {"type": "string", "required": True}
}

# After (v1.1.0) - NON-BREAKING
inputs_schema = {
    "url": {"type": "string", "required": True},
    "timeout_ms": {"type": "integer", "required": False, "default": 30000}
}
```

### Example 2: Removing Field (MAJOR)

```python
# Before (v1.0.0)
outputs_schema = {
    "status_code": {"type": "integer"},
    "body": {"type": "any"},
    "headers": {"type": "object"}
}

# After (v2.0.0) - BREAKING
outputs_schema = {
    "status_code": {"type": "integer"},
    "body": {"type": "any"}
    # headers removed - BREAKING
}
```

### Example 3: Type Change (MAJOR)

```python
# Before (v1.0.0)
outputs_schema = {
    "count": {"type": "integer"}
}

# After (v2.0.0) - BREAKING
outputs_schema = {
    "count": {"type": "string"}  # Changed from int to string
}
```

---

## Summary

| Change | Version Bump | CI Action |
|--------|-------------|-----------|
| Remove field | MAJOR | Block |
| Change type | MAJOR | Block |
| Add required field | MAJOR | Block |
| Add optional field | MINOR | Allow |
| Add output field | MINOR | Allow |
| Bug fix | PATCH | Allow |
| Documentation | PATCH | Allow |

---

## References

- `app/skills/registry_v2.py` - Version gating implementation
- `app/specs/determinism_and_replay.md` - Determinism rules
- `app/specs/error_taxonomy.md` - Error code stability rules
