# PIN-340: GC_L Implementation Specification (Policy Library, APIs, FACILITATION)

**Status:** READY FOR IMPLEMENTATION
**Date:** 2026-01-07
**Category:** Governance / Implementation Specification
**Reference:** PIN-339 (Customer Console Capability Reclassification)
**Authority:** Human-specified, governance-tight

---

## Executive Summary

This PIN provides **implementation-ready specifications** for the three core components of GC_L:

1. **Policy Library** — Schema, lifecycle, and storage
2. **GC_L API Contract** — Customer write paths with explicit constraints
3. **FACILITATION Rules Engine** — Intelligence layer with executable exports

**Core Principle:** Learning produces drafts, not authority. Activation is explicit, human-attributed.

---

## 1. Policy Library — Schema & Lifecycle

### 1.1 Core Principles (Non-Negotiable)

| Principle | Enforcement |
|-----------|-------------|
| Policies are **artifacts**, not suggestions | Schema enforced |
| Policies **do not execute themselves** | No auto-triggers |
| Learning produces **drafts**, not authority | `origin=LEARNED` → `status=DRAFT` only |
| Activation is **explicit, human-attributed** | `performed_by` required |
| Every state transition is **auditable and reversible** | `policy_activation_log` |

---

### 1.2 Database Schema (Postgres)

#### `policy_library`

```sql
CREATE TABLE policy_library (
  policy_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL,
  project_id          UUID NULL, -- NULL = org-scoped
  name                TEXT NOT NULL,
  description         TEXT,
  policy_type         TEXT NOT NULL, -- RULE | LIMIT | SAFETY | COST | ACCESS
  origin              TEXT NOT NULL, -- HUMAN | LEARNED | IMPORTED
  status              TEXT NOT NULL, -- DRAFT | SIMULATED | ACTIVE | DISABLED | DEPRECATED
  version             INTEGER NOT NULL DEFAULT 1,
  parent_policy_id    UUID NULL REFERENCES policy_library(policy_id),
  policy_definition   JSONB NOT NULL,
  created_by          UUID NOT NULL,
  created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT valid_policy_type CHECK (policy_type IN ('RULE', 'LIMIT', 'SAFETY', 'COST', 'ACCESS')),
  CONSTRAINT valid_origin CHECK (origin IN ('HUMAN', 'LEARNED', 'IMPORTED')),
  CONSTRAINT valid_status CHECK (status IN ('DRAFT', 'SIMULATED', 'ACTIVE', 'DISABLED', 'DEPRECATED'))
);

CREATE INDEX idx_policy_library_tenant ON policy_library(tenant_id);
CREATE INDEX idx_policy_library_project ON policy_library(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_policy_library_status ON policy_library(status);
CREATE INDEX idx_policy_library_type ON policy_library(policy_type);
```

#### `policy_simulation_results`

```sql
CREATE TABLE policy_simulation_results (
  simulation_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id           UUID NOT NULL REFERENCES policy_library(policy_id),
  tenant_id           UUID NOT NULL,
  simulated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  lookback_window     INTERVAL NOT NULL,
  affected_runs       INTEGER NOT NULL,
  would_block         INTEGER NOT NULL,
  would_warn          INTEGER NOT NULL,
  cost_impact_est     NUMERIC,
  risk_summary        JSONB NOT NULL,
  evidence_refs       JSONB NOT NULL
);

CREATE INDEX idx_policy_sim_policy ON policy_simulation_results(policy_id);
CREATE INDEX idx_policy_sim_tenant ON policy_simulation_results(tenant_id);
```

#### `policy_activation_log`

```sql
CREATE TABLE policy_activation_log (
  event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_id           UUID NOT NULL REFERENCES policy_library(policy_id),
  action              TEXT NOT NULL, -- ACTIVATE | DISABLE | DEPRECATE
  performed_by        UUID NOT NULL,
  performed_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  justification       TEXT,

  CONSTRAINT valid_action CHECK (action IN ('ACTIVATE', 'DISABLE', 'DEPRECATE'))
);

CREATE INDEX idx_policy_activation_policy ON policy_activation_log(policy_id);
CREATE INDEX idx_policy_activation_actor ON policy_activation_log(performed_by);
```

---

### 1.3 Policy Lifecycle (STRICT)

```
LEARNED / HUMAN / IMPORTED
        ↓
      DRAFT
        ↓
   (SIMULATE)
        ↓
     SIMULATED
        ↓
 (HUMAN ACTIVATE)
        ↓
      ACTIVE
        ↓
 DISABLED / DEPRECATED
```

#### State Transition Matrix

| From | To | Allowed | Actor Required | Conditions |
|------|-----|---------|----------------|------------|
| (new) | DRAFT | ✅ | YES | Any origin |
| DRAFT | SIMULATED | ✅ | YES | Simulation completed |
| SIMULATED | ACTIVE | ✅ | YES (Admin) | Human confirmation |
| ACTIVE | DISABLED | ✅ | YES | Manual pause |
| ACTIVE | DEPRECATED | ✅ | YES | Replaced by new version |
| DISABLED | ACTIVE | ✅ | YES | Re-enable |
| DRAFT | ACTIVE | ❌ | - | **FORBIDDEN** |
| LEARNED | ACTIVE | ❌ | - | **FORBIDDEN** |
| * | MODIFIED | ❌ | - | Must create new version |

---

### 1.4 Policy DSL (Minimal Grammar)

```json
{
  "when": {
    "metric": "string",          // cost_per_hour | error_rate | latency_p99 | ...
    "operator": "string",        // > | < | >= | <= | == | !=
    "value": "number | string",
    "window": "string"           // optional: 5m | 1h | 24h
  },
  "then": {
    "action": "string",          // WARN | BLOCK | REQUIRE_APPROVAL
    "message": "string",
    "metadata": {}               // optional context
  }
}
```

**Allowed Actions:**
- `WARN` — Advisory only, no enforcement
- `BLOCK` — Prevents execution
- `REQUIRE_APPROVAL` — Queues for human decision

**Forbidden Actions:**
- `EXECUTE` ❌
- `MUTATE` ❌
- `AUTO_APPLY` ❌

---

## 2. GC_L API Contract — Write Paths (Customer)

### 2.1 General GC_L API Rules

Every GC_L write request **MUST** include:

```json
{
  "actor_id": "uuid",
  "intent": "CONFIGURE | ACTIVATE | PAUSE | DISABLE",
  "confirmation": true,
  "reason": "string"
}
```

| Missing Field | Response |
|---------------|----------|
| `confirmation` | 400 Bad Request |
| `actor_id` | 401 Unauthorized |
| `intent` | 422 Unprocessable Entity |

---

### 2.2 Policy Library APIs

#### Create Policy (Draft)

```
POST /api/cus/policies
```

**Request:**
```json
{
  "name": "Cost Guardrail",
  "policy_type": "COST",
  "origin": "HUMAN",
  "definition": {
    "when": { "metric": "cost_per_hour", "operator": ">", "value": 200 },
    "then": { "action": "WARN", "message": "Hourly cost exceeded threshold" }
  },
  "intent": "CONFIGURE",
  "confirmation": true
}
```

**Response:** `201 Created`
```json
{
  "policy_id": "uuid",
  "status": "DRAFT",
  "version": 1
}
```

---

#### Simulate Policy

```
POST /api/cus/policies/{policy_id}/simulate
```

**Request:**
```json
{
  "lookback_days": 30,
  "intent": "SIMULATE",
  "confirmation": true
}
```

**Response:** `200 OK`
```json
{
  "simulation_id": "uuid",
  "affected_runs": 1247,
  "would_block": 23,
  "would_warn": 89,
  "cost_impact_est": -450.00,
  "risk_summary": { ... }
}
```

**Side Effect:** Creates `policy_simulation_results` record, transitions policy to `SIMULATED`

---

#### Activate Policy

```
POST /api/cus/policies/{policy_id}/activate
```

**Request:**
```json
{
  "intent": "ACTIVATE",
  "confirmation": true,
  "reason": "Reviewed simulation impact"
}
```

**Hard Checks (all must pass):**
- Policy must be `SIMULATED` status
- Actor must be tenant admin
- Version increment enforced if modifying existing

**Response:** `200 OK`
```json
{
  "policy_id": "uuid",
  "status": "ACTIVE",
  "activated_at": "ISO8601",
  "activated_by": "uuid"
}
```

---

#### Disable Policy

```
POST /api/cus/policies/{policy_id}/disable
```

**Request:**
```json
{
  "intent": "DISABLE",
  "confirmation": true,
  "reason": "Temporary pause for review"
}
```

---

### 2.3 Killswitch API (Customer)

#### Engage Killswitch

```
POST /api/cus/killswitch
```

**Request:**
```json
{
  "scope": "PROJECT | AGENT | CLASS",
  "target_id": "uuid",
  "intent": "PAUSE",
  "confirmation": true,
  "reason": "Unexpected failures"
}
```

**Behavior:**
- Immediate effect
- Manual resume only (no auto-resume)
- Broadcast state change to all listeners

**Response:** `200 OK`
```json
{
  "killswitch_id": "uuid",
  "scope": "PROJECT",
  "target_id": "uuid",
  "engaged_at": "ISO8601",
  "status": "ENGAGED"
}
```

---

#### Release Killswitch

```
POST /api/cus/killswitch/{killswitch_id}/release
```

**Request:**
```json
{
  "intent": "RESUME",
  "confirmation": true,
  "reason": "Issue resolved"
}
```

---

### 2.4 Spend Controls API

#### Update Spend Guard

```
POST /api/cus/spend/guardrails
```

**Request:**
```json
{
  "limit": 10000,
  "period": "MONTHLY",
  "action": "WARN",
  "intent": "CONFIGURE",
  "confirmation": true
}
```

**Valid Periods:** `HOURLY | DAILY | WEEKLY | MONTHLY`
**Valid Actions:** `WARN | BLOCK | REQUIRE_APPROVAL`

---

## 3. FACILITATION Rules Engine

### 3.1 FACILITATION Engine Responsibilities

#### Allowed

| Capability | Description |
|------------|-------------|
| Evaluate signals | Analyze metrics, patterns, anomalies |
| Rank risks | Score and prioritize issues |
| Generate recommendations | Produce advisory guidance |
| Prefill actions | Suggest parameters for human approval |
| Trigger UI nudges | Surface warnings in console |

#### Forbidden (ABSOLUTE)

| Capability | Reason |
|------------|--------|
| Execute actions | Violates human-only execution |
| Modify state | No write authority |
| Activate policies | Requires human confirmation |
| Call GC_L endpoints | Would bypass human gate |

---

### 3.2 FACILITATION Rule Schema

```json
{
  "rule_id": "uuid",
  "name": "string",
  "signal": "ERROR_RATE_SPIKE | COST_ANOMALY | LATENCY_DEGRADATION | ...",
  "condition": {
    "threshold": "number",
    "window": "duration",
    "comparator": "> | < | >= | <="
  },
  "recommendation": {
    "message": "string",
    "suggested_action": "ENGAGE_KILLSWITCH | REDUCE_CONCURRENCY | PAUSE_EXECUTION | ...",
    "confidence": "number (0.0-1.0)",
    "severity": "LOW | MEDIUM | HIGH | CRITICAL"
  },
  "metadata": {
    "created_at": "ISO8601",
    "source": "SYSTEM | LEARNED",
    "evidence_required": true
  }
}
```

---

### 3.3 FACILITATION Signal Catalog (Core)

| Signal ID | Name | Trigger Condition |
|-----------|------|-------------------|
| SIG-001 | ERROR_RATE_SPIKE | Error rate > threshold in window |
| SIG-002 | COST_ANOMALY | Cost deviates > 2σ from baseline |
| SIG-003 | LATENCY_DEGRADATION | P99 latency > SLA threshold |
| SIG-004 | BUDGET_APPROACHING | Spend > 80% of limit |
| SIG-005 | FAILURE_PATTERN | Repeated failures on same skill |
| SIG-006 | RATE_LIMIT_PRESSURE | Approaching rate limit ceiling |

---

### 3.4 Executable Exports (Customer Use)

FACILITATION rules can be **exported** for customer-controlled use.

#### Export Format Options

| Format | Use Case |
|--------|----------|
| YAML | Human-readable config |
| JSON | API integration |
| Rego (OPA) | Policy-as-code tooling |
| Python stub | Custom scripting |
| Bash guard | CI/CD integration |

---

#### Example: YAML Export

```yaml
rule: cost_spike_guard
signal: cost_per_hour
threshold: 200
window: 5m
recommendation:
  action: pause_execution
  message: "Cost spike detected"
  confidence: 0.82
```

---

#### Example: Python Guard Script

```python
# Exported from FACILITATION Engine
# Rule: cost_spike_guard
# WARNING: Advisory only - does not auto-enforce

def evaluate_cost_spike(cost_per_hour: float) -> dict:
    if cost_per_hour > 200:
        return {
            "triggered": True,
            "recommendation": "PAUSE_EXECUTION",
            "message": "Cost spike detected",
            "confidence": 0.82
        }
    return {"triggered": False}

# Usage: Call evaluate_cost_spike() in your monitoring
```

---

#### Example: Rego (OPA) Export

```rego
package aos.facilitation

cost_spike_alert {
  input.cost_per_hour > 200
}

recommendation["pause_execution"] {
  cost_spike_alert
}
```

---

#### Export API

```
GET /api/cus/facilitation/rules/export
```

**Query Parameters:**
- `format`: `yaml | json | rego | python | bash`
- `rule_ids`: `uuid,uuid,...` (optional, all if omitted)

**Response:** Exported content in requested format

---

### 3.5 Trust Boundary (Explicit)

| Layer | Can Decide | Can Act |
|-------|------------|---------|
| FACILITATION | ❌ | ❌ |
| Policy Library | ❌ | ❌ |
| GC_L APIs | ❌ | ❌ |
| **Human** | ✅ | ✅ |

**This table MUST NEVER change.**

---

## 4. Implementation Checklist

### Phase 1: Database

- [ ] Create `policy_library` table
- [ ] Create `policy_simulation_results` table
- [ ] Create `policy_activation_log` table
- [ ] Add migrations with version tracking
- [ ] Create Alembic migration file

### Phase 2: Policy Library Service

- [ ] Implement PolicyLibraryService
- [ ] Implement lifecycle state machine
- [ ] Implement simulation engine
- [ ] Add version management

### Phase 3: GC_L API Routes

- [ ] `POST /api/cus/policies`
- [ ] `POST /api/cus/policies/{id}/simulate`
- [ ] `POST /api/cus/policies/{id}/activate`
- [ ] `POST /api/cus/policies/{id}/disable`
- [ ] `POST /api/cus/killswitch`
- [ ] `POST /api/cus/killswitch/{id}/release`
- [ ] `POST /api/cus/spend/guardrails`

### Phase 4: FACILITATION Engine

- [ ] Implement FacilitationEngine
- [ ] Define signal catalog
- [ ] Implement rule evaluation
- [ ] Add recommendation generation
- [ ] Implement export formats

### Phase 5: Testing

- [ ] Unit tests for lifecycle transitions
- [ ] Integration tests for API routes
- [ ] Adversarial tests for forbidden transitions
- [ ] Export format validation tests

---

## 5. Governance Constraints

### Artifacts Created (This PIN)

- `PIN-340-gc-l-implementation-specification.md`

### Artifacts To Be Created (Implementation)

- `backend/app/models/policy_library.py`
- `backend/app/services/policy_library_service.py`
- `backend/app/services/facilitation_engine.py`
- `backend/app/api/cus/policies.py`
- `backend/app/api/cus/killswitch.py`
- `backend/app/api/cus/spend.py`
- `backend/alembic/versions/XXX_create_policy_library.py`
- `backend/tests/services/test_policy_library.py`
- `backend/tests/api/test_customer_policies.py`

### Layer Classification

| Component | Layer | Justification |
|-----------|-------|---------------|
| Policy models | L6 | Platform substrate |
| Policy service | L4 | Domain engine |
| FACILITATION engine | L4 | Domain engine (advisory) |
| API routes | L2 | Product APIs |
| Export handlers | L3 | Boundary adapters |

---

## References

- PIN-339: Customer Console Capability Reclassification (GC_L)
- PIN-337: Governance Enforcement Infrastructure
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md
- AUTHORITY_DECLARATIONS_V1.yaml

---

**Status:** READY FOR IMPLEMENTATION
**Next Steps (User Choice):**
1. Policy DSL formal grammar
2. FACILITATION signal catalog (full)
3. GC_L audit & replay format
4. UI irreversible-action contracts
