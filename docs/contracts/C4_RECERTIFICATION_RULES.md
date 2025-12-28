# C4 Re-Certification Rules

**Version:** 1.0
**Status:** FROZEN
**Phase:** C4 (Multi-Envelope Coordination)
**Purpose:** Prevent silent drift, scope creep, and accidental intelligence
**Reference:** PIN-230, C4_ENVELOPE_COORDINATION_CONTRACT.md

---

## 1. Why C4 Needs Re-Certification

C4 is the **first phase where the system makes tradeoffs**.

Tradeoffs rot systems unless **re-certification is mandatory**.

Re-certification is required whenever:
- Coordination semantics change
- Priority or dominance changes
- Envelopes interact differently
- Rollback assumptions shift

> If you don't force re-certification, someone will "just tweak" C4 into C5.

---

## 2. C4 Re-Certification Triggers (Hard Rules)

### RC4-T1 — Envelope Class Model Changes

**Re-certification required if:**
- A new envelope class is added
- Class meanings change
- Class priority order changes

**Reason:** Priority defines power. Power must not drift.

---

### RC4-T2 — Coordination Decision Logic Changes

**Re-certification required if:**
- Coordination rules are modified
- Rejection → preemption semantics change
- Conflict resolution becomes conditional

**Reason:** This is the brain of C4.

---

### RC4-T3 — Multi-Envelope Rollback Semantics Change

**Re-certification required if:**
- Rollback order changes
- Partial rollback is introduced
- Rollback becomes non-deterministic

**Reason:** Partial rollback = undefined state.

---

### RC4-T4 — Kill-Switch Semantics Change

**Re-certification required if:**
- Kill-switch scope narrows
- Kill-switch becomes conditional
- Kill-switch does not revert all envelopes

**Reason:** Kill-switch is the last line of defense.

---

### RC4-T5 — Replay Semantics Change

**Re-certification required if:**
- Replay no longer shows coordination decisions
- Replay order becomes inferred
- Replay depends on live state

**Reason:** If replay lies, governance dies.

---

### RC4-T6 — Audit Schema Change

**Re-certification required if:**
- Coordination audit fields change
- Audit completeness weakens
- Decisions are no longer explainable

**Reason:** Auditors don't trust partial truth.

---

### RC4-T7 — CI Guardrail Weakening

**Re-certification required if:**
- CI-C4-1 → CI-C4-6 are weakened
- Any guardrail is downgraded from blocker
- Coordination checks become optional

**Reason:** Humans forget. CI must not.

---

### RC4-T8 — Envelope Count Expansion

**Re-certification required if:**
- More than 2 envelopes may apply concurrently
- Envelope stacking rules change

**Reason:** Coordination complexity grows non-linearly.

---

## 3. Explicit Non-Triggers

Re-certification is **NOT** required for:

| Change | Reason |
|--------|--------|
| Adding new envelope that fits existing rules | Rules unchanged |
| Tuning envelope bounds | Bounds are envelope-specific |
| Adjusting timeboxes | Timeboxes are envelope-specific |
| Adding new prediction types (C2) | C2 is advisory only |

This keeps velocity without sacrificing safety.

---

## 4. Mandatory Re-Certification Artifacts

When triggered, **ALL must be updated**:

| Artifact | Requirement |
|----------|-------------|
| C4 Coordination Contract | Version bump |
| Paper Simulation | Re-run |
| CI Guardrails | Re-validated |
| Replay Proof | Re-verified |
| Certification Statement | Updated |

**Skipping any = invalid certification.**

---

## 5. CI Enforcement

CI must:
- Fail builds when trigger conditions are detected
- Require explicit re-certification acknowledgment
- Block merge without updated certification docs

**No "temporary bypass" allowed.**

---

## 6. Re-Certification Statement Template

When re-certification is completed:

```
C4 RE-CERTIFICATION STATEMENT

Trigger: RC4-T<N> — <description>
Date: <date>
Previous Version: <version>
New Version: <version>

All coordination invariants, rollback guarantees, and replay semantics
remain valid and enforced.

Artifacts Updated:
- [ ] C4 Coordination Contract
- [ ] Paper Simulation
- [ ] CI Guardrails
- [ ] Replay Proof
- [ ] Certification Statement

Signed: <signature>
```

Anything weaker is not acceptable.

---

## 7. Trigger Detection (CI Design)

```bash
# scripts/ci/c4_recert_check.sh

# RC4-T1: Class model changes
grep -r "class.*Enum" backend/app/optimization/ | diff - baseline

# RC4-T2: Coordination logic changes
sha256sum backend/app/optimization/coordinator.py | diff - baseline

# RC4-T3: Rollback changes
grep -r "rollback\|revert" backend/app/optimization/ | diff - baseline

# RC4-T4: Kill-switch changes
sha256sum backend/app/optimization/killswitch.py | diff - baseline

# RC4-T7: Guardrail weakening
grep -c "BLOCK" scripts/ci/c4_guardrails/ | diff - baseline
```

---

## 8. Truth Anchor

> C4 is where systems start making tradeoffs.
> Tradeoffs without governance become drift.
> Drift without detection becomes C5.
> Re-certification is the firewall between safe optimization and runaway intelligence.

---

## 9. Summary Table

| ID | Trigger | Severity |
|----|---------|----------|
| RC4-T1 | Envelope class model changes | HIGH |
| RC4-T2 | Coordination decision logic changes | CRITICAL |
| RC4-T3 | Multi-envelope rollback semantics change | CRITICAL |
| RC4-T4 | Kill-switch semantics change | CRITICAL |
| RC4-T5 | Replay semantics change | HIGH |
| RC4-T6 | Audit schema change | HIGH |
| RC4-T7 | CI guardrail weakening | CRITICAL |
| RC4-T8 | Envelope count expansion | MEDIUM |

---

## 10. Status

**C4 Re-Certification Rules:** FROZEN

This document must be updated (with re-certification) if any of the triggers above are modified.
