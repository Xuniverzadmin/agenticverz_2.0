# OSD-L2.1 — Order Surface Definition

**Schema ID:** `OSD_L2_1`
**Version:** 1.0.0
**Status:** SCHEMA-FROZEN
**Created:** 2026-01-07
**Authority:** NONE

---

## 0. Canonical Source of Truth

> **This document is a rendered reference view.**
> The authoritative definition of L2.1 orders lives in:
> - `l2_1_order_definitions` (table)
>
> **If discrepancies exist, tables take precedence.**

### Document Restrictions

This document may not introduce:
- New orders (O1-O5 are frozen)
- Modified order shapes
- Authority semantics
- New epistemic depths

All such changes must be applied at table level first.

### Table Mapping

```
Source Table: l2_1_order_definitions
Schema Location: design/l2_1/schema/l2_1_order_definitions.schema.sql
Seed Location: design/l2_1/seeds/l2_1_order_definitions.seed.sql
Selection Criteria: ALL (O1-O5 complete set)
```

---

## 1. Definition

**Full Name:** Order Surface Definition — L2.1

**Purpose:**
Defines the **O1–O5 epistemic contracts** once, reused everywhere.

This is where:
- O1 snapshot shape
- O2 presence gates
- O3 explanation rules
- O4 context rules
- O5 proof terminal rules

are **frozen**.

---

## 2. Epistemic Order Model

### 2.1 Order Hierarchy

| Order | Name | Meaning | Invariant |
|-------|------|---------|-----------|
| **O1** | Snapshot | Summary, scannable, shallow, safe entry | Never expands inline |
| **O2** | Presence | List of instances | "Show me instances" |
| **O3** | Detail | Explanation of a single thing | "Explain this thing" |
| **O4** | Context | Impact and relationships | "What else did this affect?" |
| **O5** | Proof | Raw records, immutable truth | "Show me proof" — TERMINAL |

### 2.2 Order Properties

| Order | Depth | Expandable | Mutable | Authority |
|-------|-------|------------|---------|-----------|
| O1 | Shallow | No | No | NONE |
| O2 | List | Yes → O3 | No | NONE |
| O3 | Single | Yes → O4 | No | NONE |
| O4 | Relational | Yes → O5 | No | NONE |
| O5 | Terminal | No | **IMMUTABLE** | NONE |

---

## 3. Order Definitions

### 3.1 O1 — Snapshot

**Purpose:** Scannable, shallow, safe entry point.

```yaml
O1_snapshot:
  definition: "Summary view of current state"
  depth: shallow

  required_fields:
    - field: id
      type: string
      description: "Unique identifier"
    - field: status
      type: enum
      values: [healthy, degraded, critical, unknown]
      description: "Current status indicator"
    - field: label
      type: string
      description: "Human-readable name"
    - field: timestamp
      type: iso8601
      description: "Last updated time"

  optional_fields:
    - field: metric_value
      type: number
      description: "Primary metric if applicable"
    - field: trend
      type: enum
      values: [up, down, stable, unknown]
      description: "Trend indicator"

  hard_prohibitions:
    - No nested objects
    - No arrays longer than 5 items
    - No raw IDs without labels
    - No actions or buttons
    - No expandable content inline

  navigation:
    expandable: false
    links_to: O2  # Can navigate to O2, never inline expand
```

### 3.2 O2 — Presence

**Purpose:** List of instances answering "show me instances."

```yaml
O2_presence:
  definition: "List of instances within a domain/topic"
  depth: list

  required_fields:
    - field: items
      type: array
      description: "List of instance summaries"
      item_shape:
        - field: id
          type: string
        - field: label
          type: string
        - field: status
          type: enum
        - field: timestamp
          type: iso8601
    - field: total_count
      type: integer
      description: "Total items (for pagination)"
    - field: page
      type: integer
      description: "Current page"

  optional_fields:
    - field: filters_applied
      type: object
      description: "Active filter state"
    - field: sort_order
      type: string
      description: "Current sort"

  gates:
    - name: "minimum_presence"
      rule: "At least one item must exist to render O2"
      fallback: "Show empty state with guidance"
    - name: "scope_bound"
      rule: "Items must be within current tenant/project scope"
      fallback: "REJECT — never show cross-scope"

  hard_prohibitions:
    - No inline O3 expansion
    - No cross-tenant items
    - No items without valid scope
    - No actions that mutate

  navigation:
    expandable: true
    links_to: O3  # Each item can navigate to O3
```

### 3.3 O3 — Detail / Explanation

**Purpose:** Explain a single thing in depth.

```yaml
O3_explanation:
  definition: "Detailed view of a single instance"
  depth: single

  required_fields:
    - field: id
      type: string
      description: "Instance identifier"
    - field: label
      type: string
      description: "Human-readable name"
    - field: status
      type: enum
      description: "Current status"
    - field: created_at
      type: iso8601
      description: "Creation timestamp"
    - field: updated_at
      type: iso8601
      description: "Last update timestamp"
    - field: summary
      type: string
      description: "Brief explanation"

  optional_fields:
    - field: details
      type: object
      description: "Domain-specific detail fields"
    - field: metadata
      type: object
      description: "Additional metadata"
    - field: related_count
      type: integer
      description: "Count of related items (teaser for O4)"

  rules:
    - name: "single_instance"
      rule: "O3 always describes exactly one instance"
    - name: "no_inline_lists"
      rule: "Lists of related items shown as counts, not inline"
    - name: "explanation_not_action"
      rule: "O3 explains — it does not offer actions"

  hard_prohibitions:
    - No inline lists (use counts, navigate to O4)
    - No mutation actions
    - No cross-instance comparison
    - No speculative content

  navigation:
    expandable: true
    links_to: O4  # Can navigate to context
    links_to_proof: O5  # Can navigate to proof
```

### 3.4 O4 — Context / Impact

**Purpose:** Show relationships and impact.

```yaml
O4_context:
  definition: "Relational view showing impact and connections"
  depth: relational

  required_fields:
    - field: source_id
      type: string
      description: "The instance being contextualized"
    - field: source_label
      type: string
      description: "Human-readable source name"
    - field: relationships
      type: array
      description: "List of related entities"
      item_shape:
        - field: type
          type: string
          description: "Relationship type"
        - field: target_id
          type: string
        - field: target_label
          type: string
        - field: target_domain
          type: string

  optional_fields:
    - field: impact_summary
      type: string
      description: "Brief impact statement"
    - field: timeline
      type: array
      description: "Chronological events"
    - field: dependency_graph
      type: object
      description: "Structured dependency info"

  scope:
    - name: "bounded_context"
      rule: "Context is bounded to current tenant/project"
    - name: "relationship_limit"
      rule: "Maximum 50 relationships per view"
    - name: "no_recursive_context"
      rule: "Context does not nest (no O4 of O4)"

  hard_prohibitions:
    - No cross-tenant relationships
    - No speculative relationships
    - No inferred causation
    - No recursive context expansion

  navigation:
    expandable: true
    links_to: O5  # Can navigate to proof for any item
```

### 3.5 O5 — Proof (TERMINAL)

**Purpose:** Raw records, immutable truth. This is the terminal order.

```yaml
O5_proof:
  definition: "Raw, immutable records — the final source of truth"
  depth: terminal

  required_fields:
    - field: proof_id
      type: string
      description: "Unique proof identifier"
    - field: source_id
      type: string
      description: "What this proves"
    - field: proof_type
      type: enum
      values: [trace, audit_log, snapshot, hash, signature]
      description: "Type of proof"
    - field: timestamp
      type: iso8601
      description: "When proof was recorded"
    - field: content
      type: object
      description: "Raw proof content"
    - field: integrity_hash
      type: string
      description: "Hash for verification"

  optional_fields:
    - field: chain_ref
      type: string
      description: "Reference to proof chain"
    - field: verification_status
      type: enum
      values: [verified, unverified, failed]

  terminal_rules:
    - name: "immutable"
      rule: "O5 content is NEVER modified after creation"
      enforcement: "Database constraint + application check"
    - name: "no_expansion"
      rule: "O5 does not expand further — it is terminal"
    - name: "no_interpretation"
      rule: "O5 shows raw data, not interpreted summaries"
    - name: "replay_faithful"
      rule: "O5 must be identical on replay"

  hard_prohibitions:
    - NO modification after creation (ABSOLUTE)
    - NO interpretation or summarization
    - NO expansion beyond raw content
    - NO cross-reference that mutates
    - NO navigation deeper than O5

  navigation:
    expandable: false  # TERMINAL
    links_to: null     # Nothing — this is the end
```

---

## 4. Order Transition Rules

### 4.1 Valid Transitions

```
O1 → O2  (snapshot to list)
O2 → O3  (list to detail)
O3 → O4  (detail to context)
O3 → O5  (detail to proof)
O4 → O5  (context to proof)
```

### 4.2 Invalid Transitions

| Transition | Reason |
|------------|--------|
| O1 → O3 | Must go through O2 |
| O1 → O4 | Must go through O2, O3 |
| O1 → O5 | Must go through intermediate orders |
| O2 → O4 | Must go through O3 |
| O2 → O5 | Must go through O3 |
| O5 → anything | O5 is terminal |
| Any → O1 | O1 is entry only (can return via navigation) |

### 4.3 Sidebar Invariant

> **Sidebar never changes with order depth.**

Navigation through O1→O5 changes the **content pane** only.
The sidebar remains stable regardless of epistemic depth.

---

## 5. Validation Schema

```python
def validate_order_shape(order: str, data: dict) -> ValidationResult:
    """Validate data matches order contract."""
    schemas = {
        "O1": O1_SCHEMA,
        "O2": O2_SCHEMA,
        "O3": O3_SCHEMA,
        "O4": O4_SCHEMA,
        "O5": O5_SCHEMA,
    }

    if order not in schemas:
        return ValidationResult(valid=False, error="Unknown order")

    # Validate required fields
    # Validate no prohibited content
    # Validate navigation constraints

    return ValidationResult(valid=True)
```

---

## 6. Hard Prohibitions (All Orders)

| Prohibition | Applies To | Reason |
|-------------|------------|--------|
| Authority signals | All | L2.1 has no authority |
| Mutation actions | All | L2.1 is read-only |
| Cross-tenant data | All | Tenant isolation absolute |
| Speculative content | All | Only facts from Phase-2 |
| Inline expansion | O1 | O1 is shallow entry |
| Recursive depth | O4 | Context doesn't nest |
| Further navigation | O5 | O5 is terminal |

---

## 7. References

- `ESM_L2_1_TEMPLATE.md` — Uses this definition
- `DSM_L2_1.md` — Domains that have orders
- `L2_1_GOVERNANCE_ASSERTIONS.md` — Governance constraints

---

**STATUS:** SCHEMA-FROZEN — Order definitions are canonical.
