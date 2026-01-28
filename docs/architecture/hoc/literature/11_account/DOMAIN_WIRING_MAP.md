# Account — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/account.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/account/` (1 files)
         ├── memory_pins.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (8 files)
                       ├── accounts_facade.py → L6 ✅
                       ├── billing_provider.py → L6 ❌ (no matching driver)
                       ├── email_verification.py → L6 ❌ (no matching driver)
                       ├── identity_resolver.py → L6 ❌ (no matching driver)
                       ├── notifications_facade.py → L6 ❌ (no matching driver)
                       ├── profile.py → L6 ❌ (no matching driver)
                       ├── tenant_engine.py → L6 ✅
                       ├── user_write_engine.py → L6 ✅
                     L5 Other (2 files)
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
| L2.1_facade | No L2.1 facade to group 1 L2 routers | Build hoc/api/facades/cus/account.py grouping: memory_pins.py |
| L3_adapter | No L3 adapters but 8 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/account/L3_adapters/ with domain adapter(s) |
| L7_models | 3 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `tenant_engine.py` | `from app.models.tenant import PLAN_QUOTAS, APIKey, Tenant, T` | L5 MUST NOT import L7 models directly | Route through L6 driver |
