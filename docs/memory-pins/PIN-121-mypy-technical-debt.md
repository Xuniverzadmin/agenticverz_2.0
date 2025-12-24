# PIN-121: Mypy Technical Debt - Type Safety Remediation Plan

**Status:** ACTIVE
**Category:** Developer Tooling / Code Quality
**Created:** 2025-12-22
**Updated:** 2025-12-24
**Milestone:** M29 (Type Safety Zones)

---

## Summary

The codebase has 1,064 mypy type errors across 163 files. Rather than chase zero globally, we enforce **Type Safety Zones** with different strictness levels based on criticality.

**Current State:** 999 errors (Zone A: **0** ✅, Zone B: ~600, Zone C: ~400)
**Target State:** Zone A maintained at 0, no regressions in any zone
**Strategy:** Zone-based enforcement + Steady-State Policy (see sections below)

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

## Updates

## 2025-12-24: Mypy Autofix Macro System Deployed

**Status:** Production-ready autofix system for mechanical type fixes

### Files Created

```
backend/tools/mypy_autofix/
├── __init__.py      # Package exports
├── macros.py        # 10 transform functions
├── rules.yaml       # Error code → fix mapping + zones
├── apply.py         # Autofix engine
└── README.md        # Documentation

.github/workflows/
└── mypy-autofix.yml # CI workflow
```

### Macro Functions (macros.py)

| Macro | Purpose |
|-------|---------|
| `guard_optional` | Insert `assert x is not None` |
| `cast_expr` | Wrap in `cast(Type, expr)` |
| `return_cast` | Wrap return in cast |
| `bool_wrap` | Wrap in `bool()` for no-any-return |
| `int_wrap` | Wrap in `int()` |
| `float_wrap` | Wrap in `float()` |
| `callable_fix` | Fix `callable` → `Callable[..., Any]` |
| `list_annotation` | Add `x: list[Any] = []` |
| `dict_annotation` | Add `x: dict[str, Any] = {}` |
| `unreachable` | Add `raise AssertionError("unreachable")` |

### Autofix Engine (apply.py)

- Parses mypy output with error codes
- Extracts variable names from source lines
- Applies mechanical transforms
- Reports applied/skipped/failed fixes

### CI Integration

```yaml
# .github/workflows/mypy-autofix.yml
- Runs autofix in dry-run mode
- Checks Zone A (blocks on failure)
- Verifies no uncommitted fixes
- Produces GitHub Actions summary
```

### Usage

```bash
python tools/mypy_autofix/apply.py --dry-run    # Preview
python tools/mypy_autofix/apply.py              # Apply all
python tools/mypy_autofix/apply.py --zone-a     # Zone A only
python tools/mypy_autofix/apply.py --report     # Detailed report
```

### Current Stats (Updated 2025-12-24)

```
Total errors:   1026
Auto-fixable:   148 (guards, wraps, SQLAlchemy casts)
Manual review:  876 (complex patterns)
Coverage:       14.4%
```

### Extended Macros (2025-12-24)

| Category | Macro | Purpose | Auto-Fix |
|----------|-------|---------|----------|
| SQLAlchemy | `sa_expr` | Cast `.desc()`, `.ilike()`, `.asc()` | ✅ Yes |
| Prometheus | `prom_metric` | Add `Any` annotation to metrics | ✅ Yes |
| FastAPI | `fastapi_dep_guard` | Guard Depends() injections | ✅ Yes |
| Pydantic | `pydantic_dict_cast` | Cast `.dict()` output | ✅ Yes |
| Async | `await_cast` | Cast awaited expressions | ✅ Yes |

### Fix Categories Applied

```
[guard]       99 fixes - assert x is not None
[sqlalchemy]  21 fixes - cast(Any, col).desc()
[bool_wrap]   15 fixes - return bool(expr)
[int_wrap]    12 fixes - return int(expr)
[callable]     1 fix   - Callable[..., Any]
```

### Fixed-Debt Watermark Rule

> **Any mypy error that has an autofix macro MUST NOT exist in `main`.**

If autofix can fix it, it should be fixed. Period.

Covered patterns that are now **forbidden to exist unresolved**:
- `union-attr` on Optional types → must have guard
- `no-any-return` for bool/int → must have wrap
- `attr-defined` for SQLAlchemy methods → must have cast or ignore
- `valid-type` for callable → must use `Callable[..., Any]`

### CI No-Regression Gate

```bash
# .github/workflows/mypy-autofix.yml
- name: Verify no autofix-able errors
  run: |
    python tools/mypy_autofix/apply.py
    if ! git diff --exit-code; then
      echo "::error::Autofix generated changes. Commit them."
      exit 1
    fi
```

### Guardrails Added (pyproject.toml)

```toml
warn_unused_ignores = true    # Catch stale ignores
disallow_any_unimported = false
# HARD RULES:
#   - No new `# type: ignore[union-attr]`
#   - No blanket `ignore_errors = True`
#   - Zone A blocks on ANY new error
```


## 2025-12-24: Zone A Mypy Errors Eliminated

**Status:** Zone A now has **0 errors** (down from 38 baseline)

### Files Fixed (11 files, 38 errors)

| File | Errors | Fix Pattern |
|------|--------|-------------|
| `services/evidence_report.py` | 12 | `if cert is None: return` guard |
| `policy/ir/ir_builder.py` | 9 | `assert x is not None` for Optional fields |
| `traces/pg_store.py` | 5 | `list[Any]` typing, `bool()` wrap, `Any` type |
| `policy/runtime/deterministic_engine.py` | 4 | `Callable[..., Any]` annotation, `bool()` wrap |
| `workflow/canonicalize.py` | 3 | `cast(Dict[str, Any], ...)`, explicit dict type |
| `utils/canonical_json.py` | 1 | `set()` wrap for frozenset argument |
| `utils/deterministic.py` | 1 | `float()` wrap for struct.unpack |
| `policy/ir/symbol_table.py` | 1 | `rules: List[Symbol] = []` annotation |
| `services/certificate.py` | 1 | `if self.secret is None: return ""` guard |
| `workflow/engine.py` | 1 | `int()` wrap for return value |
| `policy/ast/visitors.py` | 1 | Added `__all__` with explicit exports |

### Fix Patterns Used
- **Guards:** `if x is None: return` for Optional types
- **Asserts:** `assert x is not None` before accessing Optional fields
- **Casts:** `cast(Type, value)` for return type mismatches
- **Wraps:** `bool()`, `int()`, `float()` for explicit type conversion
- **Annotations:** Explicit type annotations for untyped variables
- **Exports:** `__all__` lists for module re-exports

### Validation
```
Zone A (Critical): 0 errors (baseline: 38), Delta: -38 ✅ PASS
```

### Baseline Update Required
Update `scripts/mypy_zones.py` BASELINE:
```python
BASELINE = {
    "zone_a": 0,   # Was 38, now 0
    "zone_b": 630,
    "zone_c": 400,
}
```

---

## 📕 Mypy "Never Fix" Ledger

> **Purpose:** Document mypy errors that are **intentionally accepted** and **permanently excluded** from cleanup.
> This is a **policy artifact**, not a TODO list.

### 🔒 Global Rule

> Errors listed in this ledger are **explicitly accepted technical debt**.
> They **must not** be fixed unless the underlying architecture changes.
> Reducing the raw mypy error count is **not a goal**.

---

## Category A — Structural Impossibilities

**(Do not fix. Ever.)**

These are **fundamentally untypable** in Python without lying to the type system.

**Criteria:**
- Relies on runtime mutation, reflection, or metaclasses
- Type would require re-implementing framework internals
- "Correct typing" would be more misleading than `Any`

---

### A-01: SQLAlchemy Column Assignment Instrumentation
- **Error codes:** `assignment`
- **Count:** 84
- **Example:** `model.is_resolved = True` → `Incompatible types (bool vs Column[bool])`
- **Files:** `circuit_breaker_async.py`, `alert_worker.py`, `checkpoint_offload.py`
- **Reason:** SQLAlchemy's descriptor protocol intercepts assignment. At runtime `bool` is correct; mypy sees `Column[bool]`.
- **Decision:** Never fix. This is how ORMs work.

---

### A-02: SQLAlchemy/SQLModel Session Overloads
- **Error codes:** `call-overload`
- **Count:** 74
- **Example:** `session.exec(select(Model))` → `No overload variant matches`
- **Files:** `api/guard.py` (39), `api/v1_killswitch.py` (13), `api/v1_proxy.py` (11)
- **Reason:** SQLModel's `exec()` wraps SQLAlchemy with different signatures. Stubs incomplete.
- **Decision:** Never fix. Upstream stub issue.

---

### A-03: SQLAlchemy Row Indexing
- **Error codes:** `index`
- **Count:** 49
- **Example:** `row[0]` → `Value of type "Row[Any] | None" is not indexable`
- **Files:** `registry_service.py`, `worker_service.py`, `policy/engine.py`
- **Reason:** Raw SQL queries return `Row | None`. Requires None check + cast at every access.
- **Decision:** Never fix. Would need wrapper abstraction (not worth it).

---

### A-04: Sync/Async Dual-Mode Await
- **Error codes:** `misc`
- **Count:** 28
- **Example:** `await maybe_async()` → `Incompatible types in "await" (Awaitable[T] | T)`
- **Files:** `routing/learning.py`, `routing/governor.py`, `routing/feedback.py`, `routing/care.py`
- **Reason:** Functions that work both sync and async return `Awaitable[T] | T`. Mypy can't narrow.
- **Decision:** Never fix. Pattern is intentional for Redis client compatibility.

---

### A-05: SQLAlchemy Declarative Base
- **Error codes:** `valid-type`, `misc`
- **Count:** 9
- **Example:** `class Model(Base)` → `Invalid base class "Base"`
- **Files:** `models/costsim_cb.py`, `models/m10_recovery.py`
- **Reason:** `declarative_base()` returns dynamic type. Mypy can't introspect metaclass.
- **Decision:** Never fix. Standard SQLAlchemy pattern.

---

### A-06: Lazy Module/Class Loading
- **Error codes:** `misc`, `assignment`
- **Count:** 6
- **Example:** `PostgresTraceStore: type[...] = None` → `Cannot assign to a type`
- **Files:** `traces/__init__.py`, `agents/skills/agent_spawn.py`
- **Reason:** Deferred imports to avoid circular dependencies. Assigned at module load time.
- **Decision:** Never fix. Import structure requires this.

---

**Category A Total: 250 errors**

---

## Category B — Diminishing Returns

**(Fixable, but not worth it.)**

These *can* be typed, but doing so provides **zero safety** and **high maintenance cost**.

**Criteria:**
- Glue code, observability, metrics
- Test-only utilities
- One-off adapters, debug tooling
- External SDK wrappers

---

### B-01: Prometheus Metrics Stub Mismatches
- **Error codes:** `arg-type`
- **Count:** 20
- **Example:** `Histogram(..., labelnames=[...])` → `expected "str"`
- **Files:** `utils/metrics_helpers.py`, `workflow/metrics.py`
- **Risk:** None (metrics only affect observability)
- **Cost to fix:** Would need custom stubs or casts everywhere
- **Decision:** Accept debt.

---

### B-02: Literal vs String in Event Handlers
- **Error codes:** `arg-type`
- **Count:** 12
- **Example:** `category="custom"` → `expected Literal['safety', 'privacy', ...]`
- **Files:** `integrations/events.py`
- **Risk:** Low (runtime validates)
- **Cost to fix:** Would need to change all dynamic category sources to enums
- **Decision:** Accept debt.

---

### B-03: `object` from Untyped Boundaries
- **Error codes:** `operator`, `arg-type`
- **Count:** 45
- **Example:** `time.time() - start` → `Unsupported operand types ("object" and "float")`
- **Files:** `worker/runtime/core.py`, `integrations/cost_bridges.py`
- **Risk:** None (values are correct at runtime)
- **Cost to fix:** Cast every Redis/JSON/time boundary
- **Decision:** Accept debt.

---

### B-04: Annotation Unchecked
- **Error codes:** `annotation-unchecked`
- **Count:** 41
- **Example:** Type annotations in untyped function bodies
- **Risk:** None (informational only)
- **Cost to fix:** Add return type annotations to hundreds of functions
- **Decision:** Accept debt. Not actionable errors.

---

### B-05: Dict-Item Type Mismatches
- **Error codes:** `dict-item`
- **Count:** 23
- **Example:** JSON parsing returns `dict[str, Any]` but used where typed dict expected
- **Risk:** Low (Pydantic validates at boundaries)
- **Cost to fix:** Explicit model construction everywhere
- **Decision:** Accept debt.

---

### B-06: Skill Registry Dynamic Attributes
- **Error codes:** `attr-defined`
- **Count:** 8
- **Example:** `skill_class.get_input_schema` → `"type[T]" has no attribute`
- **Files:** `skills/registry.py`
- **Risk:** None (skills validated at registration)
- **Cost to fix:** Protocol definition + runtime checks
- **Decision:** Accept debt. Plugin architecture.

---

**Category B Total: 149 errors**

---

## Category C — Requires Refactor

**(Explicitly out of scope.)**

These errors are **real**, but fixing them would require API redesign, control-flow rewrite, or architectural shifts.

**Criteria:**
- Fix implies changing function signatures
- Optionality is real, not just mypy noise
- Data shape ambiguity exists at runtime

---

### C-01: Mixed Return Types in Adapters
- **Error codes:** `no-any-return`, `return-value`
- **Count:** 57
- **Example:** `return result` → `Returning Any from function declared to return "dict[str, Any]"`
- **Files:** `skills/executor.py`, `costsim/provenance.py`, `planners/stub_adapter.py`
- **Root cause:** Functions return different shapes based on success/failure paths
- **Fix requires:** Redesigning return contracts with Result types
- **Decision:** Defer until architecture change. Autofix excluded.

---

### C-02: Optional-to-Required Parameter Passing
- **Error codes:** `arg-type`
- **Count:** 89
- **Example:** `func(value)` where `value: str | None` but param expects `str`
- **Files:** `webhook_verify.py`, `integrations/bridges.py`, `planner/interface.py`
- **Root cause:** Caller doesn't check None before passing
- **Fix requires:** Add guards at every call site OR change signatures
- **Decision:** Defer. Many are validated elsewhere.

---

### C-03: Lazy Initialization Patterns
- **Error codes:** `assignment`
- **Count:** 35
- **Example:** `self.engine: Engine = None` then assigned in `connect()`
- **Files:** `agents/skills/agent_invoke.py`, `traces/replay.py`, `auth/jwt_auth.py`
- **Root cause:** FastAPI dependency injection pattern, deferred initialization
- **Fix requires:** Change to `Optional[T]` + add None checks everywhere
- **Decision:** Defer. Pattern is intentional.

---

### C-04: Union Narrowing Failures
- **Error codes:** `assignment`
- **Count:** 25
- **Example:** `result: ExecutionResult = await run()` where return is `ExecutionResult | BaseException`
- **Files:** `policy/runtime/dag_executor.py`, `routing/probes.py`
- **Root cause:** Exception handling patterns that mypy can't narrow
- **Fix requires:** Explicit type guards or redesigned error handling
- **Decision:** Defer. Error handling works correctly.

---

### C-05: Variable Annotation Required
- **Error codes:** `var-annotated`
- **Count:** 32
- **Example:** `items = []` → `Need type annotation for "items"`
- **Files:** Various
- **Root cause:** Inferred empty collections
- **Fix requires:** Add `items: list[X] = []` everywhere
- **Decision:** Defer. Low value.

---

### C-06: Collection Append Type Mismatches
- **Error codes:** `arg-type`
- **Count:** 18
- **Example:** `errors.append(item)` where item type doesn't match list type
- **Files:** `traces/redact.py`, `skills/json_transform_v2.py`
- **Root cause:** Lists accumulate heterogeneous data
- **Fix requires:** Union types or separate collections
- **Decision:** Defer. Runtime behavior correct.

---

**Category C Total: 256 errors**

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| **A — Structural Impossibilities** | 250 | `# type: ignore` with comment |
| **B — Diminishing Returns** | 149 | Accept baseline, no ignores |
| **C — Requires Refactor** | 256 | Document as architecture |
| **Autofixable (handled)** | 148 | Fixed by autofix system |
| **Unclassified** | 223 | Review incrementally |

**Total errors:** 1,026
**Total accepted debt:** 655 (A + B + C)
**Autofix coverage:** 148 (14.4%)

---

## Enforcement Rules

### Core Rules

1. **No new errors may enter Category A or B without documentation**
2. **Category C requires a design ticket to move**
3. **Autofix must never target Category C**
4. **Deleting ledger entries requires justification**
5. **New `# type: ignore` requires comment explaining which category**
6. **No new function may return `Any` across a module boundary** — ensures casts are explicit, async normalizers are used

### Category-Specific Rules

#### Category A — Require Reason Comments

> Any Category A ignore **must include a one-line reason comment**.

```python
# ✅ Correct
session.exec(select(Model))  # type: ignore[call-overload]  # SQLAlchemy exec() stub incomplete

# ❌ Wrong - no explanation
session.exec(select(Model))  # type: ignore[call-overload]
```

This prevents "drive-by ignores" hiding behind Category A.

---

#### Category B — Literal vs str Scope Restriction

`Literal vs str` errors (B-02) are **only allowed** in:
- logging
- metrics
- config plumbing

**Disallowed** in:
- domain models
- API contracts
- function signatures

This prevents slow erosion of type meaning.

---

#### Category C — No `# type: ignore` Allowed

> Category C errors **must not receive `# type: ignore`**.
> They must remain visible until architecture changes.

This preserves them as **design pressure**, not hidden debt.

---

#### Unclassified Errors

> Unclassified errors may only be fixed **when touching the surrounding code for other reasons**.

Do NOT rush to classify these. Let them resolve naturally as code changes.

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
| 2025-12-24 | **Autofix Extended** - Added SQLAlchemy, Prometheus, FastAPI, Pydantic macros |
| 2025-12-24 | Autofix coverage: 148/1026 (14.4%) - up from 114 (11.1%) |
| 2025-12-24 | **Never-Fix Ledger** - Canonical audit: A=250, B=149, C=256 (655 total) |
| 2025-12-24 | Tightening rules added: reason comments (A), scope restrictions (B), no-ignore (C) |
| 2025-12-24 | Added Rule 6: No `Any` returns across module boundaries |
| 2025-12-24 | Applied 80 autofix fixes, 40 ruff fixes - error count now 991 |
| 2025-12-24 | **Steady-State Policy LOCKED** - 999 errors is correct target, system in maintenance mode |
| 2025-12-24 | Added Ruff Policy section - categorized F401/F841/I001 (auto-fix), E402/ASYNC (scoped), F821 (block) |
| 2025-12-24 | Current breakdown: arg-type(257), assignment(238), union-attr(112), call-overload(75) |

---

## Quarterly Debt Review Ritual

**(Optional — recommended every 2-4 weeks)**

To keep the ledger alive without busywork:

1. **Recount Category C** — Has anything moved to A or B?
2. **Check for promotion** — Any autofixable patterns that emerged?
3. **Validate baselines** — Run `python scripts/mypy_zones.py --report`
4. **Update counts** — If categories shifted, update the ledger summary

This ritual ensures:
- Ledger stays accurate
- New patterns get captured
- Technical debt stays visible, not buried

**Schedule:** Run after major refactors or quarterly, whichever comes first

---

## Steady-State Policy (2025-12-24)

**Status: LOCKED** — This system is now in maintenance mode.

### What the Numbers Mean

**999 remaining errors is the correct target.**

- ~655 are **accepted debt** by policy (Categories A + B + C)
- ~148 were **autofixable and already handled**
- ~196 are **unclassified** — intentionally visible

> **Any new mypy error is either a regression or a documented architectural decision.**

That's the win. Not "zero errors".

### What NOT to Do

1. ❌ Do not try to drive mypy below ~900
2. ❌ Do not "clean up" Category C with casts
3. ❌ Do not blanket-ignore any warnings
4. ❌ Do not merge Ruff and mypy policies (they serve different purposes)

### The Correct Workflow Loop

```bash
# Before commit
python tools/mypy_autofix/apply.py
ruff check --fix

# CI enforces
- No autofix diffs allowed
- No new mypy errors without ledger entry
- No Ruff regressions outside allowed scopes

# Quarterly
- Recount Category C
- Promote any newly patternable errors to autofix
- Update ledger counts only (not goals)
```

---

## Ruff Policy (Parallel to Mypy)

Ruff serves **different purposes** than mypy. Categorize exactly once:

### 🟢 Auto-fix + Gate (Always run, fail CI on diffs)

Safe, mechanical, no semantics:

| Code | Description |
|------|-------------|
| `F401` | Unused imports |
| `F841` | Unused locals |
| `I001` | Import sorting |
| `E741` | Ambiguous names |
| `E711/E712` | Style comparisons |

**Action:** Always run `ruff check --fix` and **fail CI if it produces diffs**.

### 🟡 Allow with Scoped Ignores (Don't chase)

Framework-driven noise:

| Code | Scope |
|------|-------|
| `E402` | `alembic/versions/*.py` only |
| `ASYNC230/101` | `tests/**` only |

**Action:** Add per-file ignores in `pyproject.toml`:

```toml
[tool.ruff.per-file-ignores]
"alembic/versions/*.py" = ["E402"]
"tests/**" = ["ASYNC230", "ASYNC101"]
```

### 🔴 Never Ignore (CI must fail)

These indicate **real bugs**:

| Code | Description |
|------|-------------|
| `F821` | Undefined name |
| `ASYNC1xx` | Blocking in prod async code |

**Action:** CI fails hard. No exceptions.

---

## Current Error Breakdown (2025-12-24)

### Mypy by Error Code

| Error Code | Count | Category |
|------------|-------|----------|
| `arg-type` | 257 | B - Literal vs str, framework |
| `assignment` | 238 | B - SQLModel/Pydantic patterns |
| `union-attr` | 112 | C - Optional chaining |
| `call-overload` | 75 | A - SQLAlchemy sessionmaker |
| `attr-defined` | 63 | Mixed |
| `misc` | 55 | Mixed - Await issues |
| `index` | 49 | B - Dict access |
| `operator` | 38 | B - None + operator |
| `var-annotated` | 33 | C - Needs annotation |
| `return-value` | 27 | C - Return mismatch |
| `dict-item` | 25 | B - Dict literal |
| Other | 27 | Various |

**Total: 999 errors**
