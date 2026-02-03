# PIN-516: MCP Customer Integration

**Status:** IN PROGRESS
**Created:** 2026-02-03
**Category:** Feature
**Predecessor:** PIN-514 (Runtime Convergence), PIN-515 (Wiring Contract)

---

## Summary

Implement MCP (Model Context Protocol) server integration for customers, enabling AI runs to invoke external tools through governed, auditable channels.

---

## Customer Journey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MCP SERVER INTEGRATION FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. REGISTER        2. DISCOVER         3. CONFIGURE       4. INVOKE       │
│  ┌─────────┐       ┌─────────┐         ┌─────────┐       ┌─────────┐       │
│  │Customer │──────▶│ System  │────────▶│Customer │──────▶│ AI Run  │       │
│  │provides │       │discovers│         │allows/  │       │invokes  │       │
│  │MCP URL  │       │tools    │         │blocks   │       │tools    │       │
│  └─────────┘       └─────────┘         └─────────┘       └─────────┘       │
│       │                 │                   │                 │             │
│       ▼                 ▼                   ▼                 ▼             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      MONITORING LAYER                                   ││
│  │  Policy Checks │ Incidents │ Activity Log │ Audit Trail                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Plan

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 1 | L7 Models + L6 Driver (Persistence) | COMPLETE |
| Phase 2 | L5 Engine (Business Logic + Protocol) | COMPLETE |
| Phase 3 | L4 Handler + L2 API (Orchestration + HTTP) | COMPLETE |
| Phase 4 | Monitoring Integration (Policy/Incidents/Activity/Logs) | COMPLETE |

---

## Phase-1 Invariants (MANDATORY)

These invariants MUST be satisfied before Phase 1 is complete. Violation blocks Phase 2.

### INV-1: L7 Models Include Lifecycle + Versioning Fields

Models must support:
- **Status tracking**: ACTIVE, DEGRADED, OFFLINE, DELETED
- **Protocol versioning**: Capture MCP protocol version at discovery
- **Temporal fields**: discovered_at, last_health_check_at, deleted_at
- **Integrity hashes**: capabilities_hash, tool_hash, input_hash, output_hash
- **Governance**: created_by, policy_decision_id

**Rationale:** Without hashes + timestamps, MCP becomes non-auditable and non-governable.

### INV-2: L6 Driver Is Pure CRUD

L6 driver must contain:
- Deterministic database operations ONLY
- No HTTP calls
- No MCP protocol logic
- No health checks
- No JSON-RPC parsing

**Rationale:** Protocol logic belongs in L5. Mixing it into L6 violates layer topology.

### INV-3: Credentials Stored By Reference Only

- `McpServer` stores only `credential_ref: str` (opaque reference)
- Real secrets live in Vault/KMS/encrypted secrets table
- Credentials are NEVER stored in plaintext in the database
- Credentials are NEVER logged or included in error messages

**Rationale:** MCP servers are external, customer-owned infrastructure. Credential leakage is a platform-level breach.

### INV-4: Phase-1 Tests Prove Survivability

Tests must answer: "If the system restarts, can we still explain what MCP servers exist?"

Required test cases:
1. **Persistence**: Create server → restart → list servers → same result
2. **Tenant isolation**: Tenant A cannot read Tenant B servers
3. **Soft delete**: Deleted server not returned in list, but queryable for audit
4. **Tool upsert idempotency**: Same tool list twice → no duplicates

**Rationale:** Happy-path tests are insufficient. Durability and isolation must be proven first.

---

## Phase-1 Deliverables

| Layer | File | Purpose |
|-------|------|---------|
| L7 | `app/models/mcp_models.py` | SQLModel ORM classes |
| L6 | `app/hoc/cus/integrations/L6_drivers/mcp_driver.py` | Database CRUD operations |
| TEST | `tests/mcp/test_mcp_phase1.py` | Survivability tests |

---

## L7 Model Specifications

### McpServer

```python
class McpServer(SQLModel, table=True):
    __tablename__ = "mcp_servers"

    id: UUID
    tenant_id: UUID
    name: str
    url: str

    # Lifecycle
    status: Literal["PENDING", "ACTIVE", "DEGRADED", "OFFLINE", "DELETED"]
    protocol_version: Optional[str]

    # Temporal
    created_at: datetime
    discovered_at: Optional[datetime]
    last_health_check_at: Optional[datetime]
    deleted_at: Optional[datetime]

    # Governance
    created_by: UUID
    credential_ref: str  # Opaque vault reference, NEVER plaintext

    # Integrity
    capabilities_hash: Optional[str]  # SHA256 of capabilities JSON

    # Metadata
    transport: Literal["HTTP", "STDIO", "SSE"]
    tool_count: int
```

### McpTool

```python
class McpTool(SQLModel, table=True):
    __tablename__ = "mcp_tools"

    id: UUID
    server_id: UUID  # FK to mcp_servers

    name: str
    description: Optional[str]
    input_schema: dict
    output_schema: Optional[dict]

    # Governance
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    enabled: bool
    requires_approval: bool

    # Temporal
    discovered_at: datetime

    # Integrity
    tool_hash: str  # SHA256(name + input_schema)
```

### McpToolInvocation

```python
class McpToolInvocation(SQLModel, table=True):
    __tablename__ = "mcp_tool_invocations"

    id: UUID
    tool_id: UUID  # FK to mcp_tools
    server_id: UUID  # FK to mcp_servers
    tenant_id: UUID
    run_id: UUID

    # Outcome
    status: Literal["SUCCESS", "FAILURE", "BLOCKED", "TIMEOUT"]
    error_code: Optional[str]
    error_message: Optional[str]

    # Governance
    policy_decision_id: Optional[UUID]

    # Integrity
    input_hash: str  # SHA256 of input parameters
    output_hash: Optional[str]  # SHA256 of output (if success)

    # Temporal
    invoked_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
```

---

## L6 Driver Signatures

```python
# app/hoc/cus/integrations/L6_drivers/mcp_driver.py

class McpDriver:
    """Pure CRUD operations for MCP persistence. No protocol logic."""

    # Server operations
    async def create_server(self, server: McpServer) -> McpServer
    async def get_server(self, server_id: UUID) -> Optional[McpServer]
    async def get_server_by_url(self, tenant_id: UUID, url: str) -> Optional[McpServer]
    async def list_servers(self, tenant_id: UUID, include_deleted: bool = False) -> List[McpServer]
    async def update_server(self, server_id: UUID, **updates) -> McpServer
    async def soft_delete_server(self, server_id: UUID) -> None

    # Tool operations
    async def upsert_tools(self, server_id: UUID, tools: List[McpTool]) -> List[McpTool]
    async def get_tools(self, server_id: UUID, enabled_only: bool = True) -> List[McpTool]
    async def get_tool(self, tool_id: UUID) -> Optional[McpTool]
    async def update_tool(self, tool_id: UUID, **updates) -> McpTool

    # Invocation operations (append-only)
    async def record_invocation(self, invocation: McpToolInvocation) -> McpToolInvocation
    async def get_invocations(self, server_id: UUID, limit: int = 100) -> List[McpToolInvocation]
    async def get_invocation(self, invocation_id: UUID) -> Optional[McpToolInvocation]
```

---

## Phase-2 Deliverables (COMPLETE)

### L5 Engine

**File:** `app/hoc/cus/integrations/L5_engines/mcp_server_engine.py`

**McpServerEngine Methods:**

| Category | Methods |
|----------|---------|
| Registration | `register_server(tenant_id, name, url, ...)` |
| Discovery | `discover_tools(server_id)` |
| Health | `health_check(server_id)` |
| Server Mgmt | `get_server`, `list_servers`, `update_server`, `disable_server` |
| Tool Mgmt | `get_tools`, `enable_tool`, `disable_tool`, `set_tool_risk_level` |

**MCP Protocol Implementation:**

| Method | JSON-RPC Method | Purpose |
|--------|-----------------|---------|
| `_mcp_initialize` | `initialize` | Get capabilities and protocol version |
| `_mcp_list_tools` | `tools/list` | Get available tools with schemas |
| `_mcp_ping` | `ping` | Health check (falls back to initialize) |

**Automatic Risk Assessment:**

Tool risk levels are automatically assigned based on name keywords:

| Risk Level | Keywords |
|------------|----------|
| Critical | delete, remove, drop, destroy, kill |
| High | write, execute, run, shell, eval, create |
| Medium | update, modify, set, put, post |
| Low | read, get, list, search, query, fetch |

**Result Types:**

```python
@dataclass(frozen=True)
class McpRegistrationResult:
    server_id: str
    name: str
    url: str
    status: str
    discovery_triggered: bool

@dataclass(frozen=True)
class McpDiscoveryResult:
    server_id: str
    protocol_version: str
    capabilities: List[str]
    tools_found: int
    tools_added: int
    tools_updated: int
    errors: List[str]

@dataclass(frozen=True)
class McpHealthResult:
    server_id: str
    is_healthy: bool
    status: str
    latency_ms: int
    error: Optional[str]
```

---

---

## Phase-5 SDK Proposal (aos_sdk)

### Overview

The aos_sdk MCP integration enables customers to programmatically:
- Register and manage MCP servers
- Discover and configure tools
- Invoke tools through governed channels
- Monitor server health

### SDK Client Methods (aos_sdk_client.py)

```python
class AOSClient:
    # MCP Server Management
    def list_mcp_servers(self, tenant_id: Optional[str] = None) -> Dict:
        """List all registered MCP servers."""
        return self._request("GET", "/api/v1/mcp/servers")

    def register_mcp_server(
        self,
        name: str,
        url: str,
        credential_ref: Optional[str] = None,
        auto_discover: bool = True,
    ) -> Dict:
        """Register a new MCP server."""
        return self._request("POST", "/api/v1/mcp/servers", json={
            "name": name,
            "url": url,
            "credential_ref": credential_ref,
            "auto_discover": auto_discover,
        })

    def get_mcp_server(self, server_id: str) -> Dict:
        """Get MCP server details."""
        return self._request("GET", f"/api/v1/mcp/servers/{server_id}")

    def discover_mcp_tools(self, server_id: str) -> Dict:
        """Trigger tool discovery for a server."""
        return self._request("POST", f"/api/v1/mcp/servers/{server_id}/discover")

    def check_mcp_health(self, server_id: str) -> Dict:
        """Check health of an MCP server."""
        return self._request("POST", f"/api/v1/mcp/servers/{server_id}/health")

    def disable_mcp_server(self, server_id: str) -> Dict:
        """Disable (soft-delete) an MCP server."""
        return self._request("DELETE", f"/api/v1/mcp/servers/{server_id}")

    # MCP Tool Management
    def list_mcp_tools(self, server_id: str) -> Dict:
        """List tools for an MCP server."""
        return self._request("GET", f"/api/v1/mcp/servers/{server_id}/tools")

    def enable_mcp_tool(self, tool_id: str) -> Dict:
        """Enable a tool."""
        return self._request("POST", f"/api/v1/mcp/tools/{tool_id}/enable")

    def disable_mcp_tool(self, tool_id: str) -> Dict:
        """Disable a tool."""
        return self._request("POST", f"/api/v1/mcp/tools/{tool_id}/disable")

    def set_mcp_tool_risk(self, tool_id: str, risk_level: str) -> Dict:
        """Set tool risk level (low, medium, high, critical)."""
        return self._request("PUT", f"/api/v1/mcp/tools/{tool_id}/risk", json={
            "risk_level": risk_level,
        })

    # MCP Tool Invocation
    def invoke_mcp_tool(
        self,
        tool_id: str,
        input_params: Dict,
        run_id: Optional[str] = None,
    ) -> Dict:
        """Invoke an MCP tool (governed)."""
        return self._request("POST", f"/api/v1/mcp/tools/{tool_id}/invoke", json={
            "input": input_params,
            "run_id": run_id,
        })
```

### SDK Module (aos_sdk_mcp.py)

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class McpServerCreate(BaseModel):
    """Request to register an MCP server."""
    name: str
    url: str
    credential_ref: Optional[str] = None
    auto_discover: bool = True
    requires_approval: bool = True
    rate_limit_requests: Optional[int] = None
    tags: List[str] = Field(default_factory=list)

class McpServerResponse(BaseModel):
    """MCP server details."""
    server_id: str
    name: str
    url: str
    status: str  # pending, active, degraded, offline, disabled
    protocol_version: Optional[str]
    tool_count: int
    last_discovery_at: Optional[datetime]
    last_health_check_at: Optional[datetime]
    registered_at: datetime

class McpToolResponse(BaseModel):
    """MCP tool details."""
    tool_id: str
    server_id: str
    name: str
    description: Optional[str]
    input_schema: Dict
    risk_level: str  # low, medium, high, critical
    enabled: bool
    invocation_count: int
    discovered_at: datetime

class McpDiscoveryResponse(BaseModel):
    """Tool discovery result."""
    server_id: str
    protocol_version: str
    capabilities: List[str]
    tools_found: int
    tools_added: int
    tools_updated: int
    errors: List[str]

class McpHealthResponse(BaseModel):
    """Health check result."""
    server_id: str
    is_healthy: bool
    status: str
    latency_ms: int
    error: Optional[str]

class McpInvokeRequest(BaseModel):
    """Tool invocation request."""
    input: Dict
    run_id: Optional[str] = None

class McpInvokeResponse(BaseModel):
    """Tool invocation result."""
    invocation_id: str
    tool_id: str
    status: str  # success, failure, blocked, timeout
    output: Optional[Dict] = None
    error: Optional[str] = None
    duration_ms: int
    policy_decision: str  # allowed, blocked, flagged
```

### CLI Commands (aos_sdk_cli.py)

```bash
# List MCP servers
aos mcp list [--json]

# Register a new server
aos mcp register --name "My Server" --url "https://mcp.example.com"

# Get server details
aos mcp describe <server_id>

# Discover tools
aos mcp discover <server_id>

# Check health
aos mcp health <server_id>

# List tools
aos mcp tools <server_id>

# Enable/disable tool
aos mcp tool enable <tool_id>
aos mcp tool disable <tool_id>

# Set tool risk level
aos mcp tool risk <tool_id> --level high

# Invoke tool (for testing)
aos mcp invoke <tool_id> --input '{"param": "value"}'
```

### Usage Examples

```python
from aos_sdk import AOSClient

# Initialize client
client = AOSClient(api_key="your-api-key")

# Register MCP server
result = client.register_mcp_server(
    name="Code Analysis Server",
    url="https://mcp.codeanalysis.example.com",
    credential_ref="vault://mcp/codeanalysis-key",
)
server_id = result["server_id"]

# Check discovered tools
tools = client.list_mcp_tools(server_id)
for tool in tools["items"]:
    print(f"Tool: {tool['name']} (risk: {tool['risk_level']})")

# Adjust tool risk level
client.set_mcp_tool_risk(tools["items"][0]["tool_id"], "critical")

# Invoke a tool
response = client.invoke_mcp_tool(
    tool_id=tools["items"][0]["tool_id"],
    input_params={"file": "src/main.py"},
)
print(f"Result: {response['output']}")
```

---

## Phase-3 Deliverables (COMPLETE)

### L4 Handler

**File:** `app/hoc/cus/hoc_spine/orchestrator/handlers/mcp_handler.py`

**Operation:** `integrations.mcp_servers`

**Methods:**

| Method | Description |
|--------|-------------|
| `register_server` | Register a new MCP server |
| `get_server` | Get server details by ID |
| `list_servers` | List all servers for tenant |
| `discover_tools` | Discover tools from MCP server |
| `health_check` | Check MCP server health |
| `delete_server` | Soft-delete a server |
| `list_tools` | List tools for a server |
| `get_invocations` | List tool invocations |

### L2 API Routes

**File:** `app/hoc/api/cus/integrations/mcp_servers.py`

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/integrations/mcp-servers` | Register a new MCP server |
| GET | `/api/v1/integrations/mcp-servers` | List MCP servers for tenant |
| GET | `/api/v1/integrations/mcp-servers/{server_id}` | Get server details |
| POST | `/api/v1/integrations/mcp-servers/{server_id}/discover` | Discover tools |
| GET | `/api/v1/integrations/mcp-servers/{server_id}/health` | Health check |
| DELETE | `/api/v1/integrations/mcp-servers/{server_id}` | Soft-delete server |
| GET | `/api/v1/integrations/mcp-servers/{server_id}/tools` | List server tools |
| GET | `/api/v1/integrations/mcp-servers/{server_id}/invocations` | List invocations |

### Request/Response Models

```python
class McpServerRegisterRequest(BaseModel):
    name: str
    url: str
    description: Optional[str]
    transport: str  # stdio, http, sse
    credential_id: Optional[str]  # Vault reference
    metadata: Optional[Dict[str, Any]]

class McpServerResponse(BaseModel):
    server_id: str
    name: str
    url: str
    description: Optional[str]
    transport: str
    status: str
    credential_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]

class McpRegistrationResponse(BaseModel):
    server_id: str
    status: str
    tools_discovered: int
    error: Optional[str]

class McpDiscoveryResponse(BaseModel):
    server_id: str
    tools_discovered: int
    tools: List[Dict[str, Any]]
    error: Optional[str]

class McpHealthResponse(BaseModel):
    server_id: str
    healthy: bool
    latency_ms: Optional[float]
    error: Optional[str]
```

### Wiring

- **Handler Registration:** `app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py`
- **Router Registration:** `app/main.py`

---

## Phase-4 Deliverables (COMPLETE)

### MCP Tool Invocation Engine

**File:** `app/hoc/cus/integrations/L5_engines/mcp_tool_invocation_engine.py`

**McpToolInvocationEngine** orchestrates governed tool invocations:

| Feature | Implementation |
|---------|---------------|
| Policy Validation | `McpPolicyChecker` protocol (injectable, default permissive) |
| Audit Trail | `MCPAuditEmitter` from logs domain |
| Tool Execution | JSON-RPC `tools/call` method |
| Incident Creation | Optional `IncidentEngine` integration |
| Invocation Recording | Via `McpDriver.record_invocation()` |

**Invocation Flow:**

```
1. Validate server & tool exist
2. Emit audit: TOOL_INVOCATION_REQUESTED
3. Check policy (McpPolicyChecker)
4. Emit audit: TOOL_INVOCATION_ALLOWED or TOOL_INVOCATION_DENIED
5. If denied → record blocked invocation, return
6. Emit audit: TOOL_INVOCATION_STARTED
7. Execute tool via MCP JSON-RPC
8. Emit audit: TOOL_INVOCATION_COMPLETED or TOOL_INVOCATION_FAILED
9. Record invocation to database
10. If failed → create incident (optional)
11. Return result
```

**Result Type:**

```python
@dataclass(frozen=True)
class McpInvocationResult:
    invocation_id: str
    tool_id: str
    server_id: str
    status: str  # success, failure, blocked, timeout
    output: Optional[Dict[str, Any]]
    error_code: Optional[str]
    error_message: Optional[str]
    duration_ms: Optional[int]
    policy_decision: str  # allowed, blocked, flagged
    policy_id: Optional[str]
    incident_id: Optional[str]  # If incident was created
```

### L4 Handler Update

**Method Added:** `invoke_tool`

```python
elif method_name == "invoke_tool":
    # Governed invocation with policy, audit, incidents
    invocation_engine = McpToolInvocationEngine(driver=driver)
    result = await invocation_engine.invoke_tool(...)
```

### L2 API Endpoint

**Endpoint:** `POST /api/v1/integrations/mcp-servers/{server_id}/tools/{tool_id}/invoke`

**Request:**
```python
class McpInvokeRequest(BaseModel):
    input: Dict[str, Any]  # Tool parameters
    run_id: Optional[str]  # Run context
    step_index: Optional[int]
    actor_id: Optional[str]
    actor_type: str = "machine"
    trace_id: Optional[str]  # For correlation
```

**Response:**
```python
class McpInvokeResponse(BaseModel):
    invocation_id: str
    tool_id: str
    server_id: str
    status: str
    output: Optional[Dict[str, Any]]
    error_code: Optional[str]
    error_message: Optional[str]
    duration_ms: Optional[int]
    policy_decision: str
    policy_id: Optional[str]
    incident_id: Optional[str]
```

### Monitoring Integration Points

| Integration | Implementation |
|-------------|---------------|
| **Policy** | `McpPolicyChecker` protocol — injectable policy validation |
| **Audit** | `MCPAuditEmitter` — compliance-grade event chain |
| **Incidents** | Optional `IncidentEngine` — failure → incident creation |
| **Activity** | Invocation records in `mcp_tool_invocations` |

### MCPAuditEmitter Events

| Event Type | When Emitted |
|------------|--------------|
| `TOOL_INVOCATION_REQUESTED` | Invocation requested |
| `TOOL_INVOCATION_ALLOWED` | Policy allows |
| `TOOL_INVOCATION_DENIED` | Policy blocks |
| `TOOL_INVOCATION_STARTED` | Execution begins |
| `TOOL_INVOCATION_COMPLETED` | Success |
| `TOOL_INVOCATION_FAILED` | Failure |

---

## Phase-5+ Deferred Items

These items are NOT in Phases 1-4 or SDK proposal:

1. **Tool schema normalization** - MCP schemas vary; canonical shape deferred
2. **Tool version drift detection** - Re-discovery breaking change detection
3. **Rate limiting per MCP server** - Required before GA, not for persistence
4. **Health check scheduling** - Background job for periodic checks
5. **Real M19 policy integration** - Production policy rules for tool invocation gating

---

## Related Documents

- **PIN-514**: Runtime Convergence (M20 policy runtime)
- **PIN-515**: Production Wiring Contract (validator injection)
- **GAP-063**: MCP Connector Service (original gap item)
- **GAP-170**: MCP Servers Database Schema (migration 119)

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-02-03 | 1.0 | Initial PIN creation with Phase-1 invariants |
| 2026-02-03 | 1.1 | Phase 1 complete (L7 models, L6 driver) |
| 2026-02-03 | 1.2 | Phase 2 complete (L5 engine with MCP protocol) |
| 2026-02-03 | 1.3 | Phase 3 complete (L4 handler, L2 API routes) |
| 2026-02-03 | 1.4 | Phase 4 complete (monitoring: policy, audit, incidents) |
