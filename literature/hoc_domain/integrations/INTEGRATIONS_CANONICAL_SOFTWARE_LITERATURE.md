# Integrations Domain — Canonical Software Literature

**Domain:** integrations
**Generated:** 2026-01-31
**Updated:** 2026-02-07 (CUS health driver extraction)
**Reference:** PIN-498, PIN-516, PIN-517, PIN-521
**Total Files:** 59 (18 L5_engines, 2 L5_engines/credentials, 2 L5_vault/engines, 1 L5_vault/drivers, 6 L6_drivers, 23 adapters, 5 L5_schemas, 1 hoc_spine/services, 1 __init__.py)

---

## Reality Delta (2026-02-07)

- Execution topology: integrations L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5 gaps).
- External connector I/O is isolated behind L6 (`backend/app/hoc/cus/integrations/L6_drivers/sql_gateway_driver.py`) with Protocol/DTO boundary in L5 schemas.
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain integrations --json --advisory` reports 0 blocking, 0 advisory.
- Remaining coherence debt (execution boundary): 5 orphaned L5 entry modules remain in `backend/app/hoc/cus/integrations/L5_engines/` (see `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`).

### Knowledge Planes (System Runtime Integration)

- Integrations is a **capability provider** for knowledge planes (connectors, vector stores, ingestion/index jobs).
- Knowledge plane lifecycle authority is **hoc_spine-owned** (internal runtime), not domain-owned.
- Canonical design literature + plan:
  - `literature/hoc_spine/KNOWLEDGE_PLANE_LITERATURE.md`
  - `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`

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
- **Status:** FROZEN (2025-12-23), QUARANTINED (PIN-508 Phase 7)
- **Location:** `_frozen/bridges_engine.py`

### connectors_facade.py
- **Role:** Connector management facade
- **Callers:** L4 integrations_handler (integrations.connectors)

### cost_bridges_engine.py
- **Role:** Cost bridge calculations for integrations

### cus_health_engine.py
- **Role:** Customer integration health checks

### cus_integration_engine.py *(renamed from cus_integration_service.py)*
- **Role:** Customer integration BYOK management — full CRUD, lifecycle, health checks (472 lines)
- **Status:** CANONICAL (rewired from legacy 2026-02-02, PIN-512 Cat-B)
- **Driver:** CusIntegrationDriver (L6) — `integrations/L6_drivers/cus_integration_driver.py`
- **Callers:** integrations_facade.py

### datasources_facade.py
- **Role:** Datasource management facade
- **Callers:** L4 integrations_handler (integrations.datasources)

### dispatcher_engine.py *(renamed from dispatcher.py)*
- **Role:** Integration dispatcher — M25_FROZEN, L5/L6 HYBRID
- **Status:** FROZEN (2025-12-23), QUARANTINED (PIN-508 Phase 7)
- **Location:** `_frozen/dispatcher_engine.py`

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
- **Role:** MCP tool invocation with governance (rate limiting, schema validation)
- **Classes:** McpConnectorService, McpConnectorConfig, McpToolDefinition

### mcp_server_engine.py *(new — PIN-516 Phase 2)*
- **Role:** MCP server lifecycle orchestration (registration, discovery, health)
- **Status:** ACTIVE (2026-02-03)
- **Classes:** McpServerEngine, McpServerStatus, McpRegistrationResult, McpDiscoveryResult, McpHealthResult
- **Protocol Methods:** _mcp_initialize, _mcp_list_tools, _mcp_ping
- **Driver Dependency:** McpDriver (L6)

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

## L6_drivers (6 files)

### __init__.py
- **Role:** Package init, exports record_policy_activation, McpDriver

### bridges_driver.py *(restored from Phase 3 backup)*
- **Role:** Bridge audit trail persistence
- **Status:** FROZEN (2025-12-23)

### connector_registry_driver.py *(renamed from connector_registry.py)*
- **Role:** Connector registry DB operations
- **Classes:** ConnectorRegistry

### cus_integration_driver.py
- **Role:** Customer integration persistence (CRUD for cus_integrations table)
- **Status:** ACTIVE (PIN-512 Cat-B rewire)

### external_response_driver.py
- **Role:** External response persistence

### mcp_driver.py *(new — PIN-516 Phase 1)*
- **Role:** MCP server and tool persistence (pure CRUD)
- **Status:** ACTIVE (2026-02-03)
- **Classes:** McpDriver, McpServerRow, McpToolRow, McpInvocationRow
- **Functions:** compute_input_hash, compute_output_hash
- **Tables:** mcp_servers, mcp_tools, mcp_tool_invocations (migration 119_w2_mcp_servers)

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

**File:** `hoc/cus/hoc_spine/orchestrator/handlers/integrations_handler.py`
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

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-507 Law 0 Remediation (2026-02-01)

**Test import rewires (L3 abolished per PIN-485):**
- `tests/test_m25_integration_loop.py`: `app.integrations.L3_adapters` → `app.integrations.bridges` (for `IncidentToCatalogBridge`, `PatternToRecoveryBridge`, `RecoveryToPolicyBridge`)
- `tests/test_m25_policy_overreach.py`: `app.integrations.L3_adapters` → `app.integrations.events` (for `ConfidenceCalculator`)

All four classes are implemented and active in legacy `app/integrations/` paths. The HOC equivalents exist in `app.hoc.cus.integrations.L5_engines.bridges_engine` and `app.hoc.cus.integrations.L5_schemas.loop_events` respectively. Tests use legacy paths as they predate HOC migration.

**Stale `__init__` re-exports cleaned:**
- `L5_engines/__init__.py`: Removed `learning_proof_engine` block (16 symbols) — module moved to `policies/L5_engines/` during PIN-498
- `L5_schemas/__init__.py`: Removed `cost_snapshot_schemas` block (8 symbols) — module lives in `analytics/L5_schemas/`
- `L5_engines/cost_bridges_engine.py`: Fixed `..schemas.loop_events` → `app.hoc.cus.integrations.L5_schemas.loop_events`
- `L5_engines/credentials/__init__.py`: Stale relative import `.types` → absolute `app.hoc.cus.integrations.L5_engines.types` (`Credential` lives in parent package, not `credentials/types.py`). Detected by `check_init_hygiene.py`

## PIN-508 Quarantine Actions (2026-02-01)

### M25_FROZEN Quarantine (Phase 7)

Hybrid engines moved to `_frozen/` subdirectory (no longer active in production wiring):

| # | File | Status | Reason |
|---|------|--------|--------|
| 1 | `L5_engines/_frozen/bridges_engine.py` | QUARANTINED | M25_FROZEN, L5/L6 HYBRID — audit trail and policy bridges mixed with DB ops |
| 2 | `L5_engines/_frozen/dispatcher_engine.py` | QUARANTINED | M25_FROZEN, L5/L6 HYBRID — dispatch logic mixed with DB operations |

**Quarantine Marker:** `L5_engines/_frozen/__init__.py` created (empty, marker file)

**Impact:** L4 integrations_handler no longer routes to these engines. Backward compat aliases removed from L5 exports.

### STUB_ENGINE Markers Added (Phase 5)

Production engines marked with STUB_ENGINE classification:

| # | File | Marker | Purpose |
|---|------|--------|---------|
| 1 | `L5_engines/cus_integration_engine.py` | STUB_ENGINE | Customer integration BYOK (legacy stub disconnected during PIN-498, now explicitly marked) |

### New Quarantine Marker File

| File | Purpose |
|------|---------|
| `L5_engines/_frozen/__init__.py` | M25_FROZEN quarantine marker — no exports, no active wiring |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-510 Phase 0 — L4 Spine Bridge Infrastructure (2026-02-01)

### Bridges Registration

Per-domain bridges established at L4 hoc_spine layer to eliminate monolithic DomainBridge.

**Location:** `app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/`

**Bridge Inventory:**

| Bridge | Target Domain | Methods | Status | Phase |
|--------|---------------|---------|--------|-------|
| IncidentsBridge | incidents | 3 (read, write, lessons) | ACTIVE | 0A |
| ControlsBridge | controls | 3 (limits_query, policy_limits, killswitch) | ACTIVE | 0A |
| ActivityBridge | activity | 1 (query) | ACTIVE | 0A |
| PoliciesBridge | policies | 1 (customer_policy_read) | ACTIVE | 0A |
| ApiKeysBridge | api_keys | 2 (keys_read, keys_write) | ACTIVE | 0A |
| LogsBridge | logs | 1 (read_service) | ACTIVE | 0A |

**Consumers:** Phase 1A adapter rewiring (integrations boundary adapters will call bridges for cross-domain L5 access)

### CI Checks Extended (Check 19–20)

New CI checks added to `scripts/ci/check_init_hygiene.py`:

| Check | ID | Rule | Enforcement |
|-------|----|----|--------------|
| 19 | `check_bridge_method_count` | Per-domain bridge max 5 capabilities | BLOCKING |
| 20 | `check_schema_admission` | hoc_spine/schemas/ files must have Consumers header | BLOCKING |

**Run CI checks:** `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci` (18 total checks)

### Architecture Rules

**L4 Spine Bridges (Binding Constraints):**
- Max 5 capability methods per bridge (CI enforced)
- Never accept session in constructor
- Return session-bound capability objects
- Lazy imports only (no circular dependencies at module load)
- Reserved for L4 handlers and coordinators only

**Phase Timeline:**
- **Phase 0A (COMPLETE):** Bridge infrastructure + CI checks (2026-02-01)
- **Phase 1A (PENDING):** Adapter rewiring — integrations adapters call bridges for cross-domain L5 access
- **Phase 1B (PENDING):** Handler stabilization — L4 handlers use bridges exclusively

## PIN-516 MCP Customer Integration (2026-02-03)

### Phase 1: Persistence Layer (COMPLETE)

MCP (Model Context Protocol) server integration for customers, enabling AI runs to invoke external tools through governed, auditable channels.

**Deliverables:**

| Layer | File | Purpose |
|-------|------|---------|
| L7 | `app/models/mcp_models.py` | SQLModel ORM classes (McpServer, McpTool, McpToolInvocation) |
| L6 | `app/hoc/cus/integrations/L6_drivers/mcp_driver.py` | Pure CRUD driver (no protocol logic) |
| TEST | `tests/mcp/test_mcp_phase1.py` | Survivability tests |
| PIN | `docs/memory-pins/PIN-516-mcp-customer-integration.md` | Design specification |

**L7 Models (app/models/mcp_models.py):**

| Model | Table | Purpose |
|-------|-------|---------|
| McpServer | mcp_servers | Registered external MCP servers |
| McpTool | mcp_tools | Tools exposed by MCP servers |
| McpToolInvocation | mcp_tool_invocations | Immutable audit trail (DB trigger enforced) |

**L6 Driver Methods (McpDriver):**

| Category | Methods |
|----------|---------|
| Server | create_server, get_server, get_server_by_url, list_servers, update_server, soft_delete_server |
| Tool | upsert_tools, get_tools, get_tool, update_tool |
| Invocation | record_invocation, get_invocations, get_invocation, get_invocations_by_tenant |

**Phase-1 Invariants Satisfied:**

| Invariant | Status | Evidence |
|-----------|--------|----------|
| INV-1: Lifecycle fields | ✓ | status, protocol_version, discovered_at, last_health_check_at |
| INV-2: L6 is pure CRUD | ✓ | No HTTP, no MCP protocol, no JSON-RPC in driver |
| INV-3: Credentials by reference | ✓ | credential_id field stores vault reference only |
| INV-4: Survivability tests | ✓ | Persistence, tenant isolation, soft delete, idempotency tests |

**Database Schema (migration 119_w2_mcp_servers):**

Tables exist with proper constraints, indexes, and immutability trigger on mcp_tool_invocations.

### Phase 2: Business Logic + Protocol (COMPLETE)

**Deliverables:**

| Layer | File | Purpose |
|-------|------|---------|
| L5 | `app/hoc/cus/integrations/L5_engines/mcp_server_engine.py` | Server lifecycle orchestration |

**McpServerEngine Methods:**

| Category | Methods |
|----------|---------|
| Registration | register_server |
| Discovery | discover_tools |
| Health | health_check |
| Server Mgmt | get_server, list_servers, update_server, disable_server |
| Tool Mgmt | get_tools, enable_tool, disable_tool, set_tool_risk_level |

**MCP Protocol Implementation:**

| Method | Purpose |
|--------|---------|
| _mcp_initialize | Discover capabilities and protocol version |
| _mcp_list_tools | Discover available tools with schemas |
| _mcp_ping | Health check (falls back to initialize) |

**Risk Assessment:**
- Automatic tool risk classification based on name keywords
- Critical: delete, remove, drop, destroy, kill
- High: write, execute, run, shell, eval, create
- Medium: update, modify, set, put, post
- Low: read, get, list, search, query, fetch

### Phase 3: HTTP Orchestration (COMPLETE)

**Deliverables:**

| Layer | File | Purpose |
|-------|------|---------|
| L4 | `app/hoc/cus/hoc_spine/orchestrator/handlers/mcp_handler.py` | Handler for integrations.mcp_servers operation |
| L2 | `app/hoc/api/cus/integrations/mcp_servers.py` | Customer-facing API routes |

**L4 Handler Methods (McpServersHandler):**

| Method | Description |
|--------|-------------|
| register_server | Register a new MCP server |
| get_server | Get server details by ID |
| list_servers | List all servers for tenant |
| discover_tools | Discover tools from MCP server |
| health_check | Check MCP server health |
| delete_server | Soft-delete a server |
| list_tools | List tools for a server |
| get_invocations | List tool invocations |

**L2 API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/integrations/mcp-servers` | Register a new MCP server |
| GET | `/integrations/mcp-servers` | List MCP servers for tenant |
| GET | `/integrations/mcp-servers/{server_id}` | Get server details |
| POST | `/integrations/mcp-servers/{server_id}/discover` | Discover tools |
| GET | `/integrations/mcp-servers/{server_id}/health` | Health check |
| DELETE | `/integrations/mcp-servers/{server_id}` | Soft-delete server |
| GET | `/integrations/mcp-servers/{server_id}/tools` | List server tools |
| GET | `/integrations/mcp-servers/{server_id}/invocations` | List invocations |

**Registration:**
- Handler registered in `handlers/__init__.py` under `register_all_handlers()`
- Router registered in `main.py` via `app.include_router(mcp_servers_router)`

### Phase 4: Monitoring Integration (COMPLETE)

**Deliverables:**

| Layer | File | Purpose |
|-------|------|---------|
| L5 | `app/hoc/cus/integrations/L5_engines/mcp_tool_invocation_engine.py` | Governed tool invocation engine |

**McpToolInvocationEngine** orchestrates governed tool invocations with:

| Feature | Implementation |
|---------|---------------|
| Policy Validation | `McpPolicyChecker` protocol (injectable, default permissive) |
| Audit Trail | `MCPAuditEmitter` from logs domain |
| Tool Execution | JSON-RPC `tools/call` method |
| Incident Creation | Optional `IncidentEngine` integration |
| Invocation Recording | Via `McpDriver.record_invocation()` |

**L4 Handler Method Added:** `invoke_tool`

**L2 API Endpoint Added:** `POST /integrations/mcp-servers/{server_id}/tools/{tool_id}/invoke`

**Monitoring Integration Points:**

- **Policy:** `McpPolicyChecker` protocol for injectable policy validation
- **Audit:** `MCPAuditEmitter` for compliance-grade event chain
- **Incidents:** Optional `IncidentEngine` for failure → incident creation
- **Activity:** Invocation records in `mcp_tool_invocations` table

---

## PIN-517 cus_vault Authority Refactor (2026-02-03)

### Overview

Establishes trust zone architecture for credential management. Resolves authority confusion between vault selection, resolution, and execution. Enables rule-based access control for customer credentials.

### L5_vault/engines (2 files)

#### vault_rule_check.py *(new — PIN-517 FIX 4.1)*
- **Role:** Credential access rule checker protocol
- **Status:** ACTIVE (2026-02-03)
- **Classes:**
  - `CredentialAccessResult` — Frozen dataclass for rule decision result
  - `CredentialAccessRuleChecker` — Protocol for async rule validation at L4
  - `DefaultCredentialAccessRuleChecker` — Permissive default (system scope)
  - `DenyAllRuleChecker` — Fail-closed default for customer scope (GAP-4)
- **Callers:** `hoc_spine/services/cus_credential_engine.py` (L4)
- **Delegates:** None (leaf module)

#### service.py *(new — PIN-517 FIX 4.2)*
- **Role:** Credential service with audit logging
- **Status:** ACTIVE (2026-02-03)
- **Classes:**
  - `CredentialAccessRecord` — Audit record with policy fields
  - `CredentialService` — SYNC operations with audit trail
- **Key Methods:**
  - `get_credential_sync(tenant_id, credential_id, accessor_id, accessor_type, ...)` — GAP-3 compliant
  - `store_credential_sync(...)` — With audit
  - `list_credentials_sync(...)` — With audit
  - `update_credential_sync(...)` — With audit
  - `delete_credential_sync(...)` — With audit
  - `rotate_credential_sync(...)` — With audit
- **Callers:** `hoc_spine/services/cus_credential_engine.py` (L4)
- **Delegates:** `L5_vault/drivers/vault.py` (CredentialVault implementations)

### L5_vault/drivers (1 file)

#### vault.py *(new — PIN-517 FIX 2+3)*
- **Role:** Credential vault implementations (Env, HashiCorp, AWS)
- **Status:** ACTIVE (2026-02-03)
- **Classes:**
  - `CredentialType` — Enum (api_key, oauth2, basic_auth, certificate, custom)
  - `CredentialMetadata` — Dataclass for credential metadata
  - `CredentialData` — Dataclass with metadata + secret_data
  - `CredentialVault` — Abstract base class for vault implementations
  - `EnvCredentialVault` — Environment variable vault (system scope only)
  - `HashiCorpVault` — HashiCorp Vault implementation (SYNC)
  - `AwsSecretsManagerVault` — AWS Secrets Manager implementation (SYNC, GAP-5 namespace)
- **Functions:**
  - `create_credential_vault(scope, provider)` — Factory with authority split (GAP-2)
- **Callers:** `L5_vault/engines/service.py`, `hoc_spine/services/cus_credential_engine.py`
- **Delegates:** boto3 (AWS), urllib (HashiCorp)

### hoc_spine/services (1 file)

#### cus_credential_engine.py *(modified — PIN-517 FIX 1+4.3)*
- **Role:** Customer Credential Service (L4 Spine)
- **Status:** ACTIVE (2026-02-03)
- **Classes:**
  - `CusCredentialService` — Resolves encrypted://, cus-vault://, env:// references
- **Key Methods:**
  - `resolve_credential(tenant_id, credential_ref)` — Sync dispatch (raises for cus-vault://)
  - `resolve_cus_vault_credential(credential_ref, accessor_id, accessor_type, access_reason)` — Async vault lookup with rule check
  - `_decrypt_credential(credential_ref)` — AES-256-GCM decryption
  - `_resolve_env_credential(credential_ref)` — Environment variable lookup
  - `encrypt_credential(tenant_id, plaintext)` — Returns encrypted:// reference
  - `validate_credential_format(value)` — Returns (is_valid, error_msg) tuple
- **Callers:** L4 handlers (integrations, MCP)
- **Delegates:** `L5_vault/engines/vault_rule_check.py`, `L5_vault/engines/service.py`, `L5_vault/drivers/vault.py`

### Credential Reference Scheme

| Format | Scope | Resolution | Rule Check Required |
|--------|-------|------------|---------------------|
| `cus-vault://<tenant_id>/<credential_id>` | Customer | Async via CredentialService | YES |
| `encrypted://<base64>` | Both | Sync AES-256-GCM | NO |
| `env://<VAR_NAME>` | System only | Sync os.environ | NO |
| `vault://...` (legacy) | REJECTED | N/A | N/A |

### Testing

**SDK Contract Tests:** `tests/test_cus_vault_sdk_contract.py` (10 tests)

| Test Class | Tests | Purpose |
|------------|-------|---------|
| `TestCusCredentialServiceContract` | 3 | cus-vault:// async requirement, legacy vault:// rejection, plaintext rejection |
| `TestVaultFactoryContract` | 3 | Customer scope env vault rejection, VAULT_TOKEN requirement, system scope env vault allowed |
| `TestCredentialAccessRuleContract` | 2 | Default rule checker allows, DenyAll rule checker blocks |
| `TestCredentialReferenceFormat` | 2 | cus-vault:// format parsing, encrypted:// roundtrip |

**Run:** `PYTHONPATH=. python3 -m pytest tests/test_cus_vault_sdk_contract.py -v`

---

## PIN-521 Phase 4: MCPAuditEmitterPort Protocol (2026-02-03)

### mcp_tool_invocation_engine.py Changes

**Purpose:** Enable L5→L5 cross-domain dependency injection for MCP audit events.

**Change:** Replaced direct import of `MCPAuditEmitter` from logs domain with Protocol-based dependency injection.

**Before:**
```python
from app.hoc.cus.logs.L5_engines.audit_evidence import (
    MCPAuditEmitter,
    get_mcp_audit_emitter,
)

class McpToolInvocationEngine:
    def __init__(self, ..., audit_emitter: Optional[MCPAuditEmitter] = None):
        self._audit_emitter = audit_emitter or get_mcp_audit_emitter()
```

**After:**
```python
from app.hoc.cus.hoc_spine.schemas.protocols import MCPAuditEmitterPort

class McpToolInvocationEngine:
    def __init__(self, ..., audit_emitter: Optional[MCPAuditEmitterPort] = None):
        self._audit_emitter = audit_emitter or self._get_default_audit_emitter()

    @staticmethod
    def _get_default_audit_emitter() -> MCPAuditEmitterPort:
        """Lazy-load default audit emitter."""
        from app.hoc.cus.logs.L5_engines.audit_evidence import get_mcp_audit_emitter
        return get_mcp_audit_emitter()
```

**Key Points:**
- Type hint uses `MCPAuditEmitterPort` Protocol from hoc_spine
- Lazy import avoids top-level cross-domain L5→L5 dependency
- Production deployments can inject custom implementations via constructor
- CI allowlist includes this file pending full L4 handler injection

**Protocol Definition (hoc_spine/schemas/protocols.py):**
```python
@runtime_checkable
class MCPAuditEmitterPort(Protocol):
    async def emit_tool_requested(...) -> Any: ...
    async def emit_tool_allowed(...) -> Any: ...
    async def emit_tool_denied(...) -> Any: ...
    async def emit_tool_started(...) -> Any: ...
    async def emit_tool_completed(...) -> Any: ...
    async def emit_tool_failed(...) -> Any: ...
```

---

## PIN-520 L4 Injection Pattern (Iter3.1)

**Date:** 2026-02-06
**Reference:** PIN-520, TODO_ITER3.1.md

### L5 Purity Achieved

L5 engines in the integrations domain no longer import from `hoc_spine.orchestrator`. Dependencies are now injected by L4 callers.

### Changes Made

| File | Violation Removed | Pattern Applied |
|------|-------------------|-----------------|
| `cost_bridges_engine.py` | create_incident_from_cost_anomaly_sync import | Protocol + constructor injection |

### L4 Bridge Capabilities Added (integrations_bridge.py / IntegrationsEngineBridge)

| Capability | Purpose | Injected Into |
|------------|---------|---------------|
| `incident_creator_capability()` | Incident creation factory | CostBridgesEngine |

### Injection Point

```python
# L4 caller pattern
bridge = get_integrations_engine_bridge()

# Cost bridges engine with incident creator injection
engine = CostBridgesEngine(
    incident_creator=bridge.incident_creator_capability()
)
```

### Evidence

```bash
# Zero hoc_spine.orchestrator imports in L5
rg "from app\\.hoc\\.cus\\.hoc_spine\\.orchestrator" app/hoc/cus/integrations/L5_engines/
# Result: No matches found
```
