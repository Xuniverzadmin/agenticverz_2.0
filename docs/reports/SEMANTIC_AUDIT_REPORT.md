# Semantic Audit Report

**Generated:** 2025-12-30T19:35:24.711561
**Scanned Path:** `/root/agenticverz2.0/backend/app`

## Executive Summary

| Metric | Value |
|--------|-------|
| Files Scanned | 336 |
| Files with Signals | 93 |
| Total Findings | 352 |
| Risk Score | 7840 |

### Risk Distribution

| Level | Count |
|-------|-------|
| CRITICAL | 0 |
| HIGH_RISK | 308 |
| WARNING | 24 |
| INFO | 20 |

## Findings by Type

### WRITE_OUTSIDE_WRITE_SERVICE

**Count:** 297

| File | Line | Message |
|------|------|---------|
| `cli.py` | 70 | DB write 'session.add' in 'create_agent' outside write service |
| `cli.py` | 70 | DB write 'session.commit' in 'create_agent' outside write service |
| `cli.py` | 122 | DB write 'session.add' in 'create_run' outside write service |
| `cli.py` | 122 | DB write 'session.commit' in 'create_run' outside write service |
| `cli.py` | 168 | DB write 'session.add' in 'run_goal' outside write service |
| `cli.py` | 168 | DB write 'session.commit' in 'run_goal' outside write service |
| `db.py` | 938 | DB write 'session.add' in 'log_status_change' outside write service |
| `db.py` | 938 | DB write 'session.commit' in 'log_status_change' outside write service |
| `main.py` | 562 | DB write 'session.add' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.commit' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.add' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.commit' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.add' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.commit' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.add' in '_execute_run_inner' outside write service |
| `main.py` | 562 | DB write 'session.commit' in '_execute_run_inner' outside write service |
| `main.py` | 852 | DB write 'session.add' in 'create_agent' outside write service |
| `main.py` | 852 | DB write 'session.commit' in 'create_agent' outside write service |
| `main.py` | 885 | DB write 'session.add' in 'post_goal' outside write service |
| `main.py` | 885 | DB write 'session.commit' in 'post_goal' outside write service |
| ... | | *277 more* |

### MISSING_SEMANTIC_HEADER

**Count:** 13

| File | Line | Message |
|------|------|---------|
| `agents/services/blackboard_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/credit_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/governance_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/invoke_audit_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/job_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/message_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/registry_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `agents/services/worker_service.py` | 1 | Boundary file (service) has comments but no semantic header fields |
| `api/legacy_routes.py` | 1 | Boundary file (api_router) missing semantic header |
| `api/rbac_api.py` | 1 | Boundary file (api_router) missing semantic header |
| `api/workers.py` | 1 | Boundary file (worker) has comments but no semantic header fields |
| `costsim/alert_worker.py` | 1 | Boundary file (worker) has comments but no semantic header fields |
| `memory/memory_service.py` | 1 | Boundary file (service) missing semantic header |

### LAYER_IMPORT_VIOLATION

**Count:** 11

| File | Line | Message |
|------|------|---------|
| `api/costsim.py` | 59 | L5 imports from L7 |
| `api/recovery_ingest.py` | 313 | L5 imports from L7 |
| `api/workers.py` | 628 | L5 imports from L7 |
| `api/workers.py` | 695 | L5 imports from L7 |
| `api/workers.py` | 962 | L5 imports from L7 |
| `api/workers.py` | 1020 | L5 imports from L7 |
| `api/workers.py` | 1363 | L5 imports from L7 |
| `services/cost_anomaly_detector.py` | 1151 | L4 imports from L6 |
| `services/cost_anomaly_detector.py` | 1154 | L4 imports from L6 |
| `services/cost_anomaly_detector.py` | 1157 | L4 imports from L6 |
| `services/cost_anomaly_detector.py` | 1160 | L4 imports from L6 |

### INCOMPLETE_SEMANTIC_HEADER

**Count:** 20

| File | Line | Message |
|------|------|---------|
| `api/customer_visibility.py` | 1 | Semantic header missing required field: Role |
| `api/guard.py` | 1 | Semantic header missing required field: Role |
| `api/v1_killswitch.py` | 1 | Semantic header missing required field: Role |
| `optimization/__init__.py` | 1 | Semantic header missing required field: Role |
| `optimization/__init__.py` | 1 | Semantic header missing required field: Layer |
| `optimization/envelopes/__init__.py` | 1 | Semantic header missing required field: Role |
| `optimization/envelopes/__init__.py` | 1 | Semantic header missing required field: Layer |
| `routing/__init__.py` | 1 | Semantic header missing required field: Role |
| `routing/__init__.py` | 1 | Semantic header missing required field: Layer |
| `security/__init__.py` | 1 | Semantic header missing required field: Role |
| `services/certificate.py` | 1 | Semantic header missing required field: Role |
| `services/cost_anomaly_detector.py` | 1 | Semantic header missing required field: Role |
| `services/email_verification.py` | 1 | Semantic header missing required field: Role |
| `services/event_emitter.py` | 1 | Semantic header missing required field: Role |
| `services/evidence_report.py` | 1 | Semantic header missing required field: Role |
| `services/pattern_detection.py` | 1 | Semantic header missing required field: Role |
| `services/policy_proposal.py` | 1 | Semantic header missing required field: Role |
| `services/prediction.py` | 1 | Semantic header missing required field: Role |
| `services/recovery_matcher.py` | 1 | Semantic header missing required field: Role |
| `services/recovery_rule_engine.py` | 1 | Semantic header missing required field: Role |

### ASYNC_BLOCKING_CALL

**Count:** 11

| File | Line | Message |
|------|------|---------|
| `api/status_history.py` | 295 | Async function 'create_export' calls blocking 'open' |
| `api/status_history.py` | 295 | Async function 'create_export' calls blocking 'open' |
| `api/status_history.py` | 362 | Async function 'download_export' calls blocking 'open' |
| `costsim/canary.py` | 574 | Async function '_save_artifacts' calls blocking 'open' |
| `costsim/canary.py` | 574 | Async function '_save_artifacts' calls blocking 'open' |
| `costsim/canary.py` | 574 | Async function '_save_artifacts' calls blocking 'open' |
| `costsim/provenance.py` | 268 | Async function '_write_to_file' calls blocking 'open' |
| `costsim/provenance.py` | 300 | Async function 'query' calls blocking 'open' |
| `stores/checkpoint_offload.py` | 369 | Async function 'restore_checkpoint_from_r2' calls blocking 'read' |
| `stores/checkpoint_offload.py` | 369 | Async function 'restore_checkpoint_from_r2' calls blocking 'read' |
| `workflow/golden.py` | 316 | Async function '_append' calls blocking 'open' |

## High Risk Findings (Detailed)

These findings require attention and should be reviewed.

### `cli.py:70`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'create_agent' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_agent

### `cli.py:70`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'create_agent' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_agent

### `cli.py:122`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'create_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_run

### `cli.py:122`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'create_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_run

### `cli.py:168`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'run_goal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: run_goal

### `cli.py:168`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'run_goal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: run_goal

### `db.py:938`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'log_status_change' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: log_status_change

### `db.py:938`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'log_status_change' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: log_status_change

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:562`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute_run_inner' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute_run_inner

### `main.py:852`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'create_agent' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_agent

### `main.py:852`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'create_agent' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_agent

### `main.py:885`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'post_goal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: post_goal

### `main.py:885`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'post_goal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: post_goal

### `main.py:1190`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'retry_failed_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: retry_failed_run

### `main.py:1190`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'retry_failed_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: retry_failed_run

### `agents/sba/evolution.py:273`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_persist_violation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_violation

### `agents/sba/evolution.py:458`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_persist_drift_signal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_drift_signal

### `agents/sba/evolution.py:582`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'apply_adjustment' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: apply_adjustment

### `agents/sba/evolution.py:651`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_persist_adjustment' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_adjustment

### `agents/sba/service.py:87`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'register_agent' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: register_agent

### `agents/sba/service.py:369`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'update_sba' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_sba

### `agents/sba/service.py:408`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'update_fulfillment_metric' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_fulfillment_metric

### `agents/sba/service.py:579`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'retrofit_missing_sba' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: retrofit_missing_sba

### `agents/services/credit_service.py:187`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'log_reservation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: log_reservation

### `agents/services/credit_service.py:276`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'spend_for_item' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: spend_for_item

### `agents/services/credit_service.py:324`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'refund_for_item' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: refund_for_item

### `agents/services/credit_service.py:381`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'charge_skill' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: charge_skill

### `agents/services/governance_service.py:220`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'update_job_budget' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_job_budget

### `agents/services/governance_service.py:315`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'allocate_worker_budget' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: allocate_worker_budget

### `agents/services/governance_service.py:436`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'record_item_llm_usage' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_item_llm_usage

### `agents/services/invoke_audit_service.py:63`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'start_invoke' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: start_invoke

### `agents/services/invoke_audit_service.py:131`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'complete_invoke' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: complete_invoke

### `agents/services/invoke_audit_service.py:185`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'fail_invoke' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: fail_invoke

### `agents/services/job_service.py:127`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'create_job' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_job

### `agents/services/job_service.py:406`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'check_job_completion' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: check_job_completion

### `agents/services/job_service.py:468`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'cancel_job' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: cancel_job

### `agents/services/message_service.py:97`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'send' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: send

### `agents/services/message_service.py:289`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'mark_delivered' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: mark_delivered

### `agents/services/message_service.py:312`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'mark_read' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: mark_read

### `agents/services/message_service.py:512`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'cleanup_old_messages' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: cleanup_old_messages

### `agents/services/registry_service.py:81`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'register' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: register

### `agents/services/registry_service.py:157`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'heartbeat' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: heartbeat

### `agents/services/registry_service.py:198`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'deregister' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: deregister

### `agents/services/registry_service.py:336`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'mark_instance_stale' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: mark_instance_stale

### `agents/services/registry_service.py:376`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'mark_stale' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: mark_stale

### `agents/services/registry_service.py:376`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'mark_stale' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: mark_stale

### `agents/services/registry_service.py:428`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'reclaim_stale_items' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: reclaim_stale_items

### `agents/services/registry_service.py:428`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'reclaim_stale_items' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: reclaim_stale_items

### `agents/services/worker_service.py:76`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'claim_item' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: claim_item

### `agents/services/worker_service.py:172`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_claim_item_raw' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _claim_item_raw

### `agents/services/worker_service.py:277`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'start_item' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: start_item

### `agents/services/worker_service.py:308`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'complete_item' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: complete_item

### `agents/services/worker_service.py:436`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'fail_item' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: fail_item

### `agents/services/worker_service.py:557`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'release_claimed' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: release_claimed

### `agents/skills/agent_invoke.py:253`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_create_invocation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _create_invocation

### `agents/skills/agent_invoke.py:407`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_fail_invocation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _fail_invocation

### `agents/skills/agent_invoke.py:425`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_timeout_invocation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _timeout_invocation

### `agents/skills/agent_invoke.py:444`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'respond_to_invoke' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: respond_to_invoke

### `agents/skills/llm_invoke_governed.py:370`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_record_governance_data' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _record_governance_data

### `api/agents.py:2101`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'update_agent_strategy' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_agent_strategy

### `api/founder_actions.py:259`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in 'execute_action' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: execute_action

### `api/founder_actions.py:517`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in 'execute_reversal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: execute_reversal

### `api/integration.py:900`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'simulate_prevention' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: simulate_prevention

### `api/integration.py:978`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'simulate_regret' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: simulate_regret

### `api/integration.py:1070`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'simulate_timeline_view' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: simulate_timeline_view

### `api/integration.py:1132`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'record_timeline_view' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_timeline_view

### `api/integration.py:1198`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'trigger_graduation_re_evaluation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: trigger_graduation_re_evaluation

### `api/memory_pins.py:135`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'write_memory_audit' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: write_memory_audit

### `api/memory_pins.py:192`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'create_or_upsert_pin' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_or_upsert_pin

### `api/memory_pins.py:448`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'delete_pin' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete_pin

### `api/memory_pins.py:505`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'cleanup_expired_pins' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: cleanup_expired_pins

### `api/policy.py:627`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'create_approval_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_approval_request

### `api/policy.py:627`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'create_approval_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_approval_request

### `api/policy.py:704`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'get_approval_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: get_approval_request

### `api/policy.py:825`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'approve_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: approve_request

### `api/policy.py:825`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'approve_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: approve_request

### `api/policy.py:892`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'reject_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: reject_request

### `api/policy.py:939`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'list_approval_requests' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: list_approval_requests

### `api/policy.py:1011`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'run_escalation_check' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: run_escalation_check

### `api/rbac_api.py:291`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'cleanup_audit_logs' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: cleanup_audit_logs

### `api/recovery.py:576`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in 'update_candidate' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_candidate

### `api/recovery_ingest.py:117`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in 'ingest_failure' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: ingest_failure

### `api/recovery_ingest.py:286`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in '_enqueue_evaluation_async' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _enqueue_evaluation_async

### `api/status_history.py:295`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function 'create_export' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `api/status_history.py:295`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function 'create_export' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `api/status_history.py:362`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function 'download_export' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `api/traces.py:653`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'bulk_report_mismatches' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: bulk_report_mismatches

### `api/traces.py:778`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'report_mismatch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: report_mismatch

### `api/traces.py:778`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'report_mismatch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: report_mismatch

### `api/traces.py:778`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'report_mismatch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: report_mismatch

### `api/traces.py:1015`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'resolve_mismatch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: resolve_mismatch

### `api/v1_proxy.py:248`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'record_usage_after_killswitch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_usage_after_killswitch

### `api/v1_proxy.py:248`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'record_usage_after_killswitch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_usage_after_killswitch

### `api/v1_proxy.py:430`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'log_proxy_call' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: log_proxy_call

### `api/v1_proxy.py:430`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'log_proxy_call' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: log_proxy_call

### `api/workers.py:194`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in '_store_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _store_run

### `api/workers.py:235`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in '_insert_cost_record' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert_cost_record

### `api/workers.py:273`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in '_check_and_emit_cost_advisory' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _check_and_emit_cost_advisory

### `api/workers.py:1208`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'write_service.commit' in 'delete_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete_run

### `auth/rbac_engine.py:396`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_audit' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _audit

### `auth/tenant_auth.py:145`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'validate_api_key_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: validate_api_key_db

### `auth/tenant_auth.py:145`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'validate_api_key_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: validate_api_key_db

### `config/flag_sync.py:109`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'sync_file_to_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: sync_file_to_db

### `config/flag_sync.py:109`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'sync_file_to_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: sync_file_to_db

### `contracts/decisions.py:949`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'backfill_run_id_for_request' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: backfill_run_id_for_request

### `contracts/decisions.py:182`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'emit' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: emit

### `contracts/decisions.py:264`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_emit_sync_impl' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _emit_sync_impl

### `costsim/alert_worker.py:303`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'enqueue_alert' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: enqueue_alert

### `costsim/alert_worker.py:303`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'enqueue_alert' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: enqueue_alert

### `costsim/alert_worker.py:357`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'retry_failed_alerts' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: retry_failed_alerts

### `costsim/alert_worker.py:395`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'purge_old_alerts' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: purge_old_alerts

### `costsim/alert_worker.py:95`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'process_batch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: process_batch

### `costsim/canary.py:574`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function '_save_artifacts' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `costsim/canary.py:574`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function '_save_artifacts' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `costsim/canary.py:574`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function '_save_artifacts' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `costsim/circuit_breaker.py:206`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_get_or_create_state' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_or_create_state

### `costsim/circuit_breaker.py:206`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_get_or_create_state' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_or_create_state

### `costsim/circuit_breaker.py:271`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_auto_recover' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _auto_recover

### `costsim/circuit_breaker.py:350`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'report_drift' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: report_drift

### `costsim/circuit_breaker.py:350`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'report_drift' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: report_drift

### `costsim/circuit_breaker.py:498`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'reset' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: reset

### `costsim/circuit_breaker.py:573`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_trip' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _trip

### `costsim/circuit_breaker.py:573`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_trip' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _trip

### `costsim/circuit_breaker.py:573`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_trip' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _trip

### `costsim/circuit_breaker.py:683`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_resolve_incident_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _resolve_incident_db

### `costsim/circuit_breaker_async.py:130`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_get_or_create_state' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_or_create_state

### `costsim/circuit_breaker_async.py:130`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in '_get_or_create_state' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_or_create_state

### `costsim/circuit_breaker_async.py:229`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in '_try_auto_recover' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _try_auto_recover

### `costsim/circuit_breaker_async.py:321`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_auto_recover' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _auto_recover

### `costsim/circuit_breaker_async.py:598`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_trip' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _trip

### `costsim/circuit_breaker_async.py:598`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in '_trip' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _trip

### `costsim/circuit_breaker_async.py:694`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_resolve_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _resolve_incident

### `costsim/circuit_breaker_async.py:762`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_enqueue_alert' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _enqueue_alert

### `costsim/circuit_breaker_async.py:762`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in '_enqueue_alert' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _enqueue_alert

### `costsim/provenance.py:268`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function '_write_to_file' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `costsim/provenance.py:300`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function 'query' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

### `costsim/provenance_async.py:61`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'write_provenance' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: write_provenance

### `costsim/provenance_async.py:61`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'write_provenance' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: write_provenance

### `costsim/provenance_async.py:146`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'write_provenance_batch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: write_provenance_batch

### `costsim/provenance_async.py:146`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'write_provenance_batch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: write_provenance_batch

### `discovery/ledger.py:50`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'emit_signal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: emit_signal

### `integrations/bridges.py:111`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'record_policy_activation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_policy_activation

### `integrations/bridges.py:415`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_increment_pattern_count' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _increment_pattern_count

### `integrations/bridges.py:432`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_create_pattern' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _create_pattern

### `integrations/bridges.py:668`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_persist_recovery' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_recovery

### `integrations/bridges.py:867`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_persist_policy' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_policy

### `integrations/bridges.py:1142`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_persist_adjustment' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_adjustment

### `integrations/cost_snapshots.py:623`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_insert_snapshot' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert_snapshot

### `integrations/cost_snapshots.py:651`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_update_snapshot' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update_snapshot

### `integrations/cost_snapshots.py:675`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_insert_aggregate' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert_aggregate

### `integrations/cost_snapshots.py:794`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_insert_baseline' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert_baseline

### `integrations/cost_snapshots.py:971`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_insert_evaluation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert_evaluation

### `integrations/cost_snapshots.py:1005`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_create_anomaly_from_evaluation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _create_anomaly_from_evaluation

### `integrations/dispatcher.py:516`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_persist_event' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_event

### `integrations/dispatcher.py:555`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_persist_loop_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_loop_status

### `integrations/dispatcher.py:591`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_persist_checkpoint' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_checkpoint

### `integrations/graduation_engine.py:757`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'persist_graduation_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_graduation_status

### `jobs/graduation_evaluator.py:38`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'evaluate_graduation_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: evaluate_graduation_status

### `jobs/storage.py:451`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_record_export_to_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _record_export_to_db

### `jobs/storage.py:491`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_update_export_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update_export_status

### `memory/memory_service.py:303`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'set' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: set

### `memory/memory_service.py:415`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'delete' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete

### `memory/memory_service.py:565`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_audit' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _audit

### `memory/store.py:64`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'store' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: store

### `memory/store.py:64`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'store' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: store

### `memory/store.py:195`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.delete' in 'delete' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete

### `memory/store.py:195`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'delete' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete

### `memory/vector_store.py:266`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'store' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: store

### `memory/vector_store.py:594`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'delete' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete

### `memory/vector_store.py:604`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'backfill_embeddings' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: backfill_embeddings

### `optimization/audit_persistence.py:62`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.add' in 'persist_audit_record' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_audit_record

### `optimization/audit_persistence.py:62`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'persist_audit_record' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_audit_record

### `policy/engine.py:1186`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_persist_evaluation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_evaluation

### `policy/engine.py:1186`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_persist_evaluation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_evaluation

### `policy/engine.py:1417`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'acknowledge_violation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: acknowledge_violation

### `policy/engine.py:1467`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'update_risk_ceiling' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_risk_ceiling

### `policy/engine.py:1502`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'reset_risk_ceiling' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: reset_risk_ceiling

### `policy/engine.py:1543`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'update_safety_rule' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_safety_rule

### `policy/engine.py:1723`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'create_policy_version' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_policy_version

### `policy/engine.py:1790`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'rollback_to_version' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: rollback_to_version

### `policy/engine.py:2007`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'resolve_conflict' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: resolve_conflict

### `policy/engine.py:2076`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'create_temporal_policy' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_temporal_policy

### `policy/engine.py:2456`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'add_dependency_with_dag_check' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: add_dependency_with_dag_check

### `policy/engine.py:2615`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'prune_temporal_metrics' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: prune_temporal_metrics

### `policy/engine.py:2786`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'activate_policy_version' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: activate_policy_version

### `predictions/api.py:65`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.add' in 'create_incident_risk_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_incident_risk_prediction

### `predictions/api.py:65`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'create_incident_risk_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_incident_risk_prediction

### `predictions/api.py:144`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.add' in 'create_spend_spike_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_spend_spike_prediction

### `predictions/api.py:144`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'create_spend_spike_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_spend_spike_prediction

### `predictions/api.py:202`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.add' in 'create_policy_drift_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_policy_drift_prediction

### `predictions/api.py:202`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'db.commit' in 'create_policy_drift_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_policy_drift_prediction

### `routing/care.py:432`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_persist_decision' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_decision

### `runtime/failure_catalog.py:577`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'persist_failure_match' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_failure_match

### `runtime/failure_catalog.py:577`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'persist_failure_match' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_failure_match

### `runtime/failure_catalog.py:791`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'update_recovery_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_recovery_status

### `runtime/failure_catalog.py:791`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'update_recovery_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_recovery_status

### `services/cost_anomaly_detector.py:676`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_record_breach_and_get_consecutive_count' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _record_breach_and_get_consecutive_count

### `services/cost_anomaly_detector.py:784`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_update_drift_tracking' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update_drift_tracking

### `services/cost_anomaly_detector.py:784`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_update_drift_tracking' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update_drift_tracking

### `services/cost_anomaly_detector.py:878`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_reset_drift_tracking' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _reset_drift_tracking

### `services/cost_anomaly_detector.py:1039`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'persist_anomalies' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_anomalies

### `services/incident_aggregator.py:263`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_get_rate_limit_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_rate_limit_incident

### `services/incident_aggregator.py:263`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_get_rate_limit_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_rate_limit_incident

### `services/incident_aggregator.py:263`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_get_rate_limit_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_rate_limit_incident

### `services/incident_aggregator.py:263`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_get_rate_limit_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _get_rate_limit_incident

### `services/incident_aggregator.py:311`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_create_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _create_incident

### `services/incident_aggregator.py:311`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_create_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _create_incident

### `services/incident_aggregator.py:366`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_add_call_to_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _add_call_to_incident

### `services/incident_aggregator.py:366`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_add_call_to_incident' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _add_call_to_incident

### `services/incident_aggregator.py:448`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_add_incident_event' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _add_incident_event

### `services/incident_aggregator.py:448`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_add_incident_event' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _add_incident_event

### `services/incident_aggregator.py:471`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'resolve_stale_incidents' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: resolve_stale_incidents

### `services/incident_aggregator.py:471`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'resolve_stale_incidents' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: resolve_stale_incidents

### `services/llm_failure_service.py:128`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self._session.commit' in 'persist_failure_and_mark_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_failure_and_mark_run

### `services/orphan_recovery.py:114`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'recover_orphaned_runs' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: recover_orphaned_runs

### `services/pattern_detection.py:227`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'emit_feedback' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: emit_feedback

### `services/pattern_detection.py:227`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in 'emit_feedback' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: emit_feedback

### `services/pattern_detection.py:268`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'run_pattern_detection' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: run_pattern_detection

### `services/policy_proposal.py:115`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'create_policy_proposal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_policy_proposal

### `services/policy_proposal.py:115`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in 'create_policy_proposal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_policy_proposal

### `services/policy_proposal.py:153`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'review_policy_proposal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: review_policy_proposal

### `services/policy_proposal.py:153`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in 'review_policy_proposal' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: review_policy_proposal

### `services/policy_proposal.py:232`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'generate_proposals_from_feedback' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: generate_proposals_from_feedback

### `services/policy_violation_service.py:110`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'persist_violation_fact' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_violation_fact

### `services/policy_violation_service.py:194`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'persist_evidence' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: persist_evidence

### `services/policy_violation_service.py:262`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'sync_session.commit' in 'create_incident_from_violation' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_incident_from_violation

### `services/prediction.py:276`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'emit_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: emit_prediction

### `services/prediction.py:276`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.flush' in 'emit_prediction' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: emit_prediction

### `services/prediction.py:318`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'run_prediction_cycle' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: run_prediction_cycle

### `services/recovery_matcher.py:576`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_upsert_candidate' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _upsert_candidate

### `services/recovery_matcher.py:814`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'approve_candidate' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: approve_candidate

### `services/tenant_service.py:67`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'create_tenant' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_tenant

### `services/tenant_service.py:112`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'update_tenant_plan' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_tenant_plan

### `services/tenant_service.py:135`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'suspend_tenant' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: suspend_tenant

### `services/tenant_service.py:151`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'create_membership_with_default' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_membership_with_default

### `services/tenant_service.py:200`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'create_api_key' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_api_key

### `services/tenant_service.py:282`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'revoke_api_key' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: revoke_api_key

### `services/tenant_service.py:367`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'increment_usage' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: increment_usage

### `services/tenant_service.py:378`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_maybe_reset_daily_counter' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _maybe_reset_daily_counter

### `services/tenant_service.py:378`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in '_maybe_reset_daily_counter' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _maybe_reset_daily_counter

### `services/tenant_service.py:394`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'record_usage' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_usage

### `services/tenant_service.py:468`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'create_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: create_run

### `services/tenant_service.py:503`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'complete_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: complete_run

### `services/worker_registry_service.py:175`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'register_worker' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: register_worker

### `services/worker_registry_service.py:217`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'update_worker_status' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_worker_status

### `services/worker_registry_service.py:245`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'set_tenant_worker_config' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: set_tenant_worker_config

### `services/worker_registry_service.py:245`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'set_tenant_worker_config' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: set_tenant_worker_config

### `services/worker_write_service_async.py:238`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self.session.commit' in 'commit' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: commit

### `skills/base.py:119`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_upsert_state' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _upsert_state

### `skills/postgres_query.py:113`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: execute

### `skills/registry_v2.py:146`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self._db.commit' in '_init_persistence' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _init_persistence

### `skills/registry_v2.py:213`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self._db.commit' in '_persist_registration' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _persist_registration

### `skills/registry_v2.py:235`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'self._db.commit' in 'deregister' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: deregister

### `stores/checkpoint_offload.py:369`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function 'restore_checkpoint_from_r2' calls blocking 'read'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: read

### `stores/checkpoint_offload.py:369`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function 'restore_checkpoint_from_r2' calls blocking 'read'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: read

### `tasks/recovery_queue_stream.py:682`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'archive_dead_letter_to_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: archive_dead_letter_to_db

### `tasks/recovery_queue_stream.py:1172`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_record_replay_to_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _record_replay_to_db

### `traces/store.py:111`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_init_db' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _init_db

### `traces/store.py:181`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'start_trace' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: start_trace

### `traces/store.py:211`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'record_step' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_step

### `traces/store.py:255`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'complete_trace' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: complete_trace

### `traces/store.py:391`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'delete_trace' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete_trace

### `traces/store.py:415`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'cleanup_old_traces' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: cleanup_old_traces

### `traces/store.py:570`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in 'update_trace_determinism' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_trace_determinism

### `traces/store.py:191`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_insert' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert

### `traces/store.py:227`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_insert' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _insert

### `traces/store.py:263`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_update' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update

### `traces/store.py:394`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_delete' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _delete

### `traces/store.py:418`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_cleanup' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _cleanup

### `traces/store.py:580`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'conn.commit' in '_update' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update

### `utils/budget_tracker.py:335`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_pause_agent' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _pause_agent

### `utils/budget_tracker.py:353`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'deduct' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: deduct

### `utils/budget_tracker.py:414`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'record_cost' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: record_cost

### `utils/db_helpers.py:378`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'get_or_create' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: get_or_create

### `utils/db_helpers.py:378`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'get_or_create' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: get_or_create

### `worker/outbox_processor.py:107`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'acquire_lock' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: acquire_lock

### `worker/outbox_processor.py:132`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'release_lock' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: release_lock

### `worker/outbox_processor.py:150`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'extend_lock' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: extend_lock

### `worker/outbox_processor.py:168`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'claim_events' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: claim_events

### `worker/outbox_processor.py:341`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'complete_event' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: complete_event

### `worker/pool.py:111`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_mark_run_started' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _mark_run_started

### `worker/pool.py:111`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_mark_run_started' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _mark_run_started

### `worker/recovery_claim_worker.py:107`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'claim_batch' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: claim_batch

### `worker/recovery_claim_worker.py:235`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'update_candidate' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: update_candidate

### `worker/recovery_claim_worker.py:284`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in 'release_pending' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: release_pending

### `worker/recovery_evaluator.py:358`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_select_action' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _select_action

### `worker/recovery_evaluator.py:409`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_record_provenance' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _record_provenance

### `worker/recovery_evaluator.py:460`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_auto_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _auto_execute

### `worker/recovery_evaluator.py:460`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_auto_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _auto_execute

### `worker/runner.py:175`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_update_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update_run

### `worker/runner.py:175`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_update_run' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _update_run

### `worker/runner.py:236`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute

### `worker/runner.py:236`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute

### `worker/runner.py:236`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute

### `worker/runner.py:236`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute

### `worker/runner.py:236`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in '_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute

### `worker/runner.py:236`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.commit' in '_execute' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: _execute

### `workflow/checkpoint.py:227`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'save' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: save

### `workflow/checkpoint.py:227`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.add' in 'save' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: save

### `workflow/checkpoint.py:428`

**Type:** WRITE_OUTSIDE_WRITE_SERVICE
**Severity:** HIGH_RISK

**Message:** DB write 'session.delete' in 'delete' outside write service

**Expected:** DB writes should be in *_write_service.py
**Observed:** Write operation in: delete

### `workflow/golden.py:316`

**Type:** ASYNC_BLOCKING_CALL
**Severity:** HIGH_RISK

**Message:** Async function '_append' calls blocking 'open'

**Expected:** Async function should use async I/O
**Observed:** Uses blocking call: open

## Findings by Domain

| Domain | Total | High Risk |
|--------|-------|-----------|
| / | 352 | 308 |

## Findings by Layer

| Layer | Total | High Risk |
|-------|-------|-----------|
| L4 | 105 | 83 |
| L5 | 59 | 46 |
| UNKNOWN | 188 | 179 |

---

*This report is observational only. It does not block CI or fail builds.*
*Review findings and address as appropriate for your context.*

Generated by Semantic Auditor v0.1.0
