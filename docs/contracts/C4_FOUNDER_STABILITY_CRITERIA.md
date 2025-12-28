# C4 Founder Stability Criteria (Synthetic Mode)

**Version:** 1.0
**Status:** FROZEN
**Applies When:** No external users, founder-only operation
**Replaces:** Time-based operational stability window (7 days)
**Reference:** C4_OPERATIONAL_STABILITY_CRITERIA.md, PIN-232

---

## Purpose

To establish operational stability of the C4 Multi-Envelope Coordination layer under founder-only conditions by substituting real-world time with controlled synthetic entropy.

This ensures C5 Learning is unlocked only after coordination safety is proven under stress, not assumption.

---

## Why Synthetic Stability Is Valid

Time-based stability assumes:
- External users generate entropy
- Real traffic exercises edge cases
- Calendar duration proves robustness

When users don't exist yet, these assumptions are false.

**Synthetic stability replaces time with stress:**
- Entropy is intentional, not accidental
- Edge cases are forced, not discovered
- Duration is measured in cycles, not days

This is **stricter than time-based stability**, not weaker.

---

## Stability Definition (Founder Mode)

C4 is considered operationally stable if:

- Coordination logic survives repeated conflict, preemption, restart, and replay
- No emergency kill-switch activations occur
- All certified invariants hold under forced entropy
- Replay remains deterministic under all tested conditions

---

## 1. Coordination Cycles (Replace 7 Days)

### Cycle Definition

A **coordination cycle** is defined as:

```
Envelope apply → coordination decision → active overlap → revert/expiry → replay check
```

### Minimum Required

| Parameter | Requirement |
|-----------|-------------|
| Total coordination cycles | ≥ **20 complete cycles** |
| Runtime sessions | ≥ **3 separate sessions** |
| Cycle verification | Each cycle must include replay |

### Cycle Counting

| Action | Cycles Earned |
|--------|---------------|
| Single envelope apply + revert | 1 |
| Two envelopes overlapping + both revert | 2 |
| Preemption (higher preempts lower) | 2 |
| Same-parameter rejection | 1 |
| Restart mid-envelope + recovery | 2 |

You do NOT need 20 unique setups — just 20 verified outcomes.

---

## 2. Mandatory Entropy Sources

All must be exercised **intentionally**. Accidental entropy doesn't count.

| Entropy Source | Minimum | Purpose |
|----------------|---------|---------|
| Overlapping envelopes | ≥ 10 | Proves coexistence |
| Priority preemptions | ≥ 3 | Proves dominance rules |
| Same-parameter rejections | ≥ 3 | Proves conflict detection |
| Backend restarts mid-envelope | ≥ 3 | Proves recovery |
| Kill-switch dry-runs (non-emergency) | ≥ 2 | Proves supremacy |
| Replay verifications | ≥ 5 | Proves determinism |

### Failure to Inject Entropy

If any entropy source is not exercised → stability INVALIDATED.

You cannot claim stability by avoiding stress.

---

## 3. Kill-Switch Rule (Unchanged from Time-Based)

This rule is **non-negotiable** and **unchanged**:

| Condition | Requirement |
|-----------|-------------|
| Emergency kill-switch activations | **ZERO** |
| Dry-run toggles | Allowed (if explicitly marked non-emergency) |

### Emergency vs Dry-Run

| Type | Definition | Allowed |
|------|------------|---------|
| Emergency | Kill-switch triggered due to actual problem | NO |
| Dry-run | Deliberate test with explicit "non-emergency" marker | YES |

### Disqualification

**One emergency activation → C5 stays locked.**

No exceptions. No "it was minor". No "we recovered quickly".

---

## 4. CI & Guardrails (Non-Negotiable)

These remain **unchanged from time-based criteria**:

| Requirement | Status |
|-------------|--------|
| CI-C4-1 through CI-C4-6 | Must pass continuously |
| Guardrail modifications | **Forbidden** |
| Guardrail bypasses | **Forbidden** |
| Skip flags | **Forbidden** |
| Coordination logic changes | **Forbidden** |

### Violation Response

Any CI violation → reset stability process to cycle 0.

---

## 5. Replay Integrity (Critical — More Important in Founder Mode)

Because there are no users, **replay is your substitute for reality**.

### Required Replay Scenarios

| Scenario | Replay Required |
|----------|-----------------|
| After envelope overlap | YES |
| After priority preemption | YES |
| After same-parameter rejection | YES |
| After backend restart | YES |
| After kill-switch dry-run | YES |

### Replay Verification Criteria

| Check | Requirement |
|-------|-------------|
| Baseline replay | Identical baseline behavior |
| Multi-envelope replay | Deterministic outcomes |
| Coordination decisions | Same decisions, same order |
| Hash comparison | Must match |
| External context | None required |

### Disqualification

**Any replay divergence → stability INVALIDATED.**

---

## 6. Session Requirements

### Minimum Sessions

| Parameter | Requirement |
|-----------|-------------|
| Total sessions | ≥ 3 |
| Session gap | At least backend restart between sessions |
| Session documentation | Each session logged with start/end timestamps |

### Why Multiple Sessions

Single-session stability proves nothing about:
- State persistence
- Recovery behavior
- Cross-restart determinism

---

## 7. Evidence Requirements

Stability must be documented using:

- `C4_STABILITY_EVIDENCE_PACK.md` (existing template)
- **Synthetic Stability Declaration** section (added)
- All coordination, audit, replay, and CI evidence attached

### Synthetic Stability Declaration (Required Section)

```
SYNTHETIC_STABILITY_DECLARATION
- mode: founder-only (no external users)
- total_coordination_cycles: __
- runtime_sessions: __
- entropy_sources_injected:
  - overlapping_envelopes: __
  - priority_preemptions: __
  - same_parameter_rejections: __
  - backend_restarts: __
  - killswitch_dryruns: __
  - replay_verifications: __
- emergency_killswitch_activations: 0
- replay_determinism: VERIFIED
- ci_guardrails: 100% passing
- signed_by: ________________
- signed_at: ____-__-__ __:__:__ UTC
```

---

## 8. Explicit Disqualifiers (Instant Failure)

Same as time-based criteria, applied to synthetic mode:

| Disqualifier | Consequence |
|--------------|-------------|
| Emergency kill-switch activation | Reset to cycle 0 |
| Change to priority order | Reset to cycle 0 |
| Change to coordination logic | Reset to cycle 0 |
| Envelope chaining beyond 2 | Reset to cycle 0 |
| Learning code introduced | Reset to cycle 0 |
| Manual coordination override | Reset to cycle 0 |
| CI guardrail bypass | Reset to cycle 0 |
| Replay non-determinism | Reset to cycle 0 |

No exceptions.

---

## 9. Unlock Phrase (Founder Mode)

Only after all criteria are met, the following statement is valid:

> **"C4 synthetic stability gate satisfied under founder-only operation. Evidence pack reviewed."**

This phrase:
- Explicitly acknowledges founder-only mode
- Does not claim user-validated stability
- Is honest and auditable
- Unlocks C5-S1 design work

---

## 10. Comparison: Time-Based vs Synthetic

| Aspect | Time-Based | Synthetic |
|--------|------------|-----------|
| Duration | ≥7 days | ≥20 cycles |
| Entropy source | User traffic | Forced injection |
| Sessions | Continuous | ≥3 separate |
| Kill-switch | Zero emergency | Zero emergency |
| CI | 100% | 100% |
| Replay | Required | **More critical** |
| Validity | User-proven | Stress-proven |

Synthetic mode is **stricter** because entropy is intentional.

---

## 11. Safety Principle

> Synthetic stability is not weaker than time-based stability.
> It is stricter, because entropy is intentional, not accidental.
>
> C4 risks are structural, not behavioral.
> Coordination failures show up under conflict, not scale.
> Learning risk comes from wrong abstractions, not traffic volume.
>
> You are validating structure, not popularity.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `C4_OPERATIONAL_STABILITY_CRITERIA.md` | Time-based criteria (for production use) |
| `C4_STABILITY_EVIDENCE_PACK.md` | Evidence pack template |
| `C4_SYNTHETIC_STABILITY_RUNBOOK.md` | Execution guide |
| `PIN-232` | C5 Entry Conditions |

---

## Truth Anchor

> Most systems fake stability by waiting without stress.
> That gives false confidence, not safety.
>
> Synthetic stability replaces passive waiting with active validation.
> If the system survives forced entropy, it's ready for real entropy.
>
> If you didn't force conflict, you didn't prove coordination.
