# PolicyMetadata Maturity Registry

**Status:** LOCKED
**Version:** 1.0
**Effective:** 2026-01-19
**Reference:** PIN-447, CROSS_DOMAIN_INVARIANTS.md Section IX

---

## Purpose

This document tracks the **materialization status** of PolicyMetadata fields.
Cross-domain consumers MUST consult this registry before depending on any field.

**Core Principle:**

> Declared correctness over premature completeness.
> Null means "not yet materialized", never "not applicable".

---

## Field Maturity Matrix

| Field | Class | Status | Source | Consumer Notes |
|-------|-------|--------|--------|----------------|
| `created_at` | A | **MATERIALIZED** | DB column | Always present |
| `origin` | A | **MATERIALIZED** | `PolicyRule.source` | Maps from MANUAL/SYSTEM/LEARNED |
| `created_by` | A | **DECLARED** | Not in model | Returns null (system-generated) |
| `source_proposal_id` | A | **DECLARED** | Not in model | Returns null |
| `approved_by` | B | **DECLARED** | Not in model | Returns null (pending workflow) |
| `approved_at` | B | **DECLARED** | Not in model | Returns null (pending workflow) |
| `effective_from` | C | **DECLARED** | Not in model | Returns null (use created_at) |
| `effective_until` | C | **DECLARED** | Not in model | Returns null (no expiry) |
| `updated_at` | - | **MATERIALIZED** | DB column | Present if model has it |

---

## Field Classification

### Class A — Immutable Provenance

Fields that establish WHO created WHAT and WHERE it came from.
Once written, these fields MUST NOT change.

| Field | Meaning | Materialization Path |
|-------|---------|---------------------|
| `created_by` | Actor who created | Add `created_by` column to PolicyRule |
| `created_at` | Creation timestamp | Already in model |
| `origin` | How it was created | Maps from `PolicyRule.source` |
| `source_proposal_id` | Link to proposal | Add column if proposal workflow real |

**Stability:** IMMUTABLE after creation.

### Class B — Governance Decisions

Fields that record HUMAN approval events.
These require the proposal workflow to be real.

| Field | Meaning | Materialization Path |
|-------|---------|---------------------|
| `approved_by` | Actor who approved | Requires PolicyProposal workflow |
| `approved_at` | Approval timestamp | Requires PolicyProposal workflow |

**Stability:** WRITE-ONCE when approval occurs.

### Class C — Temporal Validity

Fields that define WHEN the policy is effective.
Required before historical analytics or time-based queries.

| Field | Meaning | Materialization Path |
|-------|---------|---------------------|
| `effective_from` | Start of validity | Add column with default = created_at |
| `effective_until` | End of validity | Add column, null = no expiry |

**Stability:** MAY be updated by governance process (with audit).

---

## Domain Consumption Rules

### Activity Domain

**Allowed fields:**
- `created_at` — for display
- `origin` — for display
- `facade_ref` — for navigation

**Forbidden:**
- Must NOT branch on null `approved_by` to infer rejection
- Must NOT use metadata for enforcement decisions
- Must NOT cache metadata fields across requests

### Incidents Domain

**Allowed fields:**
- `created_at` — for display
- `origin` — for display
- `policy_ref`, `violation_ref` — for navigation

**Forbidden:**
- Must NOT interpret null `effective_until` as "policy expired"
- Must NOT derive enforcement status from metadata
- Must NOT store metadata snapshots (use refs)

### Policy Domain (Internal)

**Full access** to all fields for:
- Governance dashboards
- Audit reports
- Lifecycle management

---

## Schema Evolution Plan

### Phase 1: Current State (ACTIVE)

- 2/9 fields materialized (created_at, origin)
- Remaining fields return null with correct semantics
- Null = "not yet materialized"

### Phase 2: Provenance Completion (PLANNED)

Add to PolicyRule model:
```python
created_by: Optional[str] = None  # actor_id
source_proposal_id: Optional[str] = None
```

Migration: Non-breaking (nullable columns).

### Phase 3: Governance Workflow (PLANNED)

Requires PolicyProposal workflow to be real:
- `approved_by` populated on proposal acceptance
- `approved_at` populated on proposal acceptance

Migration: Depends on proposal workflow implementation.

### Phase 4: Temporal Validity (PLANNED)

Add to PolicyRule model:
```python
effective_from: Optional[datetime] = None  # default = created_at
effective_until: Optional[datetime] = None  # null = no expiry
```

Migration: Non-breaking (nullable columns with defaults).

---

## Enforcement

### CI Guards

| Check | Enforcement |
|-------|-------------|
| Null semantics | Code review (INV-META-NULL-001) |
| Field consumption | BLCA import checks |
| Schema evolution | Migration review |

### Consumer Validation

Consumers MUST NOT:

```python
# FORBIDDEN - branching on null
if metadata.approved_by is None:
    raise PolicyNotApproved()  # WRONG - null != rejected

# FORBIDDEN - inferring expiry
if metadata.effective_until is None:
    assume_expired()  # WRONG - null = no expiry

# CORRECT - null-safe access
display_approval = metadata.approved_by or "Pending"
display_expiry = metadata.effective_until or "No expiry"
```

---

## Quick Reference

```
MATERIALIZED (safe to use):
  ✅ created_at  — always present
  ✅ origin      — always present
  ✅ updated_at  — present if model supports

DECLARED (returns null, semantics stable):
  ⏳ created_by        — null = system-generated
  ⏳ source_proposal_id — null = not from proposal
  ⏳ approved_by       — null = pending or N/A
  ⏳ approved_at       — null = pending or N/A
  ⏳ effective_from    — null = use created_at
  ⏳ effective_until   — null = no expiry

CONSUMER RULES:
  ❌ Branch on null to infer absence
  ❌ Treat null as negative truth
  ❌ Cache metadata across requests
  ✅ Use refs for navigation
  ✅ Display null as "Pending" or "N/A"
  ✅ Check this registry before depending on fields
```

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-01-19 | Initial maturity registry |
