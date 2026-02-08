# Integrations — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/integrations.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/integrations/` (5 files)
         ├── cus_telemetry.py
         ├── mcp_servers.py
         ├── protection_dependencies.py
         ├── session_context.py
         ├── v1_proxy.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (11 files)
                       ├── connectors_facade.py → L6 ❌ (no matching driver)
                       ├── protocol.py → L6 ❌ (no matching driver)
                       ├── cus_health_engine.py → L6 ✅
                       ├── cus_integration_engine.py → L6 ✅
                       ├── datasources_facade.py → L6 ❌ (no matching driver)
                       ├── integrations_facade.py → L6 ❌ (no matching driver)
                       ├── mcp_server_engine.py → L6 ❌ (no matching driver)
                       ├── mcp_tool_invocation_engine.py → L6 ❌ (no matching driver)
                       ├── prevention_contract.py → L6 ❌ (no matching driver)
                       ├── sql_gateway.py → L6 ❌ (no matching driver)
                       └── ... (+1 more)
                     L5 Schemas (6 files)
                     L5 Other (4 files)
                       │
                       └──→ L6 Drivers (8 files)
                              ├── bridges_driver.py
                              ├── connector_registry_driver.py
                              ├── cus_health_driver.py
                              ├── cus_integration_driver.py
                              ├── mcp_driver.py
                              ├── proxy_driver.py
                              ├── sql_gateway_driver.py
                              ├── worker_registry_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 8 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
