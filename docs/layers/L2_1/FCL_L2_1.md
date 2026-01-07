# FCL-L2.1 — Facilitation Classification Layer

**Schema ID:** `FCL_L2_1`
**Version:** 1.0.0
**Status:** FROZEN
**Created:** 2026-01-07
**Authority:** NONE

---

## 0. Canonical Source of Truth

> **This document is a rendered reference view.**
> The authoritative facilitation rules are stored in:
> - `l2_1_epistemic_surface.facilitation` (table column)
>
> **If discrepancies exist, table constraints take precedence.**

### Document Restrictions

This document may not introduce:
- Authoritative signals
- Blocking warnings
- Auto-apply recommendations
- Authority semantics

All such changes must be applied at schema level first.

---

## 1. Definition

**Full Name:** Facilitation Classification Layer — L2.1

**Purpose:**
Explicitly labels **non-authoritative** signals:
- Recommendations
- Warnings
- Confidence bands

**Critical Rule:**
> Every output here must be stamped: `authority = NONE`

---

## 2. Core Principle

L2.1 can **facilitate** user understanding without **authorizing** actions.

| Concept | L2.1 Can | L2.1 Cannot |
|---------|----------|-------------|
| Recommendations | Show as suggestions | Enforce or auto-apply |
| Warnings | Display alerts | Block actions |
| Confidence | Show uncertainty | Make decisions based on it |
| Guidance | Provide context | Mandate behavior |

---

## 3. Signal Types

### 3.1 Recommendations

```yaml
recommendations:
  definition: "Non-authoritative suggestions for user consideration"
  authority: NONE

  schema:
    type: array
    items:
      recommendation_id:
        type: string
        description: "Unique identifier"

      category:
        type: enum
        values:
          - optimization     # "Consider X for better performance"
          - best_practice    # "Best practice suggests Y"
          - cost_saving      # "This could reduce cost by Z"
          - risk_mitigation  # "Consider addressing this risk"

      message:
        type: string
        description: "Human-readable recommendation"

      confidence:
        type: number
        range: [0.0, 1.0]
        description: "Confidence in recommendation (display only)"

      source:
        type: string
        description: "Where this recommendation comes from"

      # MANDATORY METADATA
      metadata:
        authoritative: false  # ALWAYS false
        actionable: false     # L2.1 cannot make actionable
        auto_apply: false     # NEVER auto-apply

  constraints:
    - "Recommendations are DISPLAY ONLY"
    - "User must explicitly choose to act"
    - "No default acceptance"
    - "No enforcement mechanism"
```

### 3.2 Warnings

```yaml
warnings:
  definition: "Non-authoritative alerts about potential issues"
  authority: NONE

  schema:
    type: array
    items:
      warning_id:
        type: string
        description: "Unique identifier"

      severity:
        type: enum
        values:
          - info       # Informational, no action needed
          - low        # Minor issue, consider reviewing
          - medium     # Notable issue, should review
          - high       # Significant issue, recommend action
          - critical   # Severe issue, strongly recommend action
        description: "Severity level (advisory only)"

      category:
        type: enum
        values:
          - budget          # Budget-related warning
          - rate_limit      # Rate limit approaching
          - policy          # Policy-related concern
          - health          # System health issue
          - security        # Security consideration
          - compliance      # Compliance note

      message:
        type: string
        description: "Human-readable warning message"

      context:
        type: object
        description: "Additional context for the warning"

      # MANDATORY METADATA
      metadata:
        authoritative: false  # ALWAYS false
        blocking: false       # L2.1 warnings NEVER block
        auto_resolve: false   # NEVER auto-resolve

  constraints:
    - "Warnings are ADVISORY ONLY"
    - "Cannot block user actions"
    - "Cannot auto-resolve"
    - "Cannot trigger automated responses"
```

### 3.3 Confidence Bands

```yaml
confidence_bands:
  definition: "Display-only confidence information"
  authority: NONE

  schema:
    overall:
      type: number
      range: [0.0, 1.0]
      description: "Overall confidence score"

    by_dimension:
      type: object
      description: "Confidence by specific dimension"
      properties:
        data_quality:
          type: number
          description: "Confidence in underlying data"
        completeness:
          type: number
          description: "Data completeness confidence"
        freshness:
          type: number
          description: "Data freshness confidence"
        accuracy:
          type: number
          description: "Accuracy confidence"

    uncertainty_factors:
      type: array
      items:
        factor:
          type: string
        impact:
          type: enum
          values: [low, medium, high]
        description:
          type: string

    # MANDATORY METADATA
    metadata:
      authoritative: false      # ALWAYS false
      decision_input: false     # MUST NOT be used for decisions
      mutable: false            # Read-only from Phase-2

  constraints:
    - "Confidence is DISPLAY ONLY"
    - "Cannot be used for automated decisions"
    - "Must come from Phase-2 (no L2.1 computation)"
    - "Read-only, never modified by L2.1"
```

---

## 4. Signal Metadata (MANDATORY)

Every facilitation signal MUST include:

```yaml
signal_metadata:
  # These values are FIXED and IMMUTABLE in L2.1
  authoritative: false    # L2.1 has no authority
  actionable: false       # L2.1 cannot make things actionable
  mutable: false          # L2.1 cannot mutate state
  blocking: false         # L2.1 cannot block
  auto_apply: false       # L2.1 cannot auto-apply
  enforcement: "NONE"     # L2.1 has no enforcement capability

  # Provenance (required for traceability)
  provenance:
    source_layer: "L2_1"
    ir_hash: ""           # Phase-2 interpreter result hash
    timestamp: ""         # When signal was generated
```

---

## 5. Forbidden Facilitation Patterns

| Pattern | Example | Why Forbidden |
|---------|---------|---------------|
| **Authoritative warning** | "This action is blocked" | L2.1 cannot block |
| **Auto-applied recommendation** | Default-on optimization | L2.1 cannot apply |
| **Decision-driving confidence** | "Low confidence, action denied" | L2.1 cannot decide |
| **Enforced severity** | Critical = must fix | L2.1 cannot enforce |
| **Computed confidence** | L2.1-calculated score | Must come from Phase-2 |
| **State-mutating signal** | Warning that updates status | L2.1 cannot mutate |

---

## 6. UI Presentation Hints

L2.1 can provide hints for how signals should be presented, without dictating layout:

```yaml
presentation_hints:
  # For recommendations
  recommendations:
    display_style: "suggestion"    # Not "command"
    dismissible: true              # User can dismiss
    persistence: "session"         # Don't persist across sessions

  # For warnings
  warnings:
    severity_indicator: true       # Show severity visually
    dismissible_below: "high"      # Can dismiss low/medium
    critical_highlight: true       # Highlight critical

  # For confidence
  confidence:
    show_band: true                # Show confidence band
    show_factors: false            # Hide uncertainty factors by default
    precision: 2                   # Decimal places
```

---

## 7. Integration with ESM-L2.1

FCL-L2.1 is referenced in ESM-L2.1 under the `facilitation` field:

```yaml
# In ESM-L2.1
facilitation:
  authority: NONE
  recommendations: []       # FCL recommendations
  warnings: []              # FCL warnings
  confidence_bands: {}      # FCL confidence
  signal_metadata:          # FCL metadata
    authoritative: false
    actionable: false
    mutable: false
```

---

## 8. Validation Rules

```python
def validate_fcl_signal(signal: dict) -> ValidationResult:
    """Validate FCL-L2.1 signal compliance."""

    errors = []

    # Check mandatory metadata
    metadata = signal.get("metadata", signal.get("signal_metadata", {}))

    if metadata.get("authoritative", True):
        errors.append("authoritative must be false")

    if metadata.get("actionable", True):
        errors.append("actionable must be false")

    if metadata.get("blocking", True):
        errors.append("blocking must be false")

    if metadata.get("auto_apply", True):
        errors.append("auto_apply must be false")

    # Check for forbidden patterns
    message = signal.get("message", "").lower()
    if "blocked" in message or "denied" in message:
        errors.append("Warning: message suggests authority L2.1 doesn't have")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors
    )
```

---

## 9. References

- `ESM_L2_1_TEMPLATE.md` — Uses FCL for facilitation
- `L2_1_GOVERNANCE_ASSERTIONS.md` — GA-001 (No Authority), GA-009 (Non-Auth Signals)
- `IPC_L2_1.md` — Confidence comes from Phase-2 projection

---

**STATUS:** FROZEN — Facilitation rules are canonical.
