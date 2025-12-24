# Mypy Autofix System

Mechanical, enforceable type safety enforcement for AOS.

## Philosophy

This is **not** about "fixing typing properly". It's about:
- Mechanical transforms
- Zero inference
- Enforceable guardrails
- No velocity impact

## Quick Start

```bash
# Preview what would be fixed
python tools/mypy_autofix/apply.py --dry-run

# Auto-fix all zones
python tools/mypy_autofix/apply.py

# Zone A only (critical paths)
python tools/mypy_autofix/apply.py --zone-a

# Show detailed report
python tools/mypy_autofix/apply.py --report
```

## How It Works

1. **Run mypy** - Captures all errors with codes
2. **Parse errors** - Extracts file, line, code, message
3. **Match rules** - Looks up fix strategy in `rules.yaml`
4. **Apply macros** - Mechanical transforms from `macros.py`
5. **Report** - Shows what was changed

## Fix Patterns

| Error Code | Fix Applied | Example |
|------------|-------------|---------|
| `union-attr` | `assert x is not None` | Optional access without guard |
| `no-any-return` (bool) | `return bool(expr)` | Function returns Any |
| `no-any-return` (int) | `return int(expr)` | Function returns Any |
| `var-annotated` | `x: list[Any] = []` | Untyped variable |
| `valid-type` | `x: Callable[..., Any]` | Using `callable` as type |

## Zones

| Zone | Enforcement | Auto-Fix | Paths |
|------|-------------|----------|-------|
| **A** (Critical) | Block | Yes | policy/ir/, policy/ast/, deterministic_engine.py, etc. |
| **B** (Standard) | Warn | Yes | api/, skills/, agents/, services/ |
| **C** (Flexible) | None | No | workflow/, traces/, utils/, models/ |

## CI Integration

The CI workflow (`.github/workflows/mypy.yml`) will:

1. Run the autofix engine
2. Check if any files changed
3. **Fail if fixes were applied** (forces dev to commit them)
4. Run mypy check

This ensures:
- New errors get caught immediately
- Fixes are committed explicitly
- Baseline never drifts silently

## Adding New Rules

Edit `rules.yaml`:

```yaml
new-error-code:
  description: "What this error means"
  fix: macro_function_name
  auto: true
  zones: [A, B]
```

Then add the macro to `macros.py`:

```python
def macro_function_name(arg: str) -> str:
    return f"fixed code for {arg}"
```

## Hard Rules

These are **enforced**:

1. **No new `# type: ignore[union-attr]`**
2. **No blanket `ignore_errors = True`**
3. **Zone A blocks on ANY new error**
4. **All fixes must be committed explicitly**

## Files

```
tools/mypy_autofix/
├── __init__.py     # Package exports
├── macros.py       # Transform functions
├── rules.yaml      # Error code → fix mapping
├── apply.py        # Autofix engine
└── README.md       # This file
```

## Related

- `scripts/mypy_zones.py` - Zone validation script
- `PIN-121` - Mypy Technical Debt documentation
- `pyproject.toml` - mypy configuration with guardrails
