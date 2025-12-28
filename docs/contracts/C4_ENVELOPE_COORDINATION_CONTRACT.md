# C4 Envelope Coordination Contract

**Version:** 1.0
**Status:** FROZEN
**Phase:** C4 (Multi-Envelope Coordination)
**Scope:** Contract only (no implementation)
**Reference:** PIN-226, PIN-230

---

## 1. Purpose (Why C4 Exists)

C4 exists to answer **one question only**:

> What happens when **more than one optimization envelope wants to act at the same time**?

C4 does **not** add intelligence.
It adds **conflict safety**.

---

## 2. Core Rule (Absolute)

> **No envelope may apply unless coordination rules explicitly allow it.**

Silence ≠ permission.

---

## 3. Envelope Classes (Declared, Not Inferred)

Every envelope **must declare exactly one class**.

| Class | Meaning |
|-------|---------|
| SAFETY | Reduces risk / blast radius |
| RELIABILITY | Improves stability / retries |
| COST | Reduces spend / throughput |
| PERFORMANCE | Improves latency / speed |

**Hard rule:** If class is missing → envelope rejected.

---

## 4. Priority Order (Frozen)

This order is **global and immutable**:

```
SAFETY
  ↓
RELIABILITY
  ↓
COST
  ↓
PERFORMANCE
```

Higher class **always dominates** lower class.

- No dynamic reprioritization
- No confidence-based overrides
- No utility scoring

---

## 5. Coordination Rules (Hard Constraints)

### C4-R1: Same-Parameter Rule

- Two envelopes **cannot** modify the same parameter
- Second envelope is rejected and audited
- No exceptions, no negotiation

### C4-R2: Same-Subsystem Rule

Multiple envelopes in the same subsystem:
- Allowed **only if parameters differ**
- Must not multiply effects
- If combined impact exceeds any bound → reject

### C4-R3: Cross-Subsystem Rule

Envelopes across subsystems are allowed **only if**:
- Priorities do not conflict
- Rollback remains independent
- If rollback coupling is required → reject

### C4-R4: Priority Preemption Rule

If a higher-priority envelope activates:
- Lower-priority envelopes must immediately revert, **OR**
- Lower-priority envelopes must never have applied

No coexistence across conflicting priorities.

---

## 6. Kill-Switch Semantics (Reaffirmed)

Kill-switch behavior is unchanged from C3:

| Property | Behavior |
|----------|----------|
| Scope | Overrides **all envelopes** |
| Effect | Reverts **all envelopes** |
| Order | Does not matter |
| Survival | No partial survival allowed |

**Invariant:** If any envelope survives kill-switch → **C4 invalid**.

---

## 7. Audit Contract (Coordination-Specific)

Every envelope decision must emit:

```yaml
coordination_audit:
  envelope_id: string
  envelope_class: SAFETY | RELIABILITY | COST | PERFORMANCE
  decision: applied | rejected | preempted
  reason: string
  conflicting_envelope_id: string (optional)
  timestamp: datetime
```

Auditors must be able to answer:

> "Why was this envelope allowed or blocked?"

---

## 8. Replay Semantics (C4-Specific)

Replay must show:

1. Envelope application order
2. Coordination decisions (allowed/blocked/preempted)
3. Preemptions with reasons
4. Reverts with triggers

**Critical constraint:** Replay **must not** infer decisions post hoc.

If replay requires explanation → C4 fails.

---

## 9. Conflict Resolution Matrix

| Envelope A Class | Envelope B Class | Same Parameter | Same Subsystem | Result |
|------------------|------------------|----------------|----------------|--------|
| SAFETY | SAFETY | Yes | - | Reject B |
| SAFETY | SAFETY | No | Yes | Allow both (if bounds ok) |
| SAFETY | RELIABILITY | - | - | B preempted if conflict |
| SAFETY | COST | - | - | B preempted if conflict |
| SAFETY | PERFORMANCE | - | - | B preempted if conflict |
| RELIABILITY | COST | - | - | COST preempted if conflict |
| RELIABILITY | PERFORMANCE | - | - | PERFORMANCE preempted if conflict |
| COST | PERFORMANCE | - | - | PERFORMANCE preempted if conflict |
| Any | Any | Yes | - | Always reject second |

---

## 10. Rollback Semantics (Multi-Envelope)

### R-C4-1: Independent Rollback (Default)

Each envelope rolls back independently:
- One envelope failure does not cascade
- Rollback order is reverse of application
- Audit captures each revert

### R-C4-2: Coupled Rollback (Explicit Only)

If envelopes declare coupling:
- All coupled envelopes revert together
- Coupling must be declared at application time
- Coupling is audited

### R-C4-3: Kill-Switch Rollback (Atomic)

Kill-switch triggers atomic revert:
- All envelopes revert
- Order is not significant
- Baseline is restored exactly
- No partial state survives

---

## 11. Explicit Non-Capabilities

C4 does **not** allow:

| Capability | Status | Reason |
|------------|--------|--------|
| Learning priorities | FORBIDDEN | Introduces drift |
| Confidence-based arbitration | FORBIDDEN | Unpredictable |
| Utility scoring | FORBIDDEN | Hidden tradeoffs |
| Cost/benefit optimization | FORBIDDEN | Invisible decisions |
| Envelope chaining | FORBIDDEN | Unbounded effects |
| Policy mutation | FORBIDDEN | Loss of control |
| Automatic tradeoffs | FORBIDDEN | Human override lost |

If any appear → re-certification required.

---

## 12. What C4 Enables (Only This)

C4 enables **safe coexistence**, not intelligence:

- Multiple envelopes active simultaneously
- Explicit conflict resolution
- Predictable dominance
- Explainable decisions
- Complete audit trail

Nothing more.

---

## 13. CI Enforcement Requirements

Before C4 implementation, CI must verify:

| Guard | Description |
|-------|-------------|
| CI-C4-1 | Every envelope declares exactly one class |
| CI-C4-2 | No envelope applies without coordination check |
| CI-C4-3 | Priority order is not overridable |
| CI-C4-4 | Same-parameter conflict is always rejected |
| CI-C4-5 | Kill-switch reverts all envelopes |
| CI-C4-6 | Coordination audit is emitted |

---

## 14. Contract Signature

This contract is **FROZEN**.

Changes require:
1. Explicit unlock request
2. Review of all C4 invariants
3. Re-certification of C3 guarantees
4. New coordination tests

---

## 15. Truth Anchor

> C4 is not about making the system smarter.
> C4 is about making multiple optimizations safe together.
> If two envelopes conflict, one loses — predictably, auditably, reversibly.
> There are no clever workarounds.
> There is only the contract.
