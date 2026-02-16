# HOC Layer Topology V2.0.0 — DRAFT

**Status:** RATIFIED
**Created:** 2026-01-28
**Ratified:** 2026-01-28
**Supersedes:** HOC_LAYER_TOPOLOGY_V1.4.0, HOC_SPINE_TOPOLOGY_PROPOSAL V1.5.0

---

## Executive Summary

This specification defines a **6-layer execution-centric architecture** optimized for:
- Traceability
- Single ownership
- Debuggability
- Simplicity

**Key Change:** L3 (Adapter) is removed as a first-class layer. Its responsibilities are absorbed by L2 (translation) and L4 (orchestration).

---

## Design Principles

### What We Optimize For

| Priority | Principle |
|----------|-----------|
| 1 | **Traceability** — Every execution path is linear and observable |
| 2 | **Single Ownership** — One owner per concern, no shared responsibility |
| 3 | **Debuggability** — "Question one place, find the problem" |
| 4 | **Simplicity** — Minimum layers with maximum semantic clarity |

### What We Reject

| Anti-Pattern | Why |
|--------------|-----|
| Distributed coordination | Creates "distributed blame" |
| Multiple cross-domain owners | Splits tracing, complicates debugging |
| Layers without unique responsibility | Adds indirection without value |
| Request-centric adapters | This is an execution-centric system |

---

## Two Constitutions Model

```
HOC
├── hoc_spine/                    SYSTEM CONSTITUTION
│   The execution authority.
│   Defines: what, when, how the system itself executes.
│   Owns: orchestration, lifecycle, cross-domain coordination.
│   NOT a domain. Infrastructure that domains run on.
│
└── cus/{domain}/                 CUSTOMER CONSTITUTION(S)
    The domain logic.
    Defines: what, when, how for customer-facing functions.
    Owns: business logic, domain-specific DB operations.
    Each domain is vertically isolated.
```

---

## Layer Topology (6 Layers)

### Authoritative Execution Path

```
L2.1 Facade
    ↓
L2 API (thin)
    ↓
L4 hoc_spine / Orchestrator   ← SINGLE OWNER
    ↓
L5 Domain Engine(s)
    ↓
L6 Driver(s)
    ↓
L7 Models
```

### Audience Surfaces (CUS / INT / FDR)

HOC has **multiple audience surfaces** at L2.1/L2:
- `cus/` (customer console)
- `int/` (internal operators / system runtime operators)
- `fdr/` (founder ops)

These audiences are **separate L2.1/L2 surfaces** that may expose different operations and contracts.
They all dispatch into the **same** L4 execution authority (hoc_spine).

**Invariant:** hoc_spine is the system runtime and execution authority; it is not an audience surface.
Audience runtimes must be wired intentionally via L2.1 facades and explicit handler registration.

### Layer Definitions

---

### L2.1 — FACADE (Organizer)

**Location:** `hoc/api/facades/{audience}/{domain}.py` (default) or
`hoc/api/facades/{audience}/{domain}/{domain}_fac.py` (domain-scoped package form).
Current canonical package-form examples: `hoc/api/facades/cus/account/account_fac.py`,
`hoc/api/facades/cus/policies/policies_fac.py`.
`{audience}` ∈ `{cus,int,fdr}`

**Topology Note (2026-02-16 / PIN-575):**
All canonical CUS L2.1 facades are now standardized to package-form:
`hoc/api/facades/cus/<domain>/<domain>_fac.py`.
Use package-form as the constitutional default for new CUS facade activation.

**Responsibility:** Groups L2 routers by audience and domain. Conceals API structure from outside world.

**Contract:**
- Imports L2 routers ONLY
- No business logic, no validation, no DB
- MUST NOT import L4, L5, L6, L7
- One facade per domain

**Example:**
```python
# hoc/api/facades/cus/policies/policies_fac.py
from hoc.api.cus.policies import limits, rules, proposals, enforcement

routers = [
    limits.router,
    rules.router,
    proposals.router,
    enforcement.router,
]
```

---

### L2 — API (HTTP Boundary)

**Location:** `hoc/api/{audience}/{domain}/*.py` where `{audience}` ∈ `{cus,int,fdr}`

**Responsibility:** HTTP request/response handling. Thin. Translates HTTP to domain operation.

**Contract:**
- Input validation (FastAPI + Pydantic)
- Auth/tenant extraction
- Response formatting
- Translates request to operation name + parameters
- Calls L4 orchestrator, NEVER calls L5 directly
- MUST NOT contain business logic
- MUST NOT do cross-domain coordination

**What L2 Does (Translation):**
```python
# hoc/api/cus/policies/rules.py
from hoc.cus.hoc_spine.orchestrator import execute

@router.post("/rules")
async def create_rule(
    request: Request,
    body: CreateRuleRequest,
    session: AsyncSession = Depends(get_session),
):
    # L2 responsibility: extract, validate, translate
    tenant_id = get_tenant_id(request)

    # Call L4 orchestrator — NOT L5 directly
    result = await execute(
        operation="policies.create_rule",
        tenant_id=tenant_id,
        params=body.model_dump(),
        session=session,
    )

    return CreateRuleResponse(**result)
```

---

### L4 — HOC_SPINE / ORCHESTRATOR (Single Execution Authority)

**Location:** `hoc/cus/hoc_spine/`

**Responsibility:** The SINGLE OWNER of all execution. Coordinates domains, handles cross-domain logic, owns lifecycle.

**Contract:**
- ALL execution enters L4 exactly once
- Owns cross-domain coordination (no other layer does this)
- Owns execution authority (can this run? should it run?)
- Owns transaction boundaries (commit authority)
- Owns retry/failure semantics
- Owns lifecycle (start, execute, complete, fail)
- MUST NOT contain domain-specific business logic
- MUST NOT contain L5 engines (binding constraint)

**Structure:**
```
hoc/cus/hoc_spine/                          (79 files)
├── orchestrator/                       ← Entry point for ALL execution
│   ├── __init__.py                     ← Central re-export hub
│   ├── governance_orchestrator.py      ← Main orchestration
│   ├── run_governance_facade.py        ← Run governance entry
│   ├── plan_generation_engine.py       ← Plan generation
│   ├── execution/                      ← Execution infrastructure
│   │   └── job_executor.py
│   └── lifecycle/                      ← Lifecycle management
│       ├── engines/ (onboarding, offboarding)
│       ├── drivers/ (execution driver)
│       └── pool_manager.py
├── authority/                          ← Governance & runtime decisions
│   ├── profile_policy_mode.py          ← Governance configuration
│   ├── runtime_switch.py              ← Runtime kill switch (GAP-069)
│   ├── degraded_mode_checker.py       ← Degraded mode detection
│   ├── concurrent_runs.py             ← Concurrency controls
│   ├── runtime.py                     ← Runtime configuration
│   ├── guard_write_engine.py          ← Guard write operations
│   └── contracts/
│       └── contract_engine.py         ← Contract evaluation
├── consequences/                       ← Post-execution reactions (stub)
├── services/                           ← Shared infrastructure services
│   ├── audit_store.py, audit_durability.py
│   ├── time.py, db_helpers.py, metrics_helpers.py
│   ├── facades (retrieval, lifecycle, scheduler, monitors, alerts, compliance)
│   ├── utilities (canonical_json, deterministic, dag_sorter, etc.)
│   └── domain-agnostic services (fatigue_controller, rate_limiter, etc.)
├── schemas/                            ← Shared types
│   ├── rac_models.py, common.py, response.py
│   ├── agent.py, artifact.py, plan.py, skill.py, retry.py
│   └── __init__.py
├── drivers/                            ← Cross-domain + infrastructure DB
│   ├── transaction_coordinator.py
│   ├── cross_domain.py
│   ├── guard_write_driver.py, guard_cache.py
│   ├── alert_driver.py, worker_write_service_async.py
│   ├── ledger.py, idempotency.py
│   ├── schema_parity.py, governance_signal_driver.py
│   └── dag_executor.py
├── frontend/projections/               ← UI projections
│   └── rollout_projection.py
└── mcp/                                ← MCP server registry
    ├── __init__.py
    └── mcp_server_registry.py
```

**L4 → L5 Binding Mechanism (AUTHORITATIVE):**

L4 resolves operations via a **static operation registry** defined in `hoc/cus/hoc_spine/orchestrator/registry.py`. Each operation is a declared entry mapping `operation_name → (domain, engine_class, method, context_schema)`. The registry is populated at application startup and is immutable at runtime. Dynamic dispatch and string-based if/else chains are FORBIDDEN. All operations must be explicitly registered; unregistered operations fail immediately.

```python
# hoc/cus/hoc_spine/orchestrator/registry.py

OPERATION_REGISTRY: dict[str, OperationBinding] = {
    "policies.create_rule": OperationBinding(
        domain="policies",
        engine=RuleEngine,
        method="create",
        context_schema=CreateRuleContext,
        cross_domain_deps=[],  # No cross-domain data needed
    ),
    "overview.get_highlights": OperationBinding(
        domain="overview",
        engine=OverviewEngine,
        method="get_highlights",
        context_schema=OverviewContext,
        cross_domain_deps=["incidents.active", "policies.pending", "activity.recent"],
    ),
}
```

```python
# hoc/cus/hoc_spine/orchestrator/executor.py

async def execute(operation: str, tenant_id: str, params: dict, session: AsyncSession):
    binding = OPERATION_REGISTRY.get(operation)
    if not binding:
        raise UnknownOperationError(operation)

    # Fetch cross-domain data if declared
    cross_domain_data = await fetch_cross_domain(binding.cross_domain_deps, tenant_id, session)

    # Build typed context
    context = binding.context_schema(
        tenant_id=tenant_id,
        params=params,
        cross_domain=cross_domain_data,
    )

    # Instantiate engine with driver, call method
    driver = get_driver(binding.domain, session)
    engine = binding.engine(driver)
    return await getattr(engine, binding.method)(context)
```

---

### L5 — DOMAIN ENGINE (Business Logic)

**Location:** `hoc/cus/{domain}/L5_engines/`

**Responsibility:** Domain-specific decisions, pattern detection, computation. Pure business logic.

**Contract:**
- Receives complete context from L4 (never fetches cross-domain data itself)
- Calls L6 drivers for DB operations
- MUST NOT import sqlmodel, sqlalchemy, Session
- MUST NOT import app.models directly
- MUST NOT call other domain's L5 engines
- MUST NOT reach up to L2 or L4
- Returns domain result to L4

**Context Boundary (AUTHORITATIVE):**

Context passed to L5 MUST be:
- **Typed** — Each operation has a declared `context_schema` (Pydantic model or dataclass). No opaque `dict`.
- **Immutable** — L5 receives a frozen snapshot. L5 MUST NOT mutate context.
- **Versioned** — Context schemas are versioned. Breaking changes require schema version bump.
- **Bounded** — Context contains only what the operation declares in `cross_domain_deps`. No unbounded growth.
- **Rejectable** — L5 MAY raise `InvalidContextError` if context is malformed or incomplete.

```python
# hoc/cus/policies/L5_schemas/contexts.py

@dataclass(frozen=True)  # Immutable
class CreateRuleContext:
    """Context schema for policies.create_rule operation. Version 1."""
    tenant_id: str
    params: CreateRuleParams
    cross_domain: CrossDomainData  # Empty if no deps declared

@dataclass(frozen=True)
class CrossDomainData:
    """Cross-domain data fetched by L4. Only populated fields declared in registry."""
    incidents_active: list[IncidentSummary] | None = None
    policies_pending: list[PolicySummary] | None = None
    activity_recent: list[RunSummary] | None = None
```

**Example:**
```python
# hoc/cus/policies/L5_engines/rule_evaluator.py

class RuleEvaluator:
    """
    Pure domain logic.
    Receives context, returns decision.
    No DB imports, no cross-domain calls.
    """

    def __init__(self, driver: PolicyDriver):
        self._driver = driver

    async def evaluate(
        self,
        tenant_id: str,
        rule_id: str,
        context: dict,  # Provided by L4, includes any cross-domain data
    ) -> EvaluationResult:
        rule = await self._driver.get_rule(tenant_id, rule_id)

        # Pure business logic
        if rule.condition_matches(context):
            return EvaluationResult(triggered=True, actions=rule.actions)

        return EvaluationResult(triggered=False)
```

---

### L6 — DRIVER (DB Operations)

**Location:** `hoc/cus/{domain}/L6_drivers/`

**Responsibility:** Query building, data transformation, DB read/write for a single domain.

**Contract:**
- Imports L7 models
- Returns domain objects (dataclass, dict, Pydantic), NOT ORM models
- Owns query logic — engines never write SQL
- MUST NOT contain business logic
- MUST NOT call other domain's drivers
- MUST NOT do cross-domain queries (that's L4's job via hoc_spine/drivers/)

**Example:**
```python
# hoc/cus/policies/L6_drivers/policy_driver.py

class PolicyDriver:
    """
    DB operations for policies domain only.
    Returns domain objects, not ORM models.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_rule(self, tenant_id: str, rule_id: str) -> RuleData:
        stmt = select(PolicyRule).where(
            PolicyRule.tenant_id == tenant_id,
            PolicyRule.id == rule_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()

        if not row:
            return None

        # Return domain object, NOT ORM model
        return RuleData(
            id=row.id,
            name=row.name,
            condition=row.condition,
            actions=row.actions,
        )
```

---

### L7 — MODELS (ORM Tables)

**Location:** `app/models/` (shared) or `hoc/cus/{domain}/L7_models/` (domain-specific, future)

**Responsibility:** SQLModel/SQLAlchemy table definitions. Leaf node.

**Contract:**
- Pure data definition
- No business logic
- No query logic
- Imported by L6 drivers only

**Status:** L7 model classification and domain-specific model design are DEFERRED to a separate plan.

---

## Import Rules (Simplified)

### Authoritative Import Flow

```
L2.1 → L2 → L4 → L5 → L6 → L7
              ↓
         (L4 calls multiple L5s for cross-domain)
```

### Import Rule Table

| Rule | From | To | Legal? | Notes |
|------|------|----|--------|-------|
| **API-001** | L2.1 | L2 | ✅ YES | Facade groups routers |
| **API-002** | L2 | L4 | ✅ YES | API calls orchestrator |
| **API-003** | L2 | L5/L6/L7 | ❌ FORBIDDEN | Must go through L4 |
| **SPINE-001** | L4 | Any L5 | ✅ YES | Orchestrator calls engines |
| **SPINE-002** | L4 | hoc_spine/services | ✅ YES | Shared infrastructure (see SERVICE-CONSTRAINT) |
| **SPINE-003** | L5 | hoc_spine/services | ✅ YES | Engines use shared services (see SERVICE-CONSTRAINT) |
| **DOMAIN-001** | L5 | L6 (same domain) | ✅ YES | Engine calls its driver |
| **DOMAIN-002** | L5 | L5 (other domain) | ❌ FORBIDDEN | Cross-domain via L4 only |
| **DOMAIN-003** | L5 | L6 (other domain) | ❌ FORBIDDEN | Cross-domain via L4 only |
| **DOMAIN-004** | L6 | L7 | ✅ YES | Driver uses models |
| **UP-001** | L5/L6 | L2/L4 | ❌ FORBIDDEN | Never reach up |

### Cross-Domain Rule (Critical)

**Only L4 (hoc_spine) may coordinate across domains.**

- L5 never calls another domain's L5
- L5 never calls another domain's L6
- L2 never coordinates multiple domains
- If cross-domain data is needed, L4 fetches it and passes to L5

### SERVICE-CONSTRAINT: hoc_spine/services Rules (Critical)

**hoc_spine/services MUST be:**
- **Stateless** — No instance state, no caching, no side-channel data
- **Idempotent** — Same input always produces same output
- **Domain-agnostic** — No domain-specific business logic. Services operate on generic concepts (audit, lifecycle, contracts), never on domain entities (policies, incidents, runs)
- **Infrastructure-only** — Services provide mechanical capabilities (write audit log, check contract, manage lifecycle), never business decisions

**FORBIDDEN in hoc_spine/services:**
- Domain-specific conditionals (`if domain == "policies"`)
- Business rule evaluation
- Domain entity manipulation
- Feature flags that change behavior per domain

**Rationale:** This constraint prevents hoc_spine/services from becoming a "new general" — a dumping ground for misclassified business logic. If a service needs domain knowledge, it belongs in that domain's L5, not in spine.

---

## Directory Structure (Physical)

```
backend/app/hoc/
├── hoc_spine/                        ← SYSTEM CONSTITUTION (L4) — 79 files
│   ├── orchestrator/                 ← Entry point for ALL execution
│   │   ├── execution/               ← Job execution infrastructure
│   │   └── lifecycle/               ← Lifecycle management (onboarding, offboarding)
│   ├── authority/                    ← Governance & runtime decisions
│   │   └── contracts/               ← Contract evaluation
│   ├── consequences/                 ← Post-execution reactions (stub)
│   ├── services/                     ← Shared infrastructure (24 files)
│   ├── schemas/                      ← Shared types (9 files)
│   ├── drivers/                      ← Cross-domain + infra DB (13 files)
│   ├── frontend/projections/         ← UI projections
│   └── mcp/                          ← MCP server registry
│
├── api/                              ← L2 HTTP LAYER
│   ├── facades/cus/                  ← L2.1 Facades
│   │   ├── overview/overview_fac.py
│   │   ├── activity/activity_fac.py
│   │   ├── incidents/incidents_fac.py
│   │   ├── policies/policies_fac.py
│   │   ├── controls/controls_fac.py
│   │   ├── logs/logs_fac.py
│   │   ├── analytics/analytics_fac.py
│   │   ├── integrations/integrations_fac.py
│   │   ├── api_keys/api_keys_fac.py
│   │   └── ...
│   └── cus/{domain}/                 ← L2 Route handlers
│
└── cus/                              ← CUSTOMER DOMAINS
    ├── overview/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── activity/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── incidents/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── policies/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── controls/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── logs/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── analytics/
    │   ├── L5_engines/
    │   └── L6_drivers/
    ├── integrations/
    │   ├── L5_engines/               ← External SDK wrappers live here
    │   └── L6_drivers/
    ├── apis/
    │   ├── L5_engines/
    │   └── L6_drivers/
    └── account/
        ├── L5_engines/
        └── L6_drivers/
```

---

## Migration: What Happens to Existing Files

### L3 Files → Reclassification

| Current Location | Files | New Location | Rationale |
|------------------|-------|--------------|-----------|
| `{domain}/L3_adapters/` | Domain adapters | **DELETE** — logic absorbed by L2 (translation) or L4 (coordination) | No unique responsibility |
| `integrations/L3_adapters/` | 21 integration wrappers | `integrations/L5_engines/` | They're domain logic for integrations domain |
| Any cross-domain aggregation | Various | `hoc_spine/orchestrator/coordinator.py` | L4 owns cross-domain |

### General Domain → hoc_spine

| Current Location | Files | New Location | Rationale |
|------------------|-------|--------------|-----------|
| `general/L4_runtime/` | 6 files | `hoc_spine/orchestrator/`, `hoc_spine/authority/`, `hoc_spine/consequences/` | L4 lives in spine |
| `general/L5_engines/` (shared services) | ~16 files | `hoc_spine/services/` | Shared infrastructure |
| `general/L5_engines/` (domain logic) | ~20 files | Absorb into spine OR redistribute to specific domains | Decision per file |
| `general/L5_schemas/` | 3 files | `hoc_spine/schemas/` | Shared types |
| `general/L6_drivers/` | Cross-domain drivers | `hoc_spine/drivers/` | Cross-domain DB |

---

## Binding Constraints

| Constraint | Description |
|------------|-------------|
| **NO L3 LAYER** | L3 does not exist in this topology. No `L3_adapters/` directories. |
| **NO L5 IN HOC_SPINE** | hoc_spine may have orchestrator, services, schemas, drivers — but NO L5 engines |
| **SINGLE ORCHESTRATOR** | ALL execution enters L4 exactly once. No bypassing. |
| **L5 ISOLATION** | L5 engines never call other domains. Ever. |
| **LINEAR TRACE** | Every request follows: L2 → L4 → L5 → L6 |
| **STATIC REGISTRY** | L4 → L5 binding via static operation registry. No dynamic dispatch, no if/else chains. |
| **TYPED CONTEXT** | Context passed to L5 must be typed, immutable, versioned, and bounded per operation. |
| **STATELESS SERVICES** | hoc_spine/services must be stateless, idempotent, and domain-agnostic. No business logic. |

---

## What This Topology Provides

| Benefit | How |
|---------|-----|
| **One place to debug cross-domain** | L4 coordinator |
| **Linear execution trace** | L2 → L4 → L5 → L6 |
| **Single ownership** | L4 owns orchestration, L5 owns domain logic, L6 owns DB |
| **Simpler mental model** | 6 layers instead of 7 |
| **No ambiguous layers** | Every layer has unique responsibility |
| **Easy to enforce** | Clear rules, no edge cases |

---

## Comparison: V1.4.0 vs V2.0.0

| Aspect | V1.4.0 | V2.0.0 |
|--------|--------|--------|
| Layer count | 7 (L2.1, L2, L3, L4, L5, L6, L7) | 6 (L2.1, L2, L4, L5, L6, L7) |
| Cross-domain owner | Split: L3 (aggregation) + L4 (orchestration) | Single: L4 only |
| `general` domain | Exists (confused: domain + infrastructure) | Abolished → `hoc_spine` |
| L3 adapters | Required per domain | Do not exist |
| Trace complexity | L2 → L3 → L4 → L5 → L6 | L2 → L4 → L5 → L6 |
| Debugging | Two places for cross-domain | One place (L4) |

---

## Ratification Checklist

All items confirmed on 2026-01-28:

- [x] L3 removal is acceptable (no unique L3 responsibility identified)
- [x] L4/hoc_spine as single orchestrator is acceptable
- [x] `general` domain abolishment is acceptable
- [x] Migration plan for existing L3 files is acceptable
- [x] 6-layer topology is acceptable

---

## References

- HOC_LAYER_TOPOLOGY_V1.4.0 (superseded)
- HOC_SPINE_TOPOLOGY_PROPOSAL V1.5.0 (superseded)
- HOC_SPINE_TOPOLOGY_REVIEW.md (binding decisions)
- PIN-470: HOC Layer Inventory
- PIN-483: HOC Domain Migration Complete

---

**END OF SPECIFICATION**

*Ratified 2026-01-28. This document is now BINDING.*
