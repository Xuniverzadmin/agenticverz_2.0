# PIN-109: Preflight/Postflight v2.0 - Semantic Route Validation

**Status:** ✅ COMPLETE
**Created:** 2025-12-20
**Category:** Developer Tooling / Code Quality / CI

---

## Summary

Upgraded the developer tooling (preflight/postflight) from regex-based to AST-based analysis with semantic collision detection. This addresses GPT's engineering review feedback and provides more robust route validation.

---

## What Changed

### 1. Preflight v2.0 - AST-Based Route Extraction

**Before:** Regex-based route extraction was fragile with multi-line decorators
**After:** Uses Python's `ast` module for reliable parsing

Key classes added to `scripts/ops/preflight.py`:

```python
class RouteSegment:
    """Represents a path segment with type awareness."""
    - Parses {param:type} constraints (uuid, int, path)
    - can_match() method for semantic comparison

class ASTRouteExtractor(ast.NodeVisitor):
    """Extract routes using AST parsing for reliability."""
    - Visits function definitions
    - Parses @router.get/post/etc decorators
    - Extracts path, method, line number

class SemanticCollisionDetector:
    """Detect actual route collisions based on matching semantics."""
    - Only flags when param shadows static at FIRST divergence point
    - Understands that static-prefix routes take priority
```

### 2. Improved Collision Detection Logic

The key insight: only flag as problematic when, at the **first segment** where routes differ, the earlier route has a parameter (less specific) and the later has static (more specific).

**Example - No longer false positive:**
- `/by-hash/{root_hash}` vs `/{trace_id}/mismatches`
- At position 0: "by-hash" (static) vs "{trace_id}" (param)
- Earlier is MORE specific → correct order → no issue

**Example - Still catches real bugs:**
- `/{tenant_id}` vs `/at-risk`
- At position 0: "{tenant_id}" (param) vs "at-risk" (static)
- Earlier is LESS specific → shadows static → ERROR

### 3. Runtime Validation in main.py

Added `validate_route_order()` function called during FastAPI lifespan startup:

```python
def validate_route_order(app: FastAPI) -> list:
    """Runtime validation of route ordering."""
    # Uses same improved logic as preflight
    # Logs warnings if issues detected at startup
```

### 4. Contract Tests (test_route_contracts.py)

12 tests verifying route resolution behavior:

| Test Class | Purpose |
|------------|---------|
| TestOpsRouteContracts | /customers/at-risk, /customers/{tenant_id} |
| TestOperatorRouteContracts | /replay/batch before /replay/{call_id} |
| TestTracesRouteContracts | /mismatches/bulk-report ordering |
| TestAgentsRouteContracts | /sba/version before /sba/{agent_id} |
| TestRouteValidationFunction | Tests validate_route_order itself |
| TestPIN108Regressions | UUID validation (at-risk, batch, version) |

### 5. Postflight Warning Budgets

Added to `scripts/ops/postflight.py`:

```python
DEFAULT_BUDGETS = {
    'syntax': {'error': 0, 'warning': 10, 'suggestion': 100},
    'imports': {'error': 0, 'warning': 150, 'suggestion': 200},
    'security': {'error': 0, 'warning': 10, 'suggestion': 50},
    # ... more categories
}
```

CLI options:
- `--save-baseline`: Save current counts to `.postflight-baseline.json`
- `--enforce-budget`: Fail if new warnings exceed budget
- `--show-budgets`: Display configured limits

---

## Files Modified

| File | Change |
|------|--------|
| `scripts/ops/preflight.py` | AST extraction, semantic collision detection |
| `backend/app/main.py` | Runtime route validation hook |
| `backend/tests/test_route_contracts.py` | New file - 12 contract tests |
| `scripts/ops/postflight.py` | Warning budgets, baseline tracking |
| `.postflight-baseline.json` | New file - current warning counts |

---

## Running the Tools

### Preflight (before code changes)
```bash
python3 scripts/ops/preflight.py --routes
```

### Postflight (after code changes)
```bash
# Quick check (syntax, imports, security only)
python3 scripts/ops/postflight.py --quick backend/

# Full check with baseline
python3 scripts/ops/postflight.py --full --save-baseline backend/

# Enforce budgets (CI mode)
python3 scripts/ops/postflight.py --full --enforce-budget backend/
```

### Contract Tests
```bash
PYTHONPATH=backend python3 -m pytest backend/tests/test_route_contracts.py -v
```

---

## Auto-Run Integration

See `scripts/ops/job_wrapper.sh` for automatic pre/post job execution:

```bash
./scripts/ops/job_wrapper.sh "your command here"
```

This runs:
1. `preflight.py --routes` before the job
2. Your command
3. `postflight.py --quick` after the job

---

## Verification

```bash
# All should pass
python3 scripts/ops/preflight.py --routes  # ✅ PASS
PYTHONPATH=backend python3 -m pytest backend/tests/test_route_contracts.py  # 12 passed
```

---

## Related PINs

- **PIN-108**: Initial preflight/postflight implementation
- **PIN-097**: Prevention System v1.1 (SQLModel linting)
- **PIN-106**: SQLModel Linter Fixes

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-12-20 | v2.0 | AST-based extraction, semantic collision detection |
| 2025-12-20 | v2.0 | Runtime validation hook in main.py |
| 2025-12-20 | v2.0 | Contract tests (12 tests) |
| 2025-12-20 | v2.0 | Warning budgets + baseline tracking |
