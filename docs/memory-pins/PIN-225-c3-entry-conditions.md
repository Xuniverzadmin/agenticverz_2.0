# PIN-225: C3 Optimization Safety Layer — Entry Conditions

**Created:** 2025-12-28
**Status:** APPROVED
**Phase:** C3_OPTIMIZATION
**Related PINs:** PIN-220, PIN-221, PIN-222, PIN-223, PIN-224

---

## Summary

This PIN establishes the entry conditions, invariants, and test scenarios for Phase C3 — the Optimization Safety Layer. C3 allows predictions to influence behavior **only inside explicitly bounded envelopes**, with provable rollback and no silent authority.

---

## What C3 Is (And Is Not)

### C3 IS

- The **safety cage** before optimization is allowed
- Bounded influence with provable rollback
- Explicit envelopes with declared limits
- Kill switch with immediate effect

### C3 IS NOT

- Optimization itself
- Learning
- Self-healing
- Prevention

> If C3 is done right, later optimization work becomes mechanical, auditability remains intact, and failures are bounded, reversible, and explainable.

---

## C3 Invariants (Authoritative — FROZEN)

| ID | Invariant |
|----|-----------|
| I-C3-1 | Predictions may influence behavior **only via declared optimization envelopes** |
| I-C3-2 | Every prediction-driven change is **bounded** (impact + time) |
| I-C3-3 | All prediction influence is **reversible** |
| I-C3-4 | Human override always wins |
| I-C3-5 | Replay without predictions reproduces **baseline behavior** |
| I-C3-6 | Optimization failure must never create incidents |

**Enforcement:** If any invariant is violated → C3 fails.

---

## C3 Entry Criteria (Must Be True Before Any C3 Code)

| Criterion | Status |
|-----------|--------|
| C2 certified and sealed | ✅ COMPLETE (PIN-224) |
| O4 visible to humans or explicitly deferred | ✅ COMPLETE (contracts frozen) |
| Replay determinism proven | ✅ COMPLETE (Phase A.5) |
| Envelope abstraction designed | ✅ COMPLETE (C3_ENVELOPE_ABSTRACTION.md) |
| Kill switch design agreed | ✅ COMPLETE (C3_KILLSWITCH_ROLLBACK_MODEL.md) |

---

## Canonical C3 Test Scenarios (Minimal, Sufficient)

### C3-S1: Bounded Retry Optimization

**Scenario:** Prediction suggests elevated incident risk. System adjusts retry backoff parameters within a small envelope.

**Why this scenario:**
- Non-critical
- Common
- Reversible
- No policy or enforcement semantics

**Allowed influence:**
- Retry delay ± X%
- Max retries unchanged
- Duration capped (e.g., 10 minutes)

---

### C3-S2: Cost Smoothing Optimization

**Scenario:** Spend Spike prediction exists. System adjusts batch scheduling frequency (not throttling).

**Why this scenario:**
- Financial signal
- No enforcement
- No blocking
- Tests time-bound influence

**Allowed influence:**
- Scheduling cadence only
- No hard limits
- Automatic expiry

---

### C3-S3: Prediction Failure Scenario (CRITICAL)

**Scenario:** Prediction is wrong, stale, or missing. Optimization layer must do nothing or revert safely.

**Why this scenario:**
This is the **most important C3 test**. If this fails, C3 is invalid.

**Required behavior:**
- Wrong prediction → no harmful action
- Stale prediction → automatic expiry, no action
- Missing prediction → baseline behavior
- Unavailable prediction service → safe no-op

---

## Structural Difference from C2

| Aspect | C2 | C3 |
|--------|----|----|
| Predictions | Advisory only | Advisory → bounded influence |
| Behavior | Immutable | Conditionally mutable |
| Safety | Isolation | Envelope + rollback |
| Replay | Blind | Differential but explainable |
| Risk | Semantic | Operational |

**Warning:** If C3 ever starts to feel like C2, you're under-scoping it. If it starts to feel like optimization, you're over-scoping it.

---

## Implementation Order (MANDATORY)

1. Freeze C3 acceptance criteria and scenarios ← ✅ COMPLETE (this PIN)
2. Design C3 optimization envelope abstraction ← ✅ COMPLETE (C3_ENVELOPE_ABSTRACTION.md)
3. Draft C3 kill-switch and rollback model ← ✅ COMPLETE (C3_KILLSWITCH_ROLLBACK_MODEL.md)
4. Implement minimal envelope for S1 ← ✅ COMPLETE (2025-12-28)
5. CI guardrails for C3 invariants ← ✅ COMPLETE (scripts/ci/c3_guardrails/)
6. Implement S2, S3 ← ✅ COMPLETE (2025-12-28)
7. Certification ← ✅ CERTIFIED (docs/certifications/C3_CERTIFICATION_STATEMENT.md)

**All steps complete. C3 is CERTIFIED.**

---

## C3-S1 Implementation Status (2025-12-28)

### Files Created

| File | Purpose |
|------|---------|
| `backend/app/optimization/__init__.py` | C3 module exports |
| `backend/app/optimization/killswitch.py` | Kill-switch implementation (K-1 to K-5) |
| `backend/app/optimization/envelope.py` | Envelope schema and validation (V1-V5) |
| `backend/app/optimization/manager.py` | Envelope lifecycle manager |
| `backend/app/optimization/envelopes/s1_retry_backoff.py` | S1 canary envelope declaration |
| `tests/optimization/test_c3_failure_scenarios.py` | 27 tests (F-1, F-2, F-3 + invariants) |
| `scripts/ci/c3_guardrails/run_all.sh` | CI guardrails (CI-C3-1 to CI-C3-4) |

### Failure Tests (CRITICAL - Run First)

| Test | Status | Description |
|------|--------|-------------|
| F-1 | ✅ PASS | Kill-switch reverts active envelope immediately |
| F-2 | ✅ PASS | Missing/low-confidence prediction prevents application |
| F-3 | ✅ PASS | Prediction expiry reverts envelope to baseline |

### CI Guardrails

| Guard | Status | Enforcement |
|-------|--------|-------------|
| CI-C3-1 | ✅ PASS | No envelope without validation |
| CI-C3-2 | ✅ PASS | V5 enforces revert policy |
| CI-C3-3 | ✅ PASS | Kill-switch remains testable |
| CI-C3-4 | ✅ PASS | Low confidence = baseline behavior |

### Test Results (S1)

```
27 passed in 0.10s
- TestF1_KillswitchRevertsActiveEnvelope (4 tests)
- TestF2_MissingPredictionPreventsApplication (3 tests)
- TestF3_StalePredictionAutoExpires (3 tests)
- TestEnvelopeValidationRules (5 tests)
- TestKillswitchInvariants (4 tests)
- TestRollbackGuarantees (3 tests)
- TestC3Invariants (5 tests)
```

---

## C3-S2 Cost Smoothing Implementation (2025-12-28)

### S2 Envelope Specification

| Property | Value |
|----------|-------|
| Target | scheduler.max_concurrent_jobs |
| Bounds | -10% max, increase FORBIDDEN |
| Absolute Floor | 1 (never zero concurrency) |
| Timebox | 900 seconds (15 minutes) |
| Confidence | >= 0.75 |

### S2 Validation Rules (S2-V1 to S2-V5)

| Rule | Enforcement |
|------|-------------|
| S2-V1 | Increase forbidden (max_increase = 0) |
| S2-V2 | Absolute floor >= 1 |
| S2-V3 | Timebox <= 15 minutes |
| S2-V4 | Confidence >= 0.75 |
| S2-V5 | Must target max_concurrent_jobs |

### S2 Files

- `backend/app/optimization/envelopes/s2_cost_smoothing.py`
- `tests/optimization/test_c3_s2_cost_smoothing.py` (20 tests)

---

## C3-S3 Failure Matrix (CRITICAL) (2025-12-28)

### Failure Injection Matrix

| ID | Failure | Expected Outcome | Status |
|----|---------|------------------|--------|
| F-S3-1 | Prediction deleted mid-envelope | Immediate revert | ✅ PASS |
| F-S3-2 | Prediction expires early | Immediate revert | ✅ PASS |
| F-S3-3 | Kill-switch toggled repeatedly | Idempotent, no residue | ✅ PASS |
| F-S3-4 | System restart during envelope | Baseline restored | ✅ PASS |
| F-S3-5 | Envelope validation corruption | Rejected, no effect | ✅ PASS |
| F-S3-6 | Envelope store unavailable | Optimization disabled | ✅ PASS |
| F-S3-7 | Multiple envelopes requested | Duplicates rejected | ✅ PASS |
| F-S3-8 | Replay without predictions | Baseline behavior | ✅ PASS |
| F-S3-9 | Replay with failures | Deterministic sequence | ✅ PASS |

### S3 Files

- `tests/optimization/test_c3_s3_failure_matrix.py` (22 tests)

---

## Final Test Results

```
69 passed in 0.19s

- test_c3_failure_scenarios.py: 27 tests (S1 + invariants)
- test_c3_s2_cost_smoothing.py: 20 tests (S2)
- test_c3_s3_failure_matrix.py: 22 tests (S3 failure matrix)
```

---

## C3 Certification

**Status:** CERTIFIED
**Date:** 2025-12-28
**Document:** `docs/certifications/C3_CERTIFICATION_STATEMENT.md`

All invariants verified:
- I-C3-1 to I-C3-6: VERIFIED
- K-1 to K-5: VERIFIED
- R-1 to R-5: VERIFIED
- V1-V5 + S2-V1 to S2-V5: ENFORCED

---

## Truth Anchor

> C3 is not about making the system smarter. C3 is about making influence safe. The system may optimize — but only within declared, bounded, reversible, auditable envelopes. If the prediction is wrong, nothing bad happens. If the kill switch is flipped, behavior returns to baseline immediately.

---

## Certification Requirement

C3 is **COMPLETE** only if:
- All scenarios S1–S3 pass
- All invariants I-C3-* hold
- Kill switch tested
- Replay proofs captured
- No new authority introduced

Otherwise: C3 is blocked and must be redesigned.
