# Logs — Domain Capability

**Domain:** logs  
**Total functions:** 428  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-08)

- L2 purity preserved: logs L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain logs --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `python3 scripts/ops/l5_spine_pairing_gap_detector.py --domain logs --json` reports 0 orphaned L5 entry modules (`total_l5_engines: 6`, `wired_via_l4: 6`, `direct_l2_to_l5: 0`).
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.
- Trace API endpoints route through L4 `logs.traces_api` → L5 `trace_api_engine` (no L2→L6 trace store imports).

**Note (Scope):** The CRM governance auditor lives in `backend/app/hoc/cus/account/logs/CRM/audit/audit_engine.py` and is invoked by L4 operation `governance.audit_job`. It is not part of the LLM-runs logs retrieval APIs.

## 1. Domain Purpose

Structured logging and log analysis — log ingestion, search, filtering, alerting, and retention management.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `AuditChecks.check_execution_fidelity` | audit_engine | Yes | L4:__init__ | db_write |
| `AuditChecks.check_health_preservation` | audit_engine | Yes | L4:__init__ | pure |
| `AuditChecks.check_no_unauthorized_mutations` | audit_engine | Yes | L4:__init__ | pure |
| `AuditChecks.check_rollback_availability` | audit_engine | Yes | L4:__init__ | pure |
| `AuditChecks.check_scope_compliance` | audit_engine | Yes | L4:__init__ | db_write |
| `AuditChecks.check_signal_consistency` | audit_engine | Yes | L4:__init__ | pure |
| `AuditChecks.check_timing_compliance` | audit_engine | Yes | L4:__init__ | pure |
| `AuditService.audit` | audit_engine | Yes | L4:__init__ | pure |
| `AuditService.version` | audit_engine | Yes | L4:__init__ | pure |
| `CallRecord.to_dict` | replay_determinism | Yes | L2:guard | pure |
| `Certificate.from_dict` | certificate | Yes | L4:logs_handler | pure |
| `Certificate.to_dict` | certificate | Yes | L4:logs_handler | pure |
| `Certificate.to_json` | certificate | Yes | L4:logs_handler | pure |
| `CertificatePayload.canonical_json` | certificate | Yes | L4:logs_handler | pure |
| `CertificatePayload.to_dict` | certificate | Yes | L4:logs_handler | pure |
| `CertificateService.create_policy_audit_certificate` | certificate | Yes | L4:logs_handler | pure |
| `CertificateService.create_replay_certificate` | certificate | Yes | L4:logs_handler | pure |
| `CertificateService.export_certificate` | certificate | Yes | L4:logs_handler | pure |
| `CertificateService.verify_certificate` | certificate | Yes | L4:logs_handler | pure |
| `EvidenceChain.to_dict` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceExport.to_dict` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.add_evidence` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.create_chain` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.create_export` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.get_chain` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.get_export` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.list_chains` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.list_exports` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceFacade.verify_chain` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceLink.to_dict` | evidence_facade | Yes | L4:logs_handler | pure |
| `EvidenceReportGenerator.generate` | evidence_report | Yes | L4:logs_handler | file_io |
| `LogsFacade.get_audit_access` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_audit_authorization` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_audit_entry` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_audit_exports` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_audit_identity` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_audit_integrity` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_llm_run_envelope` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_llm_run_export` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_llm_run_governance` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_llm_run_replay` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_llm_run_trace` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_system_audit` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_system_events` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_system_replay` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_system_snapshot` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.get_system_telemetry` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.list_audit_entries` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.list_llm_run_records` | logs_facade | Yes | L4:logs_handler | pure |
| `LogsFacade.list_system_records` | logs_facade | Yes | L4:logs_handler | pure |
| `ModelVersion.from_dict` | replay_determinism | Yes | L2:guard | pure |
| `ModelVersion.to_dict` | replay_determinism | Yes | L2:guard | pure |
| `PDFRenderer.render_evidence_pdf` | pdf_renderer | Yes | L4:logs_handler | pure |
| `PDFRenderer.render_executive_debrief_pdf` | pdf_renderer | Yes | L4:logs_handler | pure |
| `PDFRenderer.render_soc2_pdf` | pdf_renderer | Yes | L4:logs_handler | pure |
| `PolicyDecision.to_dict` | replay_determinism | Yes | L2:guard | pure |
| `ReplayContextBuilder.build_call_record` | replay_determinism | Yes | L2:guard | pure |
| `ReplayResult.to_dict` | replay_determinism | Yes | L2:guard | pure |
| `ReplayValidator.hash_content` | replay_determinism | Yes | L2:guard | pure |
| `ReplayValidator.validate_replay` | replay_determinism | Yes | L2:guard | pure |
| `RolloutGate.get_rollout_status` | audit_engine | Yes | L4:__init__ | pure |
| `RolloutGate.is_rollout_authorized` | audit_engine | Yes | L4:__init__ | pure |
| `SOC2ControlMapper.get_all_applicable_controls` | mapper | Yes | L4:control_registry | pure |
| `SOC2ControlMapper.map_incident_to_controls` | mapper | Yes | L4:control_registry | pure |
| `TraceFacade.add_step` | trace_facade | Yes | L4:transaction_coordinator | pure |
| `TraceFacade.complete_trace` | trace_facade | Yes | L4:transaction_coordinator | pure |
| `TraceFacade.start_trace` | trace_facade | Yes | L4:transaction_coordinator | pure |
| `VerificationResult.to_dict` | evidence_facade | Yes | L4:logs_handler | pure |
| `add_redaction_pattern` | redact | No (gap) | L2:traces | pure |
| `add_sensitive_field` | redact | No (gap) | L2:traces | db_write |
| `audit_result_to_record` | audit_engine | Yes | L4:__init__ | pure |
| `create_audit_input_from_evidence` | audit_engine | Yes | L4:__init__ | pure |
| `generate_evidence_report` | evidence_report | Yes | L4:logs_handler | pure |
| `get_control_mappings_for_incident` | mapper | Yes | L4:control_registry | pure |
| `get_evidence_facade` | evidence_facade | Yes | L4:logs_handler | pure |
| `get_logs_facade` | logs_facade | Yes | L4:logs_handler | pure |
| `get_pdf_renderer` | pdf_renderer | Yes | L4:logs_handler | pure |
| `get_trace_facade` | trace_facade | Yes | L4:transaction_coordinator | pure |
| `is_sensitive_field` | redact | No (gap) | L2:traces | pure |
| `redact_dict` | redact | No (gap) | L2:traces | pure |
| `redact_json_string` | redact | No (gap) | L2:traces | pure |
| `redact_list` | redact | No (gap) | L2:traces | pure |
| `redact_string_value` | redact | No (gap) | L2:traces | pure |
| `redact_trace_data` | redact | Yes | L4:logs.traces_api | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `AuditReconciler.check_deadline_violations` | audit_reconciler | medium |
| `EvidenceCompletenessChecker.check` | completeness_checker | medium |
| `EvidenceCompletenessChecker.should_allow_export` | completeness_checker | medium |
| `MCPAuditEmitter.emit_tool_allowed` | audit_evidence | medium |
| `MCPAuditEvent.verify_integrity` | audit_evidence | medium |
| `TracesMetrics.record_idempotency_check` | traces_metrics | medium |
| `TracesMetrics.record_parity_check` | traces_metrics | medium |
| `TracesMetrics.record_replay_enforcement` | traces_metrics | medium |
| `check_evidence_completeness` | completeness_checker | medium |
| `instrument_parity_check` | traces_metrics | medium |
| `instrument_replay_check` | traces_metrics | medium |

### Coordinators

| Function | File | Confidence |
|----------|------|------------|
| `AuditLedgerService.incident_resolved` | audit_ledger_service | medium |
| `AuditReconciler.reconcile` | audit_reconciler | medium |
| `get_audit_reconciler` | audit_reconciler | medium |

### Helpers

_154 internal helper functions._

- **audit_engine:** `AuditChecks._is_health_degraded`, `AuditService.__init__`, `AuditService._determine_verdict`, `AuditService._run_all_checks`
- **audit_evidence:** `MCPAuditEmitter.__init__`, `MCPAuditEmitter._emit`, `MCPAuditEmitter._generate_event_id`, `MCPAuditEmitter._get_publisher`, `MCPAuditEvent.__post_init__`, `MCPAuditEvent._compute_integrity_hash`, `MCPAuditEvent.to_dict`, `_contains_sensitive`, `_hash_value`, `_redact_sensitive`
- **audit_ledger_service:** `AuditLedgerService.__init__`, `AuditLedgerService._emit`
- **audit_ledger_service_async:** `AuditLedgerServiceAsync.__init__`, `AuditLedgerServiceAsync._emit`
- **audit_reconciler:** `AuditReconciler.__init__`, `AuditReconciler._record_metrics`
- **capture:** `EvidenceContextError.__init__`, `_assert_context_exists`, `_hash_content`, `_record_capture_failure`
- **certificate:** `CertificateService.__init__`, `CertificateService._sign`, `CertificateService._verify_signature`
- **completeness_checker:** `CompletenessCheckResponse.to_dict`, `EvidenceCompletenessChecker.__init__`, `EvidenceCompletenessChecker.from_governance_config`, `EvidenceCompletenessError.__init__`, `EvidenceCompletenessError.to_dict`
- **evidence_facade:** `EvidenceFacade.__init__`, `EvidenceFacade._create_link`, `EvidenceFacade._hash_data`
- **evidence_report:** `EvidenceReportGenerator.__init__`, `EvidenceReportGenerator._add_footer`, `EvidenceReportGenerator._build_certificate_section`, `EvidenceReportGenerator._build_cover_page`, `EvidenceReportGenerator._build_decision_timeline`, `EvidenceReportGenerator._build_executive_summary`, `EvidenceReportGenerator._build_factual_reconstruction`, `EvidenceReportGenerator._build_incident_snapshot`, `EvidenceReportGenerator._build_legal_attestation`, `EvidenceReportGenerator._build_policy_evaluation`
  _...and 6 more_
- **export_bundle_store:** `ExportBundleStore.__init__`
- **idempotency:** `InMemoryIdempotencyStore.__init__`, `InMemoryIdempotencyStore._make_key`, `RedisIdempotencyStore.__init__`, `RedisIdempotencyStore._ensure_script_loaded`, `RedisIdempotencyStore._make_key`, `_load_lua_script`
- **integrity:** `IntegrityAssembler.__init__`, `IntegrityAssembler._count_evidence`, `IntegrityAssembler._gather_failures`, `IntegrityAssembler._resolve_superseded`, `IntegrityAssembler._string_to_class`, `IntegrityAssembler._table_to_class`, `IntegrityEvaluator._build_explanation`, `IntegrityEvaluator._compute_grade`, `IntegrityEvaluator._find_failure`
- **job_execution:** `JobAuditEmitter.__init__`, `JobAuditEmitter._emit`, `JobAuditEmitter._generate_event_id`, `JobAuditEmitter._get_publisher`, `JobAuditEvent.__post_init__`, `JobAuditEvent._compute_integrity_hash`, `JobProgressTracker.__init__`, `JobProgressTracker._calculate_eta`, `JobProgressTracker._emit_progress`, `JobProgressTracker._get_publisher`
  _...and 2 more_
- **logs_domain_store:** `LogsDomainStore._to_audit_snapshot`, `LogsDomainStore._to_export_snapshot`, `LogsDomainStore._to_llm_run_snapshot`, `LogsDomainStore._to_system_record_snapshot`
- **logs_facade:** `LogsFacade.__init__`, `LogsFacade._snapshot_to_record_result`
- **logs_read_engine:** `LogsReadService.__init__`, `LogsReadService._get_store`
- **mapper:** `SOC2ControlMapper.__init__`, `SOC2ControlMapper._create_mapping`, `SOC2ControlMapper._determine_compliance_status`
- **panel_consistency_checker:** `PanelConsistencyChecker.__init__`, `PanelConsistencyChecker._check_rule`, `PanelConsistencyChecker._default_rules`, `PanelConsistencyChecker._eval_expr`, `PanelConsistencyChecker._evaluate_condition`
- **panel_response_assembler:** `PanelResponseAssembler.__init__`, `PanelResponseAssembler._aggregate_verification`, `PanelResponseAssembler._determine_panel_authority`, `PanelResponseAssembler._determine_panel_state`, `PanelResponseAssembler._slot_to_dict`
- **pdf_renderer:** `PDFRenderer.__init__`, `PDFRenderer._build_attestation`, `PDFRenderer._build_control_mappings`, `PDFRenderer._build_evidence_cover`, `PDFRenderer._build_evidence_summary`, `PDFRenderer._build_exec_cover`, `PDFRenderer._build_exec_metrics`, `PDFRenderer._build_exec_summary`, `PDFRenderer._build_integrity_section`, `PDFRenderer._build_policy_section`
  _...and 4 more_
- **pg_store:** `PostgresTraceStore.__init__`, `PostgresTraceStore._get_pool`, `_status_to_level`
- **replay:** `IdempotencyViolationError.__init__`, `InMemoryIdempotencyStore.__init__`, `InMemoryIdempotencyStore._make_key`, `RedisIdempotencyStore.__init__`, `RedisIdempotencyStore._get_client`, `RedisIdempotencyStore._make_key`, `ReplayEnforcer.__init__`, `ReplayMismatchError.__init__`
- **replay_determinism:** `ReplayContextBuilder.__init__`, `ReplayValidator.__init__`, `ReplayValidator._compare_policies`, `ReplayValidator._detect_model_drift`, `ReplayValidator._level_meets_requirement`, `ReplayValidator._semantic_equivalent`
- **trace_facade:** `TraceFacade.__init__`, `TraceFacade._emit_ack`, `TraceFacade._store`
- **traces_metrics:** `TracesMetrics.__init__`
- **traces_models:** `ParityResult.to_dict`, `TraceRecord.determinism_signature`, `TraceRecord.failure_count`, `TraceRecord.from_dict`, `TraceRecord.success_count`, `TraceRecord.to_dict`, `TraceRecord.to_summary`, `TraceRecord.total_cost_cents`, `TraceRecord.total_duration_ms`, `TraceStep.determinism_hash`
  _...and 5 more_
- **traces_store:** `InMemoryTraceStore.__init__`, `SQLiteTraceStore.__init__`, `SQLiteTraceStore._get_conn`, `SQLiteTraceStore._init_db`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `AuditLedgerServiceAsync.limit_breached` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.limit_created` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.limit_updated` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.policy_proposal_approved` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.policy_proposal_rejected` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.policy_rule_created` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.policy_rule_modified` | audit_ledger_service_async | pure |
| `AuditLedgerServiceAsync.policy_rule_retired` | audit_ledger_service_async | pure |
| `CaptureFailure.to_dict` | integrity | pure |
| `ExportBundleStore.get_incident` | export_bundle_store | pure |
| `ExportBundleStore.get_run_by_run_id` | export_bundle_store | pure |
| `ExportBundleStore.get_trace_steps` | export_bundle_store | pure |
| `ExportBundleStore.get_trace_summary` | export_bundle_store | pure |
| `ExportBundleStore.trace_store` | export_bundle_store | pure |
| `IdempotencyResponse.is_conflict` | idempotency | pure |
| `IdempotencyResponse.is_duplicate` | idempotency | pure |
| `IdempotencyResponse.is_new` | idempotency | pure |
| `IdempotencyStore.delete` | replay | pure |
| `IdempotencyStore.get` | replay | pure |
| `IdempotencyStore.set` | replay | pure |
| `InMemoryIdempotencyStore.check` | idempotency | pure |
| `InMemoryIdempotencyStore.clear` | replay | pure |
| `InMemoryIdempotencyStore.delete` | idempotency | pure |
| `InMemoryIdempotencyStore.delete` | replay | pure |
| `InMemoryIdempotencyStore.get` | replay | pure |
| `InMemoryIdempotencyStore.get_status` | idempotency | pure |
| `InMemoryIdempotencyStore.mark_completed` | idempotency | pure |
| `InMemoryIdempotencyStore.mark_failed` | idempotency | pure |
| `InMemoryIdempotencyStore.set` | replay | pure |
| `InMemoryTraceStore.complete_trace` | traces_store | pure |
| `InMemoryTraceStore.delete_trace` | traces_store | pure |
| `InMemoryTraceStore.get_trace` | traces_store | pure |
| `InMemoryTraceStore.list_traces` | traces_store | pure |
| `InMemoryTraceStore.record_step` | traces_store | pure |
| `InMemoryTraceStore.start_trace` | traces_store | pure |
| `IntegrityAssembler.gather` | integrity | pure |
| `IntegrityEvaluation.integrity_status` | integrity | pure |
| `IntegrityEvaluator.evaluate` | integrity | pure |
| `IntegrityFacts.has_capture_failures` | integrity | pure |
| `IntegrityFacts.has_required_evidence` | integrity | pure |
| `IntegrityFacts.unresolved_failures` | integrity | pure |
| `JobAuditEmitter.emit_completed` | job_execution | pure |
| `JobAuditEmitter.emit_created` | job_execution | pure |
| `JobAuditEmitter.emit_failed` | job_execution | pure |
| `JobAuditEmitter.emit_retried` | job_execution | pure |
| `JobAuditEmitter.emit_started` | job_execution | pure |
| `JobAuditEvent.to_dict` | job_execution | pure |
| `JobAuditEvent.verify_integrity` | job_execution | pure |
| `JobProgressTracker.complete` | job_execution | pure |
| `JobProgressTracker.fail` | job_execution | pure |
| `JobProgressTracker.get_progress` | job_execution | pure |
| `JobProgressTracker.register_callback` | job_execution | pure |
| `JobProgressTracker.start` | job_execution | pure |
| `JobProgressTracker.update` | job_execution | pure |
| `JobRetryManager.calculate_delay` | job_execution | pure |
| `JobRetryManager.clear_history` | job_execution | pure |
| `JobRetryManager.get_retry_history` | job_execution | pure |
| `JobRetryManager.record_retry` | job_execution | pure |
| `JobRetryManager.should_retry` | job_execution | pure |
| `LogsDomainStore.get_audit_entry` | logs_domain_store | db_write |
| `LogsDomainStore.get_governance_events` | logs_domain_store | db_write |
| `LogsDomainStore.get_llm_run` | logs_domain_store | db_write |
| `LogsDomainStore.get_replay_window_events` | logs_domain_store | db_write |
| `LogsDomainStore.get_system_record_by_correlation` | logs_domain_store | db_write |
| `LogsDomainStore.get_system_records_in_window` | logs_domain_store | db_write |
| `LogsDomainStore.get_trace_id_for_run` | logs_domain_store | db_write |
| `LogsDomainStore.get_trace_steps` | logs_domain_store | db_write |
| `LogsDomainStore.list_audit_entries` | logs_domain_store | db_write |
| `LogsDomainStore.list_llm_runs` | logs_domain_store | db_write |
| `LogsDomainStore.list_log_exports` | logs_domain_store | db_write |
| `LogsDomainStore.list_system_records` | logs_domain_store | db_write |
| `PanelConsistencyChecker.check` | panel_consistency_checker | pure |
| `PostgresTraceStore.check_idempotency_key` | pg_store | pure |
| `PostgresTraceStore.cleanup_old_traces` | pg_store | pure |
| `PostgresTraceStore.close` | pg_store | pure |
| `PostgresTraceStore.complete_trace` | pg_store | pure |
| `PostgresTraceStore.delete_trace` | pg_store | pure |
| `PostgresTraceStore.get_trace` | pg_store | pure |
| `PostgresTraceStore.get_trace_by_root_hash` | pg_store | pure |
| `PostgresTraceStore.get_trace_count` | pg_store | pure |
| `PostgresTraceStore.list_traces` | pg_store | pure |
| `PostgresTraceStore.mark_trace_aborted` | pg_store | pure |
| `PostgresTraceStore.record_step` | pg_store | pure |
| `PostgresTraceStore.search_traces` | pg_store | pure |
| `PostgresTraceStore.start_trace` | pg_store | pure |
| `PostgresTraceStore.store_trace` | pg_store | pure |
| `ProgressUpdate.to_dict` | job_execution | pure |
| `RedisIdempotencyStore.check` | idempotency | pure |
| `RedisIdempotencyStore.delete` | idempotency | db_write |
| `RedisIdempotencyStore.delete` | replay | db_write,external_api |
| `RedisIdempotencyStore.get` | replay | external_api |
| `RedisIdempotencyStore.get_status` | idempotency | pure |
| `RedisIdempotencyStore.mark_completed` | idempotency | pure |
| `RedisIdempotencyStore.mark_failed` | idempotency | pure |
| `RedisIdempotencyStore.set` | replay | pure |
| `ReplayEnforcer.enforce_step` | replay | pure |
| `ReplayEnforcer.enforce_trace` | replay | pure |
| `SQLiteTraceStore.cleanup_old_traces` | traces_store | db_write |
| `SQLiteTraceStore.complete_trace` | traces_store | db_write |
| `SQLiteTraceStore.delete_trace` | traces_store | db_write |
| `SQLiteTraceStore.find_matching_traces` | traces_store | pure |
| `SQLiteTraceStore.get_trace` | traces_store | pure |
| `SQLiteTraceStore.get_trace_by_root_hash` | traces_store | pure |
| `SQLiteTraceStore.get_trace_count` | traces_store | pure |
| `SQLiteTraceStore.list_traces` | traces_store | pure |
| `SQLiteTraceStore.record_step` | traces_store | db_write |
| `SQLiteTraceStore.search_traces` | traces_store | pure |
| `SQLiteTraceStore.start_trace` | traces_store | db_write |
| `SQLiteTraceStore.update_trace_determinism` | traces_store | db_write |
| `TraceStore.complete_trace` | traces_store | pure |
| `TraceStore.delete_trace` | traces_store | pure |
| `TraceStore.get_trace` | traces_store | pure |
| `TraceStore.list_traces` | traces_store | pure |
| `TraceStore.record_step` | traces_store | pure |
| `TraceStore.start_trace` | traces_store | pure |
| `canonical_json` | idempotency | pure |
| `capture_activity_evidence` | capture | db_write |
| `capture_environment_evidence` | capture | db_write |
| `capture_integrity_evidence` | capture | db_write |
| `capture_policy_decision_evidence` | capture | db_write |
| `capture_provider_evidence` | capture | db_write |
| `compute_integrity` | capture | pure |
| `compute_integrity_v2` | integrity | pure |
| `create_consistency_checker` | panel_consistency_checker | pure |
| `generate_correlation_id` | traces_store | pure |
| `generate_run_id` | traces_store | pure |
| `get_audit_ledger_service_async` | audit_ledger_service_async | pure |
| `get_export_bundle_store` | export_bundle_store | pure |
| `get_idempotency_store` | idempotency | pure |
| `get_job_audit_emitter` | job_execution | pure |
| `get_job_progress_tracker` | job_execution | pure |
| `get_job_retry_manager` | job_execution | pure |
| `get_logs_domain_store` | logs_domain_store | pure |
| `get_postgres_trace_store` | pg_store | pure |
| `get_replay_enforcer` | replay | pure |
| `hash_output` | replay | pure |
| `hash_prompt` | capture | pure |
| `hash_request` | idempotency | pure |
| `record_policy_activation` | bridges_driver | db_write |
| `reset_job_execution_services` | job_execution | pure |

### Unclassified (needs review)

_36 functions need manual classification._

- `AuditLedgerService.incident_acknowledged` (audit_ledger_service)
- `AuditLedgerService.incident_manually_closed` (audit_ledger_service)
- `AuditReconciler.get_run_audit_summary` (audit_reconciler)
- `EvidenceCompletenessChecker.ensure_complete` (completeness_checker)
- `EvidenceCompletenessChecker.get_completeness_summary` (completeness_checker)
- `EvidenceCompletenessChecker.get_field_value` (completeness_checker)
- `EvidenceCompletenessChecker.get_required_fields` (completeness_checker)
- `EvidenceCompletenessChecker.is_field_present` (completeness_checker)
- `EvidenceCompletenessChecker.strict_mode` (completeness_checker)
- `EvidenceCompletenessChecker.validation_enabled` (completeness_checker)
- `LogsReadService.get_trace` (logs_read_engine)
- `LogsReadService.get_trace_by_root_hash` (logs_read_engine)
- `LogsReadService.get_trace_count` (logs_read_engine)
- `LogsReadService.list_traces` (logs_read_engine)
- `LogsReadService.search_traces` (logs_read_engine)
- `MCPAuditEmitter.emit_server_registered` (audit_evidence)
- `MCPAuditEmitter.emit_server_unregistered` (audit_evidence)
- `MCPAuditEmitter.emit_tool_completed` (audit_evidence)
- `MCPAuditEmitter.emit_tool_denied` (audit_evidence)
- `MCPAuditEmitter.emit_tool_failed` (audit_evidence)
- _...and 16 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in LOGS_DOMAIN_LOCK_FINAL.md._
