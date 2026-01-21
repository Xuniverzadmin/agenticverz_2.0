# Run Validation Rules

**Status:** RATIFIED
**Effective:** 2026-01-18
**Authority:** Structural Completeness Definition
**Scope:** All runs persisted in the system

---

## Purpose

To define **what qualifies as a valid run** inside the system.
Invalid runs are **rejected**, not degraded.

> **Invalid runs do not exist.**
> There is no "best effort" state.

---

## Definition: Structurally Complete Run

A run is structurally complete **IFF** all conditions below hold.

### Identity Invariants

| Rule | Condition | Enforcement |
|------|-----------|-------------|
| R1 | `run_id` exists | BLOCKING |
| R2 | `agent_id` exists (NOT NULL) | BLOCKING |
| R3 | `actor_type` exists | BLOCKING |
| R4 | `actor_type = HUMAN` → `actor_id` NOT NULL | BLOCKING |
| R5 | `actor_type = SYSTEM` → `actor_id` IS NULL | BLOCKING |

---

### Attribution Integrity (Immutability)

| Rule | Condition | Enforcement |
|------|-----------|-------------|
| R6 | `agent_id` is immutable post-creation | BLOCKING |
| R7 | `actor_id` is immutable post-creation | BLOCKING |
| R8 | `actor_type` cannot be changed | BLOCKING |

---

## Rejection Semantics

If any rule fails:

| Outcome | Behavior |
|---------|----------|
| Persistence | Run MUST NOT be persisted |
| Error | Error must be explicit and typed |
| Partial writes | FORBIDDEN |

### Error Response Format

```
RUN_VALIDATION_FAILURE

Rule: R{n}
Field: {field_name}
Expected: {expected_condition}
Actual: {actual_value}
Action: REJECTED

Reference: docs/contracts/RUN_VALIDATION_RULES.md
```

---

## Analytical Implication

Because all persisted runs are structurally complete:

| Guarantee | Result |
|-----------|--------|
| Views do not need null-guards | Schema trust |
| Dimensions are trustworthy | Aggregation stability |
| Aggregations are stable | Reporting accuracy |
| "Unknown" buckets are explicit | No accidental nulls |

---

## Rule Rationale

### R1: run_id exists

Without a run_id, the execution unit has no identity. References, traces, and costs cannot be linked.

### R2: agent_id exists (NOT NULL)

A run without an agent is structurally meaningless. The system cannot attribute execution, cost, or risk to any entity.

### R3: actor_type exists

The origin class determines audit semantics. Was this human-initiated, automated, or service-driven?

### R4-R5: actor_id/actor_type consistency

If a human triggered the run, we must know who. If a system triggered the run, claiming a human actor is false attribution.

### R6-R8: Immutability

Attribution cannot be rewritten after the fact. Forensics, audits, and blame assignment depend on immutable provenance.

---

## Schema Implications

The `runs` table MUST enforce:

```sql
-- Structural completeness constraints
ALTER TABLE runs
  ALTER COLUMN agent_id SET NOT NULL,
  ALTER COLUMN actor_type SET NOT NULL;

-- actor_type enum constraint
ALTER TABLE runs
  ADD CONSTRAINT runs_actor_type_valid
  CHECK (actor_type IN ('HUMAN', 'SYSTEM', 'SERVICE'));

-- actor_id consistency constraint
ALTER TABLE runs
  ADD CONSTRAINT runs_actor_id_consistency
  CHECK (
    (actor_type = 'HUMAN' AND actor_id IS NOT NULL) OR
    (actor_type IN ('SYSTEM', 'SERVICE') AND actor_id IS NULL)
  );
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | Ingress enforcement |
| `SDSR_ATTRIBUTION_INVARIANT.md` | Control-plane law |
| `CAPABILITY_SURFACE_RULES.md` | Topic-scoped endpoint governance |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial ratification | Governance |
