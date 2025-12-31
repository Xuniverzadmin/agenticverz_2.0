# PIN-262: Signal Circuit Discovery — Governance Clarification

**Serial:** PIN-262
**Title:** Signal Circuit Discovery — Governance Clarification
**Category:** Governance / Phase 1
**Status:** RATIFIED
**Created:** 2025-12-31
**Authority:** Human-approved governance clarification

---

## Executive Summary

This PIN documents the authoritative clarification of what Signal Circuit Discovery (SCD) proves and how to evaluate circuit correctness in Phase 1.

**Key Insight:**
> A signal circuit can be structurally correct even if the system is behaviorally wrong — but a behaviorally correct system without structural signal circuits is a governance illusion.

---

## The Core Definition

**SCD proves something primitive and important:**

> If the system were to behave correctly, would the architecture even be capable of observing and enforcing that fact?

If the answer is "no", runtime correctness is irrelevant.

---

## What "Correct" Means in Phase 1

In Phase 1, a signal circuit is considered **correct** if and only if:

> Every required architectural intent has a corresponding, explicit, observable signal path — regardless of whether the code currently behaves well.

Not "working". Not "tested". Not "passes CI".

**Observable. Addressable. Ownable.**

---

## Three Levels of Truth

### Level 0 — Runtime Truth
- Is the worker actually doing the right thing?
- Is the adapter handling edge cases?
- Is the engine logic correct?

**❌ OUT OF SCOPE FOR PHASE 1**

### Level 1 — Structural Truth (Current Mission)
- Does a signal exist?
- Is it explicit (not inferred)?
- Is it bidirectional where required?
- Is it observable by CI or a human?
- Is someone accountable?

**✅ THIS IS PHASE 1**

### Level 2 — Behavioral Truth
- Does the signal fire under the right conditions?
- Does CI block when it should?
- Does remediation work?

**🚫 FORBIDDEN BEFORE PHASE 1 CLOSES**

---

## The Four Structural Tests (Authoritative)

### 1. Existence Test

Ask mechanically:
- Can I name the signal?
- Can I point to where it is emitted?
- Can I point to where it is consumed?

If any answer is "it kind of happens" → **FAIL**

### 2. Explicitness Test

Ask:
- Is the signal an explicit artifact (event, object, CI check, contract)?
- Or is it inferred from function calls, imports, return values, logs, human review?

If inferred → **IMPLICIT_SIGNAL → FAIL**

### 3. Bidirectionality Test

For every boundary:
- Does the upstream layer declare **intent**?
- Does the downstream layer report **outcome**?

If only one direction exists → **HALF-CIRCUIT → FAIL**

### 4. Observability & Ownership Test

Ask one brutal question:

> "If this signal fires and something goes wrong, who is responsible for responding?"

If no owner → **Circuit is structurally incomplete, even if it fires**

---

## Why Runtime Uncertainty Does NOT Block SCD

If the architecture **expects** a signal and you **cannot find it emitted**, mark: `MISSING_EMITTER`

You do **not** need to know whether the engine is "correct".
You only need to know whether the **architecture has a nerve** there.

---

## Governance Tasks (Explicit)

### TASK-GOV-001: Assign CI Signal Owners
- **Action:** Assign owners to all 18 unowned CI signals
- **Qualifier:** Accountability gap blocks enforcement
- **Status:** PENDING (requires human)

### TASK-GOV-002: Assign SIG-001 Owner
- **Action:** Assign single owner for SIG-001 (main CI workflow, 68KB)
- **Qualifier:** Critical control plane without owner = P0 risk
- **Status:** PENDING (requires human)

### TASK-GOV-003: Signal Ownership Required Rule
- **Action:** Any discovered signal without a named owner is classified as P0 governance defect
- **Qualifier:** Signals without owners must block Phase advancement
- **Status:** RECORDED (see SESSION_PLAYBOOK update)

---

## SESSION_PLAYBOOK Update Required

**Add to Governance Enforcement section:**

> "Any discovered signal (CI, runtime, or boundary) without a named owner is classified as a P0 governance defect and blocks phase progression. Signal Circuit Discovery must record ownership status explicitly."

---

## Phase 1 Interpretation

Current findings indicate:
- Signals **exist**
- Circuits are **partially wired**
- Enforcement is **non-deterministic**
- Failures can occur with **no responsible responder**

This is exactly what SCD is supposed to reveal.
Nothing here indicates failure of the method.
It indicates **success of the diagnosis**.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| PIN-261 | Product Development Contract v3 |
| CI_SIGNAL_REGISTRY.md | CI signal inventory |
| scd/INDEX.md | SCD boundary discovery index |
| scd/SCD-L4-L5-BOUNDARY.md | L4↔L5 discovery |
| scd/SCD-L8-ALL-BOUNDARY.md | L8↔All discovery |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | PIN-262 created — SCD governance clarification ratified |

