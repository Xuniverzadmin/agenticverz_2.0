# C5-S2 Acceptance Criteria

**Learning from Coordination Friction**
**Version:** 1.0
**Status:** FROZEN (2025-12-28)
**Reference:** PIN-232, C5_S2_LEARNING_SCENARIO.md

---

## 1. Scope & Intent (Non-Negotiable)

**C5-S2 exists solely to help humans understand coordination friction patterns.**

It does **not**:

* optimize
* merge
* consolidate
* redesign
* automate

If any criterion below is violated, **C5-S2 FAILS certification**.

---

## 2. Entry Conditions (Must Already Be True)

| ID | Condition | Required | Status |
|----|-----------|----------|--------|
| EC-S2-1 | C5-S1 certified | YES | PENDING |
| EC-S2-2 | C5-S1 >= 2 stable cycles | YES | PENDING |
| EC-S2-3 | C5 entry conditions frozen | YES | FROZEN (PIN-232) |
| EC-S2-4 | C5 CI guardrails passing | YES | PASS (6/6) |
| EC-S2-5 | S2 design frozen | YES | DRAFT |

If any entry condition is false -> **do not proceed**.

---

## 3. Observability Constraints (What C5-S2 May Observe)

### Allowed Inputs (Read-Only)

C5-S2 may observe **only**:

| Category | Allowed | Status |
|----------|---------|--------|
| Events | Coordination decisions (APPLIED/REJECTED/PREEMPTED) | PENDING |
| Metadata | Envelope ID, class, parameter | PENDING |
| Outcomes | Decision type, reason | PENDING |
| Time | Timestamps, durations | PENDING |
| Aggregates | Counts over fixed window | PENDING |

### Forbidden Inputs

C5-S2 must **never** read:

| Input | Status |
|-------|--------|
| Live runtime state | PENDING |
| Prediction confidence | PENDING |
| Incident severity | PENDING |
| Cost metrics | PENDING |
| Replay traces | PENDING |
| Control-path signals | PENDING |
| User data | PENDING |

**Test:** Any import outside metadata tables -> FAIL
**CI Enforcement:** CI-C5-3, CI-C5-6

---

## 4. Signal Detection Criteria

### S2-F1: Repeated Same-Parameter Rejection

| Criterion | Requirement |
|-----------|-------------|
| AC-S2-F1-1 | Threshold configurable (default N=3) |
| AC-S2-F1-2 | Only counts within observation window |
| AC-S2-F1-3 | Links to specific audit record IDs |
| AC-S2-F1-4 | Identifies conflicting envelope classes |

### S2-F2: Priority Oscillation

| Criterion | Requirement |
|-----------|-------------|
| AC-S2-F2-1 | Detects preempt->reapply->preempt cycles |
| AC-S2-F2-2 | Threshold configurable (default >= 2 cycles) |
| AC-S2-F2-3 | Identifies oscillating envelope pair |
| AC-S2-F2-4 | Reports cycle count and timing |

### S2-F3: Class Friction

| Criterion | Requirement |
|-----------|-------------|
| AC-S2-F3-1 | Detects recurring class conflicts |
| AC-S2-F3-2 | Threshold configurable (default >= 3 conflicts) |
| AC-S2-F3-3 | Identifies conflicting class pair |
| AC-S2-F3-4 | Reports conflict frequency |

### S2-F4: Short-Lived Envelopes

| Criterion | Requirement |
|-----------|-------------|
| AC-S2-F4-1 | Detects envelopes ending < 10% of timebox |
| AC-S2-F4-2 | Excludes rollbacks (S1 territory) |
| AC-S2-F4-3 | Excludes preemptions (normal behavior) |
| AC-S2-F4-4 | Reports average lifespan |

---

## 5. Output Constraints (What C5-S2 May Produce)

### Allowed Output

Exactly **one output type** is allowed:

> **Advisory Learning Suggestion**

Required fields:

| Field | Requirement | Status |
|-------|-------------|--------|
| advisory | Literal `TRUE` | PENDING |
| requires_human_approval | Literal `TRUE` | PENDING |
| observed_pattern | Signal ID + description | PENDING |
| supporting_evidence | Audit record IDs | PENDING |
| version | Immutable | PENDING |
| timestamp | Required | PENDING |

### Forbidden Outputs

C5-S2 must **not**:

| Forbidden Output | Status |
|------------------|--------|
| priority change suggestions | PENDING |
| envelope merge recommendations | PENDING |
| specific parameter values | PENDING |
| ranked options | PENDING |
| auto-approval flags | PENDING |
| scores or ratings | PENDING |

**Test:** Presence of forbidden output type -> FAIL
**CI Enforcement:** CI-C5-1

---

## 6. Language & Semantics (Critical)

### Mandatory Language

Suggestions **must** include at least one of:

* "observed"
* "pattern detected"
* "consider reviewing"
* "advisory"
* "human decision required"

### Forbidden Language

Any occurrence of the following -> FAIL:

| Pattern | Status |
|---------|--------|
| "should change priority" | PENDING |
| "should merge" | PENDING |
| "should consolidate" | PENDING |
| "system recommends" | PENDING |
| "will reduce friction" | PENDING |
| "apply" | PENDING |
| "automatically" | PENDING |

**Enforcement:** `validate_suggestion_text()` + CI-C5-1

---

## 7. Hard Invariants

| ID | Invariant | Test |
|----|-----------|------|
| I-C5-S2-1 | Advisory only - no changes applied | No apply() calls |
| I-C5-S2-2 | No priority suggestions | No priority in output |
| I-C5-S2-3 | No auto-resolution | No merge/disable code |
| I-C5-S2-4 | No system mutation | Suggestions are metadata |
| I-C5-S2-5 | Replay independence | Replay ignores S2 |
| I-C5-S2-6 | Kill-switch independence | Zero imports |

---

## 8. Human Approval Gate (Hard Requirement)

| Rule | Requirement | Status |
|------|-------------|--------|
| Approval | Explicit human action required | PENDING |
| Auto-approval | **Forbidden** | PENDING |
| System approval | **Forbidden** | PENDING |
| Approval bypass | **Forbidden** | PENDING |

**Test:** Any suggestion applied without human approval -> FAIL
**CI Enforcement:** CI-C5-2

---

## 9. Isolation Guarantees (Safety)

C5-S2 must demonstrate:

| Guarantee | Requirement | Status |
|-----------|-------------|--------|
| Delete safety | Deleting all S2 data changes nothing | PENDING |
| Kill-switch isolation | Kill-switch works with learning disabled | PENDING |
| Replay isolation | Replay ignores S2 entirely | PENDING |
| Envelope independence | Envelopes behave identically with or without S2 | PENDING |
| S1 independence | S2 does not affect S1 behavior | PENDING |

**Test:** Full deletion -> baseline behavior preserved -> PASS
**CI Enforcement:** CI-C5-5, CI-C5-6

---

## 10. Versioning & Immutability

| Requirement | Status |
|-------------|--------|
| Suggestions append-only | PENDING |
| Suggestions immutable | PENDING |
| Evidence links preserved | PENDING |
| Edits allowed | FORBIDDEN |

Any mutation of a suggestion record -> FAIL
**CI Enforcement:** CI-C5-4

---

## 11. CI & Guardrail Mapping

C5-S2 must pass **all** of the following:

| Guardrail | Purpose | Status |
|-----------|---------|--------|
| CI-C5-1 | Advisory-only enforcement | PENDING |
| CI-C5-2 | Human approval required | PENDING |
| CI-C5-3 | Metadata boundary | PENDING |
| CI-C5-4 | Versioning enforced | PENDING |
| CI-C5-5 | Learning disable flag | PENDING |
| CI-C5-6 | Kill-switch isolation | PENDING |

If any guardrail is skipped or weakened -> FAIL

**Runner:** `scripts/ci/c5_guardrails/run_all.sh`

---

## 12. S2-Specific Guardrails (Additional)

Beyond shared CI-C5-* guardrails, S2 requires:

| Guardrail | Purpose | Status |
|-----------|---------|--------|
| CI-C5-S2-1 | No priority suggestions in output | PENDING |
| CI-C5-S2-2 | No merge/consolidate language | PENDING |
| CI-C5-S2-3 | Evidence links required | PENDING |

---

## 13. Explicit Non-Goals (Re-stated)

C5-S2 does **not**:

| Non-Goal | Status |
|----------|--------|
| Suggest priority changes | PENDING |
| Merge conflicting envelopes | PENDING |
| Consolidate parameters | PENDING |
| Score envelope quality | PENDING |
| Rank envelopes | PENDING |
| Predict future conflicts | PENDING |
| Auto-resolve friction | PENDING |

Any implementation drifting toward these -> FAIL & RE-CERTIFICATION REQUIRED

---

## 14. Test Scenarios (When Implemented)

| Scenario | Description | Expected | Status |
|----------|-------------|----------|--------|
| S2-T1 | No friction in window | No suggestion | PENDING |
| S2-T2 | Single rejection | No suggestion | PENDING |
| S2-T3 | Repeated same-parameter rejection | S2-F1 suggestion | PENDING |
| S2-T4 | Priority oscillation | S2-F2 suggestion | PENDING |
| S2-T5 | Class friction | S2-F3 suggestion | PENDING |
| S2-T6 | Short-lived envelope | S2-F4 suggestion | PENDING |
| S2-T7 | Learning disabled | Silent skip | PENDING |
| S2-T8 | Human acknowledges | Status change only | PENDING |
| S2-T9 | Human dismisses | Status change only | PENDING |
| S2-T10 | Suggestion immutability | Update rejected | PENDING |
| S2-T11 | Kill-switch isolation | Zero imports | PENDING |
| S2-T12 | Evidence links valid | All IDs exist | PENDING |

---

## 15. Certification Statement Template

When certified, the statement will be:

> "C5-S2 provides advisory insights into coordination friction patterns, without influencing system behavior, without suggesting priority changes, requiring explicit human approval for any downstream action."

---

## 16. Implementation Artifacts (When Unlocked)

| Artifact | Location |
|----------|----------|
| Config | `backend/app/learning/config.py` (shared) |
| Suggestions | `backend/app/learning/suggestions.py` (shared) |
| Tables | `backend/app/learning/tables.py` (shared) |
| Observer | `backend/app/learning/s2_friction.py` (new) |
| Tests | `backend/tests/learning/test_s2_friction.py` (new) |

---

## Final Judgment

This acceptance criteria:

* Protects C1-C4
* Prevents priority manipulation
* Prevents auto-resolution
* Enforces evidence-based suggestions
* Keeps humans in control

**Status:** FROZEN (2025-12-28)
**Next Step:** Implementation LOCKED - requires explicit unlock
