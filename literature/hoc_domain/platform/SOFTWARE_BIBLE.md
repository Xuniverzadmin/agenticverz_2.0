# Platform — Software Bible (DRAFT)

**Domain:** platform (int/platform)
**Status:** DRAFT — not yet canonical
**L5 Engines:** 20
**L6 Drivers:** 42
**L2.1 Facades:** 3
**Subdomains:** governance, iam, policy
**Generated:** 2026-02-01
**Reference:** PIN-513 Phase 7

---

## Layer Inventory

### L5 Engines (`hoc/int/platform/engines/`)

| File | Role | Key Exports |
|------|------|-------------|
| `engine.py` | Core workflow execution | `WorkflowEngine`, `StepDescriptor`, `WorkflowSpec`, `StepContext` |
| `platform_health_engine.py` | Platform health authority | `PlatformHealthEngine`, `HealthState`, `CapabilityHealth`, `DomainHealth`, `SystemHealth` |
| `evaluator.py` | Limits evaluation | `LimitsEvaluator`, `TenantQuotas`, `ExecutionIntent` |
| `sandbox_service.py` | Sandbox policy enforcement | `SandboxService`, `SandboxPolicy`, `ExecutionRequest` |
| `state_resolver.py` | Tenant state resolution | `TenantStateResolver`, `TenantState` |
| `pool_manager.py` | Connection pool management | `ConnectionPoolManager`, `PoolType`, `PoolStatus` |
| `replay.py` | Execution replay engine | `ReplayEngine`, `ReplayResult` |
| `kill_switch_guard.py` | Kill switch enforcement | `KillSwitchGuard`, `JobKilledException` |
| `external_guard.py` | External call blocking | `ExternalCallsGuard`, `ExternalCallBlockedError` |
| `failure_intelligence.py` | Recovery intelligence | Failure pattern analysis |
| `errors.py` | Error classification | `WorkflowError`, `ErrorCategory`, `classify_exception()` |
| `metrics.py` | Metrics recording | 18+ recording functions |
| `health.py` | Health configuration | `configure_health()`, `record_checkpoint_activity()` |
| `customer_sandbox.py` | Customer sandbox auth | `resolve_sandbox_auth()`, `SandboxCustomerPrincipal` |
| `s1_rollback.py` | Rollback observation | `RollbackObserver`, `observe_rollback_frequency()` |
| `m10_metrics_collector.py` | M10 monitoring metrics | Metrics collection |
| `config.py` | Learning config | `learning_enabled()`, `set_learning_enabled()` |
| `tables.py` | Table access validation | `validate_table_access()` |

### L6 Drivers (`hoc/int/platform/drivers/`) — 42 files

**Core Infrastructure:**

| File | Role | Key Exports |
|------|------|-------------|
| `platform_health_driver.py` | Health data access | `PlatformHealthDriver`, `SignalRow`, `IncidentCount` |
| `care.py` | Fairness/rate limiting (1530 LOC) | `CAREEngine`, `RateLimiter`, `FairnessTracker` |
| `checkpoint.py` | Workflow checkpoints | `CheckpointStore`, `WorkflowCheckpoint` |
| `cost_tracker.py` | Cost enforcement | `CostTracker`, `CostQuota`, `CostEnforcementResult` |
| `executor.py` | Scheduler execution | `APSchedulerExecutor` |
| `governor.py` | Execution governance | `Governor`, `GovernorState`, `RollbackReason` |
| `policies.py` | Budget enforcement | `PolicyEnforcer`, `BudgetStore` |
| `secrets.py` | Secret management | `Secrets`, `validate_required_secrets()` |

**Observability & Events:**

| File | Role |
|------|------|
| `emitters.py` | Event emission (8 emit functions) |
| `events.py` | Event model (`UnifiedEvent`, `Severity`, `ActorType`) |
| `error_envelope.py` | Error envelope (`ErrorEnvelope`, `ErrorSeverity`) |
| `error_store.py` | Error persistence (9 functions) |
| `logging_context.py` | Structured logging context |
| `observability_provider.py` | Observability protocol |
| `golden.py` | Golden record capture |
| `canonicalize.py` | Canonical JSON for golden events |

**Intelligence & Learning:**

| File | Role |
|------|------|
| `drift_detector.py` | Execution drift detection |
| `failure_catalog.py` | Failure pattern matching |
| `feedback.py` | Feedback loops |
| `iaec.py` | Instruction-aware embedding |
| `learning.py` | Agent reputation/quarantine |
| `memory_service.py` | Memory service |
| `memory_store.py` | Memory persistence |
| `retriever.py` | Memory retrieval |
| `suggestions.py` | Learning suggestions |
| `embedding_cache.py` | Embedding cache |
| `embedding_metrics.py` | Embedding quota tracking |
| `vector_store.py` | Vector memory store |

**Planning & Execution:**

| File | Role |
|------|------|
| `interface.py` | Planner interface protocol |
| `stub_planner.py` | Stub planner implementation |
| `planner_sandbox.py` | Plan validation sandbox |
| `sandbox_executor.py` | Sandbox execution |
| `job_execution.py` | Job retry/progress/audit |
| `job_scheduler.py` | Job scheduling |
| `probes.py` | Capability probing |
| `routing_models.py` | Routing decision models |

**Configuration & Governance:**

| File | Role |
|------|------|
| `console_modes.py` | Console mode resolution |
| `flag_sync.py` | Feature flag sync |
| `governance.py` | Governance error types |
| `override_resolver.py` | Override resolution |
| `update_rules.py` | Update/merge rules |
| `external_response_service.py` | External response recording |

### L2.1 Facades (`hoc/int/platform/facades/`)

| File | Role | Key Exports |
|------|------|-------------|
| `platform_eligibility_adapter.py` | Health → API view translation | `PlatformEligibilityAdapter`, `SystemHealthView` |
| `anthropic_adapter.py` | Anthropic planner adapter | `AnthropicPlanner` |
| `stub_adapter.py` | Stub planner adapter | `StubPlanner` |

### Subdomains

| Subdomain | Layer | Files | Key Exports |
|-----------|-------|-------|-------------|
| `governance/drivers/` | L6 | `governance_signal_service.py` | `GovernanceSignalService`, `check_governance_status()` |
| `iam/engines/` | L5 | `iam_service.py` | `IAMService`, `Identity`, `AccessDecision` |
| `policy/engines/` | L5 | `policy_driver.py` | `PolicyDriver`, `get_policy_driver()` |

### L2 APIs

| File | Role |
|------|------|
| `api/cus/agent/platform.py` | `GET /platform/health`, `/platform/capabilities`, `/platform/domains/{name}` |

---

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

| File | Change | Reference |
|------|--------|-----------|
| `int/platform/facades/platform_eligibility_adapter.py:36` | Import swapped: `app.services.platform.platform_health_service` → `app.hoc.int.platform.engines.platform_health_engine` | PIN-513 Phase 7, Step 4 |
| `int/platform/engines/platform_health_engine.py` | **NEW** — L5 engine extracted from `app/services/platform/platform_health_engine.py` (607 LOC) | PIN-513 Phase 7 |
| `int/platform/drivers/platform_health_driver.py` | **NEW** — L6 driver extracted from `app/services/platform/platform_health_driver.py` (301 LOC) | PIN-513 Phase 7 |

**Result:** Zero `app.services` imports remain in platform domain.
