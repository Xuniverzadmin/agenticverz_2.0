# Policies — Call Graph

**Domain:** policies  
**Total functions:** 1020  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 48 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 127 | Calls other functions + adds its own decisions |
| WRAPPER | 442 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 163 | Terminal — calls no other domain functions |
| ENTRY | 53 | Entry point — no domain-internal callers |
| INTERNAL | 187 | Called only by other domain functions |

## Canonical Algorithm Owners

### `arbitrator.PolicyArbitrator.arbitrate`
- **Layer:** L6
- **Decisions:** 7
- **Statements:** 15
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** arbitrator.PolicyArbitrator.arbitrate → arbitrator.PolicyArbitrator._load_precedence_map → arbitrator.PolicyArbitrator._resolve_action_conflict → arbitrator.PolicyArbitrator._resolve_limit_conflict → ...+4
- **Calls:** arbitrator:PolicyArbitrator._load_precedence_map, arbitrator:PolicyArbitrator._resolve_action_conflict, arbitrator:PolicyArbitrator._resolve_limit_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_action_conflict, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `authority_checker.OverrideAuthorityChecker.check`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 13
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** authority_checker.OverrideAuthorityChecker.check → authority_checker.OverrideAuthorityChecker._is_override_active
- **Calls:** authority_checker:OverrideAuthorityChecker._is_override_active

### `compiler_parser.Parser.parse_value`
- **Layer:** L5
- **Decisions:** 9
- **Statements:** 8
- **Delegation depth:** 6
- **Persistence:** no
- **Chain:** compiler_parser.Parser.parse_value → compiler_parser.Parser.advance → compiler_parser.Parser.expect → compiler_parser.Parser.match → ...+4
- **Calls:** compiler_parser:Parser.advance, compiler_parser:Parser.expect, compiler_parser:Parser.match, compiler_parser:Parser.parse_expr, compiler_parser:Parser.parse_func_call, dsl_parser:Parser.expect, tokenizer:Tokenizer.advance

### `content_accuracy.ContentAccuracyValidator.validate`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 6
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** content_accuracy.ContentAccuracyValidator.validate → content_accuracy.ContentAccuracyValidator._claims_affirmative → content_accuracy.ContentAccuracyValidator._detect_assertion_type → content_accuracy.ContentAccuracyValidator._extract_claim → ...+1
- **Calls:** content_accuracy:ContentAccuracyValidator._claims_affirmative, content_accuracy:ContentAccuracyValidator._detect_assertion_type, content_accuracy:ContentAccuracyValidator._extract_claim, content_accuracy:ContentAccuracyValidator._get_nested_value

### `customer_policy_read_engine.CustomerPolicyReadService.get_guardrail_detail`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 5
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** customer_policy_read_engine.CustomerPolicyReadService.get_guardrail_detail → policy_read_driver.PolicyReadDriver.get_guardrail_by_id
- **Calls:** policy_read_driver:PolicyReadDriver.get_guardrail_by_id

### `decorator.governed`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 2
- **Delegation depth:** 14
- **Persistence:** no
- **Chain:** decorator.governed → decorator._extract_subject → decorator._extract_tenant_id → kernel.ExecutionKernel.invoke → ...+1
- **Calls:** decorator:_extract_subject, decorator:_extract_tenant_id, kernel:ExecutionKernel.invoke, kernel:ExecutionKernel.invoke_async

### `degraded_mode.exit_degraded_mode`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 5
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** degraded_mode.exit_degraded_mode → degraded_mode.DegradedModeStatus.get_inactive
- **Calls:** degraded_mode:DegradedModeStatus.get_inactive

### `deterministic_engine.ExecutionContext.get_variable`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 5
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** deterministic_engine.ExecutionContext.get_variable → policy_limits_engine.PolicyLimitsService.get → policy_rules_engine.PolicyRulesService.get → snapshot_engine.PolicySnapshotRegistry.get
- **Calls:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `dsl_parser.Lexer.tokenize`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 4
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** dsl_parser.Lexer.tokenize → compiler_parser.Parser.match → dsl_parser.Lexer._advance → dsl_parser.Lexer._convert_value
- **Calls:** compiler_parser:Parser.match, dsl_parser:Lexer._advance, dsl_parser:Lexer._convert_value

### `eligibility_engine.EligibilityEngine.evaluate`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 8
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** eligibility_engine.EligibilityEngine.evaluate → eligibility_engine.EligibilityEngine._create_verdict
- **Calls:** eligibility_engine:EligibilityEngine._create_verdict

### `engine.PolicyEngine.evaluate`
- **Layer:** L5
- **Decisions:** 19
- **Statements:** 36
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** engine.PolicyEngine.evaluate → engine.PolicyEngine._check_business_rules → engine.PolicyEngine._check_compliance → engine.PolicyEngine._check_cooldown → ...+7
- **Calls:** engine:PolicyEngine._check_business_rules, engine:PolicyEngine._check_compliance, engine:PolicyEngine._check_cooldown, engine:PolicyEngine._check_ethical_constraints, engine:PolicyEngine._check_risk_ceilings, engine:PolicyEngine._check_safety_rules, engine:PolicyEngine._is_cache_stale, engine:PolicyEngine._load_policies, engine:PolicyEngine._persist_evaluation, engine:PolicyEngine._route_to_governor

### `failure_mode_handler.handle_policy_failure`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 9
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** failure_mode_handler.handle_policy_failure → dsl_parser.Parser.error → failure_mode_handler.get_failure_mode → policy_limits_engine.PolicyLimitsService.get → ...+2
- **Calls:** dsl_parser:Parser.error, failure_mode_handler:get_failure_mode, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `folds.ConstantFolder.try_fold`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 5
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** folds.ConstantFolder.try_fold → folds.ConstantFolder._fold_binary_op → folds.ConstantFolder._fold_compare → folds.ConstantFolder._fold_unary_op
- **Calls:** folds:ConstantFolder._fold_binary_op, folds:ConstantFolder._fold_compare, folds:ConstantFolder._fold_unary_op

### `governance_facade.GovernanceFacade.set_mode`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 2
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** governance_facade.GovernanceFacade.set_mode → degraded_mode.enter_degraded_mode → degraded_mode.exit_degraded_mode → dsl_parser.Parser.error
- **Calls:** degraded_mode:enter_degraded_mode, degraded_mode:exit_degraded_mode, dsl_parser:Parser.error

### `interpreter.Interpreter.evaluate`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 5
- **Delegation depth:** 14
- **Persistence:** no
- **Chain:** interpreter.Interpreter.evaluate → interpreter.Interpreter._evaluate_clause
- **Calls:** interpreter:Interpreter._evaluate_clause

### `ir_builder.IRBuilder.visit_rule_decl`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 18
- **Delegation depth:** 22
- **Persistence:** no
- **Chain:** ir_builder.IRBuilder.visit_rule_decl → dsl_parser.Parser.accept → ir_builder.IRBuilder._emit → ir_builder.IRBuilder._new_block → ...+23
- **Calls:** dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, ir_builder:IRBuilder._new_block, ir_nodes:IRGovernance.from_ast, ir_nodes:IRModule.add_function, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept, symbol_table:Scope.define, symbol_table:SymbolTable.define, symbol_table:SymbolTable.enter_scope, symbol_table:SymbolTable.exit_scope, visitors:PrintVisitor._emit

### `kernel.ExecutionKernel.invoke_async`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 8
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** kernel.ExecutionKernel.invoke_async → kernel.ExecutionKernel._emit_envelope → kernel.ExecutionKernel._record_invocation_complete → kernel.ExecutionKernel._record_invocation_start → ...+1
- **Calls:** kernel:ExecutionKernel._emit_envelope, kernel:ExecutionKernel._record_invocation_complete, kernel:ExecutionKernel._record_invocation_start, kernel:get_enforcement_mode

### `learning_proof_engine.PolicyRegretTracker.add_regret`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 5
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** learning_proof_engine.PolicyRegretTracker.add_regret → learning_proof_engine.PolicyRegretTracker._trigger_demotion
- **Calls:** learning_proof_engine:PolicyRegretTracker._trigger_demotion

### `lessons_engine.LessonsLearnedEngine.detect_lesson_from_near_threshold`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 7
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** lessons_engine.LessonsLearnedEngine.detect_lesson_from_near_threshold → lessons_engine.LessonsLearnedEngine._create_lesson → lessons_engine.LessonsLearnedEngine._is_debounced → lessons_engine.get_threshold_band
- **Calls:** lessons_engine:LessonsLearnedEngine._create_lesson, lessons_engine:LessonsLearnedEngine._is_debounced, lessons_engine:get_threshold_band

### `limits_facade.LimitsFacade.update_limit`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 9
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** limits_facade.LimitsFacade.update_limit → policy_limits_engine.PolicyLimitsService.update → policy_rules_engine.PolicyRulesService.update
- **Calls:** policy_limits_engine:PolicyLimitsService.update, policy_rules_engine:PolicyRulesService.update

### `llm_policy_engine.check_safety_limits`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 9
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** llm_policy_engine.check_safety_limits → llm_policy_engine.LLMRateLimiter.check_and_record → llm_policy_engine.LLMRateLimiter.get_instance → llm_policy_engine.LLMRateLimiter.requests_remaining → ...+1
- **Calls:** llm_policy_engine:LLMRateLimiter.check_and_record, llm_policy_engine:LLMRateLimiter.get_instance, llm_policy_engine:LLMRateLimiter.requests_remaining, llm_policy_engine:estimate_cost_cents

### `phase_status_invariants.PhaseStatusInvariantChecker.check`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 6
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** phase_status_invariants.PhaseStatusInvariantChecker.check → phase_status_invariants.PhaseStatusInvariantChecker.get_allowed_statuses
- **Calls:** phase_status_invariants:PhaseStatusInvariantChecker.get_allowed_statuses

### `plan_generation_engine.PlanGenerationEngine.generate`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 11
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** plan_generation_engine.PlanGenerationEngine.generate → dsl_parser.Parser.error → policy_limits_engine.PolicyLimitsService.get → policy_rules_engine.PolicyRulesService.get → ...+1
- **Calls:** dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policies_proposals_query_engine.ProposalsQueryEngine.list_policy_requests`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 7
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** policies_proposals_query_engine.ProposalsQueryEngine.list_policy_requests → policy_proposal_read_driver.PolicyProposalReadDriver.fetch_proposals → proposals_read_driver.ProposalsReadDriver.fetch_proposals
- **Calls:** policy_proposal_read_driver:PolicyProposalReadDriver.fetch_proposals, proposals_read_driver:ProposalsReadDriver.fetch_proposals

### `policies_rules_query_engine.PolicyRulesQueryEngine.list_policy_rules`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 10
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** policies_rules_query_engine.PolicyRulesQueryEngine.list_policy_rules → policy_rules_read_driver.PolicyRulesReadDriver.fetch_policy_rules
- **Calls:** policy_rules_read_driver:PolicyRulesReadDriver.fetch_policy_rules

### `policy_command.evaluate_policy`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 4
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** policy_command.evaluate_policy → policy_command._record_policy_decision → policy_command.check_policy_violations → policy_command.simulate_cost
- **Calls:** policy_command:_record_policy_decision, policy_command:check_policy_violations, policy_command:simulate_cost

### `policy_conflict_resolver.resolve_policy_conflict`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 11
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** policy_conflict_resolver.resolve_policy_conflict → policy_limits_engine.PolicyLimitsService.get → policy_rules_engine.PolicyRulesService.get → snapshot_engine.PolicySnapshotRegistry.get
- **Calls:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_engine_driver.PolicyEngineDriver.fetch_violations`
- **Layer:** L6
- **Decisions:** 5
- **Statements:** 11
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** policy_engine_driver.PolicyEngineDriver.fetch_violations → deterministic_engine.DeterministicEngine.execute → sandbox_engine.SandboxService.execute
- **Calls:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `policy_graph_engine.PolicyConflictEngine.detect_conflicts`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 12
- **Delegation depth:** 13
- **Persistence:** no
- **Chain:** policy_graph_engine.PolicyConflictEngine.detect_conflicts → policy_graph_driver.PolicyGraphDriver.fetch_active_policies → policy_graph_driver.PolicyGraphDriver.fetch_resolved_conflicts → policy_graph_engine.PolicyConflictEngine._detect_priority_overrides → ...+4
- **Calls:** policy_graph_driver:PolicyGraphDriver.fetch_active_policies, policy_graph_driver:PolicyGraphDriver.fetch_resolved_conflicts, policy_graph_engine:PolicyConflictEngine._detect_priority_overrides, policy_graph_engine:PolicyConflictEngine._detect_scope_overlaps, policy_graph_engine:PolicyConflictEngine._detect_temporal_conflicts, policy_graph_engine:PolicyConflictEngine._detect_threshold_contradictions, policy_graph_engine:PolicyConflictEngine._involves_policy

### `policy_limits_engine.PolicyLimitsService.update`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 4
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** policy_limits_engine.PolicyLimitsService.update → policy_limits_engine.PolicyLimitsService._get_limit → policy_limits_engine.PolicyLimitsService._to_response → policy_rules_engine.PolicyRulesService._to_response
- **Calls:** policy_limits_engine:PolicyLimitsService._get_limit, policy_limits_engine:PolicyLimitsService._to_response, policy_rules_engine:PolicyRulesService._to_response

### `policy_mapper.MCPPolicyMapper.check_tool_invocation`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 11
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** policy_mapper.MCPPolicyMapper.check_tool_invocation → policy_limits_engine.PolicyLimitsService.get → policy_mapper.MCPPolicyDecision.allow → policy_mapper.MCPPolicyDecision.deny → ...+5
- **Calls:** policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_mapper:MCPPolicyDecision.deny, policy_mapper:MCPPolicyMapper._check_explicit_allow, policy_mapper:MCPPolicyMapper._check_rate_limit, policy_mapper:MCPPolicyMapper._evaluate_policy, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_proposal_engine.PolicyProposalEngine.check_proposal_eligibility`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 8
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** policy_proposal_engine.PolicyProposalEngine.check_proposal_eligibility → policy_limits_engine.PolicyLimitsService.get → policy_proposal_read_driver.PolicyProposalReadDriver.fetch_unacknowledged_feedback → policy_rules_engine.PolicyRulesService.get → ...+1
- **Calls:** policy_limits_engine:PolicyLimitsService.get, policy_proposal_read_driver:PolicyProposalReadDriver.fetch_unacknowledged_feedback, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_proposal_read_driver.PolicyProposalReadDriver.fetch_proposals`
- **Layer:** L6
- **Decisions:** 2
- **Statements:** 7
- **Delegation depth:** 11
- **Persistence:** yes
- **Chain:** policy_proposal_read_driver.PolicyProposalReadDriver.fetch_proposals → deterministic_engine.DeterministicEngine.execute → sandbox_engine.SandboxService.execute
- **Calls:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `policy_rules_engine.PolicyRulesService.update`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 4
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** policy_rules_engine.PolicyRulesService.update → policy_limits_engine.PolicyLimitsService._to_response → policy_rules_engine.PolicyRulesService._get_rule → policy_rules_engine.PolicyRulesService._to_response → ...+1
- **Calls:** policy_limits_engine:PolicyLimitsService._to_response, policy_rules_engine:PolicyRulesService._get_rule, policy_rules_engine:PolicyRulesService._to_response, policy_rules_engine:PolicyRulesService._validate_conditions

### `policy_rules_read_driver.PolicyRulesReadDriver.fetch_policy_rules`
- **Layer:** L6
- **Decisions:** 12
- **Statements:** 22
- **Delegation depth:** 11
- **Persistence:** yes
- **Chain:** policy_rules_read_driver.PolicyRulesReadDriver.fetch_policy_rules → deterministic_engine.DeterministicEngine.execute → sandbox_engine.SandboxService.execute
- **Calls:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `prevention_engine.PreventionEngine.load_snapshot`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 1
- **Delegation depth:** 16
- **Persistence:** no
- **Chain:** prevention_engine.PreventionEngine.load_snapshot → dsl_parser.Parser.error → snapshot_engine.PolicySnapshotData.get_policies → snapshot_engine.PolicySnapshotData.get_thresholds → ...+2
- **Calls:** dsl_parser:Parser.error, snapshot_engine:PolicySnapshotData.get_policies, snapshot_engine:PolicySnapshotData.get_thresholds, snapshot_engine:PolicySnapshotData.verify_integrity, symbol_table:SymbolTable.get_policies

### `prevention_hook.PreventionHook.evaluate`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 6
- **Delegation depth:** 15
- **Persistence:** no
- **Chain:** prevention_hook.PreventionHook.evaluate → content_accuracy.ContentAccuracyValidator.validate → validator.PolicyValidator.validate → validator.validate
- **Calls:** content_accuracy:ContentAccuracyValidator.validate, validator:PolicyValidator.validate, validator:validate

### `proposals_read_driver.ProposalsReadDriver.fetch_proposals`
- **Layer:** L6
- **Decisions:** 4
- **Statements:** 14
- **Delegation depth:** 11
- **Persistence:** yes
- **Chain:** proposals_read_driver.ProposalsReadDriver.fetch_proposals → deterministic_engine.DeterministicEngine.execute → sandbox_engine.SandboxService.execute
- **Calls:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `protection_provider.MockAbuseProtectionProvider.check_all`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 9
- **Delegation depth:** 12
- **Persistence:** no
- **Chain:** protection_provider.MockAbuseProtectionProvider.check_all → policy_mapper.MCPPolicyDecision.allow → prevention_engine.PreventionResult.allow → protection_provider.AbuseProtectionProvider.check_burst → ...+7
- **Calls:** policy_mapper:MCPPolicyDecision.allow, prevention_engine:PreventionResult.allow, protection_provider:AbuseProtectionProvider.check_burst, protection_provider:AbuseProtectionProvider.check_cost, protection_provider:AbuseProtectionProvider.check_rate_limit, protection_provider:AbuseProtectionProvider.detect_anomaly, protection_provider:MockAbuseProtectionProvider.check_burst, protection_provider:MockAbuseProtectionProvider.check_cost, protection_provider:MockAbuseProtectionProvider.check_rate_limit, protection_provider:MockAbuseProtectionProvider.detect_anomaly

### `recovery_matcher.RecoveryMatcher.suggest`
- **Layer:** L6
- **Decisions:** 3
- **Statements:** 19
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** recovery_matcher.RecoveryMatcher.suggest → dsl_parser.Parser.error → policy_limits_engine.PolicyLimitsService.get → policy_rules_engine.PolicyRulesService.get → ...+7
- **Calls:** dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, recovery_matcher:RecoveryMatcher._compute_confidence, recovery_matcher:RecoveryMatcher._count_occurrences, recovery_matcher:RecoveryMatcher._find_similar_failures, recovery_matcher:RecoveryMatcher._generate_suggestion, recovery_matcher:RecoveryMatcher._normalize_error, recovery_matcher:RecoveryMatcher._upsert_candidate, snapshot_engine:PolicySnapshotRegistry.get

### `runtime_command.execute_query`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 2
- **Delegation depth:** 11
- **Persistence:** no
- **Chain:** runtime_command.execute_query → policy_limits_engine.PolicyLimitsService.get → policy_rules_engine.PolicyRulesService.get → runtime_command.query_allowed_skills → ...+5
- **Calls:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, runtime_command:query_allowed_skills, runtime_command:query_execution_history, runtime_command:query_last_step_outcome, runtime_command:query_remaining_budget, runtime_command:query_skills_for_goal, snapshot_engine:PolicySnapshotRegistry.get

### `sandbox_engine.SandboxService.execute`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 19
- **Delegation depth:** 10
- **Persistence:** no
- **Chain:** sandbox_engine.SandboxService.execute → deterministic_engine.DeterministicEngine.execute → sandbox_engine.SandboxPolicy.to_resource_limits → sandbox_engine.SandboxService._check_quota → ...+3
- **Calls:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxPolicy.to_resource_limits, sandbox_engine:SandboxService._check_quota, sandbox_engine:SandboxService._get_executor, sandbox_engine:SandboxService._get_policy, sandbox_engine:SandboxService._track_execution

### `scope_resolver.ScopeResolver.resolve_applicable_policies`
- **Layer:** L6
- **Decisions:** 6
- **Statements:** 11
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** scope_resolver.ScopeResolver.resolve_applicable_policies → scope_resolver.ScopeResolver._load_scopes → scope_resolver.ScopeResolver.matches_scope → snapshot_engine.PolicySnapshotRegistry.list
- **Calls:** scope_resolver:ScopeResolver._load_scopes, scope_resolver:ScopeResolver.matches_scope, snapshot_engine:PolicySnapshotRegistry.list

### `snapshot_engine.PolicySnapshotRegistry.create`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 13
- **Delegation depth:** 14
- **Persistence:** no
- **Chain:** snapshot_engine.PolicySnapshotRegistry.create → snapshot_engine.PolicySnapshotData.compute_hash → snapshot_engine.PolicySnapshotRegistry._get_next_version → snapshot_engine.PolicySnapshotRegistry._supersede_active
- **Calls:** snapshot_engine:PolicySnapshotData.compute_hash, snapshot_engine:PolicySnapshotRegistry._get_next_version, snapshot_engine:PolicySnapshotRegistry._supersede_active

### `symbol_table.SymbolTable.lookup_rule`
- **Layer:** L6
- **Decisions:** 5
- **Statements:** 4
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** symbol_table.SymbolTable.lookup_rule → symbol_table.Scope.lookup → symbol_table.SymbolTable.lookup → symbol_table.SymbolTable.lookup_policy
- **Calls:** symbol_table:Scope.lookup, symbol_table:SymbolTable.lookup, symbol_table:SymbolTable.lookup_policy

### `tokenizer.Tokenizer.read_operator`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 9
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** tokenizer.Tokenizer.read_operator → compiler_parser.Parser.advance → compiler_parser.Parser.peek → tokenizer.Tokenizer.advance → ...+1
- **Calls:** compiler_parser:Parser.advance, compiler_parser:Parser.peek, tokenizer:Tokenizer.advance, tokenizer:Tokenizer.peek

### `visitors.PrintVisitor.visit_condition_block`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 8
- **Delegation depth:** 22
- **Persistence:** no
- **Chain:** visitors.PrintVisitor.visit_condition_block → dsl_parser.Parser.accept → ir_builder.IRBuilder._emit → nodes.ASTNode.accept → ...+16
- **Calls:** dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept, visitors:PrintVisitor._emit

### `worker_execution_command.convert_brand_request`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 14
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** worker_execution_command.convert_brand_request → worker_execution_command.get_brand_schema_types
- **Calls:** worker_execution_command:get_brand_schema_types

## Supersets (orchestrating functions)

### `arbitrator.PolicyArbitrator._resolve_action_conflict`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `arbitrator.PolicyArbitrator._resolve_limit_conflict`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `binding_moment_enforcer._check_fields_changed`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `binding_moment_enforcer.should_evaluate_policy`
- **Decisions:** 6, **Statements:** 4
- **Subsumes:** binding_moment_enforcer:_check_fields_changed, binding_moment_enforcer:_mark_evaluated, binding_moment_enforcer:_was_evaluated, binding_moment_enforcer:get_binding_moment, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `compiler_parser.Parser.parse`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** compiler_parser:Parser.match, compiler_parser:Parser.parse_import, compiler_parser:Parser.parse_policy_decl, compiler_parser:Parser.parse_rule_decl

### `compiler_parser.Parser.parse_action_block`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** compiler_parser:Parser.advance, compiler_parser:Parser.parse_route_target, tokenizer:Tokenizer.advance

### `compiler_parser.Parser.parse_policy_body`
- **Decisions:** 5, **Statements:** 3
- **Subsumes:** compiler_parser:Parser.match, compiler_parser:Parser.parse_action_block, compiler_parser:Parser.parse_condition_block, compiler_parser:Parser.parse_priority, compiler_parser:Parser.parse_rule_decl, compiler_parser:Parser.parse_rule_ref, compiler_parser:Parser.peek, tokenizer:Tokenizer.peek

### `compiler_parser.Parser.parse_rule_body`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** compiler_parser:Parser.match, compiler_parser:Parser.parse_action_block, compiler_parser:Parser.parse_condition_block, compiler_parser:Parser.parse_priority

### `content_accuracy.ContentAccuracyValidator._get_nested_value`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `deterministic_engine.DeterministicEngine._call_function`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** deterministic_engine:DeterministicEngine._execute_function, ir_nodes:IRModule.get_function

### `deterministic_engine.DeterministicEngine._execute_function`
- **Decisions:** 5, **Statements:** 10
- **Subsumes:** deterministic_engine:DeterministicEngine._execute_instruction, deterministic_engine:ExecutionContext.add_trace, deterministic_engine:ExecutionContext.pop_call, deterministic_engine:ExecutionContext.push_call, interpreter:Interpreter._execute_instruction, interpreter:_LenientInterpreter._execute_instruction, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `deterministic_engine.DeterministicEngine._execute_instruction`
- **Decisions:** 15, **Statements:** 2
- **Subsumes:** deterministic_engine:DeterministicEngine._action_to_intent_type, deterministic_engine:DeterministicEngine._call_function, deterministic_engine:DeterministicEngine._eval_binary_op, deterministic_engine:DeterministicEngine._eval_compare, deterministic_engine:DeterministicEngine._eval_unary_op, deterministic_engine:ExecutionContext.add_trace, deterministic_engine:ExecutionContext.get_variable, deterministic_engine:ExecutionContext.set_variable, intent:IntentEmitter.create_intent, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `deterministic_engine.DeterministicEngine.execute`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** deterministic_engine:DeterministicEngine._execute_function, intent:IntentEmitter.clear, intent:IntentEmitter.emit_all, ir_nodes:IRModule.get_function, ir_nodes:IRModule.get_functions_by_category, snapshot_engine:PolicySnapshotRegistry.list

### `dsl_parser.Parser._parse_actions`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** dsl_parser:Parser._try_parse_action, dsl_parser:Parser.error

### `dsl_parser.Parser._parse_atom`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** compiler_parser:Parser.expect, dsl_parser:Parser._parse_or_expr, dsl_parser:Parser._parse_predicate, dsl_parser:Parser.accept, dsl_parser:Parser.expect, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept

### `dsl_parser.Parser._parse_header`
- **Decisions:** 2, **Statements:** 13
- **Subsumes:** compiler_parser:Parser.expect, dsl_parser:Parser.accept, dsl_parser:Parser.error, dsl_parser:Parser.expect, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept

### `dsl_parser.Parser._try_parse_action`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** compiler_parser:Parser.expect, dsl_parser:Parser.accept, dsl_parser:Parser.expect, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept

### `eligibility_engine.EligibilityEngine._evaluate_e002_known_capability`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** eligibility_engine:CapabilityLookup.exists, eligibility_engine:DefaultCapabilityLookup.exists, snapshot_engine:PolicySnapshotRegistry.list

### `eligibility_engine.EligibilityEngine._evaluate_e003_no_blocking_signal`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** eligibility_engine:DefaultGovernanceSignalLookup.has_blocking_signal, eligibility_engine:GovernanceSignalLookup.has_blocking_signal

### `engine.PolicyEngine._check_business_rules`
- **Decisions:** 5, **Statements:** 4
- **Subsumes:** engine:PolicyEngine._evaluate_business_rule, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine._check_compliance`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** engine:PolicyEngine._evaluate_compliance_rule

### `engine.PolicyEngine._check_cooldown`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** snapshot_engine:PolicySnapshotRegistry.list

### `engine.PolicyEngine._check_ethical_constraints`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** engine:PolicyEngine._evaluate_ethical_constraint

### `engine.PolicyEngine._check_risk_ceilings`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** engine:PolicyEngine._evaluate_risk_ceiling

### `engine.PolicyEngine._check_safety_rules`
- **Decisions:** 5, **Statements:** 4
- **Subsumes:** engine:PolicyEngine._evaluate_safety_rule, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine._evaluate_business_rule`
- **Decisions:** 7, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine._evaluate_compliance_rule`
- **Decisions:** 8, **Statements:** 5
- **Subsumes:** compiler_parser:Parser.match, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:PolicySnapshotRegistry.list

### `engine.PolicyEngine._evaluate_ethical_constraint`
- **Decisions:** 5, **Statements:** 4
- **Subsumes:** engine:PolicyEngine._extract_text_content, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine._evaluate_risk_ceiling`
- **Decisions:** 9, **Statements:** 5
- **Subsumes:** engine:PolicyEngine._add_windowed_value, engine:PolicyEngine._get_windowed_value, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine._evaluate_safety_rule`
- **Decisions:** 10, **Statements:** 3
- **Subsumes:** engine:PolicyEngine._extract_text_content, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine._route_to_governor`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** dsl_parser:Parser.error

### `engine.PolicyEngine.activate_policy_version`
- **Decisions:** 16, **Statements:** 4
- **Subsumes:** dsl_parser:Parser.error, eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, engine:PolicyEngine.reload_policies, engine:PolicyEngine.validate_dependency_dag, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, policy_driver:PolicyDriver.reload_policies, policy_driver:PolicyDriver.validate_dependency_dag, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.activate_version, policy_engine_driver:PolicyEngineDriver.deactivate_all_versions, policy_engine_driver:PolicyEngineDriver.fetch_active_policies_for_integrity, policy_engine_driver:PolicyEngineDriver.fetch_conflicts, policy_engine_driver:PolicyEngineDriver.fetch_dependency_edges, policy_engine_driver:PolicyEngineDriver.fetch_ethical_constraints_for_integrity, policy_engine_driver:PolicyEngineDriver.fetch_policy_version_by_id_or_version, policy_engine_driver:PolicyEngineDriver.fetch_temporal_policies_for_integrity, policy_engine_driver:PolicyEngineDriver.insert_provenance, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, prevention_hook:PreventionHook.evaluate, recovery_evaluation_engine:RecoveryEvaluationEngine.evaluate, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:PolicySnapshotRegistry.list

### `engine.PolicyEngine.add_dependency_with_dag_check`
- **Decisions:** 7, **Statements:** 2
- **Subsumes:** dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_dependency_edges, policy_engine_driver:PolicyEngineDriver.insert_dependency, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine.clear_cooldowns`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** snapshot_engine:PolicySnapshotRegistry.list

### `engine.PolicyEngine.create_policy_version`
- **Decisions:** 2, **Statements:** 11
- **Subsumes:** engine:PolicyEngine.get_current_version, policy_driver:PolicyDriver.get_current_version, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.deactivate_all_versions, policy_engine_driver:PolicyEngineDriver.insert_policy_version

### `engine.PolicyEngine.evaluate_with_context`
- **Decisions:** 8, **Statements:** 24
- **Subsumes:** eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine._classify_recoverability, engine:PolicyEngine._classify_severity, engine:PolicyEngine._load_policies, engine:PolicyEngine.evaluate, engine:PolicyEngine.get_temporal_policies, engine:PolicyEngine.get_temporal_utilization, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, policy_driver:PolicyDriver.get_temporal_policies, policy_driver:PolicyDriver.get_temporal_utilization, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, prevention_hook:PreventionHook.evaluate, recovery_evaluation_engine:RecoveryEvaluationEngine.evaluate, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine.get_active_cooldowns`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** snapshot_engine:PolicySnapshotRegistry.list

### `engine.PolicyEngine.get_current_version`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_current_active_version, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine.get_risk_ceilings`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** engine:PolicyEngine._load_policies

### `engine.PolicyEngine.get_safety_rules`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** engine:PolicyEngine._load_policies

### `engine.PolicyEngine.get_temporal_storage_stats`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_temporal_storage_stats

### `engine.PolicyEngine.get_temporal_utilization`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_temporal_metric_sum, policy_engine_driver:PolicyEngineDriver.fetch_temporal_policy_for_utilization

### `engine.PolicyEngine.get_topological_evaluation_order`
- **Decisions:** 5, **Statements:** 9
- **Subsumes:** dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine.get_violation`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_violation_by_id, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine.get_violations`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_violations, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `engine.PolicyEngine.pre_check`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** dsl_parser:Parser.error, eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine._is_cache_stale, engine:PolicyEngine._load_policies, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, prevention_hook:PreventionHook.evaluate, recovery_evaluation_engine:RecoveryEvaluationEngine.evaluate

### `engine.PolicyEngine.rollback_to_version`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** dsl_parser:Parser.error, engine:PolicyEngine.reload_policies, policy_driver:PolicyDriver.reload_policies, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.activate_version, policy_engine_driver:PolicyEngineDriver.fetch_version_for_rollback, policy_engine_driver:PolicyEngineDriver.insert_provenance, policy_engine_driver:PolicyEngineDriver.mark_version_rolled_back

### `engine.PolicyEngine.update_safety_rule`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** engine:PolicyEngine.reload_policies, policy_driver:PolicyDriver.reload_policies, policy_driver:PolicyDriver.update_safety_rule, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.update_safety_rule

### `engine.PolicyEngine.validate_dependency_dag`
- **Decisions:** 8, **Statements:** 13
- **Subsumes:** dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_dependency_edges_with_type, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `folds.ConstantFolder._fold_binary_op`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `folds.ConstantFolder._fold_compare`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `folds.ConstantFolder._fold_unary_op`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `folds.DeadCodeEliminator._find_reachable_blocks`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `folds.PolicySimplifier._find_mergeable_policies`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** snapshot_engine:PolicySnapshotRegistry.list

### `governance_facade.GovernanceFacade.enable_kill_switch`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** dsl_parser:Parser.error

### `governance_facade.GovernanceFacade.get_governance_state`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `intent.IntentEmitter.emit`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** intent:IntentEmitter.validate_intent, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `interpreter.Interpreter._compare`
- **Decisions:** 7, **Statements:** 2
- **Subsumes:** interpreter:Interpreter._types_compatible

### `interpreter.Interpreter._evaluate_condition`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** deterministic_engine:DeterministicEngine._execute_instruction, interpreter:Interpreter._execute_instruction, interpreter:_LenientInterpreter._execute_instruction

### `interpreter.Interpreter._execute_instruction`
- **Decisions:** 13, **Statements:** 2
- **Subsumes:** interpreter:Interpreter._compare, interpreter:_LenientInterpreter._compare

### `interpreter._LenientInterpreter._execute_instruction`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** deterministic_engine:DeterministicEngine._execute_instruction, interpreter:Interpreter._execute_instruction

### `ir_builder.IRBuilder.visit_action_block`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit

### `ir_builder.IRBuilder.visit_func_call`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept, visitors:PrintVisitor._emit

### `ir_compiler.IRCompiler._compile_actions`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** ast:is_block_action, ast:is_require_approval_action, ast:is_warn_action

### `ir_compiler.IRCompiler._emit_condition`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** ast:is_exists_predicate, ast:is_logical_condition, ast:is_predicate, ir_compiler:IRCompiler._emit_exists, ir_compiler:IRCompiler._emit_logical, ir_compiler:IRCompiler._emit_predicate

### `kernel.ExecutionKernel._emit_envelope`
- **Decisions:** 2, **Statements:** 1
- **Subsumes:** dsl_parser:Parser.error

### `learning_proof_engine.CheckpointConfig.get_priority`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `learning_proof_engine.CheckpointConfig.should_auto_dismiss`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** learning_proof_engine:CheckpointConfig.get_priority

### `learning_proof_engine.PatternCalibration.record_outcome`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** learning_proof_engine:PatternCalibration._recalibrate

### `lessons_engine.LessonsLearnedEngine.convert_lesson_to_draft`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition

### `lessons_engine.LessonsLearnedEngine.defer_lesson`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition

### `lessons_engine.LessonsLearnedEngine.dismiss_lesson`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition

### `lessons_engine.LessonsLearnedEngine.get_lesson_stats`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** lessons_engine:LessonsLearnedEngine._get_driver

### `lessons_engine.LessonsLearnedEngine.reactivate_deferred_lesson`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition

### `lessons_engine.LessonsLearnedEngine.reactivate_expired_deferred_lessons`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** lessons_engine:LessonsLearnedEngine.get_expired_deferred_lessons, lessons_engine:LessonsLearnedEngine.reactivate_deferred_lesson

### `limits_facade.LimitsFacade.check_limit`
- **Decisions:** 5, **Statements:** 8
- **Subsumes:** limits_facade:LimitsFacade._get_or_create_limit

### `limits_facade.LimitsFacade.get_usage`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ast:PolicyMetadata.to_dict, ast:Predicate.to_dict, ast:RequireApprovalAction.to_dict, ast:WarnAction.to_dict, authority_checker:OverrideCheckResult.to_dict, content_accuracy:ContentAccuracyResult.to_dict, deterministic_engine:ExecutionResult.to_dict, governance_facade:BootStatusResult.to_dict, governance_facade:ConflictResolutionResult.to_dict, governance_facade:GovernanceStateResult.to_dict, governance_facade:KillSwitchResult.to_dict, intent:Intent.to_dict, intent:IntentPayload.to_dict, interpreter:ActionResult.to_dict, interpreter:ClauseResult.to_dict, interpreter:EvaluationResult.to_dict, ir_compiler:CompiledClause.to_dict, ir_compiler:Instruction.to_dict, ir_compiler:PolicyIR.to_dict, ir_nodes:IRGovernance.to_dict, limits_facade:LimitCheckResult.to_dict, limits_facade:LimitConfig.to_dict, limits_facade:LimitsFacade._get_or_create_limit, limits_facade:UsageSummary.to_dict, phase_status_invariants:InvariantCheckResponse.to_dict, phase_status_invariants:PhaseStatusInvariantEnforcementError.to_dict, policy_graph_engine:ConflictDetectionResult.to_dict, policy_graph_engine:DependencyGraphResult.to_dict, policy_graph_engine:PolicyConflict.to_dict, policy_graph_engine:PolicyDependency.to_dict, policy_graph_engine:PolicyNode.to_dict, policy_mapper:MCPPolicyDecision.to_dict, prevention_hook:PreventionResult.to_dict, recovery_evaluation_engine:RecoveryDecision.to_dict, sandbox_engine:ExecutionRecord.to_dict, sandbox_engine:SandboxPolicy.to_dict, snapshot_engine:PolicySnapshotData.to_dict, snapshot_engine:PolicySnapshotError.to_dict, snapshot_engine:SnapshotRegistryStats.to_dict

### `limits_facade.LimitsFacade.list_limits`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** limits_facade:LimitsFacade._get_or_create_limit

### `llm_policy_engine.get_model_for_task`
- **Decisions:** 4, **Statements:** 6
- **Subsumes:** llm_policy_engine:is_expensive_model, llm_policy_engine:is_model_allowed, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `optimizer_conflict_resolver.ConflictResolver._detect_action_conflicts`
- **Decisions:** 6, **Statements:** 3
- **Subsumes:** optimizer_conflict_resolver:ConflictResolver._get_condition_signature, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:PolicySnapshotRegistry.list

### `optimizer_conflict_resolver.ConflictResolver._detect_category_conflicts`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** optimizer_conflict_resolver:ConflictResolver._might_override, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies`
- **Decisions:** 6, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `optimizer_conflict_resolver.ConflictResolver._resolve_action_conflict`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** grammar:PLangGrammar.get_action_precedence, optimizer_conflict_resolver:ConflictResolver._get_actions, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `optimizer_conflict_resolver.ConflictResolver._resolve_category_conflict`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** grammar:PLangGrammar.get_category_priority, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `optimizer_conflict_resolver.ConflictResolver._resolve_circular_conflict`
- **Decisions:** 4, **Statements:** 5
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `optimizer_conflict_resolver.ConflictResolver._resolve_conflict`
- **Decisions:** 4, **Statements:** 1
- **Subsumes:** arbitrator:PolicyArbitrator._resolve_action_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_action_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_category_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_circular_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_priority_conflict

### `phase_status_invariants.PhaseStatusInvariantChecker.should_allow_transition`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** authority_checker:OverrideAuthorityChecker.check, phase_status_invariants:PhaseStatusInvariantChecker.check

### `policy_engine_driver.PolicyEngineDriver.fetch_conflicts`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `policy_engine_driver.PolicyEngineDriver.fetch_temporal_policies`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `policy_engine_driver.PolicyEngineDriver.update_safety_rule`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `policy_graph_engine.PolicyConflictEngine._detect_priority_overrides`
- **Decisions:** 4, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_graph_engine.PolicyConflictEngine._detect_scope_overlaps`
- **Decisions:** 5, **Statements:** 5
- **Subsumes:** policy_graph_engine:PolicyConflictEngine._has_contradicting_conditions, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_graph_engine.PolicyConflictEngine._detect_temporal_conflicts`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** policy_graph_engine:PolicyConflictEngine._time_windows_overlap, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_graph_engine.PolicyConflictEngine._detect_threshold_contradictions`
- **Decisions:** 4, **Statements:** 6
- **Subsumes:** policy_graph_driver:PolicyGraphDriver.fetch_active_limits

### `policy_graph_engine.PolicyDependencyEngine._detect_explicit_dependencies`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `policy_graph_engine.PolicyDependencyEngine.check_can_activate`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** policy_graph_engine:PolicyDependencyEngine.compute_dependency_graph

### `policy_mapper.MCPPolicyMapper._evaluate_policy`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** policy_mapper:MCPPolicyMapper._get_policy_engine

### `policy_proposal_engine.PolicyProposalEngine.delete_policy_rule`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** policy_graph_engine:PolicyDependencyEngine.check_can_delete, policy_graph_engine:get_dependency_engine, policy_proposal_engine:delete_policy_rule, policy_proposal_read_driver:PolicyProposalReadDriver.fetch_rule_by_id, policy_proposal_write_driver:PolicyProposalWriteDriver.delete_policy_rule, policy_rules_driver:PolicyRulesDriver.fetch_rule_by_id

### `policy_proposal_engine.PolicyProposalEngine.review_proposal`
- **Decisions:** 5, **Statements:** 6
- **Subsumes:** ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ast:PolicyMetadata.to_dict, ast:Predicate.to_dict, ast:RequireApprovalAction.to_dict, ast:WarnAction.to_dict, authority_checker:OverrideCheckResult.to_dict, content_accuracy:ContentAccuracyResult.to_dict, deterministic_engine:ExecutionResult.to_dict, governance_facade:BootStatusResult.to_dict, governance_facade:ConflictResolutionResult.to_dict, governance_facade:GovernanceStateResult.to_dict, governance_facade:KillSwitchResult.to_dict, intent:Intent.to_dict, intent:IntentPayload.to_dict, interpreter:ActionResult.to_dict, interpreter:ClauseResult.to_dict, interpreter:EvaluationResult.to_dict, ir_compiler:CompiledClause.to_dict, ir_compiler:Instruction.to_dict, ir_compiler:PolicyIR.to_dict, ir_nodes:IRGovernance.to_dict, limits_facade:LimitCheckResult.to_dict, limits_facade:LimitConfig.to_dict, limits_facade:UsageSummary.to_dict, phase_status_invariants:InvariantCheckResponse.to_dict, phase_status_invariants:PhaseStatusInvariantEnforcementError.to_dict, policy_graph_engine:ConflictDetectionResult.to_dict, policy_graph_engine:DependencyGraphResult.to_dict, policy_graph_engine:PolicyConflict.to_dict, policy_graph_engine:PolicyConflictEngine.detect_conflicts, policy_graph_engine:PolicyDependency.to_dict, policy_graph_engine:PolicyNode.to_dict, policy_graph_engine:get_conflict_engine, policy_mapper:MCPPolicyDecision.to_dict, policy_proposal_engine:PolicyProposalEngine._create_policy_rule_from_proposal, policy_proposal_read_driver:PolicyProposalReadDriver.count_versions_for_proposal, policy_proposal_read_driver:PolicyProposalReadDriver.fetch_proposal_by_id, policy_proposal_write_driver:PolicyProposalWriteDriver.create_version, policy_proposal_write_driver:PolicyProposalWriteDriver.update_proposal_status, prevention_hook:PreventionResult.to_dict, proposals_read_driver:ProposalsReadDriver.fetch_proposal_by_id, recovery_evaluation_engine:RecoveryDecision.to_dict, sandbox_engine:ExecutionRecord.to_dict, sandbox_engine:SandboxPolicy.to_dict, snapshot_engine:PolicySnapshotData.to_dict, snapshot_engine:PolicySnapshotError.to_dict, snapshot_engine:SnapshotRegistryStats.to_dict

### `policy_proposal_read_driver.PolicyProposalReadDriver.fetch_unacknowledged_feedback`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `prevention_engine.PreventionEngine._evaluate_custom_policy`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, prevention_engine:PreventionResult.block, snapshot_engine:PolicySnapshotRegistry.get

### `prevention_engine.PreventionEngine._evaluate_step_inner`
- **Decisions:** 12, **Statements:** 11
- **Subsumes:** binding_moment_enforcer:should_evaluate_policy, policy_conflict_resolver:resolve_policy_conflict, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionEngine._evaluate_custom_policy, prevention_engine:PreventionResult.allow, prevention_engine:PreventionResult.block, snapshot_engine:PolicySnapshotRegistry.get

### `proposals_read_driver.ProposalsReadDriver.fetch_proposal_by_id`
- **Decisions:** 2, **Statements:** 10
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `protection_provider.MockAbuseProtectionProvider.check_burst`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, snapshot_engine:PolicySnapshotRegistry.get

### `protection_provider.MockAbuseProtectionProvider.check_cost`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, snapshot_engine:PolicySnapshotRegistry.get

### `protection_provider.MockAbuseProtectionProvider.check_rate_limit`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, snapshot_engine:PolicySnapshotRegistry.get

### `recovery_matcher.RecoveryMatcher._compute_confidence`
- **Decisions:** 5, **Statements:** 13
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, recovery_matcher:RecoveryMatcher._calculate_time_weight, snapshot_engine:PolicySnapshotRegistry.get

### `recovery_matcher.RecoveryMatcher._escalate_to_llm`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `recovery_matcher.RecoveryMatcher.approve_candidate`
- **Decisions:** 3, **Statements:** 14
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `recovery_matcher.RecoveryMatcher.get_candidates`
- **Decisions:** 2, **Statements:** 11
- **Subsumes:** deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute

### `recovery_matcher.RecoveryMatcher.suggest_hybrid`
- **Decisions:** 4, **Statements:** 13
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, recovery_matcher:RecoveryMatcher._escalate_to_llm, recovery_matcher:RecoveryMatcher._find_similar_by_embedding, recovery_matcher:RecoveryMatcher._get_cached_recovery, recovery_matcher:RecoveryMatcher._normalize_error, recovery_matcher:RecoveryMatcher._set_cached_recovery, recovery_matcher:RecoveryMatcher.suggest, snapshot_engine:PolicySnapshotRegistry.get

### `sandbox_engine.SandboxService._check_quota`
- **Decisions:** 3, **Statements:** 10
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `sandbox_engine.SandboxService.get_execution_stats`
- **Decisions:** 3, **Statements:** 10
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `snapshot_engine.PolicySnapshotRegistry.archive`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `snapshot_engine.PolicySnapshotRegistry.delete`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get

### `snapshot_engine.PolicySnapshotRegistry.get_statistics`
- **Decisions:** 6, **Statements:** 5
- **Subsumes:** snapshot_engine:PolicySnapshotData.verify_integrity

### `snapshot_engine.PolicySnapshotRegistry.verify`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotData.verify_integrity, snapshot_engine:PolicySnapshotData.verify_threshold_integrity, snapshot_engine:PolicySnapshotRegistry.get

### `symbol_table.Scope.lookup`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** symbol_table:SymbolTable.lookup

### `tokenizer.Tokenizer.read_string`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** compiler_parser:Parser.advance, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, tokenizer:Tokenizer.advance

### `tokenizer.Tokenizer.tokenize`
- **Decisions:** 7, **Statements:** 4
- **Subsumes:** compiler_parser:Parser.advance, tokenizer:Tokenizer.advance, tokenizer:Tokenizer.read_identifier, tokenizer:Tokenizer.read_number, tokenizer:Tokenizer.read_operator, tokenizer:Tokenizer.read_string, tokenizer:Tokenizer.skip_comment, tokenizer:Tokenizer.skip_whitespace

### `validator.PolicyValidator._check_warnings`
- **Decisions:** 4, **Statements:** 3
- **Subsumes:** ast:is_block_action, ast:is_require_approval_action

### `validator.PolicyValidator._extract_metrics`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** ast:is_exists_predicate, ast:is_logical_condition, ast:is_predicate

### `validator.PolicyValidator._validate_metrics`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** validator:PolicyValidator._extract_metrics

### `validator.PolicyValidator._validate_mode_enforcement`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** ast:is_block_action, ast:is_require_approval_action

### `visitors.BaseVisitor.visit_binary_op`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept

### `visitors.BaseVisitor.visit_condition_block`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept

### `visitors.PrintVisitor.visit_binary_op`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, nodes:ConditionBlockNode.accept, nodes:FuncCallNode.accept, nodes:IdentNode.accept, nodes:ImportNode.accept, nodes:LiteralNode.accept, nodes:PolicyDeclNode.accept, nodes:PriorityNode.accept, nodes:ProgramNode.accept, nodes:RouteTargetNode.accept, nodes:RuleDeclNode.accept, nodes:RuleRefNode.accept, nodes:UnaryOpNode.accept, visitors:PrintVisitor._emit

## Wrappers (thin delegation)

- `arbitrator.PolicyArbitrator.__init__` → ?
- `ast.BlockAction.to_dict` → ?
- `ast.Clause.to_dict` → ast:BlockAction.to_dict
- `ast.ExistsPredicate.to_dict` → ?
- `ast.LogicalCondition.to_dict` → ast:BlockAction.to_dict
- `ast.PolicyAST.mode` → ?
- `ast.PolicyAST.name` → ?
- `ast.PolicyAST.scope` → ?
- `ast.PolicyAST.to_dict` → ast:BlockAction.to_dict
- `ast.PolicyAST.to_json` → ast:BlockAction.to_dict
- `ast.PolicyAST.version` → ?
- `ast.PolicyMetadata.to_dict` → ?
- `ast.Predicate.to_dict` → ?
- `ast.RequireApprovalAction.to_dict` → ?
- `ast.WarnAction.to_dict` → ?
- `ast.is_block_action` → ?
- `ast.is_exists_predicate` → ?
- `ast.is_logical_condition` → ?
- `ast.is_predicate` → ?
- `ast.is_require_approval_action` → ?
- `ast.is_warn_action` → ?
- `authority_checker.OverrideCheckResult.to_dict` → ?
- `authority_checker.should_skip_enforcement` → authority_checker:OverrideAuthorityChecker.check
- `binding_moment_enforcer._was_evaluated` → ?
- `claim_decision_engine.determine_claim_status` → policy_limits_engine:PolicyLimitsService.get
- `claim_decision_engine.get_result_confidence` → policy_limits_engine:PolicyLimitsService.get
- `compiler_parser.ParseError.__init__` → arbitrator:PolicyArbitrator.__init__
- `compiler_parser.Parser.__init__` → ?
- `compiler_parser.Parser.advance` → ?
- `compiler_parser.Parser.match` → ?
- `compiler_parser.Parser.parse_expr` → compiler_parser:Parser.parse_or_expr
- `content_accuracy.ContentAccuracyResult.to_dict` → ?
- `content_accuracy.validate_content_accuracy` → content_accuracy:ContentAccuracyValidator.validate
- `cus_enforcement_service.get_cus_enforcement_service` → ?
- `customer_policy_read_engine.CustomerPolicyReadService.__init__` → policy_read_driver:get_policy_read_driver
- `customer_policy_read_engine.CustomerPolicyReadService._get_guardrails` → policy_read_driver:PolicyReadDriver.list_all_guardrails
- `customer_policy_read_engine.CustomerPolicyReadService._get_rate_limits` → ?
- `customer_policy_read_engine.get_customer_policy_read_service` → ?
- `degraded_mode.DegradedModeStatus.get_inactive` → ?
- `degraded_mode.get_degraded_mode_status` → degraded_mode:DegradedModeStatus.get_inactive
- `degraded_mode.get_existing_run_action` → ?
- `degraded_mode.is_degraded_mode_active` → ?
- `deterministic_engine.DeterministicEngine.__init__` → deterministic_engine:DeterministicEngine._register_builtins
- `deterministic_engine.DeterministicEngine._action_to_intent_type` → policy_limits_engine:PolicyLimitsService.get
- `deterministic_engine.ExecutionContext.add_trace` → ?
- `deterministic_engine.ExecutionContext.push_call` → ?
- `deterministic_engine.ExecutionContext.set_variable` → ?
- `deterministic_engine.ExecutionResult.to_dict` → ast:BlockAction.to_dict
- `dsl_parser.ParseLocation.__str__` → ?
- `dsl_parser.Parser.__init__` → ?
- `dsl_parser.Parser._parse_condition` → dsl_parser:Parser._parse_or_expr
- `dsl_parser.Parser.error` → ?
- `eligibility_engine.CapabilityLookup.exists` → ?
- `eligibility_engine.CapabilityLookup.is_frozen` → ?
- `eligibility_engine.ContractLookup.has_similar_pending` → ?
- `eligibility_engine.DefaultCapabilityLookup.__init__` → ?
- `eligibility_engine.DefaultCapabilityLookup.exists` → ?
- `eligibility_engine.DefaultCapabilityLookup.is_frozen` → ?
- `eligibility_engine.DefaultContractLookup.__init__` → ?
- `eligibility_engine.DefaultGovernanceSignalLookup.__init__` → ?
- `eligibility_engine.DefaultPreApprovalLookup.__init__` → ?
- `eligibility_engine.DefaultPreApprovalLookup.has_system_pre_approval` → ?
- `eligibility_engine.DefaultSystemHealthLookup.__init__` → ?
- `eligibility_engine.DefaultSystemHealthLookup.get_status` → ?
- `eligibility_engine.EligibilityEngine._evaluate_e005_source_allowlist` → snapshot_engine:PolicySnapshotRegistry.list
- `eligibility_engine.EligibilityEngine._evaluate_e104_health_degraded` → eligibility_engine:DefaultSystemHealthLookup.get_status
- `eligibility_engine.GovernanceSignalLookup.has_blocking_signal` → ?
- `eligibility_engine.PreApprovalLookup.has_system_pre_approval` → ?
- `eligibility_engine.SystemHealthLookup.get_status` → ?
- `engine.PolicyEngine.get_metrics` → ?
- `engine.PolicyEngine.reload_policies` → engine:PolicyEngine._load_policies
- `engine.PolicyEngine.set_governor` → ?
- `failure_mode_handler.handle_evaluation_error` → failure_mode_handler:handle_policy_failure
- `failure_mode_handler.handle_missing_policy` → failure_mode_handler:handle_policy_failure
- `failure_mode_handler.handle_timeout` → failure_mode_handler:handle_policy_failure
- `folds.ConstantFolder.__init__` → ?
- `folds.DeadCodeEliminator.__init__` → ?
- `folds.PolicySimplifier.__init__` → ?
- `governance_facade.BootStatusResult.to_dict` → ?
- `governance_facade.ConflictResolutionResult.to_dict` → ?
- `governance_facade.GovernanceFacade.__init__` → ?
- `governance_facade.GovernanceFacade.list_conflicts` → dsl_parser:Parser.error
- `governance_facade.GovernanceStateResult.to_dict` → ?
- `governance_facade.KillSwitchResult.to_dict` → ?
- `grammar.PLangGrammar.get_action_precedence` → policy_limits_engine:PolicyLimitsService.get
- `grammar.PLangGrammar.get_category_priority` → policy_limits_engine:PolicyLimitsService.get
- `grammar.PLangGrammar.is_action` → ?
- `grammar.PLangGrammar.is_category` → ?
- `grammar.PLangGrammar.is_keyword` → ?
- `grammar.PLangGrammar.is_operator` → ?
- `intent.Intent.to_dict` → ast:BlockAction.to_dict
- `intent.IntentEmitter.__init__` → ?
- `intent.IntentEmitter.clear` → ?
- `intent.IntentEmitter.get_emitted` → snapshot_engine:PolicySnapshotRegistry.list
- `intent.IntentEmitter.get_pending` → snapshot_engine:PolicySnapshotRegistry.list
- `intent.IntentEmitter.register_handler` → ?
- `intent.IntentPayload.to_dict` → ?
- `interpreter.ClauseResult.to_dict` → ast:BlockAction.to_dict
- `interpreter.EvaluationResult.has_block` → ?
- `interpreter.EvaluationResult.has_require_approval` → ?
- `interpreter.EvaluationResult.to_dict` → ast:BlockAction.to_dict
- `interpreter.EvaluationResult.warnings` → ?
- `interpreter.Interpreter.__init__` → ?
- `interpreter.evaluate` → eligibility_engine:EligibilityEngine.evaluate
- `ir_builder.IRBuilder._next_block_name` → ?
- `ir_builder.IRBuilder._next_id` → ?
- `ir_builder.IRBuilder.visit_import` → ?
- `ir_builder.IRBuilder.visit_literal` → ir_builder:IRBuilder._emit
- `ir_builder.IRBuilder.visit_route_target` → ?
- `ir_compiler.CompiledClause.to_dict` → ast:BlockAction.to_dict
- `ir_compiler.IRCompiler.__init__` → ?
- `ir_compiler.IRCompiler._compile_condition` → ir_compiler:IRCompiler._emit_condition
- `ir_compiler.IRCompiler._emit_exists` → ?
- `ir_compiler.Instruction.to_dict` → snapshot_engine:PolicySnapshotRegistry.list
- `ir_compiler.OptimizingIRCompiler.__init__` → arbitrator:PolicyArbitrator.__init__
- `ir_compiler.OptimizingIRCompiler.compile` → ir_compiler:IRCompiler.compile
- `ir_compiler.PolicyIR.to_dict` → ast:BlockAction.to_dict
- `ir_compiler.PolicyIR.to_json` → ast:BlockAction.to_dict
- `ir_compiler.ir_hash` → ast:PolicyAST.compute_hash
- `ir_nodes.IRBinaryOp.__str__` → ?
- `ir_nodes.IRBlock.add_instruction` → ?
- `ir_nodes.IRCall.__str__` → ?
- `ir_nodes.IRCheckPolicy.__str__` → ?
- `ir_nodes.IRCompare.__str__` → ?
- `ir_nodes.IRFunction.add_block` → ?
- `ir_nodes.IRFunction.get_block` → policy_limits_engine:PolicyLimitsService.get
- `ir_nodes.IRGovernance.to_dict` → ?
- `ir_nodes.IRJump.__str__` → ?
- `ir_nodes.IRJumpIf.__str__` → ?
- `ir_nodes.IRLoadConst.__str__` → ?
- `ir_nodes.IRLoadVar.__str__` → ?
- `ir_nodes.IRModule.get_function` → policy_limits_engine:PolicyLimitsService.get
- `ir_nodes.IRModule.get_functions_by_category` → policy_limits_engine:PolicyLimitsService.get
- `ir_nodes.IRNode.__str__` → ?
- `ir_nodes.IRStoreVar.__str__` → ?
- `ir_nodes.IRUnaryOp.__str__` → ?
- `kernel.ExecutionKernel._record_invocation_complete` → ?
- `kernel.ExecutionKernel._record_invocation_start` → ?
- `kernel.ExecutionKernel.get_known_capabilities` → ?
- `kernel.ExecutionKernel.is_known_capability` → ?
- `kernel.get_enforcement_mode` → policy_limits_engine:PolicyLimitsService.get
- `kernel.set_enforcement_mode` → ?
- `keys_shim.KeysReadService.__init__` → ?
- `keys_shim.KeysReadService.get_key` → ?
- `keys_shim.KeysReadService.get_key_usage_today` → ?
- `keys_shim.KeysReadService.list_keys` → ?
- `keys_shim.KeysWriteService.__init__` → ?
- `keys_shim.KeysWriteService.freeze_key` → ?
- `keys_shim.KeysWriteService.unfreeze_key` → ?
- `keys_shim.get_keys_read_service` → ?
- `keys_shim.get_keys_write_service` → ?
- `kill_switch.KillSwitchStatus.get_current` → ?
- `kill_switch.should_bypass_governance` → kill_switch:is_kill_switch_active
- `learning_proof_engine.CheckpointConfig.is_blocking` → ?
- `learning_proof_engine.GlobalRegretTracker.has_proven_rollback` → ?
- `learning_proof_engine.M25GraduationStatus.gate1_passed` → ?
- `learning_proof_engine.M25GraduationStatus.gate2_passed` → ?
- `learning_proof_engine.M25GraduationStatus.gate3_passed` → ?
- `learning_proof_engine.M25GraduationStatus.is_graduated` → ?
- `learning_proof_engine.M25GraduationStatus.to_dashboard` → learning_proof_engine:M25GraduationStatus._get_next_action
- `learning_proof_engine.PatternCalibration.is_calibrated` → ?
- `learning_proof_engine.PolicyRegretTracker._trigger_demotion` → ?
- `learning_proof_engine.PolicyRegretTracker.decay_regret` → ?
- `learning_proof_engine.PolicyRegretTracker.is_demoted` → ?
- `learning_proof_engine.PreventionRecord.to_console_timeline` → ?
- `learning_proof_engine.PreventionTimeline.add_policy_born` → ?
- `learning_proof_engine.PreventionTimeline.add_prevention` → ?
- `learning_proof_engine.PreventionTimeline.add_regret` → ?
- `learning_proof_engine.PreventionTimeline.add_rollback` → ?
- `learning_proof_engine.PreventionTracker.has_proven_prevention` → ?
- `learning_proof_engine.PreventionTracker.record_failure` → ?
- `learning_proof_engine.PreventionTracker.record_prevention` → ?
- `lessons_engine.LessonsLearnedEngine.__init__` → policy_limits_engine:PolicyLimitsService.get
- `lessons_engine.LessonsLearnedEngine._generate_failure_description` → ?
- `lessons_engine.LessonsLearnedEngine.list_lessons` → lessons_engine:LessonsLearnedEngine._get_driver
- `lessons_engine.is_valid_transition` → policy_limits_engine:PolicyLimitsService.get
- `limits.Limits.is_unlimited` → ?
- `limits.derive_limits` → policy_limits_engine:PolicyLimitsService.get
- `limits_facade.LimitCheckResult.to_dict` → ?
- `limits_facade.LimitConfig.to_dict` → ?
- `limits_facade.LimitsFacade.__init__` → ?
- `limits_facade.UsageSummary.to_dict` → ?
- `limits_simulation_service.get_limits_simulation_service` → ?
- `llm_policy_engine.LLMRateLimiter.get_instance` → ?
- `llm_policy_engine.estimate_tokens` → ?
- `llm_policy_engine.is_expensive_model` → ?
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
- `nodes.ActionBlockNode.accept` → ir_builder:IRBuilder.visit_action_block
- `nodes.AttrAccessNode.accept` → ir_builder:IRBuilder.visit_attr_access
- `nodes.BinaryOpNode.accept` → ir_builder:IRBuilder.visit_binary_op
- `nodes.ConditionBlockNode.accept` → ir_builder:IRBuilder.visit_condition_block
- `nodes.FuncCallNode.accept` → ir_builder:IRBuilder.visit_func_call
- `nodes.IdentNode.accept` → ir_builder:IRBuilder.visit_ident
- `nodes.ImportNode.accept` → ir_builder:IRBuilder.visit_import
- `nodes.LiteralNode.accept` → ir_builder:IRBuilder.visit_literal
- `nodes.PolicyDeclNode.__post_init__` → grammar:PLangGrammar.get_category_priority
- `nodes.PolicyDeclNode.accept` → ir_builder:IRBuilder.visit_policy_decl
- `nodes.PriorityNode.accept` → ir_builder:IRBuilder.visit_priority
- `nodes.ProgramNode.accept` → ir_builder:IRBuilder.visit_program
- `nodes.RouteTargetNode.accept` → ir_builder:IRBuilder.visit_route_target
- `nodes.RuleDeclNode.__post_init__` → grammar:PLangGrammar.get_category_priority
- `nodes.RuleDeclNode.accept` → ir_builder:IRBuilder.visit_rule_decl
- `nodes.RuleRefNode.accept` → ir_builder:IRBuilder.visit_rule_ref
- `nodes.UnaryOpNode.accept` → ir_builder:IRBuilder.visit_unary_op
- `optimizer_conflict_resolver.ConflictResolver.__init__` → ?
- `optimizer_conflict_resolver.PolicyConflict.__str__` → ?
- `phase_status_invariants.InvariantCheckResponse.to_dict` → snapshot_engine:PolicySnapshotRegistry.list
- `phase_status_invariants.PhaseStatusInvariantChecker.__init__` → ?
- `phase_status_invariants.PhaseStatusInvariantChecker.enforcement_enabled` → ?
- `phase_status_invariants.PhaseStatusInvariantChecker.from_governance_config` → ?
- `phase_status_invariants.PhaseStatusInvariantEnforcementError.to_dict` → snapshot_engine:PolicySnapshotRegistry.list
- `phase_status_invariants.check_phase_status_invariant` → authority_checker:OverrideAuthorityChecker.check
- `phase_status_invariants.ensure_phase_status_invariant` → phase_status_invariants:PhaseStatusInvariantChecker.ensure_valid
- `plan_generation_engine.PlanGenerationEngine.__init__` → ?
- `policies_limits_query_engine.LimitsQueryEngine.__init__` → ?
- `policies_limits_query_engine.get_limits_query_engine` → ?
- `policies_proposals_query_engine.ProposalsQueryEngine.__init__` → ?
- `policies_proposals_query_engine.ProposalsQueryEngine.count_drafts` → proposals_read_driver:ProposalsReadDriver.count_draft_proposals
- `policies_proposals_query_engine.get_proposals_query_engine` → proposals_read_driver:get_proposals_read_driver
- `policies_rules_query_engine.PolicyRulesQueryEngine.__init__` → ?
- `policies_rules_query_engine.PolicyRulesQueryEngine.count_rules` → policy_rules_read_driver:PolicyRulesReadDriver.count_policy_rules
- `policies_rules_query_engine.get_policy_rules_query_engine` → policy_rules_read_driver:get_policy_rules_read_driver
- `policy_command._record_approval_action` → ?
- `policy_command._record_approval_escalation` → ?
- `policy_command._record_approval_request_created` → ?
- `policy_command._record_budget_rejection` → ?
- `policy_command._record_capability_violation` → ?
- `policy_command._record_policy_decision` → ?
- `policy_command._record_webhook_fallback` → ?
- `policy_command.record_approval_created` → policy_command:_record_approval_request_created
- `policy_command.record_approval_outcome` → policy_command:_record_approval_action
- `policy_command.record_escalation` → policy_command:_record_approval_escalation
- `policy_command.record_webhook_used` → policy_command:_record_webhook_fallback
- `policy_conflict_resolver.get_action_severity` → policy_limits_engine:PolicyLimitsService.get
- `policy_conflict_resolver.is_more_restrictive` → policy_conflict_resolver:get_action_severity
- `policy_driver.PolicyDriver.__init__` → ?
- `policy_driver.PolicyDriver.acknowledge_violation` → engine:PolicyEngine.acknowledge_violation
- `policy_driver.PolicyDriver.activate_policy_version` → engine:PolicyEngine.activate_policy_version
- `policy_driver.PolicyDriver.add_dependency_with_dag_check` → engine:PolicyEngine.add_dependency_with_dag_check
- `policy_driver.PolicyDriver.clear_cooldowns` → engine:PolicyEngine.clear_cooldowns
- `policy_driver.PolicyDriver.create_policy_version` → engine:PolicyEngine.create_policy_version
- `policy_driver.PolicyDriver.create_temporal_policy` → engine:PolicyEngine.create_temporal_policy
- `policy_driver.PolicyDriver.evaluate_with_context` → engine:PolicyEngine.evaluate_with_context
- `policy_driver.PolicyDriver.get_active_cooldowns` → engine:PolicyEngine.get_active_cooldowns
- `policy_driver.PolicyDriver.get_current_version` → engine:PolicyEngine.get_current_version
- `policy_driver.PolicyDriver.get_dependency_graph` → engine:PolicyEngine.get_dependency_graph
- `policy_driver.PolicyDriver.get_ethical_constraints` → engine:PolicyEngine.get_ethical_constraints
- `policy_driver.PolicyDriver.get_metrics` → engine:PolicyEngine.get_metrics
- `policy_driver.PolicyDriver.get_policy_conflicts` → engine:PolicyEngine.get_policy_conflicts
- `policy_driver.PolicyDriver.get_policy_versions` → engine:PolicyEngine.get_policy_versions
- `policy_driver.PolicyDriver.get_risk_ceiling` → engine:PolicyEngine.get_risk_ceiling
- `policy_driver.PolicyDriver.get_risk_ceilings` → engine:PolicyEngine.get_risk_ceilings
- `policy_driver.PolicyDriver.get_safety_rules` → engine:PolicyEngine.get_safety_rules
- `policy_driver.PolicyDriver.get_state` → engine:PolicyEngine.get_state
- `policy_driver.PolicyDriver.get_temporal_policies` → engine:PolicyEngine.get_temporal_policies
- `policy_driver.PolicyDriver.get_temporal_storage_stats` → engine:PolicyEngine.get_temporal_storage_stats
- `policy_driver.PolicyDriver.get_temporal_utilization` → engine:PolicyEngine.get_temporal_utilization
- `policy_driver.PolicyDriver.get_topological_evaluation_order` → engine:PolicyEngine.get_topological_evaluation_order
- `policy_driver.PolicyDriver.get_version_provenance` → engine:PolicyEngine.get_version_provenance
- `policy_driver.PolicyDriver.get_violation` → engine:PolicyEngine.get_violation
- `policy_driver.PolicyDriver.get_violations` → engine:PolicyEngine.get_violations
- `policy_driver.PolicyDriver.pre_check` → engine:PolicyEngine.pre_check
- `policy_driver.PolicyDriver.prune_temporal_metrics` → engine:PolicyEngine.prune_temporal_metrics
- `policy_driver.PolicyDriver.reload_policies` → engine:PolicyEngine.reload_policies
- `policy_driver.PolicyDriver.reset_risk_ceiling` → engine:PolicyEngine.reset_risk_ceiling
- `policy_driver.PolicyDriver.resolve_conflict` → engine:PolicyEngine.resolve_conflict
- `policy_driver.PolicyDriver.rollback_to_version` → engine:PolicyEngine.rollback_to_version
- `policy_driver.PolicyDriver.update_risk_ceiling` → engine:PolicyEngine.update_risk_ceiling
- `policy_driver.PolicyDriver.update_safety_rule` → engine:PolicyEngine.update_safety_rule
- `policy_driver.PolicyDriver.validate_dependency_dag` → engine:PolicyEngine.validate_dependency_dag
- `policy_driver.reset_policy_driver` → ?
- `policy_engine_driver.PolicyEngineDriver.__init__` → ?
- `policy_engine_driver.PolicyEngineDriver.activate_version` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.cap_temporal_events` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.deactivate_all_versions` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.delete_old_temporal_events` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.fetch_active_policies_for_integrity` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.fetch_dependency_edges_with_type` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.insert_dependency` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.insert_evaluation` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.insert_policy_version` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.insert_provenance` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.insert_temporal_policy` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.insert_violation` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.mark_version_rolled_back` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.reset_risk_ceiling` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.resolve_conflict` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.PolicyEngineDriver.update_violation_acknowledged` → deterministic_engine:DeterministicEngine.execute
- `policy_engine_driver.get_policy_engine_driver` → ?
- `policy_graph_driver.PolicyGraphDriver.__init__` → ?
- `policy_graph_driver.get_policy_graph_driver` → ?
- `policy_graph_engine.PolicyConflict.to_dict` → ?
- `policy_graph_engine.PolicyConflictEngine.__init__` → ?
- `policy_graph_engine.PolicyConflictEngine._involves_policy` → policy_limits_engine:PolicyLimitsService.get
- `policy_graph_engine.PolicyDependency.to_dict` → ?
- `policy_graph_engine.PolicyDependencyEngine.__init__` → ?
- `policy_graph_engine.PolicyNode.to_dict` → ?
- `policy_graph_engine.get_conflict_engine` → ?
- `policy_graph_engine.get_dependency_engine` → ?
- `policy_limits_engine.PolicyLimitsService.__init__` → ?
- `policy_limits_engine.PolicyLimitsService._to_response` → ?
- `policy_limits_engine.PolicyLimitsService.get` → policy_limits_engine:PolicyLimitsService._get_limit
- `policy_mapper.MCPPolicyDecision.allow` → ?
- `policy_mapper.MCPPolicyDecision.deny` → ?
- `policy_mapper.MCPPolicyDecision.to_dict` → ?
- `policy_mapper.MCPPolicyMapper.__init__` → ?
- `policy_mapper.MCPPolicyMapper._check_explicit_allow` → ?
- `policy_mapper.MCPPolicyMapper._check_rate_limit` → ?
- `policy_mapper.reset_mcp_policy_mapper` → ?
- `policy_proposal_engine.PolicyActivationBlockedError.__init__` → arbitrator:PolicyArbitrator.__init__
- `policy_proposal_engine.PolicyDeletionBlockedError.__init__` → arbitrator:PolicyArbitrator.__init__
- `policy_proposal_engine.PolicyProposalEngine.__init__` → ?
- `policy_proposal_engine.check_proposal_eligibility` → policy_proposal_engine:PolicyProposalEngine.check_proposal_eligibility
- `policy_proposal_engine.create_policy_proposal` → policy_proposal_engine:PolicyProposalEngine.create_proposal
- `policy_proposal_engine.delete_policy_rule` → policy_proposal_engine:PolicyProposalEngine.delete_policy_rule
- `policy_proposal_engine.get_proposal_summary` → policy_proposal_engine:PolicyProposalEngine.get_proposal_summary
- `policy_proposal_engine.review_policy_proposal` → policy_proposal_engine:PolicyProposalEngine.review_proposal
- `policy_proposal_read_driver.PolicyProposalReadDriver.__init__` → ?
- `policy_proposal_read_driver.get_policy_proposal_read_driver` → ?
- `policy_proposal_write_driver.PolicyProposalWriteDriver.__init__` → ?
- `policy_proposal_write_driver.PolicyProposalWriteDriver.delete_policy_rule` → deterministic_engine:DeterministicEngine.execute
- `policy_proposal_write_driver.get_policy_proposal_write_driver` → ?
- `policy_read_driver.PolicyReadDriver.__init__` → ?
- `policy_read_driver.PolicyReadDriver._to_guardrail_dto` → ?
- `policy_read_driver.get_policy_read_driver` → ?
- `policy_rules_driver.PolicyRulesDriver.__init__` → ?
- `policy_rules_driver.PolicyRulesDriver.add_integrity` → ?
- `policy_rules_driver.PolicyRulesDriver.add_rule` → ?
- `policy_rules_driver.PolicyRulesDriver.flush` → ?
- `policy_rules_driver.get_policy_rules_driver` → ?
- `policy_rules_engine.PolicyRulesService.__init__` → policy_rules_driver:get_policy_rules_driver
- `policy_rules_engine.PolicyRulesService._to_response` → ?
- `policy_rules_engine.PolicyRulesService.get` → policy_limits_engine:PolicyLimitsService._to_response
- `policy_rules_read_driver.PolicyRulesReadDriver.__init__` → ?
- `policy_rules_read_driver.get_policy_rules_read_driver` → ?
- `prevention_engine.PolicyViolationError.__init__` → arbitrator:PolicyArbitrator.__init__
- `prevention_engine.PreventionEngine.__init__` → ?
- `prevention_engine.PreventionResult.allow` → ?
- `prevention_engine.PreventionResult.block` → ?
- `prevention_engine.PreventionResult.warn` → ?
- `prevention_hook.PreventionResult.to_dict` → ?
- `prevention_hook.create_prevention_hook` → ?
- `proposals_read_driver.ProposalsReadDriver.__init__` → ?
- `proposals_read_driver.get_proposals_read_driver` → ?
- `protection_provider.AbuseProtectionProvider.check_all` → ?
- `protection_provider.AbuseProtectionProvider.check_burst` → ?
- `protection_provider.AbuseProtectionProvider.check_cost` → ?
- `protection_provider.AbuseProtectionProvider.check_rate_limit` → ?
- `protection_provider.AbuseProtectionProvider.detect_anomaly` → ?
- `protection_provider.MockAbuseProtectionProvider.add_cost` → policy_limits_engine:PolicyLimitsService.get
- `protection_provider.set_protection_provider` → ?
- `recovery_evaluation_engine.RecoveryDecision.to_dict` → ?
- `recovery_evaluation_engine.RecoveryEvaluationEngine.__init__` → ?
- `recovery_matcher.RecoveryMatcher.__init__` → ?
- `recovery_matcher.RecoveryMatcher._calculate_time_weight` → ?
- `recovery_write_driver.RecoveryWriteService.__init__` → ?
- `recovery_write_driver.RecoveryWriteService.enqueue_evaluation_db_fallback` → deterministic_engine:DeterministicEngine.execute
- `recovery_write_driver.RecoveryWriteService.insert_suggestion_provenance` → deterministic_engine:DeterministicEngine.execute
- `runtime_command.get_resource_contract` → ?
- `runtime_command.get_supported_query_types` → ?
- `runtime_command.list_skills` → snapshot_engine:PolicySnapshotRegistry.list
- `runtime_command.query_execution_history` → ?
- `runtime_command.query_last_step_outcome` → ?
- `runtime_command.query_remaining_budget` → ?
- `sandbox_engine.ExecutionRecord.to_dict` → ?
- `sandbox_engine.SandboxPolicy.to_dict` → snapshot_engine:PolicySnapshotRegistry.list
- `sandbox_engine.SandboxPolicy.to_resource_limits` → ?
- `sandbox_engine.SandboxService.get_policy` → policy_limits_engine:PolicyLimitsService.get
- `sandbox_engine.SandboxService.list_policies` → ?
- `scope_resolver.ScopeResolutionResult.to_snapshot` → ?
- `scope_resolver.ScopeResolver.__init__` → ?
- `scope_resolver.ScopeResolver.matches_scope` → ?
- `snapshot_engine.PolicySnapshotData.get_policies` → ?
- `snapshot_engine.PolicySnapshotData.get_thresholds` → ?
- `snapshot_engine.PolicySnapshotData.verify_integrity` → ast:PolicyAST.compute_hash
- `snapshot_engine.PolicySnapshotData.verify_threshold_integrity` → ast:PolicyAST.compute_hash
- `snapshot_engine.PolicySnapshotError.to_dict` → ?
- `snapshot_engine.PolicySnapshotRegistry.__init__` → ?
- `snapshot_engine.PolicySnapshotRegistry.get` → policy_limits_engine:PolicyLimitsService.get
- `snapshot_engine.PolicySnapshotRegistry.get_history` → ?
- `snapshot_engine.SnapshotRegistryStats.to_dict` → ?
- `snapshot_engine.create_policy_snapshot` → learning_proof_engine:PrioritizedCheckpoint.create
- `snapshot_engine.get_active_snapshot` → snapshot_engine:PolicySnapshotRegistry.get_active
- `snapshot_engine.get_policy_snapshot` → policy_limits_engine:PolicyLimitsService.get
- `snapshot_engine.get_snapshot_history` → snapshot_engine:PolicySnapshotRegistry.get_history
- `snapshot_engine.verify_snapshot` → snapshot_engine:PolicySnapshotRegistry.verify
- `state.BillingState.allows_usage` → ?
- `state.BillingState.default` → ?
- `state.BillingState.is_in_good_standing` → ?
- `symbol_table.Symbol.__repr__` → ?
- `symbol_table.SymbolTable.get_policies` → ?
- `symbol_table.SymbolTable.lookup` → symbol_table:Scope.lookup
- `tokenizer.Token.__repr__` → ?
- `tokenizer.Token.is_action` → ?
- `tokenizer.Token.is_category` → ?
- `validator.PolicyValidator.__init__` → ?
- `validator.ValidationIssue.__str__` → ?
- `validator.ValidationResult.__bool__` → ?
- `validator.ValidationResult.__post_init__` → ?
- `validator.ValidationResult.errors` → ?
- `validator.ValidationResult.warnings` → ?
- `validator.is_valid` → content_accuracy:ContentAccuracyValidator.validate
- `validator.validate` → content_accuracy:ContentAccuracyValidator.validate
- `visitors.BaseVisitor.visit_ident` → ?
- `visitors.BaseVisitor.visit_import` → ?
- `visitors.BaseVisitor.visit_literal` → ?
- `visitors.BaseVisitor.visit_priority` → ?
- `visitors.BaseVisitor.visit_route_target` → ?
- `visitors.BaseVisitor.visit_rule_ref` → ?
- `visitors.CategoryCollector.__init__` → ?
- `visitors.CategoryCollector.get_categories` → ?
- `visitors.PrintVisitor.__init__` → ?
- `visitors.PrintVisitor._emit` → ?
- `visitors.PrintVisitor.get_output` → ?
- `visitors.PrintVisitor.visit_action_block` → ir_builder:IRBuilder._emit
- `visitors.PrintVisitor.visit_ident` → ir_builder:IRBuilder._emit
- `visitors.PrintVisitor.visit_import` → ir_builder:IRBuilder._emit
- `visitors.PrintVisitor.visit_literal` → ir_builder:IRBuilder._emit
- `visitors.PrintVisitor.visit_priority` → ir_builder:IRBuilder._emit
- `visitors.PrintVisitor.visit_route_target` → ir_builder:IRBuilder._emit
- `visitors.PrintVisitor.visit_rule_ref` → ir_builder:IRBuilder._emit
- `visitors.RuleExtractor.__init__` → ?
- `visitors.RuleExtractor.get_rules` → ?
- `worker_execution_command.calculate_cost_cents` → ?
- `worker_execution_command.get_brand_schema_types` → ?
- `worker_execution_command.replay_execution` → ?

## Full Call Graph

```
[WRAPPER] arbitrator.PolicyArbitrator.__init__
[LEAF] arbitrator.PolicyArbitrator._get_precedence_map
[INTERNAL] arbitrator.PolicyArbitrator._load_precedence_map → arbitrator:PolicyArbitrator._get_precedence_map
[SUPERSET] arbitrator.PolicyArbitrator._resolve_action_conflict → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] arbitrator.PolicyArbitrator._resolve_limit_conflict → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] arbitrator.PolicyArbitrator.arbitrate → arbitrator:PolicyArbitrator._load_precedence_map, arbitrator:PolicyArbitrator._resolve_action_conflict, arbitrator:PolicyArbitrator._resolve_limit_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_action_conflict, policy_limits_engine:PolicyLimitsService.get, ...+2
[LEAF] arbitrator.get_policy_arbitrator
[WRAPPER] ast.BlockAction.to_dict
[LEAF] ast.Clause.__post_init__
[WRAPPER] ast.Clause.to_dict → ast:BlockAction.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ast:PolicyMetadata.to_dict, ...+37
[WRAPPER] ast.ExistsPredicate.to_dict
[WRAPPER] ast.LogicalCondition.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:PolicyAST.to_dict, ast:PolicyMetadata.to_dict, ...+37
[LEAF] ast.PolicyAST.__post_init__
[INTERNAL] ast.PolicyAST.compute_hash → ast:PolicyAST.to_json, ir_compiler:PolicyIR.to_json
[WRAPPER] ast.PolicyAST.mode
[WRAPPER] ast.PolicyAST.name
[WRAPPER] ast.PolicyAST.scope
[WRAPPER] ast.PolicyAST.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyMetadata.to_dict, ...+37
[WRAPPER] ast.PolicyAST.to_json → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+38
[WRAPPER] ast.PolicyAST.version
[LEAF] ast.PolicyMetadata.__post_init__
[WRAPPER] ast.PolicyMetadata.to_dict
[WRAPPER] ast.Predicate.to_dict
[WRAPPER] ast.RequireApprovalAction.to_dict
[WRAPPER] ast.WarnAction.to_dict
[WRAPPER] ast.is_block_action
[WRAPPER] ast.is_exists_predicate
[WRAPPER] ast.is_logical_condition
[WRAPPER] ast.is_predicate
[WRAPPER] ast.is_require_approval_action
[WRAPPER] ast.is_warn_action
[LEAF] authority_checker.OverrideAuthorityChecker._is_override_active
[CANONICAL] authority_checker.OverrideAuthorityChecker.check → authority_checker:OverrideAuthorityChecker._is_override_active
[LEAF] authority_checker.OverrideAuthorityChecker.check_from_dict
[WRAPPER] authority_checker.OverrideCheckResult.to_dict
[WRAPPER] authority_checker.should_skip_enforcement → authority_checker:OverrideAuthorityChecker.check, phase_status_invariants:PhaseStatusInvariantChecker.check
[SUPERSET] binding_moment_enforcer._check_fields_changed → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] binding_moment_enforcer._mark_evaluated
[WRAPPER] binding_moment_enforcer._was_evaluated
[LEAF] binding_moment_enforcer.clear_run_cache
[LEAF] binding_moment_enforcer.get_binding_moment
[SUPERSET] binding_moment_enforcer.should_evaluate_policy → binding_moment_enforcer:_check_fields_changed, binding_moment_enforcer:_mark_evaluated, binding_moment_enforcer:_was_evaluated, binding_moment_enforcer:get_binding_moment, policy_limits_engine:PolicyLimitsService.get, ...+2
[WRAPPER] claim_decision_engine.determine_claim_status → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] claim_decision_engine.get_result_confidence → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] claim_decision_engine.is_candidate_claimable
[WRAPPER] compiler_parser.ParseError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, deterministic_engine:DeterministicEngine.__init__, ...+67
[WRAPPER] compiler_parser.Parser.__init__
[WRAPPER] compiler_parser.Parser.advance
[LEAF] compiler_parser.Parser.current
[INTERNAL] compiler_parser.Parser.expect → compiler_parser:Parser.advance, tokenizer:Tokenizer.advance
[ENTRY] compiler_parser.Parser.from_source → dsl_parser:Lexer.tokenize, tokenizer:Tokenizer.tokenize
[WRAPPER] compiler_parser.Parser.match
[SUPERSET] compiler_parser.Parser.parse → compiler_parser:Parser.match, compiler_parser:Parser.parse_import, compiler_parser:Parser.parse_policy_decl, compiler_parser:Parser.parse_rule_decl
[SUPERSET] compiler_parser.Parser.parse_action_block → compiler_parser:Parser.advance, compiler_parser:Parser.parse_route_target, tokenizer:Tokenizer.advance
[INTERNAL] compiler_parser.Parser.parse_and_expr → compiler_parser:Parser.advance, compiler_parser:Parser.match, compiler_parser:Parser.parse_not_expr, tokenizer:Tokenizer.advance
[INTERNAL] compiler_parser.Parser.parse_category → compiler_parser:Parser.advance, compiler_parser:Parser.match, tokenizer:Tokenizer.advance
[INTERNAL] compiler_parser.Parser.parse_comparison → compiler_parser:Parser.advance, compiler_parser:Parser.parse_value, tokenizer:Tokenizer.advance
[INTERNAL] compiler_parser.Parser.parse_condition_block → compiler_parser:Parser.expect, compiler_parser:Parser.parse_action_block, compiler_parser:Parser.parse_expr, dsl_parser:Parser.expect
[WRAPPER] compiler_parser.Parser.parse_expr → compiler_parser:Parser.parse_or_expr
[INTERNAL] compiler_parser.Parser.parse_func_call → compiler_parser:Parser.advance, compiler_parser:Parser.expect, compiler_parser:Parser.match, compiler_parser:Parser.parse_expr, dsl_parser:Parser.expect, ...+1
[INTERNAL] compiler_parser.Parser.parse_import → compiler_parser:Parser.expect, dsl_parser:Parser.expect
[INTERNAL] compiler_parser.Parser.parse_not_expr → compiler_parser:Parser.advance, compiler_parser:Parser.match, compiler_parser:Parser.parse_comparison, tokenizer:Tokenizer.advance
[INTERNAL] compiler_parser.Parser.parse_or_expr → compiler_parser:Parser.advance, compiler_parser:Parser.match, compiler_parser:Parser.parse_and_expr, tokenizer:Tokenizer.advance
[SUPERSET] compiler_parser.Parser.parse_policy_body → compiler_parser:Parser.match, compiler_parser:Parser.parse_action_block, compiler_parser:Parser.parse_condition_block, compiler_parser:Parser.parse_priority, compiler_parser:Parser.parse_rule_decl, ...+3
[INTERNAL] compiler_parser.Parser.parse_policy_decl → compiler_parser:Parser.expect, compiler_parser:Parser.parse_category, compiler_parser:Parser.parse_policy_body, dsl_parser:Parser.expect
[INTERNAL] compiler_parser.Parser.parse_priority → compiler_parser:Parser.expect, dsl_parser:Parser.expect
[INTERNAL] compiler_parser.Parser.parse_route_target → compiler_parser:Parser.expect, dsl_parser:Parser.expect
[SUPERSET] compiler_parser.Parser.parse_rule_body → compiler_parser:Parser.match, compiler_parser:Parser.parse_action_block, compiler_parser:Parser.parse_condition_block, compiler_parser:Parser.parse_priority
[INTERNAL] compiler_parser.Parser.parse_rule_decl → compiler_parser:Parser.expect, compiler_parser:Parser.parse_category, compiler_parser:Parser.parse_rule_body, dsl_parser:Parser.expect
[INTERNAL] compiler_parser.Parser.parse_rule_ref → compiler_parser:Parser.expect, dsl_parser:Parser.expect
[CANONICAL] compiler_parser.Parser.parse_value → compiler_parser:Parser.advance, compiler_parser:Parser.expect, compiler_parser:Parser.match, compiler_parser:Parser.parse_expr, compiler_parser:Parser.parse_func_call, ...+2
[LEAF] compiler_parser.Parser.peek
[WRAPPER] content_accuracy.ContentAccuracyResult.to_dict
[INTERNAL] content_accuracy.ContentAccuracyValidator.__init__ → ir_compiler:IRCompiler.compile, ir_compiler:OptimizingIRCompiler.compile
[LEAF] content_accuracy.ContentAccuracyValidator._claims_affirmative
[LEAF] content_accuracy.ContentAccuracyValidator._detect_assertion_type
[LEAF] content_accuracy.ContentAccuracyValidator._extract_claim
[SUPERSET] content_accuracy.ContentAccuracyValidator._get_nested_value → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] content_accuracy.ContentAccuracyValidator.validate → content_accuracy:ContentAccuracyValidator._claims_affirmative, content_accuracy:ContentAccuracyValidator._detect_assertion_type, content_accuracy:ContentAccuracyValidator._extract_claim, content_accuracy:ContentAccuracyValidator._get_nested_value
[WRAPPER] content_accuracy.validate_content_accuracy → content_accuracy:ContentAccuracyValidator.validate, validator:PolicyValidator.validate, validator:validate
[WRAPPER] cus_enforcement_service.get_cus_enforcement_service
[WRAPPER] customer_policy_read_engine.CustomerPolicyReadService.__init__ → policy_read_driver:get_policy_read_driver
[LEAF] customer_policy_read_engine.CustomerPolicyReadService._calculate_period_bounds
[INTERNAL] customer_policy_read_engine.CustomerPolicyReadService._get_budget_constraint → customer_policy_read_engine:CustomerPolicyReadService._calculate_period_bounds, policy_read_driver:PolicyReadDriver.get_tenant_budget_settings, policy_read_driver:PolicyReadDriver.get_usage_sum_since
[WRAPPER] customer_policy_read_engine.CustomerPolicyReadService._get_guardrails → policy_read_driver:PolicyReadDriver.list_all_guardrails
[WRAPPER] customer_policy_read_engine.CustomerPolicyReadService._get_rate_limits
[CANONICAL] customer_policy_read_engine.CustomerPolicyReadService.get_guardrail_detail → policy_read_driver:PolicyReadDriver.get_guardrail_by_id
[ENTRY] customer_policy_read_engine.CustomerPolicyReadService.get_policy_constraints → customer_policy_read_engine:CustomerPolicyReadService._get_budget_constraint, customer_policy_read_engine:CustomerPolicyReadService._get_guardrails, customer_policy_read_engine:CustomerPolicyReadService._get_rate_limits
[WRAPPER] customer_policy_read_engine.get_customer_policy_read_service
[LEAF] decorator._extract_subject
[LEAF] decorator._extract_tenant_id
[CANONICAL] decorator.governed → decorator:_extract_subject, decorator:_extract_tenant_id, kernel:ExecutionKernel.invoke, kernel:ExecutionKernel.invoke_async
[WRAPPER] degraded_mode.DegradedModeStatus.get_inactive
[LEAF] degraded_mode.enter_degraded_mode
[CANONICAL] degraded_mode.exit_degraded_mode → degraded_mode:DegradedModeStatus.get_inactive
[WRAPPER] degraded_mode.get_degraded_mode_status → degraded_mode:DegradedModeStatus.get_inactive
[WRAPPER] degraded_mode.get_existing_run_action
[WRAPPER] degraded_mode.is_degraded_mode_active
[ENTRY] degraded_mode.should_allow_new_run → degraded_mode:is_degraded_mode_active
[WRAPPER] deterministic_engine.DeterministicEngine.__init__ → deterministic_engine:DeterministicEngine._register_builtins
[WRAPPER] deterministic_engine.DeterministicEngine._action_to_intent_type → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] deterministic_engine.DeterministicEngine._call_function → deterministic_engine:DeterministicEngine._execute_function, ir_nodes:IRModule.get_function
[LEAF] deterministic_engine.DeterministicEngine._eval_binary_op
[INTERNAL] deterministic_engine.DeterministicEngine._eval_compare → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] deterministic_engine.DeterministicEngine._eval_unary_op
[SUPERSET] deterministic_engine.DeterministicEngine._execute_function → deterministic_engine:DeterministicEngine._execute_instruction, deterministic_engine:ExecutionContext.add_trace, deterministic_engine:ExecutionContext.pop_call, deterministic_engine:ExecutionContext.push_call, interpreter:Interpreter._execute_instruction, ...+4
[SUPERSET] deterministic_engine.DeterministicEngine._execute_instruction → deterministic_engine:DeterministicEngine._action_to_intent_type, deterministic_engine:DeterministicEngine._call_function, deterministic_engine:DeterministicEngine._eval_binary_op, deterministic_engine:DeterministicEngine._eval_compare, deterministic_engine:DeterministicEngine._eval_unary_op, ...+7
[INTERNAL] deterministic_engine.DeterministicEngine._register_builtins → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] deterministic_engine.DeterministicEngine.execute → deterministic_engine:DeterministicEngine._execute_function, intent:IntentEmitter.clear, intent:IntentEmitter.emit_all, ir_nodes:IRModule.get_function, ir_nodes:IRModule.get_functions_by_category, ...+1
[ENTRY] deterministic_engine.ExecutionContext.__post_init__ → deterministic_engine:ExecutionContext._generate_id, intent:Intent._generate_id
[LEAF] deterministic_engine.ExecutionContext._generate_id
[WRAPPER] deterministic_engine.ExecutionContext.add_trace
[CANONICAL] deterministic_engine.ExecutionContext.get_variable → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] deterministic_engine.ExecutionContext.pop_call
[WRAPPER] deterministic_engine.ExecutionContext.push_call
[WRAPPER] deterministic_engine.ExecutionContext.set_variable
[WRAPPER] deterministic_engine.ExecutionResult.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[INTERNAL] dsl_parser.Lexer.__init__ → ir_compiler:IRCompiler.compile, ir_compiler:OptimizingIRCompiler.compile
[LEAF] dsl_parser.Lexer._advance
[LEAF] dsl_parser.Lexer._convert_value
[CANONICAL] dsl_parser.Lexer.tokenize → compiler_parser:Parser.match, dsl_parser:Lexer._advance, dsl_parser:Lexer._convert_value
[INTERNAL] dsl_parser.ParseError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] dsl_parser.ParseLocation.__str__
[WRAPPER] dsl_parser.Parser.__init__
[SUPERSET] dsl_parser.Parser._parse_actions → dsl_parser:Parser._try_parse_action, dsl_parser:Parser.error
[INTERNAL] dsl_parser.Parser._parse_and_expr → dsl_parser:Parser._parse_atom, dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+13
[SUPERSET] dsl_parser.Parser._parse_atom → compiler_parser:Parser.expect, dsl_parser:Parser._parse_or_expr, dsl_parser:Parser._parse_predicate, dsl_parser:Parser.accept, dsl_parser:Parser.expect, ...+16
[INTERNAL] dsl_parser.Parser._parse_clause → compiler_parser:Parser.expect, dsl_parser:Parser._parse_actions, dsl_parser:Parser._parse_condition, dsl_parser:Parser.expect
[INTERNAL] dsl_parser.Parser._parse_clauses → dsl_parser:Parser._parse_clause, dsl_parser:Parser.error
[WRAPPER] dsl_parser.Parser._parse_condition → dsl_parser:Parser._parse_or_expr
[SUPERSET] dsl_parser.Parser._parse_header → compiler_parser:Parser.expect, dsl_parser:Parser.accept, dsl_parser:Parser.error, dsl_parser:Parser.expect, nodes:ASTNode.accept, ...+15
[INTERNAL] dsl_parser.Parser._parse_or_expr → dsl_parser:Parser._parse_and_expr, dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+13
[INTERNAL] dsl_parser.Parser._parse_predicate → compiler_parser:Parser.expect, dsl_parser:Parser._parse_value, dsl_parser:Parser.accept, dsl_parser:Parser.error, dsl_parser:Parser.expect, ...+16
[INTERNAL] dsl_parser.Parser._parse_value → dsl_parser:Parser.accept, dsl_parser:Parser.error, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+13
[SUPERSET] dsl_parser.Parser._try_parse_action → compiler_parser:Parser.expect, dsl_parser:Parser.accept, dsl_parser:Parser.expect, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, ...+14
[LEAF] dsl_parser.Parser.accept
[LEAF] dsl_parser.Parser.current
[WRAPPER] dsl_parser.Parser.error
[INTERNAL] dsl_parser.Parser.expect → dsl_parser:Parser.error
[INTERNAL] dsl_parser.Parser.parse → compiler_parser:Parser.expect, dsl_parser:Parser._parse_clauses, dsl_parser:Parser._parse_header, dsl_parser:Parser.expect
[ENTRY] dsl_parser.parse → compiler_parser:Parser.parse, dsl_parser:Lexer.tokenize, dsl_parser:Parser.parse, tokenizer:Tokenizer.tokenize
[ENTRY] dsl_parser.parse_condition → dsl_parser:Lexer.tokenize, dsl_parser:Parser._parse_condition, dsl_parser:Parser.error, tokenizer:Tokenizer.tokenize
[WRAPPER] eligibility_engine.CapabilityLookup.exists
[WRAPPER] eligibility_engine.CapabilityLookup.is_frozen
[WRAPPER] eligibility_engine.ContractLookup.has_similar_pending
[WRAPPER] eligibility_engine.DefaultCapabilityLookup.__init__
[WRAPPER] eligibility_engine.DefaultCapabilityLookup.exists
[WRAPPER] eligibility_engine.DefaultCapabilityLookup.is_frozen
[WRAPPER] eligibility_engine.DefaultContractLookup.__init__
[LEAF] eligibility_engine.DefaultContractLookup.has_similar_pending
[WRAPPER] eligibility_engine.DefaultGovernanceSignalLookup.__init__
[LEAF] eligibility_engine.DefaultGovernanceSignalLookup.has_blocking_signal
[WRAPPER] eligibility_engine.DefaultPreApprovalLookup.__init__
[WRAPPER] eligibility_engine.DefaultPreApprovalLookup.has_system_pre_approval
[WRAPPER] eligibility_engine.DefaultSystemHealthLookup.__init__
[WRAPPER] eligibility_engine.DefaultSystemHealthLookup.get_status
[LEAF] eligibility_engine.EligibilityEngine.__init__
[LEAF] eligibility_engine.EligibilityEngine._create_verdict
[LEAF] eligibility_engine.EligibilityEngine._evaluate_e001_confidence_threshold
[SUPERSET] eligibility_engine.EligibilityEngine._evaluate_e002_known_capability → eligibility_engine:CapabilityLookup.exists, eligibility_engine:DefaultCapabilityLookup.exists, snapshot_engine:PolicySnapshotRegistry.list
[SUPERSET] eligibility_engine.EligibilityEngine._evaluate_e003_no_blocking_signal → eligibility_engine:DefaultGovernanceSignalLookup.has_blocking_signal, eligibility_engine:GovernanceSignalLookup.has_blocking_signal
[LEAF] eligibility_engine.EligibilityEngine._evaluate_e004_actionable_type
[WRAPPER] eligibility_engine.EligibilityEngine._evaluate_e005_source_allowlist → snapshot_engine:PolicySnapshotRegistry.list
[ENTRY] eligibility_engine.EligibilityEngine._evaluate_e006_not_duplicate → eligibility_engine:ContractLookup.has_similar_pending, eligibility_engine:DefaultContractLookup.has_similar_pending
[LEAF] eligibility_engine.EligibilityEngine._evaluate_e100_below_minimum_confidence
[LEAF] eligibility_engine.EligibilityEngine._evaluate_e101_critical_without_escalation
[ENTRY] eligibility_engine.EligibilityEngine._evaluate_e102_frozen_capability → eligibility_engine:CapabilityLookup.is_frozen, eligibility_engine:DefaultCapabilityLookup.is_frozen, snapshot_engine:PolicySnapshotRegistry.list
[ENTRY] eligibility_engine.EligibilityEngine._evaluate_e103_system_scope_without_preapproval → eligibility_engine:DefaultPreApprovalLookup.has_system_pre_approval, eligibility_engine:PreApprovalLookup.has_system_pre_approval
[WRAPPER] eligibility_engine.EligibilityEngine._evaluate_e104_health_degraded → eligibility_engine:DefaultSystemHealthLookup.get_status, eligibility_engine:SystemHealthLookup.get_status
[CANONICAL] eligibility_engine.EligibilityEngine.evaluate → eligibility_engine:EligibilityEngine._create_verdict
[WRAPPER] eligibility_engine.GovernanceSignalLookup.has_blocking_signal
[WRAPPER] eligibility_engine.PreApprovalLookup.has_system_pre_approval
[WRAPPER] eligibility_engine.SystemHealthLookup.get_status
[INTERNAL] engine.PolicyEngine.__init__ → policy_engine_driver:get_policy_engine_driver, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] engine.PolicyEngine._add_windowed_value
[SUPERSET] engine.PolicyEngine._check_business_rules → engine:PolicyEngine._evaluate_business_rule, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine._check_compliance → engine:PolicyEngine._evaluate_compliance_rule
[SUPERSET] engine.PolicyEngine._check_cooldown → snapshot_engine:PolicySnapshotRegistry.list
[SUPERSET] engine.PolicyEngine._check_ethical_constraints → engine:PolicyEngine._evaluate_ethical_constraint
[SUPERSET] engine.PolicyEngine._check_risk_ceilings → engine:PolicyEngine._evaluate_risk_ceiling
[SUPERSET] engine.PolicyEngine._check_safety_rules → engine:PolicyEngine._evaluate_safety_rule, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] engine.PolicyEngine._classify_recoverability
[LEAF] engine.PolicyEngine._classify_severity
[SUPERSET] engine.PolicyEngine._evaluate_business_rule → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine._evaluate_compliance_rule → compiler_parser:Parser.match, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:PolicySnapshotRegistry.list
[SUPERSET] engine.PolicyEngine._evaluate_ethical_constraint → engine:PolicyEngine._extract_text_content, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine._evaluate_risk_ceiling → engine:PolicyEngine._add_windowed_value, engine:PolicyEngine._get_windowed_value, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine._evaluate_safety_rule → engine:PolicyEngine._extract_text_content, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] engine.PolicyEngine._extract_text_content
[LEAF] engine.PolicyEngine._get_windowed_value
[LEAF] engine.PolicyEngine._is_cache_stale
[LEAF] engine.PolicyEngine._load_default_policies
[INTERNAL] engine.PolicyEngine._load_policies → dsl_parser:Parser.error, engine:PolicyEngine._load_default_policies, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_business_rules, policy_engine_driver:PolicyEngineDriver.fetch_ethical_constraints, ...+5
[INTERNAL] engine.PolicyEngine._persist_evaluation → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.insert_evaluation, policy_engine_driver:PolicyEngineDriver.insert_violation
[SUPERSET] engine.PolicyEngine._route_to_governor → dsl_parser:Parser.error
[INTERNAL] engine.PolicyEngine.acknowledge_violation → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.update_violation_acknowledged
[SUPERSET] engine.PolicyEngine.activate_policy_version → dsl_parser:Parser.error, eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, engine:PolicyEngine.reload_policies, engine:PolicyEngine.validate_dependency_dag, ...+21
[SUPERSET] engine.PolicyEngine.add_dependency_with_dag_check → dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_dependency_edges, policy_engine_driver:PolicyEngineDriver.insert_dependency, policy_limits_engine:PolicyLimitsService.get, ...+2
[SUPERSET] engine.PolicyEngine.clear_cooldowns → snapshot_engine:PolicySnapshotRegistry.list
[SUPERSET] engine.PolicyEngine.create_policy_version → engine:PolicyEngine.get_current_version, policy_driver:PolicyDriver.get_current_version, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.deactivate_all_versions, policy_engine_driver:PolicyEngineDriver.insert_policy_version
[INTERNAL] engine.PolicyEngine.create_temporal_policy → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.insert_temporal_policy, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] engine.PolicyEngine.evaluate → engine:PolicyEngine._check_business_rules, engine:PolicyEngine._check_compliance, engine:PolicyEngine._check_cooldown, engine:PolicyEngine._check_ethical_constraints, engine:PolicyEngine._check_risk_ceilings, ...+5
[SUPERSET] engine.PolicyEngine.evaluate_with_context → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine._classify_recoverability, engine:PolicyEngine._classify_severity, engine:PolicyEngine._load_policies, engine:PolicyEngine.evaluate, ...+12
[SUPERSET] engine.PolicyEngine.get_active_cooldowns → snapshot_engine:PolicySnapshotRegistry.list
[SUPERSET] engine.PolicyEngine.get_current_version → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_current_active_version, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] engine.PolicyEngine.get_dependency_graph → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_conflicts, policy_engine_driver:PolicyEngineDriver.fetch_dependencies, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, ...+1
[INTERNAL] engine.PolicyEngine.get_ethical_constraints → engine:PolicyEngine._load_policies
[WRAPPER] engine.PolicyEngine.get_metrics
[INTERNAL] engine.PolicyEngine.get_policy_conflicts → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_conflicts, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] engine.PolicyEngine.get_policy_versions → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_policy_versions, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] engine.PolicyEngine.get_risk_ceiling → engine:PolicyEngine._load_policies
[SUPERSET] engine.PolicyEngine.get_risk_ceilings → engine:PolicyEngine._load_policies
[SUPERSET] engine.PolicyEngine.get_safety_rules → engine:PolicyEngine._load_policies
[LEAF] engine.PolicyEngine.get_state
[INTERNAL] engine.PolicyEngine.get_temporal_policies → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_temporal_policies, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine.get_temporal_storage_stats → dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_temporal_storage_stats
[SUPERSET] engine.PolicyEngine.get_temporal_utilization → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_temporal_metric_sum, policy_engine_driver:PolicyEngineDriver.fetch_temporal_policy_for_utilization
[SUPERSET] engine.PolicyEngine.get_topological_evaluation_order → dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] engine.PolicyEngine.get_version_provenance → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_provenance, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine.get_violation → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_violation_by_id, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine.get_violations → policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_violations, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] engine.PolicyEngine.pre_check → dsl_parser:Parser.error, eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine._is_cache_stale, engine:PolicyEngine._load_policies, engine:PolicyEngine.evaluate, ...+5
[INTERNAL] engine.PolicyEngine.prune_temporal_metrics → dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.cap_temporal_events, policy_engine_driver:PolicyEngineDriver.compact_temporal_events, policy_engine_driver:PolicyEngineDriver.delete_old_temporal_events, ...+4
[WRAPPER] engine.PolicyEngine.reload_policies → engine:PolicyEngine._load_policies
[INTERNAL] engine.PolicyEngine.reset_risk_ceiling → policy_driver:PolicyDriver.reset_risk_ceiling, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.reset_risk_ceiling
[INTERNAL] engine.PolicyEngine.resolve_conflict → governance_facade:GovernanceFacade.resolve_conflict, policy_driver:PolicyDriver.resolve_conflict, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.resolve_conflict
[SUPERSET] engine.PolicyEngine.rollback_to_version → dsl_parser:Parser.error, engine:PolicyEngine.reload_policies, policy_driver:PolicyDriver.reload_policies, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.activate_version, ...+3
[WRAPPER] engine.PolicyEngine.set_governor
[INTERNAL] engine.PolicyEngine.update_risk_ceiling → engine:PolicyEngine.get_risk_ceiling, engine:PolicyEngine.reload_policies, policy_driver:PolicyDriver.get_risk_ceiling, policy_driver:PolicyDriver.reload_policies, policy_driver:PolicyDriver.update_risk_ceiling, ...+2
[SUPERSET] engine.PolicyEngine.update_safety_rule → engine:PolicyEngine.reload_policies, policy_driver:PolicyDriver.reload_policies, policy_driver:PolicyDriver.update_safety_rule, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.update_safety_rule
[SUPERSET] engine.PolicyEngine.validate_dependency_dag → dsl_parser:Parser.error, policy_engine_driver:PolicyEngineDriver._get_engine, policy_engine_driver:PolicyEngineDriver.fetch_dependency_edges_with_type, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, ...+1
[INTERNAL] engine.get_policy_engine → engine:PolicyEngine.set_governor
[LEAF] failure_mode_handler.get_failure_mode
[WRAPPER] failure_mode_handler.handle_evaluation_error → failure_mode_handler:handle_policy_failure
[WRAPPER] failure_mode_handler.handle_missing_policy → failure_mode_handler:handle_policy_failure
[CANONICAL] failure_mode_handler.handle_policy_failure → dsl_parser:Parser.error, failure_mode_handler:get_failure_mode, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] failure_mode_handler.handle_timeout → failure_mode_handler:handle_policy_failure
[WRAPPER] folds.ConstantFolder.__init__
[SUPERSET] folds.ConstantFolder._fold_binary_op → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] folds.ConstantFolder._fold_compare → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] folds.ConstantFolder._fold_unary_op → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] folds.ConstantFolder.fold_block → folds:ConstantFolder.try_fold
[INTERNAL] folds.ConstantFolder.fold_function → folds:ConstantFolder.fold_block
[ENTRY] folds.ConstantFolder.fold_module → folds:ConstantFolder.fold_function
[CANONICAL] folds.ConstantFolder.try_fold → folds:ConstantFolder._fold_binary_op, folds:ConstantFolder._fold_compare, folds:ConstantFolder._fold_unary_op
[WRAPPER] folds.DeadCodeEliminator.__init__
[INTERNAL] folds.DeadCodeEliminator._eliminate_function → folds:DeadCodeEliminator._find_reachable_blocks, folds:DeadCodeEliminator._find_used_instructions
[SUPERSET] folds.DeadCodeEliminator._find_reachable_blocks → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] folds.DeadCodeEliminator._find_used_instructions
[LEAF] folds.DeadCodeEliminator._mark_governance_critical
[ENTRY] folds.DeadCodeEliminator.eliminate → folds:DeadCodeEliminator._eliminate_function, folds:DeadCodeEliminator._mark_governance_critical
[WRAPPER] folds.PolicySimplifier.__init__
[SUPERSET] folds.PolicySimplifier._find_mergeable_policies → snapshot_engine:PolicySnapshotRegistry.list
[LEAF] folds.PolicySimplifier._merge_policies
[ENTRY] folds.PolicySimplifier.simplify → folds:PolicySimplifier._find_mergeable_policies, folds:PolicySimplifier._merge_policies
[WRAPPER] governance_facade.BootStatusResult.to_dict
[WRAPPER] governance_facade.ConflictResolutionResult.to_dict
[WRAPPER] governance_facade.GovernanceFacade.__init__
[ENTRY] governance_facade.GovernanceFacade.disable_kill_switch → dsl_parser:Parser.error
[SUPERSET] governance_facade.GovernanceFacade.enable_kill_switch → dsl_parser:Parser.error
[ENTRY] governance_facade.GovernanceFacade.get_boot_status → dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] governance_facade.GovernanceFacade.get_governance_state → dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] governance_facade.GovernanceFacade.list_conflicts → dsl_parser:Parser.error
[INTERNAL] governance_facade.GovernanceFacade.resolve_conflict → dsl_parser:Parser.error
[CANONICAL] governance_facade.GovernanceFacade.set_mode → degraded_mode:enter_degraded_mode, degraded_mode:exit_degraded_mode, dsl_parser:Parser.error
[WRAPPER] governance_facade.GovernanceStateResult.to_dict
[WRAPPER] governance_facade.KillSwitchResult.to_dict
[LEAF] governance_facade.get_governance_facade
[WRAPPER] grammar.PLangGrammar.get_action_precedence → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] grammar.PLangGrammar.get_category_priority → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] grammar.PLangGrammar.is_action
[WRAPPER] grammar.PLangGrammar.is_category
[WRAPPER] grammar.PLangGrammar.is_keyword
[WRAPPER] grammar.PLangGrammar.is_operator
[ENTRY] intent.Intent.__post_init__ → deterministic_engine:ExecutionContext._generate_id, intent:Intent._generate_id
[INTERNAL] intent.Intent._generate_id → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+38
[ENTRY] intent.Intent.from_dict → intent:IntentPayload.from_dict, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] intent.Intent.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[WRAPPER] intent.IntentEmitter.__init__
[WRAPPER] intent.IntentEmitter.clear
[LEAF] intent.IntentEmitter.create_intent
[SUPERSET] intent.IntentEmitter.emit → intent:IntentEmitter.validate_intent, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] intent.IntentEmitter.emit_all → intent:IntentEmitter.emit, snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] intent.IntentEmitter.get_emitted → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] intent.IntentEmitter.get_pending → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] intent.IntentEmitter.register_handler
[LEAF] intent.IntentEmitter.validate_intent
[INTERNAL] intent.IntentPayload.from_dict → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] intent.IntentPayload.to_dict
[LEAF] interpreter.ActionResult.to_dict
[WRAPPER] interpreter.ClauseResult.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[INTERNAL] interpreter.EvaluationError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] interpreter.EvaluationResult.has_block
[WRAPPER] interpreter.EvaluationResult.has_require_approval
[WRAPPER] interpreter.EvaluationResult.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[WRAPPER] interpreter.EvaluationResult.warnings
[WRAPPER] interpreter.Interpreter.__init__
[LEAF] interpreter.Interpreter._collect_actions
[SUPERSET] interpreter.Interpreter._compare → interpreter:Interpreter._types_compatible
[INTERNAL] interpreter.Interpreter._evaluate_clause → interpreter:Interpreter._collect_actions, interpreter:Interpreter._evaluate_condition
[SUPERSET] interpreter.Interpreter._evaluate_condition → deterministic_engine:DeterministicEngine._execute_instruction, interpreter:Interpreter._execute_instruction, interpreter:_LenientInterpreter._execute_instruction
[SUPERSET] interpreter.Interpreter._execute_instruction → interpreter:Interpreter._compare, interpreter:_LenientInterpreter._compare
[LEAF] interpreter.Interpreter._types_compatible
[CANONICAL] interpreter.Interpreter.evaluate → interpreter:Interpreter._evaluate_clause
[INTERNAL] interpreter._LenientInterpreter._compare → interpreter:Interpreter._compare
[SUPERSET] interpreter._LenientInterpreter._execute_instruction → deterministic_engine:DeterministicEngine._execute_instruction, interpreter:Interpreter._execute_instruction
[WRAPPER] interpreter.evaluate → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, policy_driver:PolicyDriver.evaluate, prevention_hook:PreventionHook.evaluate, ...+1
[ENTRY] interpreter.evaluate_policy → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, ...+2
[LEAF] ir_builder.IRBuilder.__init__
[INTERNAL] ir_builder.IRBuilder._emit → ir_builder:IRBuilder._next_id, ir_nodes:IRBlock.add_instruction
[INTERNAL] ir_builder.IRBuilder._new_block → ir_nodes:IRFunction.add_block
[WRAPPER] ir_builder.IRBuilder._next_block_name
[WRAPPER] ir_builder.IRBuilder._next_id
[ENTRY] ir_builder.IRBuilder.build → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[SUPERSET] ir_builder.IRBuilder.visit_action_block → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] ir_builder.IRBuilder.visit_attr_access → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[INTERNAL] ir_builder.IRBuilder.visit_binary_op → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[INTERNAL] ir_builder.IRBuilder.visit_condition_block → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, ir_builder:IRBuilder._new_block, ir_builder:IRBuilder._next_block_name, nodes:ASTNode.accept, ...+16
[SUPERSET] ir_builder.IRBuilder.visit_func_call → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[INTERNAL] ir_builder.IRBuilder.visit_ident → ir_builder:IRBuilder._emit, symbol_table:SymbolTable.add_reference, visitors:PrintVisitor._emit
[WRAPPER] ir_builder.IRBuilder.visit_import
[WRAPPER] ir_builder.IRBuilder.visit_literal → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] ir_builder.IRBuilder.visit_policy_decl → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, ir_builder:IRBuilder._new_block, ir_nodes:IRGovernance.from_ast, ir_nodes:IRModule.add_function, ...+21
[LEAF] ir_builder.IRBuilder.visit_priority
[INTERNAL] ir_builder.IRBuilder.visit_program → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[WRAPPER] ir_builder.IRBuilder.visit_route_target
[CANONICAL] ir_builder.IRBuilder.visit_rule_decl → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, ir_builder:IRBuilder._new_block, ir_nodes:IRGovernance.from_ast, ir_nodes:IRModule.add_function, ...+21
[INTERNAL] ir_builder.IRBuilder.visit_rule_ref → ir_builder:IRBuilder._emit, symbol_table:SymbolTable.lookup_rule, visitors:PrintVisitor._emit
[INTERNAL] ir_builder.IRBuilder.visit_unary_op → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[WRAPPER] ir_compiler.CompiledClause.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[WRAPPER] ir_compiler.IRCompiler.__init__
[SUPERSET] ir_compiler.IRCompiler._compile_actions → ast:is_block_action, ast:is_require_approval_action, ast:is_warn_action
[INTERNAL] ir_compiler.IRCompiler._compile_clause → ir_compiler:IRCompiler._compile_actions, ir_compiler:IRCompiler._compile_condition
[WRAPPER] ir_compiler.IRCompiler._compile_condition → ir_compiler:IRCompiler._emit_condition
[SUPERSET] ir_compiler.IRCompiler._emit_condition → ast:is_exists_predicate, ast:is_logical_condition, ast:is_predicate, ir_compiler:IRCompiler._emit_exists, ir_compiler:IRCompiler._emit_logical, ...+1
[WRAPPER] ir_compiler.IRCompiler._emit_exists
[INTERNAL] ir_compiler.IRCompiler._emit_logical → ir_compiler:IRCompiler._emit_condition
[LEAF] ir_compiler.IRCompiler._emit_predicate
[INTERNAL] ir_compiler.IRCompiler.compile → ir_compiler:IRCompiler._compile_clause
[WRAPPER] ir_compiler.Instruction.to_dict → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] ir_compiler.OptimizingIRCompiler.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] ir_compiler.OptimizingIRCompiler.compile → ir_compiler:IRCompiler.compile
[INTERNAL] ir_compiler.PolicyIR.compute_hash → ast:PolicyAST.to_json, ir_compiler:PolicyIR.to_json
[LEAF] ir_compiler.PolicyIR.instruction_count
[WRAPPER] ir_compiler.PolicyIR.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[WRAPPER] ir_compiler.PolicyIR.to_json → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+38
[INTERNAL] ir_compiler.compile_policy → ir_compiler:IRCompiler.compile, ir_compiler:OptimizingIRCompiler.compile
[WRAPPER] ir_compiler.ir_hash → ast:PolicyAST.compute_hash, ir_compiler:PolicyIR.compute_hash, ir_compiler:compile_policy, snapshot_engine:PolicySnapshotData.compute_hash
[LEAF] ir_nodes.IRAction.__str__
[WRAPPER] ir_nodes.IRBinaryOp.__str__
[LEAF] ir_nodes.IRBlock.__str__
[WRAPPER] ir_nodes.IRBlock.add_instruction
[LEAF] ir_nodes.IRBlock.is_terminated
[WRAPPER] ir_nodes.IRCall.__str__
[WRAPPER] ir_nodes.IRCheckPolicy.__str__
[WRAPPER] ir_nodes.IRCompare.__str__
[LEAF] ir_nodes.IREmitIntent.__str__
[LEAF] ir_nodes.IRFunction.__str__
[WRAPPER] ir_nodes.IRFunction.add_block
[WRAPPER] ir_nodes.IRFunction.get_block → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] ir_nodes.IRGovernance.from_ast
[WRAPPER] ir_nodes.IRGovernance.to_dict
[WRAPPER] ir_nodes.IRJump.__str__
[WRAPPER] ir_nodes.IRJumpIf.__str__
[WRAPPER] ir_nodes.IRLoadConst.__str__
[WRAPPER] ir_nodes.IRLoadVar.__str__
[LEAF] ir_nodes.IRModule.__str__
[LEAF] ir_nodes.IRModule.add_function
[WRAPPER] ir_nodes.IRModule.get_function → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] ir_nodes.IRModule.get_functions_by_category → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] ir_nodes.IRNode.__str__
[LEAF] ir_nodes.IRReturn.__str__
[WRAPPER] ir_nodes.IRStoreVar.__str__
[WRAPPER] ir_nodes.IRUnaryOp.__str__
[SUPERSET] kernel.ExecutionKernel._emit_envelope → dsl_parser:Parser.error
[WRAPPER] kernel.ExecutionKernel._record_invocation_complete
[WRAPPER] kernel.ExecutionKernel._record_invocation_start
[WRAPPER] kernel.ExecutionKernel.get_known_capabilities
[INTERNAL] kernel.ExecutionKernel.invoke → kernel:ExecutionKernel._emit_envelope, kernel:ExecutionKernel._record_invocation_complete, kernel:ExecutionKernel._record_invocation_start, kernel:get_enforcement_mode
[CANONICAL] kernel.ExecutionKernel.invoke_async → kernel:ExecutionKernel._emit_envelope, kernel:ExecutionKernel._record_invocation_complete, kernel:ExecutionKernel._record_invocation_start, kernel:get_enforcement_mode
[WRAPPER] kernel.ExecutionKernel.is_known_capability
[WRAPPER] kernel.get_enforcement_mode → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] kernel.set_enforcement_mode
[WRAPPER] keys_shim.KeysReadService.__init__
[WRAPPER] keys_shim.KeysReadService.get_key
[WRAPPER] keys_shim.KeysReadService.get_key_usage_today
[WRAPPER] keys_shim.KeysReadService.list_keys
[WRAPPER] keys_shim.KeysWriteService.__init__
[WRAPPER] keys_shim.KeysWriteService.freeze_key
[WRAPPER] keys_shim.KeysWriteService.unfreeze_key
[WRAPPER] keys_shim.get_keys_read_service
[WRAPPER] keys_shim.get_keys_write_service
[WRAPPER] kill_switch.KillSwitchStatus.get_current
[LEAF] kill_switch.activate_kill_switch
[LEAF] kill_switch.deactivate_kill_switch
[LEAF] kill_switch.is_kill_switch_active
[WRAPPER] kill_switch.should_bypass_governance → kill_switch:is_kill_switch_active
[LEAF] learning_proof_engine.AdaptiveConfidenceSystem.get_confidence_report
[LEAF] learning_proof_engine.AdaptiveConfidenceSystem.get_or_create_calibration
[LEAF] learning_proof_engine.AdaptiveConfidenceSystem.get_threshold_for_pattern
[ENTRY] learning_proof_engine.AdaptiveConfidenceSystem.record_outcome → learning_proof_engine:AdaptiveConfidenceSystem.get_or_create_calibration, learning_proof_engine:PatternCalibration.record_outcome
[SUPERSET] learning_proof_engine.CheckpointConfig.get_priority → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] learning_proof_engine.CheckpointConfig.is_blocking
[SUPERSET] learning_proof_engine.CheckpointConfig.should_auto_dismiss → learning_proof_engine:CheckpointConfig.get_priority
[LEAF] learning_proof_engine.GlobalRegretTracker.get_or_create_tracker
[WRAPPER] learning_proof_engine.GlobalRegretTracker.has_proven_rollback
[ENTRY] learning_proof_engine.GlobalRegretTracker.record_regret → learning_proof_engine:GlobalRegretTracker.get_or_create_tracker, learning_proof_engine:PolicyRegretTracker.add_regret, learning_proof_engine:PreventionTimeline.add_regret
[LEAF] learning_proof_engine.GlobalRegretTracker.system_regret_rate
[LEAF] learning_proof_engine.M25GraduationStatus._get_next_action
[WRAPPER] learning_proof_engine.M25GraduationStatus.gate1_passed
[WRAPPER] learning_proof_engine.M25GraduationStatus.gate2_passed
[WRAPPER] learning_proof_engine.M25GraduationStatus.gate3_passed
[WRAPPER] learning_proof_engine.M25GraduationStatus.is_graduated
[LEAF] learning_proof_engine.M25GraduationStatus.status_label
[WRAPPER] learning_proof_engine.M25GraduationStatus.to_dashboard → learning_proof_engine:M25GraduationStatus._get_next_action
[LEAF] learning_proof_engine.PatternCalibration._recalibrate
[LEAF] learning_proof_engine.PatternCalibration.accuracy
[LEAF] learning_proof_engine.PatternCalibration.get_calibrated_band
[WRAPPER] learning_proof_engine.PatternCalibration.is_calibrated
[SUPERSET] learning_proof_engine.PatternCalibration.record_outcome → learning_proof_engine:PatternCalibration._recalibrate
[WRAPPER] learning_proof_engine.PolicyRegretTracker._trigger_demotion
[CANONICAL] learning_proof_engine.PolicyRegretTracker.add_regret → learning_proof_engine:PolicyRegretTracker._trigger_demotion
[WRAPPER] learning_proof_engine.PolicyRegretTracker.decay_regret
[WRAPPER] learning_proof_engine.PolicyRegretTracker.is_demoted
[LEAF] learning_proof_engine.PolicyRegretTracker.to_rollback_timeline
[LEAF] learning_proof_engine.PreventionRecord.create_prevention
[WRAPPER] learning_proof_engine.PreventionRecord.to_console_timeline
[LEAF] learning_proof_engine.PreventionTimeline._generate_narrative
[ENTRY] learning_proof_engine.PreventionTimeline.add_incident_created → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] learning_proof_engine.PreventionTimeline.add_policy_born
[WRAPPER] learning_proof_engine.PreventionTimeline.add_prevention
[WRAPPER] learning_proof_engine.PreventionTimeline.add_regret
[WRAPPER] learning_proof_engine.PreventionTimeline.add_rollback
[ENTRY] learning_proof_engine.PreventionTimeline.to_console → learning_proof_engine:PreventionTimeline._generate_narrative
[LEAF] learning_proof_engine.PreventionTracker.get_top_preventing_patterns
[WRAPPER] learning_proof_engine.PreventionTracker.has_proven_prevention
[LEAF] learning_proof_engine.PreventionTracker.prevention_rate
[WRAPPER] learning_proof_engine.PreventionTracker.record_failure
[WRAPPER] learning_proof_engine.PreventionTracker.record_prevention
[LEAF] learning_proof_engine.PrioritizedCheckpoint.check_auto_dismiss
[INTERNAL] learning_proof_engine.PrioritizedCheckpoint.create → learning_proof_engine:CheckpointConfig.get_priority, learning_proof_engine:CheckpointConfig.is_blocking
[WRAPPER] lessons_engine.LessonsLearnedEngine.__init__ → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] lessons_engine.LessonsLearnedEngine._create_lesson → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver
[WRAPPER] lessons_engine.LessonsLearnedEngine._generate_failure_description
[LEAF] lessons_engine.LessonsLearnedEngine._generate_failure_proposed_action
[LEAF] lessons_engine.LessonsLearnedEngine._get_driver
[INTERNAL] lessons_engine.LessonsLearnedEngine._is_debounced → lessons_engine:LessonsLearnedEngine._get_driver
[SUPERSET] lessons_engine.LessonsLearnedEngine.convert_lesson_to_draft → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition
[SUPERSET] lessons_engine.LessonsLearnedEngine.defer_lesson → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition
[INTERNAL] lessons_engine.LessonsLearnedEngine.detect_lesson_from_critical_success → lessons_engine:LessonsLearnedEngine._create_lesson
[ENTRY] lessons_engine.LessonsLearnedEngine.detect_lesson_from_failure → lessons_engine:LessonsLearnedEngine._create_lesson, lessons_engine:LessonsLearnedEngine._generate_failure_description, lessons_engine:LessonsLearnedEngine._generate_failure_proposed_action
[CANONICAL] lessons_engine.LessonsLearnedEngine.detect_lesson_from_near_threshold → lessons_engine:LessonsLearnedEngine._create_lesson, lessons_engine:LessonsLearnedEngine._is_debounced, lessons_engine:get_threshold_band
[SUPERSET] lessons_engine.LessonsLearnedEngine.dismiss_lesson → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition
[ENTRY] lessons_engine.LessonsLearnedEngine.emit_critical_success → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine.detect_lesson_from_critical_success
[ENTRY] lessons_engine.LessonsLearnedEngine.emit_near_threshold → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine.detect_lesson_from_near_threshold
[INTERNAL] lessons_engine.LessonsLearnedEngine.get_expired_deferred_lessons → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver
[INTERNAL] lessons_engine.LessonsLearnedEngine.get_lesson → lessons_engine:LessonsLearnedEngine._get_driver
[SUPERSET] lessons_engine.LessonsLearnedEngine.get_lesson_stats → lessons_engine:LessonsLearnedEngine._get_driver
[WRAPPER] lessons_engine.LessonsLearnedEngine.list_lessons → lessons_engine:LessonsLearnedEngine._get_driver
[SUPERSET] lessons_engine.LessonsLearnedEngine.reactivate_deferred_lesson → dsl_parser:Parser.error, lessons_engine:LessonsLearnedEngine._get_driver, lessons_engine:LessonsLearnedEngine.get_lesson, lessons_engine:is_valid_transition
[SUPERSET] lessons_engine.LessonsLearnedEngine.reactivate_expired_deferred_lessons → lessons_engine:LessonsLearnedEngine.get_expired_deferred_lessons, lessons_engine:LessonsLearnedEngine.reactivate_deferred_lesson
[LEAF] lessons_engine.get_lessons_learned_engine
[LEAF] lessons_engine.get_threshold_band
[WRAPPER] lessons_engine.is_valid_transition → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] limits.Limits.is_unlimited
[WRAPPER] limits.derive_limits → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] limits_facade.LimitCheckResult.to_dict
[WRAPPER] limits_facade.LimitConfig.to_dict
[WRAPPER] limits_facade.LimitsFacade.__init__
[LEAF] limits_facade.LimitsFacade._get_or_create_limit
[SUPERSET] limits_facade.LimitsFacade.check_limit → limits_facade:LimitsFacade._get_or_create_limit
[LEAF] limits_facade.LimitsFacade.get_limit
[SUPERSET] limits_facade.LimitsFacade.get_usage → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+39
[SUPERSET] limits_facade.LimitsFacade.list_limits → limits_facade:LimitsFacade._get_or_create_limit
[ENTRY] limits_facade.LimitsFacade.reset_limit → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] limits_facade.LimitsFacade.update_limit → policy_limits_engine:PolicyLimitsService.update, policy_rules_engine:PolicyRulesService.update
[WRAPPER] limits_facade.UsageSummary.to_dict
[LEAF] limits_facade.get_limits_facade
[WRAPPER] limits_simulation_service.get_limits_simulation_service
[LEAF] llm_policy_engine.LLMRateLimiter.__init__
[LEAF] llm_policy_engine.LLMRateLimiter.check_and_record
[WRAPPER] llm_policy_engine.LLMRateLimiter.get_instance
[LEAF] llm_policy_engine.LLMRateLimiter.requests_remaining
[CANONICAL] llm_policy_engine.check_safety_limits → llm_policy_engine:LLMRateLimiter.check_and_record, llm_policy_engine:LLMRateLimiter.get_instance, llm_policy_engine:LLMRateLimiter.requests_remaining, llm_policy_engine:estimate_cost_cents
[INTERNAL] llm_policy_engine.estimate_cost_cents → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] llm_policy_engine.estimate_tokens
[LEAF] llm_policy_engine.get_effective_model
[SUPERSET] llm_policy_engine.get_model_for_task → llm_policy_engine:is_expensive_model, llm_policy_engine:is_model_allowed, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] llm_policy_engine.is_expensive_model
[LEAF] llm_policy_engine.is_model_allowed
[WRAPPER] nodes.ASTNode.accept
[WRAPPER] nodes.ASTNode.location
[WRAPPER] nodes.ASTVisitor.visit_action_block
[WRAPPER] nodes.ASTVisitor.visit_attr_access
[WRAPPER] nodes.ASTVisitor.visit_binary_op
[WRAPPER] nodes.ASTVisitor.visit_condition_block
[WRAPPER] nodes.ASTVisitor.visit_func_call
[WRAPPER] nodes.ASTVisitor.visit_ident
[WRAPPER] nodes.ASTVisitor.visit_import
[WRAPPER] nodes.ASTVisitor.visit_literal
[WRAPPER] nodes.ASTVisitor.visit_policy_decl
[WRAPPER] nodes.ASTVisitor.visit_priority
[WRAPPER] nodes.ASTVisitor.visit_program
[WRAPPER] nodes.ASTVisitor.visit_route_target
[WRAPPER] nodes.ASTVisitor.visit_rule_decl
[WRAPPER] nodes.ASTVisitor.visit_rule_ref
[WRAPPER] nodes.ASTVisitor.visit_unary_op
[WRAPPER] nodes.ActionBlockNode.accept → ir_builder:IRBuilder.visit_action_block, nodes:ASTVisitor.visit_action_block, visitors:BaseVisitor.visit_action_block, visitors:PrintVisitor.visit_action_block
[WRAPPER] nodes.AttrAccessNode.accept → ir_builder:IRBuilder.visit_attr_access, nodes:ASTVisitor.visit_attr_access, visitors:BaseVisitor.visit_attr_access, visitors:PrintVisitor.visit_attr_access
[WRAPPER] nodes.BinaryOpNode.accept → ir_builder:IRBuilder.visit_binary_op, nodes:ASTVisitor.visit_binary_op, visitors:BaseVisitor.visit_binary_op, visitors:PrintVisitor.visit_binary_op
[WRAPPER] nodes.ConditionBlockNode.accept → ir_builder:IRBuilder.visit_condition_block, nodes:ASTVisitor.visit_condition_block, visitors:BaseVisitor.visit_condition_block, visitors:PrintVisitor.visit_condition_block, visitors:RuleExtractor.visit_condition_block
[WRAPPER] nodes.FuncCallNode.accept → ir_builder:IRBuilder.visit_func_call, nodes:ASTVisitor.visit_func_call, visitors:BaseVisitor.visit_func_call, visitors:PrintVisitor.visit_func_call
[LEAF] nodes.GovernanceMetadata.merge_with
[WRAPPER] nodes.IdentNode.accept → ir_builder:IRBuilder.visit_ident, nodes:ASTVisitor.visit_ident, visitors:BaseVisitor.visit_ident, visitors:PrintVisitor.visit_ident
[WRAPPER] nodes.ImportNode.accept → ir_builder:IRBuilder.visit_import, nodes:ASTVisitor.visit_import, visitors:BaseVisitor.visit_import, visitors:PrintVisitor.visit_import
[WRAPPER] nodes.LiteralNode.accept → ir_builder:IRBuilder.visit_literal, nodes:ASTVisitor.visit_literal, visitors:BaseVisitor.visit_literal, visitors:PrintVisitor.visit_literal
[WRAPPER] nodes.PolicyDeclNode.__post_init__ → grammar:PLangGrammar.get_category_priority
[WRAPPER] nodes.PolicyDeclNode.accept → ir_builder:IRBuilder.visit_policy_decl, nodes:ASTVisitor.visit_policy_decl, visitors:BaseVisitor.visit_policy_decl, visitors:CategoryCollector.visit_policy_decl, visitors:PrintVisitor.visit_policy_decl, ...+1
[WRAPPER] nodes.PriorityNode.accept → ir_builder:IRBuilder.visit_priority, nodes:ASTVisitor.visit_priority, visitors:BaseVisitor.visit_priority, visitors:PrintVisitor.visit_priority
[WRAPPER] nodes.ProgramNode.accept → ir_builder:IRBuilder.visit_program, nodes:ASTVisitor.visit_program, visitors:BaseVisitor.visit_program, visitors:PrintVisitor.visit_program
[WRAPPER] nodes.RouteTargetNode.accept → ir_builder:IRBuilder.visit_route_target, nodes:ASTVisitor.visit_route_target, visitors:BaseVisitor.visit_route_target, visitors:PrintVisitor.visit_route_target
[WRAPPER] nodes.RuleDeclNode.__post_init__ → grammar:PLangGrammar.get_category_priority
[WRAPPER] nodes.RuleDeclNode.accept → ir_builder:IRBuilder.visit_rule_decl, nodes:ASTVisitor.visit_rule_decl, visitors:BaseVisitor.visit_rule_decl, visitors:CategoryCollector.visit_rule_decl, visitors:PrintVisitor.visit_rule_decl, ...+1
[WRAPPER] nodes.RuleRefNode.accept → ir_builder:IRBuilder.visit_rule_ref, nodes:ASTVisitor.visit_rule_ref, visitors:BaseVisitor.visit_rule_ref, visitors:PrintVisitor.visit_rule_ref
[WRAPPER] nodes.UnaryOpNode.accept → ir_builder:IRBuilder.visit_unary_op, nodes:ASTVisitor.visit_unary_op, visitors:BaseVisitor.visit_unary_op, visitors:PrintVisitor.visit_unary_op
[WRAPPER] optimizer_conflict_resolver.ConflictResolver.__init__
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._detect_action_conflicts → optimizer_conflict_resolver:ConflictResolver._get_condition_signature, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:PolicySnapshotRegistry.list
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._detect_category_conflicts → optimizer_conflict_resolver:ConflictResolver._might_override, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._detect_circular_dependencies → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] optimizer_conflict_resolver.ConflictResolver._detect_priority_conflicts
[LEAF] optimizer_conflict_resolver.ConflictResolver._get_actions
[LEAF] optimizer_conflict_resolver.ConflictResolver._get_condition_signature
[INTERNAL] optimizer_conflict_resolver.ConflictResolver._might_override → optimizer_conflict_resolver:ConflictResolver._get_actions
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._resolve_action_conflict → grammar:PLangGrammar.get_action_precedence, optimizer_conflict_resolver:ConflictResolver._get_actions, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._resolve_category_conflict → grammar:PLangGrammar.get_category_priority, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._resolve_circular_conflict → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] optimizer_conflict_resolver.ConflictResolver._resolve_conflict → arbitrator:PolicyArbitrator._resolve_action_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_action_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_category_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_circular_conflict, optimizer_conflict_resolver:ConflictResolver._resolve_priority_conflict
[INTERNAL] optimizer_conflict_resolver.ConflictResolver._resolve_priority_conflict → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[ENTRY] optimizer_conflict_resolver.ConflictResolver.resolve → optimizer_conflict_resolver:ConflictResolver._detect_action_conflicts, optimizer_conflict_resolver:ConflictResolver._detect_category_conflicts, optimizer_conflict_resolver:ConflictResolver._detect_circular_dependencies, optimizer_conflict_resolver:ConflictResolver._detect_priority_conflicts, optimizer_conflict_resolver:ConflictResolver._resolve_conflict
[WRAPPER] optimizer_conflict_resolver.PolicyConflict.__str__
[WRAPPER] phase_status_invariants.InvariantCheckResponse.to_dict → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] phase_status_invariants.PhaseStatusInvariantChecker.__init__
[CANONICAL] phase_status_invariants.PhaseStatusInvariantChecker.check → phase_status_invariants:PhaseStatusInvariantChecker.get_allowed_statuses
[WRAPPER] phase_status_invariants.PhaseStatusInvariantChecker.enforcement_enabled
[INTERNAL] phase_status_invariants.PhaseStatusInvariantChecker.ensure_valid → authority_checker:OverrideAuthorityChecker.check, phase_status_invariants:PhaseStatusInvariantChecker.check
[WRAPPER] phase_status_invariants.PhaseStatusInvariantChecker.from_governance_config
[INTERNAL] phase_status_invariants.PhaseStatusInvariantChecker.get_allowed_statuses → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[ENTRY] phase_status_invariants.PhaseStatusInvariantChecker.is_valid_combination → phase_status_invariants:PhaseStatusInvariantChecker.get_allowed_statuses
[SUPERSET] phase_status_invariants.PhaseStatusInvariantChecker.should_allow_transition → authority_checker:OverrideAuthorityChecker.check, phase_status_invariants:PhaseStatusInvariantChecker.check
[INTERNAL] phase_status_invariants.PhaseStatusInvariantEnforcementError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] phase_status_invariants.PhaseStatusInvariantEnforcementError.to_dict → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] phase_status_invariants.check_phase_status_invariant → authority_checker:OverrideAuthorityChecker.check, phase_status_invariants:PhaseStatusInvariantChecker.check
[WRAPPER] phase_status_invariants.ensure_phase_status_invariant → phase_status_invariants:PhaseStatusInvariantChecker.ensure_valid
[LEAF] plan.Plan.__post_init__
[LEAF] plan.PlanTier.from_string
[WRAPPER] plan_generation_engine.PlanGenerationEngine.__init__
[CANONICAL] plan_generation_engine.PlanGenerationEngine.generate → dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[ENTRY] plan_generation_engine.generate_plan_for_run → eligibility_engine:DefaultSystemHealthLookup.get_status, eligibility_engine:SystemHealthLookup.get_status, plan_generation_engine:PlanGenerationEngine.generate
[WRAPPER] policies_limits_query_engine.LimitsQueryEngine.__init__
[LEAF] policies_limits_query_engine.LimitsQueryEngine.get_limit_detail
[LEAF] policies_limits_query_engine.LimitsQueryEngine.list_budgets
[LEAF] policies_limits_query_engine.LimitsQueryEngine.list_limits
[WRAPPER] policies_limits_query_engine.get_limits_query_engine
[WRAPPER] policies_proposals_query_engine.ProposalsQueryEngine.__init__
[WRAPPER] policies_proposals_query_engine.ProposalsQueryEngine.count_drafts → proposals_read_driver:ProposalsReadDriver.count_draft_proposals
[ENTRY] policies_proposals_query_engine.ProposalsQueryEngine.get_policy_request_detail → policy_proposal_read_driver:PolicyProposalReadDriver.fetch_proposal_by_id, proposals_read_driver:ProposalsReadDriver.fetch_proposal_by_id
[CANONICAL] policies_proposals_query_engine.ProposalsQueryEngine.list_policy_requests → policy_proposal_read_driver:PolicyProposalReadDriver.fetch_proposals, proposals_read_driver:ProposalsReadDriver.fetch_proposals
[WRAPPER] policies_proposals_query_engine.get_proposals_query_engine → proposals_read_driver:get_proposals_read_driver
[WRAPPER] policies_rules_query_engine.PolicyRulesQueryEngine.__init__
[WRAPPER] policies_rules_query_engine.PolicyRulesQueryEngine.count_rules → policy_rules_read_driver:PolicyRulesReadDriver.count_policy_rules
[ENTRY] policies_rules_query_engine.PolicyRulesQueryEngine.get_policy_rule_detail → policy_rules_read_driver:PolicyRulesReadDriver.fetch_policy_rule_by_id
[CANONICAL] policies_rules_query_engine.PolicyRulesQueryEngine.list_policy_rules → policy_rules_read_driver:PolicyRulesReadDriver.fetch_policy_rules
[WRAPPER] policies_rules_query_engine.get_policy_rules_query_engine → policy_rules_read_driver:get_policy_rules_read_driver
[WRAPPER] policy_command._record_approval_action
[WRAPPER] policy_command._record_approval_escalation
[WRAPPER] policy_command._record_approval_request_created
[WRAPPER] policy_command._record_budget_rejection
[WRAPPER] policy_command._record_capability_violation
[WRAPPER] policy_command._record_policy_decision
[WRAPPER] policy_command._record_webhook_fallback
[INTERNAL] policy_command.check_policy_violations → policy_command:_record_budget_rejection, policy_command:_record_capability_violation
[CANONICAL] policy_command.evaluate_policy → policy_command:_record_policy_decision, policy_command:check_policy_violations, policy_command:simulate_cost
[WRAPPER] policy_command.record_approval_created → policy_command:_record_approval_request_created
[WRAPPER] policy_command.record_approval_outcome → policy_command:_record_approval_action
[WRAPPER] policy_command.record_escalation → policy_command:_record_approval_escalation
[WRAPPER] policy_command.record_webhook_used → policy_command:_record_webhook_fallback
[LEAF] policy_command.simulate_cost
[LEAF] policy_conflict_resolver.create_conflict_log
[WRAPPER] policy_conflict_resolver.get_action_severity → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] policy_conflict_resolver.is_more_restrictive → policy_conflict_resolver:get_action_severity
[CANONICAL] policy_conflict_resolver.resolve_policy_conflict → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] policy_driver.PolicyDriver.__init__
[LEAF] policy_driver.PolicyDriver._engine
[WRAPPER] policy_driver.PolicyDriver.acknowledge_violation → engine:PolicyEngine.acknowledge_violation
[WRAPPER] policy_driver.PolicyDriver.activate_policy_version → engine:PolicyEngine.activate_policy_version
[WRAPPER] policy_driver.PolicyDriver.add_dependency_with_dag_check → engine:PolicyEngine.add_dependency_with_dag_check
[WRAPPER] policy_driver.PolicyDriver.clear_cooldowns → engine:PolicyEngine.clear_cooldowns
[WRAPPER] policy_driver.PolicyDriver.create_policy_version → engine:PolicyEngine.create_policy_version
[WRAPPER] policy_driver.PolicyDriver.create_temporal_policy → engine:PolicyEngine.create_temporal_policy
[INTERNAL] policy_driver.PolicyDriver.evaluate → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, interpreter:evaluate, prevention_hook:PreventionHook.evaluate, ...+1
[WRAPPER] policy_driver.PolicyDriver.evaluate_with_context → engine:PolicyEngine.evaluate_with_context
[WRAPPER] policy_driver.PolicyDriver.get_active_cooldowns → engine:PolicyEngine.get_active_cooldowns
[WRAPPER] policy_driver.PolicyDriver.get_current_version → engine:PolicyEngine.get_current_version
[WRAPPER] policy_driver.PolicyDriver.get_dependency_graph → engine:PolicyEngine.get_dependency_graph
[WRAPPER] policy_driver.PolicyDriver.get_ethical_constraints → engine:PolicyEngine.get_ethical_constraints
[WRAPPER] policy_driver.PolicyDriver.get_metrics → engine:PolicyEngine.get_metrics
[WRAPPER] policy_driver.PolicyDriver.get_policy_conflicts → engine:PolicyEngine.get_policy_conflicts
[WRAPPER] policy_driver.PolicyDriver.get_policy_versions → engine:PolicyEngine.get_policy_versions
[WRAPPER] policy_driver.PolicyDriver.get_risk_ceiling → engine:PolicyEngine.get_risk_ceiling
[WRAPPER] policy_driver.PolicyDriver.get_risk_ceilings → engine:PolicyEngine.get_risk_ceilings
[WRAPPER] policy_driver.PolicyDriver.get_safety_rules → engine:PolicyEngine.get_safety_rules
[WRAPPER] policy_driver.PolicyDriver.get_state → engine:PolicyEngine.get_state
[WRAPPER] policy_driver.PolicyDriver.get_temporal_policies → engine:PolicyEngine.get_temporal_policies
[WRAPPER] policy_driver.PolicyDriver.get_temporal_storage_stats → engine:PolicyEngine.get_temporal_storage_stats
[WRAPPER] policy_driver.PolicyDriver.get_temporal_utilization → engine:PolicyEngine.get_temporal_utilization
[WRAPPER] policy_driver.PolicyDriver.get_topological_evaluation_order → engine:PolicyEngine.get_topological_evaluation_order
[WRAPPER] policy_driver.PolicyDriver.get_version_provenance → engine:PolicyEngine.get_version_provenance
[WRAPPER] policy_driver.PolicyDriver.get_violation → engine:PolicyEngine.get_violation
[WRAPPER] policy_driver.PolicyDriver.get_violations → engine:PolicyEngine.get_violations
[WRAPPER] policy_driver.PolicyDriver.pre_check → engine:PolicyEngine.pre_check
[WRAPPER] policy_driver.PolicyDriver.prune_temporal_metrics → engine:PolicyEngine.prune_temporal_metrics
[WRAPPER] policy_driver.PolicyDriver.reload_policies → engine:PolicyEngine.reload_policies
[WRAPPER] policy_driver.PolicyDriver.reset_risk_ceiling → engine:PolicyEngine.reset_risk_ceiling, policy_engine_driver:PolicyEngineDriver.reset_risk_ceiling
[WRAPPER] policy_driver.PolicyDriver.resolve_conflict → engine:PolicyEngine.resolve_conflict, governance_facade:GovernanceFacade.resolve_conflict, policy_engine_driver:PolicyEngineDriver.resolve_conflict
[WRAPPER] policy_driver.PolicyDriver.rollback_to_version → engine:PolicyEngine.rollback_to_version
[WRAPPER] policy_driver.PolicyDriver.update_risk_ceiling → engine:PolicyEngine.update_risk_ceiling, policy_engine_driver:PolicyEngineDriver.update_risk_ceiling
[WRAPPER] policy_driver.PolicyDriver.update_safety_rule → engine:PolicyEngine.update_safety_rule, policy_engine_driver:PolicyEngineDriver.update_safety_rule
[WRAPPER] policy_driver.PolicyDriver.validate_dependency_dag → engine:PolicyEngine.validate_dependency_dag
[LEAF] policy_driver.get_policy_driver
[WRAPPER] policy_driver.reset_policy_driver
[WRAPPER] policy_engine_driver.PolicyEngineDriver.__init__
[LEAF] policy_engine_driver.PolicyEngineDriver._get_engine
[WRAPPER] policy_engine_driver.PolicyEngineDriver.activate_version → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.cap_temporal_events → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.compact_temporal_events → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.deactivate_all_versions → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.delete_old_temporal_events → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.fetch_active_policies_for_integrity → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_business_rules → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] policy_engine_driver.PolicyEngineDriver.fetch_conflicts → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_current_active_version → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_dependencies → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_dependency_edges → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.fetch_dependency_edges_with_type → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_ethical_constraints → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_ethical_constraints_for_integrity → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[ENTRY] policy_engine_driver.PolicyEngineDriver.fetch_policy_version_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_policy_version_by_id_or_version → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_policy_versions → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_provenance → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_risk_ceilings → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_safety_rules → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_temporal_metric_sum → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] policy_engine_driver.PolicyEngineDriver.fetch_temporal_policies → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_temporal_policies_for_integrity → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_temporal_policy_for_utilization → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_temporal_stats → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_temporal_storage_stats → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[ENTRY] policy_engine_driver.PolicyEngineDriver.fetch_unresolved_conflicts → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_version_for_rollback → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.fetch_violation_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[CANONICAL] policy_engine_driver.PolicyEngineDriver.fetch_violations → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.insert_dependency → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.insert_evaluation → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.insert_policy_version → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.insert_provenance → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.insert_temporal_policy → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.insert_violation → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.mark_version_rolled_back → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.reset_risk_ceiling → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.resolve_conflict → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_engine_driver.PolicyEngineDriver.update_risk_ceiling → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] policy_engine_driver.PolicyEngineDriver.update_safety_rule → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.PolicyEngineDriver.update_violation_acknowledged → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_engine_driver.get_policy_engine_driver
[WRAPPER] policy_graph_driver.PolicyGraphDriver.__init__
[INTERNAL] policy_graph_driver.PolicyGraphDriver.fetch_active_limits → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_graph_driver.PolicyGraphDriver.fetch_active_policies → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_graph_driver.PolicyGraphDriver.fetch_all_limits → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_graph_driver.PolicyGraphDriver.fetch_all_policies → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_graph_driver.PolicyGraphDriver.fetch_resolved_conflicts → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_graph_driver.get_policy_graph_driver
[INTERNAL] policy_graph_engine.ConflictDetectionResult.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[INTERNAL] policy_graph_engine.DependencyGraphResult.to_dict → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+37
[WRAPPER] policy_graph_engine.PolicyConflict.to_dict
[WRAPPER] policy_graph_engine.PolicyConflictEngine.__init__
[SUPERSET] policy_graph_engine.PolicyConflictEngine._detect_priority_overrides → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] policy_graph_engine.PolicyConflictEngine._detect_scope_overlaps → policy_graph_engine:PolicyConflictEngine._has_contradicting_conditions, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] policy_graph_engine.PolicyConflictEngine._detect_temporal_conflicts → policy_graph_engine:PolicyConflictEngine._time_windows_overlap, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] policy_graph_engine.PolicyConflictEngine._detect_threshold_contradictions → policy_graph_driver:PolicyGraphDriver.fetch_active_limits
[LEAF] policy_graph_engine.PolicyConflictEngine._has_contradicting_conditions
[WRAPPER] policy_graph_engine.PolicyConflictEngine._involves_policy → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] policy_graph_engine.PolicyConflictEngine._time_windows_overlap → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] policy_graph_engine.PolicyConflictEngine.detect_conflicts → policy_graph_driver:PolicyGraphDriver.fetch_active_policies, policy_graph_driver:PolicyGraphDriver.fetch_resolved_conflicts, policy_graph_engine:PolicyConflictEngine._detect_priority_overrides, policy_graph_engine:PolicyConflictEngine._detect_scope_overlaps, policy_graph_engine:PolicyConflictEngine._detect_temporal_conflicts, ...+2
[WRAPPER] policy_graph_engine.PolicyDependency.to_dict
[WRAPPER] policy_graph_engine.PolicyDependencyEngine.__init__
[SUPERSET] policy_graph_engine.PolicyDependencyEngine._detect_explicit_dependencies → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] policy_graph_engine.PolicyDependencyEngine._detect_implicit_limit_dependencies
[LEAF] policy_graph_engine.PolicyDependencyEngine._detect_implicit_scope_dependencies
[SUPERSET] policy_graph_engine.PolicyDependencyEngine.check_can_activate → policy_graph_engine:PolicyDependencyEngine.compute_dependency_graph
[INTERNAL] policy_graph_engine.PolicyDependencyEngine.check_can_delete → policy_graph_engine:PolicyDependencyEngine.compute_dependency_graph, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] policy_graph_engine.PolicyDependencyEngine.compute_dependency_graph → policy_graph_driver:PolicyGraphDriver.fetch_all_limits, policy_graph_driver:PolicyGraphDriver.fetch_all_policies, policy_graph_engine:PolicyDependencyEngine._detect_explicit_dependencies, policy_graph_engine:PolicyDependencyEngine._detect_implicit_limit_dependencies, policy_graph_engine:PolicyDependencyEngine._detect_implicit_scope_dependencies
[WRAPPER] policy_graph_engine.PolicyNode.to_dict
[WRAPPER] policy_graph_engine.get_conflict_engine
[WRAPPER] policy_graph_engine.get_dependency_engine
[WRAPPER] policy_limits_engine.PolicyLimitsService.__init__
[LEAF] policy_limits_engine.PolicyLimitsService._get_limit
[WRAPPER] policy_limits_engine.PolicyLimitsService._to_response
[LEAF] policy_limits_engine.PolicyLimitsService._validate_category_fields
[INTERNAL] policy_limits_engine.PolicyLimitsService.create → policy_limits_engine:PolicyLimitsService._to_response, policy_limits_engine:PolicyLimitsService._validate_category_fields, policy_rules_driver:PolicyRulesDriver.add_integrity, policy_rules_engine:PolicyRulesService._to_response
[ENTRY] policy_limits_engine.PolicyLimitsService.delete → policy_limits_engine:PolicyLimitsService._get_limit, policy_rules_driver:PolicyRulesDriver.flush
[WRAPPER] policy_limits_engine.PolicyLimitsService.get → policy_limits_engine:PolicyLimitsService._get_limit, policy_limits_engine:PolicyLimitsService._to_response, policy_rules_engine:PolicyRulesService._to_response
[CANONICAL] policy_limits_engine.PolicyLimitsService.update → policy_limits_engine:PolicyLimitsService._get_limit, policy_limits_engine:PolicyLimitsService._to_response, policy_rules_engine:PolicyRulesService._to_response
[WRAPPER] policy_mapper.MCPPolicyDecision.allow
[WRAPPER] policy_mapper.MCPPolicyDecision.deny
[WRAPPER] policy_mapper.MCPPolicyDecision.to_dict
[WRAPPER] policy_mapper.MCPPolicyMapper.__init__
[WRAPPER] policy_mapper.MCPPolicyMapper._check_explicit_allow
[WRAPPER] policy_mapper.MCPPolicyMapper._check_rate_limit
[SUPERSET] policy_mapper.MCPPolicyMapper._evaluate_policy → policy_mapper:MCPPolicyMapper._get_policy_engine
[INTERNAL] policy_mapper.MCPPolicyMapper._get_policy_engine → engine:get_policy_engine
[CANONICAL] policy_mapper.MCPPolicyMapper.check_tool_invocation → policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_mapper:MCPPolicyDecision.deny, policy_mapper:MCPPolicyMapper._check_explicit_allow, policy_mapper:MCPPolicyMapper._check_rate_limit, ...+3
[LEAF] policy_mapper.MCPPolicyMapper.register_tool_policy
[LEAF] policy_mapper.configure_mcp_policy_mapper
[LEAF] policy_mapper.get_mcp_policy_mapper
[WRAPPER] policy_mapper.reset_mcp_policy_mapper
[WRAPPER] policy_proposal_engine.PolicyActivationBlockedError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] policy_proposal_engine.PolicyDeletionBlockedError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] policy_proposal_engine.PolicyProposalEngine.__init__
[INTERNAL] policy_proposal_engine.PolicyProposalEngine._create_policy_rule_from_proposal → policy_limits_engine:PolicyLimitsService.get, policy_proposal_read_driver:PolicyProposalReadDriver.check_rule_exists, policy_proposal_write_driver:PolicyProposalWriteDriver.create_policy_rule, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] policy_proposal_engine.PolicyProposalEngine.check_proposal_eligibility → policy_limits_engine:PolicyLimitsService.get, policy_proposal_read_driver:PolicyProposalReadDriver.fetch_unacknowledged_feedback, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] policy_proposal_engine.PolicyProposalEngine.create_proposal → policy_proposal_write_driver:PolicyProposalWriteDriver.create_proposal
[SUPERSET] policy_proposal_engine.PolicyProposalEngine.delete_policy_rule → policy_graph_engine:PolicyDependencyEngine.check_can_delete, policy_graph_engine:get_dependency_engine, policy_proposal_engine:delete_policy_rule, policy_proposal_read_driver:PolicyProposalReadDriver.fetch_rule_by_id, policy_proposal_write_driver:PolicyProposalWriteDriver.delete_policy_rule, ...+1
[INTERNAL] policy_proposal_engine.PolicyProposalEngine.get_proposal_summary → policy_limits_engine:PolicyLimitsService.get, policy_proposal_read_driver:PolicyProposalReadDriver.fetch_proposals, policy_rules_engine:PolicyRulesService.get, proposals_read_driver:ProposalsReadDriver.fetch_proposals, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] policy_proposal_engine.PolicyProposalEngine.review_proposal → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+46
[WRAPPER] policy_proposal_engine.check_proposal_eligibility → policy_proposal_engine:PolicyProposalEngine.check_proposal_eligibility, policy_proposal_engine:get_policy_proposal_engine
[WRAPPER] policy_proposal_engine.create_policy_proposal → policy_proposal_engine:PolicyProposalEngine.create_proposal, policy_proposal_engine:get_policy_proposal_engine, policy_proposal_write_driver:PolicyProposalWriteDriver.create_proposal
[WRAPPER] policy_proposal_engine.delete_policy_rule → policy_proposal_engine:PolicyProposalEngine.delete_policy_rule, policy_proposal_engine:get_policy_proposal_engine, policy_proposal_write_driver:PolicyProposalWriteDriver.delete_policy_rule
[LEAF] policy_proposal_engine.generate_default_rule
[INTERNAL] policy_proposal_engine.get_policy_proposal_engine → policy_proposal_read_driver:get_policy_proposal_read_driver, policy_proposal_write_driver:get_policy_proposal_write_driver
[WRAPPER] policy_proposal_engine.get_proposal_summary → policy_proposal_engine:PolicyProposalEngine.get_proposal_summary, policy_proposal_engine:get_policy_proposal_engine
[WRAPPER] policy_proposal_engine.review_policy_proposal → policy_proposal_engine:PolicyProposalEngine.review_proposal, policy_proposal_engine:get_policy_proposal_engine
[WRAPPER] policy_proposal_read_driver.PolicyProposalReadDriver.__init__
[INTERNAL] policy_proposal_read_driver.PolicyProposalReadDriver.check_rule_exists → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_proposal_read_driver.PolicyProposalReadDriver.count_versions_for_proposal → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_proposal_read_driver.PolicyProposalReadDriver.fetch_proposal_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[ENTRY] policy_proposal_read_driver.PolicyProposalReadDriver.fetch_proposal_status → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[CANONICAL] policy_proposal_read_driver.PolicyProposalReadDriver.fetch_proposals → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_proposal_read_driver.PolicyProposalReadDriver.fetch_rule_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] policy_proposal_read_driver.PolicyProposalReadDriver.fetch_unacknowledged_feedback → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_proposal_read_driver.get_policy_proposal_read_driver
[WRAPPER] policy_proposal_write_driver.PolicyProposalWriteDriver.__init__
[INTERNAL] policy_proposal_write_driver.PolicyProposalWriteDriver.create_policy_rule → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_proposal_write_driver.PolicyProposalWriteDriver.create_proposal → policy_rules_driver:PolicyRulesDriver.flush
[INTERNAL] policy_proposal_write_driver.PolicyProposalWriteDriver.create_version → policy_rules_driver:PolicyRulesDriver.flush
[WRAPPER] policy_proposal_write_driver.PolicyProposalWriteDriver.delete_policy_rule → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_proposal_write_driver.PolicyProposalWriteDriver.update_proposal_status → deterministic_engine:DeterministicEngine.execute, policy_limits_engine:PolicyLimitsService.update, policy_rules_engine:PolicyRulesService.update, sandbox_engine:SandboxService.execute
[WRAPPER] policy_proposal_write_driver.get_policy_proposal_write_driver
[WRAPPER] policy_read_driver.PolicyReadDriver.__init__
[WRAPPER] policy_read_driver.PolicyReadDriver._to_guardrail_dto
[INTERNAL] policy_read_driver.PolicyReadDriver.get_guardrail_by_id → policy_read_driver:PolicyReadDriver._to_guardrail_dto
[LEAF] policy_read_driver.PolicyReadDriver.get_tenant_budget_settings
[LEAF] policy_read_driver.PolicyReadDriver.get_usage_sum_since
[INTERNAL] policy_read_driver.PolicyReadDriver.list_all_guardrails → policy_read_driver:PolicyReadDriver._to_guardrail_dto, snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] policy_read_driver.get_policy_read_driver
[WRAPPER] policy_rules_driver.PolicyRulesDriver.__init__
[WRAPPER] policy_rules_driver.PolicyRulesDriver.add_integrity
[WRAPPER] policy_rules_driver.PolicyRulesDriver.add_rule
[INTERNAL] policy_rules_driver.PolicyRulesDriver.fetch_rule_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_rules_driver.PolicyRulesDriver.flush
[WRAPPER] policy_rules_driver.get_policy_rules_driver
[WRAPPER] policy_rules_engine.PolicyRulesService.__init__ → policy_rules_driver:get_policy_rules_driver
[LEAF] policy_rules_engine.PolicyRulesService._compute_hash
[INTERNAL] policy_rules_engine.PolicyRulesService._get_rule → policy_proposal_read_driver:PolicyProposalReadDriver.fetch_rule_by_id, policy_rules_driver:PolicyRulesDriver.fetch_rule_by_id
[WRAPPER] policy_rules_engine.PolicyRulesService._to_response
[LEAF] policy_rules_engine.PolicyRulesService._validate_conditions
[INTERNAL] policy_rules_engine.PolicyRulesService.create → policy_limits_engine:PolicyLimitsService._to_response, policy_rules_driver:PolicyRulesDriver.add_integrity, policy_rules_driver:PolicyRulesDriver.add_rule, policy_rules_engine:PolicyRulesService._compute_hash, policy_rules_engine:PolicyRulesService._to_response, ...+1
[WRAPPER] policy_rules_engine.PolicyRulesService.get → policy_limits_engine:PolicyLimitsService._to_response, policy_rules_engine:PolicyRulesService._get_rule, policy_rules_engine:PolicyRulesService._to_response
[CANONICAL] policy_rules_engine.PolicyRulesService.update → policy_limits_engine:PolicyLimitsService._to_response, policy_rules_engine:PolicyRulesService._get_rule, policy_rules_engine:PolicyRulesService._to_response, policy_rules_engine:PolicyRulesService._validate_conditions
[WRAPPER] policy_rules_read_driver.PolicyRulesReadDriver.__init__
[INTERNAL] policy_rules_read_driver.PolicyRulesReadDriver.count_policy_rules → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] policy_rules_read_driver.PolicyRulesReadDriver.fetch_policy_rule_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[CANONICAL] policy_rules_read_driver.PolicyRulesReadDriver.fetch_policy_rules → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] policy_rules_read_driver.get_policy_rules_read_driver
[WRAPPER] prevention_engine.PolicyViolationError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] prevention_engine.PreventionEngine.__init__
[SUPERSET] prevention_engine.PreventionEngine._evaluate_custom_policy → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, prevention_engine:PreventionResult.block, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] prevention_engine.PreventionEngine._evaluate_step_inner → binding_moment_enforcer:should_evaluate_policy, policy_conflict_resolver:resolve_policy_conflict, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionEngine._evaluate_custom_policy, ...+3
[ENTRY] prevention_engine.PreventionEngine.evaluate_step → failure_mode_handler:handle_evaluation_error, prevention_engine:PreventionEngine._evaluate_step_inner, prevention_engine:PreventionResult.allow, prevention_engine:PreventionResult.block
[CANONICAL] prevention_engine.PreventionEngine.load_snapshot → dsl_parser:Parser.error, snapshot_engine:PolicySnapshotData.get_policies, snapshot_engine:PolicySnapshotData.get_thresholds, snapshot_engine:PolicySnapshotData.verify_integrity, symbol_table:SymbolTable.get_policies
[WRAPPER] prevention_engine.PreventionResult.allow
[WRAPPER] prevention_engine.PreventionResult.block
[WRAPPER] prevention_engine.PreventionResult.warn
[ENTRY] prevention_engine.create_policy_snapshot_for_run → dsl_parser:Parser.error, policy_rules_driver:PolicyRulesDriver.flush
[LEAF] prevention_hook.PreventionContext.__post_init__
[LEAF] prevention_hook.PreventionHook.__init__
[CANONICAL] prevention_hook.PreventionHook.evaluate → content_accuracy:ContentAccuracyValidator.validate, validator:PolicyValidator.validate, validator:validate
[LEAF] prevention_hook.PreventionHook.get_safe_response
[LEAF] prevention_hook.PreventionResult.__post_init__
[WRAPPER] prevention_hook.PreventionResult.to_dict
[WRAPPER] prevention_hook.create_prevention_hook
[ENTRY] prevention_hook.evaluate_response → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, ...+3
[INTERNAL] prevention_hook.get_prevention_hook → prevention_hook:create_prevention_hook
[WRAPPER] proposals_read_driver.ProposalsReadDriver.__init__
[INTERNAL] proposals_read_driver.ProposalsReadDriver.count_draft_proposals → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] proposals_read_driver.ProposalsReadDriver.fetch_proposal_by_id → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[CANONICAL] proposals_read_driver.ProposalsReadDriver.fetch_proposals → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] proposals_read_driver.get_proposals_read_driver
[WRAPPER] protection_provider.AbuseProtectionProvider.check_all
[WRAPPER] protection_provider.AbuseProtectionProvider.check_burst
[WRAPPER] protection_provider.AbuseProtectionProvider.check_cost
[WRAPPER] protection_provider.AbuseProtectionProvider.check_rate_limit
[WRAPPER] protection_provider.AbuseProtectionProvider.detect_anomaly
[LEAF] protection_provider.MockAbuseProtectionProvider.__init__
[WRAPPER] protection_provider.MockAbuseProtectionProvider.add_cost → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[CANONICAL] protection_provider.MockAbuseProtectionProvider.check_all → policy_mapper:MCPPolicyDecision.allow, prevention_engine:PreventionResult.allow, protection_provider:AbuseProtectionProvider.check_burst, protection_provider:AbuseProtectionProvider.check_cost, protection_provider:AbuseProtectionProvider.check_rate_limit, ...+5
[SUPERSET] protection_provider.MockAbuseProtectionProvider.check_burst → policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] protection_provider.MockAbuseProtectionProvider.check_cost → policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, snapshot_engine:PolicySnapshotRegistry.get
[SUPERSET] protection_provider.MockAbuseProtectionProvider.check_rate_limit → policy_limits_engine:PolicyLimitsService.get, policy_mapper:MCPPolicyDecision.allow, policy_rules_engine:PolicyRulesService.get, prevention_engine:PreventionResult.allow, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] protection_provider.MockAbuseProtectionProvider.detect_anomaly
[INTERNAL] protection_provider.MockAbuseProtectionProvider.reset → intent:IntentEmitter.clear
[LEAF] protection_provider.MockAbuseProtectionProvider.reset_rate_limits
[LEAF] protection_provider.get_protection_provider
[WRAPPER] protection_provider.set_protection_provider
[LEAF] recovery_evaluation_engine.FailureContext.__post_init__
[WRAPPER] recovery_evaluation_engine.RecoveryDecision.to_dict
[WRAPPER] recovery_evaluation_engine.RecoveryEvaluationEngine.__init__
[LEAF] recovery_evaluation_engine.RecoveryEvaluationEngine.emit_decision_record
[INTERNAL] recovery_evaluation_engine.RecoveryEvaluationEngine.evaluate → ast:BlockAction.to_dict, ast:Clause.to_dict, ast:ExistsPredicate.to_dict, ast:LogicalCondition.to_dict, ast:PolicyAST.to_dict, ...+42
[ENTRY] recovery_evaluation_engine.evaluate_and_execute → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, ...+6
[ENTRY] recovery_evaluation_engine.evaluate_recovery → eligibility_engine:EligibilityEngine.evaluate, engine:PolicyEngine.evaluate, interpreter:Interpreter.evaluate, interpreter:evaluate, policy_driver:PolicyDriver.evaluate, ...+5
[WRAPPER] recovery_matcher.RecoveryMatcher.__init__
[WRAPPER] recovery_matcher.RecoveryMatcher._calculate_time_weight
[SUPERSET] recovery_matcher.RecoveryMatcher._compute_confidence → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, recovery_matcher:RecoveryMatcher._calculate_time_weight, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] recovery_matcher.RecoveryMatcher._count_occurrences → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] recovery_matcher.RecoveryMatcher._escalate_to_llm → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] recovery_matcher.RecoveryMatcher._find_similar_by_embedding → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[INTERNAL] recovery_matcher.RecoveryMatcher._find_similar_failures → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[LEAF] recovery_matcher.RecoveryMatcher._generate_suggestion
[INTERNAL] recovery_matcher.RecoveryMatcher._get_cached_recovery → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] recovery_matcher.RecoveryMatcher._normalize_error → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] recovery_matcher.RecoveryMatcher._set_cached_recovery
[INTERNAL] recovery_matcher.RecoveryMatcher._upsert_candidate → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] recovery_matcher.RecoveryMatcher.approve_candidate → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[SUPERSET] recovery_matcher.RecoveryMatcher.get_candidates → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[CANONICAL] recovery_matcher.RecoveryMatcher.suggest → dsl_parser:Parser.error, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, recovery_matcher:RecoveryMatcher._compute_confidence, recovery_matcher:RecoveryMatcher._count_occurrences, ...+5
[SUPERSET] recovery_matcher.RecoveryMatcher.suggest_hybrid → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, recovery_matcher:RecoveryMatcher._escalate_to_llm, recovery_matcher:RecoveryMatcher._find_similar_by_embedding, recovery_matcher:RecoveryMatcher._get_cached_recovery, ...+4
[WRAPPER] recovery_write_driver.RecoveryWriteService.__init__
[WRAPPER] recovery_write_driver.RecoveryWriteService.enqueue_evaluation_db_fallback → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[ENTRY] recovery_write_driver.RecoveryWriteService.get_candidate_by_idempotency_key → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[WRAPPER] recovery_write_driver.RecoveryWriteService.insert_suggestion_provenance → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[ENTRY] recovery_write_driver.RecoveryWriteService.update_recovery_candidate → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[ENTRY] recovery_write_driver.RecoveryWriteService.upsert_recovery_candidate → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxService.execute
[CANONICAL] runtime_command.execute_query → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, runtime_command:query_allowed_skills, runtime_command:query_execution_history, runtime_command:query_last_step_outcome, ...+3
[ENTRY] runtime_command.get_all_skill_descriptors → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[ENTRY] runtime_command.get_capabilities → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] runtime_command.get_resource_contract
[ENTRY] runtime_command.get_skill_info → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] runtime_command.get_supported_query_types
[WRAPPER] runtime_command.list_skills → snapshot_engine:PolicySnapshotRegistry.list
[INTERNAL] runtime_command.query_allowed_skills → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] runtime_command.query_execution_history
[WRAPPER] runtime_command.query_last_step_outcome
[WRAPPER] runtime_command.query_remaining_budget
[INTERNAL] runtime_command.query_skills_for_goal → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] sandbox_engine.ExecutionRecord.to_dict
[WRAPPER] sandbox_engine.SandboxPolicy.to_dict → snapshot_engine:PolicySnapshotRegistry.list
[WRAPPER] sandbox_engine.SandboxPolicy.to_resource_limits
[INTERNAL] sandbox_engine.SandboxService.__init__ → sandbox_engine:SandboxService._setup_default_policies
[SUPERSET] sandbox_engine.SandboxService._check_quota → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] sandbox_engine.SandboxService._get_executor
[LEAF] sandbox_engine.SandboxService._get_policy
[LEAF] sandbox_engine.SandboxService._setup_default_policies
[LEAF] sandbox_engine.SandboxService._track_execution
[LEAF] sandbox_engine.SandboxService.define_policy
[CANONICAL] sandbox_engine.SandboxService.execute → deterministic_engine:DeterministicEngine.execute, sandbox_engine:SandboxPolicy.to_resource_limits, sandbox_engine:SandboxService._check_quota, sandbox_engine:SandboxService._get_executor, sandbox_engine:SandboxService._get_policy, ...+1
[LEAF] sandbox_engine.SandboxService.get_execution_records
[SUPERSET] sandbox_engine.SandboxService.get_execution_stats → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] sandbox_engine.SandboxService.get_policy → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] sandbox_engine.SandboxService.list_policies
[WRAPPER] scope_resolver.ScopeResolutionResult.to_snapshot
[WRAPPER] scope_resolver.ScopeResolver.__init__
[LEAF] scope_resolver.ScopeResolver._get_scope
[INTERNAL] scope_resolver.ScopeResolver._load_scopes → snapshot_engine:PolicySnapshotRegistry.list
[ENTRY] scope_resolver.ScopeResolver.get_scope_for_policy → scope_resolver:ScopeResolver._get_scope
[WRAPPER] scope_resolver.ScopeResolver.matches_scope
[CANONICAL] scope_resolver.ScopeResolver.resolve_applicable_policies → scope_resolver:ScopeResolver._load_scopes, scope_resolver:ScopeResolver.matches_scope, snapshot_engine:PolicySnapshotRegistry.list
[LEAF] scope_resolver.get_scope_resolver
[LEAF] snapshot_engine.PolicySnapshotData.compute_hash
[WRAPPER] snapshot_engine.PolicySnapshotData.get_policies
[WRAPPER] snapshot_engine.PolicySnapshotData.get_thresholds
[INTERNAL] snapshot_engine.PolicySnapshotData.to_dict → snapshot_engine:PolicySnapshotData.verify_integrity
[WRAPPER] snapshot_engine.PolicySnapshotData.verify_integrity → ast:PolicyAST.compute_hash, ir_compiler:PolicyIR.compute_hash, snapshot_engine:PolicySnapshotData.compute_hash
[WRAPPER] snapshot_engine.PolicySnapshotData.verify_threshold_integrity → ast:PolicyAST.compute_hash, ir_compiler:PolicyIR.compute_hash, snapshot_engine:PolicySnapshotData.compute_hash
[INTERNAL] snapshot_engine.PolicySnapshotError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] snapshot_engine.PolicySnapshotError.to_dict
[WRAPPER] snapshot_engine.PolicySnapshotRegistry.__init__
[INTERNAL] snapshot_engine.PolicySnapshotRegistry._get_next_version → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[INTERNAL] snapshot_engine.PolicySnapshotRegistry._supersede_active → snapshot_engine:PolicySnapshotRegistry.get_active
[SUPERSET] snapshot_engine.PolicySnapshotRegistry.archive → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[ENTRY] snapshot_engine.PolicySnapshotRegistry.attempt_modify → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[ENTRY] snapshot_engine.PolicySnapshotRegistry.clear_tenant → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:PolicySnapshotRegistry.list
[CANONICAL] snapshot_engine.PolicySnapshotRegistry.create → snapshot_engine:PolicySnapshotData.compute_hash, snapshot_engine:PolicySnapshotRegistry._get_next_version, snapshot_engine:PolicySnapshotRegistry._supersede_active
[SUPERSET] snapshot_engine.PolicySnapshotRegistry.delete → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] snapshot_engine.PolicySnapshotRegistry.get → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get
[INTERNAL] snapshot_engine.PolicySnapshotRegistry.get_active → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] snapshot_engine.PolicySnapshotRegistry.get_by_version
[WRAPPER] snapshot_engine.PolicySnapshotRegistry.get_history
[SUPERSET] snapshot_engine.PolicySnapshotRegistry.get_statistics → snapshot_engine:PolicySnapshotData.verify_integrity
[LEAF] snapshot_engine.PolicySnapshotRegistry.list
[INTERNAL] snapshot_engine.PolicySnapshotRegistry.reset → intent:IntentEmitter.clear
[SUPERSET] snapshot_engine.PolicySnapshotRegistry.verify → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotData.verify_integrity, snapshot_engine:PolicySnapshotData.verify_threshold_integrity, snapshot_engine:PolicySnapshotRegistry.get
[WRAPPER] snapshot_engine.SnapshotRegistryStats.to_dict
[ENTRY] snapshot_engine._reset_snapshot_registry → protection_provider:MockAbuseProtectionProvider.reset, snapshot_engine:PolicySnapshotRegistry.reset
[WRAPPER] snapshot_engine.create_policy_snapshot → learning_proof_engine:PrioritizedCheckpoint.create, policy_limits_engine:PolicyLimitsService.create, policy_rules_engine:PolicyRulesService.create, snapshot_engine:PolicySnapshotRegistry.create, snapshot_engine:get_snapshot_registry
[WRAPPER] snapshot_engine.get_active_snapshot → snapshot_engine:PolicySnapshotRegistry.get_active, snapshot_engine:get_snapshot_registry
[WRAPPER] snapshot_engine.get_policy_snapshot → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, snapshot_engine:get_snapshot_registry
[WRAPPER] snapshot_engine.get_snapshot_history → snapshot_engine:PolicySnapshotRegistry.get_history, snapshot_engine:get_snapshot_registry
[LEAF] snapshot_engine.get_snapshot_registry
[WRAPPER] snapshot_engine.verify_snapshot → snapshot_engine:PolicySnapshotRegistry.verify, snapshot_engine:get_snapshot_registry
[WRAPPER] state.BillingState.allows_usage
[WRAPPER] state.BillingState.default
[LEAF] state.BillingState.from_string
[WRAPPER] state.BillingState.is_in_good_standing
[LEAF] symbol_table.Scope.define
[ENTRY] symbol_table.Scope.get_all_symbols → policy_limits_engine:PolicyLimitsService.update, policy_rules_engine:PolicyRulesService.update
[SUPERSET] symbol_table.Scope.lookup → symbol_table:SymbolTable.lookup
[LEAF] symbol_table.Scope.lookup_by_category
[WRAPPER] symbol_table.Symbol.__repr__
[INTERNAL] symbol_table.SymbolTable.__init__ → symbol_table:SymbolTable._define_builtins
[LEAF] symbol_table.SymbolTable.__str__
[INTERNAL] symbol_table.SymbolTable._define_builtins → symbol_table:Scope.define, symbol_table:SymbolTable.define
[INTERNAL] symbol_table.SymbolTable.add_reference → symbol_table:Scope.lookup, symbol_table:SymbolTable.lookup
[INTERNAL] symbol_table.SymbolTable.define → symbol_table:Scope.define
[LEAF] symbol_table.SymbolTable.enter_scope
[LEAF] symbol_table.SymbolTable.exit_scope
[WRAPPER] symbol_table.SymbolTable.get_policies
[LEAF] symbol_table.SymbolTable.get_rules
[ENTRY] symbol_table.SymbolTable.get_symbols_by_category → policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get
[LEAF] symbol_table.SymbolTable.get_unreferenced_symbols
[WRAPPER] symbol_table.SymbolTable.lookup → symbol_table:Scope.lookup
[INTERNAL] symbol_table.SymbolTable.lookup_policy → symbol_table:Scope.lookup, symbol_table:SymbolTable.lookup
[CANONICAL] symbol_table.SymbolTable.lookup_rule → symbol_table:Scope.lookup, symbol_table:SymbolTable.lookup, symbol_table:SymbolTable.lookup_policy
[WRAPPER] tokenizer.Token.__repr__
[WRAPPER] tokenizer.Token.is_action
[WRAPPER] tokenizer.Token.is_category
[LEAF] tokenizer.Tokenizer.__init__
[ENTRY] tokenizer.Tokenizer.__iter__ → dsl_parser:Lexer.tokenize, tokenizer:Tokenizer.tokenize
[LEAF] tokenizer.Tokenizer.advance
[LEAF] tokenizer.Tokenizer.current_char
[LEAF] tokenizer.Tokenizer.peek
[INTERNAL] tokenizer.Tokenizer.read_identifier → compiler_parser:Parser.advance, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, tokenizer:Tokenizer.advance
[INTERNAL] tokenizer.Tokenizer.read_number → compiler_parser:Parser.advance, tokenizer:Tokenizer.advance
[CANONICAL] tokenizer.Tokenizer.read_operator → compiler_parser:Parser.advance, compiler_parser:Parser.peek, tokenizer:Tokenizer.advance, tokenizer:Tokenizer.peek
[SUPERSET] tokenizer.Tokenizer.read_string → compiler_parser:Parser.advance, policy_limits_engine:PolicyLimitsService.get, policy_rules_engine:PolicyRulesService.get, snapshot_engine:PolicySnapshotRegistry.get, tokenizer:Tokenizer.advance
[INTERNAL] tokenizer.Tokenizer.skip_comment → compiler_parser:Parser.advance, tokenizer:Tokenizer.advance
[INTERNAL] tokenizer.Tokenizer.skip_whitespace → compiler_parser:Parser.advance, tokenizer:Tokenizer.advance
[SUPERSET] tokenizer.Tokenizer.tokenize → compiler_parser:Parser.advance, tokenizer:Tokenizer.advance, tokenizer:Tokenizer.read_identifier, tokenizer:Tokenizer.read_number, tokenizer:Tokenizer.read_operator, ...+3
[INTERNAL] tokenizer.TokenizerError.__init__ → arbitrator:PolicyArbitrator.__init__, compiler_parser:ParseError.__init__, compiler_parser:Parser.__init__, content_accuracy:ContentAccuracyValidator.__init__, customer_policy_read_engine:CustomerPolicyReadService.__init__, ...+67
[WRAPPER] validator.PolicyValidator.__init__
[SUPERSET] validator.PolicyValidator._check_warnings → ast:is_block_action, ast:is_require_approval_action
[SUPERSET] validator.PolicyValidator._extract_metrics → ast:is_exists_predicate, ast:is_logical_condition, ast:is_predicate
[SUPERSET] validator.PolicyValidator._validate_metrics → validator:PolicyValidator._extract_metrics
[SUPERSET] validator.PolicyValidator._validate_mode_enforcement → ast:is_block_action, ast:is_require_approval_action
[LEAF] validator.PolicyValidator._validate_structure
[INTERNAL] validator.PolicyValidator.validate → validator:PolicyValidator._check_warnings, validator:PolicyValidator._validate_metrics, validator:PolicyValidator._validate_mode_enforcement, validator:PolicyValidator._validate_structure
[WRAPPER] validator.ValidationIssue.__str__
[WRAPPER] validator.ValidationResult.__bool__
[WRAPPER] validator.ValidationResult.__post_init__
[WRAPPER] validator.ValidationResult.errors
[WRAPPER] validator.ValidationResult.warnings
[WRAPPER] validator.is_valid → content_accuracy:ContentAccuracyValidator.validate, validator:PolicyValidator.validate, validator:validate
[WRAPPER] validator.validate → content_accuracy:ContentAccuracyValidator.validate, validator:PolicyValidator.validate
[INTERNAL] visitors.BaseVisitor.visit_action_block → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[INTERNAL] visitors.BaseVisitor.visit_attr_access → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[SUPERSET] visitors.BaseVisitor.visit_binary_op → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[SUPERSET] visitors.BaseVisitor.visit_condition_block → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[INTERNAL] visitors.BaseVisitor.visit_func_call → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[WRAPPER] visitors.BaseVisitor.visit_ident
[WRAPPER] visitors.BaseVisitor.visit_import
[WRAPPER] visitors.BaseVisitor.visit_literal
[INTERNAL] visitors.BaseVisitor.visit_policy_decl → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[WRAPPER] visitors.BaseVisitor.visit_priority
[INTERNAL] visitors.BaseVisitor.visit_program → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[WRAPPER] visitors.BaseVisitor.visit_route_target
[INTERNAL] visitors.BaseVisitor.visit_rule_decl → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[WRAPPER] visitors.BaseVisitor.visit_rule_ref
[INTERNAL] visitors.BaseVisitor.visit_unary_op → dsl_parser:Parser.accept, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, nodes:BinaryOpNode.accept, ...+12
[WRAPPER] visitors.CategoryCollector.__init__
[WRAPPER] visitors.CategoryCollector.get_categories
[INTERNAL] visitors.CategoryCollector.visit_policy_decl → ir_builder:IRBuilder.visit_policy_decl, nodes:ASTVisitor.visit_policy_decl, visitors:BaseVisitor.visit_policy_decl, visitors:PrintVisitor.visit_policy_decl, visitors:RuleExtractor.visit_policy_decl
[INTERNAL] visitors.CategoryCollector.visit_rule_decl → ir_builder:IRBuilder.visit_rule_decl, nodes:ASTVisitor.visit_rule_decl, visitors:BaseVisitor.visit_rule_decl, visitors:PrintVisitor.visit_rule_decl, visitors:RuleExtractor.visit_rule_decl
[WRAPPER] visitors.PrintVisitor.__init__
[WRAPPER] visitors.PrintVisitor._emit
[WRAPPER] visitors.PrintVisitor.get_output
[WRAPPER] visitors.PrintVisitor.visit_action_block → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] visitors.PrintVisitor.visit_attr_access → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[SUPERSET] visitors.PrintVisitor.visit_binary_op → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[CANONICAL] visitors.PrintVisitor.visit_condition_block → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[INTERNAL] visitors.PrintVisitor.visit_func_call → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[WRAPPER] visitors.PrintVisitor.visit_ident → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[WRAPPER] visitors.PrintVisitor.visit_import → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[WRAPPER] visitors.PrintVisitor.visit_literal → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] visitors.PrintVisitor.visit_policy_decl → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[WRAPPER] visitors.PrintVisitor.visit_priority → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] visitors.PrintVisitor.visit_program → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+15
[WRAPPER] visitors.PrintVisitor.visit_route_target → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] visitors.PrintVisitor.visit_rule_decl → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[WRAPPER] visitors.PrintVisitor.visit_rule_ref → ir_builder:IRBuilder._emit, visitors:PrintVisitor._emit
[INTERNAL] visitors.PrintVisitor.visit_unary_op → dsl_parser:Parser.accept, ir_builder:IRBuilder._emit, nodes:ASTNode.accept, nodes:ActionBlockNode.accept, nodes:AttrAccessNode.accept, ...+14
[WRAPPER] visitors.RuleExtractor.__init__
[WRAPPER] visitors.RuleExtractor.get_rules
[INTERNAL] visitors.RuleExtractor.visit_condition_block → ir_builder:IRBuilder.visit_condition_block, nodes:ASTVisitor.visit_condition_block, visitors:BaseVisitor.visit_condition_block, visitors:PrintVisitor.visit_condition_block
[INTERNAL] visitors.RuleExtractor.visit_policy_decl → ir_builder:IRBuilder.visit_policy_decl, nodes:ASTVisitor.visit_policy_decl, visitors:BaseVisitor.visit_policy_decl, visitors:CategoryCollector.visit_policy_decl, visitors:PrintVisitor.visit_policy_decl
[INTERNAL] visitors.RuleExtractor.visit_rule_decl → ir_builder:IRBuilder.visit_rule_decl, nodes:ASTVisitor.visit_rule_decl, visitors:BaseVisitor.visit_rule_decl, visitors:CategoryCollector.visit_rule_decl, visitors:PrintVisitor.visit_rule_decl
[WRAPPER] worker_execution_command.calculate_cost_cents
[CANONICAL] worker_execution_command.convert_brand_request → worker_execution_command:get_brand_schema_types
[LEAF] worker_execution_command.execute_worker
[WRAPPER] worker_execution_command.get_brand_schema_types
[WRAPPER] worker_execution_command.replay_execution
```
