# Applicability Policy V1

**Status:** ACTIVE (Constitutional)
**Created:** 2026-01-02
**Reference:** PIN-272 (Applicability Policy Governance)

---

## Prime Invariant

> **Applicability policies gate access at request time. They do not retroactively rewrite or partition historical data.**

This single constraint prevents months of complexity.

---

## What This Means

### Authorization Controls Visibility, Not Ownership

| Concept | Meaning |
|---------|---------|
| **Visibility** | Can this actor see this data right now? |
| **Ownership** | Who created/owns this data? |
| **Partitioning** | Is data physically separated? |

**Applicability controls visibility only.**

Data ownership and partitioning are **unchanged** by applicability policies.

---

## When Admin Enables a Feature for a Team

### What Happens

When an account admin enables (e.g.) Cost Intelligence for Team-B:

| Effect | Behavior |
|--------|----------|
| APIs | May return cost intelligence data |
| Exports | Allowed |
| UI | Renders the data |
| Historical data | **Becomes visible** (all of it) |

### What Does NOT Happen

| Forbidden Effect | Why |
|------------------|-----|
| Historical data mutated | No temporal ACLs |
| Per-team storage forks | No data partitioning |
| New partitions created | No schema changes |
| Backfills triggered | No data movement |
| Policy epochs recorded | No versioned policies |

---

## Why Historical Access is Acceptable

### 1. Analytical Data, Not Transactional

Cost intelligence, metrics, traces are **insight**, not money movement.
No legal requirement for temporal ACLs in this domain.

### 2. Enterprise Expectation

When admins grant access, teams expect to see history.
"You can see cost data but only from today" is usually **surprising and wrong**.

### 3. Operational Sanity

| Avoided Complexity | Impact |
|--------------------|--------|
| Policy-epoch queries | No dual query paths |
| Cache invalidation by epoch | No stale data bugs |
| Temporal joins | No query performance issues |
| Historical backfills | No data movement ops |

---

## Visibility Levels

Applicability returns one of these levels at read time:

```python
class VisibilityLevel(Enum):
    HIDDEN = "hidden"           # Not visible at all
    METADATA_ONLY = "metadata"  # Trends, ranges, no raw numbers
    FULL = "full"               # Complete access
```

---

## Implementation Pattern

### L4: ApplicabilityEngine (Decision Point)

```python
# backend/app/applicability/engine.py

class ApplicabilityEngine:
    """
    Evaluates applicability at request time.
    No timestamps. No epochs. No history rewriting.

    Layer: L4 (Domain Engine)
    """

    def visibility_for(
        self,
        actor: ActorContext,
        resource: str,
    ) -> VisibilityLevel:
        """
        Determine visibility level for a resource.

        Evaluated at request time, not data creation time.
        """
        # 1. Check if resource is enabled for actor's team
        policy = self._get_policy(actor.account_id, actor.team_id, resource)

        if policy is None:
            return VisibilityLevel.HIDDEN

        if policy.level == "metadata":
            return VisibilityLevel.METADATA_ONLY

        return VisibilityLevel.FULL

    def export_allowed(
        self,
        actor: ActorContext,
        resource: str,
    ) -> bool:
        """
        Check if export is allowed for a resource.

        Export is a separate permission from view.
        """
        visibility = self.visibility_for(actor, resource)

        if visibility == VisibilityLevel.HIDDEN:
            return False

        # Check explicit export permission
        return self._has_export_permission(actor, resource)
```

### L3: Adapter Shapes Output

```python
# backend/app/api/cost_intelligence.py

@router.get("/cost/summary")
async def get_cost_summary(
    actor: ActorContext = Depends(get_actor),
    applicability: ApplicabilityEngine = Depends(get_applicability),
):
    visibility = applicability.visibility_for(actor, "cost_intelligence")

    if visibility == VisibilityLevel.HIDDEN:
        raise HTTPException(403, "Cost Intelligence not enabled for your team")

    data = await cost_service.get_summary(actor.tenant_id)

    if visibility == VisibilityLevel.METADATA_ONLY:
        return CostSummary(
            trend=data.trend,
            range=data.range,
            # No raw numbers
        )

    return FullCostReport(
        trend=data.trend,
        range=data.range,
        breakdown=data.breakdown,
        raw_costs=data.raw_costs,
    )
```

### L3: Export Endpoints Must Check Explicitly

```python
@router.get("/cost/export")
async def export_cost_data(
    actor: ActorContext = Depends(get_actor),
    applicability: ApplicabilityEngine = Depends(get_applicability),
):
    if not applicability.export_allowed(actor, "cost_intelligence"):
        raise HTTPException(403, "Export disabled by account admin")

    # ... generate export
```

---

## UI Role and Boundaries

### UI Must Do

| Responsibility | How |
|----------------|-----|
| Reflect backend truth | Call applicability endpoint |
| Disable buttons | Based on backend response |
| Explain state | "Disabled by account admin" |
| Link to settings | Account settings for admin |

### UI Must NOT Do

| Forbidden | Why |
|-----------|-----|
| Decide visibility | Backend owns this |
| Filter raw responses | Leaks data to console |
| Assume access from role | Applicability is separate |
| Cache visibility decisions | May become stale |

---

## What We Do NOT Build (Now)

| Feature | Why Deferred |
|---------|--------------|
| Temporal ACLs | No regulatory requirement |
| Policy versioning | Adds query complexity |
| Data partitioning | No isolation requirement |
| Historical backfills | Data doesn't move |
| Epoch-based queries | No time-scoped access |

---

## When Deeper Partitioning is Justified

Only if **ALL** are true:

| Condition | Status |
|-----------|--------|
| Regulated data (finance, healthcare, PII) | Not applicable |
| Legal requirement for time-bound access | Not applicable |
| External audits demand it | Not applicable |
| Customers explicitly ask for it | Not requested |

**We are not there.** Do not over-engineer.

---

## Resources and Applicability

### Always Visible (No Applicability Check)

| Resource | Reason |
|----------|--------|
| Account settings | Admin always sees |
| Team membership | Required for operation |
| Billing summary | Account-level always |

### Gated by Applicability

| Resource | Default for New Teams |
|----------|----------------------|
| Cost Intelligence | HIDDEN |
| Advanced Analytics | HIDDEN |
| Compliance Reports | HIDDEN |
| Raw Trace Export | HIDDEN |

### Never Historically Sensitive

| Resource | Reason |
|----------|--------|
| Execution runs | Operational data |
| Agent definitions | Configuration |
| Skill definitions | Configuration |
| Metrics | Observability |

---

## Messaging in UI

### When Feature is Disabled

```
┌─────────────────────────────────────────────┐
│  Cost Intelligence                          │
│                                             │
│  This feature is not enabled for your team. │
│                                             │
│  Contact your account admin to enable it.   │
│  [Go to Account Settings]                   │
└─────────────────────────────────────────────┘
```

### When Feature is Enabled

```
┌─────────────────────────────────────────────┐
│  Cost Intelligence                          │
│                                             │
│  Enabled by account admin on 2026-01-02     │
│                                             │
│  [View Cost Report]  [Export]               │
└─────────────────────────────────────────────┘
```

---

## Audit Trail

When applicability changes, log:

```python
@dataclass
class ApplicabilityChange:
    timestamp: datetime
    account_id: str
    team_id: str
    resource: str
    previous_level: VisibilityLevel
    new_level: VisibilityLevel
    changed_by: str  # actor_id of admin
```

This provides audit trail **without** changing data access patterns.

---

## Success Criteria

- [ ] All gated resources check applicability at request time
- [ ] No historical data is mutated by applicability changes
- [ ] Export endpoints explicitly check export permission
- [ ] UI reflects backend truth, does not decide
- [ ] Audit trail records policy changes

---

## Related Documents

- `docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md` - Actor model
- `docs/governance/PERMISSION_TAXONOMY_V1.md` - Permission definitions
- `docs/memory-pins/PIN-271-rbac-authority-separation.md` - RBAC governance
- `docs/memory-pins/PIN-272-applicability-policy-governance.md` - This policy's PIN

---

## Invariant Lock

> **Applicability policies gate access at request time.**
> **They do not retroactively rewrite or partition historical data.**
> **Historical data becomes visible once enabled.**
> **UI reflects backend truth, does not decide.**
