# Overview — Software Bible

**Domain:** overview  
**L2 Features:** 5  
**Scripts:** 2  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-12, Wave-4 Script Coverage Audit)

- Wave-4 target-scope classification for overview is complete:
- `5` scripts total (`2 UC_LINKED`, `3 NON_UC_SUPPORT`, `0 UNLINKED` in target scope).
- UC-linked overview scripts are mapped to `UC-001` in canonical linkage docs.
- Deterministic gates remain clean post-wave and governance suite reports `308` passing tests.
- Audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_AUDIT_2026-02-12.md`

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| overview_facade | L5 | `OverviewFacade.get_decisions` | CANONICAL | 8 | ?:overview | ?:overview_facade | L5:__init__ | L4:operation_registry | L4:overview_handler | YES |
| overview_facade_driver | L6 | `OverviewFacadeDriver.fetch_breach_counts` | LEAF | 0 | L6:__init__ | L5:overview_facade, overview_facade | YES |

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 5 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### GET /costs
```
L2:overview.get_costs → L4:OperationContext | get_operation_registry → L6:overview_facade_driver.OverviewFacadeDriver.fetch_breach_counts
```

#### GET /decisions
```
L2:overview.get_decisions → L4:OperationContext | get_operation_registry → L6:overview_facade_driver.OverviewFacadeDriver.fetch_breach_counts
```

#### GET /decisions/count
```
L2:overview.get_decisions_count → L4:OperationContext | get_operation_registry → L6:overview_facade_driver.OverviewFacadeDriver.fetch_breach_counts
```

#### GET /highlights
```
L2:overview.get_highlights → L4:OperationContext | get_operation_registry → L6:overview_facade_driver.OverviewFacadeDriver.fetch_breach_counts
```

#### GET /recovery-stats
```
L2:overview.get_recovery_stats → L4:OperationContext | get_operation_registry → L6:overview_facade_driver.OverviewFacadeDriver.fetch_breach_counts
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `OverviewFacade.get_costs` | overview_facade | SUPERSET | 2 | 9 | no | overview_facade_driver:OverviewFacadeDriver.fetch_breach_sta |
| `OverviewFacade.get_decisions` | overview_facade | CANONICAL | 8 | 11 | no | overview_facade_driver:OverviewFacadeDriver.fetch_pending_in |
| `OverviewFacade.get_highlights` | overview_facade | SUPERSET | 2 | 14 | no | overview_facade_driver:OverviewFacadeDriver.fetch_breach_cou |

## Wrapper Inventory

_10 thin delegation functions._

- `overview_facade.CostPeriod.to_dict` → ?
- `overview_facade.CostsResult.to_dict` → overview_facade:CostPeriod.to_dict
- `overview_facade.DecisionItem.to_dict` → ?
- `overview_facade.DecisionsCountResult.to_dict` → ?
- `overview_facade.DecisionsResult.to_dict` → overview_facade:CostPeriod.to_dict
- `overview_facade.DomainCount.to_dict` → ?
- `overview_facade.LimitCostItem.to_dict` → ?
- `overview_facade.OverviewFacade.__init__` → ?
- `overview_facade.RecoveryStatsResult.to_dict` → overview_facade:CostPeriod.to_dict
- `overview_facade.SystemPulse.to_dict` → ?

---

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `overview_handler.py` | `OverviewQueryHandler`: Replaced `getattr()` dispatch with explicit map (5 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Topology Completion & Hygiene (2026-02-01)

Cross-cutting changes spanning multiple domains. Per-domain details in each domain's SOFTWARE_BIBLE.md.

### Phase 4 — Unused Code Audit Tooling

| Artifact | Purpose | Reference |
|----------|---------|-----------|
| `literature/hoc_domain/UNUSED_CODE_AUDIT.csv` | 202 entries across hoc/cus/* (scope: Phase 7). Sub-typed: UNWIRED_FACTORY, UNWIRED_SCHEDULED, UNWIRED_CORE_LOGIC, UNWIRED_TEST_UTIL, RESOLVED, FALSE_POSITIVE. Renamed from DEAD_CODE_AUDIT.csv (Phase 7). | PIN-513 Phase 4+7 |
| CI check 26: `check_no_l3_adapters_references` | Scans `hoc/cus/` Python files for non-comment references to `L3_adapters` → CI fail. Added to `check_init_hygiene.py`. | PIN-513 Phase 4 |

### Phase 5 — Scripts Metadata Standardization

| Artifact | Purpose | Reference |
|----------|---------|-----------|
| **NEW** `scripts/ops/add_metadata_headers.py` | Bulk script to add standard `# Layer: L8` metadata headers to scripts. Applied to 129 scripts achieving 100% coverage. | PIN-513 Phase 5A |
| **NEW** `scripts/ci/intent_check_common.py` | Shared `IntentRegression` dataclass and `extract_intent_values()` AST function. Extracted from `check_priority4_intent.py` / `check_priority5_intent.py`. | PIN-513 Phase 5B |
| **NEW** `scripts/lib/ci_guard_base.py` | `GuardViolation`, `GuardResult`, `create_guard_parser()`, `report_result()`. Shared CI guard infrastructure for `--ci`, `--json`, `--summary` flag handling and exit code conventions. | PIN-513 Phase 5C |
| **NEW** `scripts/lib/__init__.py` | Package marker for shared CI/ops script libraries. | PIN-513 Phase 5C |
