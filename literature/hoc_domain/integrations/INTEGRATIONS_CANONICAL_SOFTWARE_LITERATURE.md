# Integrations Domain — Canonical Software Literature

**Domain:** integrations
**Generated:** 2026-01-31
**Reference:** PIN-498
**Total Files:** 52 (16 L5_engines, 2 L5_engines/credentials, 5 L6_drivers, 23 adapters, 5 L5_schemas, 1 __init__.py)

---

## Consolidation Actions (2026-01-31)

### Naming Violations Fixed (6 renames)

**L5 (5):**

| # | Old Name | New Name |
|---|----------|----------|
| N1 | cus_integration_service.py | cus_integration_engine.py |
| N2 | bridges.py | bridges_engine.py |
| N3 | dispatcher.py | dispatcher_engine.py |
| N4 | http_connector.py | http_connector_engine.py |
| N5 | mcp_connector.py | mcp_connector_engine.py |

**L6 (1):**

| # | Old Name | New Name |
|---|----------|----------|
| N6 | connector_registry.py | connector_registry_driver.py |

### Header Correction (1)

| File | Old Header | New Header |
|------|-----------|------------|
| integrations/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain (Integrations)` |

### Legacy Disconnection (1)

| File | Old Import | Action |
|------|-----------|--------|
| cus_integration_engine.py | `from app.services.cus_integration_engine import (...)` | Disconnected. Stubbed with TODO: rewire to HOC equivalent candidate during rewiring phase |

### Import Path Fixes (4)

| File | Old Import | New Import |
|------|-----------|------------|
| integrations_facade.py | `...cus_integration_service import` | `...cus_integration_engine import` |
| connectors_facade.py | `...L6_drivers.connector_registry import` | `...L6_drivers.connector_registry_driver import` |
| bridges_engine.py | `from .dispatcher import` | `from .dispatcher_engine import` |
| bridges_engine.py | `from .bridges_driver import` | `from app.hoc.cus.integrations.L6_drivers.bridges_driver import` |

### Schema Import Fixes (2)

| File | Old Import | New Import |
|------|-----------|------------|
| bridges_engine.py | `from ..schemas.audit_schemas import` | `from app.hoc.cus.integrations.L5_schemas.audit_schemas import` |
| bridges_engine.py | `from ..schemas.loop_events import` | `from app.hoc.cus.integrations.L5_schemas.loop_events import` |

### Broken Import Fixed (1)

`L6_drivers/bridges_driver.py` was missing — referenced by `L6_drivers/__init__.py` line 26. Restored from Phase 3 backup (`backups/hoc_phase3/domain_integrations_20260124_212926/drivers/bridges_driver.py`) with import paths corrected to absolute HOC paths.

### Duplicate Files Resolved (13)

13 adapter files existed in both `adapters/` and `L5_engines/external_adapters/` (11 differed only in layer comment line). Resolution: deleted `L5_engines/external_adapters/` entirely, retained `adapters/` as canonical location. 8 unique files moved from `external_adapters/` to `adapters/` before deletion.

**Moved files:** customer_activity_adapter.py, customer_incidents_adapter.py, customer_keys_adapter.py, customer_logs_adapter.py, customer_policies_adapter.py, founder_ops_adapter.py, runtime_adapter.py, workers_adapter.py

### Hybrid Files (Documented — Deferred to Refactor)

- `bridges_engine.py` — M25_FROZEN, L5/L6 HYBRID. Mixed business logic and DB operations. DB ops should be extracted to bridges_driver.py (L6).
- `dispatcher_engine.py` — M25_FROZEN, L5/L6 HYBRID. Mixed dispatch logic and DB operations.

### Cross-Domain Imports (Documented — Deferred to Rewiring)

All in `adapters/` (L3-declared boundary adapters):

| Adapter | Cross-Domain Target |
|---------|-------------------|
| customer_incidents_adapter.py | incidents L5 |
| customer_logs_adapter.py | logs L5 |
| customer_policies_adapter.py | policies L5 |
| customer_activity_adapter.py | activity L5 |
| customer_keys_adapter.py | api_keys L5 |

**Purpose:** These are boundary adapters that call into other domains' L5 engines. Correct architecture: L3 adapter → L4 orchestrator → L5 target domain engine. Currently L3→L5 cross-domain. Deferred to rewiring phase.

### Legacy Connections

**None remaining.** The `from app.services.cus_integration_engine` in `cus_integration_engine.py` was the only active legacy import. Now disconnected and stubbed.

---

## Domain Persona Declaration (from __init__.py)

| Persona | Purpose | Key Files |
|---------|---------|-----------|
| CUSTOMER CONSOLE | BYOK LLM integrations, datasources, limits | cus_integration_engine.py, integrations_facade.py |
| PLATFORM RUNTIME | Connector registries, lifecycle, health | connector_registry_driver.py, *_connector_engine.py |
| MEDIATION LAYER | Deny-by-default retrieval, evidence emission | sql_gateway.py, datasources_facade.py |

---

## L5_engines (16 files)

### __init__.py
- **Role:** Package init

### bridges_engine.py *(renamed from bridges.py)*
- **Role:** Integration bridges — M25_FROZEN, L5/L6 HYBRID
- **Status:** FROZEN (2025-12-23)

### connectors_facade.py
- **Role:** Connector management facade
- **Callers:** L4 integrations_handler (integrations.connectors)

### cost_bridges_engine.py
- **Role:** Cost bridge calculations for integrations

### cus_health_engine.py
- **Role:** Customer integration health checks

### cus_integration_engine.py *(renamed from cus_integration_service.py)*
- **Role:** Customer integration BYOK management
- **Legacy:** DISCONNECTED — stubbed with TODO
- **Callers:** integrations_facade.py

### datasources_facade.py
- **Role:** Datasource management facade
- **Callers:** L4 integrations_handler (integrations.datasources)

### dispatcher_engine.py *(renamed from dispatcher.py)*
- **Role:** Integration dispatcher — M25_FROZEN, L5/L6 HYBRID
- **Status:** FROZEN (2025-12-23)

### graduation_engine.py
- **Role:** Integration graduation logic

### http_connector_engine.py *(renamed from http_connector.py)*
- **Role:** HTTP connector implementation

### iam_engine.py
- **Role:** IAM/identity management for integrations

### integrations_facade.py
- **Role:** Main integrations facade
- **Callers:** L4 integrations_handler (integrations.query)

### mcp_connector_engine.py *(renamed from mcp_connector.py)*
- **Role:** MCP protocol connector

### prevention_contract.py
- **Role:** Prevention contract definitions

### sql_gateway.py
- **Role:** SQL gateway for mediated retrieval (deny-by-default)

### types.py
- **Role:** Integration type definitions

---

## L5_engines/credentials (2 files)

### __init__.py
- **Role:** Credentials package init

### protocol.py
- **Role:** Credential protocol definitions

---

## L6_drivers (5 files)

### __init__.py
- **Role:** Package init, exports record_policy_activation

### bridges_driver.py *(restored from Phase 3 backup)*
- **Role:** Bridge audit trail persistence
- **Status:** FROZEN (2025-12-23)

### connector_registry_driver.py *(renamed from connector_registry.py)*
- **Role:** Connector registry DB operations
- **Classes:** ConnectorRegistry

### external_response_driver.py
- **Role:** External response persistence

### worker_registry_driver.py
- **Role:** Worker registry DB operations

---

## adapters (23 files)

### __init__.py
- **Role:** Package init

### Boundary Adapters (L3-declared, 22 files)

**External Service Adapters (14):**
cloud_functions_adapter.py, file_storage_base.py, gcs_adapter.py, lambda_adapter.py, mcp_server_registry.py, pgvector_adapter.py, pinecone_adapter.py, s3_adapter.py, serverless_base.py, slack_adapter.py, smtp_adapter.py, vector_stores_base.py, weaviate_adapter.py, webhook_adapter.py

**Cross-Domain Adapters (8 — moved from external_adapters/):**
customer_activity_adapter.py, customer_incidents_adapter.py, customer_keys_adapter.py, customer_logs_adapter.py, customer_policies_adapter.py, founder_ops_adapter.py, runtime_adapter.py, workers_adapter.py

---

## L5_schemas (5 files)

### __init__.py
- **Role:** Schemas package init

### audit_schemas.py
- **Role:** Audit schema definitions (PolicyActivationAudit)

### cus_schemas.py
- **Role:** Customer integration schemas

### datasource_model.py
- **Role:** Datasource model definitions

### loop_events.py
- **Role:** Loop event schemas (ConfidenceCalculator, LoopEvent, etc.)

---

## L4 Handler

**File:** `hoc/hoc_spine/orchestrator/handlers/integrations_handler.py`
**Operations:** 3

| Operation | Target |
|-----------|--------|
| integrations.query | IntegrationsFacade |
| integrations.connectors | ConnectorsFacade |
| integrations.datasources | DatasourcesFacade |

No L4 handler import updates required — handler imports facade files which were not renamed.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat B: Stale Docstring References Corrected (1)

| File | Old Docstring Reference | New Docstring Reference |
|------|------------------------|------------------------|
| `L5_engines/datasources_facade.py` | `from app.services.datasources.facade import get_datasources_facade` | `from app.hoc.cus.integrations.L5_engines.datasources_facade import get_datasources_facade` |

### Cat B: Active Legacy Imports

**None.** `cus_integration_engine.py` was already disconnected during consolidation (PIN-498).

### Legacy Connections

**None.** Domain is clean — no HOC→legacy or legacy→HOC active imports.

### Cat E: Cross-Domain L5→L5/L6 Violations (Outbound — 1 — DOCUMENT ONLY)

| Source File | Import Target |
|------------|--------------|
| `adapters/customer_logs_adapter.py` | `logs.L5_engines.logs_read_engine` |

**Deferred:** Requires L4 Coordinator to mediate cross-domain reads.

### Tally

39/39 checks PASS (36 consolidation + 3 cleansing).
