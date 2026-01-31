# Domain Authority Map

**Generator:** `scripts/ops/hoc_software_bible_generator.py`

Which domain owns which concept. Derived from canonical function
analysis — the domain with the highest-decision canonical function
for a given noun is the authority.

---

## Authority Table

| Concept | Authority Domain | Canonical Function | Decisions | Contested? |
|---------|------------------|--------------------|-----------|------------|
| _add | **incidents** | `incident_aggregator.IncidentAggregator._add_call_to_incident` | 3 | No |
| _approximate | **analytics** | `canary.CanaryRunner._approximate_kl_divergence` | 4 | No |
| _attempt | **integrations** | `webhook_adapter.WebhookAdapter._attempt_delivery` | 2 | No |
| _auto | **controls** | `circuit_breaker.CircuitBreaker._auto_recover` | 2 | No |
| _build | **integrations** | `smtp_adapter.SMTPAdapter._build_email` | 4 | Yes (integrations) |
| _calculate | **integrations** | `bridges.IncidentToCatalogBridge._calculate_fuzzy_confidence` | 5 | Yes (analytics) |
| _call | **policies** | `deterministic_engine.DeterministicEngine._call_function` | 2 | No |
| _check | **policies** | `engine.PolicyEngine._check_business_rules` | 5 | Yes (logs) |
| _coerce | **integrations** | `sql_gateway.SqlGatewayService._coerce_parameter` | 23 | No |
| _compare | **policies** | `interpreter.Interpreter._compare` | 7 | Yes (logs) |
| _compile | **policies** | `ir_compiler.IRCompiler._compile_actions` | 3 | No |
| _compute | **policies** | `recovery_matcher.RecoveryMatcher._compute_confidence` | 5 | Yes (analytics) |
| _create | **logs** | `mapper.SOC2ControlMapper._create_mapping` | 3 | No |
| _deliver | **integrations** | `webhook_adapter.WebhookAdapter._deliver_with_retry` | 3 | No |
| _derive | **analytics** | `cost_anomaly_detector.CostAnomalyDetector._derive_cause` | 9 | No |
| _detect | **policies** | `optimizer_conflict_resolver.ConflictResolver._detect_action_conflicts` | 6 | Yes (analytics) |
| _determine | **logs** | `mapper.SOC2ControlMapper._determine_compliance_status` | 9 | No |
| _dry | **controls** | `scoped_execution.ScopedExecutionContext._dry_run_validate` | 3 | No |
| _emit | **policies** | `ir_compiler.IRCompiler._emit_condition` | 3 | No |
| _escalate | **policies** | `recovery_matcher.RecoveryMatcher._escalate_to_llm` | 3 | No |
| _evaluate | **policies** | `prevention_engine.PreventionEngine._evaluate_step_inner` | 12 | Yes (policies) |
| _execute | **policies** | `deterministic_engine.DeterministicEngine._execute_instruction` | 15 | Yes (policies) |
| _extract | **policies** | `validator.PolicyValidator._extract_metrics` | 3 | No |
| _find | **integrations** | `bridges.IncidentToCatalogBridge._find_matching_pattern` | 4 | Yes (analytics) |
| _flush | **analytics** | `provenance.ProvenanceLogger._flush` | 3 | No |
| _fold | **policies** | `folds.ConstantFolder._fold_binary_op` | 3 | No |
| _generate | **integrations** | `bridges.PatternToRecoveryBridge._generate_recovery` | 2 | No |
| _get | **integrations** | `http_connector.HttpConnectorService._get_auth_headers` | 5 | Yes (controls) |
| _load | **analytics** | `canary.CanaryRunner._load_samples` | 2 | No |
| _maybe | **account** | `tenant_engine.TenantEngine._maybe_reset_daily_counter` | 2 | No |
| _parse | **policies** | `dsl_parser.Parser._parse_actions` | 2 | No |
| _perform | **integrations** | `cus_health_engine.CusHealthService._perform_health_check` | 14 | No |
| _redact | **logs** | `audit_evidence._redact_sensitive` | 4 | No |
| _resolve | **policies** | `arbitrator.PolicyArbitrator._resolve_action_conflict` | 4 | Yes (integrations) |
| _revert | **analytics** | `coordinator.CoordinationManager._revert_envelope` | 3 | No |
| _route | **policies** | `engine.PolicyEngine._route_to_governor` | 3 | No |
| _run | **analytics** | `canary.CanaryRunner._run_internal` | 9 | No |
| _semantic | **logs** | `replay_determinism.ReplayValidator._semantic_equivalent` | 3 | No |
| _send | **integrations** | `channel_engine.NotifyChannelService._send_via_channel` | 6 | No |
| _trigger | **integrations** | `dispatcher.IntegrationDispatcher._trigger_next_stage` | 2 | No |
| _trip | **controls** | `circuit_breaker.CircuitBreaker._trip` | 2 | No |
| _try | **controls** | `circuit_breaker_async._try_auto_recover` | 6 | No |
| _update | **integrations** | `dispatcher.IntegrationDispatcher._update_loop_status` | 8 | Yes (analytics) |
| _validate | **integrations** | `sql_gateway.SqlGatewayService._validate_parameters` | 4 | No |
| _verify | **incidents** | `llm_failure_engine.LLMFailureService._verify_no_contamination` | 3 | No |
| accept_invitation | **account** | `accounts_facade.AccountsFacade.accept_invitation` | 4 | No |
| activate_policy | **policies** | `engine.PolicyEngine.activate_policy_version` | 16 | No |
| active_cooldown | **policies** | `engine.PolicyEngine.get_active_cooldowns` | 2 | No |
| active_incident | **incidents** | `incidents_facade_driver.IncidentsFacadeDriver.fetch_active_incidents` | 7 | Yes (incidents) |
| activity | **integrations** | `customer_activity_adapter.CustomerActivityAdapter.get_activity` | 3 | No |
| alert | **controls** | `alert_fatigue.AlertFatigueController.check_alert` | 5 | No |
| all | **policies** | `protection_provider.MockAbuseProtectionProvider.check_all` | 4 | No |
| allowed | **analytics** | `coordinator.CoordinationManager.check_allowed` | 3 | No |
| and_create_incident | **incidents** | `incident_engine.IncidentEngine.check_and_create_incident` | 2 | No |
| anomaly | **integrations** | `cost_bridges_engine.CostLoopOrchestrator.process_anomaly` | 3 | No |
| anomaly_safe | **controls** | `cost_safety_rails.SafeCostLoopOrchestrator.process_anomaly_safe` | 5 | No |
| api_key | **account** | `tenant_engine.TenantEngine.create_api_key` | 3 | No |
| applicable_policy | **policies** | `scope_resolver.ScopeResolver.resolve_applicable_policies` | 6 | No |
| approve_candidate | **policies** | `recovery_matcher.RecoveryMatcher.approve_candidate` | 3 | No |
| audit_entry | **logs** | `logs_domain_store.LogsDomainStore.list_audit_entries` | 5 | No |
| audit_input_from_evidence | **logs** | `audit_engine.create_audit_input_from_evidence` | 2 | No |
| billing_invoice | **account** | `accounts_facade.AccountsFacade.get_billing_invoices` | 2 | No |
| billing_summary | **account** | `accounts_facade.AccountsFacade.get_billing_summary` | 2 | No |
| blocked_capability | **integrations** | `graduation_engine.CapabilityGates.get_blocked_capabilities` | 3 | No |
| budget_issue | **analytics** | `cost_anomaly_detector.CostAnomalyDetector.detect_budget_issues` | 4 | No |
| build_call | **logs** | `replay_determinism.ReplayContextBuilder.build_call_record` | 2 | No |
| burst | **policies** | `protection_provider.MockAbuseProtectionProvider.check_burst` | 2 | No |
| can_activate | **policies** | `policy_graph_engine.PolicyDependencyEngine.check_can_activate` | 2 | No |
| can_auto | **controls** | `cost_safety_rails.CostSafetyRails.can_auto_apply_policy` | 5 | No |
| can_execute | **controls** | `scoped_execution.BoundExecutionScope.can_execute` | 3 | No |
| cancel_override | **controls** | `override_driver.LimitOverrideService.cancel_override` | 2 | No |
| candidate | **policies** | `recovery_matcher.RecoveryMatcher.get_candidates` | 2 | No |
| capture_integrity | **logs** | `capture.capture_integrity_evidence` | 1 | No |
| category_learning | **incidents** | `postmortem_engine.PostMortemService.get_category_learnings` | 1 | No |
| certificate | **logs** | `certificate.CertificateService.export_certificate` | 3 | No |
| chain | **logs** | `evidence_facade.EvidenceFacade.verify_chain` | 3 | Yes (logs) |
| checkpoint | **integrations** | `dispatcher.IntegrationDispatcher.resolve_checkpoint` | 4 | No |
| clear_cooldown | **policies** | `engine.PolicyEngine.clear_cooldowns` | 2 | No |
| compare_trace | **logs** | `traces_models.compare_traces` | 7 | No |
| complete_run | **account** | `tenant_engine.TenantEngine.complete_run` | 3 | No |
| completed_run | **controls** | `threshold_engine.LLMRunEvaluator.evaluate_completed_run` | 4 | No |
| configure_channel | **integrations** | `channel_engine.NotifyChannelService.configure_channel` | 2 | No |
| conflict | **policies** | `policy_graph_engine.PolicyConflictEngine.detect_conflicts` | 4 | Yes (policies) |
| connector | **integrations** | `connectors_facade.ConnectorsFacade.update_connector` | 5 | No |
| control | **controls** | `controls_facade.ControlsFacade.update_control` | 4 | Yes (controls) |
| convert_brand | **policies** | `worker_execution_command.convert_brand_request` | 1 | No |
| convert_lesson | **policies** | `lessons_engine.LessonsLearnedEngine.convert_lesson_to_draft` | 2 | No |
| cost | **overview** | `overview_facade.OverviewFacade.get_costs` | 2 | No |
| cost_spike | **analytics** | `pattern_detection.detect_cost_spikes` | 6 | No |
| credential | **integrations** | `vault.HashiCorpVault.list_credentials` | 5 | Yes (integrations) |
| current_version | **policies** | `engine.PolicyEngine.get_current_version` | 2 | No |
| dataset | **analytics** | `datasets.DatasetValidator.validate_dataset` | 7 | No |
| decision | **overview** | `overview_facade.OverviewFacade.get_decisions` | 8 | No |
| defer_lesson | **policies** | `lessons_engine.LessonsLearnedEngine.defer_lesson` | 3 | No |
| dependency_dag | **policies** | `engine.PolicyEngine.validate_dependency_dag` | 8 | No |
| dependency_with_dag_check | **policies** | `engine.PolicyEngine.add_dependency_with_dag_check` | 7 | No |
| disable_control | **controls** | `controls_facade.ControlsFacade.disable_control` | 2 | No |
| dismiss_lesson | **policies** | `lessons_engine.LessonsLearnedEngine.dismiss_lesson` | 3 | No |
| effective_worker_config | **integrations** | `worker_registry_driver.WorkerRegistryService.get_effective_worker_config` | 4 | No |
| enable_channel | **integrations** | `channel_engine.NotifyChannelService.enable_channel` | 2 | No |
| enable_control | **controls** | `controls_facade.ControlsFacade.enable_control` | 2 | No |
| enable_kill | **policies** | `governance_facade.GovernanceFacade.enable_kill_switch` | 2 | No |
| enable_v2 | **controls** | `circuit_breaker_async.enable_v2` | 2 | No |
| enabled_channel | **integrations** | `channel_engine.NotifyChannelService.get_enabled_channels` | 4 | No |
| enforce_step | **logs** | `replay.ReplayEnforcer.enforce_step` | 8 | No |
| ensure_json | **integrations** | `loop_events.ensure_json_serializable` | 7 | No |
| estimate_step | **analytics** | `cost_model_engine.estimate_step_cost` | 12 | No |
| evidence_bundle | **incidents** | `export_bundle_driver.ExportBundleService.create_evidence_bundle` | 4 | No |
| evidence_report | **logs** | `evidence_report.generate_evidence_report` | 2 | No |
| execute_query | **policies** | `runtime_command.execute_query` | 5 | No |
| execute_with | **controls** | `scoped_execution.execute_with_scope` | 6 | No |
| execution_fidelity | **logs** | `audit_engine.AuditChecks.check_execution_fidelity` | 7 | No |
| execution_stat | **policies** | `sandbox_engine.SandboxService.get_execution_stats` | 3 | No |
| executive_debrief | **incidents** | `export_bundle_driver.ExportBundleService.create_executive_debrief` | 4 | No |
| exit_degraded | **policies** | `degraded_mode.exit_degraded_mode` | 1 | No |
| expire_envelope | **analytics** | `coordinator.CoordinationManager.expire_envelope` | 2 | No |
| failure_pattern | **analytics** | `pattern_detection.detect_failure_patterns` | 3 | No |
| file | **integrations** | `gcs_adapter.GCSAdapter.list_files` | 3 | No |
| freeze_key | **integrations** | `customer_keys_adapter.CustomerKeysAdapter.freeze_key` | 2 | Yes (api_keys) |
| function | **integrations** | `lambda_adapter.LambdaAdapter.list_functions` | 4 | Yes (integrations) |
| governance_config | **account** | `profile.validate_governance_config` | 5 | No |
| governance_state | **policies** | `governance_facade.GovernanceFacade.get_governance_state` | 3 | No |
| guardrail_detail | **integrations** | `customer_policies_adapter.CustomerPoliciesAdapter.get_guardrail_detail` | 3 | No |
| health | **integrations** | `cus_health_engine.CusHealthService.check_health` | 3 | No |
| health_preservation | **logs** | `audit_engine.AuditChecks.check_health_preservation` | 4 | No |
| health_summary | **integrations** | `cus_health_engine.CusHealthService.get_health_summary` | 2 | No |
| highlight | **overview** | `overview_facade.OverviewFacade.get_highlights` | 2 | No |
| historical_incident | **incidents** | `incidents_facade_driver.IncidentsFacadeDriver.fetch_historical_incidents` | 4 | Yes (incidents) |
| identity | **integrations** | `iam_engine.IAMService.resolve_identity` | 3 | No |
| incident | **incidents** | `incident_write_engine.IncidentWriteService.resolve_incident` | 2 | No |
| incident_for_failed_run | **incidents** | `incident_engine.IncidentEngine.create_incident_for_failed_run` | 3 | No |
| incident_for_run | **incidents** | `incident_engine.IncidentEngine.create_incident_for_run` | 6 | Yes (incidents) |
| incident_from_violation | **incidents** | `policy_violation_engine.PolicyViolationService.create_incident_from_violation` | 3 | No |
| invite_user | **account** | `accounts_facade.AccountsFacade.invite_user` | 2 | No |
| invoke_async | **policies** | `kernel.ExecutionKernel.invoke_async` | 2 | No |
| invoke_batch | **integrations** | `cloud_functions_adapter.CloudFunctionsAdapter.invoke_batch` | 2 | No |
| is_disabled | **controls** | `circuit_breaker.CircuitBreaker.is_disabled` | 5 | No |
| is_field | **logs** | `completeness_checker.EvidenceCompletenessChecker.is_field_present` | 3 | No |
| is_limit | **account** | `billing_provider.MockBillingProvider.is_limit_exceeded` | 1 | No |
| is_v2 | **controls** | `circuit_breaker_async.is_v2_disabled` | 9 | Yes (analytics) |
| killswitch_statu | **controls** | `killswitch_read_driver.KillswitchReadDriver.get_killswitch_status` | 1 | No |
| kpi_regression | **integrations** | `loop_events.RoutingAdjustment.check_kpi_regression` | 2 | No |
| lesson_from_near_threshold | **policies** | `lessons_engine.LessonsLearnedEngine.detect_lesson_from_near_threshold` | 2 | No |
| lesson_stat | **policies** | `lessons_engine.LessonsLearnedEngine.get_lesson_stats` | 2 | No |
| limit | **controls** | `limits_read_driver.LimitsReadDriver.fetch_limits` | 12 | No |
| live_run | **controls** | `threshold_engine.LLMRunEvaluator.evaluate_live_run` | 2 | No |
| llm_run | **logs** | `logs_domain_store.LogsDomainStore.list_llm_runs` | 7 | No |
| llm_run_record | **logs** | `logs_facade.LogsFacade.list_llm_run_records` | 7 | No |
| log | **integrations** | `customer_logs_adapter.CustomerLogsAdapter.get_log` | 2 | No |
| lookup_rule | **policies** | `symbol_table.SymbolTable.lookup_rule` | 5 | No |
| many | **integrations** | `s3_adapter.S3Adapter.delete_many` | 2 | No |
| map_incident | **logs** | `mapper.SOC2ControlMapper.map_incident_to_controls` | 1 | No |
| metadata | **integrations** | `vault.HashiCorpVault.get_metadata` | 2 | No |
| metric | **activity** | `activity_facade.ActivityFacade.get_metrics` | 2 | No |
| model_for_task | **policies** | `llm_policy_engine.get_model_for_task` | 4 | No |
| namespace | **integrations** | `weaviate_adapter.WeaviateAdapter.list_namespaces` | 3 | No |
| no_unauthorized_mutation | **logs** | `audit_engine.AuditChecks.check_no_unauthorized_mutations` | 2 | No |
| on_cost | **integrations** | `cost_bridges_engine.CostRoutingAdjuster.on_cost_policy_created` | 8 | No |
| or_create_incident | **incidents** | `incident_aggregator.IncidentAggregator.get_or_create_incident` | 2 | No |
| orphaned_run | **activity** | `orphan_recovery.recover_orphaned_runs` | 3 | No |
| otp | **account** | `email_verification.EmailVerificationService.verify_otp` | 3 | No |
| panel | **analytics** | `ai_console_panel_engine.AIConsolePanelEngine.evaluate_panel` | 4 | No |
| parse_action | **policies** | `compiler_parser.Parser.parse_action_block` | 2 | No |
| parse_policy | **policies** | `compiler_parser.Parser.parse_policy_body` | 5 | No |
| parse_rule | **policies** | `compiler_parser.Parser.parse_rule_body` | 3 | No |
| parse_value | **policies** | `compiler_parser.Parser.parse_value` | 9 | No |
| pending_halt | **controls** | `budget_enforcement_engine.BudgetEnforcementEngine.process_pending_halts` | 7 | No |
| persist_failure | **incidents** | `llm_failure_engine.LLMFailureService.persist_failure_and_mark_run` | 1 | No |
| persist_violation | **incidents** | `policy_violation_engine.PolicyViolationService.persist_violation_fact` | 4 | Yes (incidents) |
| policy | **policies** | `policy_command.evaluate_policy` | 3 | No |
| policy_conflict | **policies** | `policy_conflict_resolver.resolve_policy_conflict` | 5 | No |
| policy_evaluation_for_run | **incidents** | `policy_violation_engine.handle_policy_evaluation_for_run` | 3 | No |
| policy_evaluation_sync | **incidents** | `policy_violation_engine.create_policy_evaluation_sync` | 5 | No |
| policy_failure | **policies** | `failure_mode_handler.handle_policy_failure` | 3 | No |
| policy_request | **policies** | `policies_proposals_query_engine.ProposalsQueryEngine.list_policy_requests` | 3 | No |
| policy_rule | **policies** | `policy_rules_read_driver.PolicyRulesReadDriver.fetch_policy_rules` | 12 | Yes (policies) |
| policy_version | **policies** | `engine.PolicyEngine.create_policy_version` | 2 | No |
| pre_check | **policies** | `engine.PolicyEngine.pre_check` | 3 | No |
| predict_cost | **analytics** | `prediction.predict_cost_overrun` | 5 | No |
| predict_failure | **analytics** | `prediction.predict_failure_likelihood` | 6 | No |
| preference | **account** | `notifications_facade.NotificationsFacade.update_preferences` | 2 | No |
| prevention_for_graduation | **integrations** | `prevention_contract.validate_prevention_for_graduation` | 5 | No |
| priority | **policies** | `learning_proof_engine.CheckpointConfig.get_priority` | 2 | No |
| project_detail | **account** | `accounts_facade.AccountsFacade.get_project_detail` | 2 | No |
| proposal | **policies** | `proposals_read_driver.ProposalsReadDriver.fetch_proposals` | 4 | Yes (policies) |
| proposal_by_id | **policies** | `proposals_read_driver.ProposalsReadDriver.fetch_proposal_by_id` | 2 | No |
| proposal_eligibility | **policies** | `policy_proposal_engine.PolicyProposalEngine.check_proposal_eligibility` | 3 | No |
| provenance | **analytics** | `provenance_async.query_provenance` | 7 | No |
| rate_limit | **policies** | `protection_provider.MockAbuseProtectionProvider.check_rate_limit` | 2 | No |
| reactivate_deferred | **policies** | `lessons_engine.LessonsLearnedEngine.reactivate_deferred_lesson` | 3 | No |
| reactivate_expired | **policies** | `lessons_engine.LessonsLearnedEngine.reactivate_expired_deferred_lessons` | 3 | No |
| read_operator | **policies** | `tokenizer.Tokenizer.read_operator` | 5 | No |
| read_string | **policies** | `tokenizer.Tokenizer.read_string` | 2 | No |
| record_alert | **controls** | `alert_fatigue.AlertFatigueController.record_alert_sent` | 2 | No |
| record_outcome | **policies** | `learning_proof_engine.PatternCalibration.record_outcome` | 3 | No |
| record_step | **logs** | `pg_store.PostgresTraceStore.record_step` | 3 | No |
| recovery | **integrations** | `cost_bridges_engine.CostRecoveryGenerator.generate_recovery` | 2 | No |
| redact_dict | **logs** | `redact.redact_dict` | 5 | No |
| redact_list | **logs** | `redact.redact_list` | 4 | No |
| redact_trace | **logs** | `redact.redact_trace_data` | 8 | No |
| register_source | **integrations** | `datasources_facade.DataSourcesFacade.register_source` | 3 | No |
| regret | **policies** | `learning_proof_engine.PolicyRegretTracker.add_regret` | 2 | No |
| render_soc2 | **logs** | `pdf_renderer.PDFRenderer.render_soc2_pdf` | 1 | No |
| replay | **logs** | `replay_determinism.ReplayValidator.validate_replay` | 4 | No |
| report | **analytics** | `divergence.DivergenceAnalyzer.generate_report` | 3 | No |
| report_drift | **controls** | `circuit_breaker.CircuitBreaker.report_drift` | 3 | No |
| request_override | **controls** | `override_driver.LimitOverrideService.request_override` | 3 | No |
| resolved_incident | **incidents** | `incidents_facade_driver.IncidentsFacadeDriver.fetch_resolved_incidents` | 7 | Yes (incidents) |
| retry_failed | **integrations** | `dispatcher.IntegrationDispatcher.retry_failed_stage` | 2 | No |
| revert_loop | **integrations** | `dispatcher.IntegrationDispatcher.revert_loop` | 3 | No |
| review_proposal | **policies** | `policy_proposal_engine.PolicyProposalEngine.review_proposal` | 5 | No |
| risk_ceiling | **policies** | `engine.PolicyEngine.get_risk_ceilings` | 2 | No |
| rollback_availability | **logs** | `audit_engine.AuditChecks.check_rollback_availability` | 4 | No |
| rollback_to | **policies** | `engine.PolicyEngine.rollback_to_version` | 2 | No |
| rotatable_credential | **integrations** | `service.CredentialService.get_rotatable_credentials` | 2 | No |
| run | **activity** | `activity_facade.ActivityFacade.get_runs` | 15 | No |
| run_anomaly | **analytics** | `cost_anomaly_detector.run_anomaly_detection_with_governance` | 2 | No |
| run_quota | **account** | `tenant_engine.TenantEngine.check_run_quota` | 4 | No |
| safety_limit | **policies** | `llm_policy_engine.check_safety_limits` | 4 | No |
| safety_rule | **policies** | `engine.PolicyEngine.update_safety_rule` | 3 | Yes (policies) |
| scope_compliance | **logs** | `audit_engine.AuditChecks.check_scope_compliance` | 2 | No |
| send_batch | **integrations** | `slack_adapter.SlackAdapter.send_batch` | 2 | No |
| send_otp | **account** | `email_verification.EmailVerificationService.send_otp` | 1 | No |
| send_thread | **integrations** | `slack_adapter.SlackAdapter.send_thread_reply` | 2 | No |
| set_mode | **policies** | `governance_facade.GovernanceFacade.set_mode` | 6 | No |
| should_allow | **logs** | `completeness_checker.EvidenceCompletenessChecker.should_allow_export` | 2 | No |
| should_auto | **policies** | `learning_proof_engine.CheckpointConfig.should_auto_dismiss` | 2 | No |
| should_escalate | **incidents** | `incident_severity_engine.IncidentSeverityEngine.should_escalate` | 2 | No |
| should_evaluate | **policies** | `binding_moment_enforcer.should_evaluate_policy` | 6 | No |
| signal | **activity** | `activity_facade.ActivityFacade.get_signals` | 2 | No |
| snapshot | **analytics** | `cost_snapshots.SnapshotAnomalyDetector.evaluate_snapshot` | 6 | No |
| source | **integrations** | `datasources_facade.DataSourcesFacade.update_source` | 3 | Yes (integrations) |
| stale_incident | **incidents** | `incident_aggregator.IncidentAggregator.resolve_stale_incidents` | 2 | No |
| start_trace | **logs** | `trace_facade.TraceFacade.start_trace` | 1 | No |
| stat | **integrations** | `weaviate_adapter.WeaviateAdapter.get_stats` | 3 | No |
| statistic | **policies** | `snapshot_engine.PolicySnapshotRegistry.get_statistics` | 6 | Yes (integrations) |
| statu | **controls** | `controls_facade.ControlsFacade.get_status` | 5 | No |
| suggest_hybrid | **policies** | `recovery_matcher.RecoveryMatcher.suggest_hybrid` | 4 | No |
| sustained_drift | **analytics** | `cost_anomaly_detector.CostAnomalyDetector.detect_sustained_drift` | 3 | No |
| system_record | **logs** | `logs_domain_store.LogsDomainStore.list_system_records` | 6 | No |
| temporal_policy | **policies** | `policy_engine_driver.PolicyEngineDriver.fetch_temporal_policies` | 2 | No |
| temporal_storage_stat | **policies** | `engine.PolicyEngine.get_temporal_storage_stats` | 2 | No |
| temporal_utilization | **policies** | `engine.PolicyEngine.get_temporal_utilization` | 2 | No |
| test_connector | **integrations** | `connectors_facade.ConnectorsFacade.test_connector` | 4 | No |
| threshold_limit_by_scope | **controls** | `threshold_driver.ThresholdDriver.get_threshold_limit_by_scope` | 2 | No |
| threshold_signal | **activity** | `activity_facade.ActivityFacade.get_threshold_signals` | 2 | No |
| to_console | **integrations** | `loop_events.LoopStatus.to_console_display` | 3 | No |
| token_quota | **account** | `tenant_engine.TenantEngine.check_token_quota` | 2 | No |
| tool_invocation | **policies** | `policy_mapper.MCPPolicyMapper.check_tool_invocation` | 8 | No |
| topological_evaluation_order | **policies** | `engine.PolicyEngine.get_topological_evaluation_order` | 5 | No |
| trace | **logs** | `pg_store.PostgresTraceStore.search_traces` | 8 | Yes (logs) |
| trace_by_root_hash | **logs** | `pg_store.PostgresTraceStore.get_trace_by_root_hash` | 2 | No |
| try_fold | **policies** | `folds.ConstantFolder.try_fold` | 4 | No |
| unacknowledged_feedback | **policies** | `policy_proposal_read_driver.PolicyProposalReadDriver.fetch_unacknowledged_feedback` | 2 | No |
| unfreeze_key | **integrations** | `customer_keys_adapter.CustomerKeysAdapter.unfreeze_key` | 2 | No |
| unlocked_capability | **integrations** | `graduation_engine.CapabilityGates.get_unlocked_capabilities` | 3 | No |
| usage | **policies** | `limits_facade.LimitsFacade.get_usage` | 3 | No |
| usage_statistic | **analytics** | `analytics_facade.AnalyticsFacade.get_usage_statistics` | 11 | No |
| usage_summary | **account** | `tenant_engine.TenantEngine.get_usage_summary` | 3 | No |
| user | **account** | `accounts_facade.AccountsFacade.remove_user` | 4 | Yes (account) |
| user_profile | **account** | `accounts_facade_driver.AccountsFacadeDriver.update_user_profile` | 3 | No |
| user_role | **account** | `accounts_facade.AccountsFacade.update_user_role` | 4 | No |
| variable | **policies** | `deterministic_engine.ExecutionContext.get_variable` | 4 | No |
| violation | **policies** | `policy_engine_driver.PolicyEngineDriver.fetch_violations` | 5 | Yes (policies) |
| visit_action | **policies** | `ir_builder.IRBuilder.visit_action_block` | 2 | No |
| visit_binary | **policies** | `visitors.BaseVisitor.visit_binary_op` | 2 | No |
| visit_condition | **policies** | `visitors.BaseVisitor.visit_condition_block` | 2 | No |
| visit_func | **policies** | `ir_builder.IRBuilder.visit_func_call` | 2 | No |
| visit_rule | **policies** | `ir_builder.IRBuilder.visit_rule_decl` | 1 | No |
| with_context | **policies** | `engine.PolicyEngine.evaluate_with_context` | 8 | No |
| worker | **integrations** | `worker_registry_driver.WorkerRegistryService.list_workers` | 2 | No |
| worker_detail | **integrations** | `worker_registry_driver.WorkerRegistryService.get_worker_details` | 4 | No |
| workers_for_tenant | **integrations** | `worker_registry_driver.WorkerRegistryService.get_workers_for_tenant` | 2 | No |
| write_provenance | **analytics** | `provenance_async.write_provenance_batch` | 4 | Yes (analytics) |

## Contested Concepts

These nouns have canonical functions in multiple domains.
The domain with the most decision logic is listed as authority.

- **_build**: integrations (canonical) vs integrations — winner has 4 decisions
- **_calculate**: integrations (canonical) vs analytics — winner has 5 decisions
- **_check**: policies (canonical) vs logs — winner has 5 decisions
- **_compare**: policies (canonical) vs logs — winner has 7 decisions
- **_compute**: policies (canonical) vs analytics — winner has 5 decisions
- **_detect**: policies (canonical) vs analytics — winner has 6 decisions
- **_evaluate**: policies (canonical) vs policies — winner has 12 decisions
- **_execute**: policies (canonical) vs policies — winner has 15 decisions
- **_find**: integrations (canonical) vs analytics — winner has 4 decisions
- **_get**: integrations (canonical) vs controls — winner has 5 decisions
- **_resolve**: policies (canonical) vs integrations — winner has 4 decisions
- **_update**: integrations (canonical) vs analytics — winner has 8 decisions
- **active_incident**: incidents (canonical) vs incidents — winner has 7 decisions
- **chain**: logs (canonical) vs logs — winner has 3 decisions
- **conflict**: policies (canonical) vs policies — winner has 4 decisions
- **control**: controls (canonical) vs controls — winner has 4 decisions
- **credential**: integrations (canonical) vs integrations — winner has 5 decisions
- **freeze_key**: integrations (canonical) vs api_keys — winner has 2 decisions
- **function**: integrations (canonical) vs integrations — winner has 4 decisions
- **historical_incident**: incidents (canonical) vs incidents — winner has 4 decisions
- **incident_for_run**: incidents (canonical) vs incidents — winner has 6 decisions
- **is_v2**: controls (canonical) vs analytics — winner has 9 decisions
- **persist_violation**: incidents (canonical) vs incidents — winner has 4 decisions
- **policy_rule**: policies (canonical) vs policies — winner has 12 decisions
- **proposal**: policies (canonical) vs policies — winner has 4 decisions
- **resolved_incident**: incidents (canonical) vs incidents — winner has 7 decisions
- **safety_rule**: policies (canonical) vs policies — winner has 3 decisions
- **source**: integrations (canonical) vs integrations — winner has 3 decisions
- **statistic**: policies (canonical) vs integrations — winner has 6 decisions
- **trace**: logs (canonical) vs logs — winner has 8 decisions
- **user**: account (canonical) vs account — winner has 4 decisions
- **violation**: policies (canonical) vs policies — winner has 5 decisions
- **write_provenance**: analytics (canonical) vs analytics — winner has 4 decisions

## By Domain

### Account
Owns 19 concepts: _maybe, accept_invitation, api_key, billing_invoice, billing_summary, complete_run, governance_config, invite_user, is_limit, otp, preference, project_detail, run_quota, send_otp, token_quota, usage_summary, user, user_profile, user_role

### Activity
Owns 5 concepts: metric, orphaned_run, run, signal, threshold_signal

### Analytics
Owns 23 concepts: _approximate, _derive, _flush, _load, _revert, _run, allowed, budget_issue, cost_spike, dataset, estimate_step, expire_envelope, failure_pattern, panel, predict_cost, predict_failure, provenance, report, run_anomaly, snapshot
  ...and 3 more

### Controls
Owns 26 concepts: _auto, _dry, _trip, _try, alert, anomaly_safe, can_auto, can_execute, cancel_override, completed_run, control, disable_control, enable_control, enable_v2, execute_with, is_disabled, is_v2, killswitch_statu, limit, live_run
  ...and 6 more

### Incidents
Owns 20 concepts: _add, _verify, active_incident, and_create_incident, category_learning, evidence_bundle, executive_debrief, historical_incident, incident, incident_for_failed_run, incident_for_run, incident_from_violation, or_create_incident, persist_failure, persist_violation, policy_evaluation_for_run, policy_evaluation_sync, resolved_incident, should_escalate, stale_incident

### Integrations
Owns 55 concepts: _attempt, _build, _calculate, _coerce, _deliver, _find, _generate, _get, _perform, _send, _trigger, _update, _validate, activity, anomaly, blocked_capability, checkpoint, configure_channel, connector, credential
  ...and 35 more

### Logs
Owns 33 concepts: _create, _determine, _redact, _semantic, audit_entry, audit_input_from_evidence, build_call, capture_integrity, certificate, chain, compare_trace, enforce_step, evidence_report, execution_fidelity, health_preservation, is_field, llm_run, llm_run_record, map_incident, no_unauthorized_mutation
  ...and 13 more

### Overview
Owns 3 concepts: cost, decision, highlight

### Policies
Owns 90 concepts: _call, _check, _compare, _compile, _compute, _detect, _emit, _escalate, _evaluate, _execute, _extract, _fold, _parse, _resolve, _route, activate_policy, active_cooldown, all, applicable_policy, approve_candidate
  ...and 70 more
