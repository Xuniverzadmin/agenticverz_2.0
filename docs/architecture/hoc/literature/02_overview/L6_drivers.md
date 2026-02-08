# Overview — L6 Drivers (1 files)

**Domain:** overview  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## overview_facade_driver.py
**Path:** `backend/app/hoc/cus/overview/L6_drivers/overview_facade_driver.py`  
**Layer:** L6_drivers | **Domain:** overview | **Lines:** 517

**Docstring:** Overview Facade Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentCountSnapshot` |  | Raw incident count data from DB. |
| `ProposalCountSnapshot` |  | Raw policy proposal count data from DB. |
| `BreachCountSnapshot` |  | Raw limit breach count data from DB. |
| `RunCountSnapshot` |  | Raw worker run count data from DB. |
| `AuditCountSnapshot` |  | Raw audit count data from DB. |
| `IncidentSnapshot` |  | Snapshot of a single incident for decisions projection. |
| `ProposalSnapshot` |  | Snapshot of a single policy proposal for decisions projection. |
| `LimitSnapshot` |  | Snapshot of a single limit for cost projection. |
| `RunCostSnapshot` |  | Snapshot of run cost data from DB. |
| `BreachStatsSnapshot` |  | Snapshot of breach statistics from DB. |
| `IncidentDecisionCountSnapshot` |  | Snapshot of incident counts by severity for decisions count. |
| `RecoverySnapshot` |  | Snapshot of incident recovery data from DB. |
| `OverviewFacadeDriver` | fetch_incident_counts, fetch_proposal_counts, fetch_breach_counts, fetch_run_counts, fetch_last_activity, fetch_pending_incidents, fetch_pending_proposals, fetch_run_cost (+5 more) | Overview Facade Driver - Pure data access layer. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, List, Optional | no |
| `sqlalchemy` | and_, case, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.audit_ledger` | AuditLedger | no |
| `app.models.killswitch` | Incident, IncidentLifecycleState | no |
| `app.models.policy` | PolicyProposal | no |
| `app.models.policy_control_plane` | Limit, LimitBreach, LimitCategory | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`OverviewFacadeDriver`, `IncidentCountSnapshot`, `ProposalCountSnapshot`, `BreachCountSnapshot`, `RunCountSnapshot`, `AuditCountSnapshot`, `IncidentSnapshot`, `ProposalSnapshot`, `LimitSnapshot`, `RunCostSnapshot`, `BreachStatsSnapshot`, `IncidentDecisionCountSnapshot`, `RecoverySnapshot`

---
