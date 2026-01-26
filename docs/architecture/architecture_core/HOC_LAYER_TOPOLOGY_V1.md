# HOC Layer Topology V1

**Version:** 1.4.0
**Status:** RATIFIED
**Created:** 2026-01-23
**Author:** Founder + Claude (Architecture Session)
**Supersedes:** LAYER_MODEL.md (partial), API_FACADE_COEXISTENCE_PLAN.md

---

## ⚠️ CANONICAL REFERENCE STATUS

> **This document is the CANONICAL layer architecture for House of Cards (HOC).**
>
> **Package name:** `hoc` (renamed from `hoc` in v1.4.0)
>
> **Referenced in:** `/CLAUDE.md` (Section: HOC Layer Topology - BL-HOC-LAYER-001)
>
> When working with HOC files, layer classification, import rules, or file naming conventions — **this document is authoritative**.

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-23 | Founder + Claude | Initial ratified version |
| 1.1.0 | 2026-01-23 | Founder + Claude | L4 Runtime restructured: Parts-based architecture (authority/execution/consequences), Independence Guarantee, L4 Runtime Contract |
| 1.2.0 | 2026-01-23 | Founder + Claude | Added layer contracts: L2.1 Facade, L3 Adapter, L5 Worker, L6 Driver. Updated Panel Engine rules. Added CI Enforcement section. |
| 1.3.0 | 2026-01-24 | Founder + Claude | Phase 3 Directory Restructure: Layer-prefixed folder names (L3_adapters/, L5_engines/, L6_drivers/). L4 centralized to general/L4_runtime/ only. API nesting (L2.1 + L2 together). |
| 1.4.0 | 2026-01-24 | Founder + Claude | Package & audience rename: `hoc` → `hoc`, `customer` → `cus`, `founder` → `fdr`, `internal` → `int`. Saves 14 chars per import path. |

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
│  hoc/api/facades/{audience}/{domain}.py                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L2: APIs                                                           │
│  hoc/api/{audience}/{domain}.py                            │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L3: ADAPTERS                                                       │
│  hoc/{audience}/{domain}/adapters/*.py                     │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L4: GOVERNED RUNTIME                                               │
│  hoc/{audience}/general/L4_runtime/*.py                       │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L5: ENGINES / WORKERS / SCHEMAS                                    │
│  hoc/{audience}/{domain}/engines/*.py                      │
│  hoc/{audience}/{domain}/workers/*.py                      │
│  hoc/{audience}/{domain}/schemas/*.py                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L6: DRIVERS                                                        │
│  hoc/{audience}/{domain}/drivers/*.py                      │
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

**Location:** `hoc/api/facades/{audience}/{domain}.py`

**Purpose:**
- Conceals API endpoints from outside world
- Groups APIs by audience and domain
- Entry point for all external requests
- HTTP-aware, thin routing only

**Example:**
```python
# hoc/api/facades/cus/policies.py
# Layer: L2.1 — API Facade
# AUDIENCE: CUSTOMER
# Role: Organizes policies-related API access

from hoc.api.cus import policies, limits

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

#### L2.1 Facade Contract

```text
L2.1 FACADE CONTRACT

1. Facades are ORGANIZERS ONLY — no business logic
2. Facades MAY import L2 routers ONLY
3. Facades MAY NOT import:
   - Adapters (L3)
   - Runtime (L4)
   - Engines/Workers (L5)
   - Drivers (L6)
   - Models (L7)
4. Facades MAY apply audience/domain grouping
5. Facades MAY apply HTTP route binding
6. Validation logic belongs in L2, not L2.1

Violations indicate authority drift.
```

**BLCA Enforcement Rule:**
```
hoc/api/facades/** → CANNOT import → hoc/{audience}/**
```

---

### 4.3 L2 — APIs

**Location:** `hoc/api/{audience}/{domain}.py`

**Purpose:**
- HTTP route handlers
- Input validation
- Response formatting
- Delegates to L3 adapters

**Example:**
```python
# hoc/api/cus/policies.py
# Layer: L2 — Product API
# AUDIENCE: CUSTOMER

from hoc.cus.policies.L3_adapters import PoliciesAdapter

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

**Location:** `hoc/{audience}/{domain}/adapters/*.py`

**Purpose:**
- Translation between API and domain
- Tenant scoping enforcement
- **Cross-domain imports allowed here**
- Distributes requests to L4 runtime or L5 engines
- Transforms responses to API-safe format

**Example:**
```python
# hoc/cus/overview/L3_adapters/overview_adapter.py
# Layer: L3 — Boundary Adapter
# AUDIENCE: CUSTOMER
# Role: Aggregates data from multiple domains

# Cross-domain imports (ALLOWED at L3)
from hoc.cus.activity.L5_engines import RunEngine
from hoc.cus.incidents.L5_engines import IncidentEngine
from hoc.cus.policies.L5_engines import PolicyEngine

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

#### L3 Adapter Contract

```text
L3 ADAPTER CONTRACT

1. Translation + aggregation ONLY
2. NO state mutation
3. NO retries or fallback logic
4. NO policy decisions
5. NO short-circuiting L4 runtime
6. Tenant scoping enforcement ONLY

Adapters that violate this contract become invisible orchestrators.
When failures occur, L4 cannot reason about what actually executed.
Violations are architectural defects, not bugs.
```

**Why This Matters:**

Adapters are the cross-domain aggregation point, making them magnets for "just one more thing."
If adapters start doing retries, they bypass L4 governance and create non-deterministic failure modes.

**Standard Adapter Header:**
```python
# Layer: L3 — Boundary Adapter
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
#
# ADAPTER CONTRACT:
# - Translation + aggregation only
# - No state mutation
# - No retries
# - No policy decisions
```

---

### 4.5 L4 — Governed Runtime (Control Plane)

**Location:** `hoc/{audience}/general/L4_runtime/`

**Purpose:**

L4 is the system's execution authority. It is the ONLY layer allowed to:
- Authorize execution
- Trigger domain engines
- Coordinate multi-engine behavior
- React to system consequences

**L4 is NOT:**
- A pipeline
- A timeline
- A workflow engine

**L4 IS:**
- A control plane
- Centralized authority (all execution flows through L4 exactly once)
- Composed of independent parts

---

#### L4 Internal Structure (Three Independent Parts)

| Part | Folder | Purpose | Can Block? | Can Execute? |
|------|--------|---------|------------|--------------|
| **Authority** | `authority/` | Grant/deny permission | ✅ Yes | ❌ No |
| **Execution** | `execution/` | Mechanical triggering | ❌ No | ✅ Yes |
| **Consequences** | `consequences/` | React to outcomes | ❌ No | ❌ No |
| **Contracts** | `contracts/` | Shared verdict objects | — | — |

---

#### Independence Guarantee

These parts:
- Do NOT call each other
- Do NOT share mutable state
- Do NOT assume execution order
- Do NOT block each other
- Are linked only by immutable inputs (verdicts, IDs, events)

---

#### L4 Runtime Contract

```text
L4 RUNTIME CONTRACT

1. Governance logic MUST be pure and side-effect free.
2. Orchestration MUST assume authority already granted.
3. Consequence handlers MUST NOT block execution.
4. Engines MUST NOT perform governance checks.
5. Adapters MUST NOT bypass runtime.
6. All execution enters via L4 exactly once.
7. No part may impersonate another.
```

---

#### What "Centralized" Means

Centralized does NOT mean:
- Synchronous
- Sequential
- Single-threaded
- A bottleneck

Centralized MEANS:
- All execution authority flows through L4 exactly once
- No engine, adapter, or worker may self-authorize

---

#### Directory Structure

```
hoc/{audience}/general/L4_runtime/
├── authority/
│   └── governance_gate.py      # Grants/denies execution
├── execution/
│   └── orchestrator.py         # Triggers engines/workers
├── consequences/
│   └── enforcement.py          # Incidents, audit, compensation
└── contracts/
    └── runtime_verdict.py      # Immutable verdict object
```

---

#### Example — Authority Part

```python
# hoc/cus/general/L4_runtime/authority/governance_gate.py
# Layer: L4 — Governed Runtime (Authority)
# AUDIENCE: CUSTOMER
# Role: Grants or denies execution permission

from hoc.cus.general.L4_runtime.contracts.runtime_verdict import RuntimeVerdict

class GovernanceGate:
    """Pure function: context → verdict. No side effects."""

    async def evaluate(self, context: dict) -> RuntimeVerdict:
        # Check policies, limits, killswitches
        if await self._is_blocked(context):
            return RuntimeVerdict(allowed=False, reason="policy_blocked")
        return RuntimeVerdict(allowed=True)
```

---

#### Example — Execution Part

```python
# hoc/cus/general/L4_runtime/execution/orchestrator.py
# Layer: L4 — Governed Runtime (Execution)
# AUDIENCE: CUSTOMER
# Role: Mechanical triggering of engines (assumes authority granted)

class Orchestrator:
    """Triggers engines. Does NOT check permissions (already granted)."""

    async def execute(self, verdict: RuntimeVerdict, context: dict):
        if not verdict.allowed:
            raise RuntimeError("Orchestrator called without authority")

        # Trigger engines mechanically
        return await self._run_engines(context)
```

---

#### Example — Consequences Part

```python
# hoc/cus/general/L4_runtime/consequences/enforcement.py
# Layer: L4 — Governed Runtime (Consequences)
# AUDIENCE: CUSTOMER
# Role: Reacts to outcomes (non-blocking)

class EnforcementHandler:
    """Reacts to outcomes. Cannot block. Cannot execute."""

    async def handle(self, outcome: dict):
        # Log to audit, create incidents, trigger compensation
        await self._log_audit(outcome)
        if outcome.get("failed"):
            await self._create_incident(outcome)
```

---

**Rules:**
| Allowed | Forbidden |
|---------|-----------|
| Call L5 engines (from execution/) | Know HTTP |
| Call L6 drivers | Cross-audience imports |
| Issue verdicts (from authority/) | Domain-specific logic |
| React to outcomes (from consequences/) | Direct API response |
| Share immutable contracts | Parts calling each other |

---

### 4.6 L5 — Engines / Workers / Schemas (Domain Business Logic)

**Location:**
- `hoc/{audience}/{domain}/engines/*.py` — Business rules, decisions
- `hoc/{audience}/{domain}/workers/*.py` — Heavy computation
- `hoc/{audience}/{domain}/schemas/*.py` — Data contracts

**Purpose:**

| Component | Responsibility |
|-----------|----------------|
| **Engines** | Business rules, pattern detection, decisions |
| **Workers** | Heavy computation, background processing |
| **Schemas** | Pydantic models, data validation, contracts |

**Example — Engine:**
```python
# hoc/cus/policies/L5_engines/policy_proposal.py
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
# hoc/cus/analytics/workers/prediction_worker.py
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
# hoc/cus/policies/L5_schemas/policy_models.py
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

#### L5 Worker Contract

```text
L5 WORKER CONTRACT

1. Workers MUST be idempotent OR explicitly marked non-idempotent
2. Workers MUST be restart-safe
3. Workers MUST NOT create incidents directly
4. Workers MUST NOT enforce policy
5. Workers MUST NOT manage retries
6. Workers MUST NOT perform governance checks

Failure escalation flows through L4:
  L4/consequences → incident creation
  L4/execution → retry logic
  L4/authority → policy enforcement
```

**Failure Ownership Matrix:**

| Concern | Owner | Location |
|---------|-------|----------|
| Retry logic | L4 | `execution/orchestrator.py` |
| Backoff policy | L4 | `execution/orchestrator.py` |
| Failure classification | L4 | `consequences/enforcement.py` |
| Incident creation | L4 | `consequences/enforcement.py` |
| Compensation | L4 | `consequences/enforcement.py` |
| Idempotency | L5 Worker | Worker itself |

**Standard Worker Header:**
```python
# Layer: L5 — Domain Worker
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Idempotent: YES | NO (if NO, explain why)
#
# WORKER CONTRACT:
# - Restart-safe
# - No incident creation
# - No policy enforcement
# - No retry management
```

---

### 4.7 L6 — Drivers (Database Operations)

**Location:** `hoc/{audience}/{domain}/drivers/*.py`

**Purpose:**
- Database read/write operations
- Query builders
- Data transformation to/from models

**Example:**
```python
# hoc/cus/policies/L6_drivers/policy_driver.py
# Layer: L6 — Database Driver
# AUDIENCE: CUSTOMER

from app.cus.models.policy import PolicyRule

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

#### L6 Driver Contract

```text
L6 DRIVER CONTRACT

1. Drivers MUST NOT return ORM models to engines
2. Drivers MUST return: primitives, dicts, dataclasses, or Pydantic models
3. ORM models are L7-only and L6-only
4. Engines (L5) MUST be schema-ignorant
5. Query logic stays in drivers, never in engines
6. Drivers own the data shape transformation

This enables:
- Schema migrations without logic breaks
- Testability without database
- Clear ownership of data shape
```

**Return Type Guidance:**

| From Driver | To Engine | Allowed? |
|-------------|-----------|----------|
| `PolicyRule` (ORM model) | Engine | ❌ No |
| `PolicyRuleSnapshot` (dataclass) | Engine | ✅ Yes |
| `dict` | Engine | ✅ Yes |
| Pydantic model | Engine | ✅ Yes |
| `list[ORM]` | Engine | ❌ No |
| `list[dict]` | Engine | ✅ Yes |

**Why This Matters:**

If engines receive ORM models:
- Engines become schema-coupled
- Migrations break logic
- Testability collapses (need real DB for unit tests)
- Query patterns leak upward

**Standard Driver Header:**
```python
# Layer: L6 — Database Driver
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
#
# DRIVER CONTRACT:
# - Returns domain objects, not ORM models
# - Owns query logic
# - Owns data shape transformation
```

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
| **Customer** | `app/cus/models/` | `policy.py`, `killswitch.py`, `knowledge.py` |
| **Founder** | `app/fdr/models/` | `ops_events.py`, `ops_segments.py` |
| **Internal** | `app/int/models/` | `recovery.py`, `agent.py` |

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

**Location:** `hoc/{audience}/frontend/{domain}/*.py`

**Purpose:**
- UI projection logic
- Panel state management
- Serves L1 frontend

**Structure:**
```
hoc/
└── cus/
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

### Panel Engine Contract

```text
PANEL ENGINE CONTRACT

1. Panels are READ-ONLY projection services
2. NO UI decisions (layout, colors, interactions)
3. NO feature flags
4. NO presentation logic
5. Data shape ONLY — frontend owns rendering
6. NO stateful behavior beyond request scope

Panels answer: "What data should be shown?"
Frontend answers: "How should it be shown?"
```

**Separation of Concerns:**

| Concern | Owner | Location |
|---------|-------|----------|
| What data | Panel Engine (Backend) | `hoc/{audience}/frontend/` |
| Data shape | Panel Engine (Backend) | Panel response schema |
| Layout | Frontend | React components |
| Styling | Frontend | CSS/Tailwind |
| Interactions | Frontend | Event handlers |
| Feature flags | Frontend or Platform | Not in panels |

**Why This Matters:**

Backend-hosted panels that make UI decisions:
- Become tightly coupled to frontend UX
- Block independent frontend evolution
- Accumulate presentation logic
- Become stateful over time

**Standard Panel Header:**
```python
# Layer: Panel Engine
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
#
# PANEL CONTRACT:
# - Read-only projection
# - No UI decisions
# - No feature flags
# - Data shape only
```

---

## 6. Directory Structure (Complete)

> **NOTE (v1.3.0):** Phase 3 introduces layer-prefixed folder names for clarity.
> See `PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md` for migration details.

### 6.1 API Layer (L2.1 + L2 Nested)

```
hoc/api/
├── customer/                             # Customer APIs
│   ├── __init__.py
│   ├── overview/
│   │   ├── __init__.py
│   │   ├── overview_facade.py            # L2.1 — API composition
│   │   └── overview_routes.py            # L2 — HTTP handlers
│   ├── activity/
│   │   ├── __init__.py
│   │   ├── activity_facade.py
│   │   └── activity_routes.py
│   ├── incidents/
│   │   ├── __init__.py
│   │   ├── incidents_facade.py
│   │   └── incidents_routes.py
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── policies_facade.py
│   │   └── policies_routes.py
│   ├── logs/
│   │   ├── __init__.py
│   │   ├── logs_facade.py
│   │   └── logs_routes.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── analytics_facade.py
│   │   └── analytics_routes.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── integrations_facade.py
│   │   └── integrations_routes.py
│   ├── api_keys/
│   │   ├── __init__.py
│   │   ├── api_keys_facade.py
│   │   └── api_keys_routes.py
│   └── account/
│       ├── __init__.py
│       ├── account_facade.py
│       └── account_routes.py
│
├── founder/                              # Founder APIs
│   └── ops/
│       ├── __init__.py
│       ├── ops_facade.py
│       └── ops_routes.py
│
└── internal/                             # Internal APIs
    └── platform/
        ├── __init__.py
        ├── platform_facade.py
        └── platform_routes.py
```

### 6.2 General Domain (Meta/Cross-Domain)

```
hoc/cus/general/
├── __init__.py
├── L4_runtime/                           # L4 — Control Plane (ONLY L4)
│   ├── __init__.py
│   ├── authority/                        # Part 1: Grant/deny permission
│   │   ├── __init__.py
│   │   └── governance_gate.py
│   ├── execution/                        # Part 2: Mechanical triggering
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   ├── consequences/                     # Part 3: React to outcomes
│   │   ├── __init__.py
│   │   └── enforcement.py
│   └── contracts/                        # Shared verdict objects
│       ├── __init__.py
│       └── runtime_verdict.py
├── L3_mcp/                               # L3 — Cross-domain MCP adapters
│   └── __init__.py
├── L5_controls/                          # L5 — Control engines (killswitch, guards)
│   └── __init__.py
├── L5_lifecycle/                         # L5 — Lifecycle management
│   └── __init__.py
├── L5_workflow/                          # L5 — Workflow contracts
│   └── __init__.py
├── L5_schemas/                           # L5 — Shared schemas
│   └── __init__.py
├── L5_utils/                             # L5 — Shared utilities
│   └── __init__.py
├── L5_ui/                                # L5 — UI projection logic
│   └── __init__.py
└── L6_drivers/                           # L6 — Shared data access
    └── __init__.py
```

### 6.3 Standard Domains (Layer-Prefixed)

```
hoc/cus/{domain}/           # overview, activity, incidents, etc.
├── __init__.py
├── L3_adapters/                          # L3 — Translation, bridges
│   └── __init__.py
├── L5_engines/                           # L5 — Business logic (includes facades)
│   └── __init__.py
├── L5_schemas/                           # L5 — Dataclasses, types
│   └── __init__.py
└── L6_drivers/                           # L6 — Data access
    └── __init__.py
```

### 6.4 Complete Customer Domain Structure

```
hoc/cus/
├── general/                              # Meta/Cross-domain (see 6.2)
│
├── overview/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── activity/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── incidents/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── policies/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── logs/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── analytics/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── integrations/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── api_keys/
│   ├── __init__.py
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
└── account/
    ├── __init__.py
    ├── L3_adapters/
    ├── L5_engines/
    ├── L5_schemas/
    └── L6_drivers/
```

### 6.5 Other Audiences (Founder, Internal)

```
hoc/fdr/
├── general/
│   ├── L4_runtime/                       # L4 (same structure as customer)
│   └── L5_utils/
│
└── ops/
    ├── L3_adapters/
    ├── L5_engines/
    ├── L5_schemas/
    └── L6_drivers/

hoc/int/
├── general/
│   ├── L4_runtime/
│   └── L5_utils/
│
├── platform/
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
├── recovery/
│   ├── L3_adapters/
│   ├── L5_engines/
│   ├── L5_schemas/
│   └── L6_drivers/
│
└── agent/
    ├── L3_adapters/
    ├── L5_engines/
    ├── L5_schemas/
    └── L6_drivers/
```

### 6.6 Models (Centralized)

```
app/models/                               # L7 — SHARED (centralized)
├── __init__.py
├── base.py
├── tenant.py
├── audit_ledger.py
└── worker_run.py
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

**Request:** `GET /api/v1/cus/policies/rules`

```
Browser
    ↓
hoc/api/facades/cus/policies.py       (L2.1)
    ↓
hoc/api/cus/policies.py               (L2)
    ↓
hoc/cus/policies/L3_adapters/adapter.py  (L3)
    ↓
hoc/cus/general/L4_runtime/orchestrator.py (L4)
    ↓
hoc/cus/policies/L5_engines/rules.py     (L5)
    ↓
hoc/cus/policies/L6_drivers/policy.py    (L6)
    ↓
app/cus/models/policy.py                       (L7)
    ↓
Database                                            (L8)
```

### 8.2 Cross-Domain Request (Overview)

**Request:** `GET /api/v1/cus/overview/highlights`

```
Browser
    ↓
hoc/api/facades/cus/overview.py       (L2.1)
    ↓
hoc/api/cus/overview.py               (L2)
    ↓
hoc/cus/overview/L3_adapters/adapter.py  (L3 — CROSS-DOMAIN)
    ├── imports from customer/activity/L5_engines/
    ├── imports from customer/incidents/L5_engines/
    └── imports from customer/policies/L5_engines/
    ↓
hoc/cus/general/L4_runtime/orchestrator.py (L4)
    ↓
├── customer/activity/L5_engines/*.py                  (L5)
├── customer/incidents/L5_engines/*.py                 (L5)
└── customer/policies/L5_engines/*.py                  (L5)
    ↓
├── customer/activity/L6_drivers/*.py                  (L6)
├── customer/incidents/L6_drivers/*.py                 (L6)
└── customer/policies/L6_drivers/*.py                  (L6)
    ↓
app/cus/models/*                               (L7)
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
| `contract_validator.py` | Layer contract compliance | YES |
| `orm_leakage_checker.py` | L6→L5 ORM isolation | YES |

### 10.2 BLCA Layer-Specific Rules

**BLCA (Bidirectional Layer Consistency Auditor)** must enforce these import rules:

| Source | Forbidden Targets | Rule |
|--------|-------------------|------|
| `hoc/api/facades/**` | `hoc/{audience}/**` | L2.1 cannot import L3-L7 |
| `hoc/api/{audience}/**` | `hoc/{audience}/**/engines/**` | L2 cannot import L5 directly |
| `hoc/{audience}/**/engines/**` | `app/**/models/**` (ORM) | L5 cannot import ORM models |
| `hoc/{audience}/**/workers/**` | `hoc/{audience}/**/runtime/**` | L5 workers cannot import L4 |

**Legacy Namespace Ban:**
```bash
# FAIL if any HOC file imports from legacy app.services
fail if: hoc/** imports app.services.**
```

### 10.3 Contract Enforcement

Each layer contract must be mechanically verifiable:

| Contract | Enforcement Method |
|----------|-------------------|
| L2.1 Facade Contract | Import analysis (no L3-L7 imports) |
| L3 Adapter Contract | Code pattern analysis (no retry/mutation patterns) |
| L4 Runtime Contract | Part isolation check (no inter-part calls) |
| L5 Worker Contract | Ownership check (no incident/policy creation) |
| L6 Driver Contract | Return type analysis (no ORM in returns) |
| Panel Engine Contract | Read-only check (no state mutation) |

### 10.4 Quarantine Registry

Legacy files that violate layer rules must be listed in a single index:

```
docs/architecture/QUARANTINE_REGISTRY.md
```

**Quarantine Rules:**
1. Every quarantined file must be explicitly listed
2. Each entry must include: file path, violation type, migration plan
3. No new files may be added to quarantine (fix or delete)
4. Quarantine count must decrease monotonically

### 10.5 Layer Assertion Tests

Cheap tests that import nothing but scan imports:

```python
# tests/architecture/test_layer_imports.py

def test_l21_facades_do_not_import_adapters():
    """L2.1 Facades must not import L3 Adapters."""
    violations = scan_imports("hoc/api/facades/", forbidden=["adapters"])
    assert violations == [], f"L2.1 Facade violations: {violations}"

def test_l5_engines_do_not_import_orm():
    """L5 Engines must not import ORM models directly."""
    violations = scan_imports("hoc/**/L5_engines/", forbidden=["app/models"])
    assert violations == [], f"L5 ORM leakage: {violations}"
```

### 10.6 File Header Requirement

Every file must include:

```python
# Layer: L{X} — {Layer Name}
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {Single-line description}
# Callers: {Who calls this}
# Reference: HOC_LAYER_TOPOLOGY_V1.md
```

**Layer-Specific Header Extensions:**

For **Adapters (L3):**
```python
# ADAPTER CONTRACT:
# - Translation + aggregation only
# - No state mutation
# - No retries
# - No policy decisions
```

For **Workers (L5):**
```python
# Idempotent: YES | NO (if NO, explain why)
# WORKER CONTRACT:
# - Restart-safe
# - No incident creation
# - No retry management
```

For **Drivers (L6):**
```python
# DRIVER CONTRACT:
# - Returns domain objects, not ORM models
# - Owns query logic
# - Owns data shape transformation
```

---

## 11. Migration Notes

### 11.1 What Moves

| From | To |
|------|-----|
| `app/api/*.py` | `hoc/api/{audience}/*.py` |
| `app/adapters/*.py` | `hoc/{audience}/{domain}/adapters/` |
| `app/services/*.py` (facades) | `hoc/{audience}/{domain}/engines/` |
| `app/models/*.py` (audience-specific) | `app/{audience}/models/` |

### 11.2 What Stays

| Location | Reason |
|----------|--------|
| `app/models/*.py` (shared) | Cross-audience tables |
| `app/worker/*.py` | Infrastructure workers (runner, lifecycle) |

### 11.3 What's New

| Location | Purpose |
|----------|---------|
| `hoc/api/facades/` | L2.1 organizers |
| `hoc/{audience}/general/L4_runtime/` | L4 governed runtime |
| `hoc/{audience}/frontend/` | Panel engine |
| `hoc/{audience}/{domain}/workers/` | L5 domain workers |

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-23 | Initial ratified version |
| 1.1.0 | 2026-01-23 | L4 Runtime restructured to parts-based control plane architecture |
| 1.2.0 | 2026-01-23 | Added layer contracts (L2.1, L3, L5, L6, Panel). Expanded CI enforcement (BLCA rules, quarantine registry, layer assertion tests). |

---

## 13. References

- PIN-464: HOC Customer Domain Comprehensive Audit
- LAYER_MODEL.md: Previous layer definitions (partially superseded)
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md: Domain definitions

---

**Document Status:** RATIFIED
**Next Review:** When migration begins
