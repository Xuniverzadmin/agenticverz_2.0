# ESM-L2.1 — Epistemic Surface Matrix Template

**Schema ID:** `ESM_L2_1`
**Version:** 1.0.0
**Status:** TEMPLATE (structure only, no sample data)
**Created:** 2026-01-07
**Authority:** NONE (facilitation only)

---

## 0. Canonical Source of Truth

> **This document is a rendered reference view.**
> The authoritative definition of L2.1 surfaces lives in:
> - `l2_1_epistemic_surface` (table)
> - `l2_1_domain_registry` (table)
> - `l2_1_order_definitions` (table)
>
> **If discrepancies exist, tables take precedence.**

### Document Restrictions

This document may not introduce:
- New domains
- New topics
- New orders
- Authority semantics

All such changes must be applied at table level first.

### Table Mapping

```
Source Table: l2_1_epistemic_surface
Schema Location: design/l2_1/schema/l2_1_epistemic_surface.schema.sql
Seed Location: design/l2_1/seeds/
```

---

## 1. Definition

**Full Name:** Epistemic Surface Matrix — L2.1

**Purpose:**
A deterministic, headless schema describing **what can be shown**, **at what epistemic depth**, under **which L1 domain**, with **zero authority**.

**What ESM-L2.1 IS:**
- A projection contract for Phase-2 semantic truth
- A headless, order-aware surface definition
- A UI-safe structure for L1 consumption
- A read-only, deterministic manifest

**What ESM-L2.1 is NOT:**
- UI (that's L1)
- API response (that's L2)
- Decision model (that's L4)
- Execution plan (that's L5)
- Learning system (forbidden at this layer)

---

## 2. Template Structure

### 2.1 Surface Identity

```yaml
surface_id: "esm_{domain}_{subdomain}_{topic}_{version}"
schema_version: "1.0.0"
layer: "L2_1"
authority: NONE  # IMMUTABLE — never changes
```

### 2.2 Domain Binding (from DSM-L2.1)

```yaml
domain:
  id: ""                    # Required: Overview | Activity | Incidents | Policies | Logs
  name: ""                  # Human-readable name
  l1_constitution_ref: ""   # Reference to L1 Constitution section

subdomain:
  id: ""                    # Optional: domain-specific subdivision
  name: ""                  # Human-readable name

topic:
  id: ""                    # Required: specific topic within subdomain
  name: ""                  # Human-readable name
  question: ""              # The question this topic answers
```

### 2.3 Epistemic Order Slots (from OSD-L2.1)

```yaml
orders:
  O1_snapshot:
    enabled: true | false
    shape: {}               # Reference OSD-L2.1 for exact shape
    required_fields: []
    optional_fields: []

  O2_presence:
    enabled: true | false
    shape: {}
    gates: []               # Conditions for presence

  O3_explanation:
    enabled: true | false
    shape: {}
    rules: []               # Explanation generation rules

  O4_context:
    enabled: true | false
    shape: {}
    scope: ""               # What context is included

  O5_proof:
    enabled: true | false
    shape: {}
    terminal: true          # Always terminal — no further depth
    immutable: true         # Proof cannot be modified
```

### 2.4 Interpreter Projection (from IPC-L2.1)

```yaml
projection:
  ir_hash: ""               # Interpreter result hash (read-only)
  fact_snapshot_id: ""      # Phase-2 fact snapshot reference
  evaluation_mode: ""       # strict | advisory
  confidence_vector: {}     # Read-only confidence data
  enrichment_allowed: false # ALWAYS false in L2.1
```

### 2.5 Facilitation Signals (from FCL-L2.1)

```yaml
facilitation:
  authority: NONE           # IMMUTABLE
  recommendations: []       # Non-authoritative suggestions
  warnings: []              # Non-authoritative alerts
  confidence_bands: {}      # Display-only confidence

  # Every signal MUST carry this stamp:
  signal_metadata:
    authoritative: false
    actionable: false       # L2.1 cannot trigger actions
    mutable: false          # L2.1 cannot mutate state
```

### 2.6 UI Intent (from UIS-L2.1)

```yaml
ui_intent:
  visibility: ""            # public | authenticated | role_gated
  consent_required: false   # true if user action has consequences
  irreversible: false       # true if action cannot be undone
  replay_available: false   # true if replay is supported

  # Affordance hints (not layout)
  affordances:
    expandable: false
    filterable: false
    exportable: false
    linkable: false
```

### 2.7 Scope Constraints

```yaml
scope:
  tenant_isolation: true    # ALWAYS true — no cross-tenant
  project_bound: true       # Typically true for Customer Console
  jurisdiction: ""          # customer | founder | ops

  # Hard constraints
  constraints:
    cross_tenant_aggregation: false  # FORBIDDEN
    cross_project_aggregation: false # FORBIDDEN in Customer Console
    authority_delegation: false      # FORBIDDEN in L2.1
```

---

## 3. Validation Rules

### 3.1 Schema Validation

| Field | Constraint | Violation Response |
|-------|------------|-------------------|
| `authority` | MUST be `NONE` | REJECT |
| `enrichment_allowed` | MUST be `false` | REJECT |
| `tenant_isolation` | MUST be `true` | REJECT |
| `signal_metadata.authoritative` | MUST be `false` | REJECT |
| `domain.id` | MUST exist in DSM-L2.1 | REJECT |

### 3.2 Relationship Validation

| Relationship | Constraint |
|--------------|------------|
| Domain → L1 Constitution | Must be subset |
| Orders → OSD-L2.1 | Must match frozen definitions |
| Projection → IPC-L2.1 | Must reference valid contract |

---

## 4. Instance Template

When creating an ESM-L2.1 instance, copy this template:

```yaml
# ESM-L2.1 Instance: {domain}/{subdomain}/{topic}
# Generated: {timestamp}
# Author: {author}

surface_id: "esm_{domain}_{subdomain}_{topic}_v1"
schema_version: "1.0.0"
layer: "L2_1"
authority: NONE

domain:
  id: ""
  name: ""
  l1_constitution_ref: ""

subdomain:
  id: ""
  name: ""

topic:
  id: ""
  name: ""
  question: ""

orders:
  O1_snapshot:
    enabled: false
    shape: {}
    required_fields: []
    optional_fields: []
  O2_presence:
    enabled: false
    shape: {}
    gates: []
  O3_explanation:
    enabled: false
    shape: {}
    rules: []
  O4_context:
    enabled: false
    shape: {}
    scope: ""
  O5_proof:
    enabled: false
    shape: {}
    terminal: true
    immutable: true

projection:
  ir_hash: ""
  fact_snapshot_id: ""
  evaluation_mode: "strict"
  confidence_vector: {}
  enrichment_allowed: false

facilitation:
  authority: NONE
  recommendations: []
  warnings: []
  confidence_bands: {}
  signal_metadata:
    authoritative: false
    actionable: false
    mutable: false

ui_intent:
  visibility: "authenticated"
  consent_required: false
  irreversible: false
  replay_available: false
  affordances:
    expandable: false
    filterable: false
    exportable: false
    linkable: false

scope:
  tenant_isolation: true
  project_bound: true
  jurisdiction: "customer"
  constraints:
    cross_tenant_aggregation: false
    cross_project_aggregation: false
    authority_delegation: false
```

---

## 5. Relationship to Other L2.1 Schemas

```
Phase 2 Interpreter
        |
        v
IPC-L2.1 (projection contract)
        |
        v
ESM-L2.1 (THIS SCHEMA - epistemic surface)
        |
        +---> FCL-L2.1 (facilitation classification)
        +---> UIS-L2.1 (UI intent surface)
        +---> GC_L proposals (governance)
        |
        v
L1 UI (skin only)
```

**Direction Rule:** No arrows may be reversed.

---

## 6. References

- `DSM_L2_1.md` — Domain Surface Manifest
- `OSD_L2_1.md` — Order Surface Definition
- `IPC_L2_1.md` — Interpreter Projection Contract
- `FCL_L2_1.md` — Facilitation Classification Layer
- `UIS_L2_1.md` — UI Intent Surface
- `L2_1_GOVERNANCE_ASSERTIONS.md` — Governance constraints

---

**STATUS:** TEMPLATE — No sample data. Structure only.
