# C4 Operational Stability Criteria

**Version:** 1.0
**Status:** FROZEN
**Phase:** C4 → C5 Gate
**Reference:** PIN-231, PIN-232

---

## Purpose

This document defines the **exact criteria** that must be satisfied before C5 (Learning & Evolution) can be unlocked. These criteria are not guidelines — they are **hard gates**.

> C4 is *operationally stable* if multiple envelopes can coexist, coordinate, preempt, and revert **in production-like operation**, without human intervention, emergency overrides, or semantic drift — for a sustained period.

This is **not** about correctness in tests.
This is about **boring correctness over time**.

---

## 1. Stability Window Definition

### Minimum Duration

| Parameter | Requirement |
|-----------|-------------|
| Duration | ≥ **7 continuous days** (or 1 business cycle, whichever is longer) |
| Environment | **Authoritative runtime** (Neon-backed, CI-enabled, kill-switch armed) |
| Load | Normal or above-normal envelope activity |
| Code Changes | No hotfixes to coordination logic |

> **Clock Reset Rule:** If any coordination logic is changed during the window → clock resets to zero.

---

## 2. Envelope Activity Requirements

C4 must prove it can coordinate **real overlap**, not idle existence.

### Required Activity During Window

| Requirement | Threshold | Rationale |
|-------------|-----------|-----------|
| Active envelopes | ≥ **2 simultaneously active** | Proves coexistence |
| Envelope classes | ≥ **2 different classes** | Proves priority ordering |
| Coordination decisions | ≥ **10 total events** | Proves decision volume |
| Priority preemptions | ≥ **1 successful** | Proves preemption works |
| Same-parameter rejections | ≥ **1 correctly rejected** | Proves conflict detection |

> **Insufficient Activity:** If envelopes never overlap, C4 has not been exercised. Stability cannot be attested.

---

## 3. Kill-Switch Discipline (Critical Gate)

This is the **single hardest requirement** — intentionally so.

### Kill-Switch Rules

| Condition | Requirement |
|-----------|-------------|
| Emergency kill-switch activations | **ZERO** |
| Manual kill-switch tests | Allowed **only in staging**, not counted toward stability |
| Kill-switch code changes | **None during window** |

### Disqualification

**If the emergency kill-switch is triggered even once → C4 is NOT stable.**

No exceptions. No "it was just a test". No "it was minor".

The kill-switch exists for emergencies. If it fires, there was an emergency. Emergencies disqualify stability.

---

## 4. Replay Integrity Evidence

### Required Replay Guarantees

| Check | Requirement |
|-------|-------------|
| Replay without predictions | Identical baseline behavior |
| Replay with envelopes | Deterministic outcomes |
| Coordination replay | Same decisions, same order |
| Audit completeness | 100% coordination decisions replayable |

### Replay Test Protocol

1. Select 3 runs from the stability window
2. Replay each with `emit_traces=False`
3. Compare outcomes to original
4. Hash comparison must match

> **Failure Mode:** If replay needs "context" or "external state" to explain outcomes, C4 is not stable.

---

## 5. Audit Completeness Requirements

### Required Audit Artifacts

| Artifact | Requirement |
|----------|-------------|
| CoordinationAuditRecord | Emitted for **every** coordination decision |
| Envelope lifecycle logs | Apply → Active → Revert (complete chain) |
| Preemption records | Include preempting envelope ID + priority + reason |
| Rejection records | Include conflicting envelope ID + explicit cause |

### Audit Coverage

```
Audit Coverage = (Audited Decisions / Total Decisions) × 100

Required: 100%
```

---

## 6. Forbidden Signals

During the stability window, there must be **zero** occurrences of:

| Forbidden Signal | Why It Disqualifies |
|------------------|---------------------|
| Implicit retries | Hides coordination failures |
| Silent envelope drops | Loss of audit trail |
| Envelope state ambiguity | Indicates coordination bugs |
| Manual coordination overrides | Human intervention = instability |
| Priority order modifications | Violates I-C4-3 |
| Same-parameter coexistence | Violates C4-R1 |

---

## 7. CI Guardrail Health

### Guardrail Requirements

| Requirement | Status |
|-------------|--------|
| CI-C4-1 through CI-C4-6 | **100% passing** throughout window |
| Guardrail modifications | **None allowed** |
| Temporary guardrail disables | **Forbidden** |
| Skip flags | **Forbidden** |

### Evidence Required

```
For each day in stability window:
  - CI run timestamp
  - All 6 guardrails: PASS
  - No skip flags used
```

> **Disqualification:** If CI was bypassed, skipped, or modified → stability invalid.

---

## 8. Explicit Disqualifiers (Instant Failure)

C4 stability is **invalidated immediately** if any of the following occur:

| Disqualifier | Severity |
|--------------|----------|
| Emergency kill-switch activation | CRITICAL |
| Change to `ENVELOPE_CLASS_PRIORITY` | CRITICAL |
| Change to coordination decision logic | CRITICAL |
| Envelope chaining beyond 2 | HIGH |
| Learning code introduced (even unused) | HIGH |
| Manual override of coordination outcome | HIGH |
| CI guardrail bypass | HIGH |
| Replay non-determinism | HIGH |

**No exceptions. No "small fix". No "we needed to patch something".**

If any disqualifier occurs:
1. Document the incident
2. Reset the stability clock to zero
3. Restart the 7-day window

---

## 9. Evidence Pack Requirements

At the end of the stability window, produce the **C4 Stability Evidence Pack**.

### Required Contents

| Section | Contents |
|---------|----------|
| 1. Attestation Header | Start/end timestamps, environment fingerprint |
| 2. Envelope Activity Summary | Count, classes, coordination events |
| 3. Kill-Switch Report | Emergency activations: 0 |
| 4. Replay Verification | Hash comparisons, determinism confirmation |
| 5. Audit Completeness | Coverage percentage (must be 100%) |
| 6. CI Health Report | Daily guardrail pass history |
| 7. Disqualifier Check | Explicit "none occurred" attestation |

### Signatures Required

| Signer | Role |
|--------|------|
| System | Automated evidence collection |
| Human Reviewer | Manual verification and attestation |

---

## 10. Unlock Condition (Exact Phrase)

Only after the evidence pack exists, is complete, and is reviewed, the following statement becomes **mechanically true**:

> "C4 has demonstrated stable, bounded, reversible coordination under real operation without emergency intervention."

At that moment — and only then — C5 stability gate is satisfied.

### Unlock Phrase

To unlock C5-S1 design, say:

> **"C5 stability gate satisfied. Evidence pack reviewed."**

Until that phrase is spoken with evidence, **C5 stays locked**.

---

## 11. What This Prevents

This criteria exists to prevent:

| Anti-Pattern | How Criteria Prevents It |
|--------------|--------------------------|
| Learning on unstable ground | Kill-switch gate |
| Encoding transient failures as patterns | 7-day stability window |
| Training on emergency behavior | Zero emergency activations |
| Confusing test pass with production stability | Authoritative environment requirement |
| Rushing to intelligence | Evidence pack requirement |

---

## 12. Why "Boring" Is the Goal

The stability window should feel **boring**.

That's the point.

If C4 is exciting:
- envelopes are conflicting unexpectedly
- kill-switch is being considered
- coordination decisions are surprising

None of those are signs of a system ready for learning.

**Boring = predictable = stable = ready for C5.**

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `PIN-231` | C4 Certification |
| `PIN-232` | C5 Entry Conditions |
| `C4_CERTIFICATION_STATEMENT.md` | C4 formal certification |
| `C4_STABILITY_EVIDENCE_PACK.md` | Evidence pack template |
| `C5_CI_GUARDRAILS_DESIGN.md` | C5 guardrails (waiting for stability) |

---

## Truth Anchor

> Most systems fail here because they confuse *passing tests* with *operating safely*.
>
> They let learning compensate for instability.
> They unlock intelligence before control is boring.
>
> This criteria ensures learning builds on discipline — not the other way around.
