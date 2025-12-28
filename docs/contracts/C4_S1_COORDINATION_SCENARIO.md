# C4-S1: Safe Coexistence Scenario

**Version:** 1.0
**Status:** DESIGN (No Code)
**Phase:** C4 (Multi-Envelope Coordination)
**Reference:** PIN-230, C4_ENVELOPE_COORDINATION_CONTRACT.md

---

## Purpose

This document specifies the first C4 test scenario: **Safe Coexistence**. Two envelopes in different subsystems with non-conflicting priorities should both apply, both be audited, and both revert cleanly.

**Critical:** This is a DESIGN document. No code should be written until this design is approved.

---

## Scenario Summary

| Property | Value |
|----------|-------|
| Scenario ID | C4-S1 |
| Name | Safe Coexistence |
| Type | Happy Path |
| Complexity | Low |
| Purpose | Prove multi-envelope can work safely |

---

## Scenario Description

### Setup

Two predictions arrive, triggering two different envelopes:

| Envelope | Class | Subsystem | Parameter | Prediction |
|----------|-------|-----------|-----------|------------|
| A | RELIABILITY | retry_policy | initial_backoff_ms | Incident Risk |
| B | COST | scheduler | max_concurrent_jobs | Spend Spike |

### Preconditions

1. Kill-switch is OFF
2. No envelopes currently active
3. Both predictions have sufficient confidence
4. Both predictions are not expired

### Execution Flow

```
T0: Prediction "Incident Risk" arrives (confidence: 0.85)
    → Envelope A (RELIABILITY) requests apply

T1: CoordinationManager.check_allowed(A)
    → No conflicts (no active envelopes)
    → Decision: ALLOWED
    → Audit: { envelope_id: A, class: RELIABILITY, decision: "applied", reason: "no_conflict" }
    → Envelope A applies
    → retry_policy.initial_backoff_ms: 1000 → 1200 (+20%)

T2: Prediction "Spend Spike" arrives (confidence: 0.80)
    → Envelope B (COST) requests apply

T3: CoordinationManager.check_allowed(B)
    → Active envelopes: [A]
    → Same subsystem? NO (retry_policy vs scheduler)
    → Same parameter? NO (initial_backoff_ms vs max_concurrent_jobs)
    → Priority conflict? NO (RELIABILITY and COST can coexist)
    → Decision: ALLOWED
    → Audit: { envelope_id: B, class: COST, decision: "applied", reason: "no_conflict" }
    → Envelope B applies
    → scheduler.max_concurrent_jobs: 10 → 9 (-10%)

T4: Both envelopes active
    → Active envelopes: [A, B]
    → System operating with both optimizations

T5: Envelope A expires (timebox)
    → Audit: { envelope_id: A, class: RELIABILITY, decision: "expired", reason: "timebox" }
    → retry_policy.initial_backoff_ms: 1200 → 1000 (baseline restored)
    → Active envelopes: [B]

T6: Envelope B expires (timebox)
    → Audit: { envelope_id: B, class: COST, decision: "expired", reason: "timebox" }
    → scheduler.max_concurrent_jobs: 9 → 10 (baseline restored)
    → Active envelopes: []

T7: System at baseline
    → All parameters restored
    → All audit records complete
```

---

## Expected Outcomes

### Functional Outcomes

| # | Outcome | Verification |
|---|---------|--------------|
| 1 | Both envelopes apply successfully | Envelope states are ACTIVE |
| 2 | Both parameters are modified | Values differ from baseline |
| 3 | Both parameters are within bounds | Values within envelope bounds |
| 4 | Both envelopes expire cleanly | Envelope states are EXPIRED |
| 5 | Both baselines are restored exactly | Values equal baseline |

### Audit Outcomes

| # | Outcome | Verification |
|---|---------|--------------|
| 1 | Envelope A apply audit emitted | Audit record exists |
| 2 | Envelope B apply audit emitted | Audit record exists |
| 3 | Envelope A expire audit emitted | Audit record exists |
| 4 | Envelope B expire audit emitted | Audit record exists |
| 5 | All audits have correct fields | Fields match schema |

### Invariant Verification

| Invariant | Check |
|-----------|-------|
| I-C4-1 | Both envelopes were allowed by coordination rules |
| I-C4-2 | Both envelopes declared exactly one class |
| I-C4-3 | Priority order was consulted (no conflict found) |
| I-C4-4 | Same-parameter check was performed (no conflict) |
| I-C4-5 | N/A (no priority preemption needed) |
| I-C4-6 | Kill-switch not fired (N/A) |
| I-C4-7 | All coordination decisions were audited |
| I-C4-8 | Replay would show same coordination decisions |

---

## Test Cases (Design)

### Test C4-S1-01: Both Envelopes Apply

```python
def test_c4_s1_both_envelopes_apply():
    """Both non-conflicting envelopes can apply."""
    # Arrange
    manager = CoordinationManager()
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY)
    envelope_b = create_s2_cost_envelope(class_=COST)
    prediction_a = create_prediction("incident_risk", confidence=0.85)
    prediction_b = create_prediction("spend_spike", confidence=0.80)

    # Act
    result_a = manager.apply_with_coordination(envelope_a, prediction_a)
    result_b = manager.apply_with_coordination(envelope_b, prediction_b)

    # Assert
    assert result_a.applied is True
    assert result_b.applied is True
    assert len(manager.active_envelopes) == 2
```

### Test C4-S1-02: Audit Records Complete

```python
def test_c4_s1_audit_records_complete():
    """All coordination decisions are audited."""
    # Arrange
    manager = CoordinationManager()
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY)
    envelope_b = create_s2_cost_envelope(class_=COST)
    prediction_a = create_prediction("incident_risk", confidence=0.85)
    prediction_b = create_prediction("spend_spike", confidence=0.80)

    # Act
    manager.apply_with_coordination(envelope_a, prediction_a)
    manager.apply_with_coordination(envelope_b, prediction_b)

    # Assert
    audits = manager.get_audit_records()
    assert len(audits) == 2
    assert audits[0].decision == "applied"
    assert audits[0].envelope_class == RELIABILITY
    assert audits[1].decision == "applied"
    assert audits[1].envelope_class == COST
```

### Test C4-S1-03: Independent Expiry

```python
def test_c4_s1_independent_expiry():
    """Envelopes expire independently."""
    # Arrange
    manager = CoordinationManager()
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY, timebox=60)
    envelope_b = create_s2_cost_envelope(class_=COST, timebox=120)
    prediction_a = create_prediction("incident_risk", confidence=0.85)
    prediction_b = create_prediction("spend_spike", confidence=0.80)
    manager.apply_with_coordination(envelope_a, prediction_a)
    manager.apply_with_coordination(envelope_b, prediction_b)

    # Act - simulate time passing
    manager.expire_due_envelopes(elapsed_seconds=61)

    # Assert
    assert len(manager.active_envelopes) == 1
    assert manager.active_envelopes[0].envelope_id == envelope_b.envelope_id
```

### Test C4-S1-04: Baselines Restored Exactly

```python
def test_c4_s1_baselines_restored_exactly():
    """All baselines are restored after expiry."""
    # Arrange
    manager = CoordinationManager()
    baseline_backoff = 1000
    baseline_concurrency = 10
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY)
    envelope_b = create_s2_cost_envelope(class_=COST)
    prediction_a = create_prediction("incident_risk", confidence=0.85)
    prediction_b = create_prediction("spend_spike", confidence=0.80)

    # Act
    manager.apply_with_coordination(envelope_a, prediction_a)
    manager.apply_with_coordination(envelope_b, prediction_b)
    manager.expire_all()

    # Assert
    assert manager.get_parameter("retry_policy", "initial_backoff_ms") == baseline_backoff
    assert manager.get_parameter("scheduler", "max_concurrent_jobs") == baseline_concurrency
```

### Test C4-S1-05: Kill-Switch Reverts Both

```python
def test_c4_s1_killswitch_reverts_both():
    """Kill-switch reverts all active envelopes."""
    # Arrange
    manager = CoordinationManager()
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY)
    envelope_b = create_s2_cost_envelope(class_=COST)
    prediction_a = create_prediction("incident_risk", confidence=0.85)
    prediction_b = create_prediction("spend_spike", confidence=0.80)
    manager.apply_with_coordination(envelope_a, prediction_a)
    manager.apply_with_coordination(envelope_b, prediction_b)

    # Act
    kill_switch.activate()
    results = manager.handle_kill_switch()

    # Assert
    assert len(results) == 2
    assert all(r.reverted for r in results)
    assert len(manager.active_envelopes) == 0
```

---

## Failure Injection Tests (Design)

### Test C4-S1-F1: Envelope A Fails Mid-Apply

```python
def test_c4_s1_envelope_a_fails_midapply():
    """If envelope A fails during apply, envelope B is unaffected."""
    # Arrange
    manager = CoordinationManager()
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY)
    envelope_a.inject_failure("apply")  # Will fail during apply
    envelope_b = create_s2_cost_envelope(class_=COST)
    prediction_a = create_prediction("incident_risk", confidence=0.85)
    prediction_b = create_prediction("spend_spike", confidence=0.80)

    # Act
    result_a = manager.apply_with_coordination(envelope_a, prediction_a)
    result_b = manager.apply_with_coordination(envelope_b, prediction_b)

    # Assert
    assert result_a.applied is False
    assert result_a.error is not None
    assert result_b.applied is True
    assert len(manager.active_envelopes) == 1
```

### Test C4-S1-F2: Coordination Manager Unavailable

```python
def test_c4_s1_coordinator_unavailable():
    """If coordinator is unavailable, no envelope applies."""
    # Arrange
    manager = CoordinationManager()
    manager.set_unavailable()  # Simulate failure
    envelope_a = create_s1_retry_envelope(class_=RELIABILITY)
    prediction_a = create_prediction("incident_risk", confidence=0.85)

    # Act
    result_a = manager.apply_with_coordination(envelope_a, prediction_a)

    # Assert
    assert result_a.applied is False
    assert result_a.reason == "coordinator_unavailable"
    assert len(manager.active_envelopes) == 0
```

---

## Replay Verification (Design)

### What Replay Must Show

```yaml
replay:
  events:
    - type: prediction_received
      prediction_id: pred_001
      prediction_type: incident_risk
      confidence: 0.85

    - type: coordination_check
      envelope_id: A
      envelope_class: RELIABILITY
      decision: allowed
      reason: no_conflict

    - type: envelope_applied
      envelope_id: A
      target: retry_policy.initial_backoff_ms
      baseline: 1000
      applied: 1200

    - type: prediction_received
      prediction_id: pred_002
      prediction_type: spend_spike
      confidence: 0.80

    - type: coordination_check
      envelope_id: B
      envelope_class: COST
      decision: allowed
      reason: no_conflict

    - type: envelope_applied
      envelope_id: B
      target: scheduler.max_concurrent_jobs
      baseline: 10
      applied: 9

    - type: envelope_expired
      envelope_id: A
      target: retry_policy.initial_backoff_ms
      restored: 1000

    - type: envelope_expired
      envelope_id: B
      target: scheduler.max_concurrent_jobs
      restored: 10
```

### Replay Invariant

> Given the same predictions in the same order, replay must produce the same coordination decisions.

---

## Acceptance Criteria

| # | Criterion | Pass Condition |
|---|-----------|----------------|
| 1 | Both envelopes apply | Both in ACTIVE state |
| 2 | No conflict detected | No rejection audit |
| 3 | Parameters modified | Values differ from baseline |
| 4 | Parameters within bounds | Values within envelope bounds |
| 5 | Independent expiry | One expires without affecting other |
| 6 | Baselines restored | Exact baseline after expiry |
| 7 | Audit complete | All 4 audit records present |
| 8 | Kill-switch works | Both revert on kill-switch |
| 9 | Replay deterministic | Same decisions on replay |

---

## Implementation Dependencies

Before C4-S1 can be implemented:

| Dependency | Status |
|------------|--------|
| `EnvelopeClass` enum | ⏳ PENDING |
| `envelope_class` field on Envelope | ⏳ PENDING |
| `CoordinationManager` class | ⏳ PENDING |
| `check_allowed()` method | ⏳ PENDING |
| `apply_with_coordination()` method | ⏳ PENDING |
| `CoordinationAuditRecord` schema | ⏳ PENDING |
| CI-C4-1 through CI-C4-6 guardrails | ⏳ PENDING |

---

## Related Scenarios

| Scenario | Description | Relationship |
|----------|-------------|--------------|
| C4-S2 | Same-Parameter Conflict | Tests rejection path |
| C4-S3 | Priority Preemption | Tests preemption path |
| C4-S4 | Kill-Switch Dominance | Tests atomic revert |
| C4-S5 | Coordination Failure | Tests safe fallback |

---

## Approval Requirement

This scenario design must be approved before implementation begins.

Approval checklist:
- [ ] Execution flow reviewed
- [ ] Expected outcomes reviewed
- [ ] Test cases reviewed
- [ ] Failure injection tests reviewed
- [ ] Replay verification reviewed
- [ ] Acceptance criteria approved
- [ ] No scope creep identified

---

## Truth Anchor

> C4-S1 proves that multi-envelope coordination can work.
> If two envelopes can coexist safely, the foundation is sound.
> If they cannot, C4 is invalid.
> This scenario is the proof that coordination is possible.
