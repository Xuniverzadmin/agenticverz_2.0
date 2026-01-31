# Overview — Call Graph

**Domain:** overview  
**Total functions:** 30  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 1 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 2 | Calls other functions + adds its own decisions |
| WRAPPER | 10 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 14 | Terminal — calls no other domain functions |
| ENTRY | 2 | Entry point — no domain-internal callers |
| INTERNAL | 1 | Called only by other domain functions |

## Canonical Algorithm Owners

### `overview_facade.OverviewFacade.get_decisions`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 11
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** overview_facade.OverviewFacade.get_decisions → overview_facade_driver.OverviewFacadeDriver.fetch_pending_incidents → overview_facade_driver.OverviewFacadeDriver.fetch_pending_proposals
- **Calls:** overview_facade_driver:OverviewFacadeDriver.fetch_pending_incidents, overview_facade_driver:OverviewFacadeDriver.fetch_pending_proposals

## Supersets (orchestrating functions)

### `overview_facade.OverviewFacade.get_costs`
- **Decisions:** 2, **Statements:** 9
- **Subsumes:** overview_facade_driver:OverviewFacadeDriver.fetch_breach_stats, overview_facade_driver:OverviewFacadeDriver.fetch_budget_limits, overview_facade_driver:OverviewFacadeDriver.fetch_run_cost

### `overview_facade.OverviewFacade.get_highlights`
- **Decisions:** 2, **Statements:** 14
- **Subsumes:** overview_facade_driver:OverviewFacadeDriver.fetch_breach_counts, overview_facade_driver:OverviewFacadeDriver.fetch_incident_counts, overview_facade_driver:OverviewFacadeDriver.fetch_last_activity, overview_facade_driver:OverviewFacadeDriver.fetch_proposal_counts, overview_facade_driver:OverviewFacadeDriver.fetch_run_counts

## Wrappers (thin delegation)

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

## Full Call Graph

```
[WRAPPER] overview_facade.CostPeriod.to_dict
[WRAPPER] overview_facade.CostsResult.to_dict → overview_facade:CostPeriod.to_dict, overview_facade:DecisionItem.to_dict, overview_facade:DecisionsCountResult.to_dict, overview_facade:DecisionsResult.to_dict, overview_facade:DomainCount.to_dict, ...+4
[WRAPPER] overview_facade.DecisionItem.to_dict
[WRAPPER] overview_facade.DecisionsCountResult.to_dict
[WRAPPER] overview_facade.DecisionsResult.to_dict → overview_facade:CostPeriod.to_dict, overview_facade:CostsResult.to_dict, overview_facade:DecisionItem.to_dict, overview_facade:DecisionsCountResult.to_dict, overview_facade:DomainCount.to_dict, ...+4
[WRAPPER] overview_facade.DomainCount.to_dict
[INTERNAL] overview_facade.HighlightsResult.to_dict → overview_facade:CostPeriod.to_dict, overview_facade:CostsResult.to_dict, overview_facade:DecisionItem.to_dict, overview_facade:DecisionsCountResult.to_dict, overview_facade:DecisionsResult.to_dict, ...+4
[WRAPPER] overview_facade.LimitCostItem.to_dict
[WRAPPER] overview_facade.OverviewFacade.__init__
[SUPERSET] overview_facade.OverviewFacade.get_costs → overview_facade_driver:OverviewFacadeDriver.fetch_breach_stats, overview_facade_driver:OverviewFacadeDriver.fetch_budget_limits, overview_facade_driver:OverviewFacadeDriver.fetch_run_cost
[CANONICAL] overview_facade.OverviewFacade.get_decisions → overview_facade_driver:OverviewFacadeDriver.fetch_pending_incidents, overview_facade_driver:OverviewFacadeDriver.fetch_pending_proposals
[ENTRY] overview_facade.OverviewFacade.get_decisions_count → overview_facade_driver:OverviewFacadeDriver.fetch_incident_decision_counts, overview_facade_driver:OverviewFacadeDriver.fetch_proposal_count
[SUPERSET] overview_facade.OverviewFacade.get_highlights → overview_facade_driver:OverviewFacadeDriver.fetch_breach_counts, overview_facade_driver:OverviewFacadeDriver.fetch_incident_counts, overview_facade_driver:OverviewFacadeDriver.fetch_last_activity, overview_facade_driver:OverviewFacadeDriver.fetch_proposal_counts, overview_facade_driver:OverviewFacadeDriver.fetch_run_counts
[ENTRY] overview_facade.OverviewFacade.get_recovery_stats → overview_facade_driver:OverviewFacadeDriver.fetch_recovery_stats
[WRAPPER] overview_facade.RecoveryStatsResult.to_dict → overview_facade:CostPeriod.to_dict, overview_facade:CostsResult.to_dict, overview_facade:DecisionItem.to_dict, overview_facade:DecisionsCountResult.to_dict, overview_facade:DecisionsResult.to_dict, ...+4
[WRAPPER] overview_facade.SystemPulse.to_dict
[LEAF] overview_facade.get_overview_facade
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_breach_counts
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_breach_stats
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_budget_limits
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_incident_counts
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_incident_decision_counts
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_last_activity
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_pending_incidents
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_pending_proposals
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_proposal_count
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_proposal_counts
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_recovery_stats
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_run_cost
[LEAF] overview_facade_driver.OverviewFacadeDriver.fetch_run_counts
```
