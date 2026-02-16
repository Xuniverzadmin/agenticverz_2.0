# UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed

**Created:** 2026-02-15 18:20:03 UTC
**Executed:** 2026-02-15 19:31:44 UTC
**Executor:** Claude (Opus 4.6)
**Pack Source:** `UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15.md`
**Status:** COMPLETED

## Executive Summary

- **Total Cases:** 51
- **Stage 1.1:** 0 PASS, 0 FAIL, 29 BLOCKED, 22 SKIPPED
- **Stage 1.2:** 8 PASS, 0 FAIL, 43 BLOCKED, 0 SKIPPED
- **Stage 2:** 0 PASS, 0 FAIL, 51 BLOCKED, 0 SKIPPED
- **Governance Gates:** 4/4 PASS
- **Trace-Cert Policy Enforced:** YES
- **Stagetest Run ID (Stage 1.2):** `20260215T183144Z`

## Stage Status

<!-- STAGE_STATUS_TABLE_START -->
| Stage | Status | Started | Completed | Notes |
|------|--------|---------|-----------|-------|
| Stage 1.1 | COMPLETED | 2026-02-15T19:31:10Z | 2026-02-15T19:31:40Z | 29 BLOCKED (trace-cert missing), 22 SKIPPED (UNMAPPED) |
| Stage 1.2 | COMPLETED | 2026-02-15T19:31:40Z | 2026-02-15T19:31:50Z | 8 PASS (operation-matched trace artifacts), 43 BLOCKED |
| Stage 2 | COMPLETED | 2026-02-15T19:31:50Z | 2026-02-15T19:31:50Z | All cases BLOCKED: real environment credentials not set |
<!-- STAGE_STATUS_TABLE_END -->

## Case Results

<!-- CASE_RESULTS_TABLE_START -->
| Case ID | UC | Operation | Stage 1.1 | Stage 1.2 | Stage 2 | Route Tested | Output Artifact | Trace Artifact | DB Writes Artifact | Notes |
|---------|----|-----------|-----------|-----------|---------|--------------|-----------------|----------------|--------------------|-------|
| `TC-UC-001-001` | `UC-001` | `event_schema_contract (shared authority)` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-001-002` | `UC-001` | `activity.query/activity.telemetry/activity.orphan_recovery` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/activity/runs; GET /hoc/api/cus/activity/runs/{run_id}; GET /hoc/api/cus/activity/summary/by-status | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); LOCAL_HTTP_PREREQ_MISSING (BASE_URL/AUTH_TOKEN/TENANT_ID) for synthetic route trigger; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-002-001` | `UC-002` | `account.onboarding.advance` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_activation_predicate.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC002OnboardingFlow__test_onboarding_advance_operation_registered.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC002OnboardingFlow__test_onboarding_advance_operation_registered.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC002OnboardingFlow__test_onboarding_advance_operation_registered.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-002-002` | `UC-002` | `account.onboarding.query/account.onboarding.advance` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc001_uc002_validation.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC002OnboardingFlow__test_onboarding_query_operation_registered.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC002OnboardingFlow__test_onboarding_query_operation_registered.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC002OnboardingFlow__test_onboarding_query_operation_registered.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-002-003` | `UC-002` | `integrations.connector_registry (L6 runtime cache for onboarding)` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc001_uc002_validation.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); STAGE12_OPERATION_MISMATCH: suite ran but no direct operation-level artifact match for this TC row; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-002-004` | `UC-002` | `event_schema_contract (shared authority)` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); STAGE12_OPERATION_MISMATCH: suite ran but no direct operation-level artifact match for this TC row; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-003-001` | `UC-003` | `list_traces/store_trace/get_trace/delete_trace/cleanup_old_traces` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/traces; POST /hoc/api/cus/traces; GET /hoc/api/cus/traces/{run_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); LOCAL_HTTP_PREREQ_MISSING (BASE_URL/AUTH_TOKEN/TENANT_ID) for synthetic route trigger; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-003-002` | `UC-003` | `start_trace/record_step/complete_trace/store_trace/get_trace/search_traces/list_traces/delete_trace/get_trace_count/cleanup_old_traces/mark_trace_aborted` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/traces; POST /hoc/api/cus/traces; GET /hoc/api/cus/traces/{run_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); LOCAL_HTTP_PREREQ_MISSING (BASE_URL/AUTH_TOKEN/TENANT_ID) for synthetic route trigger; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-004-001` | `UC-004` | `controls.evaluation_evidence` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_storage_contract.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC004ControlsEvidence__test_controls_evaluation_evidence_registered.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC004ControlsEvidence__test_controls_evaluation_evidence_registered.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC004ControlsEvidence__test_controls_evaluation_evidence_registered.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-004-002` | `UC-004` | `controls.query/controls.circuit_breaker/controls.killswitch.read/controls.killswitch.write/controls.evaluation_evidence` | BLOCKED | PASS | BLOCKED | GET /hoc/api/cus/controls; GET /hoc/api/cus/controls/status; GET /hoc/api/cus/controls/{control_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC004ControlsEvidence__test_evaluation_evidence_driver_methods.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC004ControlsEvidence__test_evaluation_evidence_driver_methods.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC004ControlsEvidence__test_evaluation_evidence_driver_methods.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-005-001` | `UC-005` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-006-001` | `UC-006` | `activity.signal_feedback` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_activity_facade.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_signal_feedback_operation_registered.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_signal_feedback_operation_registered.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC006SignalFeedbackFlow__test_signal_feedback_operation_registered.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-006-002` | `UC-006` | `activity.signal_feedback (L6 driver)` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_storage_contract.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_l6_signal_feedback_driver_methods.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_l6_signal_feedback_driver_methods.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC006SignalFeedbackFlow__test_l6_signal_feedback_driver_methods.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-006-003` | `UC-006` | `activity.signal_feedback` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_l5_signal_feedback_service_methods.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_l5_signal_feedback_service_methods.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC006SignalFeedbackFlow__test_l5_signal_feedback_service_methods.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-007-001` | `UC-007` | `incidents.query/incidents.write/incidents.cost_guard/incidents.recurrence` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/incidents; GET /hoc/api/cus/incidents/by-run/{run_id}; GET /hoc/api/cus/incidents/patterns | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); LOCAL_HTTP_PREREQ_MISSING (BASE_URL/AUTH_TOKEN/TENANT_ID) for synthetic route trigger; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-008-001` | `UC-008` | `analytics.artifacts` | BLOCKED | PASS | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_storage_contract.log` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC008AnalyticsArtifacts__test_analytics_artifacts_operation_registered.json` | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC008AnalyticsArtifacts__test_analytics_artifacts_operation_registered.json` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); PASS via operation-matched stage1.2 artifact (TestUC008AnalyticsArtifacts__test_analytics_artifacts_operation_registered.json); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-009-001` | `UC-009` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-010-001` | `UC-010` | `activity.signal_fingerprint/activity.discovery` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-011-001` | `UC-011` | `incidents.export` | BLOCKED | BLOCKED | BLOCKED | POST /hoc/api/cus/{incident_id}/export/evidence; POST /hoc/api/cus/{incident_id}/export/soc2; POST /hoc/api/cus/{incident_id}/export/executive-debrief | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); LOCAL_HTTP_PREREQ_MISSING (BASE_URL/AUTH_TOKEN/TENANT_ID) for synthetic route trigger; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-012-001` | `UC-012` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-013-001` | `UC-013` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-014-001` | `UC-014` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-015-001` | `UC-015` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-016-001` | `UC-016` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-017-001` | `UC-017` | `get_trace_by_root_hash/compare_traces/check_idempotency` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/traces; POST /hoc/api/cus/traces; GET /hoc/api/cus/traces/{run_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); STAGE12_OPERATION_MISMATCH: suite ran (test_l5_trace_api_engine_methods op=logs.trace_replay.get) but no direct operation-level artifact match for this TC row (get_trace_by_root_hash/compare_traces/check_idempotency); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-017-002` | `UC-017` | `get_trace_by_root_hash/check_idempotency_key` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/traces; POST /hoc/api/cus/traces; GET /hoc/api/cus/traces/{run_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); STAGE12_OPERATION_MISMATCH: suite ran (test_l5_trace_api_engine_methods op=logs.trace_replay.get) but no direct operation-level artifact match for this TC row (get_trace_by_root_hash/check_idempotency_key); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-017-003` | `UC-017` | `base lifecycle methods/get_trace_by_root_hash/search_traces` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/traces; POST /hoc/api/cus/traces; GET /hoc/api/cus/traces/{run_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_runtime_determinism.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); STAGE12_OPERATION_MISMATCH: suite ran (test_l6_postgres_trace_store_methods op=logs.trace_store.get) but no direct operation-level artifact match for this TC row (base lifecycle methods/get_trace_by_root_hash/search_traces); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-018-001` | `UC-018` | `policies.query/policies.rules/policies.proposals_query/policies.rules_query/policies.policy_facade/policies.approval` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/policies; POST /hoc/api/cus/policies; GET /hoc/api/cus/policies/{id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc018_uc032_expansion.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); LOCAL_HTTP_PREREQ_MISSING (BASE_URL/AUTH_TOKEN/TENANT_ID) for synthetic route trigger; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-019-001` | `UC-019` | `policies.enforcement/policies.enforcement_write/policies.health/policies.guard_read/policies.sync_guard_read/policies.workers` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc018_uc032_expansion.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-020-001` | `UC-020` | `policies.governance/rbac.audit` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc018_uc032_expansion.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-021-001` | `UC-021` | `controls.thresholds/controls.overrides` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-021-002` | `UC-021` | `policies.limits/policies.limits_query/policies.rate_limits` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc018_uc032_expansion.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-022-001` | `UC-022` | `policies.lessons/policies.recovery.match/policies.recovery.write/policies.recovery.read` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc018_uc032_expansion.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-023-001` | `UC-023` | `policies.simulate/policies.customer_visibility/policies.replay` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_uc018_uc032_expansion.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-024-001` | `UC-024` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-025-001` | `UC-025` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-026-001` | `UC-026` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-027-001` | `UC-027` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-028-001` | `UC-028` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-029-001` | `UC-029` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-030-001` | `UC-030` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-031-001` | `UC-031` | `incidents.recovery_rules` | BLOCKED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_event_contract.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); ROUTE_UNRESOLVED: cannot execute synthetic HTTP trigger locally; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-032-001` | `UC-032` | `find_matching_traces/update_trace_determinism` | BLOCKED | BLOCKED | BLOCKED | GET /hoc/api/cus/traces; POST /hoc/api/cus/traces; GET /hoc/api/cus/traces/{run_id} | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_runtime_determinism.log` | `` | `` | TRACE_CERT_MISSING_ARTIFACT (stage 1.1 verifier is structural/static and emits no trace/db artifact); STAGE12_OPERATION_MISMATCH: suite ran (test_trace_store_has_required_methods op=logs.redaction.apply) but no direct operation-level artifact match for this TC row (find_matching_traces/update_trace_determinism); REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-033-001` | `UC-033` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-034-001` | `UC-034` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-035-001` | `UC-035` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-036-001` | `UC-036` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-037-001` | `UC-037` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-038-001` | `UC-038` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-039-001` | `UC-039` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
| `TC-UC-040-001` | `UC-040` | `UNMAPPED` | SKIPPED | BLOCKED | BLOCKED | NO_ROUTE_EVIDENCE | `` | `` | `` | UNMAPPED: no test ref in manifest; UNMAPPED: no stage1.2 executable mapping; REAL_ENV_PREREQ_MISSING (BASE_URL, AUTH_TOKEN, TENANT_ID, REAL_INPUT_JSON; optional LLM_API_KEY) |
<!-- CASE_RESULTS_TABLE_END -->

## Metric Scorecard

<!-- METRIC_TABLE_START -->
| Metric | Target | Observed | Status | Evidence |
|--------|--------|----------|--------|----------|
| quality | meets UC behavior contract | Stage 1.1 verifiers all green (525 assertions, 0 failures); only operation-matched stage1.2 rows certified | PARTIAL | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_*.log`, `evidence_uc_all_trace_cert_v3_2026_02_15/stage12_uat_trace.log` |
| quantity | expected volume/count bounds | Stage1.1 assertions/tests: 525 (64+11+19+78+6+330+17); Stage1.2 tests: 23 | OBSERVED | `evidence_uc_all_trace_cert_v3_2026_02_15/stage11_*.log`, `evidence_uc_all_trace_cert_v3_2026_02_15/stage12_uat_trace.log` |
| velocity | meets latency/SLO envelope | Stage1.2 local suite: 23 passed in 0.46s | PARTIAL | `evidence_uc_all_trace_cert_v3_2026_02_15/stage12_uat_trace.log` |
| veracity | consistent with source truth | Conservative operation-match policy applied; no force-fit PASS | PARTIAL | `evidence_uc_all_trace_cert_v3_2026_02_15/stage12_uat_trace.log`, `evidence_uc_all_trace_cert_v3_2026_02_15/stage12_artifact_check.log` |
| determinism | replay/hash stable across reruns | Artifact integrity strict check 33/33 PASS | PARTIAL | `evidence_uc_all_trace_cert_v3_2026_02_15/stage12_artifact_check.log` |
| execution_trace_coverage | expected layer sequence captured | 8/51 TC rows have mapped execution_trace artifacts | PARTIAL | `backend/artifacts/stagetest/20260215T183144Z/cases/*.json` |
| db_write_observability | expected table/op writes captured | 8/51 mapped artifacts present; supplementary artifacts show 2 non-empty db_writes (synthetic write insert/update) | PARTIAL | `backend/artifacts/stagetest/20260215T183144Z/cases/*.json` |
<!-- METRIC_TABLE_END -->

## Synthetic Input Source Used

- `UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_synthetic_inputs.json`

## Command Outputs

```text
# Stage 1.1
$ PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
Total: 64 | PASS: 64 | FAIL: 0
$ PYTHONPATH=. pytest -q tests/governance/t4/test_activation_predicate_authority.py
11 passed in 1.42s
$ PYTHONPATH=. python3 scripts/verification/uc001_uc002_validation.py
Total: 19 | Passed: 19 | Failed: 0
$ PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
Total: 78 | PASS: 78 | FAIL: 0
$ PYTHONPATH=. pytest -q tests/test_activity_facade_introspection.py
6 passed in 2.68s
$ PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py
330 passed in 1.88s
$ PYTHONPATH=. pytest -q tests/runtime/test_runtime_determinism.py
17 passed in 1.50s

# Stage 1.2
$ STAGETEST_EMIT=1 PYTHONPATH=. pytest -q tests/uat/
23 passed in 0.46s
$ python3 scripts/verification/stagetest_artifact_check.py --strict --run-id 20260215T183144Z
PASS: All 33 checks passed

# Governance
$ PYTHONPATH=. python3 scripts/verification/uc_operation_manifest_check.py --strict
Summary: 6 passed, 0 failed [strict]
$ PYTHONPATH=. pytest -q tests/governance/t4/test_uc_mapping_decision_table.py tests/governance/t4/test_uc_operation_manifest_integrity.py
29 passed in 0.77s
$ PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
CLEAN: No layer boundary violations found
$ PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
All checks passed. 0 blocking violations (0 known exceptions).
```

## Execution Trace and DB Writes

<!-- TRACE_DB_TABLE_START -->
| Case ID | Execution Trace Events | DB Writes | Layer Coverage | DB Coverage | Evidence File | Notes |
|---------|------------------------|-----------|----------------|-------------|---------------|-------|
| `TC-UC-001-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-001-002` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-002-001` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC002OnboardingFlow__test_onboarding_advance_operation_registered.json` | operation-matched stage1.2 artifact |
| `TC-UC-002-002` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC002OnboardingFlow__test_onboarding_query_operation_registered.json` | operation-matched stage1.2 artifact |
| `TC-UC-002-003` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-002-004` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-003-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-003-002` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-004-001` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC004ControlsEvidence__test_controls_evaluation_evidence_registered.json` | operation-matched stage1.2 artifact |
| `TC-UC-004-002` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC004ControlsEvidence__test_evaluation_evidence_driver_methods.json` | operation-matched stage1.2 artifact |
| `TC-UC-005-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-006-001` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_signal_feedback_operation_registered.json` | operation-matched stage1.2 artifact |
| `TC-UC-006-002` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_l6_signal_feedback_driver_methods.json` | operation-matched stage1.2 artifact |
| `TC-UC-006-003` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC006SignalFeedbackFlow__test_l5_signal_feedback_service_methods.json` | operation-matched stage1.2 artifact |
| `TC-UC-007-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-008-001` | 2 | 0 | TEST | no writes captured | `backend/artifacts/stagetest/20260215T183144Z/cases/TestUC008AnalyticsArtifacts__test_analytics_artifacts_operation_registered.json` | operation-matched stage1.2 artifact |
| `TC-UC-009-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-010-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-011-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-012-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-013-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-014-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-015-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-016-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-017-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-017-002` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-017-003` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-018-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-019-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-020-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-021-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-021-002` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-022-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-023-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-024-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-025-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-026-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-027-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-028-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-029-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-030-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-031-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-032-001` | MISSING | MISSING | N/A | N/A | `` | TRACE_CERT_MISSING_ARTIFACT |
| `TC-UC-033-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-034-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-035-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-036-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-037-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-038-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-039-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
| `TC-UC-040-001` | SKIPPED | SKIPPED | N/A | N/A | `` | UNMAPPED |
<!-- TRACE_DB_TABLE_END -->

## Failures and Blockers

- Case ID: `TC-UC-002-003`, `TC-UC-002-004`, `TC-UC-017-001`, `TC-UC-017-002`, `TC-UC-017-003`, `TC-UC-032-001`
- Stage: 1.2
- Failure: Trace-capable suites ran, but no direct operation-level artifact match for those TC operation definitions.
- Root cause: Stage1.2 emitted operations (e.g., `logs.trace_replay.get`, `logs.redaction.apply`) are partially misaligned with manifest case operation strings for these rows (e.g., `get_trace_by_root_hash/compare_traces/check_idempotency`, `find_matching_traces/update_trace_determinism`).
- Next action: add operation-matched UAT cases (or update manifest split) before certifying these rows as PASS.

- Case ID: all Stage 2 rows
- Stage: 2
- Failure: Real environment prerequisites missing
- Root cause: `BASE_URL`, `AUTH_TOKEN`, `TENANT_ID`, `REAL_INPUT_JSON` are unset locally
- Next action: provide real env credentials and rerun Stage 2
