# HOC Layer Topology V1

**Version:** 1.0.0
**Status:** RATIFIED
**Created:** 2026-01-23
**Author:** Founder + Claude (Architecture Session)
**Supersedes:** LAYER_MODEL.md (partial), API_FACADE_COEXISTENCE_PLAN.md

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-23 | Founder + Claude | Initial ratified version |

---

## 1. Executive Summary

This document defines the canonical layer topology for the House of Cards (HOC) architecture. It establishes:

- **8 layers** from Frontend (L1) to Database (L8)
- **Audience-first, domain-second** organization
- **Governed runtime** as a shared orchestration layer
- **Panel engine** architecture for UI projection
- **Hybrid model** strategy for database tables

---

## 2. Design Principles

### 2.1 First Principles

| Principle | How Applied |
|-----------|-------------|
| **Single Responsibility** | Each layer has exactly one job |
| **Separation of Concerns** | Runtime (L4) separate from business logic (L5) |
| **Dependency Inversion** | Higher layers depend on abstractions |
| **Don't Repeat Yourself** | Shared runtime per audience, not per domain |
| **Locality of Behavior** | Domain logic stays in domain folders |
| **Explicit over Implicit** | Cross-domain calls only at L3 (visible) |

### 2.2 AI Console Vision Alignment

| Vision Goal | Architecture Support |
|-------------|---------------------|
| Multi-audience platform | `{audience}/` at every level |
| Domain-driven design | `{domain}/` for business boundaries |
| Governed execution | L4 runtime enforces governance |
| Panel-based UI | `frontend/{domain}/` for panel engine |
| Full observability | Clear trace path through layers |
| Easy extensibility | New domains = add folders |

---

## 3. Layer Taxonomy

```
┌─────────────────────────────────────────────────────────────────────┐
│  L1: FRONTEND                                                       │
│  AI Console (UI Projection + Panel Engine)                          │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L2.1: API FACADE (ORGANIZER)                                       │
│  houseofcards/api/facades/{audience}/{domain}.py                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L2: APIs                                                           │
│  houseofcards/api/{audience}/{domain}.py                            │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L3: ADAPTERS                                                       │
│  houseofcards/{audience}/{domain}/adapters/*.py                     │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L4: GOVERNED RUNTIME                                               │
│  houseofcards/{audience}/general/runtime/*.py                       │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L5: ENGINES / WORKERS / SCHEMAS                                    │
│  houseofcards/{audience}/{domain}/engines/*.py                      │
│  houseofcards/{audience}/{domain}/workers/*.py                      │
│  houseofcards/{audience}/{domain}/schemas/*.py                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L6: DRIVERS                                                        │
│  houseofcards/{audience}/{domain}/drivers/*.py                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L7: MODELS                                                         │
│  app/models/*.py (shared)                                           │
│  app/{audience}/models/*.py (audience-specific)                     │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L8: DATABASE                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Layer Definitions

### 4.1 L1 — Frontend

**Location:** `website/app-shell/`

**Purpose:**
- AI Console user interface
- Built with UI Projection and Panel Engine
- Consumes API via L2.1 facades

**Technology:** React, TypeScript, Panel-based architecture

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Call L2.1 API facades | Direct backend imports |
| Render panels | Business logic |
| User interaction | Direct database access |

---

### 4.2 L2.1 — API Facade (ORGANIZER)

**Location:** `houseofcards/api/facades/{audience}/{domain}.py`

**Purpose:**
- Conceals API endpoints from outside world
- Groups APIs by audience and domain
- Entry point for all external requests
- HTTP-aware, thin routing only

**Example:**
```python
# houseofcards/api/facades/customer/policies.py
# Layer: L2.1 — API Facade
# AUDIENCE: CUSTOMER
# Role: Organizes policies-related API access

from houseofcards.api.customer import policies, limits

class CustomerPoliciesFacade:
    """Groups all policies-related API routers."""

    routers = [
        policies.router,
        limits.router,
    ]
```

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Import L2 routers | Business logic |
| HTTP routing | Database access |
| Audience grouping | Direct engine calls |
| Domain grouping | Direct model imports |

---

### 4.3 L2 — APIs

**Location:** `houseofcards/api/{audience}/{domain}.py`

**Purpose:**
- HTTP route handlers
- Input validation
- Response formatting
- Delegates to L3 adapters

**Example:**
```python
# houseofcards/api/customer/policies.py
# Layer: L2 — Product API
# AUDIENCE: CUSTOMER

from houseofcards.customer.policies.adapters import PoliciesAdapter

@router.get("/rules")
async def get_rules(request: Request, session: AsyncSession):
    adapter = PoliciesAdapter(session)
    return await adapter.get_rules(get_tenant_id(request))
```

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| HTTP request/response | Business logic |
| Input validation | Direct model access |
| Call L3 adapters | Direct engine calls |
| Response serialization | Cross-domain imports |

---

### 4.4 L3 — Adapters (Distribution Layer)

**Location:** `houseofcards/{audience}/{domain}/adapters/*.py`

**Purpose:**
- Translation between API and domain
- Tenant scoping enforcement
- **Cross-domain imports allowed here**
- Distributes requests to L4 runtime or L5 engines
- Transforms responses to API-safe format

**Example:**
```python
# houseofcards/customer/overview/adapters/overview_adapter.py
# Layer: L3 — Boundary Adapter
# AUDIENCE: CUSTOMER
# Role: Aggregates data from multiple domains

# Cross-domain imports (ALLOWED at L3)
from houseofcards.customer.activity.engines import RunEngine
from houseofcards.customer.incidents.engines import IncidentEngine
from houseofcards.customer.policies.engines import PolicyEngine

class OverviewAdapter:
    async def get_highlights(self, tenant_id: str):
        # Cross-domain aggregation
        runs = await self._run_engine.get_recent(tenant_id)
        incidents = await self._incident_engine.get_active(tenant_id)
        policies = await self._policy_engine.get_pending(tenant_id)
        return self._compose_highlights(runs, incidents, policies)
```

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Call L4 runtime | Know HTTP details |
| Call L5 engines | Business decisions |
| Cross-domain imports | Own database tables |
| Tenant scoping | Direct model mutations |
| Response transformation | |

---

### 4.5 L4 — Governed Runtime (Shared per Audience)

**Location:** `houseofcards/{audience}/general/runtime/*.py`

**Purpose:**
- Trigger mechanisms
- Lifecycle management
- Orchestration of multiple engines
- Shared utilities
- (Optional) Policy/governance checks before engine execution

**Components:**
| File | Responsibility |
|------|----------------|
| `trigger_manager.py` | Event triggers, scheduling |
| `lifecycle_manager.py` | State transitions, cleanup |
| `orchestrator.py` | Multi-engine coordination |
| `governance_gate.py` | Pre-execution governance checks |

**Example:**
```python
# houseofcards/customer/general/runtime/orchestrator.py
# Layer: L4 — Governed Runtime
# AUDIENCE: CUSTOMER
# Role: Orchestrates multi-engine workflows

class CustomerOrchestrator:
    async def execute_workflow(self, workflow_id: str, context: dict):
        # Lifecycle: start
        await self._lifecycle.start(workflow_id)

        # Governance check (optional)
        if not await self._governance.can_proceed(context):
            return GatedResult(blocked=True)

        # Orchestrate engines
        result = await self._run_engines(context)

        # Lifecycle: complete
        await self._lifecycle.complete(workflow_id)
        return result
```

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Call L5 engines | Know HTTP |
| Call L6 drivers | Cross-audience imports |
| Lifecycle control | Domain-specific logic |
| Trigger management | Direct API response |
| Shared utilities | |

---

### 4.6 L5 — Engines / Workers / Schemas (Domain Business Logic)

**Location:**
- `houseofcards/{audience}/{domain}/engines/*.py` — Business rules, decisions
- `houseofcards/{audience}/{domain}/workers/*.py` — Heavy computation
- `houseofcards/{audience}/{domain}/schemas/*.py` — Data contracts

**Purpose:**

| Component | Responsibility |
|-----------|----------------|
| **Engines** | Business rules, pattern detection, decisions |
| **Workers** | Heavy computation, background processing |
| **Schemas** | Pydantic models, data validation, contracts |

**Example — Engine:**
```python
# houseofcards/customer/policies/engines/policy_proposal.py
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER

class PolicyProposalEngine:
    async def generate_proposal(self, tenant_id: str, trigger: dict):
        # Business logic
        patterns = await self._detect_patterns(trigger)
        proposal = self._build_proposal(patterns)
        await self._driver.save_proposal(proposal)
        return proposal
```

**Example — Worker:**
```python
# houseofcards/customer/analytics/workers/prediction_worker.py
# Layer: L5 — Domain Worker
# AUDIENCE: CUSTOMER

class PredictionWorker:
    async def compute_predictions(self, tenant_id: str):
        # Heavy computation
        data = await self._driver.fetch_historical(tenant_id)
        predictions = self._ml_model.predict(data)
        await self._driver.save_predictions(predictions)
```

**Example — Schema:**
```python
# houseofcards/customer/policies/schemas/policy_models.py
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER

from pydantic import BaseModel

class PolicyRuleSummary(BaseModel):
    rule_id: str
    name: str
    enforcement_mode: str
    status: str

class PolicyProposalCreate(BaseModel):
    tenant_id: str
    trigger_type: str
    proposed_rule: dict
```

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Business decisions | Know HTTP/API |
| Pattern detection | Direct response formatting |
| Call L6 drivers | Cross-audience imports |
| Call sibling workers | Own models directly |
| Use domain schemas | |

---

### 4.7 L6 — Drivers (Database Operations)

**Location:** `houseofcards/{audience}/{domain}/drivers/*.py`

**Purpose:**
- Database read/write operations
- Query builders
- Data transformation to/from models

**Example:**
```python
# houseofcards/customer/policies/drivers/policy_driver.py
# Layer: L6 — Database Driver
# AUDIENCE: CUSTOMER

from app.customer.models.policy import PolicyRule

class PolicyDriver:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_rules(self, tenant_id: str) -> list[PolicyRule]:
        query = select(PolicyRule).where(PolicyRule.tenant_id == tenant_id)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def save_rule(self, rule: PolicyRule) -> PolicyRule:
        self._session.add(rule)
        await self._session.flush()
        return rule
```

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Database operations | Business logic |
| Query building | Know about HTTP |
| Model imports (L7) | Call engines |
| Data transformation | Cross-domain queries |

---

### 4.8 L7 — Models (Database Tables)

**Location:**
- `app/models/*.py` — Shared tables
- `app/{audience}/models/*.py` — Audience-specific tables

**Purpose:**
- SQLAlchemy/SQLModel table definitions
- Database schema
- Table ownership

**Shared vs Audience-Specific:**

| Category | Location | Examples |
|----------|----------|----------|
| **Shared** | `app/models/` | `tenant.py`, `base.py`, `audit_ledger.py` |
| **Customer** | `app/customer/models/` | `policy.py`, `killswitch.py`, `knowledge.py` |
| **Founder** | `app/founder/models/` | `ops_events.py`, `ops_segments.py` |
| **Internal** | `app/internal/models/` | `recovery.py`, `agent.py` |

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Table definitions | Business logic |
| Column declarations | HTTP knowledge |
| Relationships | Import from L1-L6 |
| Indexes | |

---

### 4.9 L8 — Database

**Purpose:** PostgreSQL database

**Note:** Not a code layer, but the final destination for all data operations.

---

## 5. Panel Engine Architecture

**Status:** To Be Developed

**Location:** `houseofcards/{audience}/frontend/{domain}/*.py`

**Purpose:**
- UI projection logic
- Panel state management
- Serves L1 frontend

**Structure:**
```
houseofcards/
└── customer/
    └── frontend/
        ├── overview/
        │   └── panels/
        │       ├── highlights_panel.py
        │       └── pulse_panel.py
        ├── activity/
        │   └── panels/
        │       └── runs_panel.py
        └── policies/
            └── panels/
                └── rules_panel.py
```

---

## 6. Directory Structure (Complete)

```
houseofcards/
├── api/
│   ├── facades/                          # L2.1 — ORGANIZER
│   │   ├── __init__.py
│   │   ├── customer/
│   │   │   ├── __init__.py
│   │   │   ├── overview.py
│   │   │   ├── activity.py
│   │   │   ├── incidents.py
│   │   │   ├── policies.py
│   │   │   ├── logs.py
│   │   │   ├── analytics.py
│   │   │   ├── integrations.py
│   │   │   ├── api_keys.py
│   │   │   └── account.py
│   │   ├── founder/
│   │   │   ├── __init__.py
│   │   │   └── ops.py
│   │   └── internal/
│   │       ├── __init__.py
│   │       └── platform.py
│   │
│   ├── customer/                         # L2 — Customer APIs
│   │   ├── __init__.py
│   │   ├── overview.py
│   │   ├── activity.py
│   │   ├── incidents.py
│   │   ├── policies.py
│   │   ├── logs.py
│   │   ├── analytics.py
│   │   ├── integrations.py
│   │   ├── api_keys.py
│   │   └── account.py
│   │
│   ├── founder/                          # L2 — Founder APIs
│   │   ├── __init__.py
│   │   └── ops.py
│   │
│   └── internal/                         # L2 — Internal APIs
│       ├── __init__.py
│       └── platform.py
│
├── customer/
│   ├── general/                          # Shared for Customer
│   │   ├── __init__.py
│   │   ├── runtime/                      # L4 — Governed Runtime
│   │   │   ├── __init__.py
│   │   │   ├── trigger_manager.py
│   │   │   ├── lifecycle_manager.py
│   │   │   ├── orchestrator.py
│   │   │   └── governance_gate.py
│   │   ├── utils/                        # Shared Utilities
│   │   │   ├── __init__.py
│   │   │   └── time.py
│   │   └── schemas/                      # Shared Schemas
│   │       └── __init__.py
│   │
│   ├── frontend/                         # Panel Engine (TBD)
│   │   ├── overview/
│   │   │   └── panels/
│   │   ├── activity/
│   │   │   └── panels/
│   │   └── ... (per domain)
│   │
│   ├── overview/
│   │   ├── __init__.py
│   │   ├── adapters/                     # L3
│   │   │   └── overview_adapter.py
│   │   ├── engines/                      # L5
│   │   ├── workers/                      # L5
│   │   ├── schemas/                      # L5
│   │   └── drivers/                      # L6
│   │
│   ├── activity/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   ├── incidents/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   ├── logs/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   ├── api_keys/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   ├── engines/
│   │   ├── workers/
│   │   ├── schemas/
│   │   └── drivers/
│   │
│   └── account/
│       ├── __init__.py
│       ├── adapters/
│       ├── engines/
│       ├── workers/
│       ├── schemas/
│       └── drivers/
│
├── founder/
│   ├── general/
│   │   ├── runtime/                      # L4
│   │   └── utils/
│   │
│   ├── frontend/                         # Panel Engine (TBD)
│   │   └── ops/
│   │       └── panels/
│   │
│   └── ops/
│       ├── adapters/                     # L3
│       ├── engines/                      # L5
│       ├── workers/                      # L5
│       ├── schemas/                      # L5
│       └── drivers/                      # L6
│
└── internal/
    ├── general/
    │   ├── runtime/                      # L4
    │   └── utils/
    │
    ├── platform/
    │   ├── adapters/
    │   ├── engines/
    │   ├── workers/
    │   ├── schemas/
    │   └── drivers/
    │
    ├── recovery/
    │   ├── adapters/
    │   ├── engines/
    │   ├── workers/
    │   ├── schemas/
    │   └── drivers/
    │
    └── agent/
        ├── adapters/
        ├── engines/
        ├── workers/
        ├── schemas/
        └── drivers/


app/
├── models/                               # L7 — SHARED
│   ├── __init__.py
│   ├── base.py
│   ├── tenant.py
│   ├── audit_ledger.py
│   └── worker_run.py
│
├── customer/
│   └── models/                           # L7 — CUSTOMER
│       ├── __init__.py
│       ├── policy.py
│       ├── policy_control_plane.py
│       ├── killswitch.py
│       └── knowledge_lifecycle.py
│
├── founder/
│   └── models/                           # L7 — FOUNDER
│       ├── __init__.py
│       ├── ops_events.py
│       └── ops_segments.py
│
└── internal/
    └── models/                           # L7 — INTERNAL
        ├── __init__.py
        ├── recovery.py
        └── agent.py
```

---

## 7. Import Rules

### 7.1 Layer Dependencies

```
L2.1 (Facades)  → L2 (APIs) only
L2   (APIs)     → L3 (Adapters) only
L3   (Adapters) → L4 (Runtime), L5 (Engines) — CROSS-DOMAIN ALLOWED
L4   (Runtime)  → L5 (Engines), L6 (Drivers)
L5   (Engines)  → L5 (Workers/Schemas), L6 (Drivers)
L5   (Workers)  → L6 (Drivers)
L5   (Schemas)  → L7 (Models) — for type references only
L6   (Drivers)  → L7 (Models)
L7   (Models)   → Nothing (leaf)
```

### 7.2 Visual Diagram

```
L2.1 → L2 → L3 ─┬─→ L4 → L5 → L6 → L7
                │        ↓
                └───────→ L5 (cross-domain at L3)
```

### 7.3 Cross-Domain Rules

| Layer | Cross-Domain Import | Reason |
|-------|---------------------|--------|
| L2.1, L2 | ❌ Forbidden | Stay within audience/domain |
| **L3** | ✅ **Allowed** | Aggregation point for multi-domain data |
| L4 | ⚠️ Same audience only | Shared runtime per audience |
| L5, L6 | ❌ Forbidden | Domain isolation |
| L7 | ❌ Forbidden | Table isolation |

---

## 8. Call Flow Examples

### 8.1 Single Domain Request

**Request:** `GET /api/v1/customer/policies/rules`

```
Browser
    ↓
houseofcards/api/facades/customer/policies.py       (L2.1)
    ↓
houseofcards/api/customer/policies.py               (L2)
    ↓
houseofcards/customer/policies/adapters/adapter.py  (L3)
    ↓
houseofcards/customer/general/runtime/orchestrator.py (L4)
    ↓
houseofcards/customer/policies/engines/rules.py     (L5)
    ↓
houseofcards/customer/policies/drivers/policy.py    (L6)
    ↓
app/customer/models/policy.py                       (L7)
    ↓
Database                                            (L8)
```

### 8.2 Cross-Domain Request (Overview)

**Request:** `GET /api/v1/customer/overview/highlights`

```
Browser
    ↓
houseofcards/api/facades/customer/overview.py       (L2.1)
    ↓
houseofcards/api/customer/overview.py               (L2)
    ↓
houseofcards/customer/overview/adapters/adapter.py  (L3 — CROSS-DOMAIN)
    ├── imports from customer/activity/engines/
    ├── imports from customer/incidents/engines/
    └── imports from customer/policies/engines/
    ↓
houseofcards/customer/general/runtime/orchestrator.py (L4)
    ↓
├── customer/activity/engines/*.py                  (L5)
├── customer/incidents/engines/*.py                 (L5)
└── customer/policies/engines/*.py                  (L5)
    ↓
├── customer/activity/drivers/*.py                  (L6)
├── customer/incidents/drivers/*.py                 (L6)
└── customer/policies/drivers/*.py                  (L6)
    ↓
app/customer/models/*                               (L7)
    ↓
Database                                            (L8)
```

---

## 9. Audiences

### 9.1 Defined Audiences

| Audience | Console | Description |
|----------|---------|-------------|
| **customer** | console.agenticverz.com | Customer Console users |
| **founder** | ops.agenticverz.com | Founder/Admin users |
| **internal** | (no console) | Platform infrastructure |

### 9.2 Domains per Audience

**Customer (10 domains):**
1. overview
2. activity
3. incidents
4. policies
5. logs
6. analytics
7. integrations
8. api_keys
9. account
10. general (shared runtime/utils)

**Founder (1 domain + shared):**
1. ops
2. general (shared runtime/utils)

**Internal (3 domains + shared):**
1. platform
2. recovery
3. agent
4. general (shared runtime/utils)

---

## 10. Governance Enforcement

### 10.1 CI Checks

| Check | Enforces | Blocking |
|-------|----------|----------|
| `layer_validator.py` | Import rules | YES |
| `audience_guard.py` | Audience boundaries | YES |
| `cross_domain_checker.py` | L3-only cross-domain | YES |

### 10.2 File Header Requirement

Every file must include:

```python
# Layer: L{X} — {Layer Name}
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {Single-line description}
# Callers: {Who calls this}
# Reference: HOC_LAYER_TOPOLOGY_V1.md
```

---

## 11. Migration Notes

### 11.1 What Moves

| From | To |
|------|-----|
| `app/api/*.py` | `houseofcards/api/{audience}/*.py` |
| `app/adapters/*.py` | `houseofcards/{audience}/{domain}/adapters/` |
| `app/services/*.py` (facades) | `houseofcards/{audience}/{domain}/engines/` |
| `app/models/*.py` (audience-specific) | `app/{audience}/models/` |

### 11.2 What Stays

| Location | Reason |
|----------|--------|
| `app/models/*.py` (shared) | Cross-audience tables |
| `app/worker/*.py` | Infrastructure workers (runner, lifecycle) |

### 11.3 What's New

| Location | Purpose |
|----------|---------|
| `houseofcards/api/facades/` | L2.1 organizers |
| `houseofcards/{audience}/general/runtime/` | L4 governed runtime |
| `houseofcards/{audience}/frontend/` | Panel engine |
| `houseofcards/{audience}/{domain}/workers/` | L5 domain workers |

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-23 | Initial ratified version |

---

## 13. References

- PIN-464: HOC Customer Domain Comprehensive Audit
- LAYER_MODEL.md: Previous layer definitions (partially superseded)
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md: Domain definitions

---

**Document Status:** RATIFIED
**Next Review:** When migration begins
