# UC_STAGE11_STAGE12_EXECUTION_2026_02_15

**Created:** 2026-02-15 10:43:31 UTC
**Executor:** Claude
**Execution Rule:** This document defines test cases only. Do not auto-run tests from this generator.

## Sources

1. `/root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/INDEX.md`
2. `/root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_OPERATION_MANIFEST_2026-02-15.json`
3. `/root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_MONITORING_ROUTE_OPERATION_MAP.md`

## Scope

| UC ID | Usecase | Status | Audience |
|------|---------|--------|----------|
| `UC-002` | Customer Onboarding | ``GREEN`` | ``cust`` |
| `UC-004` | Runtime Controls Evaluation | ``GREEN`` | ``cust`` |
| `UC-006` | Activity Stream + Feedback | ``GREEN`` | ``cust`` |
| `UC-008` | Reproducible Analytics Artifacts | ``GREEN`` | ``cust`` |
| `UC-017` | Logs Replay Mode + Integrity Versioning | ``GREEN`` | ``cust`` |
| `UC-032` | Logs Redaction Governance + Trace-Safe Export | ``GREEN`` | ``cust`` |

## Stage 1.1: Wiring and Trigger Validation

| Case ID | UC | Operation | Route(s) | Trigger Command | Output Checks | Deterministic Evidence |
|---------|----|-----------|----------|-----------------|---------------|------------------------|
| `TC-UC-002-001` | `UC-002` | `account.onboarding.advance` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/governance/t4/test_activation_predicate_authority.py` |
| `TC-UC-002-002` | `UC-002` | `account.onboarding.query/account.onboarding.advance` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc001_uc002_validation.py` |
| `TC-UC-002-003` | `UC-002` | `integrations.connector_registry (L6 runtime cache for onboarding)` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc001_uc002_validation.py` |
| `TC-UC-002-004` | `UC-002` | `event_schema_contract (shared authority)` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_event_contract_check.py` |
| `TC-UC-004-001` | `UC-004` | `controls.evaluation_evidence` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_storage_contract_check.py` |
| `TC-UC-004-002` | `UC-004` | `controls.query/controls.circuit_breaker/controls.killswitch.read/controls.killswitch.write/controls.evaluation_evidence` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_event_contract_check.py` |
| `TC-UC-006-001` | `UC-006` | `activity.signal_feedback` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/test_activity_facade_introspection.py` |
| `TC-UC-006-002` | `UC-006` | `activity.signal_feedback (L6 driver)` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_storage_contract_check.py` |
| `TC-UC-006-003` | `UC-006` | `activity.signal_feedback` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_event_contract_check.py` |
| `TC-UC-008-001` | `UC-008` | `analytics.artifacts` | `NO_ROUTE_EVIDENCE` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_storage_contract_check.py` |
| `TC-UC-017-001` | `UC-017` | `get_trace_by_root_hash/compare_traces/check_idempotency` | `UNKNOWN logs.traces_api` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_event_contract_check.py` |
| `TC-UC-017-002` | `UC-017` | `get_trace_by_root_hash/check_idempotency_key` | `UNKNOWN logs.traces_api` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q scripts/verification/uc_mon_event_contract_check.py` |
| `TC-UC-017-003` | `UC-017` | `base lifecycle methods/get_trace_by_root_hash/search_traces` | `UNKNOWN logs.traces_api` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/runtime/test_runtime_determinism.py` |
| `TC-UC-032-001` | `UC-032` | `find_matching_traces/update_trace_determinism` | `UNKNOWN logs.traces_api` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | No 404/500; expected response schema fields present; handler wiring reachable. | `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/runtime/test_runtime_determinism.py` |

## Stage 1.2: Synthetic Data Injection

Synthetic source file: `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json`

| Case ID | Synthetic Input | Injection Command | Veracity Check | Determinism Check |
|---------|------------------|-------------------|----------------|-------------------|
| `TC-UC-002-001` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-002-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-002-002` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-002-002` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-002-003` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-002-003` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-002-004` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-002-004` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-004-001` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-004-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-004-002` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-004-002` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-006-001` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-006-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-006-002` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-006-002` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-006-003` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-006-003` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-008-001` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-008-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-017-001` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-017-001` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-017-002` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-017-002` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-017-003` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-017-003` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |
| `TC-UC-032-001` | `UC_STAGE11_STAGE12_EXECUTION_2026_02_15_synthetic_inputs.json::TC-UC-032-001` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | Assert response matches expected schema and semantic constraints for operation. | Run same input twice; hash key output fields; require stable digest. |

## Stage 2: Real Data Integrated Validation

Required environment: `BASE_URL`, `AUTH_TOKEN`, `TENANT_ID`, `REAL_INPUT_JSON`, optional `LLM_API_KEY`.

| Case ID | Real Route Trigger | Quality | Quantity | Velocity | Veracity | Determinism |
|---------|--------------------|---------|----------|----------|----------|-------------|
| `TC-UC-002-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-002-002` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-002-003` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-002-004` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-004-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-004-002` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-006-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-006-002` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-006-003` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-008-001` | `Route unresolved: execute mapped test refs and handler-operation checks only.` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-017-001` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-017-002` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-017-003` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |
| `TC-UC-032-001` | `curl -sS -X UNKNOWN "$BASE_URLlogs.traces_api" -H 'Authorization: Bearer $AUTH_TOKEN' -H 'X-Tenant-ID: $TENANT_ID'` | response correctness | expected record counts | latency/SLO | source-truth consistency | replay consistency |

## Determinism and Governance Gates (Manual Execution)

Run from `/root/agenticverz2.0/backend`:

1. `PYTHONPATH=. python3 scripts/verification/uc_operation_manifest_check.py --strict`
2. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc_mapping_decision_table.py tests/governance/t4/test_uc_operation_manifest_integrity.py`
3. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
4. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`

## Claude Execution Prompt

`claude -p "In /root/agenticverz2.0 execute the staged tests in UC_STAGE11_STAGE12_EXECUTION_2026_02_15.md. Fill only UC_STAGE11_STAGE12_EXECUTION_2026_02_15_executed.md with outcomes, evidence paths, command outputs, and blockers. Do not edit the source pack."`

