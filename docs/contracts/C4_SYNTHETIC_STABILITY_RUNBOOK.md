# C4 Synthetic Stability Runbook

**Version:** 1.0
**Status:** ACTIVE
**Duration:** ~10 hours (1 focused day)
**Reference:** C4_FOUNDER_STABILITY_CRITERIA.md

---

## Purpose

This runbook provides a step-by-step execution plan to achieve C4 synthetic stability in one focused day, without cutting corners or weakening governance.

**Target:** 20 coordination cycles, 3+ sessions, all entropy sources exercised.

---

## Pre-Execution Checklist

Before starting, verify:

- [ ] All C4 tests passing (83 optimization tests)
- [ ] All CI guardrails green (CI-C4-1 through CI-C4-6)
- [ ] No pending changes to coordination code
- [ ] Evidence pack template ready
- [ ] Logging enabled for coordination decisions
- [ ] Replay infrastructure working

---

## Hour 0–1: Preparation (Do NOT Skip)

### 1.1 Freeze Coordination Code

```bash
# Record current commit
git log -1 --format='%H %s' > /tmp/c4_stability_start.txt

# Confirm no uncommitted changes
git status
```

**Rule:** No commits to coordination logic after this point.

### 1.2 Confirm CI Green

```bash
./scripts/ci/c4_guardrails/run_all.sh
```

Expected: `C4 GUARDRAILS PASSED` (6/6)

### 1.3 Record Start Marker

Create stability log:

```
C4 SYNTHETIC STABILITY RUN — SESSION 1
========================================
Start: <UTC timestamp>
Commit: <hash>
Mode: Founder-only
CI Status: 6/6 passing
```

### 1.4 Prepare Envelope Definitions

Ensure you have:
- S1 envelope (retry backoff) — class: RELIABILITY
- S2 envelope (cost smoothing) — class: COST

---

## Hour 1–3: Baseline + First Overlaps (Cycles 1–5)

### Goal

Warm the system with basic coordination.

### Actions

#### Cycle 1-2: Simple Overlap

```python
# Apply S1 (RELIABILITY)
envelope_s1 = create_s1_envelope(subsystem="retry", parameter="backoff")
coordinator.apply(envelope_s1)

# Apply S2 (COST) — should coexist
envelope_s2 = create_s2_envelope(subsystem="scheduler", parameter="interval")
coordinator.apply(envelope_s2)

# Wait for natural expiry or revert both
coordinator.revert(envelope_s1)
coordinator.revert(envelope_s2)
```

**Verify:**
- [ ] Both envelopes applied
- [ ] CoordinationAuditRecord emitted for each
- [ ] Revert successful

#### Cycle 3-4: Repeat with Variation

- Apply in reverse order (S2 first, then S1)
- Verify same coexistence behavior

#### Cycle 5: First Replay

```bash
# Run replay verification
PYTHONPATH=backend python3 -m pytest backend/tests/optimization/test_c4_s1_coordination.py -v
```

**Verify:**
- [ ] All tests pass
- [ ] No replay divergence

### Checkpoint

| Metric | Target | Actual |
|--------|--------|--------|
| Cycles completed | 5 | __ |
| Overlaps | 2 | __ |
| Replays | 1 | __ |

---

## Hour 3–5: Conflict & Rejection (Cycles 6–10)

### Goal

Force refusal logic — prove same-parameter rejection works.

### Actions

#### Cycle 6-7: Same-Parameter Rejection

```python
# Apply first envelope
envelope_a = create_envelope(
    subsystem="retry",
    parameter="backoff",  # <-- same parameter
    envelope_class=EnvelopeClass.RELIABILITY
)
coordinator.apply(envelope_a)

# Attempt same parameter — MUST be rejected
envelope_b = create_envelope(
    subsystem="retry",
    parameter="backoff",  # <-- same parameter (conflict!)
    envelope_class=EnvelopeClass.COST
)
result = coordinator.check_allowed(envelope_b)

# Verify rejection
assert result.allowed == False
assert result.decision == CoordinationDecisionType.REJECTED
assert "same_parameter" in result.reason
```

**Verify:**
- [ ] Second envelope rejected
- [ ] Rejection audit record emitted
- [ ] Conflicting envelope ID logged

#### Cycle 8-9: More Rejections

Repeat with different subsystems:
- `scheduler.interval` conflict
- `memory.timeout` conflict

Each rejection = 1 cycle.

#### Cycle 10: First Backend Restart

```bash
# Restart backend mid-envelope
docker compose restart backend

# Verify envelope state recovered correctly
# (depends on your persistence model)
```

**Verify:**
- [ ] Active envelopes still tracked OR correctly expired
- [ ] No orphan envelopes
- [ ] Audit trail intact

### Checkpoint

| Metric | Target | Actual |
|--------|--------|--------|
| Cycles completed | 10 | __ |
| Same-parameter rejections | ≥3 | __ |
| Backend restarts | 1 | __ |
| Replays | ≥2 | __ |

---

## Hour 5–7: Priority Preemption (Cycles 11–15)

### Goal

Prove dominance rules — higher priority preempts lower.

### Actions

#### Cycle 11-12: RELIABILITY Preempts COST

```python
# Apply COST envelope first (lower priority)
envelope_cost = create_envelope(
    subsystem="scheduler",
    parameter="interval",
    envelope_class=EnvelopeClass.COST  # Priority 3
)
coordinator.apply(envelope_cost)

# Apply RELIABILITY envelope (higher priority, same subsystem)
envelope_reliability = create_envelope(
    subsystem="scheduler",
    parameter="delay",  # Different param, so allowed
    envelope_class=EnvelopeClass.RELIABILITY  # Priority 2
)
result = coordinator.apply(envelope_reliability)

# If same param, COST should be preempted
# Verify preemption behavior
```

**Note:** Preemption only happens if envelopes are incompatible. If different params, they coexist. Test both cases.

#### Cycle 13-14: SAFETY Preempts All

```python
# Apply any lower-priority envelope
# Then apply SAFETY envelope
# Verify SAFETY wins if conflict
```

#### Cycle 15: Restart Mid-Preemption

```bash
# With active preemption in progress, restart backend
docker compose restart backend
```

**Verify:**
- [ ] Preemption state consistent after restart
- [ ] No envelope state corruption

### Checkpoint

| Metric | Target | Actual |
|--------|--------|--------|
| Cycles completed | 15 | __ |
| Priority preemptions | ≥3 | __ |
| Backend restarts | ≥2 | __ |

---

## Hour 7–8: Kill-Switch Drills (Non-Emergency)

### Goal

Verify kill-switch supremacy without triggering emergency.

### Actions

#### Drill 1: Kill-Switch with Multiple Envelopes

```python
# Apply 2-3 envelopes
coordinator.apply(envelope_1)
coordinator.apply(envelope_2)

# Record "DRY-RUN" in logs
print("KILL-SWITCH DRY-RUN — NOT EMERGENCY")

# Fire kill-switch
reverted = coordinator.kill_switch()

# Verify all reverted
assert len(reverted) == 2
assert coordinator.active_envelope_count() == 0
```

**Verify:**
- [ ] All envelopes reverted atomically
- [ ] No envelope survives
- [ ] Audit records emitted for each revert

#### Drill 2: Kill-Switch + Replay

```bash
# After kill-switch, run replay
# Verify determinism maintained
```

### Kill-Switch Log Entry

```
KILL-SWITCH DRY-RUN
===================
Type: NON-EMERGENCY (synthetic stability test)
Envelopes reverted: 2
Emergency: NO
```

### Checkpoint

| Metric | Target | Actual |
|--------|--------|--------|
| Kill-switch dry-runs | ≥2 | __ |
| Emergency activations | 0 | __ |

---

## Hour 8–9: Final Stress (Cycles 16–20)

### Goal

Combine all entropy sources — overlap + preemption + restart + replay.

### Actions

#### Cycle 16-17: Combined Stress

```python
# Apply overlapping envelopes
# Trigger preemption
# Restart backend
# Verify state
# Replay
```

#### Cycle 18-19: Edge Cases

- Apply envelope, let it expire naturally (timebox)
- Apply envelope, revert manually
- Verify both paths work

#### Cycle 20: Final Replay

```bash
# Full replay verification
PYTHONPATH=backend python3 -m pytest backend/tests/optimization/ -v
```

**Verify:**
- [ ] All 83 tests pass
- [ ] All 14 C4 tests pass
- [ ] Replay deterministic

### Final Checkpoint

| Metric | Target | Actual |
|--------|--------|--------|
| Total cycles | ≥20 | __ |
| Overlapping envelopes | ≥10 | __ |
| Priority preemptions | ≥3 | __ |
| Same-parameter rejections | ≥3 | __ |
| Backend restarts | ≥3 | __ |
| Kill-switch dry-runs | ≥2 | __ |
| Replay verifications | ≥5 | __ |
| Emergency kill-switch | 0 | __ |

---

## Hour 9–10: Evidence Pack Assembly

### 10.1 Gather Evidence

Collect:
- Coordination audit logs
- Envelope lifecycle logs
- CI run results (all days/sessions)
- Replay verification outputs
- Kill-switch drill logs

### 10.2 Fill Evidence Pack

Open `C4_STABILITY_EVIDENCE_PACK.md` and complete:

1. Attestation Header (timestamps, commit, environment)
2. Envelope Activity Summary (counts)
3. Kill-Switch Report (emergency = 0)
4. Replay Verification Report (hash comparisons)
5. Audit Completeness (100%)
6. CI Health Report (all green)
7. Disqualifier Attestation (none occurred)
8. **Synthetic Stability Declaration** (new section)

### 10.3 Sign Declaration

```
SYNTHETIC_STABILITY_DECLARATION
- mode: founder-only (no external users)
- total_coordination_cycles: 20+
- runtime_sessions: 3+
- entropy_sources_injected:
  - overlapping_envelopes: 10+
  - priority_preemptions: 3+
  - same_parameter_rejections: 3+
  - backend_restarts: 3+
  - killswitch_dryruns: 2+
  - replay_verifications: 5+
- emergency_killswitch_activations: 0
- replay_determinism: VERIFIED
- ci_guardrails: 100% passing
- signed_by: <your identifier>
- signed_at: <UTC timestamp>
```

---

## Hour 10: Final Attestation

### Verify All Gates

| Gate | Met |
|------|-----|
| ≥20 coordination cycles | ☐ |
| ≥3 runtime sessions | ☐ |
| All entropy sources exercised | ☐ |
| Zero emergency kill-switch | ☐ |
| 100% CI guardrails | ☐ |
| Replay determinism | ☐ |
| Evidence pack complete | ☐ |

### Declare

If ALL gates are met:

> **"C4 synthetic stability gate satisfied under founder-only operation. Evidence pack reviewed."**

Record this in:
- Evidence pack
- PIN-232 (update EC5-1 status)
- Changelog

---

## Session Structure (3 Sessions)

### Session 1 (Hours 1–4)
- Cycles 1–10
- Focus: Baseline, overlaps, first rejections

### Session 2 (Hours 5–7)
- Cycles 11–15
- Focus: Preemption, restarts
- **Requires backend restart between Session 1 and 2**

### Session 3 (Hours 8–10)
- Cycles 16–20
- Focus: Kill-switch drills, final stress, evidence
- **Requires backend restart between Session 2 and 3**

---

## Troubleshooting

### If Replay Fails

1. Stop immediately
2. Investigate divergence
3. Fix coordination logic if needed
4. **Reset cycle count to 0**
5. Start over

### If Emergency Kill-Switch Triggers

1. Document incident
2. **C5 remains locked**
3. Investigate root cause
4. Fix issue
5. Start over from cycle 0

### If CI Fails

1. Do not bypass
2. Fix the issue
3. Verify CI green
4. Continue from last valid cycle

---

## Post-Completion

After successful attestation:

1. [ ] Archive evidence pack (immutable)
2. [ ] Update PIN-232 EC5-1 to SATISFIED
3. [ ] Update memory-pins INDEX.md
4. [ ] Announce C5-S1 design unlocked
5. [ ] Do NOT proceed to C5 implementation (design only)

---

## Truth Anchor

> Boredom during this runbook is a feature, not a bug.
> If nothing surprises you by cycle 15, the system is stable.
> If something surprises you at cycle 18, you found a real issue.
>
> Either outcome is valuable.
> Only fake stability is worthless.
