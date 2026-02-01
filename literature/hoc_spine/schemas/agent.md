# agent.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/agent.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            agent.py
Lives in:        schemas/
Role:            Schemas
Inbound:         API routes, engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Agent API request/response schemas (pure Pydantic DTOs)
Violations:      none
```

## Purpose

Agent API request/response schemas (pure Pydantic DTOs)

## Import Analysis

**External:**
- `pydantic`
- `retry`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `_utc_now() -> datetime`

Return timezone-aware UTC datetime.

## Classes

### `AgentStatus(str, Enum)`

Agent operational status.

### `PlannerType(str, Enum)`

Supported planner backends.

### `PlannerConfig(BaseModel)`

Configuration for the agent's planner.

Controls how goals are translated into execution plans.

### `RateLimitConfig(BaseModel)`

Rate limiting configuration for an agent.

### `BudgetConfig(BaseModel)`

Budget tracking configuration for an agent.

#### Methods

- `remaining_cents() -> Optional[int]` — Calculate remaining budget.
- `usage_percent() -> Optional[float]` — Calculate usage percentage.

### `AgentCapabilities(BaseModel)`

Defines what an agent can and cannot do.

Controls access to skills, external resources,
and establishes security boundaries.

#### Methods

- `can_use_skill(skill_name: str) -> bool` — Check if agent can use a specific skill.
- `can_access_domain(domain: str) -> bool` — Check if agent can access a domain.

### `AgentConfig(BaseModel)`

Complete configuration for an agent.

Combines capabilities, planner settings, rate limits,
and budget tracking.

## Domain Usage

**Callers:** API routes, engines

## Export Contract

```yaml
exports:
  functions:
    - name: _utc_now
      signature: "_utc_now() -> datetime"
      consumers: ["orchestrator"]
  classes:
    - name: AgentStatus
      methods: []
      consumers: ["orchestrator"]
    - name: PlannerType
      methods: []
      consumers: ["orchestrator"]
    - name: PlannerConfig
      methods: []
      consumers: ["orchestrator"]
    - name: RateLimitConfig
      methods: []
      consumers: ["orchestrator"]
    - name: BudgetConfig
      methods:
        - remaining_cents
        - usage_percent
      consumers: ["orchestrator"]
    - name: AgentCapabilities
      methods:
        - can_use_skill
        - can_access_domain
      consumers: ["orchestrator"]
    - name: AgentConfig
      methods: []
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic', 'retry']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

