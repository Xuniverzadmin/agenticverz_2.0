# Policies — Software Bible

**Domain:** policies  
**L2 Features:** 338  
**Scripts:** 73  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-08)

- Execution topology: L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5 gaps).
- L2 purity: policies L2 routes do not import L7 ORM models (`app.models.*`); they use L4-safe enum mirrors where needed.
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain policies --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.

**Strict T0 wiring fix:** policy plan generation now imports `get_planner` from `app.planners` (not `hoc.int.platform` facades) to preserve authority boundaries.

**Runtime Call Path Added:** `SandboxService.execute` is now exercised via L4 operation `policies.sandbox_execute` (handler: `hoc_spine/orchestrator/handlers/policies_sandbox_handler.py`).

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| ast | L5 | `Clause.__post_init__` | LEAF | 1 | ?:parser | ?:ir_builder | ?:visitors | ?:__init__ | L5:ir_compiler | L5:visitors | L5:compiler_parser | L5:ir_builder | L5:validator | L5:dsl_parser, deterministic_engine, intent +8 | **OVERLAP** |
| authority_checker | L5 | `OverrideAuthorityChecker.check` | CANONICAL | 5 | ?:__init__, ast, deterministic_engine +8 | **OVERLAP** |
| binding_moment_enforcer | L5 | `_check_fields_changed` | SUPERSET | 2 | ?:prevention_engine | L5:prevention_engine | ?:test_binding_moment_enforcer, prevention_engine | **OVERLAP** |
| claim_decision_engine | L5 | `is_candidate_claimable` | LEAF | 1 | — | INTERFACE |
| compiler_parser | L5 | `Parser.parse_value` | CANONICAL | 9 | dsl_parser, engine, interpreter +6 | YES |
| content_accuracy | L5 | `ContentAccuracyValidator.validate` | CANONICAL | 7 | ?:__init__ | ?:prevention_hook | L5:prevention_hook, ast, compiler_parser +15 | YES |
| cus_enforcement_engine | L5 | `CusEnforcementEngine.enforce` | CANONICAL | 9 | ?:cus_enforcement | L4:policies_handler | ?:shim_guard | YES |
| customer_policy_read_engine | L5 | `CustomerPolicyReadService.get_guardrail_detail` | CANONICAL | 3 | L3:customer_policies_adapter | L5:customer_policies_adapter, compiler_parser, dsl_parser +7 | YES |
| decorator | L5 | `governed` | CANONICAL | 1 | ?:__init__ | YES |
| degraded_mode | L5 | `exit_degraded_mode` | CANONICAL | 1 | ?:test_degraded_mode, governance_facade | YES |
| deterministic_engine | L5 | `ExecutionContext.get_variable` | CANONICAL | 4 | ?:__init__ | ?:dag_executor | ?:worker | L4:dag_executor | ?:apply | ?:mypy_zones | ?:test_m20_runtime, ast, compiler_parser +22 | YES |
| dsl_parser | L5 | `Lexer.tokenize` | CANONICAL | 3 | compiler_parser, engine, failure_mode_handler +14 | YES |
| eligibility_engine | L5 | `EligibilityEngine.evaluate` | CANONICAL | 6 | ?:__init__ | ?:contract_service | L4:contract_engine | L4:__init__ | ?:test_founder_review_invariants | ?:test_contract_invariants | ?:test_eligibility_invariants, compiler_parser, dsl_parser +12 | **OVERLAP** |
| engine | L5 | `PolicyEngine.evaluate` | CANONICAL | 19 | ?:identity_chain | ?:policy | ?:workers | ?:__init__ | ?:dag_executor | ?:checkpoint | ?:policies | ?:golden | ?:service | ?:invoke_audit_driver, compiler_parser, dsl_parser +11 | **OVERLAP** |
| failure_mode_handler | L5 | `handle_policy_failure` | CANONICAL | 3 | ?:prevention_engine | L5:prevention_engine | ?:test_failure_mode_handler, prevention_engine | YES |
| folds | L5 | `ConstantFolder.try_fold` | CANONICAL | 4 | ?:__init__ | ?:test_m20_optimizer, compiler_parser, dsl_parser +7 | YES |
| governance_facade | L5 | `GovernanceFacade.set_mode` | CANONICAL | 6 | L4:policies_handler, ast, compiler_parser +15 | YES |
| grammar | L5 | `PLangGrammar.get_action_precedence` | WRAPPER | 0 | ?:__init__ | ?:parser | ?:conflict_resolver | ?:dag_sorter | ?:ir_builder | ?:ir_nodes | ?:symbol_table | ?:visitors | ?:nodes | ?:dag_executor, nodes, optimizer_conflict_resolver | INTERFACE |
| intent | L5 | `IntentEmitter.emit` | SUPERSET | 3 | ?:recovery | ?:__init__ | ?:dag_executor | ?:deterministic_engine | L5:deterministic_engine | L2:recovery | L4:dag_executor | ?:test_m20_runtime, ast, compiler_parser +13 | YES |
| interpreter | L5 | `Interpreter.evaluate` | CANONICAL | 1 | ?:__init__ | ?:test_roundtrip | ?:test_interpreter | ?:test_replay, ast, compiler_parser +15 | **OVERLAP** |
| ir_builder | L5 | `IRBuilder.visit_rule_decl` | CANONICAL | 1 | ?:__init__ | ?:test_m20_optimizer | ?:test_m20_runtime | ?:test_m20_ir, compiler_parser, dsl_parser +9 | YES |
| ir_compiler | L5 | `IRCompiler._compile_actions` | SUPERSET | 3 | L5:interpreter | ?:__init__ | ?:interpreter | ?:test_ir_compiler | ?:test_roundtrip | ?:test_interpreter | ?:test_replay, ast, compiler_parser +13 | YES |
| ir_nodes | L5 | `IRAction.__str__` | LEAF | 2 | ?:conflict_resolver | ?:folds | ?:dag_sorter | ?:ir_builder | ?:__init__ | ?:dag_executor | ?:deterministic_engine | L6:optimizer_conflict_resolver | L5:ir_builder | L5:folds, ast, deterministic_engine +8 | INTERFACE |
| kernel | L5 | `ExecutionKernel.invoke_async` | CANONICAL | 2 | ?:__init__ | ?:decorator | ?:recovery_claim_worker | ?:main | L5:decorator | ?:aos, decorator | YES |
| ~~keys_shim~~ | ~~L5~~ | ~~`KeysReadService.__init__`~~ | **DELETED** (PIN-504 Phase 6) | — | — | — |
| kill_switch | L5 | `activate_kill_switch` | LEAF | 1 | ?:test_kill_switch | YES |
| learning_proof_engine | L5 | `PolicyRegretTracker.add_regret` | CANONICAL | 2 | L5:__init__, snapshot_engine | YES |
| lessons_engine | L5 | `LessonsLearnedEngine.detect_lesson_from_near_threshold` | CANONICAL | 2 | ?:policy_layer | ?:policy | ?:policies_facade | ?:__init__ | ?:lessons_engine | ?:run_governance_facade | ?:incident_engine | ?:main | L5:incident_engine | L4:run_governance_facade, compiler_parser, dsl_parser +7 | YES |
| limits | L5 | `Limits.is_unlimited` | WRAPPER | 0 | ?:rate_limits | ?:policy_rules_crud | ?:policies | ?:aos_cus_integrations | ?:billing_gate | ?:billing_dependencies | ?:simulate | ?:__init__ | ?:override | ?:policy_limits_crud | INTERFACE |
| limits_facade | L5 | `LimitsFacade.update_limit` | CANONICAL | 5 | L4:policies_handler, ast, compiler_parser +12 | YES |
| limits_simulation_engine | L5 | `LimitsSimulationEngine.simulate` | CANONICAL | 3 | L4:policies_handler | YES |
| llm_policy_engine | L5 | `check_safety_limits` | CANONICAL | 4 | L3:openai_adapter | L3:tenant_config | ?:tenant_config | ?:openai_adapter, compiler_parser, dsl_parser +7 | YES |
| nodes | L5 | `GovernanceMetadata.merge_with` | LEAF | 1 | ?:parser | ?:dag_sorter | ?:ir_builder | ?:visitors | ?:__init__ | ?:knowledge_plane | ?:policy_graph_engine | L5:visitors | L5:compiler_parser | L5:ir_builder, dsl_parser, ir_builder +1 | INTERFACE |
| phase_status_invariants | L5 | `PhaseStatusInvariantChecker.check` | CANONICAL | 3 | ?:__init__, ast, authority_checker +13 | **OVERLAP** |
| plan | L5 | `Plan.__post_init__` | LEAF | 3 | ?:evidence_sink | ?:execution_envelope | ?:tenant_auth | ?:guard | ?:billing_gate | ?:billing_dependencies | ?:__init__ | ?:accounts_facade | ?:tenant_service | ?:executor | **OVERLAP** |
| plan_generation_engine | L5 | `PlanGenerationEngine.generate` | CANONICAL | 2 | ?:main, compiler_parser, dsl_parser +7 | YES |
| policies_limits_query_engine | L5 | `LimitsQueryEngine.get_limit_detail` | LEAF | 1 | compiler_parser, dsl_parser, interpreter +6 | YES |
| policies_proposals_query_engine | L5 | `ProposalsQueryEngine.list_policy_requests` | CANONICAL | 3 | compiler_parser, dsl_parser, interpreter +6 | YES |
| policies_rules_query_engine | L5 | `PolicyRulesQueryEngine.list_policy_rules` | CANONICAL | 6 | compiler_parser, dsl_parser, interpreter +6 | YES |
| policy_command | L5 | `evaluate_policy` | CANONICAL | 3 | L3:policy_adapter | ?:__init__ | YES |
| policy_conflict_resolver | L5 | `resolve_policy_conflict` | CANONICAL | 5 | prevention_engine | YES |
| policy_driver | L5 | `PolicyDriver._engine` | LEAF | 1 | ?:__init__ | ?:policy_driver | L5:governance_facade | L4:policies_handler, compiler_parser, dsl_parser +10 | YES |
| policy_graph_engine | L5 | `PolicyConflictEngine.detect_conflicts` | CANONICAL | 4 | ?:policies_facade | ?:policy_proposal | L5:policy_proposal_engine | ?:policy_conflict_result | ?:policy_node_result | ?:policy_dependency_edge | ?:dependency_graph_result, ast, compiler_parser +12 | YES |
| policy_limits_engine | L5 | `PolicyLimitsService.update` | CANONICAL | 7 | L4:policies_handler, arbitrator, binding_moment_enforcer +38 | **OVERLAP** |
| policy_mapper | L5 | `MCPPolicyMapper.check_tool_invocation` | CANONICAL | 8 | ?:__init__ | ?:audit_evidence | L5:audit_evidence, ast, compiler_parser +14 | YES |
| policy_proposal_engine | L5 | `PolicyProposalEngine.check_proposal_eligibility` | CANONICAL | 3 | compiler_parser, dsl_parser, interpreter +5 | YES |
| policy_rules_engine | L5 | `PolicyRulesService.update` | CANONICAL | 6 | L4:policies_handler, arbitrator, binding_moment_enforcer +38 | **OVERLAP** |
| prevention_engine | L5 | `PreventionEngine.load_snapshot` | CANONICAL | 2 | ?:arbitrator | ?:__init__ | ?:scope_resolver | ?:step_enforcement | L7:override_authority | L7:monitor_config | L7:threshold_signal | ?:alert_emitter | ?:authority_checker | L6:arbitrator, compiler_parser, dsl_parser +7 | YES |
| prevention_hook | L5 | `PreventionHook.evaluate` | CANONICAL | 3 | ?:__init__, ast, compiler_parser +15 | **OVERLAP** |
| protection_provider | L5 | `MockAbuseProtectionProvider.check_all` | CANONICAL | 4 | compiler_parser, dsl_parser, interpreter +6 | YES |
| recovery_evaluation_engine | L5 | `FailureContext.__post_init__` | LEAF | 2 | ?:recovery_evaluator | ?:test_m10_recovery_enhanced, ast, compiler_parser +15 | **OVERLAP** |
| runtime_command | L5 | `execute_query` | CANONICAL | 5 | ?:runtime | L3:runtime_adapter | L5:runtime_adapter | L2:runtime | L4:runtime_adapter | ?:__init__ | YES |
| sandbox_engine | L5 | `SandboxService.execute` | CANONICAL | 7 | ast, compiler_parser, deterministic_engine +21 | YES |
| snapshot_engine | L5 | `PolicySnapshotRegistry.create` | CANONICAL | 1 | arbitrator, ast, binding_moment_enforcer +38 | YES |
| state | L5 | `BillingState.from_string` | LEAF | 1 | ?:gateway_config | ?:console_auth | ?:gateway_middleware | ?:rbac_middleware | ?:tier_gating | ?:tenant_auth | ?:killswitch | ?:incidents | ?:lifecycle_gate | ?:billing_gate | YES |
| tokenizer | L5 | `Tokenizer.read_operator` | CANONICAL | 5 | ?:__init__ | ?:parser | L5:compiler_parser | ?:test_m20_parser, compiler_parser, dsl_parser +6 | YES |
| validator | L5 | `PolicyValidator._check_warnings` | SUPERSET | 4 | ?:__init__ | ?:service | ?:test_validator | ?:test_roundtrip, compiler_parser, content_accuracy +9 | **OVERLAP** |
| visitors | L5 | `PrintVisitor.visit_condition_block` | CANONICAL | 2 | ?:ir_builder | ?:__init__ | L5:ir_builder | ?:test_m20_parser, compiler_parser, dsl_parser +9 | YES |
| worker_execution_command | L5 | `convert_brand_request` | CANONICAL | 1 | L3:workers_adapter | L5:workers_adapter | ?:__init__ | YES |
| arbitrator | L6 | `PolicyArbitrator.arbitrate` | CANONICAL | 7 | L7:policy_precedence | ?:test_control_action_enhancements, compiler_parser, dsl_parser +8 | YES |
| optimizer_conflict_resolver | L6 | `ConflictResolver._detect_action_conflicts` | SUPERSET | 6 | arbitrator, compiler_parser, dsl_parser +7 | YES |
| policy_engine_driver | L6 | `PolicyEngineDriver.fetch_violations` | CANONICAL | 5 | L5:engine, compiler_parser, dsl_parser +9 | YES |
| policy_graph_driver | L6 | `PolicyGraphDriver.fetch_active_limits` | INTERNAL | 0 | L5:policy_graph_engine, compiler_parser, dsl_parser +8 | YES |
| policy_proposal_read_driver | L6 | `PolicyProposalReadDriver.fetch_proposals` | CANONICAL | 2 | L6:__init__ | L5:policy_proposal_engine, compiler_parser, dsl_parser +9 | **OVERLAP** |
| policy_proposal_write_driver | L6 | `PolicyProposalWriteDriver.create_policy_rule` | INTERNAL | 0 | L6:__init__ | L5:policy_proposal_engine, compiler_parser, dsl_parser +7 | YES |
| policy_read_driver | L6 | `PolicyReadDriver.get_guardrail_by_id` | INTERNAL | 1 | L6:__init__ | L5:customer_policy_read_engine, compiler_parser, customer_policy_read_engine +8 | YES |
| policy_rules_driver | L6 | `PolicyRulesDriver.fetch_rule_by_id` | INTERNAL | 0 | L5:policy_rules_engine, compiler_parser, dsl_parser +10 | YES |
| policy_rules_read_driver | L6 | `PolicyRulesReadDriver.fetch_policy_rules` | CANONICAL | 12 | L6:__init__ | L5:policies_rules_query_engine, compiler_parser, dsl_parser +8 | YES |
| proposals_read_driver | L6 | `ProposalsReadDriver.fetch_proposals` | CANONICAL | 4 | L6:__init__ | L5:policies_proposals_query_engine, compiler_parser, dsl_parser +8 | **OVERLAP** |
| recovery_matcher | L6 | `RecoveryMatcher.suggest` | CANONICAL | 3 | ?:recovery | ?:workers | ?:worker | ?:recovery_matcher | ?:__init__ | ?:recovery_evaluation_engine | L5:recovery_evaluation_engine | L2:recovery | L2:workers | ?:check_priority5_intent, compiler_parser, dsl_parser +8 | YES |
| recovery_write_driver | L6 | `RecoveryWriteService.get_candidate_by_idempotency_key` | ENTRY | 0 | L2:recovery | L2:recovery_ingest, compiler_parser, dsl_parser +7 | YES |
| scope_resolver | L6 | `ScopeResolver.resolve_applicable_policies` | CANONICAL | 6 | L7:policy_scope | ?:test_export_scope_resolution | ?:test_scope_selector, compiler_parser, dsl_parser +7 | YES |
| symbol_table | L6 | `SymbolTable.lookup_rule` | CANONICAL | 5 | ?:ir_builder | ?:__init__ | L5:ir_builder | ?:test_m20_ir, compiler_parser, dsl_parser +8 | YES |
| policies_facade_driver | L6 | `PoliciesFacadeDriver.fetch_policy_rules` | CANONICAL | 7 | L5:policies_facade | YES |
| cus_enforcement_driver | L6 | `CusEnforcementDriver.fetch_integrations` | CANONICAL | 5 | L5:cus_enforcement_engine | YES |
| limits_simulation_driver | L6 | `LimitsSimulationDriver.fetch_tenant_quotas` | CANONICAL | 3 | L5:limits_simulation_engine | YES |

## Uncalled Functions

Functions with no internal or external callers detected.
May be: unused code, missing wiring, or entry points not yet traced.

- `claim_decision_engine.determine_claim_status`
- `claim_decision_engine.get_result_confidence`
- `claim_decision_engine.is_candidate_claimable`
- `compiler_parser.Parser.current`
- `compiler_parser.Parser.from_source`
- `dsl_parser.Parser.current`
- `dsl_parser.parse`
- `dsl_parser.parse_condition`
- `keys_shim.KeysReadService.get_key`
- `keys_shim.KeysReadService.get_key_usage_today`
- `keys_shim.KeysReadService.list_keys`
- `keys_shim.KeysWriteService.freeze_key`
- `keys_shim.KeysWriteService.unfreeze_key`
- `keys_shim.get_keys_read_service`
- `keys_shim.get_keys_write_service`
- `optimizer_conflict_resolver.ConflictResolver.resolve`
- `policies_limits_query_engine.LimitsQueryEngine.get_limit_detail`
- `policies_limits_query_engine.LimitsQueryEngine.list_budgets`
- `policies_limits_query_engine.LimitsQueryEngine.list_limits`
- `policies_limits_query_engine.get_limits_query_engine`
- `policies_proposals_query_engine.ProposalsQueryEngine.count_drafts`
- `policies_proposals_query_engine.ProposalsQueryEngine.get_policy_request_detail`
- `policies_proposals_query_engine.ProposalsQueryEngine.list_policy_requests`
- `policies_proposals_query_engine.get_proposals_query_engine`
- `policies_rules_query_engine.PolicyRulesQueryEngine.count_rules`
- `policies_rules_query_engine.PolicyRulesQueryEngine.get_policy_rule_detail`
- `policies_rules_query_engine.PolicyRulesQueryEngine.list_policy_rules`
- `policies_rules_query_engine.get_policy_rules_query_engine`
- `policy_conflict_resolver.create_conflict_log`
- `policy_conflict_resolver.is_more_restrictive`
- `policy_proposal_engine.check_proposal_eligibility`
- `policy_proposal_engine.create_policy_proposal`
- `policy_proposal_engine.generate_default_rule`
- `policy_proposal_engine.get_proposal_summary`
- `policy_proposal_engine.review_policy_proposal`
- `protection_provider.AbuseProtectionProvider.check_all`
- `protection_provider.MockAbuseProtectionProvider.add_cost`
- `protection_provider.MockAbuseProtectionProvider.check_all`
- `protection_provider.MockAbuseProtectionProvider.reset_rate_limits`
- `protection_provider.get_protection_provider`
- `protection_provider.set_protection_provider`
- `sandbox_engine.SandboxService.define_policy`
- `sandbox_engine.SandboxService.get_execution_records`
- `sandbox_engine.SandboxService.get_execution_stats`
- `sandbox_engine.SandboxService.get_policy`
- `sandbox_engine.SandboxService.list_policies`
- `snapshot_engine.PolicySnapshotRegistry.archive`
- `snapshot_engine.PolicySnapshotRegistry.attempt_modify`
- `snapshot_engine.PolicySnapshotRegistry.clear_tenant`
- `snapshot_engine.PolicySnapshotRegistry.delete`
- `snapshot_engine.PolicySnapshotRegistry.get_by_version`
- `snapshot_engine.PolicySnapshotRegistry.get_statistics`
- `snapshot_engine.create_policy_snapshot`
- `snapshot_engine.get_active_snapshot`
- `snapshot_engine.get_policy_snapshot`
- `snapshot_engine.get_snapshot_history`
- `snapshot_engine.verify_snapshot`

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `ast` — canonical: `Clause.__post_init__` (LEAF)
- `authority_checker` — canonical: `OverrideAuthorityChecker.check` (CANONICAL)
- `binding_moment_enforcer` — canonical: `_check_fields_changed` (SUPERSET)
- `eligibility_engine` — canonical: `EligibilityEngine.evaluate` (CANONICAL)
- `engine` — canonical: `PolicyEngine.evaluate` (CANONICAL)
- `interpreter` — canonical: `Interpreter.evaluate` (CANONICAL)
- `ir_nodes` — canonical: `IRAction.__str__` (LEAF)
- `keys_shim` — canonical: `KeysReadService.__init__` (WRAPPER)
- `phase_status_invariants` — canonical: `PhaseStatusInvariantChecker.check` (CANONICAL)
- `plan` — canonical: `Plan.__post_init__` (LEAF)
- `policy_limits_engine` — canonical: `PolicyLimitsService.update` (CANONICAL)
- `policy_proposal_read_driver` — canonical: `PolicyProposalReadDriver.fetch_proposals` (CANONICAL)
- `policy_rules_engine` — canonical: `PolicyRulesService.update` (CANONICAL)
- `prevention_hook` — canonical: `PreventionHook.evaluate` (CANONICAL)
- `proposals_read_driver` — canonical: `ProposalsReadDriver.fetch_proposals` (CANONICAL)
- `recovery_evaluation_engine` — canonical: `FailureContext.__post_init__` (LEAF)
- `validator` — canonical: `PolicyValidator._check_warnings` (SUPERSET)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 338 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### DELETE /cooldowns/{agent_id}
```
L2:policy_layer.clear_cooldowns → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /jobs/{job_id}
```
L2:scheduler.delete_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /limits/{limit_id}
```
L2:policy_limits_crud.delete_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /overrides/{override_id}
```
L2:override.cancel_override → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /routes/{route_id}
```
L2:alerts.delete_route → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /rules/{rule_id}
```
L2:alerts.delete_rule → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /runs/{run_id}
```
L2:workers.delete_run → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /users/{user_id}
```
L2:aos_accounts.remove_user → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /{connector_id}
```
L2:connectors.delete_connector → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /{integration_id}
```
L2:aos_cus_integrations.delete_integration → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /{monitor_id}
```
L2:monitors.delete_monitor → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### DELETE /{source_id}
```
L2:datasources.delete_source → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /_status
```
L2:analytics.get_analytics_status → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /active
```
L2:policy.get_active_policies → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /active/{policy_id}
```
L2:policy.get_active_policy_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /agents
```
L2:lifecycle.list_agents → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /agents/{agent_id}
```
L2:lifecycle.get_agent → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /anomalies
```
L2:detection.list_anomalies → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /anomalies/{anomaly_id}
```
L2:detection.get_anomaly → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit
```
L2:logs.list_audit_entries → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit
```
L2:rbac_api.query_audit_logs → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit/access
```
L2:logs.get_audit_access → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit/authorization
```
L2:logs.get_audit_authorization → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit/exports
```
L2:logs.get_audit_exports → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit/identity
```
L2:logs.get_audit_identity → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit/integrity
```
L2:logs.get_audit_integrity → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /audit/{entry_id}
```
L2:logs.get_audit_entry → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /billing
```
L2:aos_accounts.get_billing_summary → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /billing/invoices
```
L2:aos_accounts.get_billing_invoices → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /boot-status
```
L2:governance.get_boot_status → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /budgets
```
L2:policies.list_budget_definitions → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /capabilities
```
L2:runtime.get_capabilities → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /chains
```
L2:evidence.list_chains → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /chains/{chain_id}
```
L2:evidence.get_chain → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /chains/{chain_id}/verify
```
L2:evidence.verify_chain → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /channels
```
L2:notifications.list_channels → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /checkpoints
```
L2:M25_integrations.list_pending_checkpoints → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /checkpoints/{checkpoint_id}
```
L2:M25_integrations.get_checkpoint → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /conflicts
```
L2:governance.list_conflicts → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /conflicts
```
L2:policies.list_policy_conflicts → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /conflicts
```
L2:policy_layer.list_conflicts → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /cooldowns
```
L2:policy_layer.list_active_cooldowns → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /declaration/{declaration_id}
```
L2:customer_visibility.get_declaration → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /dependencies
```
L2:policies.get_policy_dependencies → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /dependencies
```
L2:policy_layer.get_dependency_graph → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /dependencies/dag/validate
```
L2:policy_layer.validate_dependency_dag → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /dependencies/evaluation-order
```
L2:policy_layer.get_evaluation_order → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /download/{export_id}
```
L2:status_history.download_export → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /entity/{entity_type}/{entity_id}
```
L2:status_history.get_entity_history → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /ethical-constraints
```
L2:policy_layer.list_ethical_constraints → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /events/{run_id}
```
L2:workers.get_run_events → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /evidence
```
L2:retrieval.list_evidence → L4:RetrievalFacade | get_retrieval_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /evidence/{evidence_id}
```
L2:retrieval.get_evidence → L4:RetrievalFacade | get_retrieval_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /exports
```
L2:evidence.list_exports → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /exports/{export_id}
```
L2:evidence.get_export → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /graduation
```
L2:M25_integrations.get_graduation_status → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /guardrails/{guardrail_id}
```
L2:guard_policies.get_guardrail_detail → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /health
```
L2:analytics.analytics_health → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /health
```
L2:workers.worker_health → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /history
```
L2:alerts.list_history → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /history/{event_id}
```
L2:alerts.get_event → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /incidents
```
L2:guard.list_incidents → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /incidents/{incident_id}
```
L2:guard.get_incident_detail → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /incidents/{incident_id}/narrative
```
L2:guard.get_customer_incident_narrative → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /incidents/{incident_id}/timeline
```
L2:guard.get_decision_timeline → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /info
```
L2:rbac_api.get_policy_info → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /invitations
```
L2:aos_accounts.list_invitations → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /jobs
```
L2:scheduler.list_jobs → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /jobs/{job_id}
```
L2:scheduler.get_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /jobs/{job_id}/runs
```
L2:scheduler.list_job_runs → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /keys
```
L2:guard.list_api_keys → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons
```
L2:policies.list_lessons → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons
```
L2:policy.get_policy_lessons → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons
```
L2:policy_layer.list_lessons → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons/stats
```
L2:policies.get_lesson_stats → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons/stats
```
L2:policy_layer.get_lesson_stats → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons/{lesson_id}
```
L2:policies.get_lesson_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons/{lesson_id}
```
L2:policy.get_policy_lesson_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /lessons/{lesson_id}
```
L2:policy_layer.get_lesson → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /library
```
L2:policy.get_policy_library → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /limits
```
L2:policies.list_limits → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /limits/{limit_id}
```
L2:policies.get_limit_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /limits/{limit_id}/evidence
```
L2:policies.get_limit_evidence → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /limits/{limit_id}/params
```
L2:policy_limits_crud.get_threshold_params → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /llm-runs
```
L2:logs.list_llm_run_records → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /llm-runs/{run_id}/envelope
```
L2:logs.get_llm_run_envelope → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /llm-runs/{run_id}/export
```
L2:logs.get_llm_run_export → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /llm-runs/{run_id}/governance
```
L2:logs.get_llm_run_governance → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /llm-runs/{run_id}/replay
```
L2:logs.get_llm_run_replay → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /llm-runs/{run_id}/trace
```
L2:logs.get_llm_run_trace → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /loop/{incident_id}
```
L2:M25_integrations.get_loop_status → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /loop/{incident_id}/narrative
```
L2:M25_integrations.get_loop_narrative → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /loop/{incident_id}/stages
```
L2:M25_integrations.get_loop_stages → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /loop/{incident_id}/stream
```
L2:M25_integrations.stream_loop_status → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /matrix
```
L2:rbac_api.get_permission_matrix → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /metrics
```
L2:policies.get_policy_metrics → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /metrics
```
L2:policy_layer.get_policy_metrics → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /outcome/{run_id}
```
L2:customer_visibility.get_outcome_reconciliation → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /overrides
```
L2:override.list_overrides → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /overrides/{override_id}
```
L2:override.get_override → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /planes
```
L2:retrieval.list_planes → L4:RetrievalFacade | get_retrieval_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /planes/{plane_id}
```
L2:retrieval.get_plane → L4:RetrievalFacade | get_retrieval_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /preferences
```
L2:notifications.get_preferences → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /profile
```
L2:aos_accounts.get_profile → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /projects
```
L2:aos_accounts.list_projects → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /projects/{project_id}
```
L2:aos_accounts.get_project_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /reports
```
L2:compliance.list_reports → L4:ComplianceFacade | get_compliance_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /reports/{report_id}
```
L2:compliance.get_report → L4:ComplianceFacade | get_compliance_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /requests
```
L2:policies.list_policy_requests → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /requests
```
L2:policy.list_approval_requests → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /requests/{request_id}
```
L2:policy.get_approval_request → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /resource-contract/{resource_id}
```
L2:runtime.get_resource_contract → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /risk-ceilings
```
L2:policy_layer.list_risk_ceilings → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /risk-ceilings/{ceiling_id}
```
L2:policy_layer.get_risk_ceiling → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /routes
```
L2:alerts.list_routes → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /routes/{route_id}
```
L2:alerts.get_route → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules
```
L2:alerts.list_rules → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules
```
L2:compliance.list_rules → L4:ComplianceFacade | get_compliance_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules
```
L2:policies.list_policy_rules → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules/{rule_id}
```
L2:alerts.get_rule → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules/{rule_id}
```
L2:compliance.get_rule → L4:ComplianceFacade | get_compliance_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules/{rule_id}
```
L2:policies.get_policy_rule_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /rules/{rule_id}/evidence
```
L2:policies.get_rule_evidence → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /runs
```
L2:lifecycle.list_runs → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /runs
```
L2:workers.list_runs → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /runs/{run_id}
```
L2:lifecycle.get_run → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /runs/{run_id}
```
L2:scheduler.get_run → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /runs/{run_id}
```
L2:workers.get_run → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /safety-rules
```
L2:policy_layer.list_safety_rules → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /schema/brand
```
L2:workers.get_brand_schema → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /schema/run
```
L2:workers.get_run_schema → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /settings
```
L2:guard.get_settings → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /skills
```
L2:runtime.list_available_skills → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /skills/{skill_id}
```
L2:runtime.describe_skill → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /snapshot/today
```
L2:guard.get_today_snapshot → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /state
```
L2:governance.get_governance_state → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /state
```
L2:policies.get_policy_state → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /state
```
L2:policy_layer.get_policy_state → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /statistics/cost
```
L2:analytics.get_cost_statistics → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /statistics/cost/export.csv
```
L2:analytics.export_cost_csv → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /statistics/cost/export.json
```
L2:analytics.export_cost_json → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /statistics/usage
```
L2:analytics.get_usage_statistics → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /statistics/usage/export.csv
```
L2:analytics.export_usage_csv → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /statistics/usage/export.json
```
L2:analytics.export_usage_json → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /stats
```
L2:M25_integrations.get_integration_stats → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /stats
```
L2:datasources.get_statistics → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /stats
```
L2:status_history.get_stats → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /stats/summary
```
L2:policy_proposals.get_proposal_stats → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /status
```
L2:compliance.get_compliance_status → L4:ComplianceFacade | get_compliance_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /status
```
L2:controls.get_status → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /status
```
L2:cus_enforcement.get_enforcement_status → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /status
```
L2:detection.get_detection_status → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /status
```
L2:guard.get_guard_status → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /status
```
L2:monitors.get_status → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /stream/{run_id}
```
L2:workers.stream_run_events → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /summary
```
L2:lifecycle.get_summary → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /support
```
L2:aos_accounts.get_support_contact → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /support/tickets
```
L2:aos_accounts.list_support_tickets → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /system
```
L2:logs.list_system_records → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /system/audit
```
L2:logs.get_system_audit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /system/{run_id}/events
```
L2:logs.get_system_events → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /system/{run_id}/replay
```
L2:logs.get_system_replay → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /system/{run_id}/snapshot
```
L2:logs.get_system_snapshot → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /system/{run_id}/telemetry
```
L2:logs.get_system_telemetry → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /temporal-metrics/storage-stats
```
L2:policy_layer.get_temporal_storage_stats → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /temporal-policies
```
L2:policy_layer.list_temporal_policies → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /temporal-policies/{policy_id}/utilization
```
L2:policy_layer.get_temporal_utilization → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /thresholds
```
L2:policy.get_policy_thresholds → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /thresholds/{threshold_id}
```
L2:policy.get_policy_threshold_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /timeline/{incident_id}
```
L2:M25_integrations.get_prevention_timeline → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /traces
```
L2:runtime.list_traces → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /traces/{run_id}
```
L2:runtime.get_trace → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /usage
```
L2:rate_limits.get_usage → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /users
```
L2:aos_accounts.list_users → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /users
```
L2:aos_accounts.list_tenant_users → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /users/{user_id}
```
L2:aos_accounts.get_user_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /versions
```
L2:policy_layer.list_policy_versions → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /versions/current
```
L2:policy_layer.get_current_version → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /versions/{version_id}/provenance
```
L2:policy_layer.get_version_provenance → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /violations
```
L2:policies.list_policy_violations → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /violations
```
L2:policy.get_policy_violations_v2 → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /violations
```
L2:policy_layer.list_violations → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /violations/{violation_id}
```
L2:policy.get_policy_violation_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /violations/{violation_id}
```
L2:policy_layer.get_violation → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{connector_id}
```
L2:connectors.get_connector → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{control_id}
```
L2:controls.get_control → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{incident_id}/explain/{item_id}
```
L2:replay.explain_replay_item → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{incident_id}/slice
```
L2:replay.get_replay_slice → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{incident_id}/summary
```
L2:replay.get_incident_summary → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{incident_id}/timeline
```
L2:replay.get_replay_timeline → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{integration_id}
```
L2:aos_cus_integrations.get_integration → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{integration_id}/health
```
L2:aos_cus_integrations.get_integration_health → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{integration_id}/limits
```
L2:aos_cus_integrations.get_integration_limits → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{key_id}
```
L2:aos_api_key.get_api_key_detail → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{limit_id}
```
L2:rate_limits.get_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{monitor_id}
```
L2:monitors.get_monitor → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{monitor_id}/history
```
L2:monitors.get_history → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{notification_id}
```
L2:notifications.get_notification → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{proposal_id}
```
L2:policy_proposals.get_proposal → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{proposal_id}/versions
```
L2:policy_proposals.list_proposal_versions → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### GET /{source_id}
```
L2:datasources.get_source → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PATCH /risk-ceilings/{ceiling_id}
```
L2:policy_layer.update_risk_ceiling → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PATCH /safety-rules/{rule_id}
```
L2:policy_layer.update_safety_rule → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /access
```
L2:retrieval.access_data → L4:RetrievalFacade | get_retrieval_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /acknowledge
```
L2:customer_visibility.acknowledge_declaration → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /agents
```
L2:lifecycle.create_agent → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /agents/{agent_id}/start
```
L2:lifecycle.start_agent → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /agents/{agent_id}/stop
```
L2:lifecycle.stop_agent → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /agents/{agent_id}/terminate
```
L2:lifecycle.terminate_agent → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /anomalies/{anomaly_id}/acknowledge
```
L2:detection.acknowledge_anomaly → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /anomalies/{anomaly_id}/resolve
```
L2:detection.resolve_anomaly → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /audit/cleanup
```
L2:rbac_api.cleanup_audit_logs → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /batch
```
L2:cus_enforcement.batch_enforcement_check → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /chains
```
L2:evidence.create_chain → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /chains/{chain_id}/evidence
```
L2:evidence.add_evidence → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /check
```
L2:cus_enforcement.check_enforcement → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /check
```
L2:rate_limits.check_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /checkpoints/{checkpoint_id}/resolve
```
L2:M25_integrations.resolve_checkpoint → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /conflicts/{conflict_id}/resolve
```
L2:policy_layer.resolve_conflict → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /dependencies/add
```
L2:policy_layer.add_dependency_with_dag_check → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /eval
```
L2:policy.evaluate_policy → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /evaluate
```
L2:policy_layer.evaluate_action → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /evaluate/batch
```
L2:policy_layer.evaluate_batch → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /evaluate/context-aware
```
L2:policy_layer.evaluate_with_context → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /export
```
L2:evidence.create_export → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /export
```
L2:status_history.create_export → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /graduation/re-evaluate
```
L2:M25_integrations.trigger_graduation_re_evaluation → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /graduation/record-view
```
L2:M25_integrations.record_timeline_view → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /graduation/simulate/prevention
```
L2:M25_integrations.simulate_prevention → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /graduation/simulate/regret
```
L2:M25_integrations.simulate_regret → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /graduation/simulate/timeline-view
```
L2:M25_integrations.simulate_timeline_view → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /history/{event_id}/acknowledge
```
L2:alerts.acknowledge_event → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /history/{event_id}/resolve
```
L2:alerts.resolve_event → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /incidents/search
```
L2:guard.search_incidents → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /incidents/{incident_id}/acknowledge
```
L2:guard.acknowledge_incident → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /incidents/{incident_id}/export
```
L2:guard.export_incident_evidence → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /incidents/{incident_id}/resolve
```
L2:guard.resolve_incident → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /invitations/{invitation_id}/accept
```
L2:aos_accounts.accept_invitation → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /jobs
```
L2:scheduler.create_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /jobs/{job_id}/pause
```
L2:scheduler.pause_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /jobs/{job_id}/resume
```
L2:scheduler.resume_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /jobs/{job_id}/trigger
```
L2:scheduler.trigger_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /keys/{key_id}/freeze
```
L2:guard.freeze_api_key → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /keys/{key_id}/unfreeze
```
L2:guard.unfreeze_api_key → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /kill-switch
```
L2:governance.toggle_kill_switch → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /killswitch/activate
```
L2:guard.activate_killswitch → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /killswitch/deactivate
```
L2:guard.deactivate_killswitch → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /lessons/{lesson_id}/convert
```
L2:policy_layer.convert_lesson_to_draft → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /lessons/{lesson_id}/defer
```
L2:policy_layer.defer_lesson → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /lessons/{lesson_id}/dismiss
```
L2:policy_layer.dismiss_lesson → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /limits
```
L2:policy_limits_crud.create_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /loop/{incident_id}/retry
```
L2:M25_integrations.retry_loop_stage → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /loop/{incident_id}/revert
```
L2:M25_integrations.revert_loop → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /mode
```
L2:governance.set_governance_mode → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /onboarding/verify
```
L2:guard.onboarding_verify → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /overrides
```
L2:override.create_override → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /planes
```
L2:retrieval.register_plane → L4:RetrievalFacade | get_retrieval_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /pre-run
```
L2:customer_visibility.get_pre_run_declaration → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /query
```
L2:runtime.query_runtime → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /reload
```
L2:policy_layer.reload_policies → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /reload
```
L2:rbac_api.reload_policies → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /replay
```
L2:workers.replay_execution_endpoint → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /replay/{call_id}
```
L2:guard.replay_call → L4:GuardWriteDriver | OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /replay/{run_id}
```
L2:runtime.replay_run → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /requests
```
L2:policy.create_approval_request → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /requests/{request_id}/approve
```
L2:policy.approve_request → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /requests/{request_id}/reject
```
L2:policy.reject_request → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /resolve-conflict
```
L2:governance.resolve_conflict → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /risk-ceilings/{ceiling_id}/reset
```
L2:policy_layer.reset_risk_ceiling → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /routes
```
L2:alerts.create_route → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /rules
```
L2:alerts.create_rule → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /rules
```
L2:policy_rules_crud.create_rule → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /run
```
L2:detection.run_detection → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /run
```
L2:workers.run_worker → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /run-streaming
```
L2:workers.run_worker_streaming → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /runs
```
L2:lifecycle.create_run → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /runs/{run_id}/cancel
```
L2:lifecycle.cancel_run → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /runs/{run_id}/pause
```
L2:lifecycle.pause_run → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /runs/{run_id}/resume
```
L2:lifecycle.resume_run → L4:LifecycleFacade | get_lifecycle_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /runs/{run_id}/retry
```
L2:workers.retry_run → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /simulate
```
L2:policy_layer.simulate_evaluation → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /simulate
```
L2:runtime.simulate_plan → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /simulate
```
L2:simulate.simulate_execution → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /support/tickets
```
L2:aos_accounts.create_support_ticket → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /temporal-metrics/prune
```
L2:policy_layer.prune_temporal_metrics → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /temporal-policies
```
L2:policy_layer.create_temporal_policy → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /users/invite
```
L2:aos_accounts.invite_user → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /validate-brand
```
L2:workers.validate_brand → L4:WorkerWriteServiceAsync → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /verify
```
L2:compliance.verify_compliance → L4:ComplianceFacade | get_compliance_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /versions
```
L2:policy_layer.create_policy_version → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /versions/activate
```
L2:policy_layer.activate_policy_version → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /versions/rollback
```
L2:policy_layer.rollback_to_version → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /versions/{version_id}/check
```
L2:policy_layer.check_version_integrity → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /violations/{violation_id}/acknowledge
```
L2:policy_layer.acknowledge_violation → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{connector_id}/test
```
L2:connectors.test_connector → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{control_id}/disable
```
L2:controls.disable_control → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{control_id}/enable
```
L2:controls.enable_control → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{integration_id}/disable
```
L2:aos_cus_integrations.disable_integration → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{integration_id}/enable
```
L2:aos_cus_integrations.enable_integration → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{integration_id}/test
```
L2:aos_cus_integrations.test_integration_credentials → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{limit_id}/reset
```
L2:rate_limits.reset_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{monitor_id}/check
```
L2:monitors.run_check → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{notification_id}/read
```
L2:notifications.mark_as_read → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{proposal_id}/approve
```
L2:policy_proposals.approve_proposal → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{proposal_id}/reject
```
L2:policy_proposals.reject_proposal → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{source_id}/activate
```
L2:datasources.activate_source → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{source_id}/deactivate
```
L2:datasources.deactivate_source → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### POST /{source_id}/test
```
L2:datasources.test_connection → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /jobs/{job_id}
```
L2:scheduler.update_job → L4:SchedulerFacade | get_scheduler_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /limits/{limit_id}
```
L2:policy_limits_crud.update_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /limits/{limit_id}/params
```
L2:policy_limits_crud.set_threshold_params → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /preferences
```
L2:notifications.update_preferences → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /profile
```
L2:aos_accounts.update_profile → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /rules/{rule_id}
```
L2:alerts.update_rule → L4:AlertsFacade | get_alerts_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /rules/{rule_id}
```
L2:policy_rules_crud.update_rule → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /users/{user_id}/role
```
L2:aos_accounts.update_user_role → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /{connector_id}
```
L2:connectors.update_connector → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /{control_id}
```
L2:controls.update_control → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /{integration_id}
```
L2:aos_cus_integrations.update_integration → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /{limit_id}
```
L2:rate_limits.update_limit → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /{monitor_id}
```
L2:monitors.update_monitor → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### PUT /{source_id}
```
L2:datasources.update_source → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### create_integration
```
L2:aos_cus_integrations.create_integration → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### create_monitor
```
L2:monitors.create_monitor → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### create_source
```
L2:datasources.create_source → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### get_policy_constraints
```
L2:guard_policies.get_policy_constraints → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_api_keys
```
L2:aos_api_key.list_api_keys → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_connectors
```
L2:connectors.list_connectors → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_controls
```
L2:controls.list_controls → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_integrations
```
L2:aos_cus_integrations.list_integrations → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_limits
```
L2:rate_limits.list_limits → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_monitors
```
L2:monitors.list_monitors → L4:MonitorsFacade | get_monitors_facade → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_notifications
```
L2:notifications.list_notifications → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_proposals
```
L2:policy_proposals.list_proposals → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### list_sources
```
L2:datasources.list_sources → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### query_status_history
```
L2:status_history.query_status_history → L4:policies_handler → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### register_connector
```
L2:connectors.register_connector → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

#### send_notification
```
L2:notifications.send_notification → L4:OperationContext | get_operation_registry → L6:optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `BaseVisitor.visit_binary_op` | visitors | SUPERSET | 2 | 2 | no | dsl_parser:Parser.accept | nodes:ASTNode.accept | nodes:Acti |
| `BaseVisitor.visit_condition_block` | visitors | SUPERSET | 2 | 2 | no | dsl_parser:Parser.accept | nodes:ASTNode.accept | nodes:Acti |
| `CheckpointConfig.get_priority` | learning_proof_engine | SUPERSET | 2 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `CheckpointConfig.should_auto_dismiss` | learning_proof_engine | SUPERSET | 2 | 4 | no | learning_proof_engine:CheckpointConfig.get_priority |
| `ConflictResolver._detect_action_conflicts` | optimizer_conflict_resolver | SUPERSET | 6 | 3 | no | optimizer_conflict_resolver:ConflictResolver._get_condition_ |
| `ConflictResolver._detect_category_conflicts` | optimizer_conflict_resolver | SUPERSET | 3 | 6 | no | optimizer_conflict_resolver:ConflictResolver._might_override |
| `ConflictResolver._detect_circular_dependencies` | optimizer_conflict_resolver | SUPERSET | 6 | 6 | yes | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ConflictResolver._resolve_action_conflict` | optimizer_conflict_resolver | SUPERSET | 3 | 4 | no | grammar:PLangGrammar.get_action_precedence | optimizer_confl |
| `ConflictResolver._resolve_category_conflict` | optimizer_conflict_resolver | SUPERSET | 3 | 4 | no | grammar:PLangGrammar.get_category_priority | policy_limits_e |
| `ConflictResolver._resolve_circular_conflict` | optimizer_conflict_resolver | SUPERSET | 4 | 5 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ConflictResolver._resolve_conflict` | optimizer_conflict_resolver | SUPERSET | 4 | 1 | no | arbitrator:PolicyArbitrator._resolve_action_conflict | optim |
| `ConstantFolder._fold_binary_op` | folds | SUPERSET | 3 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ConstantFolder._fold_compare` | folds | SUPERSET | 2 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ConstantFolder._fold_unary_op` | folds | SUPERSET | 2 | 3 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ConstantFolder.try_fold` | folds | CANONICAL | 4 | 5 | no | folds:ConstantFolder._fold_binary_op | folds:ConstantFolder. |
| `ContentAccuracyValidator._get_nested_value` | content_accuracy | SUPERSET | 2 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ContentAccuracyValidator.validate` | content_accuracy | CANONICAL | 7 | 6 | no | content_accuracy:ContentAccuracyValidator._claims_affirmativ |
| `CustomerPolicyReadService.get_guardrail_detail` | customer_policy_read_engine | CANONICAL | 3 | 5 | no | policy_read_driver:PolicyReadDriver.get_guardrail_by_id |
| `DeadCodeEliminator._find_reachable_blocks` | folds | SUPERSET | 4 | 4 | yes | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `DeterministicEngine._call_function` | deterministic_engine | SUPERSET | 2 | 4 | no | deterministic_engine:DeterministicEngine._execute_function | |
| `DeterministicEngine._execute_function` | deterministic_engine | SUPERSET | 5 | 10 | no | deterministic_engine:DeterministicEngine._execute_instructio |
| `DeterministicEngine._execute_instruction` | deterministic_engine | SUPERSET | 15 | 2 | no | deterministic_engine:DeterministicEngine._action_to_intent_t |
| `DeterministicEngine.execute` | deterministic_engine | SUPERSET | 3 | 3 | no | deterministic_engine:DeterministicEngine._execute_function | |
| `EligibilityEngine._evaluate_e002_known_capability` | eligibility_engine | SUPERSET | 2 | 4 | no | eligibility_engine:CapabilityLookup.exists | eligibility_eng |
| `EligibilityEngine._evaluate_e003_no_blocking_signal` | eligibility_engine | SUPERSET | 2 | 6 | no | eligibility_engine:DefaultGovernanceSignalLookup.has_blockin |
| `EligibilityEngine.evaluate` | eligibility_engine | CANONICAL | 6 | 8 | no | eligibility_engine:EligibilityEngine._create_verdict |
| `ExecutionContext.get_variable` | deterministic_engine | CANONICAL | 4 | 5 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `ExecutionKernel._emit_envelope` | kernel | SUPERSET | 2 | 1 | no | dsl_parser:Parser.error |
| `ExecutionKernel.invoke_async` | kernel | CANONICAL | 2 | 8 | no | kernel:ExecutionKernel._emit_envelope | kernel:ExecutionKern |
| `GovernanceFacade.enable_kill_switch` | governance_facade | SUPERSET | 2 | 2 | no | dsl_parser:Parser.error |
| `GovernanceFacade.get_governance_state` | governance_facade | SUPERSET | 3 | 1 | no | dsl_parser:Parser.error | policy_limits_engine:PolicyLimitsS |
| `GovernanceFacade.set_mode` | governance_facade | CANONICAL | 6 | 2 | no | degraded_mode:enter_degraded_mode | degraded_mode:exit_degra |
| `IRBuilder.visit_action_block` | ir_builder | SUPERSET | 2 | 4 | no | ir_builder:IRBuilder._emit | visitors:PrintVisitor._emit |
| `IRBuilder.visit_func_call` | ir_builder | SUPERSET | 2 | 3 | no | dsl_parser:Parser.accept | ir_builder:IRBuilder._emit | node |
| `IRBuilder.visit_rule_decl` | ir_builder | CANONICAL | 1 | 18 | no | dsl_parser:Parser.accept | ir_builder:IRBuilder._emit | ir_b |
| `IRCompiler._compile_actions` | ir_compiler | SUPERSET | 3 | 4 | no | ast:is_block_action | ast:is_require_approval_action | ast:i |
| `IRCompiler._emit_condition` | ir_compiler | SUPERSET | 3 | 1 | no | ast:is_exists_predicate | ast:is_logical_condition | ast:is_ |
| `IntentEmitter.emit` | intent | SUPERSET | 3 | 6 | no | intent:IntentEmitter.validate_intent | policy_limits_engine: |
| `Interpreter._compare` | interpreter | SUPERSET | 7 | 2 | no | interpreter:Interpreter._types_compatible |
| `Interpreter._evaluate_condition` | interpreter | SUPERSET | 2 | 6 | no | deterministic_engine:DeterministicEngine._execute_instructio |
| `Interpreter._execute_instruction` | interpreter | SUPERSET | 13 | 2 | no | interpreter:Interpreter._compare | interpreter:_LenientInter |
| `Interpreter.evaluate` | interpreter | CANONICAL | 1 | 5 | no | interpreter:Interpreter._evaluate_clause |
| `LessonsLearnedEngine.convert_lesson_to_draft` | lessons_engine | SUPERSET | 2 | 7 | no | dsl_parser:Parser.error | lessons_engine:LessonsLearnedEngin |
| `LessonsLearnedEngine.defer_lesson` | lessons_engine | SUPERSET | 3 | 5 | no | dsl_parser:Parser.error | lessons_engine:LessonsLearnedEngin |
| `LessonsLearnedEngine.detect_lesson_from_near_threshold` | lessons_engine | CANONICAL | 2 | 7 | no | lessons_engine:LessonsLearnedEngine._create_lesson | lessons |
| `LessonsLearnedEngine.dismiss_lesson` | lessons_engine | SUPERSET | 3 | 6 | no | dsl_parser:Parser.error | lessons_engine:LessonsLearnedEngin |
| `LessonsLearnedEngine.get_lesson_stats` | lessons_engine | SUPERSET | 2 | 5 | no | lessons_engine:LessonsLearnedEngine._get_driver |
| `LessonsLearnedEngine.reactivate_deferred_lesson` | lessons_engine | SUPERSET | 3 | 5 | no | dsl_parser:Parser.error | lessons_engine:LessonsLearnedEngin |
| `LessonsLearnedEngine.reactivate_expired_deferred_lessons` | lessons_engine | SUPERSET | 3 | 6 | no | lessons_engine:LessonsLearnedEngine.get_expired_deferred_les |
| `Lexer.tokenize` | dsl_parser | CANONICAL | 3 | 4 | no | compiler_parser:Parser.match | dsl_parser:Lexer._advance | d |
| `LimitsFacade.check_limit` | limits_facade | SUPERSET | 5 | 8 | no | limits_facade:LimitsFacade._get_or_create_limit |
| `LimitsFacade.get_usage` | limits_facade | SUPERSET | 3 | 7 | no | ast:BlockAction.to_dict | ast:Clause.to_dict | ast:ExistsPre |
| `LimitsFacade.list_limits` | limits_facade | SUPERSET | 2 | 5 | no | limits_facade:LimitsFacade._get_or_create_limit |
| `LimitsFacade.update_limit` | limits_facade | CANONICAL | 5 | 9 | no | policy_limits_engine:PolicyLimitsService.update | policy_rul |
| `MCPPolicyMapper._evaluate_policy` | policy_mapper | SUPERSET | 3 | 4 | no | policy_mapper:MCPPolicyMapper._get_policy_engine |
| `MCPPolicyMapper.check_tool_invocation` | policy_mapper | CANONICAL | 8 | 11 | no | policy_limits_engine:PolicyLimitsService.get | policy_mapper |
| `MockAbuseProtectionProvider.check_all` | protection_provider | CANONICAL | 4 | 9 | no | policy_mapper:MCPPolicyDecision.allow | prevention_engine:Pr |
| `MockAbuseProtectionProvider.check_burst` | protection_provider | SUPERSET | 2 | 6 | no | policy_limits_engine:PolicyLimitsService.get | policy_mapper |
| `MockAbuseProtectionProvider.check_cost` | protection_provider | SUPERSET | 2 | 8 | no | policy_limits_engine:PolicyLimitsService.get | policy_mapper |
| `MockAbuseProtectionProvider.check_rate_limit` | protection_provider | SUPERSET | 2 | 6 | no | policy_limits_engine:PolicyLimitsService.get | policy_mapper |
| `OverrideAuthorityChecker.check` | authority_checker | CANONICAL | 5 | 13 | no | authority_checker:OverrideAuthorityChecker._is_override_acti |
| `Parser._parse_actions` | dsl_parser | SUPERSET | 2 | 4 | no | dsl_parser:Parser._try_parse_action | dsl_parser:Parser.erro |
| `Parser._parse_atom` | dsl_parser | SUPERSET | 2 | 3 | no | compiler_parser:Parser.expect | dsl_parser:Parser._parse_or_ |
| `Parser._parse_header` | dsl_parser | SUPERSET | 2 | 13 | no | compiler_parser:Parser.expect | dsl_parser:Parser.accept | d |
| `Parser._try_parse_action` | dsl_parser | SUPERSET | 3 | 4 | no | compiler_parser:Parser.expect | dsl_parser:Parser.accept | d |
| `Parser.parse` | compiler_parser | SUPERSET | 3 | 3 | no | compiler_parser:Parser.match | compiler_parser:Parser.parse_ |
| `Parser.parse_action_block` | compiler_parser | SUPERSET | 2 | 7 | no | compiler_parser:Parser.advance | compiler_parser:Parser.pars |
| `Parser.parse_policy_body` | compiler_parser | SUPERSET | 5 | 3 | no | compiler_parser:Parser.match | compiler_parser:Parser.parse_ |
| `Parser.parse_rule_body` | compiler_parser | SUPERSET | 3 | 3 | no | compiler_parser:Parser.match | compiler_parser:Parser.parse_ |
| `Parser.parse_value` | compiler_parser | CANONICAL | 9 | 8 | no | compiler_parser:Parser.advance | compiler_parser:Parser.expe |
| `PatternCalibration.record_outcome` | learning_proof_engine | SUPERSET | 3 | 4 | no | learning_proof_engine:PatternCalibration._recalibrate |
| `PhaseStatusInvariantChecker.check` | phase_status_invariants | CANONICAL | 3 | 6 | no | phase_status_invariants:PhaseStatusInvariantChecker.get_allo |
| `PhaseStatusInvariantChecker.should_allow_transition` | phase_status_invariants | SUPERSET | 2 | 4 | no | authority_checker:OverrideAuthorityChecker.check | phase_sta |
| `PlanGenerationEngine.generate` | plan_generation_engine | CANONICAL | 2 | 11 | no | dsl_parser:Parser.error | policy_limits_engine:PolicyLimitsS |
| `PolicyArbitrator._resolve_action_conflict` | arbitrator | SUPERSET | 4 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicyArbitrator._resolve_limit_conflict` | arbitrator | SUPERSET | 4 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicyArbitrator.arbitrate` | arbitrator | CANONICAL | 7 | 15 | no | arbitrator:PolicyArbitrator._load_precedence_map | arbitrato |
| `PolicyConflictEngine._detect_priority_overrides` | policy_graph_engine | SUPERSET | 4 | 6 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicyConflictEngine._detect_scope_overlaps` | policy_graph_engine | SUPERSET | 5 | 5 | no | policy_graph_engine:PolicyConflictEngine._has_contradicting_ |
| `PolicyConflictEngine._detect_temporal_conflicts` | policy_graph_engine | SUPERSET | 2 | 4 | no | policy_graph_engine:PolicyConflictEngine._time_windows_overl |
| `PolicyConflictEngine._detect_threshold_contradictions` | policy_graph_engine | SUPERSET | 4 | 6 | no | policy_graph_driver:PolicyGraphDriver.fetch_active_limits |
| `PolicyConflictEngine.detect_conflicts` | policy_graph_engine | CANONICAL | 4 | 12 | no | policy_graph_driver:PolicyGraphDriver.fetch_active_policies  |
| `PolicyDependencyEngine._detect_explicit_dependencies` | policy_graph_engine | SUPERSET | 3 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicyDependencyEngine.check_can_activate` | policy_graph_engine | SUPERSET | 2 | 6 | no | policy_graph_engine:PolicyDependencyEngine.compute_dependenc |
| `PolicyEngine._check_business_rules` | engine | SUPERSET | 5 | 4 | no | engine:PolicyEngine._evaluate_business_rule | policy_limits_ |
| `PolicyEngine._check_compliance` | engine | SUPERSET | 3 | 4 | no | engine:PolicyEngine._evaluate_compliance_rule |
| `PolicyEngine._check_cooldown` | engine | SUPERSET | 3 | 4 | no | snapshot_engine:PolicySnapshotRegistry.list |
| `PolicyEngine._check_ethical_constraints` | engine | SUPERSET | 2 | 3 | no | engine:PolicyEngine._evaluate_ethical_constraint |
| `PolicyEngine._check_risk_ceilings` | engine | SUPERSET | 4 | 4 | no | engine:PolicyEngine._evaluate_risk_ceiling |
| `PolicyEngine._check_safety_rules` | engine | SUPERSET | 5 | 4 | no | engine:PolicyEngine._evaluate_safety_rule | policy_limits_en |
| `PolicyEngine._evaluate_business_rule` | engine | SUPERSET | 7 | 4 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicyEngine._evaluate_compliance_rule` | engine | SUPERSET | 8 | 5 | no | compiler_parser:Parser.match | policy_limits_engine:PolicyLi |
| `PolicyEngine._evaluate_ethical_constraint` | engine | SUPERSET | 5 | 4 | no | engine:PolicyEngine._extract_text_content | policy_limits_en |
| `PolicyEngine._evaluate_risk_ceiling` | engine | SUPERSET | 9 | 5 | no | engine:PolicyEngine._add_windowed_value | engine:PolicyEngin |
| `PolicyEngine._evaluate_safety_rule` | engine | SUPERSET | 10 | 3 | no | engine:PolicyEngine._extract_text_content | policy_limits_en |
| `PolicyEngine._route_to_governor` | engine | SUPERSET | 3 | 2 | no | dsl_parser:Parser.error |
| `PolicyEngine.activate_policy_version` | engine | SUPERSET | 16 | 4 | yes | dsl_parser:Parser.error | eligibility_engine:EligibilityEngi |
| `PolicyEngine.add_dependency_with_dag_check` | engine | SUPERSET | 7 | 2 | yes | dsl_parser:Parser.error | policy_engine_driver:PolicyEngineD |
| `PolicyEngine.clear_cooldowns` | engine | SUPERSET | 2 | 3 | no | snapshot_engine:PolicySnapshotRegistry.list |
| `PolicyEngine.create_policy_version` | engine | SUPERSET | 2 | 11 | yes | engine:PolicyEngine.get_current_version | policy_driver:Poli |
| `PolicyEngine.evaluate` | engine | CANONICAL | 19 | 36 | no | engine:PolicyEngine._check_business_rules | engine:PolicyEng |
| `PolicyEngine.evaluate_with_context` | engine | SUPERSET | 8 | 24 | no | eligibility_engine:EligibilityEngine.evaluate | engine:Polic |
| `PolicyEngine.get_active_cooldowns` | engine | SUPERSET | 2 | 4 | no | snapshot_engine:PolicySnapshotRegistry.list |
| `PolicyEngine.get_current_version` | engine | SUPERSET | 2 | 3 | no | policy_engine_driver:PolicyEngineDriver._get_engine | policy |
| `PolicyEngine.get_risk_ceilings` | engine | SUPERSET | 2 | 5 | no | engine:PolicyEngine._load_policies |
| `PolicyEngine.get_safety_rules` | engine | SUPERSET | 2 | 5 | no | engine:PolicyEngine._load_policies |
| `PolicyEngine.get_temporal_storage_stats` | engine | SUPERSET | 2 | 2 | no | dsl_parser:Parser.error | policy_engine_driver:PolicyEngineD |
| `PolicyEngine.get_temporal_utilization` | engine | SUPERSET | 2 | 3 | no | policy_engine_driver:PolicyEngineDriver._get_engine | policy |
| `PolicyEngine.get_topological_evaluation_order` | engine | SUPERSET | 5 | 9 | yes | dsl_parser:Parser.error | policy_limits_engine:PolicyLimitsS |
| `PolicyEngine.get_violation` | engine | SUPERSET | 3 | 3 | no | policy_engine_driver:PolicyEngineDriver._get_engine | policy |
| `PolicyEngine.get_violations` | engine | SUPERSET | 2 | 4 | no | policy_engine_driver:PolicyEngineDriver._get_engine | policy |
| `PolicyEngine.pre_check` | engine | SUPERSET | 3 | 1 | no | dsl_parser:Parser.error | eligibility_engine:EligibilityEngi |
| `PolicyEngine.rollback_to_version` | engine | SUPERSET | 2 | 3 | yes | dsl_parser:Parser.error | engine:PolicyEngine.reload_policie |
| `PolicyEngine.update_safety_rule` | engine | SUPERSET | 3 | 3 | yes | engine:PolicyEngine.reload_policies | policy_driver:PolicyDr |
| `PolicyEngine.validate_dependency_dag` | engine | SUPERSET | 8 | 13 | yes | dsl_parser:Parser.error | policy_engine_driver:PolicyEngineD |
| `PolicyEngineDriver.fetch_conflicts` | policy_engine_driver | SUPERSET | 2 | 6 | no | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyEngineDriver.fetch_temporal_policies` | policy_engine_driver | SUPERSET | 2 | 6 | no | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyEngineDriver.fetch_violations` | policy_engine_driver | CANONICAL | 5 | 11 | no | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyEngineDriver.update_safety_rule` | policy_engine_driver | SUPERSET | 2 | 4 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyLimitsService.update` | policy_limits_engine | CANONICAL | 7 | 4 | no | policy_limits_engine:PolicyLimitsService._get_limit | policy |
| `PolicyProposalEngine.check_proposal_eligibility` | policy_proposal_engine | CANONICAL | 3 | 8 | no | policy_limits_engine:PolicyLimitsService.get | policy_propos |
| `PolicyProposalEngine.delete_policy_rule` | policy_proposal_engine | SUPERSET | 2 | 8 | no | policy_graph_engine:PolicyDependencyEngine.check_can_delete  |
| `PolicyProposalEngine.review_proposal` | policy_proposal_engine | SUPERSET | 5 | 6 | no | ast:BlockAction.to_dict | ast:Clause.to_dict | ast:ExistsPre |
| `PolicyProposalReadDriver.fetch_proposals` | policy_proposal_read_driver | CANONICAL | 2 | 7 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyProposalReadDriver.fetch_unacknowledged_feedback` | policy_proposal_read_driver | SUPERSET | 2 | 6 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyRegretTracker.add_regret` | learning_proof_engine | CANONICAL | 2 | 5 | no | learning_proof_engine:PolicyRegretTracker._trigger_demotion |
| `PolicyRulesQueryEngine.list_policy_rules` | policies_rules_query_engine | CANONICAL | 6 | 10 | no | policy_rules_read_driver:PolicyRulesReadDriver.fetch_policy_ |
| `PolicyRulesReadDriver.fetch_policy_rules` | policy_rules_read_driver | CANONICAL | 12 | 22 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `PolicyRulesService.update` | policy_rules_engine | CANONICAL | 6 | 4 | no | policy_limits_engine:PolicyLimitsService._to_response | poli |
| `PolicySimplifier._find_mergeable_policies` | folds | SUPERSET | 2 | 3 | no | snapshot_engine:PolicySnapshotRegistry.list |
| `PolicySnapshotRegistry.archive` | snapshot_engine | SUPERSET | 2 | 5 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicySnapshotRegistry.create` | snapshot_engine | CANONICAL | 1 | 13 | no | snapshot_engine:PolicySnapshotData.compute_hash | snapshot_e |
| `PolicySnapshotRegistry.delete` | snapshot_engine | SUPERSET | 3 | 7 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicySnapshotRegistry.get_statistics` | snapshot_engine | SUPERSET | 6 | 5 | yes | snapshot_engine:PolicySnapshotData.verify_integrity |
| `PolicySnapshotRegistry.verify` | snapshot_engine | SUPERSET | 2 | 6 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PolicyValidator._check_warnings` | validator | SUPERSET | 4 | 3 | no | ast:is_block_action | ast:is_require_approval_action |
| `PolicyValidator._extract_metrics` | validator | SUPERSET | 3 | 3 | no | ast:is_exists_predicate | ast:is_logical_condition | ast:is_ |
| `PolicyValidator._validate_metrics` | validator | SUPERSET | 2 | 4 | no | validator:PolicyValidator._extract_metrics |
| `PolicyValidator._validate_mode_enforcement` | validator | SUPERSET | 3 | 3 | no | ast:is_block_action | ast:is_require_approval_action |
| `PreventionEngine._evaluate_custom_policy` | prevention_engine | SUPERSET | 3 | 6 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `PreventionEngine._evaluate_step_inner` | prevention_engine | SUPERSET | 12 | 11 | no | binding_moment_enforcer:should_evaluate_policy | policy_conf |
| `PreventionEngine.load_snapshot` | prevention_engine | CANONICAL | 2 | 1 | no | dsl_parser:Parser.error | snapshot_engine:PolicySnapshotData |
| `PreventionHook.evaluate` | prevention_hook | CANONICAL | 3 | 6 | no | content_accuracy:ContentAccuracyValidator.validate | validat |
| `PrintVisitor.visit_binary_op` | visitors | SUPERSET | 2 | 5 | no | dsl_parser:Parser.accept | ir_builder:IRBuilder._emit | node |
| `PrintVisitor.visit_condition_block` | visitors | CANONICAL | 2 | 8 | no | dsl_parser:Parser.accept | ir_builder:IRBuilder._emit | node |
| `ProposalsQueryEngine.list_policy_requests` | policies_proposals_query_engine | CANONICAL | 3 | 7 | no | policy_proposal_read_driver:PolicyProposalReadDriver.fetch_p |
| `ProposalsReadDriver.fetch_proposal_by_id` | proposals_read_driver | SUPERSET | 2 | 10 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `ProposalsReadDriver.fetch_proposals` | proposals_read_driver | CANONICAL | 4 | 14 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `RecoveryMatcher._compute_confidence` | recovery_matcher | SUPERSET | 5 | 13 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `RecoveryMatcher._escalate_to_llm` | recovery_matcher | SUPERSET | 3 | 1 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `RecoveryMatcher.approve_candidate` | recovery_matcher | SUPERSET | 3 | 14 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `RecoveryMatcher.get_candidates` | recovery_matcher | SUPERSET | 2 | 11 | yes | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `RecoveryMatcher.suggest` | recovery_matcher | CANONICAL | 3 | 19 | no | dsl_parser:Parser.error | policy_limits_engine:PolicyLimitsS |
| `RecoveryMatcher.suggest_hybrid` | recovery_matcher | SUPERSET | 4 | 13 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `SandboxService._check_quota` | sandbox_engine | SUPERSET | 3 | 10 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `SandboxService.execute` | sandbox_engine | CANONICAL | 7 | 19 | no | deterministic_engine:DeterministicEngine.execute | sandbox_e |
| `SandboxService.get_execution_stats` | sandbox_engine | SUPERSET | 3 | 10 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `Scope.lookup` | symbol_table | SUPERSET | 2 | 3 | no | symbol_table:SymbolTable.lookup |
| `ScopeResolver.resolve_applicable_policies` | scope_resolver | CANONICAL | 6 | 11 | no | scope_resolver:ScopeResolver._load_scopes | scope_resolver:S |
| `SymbolTable.lookup_rule` | symbol_table | CANONICAL | 5 | 4 | no | symbol_table:Scope.lookup | symbol_table:SymbolTable.lookup  |
| `Tokenizer.read_operator` | tokenizer | CANONICAL | 5 | 9 | no | compiler_parser:Parser.advance | compiler_parser:Parser.peek |
| `Tokenizer.read_string` | tokenizer | SUPERSET | 2 | 8 | no | compiler_parser:Parser.advance | policy_limits_engine:Policy |
| `Tokenizer.tokenize` | tokenizer | SUPERSET | 7 | 4 | no | compiler_parser:Parser.advance | tokenizer:Tokenizer.advance |
| `_LenientInterpreter._execute_instruction` | interpreter | SUPERSET | 2 | 2 | no | deterministic_engine:DeterministicEngine._execute_instructio |
| `_check_fields_changed` | binding_moment_enforcer | SUPERSET | 2 | 6 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `check_safety_limits` | llm_policy_engine | CANONICAL | 4 | 9 | no | llm_policy_engine:LLMRateLimiter.check_and_record | llm_poli |
| `convert_brand_request` | worker_execution_command | CANONICAL | 1 | 14 | no | worker_execution_command:get_brand_schema_types |
| `evaluate_policy` | policy_command | CANONICAL | 3 | 4 | no | policy_command:_record_policy_decision | policy_command:chec |
| `execute_query` | runtime_command | CANONICAL | 5 | 2 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `exit_degraded_mode` | degraded_mode | CANONICAL | 1 | 5 | no | degraded_mode:DegradedModeStatus.get_inactive |
| `get_model_for_task` | llm_policy_engine | SUPERSET | 4 | 6 | no | llm_policy_engine:is_expensive_model | llm_policy_engine:is_ |
| `governed` | decorator | CANONICAL | 1 | 2 | no | decorator:_extract_subject | decorator:_extract_tenant_id |  |
| `handle_policy_failure` | failure_mode_handler | CANONICAL | 3 | 9 | no | dsl_parser:Parser.error | failure_mode_handler:get_failure_m |
| `resolve_policy_conflict` | policy_conflict_resolver | CANONICAL | 5 | 11 | no | policy_limits_engine:PolicyLimitsService.get | policy_rules_ |
| `should_evaluate_policy` | binding_moment_enforcer | SUPERSET | 6 | 4 | no | binding_moment_enforcer:_check_fields_changed | binding_mome |

## Wrapper Inventory

_442 thin delegation functions._

- `nodes.ASTNode.accept` → ?
- `nodes.ASTNode.location` → ?
- `nodes.ASTVisitor.visit_action_block` → ?
- `nodes.ASTVisitor.visit_attr_access` → ?
- `nodes.ASTVisitor.visit_binary_op` → ?
- `nodes.ASTVisitor.visit_condition_block` → ?
- `nodes.ASTVisitor.visit_func_call` → ?
- `nodes.ASTVisitor.visit_ident` → ?
- `nodes.ASTVisitor.visit_import` → ?
- `nodes.ASTVisitor.visit_literal` → ?
- `nodes.ASTVisitor.visit_policy_decl` → ?
- `nodes.ASTVisitor.visit_priority` → ?
- `nodes.ASTVisitor.visit_program` → ?
- `nodes.ASTVisitor.visit_route_target` → ?
- `nodes.ASTVisitor.visit_rule_decl` → ?
- `nodes.ASTVisitor.visit_rule_ref` → ?
- `nodes.ASTVisitor.visit_unary_op` → ?
- `protection_provider.AbuseProtectionProvider.check_all` → ?
- `protection_provider.AbuseProtectionProvider.check_burst` → ?
- `protection_provider.AbuseProtectionProvider.check_cost` → ?
- `protection_provider.AbuseProtectionProvider.check_rate_limit` → ?
- `protection_provider.AbuseProtectionProvider.detect_anomaly` → ?
- `nodes.ActionBlockNode.accept` → ir_builder:IRBuilder.visit_action_block
- `nodes.AttrAccessNode.accept` → ir_builder:IRBuilder.visit_attr_access
- `visitors.BaseVisitor.visit_ident` → ?
- `visitors.BaseVisitor.visit_import` → ?
- `visitors.BaseVisitor.visit_literal` → ?
- `visitors.BaseVisitor.visit_priority` → ?
- `visitors.BaseVisitor.visit_route_target` → ?
- `visitors.BaseVisitor.visit_rule_ref` → ?
- _...and 412 more_

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `policy_limits_engine` | Removed cross-domain `AuditLedgerServiceAsync` import. Accepts `audit: Any = None` via dependency injection from L4 handler. | PIN-504 Phase 2 |
| `policy_rules_engine` | Same pattern — audit injected from L4 handler. | PIN-504 Phase 2 |
| `policy_proposal_engine` | `review_proposal` accepts `audit: Any = None` parameter. Removed inline audit creation. | PIN-504 Phase 2 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `policies_handler.py` | 9 handler classes: all `getattr()` replaced with explicit dispatch maps. `PoliciesGovernanceHandler` (7 sync), `PoliciesLessonsHandler` (14 sync), `PoliciesPolicyFacadeHandler` (34 async + 1 sync), `PoliciesRateLimitsHandler` (6 async). All `iscoroutinefunction` calls eliminated. `import asyncio` removed. Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-507 Law 0 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `app/services/policy/__init__.py` | Removed stale re-export of `LessonsLearnedEngine` from disconnected shim. Class moved to HOC `policies/L5_engines/lessons_engine.py` (PIN-468). | PIN-507 Law 0 |
| `app/services/limits/policy_limits_service.py` | Import `AuditLedgerServiceAsync` rewired from abolished `app.services.logs.audit_ledger_service_async` → `app.hoc.cus.logs.L6_drivers.audit_ledger_driver`. Transitional `services→hoc`. | PIN-507 Law 0 |
| `app/services/limits/policy_rules_service.py` | Same rewire as above. | PIN-507 Law 0 |
| `app/services/policy_proposal.py` | Same rewire as above. | PIN-507 Law 0 |
| `app/api/policy_layer.py` | Import `get_policy_facade` rewired from abolished `app.services.policy.facade` → `app.services.policy` (package re-export). | PIN-507 Law 0 |
| `app/services/governance/facade.py` | Same rewire as above (lazy import inside health check). | PIN-507 Law 0 |

## PIN-507 Law 6 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `recovery_evaluation_engine` | Pure decision function imports changed from `hoc.cus.hoc_spine.schemas.recovery_decisions` → `hoc.cus.hoc_spine.utilities.recovery_decisions`. `evaluate_rules` imported directly from `incidents/L5_engines/recovery_rule_engine` (no longer via schemas proxy). | PIN-507 Law 6 |

## PIN-508 DomainBridge Capabilities Integration (2026-02-01)

### Phase 2: Cross-Domain Capability Protocols

**New File Added:**
- `domain_bridge_capabilities.py` (L5 Schemas) — Capability protocol definitions for cross-domain access via DomainBridge. Contains: `LessonsQueryCapability`, `LimitsQueryCapability`, `PolicyLimitsCapability`.

### Phases 2A, 2B, 2C: Factory and Constructor Parameter Updates

| Script | Layer | Change | Reference |
|--------|-------|--------|-----------|
| `lessons_engine.py` | L5 | Factory now accepts `driver` parameter for DomainBridge capability injection. Enables cross-domain lessons learned queries. | PIN-508 Phase 2A |
| `policies_limits_query_engine.py` | L5 | Factory now accepts `driver` parameter for DomainBridge capability injection. | PIN-508 Phase 2B |
| `policy_limits_engine.py` | L5 | Constructor now accepts `driver` parameter for DomainBridge capability injection. | PIN-508 Phase 2C |

### Phase 5: Stub Engine Markings

| Script | Layer | Change | Reference |
|--------|-------|--------|-----------|
| `cus_enforcement_engine.py` | L5 | STUB_ENGINE marker added. Methods now raise `NotImplementedError`. Pending HOC-native implementation. | PIN-508 Phase 5 |
| `limits_simulation_engine.py` | L5 | STUB_ENGINE marker added. Methods raise `NotImplementedError`. Pending HOC-native implementation. | PIN-508 Phase 5 |
| `policies_facade.py` | L5 | STUB_ENGINE marker added. 13 methods raise `NotImplementedError`. Pending HOC-native implementation. | PIN-508 Phase 5 |

**Intent:** PIN-508 integrates cross-domain capability protocols via DomainBridge, enabling safe cross-domain queries and operations. Stub engines maintain backward compatibility while signaling incomplete implementation status.

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-510 Phase 1B — Lazy Fallback Assertion Guards (2026-02-01)

Two policies L5 engines now have assertion-guarded legacy fallbacks:

| Engine | Factory/Constructor | Guard |
|--------|-------------------|-------|
| `policies_limits_query_engine.py` | `get_limits_query_engine()` | `HOC_REQUIRE_L4_INJECTION` env flag |
| `policy_limits_engine.py` | `PolicyLimitsEngine.__init__()` | `HOC_REQUIRE_L4_INJECTION` env flag |

**Behavior:**
- `HOC_REQUIRE_L4_INJECTION` unset: fallback works, logs warning
- `HOC_REQUIRE_L4_INJECTION=1`: raises RuntimeError (enforced in CI/prod)
- After all callers migrate: remove fallback code entirely

Reference: `docs/memory-pins/PIN-510-domain-remediation-queue.md`

## PIN-513 Phase A — Policies Domain Changes (2026-02-01)

- claim_decision_engine.py (L5): DELETED — Phase R-4 moved logic inline into recovery_claim_worker.py

---

### PIN-513 Phase 9 Batch 2B Amendment (2026-02-01)

**Scope:** 26 policies symbols reclassified.

| Category | Count | Details |
|----------|-------|---------|
| PHANTOM_NO_HOC_COPY | 3 | claim_decision_engine — file does not exist in HOC |
| WIRED via policies_handler | 3 | limits/proposals/rules query engines → PoliciesLimitsQueryHandler, PoliciesProposalsQueryHandler, PoliciesRulesQueryHandler |
| WIRED pure import | 6 | dsl_parser (2), conflict_resolver (4) — pure functions, callers import directly |
| WIRED PolicyGovernanceHandler | 13 | proposal_engine (7), snapshot_engine (6) |
| WIRED middleware import | 2 | protection_provider — middleware calls directly |

**Files created:**
- `hoc_spine/orchestrator/handlers/policy_governance_handler.py` — L4 handler for policy proposal lifecycle + snapshot governance

**Files modified:**
- `hoc_spine/orchestrator/handlers/policies_handler.py` — Added 3 query handler classes (PoliciesLimitsQueryHandler, PoliciesProposalsQueryHandler, PoliciesRulesQueryHandler)

### PIN-513 Phase 9 Batch 5 Amendment (2026-02-01)

**CI invariant hardening — policies domain impact:**

- `recovery.py` frozen in check 27 allowlist (L2→L5/L6 bypass — imports recovery_matcher, recovery_write_driver, recovery_rule_engine, scoped_execution)
- `recovery_ingest.py` frozen in check 27 allowlist (L2→L5/L6 bypass — imports recovery_write_driver)
- `billing_dependencies.py` frozen in check 27 allowlist (L2→L5/L6 bypass — imports billing_provider_engine)
- `workers.py` frozen in check 27 allowlist (L2→L5/L6 bypass — imports capture_driver, recovery_evaluation_engine)
- `recovery_evaluation_engine.py` frozen in check 28 allowlist (L5→L5 cross-domain — imports incidents/recovery_rule_engine)

**No new files may introduce these patterns.**

## PIN-514 Runtime Convergence (2026-02-03)

**M20 Policy Runtime consolidated to canonical L5_engines location.**

| Action | File | Description |
|--------|------|-------------|
| CREATE | `L5_engines/intent.py` | IntentEmitter, Intent, IntentPayload, IntentType — fail-closed M19 validator injection |
| CREATE | `L5_engines/deterministic_engine.py` | DeterministicEngine, ExecutionContext, ExecutionResult — policy IR execution |
| CREATE | `L5_engines/dag_executor.py` | DAGExecutor, StageResult, ExecutionTrace — parallel policy DAG execution |
| UPDATE | `L5_engines/__init__.py` | Exports all M20 runtime components |
| DELETE | `app/policy/runtime/` | Non-canonical location removed |

**Import path changes (6 files):**

| File | Old Import | New Import |
|------|------------|------------|
| `hoc/int/integrations/engines/worker.py` | `app.policy.runtime.*` | `app.hoc.cus.policies.L5_engines.*` |
| `workers/business_builder/worker.py` | `app.policy.runtime.*` | `app.hoc.cus.policies.L5_engines.*` |
| `api/workers.py` | `app.policy.runtime.*` | `app.hoc.cus.policies.L5_engines.*` |
| `hoc/api/cus/policies/workers.py` | `app.policy.runtime.*` | `app.hoc.cus.policies.L5_engines.*` |
| `hoc/cus/hoc_spine/drivers/dag_executor.py` | `app.policy.runtime.*` | `app.hoc.cus.policies.L5_engines.*` |
| `tests/test_m20_runtime.py` | `app.policy.runtime.*` | `app.hoc.cus.policies.L5_engines.*` |

**Script Registry additions:**

| Script | Layer | Canonical Function | Role | Callers |
|--------|-------|--------------------|------|---------|
| dag_executor | L5 | `DAGExecutor.execute` | CANONICAL | L4:dag_executor, workers, test_m20_runtime |

**Canonical import path:** `from app.hoc.cus.policies.L5_engines.intent import IntentEmitter`

Reference: `docs/memory-pins/PIN-514-runtime-convergence.md`, `docs/contracts/POLICY_RUNTIME_WIRING_CONTRACT.md`

## PIN-519 System Run Introspection (2026-02-03)

**New L6 driver for policy evaluation queries.**

| Action | File | Description |
|--------|------|-------------|
| CREATE | `L6_drivers/policy_enforcement_driver.py` | Read-only policy evaluation queries for runs |

**New capabilities:**

| Method | Purpose |
|--------|---------|
| `PolicyEnforcementReadDriver.fetch_policy_evaluations_for_run(tenant_id, run_id)` | Query policy evaluations scoped to a run |

**Bridge extension:**

| Bridge | Method Added |
|--------|--------------|
| `policies_bridge.py` | `policy_evaluations_capability(session)` — returns `PolicyEnforcementReadDriver` |

**Consumer:** `RunEvidenceCoordinator` (L4) via `PoliciesBridge`

Reference: `docs/memory-pins/PIN-519-system-run-introspection.md`

## Recovery Count Query Fix (2026-02-03)

**Fixed inefficient count queries in recovery module.**

| Action | File | Description |
|--------|------|-------------|
| ADD | `L6_drivers/recovery_matcher.py` | `count_candidates(status)` method — efficient COUNT query for pagination |
| ADD | `L6_drivers/recovery_matcher.py` | `count_by_status()` method — single GROUP BY query for stats |
| FIX | `hoc/api/cus/recovery/recovery.py:269` | Use `count_candidates()` for pagination total instead of `len(candidates)` |
| FIX | `hoc/api/cus/recovery/recovery.py:362` | Use `count_by_status()` instead of 3x `get_candidates(limit=1)` |

**Problem solved:**

| Issue | Before | After |
|-------|--------|-------|
| Pagination total | `len(candidates)` = page size (broken UI) | `COUNT(*)` = actual total |
| Stats counts | 3 queries returning 0 or 1 each | 1 query with `GROUP BY decision` |

**New methods in `RecoveryMatcher`:**

```python
def count_candidates(self, status: str = "pending") -> int:
    """COUNT query for pagination — O(index scan)."""

def count_by_status(self) -> Dict[str, int]:
    """GROUP BY query for stats — single query."""
```

**No transaction boundary changes** — L6 driver, caller owns commit.
