# CLAUDE_AUTHORITY.md
## Absolute Authority & Execution Order

This document is the **highest non-human authority** governing Claude's behavior
in this repository. It overrides all other documents except **explicit instructions
from the human system owner in the current session**.

---

## 1. Order of Precedence (Non-Negotiable)

If any conflict exists, resolve strictly in this order:

1. Explicit human instruction in the **current chat**
2. **CLAUDE_AUTHORITY.md** (this file)
3. SESSION_PLAYBOOK.yaml
4. Memory PINs
5. CI rules and scripts
6. Tests
7. Existing code

**If ambiguity remains → STOP and ask the human.
Never resolve conflicts silently.**

---

## 2. Mandatory Pre-Flight (Before Writing or Modifying Code)

Before implementing *any* task, Claude **must first output**:

- Applicable FeatureIntent(s)
- Applicable TransactionIntent(s)
- Relevant invariants (by document name)
- Expected blast radius (L2/L3/L4/L5/L6)
- Expected artifacts to be created or modified

If this pre-flight step is skipped, the task is **invalid**.

---

## 3. Classification Before Fixing (Hard Rule)

No failure may be fixed unless it is **explicitly classified first**:

- **Bucket A** — Test is wrong
- **Bucket B** — Infrastructure missing
- **Bucket C** — System bug

Classification must be encoded via:
- pytest marker
- inline comment
- or invariant documentation

**Fixing without classification is prohibited.**

---

## 3.5. Infrastructure State Declaration (Hard Rule)

All infrastructure dependencies **must be declared** in `docs/infra/INFRA_REGISTRY.md`.

### Tri-State Model

| State | Name | Meaning | Test Behavior |
|-------|------|---------|---------------|
| **A** | Chosen (Conceptual) | Selected but not wired locally | MUST skip (Bucket B) |
| **B** | Local Substitute | Stub/emulator available | MUST run |
| **C** | Fully Wired | Required and available | Failures block CI |

### Bucket B Sub-Classification

- **B1** — Production-required, locally missing (must be fixed)
- **B2** — Optional/future (intentionally deferred)

### Rules

1. Tests **must declare** infra dependency via `@requires_infra("name")`
2. State A infra **must not cause test failures** (only skips)
3. State C infra **must not be skipped** (failures are real)
4. State transitions **require human approval**

If infrastructure state is unclear → **STOP and ask**.

---

## 4. Intent Is Not Optional

All non-trivial modules **must declare FeatureIntent**.

Hierarchy (must hold):

FeatureIntent (module)
→ TransactionIntent (function)
→ Primitive (implementation)

If intent is missing:
- Claude must STOP and request clarification
- Claude must NOT infer intent silently

---

## 5. Invariants Are Sacred

Any test marked `@pytest.mark.invariant`:
- Must never be weakened
- Must never be skipped without explicit human approval
- Must have documentation in `docs/invariants/`

If an invariant fails, Claude must ask:

> "Is the invariant wrong, or is the system wrong?"

---

## 6. Guidance Over Punishment Principle

The system must:
- Prefer **guidance before enforcement**
- Prefer **construction-time correctness**
- Prefer **clear affordances over CI failure**

If a rule only triggers *after* a mistake, Claude must propose
a **guidance upgrade** (template, boilerplate, example, or guardrail).

---

## 7. Artifact Accountability (Required Output Schema)

Any claim of completion **must end with**:

Artifacts Created:
- …

Artifacts Modified:
- …

Artifacts Deleted:
- …

Governance Updated:
- …

If none, state explicitly: **None**

---

## 8. Change Freezing & Ratification

When intent tables, invariants, or priority tiers are frozen:
- Claude may not alter them
- Claude may only propose changes
- Human ratification is required

---

## 9. Evolution Rule

Every incident, failure cluster, or production bug must result in **at least one**:
- New primitive
- New intent
- New invariant
- New CI guard
- New documentation

No learning may remain implicit.

---

## 10. Final Governing Principle

> **Claude may operate across roles (architecture, governance, implementation),
> but clarity, declared intent, and authority order always outrank cleverness.**

The correct path must be the easiest path.
Block only when guidance fails.
