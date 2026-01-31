# HOC Topology V2.0.0 Migration Manifest

**Status:** MIGRATION COMPLETE — CONSTRUCTION PENDING
**Created:** 2026-01-28
**Updated:** 2026-01-28
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)
**PINs:** PIN-484 (ratification), PIN-485 (migration complete), PIN-486 (L3 absorbed)

---

## Part 1: Migration (COMPLETE)

All file moves, import updates, header updates, and cleanup are done.

### Phase 1: Create hoc_spine Structure ✅ DONE
- Created `hoc/hoc_spine/` with subdirectories
- Created `__init__.py` files

### Phase 2: Move L4_runtime → hoc_spine/orchestrator/ ✅ DONE
- governance_orchestrator.py, plan_generation_engine.py → orchestrator/
- constraint_checker.py, phase_status_invariants.py → orchestrator/
- run_governance_facade.py → orchestrator/
- transaction_coordinator.py → drivers/

### Phase 3: Move Shared Services → hoc_spine/services/ ✅ DONE
- 24 files moved: audit_store, facades (alerts, compliance, scheduler, monitors, lifecycle, retrieval), utilities (canonical_json, deterministic, dag_sorter, webhook_verify, input_sanitizer), shared services (fatigue_controller, rate_limiter, guard, cus_credential_service, lifecycle_stages_base, control_registry, retrieval_mediator, audit_durability, db_helpers, metrics_helpers, time)

### Phase 4: Move Schemas → hoc_spine/schemas/ ✅ DONE
- 9 files: rac_models, common, response, agent, artifact, plan, skill, retry, __init__

### Phase 5: Move Cross-Domain Drivers → hoc_spine/drivers/ ✅ DONE
- 13 files: cross_domain, decisions, ledger, idempotency, guard_cache, schema_parity, governance_signal_driver, dag_executor, transaction_coordinator, alert_driver, alert_emitter, worker_write_service_async, guard_write_driver

### Phase 6: Remove L3_adapters → cus/{domain}/adapters/ ✅ DONE
- L3 directories cleared from cus/ domains
- 28 files parked in _deprecated_L3/ (now absorbed — see Phase 9)

### Phase 7: Update Imports ✅ DONE
- 70+ files updated from `app.hoc.cus.general.*` → `app.hoc.hoc_spine.*`
- Zero imports to `cus.general` remain in active code
- All hoc_spine headers updated: `L4 — HOC Spine ({sublayer})`
- Scope headers updated: `domain (general)` → `hoc_spine`

### Phase 8: Abolish general Domain ✅ DONE
- `cus/general/` deleted (83 files — all duplicates of hoc_spine)
- 2 stale imports fixed (guard_write_engine, profile_policy_mode)
- Logger name updated (audit_store)

### Phase 9: Absorb L3 Adapters ✅ DONE (PIN-486)
- `_deprecated_L3/` deleted (33 files)
- 28 adapter files redistributed by intent:

| Target | Files | What |
|--------|-------|------|
| `cus/integrations/adapters/` | 13 | SDK wrappers (s3, gcs, lambda, cloud_functions, slack, smtp, webhook, pinecone, weaviate, pgvector) + base classes |
| `cus/incidents/adapters/` | 2 | customer_incidents_adapter, founder_ops_adapter |
| `cus/policies/adapters/` | 3 | customer_policies_adapter, founder_contract_review_adapter, policy_adapter |
| `cus/api_keys/adapters/` | 1 | customer_keys_adapter |
| `cus/logs/adapters/` | 1 | customer_logs_adapter |
| `cus/activity/adapters/` | 2 | customer_activity_adapter, workers_adapter |
| `cus/controls/adapters/` | 1 | customer_killswitch_adapter |
| `cus/analytics/adapters/` | 1 | v2_adapter |
| `hoc_spine/adapters/` | 2 | runtime_adapter, alert_delivery |
| `hoc_spine/consequences/adapters/` | 1 | export_bundle_adapter |
| `cus/incidents/L5_engines/` | 1 | anomaly_bridge (business logic → L5) |

- All L3 header references removed from files
- All docstring/comment L3 references updated

---

## Progress Summary

| Phase | Status | Files |
|-------|--------|-------|
| 1. Create hoc_spine | ✅ DONE | 7 dirs |
| 2. Move L4_runtime | ✅ DONE | 6 files |
| 3. Move services | ✅ DONE | 24 files |
| 4. Move schemas | ✅ DONE | 9 files |
| 5. Move drivers | ✅ DONE | 13 files |
| 6. Clear L3 dirs | ✅ DONE | 28 files parked |
| 7. Update imports | ✅ DONE | 70+ files updated |
| 8. Abolish general | ✅ DONE | 83 files deleted |
| 9. Absorb L3 | ✅ DONE | 28 files redistributed |

---

## Current State

**hoc_spine: 84 files** (including adapters, mcp/)

```
hoc_spine/
├── orchestrator/                     ← Main execution entry
│   ├── __init__.py                   ← Central re-export hub
│   ├── governance_orchestrator.py
│   ├── run_governance_facade.py
│   ├── plan_generation_engine.py
│   ├── constraint_checker.py
│   ├── phase_status_invariants.py
│   ├── execution/
│   │   └── job_executor.py
│   └── lifecycle/
│       ├── engines/ (onboarding, offboarding)
│       ├── drivers/ (execution, knowledge_plane)
│       └── pool_manager.py
├── authority/                        ← Governance & runtime decisions
│   ├── profile_policy_mode.py
│   ├── runtime.py
│   ├── runtime_switch.py
│   ├── concurrent_runs.py
│   ├── degraded_mode_checker.py
│   ├── guard_write_engine.py
│   └── contracts/
│       └── contract_engine.py
├── drivers/                          ← Cross-domain + infra DB
│   ├── cross_domain.py
│   ├── transaction_coordinator.py
│   ├── guard_write_driver.py, guard_cache.py
│   ├── alert_driver.py, alert_emitter.py
│   ├── worker_write_service_async.py
│   ├── ledger.py, idempotency.py
│   ├── schema_parity.py, governance_signal_driver.py
│   ├── decisions.py
│   └── dag_executor.py
├── services/                         ← Shared infrastructure
│   ├── audit_store.py, audit_durability.py
│   ├── time.py, db_helpers.py, metrics_helpers.py
│   ├── facades (retrieval, lifecycle, scheduler, monitors, alerts, compliance)
│   └── utilities (canonical_json, deterministic, dag_sorter, etc.)
├── schemas/                          ← Shared types
│   ├── rac_models.py, common.py, response.py
│   ├── agent.py, artifact.py, plan.py, skill.py, retry.py
│   └── __init__.py
├── adapters/                         ← System-level translation
│   ├── runtime_adapter.py
│   └── alert_delivery.py
├── consequences/                     ← Post-execution reactions
│   └── adapters/
│       └── export_bundle_adapter.py
├── frontend/projections/             ← UI projections
│   └── rollout_projection.py
└── mcp/                              ← MCP server registry
    ├── __init__.py
    └── server_registry.py
```

**Domain adapters: 24 files across 7 domains**

```
cus/
├── integrations/adapters/  (13 files) — SDK wrappers + bases
├── incidents/adapters/      (2 files) — customer + founder
├── policies/adapters/       (3 files) — customer + founder + policy
├── api_keys/adapters/       (1 file)  — customer keys
├── logs/adapters/           (1 file)  — customer logs
├── activity/adapters/       (2 files) — customer + workers
├── controls/adapters/       (1 file)  — customer killswitch
└── analytics/adapters/      (1 file)  — v2 cost adapter
```

**Deleted directories:**
- `cus/general/` — abolished (Phase 8)
- `_deprecated_L3/` — absorbed (Phase 9)

**Remaining cleanup:**
- `hoc/duplicate/` — stale duplicate directory, not active code, safe to delete

---

## Part 2: Construction (PENDING)

These are new components defined in the V2.0.0 spec that need to be built.

### C1: L2.1 Facades ⏳ PENDING
**Spec:** `hoc/api/facades/cus/{domain}.py`
- One facade per domain grouping L2 routers
- No business logic, no validation, no DB
- Domains: overview, activity, incidents, policies, controls, logs, analytics, integrations, api_keys, account

### C2: Operation Registry ⏳ PENDING
**Spec:** `hoc_spine/orchestrator/registry.py`
- Static `OPERATION_REGISTRY` mapping operation_name → (domain, engine, method, context_schema)
- Immutable at runtime, populated at startup
- No dynamic dispatch, no if/else chains

### C3: Executor ⏳ PENDING
**Spec:** `hoc_spine/orchestrator/executor.py`
- Single `execute()` entry point
- Resolves operations via registry
- Fetches cross-domain data if declared
- Builds typed context, instantiates engine, calls method

### C4: Coordinator ⏳ PENDING
**Spec:** `hoc_spine/orchestrator/coordinator.py`
- Cross-domain data fetching
- Called by executor when operation declares `cross_domain_deps`

### C5: Typed Context Schemas ⏳ PENDING
**Spec:** `cus/{domain}/L5_schemas/contexts.py`
- Per-operation frozen dataclasses
- Immutable, versioned, bounded
- L5 engines receive these instead of raw dicts

### C6: Consequences ⏳ PENDING
**Spec:** `hoc_spine/consequences/`
- `incident_creator.py` — create incidents on failure
- `audit_writer.py` — audit trail

### C7: L7 Model Reclassification ⏳ DEFERRED
- Domain-specific model design deferred to separate plan
- Current: all models in `app/models/` (shared)

---

## Import Mapping Reference

| Old Path (V1.4.0) | New Path (V2.0.0) |
|--------------------|--------------------|
| `cus.general.L4_runtime.engines` | `hoc_spine.orchestrator` |
| `cus.general.L4_runtime.facades` | `hoc_spine.orchestrator` |
| `cus.general.L4_runtime.drivers` | `hoc_spine.drivers` |
| `cus.general.L5_engines` | `hoc_spine.services` / `hoc_spine.authority` |
| `cus.general.L5_schemas` | `hoc_spine.schemas` |
| `cus.general.L6_drivers` | `hoc_spine.drivers` |
| `cus.general.L5_utils.time` | `hoc_spine.services.time` |
| `cus.general.L5_controls.drivers.runtime_switch` | `hoc_spine.authority.runtime_switch` |
| `cus.general.L5_engines.profile_policy_mode` | `hoc_spine.authority.profile_policy_mode` |
| `cus.general.L5_workflow.contracts.engines` | `hoc_spine.authority.contracts` |
| `cus.general.L5_support.CRM.engines` | `hoc_spine.orchestrator.execution` |
| `cus.general.L5_ui.engines` | `hoc_spine.frontend.projections` |
| `cus.general.L5_lifecycle` | `hoc_spine.orchestrator.lifecycle` |

---

**END OF MANIFEST**
