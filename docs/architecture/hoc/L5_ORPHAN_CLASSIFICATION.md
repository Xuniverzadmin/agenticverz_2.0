# L5 Orphan Classification Report

**Generated:** 2026-01-30
**Phase:** B — PIN-491

---

## Summary

| Domain | Total | WIRED | L2-DIRECT | INTERNAL | SCHEMA-ONLY | UNCLASSIFIED |
|--------|-------|-------|-----------|----------|-------------|--------------|
| account | 10 | 2 | 0 | 0 | 2 | 6 |
| activity | 8 | 4 | 0 | 4 | 0 | 0 |
| analytics | 20 | 2 | 0 | 1 | 1 | 16 |
| api_keys | 2 | 1 | 0 | 0 | 0 | 1 |
| controls | 11 | 2 | 0 | 0 | 0 | 9 |
| incidents | 17 | 1 | 0 | 6 | 2 | 8 |
| integrations | 37 | 3 | 0 | 1 | 14 | 19 |
| logs | 18 | 6 | 0 | 1 | 0 | 11 |
| overview | 1 | 1 | 0 | 0 | 0 | 0 |
| policies | 61 | 9 | 0 | 5 | 13 | 34 |
| **TOTAL** | **185** | **31** | **0** | **18** | **32** | **104** |

---

## account (10 engines)

### WIRED (2)

| Engine | Lines | Reason |
|--------|-------|--------|
| `accounts_facade.py` | 1140 | Referenced by L4 orchestrator |
| `notifications_facade.py` | 480 | Referenced by L4 orchestrator |

### SCHEMA-ONLY (2)

| Engine | Lines | Reason |
|--------|-------|--------|
| `crm_validator_engine.py` | 739 | All classes are schema/type classes: IssueType, Severity, RecommendedAction, IssueSource, ValidatorInput, ValidatorVerdict, ValidatorErrorType, ValidatorError, ValidatorService |
| `validator_engine.py` | 735 | All classes are schema/type classes: IssueType, Severity, RecommendedAction, IssueSource, ValidatorInput, ValidatorVerdict, ValidatorErrorType, ValidatorError, ValidatorService |

### UNCLASSIFIED (6)

| Engine | Lines | Reason |
|--------|-------|--------|
| `billing_provider.py` | 251 | No importers found. Functions: 2, Classes: 2, Lines: 251 |
| `email_verification.py` | 302 | No importers found. Functions: 1, Classes: 3, Lines: 302 |
| `identity_resolver.py` | 207 | No importers found. Functions: 1, Classes: 5, Lines: 207 |
| `profile.py` | 459 | No importers found. Functions: 7, Classes: 3, Lines: 459 |
| `tenant_engine.py` | 582 | No importers found. Functions: 1, Classes: 3, Lines: 582 |
| `user_write_engine.py` | 91 | No importers found. Functions: 0, Classes: 1, Lines: 91 |

## activity (8 engines)

### WIRED (4)

| Engine | Lines | Reason |
|--------|-------|--------|
| `activity_facade.py` | 1387 | Referenced by L4 orchestrator |
| `cus_telemetry_service.py` | 77 | Referenced by L4 orchestrator |
| `signal_feedback_engine.py` | 140 | Referenced by L4 orchestrator |
| `signal_identity.py` | 79 | Referenced by L4 orchestrator |

### INTERNAL (4)

| Engine | Lines | Reason |
|--------|-------|--------|
| `activity_enums.py` | 120 | Imported by: activity_facade |
| `attention_ranking_engine.py` | 99 | Imported by: activity_facade |
| `cost_analysis_engine.py` | 93 | Imported by: activity_facade |
| `pattern_detection_engine.py` | 92 | Imported by: activity_facade |

## analytics (20 engines)

### WIRED (2)

| Engine | Lines | Reason |
|--------|-------|--------|
| `analytics_facade.py` | 639 | Referenced by L4 orchestrator |
| `detection_facade.py` | 559 | Referenced by L4 orchestrator |

### INTERNAL (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `cost_anomaly_detector.py` | 1072 | Imported by: detection_facade |

### SCHEMA-ONLY (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `costsim_models.py` | 305 | All classes are schema/type classes: V2SimulationStatus, ComparisonVerdict, V2SimulationResult, ComparisonResult, DiffResult, CanaryReport, DivergenceReport, ValidationResult |

### UNCLASSIFIED (16)

| Engine | Lines | Reason |
|--------|-------|--------|
| `ai_console_panel_engine.py` | 338 | No importers found. Functions: 2, Classes: 1, Lines: 338 |
| `canary.py` | 648 | No importers found. Functions: 1, Classes: 3, Lines: 648 |
| `config.py` | 169 | No importers found. Functions: 4, Classes: 1, Lines: 169 |
| `coordinator.py` | 565 | No importers found. Functions: 0, Classes: 2, Lines: 565 |
| `cost_model_engine.py` | 455 | No importers found. Functions: 6, Classes: 4, Lines: 455 |
| `cost_snapshots.py` | 933 | No importers found. Functions: 2, Classes: 3, Lines: 933 |
| `cost_write_engine.py` | 161 | No importers found. Functions: 0, Classes: 1, Lines: 161 |
| `datasets.py` | 723 | No importers found. Functions: 3, Classes: 3, Lines: 723 |
| `divergence.py` | 365 | No importers found. Functions: 1, Classes: 2, Lines: 365 |
| `envelope.py` | 436 | No importers found. Functions: 5, Classes: 16, Lines: 436 |
| `metrics.py` | 617 | No importers found. Functions: 2, Classes: 1, Lines: 617 |
| `pattern_detection.py` | 409 | No importers found. Functions: 6, Classes: 0, Lines: 409 |
| `prediction.py` | 463 | No importers found. Functions: 5, Classes: 0, Lines: 463 |
| `provenance.py` | 385 | No importers found. Functions: 3, Classes: 2, Lines: 385 |
| `s1_retry_backoff.py` | 148 | No importers found. Functions: 1, Classes: 0, Lines: 148 |
| `sandbox.py` | 307 | No importers found. Functions: 2, Classes: 2, Lines: 307 |

## api_keys (2 engines)

### WIRED (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `api_keys_facade.py` | 237 | Referenced by L4 orchestrator |

### UNCLASSIFIED (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `keys_engine.py` | 233 | No importers found. Functions: 2, Classes: 2, Lines: 233 |

## controls (11 engines)

### WIRED (2)

| Engine | Lines | Reason |
|--------|-------|--------|
| `controls_facade.py` | 438 | Referenced by L4 orchestrator |
| `threshold_engine.py` | 708 | Referenced by L4 orchestrator |

### UNCLASSIFIED (9)

| Engine | Lines | Reason |
|--------|-------|--------|
| `alert_fatigue.py` | 535 | No importers found. Functions: 2, Classes: 5, Lines: 535 |
| `budget_enforcement_engine.py` | 341 | No importers found. Functions: 2, Classes: 1, Lines: 341 |
| `cb_sync_wrapper.py` | 169 | No importers found. Functions: 5, Classes: 0, Lines: 169 |
| `cost_safety_rails.py` | 402 | No importers found. Functions: 1, Classes: 3, Lines: 402 |
| `customer_killswitch_read_engine.py` | 179 | No importers found. Functions: 1, Classes: 5, Lines: 179 |
| `decisions.py` | 221 | No importers found. Functions: 5, Classes: 3, Lines: 221 |
| `killswitch.py` | 262 | No importers found. Functions: 2, Classes: 5, Lines: 262 |
| `killswitch_read_driver.py` | 229 | No importers found. Functions: 1, Classes: 5, Lines: 229 |
| `s2_cost_smoothing.py` | 220 | No importers found. Functions: 3, Classes: 0, Lines: 220 |

## incidents (17 engines)

### WIRED (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `incidents_facade.py` | 983 | Referenced by L4 orchestrator |

### INTERNAL (6)

| Engine | Lines | Reason |
|--------|-------|--------|
| `incident_driver.py` | 279 | Imported by non-L5: transaction_coordinator.py |
| `incident_engine.py` | 905 | Imported by: incident_driver |
| `incident_pattern_engine.py` | 279 | Imported by: incidents_facade |
| `incident_severity_engine.py` | 218 | Imported by non-L5: incident_aggregator.py |
| `postmortem_engine.py` | 444 | Imported by: incidents_facade |
| `recurrence_analysis_engine.py` | 189 | Imported by: incidents_facade |

### SCHEMA-ONLY (2)

| Engine | Lines | Reason |
|--------|-------|--------|
| `incidents_types.py` | 44 | Constants-only module (no classes or functions) |
| `llm_failure_engine.py` | 348 | All classes are schema/type classes: LLMFailureFact, LLMFailureResult, LLMFailureService |

### UNCLASSIFIED (8)

| Engine | Lines | Reason |
|--------|-------|--------|
| `anomaly_bridge.py` | 351 | No importers found. Functions: 1, Classes: 2, Lines: 351 |
| `hallucination_detector.py` | 467 | No importers found. Functions: 1, Classes: 6, Lines: 467 |
| `incident_read_engine.py` | 153 | No importers found. Functions: 1, Classes: 1, Lines: 153 |
| `incident_write_engine.py` | 303 | No importers found. Functions: 1, Classes: 1, Lines: 303 |
| `policy_violation_engine.py` | 713 | No importers found. Functions: 4, Classes: 4, Lines: 713 |
| `prevention_engine.py` | 890 | No importers found. Functions: 4, Classes: 13, Lines: 890 |
| `recovery_rule_engine.py` | 802 | No importers found. Functions: 6, Classes: 10, Lines: 802 |
| `semantic_failures.py` | 298 | No importers found. Functions: 5, Classes: 0, Lines: 298 |

## integrations (37 engines)

### WIRED (3)

| Engine | Lines | Reason |
|--------|-------|--------|
| `connectors_facade.py` | 439 | Referenced by L4 orchestrator |
| `datasources_facade.py` | 451 | Referenced by L4 orchestrator |
| `integrations_facade.py` | 491 | Referenced by L4 orchestrator |

### INTERNAL (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `cus_integration_service.py` | 68 | Imported by: integrations_facade |

### SCHEMA-ONLY (14)

| Engine | Lines | Reason |
|--------|-------|--------|
| `cost_bridges_engine.py` | 1147 | All classes are schema/type classes: AnomalyType, AnomalySeverity, CostAnomaly, CostLoopBridge, CostPatternMatcher, CostRecoveryGenerator, CostPolicyGenerator, CostRoutingAdjuster, CostEstimationProbe, CostLoopOrchestrator |
| `dispatcher.py` | 806 | All classes are schema/type classes: DispatcherConfig, IntegrationDispatcher |
| `file_storage_base.py` | 299 | All classes are schema/type classes: FileMetadata, UploadResult, DownloadResult, ListResult, FileStorageAdapter |
| `founder_ops_adapter.py` | 145 | All classes are schema/type classes: FounderIncidentSummaryView, FounderIncidentsSummaryResponse, FounderOpsAdapter |
| `graduation_engine.py` | 594 | All classes are schema/type classes: GraduationThresholds, GateEvidence, GraduationEvidence, GraduationLevel, ComputedGraduationStatus, GraduationEngine, CapabilityGates, SimulationState |
| `http_connector.py` | 367 | All classes are schema/type classes: HttpMethod, EndpointConfig, HttpConnectorConfig, HttpConnectorError, RateLimitExceededError, HttpConnectorService |
| `iam_engine.py` | 440 | All classes are schema/type classes: IdentityProvider, ActorType, Identity, AccessDecision, IAMService |
| `mcp_connector.py` | 423 | All classes are schema/type classes: McpToolDefinition, McpConnectorConfig, McpConnectorError, McpApprovalRequiredError, McpRateLimitExceededError, McpSchemaValidationError, McpConnectorService |
| `protocol.py` | 63 | All classes are schema/type classes: CredentialService |
| `serverless_base.py` | 236 | All classes are schema/type classes: InvocationType, InvocationRequest, InvocationResult, FunctionInfo, ServerlessAdapter |
| `sql_gateway.py` | 464 | All classes are schema/type classes: ParameterType, ParameterSpec, QueryTemplate, SqlGatewayConfig, SqlGatewayError, SqlInjectionAttemptError, SqlGatewayService |
| `types.py` | 56 | All classes are schema/type classes: Credential |
| `vector_stores_base.py` | 265 | All classes are schema/type classes: VectorRecord, QueryResult, UpsertResult, DeleteResult, IndexStats, VectorStoreAdapter |
| `webhook_adapter.py` | 472 | All classes are schema/type classes: CircuitState, CircuitBreakerConfig, CircuitBreaker, WebhookDeliveryAttempt, WebhookDelivery, WebhookAdapter |

### UNCLASSIFIED (19)

| Engine | Lines | Reason |
|--------|-------|--------|
| `bridges.py` | 1229 | No importers found. Functions: 3, Classes: 6, Lines: 1229 |
| `cloud_functions_adapter.py` | 313 | No importers found. Functions: 0, Classes: 1, Lines: 313 |
| `cus_health_engine.py` | 534 | No importers found. Functions: 0, Classes: 1, Lines: 534 |
| `customer_activity_adapter.py` | 332 | No importers found. Functions: 1, Classes: 4, Lines: 332 |
| `customer_incidents_adapter.py` | 398 | No importers found. Functions: 3, Classes: 5, Lines: 398 |
| `customer_keys_adapter.py` | 305 | No importers found. Functions: 1, Classes: 4, Lines: 305 |
| `customer_logs_adapter.py` | 410 | No importers found. Functions: 1, Classes: 5, Lines: 410 |
| `customer_policies_adapter.py` | 279 | No importers found. Functions: 1, Classes: 5, Lines: 279 |
| `gcs_adapter.py` | 442 | No importers found. Functions: 0, Classes: 1, Lines: 442 |
| `lambda_adapter.py` | 281 | No importers found. Functions: 0, Classes: 1, Lines: 281 |
| `pgvector_adapter.py` | 378 | No importers found. Functions: 0, Classes: 1, Lines: 378 |
| `pinecone_adapter.py` | 283 | No importers found. Functions: 0, Classes: 1, Lines: 283 |
| `prevention_contract.py` | 201 | No importers found. Functions: 4, Classes: 2, Lines: 201 |
| `runtime_adapter.py` | 215 | No importers found. Functions: 1, Classes: 1, Lines: 215 |
| `s3_adapter.py` | 393 | No importers found. Functions: 0, Classes: 1, Lines: 393 |
| `slack_adapter.py` | 305 | No importers found. Functions: 0, Classes: 1, Lines: 305 |
| `smtp_adapter.py` | 259 | No importers found. Functions: 0, Classes: 1, Lines: 259 |
| `weaviate_adapter.py` | 399 | No importers found. Functions: 0, Classes: 1, Lines: 399 |
| `workers_adapter.py` | 208 | No importers found. Functions: 1, Classes: 1, Lines: 208 |

## logs (18 engines)

### WIRED (6)

| Engine | Lines | Reason |
|--------|-------|--------|
| `certificate.py` | 386 | Referenced by L4 orchestrator |
| `evidence_facade.py` | 570 | Referenced by L4 orchestrator |
| `evidence_report.py` | 1164 | Referenced by L4 orchestrator |
| `logs_facade.py` | 1407 | Referenced by L4 orchestrator |
| `pdf_renderer.py` | 687 | Referenced by L4 orchestrator |
| `replay_determinism.py` | 519 | Referenced by L4 orchestrator |

### INTERNAL (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `trace_facade.py` | 297 | Imported by non-L5: transaction_coordinator.py |

### UNCLASSIFIED (11)

| Engine | Lines | Reason |
|--------|-------|--------|
| `audit_engine.py` | 888 | No importers found. Functions: 2, Classes: 7, Lines: 888 |
| `audit_evidence.py` | 671 | No importers found. Functions: 6, Classes: 3, Lines: 671 |
| `audit_ledger_service.py` | 220 | No importers found. Functions: 1, Classes: 1, Lines: 220 |
| `audit_reconciler.py` | 322 | No importers found. Functions: 1, Classes: 1, Lines: 322 |
| `completeness_checker.py` | 518 | No importers found. Functions: 2, Classes: 4, Lines: 518 |
| `logs_read_engine.py` | 215 | No importers found. Functions: 1, Classes: 1, Lines: 215 |
| `mapper.py` | 273 | No importers found. Functions: 1, Classes: 1, Lines: 273 |
| `panel_response_assembler.py` | 265 | No importers found. Functions: 1, Classes: 1, Lines: 265 |
| `redact.py` | 267 | No importers found. Functions: 8, Classes: 0, Lines: 267 |
| `traces_metrics.py` | 297 | No importers found. Functions: 4, Classes: 1, Lines: 297 |
| `traces_models.py` | 420 | No importers found. Functions: 2, Classes: 5, Lines: 420 |

## overview (1 engines)

### WIRED (1)

| Engine | Lines | Reason |
|--------|-------|--------|
| `overview_facade.py` | 619 | Referenced by L4 orchestrator |

## policies (61 engines)

### WIRED (9)

| Engine | Lines | Reason |
|--------|-------|--------|
| `cus_enforcement_service.py` | 80 | Referenced by L4 orchestrator |
| `governance_facade.py` | 618 | Referenced by L4 orchestrator |
| `lessons_engine.py` | 1080 | Referenced by L4 orchestrator |
| `limits_facade.py` | 459 | Referenced by L4 orchestrator |
| `limits_simulation_service.py` | 80 | Referenced by L4 orchestrator |
| `policies_facade.py` | 111 | Referenced by L4 orchestrator |
| `policy_driver.py` | 415 | Referenced by L4 orchestrator |
| `policy_limits_engine.py` | 371 | Referenced by L4 orchestrator |
| `policy_rules_engine.py` | 394 | Referenced by L4 orchestrator |

### INTERNAL (5)

| Engine | Lines | Reason |
|--------|-------|--------|
| `engine.py` | 2843 | Imported by: policy_mapper |
| `limits.py` | 157 | Imported by non-L5: policies_handler.py |
| `policy_graph_engine.py` | 797 | Imported by: policy_proposal_engine |
| `policy_mapper.py` | 490 | Imports wired/internal engines: engine |
| `policy_proposal_engine.py` | 713 | Imports wired/internal engines: policy_graph_engine |

### SCHEMA-ONLY (13)

| Engine | Lines | Reason |
|--------|-------|--------|
| `deterministic_engine.py` | 513 | All classes are schema/type classes: ExecutionStatus, ExecutionContext, ExecutionResult, DeterministicEngine |
| `eligibility_engine.py` | 836 | All classes are schema/type classes: EligibilityDecision, SystemHealthStatus, EligibilityConfig, CapabilityLookup, GovernanceSignalLookup, SystemHealthLookup, ContractLookup, PreApprovalLookup, DefaultCapabilityLookup, DefaultGovernanceSignalLookup, DefaultSystemHealthLookup, DefaultContractLookup, DefaultPreApprovalLookup, EligibilityInput, RuleResult, EligibilityVerdict, EligibilityEngine |
| `folds.py` | 403 | All classes are schema/type classes: FoldResult, ConstantFolder, DeadCodeEliminator, PolicySimplifier |
| `grammar.py` | 216 | All classes are schema/type classes: GrammarNodeType, PolicyCategory, ActionType, GrammarProduction, PLangGrammar |
| `intent.py` | 365 | All classes are schema/type classes: IntentType, IntentPayload, Intent, IntentEmitter |
| `ir_nodes.py` | 404 | All classes are schema/type classes: IRType, IRGovernance, IRNode, IRInstruction, IRLoadConst, IRLoadVar, IRStoreVar, IRBinaryOp, IRUnaryOp, IRCompare, IRJump, IRJumpIf, IRCall, IRReturn, IRAction, IRCheckPolicy, IREmitIntent, IRBlock, IRFunction, IRModule |
| `learning_proof_engine.py` | 850 | All classes are schema/type classes: PreventionOutcome, PreventionRecord, PreventionTracker, RegretType, RegretEvent, PolicyRegretTracker, GlobalRegretTracker, PatternCalibration, AdaptiveConfidenceSystem, CheckpointPriority, CheckpointConfig, PrioritizedCheckpoint, M25GraduationStatus, PreventionTimeline |
| `nodes.py` | 379 | All classes are schema/type classes: GovernanceMetadata, ASTNode, ExprNode, ProgramNode, PolicyDeclNode, RuleDeclNode, ImportNode, RuleRefNode, PriorityNode, ConditionBlockNode, ActionBlockNode, RouteTargetNode, BinaryOpNode, UnaryOpNode, ValueNode, IdentNode, LiteralNode, FuncCallNode, AttrAccessNode, ASTVisitor |
| `plan.py` | 145 | All classes are schema/type classes: PlanTier, Plan |
| `policy_models.py` | 739 | All classes are schema/type classes: PolicyCategory, PolicyDecision, ActionType, ViolationType, ViolationSeverity, RecoverabilityType, SafetyRuleType, EthicalConstraintType, BusinessRuleType, PolicyEvaluationRequest, PolicyModification, PolicyEvaluationResult, PolicyViolation, PolicyRule, Policy, RiskCeiling, SafetyRule, EthicalConstraint, BusinessRule, PolicyState, PolicyLoadResult, PolicyVersion, PolicyProvenance, PolicyDependency, PolicyConflict, DependencyGraph, TemporalPolicyType, TemporalPolicy, TemporalMetricWindow, PolicyContext, EnhancedPolicyEvaluationRequest, EnhancedPolicyViolation, EnhancedPolicyEvaluationResult |
| `sandbox_engine.py` | 551 | All classes are schema/type classes: SandboxPolicy, ExecutionRequest, ExecutionRecord, SandboxService |
| `state.py` | 108 | All classes are schema/type classes: BillingState |
| `tokenizer.py` | 352 | All classes are schema/type classes: TokenType, Token, TokenizerError, Tokenizer |

### UNCLASSIFIED (34)

| Engine | Lines | Reason |
|--------|-------|--------|
| `ast.py` | 381 | No importers found. Functions: 6, Classes: 13, Lines: 381 |
| `authority_checker.py` | 284 | No importers found. Functions: 1, Classes: 3, Lines: 284 |
| `binding_moment_enforcer.py` | 276 | No importers found. Functions: 6, Classes: 3, Lines: 276 |
| `claim_decision_engine.py` | 123 | No importers found. Functions: 3, Classes: 0, Lines: 123 |
| `compiler_parser.py` | 460 | No importers found. Functions: 0, Classes: 2, Lines: 460 |
| `content_accuracy.py` | 386 | No importers found. Functions: 1, Classes: 5, Lines: 386 |
| `customer_policy_read_engine.py` | 343 | No importers found. Functions: 1, Classes: 5, Lines: 343 |
| `decorator.py` | 192 | No importers found. Functions: 3, Classes: 0, Lines: 192 |
| `degraded_mode.py` | 217 | No importers found. Functions: 6, Classes: 2, Lines: 217 |
| `dsl_parser.py` | 523 | No importers found. Functions: 2, Classes: 5, Lines: 523 |
| `failure_mode_handler.py` | 273 | No importers found. Functions: 5, Classes: 3, Lines: 273 |
| `interpreter.py` | 562 | No importers found. Functions: 2, Classes: 9, Lines: 562 |
| `ir_builder.py` | 408 | No importers found. Functions: 0, Classes: 1, Lines: 408 |
| `ir_compiler.py` | 460 | No importers found. Functions: 2, Classes: 6, Lines: 460 |
| `kernel.py` | 623 | No importers found. Functions: 2, Classes: 4, Lines: 623 |
| `keys_shim.py` | 152 | No importers found. Functions: 2, Classes: 2, Lines: 152 |
| `kill_switch.py` | 223 | No importers found. Functions: 4, Classes: 3, Lines: 223 |
| `llm_policy_engine.py` | 442 | No importers found. Functions: 7, Classes: 2, Lines: 442 |
| `phase_status_invariants.py` | 360 | No importers found. Functions: 2, Classes: 4, Lines: 360 |
| `plan_generation_engine.py` | 257 | No importers found. Functions: 1, Classes: 3, Lines: 257 |
| `policies_limits_query_engine.py` | 318 | No importers found. Functions: 1, Classes: 6, Lines: 318 |
| `policies_proposals_query_engine.py` | 224 | No importers found. Functions: 1, Classes: 4, Lines: 224 |
| `policies_rules_query_engine.py` | 246 | No importers found. Functions: 1, Classes: 4, Lines: 246 |
| `policy_command.py` | 478 | No importers found. Functions: 14, Classes: 3, Lines: 478 |
| `policy_conflict_resolver.py` | 267 | No importers found. Functions: 4, Classes: 5, Lines: 267 |
| `prevention_engine.py` | 521 | No importers found. Functions: 1, Classes: 6, Lines: 521 |
| `prevention_hook.py` | 302 | No importers found. Functions: 3, Classes: 4, Lines: 302 |
| `protection_provider.py` | 388 | No importers found. Functions: 2, Classes: 2, Lines: 388 |
| `recovery_evaluation_engine.py` | 411 | No importers found. Functions: 2, Classes: 3, Lines: 411 |
| `runtime_command.py` | 561 | No importers found. Functions: 12, Classes: 4, Lines: 561 |
| `snapshot_engine.py` | 594 | No importers found. Functions: 7, Classes: 6, Lines: 594 |
| `validator.py` | 386 | No importers found. Functions: 2, Classes: 4, Lines: 386 |
| `visitors.py` | 307 | No importers found. Functions: 0, Classes: 4, Lines: 307 |
| `worker_execution_command.py` | 353 | No importers found. Functions: 5, Classes: 2, Lines: 353 |
