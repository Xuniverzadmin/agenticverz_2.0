# PIN-121: Mypy Technical Debt - Type Safety Remediation Plan

**Status:** ACTIVE
**Category:** Developer Tooling / Code Quality
**Created:** 2025-12-22
**Updated:** 2025-12-22
**Milestone:** M25 (Technical Debt)

---

## Summary

The codebase has 572 mypy type errors across 118 files. This PIN documents the error categories, root causes, and a phased remediation plan with prevention mechanisms to avoid future type safety regressions.

**Current State:** 572 errors in 118 files
**Target State:** 0 blocking errors, mypy --strict on new code

---

## Error Categorization

| Category | Count | Severity | Priority |
|----------|-------|----------|----------|
| SQLModel `table` keyword | 27 | Low | P3 - Known mypy limitation |
| `None` + operator issues | 14 | Medium | P1 - Immediate fix |
| Type assignment mismatches | 13 | Medium | P2 - Gradual fix |
| Collection indexing issues | 11 | Medium | P2 - Gradual fix |
| `datetime.desc()` SQLAlchemy | 11 | Low | P3 - False positive |
| Visitor pattern type issues | 10 | Low | P2 - Structural |
| Invalid base class "Base" | 8 | Low | P3 - SQLModel pattern |
| Function signature mismatches | 7 | Medium | P2 - Gradual fix |
| Missing type annotations | ~400 | Low | P3 - Gradual improvement |

---

## Root Cause Analysis

### RC-1: SQLModel `table=True` Keyword (27 errors)

**Symptom:** `Unexpected keyword argument "table" for "__init_subclass__" of "object"`

**Root Cause:** mypy doesn't understand SQLModel's metaclass magic that enables `table=True`.

**Example:**
```python
class Run(SQLModel, table=True):  # mypy error: [call-arg]
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
```

**Status:** Known SQLModel limitation. No fix needed.

**Workaround (if strict mode required):**
```python
class Run(SQLModel, table=True):  # type: ignore[call-arg]
    ...
```

---

### RC-2: None + Operator Issues (14 errors)

**Symptom:** `Unsupported operand types for +: "None" and "str"`

**Root Cause:** Variables that can be `None` are used in operations without explicit None checks.

**Example:**
```python
# BAD
value = config.get('key')
result = value + " suffix"  # Error if value is None

# GOOD
value = config.get('key')
if value is not None:
    result = value + " suffix"
```

**Locations:**
- `backend/app/policy/compiler/tokenizer.py:246, 252, 253, 255`
- `backend/app/policy/validators/prevention_hook.py:56, 78`
- `backend/app/policy/ast/nodes.py:173, 174, 211, 212, 223, 260, 271`

**Fix Priority:** P1 - These are genuine bugs that could cause runtime errors.

---

### RC-3: Invalid Base Class "Base" (8 errors)

**Symptom:** `Variable "Base" is not valid as a type` / `Invalid base class "Base"`

**Root Cause:** SQLAlchemy's `declarative_base()` returns a dynamic type that mypy can't introspect.

**Example:**
```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()  # Type is 'Any'

class MyModel(Base):  # mypy error: Invalid base class
    ...
```

**Locations:**
- `backend/app/models/m10_recovery.py:40, 102, 207`
- `backend/app/models/costsim_cb.py:30, 77, 137, 205, 290`

**Fix:** Use type alias or `# type: ignore[misc]`.

---

### RC-4: Visitor Pattern Missing Methods (10 errors)

**Symptom:** `"ASTVisitor" has no attribute "visit_program"`

**Root Cause:** Abstract visitor pattern expects methods that aren't defined in base class.

**Location:** `backend/app/policy/ast/nodes.py:88-275`

**Fix:** Define abstract methods in `ASTVisitor` base class with `NotImplementedError`.

---

### RC-5: Union Type Attribute Access (14 errors)

**Symptom:** `Item "None" of "X | None" has no attribute "y"`

**Root Cause:** Accessing attributes on Optional types without None checks.

**Example:**
```python
# BAD
cert: Optional[Certificate] = get_cert()
print(cert.certificate_id)  # Error: cert might be None

# GOOD
if cert is not None:
    print(cert.certificate_id)
```

**Location:** `backend/app/services/evidence_report.py:862-920`

---

### RC-6: Type Assignment Mismatches (13 errors)

**Symptom:** `Incompatible types in assignment (expression has type "dict", target has type "str")`

**Root Cause:** Variables re-assigned with different types.

**Locations:**
- `backend/app/traces/redact.py:119, 121, 140, 142`
- `backend/app/workflow/canonicalize.py:440, 441`

---

## Remediation Plan

### Phase 1: Prevention (Immediate)

**Completed:**
- [x] Added mypy to pre-commit hooks (warning mode)
- [x] Created PIN-121 documenting issues
- [x] Updated postflight.py with mypy category

**In Progress:**
- [ ] Configure mypy for gradual adoption (`--strict` on new files)
- [ ] Add CI mypy step (non-blocking initially)

### Phase 2: Critical Fixes (P1)

**Target:** Fix 14 None + operator issues

Files to fix:
1. `backend/app/policy/compiler/tokenizer.py` - 4 errors
2. `backend/app/policy/validators/prevention_hook.py` - 2 errors
3. `backend/app/policy/ast/nodes.py` - 8 errors

### Phase 3: Gradual Fix (P2)

**Target:** Fix type assignment and visitor pattern issues

1. Add abstract methods to `ASTVisitor` base class
2. Fix type assignments in `redact.py` and `canonicalize.py`
3. Add None guards in `evidence_report.py`

### Phase 4: Type Stubs & Annotations (P3)

**Target:** Suppress known false positives

1. Add `# type: ignore[call-arg]` for SQLModel `table=True`
2. Add `# type: ignore[misc]` for `Base` inheritance
3. Install missing type stubs (`types-PyYAML`)

---

## Configuration

### pyproject.toml (Recommended)

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
show_error_codes = true

# Gradual adoption - strict on new code
[[tool.mypy.overrides]]
module = [
    "app.policy.compiler.*",
    "app.policy.validators.*",
    "app.services.evidence_report",
]
strict = true
warn_unreachable = true

# Known SQLModel limitations - suppress false positives
[[tool.mypy.overrides]]
module = ["app.db", "app.models.*"]
disable_error_code = ["call-arg", "misc"]
```

---

## Prevention Mechanisms

### PREV-13: Mypy Pre-Commit (Warning Mode)

**Rule:** All commits run mypy on changed files. New errors generate warnings.

**Implementation:**
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.8.0
  hooks:
    - id: mypy
      additional_dependencies:
        - types-PyYAML
      args:
        - --ignore-missing-imports
        - --show-error-codes
```

---

### PREV-14: CI Mypy Step (Non-Blocking)

**Rule:** CI runs mypy and reports errors, but doesn't block merge (initially).

**Implementation:**
```yaml
# .github/workflows/ci.yml
mypy-check:
  runs-on: ubuntu-latest
  continue-on-error: true  # Non-blocking initially
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
    - run: pip install mypy types-PyYAML
    - run: |
        mypy backend/app/ --ignore-missing-imports 2>&1 | tee mypy-output.txt
        echo "MYPY_ERRORS=$(wc -l < mypy-output.txt)" >> $GITHUB_ENV
    - run: |
        if [ "$MYPY_ERRORS" -gt 600 ]; then
          echo "::error::Mypy errors increased from baseline (572)"
          exit 1
        fi
```

---

### PREV-15: Postflight Mypy Category

**Rule:** Postflight reports mypy error counts as part of code hygiene.

**Implementation:** Added to `postflight.py` in `check_mypy()` method.

---

## Error Baseline

Track progress against this baseline:

| File Category | Errors | Date |
|---------------|--------|------|
| `backend/app/db.py` | 11 | 2025-12-22 |
| `backend/app/models/*.py` | 18 | 2025-12-22 |
| `backend/app/policy/ast/nodes.py` | 20 | 2025-12-22 |
| `backend/app/policy/compiler/*.py` | 7 | 2025-12-22 |
| `backend/app/services/evidence_report.py` | 11 | 2025-12-22 |
| `backend/app/traces/*.py` | 6 | 2025-12-22 |
| Other files | ~500 | 2025-12-22 |
| **Total** | **572** | **2025-12-22** |

---

## Related PINs

- PIN-120: Test Suite Stabilization & Prevention
- PIN-108: Developer Tooling - Preflight/Postflight
- PIN-119: SQLModel Session Safety
- PIN-097: Prevention System v1.1

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Initial creation - 572 errors documented, 6 root causes identified |
| 2025-12-22 | Added PREV-13, PREV-14, PREV-15 prevention mechanisms |
