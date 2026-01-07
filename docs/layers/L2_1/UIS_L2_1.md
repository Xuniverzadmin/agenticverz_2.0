# UIS-L2.1 — UI Intent Surface

**Schema ID:** `UIS_L2_1`
**Version:** 1.0.0
**Status:** SKELETON (fields only)
**Created:** 2026-01-07
**Authority:** NONE

---

## 0. Canonical Source of Truth

> **This document is a rendered reference view.**
> The authoritative UI intent fields are stored in:
> - `l2_1_epistemic_surface.ui_intent` (table column)
>
> **If discrepancies exist, table constraints take precedence.**

### Document Restrictions

This document may not introduce:
- New visibility levels
- Action authorization
- Layout prescriptions
- Authority semantics

All such changes must be applied at schema level first.

---

## 1. Definition

**Full Name:** UI Intent Surface — L2.1

**Purpose:**
Describes **visibility, consent, irreversibility, and affordances** — not layout, not styling.

This is what L1 "skins".

**Critical Distinction:**
- **UIS-L2.1** declares **what the UI needs to know**
- **L1** decides **how it looks**

L2.1 says: "This action requires consent"
L1 decides: "Show a modal with a red button"

---

## 2. Core Fields (Skeleton)

### 2.1 Visibility

```yaml
visibility:
  type: enum
  required: true

  values:
    public:
      description: "Visible without authentication"
      example: "Public status page"

    authenticated:
      description: "Visible to any authenticated user in tenant"
      example: "Dashboard home"

    role_gated:
      description: "Visible only to users with specific role"
      requires: role_list
      example: "Admin settings"

    permission_gated:
      description: "Visible only with specific permission"
      requires: permission_list
      example: "Billing management"

  constraints:
    - "Visibility is declarative, not enforced by L2.1"
    - "L1 and auth layer enforce actual access"
    - "L2.1 declares intent for UI to consume"
```

### 2.2 Consent Required

```yaml
consent_required:
  type: boolean
  required: true
  default: false

  when_true:
    description: "User action has consequences that require explicit acknowledgment"
    examples:
      - "Deleting a resource"
      - "Disabling a policy"
      - "Approving a budget change"

    ui_hint: "Show confirmation before proceeding"

  when_false:
    description: "Action can proceed without explicit confirmation"
    examples:
      - "Viewing details"
      - "Navigating between pages"
      - "Filtering a list"

  constraints:
    - "Consent is about user awareness, not authorization"
    - "Authorization is handled separately by RBAC"
    - "L2.1 declares need, L1 implements dialog"
```

### 2.3 Irreversible

```yaml
irreversible:
  type: boolean
  required: true
  default: false

  when_true:
    description: "Action cannot be undone after execution"
    examples:
      - "Permanent deletion"
      - "Finalizing a report"
      - "Revoking access retroactively"

    ui_hint: "Strong warning, require explicit confirmation"

    combined_with_consent:
      - "If irreversible=true, consent_required SHOULD be true"
      - "Exception: Read-only irreversible views (viewing sealed audit)"

  when_false:
    description: "Action can be reversed or has no permanent effect"
    examples:
      - "Pausing a workflow"
      - "Updating a threshold"
      - "Adding a tag"

  constraints:
    - "Irreversibility is about data permanence"
    - "L2.1 declares permanence, not enforcement"
    - "Enforcement is L4/L5 responsibility"
```

### 2.4 Replay Available

```yaml
replay_available:
  type: boolean
  required: true
  default: false

  when_true:
    description: "This surface can be replayed from historical data"
    examples:
      - "Execution trace view"
      - "Audit log detail"
      - "Historical incident report"

    implies:
      - "Data is immutable"
      - "Surface is deterministic"
      - "IPC-L2.1 replay invariant holds"

    ui_hint: "Can show 'Replay' or 'View as of' affordance"

  when_false:
    description: "This surface shows current state only"
    examples:
      - "Live dashboard"
      - "Active runs list"
      - "Current policies"

  constraints:
    - "Replay availability is a capability declaration"
    - "Actual replay is Phase-2 / L4 responsibility"
    - "L2.1 declares availability for UI to surface"
```

---

## 3. Affordance Hints

Affordances are **capability hints** for L1, not layout instructions.

```yaml
affordances:
  expandable:
    type: boolean
    default: false
    description: "Can this surface expand to show more detail?"
    ui_hint: "Show expand icon/chevron"

  filterable:
    type: boolean
    default: false
    description: "Can this surface be filtered?"
    ui_hint: "Show filter controls"
    requires: filter_fields  # List of filterable fields

  sortable:
    type: boolean
    default: false
    description: "Can this surface be sorted?"
    ui_hint: "Show sort controls"
    requires: sort_fields  # List of sortable fields

  exportable:
    type: boolean
    default: false
    description: "Can this surface be exported?"
    ui_hint: "Show export button"
    formats: []  # csv, json, pdf

  linkable:
    type: boolean
    default: false
    description: "Can items link to other surfaces?"
    ui_hint: "Render items as links"
    link_target: ""  # Target surface type

  searchable:
    type: boolean
    default: false
    description: "Can this surface be searched?"
    ui_hint: "Show search input"
    search_fields: []  # Fields included in search

  paginated:
    type: boolean
    default: false
    description: "Is this surface paginated?"
    ui_hint: "Show pagination controls"
    page_size_options: [10, 20, 50, 100]
```

---

## 4. Action Intent (Non-Authoritative)

L2.1 can declare **what actions are conceptually available** without granting authority.

```yaml
action_intent:
  description: "Actions that may be available on this surface"
  authority: NONE  # L2.1 never authorizes

  available_actions:
    type: array
    items:
      action_id:
        type: string
        description: "Unique action identifier"

      action_type:
        type: enum
        values:
          - navigate      # Move to another surface
          - filter        # Apply filter
          - sort          # Change sort order
          - export        # Export data
          - refresh       # Reload data
          # Note: No mutating actions in L2.1

      label:
        type: string
        description: "Human-readable action name"

      visibility:
        type: enum
        values: [always, conditional, role_gated]

      enabled_when:
        type: string
        description: "Condition for action availability"

  forbidden_action_types:
    - create        # L2.1 cannot create
    - update        # L2.1 cannot update
    - delete        # L2.1 cannot delete
    - approve       # L2.1 cannot approve
    - execute       # L2.1 cannot execute
```

---

## 5. Composite Surface Definition

For surfaces that combine multiple ESM instances:

```yaml
composite:
  is_composite:
    type: boolean
    default: false

  components:
    type: array
    items:
      esm_ref:
        type: string
        description: "Reference to ESM-L2.1 surface"

      position:
        type: enum
        values: [primary, secondary, sidebar, footer]
        description: "Logical position (not layout)"

      visibility_override:
        type: object
        description: "Override visibility for this component"

  layout_hint:
    type: enum
    values:
      - stack         # Vertical stack
      - grid          # Grid layout
      - split         # Side-by-side
      - tabbed        # Tab container
    description: "Hint for L1, not prescription"
```

---

## 6. Full Schema (Skeleton)

```yaml
# UIS-L2.1 Schema Skeleton
uis_l2_1:
  schema_id: "UIS_L2_1"
  version: "1.0.0"

  # Core fields
  visibility: enum [public, authenticated, role_gated, permission_gated]
  consent_required: boolean
  irreversible: boolean
  replay_available: boolean

  # Affordances
  affordances:
    expandable: boolean
    filterable: boolean
    sortable: boolean
    exportable: boolean
    linkable: boolean
    searchable: boolean
    paginated: boolean

  # Action intent (non-authoritative)
  action_intent:
    available_actions: array
    forbidden_action_types: [create, update, delete, approve, execute]

  # Composite surfaces
  composite:
    is_composite: boolean
    components: array
    layout_hint: enum

  # Metadata
  metadata:
    created_at: iso8601
    updated_at: iso8601
    surface_version: string
```

---

## 7. L1 Consumption Contract

### 7.1 What L1 Receives

```yaml
l1_receives:
  - visibility: "To render/hide appropriately"
  - consent_required: "To show confirmation UI"
  - irreversible: "To show warning severity"
  - replay_available: "To show replay affordance"
  - affordances: "To render appropriate controls"
  - action_intent: "To render action buttons/links"
```

### 7.2 What L1 Decides

```yaml
l1_decides:
  - Layout (grid, flex, positioning)
  - Styling (colors, typography, spacing)
  - Animation (transitions, loading states)
  - Responsive behavior (breakpoints)
  - Interaction patterns (click, hover, drag)
  - Accessibility implementation (ARIA, keyboard)
```

### 7.3 What L1 Cannot Do

```yaml
l1_cannot:
  - Override visibility (only enforce)
  - Skip consent when required
  - Grant authority L2.1 doesn't have
  - Add actions not in action_intent
  - Modify ESM data
```

---

## 8. Validation Rules

```python
def validate_uis_l2_1(surface: dict) -> ValidationResult:
    """Validate UIS-L2.1 compliance."""

    errors = []

    # Required fields
    required = ["visibility", "consent_required", "irreversible", "replay_available"]
    for field in required:
        if field not in surface:
            errors.append(f"Missing required field: {field}")

    # Visibility enum
    valid_visibility = ["public", "authenticated", "role_gated", "permission_gated"]
    if surface.get("visibility") not in valid_visibility:
        errors.append(f"Invalid visibility: {surface.get('visibility')}")

    # Irreversible + consent check
    if surface.get("irreversible") and not surface.get("consent_required"):
        errors.append("Warning: irreversible=true but consent_required=false")

    # No mutating actions
    if "action_intent" in surface:
        forbidden = ["create", "update", "delete", "approve", "execute"]
        for action in surface["action_intent"].get("available_actions", []):
            if action.get("action_type") in forbidden:
                errors.append(f"Forbidden action type: {action.get('action_type')}")

    return ValidationResult(
        valid=len([e for e in errors if not e.startswith("Warning")]) == 0,
        errors=errors
    )
```

---

## 9. References

- `ESM_L2_1_TEMPLATE.md` — Includes UIS reference
- `DSM_L2_1.md` — Domain definitions
- `L2_1_GOVERNANCE_ASSERTIONS.md` — Governance constraints

---

**STATUS:** SKELETON — Fields only, no sample data.
