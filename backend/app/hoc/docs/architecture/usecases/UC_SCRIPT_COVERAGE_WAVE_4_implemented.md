# UC Script Coverage Wave-4: hoc_spine + integrations + agent + api_keys + apis + ops + overview — Implementation Evidence

- Date: 2026-02-12
- Scope: Classify 150 unlinked scripts across 7 domains
- Sources: `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_WAVE4_TARGET_UNLINKED_2026-02-12.txt`
- Result: 47 UC_LINKED + 103 NON_UC_SUPPORT + 0 DEPRECATED

## 1) Before/After Counts

### Before Wave-4
| Domain | Total Scripts | UC_LINKED | Unlinked | Coverage |
|--------|-------------|-----------|----------|----------|
| hoc_spine | 78 | 0 | 78 | 0.0% |
| integrations | 48 | 0 | 48 | 0.0% |
| api_keys | 9 | 0 | 9 | 0.0% |
| overview | 5 | 0 | 5 | 0.0% |
| agent | 4 | 0 | 4 | 0.0% |
| ops | 4 | 0 | 4 | 0.0% |
| apis | 2 | 0 | 2 | 0.0% |
| **Total** | **150** | **0** | **150** | **0.0%** |

### After Wave-4
| Domain | Total Scripts | UC_LINKED | NON_UC_SUPPORT | Unclassified | Coverage |
|--------|-------------|-----------|----------------|--------------|----------|
| hoc_spine | 78 | 33 | 45 | 0 | 100% classified |
| integrations | 48 | 7 | 41 | 0 | 100% classified |
| api_keys | 9 | 5 | 4 | 0 | 100% classified |
| overview | 5 | 2 | 3 | 0 | 100% classified |
| agent | 4 | 0 | 4 | 0 | 100% classified |
| ops | 4 | 0 | 4 | 0 | 100% classified |
| apis | 2 | 0 | 2 | 0 | 100% classified |
| **Total** | **150** | **47** | **103** | **0** | **100% classified** |

### Delta
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| hoc_spine UC_LINKED | 0 | 33 | +33 |
| integrations UC_LINKED | 0 | 7 | +7 |
| api_keys UC_LINKED | 0 | 5 | +5 |
| overview UC_LINKED | 0 | 2 | +2 |
| Total UC_LINKED | 0 | 47 | +47 |
| Unclassified | 150 | 0 | -150 |

## 2) Classification Breakdown

### hoc_spine Domain (78 scripts)

**UC_LINKED Handlers (21 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `orchestrator/handlers/account_handler.py` | UC-002 | Dispatches account queries to L5 engines |
| `orchestrator/handlers/agent_handler.py` | UC-001 | Dispatches agent operations during LLM runs |
| `orchestrator/handlers/analytics_config_handler.py` | UC-024 | Analytics config for anomaly detection |
| `orchestrator/handlers/analytics_handler.py` | UC-024 | Main analytics handler dispatch |
| `orchestrator/handlers/analytics_metrics_handler.py` | UC-024 | Analytics metrics dispatch |
| `orchestrator/handlers/analytics_prediction_handler.py` | UC-025 | Prediction cycle handler |
| `orchestrator/handlers/analytics_sandbox_handler.py` | UC-027 | Sandbox/CostSim handler |
| `orchestrator/handlers/analytics_snapshot_handler.py` | UC-027 | Snapshot job handler |
| `orchestrator/handlers/analytics_validation_handler.py` | UC-026 | Dataset validation handler |
| `orchestrator/handlers/api_keys_handler.py` | UC-002 | API key management during onboarding |
| `orchestrator/handlers/incidents_handler.py` | UC-MON-07 | Incident detection/management |
| `orchestrator/handlers/integration_bootstrap_handler.py` | UC-002 | Integration bootstrap during onboarding |
| `orchestrator/handlers/integrations_handler.py` | UC-002 | Integration management dispatch |
| `orchestrator/handlers/lifecycle_handler.py` | UC-002 | Lifecycle transitions dispatch |
| `orchestrator/handlers/logs_handler.py` | UC-001 | Log operations during monitoring |
| `orchestrator/handlers/mcp_handler.py` | UC-002 | MCP handler for integration setup |
| `orchestrator/handlers/orphan_recovery_handler.py` | UC-001 | Orphan run recovery |
| `orchestrator/handlers/overview_handler.py` | UC-001 | Overview dashboard operations |
| `orchestrator/handlers/policy_governance_handler.py` | UC-001 | Policy governance during runs |
| `orchestrator/handlers/run_governance_handler.py` | UC-001 | Run governance dispatch |
| `orchestrator/handlers/traces_handler.py` | UC-001 | Trace operations |

**UC_LINKED Coordinators (12 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `orchestrator/coordinators/anomaly_incident_coordinator.py` | UC-024 | Cost anomaly to incident coordination |
| `orchestrator/coordinators/canary_coordinator.py` | UC-027 | Daily canary validation for snapshots |
| `orchestrator/coordinators/evidence_coordinator.py` | UC-001 | Evidence collection during runs |
| `orchestrator/coordinators/execution_coordinator.py` | UC-001 | Run execution coordination |
| `orchestrator/coordinators/leadership_coordinator.py` | UC-024 | Leadership election for analytics |
| `orchestrator/coordinators/provenance_coordinator.py` | UC-024 | Cost provenance tracking |
| `orchestrator/coordinators/replay_coordinator.py` | UC-001 | Run replay coordination |
| `orchestrator/coordinators/run_evidence_coordinator.py` | UC-001 | Run evidence tracking |
| `orchestrator/coordinators/run_proof_coordinator.py` | UC-001 | Run proof generation |
| `orchestrator/coordinators/signal_coordinator.py` | UC-001 | Signal routing during runs |
| `orchestrator/coordinators/signal_feedback_coordinator.py` | UC-MON-04 | Signal feedback loop |
| `orchestrator/coordinators/snapshot_scheduler.py` | UC-027 | Snapshot scheduling |

**NON_UC_SUPPORT (45 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Authority infrastructure | 15 | concurrent_runs, contracts (init+engine), degraded_mode_checker, gateway_policy, guard_write_engine, lifecycle_provider, profile_policy_mode, rbac_policy, route_planes, runtime, runtime_adapter, runtime_switch, veil_policy, init |
| Consequences adapters | 3 | dispatch_metrics_adapter, export_bundle_adapter, init |
| Coordinator bridges | 14 | 10 domain bridges, domain_bridge, lessons_coordinator, 2 init files |
| Handler infrastructure | 13 | circuit_breaker, governance_audit, idempotency, integrity, killswitch, knowledge_planes, m25_integration, ops, platform, policy_approval, proxy, system handlers + init |

### api_keys Domain (9 scripts)

**UC_LINKED (5 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/api_keys_facade.py` | UC-002 | API key operations facade |
| `L5_engines/keys_engine.py` | UC-002 | Key generation/rotation logic |
| `L6_drivers/api_keys_facade_driver.py` | UC-002 | API key persistence |
| `L6_drivers/keys_driver.py` | UC-002 | Key data access |
| `adapters/customer_keys_adapter.py` | UC-002 | Customer boundary adapter |

**NON_UC_SUPPORT (4 scripts):** Package init files across L5_engines, L5_schemas, L6_drivers, adapters

### integrations Domain (48 scripts)

**UC_LINKED (7 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/connectors_facade.py` | UC-002 | Connector management facade |
| `L5_engines/cus_health_engine.py` | UC-002 | Connector health check logic |
| `L5_engines/cus_integration_engine.py` | UC-002 | Integration CRUD logic |
| `L5_engines/integrations_facade.py` | UC-002 | Main integration facade |
| `L6_drivers/bridges_driver.py` | UC-002 | Integration bridge persistence |
| `L6_drivers/cus_health_driver.py` | UC-002 | Health check persistence |
| `L6_drivers/cus_integration_driver.py` | UC-002 | Integration persistence |

**NON_UC_SUPPORT (41 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| L5 engines infra | 9 | init, credentials (init+protocol), datasources_facade, mcp_server_engine, mcp_tool_invocation_engine, prevention_contract, sql_gateway, types |
| L5 schemas | 7 | init, audit_schemas, cus_enums, cus_schemas, datasource_model, loop_events, sql_gateway_protocol |
| L6 drivers infra | 5 | init, mcp_driver, proxy_driver, sql_gateway_driver, worker_registry_driver |
| External adapters | 20 | init, cloud_functions, customer_activity, customer_keys, file_storage_base, founder_ops, gcs, lambda, mcp_server_registry, pgvector, pinecone, runtime, s3, serverless_base, slack, smtp, vector_stores_base, weaviate, webhook, workers |

### overview Domain (5 scripts)

**UC_LINKED (2 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/overview_facade.py` | UC-001 | Overview dashboard facade for run monitoring |
| `L6_drivers/overview_facade_driver.py` | UC-001 | Overview data persistence |

**NON_UC_SUPPORT (3 scripts):** Package init files across L5_engines, L5_schemas, L6_drivers

### agent Domain (4 scripts)

**NON_UC_SUPPORT (4 scripts):** init + discovery_stats_driver, platform_driver, routing_driver — agent platform infrastructure

### ops Domain (4 scripts)

**NON_UC_SUPPORT (4 scripts):** init files + cost_ops_engine, cost_read_driver — founder ops infrastructure

### apis Domain (2 scripts)

**NON_UC_SUPPORT (2 scripts):** init + keys_driver — separate API keys driver for apis domain

## 3) Fixes Applied

No architecture violations found in Wave-4 scope. All newly-classified UC_LINKED L5 engines pass purity checks (0 runtime DB imports). No code changes were required.

## 4) Test Changes

| File | Before | After | Delta |
|------|--------|-------|-------|
| `test_uc018_uc032_expansion.py` | 250 tests | 308 tests | +58 |

New test class: `TestWave4ScriptCoverage`
- 21 L4 handler existence checks for UC_LINKED handlers
- 12 L4 coordinator existence checks for UC_LINKED coordinators
- 7 L5 existence checks for UC_LINKED engines
- 6 L6 existence checks for UC_LINKED drivers
- 1 adapter existence check for UC_LINKED adapters
- 7 L5 purity checks for UC_LINKED engines
- 1 hoc_spine authority NON_UC_SUPPORT existence check
- 1 hoc_spine bridges NON_UC_SUPPORT existence check
- 1 integrations adapters NON_UC_SUPPORT existence check
- 1 total classification count validation

## 5) Gate Results

| # | Gate | Result |
|---|------|--------|
| 1 | Cross-domain validator | `status=CLEAN, count=0` |
| 2 | Layer boundaries | `CLEAN: No layer boundary violations found` |
| 3 | CI hygiene (--ci) | `All checks passed. 0 blocking violations` |
| 4 | Pairing gap detector | `wired=70, orphaned=0, direct=0` |
| 5 | UC-MON strict | `Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0` |
| 6 | Governance tests | `308 passed in 2.34s` |

**All 6 gates PASS.**

## 6) Cumulative Coverage (Wave-1 + Wave-2 + Wave-3 + Wave-4)

| Wave | Domains | Scripts Classified | UC_LINKED | NON_UC_SUPPORT |
|------|---------|-------------------|-----------|----------------|
| Wave-1 | policies, logs | 130 | 33 | 97 |
| Wave-2 | analytics, incidents, activity | 80 | 35 | 45 |
| Wave-3 | controls, account | 52 | 19 | 33 |
| Wave-4 | hoc_spine, integrations, api_keys, overview, agent, ops, apis | 150 | 47 | 103 |
| **Total** | **14 domains** | **412** | **134** | **278** |

## 7) Residual Gap List

**All Wave-4 target domains fully classified.** No remaining unlinked scripts in Wave-4 target scope.

### Cumulative classification status:
- Total HOC CUS scripts: 573 (from canonical classification CSV)
- Pre-Wave linked (before Wave-1): 42
- Wave-1 classified: 130 (33 UC_LINKED + 97 NON_UC_SUPPORT)
- Wave-2 classified: 80 (35 UC_LINKED + 45 NON_UC_SUPPORT)
- Wave-3 classified: 52 (19 UC_LINKED + 33 NON_UC_SUPPORT)
- Wave-4 classified: 150 (47 UC_LINKED + 103 NON_UC_SUPPORT)
- Total classified by waves: 412 scripts across Waves 1-4
- Current canonical totals: 176 UC_LINKED, 278 NON_UC_SUPPORT, 119 UNLINKED residual (non-Wave-4 target scope)

### Known pre-existing violations (not Wave-4 scope):
- `logs/L6_drivers/trace_store.py`: 7 L6_TRANSACTION_CONTROL violations (`.commit()` calls in L6 driver)
- These pre-date all waves and are tracked separately

## 8) Documents Updated

| Document | Change |
|----------|--------|
| `HOC_USECASE_CODE_LINKAGE.md` | Added Script Coverage Wave-4 section with classification summary, UC_LINKED expansions for hoc_spine handlers (21) and coordinators (12), api_keys (UC-002), integrations (UC-002), overview (UC-001), NON_UC_SUPPORT groups |
| `test_uc018_uc032_expansion.py` | Added `TestWave4ScriptCoverage` class (58 tests, total now 308) |
| `UC_SCRIPT_COVERAGE_WAVE_4_implemented.md` | Created (this file) |
