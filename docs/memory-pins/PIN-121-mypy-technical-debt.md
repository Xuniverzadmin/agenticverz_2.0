# PIN-121: Mypy Technical Debt - Type Safety Remediation Plan

**Status:** ACTIVE
**Category:** Developer Tooling / Code Quality
**Created:** 2025-12-22
**Updated:** 2025-12-24
**Milestone:** M29 (Type Safety Zones)

---

## Summary

The codebase has 1,064 mypy type errors across 163 files. Rather than chase zero globally, we enforce **Type Safety Zones** with different strictness levels based on criticality.

**Current State:** 1,064 errors (Zone A: 38, Zone B: 630, Zone C: 396)
**Target State:** Zone A frozen at 38, no regressions in any zone
**Strategy:** Zone-based enforcement (see "Type Safety Zones" section below)

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

## Remediation Plan (Revised)

> **Principle:** We are not trying to reach zero warnings. We are trying to reach "warnings that matter."

### Phase 0: Stop the Bleeding (P1 Bugs) ✅ COMPLETE

**Target:** Fix None + operator issues that cause runtime errors

**Completed (2025-12-22):**
- [x] `backend/app/policy/compiler/tokenizer.py` - Added None guard in `read_operator()`
- [x] `backend/app/policy/ast/nodes.py` - Changed 7 fields from `ExprNode = None` to `Optional[ExprNode] = None`
- [x] `backend/app/policy/ast/nodes.py` - Added abstract methods to `ASTVisitor` class
- [x] `backend/app/policy/ast/visitors.py` - Removed duplicate `ASTVisitor`, added None checks
- [x] `backend/app/policy/validators/prevention_hook.py` - Fixed 2 Optional type declarations

**Result:** P1 None bugs in policy compiler = 0 errors

### Phase 1: Structural Cleanup (With Whitelist)

**Target:** Remove dead code without breaking dynamic dispatch

**Prerequisites:**
- Create whitelist for dynamic dispatch (skill registry, plugins, event handlers)
- Audit reflection usage in agent registry and SBA system
- Document entrypoints that shouldn't be pruned

**Files to address:**
- Registry patterns in `app/agents/services/registry_service.py`
- Dynamic skill loading in `app/skills/`
- Event handlers in `app/routing/`

### Phase 2: API Normalization

**Target:** Fix the 121 API warnings (not "Phase 4" material)

**Areas:**
- Response schema consistency across endpoints
- Error response format standardization
- Query parameter naming conventions

### Phase 3: Typing Hygiene

**Target:** Address remaining mypy errors (type assignment, visitor pattern)

**Files:**
- `backend/app/traces/redact.py` - Type assignment mismatches
- `backend/app/workflow/canonicalize.py` - Type re-assignments
- `backend/app/services/evidence_report.py` - None guards

### Phase 4: Tests & Coverage

**Target:** Add tests AFTER cleanup (not before)

**Rationale:** Coverage before cleanup = "tests for garbage"

---

## Prevention Completed

- [x] Added mypy to pre-commit hooks (warning mode) - PREV-13
- [x] Created PIN-121 documenting issues
- [x] Updated postflight.py with mypy category - PREV-15
- [x] CI mypy step (non-blocking) - PREV-14

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

---

## Type Safety Zones (M29 Update)

> **Strategy Shift:** Instead of chasing zero errors globally, we enforce strictness *where it matters*.

### Zone Overview

| Zone | Strictness | Enforcement | Baseline | Files |
|------|------------|-------------|----------|-------|
| **Zone A: Critical** | Strict | Pre-commit blocks | 38 | IR builder, evidence, pg_store, canonicalize |
| **Zone B: Standard** | Moderate | CI warns | 630 | API, skills, integrations, agents |
| **Zone C: Flexible** | Baseline only | Freeze | 400 | Metrics, workers, main.py, models |

**Total:** 1,064 errors across 3 zones (as of M29, 2025-12-24)

### Zone A: Critical (38 errors)

Correctness-critical paths where type bugs hide. **Pre-commit blocks on ANY increase.**

```
app/policy/ir/          # Intermediate representation
app/policy/ast/         # AST visitors
app/workflow/engine.py  # Workflow execution
app/workflow/canonicalize.py
app/services/certificate.py
app/services/evidence_report.py
app/traces/pg_store.py
app/utils/deterministic.py
app/utils/canonical_json.py
```

### Zone B: Standard (630 errors)

Business logic - warn on issues, don't block.

```
app/api/                # FastAPI routers
app/skills/             # Skill implementations
app/agents/             # SBA and agent registry
app/services/           # Business services
app/integrations/       # External integrations
app/memory/             # Memory system
app/policy/validators/  # Policy validation
```

### Zone C: Flexible (400 errors)

Infrastructure glue, metrics, utilities - known debt tolerated.

```
app/workflow/           # Metrics, logging
app/traces/             # Tracing (except pg_store)
app/utils/              # Utilities (except deterministic)
app/worker/             # Worker pool
app/workers/            # Background workers
app/main.py             # Lifecycle globals
app/models/             # SQLModel definitions
app/config/             # Configuration
```

---

## Zone Validation Script

**Location:** `backend/scripts/mypy_zones.py`

```bash
# Full zone check
python scripts/mypy_zones.py

# Zone A only (for pre-commit)
python scripts/mypy_zones.py --zone-a

# Verbose report
python scripts/mypy_zones.py --report

# Regenerate baseline
python scripts/mypy_zones.py --generate-baseline
```

**Sample Output:**
```
======================================================================
  MYPY TYPE SAFETY ZONES REPORT (PIN-121)
======================================================================

  Zone A (Critical)
    Errors:     38 (baseline: 38)
    Delta:       0
    Status:   ✅ PASS

  Zone B (Standard)
    Errors:    630 (baseline: 630)
    Delta:       0
    Status:   ✅ PASS

  Zone C (Flexible)
    Errors:    396 (baseline: 400)
    Delta:      -4
    Status:   ✅ PASS

----------------------------------------------------------------------
  Total Errors: 1064
  Overall:      ✅ PASS
======================================================================
```

---

## pyproject.toml Zone Configuration

The zone configuration is embedded in `pyproject.toml`:

```toml
# Zone A: Critical - check_untyped_defs, strict_optional
[[tool.mypy.overrides]]
module = ["app.policy.ir.*", "app.workflow.canonicalize", ...]
check_untyped_defs = true
strict_optional = true

# Zone B: Standard - warn_return_any, strict_optional
[[tool.mypy.overrides]]
module = ["app.api.*", "app.skills.*", ...]
warn_return_any = true
strict_optional = true

# Zone C: Flexible - relaxed, baseline freeze
[[tool.mypy.overrides]]
module = ["app.workflow.metrics", "app.traces.traces_metrics", ...]
warn_return_any = false
strict_optional = false
disable_error_code = ["misc", "assignment"]
```

---

## Updated Error Baseline (M29)

| Zone | Errors | Baseline | Status |
|------|--------|----------|--------|
| Zone A (Critical) | 38 | 38 | ✅ Frozen |
| Zone B (Standard) | 630 | 630 | ✅ Frozen |
| Zone C (Flexible) | 396 | 400 | ✅ Under budget |
| **Total** | **1,064** | **1,068** | **✅ PASS** |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Initial creation - 572 errors documented, 6 root causes identified |
| 2025-12-22 | Added PREV-13, PREV-14, PREV-15 prevention mechanisms |
| 2025-12-22 | **Phase 0 COMPLETE** - Fixed all P1 None bugs in policy compiler |
| 2025-12-22 | Revised roadmap based on expert feedback (cleanup before coverage) |
| 2025-12-24 | **M29 Update** - Introduced Type Safety Zones (A/B/C) |
| 2025-12-24 | Added zone validation script: `scripts/mypy_zones.py` |
| 2025-12-24 | Updated pyproject.toml with zone-based mypy overrides |
| 2025-12-24 | New baseline: 1,064 errors (38 A + 630 B + 396 C) |
