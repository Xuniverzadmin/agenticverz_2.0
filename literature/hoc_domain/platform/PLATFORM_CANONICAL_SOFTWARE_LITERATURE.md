# Platform Domain — Canonical Software Literature (DRAFT)

**Domain:** platform (int/platform)
**Status:** DRAFT — not yet canonical
**Generated:** 2026-02-01
**Reference:** PIN-513 Phase 7

---

## File Registry (Key Files)

### L5 Engines

**`platform_health_engine.py`** (NEW, ~350 LOC)
- Role: Platform Health Authority — THE source of truth for platform state
- Callers: `platform_eligibility_adapter.py` (facade), `api/cus/agent/platform.py` (L2)
- Delegates: `platform_health_driver.py` (L6)
- Key classes: `PlatformHealthEngine` (6 public methods), `HealthState` (enum), `SignalType` (enum), `HealthReason`, `CapabilityHealth`, `DomainHealth`, `SystemHealth`
- Factory: `get_platform_health_engine(session)`
- Backward compat: `PlatformHealthService = PlatformHealthEngine`
- Governance rule: HEALTH-IS-AUTHORITY — only this engine may produce health states
- Extracted from: `app/services/platform/platform_health_engine.py` (PIN-513 Phase 7)

**`engine.py`** (core workflow execution)
- Role: Core workflow orchestration engine
- Key classes: `WorkflowEngine`, `StepDescriptor`, `WorkflowSpec`, `StepContext`

**`evaluator.py`** (limits evaluation)
- Role: Tenant execution limits evaluation
- Key classes: `LimitsEvaluator`, `TenantQuotas`, `ExecutionIntent`, `LimitGroup`

**`sandbox_service.py`** (sandbox enforcement)
- Role: Sandbox policy and execution management
- Key classes: `SandboxService`, `SandboxPolicy`, `ExecutionRequest`

**`state_resolver.py`** (tenant state)
- Role: Resolve tenant state from multiple signals
- Key classes: `TenantStateResolver`, `TenantState`, `TenantNotFoundError`

**`pool_manager.py`** (connection pools)
- Role: Connection pool lifecycle management
- Key classes: `ConnectionPoolManager`, `PoolType`, `PoolStatus`

### L6 Drivers

**`platform_health_driver.py`** (NEW, ~250 LOC)
- Role: Data access for platform health evaluation (pure persistence)
- Callers: `platform_health_engine.py` (L5) only
- Key classes: `PlatformHealthDriver` (7 methods), `SignalRow` (frozen dataclass), `IncidentCount` (frozen dataclass)
- Factory: `get_platform_health_driver(session)`
- DB access: `GovernanceSignal` table, `Incident` table
- Extracted from: `app/services/platform/platform_health_driver.py` (PIN-513 Phase 7)

**`care.py`** (1530 LOC)
- Role: Fairness and rate limiting engine (CARE = Context-Aware Resource Enforcement)
- Key classes: `CAREEngine`, `RateLimiter`, `FairnessTracker`, `PerformanceStore`

**`checkpoint.py`** (workflow checkpoints)
- Role: Workflow checkpoint persistence
- Key classes: `CheckpointStore`, `WorkflowCheckpoint`, `InMemoryCheckpointStore`

**`cost_tracker.py`** (cost enforcement)
- Role: Cost tracking and quota enforcement
- Key classes: `CostTracker`, `CostQuota`, `CostEnforcementResult`

### L2.1 Facades

**`platform_eligibility_adapter.py`**
- Role: Translate L5 PlatformHealthEngine outputs to API-friendly views
- Callers: L2 platform endpoints
- Delegates: `PlatformHealthEngine` (L5)
- Key classes: `PlatformEligibilityAdapter`, `SystemHealthView`, `DomainHealthView`, `CapabilityHealthView`, `HealthReasonView`

---

## Legacy Connections

**None.** All `app.services` imports severed (PIN-513 Phase 7).

## Known Issues

- No tally script exists (`scripts/ops/hoc_platform_tally.py`)
- Domain not yet registered in `literature/hoc_domain/INDEX.md`
- 72 files total — comprehensive canonical audit not yet performed (this is a partial registry of key files)
- Subdomain files (governance, iam, policy) not fully documented
