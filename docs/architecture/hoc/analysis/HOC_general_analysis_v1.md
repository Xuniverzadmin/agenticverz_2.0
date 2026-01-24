# HOC General Domain Analysis v1

**Date:** 2026-01-22
**Domain:** `app/hoc/cus/general/`
**Status:** Analysis Complete — Governance Recommended

---

## Executive Summary

| Aspect | Assessment |
|--------|------------|
| Architectural quality | Mixed (needs governance) |
| Role clarity | Low (multi-purpose domain) |
| Current risk | Medium-High |
| Code volume | Very High (10,000+ LOC) |
| Subdomain count | 7 distinct subdomains |
| Changes recommended | Domain split + governance contracts |

**Verdict:** General is an aggregation domain that has accumulated diverse responsibilities. It functions as a "catch-all" for runtime orchestration, lifecycle management, and cross-domain operations. **This domain should be split into dedicated domains** after governance is applied.

---

## Directory Structure

```
app/hoc/cus/general/
├── __init__.py                                (12 LOC)
├── facades/
│   ├── __init__.py                            (11 LOC)
│   ├── monitors_facade.py                     (535 LOC)
│   ├── alerts_facade.py                       (671 LOC)
│   ├── scheduler_facade.py                    (544 LOC)
│   ├── compliance_facade.py                   (510 LOC)
│   └── lifecycle_facade.py                    (701 LOC)
├── engines/
│   ├── __init__.py                            (11 LOC)
│   ├── alert_emitter.py                       (~300 LOC)
│   ├── alert_fatigue.py                       (~250 LOC)
│   ├── fatigue_controller.py                  (~200 LOC)
│   ├── cus_health_service.py                  (~300 LOC)
│   ├── cus_telemetry_service.py               (~300 LOC)
│   ├── cus_enforcement_service.py             (~250 LOC)
│   ├── knowledge_lifecycle_manager.py         (~400 LOC)
│   ├── knowledge_sdk.py                       (972 LOC) ← L2 in engines?
│   ├── panel_invariant_monitor.py             (449 LOC)
│   └── alert_log_linker.py                    (752 LOC)
├── drivers/
│   └── __init__.py                            (11 LOC)
├── schemas/
│   └── __init__.py                            (11 LOC)
├── runtime/
│   └── engines/
│       ├── governance_orchestrator.py         (800 LOC)
│       ├── run_governance_facade.py           (~500 LOC)
│       ├── transaction_coordinator.py         (~400 LOC)
│       ├── phase_status_invariants.py         (~300 LOC)
│       ├── plan_generation_engine.py          (~350 LOC)
│       └── constraint_checker.py              (~300 LOC)
├── controls/
│   └── engines/
│       └── guard_write_service.py             (249 LOC) ← TEMPORARY
├── lifecycle/
│   └── engines/
│       ├── base.py                            (310 LOC)
│       ├── onboarding.py                      (~400 LOC)
│       ├── offboarding.py                     (~350 LOC)
│       ├── pool_manager.py                    (599 LOC)
│       ├── knowledge_plane.py                 (468 LOC)
│       └── execution.py                       (1313 LOC)
├── ui/
│   └── engines/
│       └── rollout_projection.py              (717 LOC)
├── workflow/
│   └── contracts/
│       └── engines/
│           └── contract_service.py            (708 LOC)
└── cross-domain/
    └── engines/
        └── cross_domain.py                    (497 LOC)
                                               ──────────
                           Total:              ~10,500+ LOC
```

---

## Subdomain Analysis

### 1. Core Facades (`facades/`)

**Total:** ~2,961 LOC across 5 facades

| File | LOC | Purpose | Assessment |
|------|-----|---------|------------|
| `monitors_facade.py` | 535 | System monitoring | Good isolation |
| `alerts_facade.py` | 671 | Alert management | Good isolation |
| `scheduler_facade.py` | 544 | Job scheduling | Good isolation |
| `compliance_facade.py` | 510 | Compliance checking | Good isolation |
| `lifecycle_facade.py` | 701 | Lifecycle management | Good isolation |

**Assessment:** Facades are well-structured but belong to different domains.

---

### 2. Core Engines (`engines/`)

**Total:** ~4,184 LOC across 10 engines

| File | LOC | Layer | Role | Issues |
|------|-----|-------|------|--------|
| `alert_emitter.py` | ~300 | L4 | Alert emission | Clean |
| `alert_fatigue.py` | ~250 | L4 | Fatigue detection | Clean |
| `fatigue_controller.py` | ~200 | L4 | Fatigue control | Clean |
| `cus_health_service.py` | ~300 | L4 | Customer health | Clean |
| `cus_telemetry_service.py` | ~300 | L4 | Telemetry | Clean |
| `cus_enforcement_service.py` | ~250 | L4 | Enforcement | Clean |
| `knowledge_lifecycle_manager.py` | ~400 | L4 | Knowledge lifecycle | Clean |
| `knowledge_sdk.py` | 972 | **L2?** | SDK Facade | **MISCLASSIFIED** |
| `panel_invariant_monitor.py` | 449 | L4 | Panel health | Clean |
| `alert_log_linker.py` | 752 | L4 | Alert-log linking | Clean (GAP-019) |

**Critical Issue:** `knowledge_sdk.py` is marked as L2 (Product APIs) but placed in engines directory. This is a layer violation.

---

### 3. Runtime Subdomain (`runtime/engines/`)

**Total:** ~2,650 LOC across 6 engines

| File | LOC | Purpose | Reference |
|------|-----|---------|-----------|
| `governance_orchestrator.py` | 800 | Orchestrates contract execution | PIN-292 |
| `run_governance_facade.py` | ~500 | Run governance interface | |
| `transaction_coordinator.py` | ~400 | Transaction coordination | |
| `phase_status_invariants.py` | ~300 | Phase invariant checking | |
| `plan_generation_engine.py` | ~350 | Plan generation | |
| `constraint_checker.py` | ~300 | Constraint validation | |

**Assessment:** Runtime is a cohesive subdomain with clear purpose. Should be extracted as dedicated domain.

**Key Classes:**
- `GovernanceOrchestrator` - Orchestrates only, does not execute
- `ContractActivationService` - Contract lifecycle
- `ExecutionOrchestrator` - Execution coordination
- `JobStateTracker` - State machine for jobs

---

### 4. Controls Subdomain (`controls/engines/`)

**Total:** 249 LOC

| File | LOC | Purpose | Status |
|------|-----|---------|--------|
| `guard_write_service.py` | 249 | Guard API DB writes | TEMPORARY |

**Header States:**
```
# TEMPORARY AGGREGATE service for Phase 2B extraction
# May split into KillSwitchWriteService and IncidentWriteService in Phase 3+
```

**Assessment:** This is temporary scaffolding. Track for Phase 3 split.

---

### 5. Lifecycle Subdomain (`lifecycle/engines/`)

**Total:** ~3,440 LOC across 6 engines

| File | LOC | Purpose | Reference |
|------|-----|---------|-----------|
| `base.py` | 310 | Stage handler protocol | GAP-071-082 |
| `onboarding.py` | ~400 | Onboarding stages | |
| `offboarding.py` | ~350 | Offboarding stages | |
| `pool_manager.py` | 599 | Connection pool mgmt | GAP-172 |
| `knowledge_plane.py` | 468 | Knowledge graph models | GAP-056 |
| `execution.py` | 1313 | Data/index/classify executors | GAP-159-161 |

**Key Design Pattern:**
```python
# Stage handlers are DUMB PLUGINS:
# - Do NOT manage state
# - Do NOT emit events
# - Do NOT check policies
# StageHandler is a Protocol with:
#   - stage_name, handles_states
#   - execute(), validate()
```

**Assessment:** Cohesive lifecycle subdomain. Should be extracted.

---

### 6. UI Subdomain (`ui/engines/`)

**Total:** 717 LOC

| File | LOC | Purpose | Reference |
|------|-----|---------|-----------|
| `rollout_projection.py` | 717 | Rollout state projection | PIN-296 |

**Key Invariants:**
```
ROLLOUT-001: Projection is read-only
ROLLOUT-002: Stage advancement requires audit PASS
ROLLOUT-003: Stage advancement requires stabilization
ROLLOUT-004: No health degradation during rollout
ROLLOUT-005: Stages are monotonic
ROLLOUT-006: Customer sees only current stage facts
```

**Assessment:** Clean projection service. Could remain in general or move to dedicated UI domain.

---

### 7. Workflow Contracts Subdomain (`workflow/contracts/engines/`)

**Total:** 708 LOC

| File | LOC | Purpose | Reference |
|------|-----|---------|-----------|
| `contract_service.py` | 708 | System Contract state machine | PIN-291 |

**Key Invariants:**
```
CONTRACT-001: Status transitions must follow state machine
CONTRACT-002: APPROVED requires approved_by
CONTRACT-003: ACTIVE requires job exists
CONTRACT-004: COMPLETED requires audit_verdict = PASS
CONTRACT-005: Terminal states are immutable
CONTRACT-006: proposed_changes must validate schema
CONTRACT-007: confidence_score range [0,1]
```

**MAY_NOT Enforcement (PIN-291):**
```python
# MAY_NOT verdicts are mechanically un-overridable
# No constructor, method, or bypass can create contracts from MAY_NOT
```

**Assessment:** Well-governed with explicit invariants. Should be extracted to dedicated contracts domain.

---

### 8. Cross-Domain Subdomain (`cross-domain/engines/`)

**Total:** 497 LOC

| File | LOC | Purpose | Reference |
|------|-----|---------|-----------|
| `cross_domain.py` | 497 | Mandatory governance functions | design/CROSS_DOMAIN_GOVERNANCE.md |

**Doctrine:**
```python
# Governance must throw
# No optional dependencies
# Learning is downstream only
```

**Key Functions:**
- `create_incident_from_cost_anomaly()` - Async
- `record_limit_breach()` - Async
- Plus sync versions for compatibility

**Assessment:** Critical governance functions. Should remain accessible from all domains.

---

## Layer Distribution

| Layer | File Count | Description |
|-------|------------|-------------|
| L4 | 25+ | Domain engines (correct) |
| L2 | 1 | `knowledge_sdk.py` (MISPLACED) |

---

## Issues Identified

### 1. CRITICAL: Layer Misclassification

**File:** `engines/knowledge_sdk.py`
**Problem:** Marked as L2 (Product APIs) but placed in engines directory
**Impact:** Violates layer architecture

**Resolution Required:**
- Move to `app/api/` if truly L2
- OR reclassify as L4 if engine behavior is correct

---

### 2. HIGH: Domain Sprawl

**Problem:** General domain accumulates unrelated functionality:
- Alerts (should be Incidents or dedicated Alerts domain)
- Monitors (should be dedicated Monitoring domain)
- Lifecycle (should be dedicated Lifecycle domain)
- Contracts (should be dedicated Contracts domain)
- Runtime (should be dedicated Runtime domain)

**Impact:** Violates single-responsibility principle at domain level.

---

### 3. MEDIUM: Temporary Service

**File:** `controls/engines/guard_write_service.py`
**Problem:** Explicitly marked as TEMPORARY
**Impact:** Technical debt if not resolved

**Track:** Phase 3 split into KillSwitchWriteService + IncidentWriteService

---

### 4. LOW: Governance Not Declared

**Problem:** No governance contract in `general/__init__.py`
**Impact:** Entry points and invariants not documented

---

## Recommended Domain Split

Based on cohesion analysis, recommend splitting general into:

| New Domain | Source Files | LOC |
|------------|--------------|-----|
| `runtime/` | `runtime/engines/*` | ~2,650 |
| `lifecycle/` | `lifecycle/engines/*` | ~3,440 |
| `contracts/` | `workflow/contracts/engines/*` | 708 |
| `alerts/` | Alert-related engines + facades | ~2,000 |
| `monitors/` | Monitor-related engines + facades | ~1,000 |

**Keep in General:**
- `cross-domain/engines/cross_domain.py` (shared governance)
- `ui/engines/rollout_projection.py` (read-only projection)

---

## Domain Contract (Proposed)

```python
"""
General Domain

TEMPORARY AGGREGATION DOMAIN
============================

This domain is an aggregation point for runtime orchestration,
lifecycle management, and cross-domain operations.

PLANNED EXTRACTION:
1. runtime/engines/* → app/hoc/cus/runtime/
2. lifecycle/engines/* → app/hoc/cus/lifecycle/
3. workflow/contracts/* → app/hoc/cus/contracts/
4. Alert engines → app/hoc/cus/alerts/

INVARIANTS (System-Wide):

INV-GEN-001: Cross-domain functions MUST throw on failure (no silent failures)
INV-GEN-002: Stage handlers are dumb plugins (no state, no events, no policies)
INV-GEN-003: Projection services are read-only (no mutation authority)
INV-GEN-004: MAY_NOT verdicts are mechanically un-overridable

KNOWN ISSUES:

1. knowledge_sdk.py is L2 in engines (layer violation)
2. guard_write_service.py is temporary (split pending)
3. Domain needs split (see PLANNED EXTRACTION above)
"""
```

---

## Cross-Domain Dependencies

| File | External Imports |
|------|------------------|
| `governance_orchestrator.py` | `app.models.contract.*` |
| `contract_service.py` | `app.models.contract.*`, `app.services.governance.*` |
| `cross_domain.py` | `app.models.incidents.*`, `app.services.policies.*` |
| `execution.py` | `app.services.connectors.*` |
| `alert_log_linker.py` | `app.models.*` |

---

## Key Architectural Properties

| Property | Status |
|----------|--------|
| Owns tables | **NO** (uses external models) |
| Tenant isolation | **YES** (where applicable) |
| Layer compliance | **PARTIAL** (knowledge_sdk.py violation) |
| Governance contract | **NO** (needs addition) |
| Cohesive domain | **NO** (needs split) |

---

## Action Items

### Immediate (Before Next Phase)

1. **Add governance contract** to `general/__init__.py`
2. **Document known issues** in domain contract
3. **Track** guard_write_service.py for Phase 3 split

### Near-Term (Phase 4+)

4. **Resolve** knowledge_sdk.py layer classification
5. **Begin extraction** of runtime subdomain
6. **Begin extraction** of lifecycle subdomain
7. **Begin extraction** of contracts subdomain

### Long-Term

8. **Complete domain split** per recommendation above
9. **Remove** general domain once empty (or keep for cross-domain only)

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total LOC | ~10,500+ |
| Subdomain count | 7 |
| Engine files | 25+ |
| Facade files | 5 |
| Layer violations | 1 |
| Temporary services | 1 |
| Documented invariants | 20+ (across files) |

---

## Conclusion

The General domain is **functional but over-aggregated**. It has accumulated diverse responsibilities that should be separated into dedicated domains.

**Strengths:**
- Individual engines are well-documented with invariants
- Clear GAP/PIN references throughout
- Governance patterns (MAY_NOT, stage handlers, projections) are sound

**Weaknesses:**
- Domain-level cohesion is low
- One layer violation exists
- Temporary service exists without resolution timeline

**Recommendation:** Apply governance contract now, plan domain split for Phase 4+.

---

## Changes Applied

| Date | Change |
|------|--------|
| 2026-01-22 | Initial analysis complete |
| 2026-01-22 | Identified layer violation (knowledge_sdk.py) |
| 2026-01-22 | Documented 7 subdomains with LOC analysis |
| 2026-01-22 | Proposed domain split strategy |
| 2026-01-22 | Proposed governance contract |

---

## References

| Reference | File |
|-----------|------|
| PIN-291 | Contract MAY_NOT enforcement |
| PIN-292 | Governance orchestrator design |
| PIN-296 | Rollout projection service |
| GAP-019 | Alert-log linking |
| GAP-056 | Knowledge plane model |
| GAP-071-082 | Lifecycle stages |
| GAP-083-085 | Knowledge SDK |
| GAP-159-161 | Execution engines |
| GAP-172 | Connection pool management |
