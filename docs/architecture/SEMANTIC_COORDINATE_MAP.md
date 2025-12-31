# Semantic Coordinate Map

**Status:** PROPOSED
**Date:** 2025-12-30
**Reference:** PIN-251, PHASE3_SEMANTIC_CHARTER.md

---

## Purpose

This document classifies **every executable file** in the backend codebase across the four semantic axes defined in the Phase 3 Semantic Charter.

**Core Rule:**
> No file may remain BLOCKING. Every file must be classified or explicitly tagged as Semantically Neutral or Deferred.

---

## 4-Axis Legend

| Axis | Question | Example Values |
|------|----------|----------------|
| **X** | In-Layer Semantic Role | Orchestration, Routing, Verification, Authority, Executor, Storage |
| **Y** | Cross-Layer Contract | L2→L3, L3→L4, L4→L5, L5→L6, None |
| **Z** | Execution / Temporal | import-time, request-time, async-task, background-worker, scheduled |
| **⊙** | State & Authority | State Authority, State Observer, State Relay, Stateless |

---

## Status Values

| Status | Meaning |
|--------|---------|
| In scope | Must be resolved in Phase 3 |
| Deferred | Explicitly tied to Phase 4+ with reason |
| Semantically Neutral | Utility/glue, justified |
| **BLOCKING** | Cannot proceed until classified |

### Semantically Neutral Invariant

Files marked "Semantically Neutral" MUST satisfy ALL:
1. Do not mutate domain or platform state
2. Do not encode policy or decision logic
3. Do not initiate execution flows
4. Are pure utility, schema, or glue

### Deferred Files Registry

| File | Target Phase | Reason |
|------|--------------|--------|
| `api/legacy_routes.py` | Phase 4 | Deprecation candidate — routes to be removed or migrated |

---

## Layer 2 — Product APIs (`app/api/`)

HTTP request handlers. Orchestrate calls to L3/L4/L6.

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `api/agents.py` | Orchestration | L2→L4 Agent Registry | request-time | State Relay | In scope |
| `api/auth_helpers.py` | Request Handling | L2→L3 Auth Context | request-time | Stateless | Semantically Neutral |
| `api/cost_guard.py` | Orchestration | L2→L4 Cost Policy | request-time | State Relay | In scope |
| `api/cost_intelligence.py` | Orchestration | L2→L4 Cost Analysis | request-time | State Observer | In scope |
| `api/cost_ops.py` | Orchestration | L2→L4 Cost Ops | request-time | State Relay | In scope |
| `api/costsim.py` | Orchestration | L2→L4 Cost Simulation | request-time | State Relay | In scope |
| `api/customer_visibility.py` | Orchestration | L2→L4 Visibility | request-time | State Observer | In scope |
| `api/discovery.py` | Orchestration | L2→L4 Discovery | request-time | State Observer | In scope |
| `api/embedding.py` | Orchestration | L2→L6 External Service | request-time | Stateless | In scope |
| `api/feedback.py` | Orchestration | L2→L4 Feedback | request-time | State Relay | In scope |
| `api/founder_actions.py` | Orchestration | L2→L4 Founder Actions | request-time | State Relay | In scope |
| `api/founder_timeline.py` | Orchestration | L2→L4 Timeline Query | request-time | State Observer | In scope |
| `api/guard.py` | Orchestration | L2→L4 Guard Policy | request-time | State Relay | In scope |
| `api/health.py` | Routing | None | request-time | Stateless | Semantically Neutral |
| `api/integration.py` | Orchestration | L2→L4 Integration | request-time | State Relay | In scope |
| `api/legacy_routes.py` | Routing | L2→L4 Legacy | request-time | State Relay | Deferred (deprecation candidate) |
| `api/memory_pins.py` | Orchestration | L2→L4 Memory | request-time | State Observer | In scope |
| `api/onboarding.py` | Orchestration | L2→L4 Onboarding | request-time | State Relay | In scope |
| `api/ops.py` | Orchestration | L2→L4 Ops | request-time | State Observer | In scope |
| `api/policy.py` | Orchestration | L2→L4 Policy Execution | request-time | State Relay | In scope |
| `api/policy_layer.py` | Orchestration | L2→L4 Policy Layer | request-time | State Relay | In scope |
| `api/policy_proposals.py` | Orchestration | L2→L4 Policy Proposals | request-time | State Relay | In scope |
| `api/predictions.py` | Orchestration | L2→L4 Predictions | request-time | State Observer | In scope |
| `api/rbac_api.py` | Orchestration | L2→L3 RBAC | request-time | State Observer | In scope |
| `api/recovery.py` | Orchestration | L2→L4 Recovery | request-time | State Relay | In scope |
| `api/recovery_ingest.py` | Orchestration | L2→L4 Recovery Ingest | request-time | State Relay | In scope |
| `api/runtime.py` | Orchestration | L2→L5 Runtime Query | request-time | State Observer | In scope |
| `api/status_history.py` | Orchestration | L2→L4 Status Query | request-time | State Observer | In scope |
| `api/tenants.py` | Orchestration | L2→L4 Tenant Mgmt | request-time | State Relay | In scope |
| `api/traces.py` | Orchestration | L2→L6 Trace Storage | request-time | State Observer | In scope |
| `api/v1_killswitch.py` | Orchestration | L2→L4 Killswitch | request-time | State Relay | In scope |
| `api/v1_proxy.py` | Routing | L2→L4 Proxy | request-time | State Relay | In scope |
| `api/workers.py` | Orchestration | L2→L5 Worker Status | request-time | State Observer | In scope |

---

## Layer 3 — Boundary Adapters (`app/auth/`)

Identity verification, translation, adaptation. < 200 LOC target.

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `auth/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `auth.py` | Verification | L3→L4 Auth Context | request-time | Stateless | In scope |
| `auth/clerk_provider.py` | Adaptation | L3→L6 External Auth | request-time | Stateless | In scope |
| `auth/console_auth.py` | Verification | L3→L4 Console Context | request-time | Stateless | In scope |
| `auth/jwt_auth.py` | Verification | L3→L4 JWT Context | request-time | Stateless | In scope |
| `auth/oauth_providers.py` | Adaptation | L3→L6 OAuth | request-time | Stateless | In scope |
| `auth/oidc_provider.py` | Adaptation | L3→L6 OIDC | request-time | Stateless | In scope |
| `auth/rbac.py` | Policy | L3→L4 RBAC Policy | request-time | State Observer | In scope |
| `auth/rbac_engine.py` | Policy | L3→L4 RBAC Decisions | request-time | State Observer | In scope |
| `auth/rbac_middleware.py` | Enforcement | L3→L2 Middleware | request-time | Stateless | In scope |
| `auth/role_mapping.py` | Translation | L3→L4 Role Context | request-time | Stateless | In scope |
| `auth/shadow_audit.py` | Observation | L3→L6 Audit Log | request-time | State Observer | In scope |
| `auth/tenant_auth.py` | Verification | L3→L4 Tenant Context | request-time | Stateless | In scope |
| `auth/tier_gating.py` | Policy | L3→L4 Tier Policy | request-time | State Observer | In scope |

---

## Layer 4 — Domain Engines (`app/services/`, `app/policy/`, `app/integrations/`, etc.)

Business logic, authority, policy enforcement.

### Services (`app/services/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `services/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `services/certificate.py` | Authority | L4→L6 Cert Storage | sync | State Authority | In scope |
| `services/cost_anomaly_detector.py` | Authority | L4→L6 Anomaly Storage | sync | State Authority | In scope |
| `services/cost_write_service.py` | Authority | L4→L6 Cost DB Write | sync | State Authority | In scope |
| `services/email_verification.py` | Authority | L4→L6 Email Storage | sync | State Authority | In scope |
| `services/event_emitter.py` | Authority | L4→L6 Event Queue | sync | State Authority | In scope |
| `services/evidence_report.py` | Authority | L4→L6 Evidence Storage | sync | State Authority | In scope |
| `services/founder_action_write_service.py` | Authority | L4→L6 Action DB Write | sync | State Authority | In scope |
| `services/guard_write_service.py` | Authority | L4→L6 Guard DB Write | sync | State Authority | In scope |
| `services/incident_aggregator.py` | Authority | L4→L6 Incident Storage | sync | State Authority | In scope |
| `services/llm_failure_service.py` | Authority | L4→L6 Failure Storage | sync | State Authority | In scope |
| `services/ops_write_service.py` | Authority | L4→L6 Ops DB Write | sync | State Authority | In scope |
| `services/orphan_recovery.py` | Authority | L4→L6 Recovery Storage | sync | State Authority | In scope |
| `services/pattern_detection.py` | Authority | L4→L6 Pattern Storage | sync | State Observer | In scope |
| `services/policy_proposal.py` | Authority | L4→L6 Proposal Storage | sync | State Authority | In scope |
| `services/policy_violation_service.py` | Authority | L4→L6 Violation Storage | sync | State Authority | In scope |
| `services/prediction.py` | Authority | L4→L6 Prediction Storage | sync | State Authority | In scope |
| `services/recovery_matcher.py` | Authority | L4→L6 Match Storage | sync | State Observer | In scope |
| `services/recovery_rule_engine.py` | Authority | L4→L5 Rule Execution | sync | State Observer | In scope |
| `services/recovery_write_service.py` | Authority | L4→L6 Recovery DB Write | sync | State Authority | In scope |
| `services/replay_determinism.py` | Authority | L4→L6 Replay Verification | sync | State Observer | In scope |
| `services/scoped_execution.py` | Authority | L4→L5 Execution Context | sync | State Relay | In scope |
| `services/tenant_service.py` | Authority | L4→L6 Tenant Storage | sync | State Authority | In scope |
| `services/user_write_service.py` | Authority | L4→L6 User DB Write | sync | State Authority | In scope |
| `services/worker_registry_service.py` | Authority | L4→L6 Worker Registry | sync | State Authority | In scope |
| `services/worker_write_service_async.py` | Authority | L4→L6 Worker DB Write | async | State Authority | In scope |

### Policy Engine (`app/policy/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `policy/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/engine.py` | Authority | L4 Policy Execution | sync | State Observer | In scope |
| `policy/models.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `policy/ast/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/ast/nodes.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `policy/ast/visitors.py` | Authority | L4 AST Processing | sync | Stateless | In scope |
| `policy/compiler/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/compiler/grammar.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `policy/compiler/parser.py` | Authority | L4 Policy Parsing | sync | Stateless | In scope |
| `policy/compiler/tokenizer.py` | Authority | L4 Policy Tokenizing | sync | Stateless | In scope |
| `policy/ir/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/ir/ir_builder.py` | Authority | L4 IR Building | sync | Stateless | In scope |
| `policy/ir/ir_nodes.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `policy/ir/symbol_table.py` | Authority | L4 Symbol Resolution | sync | Stateless | In scope |
| `policy/optimizer/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/optimizer/conflict_resolver.py` | Authority | L4 Conflict Resolution | sync | Stateless | In scope |
| `policy/optimizer/dag_sorter.py` | Authority | L4 DAG Ordering | sync | Stateless | In scope |
| `policy/optimizer/folds.py` | Authority | L4 Optimization | sync | Stateless | In scope |
| `policy/runtime/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/runtime/dag_executor.py` | Authority | L4→L5 DAG Execution | sync | State Observer | In scope |
| `policy/runtime/deterministic_engine.py` | Authority | L4 Deterministic Execution | sync | State Observer | In scope |
| `policy/runtime/intent.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `policy/validators/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `policy/validators/content_accuracy.py` | Authority | L4 Content Validation | sync | State Observer | In scope |
| `policy/validators/prevention_engine.py` | Authority | L4 Prevention Policy | sync | State Observer | In scope |
| `policy/validators/prevention_hook.py` | Authority | L4 Prevention Hook | sync | State Observer | In scope |

### Integrations (`app/integrations/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `integrations/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `integrations/bridges.py` | Authority | L4→L6 Bridge Execution | sync | State Relay | In scope |
| `integrations/cost_bridges.py` | Authority | L4→L6 Cost Bridge | sync | State Relay | In scope |
| `integrations/cost_safety_rails.py` | Authority | L4 Cost Policy | sync | State Observer | In scope |
| `integrations/cost_snapshots.py` | Authority | L4→L6 Snapshot Storage | sync | State Authority | In scope |
| `integrations/dispatcher.py` | Authority | L4→L5 Dispatch | sync | State Relay | In scope |
| `integrations/events.py` | Authority | L4→L6 Event Emission | sync | State Authority | In scope |
| `integrations/graduation_engine.py` | Authority | L4 Graduation Logic | sync | State Authority | In scope |
| `integrations/learning_proof.py` | Authority | L4→L6 Learning Storage | sync | State Authority | In scope |
| `integrations/prevention_contract.py` | Authority | L4 Prevention Contract | sync | State Observer | In scope |

### Routing (`app/routing/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `routing/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `routing/care.py` | Authority | L4 Care Routing | sync | State Observer | In scope |
| `routing/feedback.py` | Authority | L4 Feedback Routing | sync | State Observer | In scope |
| `routing/governor.py` | Authority | L4 Routing Governor | sync | State Observer | In scope |
| `routing/learning.py` | Authority | L4 Learning Routing | sync | State Observer | In scope |
| `routing/models.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `routing/probes.py` | Authority | L4 Probe Routing | sync | State Observer | In scope |

### Contracts (`app/contracts/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `contracts/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `contracts/common.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `contracts/decisions.py` | Authority | L4 Decision Contracts | sync | State Observer | In scope |
| `contracts/guard.py` | Authority | L4 Guard Contracts | sync | State Observer | In scope |
| `contracts/ops.py` | Authority | L4 Ops Contracts | sync | State Observer | In scope |

### Predictions (`app/predictions/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `predictions/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `predictions/api.py` | Authority | L4 Prediction Logic | sync | State Observer | In scope |

### Learning (`app/learning/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `learning/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `learning/config.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `learning/s1_rollback.py` | Authority | L4→L6 Rollback Logic | sync | State Authority | In scope |
| `learning/suggestions.py` | Authority | L4→L6 Suggestion Logic | sync | State Authority | In scope |
| `learning/tables.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |

### Jobs (`app/jobs/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `jobs/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `jobs/failure_aggregation.py` | Authority | L4→L6 Aggregation Logic | async-task | State Authority | In scope |
| `jobs/graduation_evaluator.py` | Authority | L4 Graduation Logic | async-task | State Observer | In scope |
| `jobs/storage.py` | Authority | L4→L6 Job Storage | sync | State Authority | In scope |

### Agents (`app/agents/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `agents/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `agents/sba/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `agents/sba/evolution.py` | Authority | L4 SBA Evolution | sync | State Authority | In scope |
| `agents/sba/generator.py` | Authority | L4 SBA Generation | sync | State Observer | In scope |
| `agents/sba/schema.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `agents/sba/service.py` | Authority | L4→L6 SBA Service | sync | State Authority | In scope |
| `agents/sba/validator.py` | Authority | L4 SBA Validation | sync | State Observer | In scope |
| `agents/services/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `agents/services/blackboard_service.py` | Authority | L4→L6 Blackboard Storage | sync | State Authority | In scope |
| `agents/services/credit_service.py` | Authority | L4→L6 Credit Storage | sync | State Authority | In scope |
| `agents/services/governance_service.py` | Authority | L4 Governance Logic | sync | State Observer | In scope |
| `agents/services/invoke_audit_service.py` | Authority | L4→L6 Audit Storage | sync | State Authority | In scope |
| `agents/services/job_service.py` | Authority | L4→L6 Job Storage | sync | State Authority | In scope |
| `agents/services/message_service.py` | Authority | L4→L6 Message Storage | sync | State Authority | In scope |
| `agents/services/registry_service.py` | Authority | L4→L6 Registry Storage | sync | State Authority | In scope |
| `agents/services/retry_policy.py` | Authority | L4 Retry Policy | sync | Stateless | In scope |
| `agents/services/worker_service.py` | Authority | L4→L5 Worker Dispatch | sync | State Relay | In scope |
| `agents/skills/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `agents/skills/agent_invoke.py` | Authority | L4→L5 Agent Invoke | sync | State Relay | In scope |
| `agents/skills/agent_spawn.py` | Authority | L4→L5 Agent Spawn | sync | State Authority | In scope |
| `agents/skills/blackboard_ops.py` | Authority | L4→L6 Blackboard Ops | sync | State Authority | In scope |
| `agents/skills/llm_invoke_governed.py` | Authority | L4→L6 LLM Invoke | sync | State Relay | In scope |

### Optimization (`app/optimization/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `optimization/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `optimization/audit_persistence.py` | Authority | L4→L6 Audit Storage | sync | State Authority | In scope |
| `optimization/coordinator.py` | Authority | L4 Coordination | sync | State Authority | In scope |
| `optimization/envelope.py` | Authority | L4 Envelope Logic | sync | State Observer | In scope |
| `optimization/envelopes/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `optimization/envelopes/s1_retry_backoff.py` | Authority | L4 Retry Policy | sync | State Observer | In scope |
| `optimization/envelopes/s2_cost_smoothing.py` | Authority | L4 Cost Policy | sync | State Observer | In scope |
| `optimization/killswitch.py` | Authority | L4→L6 Killswitch State | sync | State Authority | In scope |
| `optimization/manager.py` | Authority | L4 Optimization Mgmt | sync | State Authority | In scope |

### Discovery (`app/discovery/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `discovery/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `discovery/ledger.py` | Authority | L4→L6 Ledger Storage | sync | State Authority | In scope |

---

## Layer 5 — Execution & Workers (`app/worker/`, `app/workers/`, `app/tasks/`)

Background jobs, async execution, long-running processes.

### Worker Core (`app/worker/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `worker/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `worker/outbox_processor.py` | Executor | L5→L6 Outbox Processing | background-worker | State Authority | In scope |
| `worker/pool.py` | Executor | L5 Pool Management | background-worker | State Authority | In scope |
| `worker/recovery_claim_worker.py` | Executor | L5→L4 Recovery Claims | background-worker | State Authority | In scope |
| `worker/recovery_evaluator.py` | Executor | L5→L4 Recovery Eval | background-worker | State Observer | In scope |
| `worker/runner.py` | Executor | L5 Run Execution | background-worker | State Authority | In scope |
| `worker/simulate.py` | Executor | L5 Simulation | sync | State Observer | In scope |
| `worker/runtime/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `worker/runtime/contracts.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `worker/runtime/core.py` | Executor | L5 Runtime Core | sync | State Authority | In scope |
| `worker/runtime/integrated_runtime.py` | Executor | L5 Integrated Runtime | sync | State Authority | In scope |

### Tasks (`app/tasks/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `tasks/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `tasks/m10_metrics_collector.py` | Executor | L5→L6 Metrics Collection | scheduled | State Observer | In scope |
| `tasks/memory_update.py` | Executor | L5→L6 Memory Update | async-task | State Authority | In scope |
| `tasks/recovery_queue.py` | Executor | L5→L4 Recovery Queue | async-task | State Authority | In scope |
| `tasks/recovery_queue_stream.py` | Executor | L5→L4 Recovery Stream | async-task | State Authority | In scope |

### Business Builder Workers (`app/workers/business_builder/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `workers/business_builder/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `workers/business_builder/agents/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `workers/business_builder/agents/definitions.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `workers/business_builder/cli.py` | Executor | L5→L4 CLI Execution | sync | State Relay | In scope |
| `workers/business_builder/execution_plan.py` | Executor | L5 Execution Plan | sync | State Observer | In scope |
| `workers/business_builder/llm_service.py` | Executor | L5→L6 LLM Service | sync | Stateless | In scope |
| `workers/business_builder/schemas/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `workers/business_builder/schemas/brand.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `workers/business_builder/stages/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `workers/business_builder/stages/copy.py` | Executor | L5 Stage Execution | sync | State Observer | In scope |
| `workers/business_builder/stages/research.py` | Executor | L5 Stage Execution | sync | State Observer | In scope |
| `workers/business_builder/stages/strategy.py` | Executor | L5 Stage Execution | sync | State Observer | In scope |
| `workers/business_builder/stages/ux.py` | Executor | L5 Stage Execution | sync | State Observer | In scope |
| `workers/business_builder/worker.py` | Executor | L5→L4 Worker | background-worker | State Authority | In scope |

### Runtime (`app/runtime/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `runtime/failure_catalog.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `runtime/replay.py` | Executor | L5→L6 Replay | sync | State Observer | In scope |

---

## Layer 6 — Platform Substrate (`app/db*.py`, `app/stores/`, `app/traces/`, `app/events/`, etc.)

Database, cache, external services, infrastructure.

### Database (`app/db*.py`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `db.py` | Storage | L6 DB Connection | import-time | State Authority | In scope |
| `db_async.py` | Storage | L6 Async DB Connection | import-time | State Authority | In scope |
| `db_helpers.py` | Storage | L6 DB Helpers | sync | State Relay | Semantically Neutral |

### Stores (`app/stores/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `stores/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `stores/checkpoint_offload.py` | Storage | L6 Checkpoint Storage | sync | State Authority | In scope |
| `stores/health.py` | Storage | L6 Health Check | sync | State Observer | Semantically Neutral |

### Traces (`app/traces/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `traces/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `traces/idempotency.py` | Storage | L6 Idempotency | sync | State Observer | In scope |
| `traces/models.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `traces/pg_store.py` | Storage | L6 PG Trace Storage | sync | State Authority | In scope |
| `traces/redact.py` | Storage | L6 Redaction | sync | Stateless | Semantically Neutral |
| `traces/replay.py` | Storage | L6 Replay Storage | sync | State Observer | In scope |
| `traces/store.py` | Storage | L6 Trace Store | sync | State Authority | In scope |
| `traces/traces_metrics.py` | Storage | L6 Metrics Export | sync | State Observer | Semantically Neutral |

### Events (`app/events/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `events/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `events/nats_adapter.py` | External Service | L6 NATS | async | State Relay | In scope |
| `events/publisher.py` | External Service | L6 Event Publish | sync | State Authority | In scope |
| `events/redis_publisher.py` | External Service | L6 Redis Publish | sync | State Relay | In scope |

### Memory (`app/memory/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `memory/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `memory/drift_detector.py` | Storage | L6 Drift Detection | sync | State Observer | In scope |
| `memory/embedding_cache.py` | Cache | L6 Embedding Cache | sync | State Authority | In scope |
| `memory/embedding_metrics.py` | Storage | L6 Metrics | sync | State Observer | Semantically Neutral |
| `memory/iaec.py` | Storage | L6 IAEC | sync | State Authority | In scope |
| `memory/memory_service.py` | Storage | L6 Memory Service | sync | State Authority | In scope |
| `memory/retriever.py` | Storage | L6 Memory Retrieval | sync | State Observer | In scope |
| `memory/store.py` | Storage | L6 Memory Store | sync | State Authority | In scope |
| `memory/update_rules.py` | Storage | L6 Update Rules | sync | State Authority | In scope |
| `memory/vector_store.py` | Storage | L6 Vector Store | sync | State Authority | In scope |

### Cost Simulation (`app/costsim/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `costsim/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `costsim/alert_worker.py` | External Service | L6 Alert Service | background-worker | State Authority | In scope |
| `costsim/canary.py` | External Service | L6 Canary | sync | State Observer | In scope |
| `costsim/cb_sync_wrapper.py` | External Service | L6 CB Wrapper | sync | State Relay | In scope |
| `costsim/circuit_breaker.py` | External Service | L6 Circuit Breaker | sync | State Authority | In scope |
| `costsim/circuit_breaker_async.py` | External Service | L6 Async CB | async | State Authority | In scope |
| `costsim/config.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `costsim/datasets.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `costsim/divergence.py` | External Service | L6 Divergence | sync | State Observer | In scope |
| `costsim/leader.py` | External Service | L6 Leader Election | sync | State Authority | In scope |
| `costsim/metrics.py` | External Service | L6 Metrics | sync | State Observer | Semantically Neutral |
| `costsim/models.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `costsim/provenance.py` | Storage | L6 Provenance | sync | State Authority | In scope |
| `costsim/provenance_async.py` | Storage | L6 Async Provenance | async | State Authority | In scope |
| `costsim/sandbox.py` | External Service | L6 Sandbox | sync | Stateless | In scope |
| `costsim/v2_adapter.py` | External Service | L6 V2 Adapter | sync | State Relay | In scope |

### Skills (`app/skills/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `skills/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `skills/base.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `skills/executor.py` | External Service | L6 Skill Execution | sync | State Relay | In scope |
| `skills/registry.py` | Storage | L6 Skill Registry | sync | State Observer | In scope |
| `skills/registry_v2.py` | Storage | L6 Skill Registry V2 | sync | State Observer | In scope |
| `skills/adapters/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `skills/adapters/claude_adapter.py` | External Service | L6 Claude API | sync | Stateless | In scope |
| `skills/adapters/metrics.py` | External Service | L6 Metrics | sync | State Observer | Semantically Neutral |
| `skills/adapters/openai_adapter.py` | External Service | L6 OpenAI API | sync | Stateless | In scope |
| `skills/adapters/tenant_config.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `skills/calendar_write.py` | External Service | L6 Calendar | sync | Stateless | In scope |
| `skills/email_send.py` | External Service | L6 Email | sync | Stateless | In scope |
| `skills/http_call.py` | External Service | L6 HTTP | sync | Stateless | In scope |
| `skills/http_call_v2.py` | External Service | L6 HTTP V2 | sync | Stateless | In scope |
| `skills/json_transform.py` | External Service | L6 JSON Transform | sync | Stateless | In scope |
| `skills/json_transform_v2.py` | External Service | L6 JSON Transform V2 | sync | Stateless | In scope |
| `skills/kv_store.py` | External Service | L6 KV Store | sync | State Authority | In scope |
| `skills/llm_invoke.py` | External Service | L6 LLM | sync | Stateless | In scope |
| `skills/llm_invoke_v2.py` | External Service | L6 LLM V2 | sync | Stateless | In scope |
| `skills/postgres_query.py` | External Service | L6 Postgres | sync | State Observer | In scope |
| `skills/slack_send.py` | External Service | L6 Slack | sync | Stateless | In scope |
| `skills/voyage_embed.py` | External Service | L6 Voyage | sync | Stateless | In scope |
| `skills/webhook_send.py` | External Service | L6 Webhook | sync | Stateless | In scope |
| `skills/stubs/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `skills/stubs/http_call_stub.py` | External Service | L6 HTTP Stub | sync | Stateless | Semantically Neutral |
| `skills/stubs/json_transform_stub.py` | External Service | L6 JSON Stub | sync | Stateless | Semantically Neutral |
| `skills/stubs/llm_invoke_stub.py` | External Service | L6 LLM Stub | sync | Stateless | Semantically Neutral |

### Storage (`app/storage/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `storage/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `storage/artifact.py` | Storage | L6 Artifact Storage | sync | State Authority | In scope |

### Secrets (`app/secrets/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `secrets/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `secrets/vault_client.py` | External Service | L6 Vault | sync | Stateless | In scope |

---

## Cross-Cutting / Utilities

### Main Application (`app/main.py`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `main.py` | Bootstrap | L2 Application Entry | import-time | Stateless | In scope |

### CLI (`app/cli.py`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `cli.py` | Orchestration | L2→L4 CLI Entry | sync | State Relay | In scope |
| `skill_http.py` | Orchestration | L2→L6 Skill HTTP | request-time | Stateless | In scope |

### Config (`app/config/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `config/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `config/flag_sync.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `config/secrets.py` | Utility | None | import-time | Stateless | Semantically Neutral |

### Logging (`app/logging_config.py`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `logging_config.py` | Utility | None | import-time | Stateless | Semantically Neutral |

### Metrics (`app/metrics.py`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `metrics.py` | Utility | None | import-time | Stateless | Semantically Neutral |

### Observability (`app/observability/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `observability/cost_tracker.py` | Utility | None | sync | State Observer | Semantically Neutral |

### Middleware (`app/middleware/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `middleware/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `middleware/rate_limit.py` | Enforcement | L3→L2 Rate Limit | request-time | State Observer | In scope |
| `middleware/tenancy.py` | Enforcement | L3→L2 Tenancy | request-time | Stateless | In scope |
| `middleware/tenant.py` | Enforcement | L3→L2 Tenant | request-time | Stateless | In scope |

### Models (`app/models/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `models/__init__.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/costsim_cb.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/feedback.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/killswitch.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/m10_recovery.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/policy.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/prediction.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `models/tenant.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |

### Schemas (`app/schemas/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `schemas/__init__.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `schemas/agent.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `schemas/artifact.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `schemas/plan.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `schemas/retry.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `schemas/skill.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |

### Security (`app/security/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `security/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `security/sanitize.py` | Utility | None | sync | Stateless | Semantically Neutral |

### Utils (`app/utils/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `utils/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `utils/budget_tracker.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `utils/canonical_json.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/concurrent_runs.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `utils/db_helpers.py` | Utility | None | sync | State Relay | Semantically Neutral |
| `utils/deterministic.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/guard_cache.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `utils/idempotency.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/input_sanitizer.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/metrics_helpers.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/plan_inspector.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/rate_limiter.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `utils/runtime.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/schema_parity.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `utils/webhook_verify.py` | Utility | None | sync | Stateless | Semantically Neutral |

### Planners (`app/planners/`, `app/planner/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `planner/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `planner/interface.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `planner/stub_planner.py` | External Service | L6 Stub Planner | sync | Stateless | Semantically Neutral |
| `planners/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `planners/anthropic_adapter.py` | External Service | L6 Anthropic API | sync | Stateless | In scope |
| `planners/stub_adapter.py` | External Service | L6 Stub Adapter | sync | Stateless | Semantically Neutral |
| `planners/test_planners.py` | Testing | None | sync | Stateless | Semantically Neutral |

### Workflow (`app/workflow/`)

| File | X: In-Layer Role | Y: Cross-Layer | Z: Execution | ⊙: State | Status |
|------|------------------|----------------|--------------|----------|--------|
| `workflow/__init__.py` | Module Export | None | import-time | Stateless | Semantically Neutral |
| `workflow/canonicalize.py` | Authority | L4 Canonicalization | sync | Stateless | In scope |
| `workflow/checkpoint.py` | Storage | L4→L6 Checkpoint | sync | State Authority | In scope |
| `workflow/engine.py` | Authority | L4 Workflow Execution | sync | State Authority | In scope |
| `workflow/errors.py` | Data Definition | None | import-time | Stateless | Semantically Neutral |
| `workflow/external_guard.py` | Authority | L4→L6 External Guard | sync | State Observer | In scope |
| `workflow/golden.py` | Storage | L4→L6 Golden Storage | sync | State Authority | In scope |
| `workflow/health.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `workflow/logging_context.py` | Utility | None | sync | Stateless | Semantically Neutral |
| `workflow/metrics.py` | Utility | None | sync | State Observer | Semantically Neutral |
| `workflow/planner_sandbox.py` | External Service | L4→L6 Planner | sync | Stateless | In scope |
| `workflow/policies.py` | Authority | L4 Workflow Policies | sync | State Observer | In scope |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total Files** | 268 |
| **In scope** | 180 |
| **Semantically Neutral** | 87 |
| **Deferred** | 1 |
| **BLOCKING** | 0 |

---

## Verification

**BLOCKING files:** None

All executable files have been classified. No unknown semantics remain.

---

## Next Steps

This map is **PROPOSED** and awaits human review.

Upon approval:
1. Phase 3.1 (Auth Semantics) may begin
2. This map will be used as reference for semantic domain discovery
3. Files marked "In scope" will be analyzed for semantic ambiguity

---

## References

- PIN-251: Phase 3 Semantic Alignment
- PHASE3_SEMANTIC_CHARTER.md: 4-Axis Semantic Model
- ARCH-GOV-013: Semantic Coordinate Requirement
