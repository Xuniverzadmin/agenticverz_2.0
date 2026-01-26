# Policies Domain Architecture

**Status:** ACTIVE
**Created:** 2026-01-20
**Updated:** 2026-01-20
**Reference:** `CROSS_DOMAIN_DATA_ARCHITECTURE.md`, `POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md`

---

## 1. Overview

The Policies domain defines and manages governance rules, limits, constraints, and control levers that govern LLM execution behavior. It answers the fundamental question:

> **"How is behavior defined?"**

### 1.1 Domain Scope

| Subdomain | Topics | Purpose |
|-----------|--------|---------|
| **Governance** | Active Policies, Policy Library, Lessons | Rule definitions and templates |
| **Limits** | Controls, Violations | Resource constraints and breach records |

### 1.2 Key Responsibilities

1. **Policy Definition** — Create, update, version policy rules
2. **Scope Selection** — Determine WHO policies apply to
3. **Limit Enforcement** — Define WHAT limits exist (tokens, cost, burn rate)
4. **Conflict Resolution** — Arbitrate between multiple applicable policies
5. **Threshold Alerting** — Near-threshold warnings and breach enforcement
6. **Evidence Production** — Immutable records of policy decisions
7. **Override Management** — Emergency override with audit trail

---

## 2. Policy Control Lever Model

The Policy Control Lever is the complete governance primitive:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      POLICY CONTROL LEVER                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │   POLICY    │───►│    SCOPE    │───►│  MONITORS   │                  │
│  │   (what)    │    │   (who)     │    │  (observe)  │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                               │                         │
│                                               ▼                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │  EVIDENCE   │◄───│   ACTIONS   │◄───│   LIMITS    │                  │
│  │  (prove)    │    │  (enforce)  │    │ (constrain) │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Core Principle

> A policy is a versioned, scoped, runtime-bound control contract that deterministically governs execution behavior and produces immutable evidence.

### 2.2 Policy Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         POLICY LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CREATED ──► PENDING_REVIEW ──► APPROVED ──► ACTIVE ──► DEPRECATED     │
│                    │                │           │                       │
│                    ▼                │           ▼                       │
│               REJECTED              │      SUSPENDED                    │
│                                     │           │                       │
│                                     ▼           │                       │
│                              ACTIVE_WITH_OVERRIDE ◄──────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Models

### 3.1 Core Policy Models

#### PolicyRule (Primary)

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | UUID | Primary key |
| `tenant_id` | UUID | Tenant isolation |
| `name` | str | Human-readable name |
| `description` | str | Policy description |
| `rule_type` | str | token_limit, cost_limit, rate_limit, etc. |
| `condition` | JSON | Rule condition expression |
| `action` | str | Action on breach (pause, stop, kill) |
| `threshold` | float | Numeric threshold value |
| `status` | str | active, suspended, deprecated |
| `version` | int | Version number |
| `violation_count` | int | Total violations recorded |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

**Table:** `policy_rules`

#### PolicyLimit

| Field | Type | Description |
|-------|------|-------------|
| `limit_id` | UUID | Primary key |
| `tenant_id` | UUID | Tenant isolation |
| `policy_id` | UUID | FK to PolicyRule |
| `limit_type` | str | token, cost, burn_rate, step_count |
| `value` | float | Limit value |
| `scope` | str | per_run, per_day, per_month |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_limits`

#### PolicyProposal

| Field | Type | Description |
|-------|------|-------------|
| `proposal_id` | UUID | Primary key |
| `tenant_id` | UUID | Tenant isolation |
| `proposed_rule` | JSON | Proposed rule definition |
| `status` | str | pending, approved, rejected |
| `proposer_id` | UUID | FK to User |
| `reviewer_id` | UUID | FK to User (reviewer) |
| `review_comment` | str | Review notes |
| `created_at` | datetime | Creation timestamp |
| `reviewed_at` | datetime | Review timestamp |

**Table:** `policy_proposals`

### 3.2 Policy Control Lever Models

#### PolicyScope

| Field | Type | Description |
|-------|------|-------------|
| `scope_id` | UUID | Primary key |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `scope_type` | str | all_runs, agent, api_key, human_actor |
| `agent_ids_json` | str | JSON array of agent IDs (nullable) |
| `api_key_ids_json` | str | JSON array of API key IDs (nullable) |
| `human_actor_ids_json` | str | JSON array of human actor IDs (nullable) |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_scopes`

**Scope Types:**

| Type | Description | Example |
|------|-------------|---------|
| `ALL_RUNS` | All LLM runs for tenant | Default catch-all |
| `AGENT` | Specific agent IDs | ["agent-001", "agent-002"] |
| `API_KEY` | Specific API keys | ["key-abc", "key-xyz"] |
| `HUMAN_ACTOR` | Specific human actors | ["user-123"] |

#### PolicyPrecedence

| Field | Type | Description |
|-------|------|-------------|
| `precedence_id` | UUID | Primary key |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `precedence` | int | Lower = higher priority (default: 100) |
| `conflict_strategy` | str | most_restrictive, explicit_priority, fail_closed |
| `bind_at` | str | run_start, first_token, each_step |
| `failure_mode` | str | fail_closed, fail_open |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_precedence`

**Conflict Strategies:**

| Strategy | Behavior |
|----------|----------|
| `MOST_RESTRICTIVE` | Smallest limit, harshest action wins |
| `EXPLICIT_PRIORITY` | Higher precedence (lower number) wins |
| `FAIL_CLOSED` | If ambiguous, deny/stop |

**Binding Moments:**

| Binding | When Policy Becomes Authoritative |
|---------|-----------------------------------|
| `RUN_START` | When run is created |
| `FIRST_TOKEN` | When first LLM response received |
| `EACH_STEP` | Re-evaluated at every step |

#### MonitorConfig

| Field | Type | Description |
|-------|------|-------------|
| `config_id` | UUID | Primary key |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `monitor_token_usage` | bool | Monitor token consumption |
| `monitor_cost` | bool | Monitor cost accumulation |
| `monitor_burn_rate` | bool | Monitor tokens/second |
| `monitor_rag_access` | bool | Monitor RAG document access |
| `rag_access_patterns_json` | str | JSON array of allowed patterns |
| `allow_prompt_logging` | bool | Negative capability: prompt logging |
| `allow_pii_capture` | bool | Negative capability: PII capture |
| `allow_model_output_logging` | bool | Negative capability: output logging |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_monitor_configs`

**Negative Capabilities (Inspection Constraints):**

| Capability | Default | Description |
|------------|---------|-------------|
| `allow_prompt_logging` | false | Whether prompts can be logged |
| `allow_pii_capture` | false | Whether PII can be captured |
| `allow_model_output_logging` | true | Whether outputs can be logged |

#### ThresholdSignal

| Field | Type | Description |
|-------|------|-------------|
| `signal_id` | UUID | Primary key |
| `run_id` | UUID | FK to Run |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `signal_type` | str | near, breach |
| `metric` | str | token_usage, cost, burn_rate |
| `current_value` | float | Value at signal time |
| `threshold_value` | float | Threshold that triggered |
| `percentage` | float | Percentage of threshold |
| `step_index` | int | Step where signal occurred |
| `timestamp` | datetime | Signal timestamp |
| `action_taken` | str | Action taken (nullable, for breach) |
| `alert_sent` | bool | Whether alert was sent |
| `alert_channels_json` | str | Channels that received alert |
| `created_at` | datetime | Creation timestamp |

**Table:** `threshold_signals`

**Signal Types:**

| Type | Trigger | Action |
|------|---------|--------|
| `NEAR` | Metric >= configured % (default 80%) | Alert only |
| `BREACH` | Metric >= 100% of limit | Enforce action |

#### AlertConfig

| Field | Type | Description |
|-------|------|-------------|
| `config_id` | UUID | Primary key |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `near_threshold_enabled` | bool | Enable near-threshold alerts |
| `near_threshold_percentage` | int | Percentage trigger (default: 80) |
| `breach_alert_enabled` | bool | Enable breach alerts |
| `enabled_channels_json` | str | JSON array: ["ui", "webhook", "slack"] |
| `webhook_url` | str | Webhook URL (nullable) |
| `webhook_secret` | str | Webhook auth secret (nullable) |
| `slack_webhook_url` | str | Slack webhook URL (nullable) |
| `slack_channel` | str | Slack channel (nullable) |
| `email_recipients_json` | str | JSON array of emails (nullable) |
| `max_alerts_per_run` | int | Throttle limit per run |
| `min_alert_interval_seconds` | int | Minimum time between alerts |
| `last_alert_at` | datetime | Last alert timestamp |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_alert_configs`

**Alert Channels:**

| Channel | Purpose | Config Fields |
|---------|---------|---------------|
| `UI` | In-app notifications | - |
| `WEBHOOK` | External webhook | `webhook_url`, `webhook_secret` |
| `SLACK` | Slack integration | `slack_webhook_url`, `slack_channel` |
| `EMAIL` | Email notifications | `email_recipients_json` |

#### OverrideAuthority

| Field | Type | Description |
|-------|------|-------------|
| `authority_id` | UUID | Primary key |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `override_allowed` | bool | Whether override is permitted |
| `allowed_roles_json` | str | JSON array: ["OWNER", "SECURITY_ADMIN"] |
| `requires_reason` | bool | Mandate reason for override |
| `max_duration_seconds` | int | Maximum override duration |
| `requires_approval` | bool | Require second approver |
| `approver_roles_json` | str | JSON array of approver roles |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_override_authority`

#### OverrideRecord

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | UUID | Primary key |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `run_id` | UUID | FK to Run (nullable) |
| `override_type` | str | emergency, scheduled, approval |
| `reason` | str | Override justification |
| `requested_by` | str | User ID who requested |
| `approved_by` | str | User ID who approved (nullable) |
| `original_limits_json` | str | Limits before override |
| `override_limits_json` | str | Limits during override |
| `started_at` | datetime | Override start |
| `expires_at` | datetime | Override expiration |
| `revoked_at` | datetime | Early revocation (nullable) |
| `revoked_by` | str | User who revoked (nullable) |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_override_records`

### 3.3 Snapshot & Prevention Models

#### PolicySnapshot

| Field | Type | Description |
|-------|------|-------------|
| `snapshot_id` | UUID | Primary key |
| `tenant_id` | UUID | Tenant isolation |
| `policies_json` | str | JSON of applicable policies |
| `thresholds_json` | str | JSON of active thresholds |
| `content_hash` | str | SHA256 hash for integrity |
| `policy_count` | int | Number of policies captured |
| `arbitration_result_json` | str | Arbitration outcome |
| `created_at` | datetime | Creation timestamp |

**Table:** `policy_snapshots`

#### PreventionRecord

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | UUID | Primary key |
| `run_id` | UUID | FK to Run |
| `policy_id` | UUID | FK to PolicyRule |
| `tenant_id` | UUID | Tenant isolation |
| `action` | str | ALLOW, WARN, BLOCK |
| `step_index` | int | Step where evaluated |
| `evaluation_result_json` | str | Full evaluation result |
| `created_at` | datetime | Creation timestamp |

**Table:** `prevention_records`

---

## 4. API Routes

### 4.1 Policy CRUD

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/` | GET | List all policies |
| `/api/v1/policies/` | POST | Create new policy |
| `/api/v1/policies/{policy_id}` | GET | Get policy detail |
| `/api/v1/policies/{policy_id}` | PUT | Update policy |
| `/api/v1/policies/{policy_id}` | DELETE | Delete policy |
| `/api/v1/policies/validate` | POST | Validate policy rule |
| `/api/v1/policies/library` | GET | Get policy templates |

### 4.2 Policy Rules

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/rules/` | GET | List policy rules |
| `/api/v1/policies/rules/` | POST | Create rule |
| `/api/v1/policies/rules/{rule_id}` | GET | Get rule detail |
| `/api/v1/policies/rules/{rule_id}` | PUT | Update rule |
| `/api/v1/policies/rules/{rule_id}` | DELETE | Delete rule |

### 4.3 Policy Limits

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/limits/` | GET | List limits |
| `/api/v1/policies/limits/` | POST | Create limit |
| `/api/v1/policies/limits/{limit_id}` | GET | Get limit detail |
| `/api/v1/policies/limits/{limit_id}` | PUT | Update limit |
| `/api/v1/policies/limits/{limit_id}` | DELETE | Delete limit |
| `/api/v1/policies/controls` | GET | Get controls |
| `/api/v1/policies/controls` | PUT | Update controls |

### 4.4 Policy Proposals

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/proposals/` | GET | List proposals |
| `/api/v1/policies/proposals/` | POST | Create proposal |
| `/api/v1/policies/proposals/{proposal_id}` | GET | Get proposal detail |
| `/api/v1/policies/proposals/{proposal_id}` | PUT | Update proposal |
| `/api/v1/policies/proposals/{proposal_id}/approve` | POST | Approve proposal |
| `/api/v1/policies/proposals/{proposal_id}/reject` | POST | Reject proposal |

### 4.5 Policy Violations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/violations/` | GET | List violations |
| `/api/v1/policies/violations/stats` | GET | Violation statistics |
| `/api/v1/policies/violations/{violation_id}` | GET | Violation detail |

### 4.6 Policy Control Lever (New)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/{policy_id}/scope` | GET/PUT | Get/update scope selector |
| `/api/v1/policies/{policy_id}/precedence` | GET/PUT | Get/update precedence |
| `/api/v1/policies/{policy_id}/monitors` | GET/PUT | Get/update monitor config |
| `/api/v1/policies/{policy_id}/alerts` | GET/PUT | Get/update alert config |
| `/api/v1/policies/{policy_id}/override-authority` | GET/PUT | Get/update override rules |
| `/api/v1/policies/{policy_id}/override` | POST | Request override |
| `/api/v1/policies/{policy_id}/override/revoke` | POST | Revoke override |
| `/api/v1/policies/threshold-signals` | GET | List threshold signals |
| `/api/v1/policies/override-records` | GET | List override records |

---

## 5. Services & Engines

### 5.1 Layer Distribution

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/api/policy.py` | L2 | Policy API endpoints |
| `backend/app/api/policy_rules_crud.py` | L2 | Rules CRUD endpoints |
| `backend/app/api/policy_limits_crud.py` | L2 | Limits CRUD endpoints |
| `backend/app/api/policy_layer.py` | L2 | Policy layer operations |
| `backend/app/api/policy_proposals.py` | L2 | Proposal endpoints |
| `backend/app/policy/engine.py` | L4 | Policy evaluation engine |
| `backend/app/policy/compiler.py` | L4 | Policy rule compiler |
| `backend/app/policy/ir.py` | L4 | Intermediate representation |
| `backend/app/policy/optimizer.py` | L4 | Policy optimization |
| `backend/app/policy/runtime.py` | L4 | Runtime evaluation |
| `backend/app/policy/prevention_engine.py` | L4 | Prevention during runs |
| `backend/app/policy/scope_resolver.py` | L4 | Scope resolution |
| `backend/app/policy/arbitrator.py` | L4 | Policy arbitration |
| `backend/app/services/policy_violation_service.py` | L4 | Violation tracking |
| `backend/app/services/policy_proposal_engine.py` | L4 | Proposal workflow |
| `backend/app/services/alert_emitter.py` | L3 | Alert emission |

### 5.2 Core Services

#### PolicyEngine

**Location:** `backend/app/policy/engine.py`
**Layer:** L4
**Purpose:** Evaluate policy rules against execution context

```python
class PolicyEngine:
    def evaluate(self, context: EvaluationContext) -> EvaluationResult
    def get_applicable_rules(self, tenant_id: str) -> list[PolicyRule]
    def compile_rules(self, rules: list[PolicyRule]) -> CompiledPolicy
```

#### PreventionEngine

**Location:** `backend/app/policy/prevention_engine.py`
**Layer:** L4
**Purpose:** Real-time policy enforcement during execution

```python
class PreventionEngine:
    def evaluate_step(self, context: PreventionContext) -> PreventionResult
    def should_stop_run(self, result: PreventionResult) -> bool
    def create_violation_record(self, context: PreventionContext, result: PreventionResult) -> None
```

**PreventionResult Actions:**

| Action | Meaning | Behavior |
|--------|---------|----------|
| `ALLOW` | Step passes | Continue execution |
| `WARN` | Near threshold | Log warning, continue |
| `BLOCK` | Breach | Stop run, create incident |

#### ScopeResolver

**Location:** `backend/app/policy/scope_resolver.py`
**Layer:** L4
**Purpose:** Determine which policies apply to a run

```python
class ScopeResolver:
    def resolve_applicable_policies(self, context: RunContext) -> ScopeResolutionResult
    def matches_scope(self, scope: PolicyScope, context: RunContext) -> bool
```

**RunContext:**

```python
@dataclass
class RunContext:
    run_id: str
    tenant_id: str
    agent_id: str | None
    api_key_id: str | None
    human_actor_id: str | None
```

#### PolicyArbitrator

**Location:** `backend/app/policy/arbitrator.py`
**Layer:** L4
**Purpose:** Resolve conflicts when multiple policies apply

```python
class PolicyArbitrator:
    def arbitrate(self, policy_ids: list[str], tenant_id: str) -> ArbitrationResult
```

**ArbitrationResult:**

```python
@dataclass
class ArbitrationResult:
    policy_ids: list[str]                    # Ordered by precedence
    precedence_order: list[int]              # Precedence values
    effective_token_limit: int | None        # Resolved limit
    effective_cost_limit_cents: int | None   # Resolved limit
    effective_burn_rate_limit: float | None  # Resolved limit
    effective_breach_action: str             # Resolved action
    conflicts_resolved: int                  # Number of conflicts
    resolution_strategy: str                 # Strategy used
    arbitration_timestamp: datetime          # When arbitrated
    snapshot_hash: str                       # For audit
```

#### AlertEmitter

**Location:** `backend/app/services/alert_emitter.py`
**Layer:** L3
**Purpose:** Emit alerts via configured channels

```python
class AlertEmitter:
    async def emit_near_threshold(self, signal: ThresholdSignal, config: AlertConfig) -> bool
    async def emit_breach(self, signal: ThresholdSignal, config: AlertConfig, action: str) -> bool
```

---

## 6. Runtime Flow

### 6.1 Policy Resolution at Run Start

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    POLICY RESOLUTION (RUN START)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Run Created with context:                                              │
│    - run_id: RUN-001                                                    │
│    - tenant_id: TNT-001                                                 │
│    - agent_id: AGT-001                                                  │
│    - api_key_id: KEY-001                                                │
│                                                                         │
│  1. ScopeResolver.resolve_applicable_policies()                         │
│     │                                                                   │
│     ├─► Query PolicyScopes where:                                       │
│     │   - scope_type = ALL_RUNS, or                                     │
│     │   - agent_id in agent_ids_json, or                                │
│     │   - api_key_id in api_key_ids_json                                │
│     │                                                                   │
│     ├─► Returns: [POL-001, POL-002, POL-003]                            │
│     │                                                                   │
│  2. PolicyArbitrator.arbitrate()                                        │
│     │                                                                   │
│     ├─► Load PolicyPrecedence for each                                  │
│     ├─► Sort by precedence (lower = higher priority)                    │
│     ├─► Resolve limit conflicts:                                        │
│     │   - POL-001: token_limit=10000, precedence=10                     │
│     │   - POL-002: token_limit=50000, precedence=50                     │
│     │   - Strategy: MOST_RESTRICTIVE → 10000 wins                       │
│     ├─► Resolve action conflicts:                                       │
│     │   - POL-001: action=stop, precedence=10                           │
│     │   - POL-003: action=pause, precedence=30                          │
│     │   - Strategy: MOST_RESTRICTIVE → stop wins                        │
│     │                                                                   │
│  3. PolicySnapshot.create_snapshot()                                    │
│     │                                                                   │
│     ├─► Serialize effective limits                                      │
│     ├─► Compute content_hash                                            │
│     ├─► Store immutable snapshot                                        │
│     │                                                                   │
│  4. Attach snapshot_id to Run                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Prevention at Each Step

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PREVENTION (EACH STEP)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Step 5 completes:                                                      │
│    - tokens_so_far: 8500                                                │
│    - cost_so_far: 340 cents                                             │
│    - burn_rate: 500 tokens/second                                       │
│                                                                         │
│  1. PreventionEngine.evaluate_step()                                    │
│     │                                                                   │
│     ├─► Load MonitorConfig for policy                                   │
│     │   - monitor_token_usage: true                                     │
│     │   - monitor_cost: true                                            │
│     │   - monitor_burn_rate: false                                      │
│     │                                                                   │
│     ├─► Check token usage:                                              │
│     │   - current: 8500, limit: 10000                                   │
│     │   - percentage: 85%                                               │
│     │   - near_threshold_percentage: 80%                                │
│     │   - Result: NEAR_THRESHOLD                                        │
│     │                                                                   │
│     ├─► Create ThresholdSignal (type=NEAR)                              │
│     │                                                                   │
│  2. AlertEmitter.emit_near_threshold()                                  │
│     │                                                                   │
│     ├─► Check throttling (max_alerts_per_run, min_interval)             │
│     ├─► If not throttled:                                               │
│     │   - Send via enabled_channels: [ui, slack]                        │
│     │   - Record alert_sent=true                                        │
│     │                                                                   │
│  3. Continue execution (WARN action)                                    │
│                                                                         │
│  ---                                                                    │
│                                                                         │
│  Step 7 completes:                                                      │
│    - tokens_so_far: 11200                                               │
│                                                                         │
│  1. PreventionEngine.evaluate_step()                                    │
│     │                                                                   │
│     ├─► Check token usage:                                              │
│     │   - current: 11200, limit: 10000                                  │
│     │   - percentage: 112%                                              │
│     │   - Result: BREACH                                                │
│     │                                                                   │
│     ├─► Create ThresholdSignal (type=BREACH, action=stop)               │
│     │                                                                   │
│  2. AlertEmitter.emit_breach()                                          │
│     │                                                                   │
│     ├─► Breach alerts bypass throttling                                 │
│     ├─► Send via all enabled_channels                                   │
│     │                                                                   │
│  3. PreventionEngine → BLOCK                                            │
│     │                                                                   │
│     ├─► Update Run: status=FAILED_POLICY                                │
│     ├─► Update Run: termination_reason=POLICY_BLOCK                     │
│     ├─► Update Run: stopped_at_step=7                                   │
│     ├─► Update Run: violation_policy_id=POL-001                         │
│     │                                                                   │
│  4. Create Incident from violation                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Override Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EMERGENCY OVERRIDE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Request: Override POL-001 token limit for RUN-005                      │
│                                                                         │
│  1. Check OverrideAuthority                                             │
│     │                                                                   │
│     ├─► override_allowed: true                                          │
│     ├─► allowed_roles: [OWNER, SECURITY_ADMIN]                          │
│     ├─► requester role: OWNER ✓                                         │
│     ├─► requires_reason: true                                           │
│     ├─► requires_approval: true                                         │
│     │                                                                   │
│  2. Create OverrideRecord (status: pending_approval)                    │
│     │                                                                   │
│     ├─► reason: "Critical production issue requires extended run"       │
│     ├─► original_limits: {token: 10000}                                 │
│     ├─► override_limits: {token: 50000}                                 │
│     ├─► max_duration: 900 seconds                                       │
│     │                                                                   │
│  3. Approval required from SECURITY_ADMIN                               │
│     │                                                                   │
│     ├─► approved_by: "security-admin-001"                               │
│     ├─► started_at: now()                                               │
│     ├─► expires_at: now() + 900 seconds                                 │
│     │                                                                   │
│  4. Override ACTIVE                                                     │
│     │                                                                   │
│     ├─► New snapshot with override limits                               │
│     ├─► Full audit trail preserved                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Cross-Domain Links

### 7.1 Outbound Links (Policies →)

| Target Domain | Link Field | Purpose |
|---------------|------------|---------|
| Activity | `runs.policy_snapshot_id` | Snapshot at run start |
| Activity | `runs.violation_policy_id` | Policy that caused violation |
| Incidents | `incidents.policy_id` | Links incident to violated policy |
| Logs | `aos_traces.violation_policy_id` | Policy in trace context |

### 7.2 Inbound Links (→ Policies)

| Source Domain | Link Field | Purpose |
|---------------|------------|---------|
| Activity | `prevention_records.policy_id` | Prevention actions per step |
| Incidents | `incident_engine` | Records violation against policy |
| Analytics | Cost attribution | Tracks costs per policy |

### 7.3 Link Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    POLICIES CROSS-DOMAIN LINKS                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                           ┌─────────────┐                               │
│                           │  POLICIES   │                               │
│                           │             │                               │
│                           │ PolicyRule  │                               │
│                           │ PolicyScope │                               │
│                           │ PolicySnap  │                               │
│                           └──────┬──────┘                               │
│                                  │                                      │
│         ┌──────────────┬─────────┼─────────┬──────────────┐             │
│         │              │         │         │              │             │
│         ▼              ▼         ▼         ▼              ▼             │
│   ┌──────────┐   ┌──────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐       │
│   │ Activity │   │ Incidents│ │ Logs │ │ Analytics│ │ Overrides│       │
│   │          │   │          │ │      │ │          │ │          │       │
│   │ Run      │   │ Incident │ │Trace │ │ Cost     │ │ Record   │       │
│   │ snapshot │◄──│ policy_id│ │policy│ │ policy   │ │ policy_id│       │
│   │ _id      │   │          │ │_id   │ │ _id      │ │          │       │
│   └──────────┘   └──────────┘ └──────┘ └──────────┘ └──────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Migration

### 8.1 Tables Created by Migration 111

| Table | Purpose |
|-------|---------|
| `policy_scopes` | Scope selector definitions |
| `policy_precedence` | Precedence and conflict strategy |
| `policy_monitor_configs` | Monitor configuration |
| `threshold_signals` | Threshold event records |
| `policy_alert_configs` | Alert channel configuration |
| `policy_override_authority` | Override rules |
| `policy_override_records` | Override audit trail |

### 8.2 Immutability Triggers

```sql
-- threshold_signals: immutable after creation
CREATE TRIGGER trigger_threshold_signals_immutable
BEFORE UPDATE ON threshold_signals
FOR EACH ROW EXECUTE FUNCTION raise_immutable_error();

-- policy_override_records: immutable after creation
CREATE TRIGGER trigger_override_records_immutable
BEFORE UPDATE ON policy_override_records
FOR EACH ROW EXECUTE FUNCTION raise_immutable_error();
```

---

## 9. Failure Semantics

### 9.1 Failure Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `FAIL_CLOSED` | Deny on ambiguity | Security-critical policies |
| `FAIL_OPEN` | Allow on ambiguity | Observability-only policies |

### 9.2 Failure Handling

| Failure | Behavior |
|---------|----------|
| DB unavailable | FAIL_CLOSED (deny execution) |
| Policy not found | FAIL_CLOSED (deny execution) |
| Evaluation timeout | FAIL_CLOSED (deny step) |
| Alert delivery failure | Log error, continue (non-blocking) |
| Snapshot creation failure | FAIL_CLOSED (cannot start run) |

---

## 10. References

| Document | Purpose |
|----------|---------|
| `CROSS_DOMAIN_DATA_ARCHITECTURE.md` | Domain registry and data flow |
| `POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md` | Implementation details |
| `BACKEND_REMEDIATION_PLAN.md` | Gap remediation status |
| `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain definitions |

---

**End of Document**
