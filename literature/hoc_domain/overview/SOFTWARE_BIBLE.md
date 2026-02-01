# Overview — Software Bible

**Domain:** overview  
**L2 Features:** 5  
**Scripts:** 2  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

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
