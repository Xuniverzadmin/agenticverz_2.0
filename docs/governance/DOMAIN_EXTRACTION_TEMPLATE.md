# DOMAIN_EXTRACTION_TEMPLATE.md

**Status:** RATIFIED
**Ratified:** 2025-12-31
**Created:** 2025-12-31
**Purpose:** Extract domain authority from mixed modules without introducing dual-role behavior
**Scope:** Applies only to Phase E domain extractions; not refactors or redesigns
**Non-Goal:** Does not change system behavior, performance, or external contracts
**Reference:** PHASE_E_FIX_DESIGN.md, PIN-256
**Governance Qualifier:** Phase E domain extraction is only valid when executed under this template and enforced by BLCA-E4 rules

---

## Governing Principle

> **Extraction must reveal truth, not relocate code.**
> **If you cannot declare what semantic decision is being promoted, the extraction is invalid.**

---

## Template Authority

This template is **binding**, not advisory.

- No Phase E-4 extraction may proceed without following this template
- Any extraction that violates this template is invalid and must be reverted
- BLCA must pass after each extraction before proceeding to the next
- No exceptions. No "usually". No "in rare cases".

---

## 1. FILE STRUCTURE

### Naming Convention

```
BEFORE:
  backend/app/worker/{name}.py (L5) — mixed domain + execution

AFTER:
  backend/app/worker/{name}_engine.py (L4) — pure domain logic
  backend/app/worker/{name}.py (L5) — execution wrapper
```

### Hard Prohibitions (File Structure)

| Forbidden | Reason | If Created = |
|-----------|--------|--------------|
| `common.py` | Duality leak | Extraction INVALID |
| `helpers.py` | Duality leak | Extraction INVALID |
| `utils.py` | Duality leak | Extraction INVALID |
| `shared.py` | Duality leak | Extraction INVALID |
| Any third file | Scope creep | Extraction INVALID |

**Rule:** Each extraction produces exactly TWO files: `{name}_engine.py` (L4) and updated `{name}.py` (L5). No exceptions.

### Required Header: L4 Engine

```python
# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker (called by L5)
#   Execution: sync (REQUIRED - async forbidden)
# Role: {single-line domain decision description}
# Callers: {L5 wrapper that calls this}
# Allowed Imports: L4 only (stdlib, dataclasses, typing, enum)
# Forbidden Imports: L5, L6, L7, L8
# Reference: PIN-256 Phase E FIX-01
#
# Extraction Source: {original L5 file}
# Semantic Promotion: {what decision is being elevated}
# BLCA Violations Resolved: {VIOLATION-XXX}
```

### Required Header: L5 Wrapper (Updated)

```python
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: {original trigger}
#   Execution: {sync|async}
# Role: {orchestration/execution description}
# Callers: {original callers}
# Allowed Imports: L4, L5, L6
# Domain Engine: {name}_engine.py (L4)
# Reference: PIN-256 Phase E FIX-01
```

---

## 2. DUAL-ROLE PROHIBITION (BINDING)

An extracted L4 engine **MUST NOT**:

| Prohibition | Reason | Detection |
|-------------|--------|-----------|
| Import from L5 | Execution coupling | Static import check |
| Import from L6 | Platform coupling | Static import check |
| Import from L7/L8 | Ops/Meta coupling | Static import check |
| Accept callable parameters | Semantic laundering | grep for `Callable`, `callable`, `_fn` |
| Execute injected functions | Authority inversion | Code review |
| Perform I/O | Side effect | Code review |
| Perform persistence | Platform responsibility | grep for `session`, `db`, `write` |
| Acquire locks | Execution responsibility | grep for `lock`, `FOR UPDATE` |
| Implement retries | Execution responsibility | grep for `retry`, `backoff` |
| Use scheduling | Execution responsibility | grep for `sleep`, `schedule`, `cron` |
| Read env/config | Platform state | grep for `os.environ`, `settings` |
| Interpret external responses | Requires L6 mediation | Code review |
| Emit signals/metrics | Side effect | grep for `emit`, `metrics`, `publish` |

**CRITICAL: Callable/Callback Prohibition (Added 2025-12-31)**

L4 modules MUST NOT accept or execute callable parameters (callbacks, lambdas, injected functions).

This is **semantic laundering**: authority appears to move to L4, but control remains in L5.
If L4 needs classification logic from another domain, it must **import from L4**, not receive functions from L5.

**Correct:** L4 imports from L4 `recovery_rule_engine.py`
**Wrong:** L4 accepts `category_fn` parameter from L5

**Any violation invalidates the extraction.**

### Allowed in L4 Engine

| Allowed | Example |
|---------|---------|
| Pure functions | `def evaluate(input) -> Output` |
| Dataclasses | `@dataclass class Decision` |
| Enums | `class Status(Enum)` |
| Type hints | `from typing import List, Optional` |
| Logging (debug only) | `logger.debug(...)` |
| Math/string operations | stdlib |
| Other L4 imports | `from app.worker.other_engine import ...` |

---

## 3. INTERFACE CONTRACT (L5 → L4)

The interface between L5 wrapper and L4 engine must be **explicit and minimal**.

### Required Interface Pattern

```python
# L4 Engine — single entry point
def evaluate(input_data: InputType) -> OutputType:
    """Pure domain decision. No side effects."""
    ...
    return decision

# L5 Wrapper — calls L4 synchronously
result = engine.evaluate(prepared_data)
```

### Interface Requirements

| Requirement | Rule |
|-------------|------|
| Single entry function | One public function per engine |
| Explicit input type | Dataclass or typed dict, never raw objects |
| Explicit output type | Dataclass or typed dict, never exceptions for decisions |
| Synchronous call | No async, no callbacks |
| No dependency injection | Engine cannot receive services/clients |
| No global state | Engine cannot read module-level state |

### Interface Smells (Duality Leaks)

If any of these appear in the L4 interface, extraction is **INVALID**:

| Smell | Why It's Wrong |
|-------|----------------|
| `session` parameter | DB coupling |
| `config` parameter | Platform state coupling |
| `client` parameter | Adapter coupling |
| `context` parameter | Execution state coupling |
| Callback function | Control flow leak |
| `_fn` parameter | Semantic laundering (L5 injects behavior into L4) |
| `Callable` type hint | L4 accepts executable code from caller |
| `lambda` in call | Behavior injection disguised as data |
| `**kwargs` | Implicit contract |

### Correct Pattern

```python
# ❌ WRONG — passing platform objects
def evaluate(session: Session, config: Config, data: dict) -> Result:
    ...

# ✓ CORRECT — passing facts only
def evaluate(data: EvaluationInput) -> EvaluationResult:
    ...

# L5 prepares the facts:
input_data = EvaluationInput(
    items=[item.to_dict() for item in items],
    threshold=config.THRESHOLD,
    current_time=datetime.now(),
)
result = engine.evaluate(input_data)
```

---

## 5. SEMANTIC PROMOTION DECLARATION (MANDATORY)

Every extraction must include this section in the extraction record:

```yaml
semantic_promotion:
  # What raw facts does L5 provide to L4?
  input_facts:
    - "{fact 1: e.g., 'list of failure records'}"
    - "{fact 2: e.g., 'current timestamp'}"

  # What semantic decision does L4 produce?
  output_decision:
    type: "{classification|evaluation|gating|selection}"
    description: "{e.g., 'determines which failures are eligible for graduation'}"

  # Why can this decision NOT live in L5?
  promotion_justification: |
    {e.g., "This decision defines system truth about failure severity.
    It must be stable, idempotent, and independent of execution context.
    L5 cannot own semantic classification without becoming dual-role."}

  # How is this decision stable/idempotent?
  stability_proof: |
    {e.g., "Same input facts produce same output decision.
    No dependency on time, state, or execution context.
    Can be called multiple times safely."}
```

**If you cannot fill this out, the extraction is not ready.**

---

## 6. BLCA COVERAGE MAPPING (MANDATORY)

Every extraction must declare:

```yaml
blca_coverage:
  # Which violations does this extraction resolve?
  violations_resolved:
    - VIOLATION-XXX: "{description}"

  # Which BLCA axes are satisfied?
  axes_satisfied:
    - A1: "{layer compliance}"
    - A2: "{import boundary}"

  # What new edges are introduced?
  new_edges:
    - "{L5 wrapper} → {L4 engine}: domain decision call"

  # What old edges are removed?
  old_edges_removed:
    - "{description of violation edge removed}"

  # Post-extraction BLCA expectation
  expected_result: "PASS (violations reduced by N)"
```

### BLCA Monotonicity Rule

**Every extraction MUST reduce the open Phase-E violation count. Never increase it.**

If BLCA shows more violations after extraction → extraction is INVALID.

---

## 7. WHAT MUST NOT BE EXTRACTED (NEGATIVE EXAMPLES)

These patterns **MUST remain in L5**. Do NOT move them to L4:

### 7.1 Database Operations

```python
# ❌ WRONG — this stays in L5
def engine_save_result(session, result):
    session.add(result)
    session.commit()

# ✓ CORRECT — L4 returns decision, L5 persists
# L4:
def engine_evaluate(data) -> Decision:
    return Decision(status="approved")

# L5:
decision = engine_evaluate(data)
session.add(DecisionRecord(decision))
session.commit()
```

### 7.2 Lock Acquisition

```python
# ❌ WRONG — locks stay in L5
def engine_claim_with_lock(session, item_id):
    item = session.query(Item).filter_by(id=item_id).with_for_update().first()
    return evaluate_claim(item)

# ✓ CORRECT — L5 acquires lock, L4 evaluates
# L5:
item = session.query(Item).filter_by(id=item_id).with_for_update().first()
decision = claim_engine.evaluate(item.to_dict())
```

### 7.3 Retry Logic

```python
# ❌ WRONG — retries stay in L5
def engine_with_retry(data):
    for attempt in range(3):
        try:
            return evaluate(data)
        except TransientError:
            time.sleep(2 ** attempt)

# ✓ CORRECT — L4 is pure, L5 handles retries
# L4:
def evaluate(data) -> Result:
    return Result(...)  # Pure, can raise

# L5:
for attempt in range(3):
    try:
        return engine.evaluate(data)
    except TransientError:
        time.sleep(2 ** attempt)
```

### 7.4 External API Calls

```python
# ❌ WRONG — external calls stay in L5/L3
def engine_call_llm(prompt):
    response = anthropic.messages.create(...)
    return interpret(response)

# ✓ CORRECT — L5 fetches, L4 interprets
# L5:
raw_response = llm_adapter.call(prompt)
decision = engine.interpret(raw_response.content)
```

### 7.5 Time-Based Branching

```python
# ❌ WRONG — time-based logic is execution coupling
def engine_check_expiry(item):
    if datetime.now() > item.expires_at:
        return "expired"

# ✓ CORRECT — L5 provides timestamp as fact
# L4:
def check_expiry(item_data, current_time) -> str:
    if current_time > item_data["expires_at"]:
        return "expired"

# L5:
result = engine.check_expiry(item.to_dict(), datetime.now())
```

### 7.6 Feature Flags / Config Reading

```python
# ❌ WRONG — config is platform state
def engine_evaluate(data):
    if os.environ.get("FEATURE_X_ENABLED"):
        return new_evaluation(data)
    return old_evaluation(data)

# ✓ CORRECT — L5 passes config as parameter
# L4:
def evaluate(data, feature_x_enabled: bool) -> Result:
    if feature_x_enabled:
        return new_evaluation(data)
    return old_evaluation(data)

# L5:
result = engine.evaluate(data, settings.FEATURE_X_ENABLED)
```

---

## 8. EXTRACTION CHECKLIST (Per File)

Before extracting, verify:

```
EXTRACTION PRE-CHECK
[ ] Domain decision logic identified
[ ] All execution coupling identified (locks, retries, persistence)
[ ] Semantic promotion declaration drafted
[ ] BLCA coverage mapping completed
[ ] L4 engine file created with required header
[ ] L5 wrapper updated with required header
[ ] All prohibitions verified (dual-role check)
[ ] BLCA run after extraction
[ ] BLCA result: PASS / FAIL
```

---

## 9. PHASE E-4 EXTRACTION QUEUE

**Extraction Order:** Sequential (MANDATORY). BLCA must pass between each extraction.

| Order | Source File (L5) | Target Engine (L4) | Rationale | Status | BLCA |
|-------|------------------|--------------------|-----------|--------|------|
| 1 | `failure_aggregation.py` | `failure_classification_engine.py` | Highest blast radius | PENDING | - |
| 2 | `graduation_evaluator.py` | `graduation_rule_engine.py` | Depends on classification | PENDING | - |
| 3 | `recovery_evaluator.py` | `recovery_rule_engine.py` | Depends on graduation | PENDING | - |
| 4 | `recovery_claim_worker.py` | `claim_decision_engine.py` | Most execution-heavy | PENDING | - |

### Why Sequential (Not Parallel)

Parallel extraction is **forbidden** because:
- Authority boundaries are global, not local
- Parallel extraction hides causal regressions
- BLCA correctness > speed

### Operational Rule

After **each** extraction:
1. Run layer_validator.py
2. Update PHASE_E_FIX_DESIGN.md
3. Confirm violation count decreases
4. Only then proceed to next extraction

**No batching. No "we'll check later".**

---

## 10. TEMPLATE VIOLATION CLAUSE

If any extraction violates this template:

1. The extraction **MUST be reverted**
2. The violation **MUST be recorded** in PHASE_E_FIX_DESIGN.md
3. Phase E-4 **MUST pause** until the violation is resolved
4. No "partial extractions" or "temporary exceptions" are allowed

---

## 11. BLCA ENFORCEMENT RULES (MECHANICAL)

These rules are enforced automatically by layer_validator.py:

### BLCA-E4-01: No Dual Imports

**Rule:** Any file classified as L4:
- MUST NOT import from L5, L6, L7, L8
- MUST NOT import persistence or adapter modules

**Enforcement:** Static import check
**Failure:** BLOCKING

### BLCA-E4-02: Engine Purity Rule

**Rule:** L4 engine files:
- Must be side-effect free
- Must not write to stores
- Must not call network / FS / time

**Enforcement:** Static AST scan, banned imports list
**Failure:** BLOCKING

### BLCA-E4-03: Promotion Path Integrity

**Rule:** Any new L4 engine must be invoked only via:
- L5 wrapper
- Never directly by L2, L3, L6, L7

**Enforcement:** Caller graph analysis
**Failure:** BLOCKING

### BLCA-E4-04: Violation Closure Accounting

**Rule:** Every extraction must:
- Reduce the open Phase-E violation count
- Never increase it

**Enforcement:** Delta comparison
**Failure:** BLOCKING

### BLCA-E4-05: No New Authority Surfaces

**Rule:** L4 engine must not introduce:
- New decision types
- New gates
- New policy dimensions

**Enforcement:** Semantic diff review
**Failure:** BLOCKING

### BLCA-E4-06: Behavioral Injection Prohibition (Added 2025-12-31)

**Rule:** L4 engine must not:
- Accept callable parameters (functions, lambdas, callbacks)
- Execute behavior passed in from callers
- Use `Callable` type hints in public interfaces
- Accept `_fn` suffixed parameters

**Rationale:** Function injection is semantic laundering. Authority appears to move to L4,
but control remains in L5. This violates the Dual-Role Prohibition covertly.

**Correct Pattern:** If L4 needs classification logic from another domain:
- Import from another L4 module (L4 → L4 is allowed)
- Never receive functions from L5

**Detection:**
- grep for `Callable`, `callable`, `_fn=`, `_fn:`
- AST scan for function-type parameters
- Code review for callback patterns

**Enforcement:** Static analysis + code review
**Failure:** BLOCKING

**Origin:** Extraction #1 governance correction (2025-12-31)

---

## 12. RATIFICATION

This template requires explicit ratification before Phase E-4 may proceed.

**Ratification Status:** RATIFIED (2025-12-31)

**Ratification Criteria:**
- [x] Header/Scope/Non-Goal verified
- [x] File structure rules accepted
- [x] Dual-role prohibition absolute (no exceptions)
- [x] Interface contract verified
- [x] Semantic promotion declaration mandatory
- [x] BLCA coverage mapping mandatory
- [x] Negative examples complete
- [x] Extraction checklist complete
- [x] Sequential extraction order accepted
- [x] Template violation clause accepted
- [x] BLCA enforcement rules accepted
- [x] Human approval recorded

**Ratification Note:**
Template ratified after line-by-line governance review. Key enforcement mechanisms verified:
- Section 2 (Dual-Role Prohibition) prevents reclassification-as-fix
- Section 5 (Semantic Promotion) forces explicit authority declaration
- Section 6 (BLCA Monotonicity) ensures violations only decrease
- Sequential extraction prevents parallel coupling drift
- No flexibility added. No prohibitions weakened.

---

*Extraction must reveal truth, not relocate code.*
*Extraction is not expansion.*
*Reference: PIN-256, PHASE_E_FIX_DESIGN.md*
