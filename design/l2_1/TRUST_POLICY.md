# AURORA L2 Trust Policy

**Status:** RATIFIED
**Version:** 1.0
**Effective:** 2026-01-15
**Reference:** PIN-421, aurora_trust_evaluator.py

---

## Purpose

This document defines the rules for trust lifecycle in the AURORA L2 pipeline.
Trust is machine-owned. Humans cannot grant or revoke trust directly.

> **Trust is earned through stability, lost through regression, and immune to noise.**

---

## Trust Lifecycle

```
DECLARED → OBSERVED → TRUSTED → (demotion) → OBSERVED
              ↑                                  │
              └──────────────────────────────────┘
```

---

## 1. What Breaks Trust?

### Immediate Demotion (TRUSTED → OBSERVED)

| Trigger | Reason | Action |
|---------|--------|--------|
| **REALITY_MISMATCH** | Endpoint disappeared from backend | Immediate demotion |
| **SEMANTIC_REGRESSION** | Previously passing invariant now fails | Immediate demotion |
| **Coherency failure** | COH-009 or COH-010 fails | Immediate demotion |

These are **structural failures** — the system changed underneath the capability.

### Threshold-Based Demotion

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Pass rate drops below | 90% over 7 days | Demote to OBSERVED |
| Consecutive failures exceed | 3 in a row | Demote to OBSERVED |
| Invariant set changes | Different invariants passing | Demote to OBSERVED |

These are **stability failures** — the capability no longer demonstrates consistent behavior.

### What Does NOT Break Trust

| Event | Why Ignored |
|-------|-------------|
| Single transient failure | Network blip, not structural |
| Auth failure (401/403) | Credential issue, not capability issue |
| SDSR not run for N days | Absence of evidence ≠ evidence of absence |

---

## 2. What Resets Trust?

### Re-earning TRUSTED Status

After demotion, a capability must re-earn trust from scratch:

| Requirement | Value | Notes |
|-------------|-------|-------|
| Minimum runs | 10 | Fresh observation window |
| Pass rate | 98% | Higher bar after demotion |
| Consecutive failures | ≤ 1 | Stricter than initial |
| Time window | 7 days | Recent stability only |
| Invariant stability | Required | Same invariants passing |

### Trust History Preserved

Demotion does not delete history. The trust_history directory retains all observations for:
- Root cause analysis
- Pattern detection
- Audit trails

---

## 3. What Ignores Noise?

### Transient Failures

| Failure Class | Treatment |
|---------------|-----------|
| `TRANSIENT_FAILURE` | Logged, not counted against trust |
| `AUTH_FAILURE` | Logged, not counted against trust |
| `INTERNAL_ERROR` | Logged, flagged for investigation |

### Grace Periods

| Scenario | Grace |
|----------|-------|
| First failure after promotion | 1 retry before counting |
| Backend deployment window | Configurable skip window |
| Scheduled maintenance | Observations suspended |

### Noise vs Signal

```
NOISE (ignore):
  - Network timeout during deployment
  - 503 during backend restart
  - Rate limit hit

SIGNAL (count):
  - 404 on declared endpoint (REALITY_MISMATCH)
  - Wrong response shape (INVARIANT_VIOLATED)
  - Missing required field (SEMANTIC_REGRESSION)
```

---

## Policy Configuration

Stored in `backend/aurora_l2/tools/trust_policy.yaml`:

```yaml
# Promotion thresholds
promotion:
  min_runs: 10
  min_pass_rate: 0.98
  max_consecutive_failures: 1
  time_window_days: 7
  invariant_stability_required: true

# Demotion thresholds
demotion:
  immediate_on_reality_mismatch: true
  immediate_on_semantic_regression: true
  pass_rate_floor: 0.90
  max_consecutive_failures: 3

# Noise filtering
noise:
  ignore_transient_failures: true
  ignore_auth_failures: true
  grace_period_after_promotion: 1
```

---

## Invariants

1. **Trust is monotonic within observation window** — cannot oscillate
2. **Demotion is immediate for structural failures** — no grace period
3. **Re-earning requires fresh evidence** — old observations don't count
4. **History is immutable** — demotion doesn't delete records
5. **Humans cannot override** — trust is machine-owned

---

## Anti-Patterns (Forbidden)

| Action | Why Forbidden |
|--------|---------------|
| Manual TRUSTED promotion | Violates machine ownership |
| Ignoring REALITY_MISMATCH | Hides backend drift |
| Lowering thresholds after failure | Gaming the system |
| Deleting failed observations | Destroys audit trail |
| Skipping demotion "just this once" | Creates inconsistent state |

---

## Example Scenarios

### Scenario A: Backend Route Removed

```
1. Capability X is TRUSTED
2. Backend removes /api/v1/foo endpoint
3. SDSR runs → COH-009 fails (REALITY_MISMATCH)
4. Immediate demotion: TRUSTED → OBSERVED
5. Capability stays OBSERVED until:
   - Backend restores endpoint
   - 10 successful SDSR runs
   - 98% pass rate over 7 days
```

### Scenario B: Response Shape Changes

```
1. Capability Y is TRUSTED
2. Backend changes response from {data: [...]} to {items: [...]}
3. SDSR runs → invariant fails (SEMANTIC_REGRESSION)
4. Immediate demotion: TRUSTED → OBSERVED
5. Intent must be updated to match new shape
6. Re-verification required
```

### Scenario C: Transient Network Issue

```
1. Capability Z is TRUSTED
2. Network timeout during SDSR (TRANSIENT_FAILURE)
3. Logged but NOT counted against trust
4. Next run succeeds
5. Trust maintained
```

---

## References

- `backend/aurora_l2/tools/aurora_trust_evaluator.py` — Trust evaluation logic
- `backend/aurora_l2/tools/trust_policy.yaml` — Configurable thresholds
- `backend/scripts/sdsr/trust_history/` — Observation history
- PIN-421 — AURORA L2 Automation Suite
