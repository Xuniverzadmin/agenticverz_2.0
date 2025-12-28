# C4 CI Guardrails Design

**Version:** 1.0
**Status:** DESIGN (No Code)
**Phase:** C4 (Multi-Envelope Coordination)
**Reference:** PIN-230, C4_ENVELOPE_COORDINATION_CONTRACT.md

---

## Purpose

This document specifies the CI guardrails that must exist before C4 implementation begins. These guardrails enforce the coordination invariants mechanically.

**Critical:** This is a DESIGN document. No code should be written until this design is approved.

---

## Guardrail Summary

| ID | Name | What It Checks |
|----|------|----------------|
| CI-C4-1 | Envelope Class Declaration | Every envelope declares exactly one class |
| CI-C4-2 | Coordination Check Required | No envelope applies without coordination check |
| CI-C4-3 | Priority Order Immutable | Priority order cannot be overridden |
| CI-C4-4 | Same-Parameter Conflict | Same-parameter envelopes always rejected |
| CI-C4-5 | Kill-Switch All-Revert | Kill-switch reverts all envelopes |
| CI-C4-6 | Coordination Audit Emission | Every coordination decision emits audit |

---

## CI-C4-1: Envelope Class Declaration

### What It Checks

Every envelope MUST declare exactly one class from:
- `SAFETY`
- `RELIABILITY`
- `COST`
- `PERFORMANCE`

### How to Check (Design)

```
For each envelope declaration file:
  1. Parse envelope definition
  2. Assert `envelope_class` field exists
  3. Assert `envelope_class` is one of [SAFETY, RELIABILITY, COST, PERFORMANCE]
  4. Assert no envelope has multiple classes
```

### Failure Behavior

- If class missing → **BLOCK** (envelope cannot be registered)
- If class invalid → **BLOCK** (envelope cannot be registered)
- If multiple classes → **BLOCK** (envelope cannot be registered)

### Test Cases (Design)

| Test | Input | Expected |
|------|-------|----------|
| Valid class | `envelope_class: SAFETY` | PASS |
| Missing class | (no envelope_class) | FAIL |
| Invalid class | `envelope_class: FAST` | FAIL |
| Multiple classes | `envelope_class: [SAFETY, COST]` | FAIL |

---

## CI-C4-2: Coordination Check Required

### What It Checks

No envelope may apply without passing through the coordination layer.

### How to Check (Design)

```
For each envelope application path:
  1. Trace call path from envelope.apply()
  2. Assert CoordinationManager.check_allowed() is called
  3. Assert check result is evaluated before apply
```

### Failure Behavior

- If coordination check bypassed → **BLOCK** (CI fails)
- If check result ignored → **BLOCK** (CI fails)

### Test Cases (Design)

| Test | Input | Expected |
|------|-------|----------|
| Normal path | apply() calls coordinator first | PASS |
| Bypass attempt | apply() without coordinator | FAIL |
| Check ignored | coordinator returns REJECT, apply proceeds | FAIL |

---

## CI-C4-3: Priority Order Immutable

### What It Checks

The priority order `SAFETY > RELIABILITY > COST > PERFORMANCE` cannot be changed at runtime.

### How to Check (Design)

```
1. Assert priority order is defined as constant (not configurable)
2. Assert no code path modifies priority order
3. Assert no environment variable overrides priority
4. Assert no API endpoint changes priority
```

### Failure Behavior

- If priority defined as variable → **BLOCK**
- If priority modification code exists → **BLOCK**
- If priority config file exists → **BLOCK**

### Test Cases (Design)

| Test | Input | Expected |
|------|-------|----------|
| Constant definition | `PRIORITY_ORDER = (SAFETY, RELIABILITY, COST, PERFORMANCE)` | PASS |
| Mutable definition | `priority_order = [...]` with setter | FAIL |
| Config override | `PRIORITY_ORDER` env var | FAIL |

---

## CI-C4-4: Same-Parameter Conflict

### What It Checks

Two envelopes targeting the same parameter MUST always reject the second.

### How to Check (Design)

```
1. When envelope B requests apply:
   a. Check active envelopes
   b. If any active envelope targets same (subsystem, parameter):
      - REJECT envelope B
      - Emit audit with reason "same_parameter_conflict"
```

### Failure Behavior

- If same-parameter allows → **BLOCK**
- If rejection not audited → **BLOCK**

### Test Cases (Design)

| Test | Envelope A | Envelope B | Expected |
|------|------------|------------|----------|
| Different params | retry.backoff | retry.max_retries | Both allowed |
| Same param | retry.backoff | retry.backoff | B rejected |
| Same param, different subsystem | retry.backoff | scheduler.backoff | Both allowed |

---

## CI-C4-5: Kill-Switch All-Revert

### What It Checks

When kill-switch fires, ALL active envelopes revert immediately.

### How to Check (Design)

```
1. Create test with multiple active envelopes (e.g., 3)
2. Fire kill-switch
3. Assert all 3 envelopes are in REVERTED state
4. Assert all 3 baselines are restored
5. Assert no envelope survives
```

### Failure Behavior

- If any envelope survives kill-switch → **BLOCK**
- If any baseline not restored → **BLOCK**
- If revert order matters → **WARN** (should be atomic)

### Test Cases (Design)

| Test | Setup | Kill-Switch | Expected |
|------|-------|-------------|----------|
| Single envelope | 1 active | Fire | 1 reverted |
| Multiple envelopes | 3 active | Fire | 3 reverted |
| No envelopes | 0 active | Fire | No-op (safe) |
| Nested application | 2 active, 1 applying | Fire | All reverted |

---

## CI-C4-6: Coordination Audit Emission

### What It Checks

Every coordination decision MUST emit an audit record.

### How to Check (Design)

```
For each coordination decision type:
  1. Assert audit record is emitted
  2. Assert audit contains:
     - envelope_id
     - envelope_class
     - decision (applied | rejected | preempted)
     - reason
     - timestamp
  3. If conflicting_envelope_id exists, assert it's included
```

### Failure Behavior

- If audit missing → **BLOCK**
- If audit incomplete → **BLOCK**

### Test Cases (Design)

| Test | Decision | Expected Audit |
|------|----------|----------------|
| Apply allowed | APPLIED | envelope_id, class, "applied", reason, timestamp |
| Rejected | REJECTED | envelope_id, class, "rejected", reason, conflicting_id |
| Preempted | PREEMPTED | envelope_id, class, "preempted", reason, preempting_id |

---

## CI Script Structure (Design)

```bash
#!/bin/bash
# scripts/ci/c4_guardrails/run_all.sh

echo "=== C4 Guardrails CI ==="
echo "Reference: PIN-230, C4_ENVELOPE_COORDINATION_CONTRACT.md"
echo ""

FAILED=0

# CI-C4-1: Envelope Class Declaration
echo "CI-C4-1: Checking envelope class declarations..."
# ... checks ...

# CI-C4-2: Coordination Check Required
echo "CI-C4-2: Checking coordination check requirement..."
# ... checks ...

# CI-C4-3: Priority Order Immutable
echo "CI-C4-3: Checking priority order immutability..."
# ... checks ...

# CI-C4-4: Same-Parameter Conflict
echo "CI-C4-4: Checking same-parameter conflict handling..."
# ... checks ...

# CI-C4-5: Kill-Switch All-Revert
echo "CI-C4-5: Checking kill-switch all-revert..."
# ... checks ...

# CI-C4-6: Coordination Audit Emission
echo "CI-C4-6: Checking coordination audit emission..."
# ... checks ...

# Run C4 coordination tests
echo "Running C4 coordination tests..."
cd backend && PYTHONPATH=. python3 -m pytest tests/optimization/test_c4_*.py -v

echo ""
echo "=== C4 Guardrails Summary ==="
echo "Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
  echo "C4 GUARDRAILS PASSED"
  exit 0
else
  echo "C4 GUARDRAILS FAILED"
  exit 1
fi
```

---

## Coordination Manager Interface (Design)

```python
class CoordinationManager:
    """
    Central coordination point for multi-envelope management.

    All envelope operations MUST go through this manager.
    """

    def check_allowed(
        self,
        envelope: Envelope,
        prediction: Prediction,
    ) -> CoordinationDecision:
        """
        Check if envelope is allowed to apply.

        Returns:
            CoordinationDecision with:
            - allowed: bool
            - reason: str
            - conflicting_envelope_id: Optional[str]
        """
        ...

    def apply_with_coordination(
        self,
        envelope: Envelope,
        prediction: Prediction,
    ) -> EnvelopeResult:
        """
        Apply envelope through coordination layer.

        Steps:
        1. check_allowed()
        2. If not allowed, emit audit, return rejected
        3. Check priority preemption
        4. If preemption needed, revert lower-priority envelopes
        5. Apply envelope
        6. Emit audit
        """
        ...

    def handle_kill_switch(self) -> List[EnvelopeRevertResult]:
        """
        Revert ALL active envelopes.

        Steps:
        1. Get all active envelopes
        2. Revert each one
        3. Emit audit for each
        4. Return results
        """
        ...
```

---

## Coordination Decision Schema (Design)

```python
@dataclass
class CoordinationDecision:
    envelope_id: str
    envelope_class: EnvelopeClass
    decision: Literal["applied", "rejected", "preempted"]
    reason: str
    conflicting_envelope_id: Optional[str] = None
    preempting_envelope_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Audit Record Schema (Design)

```python
@dataclass
class CoordinationAuditRecord:
    audit_id: str
    envelope_id: str
    envelope_class: EnvelopeClass
    decision: Literal["applied", "rejected", "preempted"]
    reason: str
    conflicting_envelope_id: Optional[str] = None
    preempting_envelope_id: Optional[str] = None
    active_envelopes_count: int
    timestamp: datetime
```

---

## Implementation Order (When Approved)

| Step | Description | Depends On |
|------|-------------|------------|
| 1 | Add `envelope_class` field to Envelope | - |
| 2 | Create `EnvelopeClass` enum | Step 1 |
| 3 | Add validation for class declaration | Step 2 |
| 4 | Create `CoordinationManager` interface | Step 3 |
| 5 | Implement `check_allowed()` | Step 4 |
| 6 | Implement same-parameter check | Step 5 |
| 7 | Implement priority preemption | Step 5 |
| 8 | Update kill-switch for all-revert | Step 4 |
| 9 | Implement coordination audit | Step 4 |
| 10 | Create CI guardrails script | Step 9 |
| 11 | Write C4-S1 tests | Step 10 |

---

## Approval Requirement

This design document must be approved before any C4 implementation begins.

Approval checklist:
- [ ] CI-C4-1 through CI-C4-6 reviewed
- [ ] CoordinationManager interface approved
- [ ] Audit schema approved
- [ ] Implementation order approved
- [ ] No scope creep identified

---

## Truth Anchor

> CI guardrails are not style checks.
> They are invariant enforcement.
> If a guardrail can be bypassed, the invariant is not enforced.
> C4 without guardrails is C4 without safety.
