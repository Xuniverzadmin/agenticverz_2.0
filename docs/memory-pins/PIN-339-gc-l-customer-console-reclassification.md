# PIN-339: Customer Console Capability Reclassification (GC-L)

**Status:** APPROVED
**Date:** 2026-01-06
**Approved:** 2026-01-06
**Reference:** PIN-337, PIN-338
**Scope:** Customer Console ONLY
**Authority:** Human-approved

---

## Approval Record

**Approval Status:** ✅ GRANTED
**Approval Date:** 2026-01-06

**Binding Notes:**
1. GC_L is now the canonical customer control power class
2. Learning is permitted; enforcement without human action remains forbidden
3. Policy Library is mandatory before any learned policy surfaces
4. FACILITATION must never mutate state
5. Founder console remains unchanged and out of scope

**Authorized Actions:**
- Constitution update
- Authority declaration updates
- L2 ↔ L2.1 binding updates
- UI and API implementation under GC_L constraints

---

## Executive Summary

This PIN proposes reclassifying Customer Console capabilities from READ-only (OBSERVE_OWN) to **Governed Control with Learning (GC_L)**, enabling customers to configure their own platform within safe, pre-approved boundaries.

### Key Changes

| Change | From | To |
|--------|------|-----|
| Power Type | READ only | READ + GC_L |
| Customer Authority | Observe only | Configure within bounds |
| Policy Control | Founder-escalated | Customer-selectable from Policy Library |
| System Role | Passive | FACILITATION (advisory guidance) |

---

## Deliverable 1: Reclassification Table

### Summary

| CAP ID | Name | Current Power | Proposed Power | Change Type |
|--------|------|---------------|----------------|-------------|
| CAP-001 | Execution Replay & Activity | READ | READ | None |
| CAP-002 | Cost Simulation V2 | READ | **GC_L** | UPGRADE |
| CAP-003 | Policy Proposals | READ | **GC_L** | UPGRADE |
| CAP-004 | C2 Prediction Plane | READ | **GC_L** (limited) | UPGRADE |
| CAP-009 | M19 Policy Engine | READ | **GC_L** | UPGRADE (Core) |
| CAP-014 | M7 Memory System | READ | **GC_L** (limited) | UPGRADE |
| CAP-018 | M25 Integration Platform | READ | **GC_L** | UPGRADE |

### Detailed Reclassifications

#### CAP-002: Cost Simulation V2 → GC_L

**Rationale:** Customers should set their own cost budgets and alert thresholds.

| Attribute | Value |
|-----------|-------|
| GC_L Scope | Budget limits, alert thresholds, cost alert rules |
| New Routes | `POST /cost/budgets/apply`, `PUT /cost/alerts/configure` |
| Policy Library | PLT-COST-001 to PLT-COST-004 |
| Risk Level | MEDIUM |

#### CAP-003: Policy Proposals → GC_L

**Rationale:** Customers should respond to proposals affecting their resources.

| Attribute | Value |
|-----------|-------|
| GC_L Scope | Accept/reject proposals for own resources |
| New Routes | `POST /api/v1/policy-proposals/{id}/accept`, `POST /api/v1/policy-proposals/{id}/reject` |
| Policy Library | PLT-PROP-001 to PLT-PROP-003 |
| Risk Level | LOW |

**Note:** Creating new proposals remains FORBIDDEN.

#### CAP-004: C2 Prediction Plane → GC_L (limited)

**Rationale:** Low-risk preference tuning for advisory predictions.

| Attribute | Value |
|-----------|-------|
| GC_L Scope | Prediction preference tuning |
| New Routes | `PUT /api/v1/predictions/preferences` |
| Policy Library | PLT-PRED-001 to PLT-PRED-003 |
| Risk Level | LOW |

#### CAP-009: M19 Policy Engine → GC_L (Core)

**Rationale:** Core capability for customer self-governance. Customers select policies from Policy Library.

| Attribute | Value |
|-----------|-------|
| GC_L Scope | Select and apply policies from Policy Library |
| New Routes | `POST /api/v1/policies/apply`, `DELETE /api/v1/policies/{id}/binding` |
| Policy Library | Core Policy Library (all categories) |
| Risk Level | HIGH |

**Note:** Creating arbitrary policies remains FORBIDDEN.

#### CAP-014: M7 Memory System → GC_L (limited)

**Rationale:** Customer-controlled data lifecycle for their own memory.

| Attribute | Value |
|-----------|-------|
| GC_L Scope | Retention policy configuration |
| New Routes | `PUT /api/v1/memory/retention-policy` |
| Policy Library | PLT-MEM-001 to PLT-MEM-003 |
| Risk Level | MEDIUM |

#### CAP-018: M25 Integration Platform → GC_L

**Rationale:** Customers configure their own integrations and webhooks.

| Attribute | Value |
|-----------|-------|
| GC_L Scope | Configure integrations, manage approved webhooks |
| New Routes | `POST /api/v1/integration/configure`, `PUT /api/v1/integration/webhooks/{id}` |
| Policy Library | PLT-INT-001 to PLT-INT-003 |
| Risk Level | HIGH |

**Note:** Webhook endpoint creation still requires founder approval.

---

## Deliverable 2: Power Model Addendum

### New Power Type: GC_L (Governed Control with Learning)

```yaml
power_type: GC_L
full_name: "Governed Control with Learning"
version: "1.0.0"
effective_date: "TBD (requires approval)"

definition:
  purpose: "Enable customers to configure their own platform within safe boundaries"
  grants: [read, configure, limited_write]
  scope: tenant
  cross_tenant: false

constraints:
  - "All configuration must use Policy Library templates"
  - "Parameter values must stay within template-defined bounds"
  - "Conflicting configurations are rejected at application time"
  - "All changes are audited with customer attribution"

does_not_allow:
  - "Creating arbitrary policies from scratch"
  - "Modifying Policy Library templates"
  - "Cross-tenant configuration"
  - "Bypassing parameter bounds"

authority_hierarchy:
  position: 2
  below: [INVOKE_OWN, MUTATE_OWN, ADMIN]
  above: [OBSERVE_OWN]
  diagram: "OBSERVE_OWN < GC_L < INVOKE_OWN < MUTATE_OWN < ADMIN"

learning_component:
  description: "System learns from customer selections for recommendations"
  scope: "Recommendation only - never enforcement"
  data_usage: "Aggregate patterns across tenant for personalization"
  opt_out: "Customer may opt out of learning"
```

### New Power Type: FACILITATION

```yaml
power_type: FACILITATION
full_name: "System Facilitation"
version: "1.0.0"
effective_date: "TBD (requires approval)"

definition:
  purpose: "System advisory that guides customers toward safe choices"
  grants: [recommend, validate, upgrade]
  scope: system
  cross_tenant: false

capabilities:
  recommend:
    description: "Suggest Policy Library entries based on patterns"
    binding: "Non-binding - customer decides"
  validate:
    description: "Check configuration for conflicts and risks"
    binding: "Blocking for security-critical only"
  upgrade:
    description: "Offer safer alternatives for risky choices"
    binding: "Non-binding - customer decides"

does_not_allow:
  - "Blocking customer choices (except security-critical)"
  - "Auto-applying changes"
  - "Overriding customer decisions"
  - "Using learned authority for enforcement"

relationship_to_gc_l:
  - "FACILITATION supports GC_L by providing guidance"
  - "GC_L without FACILITATION = customer chooses freely within bounds"
  - "GC_L with FACILITATION = system guides customer choices"
```

---

## Deliverable 3: Constitution Delta

### Proposed Amendment to CUSTOMER_CONSOLE_V1_CONSTITUTION.md

**Section to Add:** After Section 6.3 (Data Integrity)

```markdown
### 6.4 Governed Control (GC_L)

Customers may exercise governed control over their own platform configuration subject to:

1. **Policy Library Constraint** — All configuration must use pre-approved Policy Library templates
2. **Parameter Bounds** — Template parameters have enforced minimum/maximum bounds
3. **Conflict Prevention** — System prevents application of conflicting policies
4. **Audit Trail** — All configuration changes are logged with attribution

**GC_L does NOT allow:**
- Creating arbitrary policies from scratch
- Modifying templates or bounds
- Cross-tenant configuration
- Automatic enforcement without customer action

### 6.5 System Facilitation

The system may provide advisory guidance to help customers make safe choices:

1. **Recommendations** — Suggest Policy Library entries based on observed patterns
2. **Warnings** — Alert customers to potentially risky configurations
3. **Alternatives** — Offer safer options when risky choices are made

**FACILITATION does NOT:**
- Block customer choices (except security-critical violations)
- Auto-apply changes
- Override customer decisions
- Use learned authority for enforcement
```

**Version Increment:** 1.2.0 → 1.3.0

---

## Deliverable 4: Risk Register

### Risk Summary

| Risk ID | Risk | Probability | Impact | Mitigation | Residual Risk |
|---------|------|-------------|--------|------------|---------------|
| GCL-R01 | Customer sets budget too high | MEDIUM | HIGH | Template bounds + FACILITATION warnings | LOW |
| GCL-R02 | Customer accepts bad policy proposal | LOW | MEDIUM | Proposal quality gates + FACILITATION review | LOW |
| GCL-R03 | Customer selects conflicting policies | MEDIUM | HIGH | Conflict detection at application time | LOW |
| GCL-R04 | Customer sets aggressive retention | LOW | HIGH | Minimum retention bounds (7 days) | LOW |
| GCL-R05 | Customer misconfigures integration | MEDIUM | HIGH | HTTPS required, security templates | MEDIUM |
| GCL-R06 | Learning data misuse | LOW | MEDIUM | Aggregate-only, opt-out available | LOW |

### Detailed Risk Analysis

#### GCL-R01: Customer Sets Budget Too High

| Attribute | Value |
|-----------|-------|
| Description | Customer selects a budget limit that causes cost overruns |
| Probability | MEDIUM - Customers may not understand cost implications |
| Impact | HIGH - Financial exposure for customer |
| Mitigation | PLT-COST-* templates enforce upper bounds; FACILITATION warns on high limits |
| Residual | LOW - Bounds cap maximum exposure |

#### GCL-R03: Customer Selects Conflicting Policies

| Attribute | Value |
|-----------|-------|
| Description | Customer applies policies that conflict with each other |
| Probability | MEDIUM - Complex policy interactions |
| Impact | HIGH - System behavior becomes unpredictable |
| Mitigation | Policy Library validates conflicts; application rejected if conflict detected |
| Residual | LOW - Conflict detection is mandatory |

#### GCL-R05: Customer Misconfigures Integration

| Attribute | Value |
|-----------|-------|
| Description | Customer configures webhook or integration that exposes data |
| Probability | MEDIUM - Integration configuration is complex |
| Impact | HIGH - Data exposure risk |
| Mitigation | HTTPS required; security templates enforce best practices |
| Residual | MEDIUM - Cannot prevent all integration misuse |
| Additional Control | Webhook endpoint creation requires founder approval |

---

## Policy Library Schema

### Full Schema Definition

```yaml
# Policy Library Entry Schema v1.0.0
policy_library_entry:
  # Identification
  id: "PLT-{category}-{number}"        # e.g., PLT-COST-001
  name: string                          # Human-readable name
  description: string                   # Detailed description
  category: enum                        # cost | proposal | prediction | policy | memory | integration
  version: semver                       # e.g., 1.0.0
  status: enum                          # DRAFT | APPROVED | DEPRECATED

  # Applicability
  applicability:
    console_scope: CUSTOMER             # Always CUSTOMER for GC_L
    authority_required: GC_L            # Always GC_L
    capability_binding: string          # CAP-XXX that this template applies to
    project_scoped: boolean             # true = per-project, false = per-tenant

  # Parameters
  parameters:
    - name: string                      # Parameter name (snake_case)
      type: enum                        # number | string | boolean | enum | duration
      required: boolean                 # Is this parameter required?
      default: value                    # Default value if not specified
      bounds:                           # Constraints
        min: value                      # Minimum (for number, duration)
        max: value                      # Maximum (for number, duration)
        enum_values: [values]           # Allowed values (for enum)
        pattern: regex                  # Pattern (for string)

  # Conflict Management
  conflicts_with: [PLT-IDs]             # Templates that conflict
  requires: [PLT-IDs]                   # Templates that must be applied first

  # FACILITATION Guidance
  facilitation:
    recommended_for: [scenarios]        # When to recommend this template
    warnings: [conditions]              # When to warn the customer
    alternatives: [{condition, PLT-ID}] # Safer alternatives when risky

  # Audit
  created: ISO8601                      # Creation date
  created_by: string                    # Author
  approved_by: string                   # Approver (human)
  approval_date: ISO8601                # Approval date
```

### Core Policy Library Entries

#### Cost Management (CAP-002)

```yaml
- id: PLT-COST-001
  name: "Daily Budget Limit"
  category: cost
  capability_binding: CAP-002
  parameters:
    - name: daily_limit_usd
      type: number
      bounds: {min: 0.01, max: 10000}
      default: 100

- id: PLT-COST-002
  name: "Monthly Budget Cap"
  category: cost
  capability_binding: CAP-002
  parameters:
    - name: monthly_cap_usd
      type: number
      bounds: {min: 1, max: 100000}
      default: 1000

- id: PLT-COST-003
  name: "Alert Threshold"
  category: cost
  capability_binding: CAP-002
  parameters:
    - name: threshold_percent
      type: number
      bounds: {min: 50, max: 100}
      default: 80

- id: PLT-COST-004
  name: "Cost Per Run Limit"
  category: cost
  capability_binding: CAP-002
  parameters:
    - name: max_per_run_usd
      type: number
      bounds: {min: 0.001, max: 100}
      default: 1
```

#### Policy Application (CAP-009)

```yaml
- id: PLT-POL-001
  name: "Rate Limit"
  category: policy
  capability_binding: CAP-009
  parameters:
    - name: requests_per_minute
      type: number
      bounds: {min: 1, max: 1000}
      default: 60

- id: PLT-POL-002
  name: "Execution Timeout"
  category: policy
  capability_binding: CAP-009
  parameters:
    - name: timeout_seconds
      type: number
      bounds: {min: 1, max: 3600}
      default: 30

- id: PLT-POL-003
  name: "Retry Policy"
  category: policy
  capability_binding: CAP-009
  parameters:
    - name: max_retries
      type: number
      bounds: {min: 0, max: 10}
      default: 3
    - name: backoff_type
      type: enum
      bounds: {enum_values: [linear, exponential]}
      default: exponential

- id: PLT-POL-004
  name: "Resource Constraint"
  category: policy
  capability_binding: CAP-009
  parameters:
    - name: max_memory_mb
      type: number
      bounds: {min: 128, max: 4096}
      default: 512
    - name: max_cpu_percent
      type: number
      bounds: {min: 10, max: 100}
      default: 50
```

#### Memory Lifecycle (CAP-014)

```yaml
- id: PLT-MEM-001
  name: "Retention Period"
  category: memory
  capability_binding: CAP-014
  parameters:
    - name: days
      type: number
      bounds: {min: 7, max: 365}
      default: 30
  facilitation:
    warnings:
      - condition: "days < 14"
        message: "Short retention may cause data loss. Minimum recommended: 14 days"

- id: PLT-MEM-002
  name: "Cleanup Schedule"
  category: memory
  capability_binding: CAP-014
  parameters:
    - name: cron_expression
      type: string
      bounds: {pattern: "^[0-9*,/-]+ [0-9*,/-]+ [0-9*,/-]+ [0-9*,/-]+ [0-9*,/-]+$"}
      default: "0 2 * * *"

- id: PLT-MEM-003
  name: "Archive Threshold"
  category: memory
  capability_binding: CAP-014
  parameters:
    - name: age_days
      type: number
      bounds: {min: 30, max: 365}
      default: 90
```

#### Integration Config (CAP-018)

```yaml
- id: PLT-INT-001
  name: "Webhook Security"
  category: integration
  capability_binding: CAP-018
  parameters:
    - name: require_https
      type: boolean
      default: true
    - name: require_signature
      type: boolean
      default: true
  facilitation:
    warnings:
      - condition: "require_https == false"
        message: "HTTPS is required for production integrations"
        severity: BLOCKING

- id: PLT-INT-002
  name: "Retry Config"
  category: integration
  capability_binding: CAP-018
  parameters:
    - name: max_retries
      type: number
      bounds: {min: 0, max: 10}
      default: 3
    - name: timeout_ms
      type: number
      bounds: {min: 1000, max: 30000}
      default: 5000

- id: PLT-INT-003
  name: "Rate Limit"
  category: integration
  capability_binding: CAP-018
  parameters:
    - name: max_per_minute
      type: number
      bounds: {min: 1, max: 1000}
      default: 60
```

---

## FACILITATION Rules

```yaml
facilitation_rules:

  # Cost warnings
  - id: FAC-COST-001
    when: "customer selects PLT-COST-001 with daily_limit > 1000"
    action: recommend
    message: "High daily budget. Consider adding PLT-COST-003 (Alert Threshold) to monitor spend."
    severity: RECOMMENDATION

  # Memory warnings
  - id: FAC-MEM-001
    when: "customer selects PLT-MEM-001 with days < 14"
    action: warn
    message: "Short retention may cause data loss. Minimum recommended: 14 days."
    severity: WARNING

  # Security enforcement
  - id: FAC-INT-001
    when: "customer selects PLT-INT-001 with require_https = false"
    action: block
    message: "HTTPS is required for production integrations."
    severity: BLOCKING

  # Conflict resolution
  - id: FAC-POL-001
    when: "customer applies PLT-POL-001 that conflicts with existing policy"
    action: suggest
    message: "Policy conflict detected. Remove conflicting policy or adjust parameters."
    alternatives: ["adjust_existing", "remove_conflicting"]
    severity: BLOCKING
```

---

## Implementation Roadmap

### Phase 1: Foundation

1. Register GC_L and FACILITATION power types in governance model
2. Create Policy Library data structures
3. Implement Policy Library storage (Postgres table)

### Phase 2: Core Capability

4. Update CAP-009 (Policy Engine) with GC_L authority
5. Implement policy application routes
6. Add conflict detection

### Phase 3: Expansion

7. Update CAP-002 (Cost) with GC_L authority
8. Update CAP-003 (Proposals) with GC_L authority
9. Update CAP-014 (Memory) with GC_L authority
10. Update CAP-018 (Integration) with GC_L authority

### Phase 4: FACILITATION

11. Implement FACILITATION rules engine
12. Add warning/recommendation UI
13. Add blocking enforcement for security-critical rules

### Phase 5: Learning

14. Implement learning data collection (opt-in)
15. Add recommendation engine based on patterns
16. Customer opt-out mechanism

---

## Approval Status

This PIN has been **APPROVED** for implementation.

### Approval Checklist

- [x] Reclassification Table approved
- [x] Power Model Addendum approved
- [x] Constitution Delta approved
- [x] Risk Register reviewed
- [x] Policy Library schema approved
- [x] FACILITATION rules approved
- [x] Implementation roadmap approved

---

## References

- PIN-337: Governance Enforcement Infrastructure
- PIN-338: Governance Validator Baseline
- CAPABILITY_REGISTRY_UNIFIED.yaml
- AUTHORITY_DECLARATIONS_V1.yaml
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md

---

**Status:** ✅ APPROVED — Implementation authorized
