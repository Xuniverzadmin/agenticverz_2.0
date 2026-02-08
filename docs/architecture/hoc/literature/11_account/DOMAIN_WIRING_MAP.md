# Account — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/account.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/account/` (1 files)
         ├── memory_pins.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (7 files)
                       ├── accounts_facade.py → L6 ✅
                       ├── billing_provider_engine.py → L6 ❌ (no matching driver)
                       ├── memory_pins_engine.py → L6 ✅
                       ├── notifications_facade.py → L6 ❌ (no matching driver)
                       ├── onboarding_engine.py → L6 ✅
                       ├── tenant_engine.py → L6 ✅
                       ├── tenant_lifecycle_engine.py → L6 ✅
                     L5 Schemas (8 files)
                       │
                       └──→ L6 Drivers (6 files)
                              ├── accounts_facade_driver.py
                              ├── memory_pins_driver.py
                              ├── onboarding_driver.py
                              ├── tenant_driver.py
                              ├── tenant_lifecycle_driver.py
                              ├── user_write_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 6 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
