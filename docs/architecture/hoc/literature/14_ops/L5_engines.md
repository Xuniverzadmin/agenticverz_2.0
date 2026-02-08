# Ops — L5 Engines (1 files)

**Domain:** ops  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## cost_ops_engine.py
**Path:** `backend/app/hoc/cus/ops/L5_engines/cost_ops_engine.py`  
**Layer:** L5_engines | **Domain:** ops | **Lines:** 644

**Docstring:** Cost Ops Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostReadDriverPort` | fetch_global_spend_summary, fetch_anomaly_summary, fetch_largest_deviation, fetch_last_snapshot_time, fetch_daily_cost_series, fetch_anomalies, fetch_tenant_cost_rollup, fetch_distinct_tenant_count (+12 more) |  |
| `CostOverviewResult` |  | Global cost overview. |
| `AnomalyItem` |  | Single anomaly item. |
| `CostAnomalyListResult` |  | Anomaly list result. |
| `TenantCostItem` |  | Single tenant cost item. |
| `CostTenantListResult` |  | Tenant list result. |
| `DailyBreakdownItem` |  | Daily cost breakdown item. |
| `FeatureCostItem` |  | Cost by feature item. |
| `UserCostItem` |  | Cost by user item. |
| `ModelCostItem` |  | Cost by model item. |
| `AnomalyHistoryItem` |  | Anomaly history item. |
| `CustomerDrilldownResult` |  | Customer cost drilldown result. |
| `CostOpsEngine` | get_overview, get_anomalies, get_tenants, get_customer_drilldown | L5 Engine for founder cost intelligence. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_compute_snapshot_status` | `(last_snapshot_at: datetime | None) -> tuple[int, str]` | no | Compute snapshot freshness status. |
| `_compute_trend` | `(daily_costs: list[float]) -> str` | no | Compute trend from daily cost values. |
| `get_cost_ops_engine` | `() -> CostOpsEngine` | no | Get the CostOpsEngine singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Protocol | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---
