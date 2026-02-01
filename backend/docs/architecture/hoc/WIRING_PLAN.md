# HOC WIRING PLAN: SWEEP-03 & BEYOND

**Document Status**: ACTIVE PLANNING (Batch 4–5 in progress)
**Last Updated**: 2026-02-01
**Owner**: Architecture Governance
**Reference**: PIN-513 (HOC Layer Topology Completion & Hygiene)

---

## Executive Summary

This document provides a unified view of HOC module migration progress and future sweeps. SWEEP-03 is the primary modernization effort, reducing non-HOC modules by systematically migrating 12 legacy `app.services.*` imports into HOC-conformant L5 engines.

**Current Status**: SWEEP-03 Batches 1–3 COMPLETE; Batch 4 PENDING; Batch 5 CONDITIONAL PLANNING

---

## Table of Contents

1. [SWEEP-03 Overview & Batches](#sweep-03-overview--batches)
2. [Module Migration Status](#module-migration-status)
3. [Batch Timeline](#batch-timeline)
4. [Governance Invariant](#governance-invariant)
5. [CI Enforcement (PIN-512)](#ci-enforcement-pin-512)
6. [Future Sweeps (SWEEP-04+)](#future-sweeps-sweep-04)
7. [Audience Boundaries](#audience-boundaries)
8. [Known Issues & Debt](#known-issues--debt)

---

## SWEEP-03 Overview & Batches

### Purpose

SWEEP-03 eliminates the `MISSING_HOC_MODULE` metric by ensuring every non-deprecated symbol imported by ≥1 HOC file has an explicit HOC module with a documented contract.

### Invariant (LOCKED)

> **Every non-deprecated symbol imported by ≥1 HOC file must have a HOC module with an explicit contract.**

This invariant is **constant** across all four batches and applies perpetually going forward.

### Batches at a Glance

| Batch | Status | Modules | Effort | MISSING_HOC_MODULE |
|-------|--------|---------|--------|-------------------|
| 1 | CLOSED | 3 | 3–5d | 10 → 7 |
| 2 | CLOSED | 3 | 3–5d | 7 → 4 |
| 3 | CLOSED | 3 | 3–5d | 4 → 1 |
| **4** | PENDING | 1 | 2–3d | 1 → 0 |
| **5** | PLANNING | 5–8 | 12–15d | 0 (consolidation) |

**Total Effort**: ~25–35 days (Batch 4–5 remaining)

---

## Module Migration Status

### All 12 Modules (SWEEP-03 Scope)

| Order | Module | Batch | Status | HOC Location | Source |
|-------|--------|-------|--------|--------------|--------|
| 1 | LimitEnforcer | 1 | ✅ CLOSED | `int/policies/L5_engines/limit_enforcer.py` | NEW (GAP-055) |
| 2 | UsageMonitor | 1 | ✅ CLOSED | `int/policies/L5_engines/usage_monitor.py` | NEW (GAP-053) |
| 3 | RunSignalService | 1 | ✅ CLOSED | `cus/activity/L6_drivers/run_signal_service.py` | NEW |
| 4 | LimitsSimulationService | 2 | ✅ CLOSED | `cus/policies/L5_engines/limits_simulation_service.py` | Wrapper |
| 5 | CusEnforcementService | 2 | ✅ CLOSED | `cus/policies/L5_engines/cus_enforcement_service.py` | Wrapper |
| 6 | CusTelemetryService | 2 | ✅ CLOSED | `cus/activity/L5_engines/cus_telemetry_service.py` | Wrapper |
| 7 | CusIntegrationService | 3 | ✅ CLOSED | `cus/integrations/L5_engines/cus_integration_service.py` | Wrapper |
| 8 | PoliciesFacade | 3 | ✅ CLOSED | `cus/policies/L5_engines/policies_facade.py` | Wrapper |
| 9 | AuditLedgerService | 3 | ✅ CLOSED | `cus/logs/L5_engines/audit_ledger_service.py` | NEW |
| 10 | **PlatformHealthService** | **4** | **PENDING** | `int/platform/L5_engines/platform_health_service.py` | Wrapper |
| 11 | [Phase 1 Consolidation] | 5 | PLANNING | [Re-exports] | Consolidation |
| 12 | [Phase 2+ Audits] | 5 | PLANNING | [Housekeeping] | Governance |

---

## Batch Timeline

### Completed Batches

#### Batch 1: Missing Module Creation (CLOSED 2026-01-25)

**Modules**: LimitEnforcer, UsageMonitor, RunSignalService  
**Metric**: 10 → 7 MISSING_HOC_MODULE  
**Delivery**: Minimal contracts + stubs  

**Lock Document**: `SWEEP_03_MISSING_MODULE_CREATION.md`

---

#### Batch 2: Service Migration (CLOSED 2026-01-25)

**Modules**: LimitsSimulationService, CusEnforcementService, CusTelemetryService  
**Metric**: 7 → 4 MISSING_HOC_MODULE  
**Delivery**: Re-export wrappers from legacy `app.services.*`  

**Lock Document**: `SWEEP_03_BATCH_2_LOCK.md`

---

#### Batch 3: Legacy Service Consolidation (CLOSED 2026-01-25)

**Modules**: CusIntegrationService, PoliciesFacade, AuditLedgerService  
**Metric**: 4 → 1 MISSING_HOC_MODULE  
**Delivery**: Re-export wrappers + new sync implementations  

**Lock Document**: `SWEEP_03_BATCH_3_LOCK.md`

---

### Pending Batches

#### Batch 4: Final Module Migration (PENDING 2026-02-01)

**Module**: PlatformHealthService (L4 orchestrator)  
**Metric**: 1 → 0 MISSING_HOC_MODULE (SWEEP-03 COMPLETE)  
**Timeline**: 2026-02-01 → 2026-02-06 (estimated 3–5 days)  
**Delivery**: Platform health orchestration in HOC  

**Lock Document**: `SWEEP_03_BATCH_4_LOCK.md`

**Key Points**:
- Audience: INTERNAL (founder/admin ops)
- Callers: platform_eligibility_adapter (INTERNAL)
- Risk: LOW
- Requires validation gate before execution

**Blockers**:
- None; all prerequisites completed (Batch 1–3)

---

#### Batch 5: Post-Sweep Consolidation (CONDITIONAL PLANNING)

**Phases**:
1. **Phase 1**: Re-export wrapper consolidation (5–7 days)
2. **Phase 2**: Dead code audit of orphaned modules (2–3 days)
3. **Phase 3**: Cross-domain dependency review (2–3 days)
4. **Phase 4**: hoc_spine governance verification (1–2 days)

**Metric**: Consolidation + hygiene (MISSING_HOC_MODULE remains 0)  
**Timeline**: 2026-02-08 → 2026-02-24 (estimated 12–15 days after Batch 4)  
**Delivery**: Clean, consolidated HOC layer ready for SWEEP-04  

**Planning Document**: `SWEEP_03_BATCH_5_PLANNING.md`

**Critical Dependency**: Batch 5 ONLY starts AFTER:
- Batch 4 verified complete (MISSING_HOC_MODULE = 0)
- All 26 CI checks passing
- SWEEP_03_COMPLETION_REPORT.md approved

---

## Governance Invariant

### Core Rule

> **Every non-deprecated symbol imported by ≥1 HOC file must have a HOC module with an explicit contract.**

### Implications

1. **No orphaned imports**: If HOC imports from legacy `app.services.*`, that symbol must have a HOC module
2. **Explicit contracts**: Every HOC module must document its interface, inputs, outputs, dependencies
3. **No silent shims**: Re-export wrappers must be documented with `# PIN-513 Phase X (Batch Y)` comments
4. **Perpetual compliance**: New HOC code added must follow this invariant immediately

### Enforcement

- **Scan tool**: `scripts/ops/layer_validator.py --backend --ci` (26 checks total)
- **CI gate**: check_init_hygiene.py fails if invariant violated
- **Manual review**: Every batch requires human validation gate

---

## CI Enforcement (PIN-512)

### Check 24: Tombstone Expiry (check_tombstone_expiry)

**Rule**: Any file with `# TOMBSTONE_EXPIRY: YYYY-MM-DD` where date < today → CI fail

**Status**: ACTIVE  
**Applies to**: `app/services/**/*.py` (after Batch 5 Phase 2)  
**Purpose**: Force cleanup of deprecated modules by expiry date  

**Example**:
```python
# TOMBSTONE_EXPIRY: 2026-05-01
# Replacement: app.hoc.cus.policies.L5_engines.limits_simulation_service
# Issue: PIN-513 Phase 8 (Batch 5)
```

---

### Check 25: L5 Database Restrictions (check_l5_no_db_module_imports)

**Rule**: L5 engines importing `sqlalchemy`, `sqlmodel`, `asyncpg`, `psycopg` → CI fail

**Status**: ACTIVE  
**Applies to**: `app/hoc/cus/*/L5_engines/**/*.py`  
**Allowlist**: 
- `app/hoc/cus/policies/L5_engines/engine.py` (frozen, special case)
- `app/hoc/cus/integrations/L5_engines/sql_gateway.py` (frozen, special case)

**Purpose**: Enforce L6 driver layer for database operations  

---

### Check 26: L3 Adapter References (check_no_l3_adapters_references)

**Rule**: Any non-comment reference to `L3_adapters` in `hoc/cus/` Python files → CI fail

**Status**: ACTIVE  
**Applies to**: `app/hoc/cus/**/*.py`  
**Purpose**: Enforce PIN-513 (L3 abolished, moved to hoc_spine)  

---

### Running All 26 Checks

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
```

**Expected output (all 26 checks)**: See `docs/governance/CHECK_INIT_HYGIENE_REFERENCE.md`

---

## Audience Boundaries

### Classification

| Audience | Definition | HOC Domain |
|----------|-----------|-----------|
| **CUSTOMER** | Customer-facing (SDK, APIs, Console) | `cus/*` (customer domains) |
| **FOUNDER** | Founder/admin-only ops | `fdr/*` + (founder logic) |
| **INTERNAL** | Infrastructure (workers, adapters) | `int/*` (internal) |
| **SHARED** | Shared utilities (logging, types) | `hoc_spine/shared/**` |

### Enforcement

- **Tool**: `python3 scripts/ops/audience_guard.py --ci`
- **Rule**: CUSTOMER code NEVER imports FOUNDER code
- **Header requirement**: Every file must declare audience in first 50 lines

**Example Header**:
```python
# Layer: L5_engines
# AUDIENCE: CUSTOMER
# Role: Policy enforcement engine for customer limits
```

### Current Status (Post-Batch 3)

- ✅ All 9 migrated modules have proper audience headers
- ✅ No CUSTOMER→FOUNDER violations
- ✅ platform_eligibility_adapter marked INTERNAL (Batch 4 prerequisite)

---

## Known Issues & Debt

### Resolved (Batches 1–3)

| Issue | Resolution | Status |
|-------|-----------|--------|
| GAP-055: LimitEnforcer | Created in Batch 1 | ✅ CLOSED |
| GAP-053: UsageMonitor | Created in Batch 1 | ✅ CLOSED |
| app.services imports in HOC | Migrated 9/10 modules | 90% COMPLETE |
| L3 references | Removed (PIN-513 Phase 3) | ✅ CLOSED |

### Remaining (Batch 4–5)

| Issue | Owner | Status | Due |
|-------|-------|--------|-----|
| PlatformHealthService migration | Batch 4 | PENDING | 2026-02-06 |
| Re-export wrapper consolidation | Batch 5 Phase 1 | PLANNING | 2026-02-14 |
| Dead code audit (tombstones) | Batch 5 Phase 2 | PLANNING | 2026-02-17 |
| Cross-domain coupling audit | Batch 5 Phase 3 | PLANNING | 2026-02-20 |
| hoc_spine governance audit | Batch 5 Phase 4 | PLANNING | 2026-02-22 |

### Legacy Debt Tolerated (PIN-438)

**BLCA Status**: Backend layer compliance audit tolerates 2 categories of violations:
1. **New violations**: BLOCKED (CI fails)
2. **Pre-existing violations**: TOLERATED (tracked in PYTHON_EXECUTION_CONTRACT.md)

**No action required** on legacy violations during SWEEP-03.

---

## Future Sweeps (SWEEP-04+)

### SWEEP-04: Authority Rules & Orchestration (POST-BATCH-5)

**Scope**: Define TIME, TX, and failure jurisdiction semantics across HOC layers

**Key Activities**:
- Async execution semantics (runbooks, timeouts, retries)
- Transaction boundaries (multi-domain ACID vs. saga)
- Failure propagation (who decides what to do on error)
- Cross-domain orchestration protocols

**Prerequisite**: Batch 5 Phase 4 (hoc_spine governance audit) complete

**Estimated Duration**: 8–10 days

---

### SWEEP-05: Performance & Observability (POST-SWEEP-04)

**Scope**: HOC-aware metrics, tracing, caching, and performance baselines

**Key Activities**:
- End-to-end request tracing (L2 → L4 → L5 → L6 → L7)
- Per-layer caching strategy
- Metrics collection per domain and layer
- Performance baseline establishment

**Estimated Duration**: 10–12 days

---

### SWEEP-06: Adapter Layer Consolidation (POST-SWEEP-05)

**Scope**: Formalize and reduce app/adapters/** surface

**Key Activities**:
- Audit all adapters for HOC eligibility
- Move adapter logic into HOC where possible
- Formalize remaining adapter→HOC wiring
- Strengthen boundary enforcement

**Estimated Duration**: 8–10 days

---

## Batch 4 Execution Checklist

### Pre-Execution (Validation)

Before beginning Batch 4, verify:

- [ ] SWEEP_03_BATCH_3_LOCK.md marked CLOSED
- [ ] All 3 Batch 3 modules migrated and callers wired
- [ ] All 26 CI checks passing
- [ ] MISSING_HOC_MODULE = 1 confirmed
- [ ] PlatformHealthService identified as sole remaining module

### Execution

- [ ] Create HOC implementation at `app/hoc/int/platform/L5_engines/platform_health_service.py`
- [ ] Define explicit contract (interface, inputs, outputs, dependencies)
- [ ] Wire platform_eligibility_adapter to import from new location
- [ ] Verify no new `app.services.platform.*` imports in HOC
- [ ] All 26 CI checks pass

### Post-Execution (Closure)

- [ ] Create SWEEP_03_COMPLETION_REPORT.md
- [ ] Document all 12 migrated modules (1–12)
- [ ] Summarize metrics: 12/12 modules, MISSING_HOC_MODULE = 0
- [ ] Approval gate: "Batch 4 verified complete. Batch 5 planning approved."

---

## Batch 5 Execution Checklist (Conditional)

### Pre-Phase-1 (Batch 4 closure verification)

- [ ] Batch 4 CLOSED (MISSING_HOC_MODULE = 0)
- [ ] SWEEP_03_COMPLETION_REPORT.md approved
- [ ] All 26 CI checks passing
- [ ] No new app.services imports detected in HOC

### Phase 1: Wrapper Consolidation

- [ ] Pre-consolidation dependency scan (15 min)
- [ ] For each of 5 wrappers: READ → DOCUMENT → CREATE native → MIGRATE
- [ ] No behavior drift detected
- [ ] Bridge re-exports added (historical tracking)

### Phase 2: Dead Code Audit

- [ ] Scan app.services/** for remaining dependencies (30 min)
- [ ] Add TOMBSTONE_EXPIRY headers to orphaned modules (90-day window)
- [ ] Create app/services/DEPRECATION_MANIFEST.md
- [ ] Verify no deletions (marking only)

### Phase 3: Cross-Domain Review

- [ ] Extract all cross-domain imports in HOC (30 min)
- [ ] Classify as LEGITIMATE (hoc_spine) or ILLEGITIMATE (L5→L5)
- [ ] Document illegitimate couplings
- [ ] Create cross-domain coupling report

### Phase 4: hoc_spine Governance

- [ ] Verify hoc_spine imports only from L5 engines
- [ ] Verify no cross-domain imports (except bridges)
- [ ] Verify orchestration-only logic
- [ ] Document cross-domain protocols

### Post-Phase-4 (Closure)

- [ ] Create SWEEP_03_BATCH_5_COMPLETION_REPORT.md
- [ ] All 26 CI checks passing
- [ ] audience_guard.py: 0 violations
- [ ] SWEEP-03 officially CLOSED
- [ ] Approval gate: "Batch 5 complete. Ready for SWEEP-04 planning."

---

## Quick Reference

### Commands

```bash
# BLCA: All 26 checks
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci

# Layer validation
python3 scripts/ops/layer_validator.py --backend --ci

# Audience guard
python3 scripts/ops/audience_guard.py --ci

# Find missing HOC modules (pre-Batch 4)
grep -r "from app.services" app/hoc --include="*.py" | grep -v "__pycache__"

# Find app.services imports in HOC (post-Batch 3, should be only PlatformHealthService)
grep -r "from app.services" app/hoc --include="*.py" | grep -v "__pycache__" | wc -l
```

### Documents

| Document | Purpose | Scope |
|----------|---------|-------|
| SWEEP_03_MISSING_MODULE_CREATION.md | Batch 1 lock | 3 modules, 10 → 7 |
| SWEEP_03_BATCH_2_LOCK.md | Batch 2 lock | 3 modules, 7 → 4 |
| SWEEP_03_BATCH_3_LOCK.md | Batch 3 lock | 3 modules, 4 → 1 |
| SWEEP_03_BATCH_4_LOCK.md | Batch 4 lock | 1 module, 1 → 0 |
| SWEEP_03_BATCH_5_PLANNING.md | Batch 5 planning | Consolidation + hygiene |
| WIRING_PLAN.md | This document | Full overview |

---

## References

| Reference | Document | Location |
|-----------|----------|----------|
| PIN-513 | Topology Completion & Hygiene | docs/memory-pins/ |
| PIN-512 | CI Guards (Checks 24–26) | docs/memory-pins/ |
| PIN-511 | Legacy services boundary | docs/memory-pins/ |
| PIN-484 | HOC Layer Topology V2.0.0 | docs/architecture/topology/ |
| HOC_LAYER_TOPOLOGY_V2.0.0.md | 6-layer spec | docs/architecture/topology/ |

---

## Approval Gates Summary

| Batch | Gate | Signoff Phrase | Owner |
|-------|------|---|-------|
| 4 | Execution | "Sweep-03 Batch-4 lock validated. Begin execution." | Human |
| 4 | Closure | "Batch 4 verified complete. Batch 5 planning approved." | QA + Architecture |
| 5 (Phase 1) | Start | "Batch 5 Phase 1 consolidation approved." | Architecture |
| 5 (Phase 2) | Start | "Tombstone expiry headers approved." | Governance |
| 5 (Completion) | Closure | "Batch 5 complete. Ready for SWEEP-04 planning." | QA + Architecture |

---

## Document History

| Date | Version | Author | Change |
|------|---------|--------|--------|
| 2026-01-25 | 1.0 | Governance | Initial Batch 1–3 summary |
| 2026-02-01 | 2.0 | Governance | Added Batch 4 lock + Batch 5 planning |
| 2026-02-01 | 2.1 | Governance | Unified WIRING_PLAN.md |

---

## Contact & Questions

- **Architecture Governance**: PIN-513 owner
- **Batch 4 Lead**: TBD (PlatformHealthService)
- **Batch 5 Lead**: TBD (Consolidation)

---

**Last Reviewed**: 2026-02-01  
**Next Review**: After Batch 4 closure (estimated 2026-02-07)

