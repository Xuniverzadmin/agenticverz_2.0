# Customer Integrations Architecture

**Status:** PHASE 6 COMPLETE (All Phases Done)
**Created:** 2026-01-17
**Updated:** 2026-01-17
**Reference:** Design Spec (Customer Integration Design Specification)

---

## 1. Overview

This document defines the architecture for customer LLM integrations in AOS. It closes two critical gaps:

1. **Integrations Management** (17% → 100%) — Control plane for customer LLM credentials
2. **SDK Telemetry** (0% → 100%) — Data plane for customer LLM usage visibility

### Design Principles (Non-Negotiable)

| Principle | Rule |
|-----------|------|
| Customer-Owned Credentials | AOS never stores raw LLM API keys beyond encrypted-at-rest config |
| Deterministic Capture | Telemetry capture is truth-first; analytics are downstream |
| Control Plane ≠ Data Plane | Integrations define authority; SDK telemetry reports facts |
| Fail-Closed Governance | Missing telemetry or policy → degrade predictably |

---

## 2. File Naming Convention

All customer integration artifacts use `cus_` prefix:

| Type | Pattern | Example |
|------|---------|---------|
| Backend Models | `cus_*.py` | `cus_models.py` |
| Backend API | `cus_*.py` | `cus_api.py` |
| Backend Services | `cus_*_service.py` | `cus_integration_service.py` |
| Migrations | `*_cus_*.py` | `100_cus_integrations.py` |
| SDK Providers | `cus_*.py` | `cus_anthropic.py` |
| SDK Telemetry | `cus_*.py` | `cus_middleware.py` |
| Scripts | `cus_*.py` | `cus_health_check.py` |
| Tests | `test_cus_*.py` | `test_cus_integrations.py` |

---

## 3. Data Model

### 3.1 Integration Model

```
┌─────────────────────────────────────────────────────────────┐
│                     cus_integrations                        │
├─────────────────────────────────────────────────────────────┤
│ id                 UUID PRIMARY KEY                         │
│ tenant_id          UUID NOT NULL → tenants(id)              │
│ name               VARCHAR(255) NOT NULL                    │
│ provider_type      VARCHAR(50) NOT NULL                     │
│                    CHECK (provider_type IN                  │
│                      ('openai','anthropic','azure_openai',  │
│                       'bedrock','custom'))                  │
│ credential_ref     TEXT NOT NULL (vault pointer)            │
│ config             JSONB DEFAULT '{}'                       │
│ status             VARCHAR(20) DEFAULT 'created'            │
│                    CHECK (status IN                         │
│                      ('created','enabled','disabled',       │
│                       'error'))                             │
│ health_state       VARCHAR(20) DEFAULT 'unknown'            │
│                    CHECK (health_state IN                   │
│                      ('unknown','healthy','degraded',       │
│                       'failing'))                           │
│ health_checked_at  TIMESTAMP WITH TIME ZONE                 │
│ health_message     TEXT                                     │
│ default_model      VARCHAR(100)                             │
│ budget_limit_cents INTEGER DEFAULT 0                        │
│ token_limit_month  BIGINT DEFAULT 0                         │
│ rate_limit_rpm     INTEGER DEFAULT 0                        │
│ created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()   │
│ updated_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()   │
│ created_by         UUID → users(id)                         │
└─────────────────────────────────────────────────────────────┘

UNIQUE INDEX: (tenant_id, name)
INDEX: (tenant_id, status)
INDEX: (tenant_id, provider_type)
```

### 3.2 Telemetry Model

```
┌─────────────────────────────────────────────────────────────┐
│                   cus_llm_usage                             │
├─────────────────────────────────────────────────────────────┤
│ id                 UUID PRIMARY KEY                         │
│ tenant_id          UUID NOT NULL → tenants(id)              │
│ integration_id     UUID NOT NULL → cus_integrations(id)     │
│ session_id         UUID                                     │
│ agent_id           VARCHAR(100)                             │
│ call_id            VARCHAR(100) UNIQUE (idempotency)        │
│ provider           VARCHAR(50) NOT NULL                     │
│ model              VARCHAR(100) NOT NULL                    │
│ tokens_in          INTEGER NOT NULL                         │
│ tokens_out         INTEGER NOT NULL                         │
│ cost_cents         INTEGER NOT NULL                         │
│ latency_ms         INTEGER                                  │
│ policy_result      VARCHAR(20) DEFAULT 'allowed'            │
│                    CHECK (policy_result IN                  │
│                      ('allowed','warned','blocked'))        │
│ error_code         VARCHAR(50)                              │
│ error_message      TEXT                                     │
│ metadata           JSONB DEFAULT '{}'                       │
│ created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()   │
└─────────────────────────────────────────────────────────────┘

INDEX: (tenant_id, created_at DESC)
INDEX: (tenant_id, integration_id, created_at DESC)
INDEX: (tenant_id, agent_id, created_at DESC)
INDEX: (call_id) -- idempotency lookup
PARTITION BY RANGE (created_at) -- monthly partitions
```

### 3.3 Usage Aggregates (Materialized)

```
┌─────────────────────────────────────────────────────────────┐
│                cus_usage_daily                              │
├─────────────────────────────────────────────────────────────┤
│ tenant_id          UUID NOT NULL                            │
│ integration_id     UUID NOT NULL                            │
│ date               DATE NOT NULL                            │
│ total_calls        INTEGER DEFAULT 0                        │
│ total_tokens_in    BIGINT DEFAULT 0                         │
│ total_tokens_out   BIGINT DEFAULT 0                         │
│ total_cost_cents   INTEGER DEFAULT 0                        │
│ avg_latency_ms     INTEGER                                  │
│ error_count        INTEGER DEFAULT 0                        │
│ blocked_count      INTEGER DEFAULT 0                        │
│ PRIMARY KEY (tenant_id, integration_id, date)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. API Surface

### 4.1 Integration Management API

**Router:** `/api/v1/cus/integrations`
**File:** `backend/app/api/cus_integrations.py`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/integrations` | List integrations | Tenant |
| `GET` | `/integrations/{id}` | Get integration detail | Tenant |
| `POST` | `/integrations` | Create integration | Tenant + Admin |
| `PUT` | `/integrations/{id}` | Update integration | Tenant + Admin |
| `DELETE` | `/integrations/{id}` | Delete integration | Tenant + Admin |
| `POST` | `/integrations/{id}/enable` | Enable integration | Tenant + Admin |
| `POST` | `/integrations/{id}/disable` | Disable integration | Tenant + Admin |
| `GET` | `/integrations/{id}/health` | Health check | Tenant |
| `POST` | `/integrations/{id}/test` | Test credentials | Tenant + Admin |

### 4.2 Telemetry Ingestion API

**Router:** `/api/v1/cus/telemetry`
**File:** `backend/app/api/cus_telemetry.py`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/llm-usage` | Ingest LLM usage | SDK Key |
| `POST` | `/llm-usage/batch` | Batch ingest | SDK Key |
| `GET` | `/llm-usage/summary` | Usage summary | Tenant |

### 4.3 Request/Response Schemas

**File:** `backend/app/schemas/cus_schemas.py`

```python
# Integration Create
class CusIntegrationCreate(BaseModel):
    name: str
    provider_type: Literal["openai", "anthropic", "azure_openai", "bedrock", "custom"]
    credential: dict  # Encrypted before storage
    config: dict = {}
    default_model: str | None = None
    budget_limit_cents: int = 0
    token_limit_month: int = 0
    rate_limit_rpm: int = 0

# Integration Response
class CusIntegrationResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    status: str
    health_state: str
    health_checked_at: datetime | None
    config: dict
    default_model: str | None
    budget_limit_cents: int
    token_limit_month: int
    rate_limit_rpm: int
    created_at: datetime
    updated_at: datetime

# Telemetry Ingest
class CusLLMUsageIngest(BaseModel):
    call_id: str  # Idempotency key
    integration_id: str
    session_id: str | None = None
    agent_id: str | None = None
    model: str
    tokens_in: int
    tokens_out: int
    cost_cents: int
    latency_ms: int | None = None
    policy_result: Literal["allowed", "warned", "blocked"] = "allowed"
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict = {}
    timestamp: datetime
```

---

## 5. SDK Architecture

### 5.1 Directory Structure (Implemented)

```
sdk/python/aos_sdk/
├── __init__.py               # Exports all cus_* modules
├── client.py                 # Existing AOS client
├── runtime.py                # Existing runtime
├── trace.py                  # Existing trace
│
│ # Phase 2: Telemetry Reporter
├── cus_reporter.py           # ✅ CusReporter, CusUsageRecord, batching
│
│ # Phase 3: Provider Adapters (VISIBILITY ONLY)
├── cus_base.py               # ✅ CusBaseProvider abstract contract
├── cus_token_counter.py      # ✅ Model-aware token counting (tiktoken)
├── cus_cost.py               # ✅ Deterministic table-driven pricing
├── cus_openai.py             # ✅ OpenAI provider adapter
├── cus_anthropic.py          # ✅ Anthropic provider adapter
└── cus_middleware.py         # ✅ Decorator, context manager, wrapper patterns
```

**Note:** Flat structure chosen over nested directories for simpler imports and discoverability.

### 5.2 Provider Interface (Implemented)

**File:** `sdk/python/aos_sdk/cus_base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")  # Native SDK client type

@dataclass
class CusProviderConfig:
    """Configuration for a customer provider adapter."""
    integration_key: str | None = None  # AOS integration key
    base_url: str = "http://127.0.0.1:8000"  # AOS API base URL
    auto_report: bool = True  # Auto-report telemetry

@dataclass
class CusCallContext:
    """Context for a single LLM call."""
    call_id: str
    model: str
    start_time: float
    session_id: str | None = None
    agent_id: str | None = None

class CusBaseProvider(ABC, Generic[T]):
    """Abstract base class for LLM provider adapters.

    Phase 3: VISIBILITY ONLY - captures and reports telemetry.
    No blocking, no throttling, no policy enforcement.
    """

    @abstractmethod
    def _create_client(self, api_key: str, **kwargs) -> T:
        """Create native SDK client."""
        pass

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Return provider name (openai, anthropic, etc.)."""
        pass

    @abstractmethod
    def _extract_usage(self, response: Any) -> tuple[int, int]:
        """Extract (tokens_in, tokens_out) from response."""
        pass

    @abstractmethod
    def _calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> int:
        """Calculate cost in cents."""
        pass

    @property
    def client(self) -> T:
        """Access the native SDK client directly."""
        return self._client
```

**Key Design Decisions:**
- Generic `T` type allows type-safe access to native SDK client
- `_execute_with_telemetry()` wraps all calls with timing and reporting
- Provider adapters expose native SDK methods (e.g., `chat_completions_create`)
- Phase 3 explicitly does NOT implement enforcement

### 5.3 Telemetry Middleware (Implemented)

**File:** `sdk/python/aos_sdk/cus_middleware.py`

The middleware provides four patterns for telemetry capture:

#### Pattern 1: Decorator
```python
from aos_sdk import cus_telemetry

@cus_telemetry(model="gpt-4o", provider="openai")
def my_llm_function(prompt):
    return openai.chat.completions.create(model="gpt-4o", messages=[...])
```

#### Pattern 2: Context Manager
```python
from aos_sdk import cus_track

with cus_track("gpt-4o", provider="openai") as tracker:
    response = openai.chat.completions.create(model="gpt-4o", messages=[...])
    tracker.set_usage_from_response(response, "openai")
```

#### Pattern 3: Wrapper Function
```python
from aos_sdk import cus_wrap

response = cus_wrap(
    lambda: openai.chat.completions.create(model="gpt-4o", messages=messages),
    model="gpt-4o",
    provider="openai",
)
```

#### Pattern 4: SDK Patching (Experimental)
```python
from aos_sdk import cus_configure, cus_install_middleware

# Configure once at startup
cus_configure(integration_key="tenant:integration:secret")
cus_install_middleware(patch_openai=True, patch_anthropic=True)

# All subsequent SDK calls are automatically tracked
response = openai.chat.completions.create(...)  # Telemetry captured
```

#### Global Configuration
```python
from aos_sdk import cus_configure, cus_shutdown

# Initialize
reporter = cus_configure(
    integration_key="tenant:integration:secret",
    base_url="https://api.agenticverz.com",
    batch_telemetry=True,
    batch_size=50,
    batch_interval=5.0,
)

# Shutdown (flushes pending telemetry)
cus_shutdown()
```

**Key Design Decisions:**
- Multiple patterns for different integration styles
- Auto-extracts usage from provider responses
- Non-blocking telemetry (failures don't break LLM calls)
- Batching support for high-throughput scenarios

---

## 6. Call Flow

### 6.1 Phase 3 Flow (VISIBILITY ONLY - Current)

```
┌─────────────────────────────────────────────────────────────┐
│              PHASE 3 SDK CALL FLOW (VISIBILITY ONLY)        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Customer Code                                           │
│     │                                                       │
│     ▼                                                       │
│  2. Provider Adapter / Middleware                           │
│     │  (CusOpenAIProvider, @cus_telemetry, etc.)           │
│     ▼                                                       │
│  3. Start Timer                                             │
│     │                                                       │
│     ▼                                                       │
│  4. Invoke Provider (actual LLM call)                       │
│     │  ❌ NO pre-call checks                                │
│     │  ❌ NO blocking                                       │
│     ▼                                                       │
│  5. Stop Timer, Extract Usage                               │
│     │  • tokens_in, tokens_out from response               │
│     │  • latency_ms from timer                             │
│     ▼                                                       │
│  6. Calculate Cost (deterministic, table-driven)            │
│     │  • Uses CusPricingTable                              │
│     │  • Microcents precision → cents                      │
│     ▼                                                       │
│  7. Emit Telemetry (async, non-blocking)                    │
│     │  • Via CusReporter                                   │
│     │  • Batched if enabled                                │
│     │  ❌ NO post-call enforcement                         │
│     ▼                                                       │
│  8. Return Response to Customer                             │
│     │  • Unmodified from provider                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Phase 3 Invariants:**
- ✅ Capture telemetry (tokens, cost, latency)
- ✅ Report to AOS
- ❌ NO limit checks
- ❌ NO policy evaluation
- ❌ NO blocking or throttling
- ❌ NO behavior modification

### 6.2 Phase 5 Flow (ENFORCEMENT - Future)

```
┌─────────────────────────────────────────────────────────────┐
│              PHASE 5 SDK CALL FLOW (WITH ENFORCEMENT)       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Customer Code                                           │
│     │                                                       │
│     ▼                                                       │
│  2. Load Integration Config (from AOS or cache)             │
│     │                                                       │
│     ▼                                                       │
│  3. PRE-CHECK: Budget + Token + Rate Limits      ← Phase 5  │
│     │  ├── PASS → Continue                                  │
│     │  └── FAIL → Return CusLimitExceeded                   │
│     ▼                                                       │
│  4. Invoke Provider (actual LLM call)                       │
│     │                                                       │
│     ▼                                                       │
│  5. Extract Usage + Calculate Cost                          │
│     │                                                       │
│     ▼                                                       │
│  6. Emit Telemetry (async, non-blocking)                    │
│     │                                                       │
│     ▼                                                       │
│  7. POST-CHECK: Enforce post-call rules          ← Phase 5  │
│     │                                                       │
│     ▼                                                       │
│  8. Return Response to Customer                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Backend Services

### 7.1 Service Layer

| Service | File | Responsibility |
|---------|------|----------------|
| `CusIntegrationService` | `cus_integration_service.py` | CRUD + lifecycle |
| `CusCredentialService` | `cus_credential_service.py` | Vault operations |
| `CusHealthService` | `cus_health_service.py` | Health checks |
| `CusTelemetryService` | `cus_telemetry_service.py` | Ingestion + aggregation |
| `CusEnforcementService` | `cus_enforcement_service.py` | Limit enforcement |

### 7.2 File Locations

```
backend/app/
├── api/
│   ├── cus_integrations.py       # Integration API
│   └── cus_telemetry.py          # Telemetry API
├── models/
│   └── cus_models.py             # SQLModel definitions
├── schemas/
│   └── cus_schemas.py            # Pydantic schemas
├── services/
│   ├── cus_integration_service.py
│   ├── cus_credential_service.py
│   ├── cus_health_service.py
│   ├── cus_telemetry_service.py
│   └── cus_enforcement_service.py
└── alembic/versions/
    └── 100_cus_integrations.py   # Migration
```

---

## 8. Scripts

| Script | Purpose |
|--------|---------|
| `scripts/cus_health_check.py` | CLI for integration health checks |
| `scripts/cus_migrate_workers.py` | Migrate existing WorkerConfig to Integrations |
| `scripts/cus_telemetry_backfill.py` | Backfill usage aggregates |
| `scripts/cus_credential_rotate.py` | Rotate integration credentials |

---

## 9. Testing

| Test File | Coverage |
|-----------|----------|
| `tests/api/test_cus_integrations.py` | Integration CRUD API |
| `tests/api/test_cus_telemetry.py` | Telemetry ingestion API |
| `tests/services/test_cus_integration_service.py` | Service layer |
| `tests/sdk/test_cus_providers.py` | Provider adapters |
| `tests/sdk/test_cus_middleware.py` | Telemetry middleware |
| `tests/e2e/test_cus_flow.py` | End-to-end customer flow |

---

## 10. Implementation Phases

### Phase 1: Foundation ✅ COMPLETE

| Task | File | Status |
|------|------|--------|
| Migration | `103_cus_integrations.py` | ✅ |
| Models | `cus_models.py` | ✅ |
| Schemas | `cus_schemas.py` | ✅ |

### Phase 2: Telemetry Ingest ✅ COMPLETE

| Task | File | Status |
|------|------|--------|
| Telemetry API router | `cus_telemetry.py` | ✅ |
| Telemetry service | `cus_telemetry_service.py` | ✅ |
| SDK Reporter | `cus_reporter.py` | ✅ |
| Router registration | `main.py` | ✅ |

### Phase 3: Provider Adapters (VISIBILITY ONLY) ✅ COMPLETE

| Task | File | Status |
|------|------|--------|
| Base provider contract | `cus_base.py` | ✅ |
| Token counting | `cus_token_counter.py` | ✅ |
| Cost calculation | `cus_cost.py` | ✅ |
| OpenAI adapter | `cus_openai.py` | ✅ |
| Anthropic adapter | `cus_anthropic.py` | ✅ |
| Middleware patterns | `cus_middleware.py` | ✅ |

**Phase 3 Scope:** VISIBILITY ONLY
- ✅ Capture telemetry
- ✅ Report to AOS
- ❌ NO enforcement (deferred to Phase 5)

### Phase 4: Integration Management API ✅ COMPLETE

| Task | File | Status |
|------|------|--------|
| Integration CRUD endpoints | `cus_integrations.py` | ✅ |
| Integration service | `cus_integration_service.py` | ✅ |
| Enable/Disable endpoints | `cus_integrations.py` | ✅ |
| Health check endpoints | `cus_integrations.py` | ✅ |
| Credential service (encryption) | `cus_credential_service.py` | ✅ |
| Health service (provider checks) | `cus_health_service.py` | ✅ |
| Health check CLI | `cli/cus_health_check.py` | ✅ |
| Router registration | `main.py` | ✅ |

### Phase 5: Enforcement ✅ COMPLETE

| Task | File | Status |
|------|------|--------|
| Enforcement service | `cus_enforcement_service.py` | ✅ |
| Enforcement API | `cus_enforcement.py` | ✅ |
| SDK enforcer | `cus_enforcer.py` | ✅ |
| Usage aggregator | `scripts/cus_usage_aggregator.py` | ✅ |
| Router registration | `main.py` | ✅ |

### Phase 6: Observability ✅ COMPLETE

| Task | File | Status |
|------|------|--------|
| Evidence-Observability Linking Spec | Section 16 (this doc) | ✅ |
| Customer integration metrics | `metrics.py` (cus_* namespace) | ✅ |
| Grafana dashboard | `cus_llm_observability_dashboard.json` | ✅ |
| Alert rules | `cus_integration_alerts.yml` | ✅ |

**Phase 6 Approach:** "Evidence → Observability Signal Wiring"
- No new infrastructure created
- Linking specification locked in Section 16
- Metrics, dashboard, and alerts extend existing infrastructure

---

## 11. Cost Calculation System

**File:** `sdk/python/aos_sdk/cus_cost.py`

### 11.1 Design Principles

| Principle | Implementation |
|-----------|----------------|
| Deterministic | Table-driven, no external API calls |
| Precision | Microcents internally (1/10000 cent) |
| Versioned | `CusPricingTable.TABLE_VERSION = "2026-01-17"` |
| Auditable | All calculations reproducible |

### 11.2 Pricing Tables

```python
class CusPricingTable:
    TABLE_VERSION = "2026-01-17"

    # OpenAI Models
    OPENAI_PRICING = {
        "gpt-4o":        CusModelPricing(input=0.0025, output=0.010),   # $2.50/$10 per 1M
        "gpt-4o-mini":   CusModelPricing(input=0.00015, output=0.0006), # $0.15/$0.60 per 1M
        "gpt-4-turbo":   CusModelPricing(input=0.01, output=0.03),      # $10/$30 per 1M
        "o1":            CusModelPricing(input=0.015, output=0.06),     # $15/$60 per 1M
        "o1-mini":       CusModelPricing(input=0.003, output=0.012),    # $3/$12 per 1M
    }

    # Anthropic Models
    ANTHROPIC_PRICING = {
        "claude-opus-4":     CusModelPricing(input=0.015, output=0.075),  # $15/$75 per 1M
        "claude-sonnet-4":   CusModelPricing(input=0.003, output=0.015),  # $3/$15 per 1M
        "claude-3-5-sonnet": CusModelPricing(input=0.003, output=0.015),  # $3/$15 per 1M
        "claude-3-5-haiku":  CusModelPricing(input=0.001, output=0.005),  # $1/$5 per 1M
    }
```

### 11.3 Cost Calculation Formula

```
input_microcents  = tokens_in  * (input_per_1k  * 1000 * 100)
output_microcents = tokens_out * (output_per_1k * 1000 * 100)
total_microcents  = input_microcents + output_microcents
cost_cents        = (total_microcents + 9999) // 10000  # Round up
```

### 11.4 SDK Functions

| Function | Purpose |
|----------|---------|
| `calculate_cost(model, tokens_in, tokens_out)` | Returns cost in cents |
| `calculate_cost_breakdown(...)` | Returns detailed breakdown |
| `estimate_cost(...)` | Pre-call estimation |
| `get_model_pricing(model)` | Get pricing info |
| `format_cost(cents)` | Format as "$X.XX" |

### 11.5 Cost Determinism Verification (Gate C)

**Test Protocol:** For any historical call, verify:

```python
from aos_sdk import calculate_cost, get_model_pricing

# Example: GPT-4o call with 1000 input, 500 output tokens
cost = calculate_cost("gpt-4o", tokens_in=1000, tokens_out=500)
# Expected: (1000 * 0.0025 + 500 * 0.01) * 100 / 1000 = 0.75 cents → rounds to 1 cent

breakdown = calculate_cost_breakdown("gpt-4o", 1000, 500)
# Returns: {input_cost_cents, output_cost_cents, total_cost_cents, pricing_version}
```

**Verification Checklist:**

| Model | Tokens In | Tokens Out | Expected Cost | Provider Dashboard | Delta |
|-------|-----------|------------|---------------|-------------------|-------|
| gpt-4o | 1000 | 500 | 1 cent | _verify_ | ±0 |
| gpt-4o-mini | 10000 | 5000 | 1 cent | _verify_ | ±0 |
| claude-sonnet-4 | 1000 | 500 | 1 cent | _verify_ | ±0 |
| claude-opus-4 | 1000 | 500 | 5 cents | _verify_ | ±0 |
| o1 | 1000 | 500 | 5 cents | _verify_ | ±0 |

**Known Deltas:**
- Token count may vary ±5% from provider dashboard due to tokenizer differences
- Cost always rounds UP to nearest cent (billing fairness)
- Anthropic token counts are estimates (no public tokenizer)

---

## 12. Token Counting System

**File:** `sdk/python/aos_sdk/cus_token_counter.py`

### 12.1 Model Registry

```python
MODEL_REGISTRY = {
    # OpenAI
    "gpt-4o":        ModelInfo(context=128000, tokenizer="cl100k_base"),
    "gpt-4o-mini":   ModelInfo(context=128000, tokenizer="cl100k_base"),
    "gpt-4-turbo":   ModelInfo(context=128000, tokenizer="cl100k_base"),

    # Anthropic
    "claude-opus-4":     ModelInfo(context=200000, tokenizer="anthropic"),
    "claude-sonnet-4":   ModelInfo(context=200000, tokenizer="anthropic"),
}
```

### 12.2 Token Counting Strategy

| Provider | Method | Fallback |
|----------|--------|----------|
| OpenAI | tiktoken (exact) | char/4 approximation |
| Anthropic | char/4 approximation | char/4 approximation |

```python
def count_tokens(text: str, model: str) -> int:
    """Model-aware token counting."""
    info = get_model_info(model)

    if info.tokenizer_type == "tiktoken" and tiktoken_available():
        return _count_with_tiktoken(text, info.tokenizer_name)

    # Fallback: character-based approximation
    return estimate_tokens(text)

def estimate_tokens(text: str) -> int:
    """Fast approximation: ~4 chars per token."""
    return max(1, len(text) // 4)
```

### 12.3 Usage Extraction

```python
def extract_usage(response: Any, provider: str) -> tuple[int, int]:
    """Extract (tokens_in, tokens_out) from provider response."""
    if provider == "openai":
        return extract_openai_usage(response)
    elif provider == "anthropic":
        return extract_anthropic_usage(response)
    return (0, 0)
```

---

## 13. SDK Governance Contract

### 13.1 Provider Bypass Prevention (MANDATORY)

> **All governed LLM calls MUST pass through cus_middleware or a CusProvider adapter.**

This is the foundational requirement for telemetry and enforcement to function correctly.

**Bypass Detection (Phase 5):**
- SDK will emit `bypass_detected` events when direct provider calls are observed
- Dashboard will surface bypass percentage per integration
- Enforcement requires ≥95% coverage before enabling hard blocks

**Customer Responsibility:**
- Customers MUST use one of:
  - `CusOpenAIProvider` / `CusAnthropicProvider` adapters
  - `@cus_telemetry` decorator
  - `cus_track()` context manager
  - `cus_wrap()` wrapper function
  - `cus_install_middleware()` SDK patching

**Direct SDK calls bypass governance and will:**
- Not be counted toward usage limits
- Not appear in telemetry dashboards
- Not be subject to policy enforcement (Phase 5)

---

### 13.2 Existing Infrastructure to Leverage

| Component | Location | Reuse |
|-----------|----------|-------|
| Budget enforcement | `budget_tracker.py` | Adapt for integrations |
| Cost model | `claude_adapter.py:43-48` | Extract to shared |
| Token counting | LLM adapters | Extract to SDK |
| Tenant isolation | All APIs | Standard pattern |

### 13.3 New Governance Rules

| Rule | Enforcement |
|------|-------------|
| CUS-001 | Integration required for SDK telemetry |
| CUS-002 | Credentials encrypted at rest |
| CUS-003 | Telemetry is append-only |
| CUS-004 | Health checks are non-blocking |
| CUS-005 | Budget enforcement is pre-call (Phase 5) |
| CUS-006 | Provider bypass detection required (Phase 5) |

---

## 14. SDK Exports Summary

All Phase 2 and Phase 3 modules are exported from `aos_sdk.__init__`:

```python
from aos_sdk import (
    # Phase 2: Telemetry Reporter
    CusReporter,
    CusUsageRecord,
    CusCallTracker,

    # Phase 3: Provider Base
    CusBaseProvider,
    CusProviderConfig,
    CusProviderError,

    # Phase 3: Token Counting
    count_tokens,
    estimate_tokens,
    get_model_info,
    tiktoken_available,

    # Phase 3: Cost Calculation
    calculate_cost,
    calculate_cost_breakdown,
    get_model_pricing,
    format_cost,
    CusPricingTable,

    # Phase 3: Provider Adapters
    CusOpenAIProvider,
    create_openai_provider,
    CusAnthropicProvider,
    create_anthropic_provider,

    # Phase 3: Middleware
    cus_configure,
    cus_track,
    cus_telemetry,
    cus_wrap,
    cus_install_middleware,
    cus_shutdown,
)
```

---

## 15. Enforcement Precedence (LOCKED)

**Status:** LOCKED (Phase 5 prerequisite)
**Effective:** 2026-01-17

This section defines the **exact order** of enforcement checks. No ambiguity allowed.

### 15.1 Kill-Switch Precedence Order

```
┌─────────────────────────────────────────────────────────────┐
│              ENFORCEMENT DECISION FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Integration Disabled?    ──YES──►  HARD BLOCK           │
│           │ NO                                              │
│           ▼                                                 │
│  2. Integration in ERROR?    ──YES──►  HARD BLOCK           │
│           │ NO                                              │
│           ▼                                                 │
│  3. Credentials Invalid?     ──YES──►  HARD BLOCK           │
│           │ NO                                              │
│           ▼                                                 │
│  4. Budget Exceeded?         ──YES──►  BLOCK                │
│           │ NO                                              │
│           ▼                                                 │
│  5. Token Limit Exceeded?    ──YES──►  BLOCK                │
│           │ NO                                              │
│           ▼                                                 │
│  6. Rate Limit Exceeded?     ──YES──►  THROTTLE             │
│           │ NO                                              │
│           ▼                                                 │
│  7. Budget Near Limit (>80%)?──YES──►  WARN                 │
│           │ NO                                              │
│           ▼                                                 │
│  8. Token Near Limit (>80%)? ──YES──►  WARN                 │
│           │ NO                                              │
│           ▼                                                 │
│  9. All checks pass          ──────►  ALLOW                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 15.2 Enforcement Results

| Result | Code | Behavior |
|--------|------|----------|
| `HARD_BLOCK` | `hard_blocked` | Immediate rejection. No retry. |
| `BLOCK` | `blocked` | Rejection due to limit. Can retry after reset. |
| `THROTTLE` | `throttled` | Delayed execution. SDK should back off. |
| `WARN` | `warned` | Allowed but warning emitted. |
| `ALLOW` | `allowed` | Normal execution. |

### 15.3 HARD_BLOCK vs BLOCK

| Condition | Type | Retry Possible? | User Action |
|-----------|------|-----------------|-------------|
| Integration disabled | HARD_BLOCK | No | Enable integration |
| Integration error state | HARD_BLOCK | No | Fix health issue |
| Invalid credentials | HARD_BLOCK | No | Rotate credentials |
| Budget exceeded | BLOCK | Yes (next period) | Increase limit or wait |
| Token limit exceeded | BLOCK | Yes (next period) | Increase limit or wait |
| Rate limit exceeded | THROTTLE | Yes (after delay) | Wait ~60s |

### 15.4 Enforcement Ladder (Immutable)

This ladder is **locked** and cannot be changed without governance approval:

```
VISIBILITY (P3) - Observe only
      ↓
CONTROL PLANE (P4) - Define limits
      ↓
WARN - Soft notification
      ↓
THROTTLE - Rate limiting
      ↓
BLOCK - Limit enforcement
      ↓
HARD_BLOCK - System-level denial
```

No skipping steps unless:
- Integration is disabled/error
- Credentials are invalid

### 15.5 Telemetry Requirements for Enforcement

| Check Type | Data Source | Fallback |
|------------|-------------|----------|
| Budget | `SUM(cost_cents)` from `cus_llm_usage` | ALLOW with `degraded: true` |
| Token | `SUM(tokens_in + tokens_out)` from `cus_llm_usage` | ALLOW with `degraded: true` |
| Rate | `COUNT(*)` from `cus_llm_usage` (last minute) | ALLOW with `degraded: true` |

**Invariant:** Enforcement NEVER uses `cus_usage_daily` for decisions.

---

## 16. Evidence-Observability Linking Specification (LOCKED)

**Status:** LOCKED (Phase 6)
**Effective:** 2026-01-17

This section defines the **explicit linking** between the Evidence Plane (Phases 1-5) and the existing Observability Infrastructure. Phase 6 wires Evidence → Observability; it does NOT add a new layer.

### 16.1 Mental Model (Three Layers)

| Layer | What It Is | Status |
|-------|------------|--------|
| **Evidence Plane** | Immutable governance facts | ✅ Built (Phases 1-5) |
| **Observability Infrastructure** | Metrics, dashboards, alerts | ✅ Already exists |
| **Console Domains** | Human-facing interpretation | ✅ Already exists |

### 16.2 Evidence → Prometheus Metrics (Linking Rules)

**Purpose:** Expose **signals**, not truth.

**Hard Rule:**
> Metrics may summarize Evidence, but Evidence may NEVER depend on metrics.

#### What Gets Exported

| Evidence Source | Metric Type | Example |
|-----------------|-------------|---------|
| `cus_llm_usage` | Counter | `cus_llm_calls_total` |
| Enforcement decisions | Counter | `cus_enforcement_blocked_total` |
| Policy result | Counter (labels) | `cus_policy_results_total{result="warned"}` |
| Cost (per call) | Counter | `cus_llm_cost_cents_total` |
| Health transitions | Gauge | `cus_integration_health_state` |

**Cardinality Rules:**
- ❌ No per-call cardinality
- ❌ No `call_id` labels

Metrics answer **"how often"**, never **"why exactly"**.

#### File Location

```
backend/app/metrics.py
```

#### Naming Convention (Mandatory)

```
cus_llm_*
cus_enforcement_*
cus_integration_*
```

No reuse of internal infra metric namespaces.

### 16.3 Evidence → Grafana Dashboards

**Purpose:** Human situational awareness, not forensic truth.

Grafana **visualizes trends**, not decisions.

#### Allowed

- ✅ Cost over time
- ✅ % budget consumed
- ✅ Block / throttle rate
- ✅ Health state timeline

#### Forbidden

- ❌ "Why was this specific run blocked?"
- ❌ "Which policy exactly triggered this run?"

Those belong to **Console → Logs / Records**, backed directly by Evidence.

#### Dashboard Contract

**Role:**
> "Are we okay, drifting, or failing?"

**Not:**
> "Explain this incident."

#### Linking Rule

Every Grafana panel MUST include:
- A label hint or link to Console deep-link
- Example: "View evidence in Console → Activity / Incidents"

Grafana **never becomes the investigation surface**.

### 16.4 Evidence → Alertmanager Rules

**Purpose:** Signal **state transitions**, not raw data.

#### What Alerts Trigger On

| Alert | Trigger |
|-------|---------|
| Budget near threshold | `cus_policy_results_total{result="warned"}` |
| Enforcement active | `cus_enforcement_blocked_total > 0` |
| Health degraded | `cus_integration_health_state != healthy` |

📌 Alerts fire on **decisions**, not raw usage.

#### Alert Payload Rule

Every alert MUST include:
- `tenant_id`
- `integration_id`
- `enforcement_state`

And MUST instruct:
> "Investigate in Console → Evidence-backed views"

No alerts attempt to explain causality themselves.

### 16.5 Evidence ↔ Analytics API (Boundary)

**Critical Boundary:**

```
Evidence Plane (truth)
   ↓
Analytics API (derived views)
   ↓
Console Summary / Overview
```

**Rules:**
- 📌 Analytics API **never writes** to Evidence
- 📌 Enforcement **never reads** from Analytics

### 16.6 Evidence ↔ Observability Provider Framework

**Role of `backend/app/observability/`:**
- Adapter for metrics emission
- Tracing hooks
- Cost summarization
- **Not** a governance decision-maker

Conceptual rename:
> Observability Provider = **Evidence Signal Emitter**

### 16.7 Non-Overlap Contract (IMMUTABLE)

| Layer | Properties |
|-------|------------|
| **Evidence Plane** | Immutable, Append-only, Per-event truth, Explains decisions |
| **Observability Infra** | Aggregated, Sampled, Trend-based, Signals attention |
| **Console Domains** | Interprets, Prioritizes, Decides next action |

**Invariant:** If a feature violates this separation, it is **architecturally invalid**.

### 16.8 Phase 6 Status

Phase 6 is declared **COMPLETE** as:
- "Evidence → Observability Signal Wiring"
- Infrastructure exists
- Linking is explicit via this specification
- Minimal extension artifacts created

---

## 17. Related Documents

- Design Spec: Customer Integration Design Specification
- Implementation Plan: `docs/architecture/CUSTOMER_INTEGRATIONS_IMPLEMENTATION_PLAN.md`
- Audit: `docs/architecture/connectivity/CONNECTIVITY_DOMAIN_AUDIT.md`
- Budget: `backend/app/utils/budget_tracker.py`
- Adapters: `backend/app/skills/adapters/`

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-17 | Phase 6 complete: Observability (metrics, dashboard, alerts) - All phases DONE |
| 2026-01-17 | Added Section 16: Evidence-Observability Linking Specification (LOCKED) |
| 2026-01-17 | Phase 5 complete: Enforcement (service, API, SDK enforcer, aggregator) |
| 2026-01-17 | Phase 5 gates complete: G1 (limits source), G2 (telemetry invariant), G3 (enforcement precedence) |
| 2026-01-17 | Added Section 15: Enforcement Precedence (LOCKED) |
| 2026-01-17 | Phase 4 complete: Integration Management API |
| 2026-01-17 | Gate checks complete: A (no hidden control), B (bypass prevention), C (cost determinism) |
| 2026-01-17 | Added SDK Governance Contract section with bypass prevention language |
| 2026-01-17 | Added Cost Determinism Verification protocol |
| 2026-01-17 | Phase 3 complete: Provider adapters (visibility only) |
| 2026-01-17 | Phase 2 complete: Telemetry ingest API and SDK reporter |
| 2026-01-17 | Phase 1 complete: Foundation (migration, models, schemas) |
| 2026-01-17 | Initial architecture document |
