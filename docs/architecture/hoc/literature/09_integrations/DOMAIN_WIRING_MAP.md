# Integrations — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/integrations.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/integrations/` (3 files)
         ├── cus_telemetry.py
         ├── protection_dependencies.py
         ├── session_context.py
         │
         └──→ L3 Adapters (21 files)
                ├── cloud_functions_adapter.py ✅
                ├── customer_activity_adapter.py ✅
                ├── customer_incidents_adapter.py ✅
                ├── customer_keys_adapter.py ✅
                ├── customer_logs_adapter.py ✅
                ├── customer_policies_adapter.py ✅
                ├── file_storage_base.py ✅
                ├── founder_ops_adapter.py ✅
                ├── gcs_adapter.py ✅
                ├── lambda_adapter.py ✅
                ├── pgvector_adapter.py ✅
                ├── pinecone_adapter.py ✅
                ├── runtime_adapter.py ✅
                ├── s3_adapter.py ✅
                ├── serverless_base.py ✅
                ├── slack_adapter.py ✅
                ├── smtp_adapter.py ✅
                ├── vector_stores_base.py ✅
                ├── weaviate_adapter.py ✅
                ├── webhook_adapter.py ✅
                ├── workers_adapter.py ✅
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (16 files)
                       ├── bridges.py → L6 ❌ (no matching driver)
                       ├── connectors_facade.py → L6 ❌ (no matching driver)
                       ├── cost_bridges_engine.py → L6 ❌ (no matching driver)
                       ├── protocol.py → L6 ❌ (no matching driver)
                       ├── cus_health_engine.py → L6 ❌ (no matching driver)
                       ├── cus_integration_service.py → L6 ❌ (no matching driver)
                       ├── datasources_facade.py → L6 ❌ (no matching driver)
                       ├── dispatcher.py → L6 ❌ (no matching driver)
                       ├── graduation_engine.py → L6 ❌ (no matching driver)
                       ├── http_connector.py → L6 ❌ (no matching driver)
                       └── ... (+6 more)
                     L5 Schemas (4 files)
                     L5 Other (3 files)
                       │
                       └──→ L6 Drivers (3 files)
                              ├── connector_registry.py
                              ├── external_response_driver.py
                              ├── worker_registry_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 3 L2 routers | Build hoc/api/facades/cus/integrations.py grouping: cus_telemetry.py, protection_dependencies.py, session_context.py |
| L6_driver | cus_health_engine.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/integrations/L6_drivers/cus_health_driver.py |
| L7_models | 3 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `cus_telemetry.py` | `from app.hoc.cus.activity.L5_engines.cus_telemetry_service i` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `customer_incidents_adapter.py` | `from sqlmodel import Session` | L3 MUST NOT access DB | Delegate to L5 engine or L6 driver |
| `customer_keys_adapter.py` | `from sqlmodel import Session` | L3 MUST NOT access DB | Delegate to L5 engine or L6 driver |
| `cus_health_engine.py` | `from sqlmodel import Session, select` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver |
| `cus_health_engine.py` | `from app.db import get_engine` | L5 MUST NOT access DB directly | Use L6 driver for DB access |
| `cus_health_engine.py` | `from app.models.cus_models import CusHealthState, CusIntegra` | L5 MUST NOT import L7 models directly | Route through L6 driver |
