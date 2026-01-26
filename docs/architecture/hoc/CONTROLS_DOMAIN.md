# Controls Domain Architecture

**Status:** DRAFT
**Created:** 2026-01-26
**Location:** `backend/app/hoc/cus/controls/`
**Audience:** CUSTOMER

---

## 1. Domain Purpose

The Controls domain provides customer-facing configuration and enforcement of:

| Control Type | Description | Example |
|--------------|-------------|---------|
| **Token Limits** | Maximum tokens per request/day/month | 100K tokens/day |
| **Cost Limits** | Budget caps and spending thresholds | $50/month hard cap |
| **Credit Usage** | Pre-paid credit tracking and alerts | Alert at 80% consumed |
| **RAG Auditing** | Verify LLM accessed RAG before inference | Audit trail required |

---

## 2. Domain Question

> **"What limits apply, and were they respected?"**

This domain answers:
- What are my current usage limits?
- How close am I to hitting limits?
- Did the LLM actually consult my knowledge base before answering?
- What happens when limits are exceeded?

---

## 3. Layer Structure

```
hoc/cus/controls/
├── __init__.py
├── L3_adapters/           # Cross-domain integration
│   ├── __init__.py
│   ├── policies_adapter.py      # Connect to policy enforcement
│   ├── analytics_adapter.py     # Pull usage metrics
│   └── activity_adapter.py      # Run-level control checks
│
├── L5_engines/            # Business logic (NO DB ACCESS)
│   ├── __init__.py
│   ├── token_limit_engine.py    # Token usage evaluation
│   ├── cost_limit_engine.py     # Cost/budget evaluation
│   ├── credit_engine.py         # Credit balance tracking
│   ├── rag_audit_engine.py      # RAG access verification
│   ├── threshold_engine.py      # Alert threshold logic
│   └── controls_facade.py       # Unified controls interface
│
├── L5_schemas/            # Pydantic models
│   ├── __init__.py
│   ├── limits.py                # Limit configuration schemas
│   ├── thresholds.py            # Threshold definitions
│   ├── audit_records.py         # RAG audit trail schemas
│   └── control_events.py        # Control violation events
│
└── L6_drivers/            # Database operations
    ├── __init__.py
    ├── limits_driver.py         # CRUD for limit configs
    ├── usage_driver.py          # Usage tracking persistence
    ├── credit_driver.py         # Credit balance operations
    └── audit_driver.py          # RAG audit trail storage
```

---

## 4. Control Categories

### 4.1 Token Usage Controls

| Control | Scope | Enforcement |
|---------|-------|-------------|
| `token_limit_per_request` | Per-request | Hard block |
| `token_limit_daily` | Per-tenant daily | Soft warn → Hard block |
| `token_limit_monthly` | Per-tenant monthly | Alert thresholds |

**Schema:**
```python
class TokenLimit(BaseModel):
    tenant_id: UUID
    limit_type: Literal["request", "daily", "monthly"]
    max_tokens: int
    action_on_exceed: Literal["block", "warn", "allow_with_flag"]
    alert_threshold_pct: float = 0.8  # Alert at 80%
```

### 4.2 Cost Usage Controls

| Control | Scope | Enforcement |
|---------|-------|-------------|
| `cost_budget_daily` | Per-tenant daily | Soft cap |
| `cost_budget_monthly` | Per-tenant monthly | Hard cap option |
| `cost_per_run_max` | Per-run | Pre-execution check |

**Integration:** Pulls cost data from `analytics` domain via L3 adapter.

### 4.3 Credit Usage Controls

| Control | Scope | Enforcement |
|---------|-------|-------------|
| `credit_balance` | Per-tenant | Pre-execution check |
| `credit_alert_threshold` | Per-tenant | Alert at N% remaining |
| `credit_auto_pause` | Per-tenant | Pause at 0 balance |

**Integration:** Connects to `account` domain for billing/credit state.

### 4.4 RAG Access Auditing

| Audit Type | Description | Evidence |
|------------|-------------|----------|
| `rag_accessed` | Did LLM query RAG before inference? | Boolean + trace_id |
| `rag_sources_used` | Which documents were retrieved? | List of doc_ids |
| `rag_relevance_score` | How relevant was retrieved content? | Float 0-1 |
| `inference_without_rag` | LLM answered without RAG? | Flag for review |

**Purpose:** Customers need assurance that AI answers are grounded in their data, not hallucinated.

---

## 5. Cross-Domain Integration

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROLS DOMAIN                         │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Token Limit │   │ Cost Limit  │   │ RAG Audit   │       │
│  │   Engine    │   │   Engine    │   │   Engine    │       │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
│         │                 │                 │               │
│         └────────┬────────┴────────┬────────┘               │
│                  │                 │                        │
│           L3 Adapters              │                        │
└─────────────────┬──────────────────┴────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Activity│  │ Analytics│  │ Policies │  │ Account  │
│ Domain │  │  Domain  │  │  Domain  │  │  Domain  │
└────────┘  └──────────┘  └──────────┘  └──────────┘
  (runs)     (costs)      (enforce)     (credits)
```

---

## 6. API Endpoints (L2)

To be created at `hoc/api/cus/controls/`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/controls/limits` | GET | Get all limit configurations |
| `/controls/limits` | POST | Create/update limit config |
| `/controls/limits/{type}` | GET | Get specific limit type |
| `/controls/usage` | GET | Get current usage vs limits |
| `/controls/usage/history` | GET | Usage history over time |
| `/controls/credits` | GET | Get credit balance and alerts |
| `/controls/rag-audit` | GET | Get RAG audit trail |
| `/controls/rag-audit/{run_id}` | GET | RAG audit for specific run |

---

## 7. Database Tables (L7)

To be created at `app/models/`:

| Table | Purpose |
|-------|---------|
| `control_limits` | Limit configurations per tenant |
| `control_usage_snapshots` | Periodic usage snapshots |
| `control_alerts` | Alert history and acknowledgments |
| `rag_audit_records` | RAG access verification trail |

**Schema Draft:**

```sql
CREATE TABLE control_limits (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    limit_type VARCHAR(50) NOT NULL,  -- token_daily, cost_monthly, etc.
    max_value DECIMAL NOT NULL,
    action_on_exceed VARCHAR(20) NOT NULL,  -- block, warn, allow
    alert_threshold_pct DECIMAL DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, limit_type)
);

CREATE TABLE rag_audit_records (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    run_id UUID NOT NULL,
    rag_accessed BOOLEAN NOT NULL,
    sources_used JSONB,  -- [{doc_id, relevance_score}]
    inference_grounded BOOLEAN,  -- Was answer grounded in RAG?
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. Engine Contracts (L5)

### TokenLimitEngine

```python
class TokenLimitEngine:
    """
    L5 Engine - NO database access allowed.
    Receives data from driver, returns decisions.
    """

    def check_limit(
        self,
        current_usage: int,
        limit_config: TokenLimit
    ) -> LimitCheckResult:
        """Check if usage exceeds limit, return action."""
        pass

    def calculate_remaining(
        self,
        current_usage: int,
        limit_config: TokenLimit
    ) -> RemainingAllowance:
        """Calculate remaining allowance and alert status."""
        pass
```

### RAGAuditEngine

```python
class RAGAuditEngine:
    """
    L5 Engine - Verifies RAG was consulted before inference.
    """

    def verify_rag_access(
        self,
        run_trace: RunTrace
    ) -> RAGAuditResult:
        """
        Analyze trace to verify:
        1. RAG retrieval step occurred
        2. Retrieved documents were relevant
        3. Inference used retrieved context
        """
        pass

    def flag_ungrounded_inference(
        self,
        run_id: UUID,
        reason: str
    ) -> AuditFlag:
        """Flag runs where inference bypassed RAG."""
        pass
```

---

## 9. Implementation Phases

### Phase 1: Foundation
- [ ] Create L6 drivers for limit CRUD
- [ ] Create L5 schemas for limits and thresholds
- [ ] Create basic L5 engines

### Phase 2: Token & Cost Limits
- [ ] TokenLimitEngine with daily/monthly tracking
- [ ] CostLimitEngine integrated with analytics
- [ ] L2 API endpoints

### Phase 3: Credit System
- [ ] CreditEngine with balance tracking
- [ ] Integration with account domain
- [ ] Auto-pause on zero balance

### Phase 4: RAG Auditing
- [ ] RAGAuditEngine with trace analysis
- [ ] Audit trail persistence
- [ ] Customer-facing audit reports

---

## 10. Relationship to Existing Domains

| Domain | Relationship | Data Flow |
|--------|--------------|-----------|
| **policies** | Controls inform policy decisions | Controls → Policies |
| **analytics** | Analytics provides usage data | Analytics → Controls |
| **activity** | Per-run control checks | Activity ↔ Controls |
| **account** | Credit/billing state | Account → Controls |
| **incidents** | Limit violations create incidents | Controls → Incidents |

---

## 11. Governance

### L5/L6 Boundary Rules

| Rule | Enforcement |
|------|-------------|
| L5 engines MUST NOT import sqlalchemy | BLCA enforced |
| L6 drivers MUST NOT contain business logic | Code review |
| All DB operations through drivers | Import boundary |

### Naming Conventions

| Pattern | Layer | Example |
|---------|-------|---------|
| `*_engine.py` | L5 | `token_limit_engine.py` |
| `*_driver.py` | L6 | `limits_driver.py` |
| `*_adapter.py` | L3 | `analytics_adapter.py` |
| `*_facade.py` | L5 | `controls_facade.py` |

---

## 12. References

- HOC Layer Topology: `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md`
- Policies Domain: `backend/app/hoc/cus/policies/POLICIES_DOMAIN_LOCK_FINAL.md`
- Analytics Domain: `backend/app/hoc/cus/analytics/`
- PIN-470: HOC Layer Inventory

---

*Document Status: DRAFT - Pending implementation*
