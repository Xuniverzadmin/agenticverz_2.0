# Logs — Call Graph

**Domain:** logs  
**Total functions:** 428  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 21 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 30 | Calls other functions + adds its own decisions |
| WRAPPER | 138 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 109 | Terminal — calls no other domain functions |
| ENTRY | 75 | Entry point — no domain-internal callers |
| INTERNAL | 55 | Called only by other domain functions |

## Canonical Algorithm Owners

### `audit_engine.AuditChecks.check_execution_fidelity`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 9
- **Delegation depth:** 3
- **Persistence:** yes
- **Chain:** audit_engine.AuditChecks.check_execution_fidelity → replay.IdempotencyStore.get → replay.IdempotencyStore.set → replay.InMemoryIdempotencyStore.get → ...+3
- **Calls:** replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, replay:RedisIdempotencyStore.set

### `audit_reconciler.AuditReconciler.reconcile`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 19
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** audit_reconciler.AuditReconciler.reconcile → audit_reconciler.AuditReconciler._record_metrics
- **Calls:** audit_reconciler:AuditReconciler._record_metrics

### `capture.capture_integrity_evidence`
- **Layer:** L6
- **Decisions:** 1
- **Statements:** 5
- **Delegation depth:** 8
- **Persistence:** yes
- **Chain:** capture.capture_integrity_evidence → capture.compute_integrity → replay.IdempotencyStore.get → replay.InMemoryIdempotencyStore.get → ...+1
- **Calls:** capture:compute_integrity, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `completeness_checker.EvidenceCompletenessChecker.check`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 12
- **Delegation depth:** 5
- **Persistence:** yes
- **Chain:** completeness_checker.EvidenceCompletenessChecker.check → completeness_checker.EvidenceCompletenessChecker.get_required_fields → completeness_checker.EvidenceCompletenessChecker.is_field_present → replay.IdempotencyStore.set → ...+2
- **Calls:** completeness_checker:EvidenceCompletenessChecker.get_required_fields, completeness_checker:EvidenceCompletenessChecker.is_field_present, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set

### `evidence_facade.EvidenceFacade.create_chain`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 9
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** evidence_facade.EvidenceFacade.create_chain → evidence_facade.EvidenceFacade._create_link → evidence_facade.EvidenceFacade._hash_data → replay.IdempotencyStore.get → ...+2
- **Calls:** evidence_facade:EvidenceFacade._create_link, evidence_facade:EvidenceFacade._hash_data, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `evidence_report.EvidenceReportGenerator.generate`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 21
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** evidence_report.EvidenceReportGenerator.generate → evidence_report.EvidenceReportGenerator._build_certificate_section → evidence_report.EvidenceReportGenerator._build_cover_page → evidence_report.EvidenceReportGenerator._build_decision_timeline → ...+8
- **Calls:** evidence_report:EvidenceReportGenerator._build_certificate_section, evidence_report:EvidenceReportGenerator._build_cover_page, evidence_report:EvidenceReportGenerator._build_decision_timeline, evidence_report:EvidenceReportGenerator._build_executive_summary, evidence_report:EvidenceReportGenerator._build_factual_reconstruction, evidence_report:EvidenceReportGenerator._build_incident_snapshot, evidence_report:EvidenceReportGenerator._build_legal_attestation, evidence_report:EvidenceReportGenerator._build_policy_evaluation, evidence_report:EvidenceReportGenerator._build_prevention_proof, evidence_report:EvidenceReportGenerator._build_remediation, evidence_report:EvidenceReportGenerator._build_replay_verification

### `idempotency.InMemoryIdempotencyStore.check`
- **Layer:** L6
- **Decisions:** 2
- **Statements:** 6
- **Delegation depth:** 8
- **Persistence:** no
- **Chain:** idempotency.InMemoryIdempotencyStore.check → idempotency.InMemoryIdempotencyStore._make_key → idempotency.RedisIdempotencyStore._make_key → idempotency.hash_request → ...+5
- **Calls:** idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, idempotency:hash_request, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore._make_key, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore._make_key, replay:RedisIdempotencyStore.get

### `integrity.IntegrityEvaluator.evaluate`
- **Layer:** L6
- **Decisions:** 2
- **Statements:** 10
- **Delegation depth:** 6
- **Persistence:** no
- **Chain:** integrity.IntegrityEvaluator.evaluate → audit_evidence.MCPAuditEvent.to_dict → certificate.Certificate.to_dict → certificate.CertificatePayload.to_dict → ...+20
- **Calls:** audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, evidence_facade:EvidenceChain.to_dict, evidence_facade:EvidenceExport.to_dict, evidence_facade:EvidenceLink.to_dict, evidence_facade:VerificationResult.to_dict, integrity:CaptureFailure.to_dict, integrity:IntegrityEvaluator._build_explanation, integrity:IntegrityEvaluator._compute_grade, integrity:IntegrityEvaluator._find_failure, job_execution:JobAuditEvent.to_dict, job_execution:ProgressUpdate.to_dict, replay_determinism:CallRecord.to_dict, replay_determinism:ModelVersion.to_dict, replay_determinism:PolicyDecision.to_dict, replay_determinism:ReplayResult.to_dict, traces_models:ParityResult.to_dict, traces_models:TraceRecord.to_dict, traces_models:TraceStep.to_dict, traces_models:TraceSummary.to_dict

### `job_execution.JobProgressTracker.update`
- **Layer:** L6
- **Decisions:** 8
- **Statements:** 13
- **Delegation depth:** 7
- **Persistence:** no
- **Chain:** job_execution.JobProgressTracker.update → job_execution.JobProgressTracker._calculate_eta → job_execution.JobProgressTracker._emit_progress → replay.IdempotencyStore.get → ...+2
- **Calls:** job_execution:JobProgressTracker._calculate_eta, job_execution:JobProgressTracker._emit_progress, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `logs_domain_store.LogsDomainStore.list_llm_runs`
- **Layer:** L6
- **Decisions:** 7
- **Statements:** 16
- **Delegation depth:** 1
- **Persistence:** yes
- **Chain:** logs_domain_store.LogsDomainStore.list_llm_runs → logs_domain_store.LogsDomainStore._to_llm_run_snapshot
- **Calls:** logs_domain_store:LogsDomainStore._to_llm_run_snapshot

### `logs_facade.LogsFacade.list_llm_run_records`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 11
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** logs_facade.LogsFacade.list_llm_run_records → logs_domain_store.LogsDomainStore.list_llm_runs → logs_facade.LogsFacade._snapshot_to_record_result
- **Calls:** logs_domain_store:LogsDomainStore.list_llm_runs, logs_facade:LogsFacade._snapshot_to_record_result

### `mapper.SOC2ControlMapper.map_incident_to_controls`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 4
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** mapper.SOC2ControlMapper.map_incident_to_controls → mapper.SOC2ControlMapper._create_mapping → replay.IdempotencyStore.get → replay.InMemoryIdempotencyStore.get → ...+1
- **Calls:** mapper:SOC2ControlMapper._create_mapping, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `panel_consistency_checker.PanelConsistencyChecker.check`
- **Layer:** L6
- **Decisions:** 3
- **Statements:** 7
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** panel_consistency_checker.PanelConsistencyChecker.check → panel_consistency_checker.PanelConsistencyChecker._check_rule
- **Calls:** panel_consistency_checker:PanelConsistencyChecker._check_rule

### `pdf_renderer.PDFRenderer.render_soc2_pdf`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 15
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** pdf_renderer.PDFRenderer.render_soc2_pdf → pdf_renderer.PDFRenderer._build_attestation → pdf_renderer.PDFRenderer._build_control_mappings → pdf_renderer.PDFRenderer._build_evidence_summary → ...+2
- **Calls:** pdf_renderer:PDFRenderer._build_attestation, pdf_renderer:PDFRenderer._build_control_mappings, pdf_renderer:PDFRenderer._build_evidence_summary, pdf_renderer:PDFRenderer._build_soc2_cover, pdf_renderer:PDFRenderer._build_trace_timeline

### `pg_store.PostgresTraceStore.search_traces`
- **Layer:** L6
- **Decisions:** 8
- **Statements:** 14
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** pg_store.PostgresTraceStore.search_traces → pg_store.PostgresTraceStore._get_pool
- **Calls:** pg_store:PostgresTraceStore._get_pool

### `redact.redact_trace_data`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 5
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** redact.redact_trace_data → redact.redact_dict → redact.redact_list
- **Calls:** redact:redact_dict, redact:redact_list

### `replay.ReplayEnforcer.enforce_step`
- **Layer:** L6
- **Decisions:** 8
- **Statements:** 11
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** replay.ReplayEnforcer.enforce_step → replay.IdempotencyStore.get → replay.IdempotencyStore.set → replay.InMemoryIdempotencyStore.get → ...+4
- **Calls:** replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, replay:RedisIdempotencyStore.set, replay:hash_output

### `replay_determinism.ReplayValidator.validate_replay`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 13
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** replay_determinism.ReplayValidator.validate_replay → replay_determinism.ReplayValidator._compare_policies → replay_determinism.ReplayValidator._detect_model_drift → replay_determinism.ReplayValidator._level_meets_requirement → ...+1
- **Calls:** replay_determinism:ReplayValidator._compare_policies, replay_determinism:ReplayValidator._detect_model_drift, replay_determinism:ReplayValidator._level_meets_requirement, replay_determinism:ReplayValidator._semantic_equivalent

### `trace_facade.TraceFacade.start_trace`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 6
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** trace_facade.TraceFacade.start_trace → pg_store.PostgresTraceStore.start_trace → trace_facade.TraceFacade._emit_ack → traces_store.InMemoryTraceStore.start_trace → ...+2
- **Calls:** pg_store:PostgresTraceStore.start_trace, trace_facade:TraceFacade._emit_ack, traces_store:InMemoryTraceStore.start_trace, traces_store:SQLiteTraceStore.start_trace, traces_store:TraceStore.start_trace

### `traces_models.compare_traces`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 6
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** traces_models.compare_traces → traces_models.TraceRecord.determinism_signature → traces_models.TraceStep.determinism_hash
- **Calls:** traces_models:TraceRecord.determinism_signature, traces_models:TraceStep.determinism_hash

### `traces_store.SQLiteTraceStore.search_traces`
- **Layer:** L6
- **Decisions:** 8
- **Statements:** 2
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** traces_store.SQLiteTraceStore.search_traces → traces_store.SQLiteTraceStore._get_conn
- **Calls:** traces_store:SQLiteTraceStore._get_conn

## Supersets (orchestrating functions)

### `audit_engine.AuditChecks.check_health_preservation`
- **Decisions:** 4, **Statements:** 7
- **Subsumes:** audit_engine:AuditChecks._is_health_degraded, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `audit_engine.AuditChecks.check_no_unauthorized_mutations`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, replay:RedisIdempotencyStore.set

### `audit_engine.AuditChecks.check_rollback_availability`
- **Decisions:** 4, **Statements:** 8
- **Subsumes:** replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `audit_engine.AuditChecks.check_scope_compliance`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, replay:RedisIdempotencyStore.set

### `audit_engine.create_audit_input_from_evidence`
- **Decisions:** 2, **Statements:** 9
- **Subsumes:** replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `audit_evidence._redact_sensitive`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** audit_evidence:_contains_sensitive

### `certificate.CertificateService.export_certificate`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:Certificate.to_json, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, evidence_facade:EvidenceChain.to_dict, evidence_facade:EvidenceExport.to_dict, evidence_facade:EvidenceLink.to_dict, evidence_facade:VerificationResult.to_dict, integrity:CaptureFailure.to_dict, job_execution:JobAuditEvent.to_dict, job_execution:ProgressUpdate.to_dict, replay_determinism:CallRecord.to_dict, replay_determinism:ModelVersion.to_dict, replay_determinism:PolicyDecision.to_dict, replay_determinism:ReplayResult.to_dict, traces_models:ParityResult.to_dict, traces_models:TraceRecord.to_dict, traces_models:TraceStep.to_dict, traces_models:TraceSummary.to_dict

### `completeness_checker.EvidenceCompletenessChecker.is_field_present`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** completeness_checker:EvidenceCompletenessChecker.get_field_value

### `completeness_checker.EvidenceCompletenessChecker.should_allow_export`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** completeness_checker:EvidenceCompletenessChecker.check, idempotency:InMemoryIdempotencyStore.check, idempotency:RedisIdempotencyStore.check, panel_consistency_checker:PanelConsistencyChecker.check

### `evidence_facade.EvidenceFacade.verify_chain`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** evidence_facade:EvidenceFacade._hash_data, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `evidence_report.EvidenceReportGenerator._build_executive_summary`
- **Decisions:** 2, **Statements:** 25
- **Subsumes:** replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `evidence_report.EvidenceReportGenerator._build_policy_evaluation`
- **Decisions:** 4, **Statements:** 16
- **Subsumes:** replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `evidence_report.generate_evidence_report`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** evidence_report:EvidenceReportGenerator.generate, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `integrity.IntegrityAssembler.gather`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** integrity:IntegrityAssembler._count_evidence, integrity:IntegrityAssembler._gather_failures, integrity:IntegrityAssembler._resolve_superseded, integrity:IntegrityAssembler._table_to_class

### `logs_domain_store.LogsDomainStore.list_audit_entries`
- **Decisions:** 5, **Statements:** 14
- **Subsumes:** logs_domain_store:LogsDomainStore._to_audit_snapshot

### `logs_domain_store.LogsDomainStore.list_system_records`
- **Decisions:** 6, **Statements:** 15
- **Subsumes:** logs_domain_store:LogsDomainStore._to_system_record_snapshot

### `logs_facade.LogsFacade.list_audit_entries`
- **Decisions:** 5, **Statements:** 9
- **Subsumes:** logs_domain_store:LogsDomainStore.list_audit_entries

### `logs_facade.LogsFacade.list_system_records`
- **Decisions:** 5, **Statements:** 9
- **Subsumes:** logs_domain_store:LogsDomainStore.list_system_records

### `mapper.SOC2ControlMapper._create_mapping`
- **Decisions:** 3, **Statements:** 9
- **Subsumes:** mapper:SOC2ControlMapper._determine_compliance_status, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `mapper.SOC2ControlMapper._determine_compliance_status`
- **Decisions:** 9, **Statements:** 8
- **Subsumes:** replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `panel_consistency_checker.PanelConsistencyChecker._check_rule`
- **Decisions:** 4, **Statements:** 8
- **Subsumes:** panel_consistency_checker:PanelConsistencyChecker._evaluate_condition, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get

### `panel_consistency_checker.PanelConsistencyChecker._evaluate_condition`
- **Decisions:** 4, **Statements:** 5
- **Subsumes:** panel_consistency_checker:PanelConsistencyChecker._eval_expr

### `pg_store.PostgresTraceStore.get_trace`
- **Decisions:** 4, **Statements:** 2
- **Subsumes:** pg_store:PostgresTraceStore._get_pool

### `pg_store.PostgresTraceStore.get_trace_by_root_hash`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** logs_read_engine:LogsReadService.get_trace, pg_store:PostgresTraceStore._get_pool, pg_store:PostgresTraceStore.get_trace, traces_store:InMemoryTraceStore.get_trace, traces_store:SQLiteTraceStore.get_trace, traces_store:TraceStore.get_trace

### `pg_store.PostgresTraceStore.record_step`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** pg_store:PostgresTraceStore._get_pool, pg_store:_status_to_level

### `redact.redact_dict`
- **Decisions:** 5, **Statements:** 4
- **Subsumes:** redact:redact_list, redact:redact_string_value

### `redact.redact_list`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** redact:redact_dict, redact:redact_string_value

### `replay_determinism.ReplayContextBuilder.build_call_record`
- **Decisions:** 2, **Statements:** 9
- **Subsumes:** replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, replay_determinism:ReplayValidator.hash_content

### `replay_determinism.ReplayValidator._compare_policies`
- **Decisions:** 5, **Statements:** 6
- **Subsumes:** replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set

### `replay_determinism.ReplayValidator._semantic_equivalent`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set

## Wrappers (thin delegation)

- `audit_engine.AuditService.__init__` → ?
- `audit_engine.AuditService.version` → ?
- `audit_engine.RolloutGate.is_rollout_authorized` → ?
- `audit_evidence.MCPAuditEmitter.__init__` → ?
- `audit_evidence.MCPAuditEmitter._generate_event_id` → ?
- `audit_evidence.MCPAuditEvent.to_dict` → ?
- `audit_evidence.MCPAuditEvent.verify_integrity` → audit_evidence:MCPAuditEvent._compute_integrity_hash
- `audit_evidence._contains_sensitive` → ?
- `audit_evidence.reset_mcp_audit_emitter` → ?
- `audit_ledger_service.AuditLedgerService.__init__` → ?
- `audit_ledger_service.AuditLedgerService.incident_acknowledged` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service.AuditLedgerService.incident_manually_closed` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service.AuditLedgerService.incident_resolved` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service.get_audit_ledger_service` → ?
- `audit_ledger_service_async.AuditLedgerServiceAsync.__init__` → ?
- `audit_ledger_service_async.AuditLedgerServiceAsync.limit_breached` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.limit_created` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.limit_updated` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_proposal_approved` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_proposal_rejected` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_created` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_modified` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_retired` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.get_audit_ledger_service_async` → ?
- `audit_reconciler.AuditReconciler.__init__` → ?
- `capture.EvidenceContextError.__init__` → audit_engine:AuditService.__init__
- `capture.compute_integrity` → integrity:compute_integrity_v2
- `capture.hash_prompt` → capture:_hash_content
- `certificate.Certificate.to_dict` → audit_evidence:MCPAuditEvent.to_dict
- `certificate.Certificate.to_json` → audit_evidence:MCPAuditEvent.to_dict
- `certificate.CertificatePayload.canonical_json` → audit_evidence:MCPAuditEvent.to_dict
- `certificate.CertificatePayload.to_dict` → ?
- `certificate.CertificateService._verify_signature` → certificate:CertificateService._sign
- `completeness_checker.CompletenessCheckResponse.to_dict` → ?
- `completeness_checker.EvidenceCompletenessChecker.__init__` → ?
- `completeness_checker.EvidenceCompletenessChecker.strict_mode` → ?
- `completeness_checker.EvidenceCompletenessChecker.validation_enabled` → ?
- `completeness_checker.EvidenceCompletenessError.to_dict` → ?
- `completeness_checker.check_evidence_completeness` → completeness_checker:EvidenceCompletenessChecker.check
- `completeness_checker.ensure_evidence_completeness` → completeness_checker:EvidenceCompletenessChecker.ensure_complete
- `evidence_facade.EvidenceChain.to_dict` → audit_evidence:MCPAuditEvent.to_dict
- `evidence_facade.EvidenceExport.to_dict` → ?
- `evidence_facade.EvidenceFacade.__init__` → ?
- `evidence_facade.EvidenceLink.to_dict` → ?
- `evidence_facade.VerificationResult.to_dict` → ?
- `evidence_report.EvidenceReportGenerator.__init__` → evidence_report:EvidenceReportGenerator._setup_custom_styles
- `evidence_report.EvidenceReportGenerator._compute_report_hash` → evidence_report:EvidenceReportGenerator._compute_hash
- `export_bundle_store.ExportBundleStore.__init__` → ?
- `idempotency.IdempotencyResponse.is_conflict` → ?
- `idempotency.IdempotencyResponse.is_duplicate` → ?
- `idempotency.IdempotencyResponse.is_new` → ?
- `idempotency.InMemoryIdempotencyStore.__init__` → ?
- `idempotency.InMemoryIdempotencyStore._make_key` → ?
- `idempotency.InMemoryIdempotencyStore.delete` → idempotency:InMemoryIdempotencyStore._make_key
- `idempotency.InMemoryIdempotencyStore.get_status` → idempotency:InMemoryIdempotencyStore._make_key
- `idempotency.RedisIdempotencyStore._make_key` → ?
- `idempotency.canonical_json` → ?
- `integrity.CaptureFailure.to_dict` → ?
- `integrity.IntegrityAssembler.__init__` → ?
- `integrity.IntegrityAssembler._table_to_class` → replay:IdempotencyStore.get
- `integrity.IntegrityFacts.has_capture_failures` → ?
- `integrity.IntegrityFacts.has_required_evidence` → ?
- `integrity.IntegrityFacts.unresolved_failures` → ?
- `job_execution.JobAuditEmitter.__init__` → ?
- `job_execution.JobAuditEmitter._generate_event_id` → ?
- `job_execution.JobAuditEvent.to_dict` → ?
- `job_execution.JobAuditEvent.verify_integrity` → audit_evidence:MCPAuditEvent._compute_integrity_hash
- `job_execution.JobProgressTracker.__init__` → ?
- `job_execution.JobProgressTracker.get_progress` → replay:IdempotencyStore.get
- `job_execution.JobRetryManager.__init__` → ?
- `job_execution.JobRetryManager.clear_history` → ?
- `job_execution.JobRetryManager.get_retry_history` → replay:IdempotencyStore.get
- `job_execution.ProgressUpdate.to_dict` → ?
- `logs_domain_store.LogsDomainStore._to_audit_snapshot` → ?
- `logs_domain_store.LogsDomainStore._to_export_snapshot` → ?
- `logs_domain_store.LogsDomainStore._to_llm_run_snapshot` → ?
- `logs_domain_store.LogsDomainStore._to_system_record_snapshot` → ?
- `logs_facade.LogsFacade.__init__` → logs_domain_store:get_logs_domain_store
- `logs_facade.LogsFacade._snapshot_to_record_result` → ?
- `logs_facade.LogsFacade.get_system_telemetry` → ?
- `logs_read_engine.LogsReadService.__init__` → ?
- `logs_read_engine.LogsReadService.get_trace` → logs_read_engine:LogsReadService._get_store
- `logs_read_engine.LogsReadService.get_trace_by_root_hash` → logs_read_engine:LogsReadService._get_store
- `logs_read_engine.LogsReadService.get_trace_count` → logs_read_engine:LogsReadService._get_store
- `mapper.SOC2ControlMapper.__init__` → ?
- `panel_consistency_checker.PanelConsistencyChecker.__init__` → panel_consistency_checker:PanelConsistencyChecker._default_rules
- `panel_consistency_checker.PanelConsistencyChecker._default_rules` → ?
- `panel_consistency_checker.create_consistency_checker` → ?
- `panel_response_assembler.PanelResponseAssembler.__init__` → ?
- `panel_response_assembler.PanelResponseAssembler.assemble_error` → ?
- `panel_response_assembler.create_response_assembler` → ?
- `pdf_renderer.PDFRenderer.__init__` → pdf_renderer:PDFRenderer._setup_styles
- `pg_store.PostgresTraceStore.__init__` → ?
- `pg_store.PostgresTraceStore.list_traces` → logs_read_engine:LogsReadService.search_traces
- `redact.add_redaction_pattern` → ?
- `redact.add_sensitive_field` → ?
- `redact.is_sensitive_field` → ?
- `replay.IdempotencyStore.delete` → ?
- `replay.IdempotencyStore.get` → ?
- `replay.IdempotencyStore.set` → ?
- `replay.IdempotencyViolationError.__init__` → audit_engine:AuditService.__init__
- `replay.InMemoryIdempotencyStore.__init__` → ?
- `replay.InMemoryIdempotencyStore._make_key` → ?
- `replay.InMemoryIdempotencyStore.clear` → ?
- `replay.InMemoryIdempotencyStore.get` → idempotency:InMemoryIdempotencyStore._make_key
- `replay.InMemoryIdempotencyStore.set` → idempotency:InMemoryIdempotencyStore._make_key
- `replay.RedisIdempotencyStore._make_key` → ?
- `replay.ReplayEnforcer.__init__` → ?
- `replay_determinism.ModelVersion.to_dict` → ?
- `replay_determinism.PolicyDecision.to_dict` → ?
- `replay_determinism.ReplayContextBuilder.__init__` → ?
- `replay_determinism.ReplayResult.to_dict` → audit_evidence:MCPAuditEvent.to_dict
- `replay_determinism.ReplayValidator.__init__` → ?
- `replay_determinism.ReplayValidator._level_meets_requirement` → ?
- `trace_facade.TraceFacade.__init__` → ?
- `trace_facade.TraceFacade.add_step` → ?
- `traces_metrics.TracesMetrics.__init__` → ?
- `traces_metrics.TracesMetrics.record_idempotency_check` → ?
- `traces_metrics.TracesMetrics.record_replay_enforcement` → ?
- `traces_models.ParityResult.to_dict` → ?
- `traces_models.TraceRecord.failure_count` → ?
- `traces_models.TraceRecord.success_count` → ?
- `traces_models.TraceRecord.to_summary` → ?
- `traces_models.TraceRecord.total_cost_cents` → ?
- `traces_models.TraceRecord.total_duration_ms` → ?
- `traces_models.TraceStep.to_dict` → ?
- `traces_store.InMemoryTraceStore.__init__` → ?
- `traces_store.InMemoryTraceStore.start_trace` → ?
- `traces_store.SQLiteTraceStore._get_conn` → ?
- `traces_store.SQLiteTraceStore.find_matching_traces` → logs_read_engine:LogsReadService.search_traces
- `traces_store.TraceStore.complete_trace` → ?
- `traces_store.TraceStore.delete_trace` → ?
- `traces_store.TraceStore.get_trace` → ?
- `traces_store.TraceStore.list_traces` → ?
- `traces_store.TraceStore.record_step` → ?
- `traces_store.TraceStore.start_trace` → ?
- `traces_store.generate_correlation_id` → ?
- `traces_store.generate_run_id` → ?

## Full Call Graph

```
[INTERNAL] audit_engine.AuditChecks._is_health_degraded → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[CANONICAL] audit_engine.AuditChecks.check_execution_fidelity → replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, ...+1
[SUPERSET] audit_engine.AuditChecks.check_health_preservation → audit_engine:AuditChecks._is_health_degraded, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[SUPERSET] audit_engine.AuditChecks.check_no_unauthorized_mutations → replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, ...+1
[SUPERSET] audit_engine.AuditChecks.check_rollback_availability → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[SUPERSET] audit_engine.AuditChecks.check_scope_compliance → replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, ...+1
[LEAF] audit_engine.AuditChecks.check_signal_consistency
[LEAF] audit_engine.AuditChecks.check_timing_compliance
[WRAPPER] audit_engine.AuditService.__init__
[LEAF] audit_engine.AuditService._determine_verdict
[INTERNAL] audit_engine.AuditService._run_all_checks → audit_engine:AuditChecks.check_execution_fidelity, audit_engine:AuditChecks.check_health_preservation, audit_engine:AuditChecks.check_no_unauthorized_mutations, audit_engine:AuditChecks.check_rollback_availability, audit_engine:AuditChecks.check_scope_compliance, ...+2
[ENTRY] audit_engine.AuditService.audit → audit_engine:AuditService._determine_verdict, audit_engine:AuditService._run_all_checks
[WRAPPER] audit_engine.AuditService.version
[LEAF] audit_engine.RolloutGate.get_rollout_status
[WRAPPER] audit_engine.RolloutGate.is_rollout_authorized
[LEAF] audit_engine.audit_result_to_record
[SUPERSET] audit_engine.create_audit_input_from_evidence → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] audit_evidence.MCPAuditEmitter.__init__
[INTERNAL] audit_evidence.MCPAuditEmitter._emit → audit_evidence:MCPAuditEmitter._get_publisher, audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, ...+18
[WRAPPER] audit_evidence.MCPAuditEmitter._generate_event_id
[LEAF] audit_evidence.MCPAuditEmitter._get_publisher
[ENTRY] audit_evidence.MCPAuditEmitter.emit_server_registered → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] audit_evidence.MCPAuditEmitter.emit_server_unregistered → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] audit_evidence.MCPAuditEmitter.emit_tool_allowed → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] audit_evidence.MCPAuditEmitter.emit_tool_completed → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_evidence:_hash_value, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, ...+3
[ENTRY] audit_evidence.MCPAuditEmitter.emit_tool_denied → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] audit_evidence.MCPAuditEmitter.emit_tool_failed → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] audit_evidence.MCPAuditEmitter.emit_tool_requested → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_evidence:_hash_value, audit_evidence:_redact_sensitive, audit_ledger_service:AuditLedgerService._emit, ...+4
[ENTRY] audit_evidence.MCPAuditEmitter.emit_tool_started → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] audit_evidence.MCPAuditEvent.__post_init__ → audit_evidence:MCPAuditEvent._compute_integrity_hash, job_execution:JobAuditEvent._compute_integrity_hash
[LEAF] audit_evidence.MCPAuditEvent._compute_integrity_hash
[WRAPPER] audit_evidence.MCPAuditEvent.to_dict
[WRAPPER] audit_evidence.MCPAuditEvent.verify_integrity → audit_evidence:MCPAuditEvent._compute_integrity_hash, job_execution:JobAuditEvent._compute_integrity_hash
[WRAPPER] audit_evidence._contains_sensitive
[LEAF] audit_evidence._hash_value
[SUPERSET] audit_evidence._redact_sensitive → audit_evidence:_contains_sensitive
[LEAF] audit_evidence.configure_mcp_audit_emitter
[LEAF] audit_evidence.get_mcp_audit_emitter
[WRAPPER] audit_evidence.reset_mcp_audit_emitter
[WRAPPER] audit_ledger_service.AuditLedgerService.__init__
[LEAF] audit_ledger_service.AuditLedgerService._emit
[WRAPPER] audit_ledger_service.AuditLedgerService.incident_acknowledged → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service.AuditLedgerService.incident_manually_closed → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service.AuditLedgerService.incident_resolved → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service.get_audit_ledger_service
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.__init__
[LEAF] audit_ledger_service_async.AuditLedgerServiceAsync._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.limit_breached → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.limit_created → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.limit_updated → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.policy_proposal_approved → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.policy_proposal_rejected → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_created → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_modified → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_retired → audit_evidence:MCPAuditEmitter._emit, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit
[WRAPPER] audit_ledger_service_async.get_audit_ledger_service_async
[WRAPPER] audit_reconciler.AuditReconciler.__init__
[LEAF] audit_reconciler.AuditReconciler._record_metrics
[LEAF] audit_reconciler.AuditReconciler.check_deadline_violations
[LEAF] audit_reconciler.AuditReconciler.get_run_audit_summary
[CANONICAL] audit_reconciler.AuditReconciler.reconcile → audit_reconciler:AuditReconciler._record_metrics
[LEAF] audit_reconciler.get_audit_reconciler
[LEAF] bridges_driver.record_policy_activation
[WRAPPER] capture.EvidenceContextError.__init__ → audit_engine:AuditService.__init__, audit_evidence:MCPAuditEmitter.__init__, audit_ledger_service:AuditLedgerService.__init__, audit_ledger_service_async:AuditLedgerServiceAsync.__init__, audit_reconciler:AuditReconciler.__init__, ...+30
[LEAF] capture._assert_context_exists
[LEAF] capture._hash_content
[INTERNAL] capture._record_capture_failure → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] capture.capture_activity_evidence → capture:_assert_context_exists, capture:_record_capture_failure
[ENTRY] capture.capture_environment_evidence → capture:_assert_context_exists, capture:_record_capture_failure
[CANONICAL] capture.capture_integrity_evidence → capture:compute_integrity, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] capture.capture_policy_decision_evidence → capture:_assert_context_exists, capture:_record_capture_failure
[ENTRY] capture.capture_provider_evidence → capture:_assert_context_exists, capture:_record_capture_failure
[WRAPPER] capture.compute_integrity → integrity:compute_integrity_v2
[WRAPPER] capture.hash_prompt → capture:_hash_content
[ENTRY] certificate.Certificate.from_dict → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] certificate.Certificate.to_dict → audit_evidence:MCPAuditEvent.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, evidence_facade:EvidenceChain.to_dict, ...+14
[WRAPPER] certificate.Certificate.to_json → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+15
[WRAPPER] certificate.CertificatePayload.canonical_json → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+15
[WRAPPER] certificate.CertificatePayload.to_dict
[LEAF] certificate.CertificateService.__init__
[LEAF] certificate.CertificateService._sign
[WRAPPER] certificate.CertificateService._verify_signature → certificate:CertificateService._sign
[ENTRY] certificate.CertificateService.create_policy_audit_certificate → certificate:CertificatePayload.canonical_json, certificate:CertificateService._sign, idempotency:canonical_json, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, ...+1
[ENTRY] certificate.CertificateService.create_replay_certificate → certificate:CertificatePayload.canonical_json, certificate:CertificateService._sign, idempotency:canonical_json
[SUPERSET] certificate.CertificateService.export_certificate → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:Certificate.to_json, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, ...+16
[ENTRY] certificate.CertificateService.verify_certificate → certificate:CertificatePayload.canonical_json, certificate:CertificateService._verify_signature, idempotency:canonical_json
[WRAPPER] completeness_checker.CompletenessCheckResponse.to_dict
[WRAPPER] completeness_checker.EvidenceCompletenessChecker.__init__
[CANONICAL] completeness_checker.EvidenceCompletenessChecker.check → completeness_checker:EvidenceCompletenessChecker.get_required_fields, completeness_checker:EvidenceCompletenessChecker.is_field_present, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set
[INTERNAL] completeness_checker.EvidenceCompletenessChecker.ensure_complete → completeness_checker:EvidenceCompletenessChecker.check, idempotency:InMemoryIdempotencyStore.check, idempotency:RedisIdempotencyStore.check, panel_consistency_checker:PanelConsistencyChecker.check
[LEAF] completeness_checker.EvidenceCompletenessChecker.from_governance_config
[ENTRY] completeness_checker.EvidenceCompletenessChecker.get_completeness_summary → completeness_checker:EvidenceCompletenessChecker.get_required_fields, completeness_checker:EvidenceCompletenessChecker.is_field_present
[INTERNAL] completeness_checker.EvidenceCompletenessChecker.get_field_value → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] completeness_checker.EvidenceCompletenessChecker.get_required_fields
[SUPERSET] completeness_checker.EvidenceCompletenessChecker.is_field_present → completeness_checker:EvidenceCompletenessChecker.get_field_value
[SUPERSET] completeness_checker.EvidenceCompletenessChecker.should_allow_export → completeness_checker:EvidenceCompletenessChecker.check, idempotency:InMemoryIdempotencyStore.check, idempotency:RedisIdempotencyStore.check, panel_consistency_checker:PanelConsistencyChecker.check
[WRAPPER] completeness_checker.EvidenceCompletenessChecker.strict_mode
[WRAPPER] completeness_checker.EvidenceCompletenessChecker.validation_enabled
[INTERNAL] completeness_checker.EvidenceCompletenessError.__init__ → audit_engine:AuditService.__init__, audit_evidence:MCPAuditEmitter.__init__, audit_ledger_service:AuditLedgerService.__init__, audit_ledger_service_async:AuditLedgerServiceAsync.__init__, audit_reconciler:AuditReconciler.__init__, ...+30
[WRAPPER] completeness_checker.EvidenceCompletenessError.to_dict
[WRAPPER] completeness_checker.check_evidence_completeness → completeness_checker:EvidenceCompletenessChecker.check, idempotency:InMemoryIdempotencyStore.check, idempotency:RedisIdempotencyStore.check, panel_consistency_checker:PanelConsistencyChecker.check
[WRAPPER] completeness_checker.ensure_evidence_completeness → completeness_checker:EvidenceCompletenessChecker.ensure_complete
[WRAPPER] evidence_facade.EvidenceChain.to_dict → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+14
[WRAPPER] evidence_facade.EvidenceExport.to_dict
[WRAPPER] evidence_facade.EvidenceFacade.__init__
[INTERNAL] evidence_facade.EvidenceFacade._create_link → evidence_facade:EvidenceFacade._hash_data
[LEAF] evidence_facade.EvidenceFacade._hash_data
[ENTRY] evidence_facade.EvidenceFacade.add_evidence → evidence_facade:EvidenceFacade._create_link, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[CANONICAL] evidence_facade.EvidenceFacade.create_chain → evidence_facade:EvidenceFacade._create_link, evidence_facade:EvidenceFacade._hash_data, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] evidence_facade.EvidenceFacade.create_export → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] evidence_facade.EvidenceFacade.get_chain → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] evidence_facade.EvidenceFacade.get_export → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] evidence_facade.EvidenceFacade.list_chains
[LEAF] evidence_facade.EvidenceFacade.list_exports
[SUPERSET] evidence_facade.EvidenceFacade.verify_chain → evidence_facade:EvidenceFacade._hash_data, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] evidence_facade.EvidenceLink.to_dict
[WRAPPER] evidence_facade.VerificationResult.to_dict
[LEAF] evidence_facade.get_evidence_facade
[WRAPPER] evidence_report.EvidenceReportGenerator.__init__ → evidence_report:EvidenceReportGenerator._setup_custom_styles
[LEAF] evidence_report.EvidenceReportGenerator._add_footer
[LEAF] evidence_report.EvidenceReportGenerator._build_certificate_section
[LEAF] evidence_report.EvidenceReportGenerator._build_cover_page
[INTERNAL] evidence_report.EvidenceReportGenerator._build_decision_timeline → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[SUPERSET] evidence_report.EvidenceReportGenerator._build_executive_summary → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] evidence_report.EvidenceReportGenerator._build_factual_reconstruction
[INTERNAL] evidence_report.EvidenceReportGenerator._build_incident_snapshot → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[INTERNAL] evidence_report.EvidenceReportGenerator._build_legal_attestation → evidence_report:EvidenceReportGenerator._compute_report_hash
[SUPERSET] evidence_report.EvidenceReportGenerator._build_policy_evaluation → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[INTERNAL] evidence_report.EvidenceReportGenerator._build_prevention_proof → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] evidence_report.EvidenceReportGenerator._build_remediation
[INTERNAL] evidence_report.EvidenceReportGenerator._build_replay_verification → evidence_report:EvidenceReportGenerator._compute_hash, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] evidence_report.EvidenceReportGenerator._compute_hash
[WRAPPER] evidence_report.EvidenceReportGenerator._compute_report_hash → evidence_report:EvidenceReportGenerator._compute_hash
[LEAF] evidence_report.EvidenceReportGenerator._setup_custom_styles
[CANONICAL] evidence_report.EvidenceReportGenerator.generate → evidence_report:EvidenceReportGenerator._build_certificate_section, evidence_report:EvidenceReportGenerator._build_cover_page, evidence_report:EvidenceReportGenerator._build_decision_timeline, evidence_report:EvidenceReportGenerator._build_executive_summary, evidence_report:EvidenceReportGenerator._build_factual_reconstruction, ...+6
[SUPERSET] evidence_report.generate_evidence_report → evidence_report:EvidenceReportGenerator.generate, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] export_bundle_store.ExportBundleStore.__init__
[ENTRY] export_bundle_store.ExportBundleStore.get_incident → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] export_bundle_store.ExportBundleStore.get_run_by_run_id
[INTERNAL] export_bundle_store.ExportBundleStore.get_trace_steps → logs_domain_store:LogsDomainStore.get_trace_steps
[LEAF] export_bundle_store.ExportBundleStore.get_trace_summary
[LEAF] export_bundle_store.ExportBundleStore.trace_store
[LEAF] export_bundle_store.get_export_bundle_store
[WRAPPER] idempotency.IdempotencyResponse.is_conflict
[WRAPPER] idempotency.IdempotencyResponse.is_duplicate
[WRAPPER] idempotency.IdempotencyResponse.is_new
[WRAPPER] idempotency.InMemoryIdempotencyStore.__init__
[WRAPPER] idempotency.InMemoryIdempotencyStore._make_key
[CANONICAL] idempotency.InMemoryIdempotencyStore.check → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, idempotency:hash_request, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore._make_key, ...+3
[WRAPPER] idempotency.InMemoryIdempotencyStore.delete → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[WRAPPER] idempotency.InMemoryIdempotencyStore.get_status → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore._make_key, replay:InMemoryIdempotencyStore.get, ...+2
[ENTRY] idempotency.InMemoryIdempotencyStore.mark_completed → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[ENTRY] idempotency.InMemoryIdempotencyStore.mark_failed → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[LEAF] idempotency.RedisIdempotencyStore.__init__
[INTERNAL] idempotency.RedisIdempotencyStore._ensure_script_loaded → idempotency:_load_lua_script
[WRAPPER] idempotency.RedisIdempotencyStore._make_key
[INTERNAL] idempotency.RedisIdempotencyStore.check → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._ensure_script_loaded, idempotency:RedisIdempotencyStore._make_key, idempotency:hash_request, replay:InMemoryIdempotencyStore._make_key, ...+1
[INTERNAL] idempotency.RedisIdempotencyStore.delete → idempotency:InMemoryIdempotencyStore._make_key, idempotency:InMemoryIdempotencyStore.delete, idempotency:RedisIdempotencyStore._make_key, replay:IdempotencyStore.delete, replay:InMemoryIdempotencyStore._make_key, ...+3
[ENTRY] idempotency.RedisIdempotencyStore.get_status → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[ENTRY] idempotency.RedisIdempotencyStore.mark_completed → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, idempotency:hash_request, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[ENTRY] idempotency.RedisIdempotencyStore.mark_failed → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[LEAF] idempotency._load_lua_script
[WRAPPER] idempotency.canonical_json
[LEAF] idempotency.get_idempotency_store
[INTERNAL] idempotency.hash_request → certificate:CertificatePayload.canonical_json, idempotency:canonical_json
[WRAPPER] integrity.CaptureFailure.to_dict
[WRAPPER] integrity.IntegrityAssembler.__init__
[LEAF] integrity.IntegrityAssembler._count_evidence
[INTERNAL] integrity.IntegrityAssembler._gather_failures → integrity:IntegrityAssembler._string_to_class
[LEAF] integrity.IntegrityAssembler._resolve_superseded
[LEAF] integrity.IntegrityAssembler._string_to_class
[WRAPPER] integrity.IntegrityAssembler._table_to_class → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[SUPERSET] integrity.IntegrityAssembler.gather → integrity:IntegrityAssembler._count_evidence, integrity:IntegrityAssembler._gather_failures, integrity:IntegrityAssembler._resolve_superseded, integrity:IntegrityAssembler._table_to_class
[LEAF] integrity.IntegrityEvaluation.integrity_status
[LEAF] integrity.IntegrityEvaluator._build_explanation
[LEAF] integrity.IntegrityEvaluator._compute_grade
[LEAF] integrity.IntegrityEvaluator._find_failure
[CANONICAL] integrity.IntegrityEvaluator.evaluate → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+18
[WRAPPER] integrity.IntegrityFacts.has_capture_failures
[WRAPPER] integrity.IntegrityFacts.has_required_evidence
[WRAPPER] integrity.IntegrityFacts.unresolved_failures
[INTERNAL] integrity.compute_integrity_v2 → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+17
[WRAPPER] job_execution.JobAuditEmitter.__init__
[INTERNAL] job_execution.JobAuditEmitter._emit → audit_evidence:MCPAuditEmitter._get_publisher, audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, ...+18
[WRAPPER] job_execution.JobAuditEmitter._generate_event_id
[LEAF] job_execution.JobAuditEmitter._get_publisher
[ENTRY] job_execution.JobAuditEmitter.emit_completed → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_evidence:_hash_value, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, ...+3
[ENTRY] job_execution.JobAuditEmitter.emit_created → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_evidence:_hash_value, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, ...+3
[ENTRY] job_execution.JobAuditEmitter.emit_failed → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] job_execution.JobAuditEmitter.emit_retried → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] job_execution.JobAuditEmitter.emit_started → audit_evidence:MCPAuditEmitter._emit, audit_evidence:MCPAuditEmitter._generate_event_id, audit_ledger_service:AuditLedgerService._emit, audit_ledger_service_async:AuditLedgerServiceAsync._emit, job_execution:JobAuditEmitter._emit, ...+1
[ENTRY] job_execution.JobAuditEvent.__post_init__ → audit_evidence:MCPAuditEvent._compute_integrity_hash, job_execution:JobAuditEvent._compute_integrity_hash
[LEAF] job_execution.JobAuditEvent._compute_integrity_hash
[WRAPPER] job_execution.JobAuditEvent.to_dict
[WRAPPER] job_execution.JobAuditEvent.verify_integrity → audit_evidence:MCPAuditEvent._compute_integrity_hash, job_execution:JobAuditEvent._compute_integrity_hash
[WRAPPER] job_execution.JobProgressTracker.__init__
[LEAF] job_execution.JobProgressTracker._calculate_eta
[INTERNAL] job_execution.JobProgressTracker._emit_progress → audit_evidence:MCPAuditEmitter._get_publisher, audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, ...+21
[LEAF] job_execution.JobProgressTracker._get_publisher
[ENTRY] job_execution.JobProgressTracker.complete → job_execution:JobProgressTracker._emit_progress, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] job_execution.JobProgressTracker.fail → job_execution:JobProgressTracker._emit_progress, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] job_execution.JobProgressTracker.get_progress → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] job_execution.JobProgressTracker.register_callback
[ENTRY] job_execution.JobProgressTracker.start → job_execution:JobProgressTracker._emit_progress
[CANONICAL] job_execution.JobProgressTracker.update → job_execution:JobProgressTracker._calculate_eta, job_execution:JobProgressTracker._emit_progress, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] job_execution.JobRetryManager.__init__
[LEAF] job_execution.JobRetryManager.calculate_delay
[WRAPPER] job_execution.JobRetryManager.clear_history
[WRAPPER] job_execution.JobRetryManager.get_retry_history → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] job_execution.JobRetryManager.record_retry → job_execution:JobRetryManager.calculate_delay
[LEAF] job_execution.JobRetryManager.should_retry
[WRAPPER] job_execution.ProgressUpdate.to_dict
[LEAF] job_execution._hash_value
[LEAF] job_execution.get_job_audit_emitter
[LEAF] job_execution.get_job_progress_tracker
[LEAF] job_execution.get_job_retry_manager
[LEAF] job_execution.reset_job_execution_services
[WRAPPER] logs_domain_store.LogsDomainStore._to_audit_snapshot
[WRAPPER] logs_domain_store.LogsDomainStore._to_export_snapshot
[WRAPPER] logs_domain_store.LogsDomainStore._to_llm_run_snapshot
[WRAPPER] logs_domain_store.LogsDomainStore._to_system_record_snapshot
[INTERNAL] logs_domain_store.LogsDomainStore.get_audit_entry → logs_domain_store:LogsDomainStore._to_audit_snapshot
[INTERNAL] logs_domain_store.LogsDomainStore.get_governance_events → logs_domain_store:LogsDomainStore._to_audit_snapshot
[INTERNAL] logs_domain_store.LogsDomainStore.get_llm_run → logs_domain_store:LogsDomainStore._to_llm_run_snapshot
[LEAF] logs_domain_store.LogsDomainStore.get_replay_window_events
[INTERNAL] logs_domain_store.LogsDomainStore.get_system_record_by_correlation → logs_domain_store:LogsDomainStore._to_system_record_snapshot
[INTERNAL] logs_domain_store.LogsDomainStore.get_system_records_in_window → logs_domain_store:LogsDomainStore._to_system_record_snapshot
[LEAF] logs_domain_store.LogsDomainStore.get_trace_id_for_run
[LEAF] logs_domain_store.LogsDomainStore.get_trace_steps
[SUPERSET] logs_domain_store.LogsDomainStore.list_audit_entries → logs_domain_store:LogsDomainStore._to_audit_snapshot
[CANONICAL] logs_domain_store.LogsDomainStore.list_llm_runs → logs_domain_store:LogsDomainStore._to_llm_run_snapshot
[INTERNAL] logs_domain_store.LogsDomainStore.list_log_exports → logs_domain_store:LogsDomainStore._to_export_snapshot
[SUPERSET] logs_domain_store.LogsDomainStore.list_system_records → logs_domain_store:LogsDomainStore._to_system_record_snapshot
[LEAF] logs_domain_store.get_logs_domain_store
[WRAPPER] logs_facade.LogsFacade.__init__ → logs_domain_store:get_logs_domain_store
[WRAPPER] logs_facade.LogsFacade._snapshot_to_record_result
[ENTRY] logs_facade.LogsFacade.get_audit_access → logs_domain_store:LogsDomainStore.list_audit_entries, logs_facade:LogsFacade.list_audit_entries
[ENTRY] logs_facade.LogsFacade.get_audit_authorization → logs_domain_store:LogsDomainStore.list_audit_entries, logs_facade:LogsFacade.list_audit_entries
[ENTRY] logs_facade.LogsFacade.get_audit_entry → logs_domain_store:LogsDomainStore.get_audit_entry
[ENTRY] logs_facade.LogsFacade.get_audit_exports → logs_domain_store:LogsDomainStore.list_log_exports
[ENTRY] logs_facade.LogsFacade.get_audit_identity → logs_domain_store:LogsDomainStore.list_audit_entries, logs_facade:LogsFacade.list_audit_entries
[LEAF] logs_facade.LogsFacade.get_audit_integrity
[ENTRY] logs_facade.LogsFacade.get_llm_run_envelope → logs_domain_store:LogsDomainStore.get_llm_run
[ENTRY] logs_facade.LogsFacade.get_llm_run_export → logs_domain_store:LogsDomainStore.get_llm_run
[ENTRY] logs_facade.LogsFacade.get_llm_run_governance → logs_domain_store:LogsDomainStore.get_governance_events
[ENTRY] logs_facade.LogsFacade.get_llm_run_replay → logs_domain_store:LogsDomainStore.get_llm_run, logs_domain_store:LogsDomainStore.get_replay_window_events
[ENTRY] logs_facade.LogsFacade.get_llm_run_trace → export_bundle_store:ExportBundleStore.get_trace_steps, logs_domain_store:LogsDomainStore.get_trace_id_for_run, logs_domain_store:LogsDomainStore.get_trace_steps
[ENTRY] logs_facade.LogsFacade.get_system_audit → logs_domain_store:LogsDomainStore.list_system_records, logs_facade:LogsFacade.list_system_records
[ENTRY] logs_facade.LogsFacade.get_system_events → logs_domain_store:LogsDomainStore.list_system_records, logs_facade:LogsFacade.list_system_records
[ENTRY] logs_facade.LogsFacade.get_system_replay → logs_domain_store:LogsDomainStore.get_llm_run, logs_domain_store:LogsDomainStore.get_system_records_in_window
[ENTRY] logs_facade.LogsFacade.get_system_snapshot → logs_domain_store:LogsDomainStore.get_system_record_by_correlation
[WRAPPER] logs_facade.LogsFacade.get_system_telemetry
[SUPERSET] logs_facade.LogsFacade.list_audit_entries → logs_domain_store:LogsDomainStore.list_audit_entries
[CANONICAL] logs_facade.LogsFacade.list_llm_run_records → logs_domain_store:LogsDomainStore.list_llm_runs, logs_facade:LogsFacade._snapshot_to_record_result
[SUPERSET] logs_facade.LogsFacade.list_system_records → logs_domain_store:LogsDomainStore.list_system_records
[LEAF] logs_facade.get_logs_facade
[WRAPPER] logs_read_engine.LogsReadService.__init__
[INTERNAL] logs_read_engine.LogsReadService._get_store → pg_store:get_postgres_trace_store
[WRAPPER] logs_read_engine.LogsReadService.get_trace → logs_read_engine:LogsReadService._get_store, pg_store:PostgresTraceStore.get_trace, traces_store:InMemoryTraceStore.get_trace, traces_store:SQLiteTraceStore.get_trace, traces_store:TraceStore.get_trace
[WRAPPER] logs_read_engine.LogsReadService.get_trace_by_root_hash → logs_read_engine:LogsReadService._get_store, pg_store:PostgresTraceStore.get_trace_by_root_hash, traces_store:SQLiteTraceStore.get_trace_by_root_hash
[WRAPPER] logs_read_engine.LogsReadService.get_trace_count → logs_read_engine:LogsReadService._get_store, pg_store:PostgresTraceStore.get_trace_count, traces_store:SQLiteTraceStore.get_trace_count
[ENTRY] logs_read_engine.LogsReadService.list_traces → logs_read_engine:LogsReadService._get_store, pg_store:PostgresTraceStore.list_traces, traces_store:InMemoryTraceStore.list_traces, traces_store:SQLiteTraceStore.list_traces, traces_store:TraceStore.list_traces
[INTERNAL] logs_read_engine.LogsReadService.search_traces → logs_read_engine:LogsReadService._get_store, pg_store:PostgresTraceStore.search_traces, traces_store:SQLiteTraceStore.search_traces
[LEAF] logs_read_engine.get_logs_read_service
[WRAPPER] mapper.SOC2ControlMapper.__init__
[SUPERSET] mapper.SOC2ControlMapper._create_mapping → mapper:SOC2ControlMapper._determine_compliance_status, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[SUPERSET] mapper.SOC2ControlMapper._determine_compliance_status → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] mapper.SOC2ControlMapper.get_all_applicable_controls → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[CANONICAL] mapper.SOC2ControlMapper.map_incident_to_controls → mapper:SOC2ControlMapper._create_mapping, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[ENTRY] mapper.get_control_mappings_for_incident → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+16
[WRAPPER] panel_consistency_checker.PanelConsistencyChecker.__init__ → panel_consistency_checker:PanelConsistencyChecker._default_rules
[SUPERSET] panel_consistency_checker.PanelConsistencyChecker._check_rule → panel_consistency_checker:PanelConsistencyChecker._evaluate_condition, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] panel_consistency_checker.PanelConsistencyChecker._default_rules
[LEAF] panel_consistency_checker.PanelConsistencyChecker._eval_expr
[SUPERSET] panel_consistency_checker.PanelConsistencyChecker._evaluate_condition → panel_consistency_checker:PanelConsistencyChecker._eval_expr
[CANONICAL] panel_consistency_checker.PanelConsistencyChecker.check → panel_consistency_checker:PanelConsistencyChecker._check_rule
[WRAPPER] panel_consistency_checker.create_consistency_checker
[WRAPPER] panel_response_assembler.PanelResponseAssembler.__init__
[LEAF] panel_response_assembler.PanelResponseAssembler._aggregate_verification
[LEAF] panel_response_assembler.PanelResponseAssembler._determine_panel_authority
[LEAF] panel_response_assembler.PanelResponseAssembler._determine_panel_state
[LEAF] panel_response_assembler.PanelResponseAssembler._slot_to_dict
[ENTRY] panel_response_assembler.PanelResponseAssembler.assemble → panel_response_assembler:PanelResponseAssembler._aggregate_verification, panel_response_assembler:PanelResponseAssembler._determine_panel_authority, panel_response_assembler:PanelResponseAssembler._determine_panel_state, panel_response_assembler:PanelResponseAssembler._slot_to_dict
[WRAPPER] panel_response_assembler.PanelResponseAssembler.assemble_error
[WRAPPER] panel_response_assembler.create_response_assembler
[WRAPPER] pdf_renderer.PDFRenderer.__init__ → pdf_renderer:PDFRenderer._setup_styles
[LEAF] pdf_renderer.PDFRenderer._build_attestation
[LEAF] pdf_renderer.PDFRenderer._build_control_mappings
[LEAF] pdf_renderer.PDFRenderer._build_evidence_cover
[LEAF] pdf_renderer.PDFRenderer._build_evidence_summary
[LEAF] pdf_renderer.PDFRenderer._build_exec_cover
[LEAF] pdf_renderer.PDFRenderer._build_exec_metrics
[LEAF] pdf_renderer.PDFRenderer._build_exec_summary
[LEAF] pdf_renderer.PDFRenderer._build_integrity_section
[LEAF] pdf_renderer.PDFRenderer._build_policy_section
[LEAF] pdf_renderer.PDFRenderer._build_recommendations
[LEAF] pdf_renderer.PDFRenderer._build_soc2_cover
[LEAF] pdf_renderer.PDFRenderer._build_trace_timeline
[LEAF] pdf_renderer.PDFRenderer._setup_styles
[ENTRY] pdf_renderer.PDFRenderer.render_evidence_pdf → pdf_renderer:PDFRenderer._build_evidence_cover, pdf_renderer:PDFRenderer._build_evidence_summary, pdf_renderer:PDFRenderer._build_integrity_section, pdf_renderer:PDFRenderer._build_policy_section, pdf_renderer:PDFRenderer._build_trace_timeline
[ENTRY] pdf_renderer.PDFRenderer.render_executive_debrief_pdf → pdf_renderer:PDFRenderer._build_exec_cover, pdf_renderer:PDFRenderer._build_exec_metrics, pdf_renderer:PDFRenderer._build_exec_summary, pdf_renderer:PDFRenderer._build_recommendations
[CANONICAL] pdf_renderer.PDFRenderer.render_soc2_pdf → pdf_renderer:PDFRenderer._build_attestation, pdf_renderer:PDFRenderer._build_control_mappings, pdf_renderer:PDFRenderer._build_evidence_summary, pdf_renderer:PDFRenderer._build_soc2_cover, pdf_renderer:PDFRenderer._build_trace_timeline
[LEAF] pdf_renderer.get_pdf_renderer
[WRAPPER] pg_store.PostgresTraceStore.__init__
[LEAF] pg_store.PostgresTraceStore._get_pool
[ENTRY] pg_store.PostgresTraceStore.check_idempotency_key → pg_store:PostgresTraceStore._get_pool
[ENTRY] pg_store.PostgresTraceStore.cleanup_old_traces → pg_store:PostgresTraceStore._get_pool
[LEAF] pg_store.PostgresTraceStore.close
[INTERNAL] pg_store.PostgresTraceStore.complete_trace → pg_store:PostgresTraceStore._get_pool
[ENTRY] pg_store.PostgresTraceStore.delete_trace → pg_store:PostgresTraceStore._get_pool
[SUPERSET] pg_store.PostgresTraceStore.get_trace → pg_store:PostgresTraceStore._get_pool
[SUPERSET] pg_store.PostgresTraceStore.get_trace_by_root_hash → logs_read_engine:LogsReadService.get_trace, pg_store:PostgresTraceStore._get_pool, pg_store:PostgresTraceStore.get_trace, traces_store:InMemoryTraceStore.get_trace, traces_store:SQLiteTraceStore.get_trace, ...+1
[INTERNAL] pg_store.PostgresTraceStore.get_trace_count → pg_store:PostgresTraceStore._get_pool
[WRAPPER] pg_store.PostgresTraceStore.list_traces → logs_read_engine:LogsReadService.search_traces, pg_store:PostgresTraceStore.search_traces, traces_store:SQLiteTraceStore.search_traces
[ENTRY] pg_store.PostgresTraceStore.mark_trace_aborted → pg_store:PostgresTraceStore._get_pool
[SUPERSET] pg_store.PostgresTraceStore.record_step → pg_store:PostgresTraceStore._get_pool, pg_store:_status_to_level
[CANONICAL] pg_store.PostgresTraceStore.search_traces → pg_store:PostgresTraceStore._get_pool
[INTERNAL] pg_store.PostgresTraceStore.start_trace → pg_store:PostgresTraceStore._get_pool
[ENTRY] pg_store.PostgresTraceStore.store_trace → pg_store:PostgresTraceStore._get_pool, pg_store:_status_to_level, redact:redact_trace_data, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, ...+1
[LEAF] pg_store._status_to_level
[LEAF] pg_store.get_postgres_trace_store
[WRAPPER] redact.add_redaction_pattern
[WRAPPER] redact.add_sensitive_field
[WRAPPER] redact.is_sensitive_field
[SUPERSET] redact.redact_dict → redact:redact_list, redact:redact_string_value
[LEAF] redact.redact_json_string
[SUPERSET] redact.redact_list → redact:redact_dict, redact:redact_string_value
[LEAF] redact.redact_string_value
[CANONICAL] redact.redact_trace_data → redact:redact_dict, redact:redact_list
[WRAPPER] replay.IdempotencyStore.delete
[WRAPPER] replay.IdempotencyStore.get
[WRAPPER] replay.IdempotencyStore.set
[WRAPPER] replay.IdempotencyViolationError.__init__ → audit_engine:AuditService.__init__, audit_evidence:MCPAuditEmitter.__init__, audit_ledger_service:AuditLedgerService.__init__, audit_ledger_service_async:AuditLedgerServiceAsync.__init__, audit_reconciler:AuditReconciler.__init__, ...+30
[WRAPPER] replay.InMemoryIdempotencyStore.__init__
[WRAPPER] replay.InMemoryIdempotencyStore._make_key
[WRAPPER] replay.InMemoryIdempotencyStore.clear
[INTERNAL] replay.InMemoryIdempotencyStore.delete → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[WRAPPER] replay.InMemoryIdempotencyStore.get → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key, ...+1
[WRAPPER] replay.InMemoryIdempotencyStore.set → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._make_key
[LEAF] replay.RedisIdempotencyStore.__init__
[LEAF] replay.RedisIdempotencyStore._get_client
[WRAPPER] replay.RedisIdempotencyStore._make_key
[INTERNAL] replay.RedisIdempotencyStore.delete → idempotency:InMemoryIdempotencyStore._make_key, idempotency:InMemoryIdempotencyStore.delete, idempotency:RedisIdempotencyStore._make_key, idempotency:RedisIdempotencyStore.delete, replay:IdempotencyStore.delete, ...+4
[INTERNAL] replay.RedisIdempotencyStore.get → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore._make_key, replay:InMemoryIdempotencyStore.get, ...+2
[INTERNAL] replay.RedisIdempotencyStore.set → idempotency:InMemoryIdempotencyStore._make_key, idempotency:RedisIdempotencyStore._make_key, replay:InMemoryIdempotencyStore._make_key, replay:RedisIdempotencyStore._get_client, replay:RedisIdempotencyStore._make_key
[WRAPPER] replay.ReplayEnforcer.__init__
[CANONICAL] replay.ReplayEnforcer.enforce_step → replay:IdempotencyStore.get, replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.get, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.get, ...+2
[ENTRY] replay.ReplayEnforcer.enforce_trace → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, replay:ReplayEnforcer.enforce_step
[INTERNAL] replay.ReplayMismatchError.__init__ → audit_engine:AuditService.__init__, audit_evidence:MCPAuditEmitter.__init__, audit_ledger_service:AuditLedgerService.__init__, audit_ledger_service_async:AuditLedgerServiceAsync.__init__, audit_reconciler:AuditReconciler.__init__, ...+30
[LEAF] replay.get_replay_enforcer
[LEAF] replay.hash_output
[INTERNAL] replay_determinism.CallRecord.to_dict → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+14
[ENTRY] replay_determinism.ModelVersion.from_dict → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] replay_determinism.ModelVersion.to_dict
[WRAPPER] replay_determinism.PolicyDecision.to_dict
[WRAPPER] replay_determinism.ReplayContextBuilder.__init__
[SUPERSET] replay_determinism.ReplayContextBuilder.build_call_record → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, replay_determinism:ReplayValidator.hash_content
[WRAPPER] replay_determinism.ReplayResult.to_dict → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+14
[WRAPPER] replay_determinism.ReplayValidator.__init__
[SUPERSET] replay_determinism.ReplayValidator._compare_policies → replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set
[LEAF] replay_determinism.ReplayValidator._detect_model_drift
[WRAPPER] replay_determinism.ReplayValidator._level_meets_requirement
[SUPERSET] replay_determinism.ReplayValidator._semantic_equivalent → replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set
[LEAF] replay_determinism.ReplayValidator.hash_content
[CANONICAL] replay_determinism.ReplayValidator.validate_replay → replay_determinism:ReplayValidator._compare_policies, replay_determinism:ReplayValidator._detect_model_drift, replay_determinism:ReplayValidator._level_meets_requirement, replay_determinism:ReplayValidator._semantic_equivalent
[WRAPPER] trace_facade.TraceFacade.__init__
[INTERNAL] trace_facade.TraceFacade._emit_ack → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] trace_facade.TraceFacade._store
[WRAPPER] trace_facade.TraceFacade.add_step
[ENTRY] trace_facade.TraceFacade.complete_trace → pg_store:PostgresTraceStore.complete_trace, trace_facade:TraceFacade._emit_ack, traces_store:InMemoryTraceStore.complete_trace, traces_store:SQLiteTraceStore.complete_trace, traces_store:TraceStore.complete_trace
[CANONICAL] trace_facade.TraceFacade.start_trace → pg_store:PostgresTraceStore.start_trace, trace_facade:TraceFacade._emit_ack, traces_store:InMemoryTraceStore.start_trace, traces_store:SQLiteTraceStore.start_trace, traces_store:TraceStore.start_trace
[LEAF] trace_facade.get_trace_facade
[WRAPPER] traces_metrics.TracesMetrics.__init__
[LEAF] traces_metrics.TracesMetrics.measure_request
[LEAF] traces_metrics.TracesMetrics.measure_storage
[WRAPPER] traces_metrics.TracesMetrics.record_idempotency_check
[INTERNAL] traces_metrics.TracesMetrics.record_parity_check → replay:IdempotencyStore.set, replay:InMemoryIdempotencyStore.set, replay:RedisIdempotencyStore.set
[WRAPPER] traces_metrics.TracesMetrics.record_replay_enforcement
[LEAF] traces_metrics.TracesMetrics.record_trace_stored
[LEAF] traces_metrics.get_traces_metrics
[ENTRY] traces_metrics.instrument_parity_check → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, traces_metrics:TracesMetrics.record_parity_check, traces_metrics:get_traces_metrics
[ENTRY] traces_metrics.instrument_replay_check → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, traces_metrics:TracesMetrics.record_replay_enforcement, traces_metrics:get_traces_metrics
[ENTRY] traces_metrics.instrument_trace_request → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, traces_metrics:TracesMetrics.measure_request, traces_metrics:get_traces_metrics
[WRAPPER] traces_models.ParityResult.to_dict
[INTERNAL] traces_models.TraceRecord.determinism_signature → traces_models:TraceStep.determinism_hash
[WRAPPER] traces_models.TraceRecord.failure_count
[ENTRY] traces_models.TraceRecord.from_dict → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get, traces_models:TraceStep.from_dict
[WRAPPER] traces_models.TraceRecord.success_count
[INTERNAL] traces_models.TraceRecord.to_dict → audit_evidence:MCPAuditEvent.to_dict, certificate:Certificate.to_dict, certificate:CertificatePayload.to_dict, completeness_checker:CompletenessCheckResponse.to_dict, completeness_checker:EvidenceCompletenessError.to_dict, ...+15
[WRAPPER] traces_models.TraceRecord.to_summary
[WRAPPER] traces_models.TraceRecord.total_cost_cents
[WRAPPER] traces_models.TraceRecord.total_duration_ms
[INTERNAL] traces_models.TraceStep.determinism_hash → traces_models:_normalize_for_determinism
[INTERNAL] traces_models.TraceStep.from_dict → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[WRAPPER] traces_models.TraceStep.to_dict
[LEAF] traces_models.TraceSummary.to_dict
[LEAF] traces_models._normalize_for_determinism
[CANONICAL] traces_models.compare_traces → traces_models:TraceRecord.determinism_signature, traces_models:TraceStep.determinism_hash
[WRAPPER] traces_store.InMemoryTraceStore.__init__
[INTERNAL] traces_store.InMemoryTraceStore.complete_trace → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] traces_store.InMemoryTraceStore.delete_trace
[INTERNAL] traces_store.InMemoryTraceStore.get_trace → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[INTERNAL] traces_store.InMemoryTraceStore.list_traces → replay:IdempotencyStore.get, replay:InMemoryIdempotencyStore.get, replay:RedisIdempotencyStore.get
[LEAF] traces_store.InMemoryTraceStore.record_step
[WRAPPER] traces_store.InMemoryTraceStore.start_trace
[INTERNAL] traces_store.SQLiteTraceStore.__init__ → traces_store:SQLiteTraceStore._init_db
[WRAPPER] traces_store.SQLiteTraceStore._get_conn
[LEAF] traces_store.SQLiteTraceStore._init_db
[ENTRY] traces_store.SQLiteTraceStore.cleanup_old_traces → traces_store:SQLiteTraceStore._get_conn
[INTERNAL] traces_store.SQLiteTraceStore.complete_trace → traces_store:SQLiteTraceStore._get_conn
[ENTRY] traces_store.SQLiteTraceStore.delete_trace → traces_store:SQLiteTraceStore._get_conn
[WRAPPER] traces_store.SQLiteTraceStore.find_matching_traces → logs_read_engine:LogsReadService.search_traces, pg_store:PostgresTraceStore.search_traces, traces_store:SQLiteTraceStore.search_traces
[INTERNAL] traces_store.SQLiteTraceStore.get_trace → traces_store:SQLiteTraceStore._get_conn
[INTERNAL] traces_store.SQLiteTraceStore.get_trace_by_root_hash → logs_read_engine:LogsReadService.get_trace, pg_store:PostgresTraceStore.get_trace, traces_store:InMemoryTraceStore.get_trace, traces_store:SQLiteTraceStore._get_conn, traces_store:SQLiteTraceStore.get_trace, ...+1
[INTERNAL] traces_store.SQLiteTraceStore.get_trace_count → traces_store:SQLiteTraceStore._get_conn
[INTERNAL] traces_store.SQLiteTraceStore.list_traces → traces_store:SQLiteTraceStore._get_conn
[ENTRY] traces_store.SQLiteTraceStore.record_step → traces_store:SQLiteTraceStore._get_conn
[CANONICAL] traces_store.SQLiteTraceStore.search_traces → traces_store:SQLiteTraceStore._get_conn
[INTERNAL] traces_store.SQLiteTraceStore.start_trace → traces_store:SQLiteTraceStore._get_conn
[ENTRY] traces_store.SQLiteTraceStore.update_trace_determinism → traces_store:SQLiteTraceStore._get_conn
[WRAPPER] traces_store.TraceStore.complete_trace
[WRAPPER] traces_store.TraceStore.delete_trace
[WRAPPER] traces_store.TraceStore.get_trace
[WRAPPER] traces_store.TraceStore.list_traces
[WRAPPER] traces_store.TraceStore.record_step
[WRAPPER] traces_store.TraceStore.start_trace
[WRAPPER] traces_store.generate_correlation_id
[WRAPPER] traces_store.generate_run_id
```
