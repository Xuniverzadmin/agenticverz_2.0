# PIN-520: L4 Uniformity Initiative

**Status:** ACTIVE
**Date:** 2026-02-03
**Category:** Architecture / HOC Layer Topology
**Predecessor:** PIN-491 (Operation Registry), PIN-484 (HOC Topology V2.0.0)
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

---

## Executive Summary

This PIN establishes a phased initiative to enforce **uniform L4 (hoc_spine) usage** across all 10 HOC domains. The goal is to eliminate L2→L5 bypasses, restore L5 purity, complete bridge coverage, and build the consequences subsystem.

**Core Principle:**
> At completion, uniformity stops being a goal and becomes a property.

---

## Problem Statement

### Current Violations

| Violation Type | Count | Impact |
|----------------|-------|--------|
| L2→L5 direct imports | 35+ | L4 loses visibility, no centralized dispatch |
| L5 DB imports (sqlmodel/sqlalchemy) | 17+ | L5 not pure, couples to persistence |
| L5→L5 cross-domain imports | 3 | Allowlisted but violates topology |
| L5 Session parameters | 42+ | Blurs L5/L6 boundary |
| Missing bridges | 3 domains | Forces L5→L5 direct imports |
| Consequences subsystem | STUB | No post-execution hooks |

### Root Causes

1. Operation registry exists (PIN-491) but L2 APIs bypass it
2. No CI enforcement for registry usage
3. Bridge coverage incomplete (7/10 domains)
4. AuthorityDecision not unified

---

## Phase Structure

### Phase 1: Registry Enforcement + AuthorityDecision Schema

**Objective:** Force all L2 calls through operation registry

**Deliverables:**
1. `hoc_spine/schemas/authority_decision.py` — Unified authority schema
2. CI check: `check_l2_no_direct_l5_imports` — Detect bypasses
3. Register operations for analytics/costsim endpoints (6 bypasses)
4. Register operations for policies/workers endpoints (4 bypasses)

**Non-Negotiable Constraints:**

| ID | Constraint | Enforcement |
|----|------------|-------------|
| STATIC-001 | Registry entries immutable at runtime | `freeze()` at startup |
| BINDING-001 | One operation → one L5 entry point | No fan-out in executor |
| DUMB-001 | Executor does context build + dispatch only | No domain conditionals |

**Success Metric:** Operations bypassing registry = 0 (for migrated endpoints)

---

### Phase 2: Bridge Completion (Ordered)

**Objective:** All 10 domains have L4 bridges

**Execution Order:**
1. `analytics_bridge.py` — Causal root of L5→L5 violations
2. `integrations_bridge.py` — Causal root of L5→L5 violations
3. `overview_bridge.py` — Read aggregation, lowest leverage

**Each Bridge Contract:**
- Max 5 methods
- Returns facades/engines (not sessions)
- Lazy imports from domain L5/L6
- No cross-domain imports at top level

**Success Metric:** Bridges = 10/10

---

### Phase 3A: Mechanical L5 Purity

**Objective:** Remove DB imports from L5, no semantic changes

**Scope:**
- Remove `Session`, `sqlmodel`, `select` from 17+ L5 engines
- Push DB access into corresponding L6 drivers
- Keep existing function signatures temporarily

**Pattern:**
```python
# BEFORE (L5 - impure)
def calculate(self, session: Session, tenant_id: str):
    rows = session.exec(select(Model))
    return self._compute(rows)

# AFTER (L5 - pure + L6)
# L5:
def calculate(self, tenant_id: str, rows: list[RowData]):
    return self._compute(rows)

# L6:
def fetch_rows(self, session: Session, tenant_id: str) -> list[RowData]:
    return session.exec(select(Model))
```

**Success Metric:** L5 DB imports = 0

---

### Phase 3B: Typed Context Hardening

**Objective:** Introduce immutable, versioned context schemas

**Scope:**
- Create `L5_schemas/contexts.py` per domain
- Define frozen dataclasses per operation
- Enforce via type checks

**Success Metric:** All registry operations have typed context schemas

---

### Phase 4: Consequences Subsystem (Minimal)

**Objective:** Build post-execution hooks

**Exactly 3 hooks:**

| Hook | Purpose |
|------|---------|
| `AuditConsequence` | Emit audit record |
| `IncidentConsequence` | Create incident if warranted |
| `NotificationConsequence` | Send alert/notification |

**PostExecutionHook Protocol:**
```python
class PostExecutionHook(Protocol):
    def on_success(self, result: Any, context: ExecutionContext) -> None: ...
    def on_failure(self, error: Exception, context: ExecutionContext) -> None: ...
```

**NOT in scope:** Retries, async routing, fan-out policies

**Success Metric:** 3 hooks implemented and wired

---

### Phase 5: Authority Implementation Unification

**Objective:** All authority checks return AuthorityDecision

**Scope:**
- `concurrent_runs.py` → returns AuthorityDecision
- `degraded_mode_checker.py` → returns AuthorityDecision
- `contract_engine.py` → returns AuthorityDecision

**Success Metric:** Single authority interface, no fragmented patterns

---

## CI Enforcement Sequence

**Rule:** Never unfreeze more than one violation class at a time

| Order | Violation Class | Current | Target | Unfreeze When |
|-------|-----------------|---------|--------|---------------|
| 1 | L2→L5 imports | 35+ | 0 | Phase 1 complete |
| 2 | L5 DB imports | 17+ | 0 | Phase 3A complete |
| 3 | L5→L5 cross-domain | 3 | 0 | Phase 2 complete |

Each unfreeze must reach **zero violations** before moving on.

---

## Complete Metrics Table

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| L2→L5 direct imports | ~20 | 0 | Reduced (-costsim, -workers, -main) |
| L5 DB imports | 17+ | 0 | Frozen |
| L5→L5 cross-domain | 3 | 0 | Frozen |
| Domains with bridges | 10/10 | 10/10 | ✅ COMPLETE |
| Operations in registry | ~30 | 150+ | Growing (+8 handlers) |
| Operations bypassing registry | ~20 | 0 | Phase 1 core complete |
| L2 bypass allowlist | 5 files | 0 | recovery*, billing*, cost_intel |
| Consequences hooks | 0 | 3 | Not started |
| AuthorityDecision unified | Partial | Yes | Schema created |

---

## Explicit Exclusions (What NOT to Add)

| Exclusion | Reason |
|-----------|--------|
| Dynamic operation discovery | Reintroduces drift |
| Plugin systems | Indirection without enforcement |
| Async orchestration in executor | Complexity amplifier |
| Domain-specific exceptions in registry | Defeats uniformity |
| Consequence chaining/fan-out | Amplifies failure modes |

---

## Implementation Tracking

### Phase 1 Checklist ✅ COMPLETE

- [x] Create `authority_decision.py` schema ✅ (2026-02-03)
- [x] CI check for L2→L5 bypasses (check 27 already exists - PIN-513) ✅
- [x] Register analytics/costsim operations ✅ (2026-02-03)
  - analytics.costsim.status
  - analytics.costsim.simulate
  - analytics.costsim.divergence
  - analytics.costsim.datasets
  - controls.circuit_breaker
- [x] Register policies/workers operations ✅ (2026-02-03)
  - logs.capture (evidence capture)
  - policies.health (moat health checks)
- [x] Migrate costsim.py to use registry ✅ (2026-02-03)
  - Removed from L2 bypass allowlist
- [x] Migrate workers.py to use registry ✅ (2026-02-03)
  - capture_environment_evidence → logs.capture
  - L5 health checks → policies.health
  - Removed from L2 bypass allowlist
- [x] Migrate main.py to use registry ✅ (2026-02-03)
  - recover_orphaned_runs → activity.orphan_recovery
  - Removed from L2 bypass allowlist
- [x] Create additional handlers for remaining migrations ✅ (2026-02-03)
  - account.billing.provider (for billing_dependencies.py, billing_gate.py)
  - activity.orphan_recovery (for main.py)
  - incidents.recovery_rules (for recovery.py)
  - policies.recovery.match (for recovery.py)
  - policies.recovery.write (for recovery_ingest.py, recovery.py)
- [x] Update literature documentation ✅ (2026-02-03)
  - logs_handler.md, policies_handler.md, logs_bridge.md
  - _summary.md updated with PIN-520 Phase 1 section
- [ ] Migrate remaining files (blocked by pre-existing issues):
  - billing_dependencies.py, billing_gate.py (sync FastAPI deps, needs sync handler pattern)
  - recovery.py (scoped_execution imports don't exist)
  - recovery_ingest.py (can migrate with policies.recovery.write)
  - cost_intelligence.py (import path doesn't exist)
- [ ] Unfreeze L2→L5 allowlist (when ready)

### Phase 2 Checklist

- [x] Create analytics_bridge.py ✅ (2026-02-03)
- [x] Create integrations_bridge.py ✅ (2026-02-03)
- [x] Create overview_bridge.py ✅ (2026-02-03)
- [x] Update __init__.py exports ✅ (2026-02-03)
- [ ] Verify cross-domain L5 violations resolved

### Phase 3A Checklist

- [ ] Audit all 17+ L5 engines with DB imports
- [ ] Extract DB logic to L6 drivers (per engine)
- [ ] Remove sqlmodel/sqlalchemy from L5
- [ ] Update CI allowlist

### Phase 3B Checklist

- [ ] Create context schemas per domain
- [ ] Update operation bindings to use typed contexts
- [ ] Add type enforcement tests

### Phase 4 Checklist

- [ ] Define PostExecutionHook protocol
- [ ] Implement AuditConsequence
- [ ] Implement IncidentConsequence
- [ ] Implement NotificationConsequence
- [ ] Wire hooks into executor

### Phase 5 Checklist

- [ ] Refactor concurrent_runs.py → AuthorityDecision
- [ ] Refactor degraded_mode_checker.py → AuthorityDecision
- [ ] Refactor contract_engine.py → AuthorityDecision
- [ ] Update executor to use unified interface

---

## Definition of Done

PIN-520 is **COMPLETE** when:

1. All L2 APIs route through operation registry (0 bypasses)
2. All 10 domains have bridges
3. All L5 engines are DB-import free
4. Consequences subsystem has 3 working hooks
5. Authority checks return unified AuthorityDecision
6. CI enforces all constraints (no frozen allowlists)

At that point, **uniformity is a property, not a goal**.

---

## References

- HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)
- PIN-491: Operation Registry
- PIN-484: HOC Topology V2.0.0 Ratification
- PIN-513: L1 Protocol Re-wiring
- literature/hoc_spine/ (65 files)
- literature/hoc_domain/ (10 domains)

---

*Created: 2026-02-03*
*Phase: 1 CORE COMPLETE (3/8 L2 files migrated, handlers ready for remaining)*
*Blockers: Pre-existing issues in recovery.py (missing scoped_execution), billing_*.py (sync deps)*
