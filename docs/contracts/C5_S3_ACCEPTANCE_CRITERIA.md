# C5-S3 Acceptance Criteria

**Learning from Optimization Effectiveness**
**Version:** 1.0
**Status:** FROZEN (2025-12-28)
**Reference:** PIN-232, C5_S3_LEARNING_SCENARIO.md

---

## 1. Scope & Intent (Non-Negotiable)

**C5-S3 exists solely to report whether metrics moved in the intended direction.**

It does **not**:

* define thresholds
* rank envelopes
* recommend actions
* judge effectiveness
* optimize anything

If any criterion below is violated, **C5-S3 FAILS certification**.

---

## 2. Entry Conditions (Must Already Be True)

| ID | Condition | Required | Status |
|----|-----------|----------|--------|
| EC-S3-1 | C5-S1 certified | YES | CERTIFIED |
| EC-S3-2 | C5-S2 design frozen | YES | DRAFT |
| EC-S3-3 | C5 entry conditions frozen | YES | FROZEN (PIN-232) |
| EC-S3-4 | C5 CI guardrails passing | YES | PASS (6/6) |
| EC-S3-5 | S3 design frozen | YES | DRAFT |
| EC-S3-6 | No threshold creep in S1/S2 | YES | PENDING |

If any entry condition is false -> **do not proceed**.

---

## 3. Observability Constraints (What C5-S3 May Observe)

### Allowed Inputs (Read-Only)

C5-S3 may observe **only**:

| Category | Allowed | Status |
|----------|---------|--------|
| Events | Envelope lifecycle (applied, ended) | PENDING |
| Metadata | Envelope ID, class, parameter, bounds | PENDING |
| Outcomes | Envelope outcome (expired, reverted, etc.) | PENDING |
| Metrics | Historical aggregates (before/after) | PENDING |
| Time | Baseline period, envelope period | PENDING |

### Forbidden Inputs

C5-S3 must **never** read:

| Input | Status |
|-------|--------|
| Live runtime state | PENDING |
| Prediction confidence | PENDING |
| Real-time metrics | PENDING |
| Control-path signals | PENDING |
| User data | PENDING |
| Kill-switch state | PENDING |

**Test:** Any import outside metadata tables -> FAIL
**CI Enforcement:** CI-C5-3, CI-C5-6

---

## 4. Signal Detection Criteria

### S3-E1: Positive Effect

| Criterion | Requirement |
|-----------|-------------|
| AC-S3-E1-1 | Metrics moved in intended direction |
| AC-S3-E1-2 | No threshold applied |
| AC-S3-E1-3 | No "effective" judgment language |
| AC-S3-E1-4 | Reports raw before/after values |

### S3-E2: Neutral Effect

| Criterion | Requirement |
|-----------|-------------|
| AC-S3-E2-1 | Metrics did not change significantly |
| AC-S3-E2-2 | No "ineffective" judgment language |
| AC-S3-E2-3 | Reports raw before/after values |
| AC-S3-E2-4 | No recommendation to remove |

### S3-E3: Negative Effect

| Criterion | Requirement |
|-----------|-------------|
| AC-S3-E3-1 | Metrics moved opposite to intended |
| AC-S3-E3-2 | No alarm language |
| AC-S3-E3-3 | Reports raw before/after values |
| AC-S3-E3-4 | No recommendation to revert |

### S3-E4: Indeterminate

| Criterion | Requirement |
|-----------|-------------|
| AC-S3-E4-1 | Insufficient data to compare |
| AC-S3-E4-2 | Confounding factors noted if detectable |
| AC-S3-E4-3 | No guess or interpolation |
| AC-S3-E4-4 | Honest uncertainty |

---

## 5. Output Constraints (What C5-S3 May Produce)

### Allowed Output

Exactly **one output type** is allowed:

> **Advisory Learning Suggestion**

Required fields:

| Field | Requirement | Status |
|-------|-------------|--------|
| advisory | Literal `TRUE` | PENDING |
| requires_human_approval | Literal `TRUE` | PENDING |
| observed_outcome | Signal ID + raw metrics | PENDING |
| baseline_metrics | Before values | PENDING |
| envelope_metrics | During values | PENDING |
| direction | Which way metrics moved | PENDING |
| aligned | Did direction match intent? | PENDING |
| version | Immutable | PENDING |

### Forbidden Outputs

C5-S3 must **not**:

| Forbidden Output | Status |
|------------------|--------|
| Thresholds | PENDING |
| Rankings | PENDING |
| "Effective" / "Ineffective" labels | PENDING |
| Action recommendations | PENDING |
| Scores | PENDING |
| Percentages as judgment | PENDING |

**Test:** Presence of forbidden output type -> FAIL
**CI Enforcement:** CI-C5-1

---

## 6. Language & Semantics (Critical)

### Mandatory Language

Suggestions **must** include at least one of:

* "observed"
* "metrics changed from X to Y"
* "direction was [increase/decrease]"
* "during envelope period"
* "human interpretation required"

### Forbidden Language

Any occurrence of the following -> FAIL:

| Pattern | Status |
|---------|--------|
| "effective" / "ineffective" | PENDING |
| "should keep" / "should remove" | PENDING |
| "recommend continuing" | PENDING |
| "will improve" | PENDING |
| "better" / "worse" | PENDING |
| "X% improvement" as judgment | PENDING |
| "success" / "failure" | PENDING |

**Enforcement:** `validate_suggestion_text()` + CI-C5-1

---

## 7. Hard Invariants

| ID | Invariant | Test |
|----|-----------|------|
| I-C5-S3-1 | Observation only - no changes | No apply() calls |
| I-C5-S3-2 | No thresholds | No numeric comparison for judgment |
| I-C5-S3-3 | No rankings | No envelope comparison |
| I-C5-S3-4 | No recommendations | No action suggestions |
| I-C5-S3-5 | Replay independence | Replay ignores S3 |
| I-C5-S3-6 | Kill-switch independence | Zero imports |

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

C5-S3 must demonstrate:

| Guarantee | Requirement | Status |
|-----------|-------------|--------|
| Delete safety | Deleting all S3 data changes nothing | PENDING |
| Kill-switch isolation | Kill-switch works with learning disabled | PENDING |
| Replay isolation | Replay ignores S3 entirely | PENDING |
| Envelope independence | Envelopes behave identically with or without S3 | PENDING |
| S1/S2 independence | S3 does not affect S1/S2 behavior | PENDING |

**Test:** Full deletion -> baseline behavior preserved -> PASS
**CI Enforcement:** CI-C5-5, CI-C5-6

---

## 10. Versioning & Immutability

| Requirement | Status |
|-------------|--------|
| Suggestions append-only | PENDING |
| Suggestions immutable | PENDING |
| Baseline/envelope metrics preserved | PENDING |
| Edits allowed | FORBIDDEN |

Any mutation of a suggestion record -> FAIL
**CI Enforcement:** CI-C5-4

---

## 11. CI & Guardrail Mapping

C5-S3 must pass **all** of the following:

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

## 12. S3-Specific Guardrails (Additional)

Beyond shared CI-C5-* guardrails, S3 requires:

| Guardrail | Purpose | Status |
|-----------|---------|--------|
| CI-C5-S3-1 | No thresholds in code | PENDING |
| CI-C5-S3-2 | No rankings in output | PENDING |
| CI-C5-S3-3 | No "effective" language | PENDING |
| CI-C5-S3-4 | Raw metrics required | PENDING |

---

## 13. Explicit Non-Goals (Re-stated)

C5-S3 does **not**:

| Non-Goal | Status |
|----------|--------|
| Define what "effective" means | PENDING |
| Rank envelopes by outcome | PENDING |
| Recommend envelope renewal | PENDING |
| Recommend envelope removal | PENDING |
| Set thresholds for success | PENDING |
| Optimize for any metric | PENDING |
| Compare envelopes to each other | PENDING |

Any implementation drifting toward these -> FAIL & RE-CERTIFICATION REQUIRED

---

## 14. Test Scenarios (When Implemented)

| Scenario | Description | Expected | Status |
|----------|-------------|----------|--------|
| S3-T1 | Positive effect | S3-E1, raw metrics, no judgment | PENDING |
| S3-T2 | Neutral effect | S3-E2, raw metrics, no judgment | PENDING |
| S3-T3 | Negative effect | S3-E3, raw metrics, no judgment | PENDING |
| S3-T4 | Indeterminate | S3-E4, honest uncertainty | PENDING |
| S3-T5 | No threshold check | No numeric judgment | PENDING |
| S3-T6 | No ranking check | No comparison language | PENDING |
| S3-T7 | No recommendation check | No action language | PENDING |
| S3-T8 | Learning disabled | Silent skip | PENDING |
| S3-T9 | Human acknowledges | Status change only | PENDING |
| S3-T10 | Human dismisses | Status change only | PENDING |
| S3-T11 | Suggestion immutability | Update rejected | PENDING |
| S3-T12 | Kill-switch isolation | Zero imports | PENDING |

---

## 15. Certification Statement Template

When certified, the statement will be:

> "C5-S3 reports whether metrics moved in the intended direction, without defining thresholds, without ranking envelopes, without recommending actions, requiring explicit human interpretation of what constitutes effectiveness."

---

## 16. Implementation Artifacts (When Unlocked)

| Artifact | Location |
|----------|----------|
| Config | `backend/app/learning/config.py` (shared) |
| Suggestions | `backend/app/learning/suggestions.py` (shared) |
| Tables | `backend/app/learning/tables.py` (shared) |
| Observer | `backend/app/learning/s3_effectiveness.py` (new) |
| Tests | `backend/tests/learning/test_s3_effectiveness.py` (new) |

---

## 17. The Hardest Part

The hardest discipline in S3 is **not adding thresholds**.

When the system reports:
- "Cost decreased from $0.0045 to $0.0038"

The human will ask: *"Is that good enough?"*

**The system must not answer.**

Only humans can decide:
- What "enough" means
- Whether the cost was worth it
- Whether to renew the envelope
- Whether to adjust bounds

If the system answers, it has crossed into optimization.

---

## Final Judgment

This acceptance criteria:

* Protects C1-C4
* Prevents threshold creep
* Prevents ranking systems
* Prevents optimization loops
* Keeps humans as interpreters

**Status:** FROZEN (2025-12-28)
**Next Step:** Implementation LOCKED - C5 design surface COMPLETE
