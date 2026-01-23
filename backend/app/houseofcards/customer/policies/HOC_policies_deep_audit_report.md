# HOC Policies Domain Deep Audit Report

**Date:** 2026-01-23
**Scope:** `houseofcards/customer/policies/` only
**Auditor:** Claude Code
**Reference:** Follows quarantine strategy from incidents domain audit

---

## Executive Summary

Audited **35 Python files** within the policies domain. Found **6 duplication issues** requiring attention. The policies domain has clearer separation than the incidents domain, but several dataclass/type duplications exist between facades and engines.

| Metric | Count |
|--------|-------|
| Total Files Scanned | 35 |
| Facades | 5 |
| Engines | 24 |
| Controls Subfolder | 6 |
| **Duplication Issues** | **6** |
| Severity: HIGH | 0 |
| Severity: MEDIUM | 4 |
| Severity: LOW | 2 |

---

## Files Inventoried

### Facades (5 files)

| File | Dataclasses | Enums | Classes |
|------|-------------|-------|---------|
| `policies_facade.py` | 27 | 0 | PoliciesFacade |
| `controls_facade.py` | 2 | 2 | ControlsFacade |
| `governance_facade.py` | 4 | 1 | GovernanceFacade |
| `limits_facade.py` | 3 | 2 | LimitsFacade |
| `run_governance_facade.py` | 0 | 0 | RunGovernanceFacade |

### Engines (24 files)

| File | Dataclasses | Enums | Key Classes |
|------|-------------|-------|-------------|
| `policy_violation_service.py` | 3 | 0 | PolicyViolationService |
| `snapshot_service.py` | 2 | 2 | PolicySnapshotRegistry |
| `validator_service.py` | 3 | 5 | ValidatorService |
| `policy_mapper.py` | 2 | 2 | MCPPolicyMapper |
| `policy_proposal.py` | 0 | 0 | (Exceptions only) |
| `lessons_engine.py` | 0 | 0 | LessonsLearnedEngine |
| `llm_policy_engine.py` | 1 | 0 | LLMRateLimiter |
| `budget_enforcement_engine.py` | 0 | 0 | BudgetEnforcementEngine |
| `claim_decision_engine.py` | 0 | 0 | (Functions only) |
| `policy_graph_engine.py` | 5 | 3 | PolicyConflictEngine, PolicyDependencyEngine |
| `customer_policy_read_service.py` | 4 | 0 | CustomerPolicyReadService |
| `override_service.py` | 0 | 0 | LimitOverrideService |
| `policy_limits_service.py` | 0 | 0 | PolicyLimitsService |
| `policy_rules_service.py` | 0 | 0 | PolicyRulesService |
| `simulation_service.py` | 0 | 0 | LimitsSimulationService |
| `eligibility_engine.py` | 4 | 2 | EligibilityEngine |
| `control_registry.py` | 2 | 2 | SOC2ControlRegistry |
| `mapper.py` | 0 | 0 | SOC2ControlMapper |
| `hallucination_detector.py` | 3 | 2 | HallucinationDetector |
| `authority_checker.py` | 1 | 1 | OverrideAuthorityChecker |

### Controls Subfolder (6 files)

| File | Dataclasses | Enums | Key Artifacts |
|------|-------------|-------|---------------|
| `runtime_switch.py` | 1 | 0 | GovernanceState, helper functions |
| `degraded_mode_checker.py` | 3 | 2 | GovernanceDegradedModeChecker |
| `customer_killswitch_read_service.py` | 4 | 0 | CustomerKillswitchReadService |

---

## Duplication Issues Found

### POL-DUP-001: PolicyNodeResult vs PolicyNode

**Severity:** MEDIUM
**Type:** 100% Field Overlap

| Location | Class Name | Fields |
|----------|------------|--------|
| `facades/policies_facade.py:240` | PolicyNodeResult | id, name, rule_type, scope, status, enforcement_mode, depends_on, required_by |
| `engines/policy_graph_engine.py` | PolicyNode | id, name, rule_type, scope, status, enforcement_mode, depends_on, required_by |

**Issue:** Facade defines its own dataclass instead of importing from engine. 100% field overlap.

**Recommendation:** Remove `PolicyNodeResult` from facade. Import and use `PolicyNode` from `policy_graph_engine.py`.

---

### POL-DUP-002: PolicyDependencyEdge vs PolicyDependency

**Severity:** MEDIUM
**Type:** Same Fields, Different Names

| Location | Class Name | Fields |
|----------|------------|--------|
| `facades/policies_facade.py:254` | PolicyDependencyEdge | policy_id, depends_on_id, policy_name, depends_on_name, dependency_type, reason |
| `engines/policy_graph_engine.py` | PolicyDependency | policy_id, depends_on_id, policy_name, depends_on_name, dependency_type, reason |

**Issue:** Identical structure with different class names.

**Recommendation:** Consolidate to single type. Facade should import from engine.

---

### POL-DUP-003: DependencyGraphResult Re-definition

**Severity:** MEDIUM
**Type:** Structural Overlap with Extension

| Location | Class Name | Fields |
|----------|------------|--------|
| `facades/policies_facade.py:266` | DependencyGraphResult | nodes, edges, nodes_count, edges_count, computed_at |
| `engines/policy_graph_engine.py` | DependencyGraphResult | nodes, edges, computed_at |

**Issue:** Facade re-defines engine DTO with added fields (nodes_count, edges_count).

**Recommendation:** If added fields are needed, extend engine DTO. Otherwise, compute counts at usage site rather than duplicating structure.

---

### POL-DUP-004: PolicyConflictResult vs PolicyConflict

**Severity:** MEDIUM
**Type:** 100% Field Overlap

| Location | Class Name | Fields |
|----------|------------|--------|
| `facades/policies_facade.py:205` | PolicyConflictResult | policy_a_id, policy_b_id, policy_a_name, policy_b_name, conflict_type, severity, explanation, recommended_action, detected_at |
| `engines/policy_graph_engine.py` | PolicyConflict | policy_a_id, policy_b_id, policy_a_name, policy_b_name, conflict_type, severity, explanation, recommended_action, detected_at |

**Issue:** Complete field overlap. Facade creates duplicate dataclass.

**Recommendation:** Remove `PolicyConflictResult`. Import `PolicyConflict` from engine and use directly or create thin alias.

---

### POL-DUP-005: LimitNotFoundError Duplicate Exception

**Severity:** LOW
**Type:** Same Exception Name, Different Hierarchies

| Location | Exception | Base Class |
|----------|-----------|------------|
| `engines/override_service.py:57` | LimitNotFoundError | LimitOverrideServiceError |
| `engines/policy_limits_service.py:61` | LimitNotFoundError | PolicyLimitsServiceError |

**Issue:** Same exception class name used in two different services with different base classes. Can cause confusion when catching exceptions.

**Recommendation:** Either:
1. Create shared `LimitNotFoundError` in `engines/policies_types.py` (like incidents domain)
2. Or rename to service-specific names (`OverrideLimitNotFoundError`, `PolicyLimitNotFoundError`)

---

### POL-DUP-006: utc_now() and generate_uuid() Helper Duplication

**Severity:** LOW
**Type:** Repeated Utility Functions

| Location | Functions |
|----------|-----------|
| `engines/override_service.py:42-49` | utc_now(), generate_uuid() |
| `engines/policy_limits_service.py:46-53` | utc_now(), generate_uuid() |
| `engines/policy_rules_service.py:46-53` | utc_now(), generate_uuid() |

**Issue:** Identical helper functions copied across 3+ engine files.

**Recommendation:** Create `engines/policies_types.py` (similar to incidents domain) with shared:
- `UuidFn = Callable[[], str]`
- `ClockFn = Callable[[], datetime]`
- Default implementations: `utc_now()`, `generate_uuid()`

---

## Pattern Analysis

### Positive Patterns Observed

1. **Clear L4 Header Comments:** All files have proper layer annotations
2. **Singleton Factories:** Consistent `get_*()` pattern for singletons
3. **Tenant Isolation:** All facades enforce tenant_id scoping
4. **Frozen Dataclasses:** Engine DTOs use `frozen=True` where appropriate

### Architectural Concerns

1. **Facade DTO Duplication:** Multiple facade dataclasses are 100% copies of engine DTOs. This violates the principle that facades should compose/extend engine types, not duplicate them.

2. **Missing Shared Types Module:** Unlike the incidents domain which now has `engines/incidents_types.py`, the policies domain lacks a shared types module for common type aliases.

---

## Recommended Actions

### Phase 1: Create Shared Types (POL-DUP-006)

Create `engines/policies_types.py`:
```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Shared type aliases for policies domain engines

from datetime import datetime, timezone
from typing import Callable
import uuid

UuidFn = Callable[[], str]
ClockFn = Callable[[], datetime]

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    return str(uuid.uuid4())

__all__ = ["UuidFn", "ClockFn", "utc_now", "generate_uuid"]
```

### Phase 2: Consolidate Graph DTOs (POL-DUP-001 to POL-DUP-004)

1. Update `facades/policies_facade.py` to import from `engines/policy_graph_engine.py`:
   - Remove `PolicyNodeResult`, use `PolicyNode`
   - Remove `PolicyDependencyEdge`, use `PolicyDependency`
   - Remove `PolicyConflictResult`, use `PolicyConflict`
   - Either extend `DependencyGraphResult` or add counts at usage site

### Phase 3: Exception Consolidation (POL-DUP-005)

Either:
- Create shared `LimitNotFoundError` in `policies_types.py`
- Or rename to service-specific names for clarity

---

## Comparison to Incidents Domain

| Aspect | Incidents Domain | Policies Domain |
|--------|------------------|-----------------|
| Total Issues | 10 | 6 |
| Quarantined Files | 3+ | **4** ✅ |
| Shared Types Module | YES (`incidents_types.py`) | NO (deferred) |
| Pattern | Heavy duplication | Moderate duplication |

The policies domain is in better shape than incidents was. Quarantine has been executed.

---

## Quarantine Execution Summary

**Executed:** 2026-01-23

### Actions Taken

| Issue | Action | Status |
|-------|--------|--------|
| POL-DUP-001 | Quarantined `PolicyNodeResult` | ✅ COMPLETE |
| POL-DUP-002 | Quarantined `PolicyDependencyEdge` | ✅ COMPLETE |
| POL-DUP-003 | Quarantined `DependencyGraphResult` | ✅ COMPLETE |
| POL-DUP-004 | Quarantined `PolicyConflictResult` | ✅ COMPLETE |
| POL-DUP-005 | `LimitNotFoundError` exception | ⏸ DEFERRED |
| POL-DUP-006 | `utc_now()`/`generate_uuid()` helpers | ⏸ DEFERRED |

### Quarantine Location

```
houseofcards/duplicate/policies/
├── __init__.py                    # NO EXPORTS
├── policy_conflict_result.py      # POL-DUP-004
├── policy_node_result.py          # POL-DUP-001
├── policy_dependency_edge.py      # POL-DUP-002
├── dependency_graph_result.py     # POL-DUP-003
└── README.md
```

### Canonical Authority Declared

| Type | Authoritative Location |
|------|------------------------|
| PolicyConflict | `engines/policy_graph_engine.py:73` |
| PolicyNode | `engines/policy_graph_engine.py:125` |
| PolicyDependency | `engines/policy_graph_engine.py:101` |
| DependencyGraphResult | `engines/policy_graph_engine.py:151` |

---

## Summary

The policies domain audit identified **6 duplication issues**:

| Category | Issues | Status |
|----------|--------|--------|
| Facade DTO duplicates | 4 (MEDIUM) | ✅ QUARANTINED |
| Helper function duplication | 1 (LOW) | ⏸ DEFERRED |
| Exception name collision | 1 (LOW) | ⏸ DEFERRED |

**Remaining Work:**
1. ⏸ Create `engines/policies_types.py` (deferred — not urgent)
2. ⏸ Resolve exception naming (deferred — error taxonomy work)
3. ✅ Quarantine complete — engine DTOs are authoritative

---

**Report Generated:** 2026-01-23
**Quarantine Executed:** 2026-01-23
**Status:** COMPLETE
