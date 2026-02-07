# Logs — Software Bible

**Domain:** logs  
**L2 Features:** 44  
**Scripts:** 30  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-07)

- Execution topology: logs L2 routes dispatch via L4 `OperationRegistry` (no direct L2→L5 gaps).
- Clean-arch note: several L5 engines still import `app.models.*` (e.g. audit ledger + PDF rendering) and should be pushed behind L6 drivers to satisfy strict driver/engine purity.
- Verify now: `python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain logs`.

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| audit_engine | L5 | `AuditChecks.check_execution_fidelity` | CANONICAL | 7 | L4:__init__, capture, completeness_checker +1 | YES |
| audit_evidence | L5 | `_redact_sensitive` | SUPERSET | 4 | ?:__init__, audit_ledger_service, audit_ledger_service_async +10 | YES |
| audit_ledger_service | L5 | `AuditLedgerService._emit` | LEAF | 0 | ?:incident_write_engine | L5:incident_write_engine, audit_evidence, audit_ledger_service_async +4 | INTERFACE |
| audit_reconciler | L5 | `AuditReconciler.reconcile` | CANONICAL | 2 | ?:run_orchestration_kernel, capture, completeness_checker +1 | YES |
| certificate | L5 | `CertificateService.export_certificate` | SUPERSET | 3 | ?:guard | ?:certificate | L4:logs_handler | ?:apply | ?:mypy_zones, audit_evidence, capture +9 | YES |
| completeness_checker | L5 | `EvidenceCompletenessChecker.check` | CANONICAL | 6 | ?:__init__, audit_evidence, capture +8 | **OVERLAP** |
| evidence_facade | L5 | `EvidenceFacade.create_chain` | CANONICAL | 1 | L5:__init__ | L4:logs_handler, audit_evidence, capture +8 | YES |
| evidence_report | L5 | `EvidenceReportGenerator.generate` | CANONICAL | 1 | ?:guard | L4:logs_handler | ?:apply | ?:mypy_zones, capture, completeness_checker +1 | YES |
| logs_facade | L5 | `LogsFacade.list_llm_run_records` | CANONICAL | 7 | ?:logs | L5:__init__ | L4:logs_handler, capture, completeness_checker +1 | YES |
| logs_read_engine | L5 | `LogsReadService._get_store` | INTERNAL | 1 | L3:customer_logs_adapter | L5:customer_logs_adapter, capture, completeness_checker +3 | YES |
| mapper | L5 | `SOC2ControlMapper.map_incident_to_controls` | CANONICAL | 1 | ?:__init__ | ?:control_registry | L4:control_registry, capture, completeness_checker +1 | YES |
| panel_response_assembler | L5 | `PanelResponseAssembler._aggregate_verification` | LEAF | 0 | ?:__init__ | ?:ai_console_panel_engine | L5:ai_console_panel_engine, capture, completeness_checker +1 | YES |
| pdf_renderer | L5 | `PDFRenderer.render_soc2_pdf` | CANONICAL | 1 | ?:incidents | L7:export_bundles | L4:logs_handler, capture, completeness_checker +1 | YES |
| redact | L5 | `redact_trace_data` | CANONICAL | 8 | ?:traces | ?:pg_store | ?:__init__ | L6:pg_store | L2:traces | ?:mypy_zones, pg_store | YES |
| replay_determinism | L5 | `ReplayValidator.validate_replay` | CANONICAL | 4 | ?:guard | ?:certificate | ?:replay_determinism | L5:certificate | L2:guard | L4:logs_handler, audit_evidence, capture +8 | YES |
| trace_facade | L5 | `TraceFacade.start_trace` | CANONICAL | 1 | ?:transaction_coordinator | ?:__init__ | ?:trace_facade | L5:__init__ | L4:transaction_coordinator, capture, completeness_checker +1 | YES |
| traces_metrics | L5 | `TracesMetrics.measure_request` | LEAF | 0 | ?:__init__, capture, completeness_checker +1 | YES |
| traces_models | L5 | `compare_traces` | CANONICAL | 7 | audit_evidence, certificate, evidence_facade +4 | YES |
| audit_ledger_service_async | L6 | `AuditLedgerServiceAsync._emit` | LEAF | 0 | ?:policy_proposal | ?:policy_rules_service | ?:policy_limits_service | L5:policy_limits_engine | L5:policy_rules_engine | L5:policy_proposal_engine, audit_evidence, audit_ledger_service +4 | INTERFACE |
| bridges_driver | L6 | `record_policy_activation` | LEAF | 0 | L6:__init__ | L5:bridges | YES |
| capture | L6 | `capture_integrity_evidence` | CANONICAL | 1 | ?:workers | ?:runner | ?:__init__ | ?:executor | L2:workers | ?:inject_synthetic, completeness_checker, replay | YES |
| export_bundle_store | L6 | `ExportBundleStore.get_incident` | ENTRY | 1 | L6:__init__ | L3:export_bundle_adapter, capture, completeness_checker +2 | YES |
| idempotency | L6 | `InMemoryIdempotencyStore.check` | CANONICAL | 2 | ?:__init__ | ?:job_queue_worker | ?:main | ?:base | ?:skills_base, capture, certificate +2 | **OVERLAP** |
| integrity | L6 | `IntegrityEvaluator.evaluate` | CANONICAL | 2 | ?:logs | ?:__init__ | ?:capture | L6:capture | L2:logs | ?:SDSR_output_emit_AURORA_L2, audit_evidence, capture +8 | YES |
| job_execution | L6 | `JobProgressTracker.update` | CANONICAL | 8 | ?:__init__, audit_evidence, audit_ledger_service +10 | YES |
| logs_domain_store | L6 | `LogsDomainStore.list_llm_runs` | CANONICAL | 7 | L6:__init__ | L5:logs_facade, export_bundle_store, logs_facade | YES |
| panel_consistency_checker | L6 | `PanelConsistencyChecker.check` | CANONICAL | 3 | ?:__init__ | ?:panel_metrics_emitter | ?:panel_response_assembler | ?:ai_console_panel_engine | L5:ai_console_panel_engine | L5:panel_response_assembler, capture, completeness_checker +1 | **OVERLAP** |
| pg_store | L6 | `PostgresTraceStore.search_traces` | CANONICAL | 8 | ?:traces | ?:runner | ?:__init__ | ?:logs_read_service | ?:replay | L5:logs_read_engine | L2:traces | ?:apply | ?:mypy_zones | ?:test_trace_fail_closed, capture, completeness_checker +4 | **OVERLAP** |
| replay | L6 | `ReplayEnforcer.enforce_step` | CANONICAL | 8 | ?:logs | ?:runtime | ?:workers | ?:execution_plan | ?:__init__ | ?:main | L2:logs | L2:runtime | L2:workers | L4:logs_handler, audit_engine, capture +16 | YES |
| traces_store | L6 | `SQLiteTraceStore.search_traces` | CANONICAL | 8 | capture, completeness_checker, logs_read_engine +3 | **OVERLAP** |

## Uncalled Functions

Functions with no internal or external callers detected.
May be: dead code, missing wiring, or entry points not yet traced.

- `traces_models.TraceRecord.failure_count`
- `traces_models.TraceRecord.from_dict`
- `traces_models.TraceRecord.success_count`
- `traces_models.TraceRecord.to_summary`
- `traces_models.TraceRecord.total_cost_cents`
- `traces_models.TraceRecord.total_duration_ms`
- `traces_models.compare_traces`
- `traces_store.InMemoryTraceStore.delete_trace`
- `traces_store.InMemoryTraceStore.record_step`
- `traces_store.SQLiteTraceStore.cleanup_old_traces`
- `traces_store.SQLiteTraceStore.delete_trace`
- `traces_store.SQLiteTraceStore.find_matching_traces`
- `traces_store.SQLiteTraceStore.record_step`
- `traces_store.SQLiteTraceStore.update_trace_determinism`
- `traces_store.TraceStore.delete_trace`
- `traces_store.TraceStore.record_step`
- `traces_store.generate_correlation_id`
- `traces_store.generate_run_id`

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `completeness_checker` — canonical: `EvidenceCompletenessChecker.check` (CANONICAL)
- `idempotency` — canonical: `InMemoryIdempotencyStore.check` (CANONICAL)
- `panel_consistency_checker` — canonical: `PanelConsistencyChecker.check` (CANONICAL)
- `pg_store` — canonical: `PostgresTraceStore.search_traces` (CANONICAL)
- `traces_store` — canonical: `SQLiteTraceStore.search_traces` (CANONICAL)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 44 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### DELETE /api-keys/{key_id}
```
L2:tenants.revoke_api_key → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### DELETE /{run_id}
```
L2:traces.delete_trace → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /anomalies
```
L2:cost_intelligence.get_anomalies → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /api-keys
```
L2:tenants.list_api_keys → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /budgets
```
L2:cost_intelligence.list_budgets → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /by-feature
```
L2:cost_intelligence.get_costs_by_feature → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /by-hash/{root_hash}
```
L2:traces.get_trace_by_hash → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /by-model
```
L2:cost_intelligence.get_costs_by_model → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /by-user
```
L2:cost_intelligence.get_costs_by_user → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /compare/{run_id1}/{run_id2}
```
L2:traces.compare_traces → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /dashboard
```
L2:cost_intelligence.get_cost_dashboard → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /export
```
L2:guard_logs.export_logs → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /features
```
L2:cost_intelligence.list_feature_tags → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /idempotency/{idempotency_key}
```
L2:traces.check_idempotency → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /mismatches
```
L2:traces.list_all_mismatches → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /projection
```
L2:cost_intelligence.get_projection → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /runs
```
L2:tenants.list_runs → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /summary
```
L2:cost_intelligence.get_cost_summary → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /tenant
```
L2:tenants.get_current_tenant → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /tenant/health
```
L2:tenants.tenant_health → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /tenant/quota/runs
```
L2:tenants.check_run_quota → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /tenant/quota/tokens
```
L2:tenants.check_token_quota → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /tenant/usage
```
L2:tenants.get_tenant_usage → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /workers
```
L2:tenants.list_workers → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /workers/available
```
L2:tenants.list_available_workers_for_tenant → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /workers/{worker_id}
```
L2:tenants.get_worker_details → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /workers/{worker_id}/config
```
L2:tenants.get_worker_config → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /{log_id}
```
L2:guard_logs.get_log → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /{run_id}
```
L2:traces.get_trace → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### GET /{trace_id}/mismatches
```
L2:traces.list_trace_mismatches → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /anomalies/detect
```
L2:cost_intelligence.trigger_anomaly_detection → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /api-keys
```
L2:tenants.create_api_key → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /budgets
```
L2:cost_intelligence.create_or_update_budget → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /cleanup
```
L2:traces.cleanup_old_traces → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /features
```
L2:cost_intelligence.create_feature_tag → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /mismatches/bulk-report
```
L2:traces.bulk_report_mismatches → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /record
```
L2:cost_intelligence.record_cost → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /{trace_id}/mismatch
```
L2:traces.report_mismatch → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### POST /{trace_id}/mismatches/{mismatch_id}/resolve
```
L2:traces.resolve_mismatch → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### PUT /features/{tag}
```
L2:cost_intelligence.update_feature_tag → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### PUT /workers/{worker_id}/config
```
L2:tenants.set_worker_config → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### list_logs
```
L2:guard_logs.list_logs → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### list_traces
```
L2:traces.list_traces → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

#### store_trace
```
L2:traces.store_trace → L4:logs_handler → L6:audit_ledger_service_async.AuditLedgerServiceAsync._emit
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `AuditChecks.check_execution_fidelity` | audit_engine | CANONICAL | 7 | 9 | yes | replay:IdempotencyStore.get | replay:IdempotencyStore.set |  |
| `AuditChecks.check_health_preservation` | audit_engine | SUPERSET | 4 | 7 | no | audit_engine:AuditChecks._is_health_degraded | replay:Idempo |
| `AuditChecks.check_no_unauthorized_mutations` | audit_engine | SUPERSET | 2 | 8 | no | replay:IdempotencyStore.get | replay:IdempotencyStore.set |  |
| `AuditChecks.check_rollback_availability` | audit_engine | SUPERSET | 4 | 8 | no | replay:IdempotencyStore.get | replay:InMemoryIdempotencyStor |
| `AuditChecks.check_scope_compliance` | audit_engine | SUPERSET | 2 | 6 | yes | replay:IdempotencyStore.get | replay:IdempotencyStore.set |  |
| `AuditReconciler.reconcile` | audit_reconciler | CANONICAL | 2 | 19 | no | audit_reconciler:AuditReconciler._record_metrics |
| `CertificateService.export_certificate` | certificate | SUPERSET | 3 | 1 | no | audit_evidence:MCPAuditEvent.to_dict | certificate:Certifica |
| `EvidenceCompletenessChecker.check` | completeness_checker | CANONICAL | 6 | 12 | yes | completeness_checker:EvidenceCompletenessChecker.get_require |
| `EvidenceCompletenessChecker.is_field_present` | completeness_checker | SUPERSET | 3 | 5 | no | completeness_checker:EvidenceCompletenessChecker.get_field_v |
| `EvidenceCompletenessChecker.should_allow_export` | completeness_checker | SUPERSET | 2 | 4 | no | completeness_checker:EvidenceCompletenessChecker.check | ide |
| `EvidenceFacade.create_chain` | evidence_facade | CANONICAL | 1 | 9 | no | evidence_facade:EvidenceFacade._create_link | evidence_facad |
| `EvidenceFacade.verify_chain` | evidence_facade | SUPERSET | 3 | 6 | no | evidence_facade:EvidenceFacade._hash_data | replay:Idempoten |
| `EvidenceReportGenerator._build_executive_summary` | evidence_report | SUPERSET | 2 | 25 | no | replay:IdempotencyStore.get | replay:InMemoryIdempotencyStor |
| `EvidenceReportGenerator._build_policy_evaluation` | evidence_report | SUPERSET | 4 | 16 | no | replay:IdempotencyStore.get | replay:InMemoryIdempotencyStor |
| `EvidenceReportGenerator.generate` | evidence_report | CANONICAL | 1 | 21 | no | evidence_report:EvidenceReportGenerator._build_certificate_s |
| `InMemoryIdempotencyStore.check` | idempotency | CANONICAL | 2 | 6 | no | idempotency:InMemoryIdempotencyStore._make_key | idempotency |
| `IntegrityAssembler.gather` | integrity | SUPERSET | 2 | 5 | no | integrity:IntegrityAssembler._count_evidence | integrity:Int |
| `IntegrityEvaluator.evaluate` | integrity | CANONICAL | 2 | 10 | no | audit_evidence:MCPAuditEvent.to_dict | certificate:Certifica |
| `JobProgressTracker.update` | job_execution | CANONICAL | 8 | 13 | no | job_execution:JobProgressTracker._calculate_eta | job_execut |
| `LogsDomainStore.list_audit_entries` | logs_domain_store | SUPERSET | 5 | 14 | yes | logs_domain_store:LogsDomainStore._to_audit_snapshot |
| `LogsDomainStore.list_llm_runs` | logs_domain_store | CANONICAL | 7 | 16 | yes | logs_domain_store:LogsDomainStore._to_llm_run_snapshot |
| `LogsDomainStore.list_system_records` | logs_domain_store | SUPERSET | 6 | 15 | yes | logs_domain_store:LogsDomainStore._to_system_record_snapshot |
| `LogsFacade.list_audit_entries` | logs_facade | SUPERSET | 5 | 9 | no | logs_domain_store:LogsDomainStore.list_audit_entries |
| `LogsFacade.list_llm_run_records` | logs_facade | CANONICAL | 7 | 11 | no | logs_domain_store:LogsDomainStore.list_llm_runs | logs_facad |
| `LogsFacade.list_system_records` | logs_facade | SUPERSET | 5 | 9 | no | logs_domain_store:LogsDomainStore.list_system_records |
| `PDFRenderer.render_soc2_pdf` | pdf_renderer | CANONICAL | 1 | 15 | no | pdf_renderer:PDFRenderer._build_attestation | pdf_renderer:P |
| `PanelConsistencyChecker._check_rule` | panel_consistency_checker | SUPERSET | 4 | 8 | no | panel_consistency_checker:PanelConsistencyChecker._evaluate_ |
| `PanelConsistencyChecker._evaluate_condition` | panel_consistency_checker | SUPERSET | 4 | 5 | no | panel_consistency_checker:PanelConsistencyChecker._eval_expr |
| `PanelConsistencyChecker.check` | panel_consistency_checker | CANONICAL | 3 | 7 | no | panel_consistency_checker:PanelConsistencyChecker._check_rul |
| `PostgresTraceStore.get_trace` | pg_store | SUPERSET | 4 | 2 | no | pg_store:PostgresTraceStore._get_pool |
| `PostgresTraceStore.get_trace_by_root_hash` | pg_store | SUPERSET | 2 | 2 | no | logs_read_engine:LogsReadService.get_trace | pg_store:Postgr |
| `PostgresTraceStore.record_step` | pg_store | SUPERSET | 3 | 7 | yes | pg_store:PostgresTraceStore._get_pool | pg_store:_status_to_ |
| `PostgresTraceStore.search_traces` | pg_store | CANONICAL | 8 | 14 | no | pg_store:PostgresTraceStore._get_pool |
| `ReplayContextBuilder.build_call_record` | replay_determinism | SUPERSET | 2 | 9 | no | replay:IdempotencyStore.get | replay:InMemoryIdempotencyStor |
| `ReplayEnforcer.enforce_step` | replay | CANONICAL | 8 | 11 | no | replay:IdempotencyStore.get | replay:IdempotencyStore.set |  |
| `ReplayValidator._compare_policies` | replay_determinism | SUPERSET | 5 | 6 | no | replay:IdempotencyStore.set | replay:InMemoryIdempotencyStor |
| `ReplayValidator._semantic_equivalent` | replay_determinism | SUPERSET | 3 | 5 | no | replay:IdempotencyStore.set | replay:InMemoryIdempotencyStor |
| `ReplayValidator.validate_replay` | replay_determinism | CANONICAL | 4 | 13 | no | replay_determinism:ReplayValidator._compare_policies | repla |
| `SOC2ControlMapper._create_mapping` | mapper | SUPERSET | 3 | 9 | no | mapper:SOC2ControlMapper._determine_compliance_status | repl |
| `SOC2ControlMapper._determine_compliance_status` | mapper | SUPERSET | 9 | 8 | no | replay:IdempotencyStore.get | replay:InMemoryIdempotencyStor |
| `SOC2ControlMapper.map_incident_to_controls` | mapper | CANONICAL | 1 | 4 | no | mapper:SOC2ControlMapper._create_mapping | replay:Idempotenc |
| `SQLiteTraceStore.search_traces` | traces_store | CANONICAL | 8 | 2 | no | traces_store:SQLiteTraceStore._get_conn |
| `TraceFacade.start_trace` | trace_facade | CANONICAL | 1 | 6 | no | pg_store:PostgresTraceStore.start_trace | trace_facade:Trace |
| `_redact_sensitive` | audit_evidence | SUPERSET | 4 | 4 | no | audit_evidence:_contains_sensitive |
| `capture_integrity_evidence` | capture | CANONICAL | 1 | 5 | yes | capture:compute_integrity | replay:IdempotencyStore.get | re |
| `compare_traces` | traces_models | CANONICAL | 7 | 6 | no | traces_models:TraceRecord.determinism_signature | traces_mod |
| `create_audit_input_from_evidence` | audit_engine | SUPERSET | 2 | 9 | no | replay:IdempotencyStore.get | replay:InMemoryIdempotencyStor |
| `generate_evidence_report` | evidence_report | SUPERSET | 2 | 6 | no | evidence_report:EvidenceReportGenerator.generate | replay:Id |
| `redact_dict` | redact | SUPERSET | 5 | 4 | no | redact:redact_list | redact:redact_string_value |
| `redact_list` | redact | SUPERSET | 4 | 4 | no | redact:redact_dict | redact:redact_string_value |
| `redact_trace_data` | redact | CANONICAL | 8 | 5 | no | redact:redact_dict | redact:redact_list |

## Wrapper Inventory

_138 thin delegation functions._

- `audit_ledger_service.AuditLedgerService.__init__` → ?
- `audit_ledger_service.AuditLedgerService.incident_acknowledged` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service.AuditLedgerService.incident_manually_closed` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service.AuditLedgerService.incident_resolved` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.__init__` → ?
- `audit_ledger_service_async.AuditLedgerServiceAsync.limit_breached` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.limit_created` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.limit_updated` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_proposal_approved` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_proposal_rejected` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_created` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_modified` → audit_evidence:MCPAuditEmitter._emit
- `audit_ledger_service_async.AuditLedgerServiceAsync.policy_rule_retired` → audit_evidence:MCPAuditEmitter._emit
- `audit_reconciler.AuditReconciler.__init__` → ?
- `audit_engine.AuditService.__init__` → ?
- `audit_engine.AuditService.version` → ?
- `integrity.CaptureFailure.to_dict` → ?
- `certificate.Certificate.to_dict` → audit_evidence:MCPAuditEvent.to_dict
- `certificate.Certificate.to_json` → audit_evidence:MCPAuditEvent.to_dict
- `certificate.CertificatePayload.canonical_json` → audit_evidence:MCPAuditEvent.to_dict
- `certificate.CertificatePayload.to_dict` → ?
- `certificate.CertificateService._verify_signature` → certificate:CertificateService._sign
- `completeness_checker.CompletenessCheckResponse.to_dict` → ?
- `evidence_facade.EvidenceChain.to_dict` → audit_evidence:MCPAuditEvent.to_dict
- `completeness_checker.EvidenceCompletenessChecker.__init__` → ?
- `completeness_checker.EvidenceCompletenessChecker.strict_mode` → ?
- `completeness_checker.EvidenceCompletenessChecker.validation_enabled` → ?
- `completeness_checker.EvidenceCompletenessError.to_dict` → ?
- `capture.EvidenceContextError.__init__` → audit_engine:AuditService.__init__
- `evidence_facade.EvidenceExport.to_dict` → ?
- _...and 108 more_

---

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `logs_handler.py` | `LogsQueryHandler`: Split into `async_dispatch` (17 methods) + `sync_dispatch` (2 methods: `get_system_telemetry`, `get_audit_integrity`). Eliminated `iscoroutinefunction`. `LogsEvidenceHandler`: explicit map (8 methods). `LogsCertificateHandler`: explicit sync map (4 methods). `LogsPdfHandler`: explicit sync map (3 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-507 Law 0 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `audit_ledger_engine` (L5) | Now imported by legacy `app/services/incident_write_engine.py` as transitional `services→hoc` dependency. Import path: `app.hoc.cus.logs.L5_engines.audit_ledger_engine.AuditLedgerService`. Previous broken path `app.services.logs.audit_ledger_service` was abolished during HOC migration. | PIN-507 Law 0 |
| `audit_ledger_driver` (L6) | Now imported by 3 legacy services (`policy_limits_service`, `policy_rules_service`, `policy_proposal`) as transitional `services→hoc` dependency. Previous broken path `app.services.logs.audit_ledger_service_async` was abolished. | PIN-507 Law 0 |
| `export_bundle_store` (L6) | Fixed import: `Incident` model moved from `app.db` → `app.models.killswitch`. L6→L7 boundary comment added. | PIN-507 Law 0 |
| `L5_engines/__init__.py` | Fixed wrong class name: `LogsDomainFacade` → `LogsFacade`, `get_logs_domain_facade` → `get_logs_facade`. Added eager-import warning docstring. | PIN-507 Law 0 |
| `L6_drivers/__init__.py` | Added eager-import warning docstring. | PIN-507 Law 0 |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

| File | Change | Reference |
|------|--------|-----------|
| `api/cus/logs/cost_intelligence.py:43` | Import swapped to analytics L5 engine (`CostWriteService`) | PIN-513 Phase 7, Step 1 |
| `api/cus/logs/cost_intelligence.py:1240` | Import swapped to analytics L5 engine (`run_anomaly_detection`) | PIN-513 Phase 7, Step 2 |
| `int/logs/drivers/reactor_initializer.py:59` | Import swapped: `app.services.governance.profile` → `app.hoc.cus.hoc_spine.authority.profile_policy_mode` | PIN-513 Phase 7, Step 8 |

**Impact:** 3 imports fully severed. Zero TRANSITIONAL tags remain in logs domain.

## PIN-513 Phase 8 — Zero-Caller Wiring (2026-02-01)

| Component | L4 Owner | Action |
|-----------|----------|--------|
| `replay_driver` (L6) | **NEW** `hoc_spine/orchestrator/coordinators/replay_coordinator.py` | L4 coordinator: `enforce_step()` and `enforce_trace()` delegate to `ReplayEnforcer` singleton via lazy import |
| `job_execution_driver` (L6) | **NEW** `hoc_spine/orchestrator/coordinators/execution_coordinator.py` | L4 coordinator: `should_retry()`, `track_progress()`, `emit_audit_created/completed/failed()` delegate to `JobRetryManager`, `JobProgressTracker`, `JobAuditEmitter` |

**Signature audit fix:** `replay_coordinator.py` — changed `enforce_step` from individual params to `(step: dict, execute_fn, tenant_id)`; `enforce_trace` from `(steps, tenant_id)` to `(trace: dict, step_executor, tenant_id)`. `execution_coordinator.py` — `JobRetryManager()` no-arg (was `job_id`); `should_retry(job_id, error, attempt_number)` matched; `JobProgressTracker()`/`JobAuditEmitter()` no-arg (were `job_id`); audit split into `emit_created/completed/failed`. All 17 call sites verified.

## PIN-513 Phase B & C — Logs Domain Changes (2026-02-01)

Phase B: Fixed broken import in `traces_store.py` (`from .models import` → `from app.hoc.cus.logs.L5_engines.traces_models import`).

Phase C (Legacy Cutover):
- `app/traces/` and `app/evidence/` callers rewired to HOC logs domain
- logs_read_engine.py: Rewired 2 imports (traces.models→traces_models, traces.pg_store→pg_store)
- traces_store.py: Import fix (Phase B)
- External callers rewired: runtime/replay.py, hoc/int/platform/engines/replay.py, incidents/L6_drivers/export_bundle_driver.py, stores/__init__.py, api/workers.py, hoc/api/cus/policies/workers.py, skills/executor.py (×2), worker/runner.py, hoc/int/agent/engines/executor.py (×2), hoc/int/analytics/engines/runner.py

---

### PIN-513 Phase 9 Batch 3B Amendment (2026-02-01)

**Scope:** 20 logs symbols reclassified.

| Category | Count | Details |
|----------|-------|---------|
| CSV stale (already wired) | 6 | job_execution_driver (4) via execution_coordinator, replay_driver (1) via replay_coordinator, hash_output (1) |
| PURE_UTILITY | 3 | traces_models.compare_traces, traces_store.generate_correlation_id, traces_store.generate_run_id |
| WIRED (new) | 11 | capture_driver (7) via evidence_coordinator, integrity_driver (1) via integrity_handler, idempotency_driver (3) via idempotency_handler |

**Files created:**
- `hoc_spine/orchestrator/coordinators/evidence_coordinator.py` — L4: evidence capture orchestration
- `hoc_spine/orchestrator/handlers/integrity_handler.py` — L4: V2 integrity computation
- `hoc_spine/orchestrator/handlers/idempotency_handler.py` — L4: request idempotency

### PIN-513 Phase 9 Batch 5 Amendment (2026-02-01)

**CI invariant hardening — logs domain impact:**

- No logs files appear in Batch 5 frozen allowlists
- `traces_store.py` L6→L5 violation (imports traces_models from L5_engines) already caught by existing check 5

**Total CI checks:** 30 system-wide.

---

## PIN-519 System Run Introspection (2026-02-03)

### New Files

| File | Layer | Purpose | Reference |
|------|-------|---------|-----------|
| `audit_ledger_read_driver.py` | L6 | Read-only audit ledger queries for signal feedback | PIN-519 |

### Modified Files

| File | Change | Reference |
|------|--------|-----------|
| `audit_ledger_driver.py` | Added `signal_acknowledged()`, `signal_suppressed()`, `signal_escalated()` methods | PIN-519 |

### New Capabilities Exposed via LogsBridge

| Capability | L6 Driver | Purpose |
|------------|-----------|---------|
| `traces_store_capability()` | `traces_store.SQLiteTraceStore` | Run-scoped trace queries |
| `audit_ledger_read_capability()` | `audit_ledger_read_driver.AuditLedgerReadDriver` | Signal feedback queries |

### Script Registry Addition

| Script | Layer | Canonical Function | Role | Reference |
|--------|-------|--------------------|------|-----------|
| `audit_ledger_read_driver` | L6 | `AuditLedgerReadDriver.get_signal_feedback` | CANONICAL | PIN-519 |
