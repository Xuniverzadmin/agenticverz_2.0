# Analytics — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/analytics.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/analytics/` (4 files)
         ├── costsim.py
         ├── feedback.py
         ├── predictions.py
         ├── scenarios.py
         │
         └──→ L3 Adapters (2 files)
                ├── alert_delivery.py ✅
                ├── v2_adapter.py ✅
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (20 files)
                       ├── ai_console_panel_engine.py → L6 ❌ (no matching driver)
                       ├── analytics_facade.py → L6 ✅
                       ├── canary.py → L6 ❌ (no matching driver)
                       ├── config.py → L6 ❌ (no matching driver)
                       ├── coordinator.py → L6 ❌ (no matching driver)
                       ├── cost_anomaly_detector.py → L6 ❌ (no matching driver)
                       ├── cost_model_engine.py → L6 ❌ (no matching driver)
                       ├── cost_snapshots.py → L6 ❌ (no matching driver)
                       ├── cost_write_engine.py → L6 ✅
                       ├── costsim_models.py → L6 ❌ (no matching driver)
                       └── ... (+10 more)
                     L5 Schemas (1 files)
                       │
                       └──→ L6 Drivers (8 files)
                              ├── analytics_read_driver.py
                              ├── audit_persistence.py
                              ├── cost_anomaly_driver.py
                              ├── cost_write_driver.py
                              ├── leader.py
                              ├── pattern_detection_driver.py
                              ├── prediction_driver.py
                              ├── provenance_async.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 4 L2 routers | Build hoc/api/facades/cus/analytics.py grouping: costsim.py, feedback.py, predictions.py, scenarios.py |
| L6_driver | coordinator.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/analytics/L6_drivers/coordinator.py_driver.py |
| L6_driver | cost_anomaly_detector.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/analytics/L6_drivers/cost_anomaly_detector.py_driver.py |
| L6_driver | cost_snapshots.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/analytics/L6_drivers/cost_snapshots.py_driver.py |
| L6_driver | pattern_detection.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/analytics/L6_drivers/pattern_detection.py_driver.py |
| L6_driver | prediction.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/analytics/L6_drivers/prediction.py_driver.py |
| L7_models | 8 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `coordinator.py` | `from sqlmodel import Session` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver |
| `cost_anomaly_detector.py` | `from sqlmodel import Session, select` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver |
| `cost_anomaly_detector.py` | `from app.db import CostAnomaly, CostBudget, utc_now` | L5 MUST NOT access DB directly | Use L6 driver for DB access |
| `cost_snapshots.py` | `from sqlalchemy.ext.asyncio import AsyncSession` | L5 MUST NOT import sqlalchemy | Move DB logic to L6 driver |
| `pattern_detection.py` | `from app.db import get_async_session` | L5 MUST NOT access DB directly | Use L6 driver for DB access |
| `pattern_detection.py` | `from app.models.feedback import PatternFeedbackCreate` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `prediction.py` | `from app.db import get_async_session` | L5 MUST NOT access DB directly | Use L6 driver for DB access |
