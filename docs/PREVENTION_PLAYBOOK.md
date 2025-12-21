# Prevention Playbook - Keeping Code Quality Checks Updated

This document outlines the process for maintaining and updating our prevention systems when new bug patterns are discovered.

## Prevention Systems Overview

| System | Location | Purpose |
|--------|----------|---------|
| SQLModel Pattern Linter | `scripts/ops/lint_sqlmodel_patterns.py` | Detect Row tuple extraction bugs |
| API Wiring Check | `scripts/ops/check_api_wiring.py` | Validate endpoint configuration |
| Frontend API ID Linter | `scripts/ops/lint_frontend_api_calls.py` | Detect ID type mismatches in API calls |
| DB Helpers | `backend/app/db_helpers.py` | Safe query helper functions |
| CI Consistency Check | `scripts/ops/ci_consistency_check.sh` | Comprehensive CI validation |
| Pre-commit Hooks | `.pre-commit-config.yaml` | Pre-push code quality gates |

## When to Update Prevention Systems

Update the prevention systems whenever you encounter:

1. **A bug that slipped through** - Add detection for that pattern
2. **A new unsafe pattern** - Document and add linting for it
3. **A common mistake** - Create a helper function to prevent it
4. **An integration issue** - Add wiring check validation

## Process: Adding a New Pattern to Prevention

### Step 1: Document the Issue

Create a brief issue record in the linter file:

```python
# Issue: <description>
# Discovered: <date>
# Root cause: <technical explanation>
# Fix pattern: <the correct way to do it>
```

### Step 2: Add Detection Pattern

For SQLModel issues, edit `scripts/ops/lint_sqlmodel_patterns.py`:

```python
UNSAFE_PATTERNS = [
    # ... existing patterns ...
    {
        "regex": r"<regex pattern to match unsafe code>",
        "message": "<what's wrong>",
        "suggestion": "<how to fix it>",
    },
]
```

### Step 3: Add Safe Pattern (if applicable)

If there's a safe alternative, add it to `SAFE_PATTERNS`:

```python
SAFE_PATTERNS = [
    # ... existing patterns ...
    r"<regex that matches the safe version>",
]
```

### Step 4: Add Helper Function (if needed)

For common patterns, add a helper to `backend/app/db_helpers.py`:

```python
def query_<new_pattern>(session: Session, ...) -> <return_type>:
    """
    <Description of what this helper does safely>

    Example:
        <usage example>
    """
    # Safe implementation
    ...
```

### Step 5: Test the New Check

```bash
# Test the linter catches the issue
python scripts/ops/lint_sqlmodel_patterns.py backend/app/

# Run full CI check
bash scripts/ops/ci_consistency_check.sh
```

### Step 6: Commit the Prevention Update

```bash
git add scripts/ops/lint_sqlmodel_patterns.py
git add backend/app/db_helpers.py  # if modified
git commit -m "prevention: Add detection for <issue description>

- Added pattern: <brief pattern description>
- Added helper: <helper name if applicable>
- Discovered in: <file/feature where issue was found>
"
```

## Example: Adding the Row Tuple Pattern (Historical)

This is how we added the SQLModel Row tuple detection:

### The Issue
```
Error: AttributeError: 'id' when accessing session.exec(stmt).first().id
Root cause: .first() returns Row tuple (Model,) not Model
```

### The Pattern Added
```python
{
    "regex": r"session\.exec\([^)]+\)\.first\(\)\.\w+",
    "message": "Unsafe: accessing attribute on .first() result (Row tuple)",
    "suggestion": "Extract model first: row = session.exec(stmt).first(); obj = row[0] if row else None",
}
```

### The Safe Helper Added
```python
def query_one(session: Session, stmt) -> Optional[Any]:
    row = session.exec(stmt).first()
    return row[0] if row else None
```

## Example: Adding the ID Type Mismatch Pattern (2025-12-21)

This is how we added the Frontend API ID Type detection:

### The Issue
```
Error: POST /guard/replay/inc_demo_4a5e594b 404 (Not Found)
Root cause: onReplay(incident.id) passed incident_id but endpoint expected call_id
```

### The Pattern Added
```python
# In scripts/ops/lint_frontend_api_calls.py
{
    "name": "incident_id_in_replay",
    "description": "incident.id used in replay context (should be call_id)",
    "regex": r"(?:onReplay|replay|Replay)\s*\(\s*(?:incident|inc)\.id\s*\)",
    "suggestion": "Use incident.call_id instead of incident.id for replay",
    "severity": "error",
}
```

### The Fix Applied
```typescript
// Before (wrong):
onReplay(incident.id);

// After (correct):
onReplay(incident.call_id);
```

### API ID Type Contracts
| Endpoint Pattern | Expected ID Type | Prefix |
|-----------------|------------------|--------|
| `/replay/{id}` | call_id | `call_` |
| `/incidents/{id}` | incident_id | `inc_` |
| `/keys/{id}` | key_id | varies |

## Checklist for New Bug Patterns

When you find a new bug pattern, go through this checklist:

- [ ] Is this a repeatable pattern that could occur elsewhere?
- [ ] Can we detect it with regex or AST analysis?
- [ ] Is there a safe helper function we should create?
- [ ] Should this be a warning or error in CI?
- [ ] Have we documented the fix pattern?
- [ ] Have we tested the detection works?
- [ ] Have we committed the prevention update?

## Integration Points

### CI Pipeline
The `ci_consistency_check.sh` script runs all checks. To add a new check:

```bash
check_<new_check>() {
    header "<New Check Name>"
    if <check command>; then
        log_ok "<Success message>"
    else
        log_warn "<Failure message>"
    fi
}

# Add to main flow
check_<new_check>
```

### Pre-commit Hooks
For checks that should run before every commit:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: <new-check-id>
      name: <New Check Name>
      entry: python scripts/ops/<new_check>.py
      language: python
      types: [python]
      pass_filenames: false
```

## Quarterly Review

Every quarter, review the prevention systems:

1. **Check effectiveness**: Are the patterns catching real issues?
2. **Reduce false positives**: Are there safe patterns we should exclude?
3. **Update documentation**: Are the fix suggestions still accurate?
4. **Performance**: Are the checks fast enough for CI?

## Contact

When in doubt about whether to add a prevention pattern:
- If it caught you once, it will catch someone else
- If it took more than 10 minutes to debug, it's worth preventing
- If it affects multiple files, definitely add prevention

---

*Last updated: 2025-12-19*
*Prevention system version: 1.0*
