# PIN-272: Applicability Policy Governance

**Status:** ACTIVE (Constitutional)
**Created:** 2026-01-02
**Category:** Architecture / Authorization / Visibility
**Severity:** CONSTITUTIONAL

---

## Summary

Codifies the invariant that applicability policies gate access at request time only. They do not retroactively rewrite or partition historical data. This prevents months of unnecessary complexity while maintaining correct access control.

---

## The Problem Solved

When implementing team-level feature enablement, there's a dangerous temptation to:

1. **Over-engineer**: Create temporal ACLs, policy epochs, data partitioning
2. **Under-engineer**: Only hide in UI, leak data through APIs

Both are wrong.

### The Over-Engineering Trap

If you enforce "properly" with historical re-authorization:

| Question | Complexity |
|----------|------------|
| From which point in time is data allowed? | Temporal ACLs |
| Should Team-B see all historical data? | Policy versioning |
| What about cached reports? | Cache invalidation |
| What about materialized views? | Backfills |
| What about exports already generated? | Data partitioning |

This explodes complexity for no business value in our domain.

### The Under-Engineering Trap

If you only hide in UI:

| Leak Vector | Consequence |
|-------------|-------------|
| APIs still return data | Direct access bypass |
| Export endpoints leak | CSV download |
| Workers may send reports | Email/notification leak |
| Future engineers bypass UI | Accidental exposure |

This creates false safety.

---

## The Solution

### Prime Invariant

> **Applicability policies gate access at request time. They do not retroactively rewrite or partition historical data.**

### What This Means

| When admin enables feature | Effect |
|----------------------------|--------|
| APIs | May return data |
| Exports | Allowed |
| UI | Renders data |
| Historical data | **All becomes visible** |

| What does NOT happen | Why |
|----------------------|-----|
| Historical data mutated | No temporal ACLs needed |
| Per-team storage forks | No partitioning needed |
| Policy epochs recorded | No versioning needed |
| Backfills triggered | No data movement needed |

---

## Why This is Correct

### 1. Domain Appropriateness

Cost intelligence, metrics, traces are **analytical**, not transactional.
No legal requirement for temporal ACLs.

### 2. Enterprise Expectation

When admins grant access, teams expect history.
"See data only from today" is surprising and wrong.

### 3. Operational Sanity

| Avoided | Impact |
|---------|--------|
| Policy-epoch queries | No dual query paths |
| Cache invalidation by epoch | No stale data bugs |
| Temporal joins | No query performance issues |

---

## Architecture Pattern

```
┌─────────────────────────────────────────────────┐
│                L2: Product APIs                 │
│   GET /cost/summary → calls ApplicabilityEngine │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│            L4: ApplicabilityEngine              │
│   visibility_for(actor, resource) → Level       │
│   export_allowed(actor, resource) → bool        │
│                                                 │
│   Evaluated at REQUEST TIME, not data time      │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│             L3: Response Shaping                │
│   HIDDEN → 403 Forbidden                        │
│   METADATA_ONLY → Trends, no raw numbers        │
│   FULL → Complete data                          │
└─────────────────────────────────────────────────┘
```

---

## Visibility Levels

```python
class VisibilityLevel(Enum):
    HIDDEN = "hidden"           # Not visible at all
    METADATA_ONLY = "metadata"  # Trends, ranges, no raw numbers
    FULL = "full"               # Complete access
```

---

## UI Boundaries

### UI Must Do

- Reflect backend truth
- Disable buttons based on backend response
- Explain "Disabled by account admin"
- Link to account settings

### UI Must NOT Do

- Decide visibility
- Filter raw responses
- Assume access from role alone
- Cache visibility decisions

---

## What We Do NOT Build (Now)

| Feature | Why Deferred |
|---------|--------------|
| Temporal ACLs | No regulatory requirement |
| Policy versioning | Adds query complexity |
| Data partitioning | No isolation requirement |
| Epoch-based queries | No time-scoped access |

### When Would These Be Justified?

Only if **ALL** are true:
- Regulated data (finance, healthcare, PII)
- Legal requirement for time-bound access
- External audits demand it
- Customers explicitly ask for it

**We are not there.**

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `docs/governance/APPLICABILITY_POLICY_V1.md` | Full policy document |
| `docs/memory-pins/PIN-272-applicability-policy-governance.md` | This PIN |
| `docs/memory-pins/INDEX.md` | Updated with PIN-272 |

---

## Related PINs

- PIN-271 (RBAC Authority Separation) - Actor model
- PIN-270 (Engineering Authority) - Anti-over-engineering principles

---

## Success Criteria

- [ ] All gated resources check applicability at request time
- [ ] No historical data mutated by applicability changes
- [ ] Export endpoints explicitly check export permission
- [ ] UI reflects backend truth, does not decide
- [ ] Audit trail records policy changes (not data changes)

---

## Invariant Lock

> **Applicability policies gate access at request time.**
> **They do not retroactively rewrite or partition historical data.**
> **Historical data becomes visible once enabled.**
> **UI reflects backend truth, does not decide.**
> **Do not over-engineer. Do not under-engineer.**
