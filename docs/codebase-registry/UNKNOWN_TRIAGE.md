# UNKNOWN Files Triage — Research Pass

**Date:** 2025-12-30
**Status:** ✅ COMPLETE
**Purpose:** Convert UNKNOWN → KNOWN (metadata only)
**Total UNKNOWN (Start):** 183 files
**Total UNKNOWN (End):** 0 files

---

## Research Pass Summary

| Batch | Files | Status |
|-------|-------|--------|
| Batch 1: Foundational | 7 | ✅ Headers added |
| Batch 2: Security, Policy, Optimization, Routing, SBA, Adapters | 66 | ✅ Headers added |
| Batch 3: Traces, Storage, Models, Schemas, Utils, Integrations | 56 | ✅ Headers added |
| Batch 4: Auth, Workflow, Skills, Policy Runtime | 30 | ✅ Headers added |
| Batch 5: __init__.py files + Frontend (hooks, lib, types) | 27 | ✅ Headers added |
| **Total** | **186** | ✅ Complete |

### Final Inventory Metrics

```
Layer Distribution:
  L1 (Product Experience): 106 files
  L2 (Product APIs): 60 files
  L3 (Boundary Adapters): 25 files
  L4 (Domain Engines): 149 files
  L5 (Execution & Workers): 30 files
  L6 (Platform Substrate): 109 files
  L7 (Ops & Deployment): 53 files
  L8 (Catalyst/Meta): 164 files
  UNKNOWN: 0 files ← Goal achieved

Confidence Distribution:
  HIGH: 213 files (30.6%) ← +188 from start
  MEDIUM: 466 files (67.0%)
  LOW: 17 files (2.4%) ← mostly __init__.py
```

---

## Original Triage Buckets (for reference)

**Total UNKNOWN (initial):** 129 files (in backend/app only)

---

## Bucket 1: FOUNDATIONAL ENTRYPOINTS (7 files)

Core bootstrap files that everything depends on.

| File | Likely Layer | Notes |
|------|--------------|-------|
| `backend/app/main.py` | L2 | FastAPI app entry |
| `backend/app/db.py` | L6 | Database connection |
| `backend/app/db_async.py` | L6 | Async DB |
| `backend/app/db_helpers.py` | L6 | DB utilities |
| `backend/app/auth.py` | L6 | Auth bootstrap |
| `backend/app/logging_config.py` | L6 | Logging setup |
| `backend/app/metrics.py` | L6 | Prometheus setup |

---

## Bucket 2: SECURITY / AUTH / MIDDLEWARE (6 files)

Security-critical, tenant isolation, rate limiting.

| File | Likely Layer | Notes |
|------|--------------|-------|
| `backend/app/middleware/rate_limit.py` | L6 | Rate limiting |
| `backend/app/middleware/tenancy.py` | L6 | Tenant context |
| `backend/app/middleware/tenant.py` | L6 | Tenant isolation |
| `backend/app/secrets/vault_client.py` | L6 | Vault integration |
| `backend/app/config/secrets.py` | L6 | Secret loading |
| `backend/app/config/flag_sync.py` | L6 | Feature flags |

---

## Bucket 3: DOMAIN-CORE (Engines, Planners, Coordinators) (45 files)

Business logic, rules, orchestration - L4/L5.

### Policy Engine (12 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/policy/engine.py` | L4 |
| `backend/app/policy/models.py` | L4 |
| `backend/app/policy/ast/nodes.py` | L4 |
| `backend/app/policy/ast/visitors.py` | L4 |
| `backend/app/policy/compiler/grammar.py` | L4 |
| `backend/app/policy/compiler/parser.py` | L4 |
| `backend/app/policy/compiler/tokenizer.py` | L4 |
| `backend/app/policy/ir/ir_builder.py` | L4 |
| `backend/app/policy/ir/ir_nodes.py` | L4 |
| `backend/app/policy/ir/symbol_table.py` | L4 |
| `backend/app/policy/optimizer/conflict_resolver.py` | L4 |
| `backend/app/policy/optimizer/dag_sorter.py` | L4 |
| `backend/app/policy/optimizer/folds.py` | L4 |
| `backend/app/policy/validators/content_accuracy.py` | L4 |
| `backend/app/policy/validators/prevention_engine.py` | L4 |
| `backend/app/policy/validators/prevention_hook.py` | L4 |

### Optimization Envelopes (6 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/optimization/coordinator.py` | L5 |
| `backend/app/optimization/envelope.py` | L4 |
| `backend/app/optimization/manager.py` | L5 |
| `backend/app/optimization/killswitch.py` | L4 |
| `backend/app/optimization/audit_persistence.py` | L6 |
| `backend/app/optimization/envelopes/s1_retry_backoff.py` | L4 |
| `backend/app/optimization/envelopes/s2_cost_smoothing.py` | L4 |

### Learning System (4 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/learning/config.py` | L4 |
| `backend/app/learning/s1_rollback.py` | L4 |
| `backend/app/learning/suggestions.py` | L4 |
| `backend/app/learning/tables.py` | L6 |

### Routing / CARE-L (6 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/routing/care.py` | L4 |
| `backend/app/routing/feedback.py` | L4 |
| `backend/app/routing/governor.py` | L4 |
| `backend/app/routing/learning.py` | L4 |
| `backend/app/routing/models.py` | L4 |
| `backend/app/routing/probes.py` | L4 |

### SBA Agents (5 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/agents/sba/evolution.py` | L4 |
| `backend/app/agents/sba/generator.py` | L4 |
| `backend/app/agents/sba/schema.py` | L4 |
| `backend/app/agents/sba/service.py` | L4 |
| `backend/app/agents/sba/validator.py` | L4 |

### Contracts (4 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/contracts/common.py` | L4 |
| `backend/app/contracts/decisions.py` | L4 |
| `backend/app/contracts/guard.py` | L4 |
| `backend/app/contracts/ops.py` | L4 |

### Discovery (1 file)
| File | Likely Layer |
|------|--------------|
| `backend/app/discovery/ledger.py` | L4 |

### Predictions (1 file)
| File | Likely Layer |
|------|--------------|
| `backend/app/predictions/api.py` | L4 |

---

## Bucket 4: ADAPTER CANDIDATES (8 files)

Translation layers, external provider bindings.

| File | Likely Layer | Notes |
|------|--------------|-------|
| `backend/app/planners/anthropic_adapter.py` | L3 | LLM adapter |
| `backend/app/planners/stub_adapter.py` | L3 | Test stub |
| `backend/app/planner/interface.py` | L3 | Interface definition |
| `backend/app/planner/stub_planner.py` | L3 | Test stub |
| `backend/app/events/nats_adapter.py` | L3 | NATS adapter |
| `backend/app/events/publisher.py` | L3 | Event publishing |
| `backend/app/events/redis_publisher.py` | L3 | Redis pub/sub |
| `backend/app/skill_http.py` | L3 | HTTP skill adapter |

---

## Bucket 5: BACKGROUND JOBS / TASKS (8 files)

Async workers, scheduled tasks - L5.

| File | Likely Layer |
|------|--------------|
| `backend/app/jobs/failure_aggregation.py` | L5 |
| `backend/app/jobs/graduation_evaluator.py` | L5 |
| `backend/app/jobs/storage.py` | L5 |
| `backend/app/tasks/m10_metrics_collector.py` | L5 |
| `backend/app/tasks/memory_update.py` | L5 |
| `backend/app/tasks/recovery_queue.py` | L5 |
| `backend/app/tasks/recovery_queue_stream.py` | L5 |
| `backend/app/cli.py` | L7 |

---

## Bucket 6: PLATFORM / STORAGE / TRACES (18 files)

Platform substrate, data storage - L6.

### Traces (7 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/traces/idempotency.py` | L6 |
| `backend/app/traces/models.py` | L6 |
| `backend/app/traces/pg_store.py` | L6 |
| `backend/app/traces/redact.py` | L6 |
| `backend/app/traces/replay.py` | L6 |
| `backend/app/traces/store.py` | L6 |
| `backend/app/traces/traces_metrics.py` | L6 |

### Storage (3 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/storage/artifact.py` | L6 |
| `backend/app/stores/checkpoint_offload.py` | L6 |
| `backend/app/stores/health.py` | L6 |

### Models (Data) (6 files)
| File | Likely Layer |
|------|--------------|
| `backend/app/models/costsim_cb.py` | L6 |
| `backend/app/models/feedback.py` | L6 |
| `backend/app/models/killswitch.py` | L6 |
| `backend/app/models/m10_recovery.py` | L6 |
| `backend/app/models/policy.py` | L6 |
| `backend/app/models/prediction.py` | L6 |
| `backend/app/models/tenant.py` | L6 |

### Observability (1 file)
| File | Likely Layer |
|------|--------------|
| `backend/app/observability/cost_tracker.py` | L6 |

---

## Bucket 7: SCHEMAS (5 files)

Data shapes, API contracts - L6 (data definitions).

| File | Likely Layer |
|------|--------------|
| `backend/app/schemas/agent.py` | L6 |
| `backend/app/schemas/artifact.py` | L6 |
| `backend/app/schemas/plan.py` | L6 |
| `backend/app/schemas/retry.py` | L6 |
| `backend/app/schemas/skill.py` | L6 |

---

## Bucket 8: UTILITIES (17 files)

Helpers, shared logic - L6.

| File | Likely Layer |
|------|--------------|
| `backend/app/utils/budget_tracker.py` | L6 |
| `backend/app/utils/canonical_json.py` | L6 |
| `backend/app/utils/concurrent_runs.py` | L6 |
| `backend/app/utils/db_helpers.py` | L6 |
| `backend/app/utils/deterministic.py` | L6 |
| `backend/app/utils/guard_cache.py` | L6 |
| `backend/app/utils/idempotency.py` | L6 |
| `backend/app/utils/input_sanitizer.py` | L6 |
| `backend/app/utils/metrics_helpers.py` | L6 |
| `backend/app/utils/plan_inspector.py` | L6 |
| `backend/app/utils/rate_limiter.py` | L6 |
| `backend/app/utils/runtime.py` | L6 |
| `backend/app/utils/schema_parity.py` | L6 |
| `backend/app/utils/webhook_verify.py` | L6 |

---

## Bucket 9: INTEGRATIONS (9 files)

Cross-cutting integrations - L4/L6.

| File | Likely Layer |
|------|--------------|
| `backend/app/integrations/L3_adapters.py` | L4 |
| `backend/app/integrations/cost_bridges.py` | L4 |
| `backend/app/integrations/cost_safety_rails.py` | L4 |
| `backend/app/integrations/cost_snapshots.py` | L4 |
| `backend/app/integrations/dispatcher.py` | L5 |
| `backend/app/integrations/events.py` | L4 |
| `backend/app/integrations/graduation_engine.py` | L4 |
| `backend/app/integrations/learning_proof.py` | L4 |
| `backend/app/integrations/prevention_contract.py` | L4 |

---

## Bucket 10: BUSINESS BUILDER (8 files)

Product Builder domain - L4/L5.

| File | Likely Layer |
|------|--------------|
| `backend/app/workers/business_builder/agents/definitions.py` | L4 |
| `backend/app/workers/business_builder/cli.py` | L7 |
| `backend/app/workers/business_builder/execution_plan.py` | L4 |
| `backend/app/workers/business_builder/llm_service.py` | L3 |
| `backend/app/workers/business_builder/schemas/brand.py` | L6 |
| `backend/app/workers/business_builder/stages/copy.py` | L4 |
| `backend/app/workers/business_builder/stages/research.py` | L4 |
| `backend/app/workers/business_builder/stages/strategy.py` | L4 |
| `backend/app/workers/business_builder/stages/ux.py` | L4 |
| `backend/app/workers/business_builder/worker.py` | L5 |

---

## Summary by Layer (After Triage)

| Layer | Count | Categories |
|-------|-------|------------|
| L3 | 8 | Adapters |
| L4 | 54 | Domain engines, policy, routing, learning, integrations |
| L5 | 13 | Jobs, tasks, workers, coordination |
| L6 | 47 | Platform, storage, traces, models, utils, schemas |
| L7 | 2 | CLI |

**Total triaged:** 124 files (5 overlap/duplicate removed)

---

## Next Step

Add layer headers to each file in priority order:
1. Bucket 1 (Foundational) - critical path
2. Bucket 6 (Platform) - dependencies
3. Bucket 3 (Domain) - business logic
4. Remaining buckets
