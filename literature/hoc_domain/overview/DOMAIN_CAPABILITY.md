# Overview — Domain Capability

**Domain:** overview  
**Total functions:** 30  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for overview is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/overview/overview_fac.py
- L2 public boundary module for domain-scoped facade entry is present at:
- backend/app/hoc/api/cus/overview/overview_public.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> overview_public.py -> L4 registry.execute(...)
- Current status: overview_public.py now implements `GET /cus/overview/highlights` read facade with strict boundary validation, one-dispatch mapping to `overview.query`, and trace/meta propagation; existing domain routers remain active during incremental rollout.

## 1. Domain Purpose

Customer dashboard overview — aggregated health status, key metrics, and quick-access navigation across all domains.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `CostPeriod.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `CostsResult.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `DecisionItem.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `DecisionsCountResult.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `DecisionsResult.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `DomainCount.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `HighlightsResult.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `LimitCostItem.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `OverviewFacade.get_costs` | overview_facade | Yes | L4:operation_registry | pure |
| `OverviewFacade.get_decisions` | overview_facade | Yes | L4:operation_registry | pure |
| `OverviewFacade.get_decisions_count` | overview_facade | Yes | L4:operation_registry | pure |
| `OverviewFacade.get_highlights` | overview_facade | Yes | L4:operation_registry | pure |
| `OverviewFacade.get_recovery_stats` | overview_facade | Yes | L4:operation_registry | pure |
| `RecoveryStatsResult.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `SystemPulse.to_dict` | overview_facade | Yes | L4:operation_registry | pure |
| `get_overview_facade` | overview_facade | Yes | L4:operation_registry | pure |

## 3. Internal Functions

### Helpers

_1 internal helper functions._

- **overview_facade:** `OverviewFacade.__init__`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `OverviewFacadeDriver.fetch_breach_counts` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_breach_stats` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_budget_limits` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_incident_counts` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_incident_decision_counts` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_last_activity` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_pending_incidents` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_pending_proposals` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_proposal_count` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_proposal_counts` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_recovery_stats` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_run_cost` | overview_facade_driver | db_write |
| `OverviewFacadeDriver.fetch_run_counts` | overview_facade_driver | db_write |

## 4. Explicit Non-Features

_No explicit non-feature declarations found in OVERVIEW_DOMAIN_LOCK_FINAL.md._
