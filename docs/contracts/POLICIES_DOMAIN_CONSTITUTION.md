# Policies Domain Constitution

**Status:** RATIFIED
**Effective:** 2026-01-17
**Reference:** PIN-411, POLICIES_DOMAIN_AUDIT.md Section 14

---

## Preamble

This constitution establishes the permanent governance framework for the Policies domain.
It cannot be amended without explicit founder approval and must be enforced mechanically.

---

## Article I: Governance Invariants

The following invariants are **mandatory** and **cannot be optionalized**:

### GOV-POL-001: Conflict Detection is Mandatory Pre-Activation

> A policy cannot transition to ACTIVE status if BLOCKING conflicts exist.

**Rationale:** Prevents contradictory policies from entering enforcement simultaneously.

**Enforcement:**
- Location: `PolicyProposalEngine.approve()`
- Mechanism: PolicyConflictEngine.detect_conflicts() must return zero BLOCKING conflicts
- Violation: Activation blocked with error "BLOCKING conflict detected"

```python
# Enforcement pattern
conflicts = conflict_engine.detect_conflicts(policy_id)
blocking = [c for c in conflicts if c.severity == "BLOCKING"]
if blocking:
    raise PolicyActivationBlockedError(
        f"Cannot activate: {len(blocking)} BLOCKING conflicts exist"
    )
```

### GOV-POL-002: Dependency Resolution is Mandatory Pre-Delete

> A policy cannot be deleted if other policies depend on it.

**Rationale:** Prevents orphaned dependencies that break policy evaluation.

**Enforcement:**
- Location: `PolicyEngine.delete_rule()`
- Mechanism: PolicyDependencyEngine.get_dependents() must return empty list
- Violation: Deletion blocked with error "Dependent policies exist"

```python
# Enforcement pattern
dependents = dependency_engine.get_dependents(policy_id)
if dependents:
    raise PolicyDeletionBlockedError(
        f"Cannot delete: {len(dependents)} policies depend on this"
    )
```

### GOV-POL-003: Panel Invariants are Operator-Monitored

> Zero results trigger out-of-band alerts, never UI blocking.

**Rationale:** Distinguishes "nothing happened" (acceptable) from "ingestion is broken" (failure).

**Enforcement:**
- Location: `PanelInvariantMonitor` (scheduler-triggered)
- Mechanism: panel_invariant_registry.yaml defines expected behavior per panel
- Violation: Alert emitted to operator channel, UI continues to render

```python
# Enforcement pattern (never block UI)
result_count = await fetch_panel_data(panel_id)
if result_count == 0 and not invariant.zero_allowed:
    await monitor.emit_alert(AlertType.EMPTY_PANEL, panel_id)
    # UI STILL RENDERS - alert is out-of-band
```

---

## Article II: Conflict Types

The PolicyConflictEngine recognizes four conflict types:

| Type | Description | Default Severity |
|------|-------------|------------------|
| `SCOPE_OVERLAP` | Overlapping scopes with different enforcement modes | WARNING |
| `THRESHOLD_CONTRADICTION` | Same limit type with contradictory values | BLOCKING |
| `TEMPORAL_CONFLICT` | Overlapping time windows with conflicting rules | WARNING |
| `PRIORITY_OVERRIDE` | Lower priority rule contradicts higher priority | WARNING |

**Severity Meanings:**

| Severity | Meaning | Action |
|----------|---------|--------|
| `BLOCKING` | Must prevent activation | GOV-POL-001 applies |
| `WARNING` | Requires review | Human approval can override |

---

## Article III: Dependency Types

The PolicyDependencyEngine computes three dependency types:

| Type | Description | Source |
|------|-------------|--------|
| `EXPLICIT` | Declared via `depends_on` field | Policy definition |
| `IMPLICIT_SCOPE` | Same scope implies ordering | Computed |
| `IMPLICIT_LIMIT` | Limit references rule for threshold | Computed |

**Dependency Direction:** A → B means "A depends on B" (deleting B requires checking A).

---

## Article IV: Panel Invariant Registry

The panel invariant registry (`panel_invariant_registry.yaml`) defines expected behavior:

| Field | Purpose |
|-------|---------|
| `panel_id` | Unique panel identifier |
| `panel_question` | Human-readable panel intent |
| `endpoint` | API endpoint backing this panel |
| `filters` | Query parameters defining panel data |
| `min_rows` | Minimum expected rows in steady state |
| `warmup_grace_minutes` | Grace period after system start |
| `alert_after_minutes` | Duration of zero before alert |
| `zero_allowed` | Whether zero results is valid |
| `alert_enabled` | Whether to emit alerts |

**CI Guard (Mandatory):**

Any change to `/api/v1/policies/*` filters must update `panel_invariant_registry.yaml`
if it affects panel semantics.

Script: `scripts/preflight/check_panel_invariant_registry.py`

---

## Article V: Residual Risk Acceptance

**Accepted Risk:** False negatives in conflict detection due to semantic complexity.

This risk is acceptable because:
1. Severity classification separates BLOCKING from WARNING
2. BLOCKING conflicts prevent activation (mechanically enforced)
3. WARNING conflicts allow activation with visibility
4. Human review is required for all policy activation

**Trade-off principle:** Block what we can prove, warn on what we suspect, never silently allow contradictions.

---

## Article VI: Amendment Process

This constitution can only be amended with:
1. Explicit founder approval
2. Documented rationale in PIN
3. Mechanical enforcement update (CI or engine code)
4. Update to POLICIES_DOMAIN_AUDIT.md

"Temporary" exceptions are prohibited. Optionalization is prohibited.

---

## Signatures

- **Author:** Claude (PIN-411 implementation)
- **Date:** 2026-01-17
- **Status:** RATIFIED (pending founder ratification)
