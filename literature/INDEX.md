# HOC Spine — Literature Study Index

**Total scripts:** 65  
**Clean:** 63  
**With violations:** 2  
**Source:** `backend/app/hoc/cus/hoc_spine/`  
**Validator:** `scripts/ops/hoc_spine_study_validator.py`

---

## Navigation

| Folder | Layer | Scripts | Violations | Purpose |
|--------|-------|---------|------------|---------|
| [Orchestrator](hoc_spine/orchestrator/_summary.md) | L4 | 11 | 0 | Sole execution entry point from L2. Owns transaction boundaries, operation resol... |
| [Authority](hoc_spine/authority/_summary.md) | L4 | 8 | 0 | Decides WHAT is allowed, not HOW. Determines eligibility, runtime mode, policy p... |
| [Consequences](hoc_spine/consequences/_summary.md) | L5 | 1 | 0 | After-the-fact reactions. Handles effects (notifications, exports, escalations),... |
| [Services](hoc_spine/services/_summary.md) | L5 | 24 | 0 | Spine-only shared utilities. Must be stateless, deterministic, and domain-agnost... |
| [Schemas](hoc_spine/schemas/_summary.md) | L5 | 8 | 0 | Shared contracts, not models. Defines operation shapes, execution context, and a... |
| [Drivers](hoc_spine/drivers/_summary.md) | L6 | 13 | 2 | Cross-domain DB boundary. Reads/writes across domain tables. Participates in tra... |

## Orchestrator

[Folder Summary](hoc_spine/orchestrator/_summary.md)

- [constraint_checker.py](hoc_spine/orchestrator/constraint_checker.md) — Module: constraint_checker
- [execution.py](hoc_spine/orchestrator/execution.md) — Module: execution
- [governance_orchestrator.py](hoc_spine/orchestrator/governance_orchestrator.md) — Part-2 Governance Orchestrator (L4)
- [job_executor.py](hoc_spine/orchestrator/job_executor.md) — Part-2 Job Executor (L5)
- [knowledge_plane.py](hoc_spine/orchestrator/knowledge_plane.md) — KnowledgePlane - Knowledge plane models and registry.
- [offboarding.py](hoc_spine/orchestrator/offboarding.md) — Offboarding Stage Handlers
- [onboarding.py](hoc_spine/orchestrator/onboarding.md) — Onboarding Stage Handlers
- [phase_status_invariants.py](hoc_spine/orchestrator/phase_status_invariants.md) — Module: phase_status_invariants
- [plan_generation_engine.py](hoc_spine/orchestrator/plan_generation_engine.md) — Domain engine for plan generation.
- [pool_manager.py](hoc_spine/orchestrator/pool_manager.md) — Connection Pool Manager (GAP-172)
- [run_governance_facade.py](hoc_spine/orchestrator/run_governance_facade.md) — Run Governance Facade (L4 Domain Logic)

## Authority

[Folder Summary](hoc_spine/authority/_summary.md)

- [concurrent_runs.py](hoc_spine/authority/concurrent_runs.md) — Concurrent run limit enforcement (Redis-backed)
- [contract_engine.py](hoc_spine/authority/contract_engine.md) — Part-2 Contract Service (L4)
- [degraded_mode_checker.py](hoc_spine/authority/degraded_mode_checker.md) — Module: degraded_mode_checker
- [guard_write_engine.py](hoc_spine/authority/guard_write_engine.md) — Guard Write Engine (L5)
- [profile_policy_mode.py](hoc_spine/authority/profile_policy_mode.md) — Governance Profile Configuration
- [runtime.py](hoc_spine/authority/runtime.md) — Runtime Utilities - Centralized Shared Helpers
- [runtime_adapter.py](hoc_spine/authority/runtime_adapter.md) — Runtime Adapter (L2)
- [runtime_switch.py](hoc_spine/authority/runtime_switch.md) — Module: runtime_switch

## Consequences

[Folder Summary](hoc_spine/consequences/_summary.md)

- [export_bundle_adapter.py](hoc_spine/consequences/export_bundle_adapter.md) — Export Bundle Adapter (L2)

## Services

[Folder Summary](hoc_spine/services/_summary.md)

- [alert_delivery.py](hoc_spine/services/alert_delivery.md) — Alert Delivery Adapter (L2)
- [alerts_facade.py](hoc_spine/services/alerts_facade.md) — Alerts Facade (L4 Domain Logic)
- [audit_durability.py](hoc_spine/services/audit_durability.md) — Module: durability
- [audit_store.py](hoc_spine/services/audit_store.md) — Audit Store
- [canonical_json.py](hoc_spine/services/canonical_json.md) — Canonical JSON serialization for AOS.
- [compliance_facade.py](hoc_spine/services/compliance_facade.md) — Compliance Facade (L4 Domain Logic)
- [control_registry.py](hoc_spine/services/control_registry.md) — Module: control_registry
- [cus_credential_service.py](hoc_spine/services/cus_credential_service.md) — Customer Credential Service
- [dag_sorter.py](hoc_spine/services/dag_sorter.md) — DAG-based execution ordering for PLang v2.0.
- [db_helpers.py](hoc_spine/services/db_helpers.md) — Database helper functions for SQLModel row extraction.
- [deterministic.py](hoc_spine/services/deterministic.md) — Deterministic execution utilities (pure computation, no boundary cross
- [fatigue_controller.py](hoc_spine/services/fatigue_controller.md) — AlertFatigueController - Alert fatigue management service.
- [guard.py](hoc_spine/services/guard.md) — Guard Console Data Contracts - Customer-Facing API
- [input_sanitizer.py](hoc_spine/services/input_sanitizer.md) — Input sanitization for security (pure regex validation and URL parsing
- [lifecycle_facade.py](hoc_spine/services/lifecycle_facade.md) — Lifecycle Facade (L4 Domain Logic)
- [lifecycle_stages_base.py](hoc_spine/services/lifecycle_stages_base.md) — Stage Handler Protocol and Base Types
- [metrics_helpers.py](hoc_spine/services/metrics_helpers.md) — Prometheus Metrics Helpers - Idempotent Registration
- [monitors_facade.py](hoc_spine/services/monitors_facade.md) — Monitors Facade (L4 Domain Logic)
- [rate_limiter.py](hoc_spine/services/rate_limiter.md) — Rate limiting utilities (Redis-backed)
- [retrieval_facade.py](hoc_spine/services/retrieval_facade.md) — Retrieval Facade (L4 Domain Logic)
- [retrieval_mediator.py](hoc_spine/services/retrieval_mediator.md) — Module: retrieval_mediator
- [scheduler_facade.py](hoc_spine/services/scheduler_facade.md) — Scheduler Facade (L4 Domain Logic)
- [time.py](hoc_spine/services/time.md) — Common time utilities for customer domain modules (pure datetime compu
- [webhook_verify.py](hoc_spine/services/webhook_verify.md) — Webhook Signature Verification Utility

## Schemas

[Folder Summary](hoc_spine/schemas/_summary.md)

- [agent.py](hoc_spine/schemas/agent.md) — Agent API request/response schemas (pure Pydantic DTOs)
- [artifact.py](hoc_spine/schemas/artifact.md) — Artifact API schemas (pure Pydantic DTOs)
- [common.py](hoc_spine/schemas/common.md) — Common Data Contracts - Shared Infrastructure Types
- [plan.py](hoc_spine/schemas/plan.md) — Plan API schemas (pure Pydantic DTOs)
- [rac_models.py](hoc_spine/schemas/rac_models.md) — Runtime Audit Contract (RAC) Models
- [response.py](hoc_spine/schemas/response.md) — Standard API Response Envelope
- [retry.py](hoc_spine/schemas/retry.md) — Retry API schemas
- [skill.py](hoc_spine/schemas/skill.md) — Skill API schemas (pure Pydantic DTOs)

## Drivers

[Folder Summary](hoc_spine/drivers/_summary.md)

- [alert_driver.py](hoc_spine/drivers/alert_driver.md) — Alert Driver (L6)
- [alert_emitter.py](hoc_spine/drivers/alert_emitter.md) — Alert Emitter Service
- [cross_domain.py](hoc_spine/drivers/cross_domain.md) — Cross-Domain Governance Functions (Mandatory)
- [dag_executor.py](hoc_spine/drivers/dag_executor.md) — DAG-based executor for PLang v2.0.
- [decisions.py](hoc_spine/drivers/decisions.md) — Phase 4B: Decision Record Models and Service
- [governance_signal_driver.py](hoc_spine/drivers/governance_signal_driver.md) — Governance Signal Service (Phase E FIX-03)
- [guard_cache.py](hoc_spine/drivers/guard_cache.md) — Redis-based cache for Guard Console endpoints.
- [guard_write_driver.py](hoc_spine/drivers/guard_write_driver.md) — Guard Write Driver (L6)
- [idempotency.py](hoc_spine/drivers/idempotency.md) — Idempotency key utilities
- [ledger.py](hoc_spine/drivers/ledger.md) — Discovery Ledger - signal recording helpers.
- [schema_parity.py](hoc_spine/drivers/schema_parity.md) — M26 Prevention Mechanism #2: Startup Schema Parity Guard
- [transaction_coordinator.py](hoc_spine/drivers/transaction_coordinator.md) — Transaction Coordinator for Cross-Domain Writes
- [worker_write_service_async.py](hoc_spine/drivers/worker_write_service_async.md) — Worker Write Service (Async) - DB write operations for Worker API.

---

## Violation Summary

**2 violations across 2 files:**

| Folder | Script | Violation |
|--------|--------|-----------|
| drivers | decisions.py | Driver calls commit (only transaction_coordinator allowed) |
| drivers | ledger.py | Driver calls commit (only transaction_coordinator allowed) |

## Build List — Missing Spine Primitives

### Orchestrator

- [ ] Explicit OperationRegistry — operation→callable mapping
- [ ] Mandatory cross_domain_deps=[] declaration per operation
- [ ] Hard assertion: no L5 may call coordinator directly

### Authority

- [ ] Unified AuthorityDecision object returned to orchestrator
- [ ] Explicit deny / degraded / conditional execution states

### Consequences

- [ ] Generic PostExecutionHook interface
- [ ] Sync vs async consequence separation

### Schemas

- [ ] AuthorityDecision schema
- [ ] ExecutionContext schema (unified)

### Drivers

- [ ] Runtime enforcement: block commit() in non-coordinator drivers
- [ ] Clear READ vs WRITE driver naming distinction
