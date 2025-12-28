# C5-S1 Acceptance Criteria

**Learning from Rollback Frequency**
**Version:** 2.0
**Status:** FROZEN
**Frozen Date:** 2025-12-28
**Implementation Status:** VERIFIED (46/46 checks pass)
**Reference:** PIN-232, C5_S1_LEARNING_SCENARIO.md

---

## 1. Scope & Intent (Non-Negotiable)

**C5-S1 exists solely to help humans understand envelope instability patterns.**

It does **not**:

* optimize
* tune
* adapt
* enforce
* automate

If any criterion below is violated, **C5-S1 FAILS certification**.

---

## 2. Entry Conditions (Must Already Be True)

| ID      | Condition                   | Required | Status |
| ------- | --------------------------- | -------- | ------ |
| EC-S1-1 | C4 certified                | ✅        | ✅ SATISFIED |
| EC-S1-2 | C4 stability gate satisfied | ✅        | ✅ SATISFIED (synthetic) |
| EC-S1-3 | C5 entry conditions frozen  | ✅        | ✅ FROZEN (PIN-232) |
| EC-S1-4 | C5 CI guardrails designed   | ✅        | ✅ IMPLEMENTED |
| EC-S1-5 | No C5 code exists yet       | ✅        | ✅ (was true at design) |

If any entry condition is false → **do not proceed**.

---

## 3. Observability Constraints (What C5-S1 May Observe)

### ✅ Allowed Inputs (Read-Only)

C5-S1 may observe **only**:

| Category   | Allowed                            | Status |
| ---------- | ---------------------------------- | ------ |
| Events     | Envelope rollback events           | ✅ VERIFIED |
| Metadata   | Envelope ID, class, parameter      | ✅ VERIFIED |
| Reasons    | Rollback reason codes              | ✅ VERIFIED |
| Time       | Timestamp, duration until rollback | ✅ VERIFIED |
| Aggregates | Count, frequency over fixed window | ✅ VERIFIED |

### ❌ Forbidden Inputs

C5-S1 must **never** read:

| Input | Status |
| ----- | ------ |
| runtime performance metrics | ✅ NO IMPORTS |
| live request outcomes | ✅ NO IMPORTS |
| prediction confidence loops | ✅ NO IMPORTS |
| coordination state | ✅ NO IMPORTS |
| envelope bounds directly | ✅ NO IMPORTS |
| kill-switch state | ✅ NO IMPORTS |
| user data | ✅ NO IMPORTS |
| external signals | ✅ NO IMPORTS |

**Test:** any import outside metadata tables → FAIL
**CI Enforcement:** CI-C5-3, CI-C5-6

---

## 4. Output Constraints (What C5-S1 May Produce)

### ✅ Allowed Output

Exactly **one output type** is allowed:

> **Advisory Learning Suggestion**

Required fields:

| Field                   | Requirement                      | Status |
| ----------------------- | -------------------------------- | ------ |
| advisory                | Literal `TRUE`                   | ✅ `Literal["advisory"]` |
| requires_human_approval | Literal `TRUE`                   | ✅ `status = pending_review` |
| scope                   | envelope + parameter             | ✅ `envelope_class` + `target_parameter` |
| observation_window      | explicit (e.g. last N cycles)    | ✅ `observation_window_start/end` |
| summary                 | neutral, non-imperative language | ✅ `validate_suggestion_text()` |
| version                 | immutable                        | ✅ `version >= 1` |
| timestamp               | required                         | ✅ `created_at` |

### ❌ Forbidden Outputs

C5-S1 must **not**:

| Forbidden Output | Status |
| ---------------- | ------ |
| actions | ✅ NO FIELD |
| new bounds | ✅ NO FIELD |
| thresholds | ✅ NO FIELD |
| probabilities of success | ✅ NO FIELD |
| "recommended changes" | ✅ NO FIELD |
| ranked options | ✅ NO FIELD |
| auto-approval flags | ✅ NO FIELD |

**Test:** presence of imperative verbs → FAIL
**CI Enforcement:** CI-C5-1

---

## 5. Language & Semantics (Critical)

### ✅ Mandatory Language

Suggestions **must** include at least one of:

* "observed" ✅
* "may indicate" ✅
* "suggests review" / "suggests" ✅
* "advisory" ✅
* "human decision required" / "may want to review" ✅

### ❌ Forbidden Language

Any occurrence of the following → FAIL:

| Pattern | Status |
| ------- | ------ |
| "should change" | ✅ BLOCKED |
| "system recommends" | ✅ BLOCKED |
| "will improve" | ✅ BLOCKED |
| "apply" | ✅ BLOCKED |
| "optimize" | ✅ BLOCKED |
| "automatically" | ✅ BLOCKED |
| "confidence > X" | ✅ BLOCKED |

**Enforcement:** `validate_suggestion_text()` + CI-C5-1

---

## 6. Human Approval Gate (Hard Requirement)

| Rule            | Requirement                    | Status |
| --------------- | ------------------------------ | ------ |
| Approval        | Explicit human action required | ✅ ENFORCED |
| Auto-approval   | **Forbidden**                  | ✅ NO CODE |
| System approval | **Forbidden**                  | ✅ NO CODE |
| Approval bypass | **Forbidden**                  | ✅ NO CODE |

**Test:** any suggestion applied without human approval → FAIL
**CI Enforcement:** CI-C5-2

---

## 7. Isolation Guarantees (Safety)

C5-S1 must demonstrate:

| Guarantee             | Requirement                                        | Status |
| --------------------- | -------------------------------------------------- | ------ |
| Delete safety         | Deleting all C5-S1 data changes nothing            | ✅ ISOLATED |
| Kill-switch isolation | Kill-switch works with learning disabled           | ✅ VERIFIED (CI-C5-6) |
| Replay isolation      | Replay ignores C5-S1 entirely                      | ✅ NO IMPORTS |
| Envelope independence | Envelopes behave identically with or without C5-S1 | ✅ VERIFIED |

**Test:** full deletion → baseline behavior preserved → PASS
**CI Enforcement:** CI-C5-5, CI-C5-6

---

## 8. Versioning & Immutability

| Requirement                      | Status |
| -------------------------------- | ------ |
| Suggestions append-only          | ✅ DB TRIGGER |
| Suggestions immutable            | ✅ `prevent_suggestion_mutation()` |
| Historical suggestions preserved | ✅ NO DELETE |
| Edits allowed                    | ❌ BLOCKED |

Any mutation of a suggestion record → FAIL
**CI Enforcement:** CI-C5-4

---

## 9. CI & Guardrail Mapping

C5-S1 must pass **all** of the following:

| Guardrail | Purpose                   | Status |
| --------- | ------------------------- | ------ |
| CI-C5-1   | Advisory-only enforcement | ✅ PASS |
| CI-C5-2   | Human approval required   | ✅ PASS |
| CI-C5-3   | Metadata boundary         | ✅ PASS |
| CI-C5-4   | Versioning enforced       | ✅ PASS |
| CI-C5-5   | Learning disable flag     | ✅ PASS |
| CI-C5-6   | Kill-switch isolation     | ✅ PASS |

If any guardrail is skipped or weakened → FAIL

**Runner:** `scripts/ci/c5_guardrails/run_all.sh`
**Result:** 6/6 PASS (2025-12-28)

---

## 10. Explicit Non-Goals (Re-stated)

C5-S1 does **not**:

| Non-Goal | Status |
| -------- | ------ |
| learn optimal bounds | ✅ NO CODE |
| adapt envelopes | ✅ NO CODE |
| feed back into prediction | ✅ NO CODE |
| tune coordination | ✅ NO CODE |
| rank options | ✅ NO CODE |
| score envelopes | ✅ NO CODE |
| trigger changes | ✅ NO CODE |

Any implementation drifting toward these → FAIL & RE-CERTIFICATION REQUIRED

---

## 11. Test Results (Implementation Verification)

### Unit Tests (27/27 PASS)

| Series | Tests | Status |
| ------ | ----- | ------ |
| I-Series (Invariant) | 8 | ✅ ALL PASS |
| B-Series (Boundary) | 4 | ✅ ALL PASS |
| M-Series (Immutability) | 3 | ✅ ALL PASS |
| O-Series (Observation) | 4 | ✅ ALL PASS |
| H-Series (Human Interaction) | 4 | ✅ ALL PASS |
| D-Series (Disable Flag) | 3 | ✅ ALL PASS |
| Text Generation | 1 | ✅ PASS |

### Compliance Check (46/46 PASS)

| Section | Checks | Status |
| ------- | ------ | ------ |
| 3. Observability | 7 | ✅ ALL PASS |
| 4. Output | 10 | ✅ ALL PASS |
| 5. Language | 8 | ✅ ALL PASS |
| 6. Approval Gate | 4 | ✅ ALL PASS |
| 7. Isolation | 5 | ✅ ALL PASS |
| 8. Immutability | 4 | ✅ ALL PASS |
| 9. CI Guardrails | 1 | ✅ ALL PASS |
| 10. Non-Goals | 7 | ✅ ALL PASS |

---

## 12. Certification Statement

> "C5-S1 provides advisory insights derived from rollback frequency, without influencing system behavior, requiring explicit human approval for any downstream action."

---

## 13. Implementation Artifacts

| Artifact | Location |
| -------- | -------- |
| Config | `backend/app/learning/config.py` |
| Suggestions | `backend/app/learning/suggestions.py` |
| Tables | `backend/app/learning/tables.py` |
| Observer | `backend/app/learning/s1_rollback.py` |
| Migration | `backend/alembic/versions/062_c5_learning_suggestions.py` |
| CI Scripts | `scripts/ci/c5_guardrails/` |
| Tests | `backend/tests/learning/test_s1_rollback.py` |

---

## Final Judgment

This acceptance criteria:

* protects C1–C4
* prevents silent autonomy
* enforces humility in learning
* keeps humans in control

**Status:** FROZEN (2025-12-28)
**Compliance:** 100% (46/46 checks pass)
**Certification:** READY FOR SIGN-OFF
