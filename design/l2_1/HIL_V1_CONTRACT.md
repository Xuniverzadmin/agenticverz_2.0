# Human Interpretation Layer (HIL) v1 Contract

**Status:** ACTIVE
**Version:** 1.0.0
**Created:** 2026-01-14
**Scope:** UI panel classification and provenance tracking
**Reference:** AURORA_L2.md, PIN-352 (SUPERSEDED), PIN-370

---

## 1. Purpose

The Human Interpretation Layer (HIL) provides a **narrative layer over execution truth**
without altering that truth. It enables humans to understand what happened by adding
summaries, insights, and aggregations while maintaining full traceability to source data.

**Core Principle:**

> Interpretation panels must never invent information. They transform, summarize, or
> aggregate execution data with explicit provenance.

---

## 2. Panel Classification (panel_class)

All panels are classified into exactly one of two classes:

| Panel Class | Purpose | Examples |
|-------------|---------|----------|
| `execution` | Raw facts, lists, details | Run List, Incident Details, Trace Steps |
| `interpretation` | Summaries, insights, aggregations | Activity Summary, Incident Trends, Health Pulse |

### 2.1 Classification Rules

| Rule | Enforcement |
|------|-------------|
| Every panel MUST have a `panel_class` | BLOCKING |
| Default for migrated panels is `execution` | AUTOMATIC |
| `interpretation` panels MUST declare `provenance` | BLOCKING |
| `execution` panels MUST NOT declare `provenance` | BLOCKING |

### 2.2 Classification Criteria

**Execution Panels (panel_class: execution):**
- Display raw data from single backend endpoint
- Support filtering, sorting, pagination
- No aggregation or transformation
- 1:1 mapping between UI rows and database records

**Interpretation Panels (panel_class: interpretation):**
- Aggregate data from one or more execution sources
- Provide summaries, counts, trends, or insights
- Backend-computed (no frontend math)
- Explicit provenance declaration required

---

## 3. Provenance Declaration

Interpretation panels MUST declare their data provenance:

```yaml
provenance:
  source_panels:
    - ACT-EX-CR-O2        # Completed Runs List
    - ACT-EX-AR-O2        # Active Runs List
  aggregation: COUNT      # How sources are combined
  endpoint: /api/v1/activity/summary  # Dedicated backend endpoint
```

### 3.1 Provenance Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_panels` | array[string] | YES | Panel IDs this interpretation derives from |
| `aggregation` | enum | YES | Aggregation type (see 3.2) |
| `endpoint` | string | YES | Dedicated backend endpoint for aggregated data |

### 3.2 Aggregation Types (Closed Enum)

| Aggregation | Description | Example |
|-------------|-------------|---------|
| `COUNT` | Simple count of records | "12 runs today" |
| `SUM` | Sum of numeric field | "Total cost: $45.00" |
| `TREND` | Time-series comparison | "Up 15% from yesterday" |
| `STATUS_BREAKDOWN` | Grouped counts by status | "5 success, 2 failed, 1 running" |
| `TOP_N` | Ranked subset | "Top 3 failing agents" |
| `LATEST` | Most recent N items | "Last 5 incidents" |

### 3.3 Provenance Invariant

> **No interpretation panel may display data that cannot be traced to source execution panels.**

If an interpretation panel shows "12 runs today", the user must be able to navigate to
the source execution panel (e.g., `ACT-EX-CR-O2`) and find exactly 12 matching records.

---

## 4. Domain Intent (Documentation-Level)

Each domain has a **domain_intent** that answers the core question the domain exists to answer.
This is documentation-level metadata, not per-panel configuration.

### 4.1 Frozen Domain Intents

| Domain | Domain Intent | Core Question |
|--------|---------------|---------------|
| **Overview** | system_health | Is the system okay right now? |
| **Activity** | execution_visibility | What ran / is running? |
| **Incidents** | failure_understanding | What went wrong? |
| **Policies** | behavior_governance | How is behavior defined? |
| **Logs** | evidence_trail | What is the raw truth? |

### 4.2 Domain Intent Registry

```yaml
# design/l2_1/AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml

domains:
  Overview:
    intent: system_health
    question: "Is the system okay right now?"
    primary_object: Health

  Activity:
    intent: execution_visibility
    question: "What ran / is running?"
    primary_object: Run

  Incidents:
    intent: failure_understanding
    question: "What went wrong?"
    primary_object: Incident

  Policies:
    intent: behavior_governance
    question: "How is behavior defined?"
    primary_object: Policy

  Logs:
    intent: evidence_trail
    question: "What is the raw truth?"
    primary_object: Trace
```

---

## 5. Schema Extension

The intent YAML schema is extended with these fields:

```yaml
# HIL v1 Schema Extension

panel_class:
  type: string
  enum: [execution, interpretation]
  default: execution
  description: "Classification of panel behavior"

provenance:
  type: object
  required_if: panel_class == interpretation
  properties:
    source_panels:
      type: array
      items:
        type: string
        pattern: "^[A-Z]{2,4}-[A-Z]{2}-[A-Z]{2,3}-O[1-5]$"
      minItems: 1
      description: "Panel IDs this interpretation derives from"
    aggregation:
      type: string
      enum: [COUNT, SUM, TREND, STATUS_BREAKDOWN, TOP_N, LATEST]
      description: "How source data is aggregated"
    endpoint:
      type: string
      pattern: "^/api/v1/"
      description: "Backend endpoint for aggregated data"
```

---

## 6. Example: Activity Summary Panel (Interpretation)

```yaml
# design/l2_1/intents/ACT-EX-SUM-O1.yaml
# This is an INTERPRETATION panel

panel_id: ACT-EX-SUM-O1
version: 1.0.0
panel_class: interpretation    # <-- HIL field

metadata:
  domain: Activity
  subdomain: EXECUTIONS
  topic: EXECUTION_SUMMARY
  topic_id: ACTIVITY.EXECUTIONS.EXECUTION_SUMMARY
  order: O1
  action_layer: L2_1
  migration_status: REVIEWED

display:
  name: Activity Summary
  visible_by_default: true
  nav_required: false
  expansion_mode: INLINE

provenance:                    # <-- HIL field (required for interpretation)
  source_panels:
    - ACT-EX-AR-O2             # Active Runs List
    - ACT-EX-CR-O2             # Completed Runs List
  aggregation: STATUS_BREAKDOWN
  endpoint: /api/v1/activity/summary

data:
  read: true
  download: false
  write: false
  replay: false

controls:
  filtering: false
  activate: false
  confirmation_required: false

notes: "HIL v1 interpretation panel - aggregates run status"
```

---

## 7. Example: Completed Runs List (Execution)

```yaml
# design/l2_1/intents/ACT-EX-CR-O2.yaml
# This is an EXECUTION panel

panel_id: ACT-EX-CR-O2
version: 1.0.0
panel_class: execution         # <-- HIL field (explicit, though default)

metadata:
  domain: Activity
  subdomain: EXECUTIONS
  topic: COMPLETED_RUNS
  topic_id: ACTIVITY.EXECUTIONS.COMPLETED_RUNS
  order: O2
  action_layer: L2_1
  migration_status: UNREVIEWED

display:
  name: Completed Runs List
  visible_by_default: true
  nav_required: false
  expansion_mode: INLINE

# No provenance field - execution panels don't aggregate

data:
  read: true
  download: true
  write: false
  replay: true

controls:
  filtering: true
  selection_mode: SINGLE
  activate: false
  confirmation_required: false
  control_set: [FILTER, SORT, SELECT_SINGLE, DOWNLOAD, NAVIGATE]

notes: "List of completed runs"
```

---

## 8. Backend Contract

### 8.1 Interpretation Endpoint Requirements

Every interpretation panel requires a dedicated backend endpoint that:

1. Returns pre-computed aggregations (no frontend math)
2. Accepts same filters as source execution panels
3. Returns provenance metadata in response

**Response Schema:**

```json
{
  "data": {
    "total_runs": 12,
    "by_status": {
      "success": 8,
      "failed": 3,
      "running": 1
    }
  },
  "provenance": {
    "source_panels": ["ACT-EX-AR-O2", "ACT-EX-CR-O2"],
    "aggregation": "STATUS_BREAKDOWN",
    "computed_at": "2026-01-14T10:30:00Z"
  }
}
```

### 8.2 Frontend Rendering Rules

| Rule | Enforcement |
|------|-------------|
| Frontend MUST NOT compute aggregations | BLOCKING |
| Frontend MUST display provenance link | REQUIRED |
| Clicking provenance navigates to source panel | REQUIRED |

---

## 9. Execution Plan

### Phase 1: Schema Extension (Current)
- [x] Document panel_class and provenance schema
- [ ] Update intent_spec_schema.json with HIL fields
- [ ] Create AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml

### Phase 2: Runtime Support
- [ ] Compiler propagates panel_class to projection
- [ ] Frontend groups panels by class
- [ ] Add provenance badge to interpretation panels

### Phase 3: First Implementation (Activity Domain)
- [ ] Create ACT-EX-SUM-O1 interpretation panel
- [ ] Create /api/v1/activity/summary endpoint
- [ ] Wire frontend renderer

### Phase 4: Expand
- [ ] Add interpretation panels to other domains
- [ ] Evaluate and refine based on usage

---

## 10. Governance Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| HIL-001 | All panels must have panel_class | BLOCKING |
| HIL-002 | Interpretation panels must have provenance | BLOCKING |
| HIL-003 | Execution panels must not have provenance | BLOCKING |
| HIL-004 | Provenance must reference valid panel IDs | BLOCKING |
| HIL-005 | No frontend aggregation | BLOCKING |
| HIL-006 | Interpretation endpoints must return provenance metadata | REQUIRED |

---

## 11. Anti-Patterns (Forbidden)

| Anti-Pattern | Why Forbidden |
|--------------|---------------|
| Frontend summing counts | Violates backend-owned aggregation |
| Interpretation without provenance | Untraceable data |
| Execution panel claiming aggregation | Misclassification |
| Provenance pointing to non-existent panels | Broken audit trail |
| Hardcoded summary text | Must derive from real data |

---

## 12. Related Documents

- `design/l2_1/AURORA_L2.md` — Pipeline architecture
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md` — Domain definitions
- `backend/aurora_l2/schema/intent_spec_schema.json` — JSON Schema
- PIN-370 — SDSR System Contract
- PIN-352 (SUPERSEDED) — Legacy L2.1 Pipeline

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-14 | Initial HIL v1 Contract created |
