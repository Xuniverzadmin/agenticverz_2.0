# Controls — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/controls.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/controls/` — **GAP** (0 files)
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (2 files)
                       ├── controls_facade.py → L6 ❌ (no matching driver)
                       ├── threshold_engine.py → L6 ✅
                     L5 Schemas (3 files)
                       │
                       └──→ L6 Drivers (5 files)
                              ├── budget_enforcement_driver.py
                              ├── limits_read_driver.py
                              ├── override_driver.py
                              ├── policy_limits_driver.py
                              ├── threshold_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2_api | No L2 API routes but 2 engines exist | Build hoc/api/cus/controls/ with route handlers |
| L3_adapter | No L3 adapters but 2 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/controls/L3_adapters/ with domain adapter(s) |
| L7_models | 5 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
