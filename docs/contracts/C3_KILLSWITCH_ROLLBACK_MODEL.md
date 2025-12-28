# C3 Kill-Switch & Rollback Model

**Version:** 1.0
**Status:** FROZEN
**Created:** 2025-12-28
**Phase:** C3 Optimization Safety
**Scope:** Contract only (no implementation)
**Reference:** PIN-225, C3_OPTIMIZATION_SAFETY_CONTRACT.md, C3_ENVELOPE_ABSTRACTION.md

---

## 1. Purpose (Why This Exists)

The **Kill-Switch** guarantees that *any* prediction-driven influence can be **immediately and globally neutralized**, regardless of:

- prediction correctness
- envelope validity
- system health
- operator confidence

> If humans lose trust, the system must stop optimizing **now**, not "soon".

This is the **hard stop** that prevents cascading failure.

---

## 2. Kill-Switch Definition

The kill-switch is a **global, authoritative state** with exactly two values:

```yaml
optimization_state:
  ENABLED | DISABLED
```

**No partial states. No per-envelope switches.**

---

## 3. Kill-Switch Invariants (Non-Negotiable)

| ID | Invariant |
|----|-----------|
| K-1 | Kill-switch overrides all envelopes |
| K-2 | Kill-switch causes immediate reversion |
| K-3 | Kill-switch does not depend on predictions |
| K-4 | Kill-switch does not require redeploy |
| K-5 | Kill-switch is auditable |

**If ANY invariant fails → C3 fails certification.**

---

## 4. Kill-Switch Activation Semantics

### 4.1 Activation Triggers (Authoritative)

The kill-switch **may be activated** by:

- Human operator (primary)
- Safety automation (optional, future)
- System integrity failure (mandatory)

The kill-switch **must not be activated** by:

- predictions
- envelopes
- optimization logic

---

### 4.2 Activation Effects (Immediate)

Upon activation:

1. **All active envelopes are revoked**
2. **All envelope deltas are reverted**
3. **No new envelopes may be applied**
4. **Predictions remain readable (O4 unaffected)**

**No grace period. No batching. No retries.**

---

## 5. Rollback Model (How Reversion Works)

Rollback is **deterministic**, not compensating.

### 5.1 Rollback Order (Fixed)

```
Kill-Switch Triggered
      |
      v
Enumerate Active Envelopes
      |
      v
Restore Baseline Values
      |
      v
Emit Audit Records
      |
      v
System Returns to Baseline State
```

Order is fixed to guarantee reproducibility.

---

### 5.2 Rollback Guarantees

| Guarantee | Requirement |
|-----------|-------------|
| R-1 | Baseline restored exactly |
| R-2 | No derived state remains |
| R-3 | Rollback is idempotent |
| R-4 | Rollback works even if prediction is missing |
| R-5 | Rollback does not create incidents |

**If rollback leaves residue → C3 invalid.**

---

## 6. Rollback Failure Handling (Critical)

If rollback fails:

- System must **fail closed**
- Optimization remains **disabled**
- Incident **may be logged**, but **must not be caused by rollback itself**

Rollback failure must never:

- re-enable optimization
- retry indefinitely
- partially apply envelopes

---

## 7. Kill-Switch Lifecycle

```
[ENABLED] ---+
             |
             v
         [DISABLED]
             |
             +-- rollback all envelopes
             +-- block new envelopes
             v
         [DISABLED + BASELINE]
```

Re-enabling optimization requires **explicit human action**.

**No auto-rearm. No cooldown logic.**

---

## 8. Audit Contract (Mandatory)

Every kill-switch event must emit an audit record.

### Required Fields

```yaml
kill_switch_event:
  event_id: <uuid>
  triggered_by: <enum>        # human | system
  trigger_reason: <string>
  activated_at: <timestamp>
  active_envelopes_count: <int>
  rollback_completed_at: <timestamp>
  rollback_status: <enum>     # success | partial | failed
```

### Audit Invariant

> An auditor must be able to answer:
> **"Who stopped optimization, when, and what was reverted?"**

---

## 9. Replay Semantics

### Replay Without Kill-Switch

- Shows normal envelope lifecycle

### Replay With Kill-Switch

- Shows:
  - envelopes active
  - kill-switch activation
  - immediate rollback
  - return to baseline

Replay must be:

- deterministic
- explainable
- identical across runs

**If replay diverges → C3 invalid.**

---

## 10. Interaction with C3 Scenarios

| Scenario | Kill-Switch Role |
|----------|------------------|
| C3-S1 | Manual kill during retry optimization |
| C3-S2 | Kill during cost smoothing window |
| C3-S3 | Mandatory kill on prediction failure |

**C3-S3 is non-optional.**
If prediction disappears and kill-switch fails → **C3 fails**.

---

## 11. Explicit Non-Goals (Locked)

The kill-switch must **never**:

- tune behavior
- degrade gracefully
- partially apply rollback
- re-enable itself
- be scoped per tenant (global only)

**If any of these appear → re-certification required.**

---

## 12. C3 Safety Closure

With:

- Envelope abstraction frozen ✅
- Kill-switch & rollback model frozen ✅

You now have:

> **A complete safety cage for prediction-driven optimization.**

Only now is **C3 implementation allowed**.

---

## 13. Implementation Gate

C3 code implementation is unlocked when:

| Prerequisite | Status |
|--------------|--------|
| C3 acceptance criteria frozen | ✅ C3_OPTIMIZATION_SAFETY_CONTRACT.md |
| Envelope abstraction frozen | ✅ C3_ENVELOPE_ABSTRACTION.md |
| Kill-switch model frozen | ✅ THIS DOCUMENT |

**All three must be frozen before any C3 code is written.**

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-12-28 | Initial freeze |
