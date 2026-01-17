# Connectivity Domain Audit

**Status:** PARTIALLY IMPLEMENTED
**Last Updated:** 2026-01-16
**Reference:** PIN-411 (Unified Facades)

---

## 0. Domain Characteristics

**Connectivity is a SECONDARY SIDEBAR section** (not a Core Lens domain).

**Two Sub-Sections:**
- **Integrations** - Connect external systems (LLM providers, tools, webhooks)
- **API Keys** - Authenticate SDK/CLI access to Agentiverz

**Customer Use Cases:**

| Section | What Customers Do |
|---------|-------------------|
| **Integrations** | Configure external LLM providers, webhooks, notification channels |
| **API Keys** | Generate keys for programmatic access via SDK/CLI |

---

## 1. Summary Status

| Component | Status | Details |
|-----------|--------|---------|
| **API Keys** | ✅ MOSTLY COMPLETE | Create, list, freeze/unfreeze, revoke |
| **Integrations** | ❌ NOT IMPLEMENTED | Customer console has no integration management |
| **Lifecycle Ops** | ⚠️ PARTIAL | Missing: rotation, health checks, validation endpoint |

---

## 2. How It Works with Agentiverz

### API Key Flow

```
Customer Console
       │
       ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/api-keys                  │
│  Creates key: aos_1234567890abcdef      │
│  Key shown ONCE, then hashed            │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  SDK/CLI Request                        │
│  Header: X-AOS-Key: aos_xxxxx           │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  AuthGateway                            │
│  1. Hash the provided key               │
│  2. Lookup by key_hash in DB            │
│  3. Check: active? not expired? not revoked? │
│  4. Extract scopes from permissions_json│
│  5. Return MachineCapabilityContext     │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Run Execution                          │
│  - Key validated per request            │
│  - Usage tracked (last_used_at, total_requests) │
│  - Rate limits enforced                 │
└─────────────────────────────────────────┘
```

### Integration Flow (NOT YET IMPLEMENTED)

```
Customer Console
       │
       ▼
┌─────────────────────────────────────────┐
│  Configure Integration                  │
│  - LLM Provider (API key, model)        │
│  - Webhook (URL, secret)                │
│  - Notification Channel                 │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  WorkerConfig (per-tenant)              │
│  - enabled: true/false                  │
│  - config_json: provider settings       │
│  - limits: max_runs_per_day             │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Run Execution                          │
│  - Worker uses tenant's integration config │
│  - Credentials fetched at runtime       │
└─────────────────────────────────────────┘
```

---

## 3. Lifecycle Management

### API Keys Lifecycle

| Operation | Status | Endpoint | Notes |
|-----------|--------|----------|-------|
| **CREATE** | ✅ IMPLEMENTED | `POST /api/v1/api-keys` | Full key shown ONCE |
| **LIST** | ✅ IMPLEMENTED | `GET /guard/keys` | Customer view (prefix only) |
| **DETAIL** | ✅ IMPLEMENTED | `GET /guard/keys/{id}` | Tenant-isolated |
| **FREEZE** | ✅ IMPLEMENTED | `POST /guard/keys/{id}/freeze` | Temporary block |
| **UNFREEZE** | ✅ IMPLEMENTED | `POST /guard/keys/{id}/unfreeze` | Resume access |
| **REVOKE** | ✅ IMPLEMENTED | `DELETE /api/v1/api-keys/{id}` | Permanent, irreversible |
| **ROTATE** | ❌ MISSING | - | No rotation endpoint |
| **TEST** | ❌ MISSING | - | No explicit validation endpoint |
| **UPDATE** | ⚠️ PARTIAL | - | Rename only, no scope changes |

### API Key Status Transitions

```
         ┌──────────────────────┐
         │       ACTIVE         │
         └──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌───────────────┐
│    FROZEN     │    │    REVOKED    │
│  (temporary)  │    │  (permanent)  │
└───────────────┘    └───────────────┘
        │
        ▼
┌───────────────┐
│    ACTIVE     │  (unfreeze)
└───────────────┘

Note: EXPIRED checked at validation time (not a DB state)
```

### Integrations Lifecycle (NOT IMPLEMENTED)

| Operation | Status | Notes |
|-----------|--------|-------|
| **CREATE** | ❌ MISSING | Cannot configure LLM providers |
| **LIST** | ⚠️ PARTIAL | Worker registry is read-only |
| **DETAIL** | ⚠️ PARTIAL | No per-tenant config view |
| **UPDATE** | ❌ MISSING | Cannot modify integration settings |
| **DELETE** | ❌ MISSING | Cannot remove integrations |
| **TEST** | ❌ MISSING | No health check endpoint |
| **ENABLE/DISABLE** | ❌ MISSING | No per-tenant toggle |

---

## 4. API Routes

### Customer Console (`/guard/*`)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/guard/keys` | GET | List customer's API keys | ✅ |
| `/guard/keys/{id}` | GET | Key detail | ✅ |
| `/guard/keys/{id}/freeze` | POST | Freeze key temporarily | ✅ |
| `/guard/keys/{id}/unfreeze` | POST | Unfreeze key | ✅ |

### Admin API (`/api/v1/*`)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/api-keys` | GET | List all tenant keys | ✅ |
| `/api/v1/api-keys` | POST | Create new key | ✅ |
| `/api/v1/api-keys/{id}` | GET | Key detail | ✅ |
| `/api/v1/api-keys/{id}` | DELETE | Revoke key | ✅ |

### Connectivity Facade (`/api/v1/connectivity/*`)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/connectivity/integrations` | GET | List available workers | ⚠️ READ-ONLY |
| `/api/v1/connectivity/integrations/{id}` | GET | Worker detail | ⚠️ READ-ONLY |
| `/api/v1/connectivity/api-keys` | GET | List API keys | ✅ |
| `/api/v1/connectivity/api-keys/{id}` | GET | Key detail | ✅ |

---

## 5. Models

### APIKey Model (L6)

**File:** `backend/app/models/tenant.py`

```python
class APIKey(SQLModel):
    # Identification
    id: str (UUID)
    tenant_id: str (FK → Tenant)
    name: str

    # Security (NEVER store plaintext)
    key_prefix: str        # "aos_xxxxxxxx" (display only)
    key_hash: str          # SHA-256 hash

    # Permissions
    permissions_json: str  # ["run:*", "read:*"]
    allowed_workers_json: str

    # Rate Limits
    rate_limit_rpm: int
    max_concurrent_runs: int

    # Status
    status: str            # active, revoked, expired
    expires_at: datetime
    revoked_at: datetime
    revoked_reason: str

    # Freeze State
    is_frozen: bool
    frozen_at: datetime

    # Usage Tracking
    last_used_at: datetime
    total_requests: int

    # SDSR Marking
    is_synthetic: bool
    synthetic_scenario_id: str
```

### WorkerRegistry Model (L6)

```python
class WorkerRegistry(SQLModel):
    id: str                # e.g., "business-builder"
    name: str
    description: str
    version: str
    status: str            # available, beta, coming_soon, deprecated
    is_public: bool

    # Configuration Schema
    moats_json: str        # ["M9", "M10", "M17"]
    default_config_json: str
    input_schema_json: str
    output_schema_json: str

    # Pricing
    tokens_per_run_estimate: int
    cost_per_run_cents: int
```

### WorkerConfig Model (L6)

```python
class WorkerConfig(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)
    worker_id: str (FK → WorkerRegistry)

    enabled: bool
    config_json: str       # Tenant-specific overrides
    brand_json: str

    max_runs_per_day: int
    max_tokens_per_run: int
```

---

## 6. Services & Adapters

### Layer Architecture

```
L2: API Routes (guard.py, tenants.py, connectivity.py)
     │
     ▼
L3: CustomerKeysAdapter (customer_keys_adapter.py)
     │
     ▼
L4: KeysReadService, KeysWriteService (keys_service.py)
     │
     ▼
L6: APIKey Model (tenant.py)
```

### ApiKeyService (L4)

**File:** `backend/app/auth/api_key_service.py`

| Method | Purpose |
|--------|---------|
| `validate_key(api_key)` | Hash and validate key |
| `_lookup_key_by_hash(hash)` | Database lookup |
| `_parse_scopes(permissions_json)` | Extract permissions |
| `revoke_key(key_id, reason)` | Permanent revocation |

### CustomerKeysAdapter (L3)

**File:** `backend/app/adapters/customer_keys_adapter.py`

| Method | Purpose |
|--------|---------|
| `list_keys(tenant_id)` | List with tenant isolation |
| `get_key(key_id, tenant_id)` | Detail with isolation |
| `freeze_key(key_id, tenant_id)` | Freeze operation |
| `unfreeze_key(key_id, tenant_id)` | Unfreeze operation |

**Security:** All operations enforce tenant isolation. Only key prefix exposed (never full key).

---

## 7. Capability Registry

**Finding:** NO dedicated capability files exist for Connectivity domain.

**Reason:** Connectivity is secondary navigation, not an SDSR-observed domain.

**Related Capabilities:**
- CAP-006: Authentication (API key validation at runtime)
- CAP-018: M25 Integration (Founder Console only)

---

## 8. Panel Questions

**Finding:** NO L2.1 intent files exist for CONNECTIVITY.

**Reason:** Connectivity is NOT in the L2.1 frozen seed. The 5 Core Lens domains are:
- Overview, Activity, Incidents, Policies, Logs

**UI Approach:** Direct configuration UI, not panel-based epistemic surface.

---

## 9. Coverage Summary

### API Keys

```
Lifecycle Operations:    6/8 (75%)
  - CREATE:    ✅
  - LIST:      ✅
  - DETAIL:    ✅
  - FREEZE:    ✅
  - UNFREEZE:  ✅
  - REVOKE:    ✅
  - ROTATE:    ❌ MISSING
  - TEST:      ❌ MISSING

Security:               COMPLETE
  - Hashing:   ✅ SHA-256
  - Isolation: ✅ Tenant-scoped
  - Prefix:    ✅ Display only
  - Audit:     ✅ Usage tracked
```

### Integrations

```
Lifecycle Operations:    1/6 (17%)
  - CREATE:    ❌ MISSING
  - LIST:      ⚠️ READ-ONLY (WorkerRegistry)
  - DETAIL:    ⚠️ READ-ONLY
  - UPDATE:    ❌ MISSING
  - DELETE:    ❌ MISSING
  - TEST:      ❌ MISSING

Customer Console:       NOT IMPLEMENTED
Founder Console:        Available (M25)
```

---

## 10. TODO: Missing Implementations

### 10.1 API Key Rotation (HIGH PRIORITY)

```
POST /api/v1/api-keys/{id}/rotate

Request: { "grace_period_days": 7 }

Response: {
  "new_key": "aos_newkey1234567890",
  "old_key_expires_at": "2026-01-23T00:00:00Z",
  "message": "Old key will be revoked after grace period"
}

Behavior:
1. Generate new key
2. Mark old key for delayed revocation
3. Both keys valid during grace period
4. Old key auto-revoked after grace period
```

### 10.2 API Key Test Endpoint (MEDIUM PRIORITY)

```
POST /api/v1/api-keys/{id}/test

Response: {
  "valid": true,
  "status": "active",
  "scopes": ["run:*", "read:*"],
  "rate_limit_remaining": 95,
  "usage_today": {
    "requests": 5,
    "runs": 2
  }
}
```

### 10.3 Integration Health Check (MEDIUM PRIORITY)

```
GET /api/v1/connectivity/integrations/{id}/health

Response: {
  "status": "healthy|degraded|down",
  "latency_ms": 120,
  "last_checked_at": "2026-01-16T10:00:00Z",
  "checks": [
    { "name": "api_reachable", "passed": true },
    { "name": "credentials_valid", "passed": true }
  ]
}
```

### 10.4 Integration Management for Customer Console (LOW PRIORITY)

**Endpoints Needed:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/connectivity/integrations` | POST | Create integration |
| `/api/v1/connectivity/integrations/{id}` | PUT | Update config |
| `/api/v1/connectivity/integrations/{id}` | DELETE | Remove integration |
| `/api/v1/connectivity/integrations/{id}/enable` | POST | Enable for tenant |
| `/api/v1/connectivity/integrations/{id}/disable` | POST | Disable for tenant |

---

## 11. Security Model

### API Key Security

| Property | Status | Details |
|----------|--------|---------|
| **Hashing** | ✅ | SHA-256, never plaintext |
| **Single Exposure** | ✅ | Full key shown once at creation |
| **Prefix Display** | ✅ | Only `aos_xxxxxxxx` in UI |
| **Tenant Isolation** | ✅ | All queries scoped to tenant_id |
| **Rate Limiting** | ✅ | Per-key RPM limits |
| **Expiration** | ✅ | Optional expiry date |
| **Revocation** | ✅ | Permanent with reason |
| **Freeze/Unfreeze** | ✅ | Temporary block |

### Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| No rotation | HIGH | Implement rotation endpoint |
| Freeze reversible | MEDIUM | Audit all freeze/unfreeze |
| Key shown once | LOW | Educate on secure storage |
| No scope modification | LOW | Create new key with different scope |

---

## 12. Related Files

| File | Purpose | Layer |
|------|---------|-------|
| `backend/app/api/guard.py` | Customer key endpoints | L2 |
| `backend/app/api/tenants.py` | Admin key endpoints | L2 |
| `backend/app/api/connectivity.py` | Unified facade | L2 |
| `backend/app/adapters/customer_keys_adapter.py` | Tenant isolation | L3 |
| `backend/app/services/keys_service.py` | Key operations | L4 |
| `backend/app/auth/api_key_service.py` | Key validation | L4 |
| `backend/app/models/tenant.py` | APIKey, WorkerConfig models | L6 |

---

## 13. Implementation Status

**Date:** 2026-01-16

### API Keys: Grade A-

| Component | Status |
|-----------|--------|
| Create | ✅ COMPLETE |
| List/Detail | ✅ COMPLETE |
| Freeze/Unfreeze | ✅ COMPLETE |
| Revoke | ✅ COMPLETE |
| Security (hash, isolation) | ✅ COMPLETE |
| Usage Tracking | ✅ COMPLETE |
| Rotation | ❌ MISSING |
| Test Endpoint | ❌ MISSING |

### Integrations: Grade D

| Component | Status |
|-----------|--------|
| List (read-only) | ⚠️ PARTIAL |
| Detail (read-only) | ⚠️ PARTIAL |
| Create | ❌ MISSING |
| Update | ❌ MISSING |
| Delete | ❌ MISSING |
| Health Check | ❌ MISSING |
| Enable/Disable | ❌ MISSING |

### Overall Assessment

**API Keys** are production-ready with solid security. Missing rotation and test endpoints are enhancements.

**Integrations** are not customer-manageable. Only WorkerRegistry read access exists. Full integration management (LLM providers, webhooks, notifications) not implemented for customer console.

---

## 14. SDK Integration Audit

### Expected Customer Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Customer installs SDK: npm install aos-sdk              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Customer provides THEIR OWN LLM credentials             │
│     - Anthropic API key                                     │
│     - OpenAI API key                                        │
│     - Other LLM provider keys                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. SDK wraps/intercepts customer's LLM calls               │
│     - Measures tokens used                                  │
│     - Tracks latency                                        │
│     - Records cost                                          │
│     - Captures request/response traces                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. AOS backend receives telemetry                          │
│     - Token usage per call                                  │
│     - Cost calculation (by model)                           │
│     - Latency metrics                                       │
│     - Trace data for debugging                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Customer Console displays                               │
│     - Total LLM spend                                       │
│     - Usage by provider/model                               │
│     - Performance metrics                                   │
│     - LLM call traces in Logs domain                        │
└─────────────────────────────────────────────────────────────┘
```

### Actual SDK State (What Exists)

| Component | Status | Location |
|-----------|--------|----------|
| Python SDK package | ✅ EXISTS | `sdk/python/aos_sdk/` |
| JavaScript SDK package | ✅ EXISTS | `sdk/js/` |
| HTTP client | ✅ EXISTS | `sdk/python/aos_sdk/client.py` |
| Runtime context | ✅ EXISTS | `sdk/python/aos_sdk/runtime.py` |
| Trace collection | ✅ EXISTS | `sdk/python/aos_sdk/trace.py` |
| AOS API key auth | ✅ EXISTS | SDK accepts AOS key for backend calls |

### CRITICAL GAPS (What's Missing)

| Component | Status | Impact |
|-----------|--------|--------|
| **Customer LLM credential acceptance** | ❌ NOT IMPLEMENTED | SDK cannot receive customer's Anthropic/OpenAI keys |
| **LLM provider adapters** | ❌ NOT IMPLEMENTED | No wrappers for Anthropic, OpenAI, etc. |
| **LLM call interception** | ❌ NOT IMPLEMENTED | Customer's direct LLM calls are INVISIBLE |
| **Token counting middleware** | ❌ NOT IMPLEMENTED | Cannot measure customer's token usage |
| **Cost calculation from usage** | ❌ NOT IMPLEMENTED | Cannot calculate customer's LLM spend |
| **Telemetry recording endpoint** | ❌ NOT IMPLEMENTED | No backend endpoint for customer LLM telemetry |

### Architecture Gap Analysis

**Current SDK Design:**
```python
# What SDK currently does
from aos_sdk import AOSClient

client = AOSClient(
    api_key="aos_xxx",  # AOS API key only
    base_url="https://api.agentiverz.com"
)

# SDK calls AOS backend APIs
runs = client.runs.list()
```

**Expected SDK Design:**
```python
# What SDK SHOULD do
from aos_sdk import AOSClient
from aos_sdk.providers import AnthropicProvider

client = AOSClient(
    api_key="aos_xxx",  # AOS API key for backend
    llm_credentials={
        "anthropic": "sk-ant-xxx",  # Customer's LLM key
        "openai": "sk-xxx"          # Customer's LLM key
    }
)

# Wrapped LLM call - AOS intercepts and records
response = client.anthropic.messages.create(
    model="claude-3-opus",
    messages=[{"role": "user", "content": "Hello"}]
)
# AOS automatically tracks: tokens, cost, latency
```

### Missing SDK Components

#### 1. Provider Adapters (HIGH PRIORITY)

```
sdk/
├── python/aos_sdk/
│   └── providers/           # ❌ MISSING
│       ├── __init__.py
│       ├── base.py          # Base provider interface
│       ├── anthropic.py     # Anthropic wrapper
│       ├── openai.py        # OpenAI wrapper
│       └── langchain.py     # LangChain integration
```

#### 2. Telemetry Middleware (HIGH PRIORITY)

```python
# Missing: middleware to intercept and record LLM calls
class LLMTelemetryMiddleware:
    def before_call(self, request):
        self.start_time = time.time()
        self.input_tokens = count_tokens(request)

    def after_call(self, response):
        self.output_tokens = count_tokens(response)
        self.latency_ms = (time.time() - self.start_time) * 1000
        self.send_telemetry_to_aos()
```

#### 3. Backend Telemetry Endpoint (HIGH PRIORITY)

```
POST /api/v1/telemetry/llm-calls

Request: {
    "provider": "anthropic",
    "model": "claude-3-opus",
    "input_tokens": 150,
    "output_tokens": 500,
    "latency_ms": 1200,
    "cost_cents": 3.25,
    "trace_id": "uuid",
    "timestamp": "2026-01-16T10:00:00Z"
}
```

### Integration Status Summary

```
Customer LLM Integration:     0% IMPLEMENTED

SDK Components:
  - SDK Package:              ✅ EXISTS
  - AOS Backend Client:       ✅ EXISTS
  - LLM Credential Accept:    ❌ NOT IMPLEMENTED
  - Provider Adapters:        ❌ NOT IMPLEMENTED
  - Call Interception:        ❌ NOT IMPLEMENTED
  - Token Counting:           ❌ NOT IMPLEMENTED
  - Cost Calculation:         ❌ NOT IMPLEMENTED

Backend Components:
  - Telemetry Endpoint:       ❌ NOT IMPLEMENTED
  - LLMRunRecord Model:       ✅ EXISTS (backend workers only)
  - Customer LLM Storage:     ❌ NOT IMPLEMENTED

Result: Customer's LLM usage is COMPLETELY INVISIBLE to Agentiverz.
```

### TODO: SDK Integration Implementation

#### Phase 1: Provider Adapters (CRITICAL)

| Task | Priority |
|------|----------|
| Create `sdk/python/aos_sdk/providers/` module | HIGH |
| Implement `AnthropicProvider` adapter | HIGH |
| Implement `OpenAIProvider` adapter | HIGH |
| Add credential configuration to SDK init | HIGH |

#### Phase 2: Telemetry Pipeline (CRITICAL)

| Task | Priority |
|------|----------|
| Add `POST /api/v1/telemetry/llm-calls` endpoint | HIGH |
| Create `CustomerLLMCall` model (separate from internal LLMRunRecord) | HIGH |
| Implement token counting for each provider | HIGH |
| Implement cost calculation by model | HIGH |

#### Phase 3: Customer Console Integration (MEDIUM)

| Task | Priority |
|------|----------|
| Display customer LLM usage in Overview/costs | MEDIUM |
| Add customer LLM calls to Logs domain | MEDIUM |
| Show cost breakdown by provider/model | MEDIUM |
| Add usage alerts/limits for customer LLM spend | MEDIUM |

---

## 15. Overall Connectivity Assessment

| Section | Grade | Notes |
|---------|-------|-------|
| **API Keys** | A- | Production-ready, missing rotation/test |
| **Integrations (WorkerConfig)** | D | Read-only, no customer management |
| **SDK Integration (Customer LLM)** | F | NOT IMPLEMENTED - critical gap |

**Critical Finding:** The entire customer LLM monitoring value proposition is unimplemented. Customers cannot connect their own LLM providers to Agentiverz for monitoring.
