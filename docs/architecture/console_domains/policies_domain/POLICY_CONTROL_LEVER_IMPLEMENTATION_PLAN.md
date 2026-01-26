# Policy Control Lever Implementation Plan

**Status:** ✅ PHASE 1 COMPLETE
**Created:** 2026-01-20
**Updated:** 2026-01-20 (Phase 1 models/engines complete)
**Reference:** `CROSS_DOMAIN_DATA_ARCHITECTURE.md`, `BACKEND_REMEDIATION_PLAN.md`

---

## 1. Objective

Implement a comprehensive policy control lever system that provides:

```
Policy → Scope Selector → Monitors → Limits → Thresholds → Actions → Evidence
```

**Core Principle:**
> A policy is a versioned, scoped, runtime-bound control contract that deterministically governs execution behavior and produces immutable evidence.

---

## 2. Gap Registry

| Gap ID | Description | Priority | Dependencies | Status |
|--------|-------------|----------|--------------|--------|
| PCL-001 | Scope Selector model (agent, API key, human actor) | P0 | None | ✅ DONE |
| PCL-002 | Scope Resolver engine | P0 | PCL-001 | ✅ DONE |
| PCL-003 | Policy Precedence model | P0 | None | ✅ DONE |
| PCL-004 | Policy Arbitrator engine | P0 | PCL-003 | ✅ DONE |
| PCL-005 | Monitor Configuration model | P1 | None | ✅ DONE |
| PCL-006 | Threshold Signal model | P1 | PCL-005 | ✅ DONE |
| PCL-007 | Alert Emitter service | P1 | PCL-006 | ✅ DONE |
| PCL-008 | Binding Moment field | P2 | None | ✅ DONE (in PolicyPrecedence) |
| PCL-009 | Negative Capabilities model | P2 | None | ✅ DONE (in MonitorConfig) |
| PCL-010 | Override Authority model | P2 | None | ✅ DONE |
| PCL-011 | Failure Semantics config | P3 | None | ✅ DONE (in PolicyPrecedence) |
| PCL-012 | Alembic migration | P0 | PCL-001 to PCL-007 | ✅ DONE |
| PCL-013 | Policy lifecycle audit events | P1 | PCL-012 | ⏳ PENDING (API wiring)

---

## 3. Design Specifications

### 3.1 Scope Selector (PCL-001)

**Purpose:** Define WHO the policy applies to

```python
class ScopeType(str, Enum):
    ALL_RUNS = "all_runs"           # All LLM runs for tenant
    AGENT = "agent"                 # Specific agent IDs
    API_KEY = "api_key"             # Specific API keys
    HUMAN_ACTOR = "human_actor"     # Specific human actors

class PolicyScope(SQLModel, table=True):
    __tablename__ = "policy_scopes"

    id: int = Field(primary_key=True)
    scope_id: str = Field(index=True, unique=True)
    policy_id: str = Field(foreign_key="policy_rules.policy_id", index=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)

    # Scope definition
    scope_type: str  # ScopeType value
    agent_ids: str | None  # JSON array
    api_key_ids: str | None  # JSON array
    human_actor_ids: str | None  # JSON array

    # Metadata
    created_at: datetime
    updated_at: datetime
```

**Invariants:**
- `ALL_RUNS` cannot be combined with specific IDs
- Scope is resolved BEFORE run starts
- Resolved scope is stored in policy snapshot

### 3.2 Policy Precedence (PCL-003)

**Purpose:** Define conflict resolution strategy

```python
class ConflictStrategy(str, Enum):
    MOST_RESTRICTIVE = "most_restrictive"
    EXPLICIT_PRIORITY = "explicit_priority"
    FAIL_CLOSED = "fail_closed"

class PolicyPrecedence(SQLModel, table=True):
    __tablename__ = "policy_precedence"

    id: int = Field(primary_key=True)
    policy_id: str = Field(foreign_key="policy_rules.policy_id", unique=True)

    precedence: int = Field(default=100)  # Lower = higher priority
    conflict_strategy: str = Field(default="most_restrictive")

    # Binding moment
    bind_at: str = Field(default="run_start")  # run_start | first_token | each_step
```

**Arbitration Rules:**
1. Lower precedence number wins
2. Same precedence → use conflict_strategy
3. MOST_RESTRICTIVE → smallest limit, harshest action
4. FAIL_CLOSED → if ambiguous, deny

### 3.3 Monitor Configuration (PCL-005)

**Purpose:** Define WHAT signals to collect

```python
class MonitorConfig(SQLModel, table=True):
    __tablename__ = "policy_monitor_configs"

    id: int = Field(primary_key=True)
    config_id: str = Field(index=True, unique=True)
    policy_id: str = Field(foreign_key="policy_rules.policy_id", index=True)

    # Token monitoring
    monitor_token_usage: bool = Field(default=True)
    monitor_token_per_step: bool = Field(default=False)

    # Cost monitoring
    monitor_cost: bool = Field(default=True)
    monitor_burn_rate: bool = Field(default=False)
    burn_rate_window_seconds: int = Field(default=60)

    # RAG monitoring
    monitor_rag_access: bool = Field(default=False)
    allowed_rag_sources: str | None  # JSON array of allowed source IDs

    # Inspection constraints (negative capabilities)
    allow_prompt_logging: bool = Field(default=False)
    allow_response_logging: bool = Field(default=False)
    allow_pii_capture: bool = Field(default=False)
```

### 3.4 Threshold Signal (PCL-006)

**Purpose:** Record near/breach events for alerting and audit

```python
class SignalType(str, Enum):
    NEAR = "near"
    BREACH = "breach"

class ThresholdSignal(SQLModel, table=True):
    __tablename__ = "threshold_signals"

    id: int = Field(primary_key=True)
    signal_id: str = Field(index=True, unique=True)

    # References
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    policy_id: str = Field(foreign_key="policy_rules.policy_id", index=True)
    tenant_id: str = Field(index=True)
    step_index: int | None

    # Signal data
    signal_type: str  # SignalType value
    metric: str  # token_usage, cost, burn_rate, rag_access
    current_value: float
    threshold_value: float
    percentage: float | None  # For NEAR signals

    # Metadata
    timestamp: datetime
    acknowledged: bool = Field(default=False)
    acknowledged_by: str | None
    acknowledged_at: datetime | None
```

### 3.5 Near-Threshold Alert Config (PCL-007)

**Purpose:** Configure alerting behavior for near-threshold events

```python
class AlertConfig(SQLModel, table=True):
    __tablename__ = "policy_alert_configs"

    id: int = Field(primary_key=True)
    policy_id: str = Field(foreign_key="policy_rules.policy_id", unique=True)

    # Near-threshold alerting
    near_threshold_enabled: bool = Field(default=True)
    near_threshold_percentage: int = Field(default=80)

    # Notification channels
    notify_ui: bool = Field(default=True)
    notify_webhook: bool = Field(default=False)
    webhook_url: str | None

    # Alert throttling
    min_alert_interval_seconds: int = Field(default=60)
```

### 3.6 Override Authority (PCL-010)

**Purpose:** Define emergency override rules

```python
class OverrideAuthority(SQLModel, table=True):
    __tablename__ = "policy_override_authority"

    id: int = Field(primary_key=True)
    policy_id: str = Field(foreign_key="policy_rules.policy_id", unique=True)

    # Override rules
    override_allowed: bool = Field(default=True)
    allowed_roles: str  # JSON array: ["OWNER", "SECURITY_ADMIN"]
    requires_reason: bool = Field(default=True)
    max_duration_seconds: int = Field(default=900)  # 15 minutes default

    # Audit
    last_override_at: datetime | None
    last_override_by: str | None
    last_override_reason: str | None
```

---

## 4. Engine Implementations

### 4.1 Scope Resolver (PCL-002)

**File:** `backend/app/policy/scope_resolver.py`

```python
class ScopeResolver:
    """Resolve which policies apply to a given run context."""

    def resolve_applicable_policies(
        self,
        tenant_id: str,
        agent_id: str | None,
        api_key_id: str | None,
        human_actor_id: str | None
    ) -> list[PolicyRule]:
        """Return all policies that match the run context."""
        pass

    def matches_scope(
        self,
        scope: PolicyScope,
        agent_id: str | None,
        api_key_id: str | None,
        human_actor_id: str | None
    ) -> bool:
        """Check if a single scope matches the context."""
        pass
```

### 4.2 Policy Arbitrator (PCL-004)

**File:** `backend/app/policy/arbitrator.py`

```python
class PolicyArbitrator:
    """Resolve conflicts between multiple applicable policies."""

    def arbitrate(
        self,
        policies: list[PolicyRule],
        precedence_map: dict[str, PolicyPrecedence]
    ) -> ArbitrationResult:
        """Return effective limits and actions from multiple policies."""
        pass

    def resolve_limit_conflict(
        self,
        limits: list[PolicyLimit],
        strategy: ConflictStrategy
    ) -> PolicyLimit:
        """Resolve conflicting limits using strategy."""
        pass

    def resolve_action_conflict(
        self,
        actions: list[str],
        strategy: ConflictStrategy
    ) -> str:
        """Resolve conflicting actions (PAUSE vs STOP vs KILL)."""
        pass
```

### 4.3 Alert Emitter (PCL-007)

**File:** `backend/app/services/alert_emitter.py`

```python
class AlertEmitter:
    """Emit alerts for near-threshold and breach events."""

    async def emit_near_threshold(
        self,
        signal: ThresholdSignal,
        alert_config: AlertConfig
    ) -> None:
        """Emit near-threshold alert via configured channels."""
        pass

    async def emit_breach(
        self,
        signal: ThresholdSignal,
        action_taken: str
    ) -> None:
        """Emit breach alert with enforcement action."""
        pass
```

---

## 5. Execution Order

| Order | Phase | Task | Files | Status |
|-------|-------|------|-------|--------|
| 1 | Models | Create PolicyScope model | `models/policy_scope.py` | ✅ DONE |
| 2 | Models | Create PolicyPrecedence model | `models/policy_precedence.py` | ✅ DONE |
| 3 | Models | Create MonitorConfig model | `models/monitor_config.py` | ✅ DONE |
| 4 | Models | Create ThresholdSignal model | `models/threshold_signal.py` | ✅ DONE |
| 5 | Models | Create AlertConfig model | `models/alert_config.py` | ✅ DONE |
| 6 | Models | Create OverrideAuthority model | `models/override_authority.py` | ✅ DONE |
| 7 | Migration | Create Alembic migration | `alembic/versions/111_policy_control_lever.py` | ✅ DONE |
| 8 | Engine | Implement ScopeResolver | `policy/scope_resolver.py` | ✅ DONE |
| 9 | Engine | Implement PolicyArbitrator | `policy/arbitrator.py` | ✅ DONE |
| 10 | Service | Implement AlertEmitter | `services/alert_emitter.py` | ✅ DONE |
| 11 | Integration | Wire into PreventionEngine | `policy/prevention_engine.py` | ⏳ PENDING |
| 12 | API | Add scope/monitor endpoints | `api/policy_*.py` | ⏳ PENDING |
| 13 | Docs | Update CROSS_DOMAIN_DATA_ARCHITECTURE.md | docs/ | ✅ DONE |
| 14 | Docs | Create POLICIES_DOMAIN_ARCHITECTURE.md | docs/ | ✅ DONE |
| 15 | Docs | Create LOGS_DOMAIN_ARCHITECTURE.md | docs/ | ✅ DONE |

---

## 6. Runtime Flow (Target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          RUN CREATED                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. ScopeResolver.resolve_applicable_policies()                          │
│    - Query all active policies for tenant                               │
│    - Filter by scope (agent_id, api_key_id, human_actor_id)            │
│    - Return matching policies                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. PolicyArbitrator.arbitrate()                                         │
│    - Load precedence for each policy                                    │
│    - Sort by precedence (lower = higher priority)                       │
│    - Resolve limit conflicts (most_restrictive wins)                    │
│    - Resolve action conflicts (harshest action wins)                    │
│    - Return ArbitrationResult                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. PolicySnapshot.create_snapshot()                                     │
│    - Serialize resolved policies                                        │
│    - Serialize effective limits                                         │
│    - Hash for immutability                                              │
│    - Attach to run context                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FOR EACH EXECUTION STEP:                                                │
│                                                                         │
│   4a. MonitorCollector.collect_signals()                                │
│       - Token count                                                     │
│       - Cost delta                                                      │
│       - Burn rate (rolling window)                                      │
│       - RAG source access                                               │
│                                                                         │
│   4b. ThresholdEvaluator.evaluate()                                     │
│       - Compare current vs limits                                       │
│       - Calculate percentage                                            │
│       - Emit NEAR signal if >= alert_percentage                         │
│       - Emit BREACH signal if >= 100%                                   │
│                                                                         │
│   4c. AlertEmitter.emit() [if NEAR]                                     │
│       - Create ThresholdSignal record                                   │
│       - Send UI notification                                            │
│       - Send webhook if configured                                      │
│                                                                         │
│   4d. PreventionEngine.enforce() [if BREACH]                            │
│       - Mark inflection point                                           │
│       - Execute action (PAUSE / STOP / KILL)                            │
│       - Create incident                                                 │
│       - Halt execution                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. Evidence Persistence                                                 │
│    - TraceSummary with violation_step_index                             │
│    - ThresholdSignal records                                            │
│    - Incident with policy reference                                     │
│    - Audit log entries                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Audit Events (PCL-013)

| Event Type | Trigger | Data Captured |
|------------|---------|---------------|
| `POLICY_SCOPE_CREATED` | Scope added to policy | scope_id, policy_id, scope_type, target_ids |
| `POLICY_SCOPE_UPDATED` | Scope modified | scope_id, old_values, new_values |
| `POLICY_PRECEDENCE_SET` | Precedence assigned | policy_id, precedence, conflict_strategy |
| `THRESHOLD_NEAR` | Near-threshold signal | run_id, policy_id, metric, percentage |
| `THRESHOLD_BREACH` | Breach signal | run_id, policy_id, metric, action_taken |
| `POLICY_OVERRIDE_APPLIED` | Override used | policy_id, run_id, override_by, reason |
| `POLICY_ARBITRATION` | Conflict resolved | run_id, policies, resolution |

---

## 8. Success Criteria

After implementation, the system must satisfy:

> **At run start:** The system can explain which policies apply, why they apply, and which limits are effective after arbitration.

> **During execution:** The system emits near-threshold alerts before breach and enforces actions immediately on breach.

> **After enforcement:** The system produces immutable evidence linking run → policy → threshold → action → audit.

### Verification Checklist

- [ ] Scope selector filters policies correctly (agent, API key, human actor)
- [ ] Multiple policies arbitrate by precedence
- [ ] Most restrictive limit wins on conflict
- [ ] Near-threshold alerts emit at configured percentage
- [ ] Breach triggers immediate action (PAUSE/STOP/KILL)
- [ ] PolicySnapshot captures effective limits
- [ ] ThresholdSignal records are immutable
- [ ] Audit log captures all lifecycle events
- [ ] Export bundles include threshold signals

---

## 9. Files to Create/Modify

| Action | File | Purpose | Status |
|--------|------|---------|--------|
| CREATE | `backend/app/models/policy_scope.py` | Scope selector model | ✅ DONE |
| CREATE | `backend/app/models/policy_precedence.py` | Precedence model | ✅ DONE |
| CREATE | `backend/app/models/monitor_config.py` | Monitor config model | ✅ DONE |
| CREATE | `backend/app/models/threshold_signal.py` | Threshold signal model | ✅ DONE |
| CREATE | `backend/app/models/alert_config.py` | Alert config model | ✅ DONE |
| CREATE | `backend/app/models/override_authority.py` | Override model | ✅ DONE |
| CREATE | `backend/app/policy/scope_resolver.py` | Scope resolver engine | ✅ DONE |
| CREATE | `backend/app/policy/arbitrator.py` | Policy arbitrator engine | ✅ DONE |
| CREATE | `backend/app/services/alert_emitter.py` | Alert emitter service | ✅ DONE |
| CREATE | `backend/alembic/versions/111_policy_control_lever.py` | Migration | ✅ DONE |
| MODIFY | `backend/app/policy/prevention_engine.py` | Wire new components | ⏳ PENDING |
| MODIFY | `backend/app/models/__init__.py` | Export new models | ⏳ PENDING |
| MODIFY | `backend/app/policy/__init__.py` | Export new engines | ⏳ PENDING |
| CREATE | `docs/architecture/POLICIES_DOMAIN_ARCHITECTURE.md` | Policy domain doc | ✅ DONE |
| CREATE | `docs/architecture/LOGS_DOMAIN_ARCHITECTURE.md` | Logs domain doc | ✅ DONE |
| MODIFY | `docs/architecture/CROSS_DOMAIN_DATA_ARCHITECTURE.md` | Update with PCL | ✅ DONE |

---

## 10. References

| Document | Purpose |
|----------|---------|
| `CROSS_DOMAIN_DATA_ARCHITECTURE.md` | Domain registry |
| `BACKEND_REMEDIATION_PLAN.md` | Existing prevention engine |
| `prevention_engine.py` | Existing enforcement |
| `policy_snapshot.py` | Existing snapshot model |
