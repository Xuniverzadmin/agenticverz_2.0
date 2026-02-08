# Integrations — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/integrations.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/integrations/` (3 files)
         ├── cus_telemetry.py
         ├── protection_dependencies.py
         ├── session_context.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (8 files)
                       ├── connectors_facade.py → L6 ❌ (no matching driver)
                       ├── protocol.py → L6 ❌ (no matching driver)
                       ├── cus_health_engine.py → L6 ❌ (no matching driver)
                       ├── datasources_facade.py → L6 ❌ (no matching driver)
                       ├── integrations_facade.py → L6 ❌ (no matching driver)
                       ├── prevention_contract.py → L6 ❌ (no matching driver)
                       ├── sql_gateway.py → L6 ❌ (no matching driver)
                       ├── types.py → L6 ❌ (no matching driver)
                     L5 Schemas (4 files)
                     L5 Other (3 files)
                       │
                       └──→ L6 Drivers (1 files)
                              ├── worker_registry_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L3_adapter | No L3 adapters but 8 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/integrations/L3_adapters/ with domain adapter(s) |
| L7_models | 1 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
