# Product Boundary Contract

**Status:** ENFORCED
**Version:** 1.0
**Effective:** 2025-12-29
**Scope:** All code artifacts in /root/agenticverz2.0

---

## Prime Invariant

> **No code artifact may be created, modified, or reasoned about unless ALL of the following are declared and accepted:**
>
> 1. Product ownership
> 2. Invocation ownership
> 3. Boundary classification
> 4. Failure jurisdiction

If ANY are unknown → **STOP and ask for clarification**.

---

## The Core Shift

This contract enforces:

> **"Block code existence unless provenance is declared."**

This is a **design-time gate**, not a runtime check.

---

## Product Definitions

### AI Console (Customer Console)

The AI Console is a **read-first, decision-surface product**.

**It SHALL:**
- Own UI pages and components
- Own console-only API routes (`/guard/*`, `/customer/*`)
- Own translation adapters (thin transformation layers)
- Depend on platform services (read-only consumption)

**It SHALL NOT:**
- Be depended on by workers
- Own recovery, execution, or policy engines
- Mutate global platform state directly
- Own services that workers or SDK require

### System-Wide (Platform)

Platform capabilities serve **all product surfaces**.

**Characteristics:**
- Called by workers, SDK, multiple consoles
- Owns execution, persistence, enforcement
- Failure affects entire system, not just one console

### Product Builder

Dedicated surfaces for specific non-console use cases.

---

## Boundary Buckets (Mandatory Classification)

Every artifact MUST be classified into exactly ONE bucket:

### Bucket 1: Surface

**Definition:** User-facing presentation layer, product-specific.

**Criteria:**
- Only imported by product UI or product-specific routes
- Removal breaks ONLY this product
- No platform dependencies rely on it

**Examples:** Pages, console routes, product layouts

### Bucket 2: Adapter

**Definition:** Thin translation layer between platform and product.

**Criteria:**
- Transforms platform data into product semantics
- Must remain thin (< 200 LOC, no business logic)
- May not mutate global state
- Called only by product surface

**Examples:** Evidence export, policy proposals, predictions

**Warning:** Adapter creep is the #1 boundary violation. If an adapter:
- Grows > 200 LOC
- Adds business logic
- Introduces state mutation

→ It must be **split** or **promoted to platform**.

### Bucket 3: Platform

**Definition:** Shared infrastructure serving multiple surfaces.

**Criteria:**
- Called by workers, SDK, or multiple products
- Removal affects system-wide functionality
- Owns truth, not presentation

**Examples:** Workers, BudgetLLM, memory service, policy engine

### Bucket 4: Orphan (Invalid State)

**Definition:** Artifact with no production callers.

**Rule:** Orphans are ILLEGAL. They must be:
- Integrated (add production caller)
- Deleted
- Parked in `/archive/` with deprecation notice

No third state. No "keeping for later."

---

## Invocation Ownership Rules

### Rule 1: Caller Graph Determines Truth

Labels lie. Callers don't.

An artifact's TRUE product ownership is determined by:

```
WHO CALLS IT IN PRODUCTION (not tests)?
```

Not by:
- What label it has
- What directory it's in
- What the developer intended

### Rule 2: Non-Console Caller = Not Console-Owned

If ANY of these call an artifact:
- `workers/*`
- `sdk/*`
- `ops/*` (founder/ops console)
- External API consumers

Then the artifact is **NOT ai-console owned**.

### Rule 3: The Negative Dependency Test

Before labeling `product: ai-console`, answer:

> "Does anything NON-console depend on this?"

If yes → **platform**.

This kills 90% of mislabeling.

---

## The Three Blocking Questions

Every time code is proposed, these MUST be answered **before proceeding**:

| Question | If Answer is Uncertain |
|----------|----------------------|
| **1. Who calls this in production?** | BLOCK |
| **2. What breaks if AI Console is deleted?** | BLOCK |
| **3. Who must NOT depend on this?** | BLOCK |

Acceptable answers:
- Specific modules/files
- "Nothing" (orphan → reject or archive)
- Explicit list of forbidden callers

Unacceptable answers:
- "Not sure"
- "Later"
- "Probably"
- "We'll figure it out"

---

## Forbidden Inferences

The system is FORBIDDEN from inferring:

| Inference | Why Forbidden |
|-----------|---------------|
| Product ownership from filename | Filenames lie |
| Future callers | Speculation creates debt |
| Intended reuse | Intent ≠ reality |
| "Likely platform use" | Assumption creates boundary leak |
| Authority from behavior | Behavior must match declaration |

If not explicitly stated → it is **UNKNOWN**.
Unknown is **BLOCKING**.

---

## Boundary Violation Types

### Type 1: Mislabeled Product

**Definition:** Artifact labeled `ai-console` but has non-console callers.

**Detection:** Caller graph analysis.

**Resolution:** Reclassify to `system-wide`.

### Type 2: Adapter Creep

**Definition:** Adapter exceeds thin boundary criteria.

**Detection:** LOC > 200, state mutation, business logic.

**Resolution:** Split or promote to platform.

### Type 3: Orphan Existence

**Definition:** Artifact with no production callers.

**Detection:** Caller graph shows tests-only or no callers.

**Resolution:** Integrate or delete.

### Type 4: Dual-Surface Hazard

**Definition:** Single artifact serving multiple products.

**Detection:** Callers from multiple product surfaces.

**Resolution:** Split into product-specific facades + shared core.

### Type 5: Silent Platform Dependency

**Definition:** Console artifact secretly depends on platform state.

**Detection:** Import analysis shows hidden platform coupling.

**Resolution:** Make dependency explicit or restructure.

---

## Pre-Build Registration Requirement

### Mandatory Before Code Creation

No code may be written until this exists:

```yaml
artifact_id: AOS-XXX-YYY-ZZZ
type: service | api | page | worker | script | sdk
product: ai-console | system-wide | product-builder
bucket: surface | adapter | platform
intent:
  purpose: <1-2 sentences, no implementation details>
  user_promise: <what the user gets, or NONE>
invocation:
  expected_callers:
    - <module/file>
  forbidden_callers:
    - <module/pattern>
failure_scope:
  breaks_if_removed:
    - <product list>
  must_not_break:
    - <product/component list>
state:
  mutates_global_state: true | false
  mutates_tenant_state: true | false
```

If this cannot be filled → the artifact is not understood yet → **BLOCK**.

---

## Change Binding Rule

Any modification to existing artifact requires:

```yaml
change_reason:
  trigger: <why now>
  boundary_change: yes | no
  new_callers: []
  removed_callers: []
  bucket_migration: null | surface→adapter | adapter→platform
```

If `boundary_change: yes` → **mandatory review + reclassification**.

No silent drift.

---

## Enforcement Timeline

| Gate | When | Enforcer |
|------|------|----------|
| Design-time | Before code written | Session playbook |
| Pre-commit | Before merge | Human review |
| CI | After merge | Automated caller graph |
| Periodic | Weekly | Registry audit |

The earlier the gate, the cheaper the fix.

---

## Violation Response Protocol

1. **Detect** — Caller graph mismatch, orphan, or creep
2. **Flag** — Create boundary violation record
3. **Stop** — Block further work on artifact
4. **Classify** — Determine violation type
5. **Resolve** — Reclassify, split, delete, or document exception
6. **Verify** — Confirm caller graph matches label
7. **Close** — Update registry and PIN

---

## Known Violations (From 2025-12-29 Analysis)

| Artifact | Current Label | Violation | Required Action |
|----------|---------------|-----------|-----------------|
| recovery_matcher.py | ai-console | Mislabeled | → system-wide |
| recovery_rule_engine.py | ai-console | Mislabeled | → system-wide |
| event_emitter.py | ai-console | Wrong surface | → system-wide (founder) |
| cost_anomaly_detector.py | ai-console | Test callers | → system-wide |
| pattern_detection.py | ai-console | Orphan | → delete or integrate |
| v1_killswitch.py | ai-console | Dual-surface | → split or document |

---

## Contract Authority

This contract has **blocking authority**.

Any artifact violating this contract is **invalid, regardless of correctness**.

Code that "works" but violates boundaries is **rejected**.

---

## References

- PIN-238: Code Registration & Evolution Governance
- PIN-237: Codebase Registry Survey
- SESSION_PLAYBOOK.yaml Section 20-21
- CLAUDE_BEHAVIOR_LIBRARY.md (BL-BOUNDARY-*)

---

## One-Line Summary

> **Code may only exist if its product boundary is declared, its callers are known, and its failure scope is explicit.**
