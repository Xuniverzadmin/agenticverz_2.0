# C3 Optimization Safety Contract

**Version:** 1.0
**Status:** FROZEN
**Created:** 2025-12-28
**Reference:** PIN-225

---

## Purpose

This contract defines the acceptance criteria for Phase C3 — the Optimization Safety Layer. C3 allows predictions to influence behavior **only inside explicitly bounded envelopes**, with provable rollback and no silent authority.

---

## C3 Invariants (Authoritative)

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| I-C3-1 | Predictions may influence behavior **only via declared optimization envelopes** | Code review + CI |
| I-C3-2 | Every prediction-driven change is **bounded** (impact + time) | Envelope declaration |
| I-C3-3 | All prediction influence is **reversible** | Rollback test |
| I-C3-4 | Human override always wins | Kill switch test |
| I-C3-5 | Replay without predictions reproduces **baseline behavior** | Replay regression |
| I-C3-6 | Optimization failure must never create incidents | Failure scenario test |

**If any invariant is violated → C3 FAILS.**

---

## A. Entry Criteria

**Must be true before any C3 code is written.**

| Criterion | Required | Status |
|-----------|----------|--------|
| C2 certified and sealed | YES | ✅ COMPLETE |
| O4 visible to humans or explicitly deferred | YES | ✅ COMPLETE |
| Replay determinism proven | YES | ✅ COMPLETE |
| Kill switch design agreed | YES | ⏳ PENDING |

**If not met → DO NOT START C3.**

---

## B. Functional Acceptance

### B1. Envelope Declaration

Every optimization must declare:

| Field | Description | Required |
|-------|-------------|----------|
| `target` | What parameter can change | YES |
| `max_delta` | Maximum change from baseline | YES |
| `max_duration` | Maximum time influence can last | YES |
| `expiry_behavior` | What happens when envelope expires | YES |
| `prediction_source` | Which prediction type triggers this | YES |

**Acceptance:**
- ✅ PASS if declared in code + docs
- ❌ FAIL if implicit or inferred

---

### B2. No Implicit Authority

Predictions must NOT:
- Directly mutate behavior
- Bypass envelope logic
- Self-extend influence
- Create new envelopes dynamically

**Acceptance:**
- ✅ PASS if influence flows only via declared envelope
- ❌ FAIL otherwise

---

## C. Safety Acceptance (CRITICAL)

### C1. Bounded Impact

| Requirement | Test |
|-------------|------|
| Optimization effect never exceeds declared bounds | Bound violation test |
| Time-bound enforced automatically | Expiry test |
| No cascading effects | Isolation test |

**Acceptance:**
- ✅ PASS if bounds are provable (CI test exists)
- ❌ FAIL if unbounded or untested

---

### C2. Kill Switch

| Requirement | Test |
|-------------|------|
| One switch disables ALL prediction-driven optimization | Kill switch test |
| Immediate effect (< 1 second) | Latency test |
| No redeploy required | Runtime verification |
| Persists across restarts | Durability test |

**Acceptance:**
- ✅ PASS if kill switch tested and documented
- ❌ FAIL if manual intervention required

---

### C3. Reversibility

| Requirement | Test |
|-------------|------|
| Turning off prediction influence restores baseline behavior | Revert test |
| No lingering state after revert | State cleanup test |
| No configuration drift | Diff test |

**Acceptance:**
- ✅ PASS if revert is clean and automatic
- ❌ FAIL if cleanup required

---

### C4. Prediction Failure Safety (MOST IMPORTANT)

If prediction:
- is wrong
- expires
- disappears
- is unavailable

Then:
- Optimization does nothing harmful
- System continues normally
- No degraded behavior
- No silent failures

**Acceptance:**
- ✅ PASS if safe no-op in all failure modes
- ❌ FAIL if any degraded behavior

---

## D. Replay & Audit Acceptance

### D1. Replay Baseline Integrity

| Requirement | Test |
|-------------|------|
| Replay without predictions = pre-C3 behavior | Baseline replay test |
| Replay with predictions = explainable delta | Delta replay test |
| Differential is auditable | Audit log verification |

**Acceptance:**
- ✅ PASS if both reproducible and explainable
- ❌ FAIL if replay diverges unpredictably

---

### D2. Audit Traceability

For every optimization action:
- Prediction ID recorded
- Envelope ID recorded
- Applied delta recorded
- Duration recorded
- Outcome recorded

**Acceptance:**
- ✅ PASS if auditor can answer "why did this happen?"
- ❌ FAIL if opaque

---

## E. CI & Regression Acceptance

### E1. Automated Tests (REQUIRED)

CI must include:

| Test | Purpose |
|------|---------|
| Envelope bound check | I-C3-2 |
| Kill switch test | I-C3-4 |
| Revert test | I-C3-3 |
| Prediction-missing test | I-C3-6 |
| Baseline replay test | I-C3-5 |

---

### E2. No C2 Regression

All C2 tests must remain green:
- Advisory semantics (is_advisory=TRUE)
- Delete safety (no FK violations)
- Replay blindness (baseline unaffected)

**If C2 breaks → C3 REJECTED.**

---

## F. Exit Criteria (Binary)

C3 is **COMPLETE** only if ALL of these are true:

| Criterion | Required |
|-----------|----------|
| All scenarios S1–S3 pass | YES |
| All invariants I-C3-1 to I-C3-6 hold | YES |
| Kill switch tested | YES |
| Replay proofs captured | YES |
| No new authority introduced | YES |
| C2 regression suite green | YES |

**Otherwise: C3 is blocked and must be redesigned.**

---

## G. Canonical Test Scenarios

### C3-S1: Bounded Retry Optimization

```
GIVEN: Incident Risk prediction exists (confidence > 0.7)
AND: Retry envelope declared (max_delta: +50%, max_duration: 10m)
WHEN: System processes retry logic
THEN: Retry delay increased by ≤ 50%
AND: Effect expires after 10 minutes
AND: Max retries unchanged
AND: Audit record created
```

---

### C3-S2: Cost Smoothing Optimization

```
GIVEN: Spend Spike prediction exists
AND: Scheduling envelope declared (cadence: +20%, max_duration: 30m)
WHEN: Batch scheduler runs
THEN: Scheduling interval increased by ≤ 20%
AND: No hard limits applied
AND: Effect expires after 30 minutes
AND: Audit record created
```

---

### C3-S3: Prediction Failure Scenario

```
GIVEN: Optimization envelope is active
WHEN: Prediction becomes unavailable/wrong/stale
THEN: Optimization does nothing
AND: Baseline behavior continues
AND: No incidents created
AND: Warning logged (not error)
```

---

## H. Envelope Schema (Reference)

```yaml
optimization_envelope:
  id: string (UUID)
  name: string
  prediction_type: enum (incident_risk, spend_spike, policy_drift)
  target: string (e.g., "retry_delay_ms")
  baseline_value: number
  max_delta_percent: number
  max_delta_absolute: number (optional)
  max_duration_seconds: number
  expiry_behavior: enum (revert, freeze, warn)
  enabled: boolean
  kill_switch_respects: boolean (must be true)
```

---

## I. Kill Switch Design (Reference)

```yaml
optimization_kill_switch:
  name: "C3_OPTIMIZATION_ENABLED"
  type: environment_variable + Redis flag
  default: true
  effect: immediate (< 1s)
  scope: all optimization envelopes
  persistence: survives restart

  behavior_when_disabled:
    - all envelopes ignored
    - baseline behavior restored
    - no new optimizations applied
    - existing optimizations expire immediately
```

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-12-28 | Initial freeze |
