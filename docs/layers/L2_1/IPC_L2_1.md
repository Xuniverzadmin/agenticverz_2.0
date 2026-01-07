# IPC-L2.1 — Interpreter Projection Contract

**Schema ID:** `IPC_L2_1`
**Version:** 1.0.0
**Status:** FROZEN
**Created:** 2026-01-07
**Authority:** NONE

---

## 0. Canonical Source of Truth

> **This document is a rendered reference view.**
> The authoritative projection rules are enforced via:
> - `l2_1_epistemic_surface.projection` (table column)
> - Application-level IPC validation
>
> **If discrepancies exist, table constraints take precedence.**

### Document Restrictions

This document may not introduce:
- New projection fields
- Enrichment allowances
- Authority semantics
- Bypass mechanisms

All such changes must be applied at schema level first.

---

## 1. Definition

**Full Name:** Interpreter Projection Contract — L2.1

**Purpose:**
Defines **exactly how Phase-2 outputs are referenced**, never reinterpreted.

L2.1 **projects** Phase-2 truth — it does not:
- Reinterpret
- Enrich
- Transform
- Infer

---

## 2. Core Principle

> **Phase-2 is the source of truth. L2.1 is a lens, not a filter.**

L2.1 can:
- **Reference** Phase-2 outputs
- **Select** which outputs to show
- **Order** outputs for presentation
- **Format** outputs for display

L2.1 cannot:
- **Modify** Phase-2 outputs
- **Enrich** with derived data
- **Infer** missing data
- **Aggregate** across Phase-2 boundaries

---

## 3. Projection Fields

### 3.1 Required Fields

Every L2.1 surface that references Phase-2 MUST include:

```yaml
projection:
  # Interpreter Result Hash — immutable reference
  ir_hash:
    type: string
    format: "sha256"
    description: "Hash of the Phase-2 interpreter result being projected"
    mutable: false
    required: true

  # Fact Snapshot ID — point-in-time reference
  fact_snapshot_id:
    type: string
    format: "uuid"
    description: "ID of the Phase-2 fact snapshot"
    mutable: false
    required: true

  # Evaluation Mode — how Phase-2 was evaluated
  evaluation_mode:
    type: enum
    values:
      - strict      # All assertions verified
      - advisory    # Best-effort, some assertions skipped
      - replay      # Replay mode, read-only
    description: "Mode under which Phase-2 evaluation occurred"
    required: true

  # Confidence Vector — read-only confidence data
  confidence_vector:
    type: object
    description: "Phase-2 confidence metrics"
    mutable: false
    required: false
    shape:
      overall: number  # 0.0 - 1.0
      by_assertion: object  # assertion_id -> confidence

  # Enrichment Flag — ALWAYS false
  enrichment_allowed:
    type: boolean
    value: false
    mutable: false
    required: true
    description: "L2.1 NEVER enriches Phase-2 data"
```

### 3.2 Optional Reference Fields

```yaml
projection_metadata:
  # Projection timestamp
  projected_at:
    type: iso8601
    description: "When this projection was created"

  # Projection version
  projection_version:
    type: string
    description: "Version of projection contract used"

  # Source system
  source_system:
    type: string
    description: "Which Phase-2 component produced this"

  # Staleness indicator
  staleness_seconds:
    type: integer
    description: "Seconds since Phase-2 snapshot"
```

---

## 4. Forbidden Enrichments

The following are **explicitly forbidden** in L2.1 projections:

| Enrichment Type | Example | Reason |
|-----------------|---------|--------|
| **Derived metrics** | "Average response time" computed from raw | Computation is Phase-2's job |
| **Inferred status** | "Probably degraded" from partial data | Inference is forbidden |
| **Cross-run aggregation** | "Total failures this week" | Aggregation crosses Phase-2 boundaries |
| **Time-series smoothing** | Moving averages | Transformation not allowed |
| **Null imputation** | Filling missing values | Inference is forbidden |
| **Label enrichment** | Adding descriptions not in Phase-2 | Must come from Phase-2 |
| **Relationship inference** | "Likely caused by X" | Causation must be Phase-2 fact |

### 4.1 Violation Response

If enrichment is detected:

```yaml
violation:
  type: IPC_ENRICHMENT_VIOLATION
  severity: BLOCKING
  response: REJECT
  message: "L2.1 cannot enrich Phase-2 data"
  remediation: "Move computation to Phase-2 interpreter"
```

---

## 5. Allowed Operations

The following operations ARE allowed:

| Operation | Example | Constraint |
|-----------|---------|------------|
| **Selection** | Show only error runs | Selection criteria must be explicit |
| **Ordering** | Sort by timestamp | Order must be deterministic |
| **Formatting** | ISO8601 → human date | Format is reversible |
| **Filtering** | Hide resolved incidents | Filter state is visible |
| **Pagination** | Show 20 items | Page state is explicit |
| **Localization** | Translate labels | Original label preserved |

### 5.1 Selection Contract

```yaml
selection:
  criteria:
    type: array
    items:
      field: string
      operator: enum [eq, ne, gt, lt, gte, lte, in, not_in]
      value: any

  constraints:
    - "Criteria must reference Phase-2 fields only"
    - "No computed criteria"
    - "No cross-entity criteria"
```

### 5.2 Ordering Contract

```yaml
ordering:
  fields:
    type: array
    items:
      field: string
      direction: enum [asc, desc]

  constraints:
    - "Fields must exist in Phase-2 output"
    - "Order must be deterministic (tie-breaker required)"
    - "No computed sort keys"
```

---

## 6. Replay Invariant

**Critical Rule:**

> **L2.1 projections MUST be identical on replay.**

Given:
- Same `ir_hash`
- Same `fact_snapshot_id`
- Same selection/ordering criteria

The resulting L2.1 surface MUST be byte-identical.

### 6.1 Replay Verification

```python
def verify_replay_invariant(
    projection_1: Projection,
    projection_2: Projection
) -> bool:
    """Verify two projections of same source are identical."""

    # Same source
    assert projection_1.ir_hash == projection_2.ir_hash
    assert projection_1.fact_snapshot_id == projection_2.fact_snapshot_id

    # Same criteria
    assert projection_1.selection == projection_2.selection
    assert projection_1.ordering == projection_2.ordering

    # Must produce identical output
    return projection_1.output == projection_2.output
```

### 6.2 Replay Mode Behavior

When `evaluation_mode: replay`:

```yaml
replay_constraints:
  emit_new_data: false
  modify_existing: false
  side_effects: false
  audit_trail: read_only

  allowed:
    - Read Phase-2 snapshot
    - Project to L2.1 surface
    - Verify against stored projection

  forbidden:
    - Create new Phase-2 data
    - Modify projection output
    - Trigger downstream systems
```

---

## 7. Projection Lifecycle

```
Phase-2 Evaluation
        |
        v
IR (Interpreter Result) Created
        |
        v
IR Hash Computed (immutable)
        |
        v
Fact Snapshot Stored
        |
        v
L2.1 Projection Request
        |
        v
IPC-L2.1 Validation
        |
        +---> PASS: Create Projection
        |           |
        |           v
        |     Selection/Ordering Applied
        |           |
        |           v
        |     ESM-L2.1 Surface Generated
        |
        +---> FAIL: Reject with violation
```

---

## 8. Integration Points

### 8.1 Phase-2 → L2.1

```yaml
phase_2_interface:
  input:
    - ir_hash: "Interpreter result to project"
    - fact_snapshot_id: "Snapshot to use"

  output:
    - projection: "IPC-L2.1 compliant projection"

  contract:
    - "Phase-2 is authoritative"
    - "L2.1 is read-only consumer"
    - "No back-channel to Phase-2"
```

### 8.2 L2.1 → L1

```yaml
l1_interface:
  input:
    - esm_surface: "ESM-L2.1 compliant surface"

  output:
    - ui_render: "Visual representation"

  contract:
    - "L1 adds skin only"
    - "L1 cannot modify ESM content"
    - "L1 can add visual affordances"
```

---

## 9. Validation Rules

### 9.1 Projection Validation

```python
def validate_projection(projection: dict) -> ValidationResult:
    """Validate IPC-L2.1 compliance."""

    errors = []

    # Required fields
    if "ir_hash" not in projection:
        errors.append("Missing ir_hash")
    if "fact_snapshot_id" not in projection:
        errors.append("Missing fact_snapshot_id")
    if "evaluation_mode" not in projection:
        errors.append("Missing evaluation_mode")

    # Enrichment check
    if projection.get("enrichment_allowed", False):
        errors.append("enrichment_allowed must be false")

    # Confidence vector immutability
    if "confidence_vector" in projection:
        if projection["confidence_vector"].get("mutable", True):
            errors.append("confidence_vector must be immutable")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors
    )
```

### 9.2 Enrichment Detection

```python
def detect_enrichment(
    phase_2_output: dict,
    l2_1_projection: dict
) -> list[EnrichmentViolation]:
    """Detect if L2.1 added data not in Phase-2."""

    violations = []

    # Check for fields not in Phase-2
    for field in l2_1_projection.get("data", {}):
        if field not in phase_2_output:
            violations.append(EnrichmentViolation(
                field=field,
                type="ADDED_FIELD",
                message=f"Field '{field}' not in Phase-2 output"
            ))

    # Check for modified values
    for field, value in l2_1_projection.get("data", {}).items():
        if field in phase_2_output:
            if value != phase_2_output[field]:
                # Allow formatting changes
                if not is_format_only_change(phase_2_output[field], value):
                    violations.append(EnrichmentViolation(
                        field=field,
                        type="MODIFIED_VALUE",
                        message=f"Field '{field}' value differs from Phase-2"
                    ))

    return violations
```

---

## 10. References

- `ESM_L2_1_TEMPLATE.md` — Uses projection contract
- `OSD_L2_1.md` — Order definitions
- `L2_1_GOVERNANCE_ASSERTIONS.md` — Governance constraints
- Phase-2 Interpreter Documentation (external)

---

**STATUS:** FROZEN — Projection rules are canonical.
