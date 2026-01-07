# L2.1 Governance Assertions

**Document ID:** `L2_1_GOVERNANCE_ASSERTIONS`
**Version:** 1.0.0
**Status:** ACTIVE (FROZEN)
**Created:** 2026-01-07
**Authority Level:** NONE (this layer has no authority)

---

## 1. Purpose

This document explicitly asserts the governance constraints that apply to **all L2.1 artifacts**.

These are not guidelines. These are **hard rules**.

Violation of any assertion invalidates the L2.1 artifact.

---

## 2. Core Assertions

### GA-001: No Authority

```yaml
assertion_id: GA-001
name: "No Authority"
status: FROZEN

statement: |
  L2.1 has NO authority over any system behavior.
  L2.1 cannot:
    - Approve actions
    - Deny actions
    - Enforce policies
    - Modify state
    - Execute operations

enforcement:
  mechanism: Schema validation
  violation_response: REJECT

evidence_fields:
  - authority: "MUST be NONE"
  - signal_metadata.authoritative: "MUST be false"
  - action_intent.forbidden_action_types: "MUST include all mutating types"
```

### GA-002: No Execution

```yaml
assertion_id: GA-002
name: "No Execution"
status: FROZEN

statement: |
  L2.1 cannot execute any operation.
  L2.1 cannot:
    - Trigger workflows
    - Start jobs
    - Send requests
    - Invoke APIs
    - Mutate databases

enforcement:
  mechanism: Code review + static analysis
  violation_response: REJECT

evidence_fields:
  - All L2.1 modules: "MUST be pure functions or read-only"
  - No side effects: "MUST NOT have observable side effects"
  - No async triggers: "MUST NOT schedule or trigger async work"
```

### GA-003: No Learning

```yaml
assertion_id: GA-003
name: "No Learning"
status: FROZEN

statement: |
  L2.1 cannot learn, adapt, or evolve based on inputs.
  L2.1 cannot:
    - Store patterns
    - Update models
    - Adjust thresholds
    - Remember preferences
    - Build profiles

enforcement:
  mechanism: Code review + state audit
  violation_response: REJECT

evidence_fields:
  - No mutable state: "MUST NOT maintain learning state"
  - No ML inference: "MUST NOT run ML models"
  - No pattern storage: "MUST NOT persist observed patterns"
  - Deterministic: "Same input MUST produce same output"
```

### GA-004: No Cross-Tenant Scope

```yaml
assertion_id: GA-004
name: "No Cross-Tenant Scope"
status: FROZEN

statement: |
  L2.1 is strictly tenant-isolated.
  L2.1 cannot:
    - Aggregate across tenants
    - Compare tenant data
    - Reference other tenants
    - Leak tenant information

enforcement:
  mechanism: Schema validation + code review
  violation_response: REJECT (security critical)

evidence_fields:
  - scope.tenant_isolation: "MUST be true"
  - scope.constraints.cross_tenant_aggregation: "MUST be false"
  - All queries: "MUST include tenant_id filter"
```

---

## 3. Secondary Assertions

### GA-005: Phase-2 Projection Only

```yaml
assertion_id: GA-005
name: "Phase-2 Projection Only"
status: FROZEN

statement: |
  L2.1 can only project Phase-2 outputs.
  L2.1 cannot:
    - Generate new data
    - Enrich Phase-2 data
    - Infer missing data
    - Transform data semantically

enforcement:
  mechanism: IPC-L2.1 validation
  violation_response: REJECT

evidence_fields:
  - projection.enrichment_allowed: "MUST be false"
  - All data: "MUST trace to Phase-2 ir_hash"
```

### GA-006: L1 Constitution Alignment

```yaml
assertion_id: GA-006
name: "L1 Constitution Alignment"
status: FROZEN

statement: |
  L2.1 domains MUST be a subset of L1 Constitution.
  L2.1 cannot:
    - Add new domains
    - Rename domains
    - Merge domains
    - Create domain hierarchies not in L1

enforcement:
  mechanism: DSM-L2.1 validation
  violation_response: REJECT

evidence_fields:
  - All domain_id values: "MUST exist in DSM-L2.1"
  - DSM-L2.1: "MUST be subset of L1 Constitution"
```

### GA-007: Order Contract Compliance

```yaml
assertion_id: GA-007
name: "Order Contract Compliance"
status: FROZEN

statement: |
  L2.1 surfaces MUST comply with OSD-L2.1 order definitions.
  L2.1 cannot:
    - Define new orders
    - Modify order shapes
    - Skip order validation
    - Violate order transitions

enforcement:
  mechanism: OSD-L2.1 validation
  violation_response: REJECT

evidence_fields:
  - orders.*: "MUST match OSD-L2.1 shape"
  - O5: "MUST be terminal and immutable"
```

### GA-008: Replay Invariant

```yaml
assertion_id: GA-008
name: "Replay Invariant"
status: FROZEN

statement: |
  L2.1 projections MUST be replay-identical.
  Given same inputs:
    - Same ir_hash
    - Same fact_snapshot_id
    - Same selection/ordering criteria

  Output MUST be byte-identical.

enforcement:
  mechanism: Replay tests
  violation_response: REJECT

evidence_fields:
  - Deterministic functions: "MUST NOT use random, time, or external state"
  - No side-effect reads: "MUST NOT read mutable external state"
```

---

## 4. Facilitation Constraints

### GA-009: Non-Authoritative Signals Only

```yaml
assertion_id: GA-009
name: "Non-Authoritative Signals Only"
status: FROZEN

statement: |
  All L2.1 signals (recommendations, warnings) are non-authoritative.
  Every signal MUST carry:
    - authority: NONE
    - signal_metadata.authoritative: false
    - signal_metadata.actionable: false

enforcement:
  mechanism: Schema validation
  violation_response: REJECT

evidence_fields:
  - facilitation.authority: "MUST be NONE"
  - facilitation.signal_metadata.authoritative: "MUST be false"
```

### GA-010: UI Intent Not Layout

```yaml
assertion_id: GA-010
name: "UI Intent Not Layout"
status: FROZEN

statement: |
  UIS-L2.1 declares intent, not layout.
  L2.1 cannot:
    - Specify pixel dimensions
    - Dictate colors
    - Define animations
    - Prescribe component types

enforcement:
  mechanism: Code review
  violation_response: REJECT

evidence_fields:
  - No CSS: "MUST NOT include styling"
  - No dimensions: "MUST NOT specify sizes"
  - Affordance hints only: "MUST use abstract capability declarations"
```

---

## 5. Violation Handling

### 5.1 Violation Severity

| Assertion | Severity | Response |
|-----------|----------|----------|
| GA-001 (No Authority) | CRITICAL | REJECT + incident |
| GA-002 (No Execution) | CRITICAL | REJECT + incident |
| GA-003 (No Learning) | CRITICAL | REJECT + incident |
| GA-004 (No Cross-Tenant) | CRITICAL | REJECT + security incident |
| GA-005 (Phase-2 Only) | HIGH | REJECT |
| GA-006 (L1 Alignment) | HIGH | REJECT |
| GA-007 (Order Compliance) | HIGH | REJECT |
| GA-008 (Replay Invariant) | HIGH | REJECT |
| GA-009 (Non-Auth Signals) | MEDIUM | REJECT |
| GA-010 (Intent Not Layout) | MEDIUM | REJECT |

### 5.2 Violation Response Template

```yaml
violation_report:
  assertion_id: ""
  artifact_id: ""
  timestamp: ""
  severity: ""

  violation_details:
    field: ""
    expected: ""
    actual: ""
    evidence: ""

  response:
    action: REJECT | WARN | INCIDENT
    remediation: ""
    escalation: ""
```

---

## 6. Assertion Validation

### 6.1 Automated Checks

```python
def validate_l2_1_governance(artifact: dict) -> GovernanceResult:
    """Validate all L2.1 governance assertions."""

    violations = []

    # GA-001: No Authority
    if artifact.get("authority") != "NONE":
        violations.append(GovernanceViolation("GA-001", "authority != NONE"))

    # GA-002: No Execution (code analysis required)
    # GA-003: No Learning (code analysis required)

    # GA-004: No Cross-Tenant
    if not artifact.get("scope", {}).get("tenant_isolation", False):
        violations.append(GovernanceViolation("GA-004", "tenant_isolation != true"))

    # GA-005: Phase-2 Projection
    if artifact.get("projection", {}).get("enrichment_allowed", True):
        violations.append(GovernanceViolation("GA-005", "enrichment_allowed != false"))

    # GA-006: L1 Alignment
    domain_id = artifact.get("domain", {}).get("id")
    if domain_id and not validate_domain_exists(domain_id):
        violations.append(GovernanceViolation("GA-006", f"domain {domain_id} not in DSM"))

    # GA-009: Non-Auth Signals
    facilitation = artifact.get("facilitation", {})
    if facilitation.get("authority") != "NONE":
        violations.append(GovernanceViolation("GA-009", "facilitation.authority != NONE"))

    return GovernanceResult(
        valid=len(violations) == 0,
        violations=violations
    )
```

### 6.2 Manual Review Checklist

For assertions requiring code review:

```markdown
## L2.1 Governance Review Checklist

### GA-002: No Execution
- [ ] No HTTP calls
- [ ] No database writes
- [ ] No queue publishes
- [ ] No file system writes
- [ ] No subprocess spawning

### GA-003: No Learning
- [ ] No mutable module-level state
- [ ] No ML model loading
- [ ] No pattern caching
- [ ] No preference storage
- [ ] All functions are pure

### GA-010: UI Intent Not Layout
- [ ] No pixel values
- [ ] No color codes
- [ ] No CSS classes
- [ ] No component names
- [ ] Only abstract affordances
```

---

## 7. Amendment Process

These assertions are **FROZEN**.

To amend:

1. **Propose** amendment with detailed rationale
2. **Impact analysis** on all existing L2.1 artifacts
3. **Human ratification** required
4. **Update** this document with version increment
5. **Re-validate** all existing artifacts

**No silent amendments. No Claude-initiated amendments.**

---

## 8. References

- `ESM_L2_1_TEMPLATE.md` — Master template
- `DSM_L2_1.md` — Domain manifest
- `OSD_L2_1.md` — Order definitions
- `IPC_L2_1.md` — Projection contract
- `UIS_L2_1.md` — UI intent surface
- `CLAUDE_AUTHORITY.md` — Authority hierarchy
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md` — L1 Constitution

---

## 9. Summary Table

| ID | Assertion | Status | Severity |
|----|-----------|--------|----------|
| GA-001 | No Authority | FROZEN | CRITICAL |
| GA-002 | No Execution | FROZEN | CRITICAL |
| GA-003 | No Learning | FROZEN | CRITICAL |
| GA-004 | No Cross-Tenant Scope | FROZEN | CRITICAL |
| GA-005 | Phase-2 Projection Only | FROZEN | HIGH |
| GA-006 | L1 Constitution Alignment | FROZEN | HIGH |
| GA-007 | Order Contract Compliance | FROZEN | HIGH |
| GA-008 | Replay Invariant | FROZEN | HIGH |
| GA-009 | Non-Authoritative Signals Only | FROZEN | MEDIUM |
| GA-010 | UI Intent Not Layout | FROZEN | MEDIUM |

---

**STATUS:** ACTIVE (FROZEN) — These assertions govern all L2.1 artifacts.
