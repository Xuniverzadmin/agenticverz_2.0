# C3 Optimization Envelope Abstraction

**Version:** 1.0
**Status:** FROZEN
**Created:** 2025-12-28
**Phase:** C3 Optimization Safety
**Scope:** Contract only (no implementation)
**Reference:** PIN-225, C3_OPTIMIZATION_SAFETY_CONTRACT.md

---

## 1. Purpose (Why the Envelope Exists)

The **Optimization Envelope** is the *only legal interface* through which predictions may influence system behavior.

> **Predictions never modify behavior directly.**
> They may only request an envelope to be applied.

The envelope guarantees:

- bounded impact
- bounded time
- reversibility
- auditability

If any of these are missing, **C3 is invalid**.

---

## 2. Envelope Definition (Canonical Schema)

Every envelope is a **declarative contract**.
Nothing implicit. Nothing inferred.

### 2.1 Required Fields (Non-Negotiable)

```yaml
envelope_id: <string>                 # immutable, versioned
envelope_version: <semver>            # e.g. 1.0.0

trigger:
  prediction_type: <enum>             # C2 prediction type
  min_confidence: <float 0.0-1.0>     # advisory threshold only

scope:
  target_subsystem: <enum>            # e.g. retry_policy, scheduler
  target_parameter: <string>          # single parameter only

bounds:
  delta_type: <enum>                  # pct | absolute
  max_increase: <number>              # upper bound
  max_decrease: <number>              # lower bound
  absolute_ceiling: <number>          # hard stop (optional)

timebox:
  max_duration_seconds: <int>         # REQUIRED
  hard_expiry: true                   # must revert automatically

baseline:
  source: <enum>                      # config_default | last_known_good
  reference_id: <string>              # version/hash

revert_policy:
  revert_on:
    - prediction_expired
    - prediction_deleted
    - kill_switch
    - validation_error
    - system_restart

audit:
  record_prediction_id: true
  record_envelope_id: true
  record_applied_delta: true
  record_start_time: true
  record_end_time: true
```

**If any field is missing, the envelope is INVALID.**

---

## 3. Validation Rules (Hard Gates)

These rules are evaluated **before an envelope can ever apply**.

### V1. Single-Parameter Rule

- Exactly **one** `target_parameter`
- No compound or derived parameters

**REJECT if violated.**

---

### V2. Explicit Bounds Rule

- Bounds must be numeric
- No "adaptive", "dynamic", or computed bounds

**REJECT if bounds are inferred.**

---

### V3. Timebox Rule

- `max_duration_seconds` must be finite
- No rolling extensions
- No auto-renew

**REJECT if extension is attempted.**

---

### V4. Baseline Integrity Rule

- Baseline must be:
  - explicit
  - versioned
  - restorable without computation

**REJECT if baseline is "current state".**

---

### V5. Prediction Dependency Rule

- Envelope validity depends on prediction existence
- If prediction disappears → envelope must revert

**REJECT envelopes without revert policy.**

---

## 4. Envelope Application Lifecycle

This lifecycle is **fixed**. No deviations allowed.

```
[Declared]
    |
    v
[Validated]
    |
    v
[Applied] --> [Active] --> [Expired]
                  |
                  +-- kill_switch
                  +-- prediction_deleted
                  +-- error
                  v
              [Reverted]
```

### Lifecycle Invariants

- Envelope may only be **Applied** once
- Envelope may only be **Active** within timebox
- Envelope must always end in **Reverted** or **Expired**

**No terminal "active" state.**

---

## 5. Reversion Semantics (Critical)

Reversion is **not optional**.

### R1. Deterministic Revert

- Revert restores exact baseline value
- No gradual rollback
- No compensating adjustments

---

### R2. Residue-Free Guarantee

After revert:

- No state
- No flags
- No counters
- No hidden configuration

**If residue exists → C3 failure.**

---

## 6. Kill Switch Contract

The kill switch is **global and immediate**.

### Properties

- Disables **all envelopes**
- Does not require redeploy
- Does not require prediction availability
- Does not wait for timebox expiry

### Kill Switch Effects

- All active envelopes revert immediately
- No envelope may be applied while switch is active

**If kill switch is slow or partial → C3 invalid.**

---

## 7. Audit Record Contract

Every envelope must emit an **immutable audit record**.

### Required Audit Fields

```yaml
audit_event:
  envelope_id: <string>
  envelope_version: <string>
  prediction_id: <string>
  target_subsystem: <string>
  target_parameter: <string>
  baseline_value: <number>
  applied_value: <number>
  applied_at: <timestamp>
  reverted_at: <timestamp>
  revert_reason: <enum>
```

### Audit Invariant

> An auditor must be able to answer:
> **"What changed, why, for how long, and was it reversed?"**

**If any answer is ambiguous → C3 invalid.**

---

## 8. Replay & Baseline Guarantees

### Replay Without Predictions

- Must reproduce **pre-C3 baseline behavior**

### Replay With Predictions

- Must show:
  - envelope application
  - envelope expiry/revert
  - no hidden state

**If replay diverges → C3 invalid.**

---

## 9. Mapping to Frozen C3 Scenarios

| Scenario | Envelope Role |
|----------|---------------|
| C3-S1 | Retry backoff envelope |
| C3-S2 | Scheduling cadence envelope |
| C3-S3 | Forced revert via prediction loss |

**C3-S3 is mandatory.**
If S3 fails, C3 fails regardless of S1/S2.

---

## 10. Explicit Non-Goals (Locked)

The envelope must **never**:

- learn
- adapt
- chain with other envelopes
- expose controls to UI
- persist beyond timebox
- justify enforcement actions

**If any of these appear later → re-certification required.**

---

## 11. C3 Acceptance Hook

No C3 code may be written unless:

- Envelope contract is frozen ← **THIS DOCUMENT**
- Validation rules are enforced
- Kill switch semantics are agreed
- Audit schema is locked

This document is the **gate**.

---

## 12. Summary (Plain Truth)

- C2 proved predictions can exist safely
- **C3 proves predictions can influence behavior safely**
- The envelope is the safety cage

If the envelope feels boring, restrictive, and explicit — **it is correct**.

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-12-28 | Initial freeze |
