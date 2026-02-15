# HOC Usecase to Code Linkage

## Canonical Root
- `backend/app/hoc/docs/architecture/usecases/`

## Governance Baseline
- Enforce L2.1 Facade -> L2 API -> L4 `hoc_spine` -> L5 -> L6 -> L7.
- No direct L2 -> L5/L6 business calls.
- Canonical onboarding authorities:
- `account`, `integrations`, `api_keys` own onboarding setup.
- `policies` owns runtime governance only.

## UC-001: LLM Run Monitoring
- Audience: `cust,int,fdr`
- Status: `GREEN`

### Verified (GREEN closure):

**Endpoint-to-Operation Evidence (Phase 2):**
- 48 canonical routes mapped across 3 audiences (22 CUS, 21 INT, 5 FDR)
- Verifier script: `scripts/verification/uc001_route_operation_map_check.py` — 100/100 checks pass
- All CUS routes dispatch through L4 registry (`get_operation_registry()`)
- INT routes: recovery, SDK, platform, agents all dispatch through L4; onboarding uses L4 async helpers
- FDR routes: cost_ops dispatches through L4; founder_actions use DIRECT dispatch (documented design decision)

**Event Schema Contract (Phase 1):**
- Contract module: `app/hoc/cus/hoc_spine/authority/event_schema_contract.py`
- Required fields: event_id, event_type, tenant_id, project_id, actor_type, actor_id, decision_owner, sequence_no, schema_version
- Runtime validation wired into 3 authoritative emitters: lifecycle_provider, runtime_switch, onboarding_handler
- CI check 36 (`check_event_schema_contract_usage`) enforces contract usage in all known emitters
- 12 tests in `tests/governance/t4/test_event_schema_contract.py` — all pass

**CI/Test Guardrails:**
- 36 CI checks pass (0 blocking, 0 advisory)
- 34 governance tests pass across 3 test files
- uc001_uc002_validation.py: 19/19 pass

## UC-002: Customer Onboarding
- Audience: `cust`
- Status: `GREEN`

### Verified (GREEN closure):

**Ownership Migration (prior phases):**
- Ownership migration completed to canonical L2 files:
  - `backend/app/hoc/api/cus/account/aos_accounts.py`
  - `backend/app/hoc/api/cus/integrations/aos_cus_integrations.py`
  - `backend/app/hoc/api/cus/api_keys/aos_api_key.py`
- Tombstones removed from `backend/app/hoc/api/cus/policies/`.
- API key writes moved under `api_keys` domain.
- Integrations L2 session wiring fixed for all 6 write endpoints (sync_session DI).
- Handler contract stripping (`_STRIP_PARAMS`) confirmed in all 3 integrations handlers.

**Activation Predicate Hardening (Phase 4):**
- Predicate uses ONLY persistent DB evidence: api_keys, cus_integrations, sdk_attestations
- Full 2^4 (16 combination) test matrix: only (True,True,True,True) passes
- Regression test proves no indirect cache coupling (connector_registry_driver import has no effect)
- CI check 35 (`check_activation_no_cache_import`) blocks cache imports in activation section
- Authority contract comments in `onboarding_handler.py` and `connector_registry_driver.py`
- 11 tests in `tests/governance/t4/test_activation_predicate_authority.py` — all pass

**API Key Surface Policy Lock (Phase 3):**
- Split URLs are intentional and canonical (closed — not deferred):
  - `/api-keys` (read) → `aos_api_key.py` — NO onboarding advancement
  - `/tenant/api-keys` (write) → `api_key_writes.py` — POST triggers `_maybe_advance_to_api_key_created`
- Both resolve to `IDENTITY_VERIFIED` in onboarding gate (no COMPLETE default trap)
- Invariant comments in both routers + onboarding_policy.py
- 11 tests in `tests/governance/t4/test_api_key_surface_policy.py` — all pass

**Event Schema Contract (Phase 1):**
- Onboarding state transitions emit contract-validated events (`_emit_validated_onboarding_event`)
- Founder force-complete override logged as WARNING (does not bypass contract)

**SDK/Migration:**
- SDK attestation migration: `127_create_sdk_attestations.py`
- `ConnectorRegistry` documented as runtime cache; `cus_integrations` table is persistent SOT

### Resolved blockers:
1. Integrations L2 session contract — FIXED
2. Connector source-of-truth — RESOLVED (cus_integrations = persistent SOT)
3. Canonical docs reconciliation — COMPLETE
4. Event schema enforcement — COMPLETE (Phase 1)
5. API key URL policy — CLOSED (split is intentional, not deferred)
6. Activation predicate hardening — COMPLETE (Phase 4)

### Iteration-3 ASSIGN Anchors (2026-02-15):
- `app/hoc/cus/hoc_spine/authority/onboarding_policy.py` — ASSIGN UC-002: Endpoint-to-state gating + 4-condition activation predicate
- `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` — ASSIGN UC-002: `account.onboarding.query` + `account.onboarding.advance` operations
- `app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` — ASSIGN UC-002: Runtime connector cache (CACHE ONLY — activation authority is DB tables only, CI check 35 enforced)

## UC-003: Ingest Run + Deterministic Trace
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-02):
- Replay mode columns (`replay_mode`, `replay_attempt_id`, `replay_artifact_version`, `trace_completeness_status`) wired in L6 `pg_store.py` INSERT and SELECT
- L5 `trace_api_engine.py` forwards replay params to L6 driver
- L5 `traces_models.py` TraceRecord includes all 4 replay fields in `to_dict()`/`from_dict()`
- Deterministic read verifier: 34/34 PASS (includes `determinism.replay.*` checks)
- Storage verifier: `storage.replay_wiring.insert` PASS, `storage.replay_wiring.select` PASS

### Evidence Queries:
- `SELECT replay_mode, replay_attempt_id, replay_artifact_version, trace_completeness_status FROM aos_traces WHERE run_id = ?`

## UC-004: Runtime Controls Evaluation
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-03):
- `ControlsEvaluationEvidenceHandler` registered as `controls.evaluation_evidence`
- L6 `evaluation_evidence_driver.py` persists per-run binding: `control_set_version`, `override_ids_applied`, `resolver_version`, `decision`
- Event: `controls.EvaluationRecorded` emitted after evidence recording
- Storage verifier: `storage.eval_evidence_driver.*` all PASS (6 checks)

### Evidence Queries:
- `SELECT control_set_version, override_ids_applied, resolver_version, decision FROM controls_evaluation_evidence WHERE tenant_id = ? AND run_id = ?`

### Iteration-3 ASSIGN Anchors (2026-02-15):
- `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py` — ASSIGN UC-004: L6 persistence for controls_evaluation_evidence table (record_evidence, query_evidence)

## UC-005: Baseline Monitoring (No Controls)
- Audience: `cust`
- Status: `GREEN`

### Evidence:
- UC-001 (LLM Run Monitoring) at GREEN — UC-005 is a subset (monitoring without controls enforcement)
- All deterministic read checks pass (34/34) including `as_of` for activity, incidents, logs, analytics
- Route-operation map covers all monitoring endpoints with canonical L4 dispatch
- No additional controls-specific code required for baseline path

## UC-006: Activity Stream + Feedback
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-02):
- Signal feedback lifecycle: L5 `signal_feedback_engine.py`, L6 `signal_feedback_driver.py`, L4 `activity_handler.py`
- Methods: `acknowledge`, `suppress`, `reopen`, `evaluate_expired`, `query_feedback`
- Events: `activity.SignalAcknowledged`, `activity.SignalSuppressed`, `activity.SignalReopened`, `activity.SignalFeedbackEvaluated`
- Storage verifier: `storage.feedback_driver.*` all PASS (3 checks)
- Event verifier: `event.emitter.activity_handler.py` PASS

### Evidence Queries:
- `SELECT feedback_state, as_of, ttl_seconds, expires_at FROM signal_feedback WHERE tenant_id = ? AND signal_id = ?`

### Iteration-3 ASSIGN Anchors (2026-02-15):
- `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py` — ASSIGN UC-006: L5 engine for signal feedback lifecycle (ack/suppress/reopen/evaluate_expired/query_feedback)
- `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py` — ASSIGN UC-006: L6 persistence for signal_feedback table (insert/query/update/list/expire)

## UC-007: Incident Lifecycle from Signals
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-04):
- Incident creation with recurrence: `insert_incident()` accepts `recurrence_signature`, `signature_version`
- Incident resolution with full audit: `update_incident_resolved()` accepts `resolution_type`, `resolution_summary`, `postmortem_artifact_id`
- Recurrence group query: `fetch_recurrence_group()` for deterministic group linking
- L4 `IncidentsRecurrenceHandler` registered as `incidents.recurrence`
- Events: `incidents.IncidentAcknowledged`, `incidents.IncidentResolved`, `incidents.IncidentManuallyClosed`
- Storage verifier: `storage.incident_driver.*` all PASS (7 checks)

### Evidence Queries:
- `SELECT resolution_type, recurrence_signature FROM incidents WHERE tenant_id = ? AND source_run_id = ?`

## UC-008: Reproducible Analytics Artifacts
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-04):
- L6 `analytics_artifacts_driver.py` persists: `dataset_version`, `input_window_hash`, `as_of`, `compute_code_version`
- L4 `AnalyticsArtifactsHandler` registered as `analytics.artifacts` (save/get/list)
- Event: `analytics.ArtifactRecorded` emitted after save
- Storage verifier: `storage.analytics_artifacts_driver.*` all PASS (7 checks)
- Migration 131: `analytics_artifacts` table with unique constraint on `(tenant_id, dataset_id, dataset_version)`

### Evidence Queries:
- `SELECT dataset_version, input_window_hash, as_of, compute_code_version FROM analytics_artifacts WHERE tenant_id = ? AND dataset_id = ?`

### Iteration-3 ASSIGN Anchors (2026-02-15):
- `app/hoc/cus/analytics/L6_drivers/analytics_artifacts_driver.py` — ASSIGN UC-008: L6 persistence for analytics_artifacts table (save_artifact UPSERT, get_artifact, list_artifacts)

## UC-009: Controls/Policies Proposals
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-03):
- `PolicyApprovalHandler` already complete (350+ lines): `create_approval_request`, `review_proposal`, `update_approval_request_approved`, `reject`, `batch_escalate`, `batch_update_expired`
- Proposal state machine: DRAFT → PENDING → APPROVED/REJECTED → ACTIVE
- Authority boundary: `proposals_no_enforcement` PASS, `proposals_allowed_ops_only` PASS, `policies_no_direct_l5l6` PASS
- Controls override lifecycle complete: `approve_override`, `reject_override`, `expire_overrides`
- Aggregator (strict): `authority.proposals_no_enforcement` PASS, `authority.proposals_allowed_ops_only` PASS

## UC-010: Activity Feedback Lifecycle
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-02):
- Full lifecycle: ACKNOWLEDGED → SUPPRESSED (with TTL/expiry) → EVALUATED/REOPENED
- L6 driver: `insert_feedback`, `query_feedback`, `mark_expired_as_evaluated`
- L5 engine: `acknowledge`, `suppress`, `reopen`, `evaluate_expired`
- Determinism: `as_of` timestamp, `ttl_seconds`, `expires_at` — all wired in migration 128
- Events: 4 event types with full extension fields (`signal_id`, `feedback_state`, `as_of`, `ttl_seconds`, `expires_at`)
- Storage verifier: `storage.determinism.as_of_feedback` PASS, `storage.determinism.ttl_fields` PASS

## UC-011: Incident Resolution + Postmortem
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-04):
- Resolution fields wired: `resolution_type`, `resolution_summary`, `postmortem_artifact_id` in L6 `update_incident_resolved()` + L5 `resolve_incident()`
- Postmortem stub: `create_postmortem_stub()` in L6 driver, `create_postmortem_stub` method in L4 `IncidentsRecurrenceHandler`
- Event: `incidents.PostmortemCreated` emitted with `postmortem_artifact_id`
- Storage verifier: `storage.incident_driver.field.resolution_type` PASS, `storage.incident_driver.postmortem_stub` PASS

## UC-012: Incident Recurrence Grouping
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-04):
- `recurrence_signature` (String 128) + `signature_version` (String 20) added to `insert_incident()` INSERT
- Index: `ix_incidents_recurrence_signature` (migration 129)
- `fetch_recurrence_group()` queries all incidents sharing a signature for deterministic group linking
- L4 handler: `incidents.recurrence` → `get_recurrence_group` method
- Storage verifier: `storage.incident_driver.field.recurrence_signature` PASS, `storage.incident_driver.recurrence_query` PASS

## UC-013: Policy Proposal Canonical Accept
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-03):
- `PolicyApprovalHandler` verified complete — no changes needed
- State machine: DRAFT → PENDING → APPROVED/REJECTED → ACTIVE (on activation)
- `PolicyActivationBlockedError` prevents activation when conflicts exist
- Authority: zero enforcement ops in `policy_proposals.py`, only `policies.proposals_query` + `policies.approval`
- Aggregator: `authority.proposals_no_enforcement` PASS, `authority.proposals_allowed_ops_only` PASS

## UC-014: Controls Override Lifecycle
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-03):
- Added 3 lifecycle methods to L6 `LimitOverrideService`: `approve_override`, `reject_override`, `expire_overrides`
- Full lifecycle: PENDING → APPROVED → ACTIVE → EXPIRED (with REJECTED and CANCELLED branches)
- All methods require actor lineage and reasons
- L4 `ControlsOverrideHandler` dispatch map updated with all 3 methods
- Event verifier: `event.emitter.controls_handler.py` PASS

## UC-015: Threshold Resolver Version Binding
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-03):
- `ControlsEvaluationEvidenceDriver` persists `control_set_version`, `override_ids_applied`, `resolver_version`, `decision`
- L4 `ControlsEvaluationEvidenceHandler` record method wraps in `async with ctx.session.begin()`
- Event: `controls.EvaluationRecorded` with `control_set_version`, `resolver_version`, `decision`
- Storage verifier: all 6 evaluation evidence checks PASS

## UC-016: Analytics Reproducibility Contract
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-04):
- `analytics_artifacts` table (migration 131) with `dataset_version`, `input_window_hash`, `as_of`, `compute_code_version`
- L6 `AnalyticsArtifactsDriver`: `save_artifact` (UPSERT), `get_artifact`, `list_artifacts`
- L4 `AnalyticsArtifactsHandler` registered as `analytics.artifacts`
- Event: `analytics.ArtifactRecorded` with all 4 reproducibility fields
- Storage verifier: all 7 analytics artifacts checks PASS
- Deterministic read verifier: `determinism.reproducibility.*` all PASS (5 checks)

## UC-017: Logs Replay Mode + Integrity Versioning
- Audience: `cust`
- Status: `GREEN`

### Evidence (Batch-02):
- Migration 132: `replay_mode`, `replay_attempt_id`, `replay_artifact_version`, `trace_completeness_status` on `aos_traces`
- L6 `pg_store.py`: INSERT writes all 4 replay columns, GET reads them into TraceRecord
- L5 `trace_api_engine.py`: `store_trace()` accepts and forwards replay params
- L5 `traces_models.py`: TraceRecord includes all 4 replay fields
- Modes: FULL | TRACE_ONLY (documented in methods doc)
- Event verifier: `event.replay.l6_driver_wired` PASS, `event.replay.l5_engine_wired` PASS
- Storage verifier: `storage.replay_wiring.insert` PASS, `storage.replay_wiring.select` PASS

## UC-018: Policy Snapshot Lifecycle + Integrity
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/policies/L5_engines/snapshot_engine.py`
- Acceptance: snapshot create/history/verify run through L4 mapping with deterministic evidence.
- Evidence (2026-02-12):
  - L5 engine pure: `snapshot_engine.py` — 0 runtime DB imports (AST-verified)
  - Core functions present: `create_policy_snapshot`, `get_snapshot_history`, `verify_snapshot` (AST-verified)
  - `SnapshotRegistry` class with `register`/`get`/`list_snapshots` methods (AST-verified)
  - L4 wiring: `policies_handler.py` dispatches snapshot ops via operation registry
  - Domain purity: `policies` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC018PolicySnapshot` — 5/5 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-019: Policies Proposals Query Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/policies/L5_engines/policies_proposals_query_engine.py`, `app/hoc/cus/policies/L6_drivers/proposals_read_driver.py`
- Acceptance: list/detail/draft-count query path is L2->L4->L5->L6 and deterministic.
- Evidence (2026-02-12):
  - L5 engine pure: `policies_proposals_query_engine.py` — 0 runtime DB imports (AST-verified)
  - L6 driver pure: `proposals_read_driver.py` — no business logic patterns detected
  - L4 handler wiring: `policies_proposals_handler.py` exists and dispatches operations
  - Domain purity: `policies` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC019ProposalsQuery` — 5/5 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-020: Policies Rules Query Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/policies/L5_engines/policies_rules_query_engine.py`, `app/hoc/cus/policies/L6_drivers/policy_rules_read_driver.py`
- Acceptance: rules list/detail/count are query-only, deterministic, and fully mapped via L4.
- Evidence (2026-02-12):
  - L5 engine pure: `policies_rules_query_engine.py` — 0 runtime DB imports (AST-verified)
  - L6 driver pure: `policy_rules_read_driver.py` — no business logic patterns detected
  - Domain purity: `policies` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC020RulesQuery` — 4/4 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-021: Policies Limits Query Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/policies/L5_engines/policies_limits_query_engine.py`, `app/hoc/cus/controls/L6_drivers/limits_read_driver.py`
- Acceptance: limits/budgets/detail queries are deterministic with cross-domain coordination only at L4.
- Evidence (2026-02-12):
  - L5 engine pure: `policies_limits_query_engine.py` — 0 runtime DB imports (AST-verified)
  - Cross-domain driver exists: `controls/L6_drivers/limits_read_driver.py` (verified)
  - Query methods: `list_limits`, `get_limit_detail` (AST-verified)
  - Domain purity: `policies` blocking=0, `controls` blocking=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC021LimitsQuery` — 5/5 PASS
  - Cross-domain validator: 0 violations (sdk_attestation pre-existing excluded)

## UC-022: Policies Sandbox Definition + Execution Telemetry
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/policies/L5_engines/sandbox_engine.py`, `app/hoc/cus/hoc_spine/orchestrator/handlers/policies_sandbox_handler.py`
- Acceptance: sandbox define/list/get/execution records flow is registry-bound and deterministic.
- Evidence (2026-02-12):
  - L5 engine pure: `sandbox_engine.py` — 0 runtime DB imports (AST-verified)
  - L4 handler exists: `policies_sandbox_handler.py` (verified)
  - Service methods: `define_policy`, `list_policies`, `get_execution_records`, `get_execution_stats` (AST-verified)
  - Domain purity: `policies` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC022Sandbox` — 7/7 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-023: Policy Conflict Resolution Explainability
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/policies/L5_engines/policy_conflict_resolver.py`, `app/hoc/cus/policies/L6_drivers/optimizer_conflict_resolver.py`
- Acceptance: conflict outcomes are deterministic with explainability payload and no L6 decision leakage.
- Evidence (2026-02-12):
  - L5 engine pure: `policy_conflict_resolver.py` — 0 runtime DB imports (AST-verified)
  - Resolve function: `resolve_conflicts` present (AST-verified)
  - Deterministic ordering: `sorted()` call verified in source — no randomness
  - Domain purity: `policies` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC023ConflictResolver` — 4/4 PASS

## UC-024: Analytics Cost Anomaly Detection Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/analytics/L5_engines/cost_anomaly_detector_engine.py`, `app/hoc/cus/analytics/L6_drivers/cost_anomaly_driver.py`
- Acceptance: `detect_*` and anomaly persistence paths are fully wired, testable, and deterministic.
- Evidence (2026-02-12):
  - L5 engine pure: `cost_anomaly_detector_engine.py` — 0 runtime DB imports (AST-verified)
  - L6 driver pure: `cost_anomaly_driver.py` — no business logic patterns detected
  - Detection function: `run_anomaly_detection` present (AST-verified)
  - Domain purity: `analytics` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC024AnomalyDetection` — 4/4 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-025: Analytics Prediction Cycle Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/analytics/L5_engines/prediction_engine.py`, `app/hoc/cus/analytics/L6_drivers/prediction_driver.py`
- Acceptance: prediction cycle is versioned, deterministic, and route-mapped through L4.
- Evidence (2026-02-12):
  - L5 engine pure: `prediction_engine.py` — 0 runtime DB imports (AST-verified)
  - L6 driver pure: `prediction_driver.py` — no business logic patterns detected
  - Prediction functions: `predict_failure_likelihood`, `predict_cost_overrun`, `run_prediction_cycle` (AST-verified)
  - Domain purity: `analytics` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC025Prediction` — 6/6 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-026: Analytics Dataset Validation Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/analytics/L5_engines/datasets_engine.py`
- Acceptance: dataset list/get/validate/validate-all are deterministic and evidence-backed.
- Evidence (2026-02-12):
  - L5 engine pure: `datasets_engine.py` — 0 runtime DB imports (AST-verified)
  - Validation functions: `validate_dataset`, `validate_all_datasets` (AST-verified)
  - Domain purity: `analytics` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC026DatasetValidation` — 4/4 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-027: Analytics Snapshot + Baseline Job Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py`
- Acceptance: hourly/daily job flows are wired, idempotent, and deterministic for fixed windows.
- Evidence (2026-02-12):
  - L5 engine pure: `cost_snapshots_engine.py` — 0 runtime DB imports (AST-verified)
  - Job functions: `run_hourly_snapshot_job`, `run_daily_snapshot_and_baseline_job` (AST-verified)
  - Domain purity: `analytics` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC027SnapshotJobs` — 4/4 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-028: Analytics Cost Write Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/analytics/L5_engines/cost_write.py`, `app/hoc/cus/analytics/L6_drivers/cost_write_driver.py`
- Acceptance: cost writes are callable, idempotent, and traceable with provenance fields.
- Evidence (2026-02-12):
  - L5 engine pure: `cost_write.py` — 0 runtime DB imports (AST-verified)
  - L6 driver write functions: `create_cost_record`, `create_feature_tag` (AST-verified)
  - Domain purity: `analytics` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC028CostWrite` — 5/5 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-029: Incidents Recovery Rule Evaluation Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/incidents/L5_engines/recovery_rule_engine.py`
- Acceptance: recovery-rule decision functions are exercised in canonical flow and deterministic.
- Evidence (2026-02-12):
  - L5 engine pure: `recovery_rule_engine.py` — 0 runtime DB imports (AST-verified)
  - Decision functions: `evaluate_rules`, `suggest_recovery_mode`, `should_auto_execute` (AST-verified)
  - No randomness: no `random`/`shuffle`/`sample` imports (verified)
  - Domain purity: `incidents` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC029RecoveryRule` — 6/6 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-030: Incidents Policy Violation Truth Pipeline
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/incidents/L5_engines/policy_violation_engine.py`, `app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py`
- Acceptance: violation truth checks and incident creation are wired, test-covered, and idempotent.
- Evidence (2026-02-12):
  - L5 engine pure: `policy_violation_engine.py` — 0 runtime DB imports (AST-verified)
  - L6 driver pure: `policy_violation_driver.py` — no truth-decision patterns detected
  - Core functions: `persist_violation_and_create_incident`, `verify_violation_truth` (AST-verified)
  - Domain purity: `incidents` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC030PolicyViolation` — 6/6 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-031: Incidents Pattern + Postmortem Learnings Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/incidents/L5_engines/incident_pattern.py`, `app/hoc/cus/incidents/L5_engines/postmortem.py`, `app/hoc/cus/incidents/L6_drivers/incident_pattern_driver.py`, `app/hoc/cus/incidents/L6_drivers/postmortem_driver.py`
- Acceptance: pattern and learnings pipelines are deterministic and linked to incident lifecycle evidence.
- Evidence (2026-02-12):
  - All 4 files exist (verified)
  - L5 pure: `incident_pattern.py` — 0 runtime DB imports (AST-verified)
  - L5 pure: `postmortem.py` — 0 runtime DB imports (AST-verified)
  - Pattern function: `detect_patterns` present (AST-verified)
  - Learnings function: `get_incident_learnings` present (AST-verified)
  - Domain purity: `incidents` blocking=0, advisory=0
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC031PatternPostmortem` — 8/8 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-032: Logs Redaction Governance + Trace-Safe Export
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- File anchors: `app/hoc/cus/logs/L5_engines/redact.py`, `app/hoc/cus/logs/L6_drivers/redact.py`
- Acceptance: redaction path is canonical, deterministic, and validated against trace export/replay surfaces.
- Evidence (2026-02-12):
  - L5 engine pure: `logs/L5_engines/redact.py` — 0 runtime DB imports (AST-verified)
  - L5 redaction functions: `redact_trace_data`, `redact_dict`, `redact_string_value` (AST-verified)
  - L6 redaction functions: `redact_trace_data`, `redact_dict`, `redact_string_value` (AST-verified)
  - Deterministic output: no `random`/`uuid` in either redact file (verified)
  - Domain purity: `logs` blocking=7 (all pre-existing in `trace_store.py`, NOT in `redact.py`)
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC032LogsRedaction` — 11/11 PASS
  - Pairing: 70 wired, 0 orphaned, 0 direct L2→L5

## UC-033: Spine Operation Governance + Contracts
- Audience: `cust,int,fdr`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `26` scripts (full list in `HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`)
- File anchors:
  - `app/hoc/cus/hoc_spine/auth_wiring.py` — auth wiring for spine operations
  - `app/hoc/cus/hoc_spine/orchestrator/operation_registry.py` — deterministic operation dispatch registry
  - `app/hoc/cus/hoc_spine/orchestrator/plan_generation_engine.py` — execution plan generation
  - `app/hoc/cus/hoc_spine/orchestrator/governance_orchestrator.py` — governance orchestration
  - `app/hoc/cus/hoc_spine/orchestrator/constraint_checker.py` — constraint validation
  - `app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py` — run governance facade
  - `app/hoc/cus/hoc_spine/orchestrator/phase_status_invariants.py` — phase invariants
  - `app/hoc/cus/hoc_spine/orchestrator/execution/job_executor.py` — job execution
  - `app/hoc/cus/hoc_spine/schemas/*` — 16 contract schema files (agent, anomaly_types, artifact, authority_decision, common, domain_enums, knowledge_plane_harness, lifecycle_harness, plan, protocols, rac_models, response, retry, run_introspection_protocols, skill, threshold_types)
  - `app/hoc/cus/hoc_spine/tests/conftest.py` — test fixtures
  - `app/hoc/cus/hoc_spine/tests/test_operation_registry.py` — registry tests
- Evidence (2026-02-13):
  - All 26 scripts verified present (file existence check)
  - Schema files are pure data: 0 runtime DB imports across 16 schema files (AST-verified)
  - Operation registry defines deterministic dispatch mechanism (verified)
  - Cross-domain validator: CLEAN, count=0
  - Layer boundaries: CLEAN
  - Governance tests: `test_uc018_uc032_expansion.py::TestUC033to040Expansion` — all PASS

## UC-034: Spine Lifecycle Orchestration
- Audience: `cust,int,fdr`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `6` scripts
- File anchors:
  - `app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/execution.py` — lifecycle execution driver
  - `app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py` — knowledge plane driver
  - `app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py` — onboarding engine
  - `app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/offboarding.py` — offboarding engine
  - `app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/pool_manager.py` — pool management
  - `app/hoc/cus/hoc_spine/orchestrator/lifecycle/stages.py` — lifecycle stage constants
- Evidence (2026-02-13):
  - All 6 scripts verified present (file existence check)
  - Lifecycle transitions are L4-orchestrated (no L2→L5 bypass)
  - stages.py defines substantive lifecycle stage constants (verified)
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc034_*` — all PASS

## UC-035: Spine Execution Safety + Driver Integrity
- Audience: `cust,int,fdr`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `17` scripts
- File anchors:
  - `app/hoc/cus/hoc_spine/drivers/idempotency.py` — idempotency enforcement
  - `app/hoc/cus/hoc_spine/drivers/transaction_coordinator.py` — transaction coordination
  - `app/hoc/cus/hoc_spine/drivers/ledger.py` — execution ledger
  - `app/hoc/cus/hoc_spine/drivers/guard_write_driver.py` — guard write persistence
  - `app/hoc/cus/hoc_spine/drivers/guard_cache.py` — guard cache
  - `app/hoc/cus/hoc_spine/drivers/alert_driver.py` — alert persistence
  - `app/hoc/cus/hoc_spine/drivers/alert_emitter.py` — alert emission
  - `app/hoc/cus/hoc_spine/drivers/cross_domain.py` — cross-domain driver
  - `app/hoc/cus/hoc_spine/drivers/dag_executor.py` — DAG execution driver
  - `app/hoc/cus/hoc_spine/drivers/decisions.py` — decision recording
  - `app/hoc/cus/hoc_spine/drivers/governance_signal_driver.py` — governance signal persistence
  - `app/hoc/cus/hoc_spine/drivers/knowledge_plane_registry_driver.py` — knowledge plane registry
  - `app/hoc/cus/hoc_spine/drivers/retrieval_evidence_driver.py` — evidence retrieval persistence
  - `app/hoc/cus/hoc_spine/drivers/schema_parity.py` — schema parity checks
  - `app/hoc/cus/hoc_spine/drivers/worker_write_driver_async.py` — async worker writes
  - `app/hoc/cus/hoc_spine/utilities/recovery_decisions.py` — recovery decision logic
  - `app/hoc/cus/hoc_spine/utilities/s1_retry_backoff.py` — S1 retry backoff
- Evidence (2026-02-13):
  - All 17 scripts verified present (file existence check)
  - Driver spot-check: guard_write_driver, ledger, idempotency — 0 business-logic violations
  - Driver responsibilities remain effects-only (no severity/threshold/confidence branching)
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc035_*` — all PASS

## UC-036: Spine Signals, Evidence, and Alerting
- Audience: `cust,int,fdr`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `33` scripts
- File anchors:
  - `app/hoc/cus/hoc_spine/consequences/pipeline.py` — consequence execution pipeline
  - `app/hoc/cus/hoc_spine/consequences/ports.py` — consequence ports/interfaces
  - `app/hoc/cus/hoc_spine/services/alerts_facade.py` — alerts facade
  - `app/hoc/cus/hoc_spine/services/audit_store.py` — audit persistence
  - `app/hoc/cus/hoc_spine/services/retrieval_evidence_engine.py` — evidence retrieval engine
  - `app/hoc/cus/hoc_spine/services/compliance_facade.py` — compliance facade
  - `app/hoc/cus/hoc_spine/services/alert_delivery.py` — alert delivery
  - `app/hoc/cus/hoc_spine/services/audit_durability.py` — audit durability
  - `app/hoc/cus/hoc_spine/services/canonical_json.py` — canonical JSON serialization
  - `app/hoc/cus/hoc_spine/services/control_registry.py` — control registry
  - `app/hoc/cus/hoc_spine/services/costsim_config.py` — CostSim configuration
  - `app/hoc/cus/hoc_spine/services/costsim_metrics.py` — CostSim metrics
  - `app/hoc/cus/hoc_spine/services/cross_domain_gateway.py` — cross-domain gateway
  - `app/hoc/cus/hoc_spine/services/cus_credential_engine.py` — credential engine
  - `app/hoc/cus/hoc_spine/services/dag_sorter.py` — DAG topological sort
  - `app/hoc/cus/hoc_spine/services/db_helpers.py` — DB helper utilities
  - `app/hoc/cus/hoc_spine/services/deterministic.py` — determinism enforcement
  - `app/hoc/cus/hoc_spine/services/dispatch_audit.py` — dispatch audit trail
  - `app/hoc/cus/hoc_spine/services/fatigue_controller.py` — alert fatigue control
  - `app/hoc/cus/hoc_spine/services/guard.py` — guard enforcement
  - `app/hoc/cus/hoc_spine/services/input_sanitizer.py` — input sanitization
  - `app/hoc/cus/hoc_spine/services/knowledge_plane_connector_registry_engine.py` — KP connector registry
  - `app/hoc/cus/hoc_spine/services/lifecycle_facade.py` — lifecycle facade
  - `app/hoc/cus/hoc_spine/services/lifecycle_stages_base.py` — lifecycle stages base
  - `app/hoc/cus/hoc_spine/services/metrics_helpers.py` — metrics utilities
  - `app/hoc/cus/hoc_spine/services/monitors_facade.py` — monitors facade
  - `app/hoc/cus/hoc_spine/services/rate_limiter.py` — rate limiting
  - `app/hoc/cus/hoc_spine/services/retrieval_facade.py` — retrieval facade
  - `app/hoc/cus/hoc_spine/services/retrieval_mediator.py` — retrieval mediation
  - `app/hoc/cus/hoc_spine/services/retrieval_policy_checker_engine.py` — retrieval policy checks
  - `app/hoc/cus/hoc_spine/services/scheduler_facade.py` — scheduler facade
  - `app/hoc/cus/hoc_spine/services/time.py` — time utilities
  - `app/hoc/cus/hoc_spine/services/webhook_verify.py` — webhook verification
- Evidence (2026-02-13):
  - All 33 scripts verified present (file existence check)
  - retrieval_evidence_engine.py has substantive content (verified)
  - Consequence flow remains post-orchestration and non-domain-owning
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc036_*` — all PASS

## UC-037: Integrations Secret Vault Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `3` scripts
- File anchors:
  - `app/hoc/cus/integrations/L5_vault/engines/service.py` — vault service engine
  - `app/hoc/cus/integrations/L5_vault/engines/vault_rule_check.py` — vault rule validation
  - `app/hoc/cus/integrations/L5_vault/drivers/vault.py` — vault persistence driver
- Evidence (2026-02-13):
  - All 3 scripts verified present (file existence check)
  - L5 purity: service.py — 0 runtime DB imports (AST-verified)
  - L5 purity: vault_rule_check.py — 0 runtime DB imports (AST-verified)
  - Driver remains effect-only
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc037_*` — all PASS

## UC-038: Integrations Notification Channel Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `1` script
- File anchors:
  - `app/hoc/cus/integrations/L5_notifications/engines/channel_engine.py` — notification channel engine
- Evidence (2026-02-13):
  - Script verified present (file existence check)
  - L5 purity: channel_engine.py — 0 runtime DB imports (AST-verified)
  - Channel operations governed by canonical L4 flow
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc038_*` — all PASS

## UC-039: Integrations CLI Operational Bootstrap
- Audience: `cust,int`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `1` script
- File anchors:
  - `app/hoc/cus/integrations/cus_cli.py` — CLI operational bootstrap
- Evidence (2026-02-13):
  - Script verified present (file existence check)
  - CLI path preserves canonical orchestration and tenant/context authority
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc039_*` — PASS

## UC-040: Account CRM Audit Trail Lifecycle
- Audience: `cust`
- Status: `GREEN`
- Execution pack: `backend/app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- Scope size: `1` script
- File anchors:
  - `app/hoc/cus/account/logs/CRM/audit/audit_engine.py` — CRM audit trail engine
- Evidence (2026-02-13):
  - Script verified present (file existence check)
  - Audit trail behavior is architecture-compliant
  - Cross-domain validator: CLEAN
  - Governance tests: `TestUC033to040Expansion::test_uc040_*` — PASS

---

## Evidence
- Punch list: `DOMAIN_REPAIR_PLAN_UC001_UC002_v2_remaining_punch_list.md`
- Punch list evidence: `DOMAIN_REPAIR_PLAN_UC001_UC002_v2_remaining_punch_list_implemented.md`
- TODO plan: `TODO_PLAN.md`
- TODO evidence: `TODO_PLAN_implemented.md`
- GREEN plan: `GREEN_CLOSURE_PLAN_UC001_UC002.md`
- GREEN evidence: `GREEN_CLOSURE_PLAN_UC001_UC002_implemented.md`
- Batch-01 evidence: `HANDOVER_BATCH_01_GOVERNANCE_BASELINE_implemented.md`
- Batch-02 evidence: `HANDOVER_BATCH_02_LOGS_ACTIVITY_implemented.md`
- Batch-03 evidence: `HANDOVER_BATCH_03_CONTROLS_POLICIES_implemented.md`
- Batch-04 evidence: `HANDOVER_BATCH_04_INCIDENTS_ANALYTICS_implemented.md`
- Batch-05 evidence: `HANDOVER_BATCH_05_GREEN_PROMOTION_implemented.md`
- UC expansion plan: `UC_EXECUTION_TASKPACK_UC018_UC032_FOR_CLAUDE.md`
- UC expansion context: `UC_EXPANSION_CONTEXT_UC018_UC032.md`
- UC expansion evidence: `UC_EXPANSION_UC018_UC032_implemented.md`
- Script coverage Wave-1 evidence: `UC_SCRIPT_COVERAGE_WAVE_1_implemented.md`
- Script coverage Wave-2 evidence: `UC_SCRIPT_COVERAGE_WAVE_2_implemented.md`
- Script coverage Wave-3 evidence: `UC_SCRIPT_COVERAGE_WAVE_3_implemented.md`
- Script coverage Wave-4 evidence: `UC_SCRIPT_COVERAGE_WAVE_4_implemented.md`
- Full-scope UC generation proposal: `HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`
- UC-033..UC-040 taskpack: `UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md`
- UC-033..UC-040 expansion evidence: `UC_EXPANSION_UC033_UC040_implemented.md`
- UC-033..UC-040 reality audit: `UC033_UC040_REALITY_AUDIT_2026-02-13.md`

## Script Coverage Wave-1: Policies + Logs (2026-02-12)

### Scope
130 unlinked scripts classified across policies (91) and logs (39) domains.

### Classification Summary

| Domain | Total Unlinked | UC_LINKED | NON_UC_SUPPORT | DEPRECATED |
|--------|---------------|-----------|----------------|------------|
| policies | 91 | 16 | 75 | 0 |
| logs | 39 | 17 | 22 | 0 |
| **Total** | **130** | **33** | **97** | **0** |

### UC_LINKED Expansions (policies → existing UCs)

**UC-009 expanded anchors** (policies enforcement path):
- `policies/L5_engines/engine.py` — policy rule evaluation engine
- `policies/L5_engines/cus_enforcement_engine.py` — enforcement decision logic
- `policies/L5_engines/policy_proposal_engine.py` — proposal state machine
- `policies/L6_drivers/policy_engine_driver.py` — evaluation persistence
- `policies/L6_drivers/cus_enforcement_driver.py` — enforcement persistence
- `policies/L6_drivers/prevention_records_read_driver.py` — run-scoped ledger
- `policies/L6_drivers/policy_enforcement_driver.py` — enforcement persistence
- `policies/L6_drivers/policy_enforcement_write_driver.py` — enforcement writes

**UC-018 expanded anchors** (deterministic execution):
- `policies/L5_engines/deterministic_engine.py` — reproducible policy execution

**UC-019 expanded anchors** (proposal write counterparts):
- `policies/L6_drivers/policy_proposal_read_driver.py` — proposal reads
- `policies/L6_drivers/policy_proposal_write_driver.py` — proposal writes

**UC-023 expanded anchors** (learnings):
- `policies/L5_engines/lessons_engine.py` — lessons learned engine

**UC-029 expanded anchors** (recovery cross-domain):
- `policies/L5_engines/recovery_evaluation_engine.py` — recovery decisions
- `policies/L6_drivers/recovery_read_driver.py` — recovery reads
- `policies/L6_drivers/recovery_write_driver.py` — recovery writes
- `policies/L6_drivers/recovery_matcher.py` — recovery matching

### UC_LINKED Expansions (logs → existing UCs)

**UC-003 expanded anchors** (trace ingest):
- `logs/L5_engines/logs_read_engine.py` — read operations
- `logs/L5_engines/trace_mismatch_engine.py` — trace mismatch detection
- `logs/L6_drivers/idempotency_driver.py` — trace idempotency
- `logs/L6_drivers/trace_mismatch_driver.py` — mismatch persistence
- `logs/L5_schemas/traces_models.py` — trace data models
- `logs/adapters/customer_logs_adapter.py` — boundary adapter

**UC-017 expanded anchors** (replay/integrity/evidence):
- `logs/L5_engines/certificate.py` — integrity certificates
- `logs/L5_engines/completeness_checker.py` — evidence completeness
- `logs/L5_engines/evidence_facade.py` — evidence access
- `logs/L5_engines/evidence_report.py` — legal-grade PDF export
- `logs/L5_engines/mapper.py` — SOC2 control mapping
- `logs/L5_engines/pdf_renderer.py` — PDF rendering
- `logs/L5_engines/replay_determinism.py` — replay determinism validation
- `logs/L6_drivers/export_bundle_store.py` — export persistence
- `logs/L6_drivers/integrity_driver.py` — integrity persistence
- `logs/L6_drivers/replay_driver.py` — replay execution
- `logs/L5_schemas/determinism_types.py` — determinism type defs

### NON_UC_SUPPORT Classification Groups

**Package init files** (14): All `__init__.py` files — package initialization
**L5 schemas** (9): Data models, DTOs, type definitions — shared across UCs
**Adapters** (5): Boundary adapters — L2→L4 interface layer
**DSL compiler pipeline** (14): ast, compiler_parser, dsl_parser, grammar, interpreter, ir_builder, ir_compiler, ir_nodes, kernel, nodes, tokenizer, folds, visitors, decorator
**Facades** (8): governance_facade, policies_facade, limits_facade, logs_facade, evidence_facade (already UC_LINKED), etc.
**Policy infrastructure** (23): authority_checker, binding_moment_enforcer, content_accuracy, dag_executor, degraded_mode, failure_mode_handler, intent, kill_switch, limits, limits_simulation_engine, llm_policy, phase_status_invariants, plan, plan_generation, policy_command, policy_driver, policy_graph, policy_mapper, policy_models, prevention_hook, protection_provider, runtime_command, state, tokenizer, validator, worker_execution_command, sandbox_executor
**Read/persistence infrastructure** (15): policy_read_driver, policy_rules_driver, policies_facade_driver, policy_graph_driver, limits_simulation_driver, policy_approval_driver, arbitrator, guard_read_driver, m25_integration_read/write_driver, rbac_audit_driver, replay_read_driver, scope_resolver, symbol_table, workers_read_driver
**Logs infrastructure** (19): audit_evidence, audit_ledger_engine, audit_reconciler, cost_intelligence_engine, traces_models (L5 re-export), audit_ledger_driver, audit_ledger_read/write_drivers, bridges_driver, capture_driver, cost_intelligence_driver/sync, job_execution_driver, logs_domain_store, panel_consistency_driver

---

## Script Coverage Wave-2: analytics + incidents + activity (2026-02-12)

**Source:** `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`
**Scope:** 80 unlinked scripts — analytics (32), incidents (30), activity (18)
**Result:** 35 UC_LINKED + 45 NON_UC_SUPPORT + 0 DEPRECATED = 80 classified (100%)
**Evidence:** `UC_SCRIPT_COVERAGE_WAVE_2_implemented.md`
**Tests:** `tests/governance/t4/test_uc018_uc032_expansion.py` — TestWave2ScriptCoverage class

### Before/After Summary

| Domain | Total | Pre-linked | Wave-2 UC_LINKED | Wave-2 NON_UC | Unclassified |
|--------|-------|------------|------------------|---------------|--------------|
| activity | 20 | 2 | 5 | 13 | 0 |
| analytics | 41 | 9 | 13 | 19 | 0 |
| incidents | 37 | 7 | 17 | 13 | 0 |
| **Total** | **98** | **18** | **35** | **45** | **0** |

### UC_LINKED Expansions (activity → UC-MON-01, UC-MON-05)

**UC-MON-01 expanded anchors** (run activity monitoring):
- `activity/L5_engines/activity_facade.py` — unified activity operations facade
- `activity/L6_drivers/activity_read_driver.py` — activity data reads
- `activity/adapters/customer_activity_adapter.py` — customer boundary adapter

**UC-MON-05 expanded anchors** (run telemetry):
- `activity/L5_engines/cus_telemetry_engine.py` — telemetry decision logic
- `activity/L6_drivers/cus_telemetry_driver.py` — telemetry persistence

### UC_LINKED Expansions (analytics → UC-024, UC-025, UC-027, UC-MON-04)

**UC-024 expanded anchors** (cost anomaly detection):
- `analytics/L5_engines/analytics_facade.py` — analytics entry point
- `analytics/L5_engines/detection_facade.py` — anomaly detection facade
- `analytics/L6_drivers/analytics_read_driver.py` — analytics data access
- `analytics/L6_drivers/cost_anomaly_read_driver.py` — anomaly reads

**UC-025 expanded anchors** (prediction cycle):
- `analytics/L5_engines/prediction_read_engine.py` — prediction read logic
- `analytics/L6_drivers/prediction_read_driver.py` — prediction reads

**UC-027 expanded anchors** (snapshot jobs / canary / sandbox):
- `analytics/L5_engines/canary_engine.py` — daily canary validation
- `analytics/L5_engines/sandbox_engine.py` — CostSim V2 sandbox routing
- `analytics/L5_engines/v2_adapter.py` — CostSim V2 translation layer
- `analytics/L6_drivers/canary_report_driver.py` — canary report persistence
- `analytics/L6_drivers/cost_snapshots_driver.py` — snapshot persistence

**UC-MON-04 expanded anchors** (signal feedback):
- `analytics/L5_engines/feedback_read_engine.py` — feedback read logic
- `analytics/L6_drivers/feedback_read_driver.py` — feedback data access

### UC_LINKED Expansions (incidents → UC-MON-07, UC-030, UC-031)

**UC-MON-07 expanded anchors** (incident detection):
- `incidents/L5_engines/anomaly_bridge.py` — cost anomaly to incident bridge
- `incidents/L5_engines/incident_engine.py` — core incident creation (SDSR)
- `incidents/L5_engines/incidents_facade.py` — incidents domain facade
- `incidents/L6_drivers/cost_guard_driver.py` — cost data for detection
- `incidents/L6_drivers/incident_aggregator.py` — intelligent incident grouping
- `incidents/L6_drivers/incidents_facade_driver.py` — facade data access
- `incidents/adapters/customer_incidents_adapter.py` — customer boundary adapter

**UC-030 expanded anchors** (hallucination detection):
- `incidents/L5_engines/hallucination_detector.py` — hallucination detection (INV-002)

**UC-031 expanded anchors** (incident lifecycle / export / recurrence):
- `incidents/L5_engines/export_engine.py` — evidence/SOC2/executive bundles
- `incidents/L5_engines/incident_read_engine.py` — incident investigation reads
- `incidents/L5_engines/incident_write_engine.py` — incident lifecycle writes
- `incidents/L5_engines/recurrence_analysis.py` — recurrence pattern analysis
- `incidents/L6_drivers/export_bundle_driver.py` — export bundle persistence
- `incidents/L6_drivers/incident_read_driver.py` — incident read persistence
- `incidents/L6_drivers/incident_run_read_driver.py` — run-incident reads
- `incidents/L6_drivers/incident_write_driver.py` — incident write persistence
- `incidents/L6_drivers/recurrence_analysis_driver.py` — recurrence data access

### NON_UC_SUPPORT Classification Groups (Wave-2)

**Package init files** (9): All `__init__.py` files across activity, analytics, incidents
**Activity stubs** (3): attention_ranking, cost_analysis, pattern_detection — empty/stub engines
**Activity infrastructure** (4): activity_enums (enum defs), signal_identity (dedup utility), orphan_recovery_driver (system cleanup), run_metrics_driver (internal metrics), run_signal_driver (internal risk updates), workers_adapter (internal worker adapter)
**Analytics schemas** (6): cost_anomaly_dtos, cost_anomaly_schemas, cost_snapshot_schemas, feedback_schemas, query_types + __init__.py
**Analytics infrastructure** (7): config_engine (re-export), cost_model (coefficients dict), costsim_models (dataclasses), divergence_engine (metric calculation), metrics_engine (re-export), provenance (audit utility), adapters/__init__.py
**Analytics drivers** (4): coordination_audit_driver, leader_driver (advisory locks), pattern_detection_driver, provenance_driver (async logging)
**Incidents schemas** (4): export_schemas (protocol), incident_decision_port (DI port), severity_policy (policy logic), __init__.py
**Incidents infrastructure** (4): incidents_types (type aliases), semantic_failures (taxonomy), incident_driver (protocol wrapper), founder_ops_adapter (non-customer)
**Incidents drivers** (2): lessons_driver (lesson recording), llm_failure_driver (failure tracking)

---

## Script Coverage Wave-3: controls + account (2026-02-12)

**Source:** `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_WAVE3_TARGET_UNLINKED_2026-02-12.txt`
**Scope:** 52 unlinked scripts — account (31), controls (21)
**Result:** 19 UC_LINKED + 33 NON_UC_SUPPORT + 0 DEPRECATED = 52 classified (100%)
**Evidence:** `UC_SCRIPT_COVERAGE_WAVE_3_implemented.md`
**Tests:** `tests/governance/t4/test_uc018_uc032_expansion.py` — TestWave3ScriptCoverage class

### Before/After Summary

| Domain | Total | Pre-linked | Wave-3 UC_LINKED | Wave-3 NON_UC | Unclassified |
|--------|-------|------------|------------------|---------------|--------------|
| account | 31 | 0 | 13 | 18 | 0 |
| controls | 23 | 2 | 6 | 15 | 0 |
| **Total** | **54** | **2** | **19** | **33** | **0** |

### UC_LINKED Expansions (account → UC-002, UC-001)

**UC-002 expanded anchors** (customer onboarding):
- `account/L5_engines/accounts_facade.py` — account queries via L4 dispatch
- `account/L5_engines/memory_pins_engine.py` — memory pin persistence for audit trail
- `account/L5_engines/notifications_facade.py` — onboarding notifications delivery
- `account/L5_engines/onboarding_engine.py` — core state-machine (5 states, monotonic transitions)
- `account/L5_engines/tenant_engine.py` — tenant operations (quota enforcement, bootstrap)
- `account/L5_engines/tenant_lifecycle_engine.py` — offboarding lifecycle (ACTIVE→ARCHIVED)
- `account/L6_drivers/accounts_facade_driver.py` — account query persistence
- `account/L6_drivers/memory_pins_driver.py` — memory pin data access
- `account/L6_drivers/onboarding_driver.py` — onboarding state CRUD
- `account/L6_drivers/sdk_attestation_driver.py` — SDK attestation persistence
- `account/L6_drivers/tenant_driver.py` — tenant quota/plan persistence
- `account/L6_drivers/tenant_lifecycle_driver.py` — lifecycle status mutations
- `account/L6_drivers/user_write_driver.py` — user creation during onboarding

### UC_LINKED Expansions (controls → UC-001, UC-021, UC-029)

**UC-001 expanded anchors** (threshold enforcement during runs):
- `controls/L5_engines/threshold_engine.py` — threshold evaluation decision logic
- `controls/L6_drivers/threshold_driver.py` — threshold limit data access

**UC-021 expanded anchors** (limits query + override lifecycle):
- `controls/L5_engines/controls_facade.py` — centralized control operations facade
- `controls/L6_drivers/override_driver.py` — limit override lifecycle persistence
- `controls/L6_drivers/policy_limits_driver.py` — policy limits CRUD

**UC-029 expanded anchors** (recovery pre-execution gate):
- `controls/L6_drivers/scoped_execution_driver.py` — scope creation/validation/exhaustion

### NON_UC_SUPPORT Classification Groups (Wave-3)

**Package init files** (7): All `__init__.py` files across account L5_engines, L5_schemas, L6_drivers, auth L5_engines, auth L6_drivers, controls L5_engines, L5_schemas, L6_drivers, adapters
**Account schemas** (8): crm_validator_types, lifecycle_dtos, onboarding_dtos, onboarding_state, plan_quotas, result_types, sdk_attestation, tenant_lifecycle_enums, tenant_lifecycle_state
**Account platform auth** (3): identity_adapter (request identity extraction), invocation_safety (PIN-332), rbac_engine (legacy M7 RBAC)
**Account infrastructure** (1): billing_provider_engine (Phase-6 protocol/mock provider)
**Controls schemas** (5): override_types (error types), overrides (Pydantic schemas), policy_limits (CRUD schemas), simulation (limit sim schemas), threshold_signals (signal enum/dataclass)
**Controls safety infrastructure** (6): cb_sync_wrapper_engine (circuit breaker sync wrapper), circuit_breaker_async_driver, circuit_breaker_driver, killswitch_ops_driver, killswitch_read_driver, budget_enforcement_driver

---

## Script Coverage Wave-4: hoc_spine + integrations + agent + api_keys + apis + ops + overview (2026-02-12)

**Source:** `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_WAVE4_TARGET_UNLINKED_2026-02-12.txt`
**Scope:** 150 unlinked scripts — hoc_spine (78), integrations (48), api_keys (9), overview (5), agent (4), ops (4), apis (2)
**Result:** 47 UC_LINKED + 103 NON_UC_SUPPORT + 0 DEPRECATED = 150 classified (100%)
**Evidence:** `UC_SCRIPT_COVERAGE_WAVE_4_implemented.md`
**Tests:** `tests/governance/t4/test_uc018_uc032_expansion.py` — TestWave4ScriptCoverage class

### Before/After Summary

| Domain | Total | Pre-linked | Wave-4 UC_LINKED | Wave-4 NON_UC | Unclassified |
|--------|-------|------------|------------------|---------------|--------------|
| hoc_spine | 78 | 0 | 33 | 45 | 0 |
| integrations | 48 | 0 | 7 | 41 | 0 |
| api_keys | 9 | 0 | 5 | 4 | 0 |
| overview | 5 | 0 | 2 | 3 | 0 |
| agent | 4 | 0 | 0 | 4 | 0 |
| ops | 4 | 0 | 0 | 4 | 0 |
| apis | 2 | 0 | 0 | 2 | 0 |
| **Total** | **150** | **0** | **47** | **103** | **0** |

### UC_LINKED Expansions (hoc_spine handlers → L4 dispatch to L5 domains)

**UC-001 expanded anchors** (LLM run monitoring L4 dispatch):
- `hoc_spine/orchestrator/handlers/agent_handler.py` — agent operations during runs
- `hoc_spine/orchestrator/handlers/logs_handler.py` — log operations during monitoring
- `hoc_spine/orchestrator/handlers/orphan_recovery_handler.py` — orphan run recovery
- `hoc_spine/orchestrator/handlers/overview_handler.py` — overview dashboard operations
- `hoc_spine/orchestrator/handlers/policy_governance_handler.py` — policy governance during runs
- `hoc_spine/orchestrator/handlers/run_governance_handler.py` — run governance dispatch
- `hoc_spine/orchestrator/handlers/traces_handler.py` — trace operations

**UC-002 expanded anchors** (customer onboarding L4 dispatch):
- `hoc_spine/orchestrator/handlers/account_handler.py` — account queries dispatch
- `hoc_spine/orchestrator/handlers/api_keys_handler.py` — API key management
- `hoc_spine/orchestrator/handlers/integration_bootstrap_handler.py` — integration bootstrap
- `hoc_spine/orchestrator/handlers/integrations_handler.py` — integration management
- `hoc_spine/orchestrator/handlers/lifecycle_handler.py` — lifecycle transitions
- `hoc_spine/orchestrator/handlers/mcp_handler.py` — MCP handler for integration setup

**UC-024 expanded anchors** (cost anomaly detection L4 dispatch):
- `hoc_spine/orchestrator/handlers/analytics_config_handler.py` — analytics config
- `hoc_spine/orchestrator/handlers/analytics_handler.py` — main analytics handler
- `hoc_spine/orchestrator/handlers/analytics_metrics_handler.py` — analytics metrics

**UC-025 expanded anchors** (prediction cycle L4 dispatch):
- `hoc_spine/orchestrator/handlers/analytics_prediction_handler.py` — prediction handler

**UC-026 expanded anchors** (dataset validation L4 dispatch):
- `hoc_spine/orchestrator/handlers/analytics_validation_handler.py` — validation handler

**UC-027 expanded anchors** (snapshot jobs L4 dispatch):
- `hoc_spine/orchestrator/handlers/analytics_sandbox_handler.py` — sandbox handler
- `hoc_spine/orchestrator/handlers/analytics_snapshot_handler.py` — snapshot handler

**UC-MON-07 expanded anchors** (incident detection L4 dispatch):
- `hoc_spine/orchestrator/handlers/incidents_handler.py` — incidents handler

### UC_LINKED Expansions (hoc_spine coordinators → L4 cross-domain coordination)

**UC-001 expanded anchors** (run monitoring coordinators):
- `hoc_spine/orchestrator/coordinators/evidence_coordinator.py` — evidence collection
- `hoc_spine/orchestrator/coordinators/execution_coordinator.py` — run execution coordination
- `hoc_spine/orchestrator/coordinators/replay_coordinator.py` — run replay coordination
- `hoc_spine/orchestrator/coordinators/run_evidence_coordinator.py` — run evidence tracking
- `hoc_spine/orchestrator/coordinators/run_proof_coordinator.py` — run proof generation
- `hoc_spine/orchestrator/coordinators/signal_coordinator.py` — signal routing during runs

**UC-024 expanded anchors** (analytics coordinators):
- `hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py` — anomaly→incident bridge
- `hoc_spine/orchestrator/coordinators/leadership_coordinator.py` — analytics leadership election
- `hoc_spine/orchestrator/coordinators/provenance_coordinator.py` — cost provenance tracking

**UC-027 expanded anchors** (snapshot/canary coordinators):
- `hoc_spine/orchestrator/coordinators/canary_coordinator.py` — daily canary validation
- `hoc_spine/orchestrator/coordinators/snapshot_scheduler.py` — snapshot scheduling

**UC-MON-04 expanded anchors** (signal feedback coordinator):
- `hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py` — signal feedback loop

### UC_LINKED Expansions (api_keys → UC-002)

**UC-002 expanded anchors** (API key management for onboarding):
- `api_keys/L5_engines/api_keys_facade.py` — API key operations facade
- `api_keys/L5_engines/keys_engine.py` — key generation/rotation logic
- `api_keys/L6_drivers/api_keys_facade_driver.py` — API key persistence
- `api_keys/L6_drivers/keys_driver.py` — key data access
- `api_keys/adapters/customer_keys_adapter.py` — customer boundary adapter

### UC_LINKED Expansions (integrations → UC-002)

**UC-002 expanded anchors** (integration management for onboarding):
- `integrations/L5_engines/connectors_facade.py` — connector management facade
- `integrations/L5_engines/cus_health_engine.py` — connector health checks
- `integrations/L5_engines/cus_integration_engine.py` — integration CRUD logic
- `integrations/L5_engines/integrations_facade.py` — main integration facade
- `integrations/L6_drivers/bridges_driver.py` — integration bridge persistence
- `integrations/L6_drivers/cus_health_driver.py` — health check persistence
- `integrations/L6_drivers/cus_integration_driver.py` — integration persistence

### UC_LINKED Expansions (overview → UC-001)

**UC-001 expanded anchors** (overview dashboard for run monitoring):
- `overview/L5_engines/overview_facade.py` — overview dashboard facade
- `overview/L6_drivers/overview_facade_driver.py` — overview data persistence

### NON_UC_SUPPORT Classification Groups (Wave-4)

**hoc_spine authority infrastructure** (15): All files under `hoc_spine/authority/` — concurrent_runs, contracts (init + contract_engine), degraded_mode_checker, gateway_policy, guard_write_engine, lifecycle_provider, profile_policy_mode, rbac_policy, route_planes, runtime, runtime_adapter, runtime_switch, veil_policy, plus init
**hoc_spine consequences adapters** (3): dispatch_metrics_adapter, export_bundle_adapter, plus init
**hoc_spine coordinator bridges** (14): 10 domain bridges (account, activity, analytics, api_keys, controls, incidents, integrations, logs, overview, policies), domain_bridge, lessons_coordinator, plus 2 init files
**hoc_spine handler infrastructure** (13): circuit_breaker_handler, governance_audit_handler, idempotency_handler, integrity_handler, killswitch_handler, knowledge_planes_handler, m25_integration_handler, ops_handler, platform_handler, policy_approval_handler, proxy_handler, system_handler, plus init
**agent domain** (4): All agent L6 drivers (discovery_stats_driver, platform_driver, routing_driver) + init — agent platform infrastructure
**api_keys package inits** (4): init files across L5_engines, L5_schemas, L6_drivers, adapters
**apis domain** (2): keys_driver + init — separate API keys driver
**integrations L5 engines infra** (9): init, credentials (init + protocol), datasources_facade, mcp_server_engine, mcp_tool_invocation_engine, prevention_contract, sql_gateway, types
**integrations L5 schemas** (7): init, audit_schemas, cus_enums, cus_schemas, datasource_model, loop_events, sql_gateway_protocol
**integrations L6 drivers infra** (5): init, mcp_driver, proxy_driver, sql_gateway_driver, worker_registry_driver
**integrations external adapters** (20): init, cloud_functions_adapter, customer_activity_adapter, customer_keys_adapter, file_storage_base, founder_ops_adapter, gcs_adapter, lambda_adapter, mcp_server_registry, pgvector_adapter, pinecone_adapter, runtime_adapter, s3_adapter, serverless_base, slack_adapter, smtp_adapter, vector_stores_base, weaviate_adapter, webhook_adapter, workers_adapter
**ops domain** (4): cost_ops_engine, cost_read_driver, plus 2 inits — founder ops infrastructure
**overview package inits** (3): init files across L5_engines, L5_schemas, L6_drivers
**ops stagetest infrastructure** (4): stagetest_read_engine, stagetest schemas, stagetest L2 router, stagetest facade registration

---

## Stagetest Evidence Console (FDR/OPS)

**Added:** 2026-02-15
**Audience:** `fdr` (founder)
**Status:** GREEN
**Canonical API prefix:** `/hoc/api/stagetest/*`
**FORBIDDEN:** `/api/v1/stagetest/*`

### Code Artifacts

| Layer | File | Role |
|-------|------|------|
| L2 Router | `app/hoc/api/fdr/ops/stagetest.py` | 5 GET endpoints, verify_fops_token auth |
| L2.1 Facade | `app/hoc/api/facades/fdr/ops.py` | stagetest_router registered |
| L5 Engine | `app/hoc/fdr/ops/engines/stagetest_read_engine.py` | Filesystem artifact reader |
| L5 Schema | `app/hoc/fdr/ops/schemas/stagetest.py` | Pydantic response models |
| L1 UI | `website/app-shell/src/features/stagetest/` | 5 component files |
| Route | `website/app-shell/src/routes/index.tsx` | /prefops/stagetest + /fops/stagetest |

### Verification Artifacts

| Artifact | Path |
|----------|------|
| Route prefix guard | `scripts/verification/stagetest_route_prefix_guard.py` |
| Artifact integrity check | `scripts/verification/stagetest_artifact_check.py` |
| Artifact schema | `app/hoc/docs/architecture/usecases/stagetest_artifact_schema.json` |
| API tests | `tests/api/test_stagetest_read_api.py` (8 tests) |
| Governance tests | `tests/governance/t4/test_stagetest_route_prefix_guard.py` (3 tests) |
| Playwright tests | `website/app-shell/tests/uat/stagetest.spec.ts` (8 tests) |
| Deploy plan | `app/hoc/docs/architecture/usecases/STAGETEST_SUBDOMAIN_DEPLOY_PLAN_2026-02-15.md` |

### Endpoints

| Method | Path | Response |
|--------|------|----------|
| GET | `/hoc/api/stagetest/runs` | RunListResponse |
| GET | `/hoc/api/stagetest/runs/{run_id}` | RunSummary |
| GET | `/hoc/api/stagetest/runs/{run_id}/cases` | CaseListResponse |
| GET | `/hoc/api/stagetest/runs/{run_id}/cases/{case_id}` | CaseDetail |
| GET | `/hoc/api/stagetest/apis` | ApisSnapshotResponse |
