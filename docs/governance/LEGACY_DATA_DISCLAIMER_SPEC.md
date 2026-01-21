# Legacy Data Disclaimer Specification

**Status:** RATIFIED
**Effective:** 2026-01-18
**Purpose:** How to surface legacy-unknown data without lying
**Reference:** ATTRIBUTION_MIGRATION_CHECKLIST.md

---

## Purpose

Legacy data **will exist** after attribution enforcement. This specification defines how to handle, display, and disclaim that data **without introducing ambiguity or false confidence**.

---

## Core Principle

> **Absence of attribution is not absence of data.**
> Legacy data must be **explicit, visible, and disclaimed** — never hidden or merged.

---

## 1. Canonical Legacy Markers

### Standard Values

| Field | Legacy Value | Meaning |
|-------|--------------|---------|
| `agent_id` | `legacy-unknown` | Agent not captured at creation time |
| `actor_type` | `SYSTEM` | Assumed non-human (conservative) |
| `actor_id` | `NULL` | No human identity available |
| `origin_system_id` | `legacy-migration` | Backfilled by migration script |

### Properties

These values are:
- **Explicit** — Not NULL, not empty string
- **Searchable** — Can filter by `agent_id = 'legacy-unknown'`
- **Countable** — Can aggregate legacy bucket size
- **Non-ambiguous** — Clearly distinguishable from real values

---

## 2. Backfill SQL (Reference)

```sql
-- Phase 1 backfill for historical runs
UPDATE runs
SET
  agent_id = 'legacy-unknown',
  actor_type = 'SYSTEM',
  actor_id = NULL,
  origin_system_id = 'legacy-migration'
WHERE agent_id IS NULL
   OR agent_id = '';

-- Record backfill timestamp
INSERT INTO migration_audit (
  migration_id,
  table_name,
  rows_affected,
  executed_at,
  description
) VALUES (
  'ATTRIBUTION-BACKFILL-001',
  'runs',
  (SELECT COUNT(*) FROM runs WHERE agent_id = 'legacy-unknown'),
  NOW(),
  'Attribution enforcement backfill - legacy runs marked'
);
```

---

## 3. UI Rendering Rules

### Panel Display (LIVE-O5, COMPLETED-O5)

| Value | Display Label | Visual Treatment |
|-------|---------------|------------------|
| Known agent | Agent name/ID | Normal |
| `legacy-unknown` | "Legacy (pre-attribution)" | Warning indicator |

### Required Tooltip (Mandatory)

When hovering over legacy bucket:

> **"Runs created before attribution enforcement."**
> "Not representative of current system behavior. These runs were created before agent tracking was mandatory."

### Visual Indicator

- Use warning icon (⚠️) or muted styling
- Never use error styling (not an error, just legacy)
- Must be distinguishable at a glance

---

## 4. Analytics Rules

### Aggregation Behavior

| Rule | Requirement |
|------|-------------|
| Legacy bucket visibility | ALWAYS visible in breakdowns |
| Merge with "Other" | FORBIDDEN |
| Hide from totals | FORBIDDEN |
| Rename to something else | FORBIDDEN |

### Chart Display

```
By Agent Distribution:

agent-policy-executor    ████████████ 45%
agent-user-assistant     ██████████   38%
legacy-unknown ⚠️        ████         12%
agent-cron-worker        ██            5%
```

Legacy bucket must appear in sorted position (typically by count).

---

## 5. Query Patterns

### Include Legacy

```sql
-- All runs including legacy
SELECT agent_id, COUNT(*)
FROM v_runs_o2
WHERE tenant_id = :tenant_id
GROUP BY agent_id;
```

### Exclude Legacy (Analytics)

```sql
-- Only attributed runs (post-enforcement)
SELECT agent_id, COUNT(*)
FROM v_runs_o2
WHERE tenant_id = :tenant_id
  AND agent_id != 'legacy-unknown'
GROUP BY agent_id;
```

### Legacy-Only (Audit)

```sql
-- Count legacy runs (should decrease over time)
SELECT COUNT(*)
FROM v_runs_o2
WHERE agent_id = 'legacy-unknown';
```

---

## 6. Time-Based Sunset

### Enforcement Date (T₀)

After attribution enforcement is deployed (T₀):

| Condition | Expected | Action if Violated |
|-----------|----------|-------------------|
| New runs with `agent_id = 'legacy-unknown'` | 0 | INCIDENT |
| New runs with missing `agent_id` | 0 | SDK REJECTION |
| Legacy bucket growth | 0 | INVESTIGATION |

### Monitoring Query

```sql
-- Alert if legacy bucket grows after T₀
SELECT COUNT(*) as new_legacy_runs
FROM runs
WHERE agent_id = 'legacy-unknown'
  AND created_at > :enforcement_date;

-- Expected: 0
-- If > 0: Enforcement failure, trigger incident
```

---

## 7. API Response Handling

### Dimension Breakdown Response

```json
{
  "dimension": "agent_id",
  "groups": [
    {
      "value": "agent-policy-executor",
      "count": 450,
      "percentage": 45.0,
      "is_legacy": false
    },
    {
      "value": "legacy-unknown",
      "count": 120,
      "percentage": 12.0,
      "is_legacy": true,
      "disclaimer": "Runs created before attribution enforcement"
    }
  ],
  "total_runs": 1000,
  "legacy_count": 120,
  "state_filter": "COMPLETED"
}
```

### Response Schema Addition

```yaml
DimensionGroup:
  properties:
    value:
      type: string
    count:
      type: integer
    percentage:
      type: number
    is_legacy:
      type: boolean
      default: false
    disclaimer:
      type: string
      nullable: true
```

---

## 8. Documentation Requirements

### User-Facing Documentation

Include in help/docs:

> **What is "Legacy (pre-attribution)"?**
>
> Runs created before [DATE] were not required to specify which agent executed them. These runs are marked as "legacy-unknown" in reports and analytics.
>
> This does not indicate an error — it simply means attribution tracking was not yet enforced when these runs were created.
>
> **Will legacy runs ever be fixed?**
>
> No. Historical attribution cannot be retroactively determined. Legacy runs will always show as "legacy-unknown".
>
> **Are new runs affected?**
>
> No. All runs created after [DATE] are required to have full attribution (agent, actor type, origin system).

---

## 9. Compliance & Audit

### Audit Log Entry

When backfill runs:

```json
{
  "event_type": "MIGRATION_BACKFILL",
  "migration_id": "ATTRIBUTION-BACKFILL-001",
  "table": "runs",
  "rows_affected": 15423,
  "timestamp": "2026-01-18T12:00:00Z",
  "description": "Backfilled legacy runs with explicit unknown markers",
  "reversible": false
}
```

### Compliance Statement

> "Historical runs created before attribution enforcement have been marked with explicit 'legacy-unknown' values. This preserves data integrity while clearly distinguishing unattributed historical data from fully attributed current data."

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `ATTRIBUTION_MIGRATION_CHECKLIST.md` | Rollout phases |
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | Enforcement rules |
| `ATTRIBUTION_FAILURE_MODE_MATRIX.md` | What breaks if violated |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
