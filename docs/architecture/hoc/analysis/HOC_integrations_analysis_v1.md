# HOC Integrations Domain Analysis v1.0

**Domain:** integrations
**Date:** 2026-01-22
**Status:** 2 VIOLATIONS DETECTED (DEFERRED TO PHASE 5)

---

## Executive Judgment

**Overall quality:** High. This is a *serious* integrations domain, not a toy SDK layer.

**Primary strength:** Strong security invariants + deny-by-default mediation.

**Primary risk:** Audience boundary leakage, not logic errors.

**Secondary risk:** The domain is doing platform work while pretending to be customer-only.

**Phase-5 deferral decision:** Acceptable — but only because invariants are locked down now.

---

## 1. FILE STRUCTURE & LOC COUNTS

```
integrations/                                     (21 files, ~6,300 LOC)
├── __init__.py                                   (12 LOC) - CUSTOMER
├── facades/
│   ├── __init__.py                              (11 LOC) - CUSTOMER
│   ├── integrations_facade.py                   (484 LOC) - CUSTOMER
│   ├── connectors_facade.py                     (431 LOC) - L4 Domain Engine
│   ├── datasources_facade.py                    (445 LOC) - L4 Domain Engine
│   └── retrieval_facade.py                      (513 LOC) - L4 Domain Engine
├── engines/
│   ├── __init__.py                              (11 LOC) - CUSTOMER
│   ├── connector_registry.py                    (823 LOC) - L4 Domain Engine
│   ├── http_connector.py                        (364 LOC) - L4 Domain Engine
│   ├── mcp_connector.py                         (420 LOC) - L4 Domain Engine
│   ├── sql_gateway.py                           (461 LOC) - L4 Domain Engine
│   ├── server_registry.py                       (566 LOC) - **VIOLATION: AUDIENCE: INTERNAL**
│   ├── cus_integration_service.py               (551 LOC) - CUSTOMER
│   ├── external_response_service.py             (279 LOC) - L6 Platform Substrate
│   └── retrieval_mediator.py                    (466 LOC) - L4 Domain Engine
├── vault/
│   └── engines/
│       ├── cus_credential_service.py            (471 LOC) - L4 Domain Engine
│       ├── service.py                           (545 LOC) - L4 Domain Engine
│       └── vault.py                             (735 LOC) - **VIOLATION: AUDIENCE: INTERNAL**
├── schemas/
│   └── datasource_model.py                      (583 LOC) - L4 Domain Engine
└── drivers/
    └── __init__.py                              (11 LOC) - CUSTOMER (placeholder)
```

**Total:** ~6,300 LOC across 21 files

---

## 2. VIOLATIONS SUMMARY

| File | Header | Current Path | Required Path | Status |
|------|--------|--------------|---------------|--------|
| `server_registry.py` | `AUDIENCE: INTERNAL` | `customer/integrations/engines/` | `internal/platform/mcp/engines/` | DEFERRED |
| `vault.py` | `AUDIENCE: INTERNAL` | `customer/integrations/vault/engines/` | `internal/platform/vault/engines/` | DEFERRED |

**Rationale for Deferral:** These files are deep in subdirectories with existing callers. Moving them requires Phase 5 (Wire Imports) when all import paths will be updated systematically.

**Mitigation Applied:** Files marked as TRANSITIONAL with import guards.

---

## 3. FACADES ANALYSIS (5 files)

### 3.1 integrations_facade.py (484 LOC)
**Role:** Main facade for BYOK LLM integration management (Customer Console)
**Layer:** L4 Domain Engine
**Audience:** CUSTOMER

**Methods:**
- `create_integration()` - Create new LLM integration
- `get_integration()` - Get integration by ID
- `list_integrations()` - List all integrations
- `update_integration()` - Update integration settings
- `delete_integration()` - Delete integration
- `enable_integration()` - Enable integration
- `disable_integration()` - Disable integration
- `test_integration()` - Test credentials health
- `get_limits_status()` - Get usage vs limits

**Exports:** `IntegrationsFacade`, `get_integrations_facade()`

### 3.2 connectors_facade.py (431 LOC)
**Role:** Connector operations (HTTP, SQL, MCP, Vector, File, Serverless)
**Layer:** L4 Domain Engine

**Methods:**
- `create_connector()` - Register new connector
- `get_connector()` - Get connector by ID
- `list_connectors()` - List connectors
- `connect()` / `disconnect()` - Connection lifecycle
- `execute()` - Execute connector action
- `health_check()` - Check connector health
- `get_statistics()` - Get connector stats

**Exports:** `ConnectorsFacade`, `get_connectors_facade()`

### 3.3 datasources_facade.py (445 LOC)
**Role:** Data source operations (Database, Document, File, Vector, API, Stream)
**Layer:** L4 Domain Engine

**Methods:**
- `register_datasource()` - Register new data source
- `get_datasource()` / `list_datasources()` - Read operations
- `update_datasource()` / `delete_datasource()` - Update/Delete
- `activate()` / `deactivate()` - Lifecycle
- `get_statistics()` - Get stats

**Exports:** `DatasourcesFacade`, `get_datasources_facade()`

### 3.4 retrieval_facade.py (513 LOC)
**Role:** Mediated data retrieval with policy enforcement (GAP-094)
**Layer:** L4 Domain Engine

**DTOs:**
- `AccessResult` - Result of mediated data access
- `PlaneInfo` - Knowledge plane information
- `EvidenceInfo` - Evidence record information

**Methods:**
- `access_data()` - Mediated access (deny-by-default)
- `list_planes()` / `register_plane()` / `get_plane()` - Plane management
- `list_evidence()` / `get_evidence()` / `record_evidence()` - Evidence tracking

**Exports:** `RetrievalFacade`, `get_retrieval_facade()`

---

## 4. ENGINES ANALYSIS (9 files)

### 4.1 connector_registry.py (823 LOC)
**Role:** Connector management and registration (GAP-057, GAP-061/062/064)
**Layer:** L4 Domain Engine

**Enums:**
- `ConnectorType` - HTTP, SQL, MCP, VECTOR, FILE, SERVERLESS, STREAM, CUSTOM
- `ConnectorStatus` - REGISTERED, CONFIGURING, READY, CONNECTED, DISCONNECTED, ERROR, DEPRECATED
- `ConnectorCapability` - READ, WRITE, QUERY, STREAM, BATCH, TRANSACTION, SEARCH, VECTOR_SEARCH

**Classes:**
- `ConnectorConfig` - Base configuration
- `ConnectorError` - Error class
- `BaseConnector` (ABC) - Abstract base with connect/disconnect/health_check
- `VectorConnector` (GAP-061) - Vector database connector
- `FileConnector` (GAP-062) - File storage connector
- `ServerlessConnector` (GAP-064) - Serverless function connector
- `ConnectorStats` - Statistics dataclass
- `ConnectorRegistry` - Main registry class

**Exports:** `ConnectorRegistry`, `get_connector_registry()`, helper functions

**Note:** Large file (~800 LOC) but expected gravity for integration hub. Cohesion > file size.

### 4.2 http_connector.py (364 LOC)
**Role:** Machine-controlled HTTP connector (GAP-059) - NOT LLM-controlled
**Layer:** L4 Domain Engine

**Security Model:**
- Base URL: Machine-controlled (from connector config)
- Auth: Machine-controlled (from vault)
- Endpoints: Machine-controlled (action → path mapping)
- Payload: LLM-controlled but validated against schema

**Classes:**
- `HttpMethod` - GET, POST, PUT, PATCH, DELETE
- `EndpointConfig` - Single endpoint configuration
- `HttpConnectorConfig` - Connector configuration
- `HttpConnectorService` - Governed HTTP access
- `HttpConnectorError`, `RateLimitExceededError`

**Acceptance Criteria:** AC-059-01 through AC-059-09 (all checked)

### 4.3 mcp_connector.py (420 LOC)
**Role:** Model Context Protocol tool invocation with governance (GAP-063)
**Layer:** L4 Domain Engine

**Security Model:**
- Tool allowlist: Machine-controlled
- Server URL: Machine-controlled
- Authentication: Machine-controlled (from vault)
- Parameter validation: Against JSON Schema

**Classes:**
- `McpToolDefinition` - Tool definition
- `McpConnectorConfig` - Connector configuration
- `McpConnectorService` - Governed MCP tool invocation
- `McpConnectorError`, `McpApprovalRequiredError`, `McpSchemaValidationError`, `McpRateLimitExceededError`

**Acceptance Criteria:** AC-063-01 through AC-063-09 (all checked)

### 4.4 sql_gateway.py (461 LOC)
**Role:** Template-based SQL queries - NO raw SQL from LLM (GAP-060)
**Layer:** L4 Domain Engine

**Security Invariant:** LLM NEVER sees or constructs SQL. SQL comes from pre-registered, audited templates.

**Classes:**
- `ParameterType` - STRING, INTEGER, FLOAT, BOOLEAN, DATE, TIMESTAMP, UUID, LIST_*
- `ParameterSpec` - Parameter specification
- `QueryTemplate` - SQL template definition
- `SqlGatewayConfig` - Gateway configuration
- `SqlGatewayService` - Governed SQL access
- `SqlGatewayError`, `SqlInjectionAttemptError`

**Acceptance Criteria:** AC-060-01 through AC-060-09 (all checked)

### 4.5 server_registry.py (566 LOC) - TRANSITIONAL
**Role:** Registry for external MCP servers (GAP-141)
**Layer:** L4 Domain Engine
**AUDIENCE:** INTERNAL (will migrate to internal/platform/mcp/engines/ in Phase 5)

**Classes:**
- `MCPServerStatus` - PENDING, ACTIVE, DEGRADED, OFFLINE, SUSPENDED
- `MCPCapability` - TOOLS, RESOURCES, PROMPTS, SAMPLING
- `MCPTool` - Tool exposed by MCP server
- `MCPServer` - Registered MCP server
- `MCPRegistrationResult` - Registration result
- `MCPServerRegistry` - Main registry

**Methods:**
- `register_server()` / `unregister_server()` - Registration
- `get_server()` / `list_servers()` - Read
- `get_tools()` / `get_tool()` / `refresh_tools()` - Tool management
- `check_health()` - Health monitoring

**Exports:** `MCPServerRegistry`, `get_mcp_registry()`, `configure_mcp_registry()`

### 4.6 cus_integration_service.py (551 LOC)
**Role:** Business logic for Customer Integration domain (LLM BYOK)
**Layer:** L4 Domain Engine
**AUDIENCE:** CUSTOMER

**State Machine:**
```
created -> enabled -> disabled -> enabled (cycle)
created -> deleted (terminal)
enabled -> deleted (terminal)
disabled -> deleted (terminal)
```

**Class:** `CusIntegrationService`

**Methods:**
- CREATE: `create_integration()`
- READ: `get_integration()`, `list_integrations()`
- UPDATE: `update_integration()`
- DELETE: `delete_integration()` (soft delete)
- LIFECYCLE: `enable_integration()`, `disable_integration()`
- HEALTH: `test_credentials()`
- LIMITS: `get_limits_status()`

### 4.7 external_response_service.py (279 LOC)
**Role:** External response persistence and interpretation (Phase E FIX-04)
**Layer:** L6 Platform Substrate

**Contract:**
- Every external response has explicit interpretation owner
- L3 adapters never interpret - only record raw data
- L4 engines are the only authority for interpretation
- L5/L2 never see raw_response - only interpreted_value

**Class:** `ExternalResponseService`

**Methods:**
- `record_raw_response()` - L3 → L6 write
- `interpret()` - L4 → L6 write
- `get_raw_for_interpretation()` - For L4 engines
- `get_interpreted()` - L5/L2 ← L6 read
- `get_pending_interpretations()` - Find work needing interpretation

**Note:** L6 placement is correct - enforces platform-wide contract.

### 4.8 retrieval_mediator.py (466 LOC) - NON-NEGOTIABLE
**Role:** CENTRAL CHOKE POINT for all external data access (GAP-065)
**Layer:** L4 Domain Engine

**Invariant:** Deny-by-default. All access blocked unless explicitly allowed.

**Flow:**
1. Receive access request (plane_id, action, payload)
2. Tenant isolation check
3. Policy check (deny-by-default)
4. Connector resolution (plane → data source)
5. Execute access through connector
6. Emit retrieval evidence
7. Return result

**Classes:**
- `MediationAction` - QUERY, RETRIEVE, SEARCH, LIST
- `MediatedResult` - Result of mediated access
- `PolicyCheckResult` - Policy check result
- `EvidenceRecord` - Evidence for audit
- `MediationDeniedError` - Access denied error
- Protocols: `Connector`, `ConnectorRegistry`, `PolicyChecker`, `EvidenceService`
- `RetrievalMediator` - Main class

**Exports:** `RetrievalMediator`, `get_retrieval_mediator()`, `configure_retrieval_mediator()`

**Acceptance Criteria:** AC-065-01 through AC-065-05 (all checked)

**GOVERNANCE:** This file is non-negotiable infrastructure logic. No refactor, no split, no "simplification".

---

## 5. VAULT SUBDOMAIN ANALYSIS (3 files)

### 5.1 cus_credential_service.py (471 LOC)
**Role:** Credential encryption and vault integration for customer LLM integrations
**Layer:** L4 Domain Engine
**AUDIENCE:** CUSTOMER

**Security Principles:**
1. NO PLAINTEXT PERSISTENCE - All stored credentials are encrypted
2. ROTATION-READY - Credentials can be rotated without downtime
3. AUDIT TRAIL - All credential access is logged
4. MINIMAL EXPOSURE - Decryption only at point of use

**Credential Reference Formats:**
- `vault://<path>` - HashiCorp Vault reference
- `encrypted://<id>` - Locally encrypted (AES-256-GCM)
- `env://<var_name>` - Environment variable (dev only)

**Class:** `CusCredentialService`

**Methods:**
- `encrypt_credential()` / `decrypt_credential()` - Encryption operations
- `resolve_credential()` - Resolve reference to plaintext
- `rotate_credential()` - Credential rotation
- `validate_credential_format()` - Format validation
- `mask_credential()` - Safe masking for logs
- `generate_master_key()` - Generate new master key

### 5.2 service.py (545 LOC)
**Role:** High-level credential service with validation and auditing (GAP-171)
**Layer:** L4 Domain Engine

**Class:** `CredentialService`

**Features:**
- Credential CRUD with validation
- Expiration checking
- Access auditing
- Rotation support

**Methods:**
- `store_credential()` / `get_credential()` / `get_secret_value()`
- `list_credentials()` / `update_credential()` / `delete_credential()`
- `rotate_credential()`
- `get_expiring_credentials()` / `get_rotatable_credentials()`
- `get_access_log()` - Audit log retrieval

### 5.3 vault.py (735 LOC) - TRANSITIONAL
**Role:** Credential vault abstraction with multiple provider support (GAP-171)
**Layer:** L4 Domain Engine
**AUDIENCE:** INTERNAL (will migrate to internal/platform/vault/engines/ in Phase 5)

**Supported Providers:**
- HashiCorp Vault (production)
- AWS Secrets Manager (production) - TODO
- Environment variables (development only)

**Enums:**
- `VaultProvider` - HASHICORP, AWS_SECRETS, ENV
- `CredentialType` - API_KEY, OAUTH, DATABASE, BEARER_TOKEN, BASIC_AUTH, SSH_KEY, CERTIFICATE, CUSTOM

**Classes:**
- `CredentialMetadata` - Metadata without secrets
- `CredentialData` - Full credential with secrets
- `CredentialVault` (ABC) - Abstract vault interface
- `HashiCorpVault` - HashiCorp Vault implementation
- `EnvCredentialVault` - Development-only env vault

**Factory:** `create_credential_vault()` - Creates appropriate vault based on config

---

## 6. SCHEMAS ANALYSIS (1 file)

### 6.1 datasource_model.py (583 LOC)
**Role:** Customer data source models and registry (GAP-055)
**Layer:** L4 Domain Engine

**Enums:**
- `DataSourceType` - DATABASE, DOCUMENT, FILE, VECTOR, API, STREAM, CUSTOM
- `DataSourceStatus` - PENDING, CONFIGURING, ACTIVE, INACTIVE, ERROR, DEPRECATED

**Classes:**
- `DataSourceConfig` - Connection configuration
- `CustomerDataSource` - Data source representation
- `DataSourceError` - Error class
- `DataSourceStats` - Statistics
- `DataSourceRegistry` - Registry for managing sources

**Exports:** `DataSourceRegistry`, `get_datasource_registry()`, helper functions

---

## 7. LAYER DISTRIBUTION

| Layer | Files | Purpose |
|-------|-------|---------|
| L4 Domain Engine | 17 | Business logic, facades, registries, services |
| L6 Platform Substrate | 1 | external_response_service.py |
| Placeholder | 3 | __init__.py files |

---

## 8. CROSS-DOMAIN DEPENDENCIES

**Imports FROM integrations:**
- `policies/` - Policy checking via `PolicyChecker` protocol
- `logs/` - Evidence recording via `EvidenceService` protocol
- `general/` - Cross-domain coordination

**Imports INTO integrations:**
- `app/models/cus_models` - CusIntegration, CusLLMUsage, CusUsageDaily
- `app/schemas/cus_schemas` - CusLimitsStatus
- `app/models/external_response` - ExternalResponse, InterpretedResponse
- `app/db` - Database engine

---

## 9. DOMAIN PERSONA DECLARATION

Integrations serves three personas:

| Persona | Scope | Key Files |
|---------|-------|-----------|
| **CUSTOMER CONSOLE** | BYOK LLM integrations, datasources, limits | `cus_integration_service.py`, `integrations_facade.py` |
| **PLATFORM RUNTIME** | Connector registries, lifecycle, health | `connector_registry.py`, `*_connector.py` |
| **MEDIATION LAYER** | Deny-by-default retrieval, evidence emission | `retrieval_mediator.py`, `retrieval_facade.py` |

Some engines are transitional and will migrate to internal/ in Phase 5.

---

## 10. GOVERNANCE DECLARATIONS

### INV-INT-001: LLM Never Constructs Raw SQL
**Enforcement:** `sql_gateway.py` - template-only queries
**Violation:** BLOCKING - any raw SQL from LLM is rejected

### INV-INT-002: LLM Never Controls Base URL
**Enforcement:** `http_connector.py` - machine-controlled base URLs
**Violation:** BLOCKING - base URL must come from connector config

### INV-INT-003: Deny-by-Default Mediation
**Enforcement:** `retrieval_mediator.py` - policy check before execution
**Violation:** BLOCKING - no policy checker configured = access denied

### INV-INT-004: Tenant Isolation
**Enforcement:** All connectors - tenant_id verification on every operation
**Violation:** BLOCKING - cross-tenant access raises MediationDeniedError

### INV-INT-005: No Plaintext Credentials
**Enforcement:** `cus_credential_service.py` - AES-256-GCM encryption
**Violation:** BLOCKING - raw API keys rejected by validate_credential_format()

### INV-INT-006: INTERNAL Files Are Quarantined
**Enforcement:** Import guards on server_registry.py, vault.py
**Violation:** BLOCKING - new customer-facing imports forbidden

---

## 11. GOVERNANCE DECISIONS

### PRESERVE (Do Not Touch)

| Item | Rationale |
|------|-----------|
| `retrieval_mediator.py` | Non-negotiable infrastructure. No refactor, no split. |
| Security invariants (INV-INT-001 to INV-INT-005) | Actually enforced in code. Freeze as law. |
| `connector_registry.py` size | Expected gravity. Cohesion > file size. |
| `external_response_service.py` placement | Correct L6 position for platform contract. |
| Vault subdomain design | Customer vs provider split is correct. |
| Domain scope boundaries | Mediation, connectors, BYOK - not policy or audit. |

### ACT (Required Now)

| Action | Status |
|--------|--------|
| Document transitional files | DONE |
| Lock import discipline | DONE |
| Add domain persona note | DONE |
| Freeze invariants as governance | DONE |

### DO NOT DO

| Forbidden Action | Why |
|------------------|-----|
| Split domain by connector type | Only if plugin system needed |
| Extract mediation into general/ | Mediation belongs here |
| Collapse customer + internal credential logic | Abstraction boundary is correct |
| Move files without fixing imports globally | Structure is stable |
| Allow new customer imports to INTERNAL files | Boundary erosion risk |
| Refactor retrieval_mediator.py | It's doing the right job |

---

## 12. CROSS-DOMAIN CONTRACTS

| Consumer | Contract | Binding |
|----------|----------|---------|
| **Policies** | `PolicyChecker` protocol | Injected into RetrievalMediator |
| **Logs** | `EvidenceService` protocol | Injected into RetrievalMediator |
| **General** | Cross-domain coordination | Via facades only |

---

## 13. PHASE 5 SAFE MOVE PLAN

| File | Current | Target | Pre-condition |
|------|---------|--------|---------------|
| `server_registry.py` | `customer/integrations/engines/` | `internal/platform/mcp/engines/` | All callers updated |
| `vault.py` | `customer/integrations/vault/engines/` | `internal/platform/vault/engines/` | All callers updated |

**Import discipline locked NOW** so Phase 5 move is mechanical, not traumatic.

---

## 14. REQUIRED ACTIONS SUMMARY

| Priority | Action | Status |
|----------|--------|--------|
| P0 | Document transitional files with governance comments | DONE |
| P0 | Add domain persona declaration to __init__.py | DONE |
| P0 | Freeze invariants in this document | DONE |
| DEFERRED | Move server_registry.py to internal/ | Phase 5 |
| DEFERRED | Move vault.py to internal/ | Phase 5 |

---

## 15. EXPORTS SUMMARY

### Facades
- `IntegrationsFacade`, `get_integrations_facade()`
- `ConnectorsFacade`, `get_connectors_facade()`
- `DatasourcesFacade`, `get_datasources_facade()`
- `RetrievalFacade`, `get_retrieval_facade()`

### Engines
- `ConnectorRegistry`, `get_connector_registry()`
- `HttpConnectorService`, `HttpConnectorConfig`
- `McpConnectorService`, `McpConnectorConfig`, `McpToolDefinition`
- `SqlGatewayService`, `SqlGatewayConfig`, `QueryTemplate`
- `MCPServerRegistry`, `get_mcp_registry()` (TRANSITIONAL)
- `CusIntegrationService`
- `ExternalResponseService`, `record_external_response()`, `interpret_response()`
- `RetrievalMediator`, `get_retrieval_mediator()`, `configure_retrieval_mediator()`

### Vault
- `CusCredentialService`
- `CredentialService`, `CredentialAccessRecord`
- `CredentialVault`, `HashiCorpVault`, `EnvCredentialVault`, `create_credential_vault()` (TRANSITIONAL)
- `CredentialType`, `CredentialMetadata`, `CredentialData`

### Schemas
- `DataSourceRegistry`, `get_datasource_registry()`
- `CustomerDataSource`, `DataSourceConfig`, `DataSourceType`, `DataSourceStatus`
