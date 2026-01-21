# SDSR Attribution Invariant Clause

**Status:** RATIFIED
**Effective:** 2026-01-18
**Clause ID:** SDSR-ATTRIBUTION-INVARIANT-001
**Authority:** Control-Plane Law — Non-Negotiable

---

## Clause Text (Authoritative)

> **A capability SHALL NOT declare a dimension unless the underlying data plane schema projects that dimension as a first-class, non-derived field.**

---

## Governing Principle

> **Claim ≠ Truth unless enforced by schema.**

Capabilities are promises.
Schemas are proofs.

The system is only as honest as the weakest attribution invariant.

---

## Binding Implications

### Capability Declaration Rules

If a capability declares:

```yaml
dimensions:
  - agent_id
  - actor_type
  - provider_type
```

Then **each declared dimension** MUST exist in:

| Location | Requirement |
|----------|-------------|
| Base table (`runs`) | Column exists, correct type |
| Analytical views (`v_runs_o2`) | Column projected |
| Query paths | Column queryable without transformation |

**Absence is a schema violation, not a runtime bug.**

---

## Forbidden States

The following are **explicitly illegal**:

| State | Why Forbidden |
|-------|---------------|
| Declaring "By Agent" without `agent_id` in views | Capability promises what schema cannot deliver |
| Returning empty results due to missing schema | Silent failure masquerading as data absence |
| Masking schema gaps with UI suppression | Hiding truth from operators |
| "Planned but not yet projected" dimensions | Claims must be backed at declaration time |

---

## Enforcement Points

This clause is enforced at:

| Phase | Enforcement |
|-------|-------------|
| SDSR review | Scenario must validate dimension exists |
| Capability registration | Dimension must map to schema column |
| View migration approval | View must project all declared dimensions |
| Panel binding | Panel cannot bind to unbackable capability |

### Violation Response

```
SDSR-ATTRIBUTION-INVARIANT-001 VIOLATION

Capability: {capability_id}
Declared dimension: {dimension_name}
Schema location: {table_or_view}
Column status: MISSING / NOT PROJECTED

Action: Capability declaration INVALID
Panel binding: BLOCKED

Reference: docs/contracts/SDSR_ATTRIBUTION_INVARIANT.md
```

---

## Dimension-to-Schema Mapping (Required)

For `activity.runs_by_dimension`, the following mappings MUST be satisfied:

| Dimension | Base Table Column | View Column | Status |
|-----------|-------------------|-------------|--------|
| `provider_type` | `runs.provider_type` | `v_runs_o2.provider_type` | Required |
| `source` | `runs.source` | `v_runs_o2.source` | Required |
| `agent_id` | `runs.agent_id` | `v_runs_o2.agent_id` | Required |
| `risk_level` | `runs.risk_level` | `v_runs_o2.risk_level` | Required |
| `status` | `runs.status` | `v_runs_o2.status` | Required |
| `actor_type` | `runs.actor_type` | `v_runs_o2.actor_type` | Required |

If any column is missing from the view, the dimension MUST be removed from the capability declaration until the schema is corrected.

---

## View Contract

### v_runs_o2 Required Columns

The `v_runs_o2` view MUST project all attribution fields:

```sql
CREATE OR REPLACE VIEW v_runs_o2 AS
SELECT
  id,
  tenant_id,
  agent_id,          -- REQUIRED: attribution
  actor_type,        -- REQUIRED: attribution
  actor_id,          -- REQUIRED: attribution (nullable)
  source,            -- REQUIRED: attribution
  provider_type,
  status,
  state,
  risk_level,
  -- ... other fields
FROM runs;
```

### View Migration Rule

Any migration that:
- Removes a projected column
- Renames an attribution field
- Changes attribution field nullability

**MUST be approved through governance review.**

---

## System Outcome

After this clause is enforced:

| Guarantee | Result |
|-----------|--------|
| LIVE-O5 "By Agent" | Provably correct |
| Attribution ambiguity | Eliminated |
| Cost/risk/signals | Gain ownership context |
| Control-plane integrity | Restored |
| This failure class | Cannot reoccur |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | Ingress enforcement |
| `RUN_VALIDATION_RULES.md` | Structural completeness |
| `CAPABILITY_SURFACE_RULES.md` | Topic-scoped endpoint governance |
| `INTENT_LEDGER.md` | Capability declarations |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial ratification | Governance |
