# HOC Spine Topology — Architectural Review & Decisions

**Status:** REVIEWED
**Date:** 2026-01-28
**Reference:** HOC_SPINE_TOPOLOGY_PROPOSAL.md (V1.5.0)

---

## 1. Renaming `general` → `hoc_spine`

**Status: STRONGLY CORRECT**

This is not cosmetic. It fixes a *category error* that has been poisoning classification.

### Why this is correct

* `general` behaved like:
  * a domain (files, L5 engines, L6 drivers), **and**
  * infrastructure (runtime, governance, lifecycle)
* That duality caused:
  * false "cross-domain violations"
  * endless debates about ownership
  * broken reasoning in audits and tooling

By renaming to **`hoc_spine`** and explicitly declaring:

> **hoc_spine is NOT a domain**

you restore a **clean ontological separation**.

**Conclusion:**
`hoc_spine` as *system constitution* is the right abstraction.

---

## 2. Two Constitutions Model

**Status: ARCHITECTURALLY SOUND**

The framing is precise and defensible:

### System Constitution — `hoc_spine`

* Defines **what, when, how** the *system itself* executes
* Owns:
  * lifecycle
  * orchestration
  * governance timing
  * invariants
* Cross-domain by definition
* Imported by all domains
* Never customer-facing as a "feature domain"

### Customer Constitutions — `cus/{domain}`

* Each domain defines **what, when, how** for *customer-facing behavior*
* Vertically complete:
  * L2 → L3 → L5 → L6
* Domain-isolated
* Business semantics live here

This resolves the long-standing ambiguity:

> "Is this system governance or customer policy?"

Now the answer is structural, not semantic.

---

## 3. Modified Layer Topology (V1.5.0)

**Status: CONFIRMED, with one important clarification**

### Key confirmation

* L4 Runtime **must live only in hoc_spine**
* Domains **never own L4**
* Domains *enter* L4, they don't define it

This aligns perfectly with the earlier rule:

> "All execution enters L4 exactly once."

### Critical clarification (important)

**Explicitly ban L5 engines inside hoc_spine.**

`hoc_spine` may have:

* L4_runtime
* services
* schemas
* drivers

But **no L5 engines**, otherwise it re-becomes a domain.

> hoc_spine is execution law, not business logic.

---

## 4. Import Rules — Verdict

The rules are **correct and complete**.

Especially important:

* **SPINE-001 / SPINE-002**
  → Spine is *legally importable* everywhere
* **DOMAIN-001**
  → Cross-domain at L5 is forbidden
* **DOMAIN-002**
  → L2 must go through L3

This eliminates 80% of ambiguity in audits.

No changes needed.

---

## 5. What Happens to "General" Domain Files?

### DECISION: Option C — Absorb into hoc_spine

#### Rejected: Option A (keep "general" as domain)

* Reintroduces the exact ambiguity just removed
* Creates:
  * "general the domain"
  * "hoc_spine the constitution"
* Humans and tools will confuse them again

#### Rejected: Option B (redistribute to other domains)

* Not default — only if a file clearly belongs to one domain

#### Approved: Option C (absorb into hoc_spine)

Move into `hoc_spine/services/` **if ALL are true**:

* No customer configuration
* No domain semantics
* Used by ≥2 domains
* Enforces invariants or shared mechanics

Examples that belong in **hoc_spine**:

* canonical_json
* dag_sorter
* webhook_verify (if system-level)
* lifecycle invariants
* shared guards

### Decision rule (simple and enforceable)

| Question | If YES | If NO |
|----------|--------|-------|
| Is it system lifecycle / invariant / orchestration? | hoc_spine | continue |
| Is it domain-specific customer behavior? | cus/{domain} | continue |
| Is it used by many domains but has no business rules? | hoc_spine/services | investigate |

---

## 6. Impact on Tooling & Scripts

The **literature generator** becomes *cleaner* with this change:

* No more "general" heuristics
* Classification becomes:
  * `hoc_spine/*` → system constitution
  * `cus/*` → customer constitution
* Many prior "violations" disappear because they were never violations

This is a **net reduction in complexity**, not an increase.

---

## Final Decisions (Binding)

1. **APPROVED** — `hoc_spine` rename and constitution model
2. **APPROVED** — Modified Topology V1.5.0
3. **REJECTED** — Do NOT keep `general` as a domain (Option A rejected)
4. **APPROVED** — Option C (absorb into spine) as true system invariants
5. **BINDING CONSTRAINT** — Never allow L5 engines inside hoc_spine
