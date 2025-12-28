# C5 CI Guardrails Design

**Version:** 1.0
**Status:** DESIGN (No Code)
**Phase:** C5 (Learning & Evolution)
**Reference:** PIN-232, C5 Entry Conditions (FROZEN)

---

## Purpose

This document specifies the CI guardrails that must exist before C5 implementation begins. These guardrails enforce the learning invariants mechanically.

**Critical:** This is a DESIGN document. No C5 code should be written until:
1. This design is approved
2. C4 has been operational for ≥1 full cycle
3. No emergency kill-switch activations during that period

---

## Core Principle

> **Learning may suggest. Humans decide. Systems apply through existing envelopes.**

Every guardrail exists to enforce this principle mechanically.

---

## Guardrail Summary

| ID | Name | What It Checks |
|----|------|----------------|
| CI-C5-1 | Advisory-Only Output | All learning outputs are advisory, never authoritative |
| CI-C5-2 | Human Approval Gate | No learned change applies without explicit approval flag |
| CI-C5-3 | Metadata Boundary | Learning operates on metadata tables only, not runtime |
| CI-C5-4 | Suggestion Versioning | All learned suggestions are versioned and traceable |
| CI-C5-5 | Learning Disable Flag | Learning can be disabled without affecting C1-C4 |
| CI-C5-6 | Kill-Switch Isolation | Kill-switch behavior is unchanged by learning |

---

## CI-C5-1: Advisory-Only Output

### What It Checks

All learning outputs MUST be advisory. They cannot:
- Modify envelopes directly
- Change priority order
- Alter coordination rules
- Update runtime parameters

### How to Check (Design)

```
For each learning module:
  1. Parse all output types
  2. Assert output type is "LearningSuggestion" (not "EnvelopeUpdate")
  3. Assert output has field `advisory: true` (not configurable)
  4. Assert output has field `requires_approval: true`
  5. Assert no direct calls to EnvelopeManager.apply()
  6. Assert no direct calls to CoordinationManager.update_priority()
```

### Pattern Detection

```python
# FORBIDDEN PATTERNS (must not exist in learning module code)

# Pattern 1: Direct envelope modification
envelope.bounds = learned_bounds  # FORBIDDEN

# Pattern 2: Direct apply call
envelope_manager.apply(learned_envelope)  # FORBIDDEN

# Pattern 3: Priority modification
ENVELOPE_CLASS_PRIORITY[class] = new_priority  # FORBIDDEN

# Pattern 4: Authoritative output
output = LearningOutput(advisory=False, ...)  # FORBIDDEN
```

### Required Patterns

```python
# REQUIRED PATTERNS (must exist in learning module code)

# Pattern 1: Advisory-only output class
@dataclass
class LearningSuggestion:
    suggestion_id: str
    suggested_change: dict
    rationale: str
    confidence: float
    advisory: Literal[True] = True  # Always True, not configurable
    requires_approval: Literal[True] = True  # Always True
    approved: bool = False  # Default False, set by human

# Pattern 2: Suggestion emission (never application)
def emit_suggestion(self, suggestion: LearningSuggestion) -> None:
    # Store for human review
    self.suggestion_store.save(suggestion)
    # Never apply directly
```

### Failure Behavior

- If learning outputs are non-advisory → **BLOCK**
- If direct modification patterns found → **BLOCK**
- If `advisory=False` anywhere → **BLOCK**

### Test Cases (Design)

| Test | Input | Expected |
|------|-------|----------|
| Advisory output | `LearningSuggestion(advisory=True)` | PASS |
| Non-advisory output | `LearningOutput(advisory=False)` | FAIL |
| Direct apply | `envelope_manager.apply(learned)` | FAIL |
| Suggestion only | `emit_suggestion(suggestion)` | PASS |

---

## CI-C5-2: Human Approval Gate

### What It Checks

No learned change may affect system behavior without explicit human approval.

### How to Check (Design)

```
For each suggestion application path:
  1. Assert `approved: bool` field exists on suggestion
  2. Assert `approved` is checked before any state change
  3. Assert `approved_by: str` field is populated when approved
  4. Assert `approved_at: datetime` field is populated when approved
  5. Assert no "auto-approve" logic exists
```

### Pattern Detection

```python
# FORBIDDEN PATTERNS

# Pattern 1: Auto-approval
if suggestion.confidence > 0.9:
    suggestion.approved = True  # FORBIDDEN

# Pattern 2: Approval bypass
def apply_suggestion(suggestion):
    # Missing approval check - FORBIDDEN
    do_apply(suggestion)

# Pattern 3: System-approved
suggestion.approved_by = "system"  # FORBIDDEN (must be human identifier)
```

### Required Patterns

```python
# REQUIRED PATTERNS

# Pattern 1: Approval check before apply
def apply_approved_suggestion(suggestion: LearningSuggestion) -> Result:
    if not suggestion.approved:
        raise ApprovalRequiredError("Human approval required")
    if not suggestion.approved_by:
        raise ApprovalRequiredError("Approver identity required")
    if suggestion.approved_by == "system":
        raise ApprovalRequiredError("System cannot approve")
    # Only then proceed
    return do_apply(suggestion)

# Pattern 2: Approval endpoint (human-triggered only)
@router.post("/learning/suggestions/{id}/approve")
async def approve_suggestion(
    id: str,
    approval: ApprovalRequest,
    current_user: User = Depends(get_current_user),  # Human identity
):
    suggestion = await get_suggestion(id)
    suggestion.approved = True
    suggestion.approved_by = current_user.id  # Human identifier
    suggestion.approved_at = datetime.now(timezone.utc)
    await save_suggestion(suggestion)
```

### Failure Behavior

- If approval check missing → **BLOCK**
- If auto-approve logic exists → **BLOCK**
- If system can approve → **BLOCK**

### Test Cases (Design)

| Test | Setup | Action | Expected |
|------|-------|--------|----------|
| Unapproved apply | `approved=False` | Apply | REJECT |
| Approved apply | `approved=True, approved_by="human123"` | Apply | PASS |
| System approve | `approved_by="system"` | Apply | REJECT |
| Auto-approve | `confidence > threshold → approved` | - | FAIL (CI) |

---

## CI-C5-3: Metadata Boundary

### What It Checks

Learning MUST operate on metadata tables only. It cannot:
- Read or write runtime parameters
- Access live envelope state
- Query active coordination decisions
- Modify kill-switch logic

### How to Check (Design)

```
For each learning module:
  1. List all database tables accessed
  2. Assert all tables are in LEARNING_ALLOWED_TABLES
  3. Assert no access to RUNTIME_TABLES
  4. Assert no access to COORDINATION_TABLES
  5. Assert no access to KILLSWITCH_TABLES
```

### Table Classification

```python
# Allowed tables for learning (metadata only)
LEARNING_ALLOWED_TABLES = {
    "learning_suggestions",
    "learning_outcomes",
    "learning_metrics",
    "historical_envelope_stats",  # Read-only aggregates
    "historical_coordination_stats",  # Read-only aggregates
}

# Forbidden tables (runtime)
LEARNING_FORBIDDEN_TABLES = {
    # Runtime
    "active_envelopes",
    "envelope_state",
    "current_baselines",

    # Coordination
    "coordination_decisions",
    "priority_overrides",  # Should not exist, but check anyway

    # Kill-switch
    "killswitch_state",
    "killswitch_history",

    # Core execution
    "runs",
    "traces",
    "workflow_state",
}
```

### Pattern Detection

```python
# FORBIDDEN PATTERNS

# Pattern 1: Runtime table access
session.query(ActiveEnvelope).filter(...)  # FORBIDDEN

# Pattern 2: Direct envelope state access
envelope = EnvelopeState.get_current(subsystem)  # FORBIDDEN

# Pattern 3: Coordination table write
CoordinationDecision.create(...)  # FORBIDDEN
```

### Required Patterns

```python
# REQUIRED PATTERNS

# Pattern 1: Metadata table access only
from app.learning.tables import LEARNING_ALLOWED_TABLES

def validate_query(query_target: str) -> None:
    if query_target not in LEARNING_ALLOWED_TABLES:
        raise LearningBoundaryViolation(f"Cannot access {query_target}")

# Pattern 2: Historical aggregates only
def get_learning_input() -> LearningInput:
    # Only aggregated historical data
    stats = session.query(HistoricalEnvelopeStats).all()
    return LearningInput(historical_stats=stats)
```

### Failure Behavior

- If runtime table accessed → **BLOCK**
- If coordination table accessed → **BLOCK**
- If kill-switch table accessed → **BLOCK**

### Test Cases (Design)

| Test | Table Access | Expected |
|------|--------------|----------|
| Learning suggestions | `learning_suggestions` | PASS |
| Historical stats | `historical_envelope_stats` | PASS |
| Active envelopes | `active_envelopes` | FAIL |
| Coordination decisions | `coordination_decisions` | FAIL |
| Kill-switch state | `killswitch_state` | FAIL |

---

## CI-C5-4: Suggestion Versioning

### What It Checks

All learned suggestions MUST be versioned and traceable.

### How to Check (Design)

```
For each LearningSuggestion:
  1. Assert `suggestion_id` is unique and immutable
  2. Assert `version` field exists
  3. Assert `created_at` timestamp exists
  4. Assert `parent_suggestion_id` exists (for evolution tracking)
  5. Assert suggestions are append-only (no updates, no deletes)
```

### Schema Requirements

```python
@dataclass
class LearningSuggestion:
    # Identity (immutable)
    suggestion_id: str  # UUID, never changes
    version: int  # Monotonically increasing

    # Provenance
    created_at: datetime  # When suggested
    parent_suggestion_id: Optional[str]  # Previous version, if any
    learning_run_id: str  # Which learning run produced this

    # Content
    suggestion_type: str  # e.g., "envelope_bounds", "priority_weight"
    target_subsystem: str
    target_parameter: str
    suggested_value: Any
    current_value: Any
    rationale: str

    # Confidence
    confidence: float
    evidence: List[str]  # References to historical data

    # Approval state
    advisory: Literal[True] = True
    requires_approval: Literal[True] = True
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Outcome tracking
    applied: bool = False
    applied_at: Optional[datetime] = None
    outcome: Optional[str] = None  # "effective", "reverted", "expired"
```

### Pattern Detection

```python
# FORBIDDEN PATTERNS

# Pattern 1: Suggestion update (must be append-only)
suggestion.suggested_value = new_value
session.commit()  # FORBIDDEN - creates new version instead

# Pattern 2: Suggestion delete
session.delete(suggestion)  # FORBIDDEN

# Pattern 3: Missing version
LearningSuggestion(suggestion_id=id, ...)  # Missing version - FORBIDDEN
```

### Required Patterns

```python
# REQUIRED PATTERNS

# Pattern 1: Append-only storage
def save_suggestion(suggestion: LearningSuggestion) -> None:
    # Always insert, never update
    session.add(suggestion)
    session.commit()

# Pattern 2: New version creation
def create_new_version(old: LearningSuggestion, changes: dict) -> LearningSuggestion:
    return LearningSuggestion(
        suggestion_id=generate_uuid(),  # New ID
        version=old.version + 1,  # Increment
        parent_suggestion_id=old.suggestion_id,  # Link to parent
        # ... copy other fields with changes
    )
```

### Failure Behavior

- If version missing → **BLOCK**
- If suggestion updated in place → **BLOCK**
- If suggestion deleted → **BLOCK**
- If parent_suggestion_id missing for v2+ → **BLOCK**

### Test Cases (Design)

| Test | Action | Expected |
|------|--------|----------|
| Create v1 | Insert with version=1 | PASS |
| Create v2 | Insert with version=2, parent_id=v1.id | PASS |
| Update in place | UPDATE suggestion SET value=x | FAIL |
| Delete | DELETE FROM suggestions | FAIL |
| Missing version | Insert without version | FAIL |

---

## CI-C5-5: Learning Disable Flag

### What It Checks

Learning MUST be disableable without affecting C1-C4 functionality.

### How to Check (Design)

```
1. Assert LEARNING_ENABLED flag exists
2. Assert flag defaults to False
3. When flag is False:
   - Assert C1 (Telemetry) works normally
   - Assert C2 (Predictions) works normally
   - Assert C3 (Optimization) works normally
   - Assert C4 (Coordination) works normally
   - Assert no learning code executes
4. Assert flag is checkable at startup
5. Assert flag is changeable at runtime (without restart)
```

### Flag Implementation

```python
# Configuration
class LearningConfig:
    # Default OFF - learning must be explicitly enabled
    LEARNING_ENABLED: bool = False

    # Runtime toggle endpoint
    # Only accessible to operators, not via API
    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        cls.LEARNING_ENABLED = enabled
        emit_audit("learning_toggle", {"enabled": enabled})

# Guard pattern (required in all learning entry points)
def require_learning_enabled(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not LearningConfig.LEARNING_ENABLED:
            return LearningDisabledResult()
        return func(*args, **kwargs)
    return wrapper
```

### Pattern Detection

```python
# FORBIDDEN PATTERNS

# Pattern 1: Learning without flag check
def run_learning():
    # Missing flag check - FORBIDDEN
    suggestions = learn_from_history()

# Pattern 2: Learning affects C1-C4 when disabled
if not LEARNING_ENABLED:
    # C1-C4 should work normally
    disable_telemetry()  # FORBIDDEN
```

### Required Patterns

```python
# REQUIRED PATTERNS

# Pattern 1: Flag check at entry point
@require_learning_enabled
def run_learning_cycle():
    ...

# Pattern 2: C1-C4 independence
def run_optimization():
    # This should work regardless of LEARNING_ENABLED
    envelope = create_envelope(...)
    coordinator.apply(envelope)
    # No learning dependency here
```

### Failure Behavior

- If learning runs when disabled → **BLOCK**
- If C1-C4 fails when learning disabled → **BLOCK**
- If flag missing → **BLOCK**
- If flag defaults to True → **BLOCK**

### Test Cases (Design)

| Test | LEARNING_ENABLED | Action | Expected |
|------|------------------|--------|----------|
| Learning disabled | False | run_learning() | No-op |
| Learning enabled | True | run_learning() | Runs |
| C4 with learning disabled | False | coordinator.apply() | Works |
| C3 with learning disabled | False | envelope.apply() | Works |
| C2 with learning disabled | False | emit_prediction() | Works |
| C1 with learning disabled | False | emit_telemetry() | Works |

---

## CI-C5-6: Kill-Switch Isolation

### What It Checks

Kill-switch behavior is completely unchanged by learning.

### How to Check (Design)

```
1. Assert kill-switch code has no learning imports
2. Assert kill-switch code has no learning dependencies
3. Assert kill-switch behavior is identical with/without learning enabled
4. Assert learning cannot intercept kill-switch
5. Assert learning cannot delay kill-switch
6. Assert learning cannot filter kill-switch targets
```

### Pattern Detection

```python
# FORBIDDEN PATTERNS (in killswitch.py)

# Pattern 1: Learning import
from app.learning import ...  # FORBIDDEN in killswitch module

# Pattern 2: Learning check before kill
def fire_killswitch():
    if learning.should_allow_kill():  # FORBIDDEN
        do_kill()

# Pattern 3: Learning notification that could delay
def fire_killswitch():
    learning.notify_before_kill()  # FORBIDDEN (could block)
    do_kill()

# Pattern 4: Learning-influenced targets
def fire_killswitch():
    targets = learning.filter_targets(all_envelopes)  # FORBIDDEN
    for t in targets:
        revert(t)
```

### Required Patterns

```python
# REQUIRED PATTERNS

# Pattern 1: No learning in kill-switch path
# killswitch.py should have ZERO learning imports

# Pattern 2: Kill-switch is synchronous and unconditional
def fire_killswitch() -> List[RevertResult]:
    """
    Revert all envelopes immediately.

    No learning involvement. No filtering. No delays.
    """
    results = []
    for envelope in get_all_active_envelopes():
        result = envelope.revert()
        results.append(result)
    return results

# Pattern 3: Learning notified AFTER kill (async, non-blocking)
def fire_killswitch() -> List[RevertResult]:
    results = do_kill_all()

    # Notification is:
    # - After the fact
    # - Async (does not block return)
    # - Optional (failure doesn't affect kill)
    asyncio.create_task(notify_learning_of_kill(results))

    return results  # Returns immediately
```

### Failure Behavior

- If learning import in killswitch.py → **BLOCK**
- If learning can block kill-switch → **BLOCK**
- If learning can filter targets → **BLOCK**

### Test Cases (Design)

| Test | Setup | Kill-Switch | Expected |
|------|-------|-------------|----------|
| Learning enabled | LEARNING_ENABLED=True, 3 envelopes | Fire | All 3 reverted |
| Learning disabled | LEARNING_ENABLED=False, 3 envelopes | Fire | All 3 reverted |
| Learning has suggestion | Active suggestion for envelope | Fire | Envelope reverted (suggestion ignored) |
| Learning module failing | Learning throws exception | Fire | All envelopes reverted (learning failure ignored) |

---

## CI Script Structure (Design)

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/run_all.sh

set -e

echo "=== C5 Guardrails CI ==="
echo "Reference: PIN-232, C5 Entry Conditions (FROZEN)"
echo ""

FAILED=0
PASSED=0

# CI-C5-1: Advisory-Only Output
echo "CI-C5-1: Checking advisory-only output..."
./scripts/ci/c5_guardrails/check_advisory_only.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

# CI-C5-2: Human Approval Gate
echo "CI-C5-2: Checking human approval gate..."
./scripts/ci/c5_guardrails/check_approval_gate.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

# CI-C5-3: Metadata Boundary
echo "CI-C5-3: Checking metadata boundary..."
./scripts/ci/c5_guardrails/check_metadata_boundary.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

# CI-C5-4: Suggestion Versioning
echo "CI-C5-4: Checking suggestion versioning..."
./scripts/ci/c5_guardrails/check_versioning.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

# CI-C5-5: Learning Disable Flag
echo "CI-C5-5: Checking learning disable flag..."
./scripts/ci/c5_guardrails/check_disable_flag.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

# CI-C5-6: Kill-Switch Isolation
echo "CI-C5-6: Checking kill-switch isolation..."
./scripts/ci/c5_guardrails/check_killswitch_isolation.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

echo ""
echo "=== C5 Guardrails Summary ==="
echo "Passed: $PASSED / 6"
echo "Failed: $FAILED / 6"

if [ $FAILED -eq 0 ]; then
  echo "C5 GUARDRAILS PASSED"
  exit 0
else
  echo "C5 GUARDRAILS FAILED"
  exit 1
fi
```

---

## Learning Module Structure (Design)

```
backend/app/learning/
├── __init__.py
├── config.py           # LEARNING_ENABLED flag
├── suggestions.py      # LearningSuggestion dataclass
├── store.py           # Append-only suggestion storage
├── engine.py          # Learning engine (guarded by flag)
├── approval.py        # Human approval endpoints
├── metrics.py         # Learning metrics (metadata only)
└── tables.py          # LEARNING_ALLOWED_TABLES, LEARNING_FORBIDDEN_TABLES
```

### Module Isolation

```python
# app/learning/__init__.py

# This module MUST NOT be imported by:
# - app/optimization/killswitch.py
# - app/optimization/coordinator.py (core paths)
# - app/optimization/envelope.py (core paths)

# It MAY be imported by:
# - app/optimization/metrics.py (for learning metrics)
# - app/api/learning.py (for approval endpoints)
```

---

## Invariant Mapping

| Guardrail | Enforces Invariant |
|-----------|-------------------|
| CI-C5-1 | I-C5-1: Learning suggests, humans decide |
| CI-C5-2 | I-C5-2: No learned change applies without approval |
| CI-C5-3 | I-C5-3: Learning operates on metadata, not runtime |
| CI-C5-4 | I-C5-4: All learned suggestions are versioned |
| CI-C5-5 | I-C5-5: Learning can be disabled without affecting coordination |
| CI-C5-6 | I-C5-6: Kill-switch supremacy is unchanged |

---

## Implementation Order (When C5 Unlocked)

| Step | Description | Depends On |
|------|-------------|------------|
| 1 | Create `app/learning/` module structure | - |
| 2 | Implement `LEARNING_ENABLED` flag (default False) | Step 1 |
| 3 | Create `LearningSuggestion` dataclass | Step 1 |
| 4 | Create `LEARNING_ALLOWED_TABLES` constant | Step 1 |
| 5 | Implement append-only suggestion store | Step 3 |
| 6 | Implement `@require_learning_enabled` decorator | Step 2 |
| 7 | Create approval endpoint | Step 5 |
| 8 | Verify kill-switch has no learning imports | Step 1 |
| 9 | Create CI guardrail scripts | Steps 1-8 |
| 10 | Write C5-S1 tests (advisory only) | Step 9 |

---

## Pre-Implementation Checklist

Before any C5 code is written:

- [ ] C4 has been operational for ≥1 full cycle
- [ ] No emergency kill-switch activations during that period
- [ ] This design document is approved
- [ ] CI-C5-1 through CI-C5-6 scripts are written (no learning code yet)
- [ ] `app/learning/` module structure is approved
- [ ] Invariant mapping is verified

---

## Approval Requirement

This design document must be approved before any C5 implementation begins.

Approval checklist:
- [ ] CI-C5-1 through CI-C5-6 reviewed
- [ ] LearningSuggestion schema approved
- [ ] Table classification approved
- [ ] Module structure approved
- [ ] Implementation order approved
- [ ] No scope creep identified

---

## Truth Anchor

> Learning is where systems become unpredictable if not governed.
> These guardrails exist to ensure learning never escapes human control.
>
> If a guardrail can be bypassed, the learning system is unsafe.
> If learning can modify runtime state without approval, the system has failed.
>
> The only safe learning is learning that suggests but never decides.
