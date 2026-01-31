# Policies — Domain Capability

**Domain:** policies  
**Total functions:** 1020  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## 1. Domain Purpose

Policy engine — DSL-based policy definition, compilation, evaluation, versioning, and enforcement across all operations.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `BootStatusResult.to_dict` | governance_facade | Yes | L4:policies_handler | pure |
| `CapabilityLookup.exists` | eligibility_engine | Yes | L4:contract_engine | pure |
| `CapabilityLookup.is_frozen` | eligibility_engine | Yes | L4:contract_engine | pure |
| `ConflictResolutionResult.to_dict` | governance_facade | Yes | L4:policies_handler | pure |
| `ContractLookup.has_similar_pending` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DefaultCapabilityLookup.exists` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DefaultCapabilityLookup.is_frozen` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DefaultContractLookup.has_similar_pending` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DefaultGovernanceSignalLookup.has_blocking_signal` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DefaultPreApprovalLookup.has_system_pre_approval` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DefaultSystemHealthLookup.get_status` | eligibility_engine | Yes | L4:contract_engine | pure |
| `DeterministicEngine.execute` | deterministic_engine | Yes | L4:dag_executor | pure |
| `EligibilityEngine.evaluate` | eligibility_engine | Yes | L4:contract_engine | pure |
| `ExecutionContext.add_trace` | deterministic_engine | Yes | L4:dag_executor | pure |
| `ExecutionContext.get_variable` | deterministic_engine | Yes | L4:dag_executor | pure |
| `ExecutionContext.pop_call` | deterministic_engine | Yes | L4:dag_executor | pure |
| `ExecutionContext.push_call` | deterministic_engine | Yes | L4:dag_executor | pure |
| `ExecutionContext.set_variable` | deterministic_engine | Yes | L4:dag_executor | pure |
| `ExecutionResult.to_dict` | deterministic_engine | Yes | L4:dag_executor | pure |
| `GovernanceFacade.disable_kill_switch` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceFacade.enable_kill_switch` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceFacade.get_boot_status` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceFacade.get_governance_state` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceFacade.list_conflicts` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceFacade.resolve_conflict` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceFacade.set_mode` | governance_facade | Yes | L4:policies_handler | pure |
| `GovernanceSignalLookup.has_blocking_signal` | eligibility_engine | Yes | L4:contract_engine | pure |
| `GovernanceStateResult.to_dict` | governance_facade | Yes | L4:policies_handler | pure |
| `Intent.from_dict` | intent | Yes | L2:recovery | pure |
| `Intent.to_dict` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.clear` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.create_intent` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.emit` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.emit_all` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.get_emitted` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.get_pending` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.register_handler` | intent | Yes | L2:recovery | pure |
| `IntentEmitter.validate_intent` | intent | Yes | L2:recovery | pure |
| `IntentPayload.from_dict` | intent | Yes | L2:recovery | pure |
| `IntentPayload.to_dict` | intent | Yes | L2:recovery | pure |
| `KillSwitchResult.to_dict` | governance_facade | Yes | L4:policies_handler | pure |
| `LessonsLearnedEngine.convert_lesson_to_draft` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.defer_lesson` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.detect_lesson_from_critical_success` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.detect_lesson_from_failure` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.detect_lesson_from_near_threshold` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.dismiss_lesson` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.emit_critical_success` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.emit_near_threshold` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.get_expired_deferred_lessons` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.get_lesson` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.get_lesson_stats` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.list_lessons` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.reactivate_deferred_lesson` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LessonsLearnedEngine.reactivate_expired_deferred_lessons` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `LimitCheckResult.to_dict` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitConfig.to_dict` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitsFacade.check_limit` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitsFacade.get_limit` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitsFacade.get_usage` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitsFacade.list_limits` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitsFacade.reset_limit` | limits_facade | Yes | L4:policies_handler | pure |
| `LimitsFacade.update_limit` | limits_facade | Yes | L4:policies_handler | pure |
| `PolicyDriver.acknowledge_violation` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.activate_policy_version` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.add_dependency_with_dag_check` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.clear_cooldowns` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.create_policy_version` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.create_temporal_policy` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.evaluate` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.evaluate_with_context` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_active_cooldowns` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_current_version` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_dependency_graph` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_ethical_constraints` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_metrics` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_policy_conflicts` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_policy_versions` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_risk_ceiling` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_risk_ceilings` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_safety_rules` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_state` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_temporal_policies` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_temporal_storage_stats` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_temporal_utilization` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_topological_evaluation_order` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_version_provenance` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_violation` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.get_violations` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.pre_check` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.prune_temporal_metrics` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.reload_policies` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.reset_risk_ceiling` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.resolve_conflict` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.rollback_to_version` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.update_risk_ceiling` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.update_safety_rule` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyDriver.validate_dependency_dag` | policy_driver | Yes | L4:policies_handler | pure |
| `PolicyLimitsService.create` | policy_limits_engine | Yes | L4:policies_handler | pure |
| `PolicyLimitsService.delete` | policy_limits_engine | Yes | L4:policies_handler | db_write |
| `PolicyLimitsService.get` | policy_limits_engine | Yes | L4:policies_handler | pure |
| `PolicyLimitsService.update` | policy_limits_engine | Yes | L4:policies_handler | pure |
| `PolicyRulesService.create` | policy_rules_engine | Yes | L4:policies_handler | pure |
| `PolicyRulesService.get` | policy_rules_engine | Yes | L4:policies_handler | pure |
| `PolicyRulesService.update` | policy_rules_engine | Yes | L4:policies_handler | pure |
| `PreApprovalLookup.has_system_pre_approval` | eligibility_engine | Yes | L4:contract_engine | pure |
| `SystemHealthLookup.get_status` | eligibility_engine | Yes | L4:contract_engine | pure |
| `UsageSummary.to_dict` | limits_facade | Yes | L4:policies_handler | pure |
| `execute_query` | runtime_command | Yes | L2:runtime | pure |
| `get_all_skill_descriptors` | runtime_command | Yes | L2:runtime | pure |
| `get_capabilities` | runtime_command | Yes | L2:runtime | pure |
| `get_cus_enforcement_service` | cus_enforcement_service | Yes | L4:policies_handler | pure |
| `get_governance_facade` | governance_facade | Yes | L4:policies_handler | pure |
| `get_lessons_learned_engine` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `get_limits_facade` | limits_facade | Yes | L4:policies_handler | pure |
| `get_limits_simulation_service` | limits_simulation_service | Yes | L4:policies_handler | pure |
| `get_policy_driver` | policy_driver | Yes | L4:policies_handler | pure |
| `get_resource_contract` | runtime_command | Yes | L2:runtime | pure |
| `get_skill_info` | runtime_command | Yes | L2:runtime | pure |
| `get_supported_query_types` | runtime_command | Yes | L2:runtime | pure |
| `get_threshold_band` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `is_valid_transition` | lessons_engine | Yes | L4:run_governance_facade | pure |
| `list_skills` | runtime_command | Yes | L2:runtime | pure |
| `query_allowed_skills` | runtime_command | Yes | L2:runtime | pure |
| `query_execution_history` | runtime_command | Yes | L2:runtime | pure |
| `query_last_step_outcome` | runtime_command | Yes | L2:runtime | pure |
| `query_remaining_budget` | runtime_command | Yes | L2:runtime | pure |
| `query_skills_for_goal` | runtime_command | Yes | L2:runtime | pure |
| `reset_policy_driver` | policy_driver | Yes | L4:policies_handler | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `AbuseProtectionProvider.check_all` | protection_provider | ambiguous |
| `AbuseProtectionProvider.check_burst` | protection_provider | ambiguous |
| `AbuseProtectionProvider.check_cost` | protection_provider | ambiguous |
| `AbuseProtectionProvider.check_rate_limit` | protection_provider | ambiguous |
| `BillingState.allows_usage` | state | medium |
| `CheckpointConfig.should_auto_dismiss` | learning_proof_engine | ambiguous |
| `ContentAccuracyValidator.validate` | content_accuracy | medium |
| `CustomerPolicyReadService.get_guardrail_detail` | customer_policy_read_engine | medium |
| `Interpreter.evaluate` | interpreter | medium |
| `LLMRateLimiter.check_and_record` | llm_policy_engine | medium |
| `MCPPolicyDecision.allow` | policy_mapper | medium |
| `MCPPolicyDecision.deny` | policy_mapper | medium |
| `MCPPolicyMapper.check_tool_invocation` | policy_mapper | medium |
| `MockAbuseProtectionProvider.check_all` | protection_provider | ambiguous |
| `MockAbuseProtectionProvider.check_burst` | protection_provider | ambiguous |
| `MockAbuseProtectionProvider.check_cost` | protection_provider | ambiguous |
| `MockAbuseProtectionProvider.check_rate_limit` | protection_provider | ambiguous |
| `OverrideAuthorityChecker.check` | authority_checker | medium |
| `OverrideAuthorityChecker.check_from_dict` | authority_checker | ambiguous |
| `PhaseStatusInvariantChecker.check` | phase_status_invariants | medium |
| `PhaseStatusInvariantChecker.enforcement_enabled` | phase_status_invariants | medium |
| `PhaseStatusInvariantChecker.get_allowed_statuses` | phase_status_invariants | medium |
| `PhaseStatusInvariantChecker.is_valid_combination` | phase_status_invariants | medium |
| `PhaseStatusInvariantChecker.should_allow_transition` | phase_status_invariants | medium |
| `PolicyDependencyEngine.check_can_activate` | policy_graph_engine | medium |
| `PolicyDependencyEngine.check_can_delete` | policy_graph_engine | medium |
| `PolicyEngine.add_dependency_with_dag_check` | engine | medium |
| `PolicyEngine.evaluate` | engine | medium |
| `PolicyEngine.evaluate_with_context` | engine | medium |
| `PolicyEngine.pre_check` | engine | medium |
| `PolicyEngine.validate_dependency_dag` | engine | medium |
| `PolicyProposalEngine.check_proposal_eligibility` | policy_proposal_engine | ambiguous |
| `PolicySnapshotData.verify_integrity` | snapshot_engine | ambiguous |
| `PolicySnapshotData.verify_threshold_integrity` | snapshot_engine | ambiguous |
| `PolicySnapshotRegistry.verify` | snapshot_engine | ambiguous |
| `PolicyValidator.validate` | validator | medium |
| `PreventionEngine.evaluate_step` | prevention_engine | medium |
| `PreventionHook.evaluate` | prevention_hook | medium |
| `PreventionResult.allow` | prevention_engine | medium |
| `PrioritizedCheckpoint.check_auto_dismiss` | learning_proof_engine | ambiguous |
| `RecoveryEvaluationEngine.evaluate` | recovery_evaluation_engine | medium |
| `check_phase_status_invariant` | phase_status_invariants | medium |
| `check_policy_violations` | policy_command | medium |
| `check_proposal_eligibility` | policy_proposal_engine | ambiguous |
| `check_safety_limits` | llm_policy_engine | medium |
| `evaluate` | interpreter | medium |
| `evaluate_and_execute` | recovery_evaluation_engine | medium |
| `evaluate_policy` | interpreter | medium |
| `evaluate_policy` | policy_command | medium |
| `evaluate_recovery` | recovery_evaluation_engine | medium |
| `evaluate_response` | prevention_hook | medium |
| `get_enforcement_mode` | kernel | medium |
| `is_model_allowed` | llm_policy_engine | medium |
| `is_valid` | validator | medium |
| `set_enforcement_mode` | kernel | medium |
| `should_allow_new_run` | degraded_mode | medium |
| `should_bypass_governance` | kill_switch | medium |
| `should_evaluate_policy` | binding_moment_enforcer | medium |
| `should_skip_enforcement` | authority_checker | medium |
| `validate` | validator | medium |
| `validate_content_accuracy` | content_accuracy | medium |
| `verify_snapshot` | snapshot_engine | ambiguous |

### Coordinators

| Function | File | Confidence |
|----------|------|------------|
| `GovernanceMetadata.merge_with` | nodes | medium |
| `PolicyEngine.resolve_conflict` | engine | medium |
| `resolve_policy_conflict` | policy_conflict_resolver | ambiguous |

### Helpers

_444 internal helper functions._

- **arbitrator:** `PolicyArbitrator.__init__`, `PolicyArbitrator._get_precedence_map`, `PolicyArbitrator._load_precedence_map`, `PolicyArbitrator._resolve_action_conflict`, `PolicyArbitrator._resolve_limit_conflict`
- **ast:** `BlockAction.to_dict`, `Clause.__post_init__`, `Clause.to_dict`, `ExistsPredicate.to_dict`, `LogicalCondition.to_dict`, `PolicyAST.__post_init__`, `PolicyAST.to_dict`, `PolicyAST.to_json`, `PolicyMetadata.__post_init__`, `PolicyMetadata.to_dict`
  _...and 3 more_
- **authority_checker:** `OverrideAuthorityChecker._is_override_active`, `OverrideCheckResult.to_dict`
- **binding_moment_enforcer:** `_check_fields_changed`, `_mark_evaluated`, `_was_evaluated`
- **claim_decision_engine:** `determine_claim_status`, `get_result_confidence`, `is_candidate_claimable`
- **compiler_parser:** `ParseError.__init__`, `Parser.__init__`, `Parser.advance`, `Parser.current`, `Parser.expect`, `Parser.from_source`, `Parser.match`, `Parser.parse`, `Parser.parse_action_block`, `Parser.parse_and_expr`
  _...and 17 more_
- **content_accuracy:** `ContentAccuracyResult.to_dict`, `ContentAccuracyValidator.__init__`, `ContentAccuracyValidator._claims_affirmative`, `ContentAccuracyValidator._detect_assertion_type`, `ContentAccuracyValidator._extract_claim`, `ContentAccuracyValidator._get_nested_value`
- **customer_policy_read_engine:** `CustomerPolicyReadService.__init__`, `CustomerPolicyReadService._calculate_period_bounds`, `CustomerPolicyReadService._get_budget_constraint`, `CustomerPolicyReadService._get_guardrails`, `CustomerPolicyReadService._get_rate_limits`
- **decorator:** `_extract_subject`, `_extract_tenant_id`
- **deterministic_engine:** `DeterministicEngine.__init__`, `DeterministicEngine._action_to_intent_type`, `DeterministicEngine._call_function`, `DeterministicEngine._eval_binary_op`, `DeterministicEngine._eval_compare`, `DeterministicEngine._eval_unary_op`, `DeterministicEngine._execute_function`, `DeterministicEngine._execute_instruction`, `DeterministicEngine._register_builtins`, `ExecutionContext.__post_init__`
  _...and 1 more_
- **dsl_parser:** `Lexer.__init__`, `Lexer._advance`, `Lexer._convert_value`, `Lexer.tokenize`, `ParseError.__init__`, `ParseLocation.__str__`, `Parser.__init__`, `Parser._parse_actions`, `Parser._parse_and_expr`, `Parser._parse_atom`
  _...and 15 more_
- **eligibility_engine:** `DefaultCapabilityLookup.__init__`, `DefaultContractLookup.__init__`, `DefaultGovernanceSignalLookup.__init__`, `DefaultPreApprovalLookup.__init__`, `DefaultSystemHealthLookup.__init__`, `EligibilityEngine.__init__`, `EligibilityEngine._create_verdict`, `EligibilityEngine._evaluate_e001_confidence_threshold`, `EligibilityEngine._evaluate_e002_known_capability`, `EligibilityEngine._evaluate_e003_no_blocking_signal`
  _...and 8 more_
- **engine:** `PolicyEngine.__init__`, `PolicyEngine._add_windowed_value`, `PolicyEngine._check_business_rules`, `PolicyEngine._check_compliance`, `PolicyEngine._check_cooldown`, `PolicyEngine._check_ethical_constraints`, `PolicyEngine._check_risk_ceilings`, `PolicyEngine._check_safety_rules`, `PolicyEngine._classify_recoverability`, `PolicyEngine._classify_severity`
  _...and 13 more_
- **folds:** `ConstantFolder.__init__`, `ConstantFolder._fold_binary_op`, `ConstantFolder._fold_compare`, `ConstantFolder._fold_unary_op`, `DeadCodeEliminator.__init__`, `DeadCodeEliminator._eliminate_function`, `DeadCodeEliminator._find_reachable_blocks`, `DeadCodeEliminator._find_used_instructions`, `DeadCodeEliminator._mark_governance_critical`, `PolicySimplifier.__init__`
  _...and 2 more_
- **governance_facade:** `GovernanceFacade.__init__`
- **intent:** `Intent.__post_init__`, `Intent._generate_id`, `IntentEmitter.__init__`
- **interpreter:** `ActionResult.to_dict`, `ClauseResult.to_dict`, `EvaluationError.__init__`, `EvaluationResult.to_dict`, `Interpreter.__init__`, `Interpreter._collect_actions`, `Interpreter._compare`, `Interpreter._evaluate_clause`, `Interpreter._evaluate_condition`, `Interpreter._execute_instruction`
  _...and 3 more_
- **ir_builder:** `IRBuilder.__init__`, `IRBuilder._emit`, `IRBuilder._new_block`, `IRBuilder._next_block_name`, `IRBuilder._next_id`
- **ir_compiler:** `CompiledClause.to_dict`, `IRCompiler.__init__`, `IRCompiler._compile_actions`, `IRCompiler._compile_clause`, `IRCompiler._compile_condition`, `IRCompiler._emit_condition`, `IRCompiler._emit_exists`, `IRCompiler._emit_logical`, `IRCompiler._emit_predicate`, `Instruction.to_dict`
  _...and 3 more_
- **ir_nodes:** `IRAction.__str__`, `IRBinaryOp.__str__`, `IRBlock.__str__`, `IRCall.__str__`, `IRCheckPolicy.__str__`, `IRCompare.__str__`, `IREmitIntent.__str__`, `IRFunction.__str__`, `IRGovernance.from_ast`, `IRGovernance.to_dict`
  _...and 9 more_
- **kernel:** `ExecutionKernel._emit_envelope`, `ExecutionKernel._record_invocation_complete`, `ExecutionKernel._record_invocation_start`
- **keys_shim:** `KeysReadService.__init__`, `KeysReadService.get_key`, `KeysReadService.get_key_usage_today`, `KeysReadService.list_keys`, `KeysWriteService.__init__`, `KeysWriteService.freeze_key`, `KeysWriteService.unfreeze_key`, `get_keys_read_service`, `get_keys_write_service`
- **learning_proof_engine:** `M25GraduationStatus._get_next_action`, `M25GraduationStatus.to_dashboard`, `PatternCalibration._recalibrate`, `PolicyRegretTracker._trigger_demotion`, `PolicyRegretTracker.to_rollback_timeline`, `PreventionRecord.to_console_timeline`, `PreventionTimeline._generate_narrative`, `PreventionTimeline.to_console`
- **lessons_engine:** `LessonsLearnedEngine.__init__`, `LessonsLearnedEngine._create_lesson`, `LessonsLearnedEngine._generate_failure_description`, `LessonsLearnedEngine._generate_failure_proposed_action`, `LessonsLearnedEngine._get_driver`, `LessonsLearnedEngine._is_debounced`
- **limits_facade:** `LimitsFacade.__init__`, `LimitsFacade._get_or_create_limit`
- **llm_policy_engine:** `LLMRateLimiter.__init__`
- **nodes:** `PolicyDeclNode.__post_init__`, `RuleDeclNode.__post_init__`
- **optimizer_conflict_resolver:** `ConflictResolver.__init__`, `ConflictResolver._detect_action_conflicts`, `ConflictResolver._detect_category_conflicts`, `ConflictResolver._detect_circular_dependencies`, `ConflictResolver._detect_priority_conflicts`, `ConflictResolver._get_actions`, `ConflictResolver._get_condition_signature`, `ConflictResolver._might_override`, `ConflictResolver._resolve_action_conflict`, `ConflictResolver._resolve_category_conflict`
  _...and 4 more_
- **phase_status_invariants:** `InvariantCheckResponse.to_dict`, `PhaseStatusInvariantChecker.__init__`, `PhaseStatusInvariantChecker.from_governance_config`, `PhaseStatusInvariantEnforcementError.__init__`, `PhaseStatusInvariantEnforcementError.to_dict`
- **plan:** `Plan.__post_init__`, `PlanTier.from_string`
- **plan_generation_engine:** `PlanGenerationEngine.__init__`
- **policies_limits_query_engine:** `LimitsQueryEngine.__init__`, `LimitsQueryEngine.get_limit_detail`, `LimitsQueryEngine.list_budgets`, `LimitsQueryEngine.list_limits`, `get_limits_query_engine`
- **policies_proposals_query_engine:** `ProposalsQueryEngine.__init__`, `ProposalsQueryEngine.count_drafts`, `ProposalsQueryEngine.get_policy_request_detail`, `get_proposals_query_engine`
- **policies_rules_query_engine:** `PolicyRulesQueryEngine.__init__`, `PolicyRulesQueryEngine.count_rules`, `PolicyRulesQueryEngine.get_policy_rule_detail`, `PolicyRulesQueryEngine.list_policy_rules`, `get_policy_rules_query_engine`
- **policy_command:** `_record_approval_action`, `_record_approval_escalation`, `_record_approval_request_created`, `_record_budget_rejection`, `_record_capability_violation`, `_record_policy_decision`, `_record_webhook_fallback`
- **policy_conflict_resolver:** `create_conflict_log`, `get_action_severity`, `is_more_restrictive`
- **policy_driver:** `PolicyDriver.__init__`, `PolicyDriver._engine`
- **policy_engine_driver:** `PolicyEngineDriver.__init__`, `PolicyEngineDriver._get_engine`
- **policy_graph_driver:** `PolicyGraphDriver.__init__`
- **policy_graph_engine:** `ConflictDetectionResult.to_dict`, `DependencyGraphResult.to_dict`, `PolicyConflict.to_dict`, `PolicyConflictEngine.__init__`, `PolicyConflictEngine._detect_priority_overrides`, `PolicyConflictEngine._detect_scope_overlaps`, `PolicyConflictEngine._detect_temporal_conflicts`, `PolicyConflictEngine._detect_threshold_contradictions`, `PolicyConflictEngine._has_contradicting_conditions`, `PolicyConflictEngine._involves_policy`
  _...and 7 more_
- **policy_limits_engine:** `PolicyLimitsService.__init__`, `PolicyLimitsService._get_limit`, `PolicyLimitsService._to_response`, `PolicyLimitsService._validate_category_fields`
- **policy_mapper:** `MCPPolicyDecision.to_dict`, `MCPPolicyMapper.__init__`, `MCPPolicyMapper._check_explicit_allow`, `MCPPolicyMapper._check_rate_limit`, `MCPPolicyMapper._evaluate_policy`, `MCPPolicyMapper._get_policy_engine`
- **policy_proposal_engine:** `PolicyActivationBlockedError.__init__`, `PolicyDeletionBlockedError.__init__`, `PolicyProposalEngine.__init__`, `PolicyProposalEngine._create_policy_rule_from_proposal`, `PolicyProposalEngine.create_proposal`, `PolicyProposalEngine.delete_policy_rule`, `PolicyProposalEngine.get_proposal_summary`, `PolicyProposalEngine.review_proposal`, `create_policy_proposal`, `delete_policy_rule`
  _...and 4 more_
- **policy_proposal_read_driver:** `PolicyProposalReadDriver.__init__`
- **policy_proposal_write_driver:** `PolicyProposalWriteDriver.__init__`
- **policy_read_driver:** `PolicyReadDriver.__init__`, `PolicyReadDriver._to_guardrail_dto`
- **policy_rules_driver:** `PolicyRulesDriver.__init__`
- **policy_rules_engine:** `PolicyRulesService.__init__`, `PolicyRulesService._compute_hash`, `PolicyRulesService._get_rule`, `PolicyRulesService._to_response`, `PolicyRulesService._validate_conditions`
- **policy_rules_read_driver:** `PolicyRulesReadDriver.__init__`
- **prevention_engine:** `PolicyViolationError.__init__`, `PreventionEngine.__init__`, `PreventionEngine._evaluate_custom_policy`, `PreventionEngine._evaluate_step_inner`
- **prevention_hook:** `PreventionContext.__post_init__`, `PreventionHook.__init__`, `PreventionResult.__post_init__`, `PreventionResult.to_dict`
- **proposals_read_driver:** `ProposalsReadDriver.__init__`
- **protection_provider:** `AbuseProtectionProvider.detect_anomaly`, `MockAbuseProtectionProvider.__init__`, `MockAbuseProtectionProvider.add_cost`, `MockAbuseProtectionProvider.detect_anomaly`, `MockAbuseProtectionProvider.reset`, `MockAbuseProtectionProvider.reset_rate_limits`, `get_protection_provider`, `set_protection_provider`
- **recovery_evaluation_engine:** `FailureContext.__post_init__`, `RecoveryDecision.to_dict`, `RecoveryEvaluationEngine.__init__`
- **recovery_matcher:** `RecoveryMatcher.__init__`, `RecoveryMatcher._calculate_time_weight`, `RecoveryMatcher._compute_confidence`, `RecoveryMatcher._count_occurrences`, `RecoveryMatcher._escalate_to_llm`, `RecoveryMatcher._find_similar_by_embedding`, `RecoveryMatcher._find_similar_failures`, `RecoveryMatcher._generate_suggestion`, `RecoveryMatcher._get_cached_recovery`, `RecoveryMatcher._normalize_error`
  _...and 2 more_
- **recovery_write_driver:** `RecoveryWriteService.__init__`
- **sandbox_engine:** `ExecutionRecord.to_dict`, `SandboxPolicy.to_dict`, `SandboxPolicy.to_resource_limits`, `SandboxService.__init__`, `SandboxService._check_quota`, `SandboxService._get_executor`, `SandboxService._get_policy`, `SandboxService._setup_default_policies`, `SandboxService._track_execution`, `SandboxService.define_policy`
  _...and 5 more_
- **scope_resolver:** `ScopeResolver.__init__`, `ScopeResolver._get_scope`, `ScopeResolver._load_scopes`
- **snapshot_engine:** `PolicySnapshotData.compute_hash`, `PolicySnapshotData.get_policies`, `PolicySnapshotData.get_thresholds`, `PolicySnapshotData.to_dict`, `PolicySnapshotError.__init__`, `PolicySnapshotError.to_dict`, `PolicySnapshotRegistry.__init__`, `PolicySnapshotRegistry._get_next_version`, `PolicySnapshotRegistry._supersede_active`, `PolicySnapshotRegistry.archive`
  _...and 17 more_
- **state:** `BillingState.from_string`
- **symbol_table:** `Symbol.__repr__`, `SymbolTable.__init__`, `SymbolTable.__str__`, `SymbolTable._define_builtins`
- **tokenizer:** `Token.__repr__`, `Tokenizer.__init__`, `Tokenizer.__iter__`, `TokenizerError.__init__`
- **validator:** `PolicyValidator.__init__`, `PolicyValidator._check_warnings`, `PolicyValidator._extract_metrics`, `PolicyValidator._validate_metrics`, `PolicyValidator._validate_mode_enforcement`, `PolicyValidator._validate_structure`, `ValidationIssue.__str__`, `ValidationResult.__bool__`, `ValidationResult.__post_init__`
- **visitors:** `CategoryCollector.__init__`, `PrintVisitor.__init__`, `PrintVisitor._emit`, `RuleExtractor.__init__`
- **worker_execution_command:** `convert_brand_request`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `ConflictResolver.resolve` | optimizer_conflict_resolver | pure |
| `PolicyArbitrator.arbitrate` | arbitrator | pure |
| `PolicyEngineDriver.activate_version` | policy_engine_driver | pure |
| `PolicyEngineDriver.cap_temporal_events` | policy_engine_driver | pure |
| `PolicyEngineDriver.compact_temporal_events` | policy_engine_driver | pure |
| `PolicyEngineDriver.deactivate_all_versions` | policy_engine_driver | pure |
| `PolicyEngineDriver.delete_old_temporal_events` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_active_policies_for_integrity` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_business_rules` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_conflicts` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_current_active_version` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_dependencies` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_dependency_edges` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_dependency_edges_with_type` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_ethical_constraints` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_ethical_constraints_for_integrity` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_policy_version_by_id` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_policy_version_by_id_or_version` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_policy_versions` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_provenance` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_risk_ceilings` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_safety_rules` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_temporal_metric_sum` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_temporal_policies` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_temporal_policies_for_integrity` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_temporal_policy_for_utilization` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_temporal_stats` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_temporal_storage_stats` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_unresolved_conflicts` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_version_for_rollback` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_violation_by_id` | policy_engine_driver | pure |
| `PolicyEngineDriver.fetch_violations` | policy_engine_driver | pure |
| `PolicyEngineDriver.insert_dependency` | policy_engine_driver | pure |
| `PolicyEngineDriver.insert_evaluation` | policy_engine_driver | pure |
| `PolicyEngineDriver.insert_policy_version` | policy_engine_driver | pure |
| `PolicyEngineDriver.insert_provenance` | policy_engine_driver | pure |
| `PolicyEngineDriver.insert_temporal_policy` | policy_engine_driver | pure |
| `PolicyEngineDriver.insert_violation` | policy_engine_driver | pure |
| `PolicyEngineDriver.mark_version_rolled_back` | policy_engine_driver | pure |
| `PolicyEngineDriver.reset_risk_ceiling` | policy_engine_driver | pure |
| `PolicyEngineDriver.resolve_conflict` | policy_engine_driver | pure |
| `PolicyEngineDriver.update_risk_ceiling` | policy_engine_driver | pure |
| `PolicyEngineDriver.update_safety_rule` | policy_engine_driver | pure |
| `PolicyEngineDriver.update_violation_acknowledged` | policy_engine_driver | pure |
| `PolicyGraphDriver.fetch_active_limits` | policy_graph_driver | db_write |
| `PolicyGraphDriver.fetch_active_policies` | policy_graph_driver | db_write |
| `PolicyGraphDriver.fetch_all_limits` | policy_graph_driver | db_write |
| `PolicyGraphDriver.fetch_all_policies` | policy_graph_driver | db_write |
| `PolicyGraphDriver.fetch_resolved_conflicts` | policy_graph_driver | db_write |
| `PolicyProposalReadDriver.check_rule_exists` | policy_proposal_read_driver | db_write |
| `PolicyProposalReadDriver.count_versions_for_proposal` | policy_proposal_read_driver | db_write |
| `PolicyProposalReadDriver.fetch_proposal_by_id` | policy_proposal_read_driver | db_write |
| `PolicyProposalReadDriver.fetch_proposal_status` | policy_proposal_read_driver | db_write |
| `PolicyProposalReadDriver.fetch_proposals` | policy_proposal_read_driver | db_write |
| `PolicyProposalReadDriver.fetch_rule_by_id` | policy_proposal_read_driver | db_write |
| `PolicyProposalReadDriver.fetch_unacknowledged_feedback` | policy_proposal_read_driver | db_write |
| `PolicyProposalWriteDriver.create_policy_rule` | policy_proposal_write_driver | db_write |
| `PolicyProposalWriteDriver.create_proposal` | policy_proposal_write_driver | db_write |
| `PolicyProposalWriteDriver.create_version` | policy_proposal_write_driver | db_write |
| `PolicyProposalWriteDriver.delete_policy_rule` | policy_proposal_write_driver | db_write |
| `PolicyProposalWriteDriver.update_proposal_status` | policy_proposal_write_driver | db_write |
| `PolicyReadDriver.get_guardrail_by_id` | policy_read_driver | pure |
| `PolicyReadDriver.get_tenant_budget_settings` | policy_read_driver | pure |
| `PolicyReadDriver.get_usage_sum_since` | policy_read_driver | pure |
| `PolicyReadDriver.list_all_guardrails` | policy_read_driver | pure |
| `PolicyRulesDriver.add_integrity` | policy_rules_driver | db_write |
| `PolicyRulesDriver.add_rule` | policy_rules_driver | db_write |
| `PolicyRulesDriver.fetch_rule_by_id` | policy_rules_driver | db_write |
| `PolicyRulesDriver.flush` | policy_rules_driver | db_write |
| `PolicyRulesReadDriver.count_policy_rules` | policy_rules_read_driver | db_write |
| `PolicyRulesReadDriver.fetch_policy_rule_by_id` | policy_rules_read_driver | db_write |
| `PolicyRulesReadDriver.fetch_policy_rules` | policy_rules_read_driver | db_write |
| `ProposalsReadDriver.count_draft_proposals` | proposals_read_driver | db_write |
| `ProposalsReadDriver.fetch_proposal_by_id` | proposals_read_driver | db_write |
| `ProposalsReadDriver.fetch_proposals` | proposals_read_driver | db_write |
| `RecoveryMatcher.approve_candidate` | recovery_matcher | db_write |
| `RecoveryMatcher.get_candidates` | recovery_matcher | db_write |
| `RecoveryMatcher.suggest` | recovery_matcher | pure |
| `RecoveryMatcher.suggest_hybrid` | recovery_matcher | pure |
| `RecoveryWriteService.enqueue_evaluation_db_fallback` | recovery_write_driver | db_write |
| `RecoveryWriteService.get_candidate_by_idempotency_key` | recovery_write_driver | db_write |
| `RecoveryWriteService.insert_suggestion_provenance` | recovery_write_driver | db_write |
| `RecoveryWriteService.update_recovery_candidate` | recovery_write_driver | db_write |
| `RecoveryWriteService.upsert_recovery_candidate` | recovery_write_driver | db_write |
| `Scope.define` | symbol_table | pure |
| `Scope.get_all_symbols` | symbol_table | pure |
| `Scope.lookup` | symbol_table | pure |
| `Scope.lookup_by_category` | symbol_table | pure |
| `ScopeResolutionResult.to_snapshot` | scope_resolver | pure |
| `ScopeResolver.get_scope_for_policy` | scope_resolver | pure |
| `ScopeResolver.matches_scope` | scope_resolver | pure |
| `ScopeResolver.resolve_applicable_policies` | scope_resolver | pure |
| `SymbolTable.add_reference` | symbol_table | pure |
| `SymbolTable.define` | symbol_table | pure |
| `SymbolTable.enter_scope` | symbol_table | pure |
| `SymbolTable.exit_scope` | symbol_table | pure |
| `SymbolTable.get_policies` | symbol_table | pure |
| `SymbolTable.get_rules` | symbol_table | pure |
| `SymbolTable.get_symbols_by_category` | symbol_table | pure |
| `SymbolTable.get_unreferenced_symbols` | symbol_table | pure |
| `SymbolTable.lookup` | symbol_table | pure |
| `SymbolTable.lookup_policy` | symbol_table | pure |
| `SymbolTable.lookup_rule` | symbol_table | pure |
| `get_policy_arbitrator` | arbitrator | pure |
| `get_policy_engine_driver` | policy_engine_driver | pure |
| `get_policy_graph_driver` | policy_graph_driver | pure |
| `get_policy_proposal_read_driver` | policy_proposal_read_driver | pure |
| `get_policy_proposal_write_driver` | policy_proposal_write_driver | pure |
| `get_policy_read_driver` | policy_read_driver | pure |
| `get_policy_rules_driver` | policy_rules_driver | pure |
| `get_policy_rules_read_driver` | policy_rules_read_driver | pure |
| `get_proposals_read_driver` | proposals_read_driver | pure |
| `get_scope_resolver` | scope_resolver | pure |

### Unclassified (needs review)

_269 functions need manual classification._

- `ASTNode.accept` (nodes)
- `ASTNode.location` (nodes)
- `ASTVisitor.visit_action_block` (nodes)
- `ASTVisitor.visit_attr_access` (nodes)
- `ASTVisitor.visit_binary_op` (nodes)
- `ASTVisitor.visit_condition_block` (nodes)
- `ASTVisitor.visit_func_call` (nodes)
- `ASTVisitor.visit_ident` (nodes)
- `ASTVisitor.visit_import` (nodes)
- `ASTVisitor.visit_literal` (nodes)
- `ASTVisitor.visit_policy_decl` (nodes)
- `ASTVisitor.visit_priority` (nodes)
- `ASTVisitor.visit_program` (nodes)
- `ASTVisitor.visit_route_target` (nodes)
- `ASTVisitor.visit_rule_decl` (nodes)
- `ASTVisitor.visit_rule_ref` (nodes)
- `ASTVisitor.visit_unary_op` (nodes)
- `ActionBlockNode.accept` (nodes)
- `AdaptiveConfidenceSystem.get_confidence_report` (learning_proof_engine)
- `AdaptiveConfidenceSystem.get_or_create_calibration` (learning_proof_engine)
- _...and 249 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in POLICIES_DOMAIN_LOCK_FINAL.md._
