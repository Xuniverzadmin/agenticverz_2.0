# HOC Integrations Domain — Deep Audit Report

**Audit Date:** 2026-01-23
**Auditor:** Claude (rigorous line-by-line analysis)
**Scope:** `houseofcards/customer/integrations/` — WITHIN DOMAIN ONLY
**Status:** FINDINGS IDENTIFIED

---

## 1. DOMAIN STRUCTURE

```
houseofcards/customer/integrations/
├── __init__.py
├── drivers/
│   └── __init__.py
├── engines/
│   ├── __init__.py
│   ├── connector_registry.py      (823 lines)
│   ├── cus_integration_service.py (551 lines)
│   ├── external_response_service.py (279 lines)
│   ├── http_connector.py          (364 lines)
│   ├── mcp_connector.py           (420 lines)
│   ├── retrieval_mediator.py      (466 lines)
│   ├── server_registry.py         (574 lines)
│   └── sql_gateway.py             (461 lines)
├── facades/
│   ├── __init__.py
│   ├── connectors_facade.py       (431 lines)
│   ├── datasources_facade.py      (445 lines)
│   ├── integrations_facade.py     (484 lines)
│   └── retrieval_facade.py        (513 lines)
├── schemas/
│   ├── __init__.py
│   └── datasource_model.py        (583 lines)
└── vault/
    └── engines/
        ├── cus_credential_service.py (471 lines)
        ├── service.py             (545 lines)
        └── vault.py               (743 lines)
```

**Total Files:** 16 substantive Python files (excluding `__init__.py`)
**Total Lines:** ~6,695 lines

---

## 2. FILE INVENTORY WITH LINE COUNTS

### 2.1 Facades (4 files)

| File | Lines | Purpose |
|------|-------|---------|
| integrations_facade.py | 484 | Integration CRUD operations |
| datasources_facade.py | 445 | Data source management |
| retrieval_facade.py | 513 | Retrieval operations |
| connectors_facade.py | 431 | Connector operations |

### 2.2 Engines (8 files)

| File | Lines | Purpose |
|------|-------|---------|
| connector_registry.py | 823 | Connector registry and lifecycle |
| cus_integration_service.py | 551 | Customer integration CRUD |
| external_response_service.py | 279 | External response handling |
| http_connector.py | 364 | HTTP/REST connector |
| mcp_connector.py | 420 | Model Context Protocol connector |
| retrieval_mediator.py | 466 | Mediates retrieval requests |
| server_registry.py | 574 | MCP server registry |
| sql_gateway.py | 461 | Template-based SQL gateway |

### 2.3 Vault Engines (3 files)

| File | Lines | Purpose |
|------|-------|---------|
| cus_credential_service.py | 471 | AES-256-GCM credential encryption |
| service.py | 545 | High-level credential service with audit |
| vault.py | 743 | Vault abstraction (HashiCorp, Env) |

### 2.4 Schemas (1 file)

| File | Lines | Purpose |
|------|-------|---------|
| datasource_model.py | 583 | CustomerDataSource model and registry |

---

## 3. ARTIFACT CATALOG

### 3.1 Enums

| Enum | File | Lines | Values |
|------|------|-------|--------|
| DataSourceType | datasource_model.py | 22-31 | DATABASE, DOCUMENT, FILE, VECTOR, API, STREAM, CUSTOM |
| DataSourceStatus | datasource_model.py | 34-42 | PENDING, CONFIGURING, ACTIVE, INACTIVE, ERROR, DEPRECATED |
| ConnectorType | connector_registry.py | 55-64 | HTTP, SQL, MCP, VECTOR, FILE, SERVERLESS, STREAM, CUSTOM |
| ConnectorStatus | connector_registry.py | 67-76 | REGISTERED, CONFIGURING, READY, CONNECTED, DISCONNECTED, ERROR, DEPRECATED |
| MCPServerStatus | server_registry.py | 53-58 | PENDING, ACTIVE, DEGRADED, OFFLINE, SUSPENDED |
| ParameterType | sql_gateway.py | 61-72 | STRING, INTEGER, FLOAT, BOOLEAN, DATE, TIMESTAMP, UUID, LIST_STRING, LIST_INT |
| VaultProvider | vault.py | 42-48 | HASHICORP, AWS_SECRETS, ENV |
| CredentialType | vault.py | 50-60 | API_KEY, OAUTH, DATABASE, BEARER_TOKEN, BASIC_AUTH, SSH_KEY, CERTIFICATE, CUSTOM |

### 3.2 Dataclasses

| Dataclass | File | Lines | Fields |
|-----------|------|-------|--------|
| **Credential** | http_connector.py | 99-103 | value, expires_at |
| **Credential** | mcp_connector.py | 90-94 | value, expires_at |
| **Credential** | sql_gateway.py | 114-118 | value, expires_at |
| DataSourceConfig | datasource_model.py | 45-102 | connection_string, host, port, etc. |
| CustomerDataSource | datasource_model.py | 125-254 | source_id, tenant_id, name, etc. |
| DataSourceStats | datasource_model.py | 280-308 | total_sources, active_sources, etc. |
| EndpointConfig | http_connector.py | 73-84 | path, method, headers, etc. |
| HttpConnectorConfig | http_connector.py | 86-97 | id, name, base_url, etc. |
| McpToolDefinition | mcp_connector.py | 63-72 | name, description, input_schema, etc. |
| McpConnectorConfig | mcp_connector.py | 75-88 | id, name, server_url, etc. |
| ParameterSpec | sql_gateway.py | 74-85 | name, param_type, required, etc. |
| QueryTemplate | sql_gateway.py | 87-98 | id, name, description, sql, etc. |
| SqlGatewayConfig | sql_gateway.py | 100-112 | id, name, connection_string_ref, etc. |
| ConnectorConfig | connector_registry.py | 78-99 | connector_id, connector_type, tenant_id, etc. |
| ConnectorInstance | connector_registry.py | 101-140 | config, status, health_state, etc. |
| MCPServerConfig | server_registry.py | 60-78 | server_id, name, url, etc. |
| MCPServerInstance | server_registry.py | 80-127 | config, status, health_state, etc. |
| CredentialMetadata | vault.py | 63-81 | credential_id, tenant_id, name, etc. |
| CredentialData | vault.py | 83-97 | metadata, secret_data |
| CredentialAccessRecord | service.py | 37-48 | credential_id, tenant_id, accessor_id, etc. |

### 3.3 Protocols

| Protocol | File | Lines | Methods |
|----------|------|-------|---------|
| **CredentialService** | http_connector.py | 106-112 | get(credential_ref) -> Credential |
| **CredentialService** | mcp_connector.py | 97-103 | get(credential_ref) -> Credential |
| **CredentialService** | sql_gateway.py | 121-127 | get(credential_ref) -> Credential |
| Connector | connector_registry.py | 142-160 | id, execute(action, payload, tenant_id) |

### 3.4 Classes

| Class | File | Lines | Type |
|-------|------|-------|------|
| DataSourceRegistry | datasource_model.py | 311-530 | Engine |
| DataSourceError | datasource_model.py | 257-277 | Exception |
| HttpConnectorError | http_connector.py | 115-119 | Exception |
| HttpConnectorService | http_connector.py | 121-275 | Engine |
| McpConnectorError | mcp_connector.py | 106-111 | Exception |
| McpApprovalRequiredError | mcp_connector.py | 114-119 | Exception |
| McpRateLimitExceededError | mcp_connector.py | 122-127 | Exception |
| McpSchemaValidationError | mcp_connector.py | 130-135 | Exception |
| McpConnectorService | mcp_connector.py | 138-419 | Engine |
| SqlGatewayError | sql_gateway.py | 130-132 | Exception |
| SqlInjectionAttemptError | sql_gateway.py | 135-137 | Exception |
| SqlGatewayService | sql_gateway.py | 140-456 | Engine |
| ConnectorRegistry | connector_registry.py | 162-823 | Engine |
| MCPServerRegistry | server_registry.py | 129-574 | Engine |
| CredentialVault | vault.py | 99-257 | ABC |
| HashiCorpVault | vault.py | 259-552 | Engine |
| EnvCredentialVault | vault.py | 555-719 | Engine |
| CusCredentialService | cus_credential_service.py | 48-471 | Engine |
| CredentialService | service.py | 51-545 | Engine |

---

## 4. DUPLICATE ANALYSIS

### 4.1 CONFIRMED DUPLICATES

#### INT-DUP-001: `Credential` Dataclass (3 copies)

**SEVERITY:** HIGH — Authority-bearing type duplicated across 3 connector files

| Location | Lines | Definition |
|----------|-------|------------|
| http_connector.py | 99-103 | `@dataclass class Credential: value: str; expires_at: Optional[datetime] = None` |
| mcp_connector.py | 90-94 | `@dataclass class Credential: value: str; expires_at: Optional[datetime] = None` |
| sql_gateway.py | 114-118 | `@dataclass class Credential: value: str; expires_at: Optional[datetime] = None` |

**Evidence (verbatim from files):**

```python
# http_connector.py lines 99-103
@dataclass
class Credential:
    """Credential from vault."""
    value: str
    expires_at: Optional[datetime] = None
```

```python
# mcp_connector.py lines 90-94
@dataclass
class Credential:
    """Credential from vault."""
    value: str
    expires_at: Optional[datetime] = None
```

```python
# sql_gateway.py lines 114-118
@dataclass
class Credential:
    """Credential from vault."""
    value: str
    expires_at: Optional[datetime] = None
```

**Overlap:** 100% identical (name, fields, docstring, types)

---

#### INT-DUP-002: `CredentialService` Protocol (3 copies)

**SEVERITY:** HIGH — Authority-bearing protocol duplicated across 3 connector files

| Location | Lines | Definition |
|----------|-------|------------|
| http_connector.py | 106-112 | `@runtime_checkable class CredentialService(Protocol): async def get(...)` |
| mcp_connector.py | 97-103 | `@runtime_checkable class CredentialService(Protocol): async def get(...)` |
| sql_gateway.py | 121-127 | `@runtime_checkable class CredentialService(Protocol): async def get(...)` |

**Evidence (verbatim from files):**

```python
# http_connector.py lines 106-112
@runtime_checkable
class CredentialService(Protocol):
    """Protocol for credential service."""

    async def get(self, credential_ref: str) -> Credential:
        """Get credential from vault."""
        ...
```

```python
# mcp_connector.py lines 97-103
@runtime_checkable
class CredentialService(Protocol):
    """Protocol for credential service."""

    async def get(self, credential_ref: str) -> Credential:
        """Get credential from vault."""
        ...
```

```python
# sql_gateway.py lines 121-127
@runtime_checkable
class CredentialService(Protocol):
    """Protocol for credential service."""

    async def get(self, credential_ref: str) -> Credential:
        """Get credential from vault."""
        ...
```

**Overlap:** 100% identical (name, method signature, docstring)

---

### 4.2 NOT DUPLICATES (Semantic Differentiation)

#### Status Enums — Different Semantics

| Enum | File | Values | Semantic Domain |
|------|------|--------|-----------------|
| DataSourceStatus | datasource_model.py | PENDING, CONFIGURING, ACTIVE, INACTIVE, ERROR, DEPRECATED | Data source lifecycle |
| ConnectorStatus | connector_registry.py | REGISTERED, CONFIGURING, READY, CONNECTED, DISCONNECTED, ERROR, DEPRECATED | Connector lifecycle |
| MCPServerStatus | server_registry.py | PENDING, ACTIVE, DEGRADED, OFFLINE, SUSPENDED | MCP server lifecycle |

**Analysis:** These share some overlapping values (CONFIGURING, ERROR, DEPRECATED) but represent distinct lifecycle states for different entity types. NOT duplicates.

#### Type Enums — Different Semantics

| Enum | File | Values | Semantic Domain |
|------|------|--------|-----------------|
| DataSourceType | datasource_model.py | DATABASE, DOCUMENT, FILE, VECTOR, API, STREAM, CUSTOM | Data source types |
| ConnectorType | connector_registry.py | HTTP, SQL, MCP, VECTOR, FILE, SERVERLESS, STREAM, CUSTOM | Connector types |

**Analysis:** Similar but distinct taxonomies. NOT duplicates.

#### Credential Services — Different Purposes

| Class | File | Purpose |
|-------|------|---------|
| CusCredentialService | cus_credential_service.py | AES-256-GCM encryption/decryption |
| CredentialService | service.py | High-level CRUD with auditing |

**Analysis:** Different responsibilities despite similar naming. NOT duplicates.

---

## 5. CROSS-FILE IMPORTS

### 5.1 Internal Imports

| From File | Imports | To File |
|-----------|---------|---------|
| service.py | CredentialData, CredentialMetadata, CredentialType, CredentialVault | vault.py |

### 5.2 Import Issues

**INT-FIND-001: No canonical source for connector Credential types**

The `Credential` dataclass and `CredentialService` Protocol are locally defined in each connector file instead of being imported from a shared location.

**Expected Pattern:**
```python
from app.houseofcards.customer.integrations.engines.vault.vault import (
    CredentialData,  # or a simplified Credential type
)
```

**Actual Pattern:**
```python
# Each file defines its own identical copy
@dataclass
class Credential:
    ...
```

---

## 6. HEADER COMPLIANCE

### 6.1 Files WITH AUDIENCE Header

| File | AUDIENCE | Line |
|------|----------|------|
| cus_integration_service.py | CUSTOMER | 2 |
| vault.py | INTERNAL | 2 |

### 6.2 Files WITHOUT AUDIENCE Header

| File | Status |
|------|--------|
| http_connector.py | Missing AUDIENCE |
| mcp_connector.py | Missing AUDIENCE |
| sql_gateway.py | Missing AUDIENCE |
| connector_registry.py | Missing AUDIENCE |
| server_registry.py | Missing AUDIENCE |
| retrieval_mediator.py | Missing AUDIENCE |
| external_response_service.py | Missing AUDIENCE |
| datasource_model.py | Missing AUDIENCE |
| cus_credential_service.py | Missing AUDIENCE |
| service.py | Missing AUDIENCE |
| All 4 facade files | Missing AUDIENCE |

**INT-FIND-002:** 14 of 16 files missing AUDIENCE header

---

## 7. FINDINGS AND RESOLUTIONS

| Issue ID | Type | Severity | Status | Description |
|----------|------|----------|--------|-------------|
| **INT-DUP-001** | Duplicate dataclass | HIGH | **QUARANTINED** | `Credential` dataclass in 3 files |
| **INT-DUP-002** | Duplicate protocol | HIGH | **QUARANTINED** | `CredentialService` Protocol in 3 files |
| INT-FIND-001 | Import pattern | MEDIUM | **RESOLVED** | No canonical source — canonical source created |
| INT-FIND-002 | Header compliance | LOW | DEFERRED | 14 files missing AUDIENCE header — hygiene sweep |

### 7.1 Resolution Details

#### INT-DUP-001 & INT-DUP-002: QUARANTINED (2026-01-23)

**Canonical Source Created:**
```
houseofcards/customer/integrations/engines/credentials/
├── __init__.py      # Package exports
├── types.py         # Credential dataclass (canonical)
└── protocol.py      # CredentialService protocol (canonical)
```

**Quarantine Artifacts Created:**
```
houseofcards/duplicate/integrations/
├── __init__.py
├── credential.py           # Frozen Credential copy
├── credential_service.py   # Frozen CredentialService copy
└── README.md
```

**Connectors Updated:**
- `http_connector.py` — Local definitions removed, imports from canonical
- `mcp_connector.py` — Local definitions removed, imports from canonical
- `sql_gateway.py` — Local definitions removed, imports from canonical

#### INT-FIND-001: RESOLVED

Resolved by canonical source creation. Connectors now import from:
```python
from app.houseofcards.customer.integrations.engines.credentials import (
    Credential,
    CredentialService,
)
```

#### INT-FIND-002: DEFERRED

Missing AUDIENCE headers to be addressed in separate hygiene sweep.

---

## 8. CANONICAL AUTHORITY DETERMINATION

### For INT-DUP-001 and INT-DUP-002

**Question:** Which file should be the canonical authority for `Credential` and `CredentialService`?

**Options:**

1. **vault/engines/vault.py** — Already has `CredentialData` and `CredentialMetadata`, but these have more fields than the simple `Credential` dataclass

2. **New shared file** — Create `engines/connector_credential.py` with the shared types

3. **One of the connector files** — Promote one as canonical, others import

**Recommendation:** Create a new canonical source file `engines/connector_credential.py` that exports the `Credential` dataclass and `CredentialService` Protocol. This keeps connector-specific types separate from the vault's more complex credential types.

---

## 9. AUDIT METHODOLOGY

1. Listed all Python files in domain
2. Read each file completely
3. Extracted all enums, dataclasses, protocols, classes with exact line numbers
4. Cross-compared definitions for identical or near-identical matches
5. Verified duplicates by reading relevant sections verbatim
6. Documented findings with exact evidence

---

## 10. RECOMMENDATIONS — COMPLETED

### Immediate Actions (Quarantine) — DONE

1. **INT-DUP-001 & INT-DUP-002:** ~~Create canonical source and quarantine duplicates~~ **COMPLETED 2026-01-23**

### Deferred Actions

1. ~~**INT-FIND-001:** Resolve as part of quarantine work~~ **RESOLVED** — Canonical source created
2. **INT-FIND-002:** Missing AUDIENCE headers — hygiene sweep (still pending)

---

## 11. CROSS-DOMAIN QUARANTINE STATUS

| Domain | Quarantine Count | Status |
|--------|------------------|--------|
| Policies | 4 | QUARANTINED |
| Incidents | TBD | — |
| Logs | 0 | CLEAN |
| Analytics | 1 | QUARANTINED |
| **Integrations** | **2** | **QUARANTINED** |

---

## 12. AUDIT TRAIL

| Date | Action | Actor |
|------|--------|-------|
| 2026-01-23 | Initial audit completed | Claude |
| 2026-01-23 | Policy guidance received | User |
| 2026-01-23 | Canonical source created: `engines/credentials/` | Claude |
| 2026-01-23 | Quarantine folder created: `duplicate/integrations/` | Claude |
| 2026-01-23 | Connectors updated (3 files) | Claude |
| 2026-01-23 | Audit report updated with resolutions | Claude |

---

**END OF AUDIT REPORT**
