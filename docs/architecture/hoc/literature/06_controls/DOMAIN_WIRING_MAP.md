# Controls — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/controls.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/controls/` — **GAP** (0 files)
         │
         └──→ L3 Adapters (1 files)
                ├── customer_killswitch_adapter.py ✅
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (9 files)
                       ├── alert_fatigue.py → L6 ❌ (no matching driver)
                       ├── budget_enforcement_engine.py → L6 ✅
                       ├── cb_sync_wrapper.py → L6 ❌ (no matching driver)
                       ├── controls_facade.py → L6 ❌ (no matching driver)
                       ├── cost_safety_rails.py → L6 ❌ (no matching driver)
                       ├── decisions.py → L6 ❌ (no matching driver)
                       ├── killswitch.py → L6 ❌ (no matching driver)
                       ├── s2_cost_smoothing.py → L6 ❌ (no matching driver)
                       ├── threshold_engine.py → L6 ✅
                     L5 Schemas (3 files)
                     L5 Other (2 files)
                       │
                       └──→ L6 Drivers (8 files)
                              ├── budget_enforcement_driver.py
                              ├── circuit_breaker.py
                              ├── circuit_breaker_async.py
                              ├── limits_read_driver.py
                              ├── override_driver.py
                              ├── policy_limits_driver.py
                              ├── scoped_execution.py
                              ├── threshold_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2_api | No L2 API routes but 9 engines exist | Build hoc/api/cus/controls/ with route handlers |
| L7_models | 8 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `customer_killswitch_adapter.py` | `from sqlmodel import Session` | L3 MUST NOT access DB | Delegate to L5 engine or L6 driver |
| `customer_killswitch_adapter.py` | `from app.models.killswitch import TriggerType` | L3 MUST NOT import L7 models | Use L5 schemas for data contracts |
| `killswitch_read_driver.py` | `from sqlalchemy import and_, desc, func, select` | L5 MUST NOT import sqlalchemy | Move DB logic to L6 driver |
| `killswitch_read_driver.py` | `from sqlmodel import Session` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver |
| `killswitch_read_driver.py` | `from app.models.killswitch import DefaultGuardrail, Incident` | L5 MUST NOT import L7 models directly | Route through L6 driver |
