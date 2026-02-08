# Account — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/account.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/account/` (1 files)
         ├── memory_pins.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (3 files)
                       ├── accounts_facade.py → L6 ✅
                       ├── notifications_facade.py → L6 ❌ (no matching driver)
                       ├── tenant_engine.py → L6 ✅
                       │
                       └──→ L6 Drivers (3 files)
                              ├── accounts_facade_driver.py
                              ├── tenant_driver.py
                              ├── user_write_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L3_adapter | No L3 adapters but 3 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/account/L3_adapters/ with domain adapter(s) |
| L7_models | 3 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
