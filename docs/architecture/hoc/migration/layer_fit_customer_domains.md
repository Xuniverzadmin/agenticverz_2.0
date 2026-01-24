# HOC Layer Fit Analysis - Customer Domain Report

**Generated:** 2026-01-23
**Total Files:** 715
**Total Work Items:** 542

---

## Executive Summary

| Domain | Files | FIT | MISFIT | NO_ACTION | HEADER_FIX | RECLASSIFY | EXTRACT_DRIVER | EXTRACT_AUTH | SPLIT |
|--------|-------|-----|--------|-----------|------------|------------|----------------|--------------|-------|
| **account** | 12 | 1 | 11 | 1 | 0 | 3 | 7 | 0 | 1 |
| **activity** | 9 | 5 | 4 | 5 | 1 | 2 | 1 | 0 | 0 |
| **agent** | 12 | 0 | 12 | 0 | 1 | 10 | 1 | 0 | 0 |
| **analytics** | 30 | 7 | 23 | 12 | 1 | 7 | 9 | 0 | 1 |
| **api_keys** | 3 | 0 | 3 | 0 | 0 | 0 | 3 | 0 | 0 |
| **general** | 56 | 18 | 38 | 18 | 4 | 14 | 19 | 1 | 0 |
| **incidents** | 31 | 4 | 27 | 4 | 2 | 10 | 13 | 0 | 2 |
| **integrations** | 58 | 10 | 48 | 11 | 4 | 16 | 20 | 1 | 6 |
| **logs** | 52 | 11 | 41 | 11 | 3 | 12 | 23 | 0 | 3 |
| **ops** | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| **overview** | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| **platform** | 7 | 1 | 6 | 1 | 0 | 3 | 1 | 1 | 1 |
| **policies** | 102 | 19 | 83 | 20 | 3 | 42 | 34 | 0 | 3 |
| **TOTAL** | 374 | 76 | 298 | 83 | 20 | 119 | 132 | 3 | 17 |

---

## Work Priority Matrix

| Priority | Domain | Work Items | LOW | MEDIUM | HIGH | Recommendation |
|----------|--------|------------|-----|--------|------|----------------|
| 1 | **policies** | 82 | 45 | 34 | 3 | Quick wins first |
| 2 | **integrations** | 47 | 20 | 20 | 7 | Quick wins first |
| 3 | **logs** | 41 | 15 | 23 | 3 | Batch extract drivers |
| 4 | **general** | 38 | 18 | 19 | 1 | Batch extract drivers |
| 5 | **incidents** | 27 | 12 | 13 | 2 | Batch extract drivers |
| 6 | **analytics** | 18 | 8 | 9 | 1 | Batch extract drivers |
| 7 | **agent** | 12 | 11 | 1 | 0 | Quick wins first |
| 8 | **account** | 11 | 3 | 7 | 1 | Batch extract drivers |
| 9 | **platform** | 6 | 3 | 1 | 2 | Quick wins first |
| 10 | **activity** | 4 | 3 | 1 | 0 | Quick wins first |
| 11 | **api_keys** | 3 | 0 | 3 | 0 | Batch extract drivers |
| 12 | **ops** | 1 | 1 | 0 | 0 | Quick wins first |
| 13 | **overview** | 1 | 0 | 1 | 0 | Batch extract drivers |

---

## Detailed Domain Analysis

### ACCOUNT

**Files:** 12

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 2 | 9 | 0 | 1 | 0 |
| Declared | 0 | 1 | 7 | 1 | 2 | 0 |
| Dominant | 0 | 0 | 0 | 0 | 12 | 0 |

**Work Backlog:** 11 items

**RECLASSIFY_ONLY** (3 files, LOW effort)

- `profile.py` (declared: L4, detected: L6)
- `identity_resolver.py` (declared: L4, detected: L6)
- `tenant_service.py` (declared: L6, detected: L6)

**EXTRACT_DRIVER** (7 files, MEDIUM effort)

- `accounts_facade.py` (declared: L4, detected: L6)
- `notifications_facade.py` (declared: L4, detected: L6)
- `user_write_service.py` (declared: L4, detected: L6)
- `email_verification.py` (declared: L3, detected: L6)
- `validator_service.py` (declared: L4, detected: L6)
- ... and 2 more

**SPLIT_FILE** (1 files, HIGH effort)

- `channel_service.py` (declared: L4, detected: L6)

---

### ACTIVITY

**Files:** 9

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 2 | 7 | 0 | 0 | 0 |
| Declared | 0 | 0 | 9 | 0 | 0 | 0 |
| Dominant | 0 | 1 | 0 | 0 | 7 | 1 |

**Work Backlog:** 4 items

**HEADER_FIX_ONLY** (1 files, LOW effort)

- `run_governance_facade.py` (declared: L4, detected: L3)

**RECLASSIFY_ONLY** (2 files, LOW effort)

- `llm_threshold_service.py` (declared: L4, detected: L6)
- `activity_enums.py` (declared: L4, detected: L6)

**EXTRACT_DRIVER** (1 files, MEDIUM effort)

- `activity_facade.py` (declared: L4, detected: L6)

---

### AGENT

**Files:** 12

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 0 | 12 | 0 | 0 | 0 |
| Declared | 11 | 0 | 0 | 0 | 1 | 0 |
| Dominant | 0 | 0 | 0 | 0 | 6 | 6 |

**Work Backlog:** 12 items

**HEADER_FIX_ONLY** (1 files, LOW effort)

- `panel_signal_collector.py` (declared: L2, detected: L6)

**RECLASSIFY_ONLY** (10 files, LOW effort)

- `panel_capability_resolver.py` (declared: L2, detected: L6)
- `semantic_validator.py` (declared: L2, detected: None)
- `intent_guardrails.py` (declared: L2, detected: None)
- `panel_types.py` (declared: L2, detected: L6)
- `panel_spec_loader.py` (declared: L2, detected: None)
- ... and 5 more

**EXTRACT_DRIVER** (1 files, MEDIUM effort)

- `panel_signal_translator.py` (declared: L2, detected: L6)

---

### ANALYTICS

**Files:** 30

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 3 | 27 | 0 | 0 | 0 |
| Declared | 1 | 1 | 11 | 2 | 1 | 14 |
| Dominant | 0 | 0 | 2 | 0 | 25 | 3 |

**Work Backlog:** 18 items

**HEADER_FIX_ONLY** (1 files, LOW effort)

- `ai_console_panel_engine.py` (declared: L2, detected: L4)

**RECLASSIFY_ONLY** (7 files, LOW effort)

- `leader.py` (declared: None, detected: L6)
- `killswitch.py` (declared: L4, detected: L6)
- `manager.py` (declared: L5, detected: L6)
- `provenance_async.py` (declared: None, detected: L6)
- `circuit_breaker_async.py` (declared: None, detected: L6)
- ... and 2 more

**EXTRACT_DRIVER** (9 files, MEDIUM effort)

- `analytics_facade.py` (declared: L4, detected: L6)
- `cost_anomaly_detector.py` (declared: L4, detected: L6)
- `coordinator.py` (declared: L5, detected: L6)
- `alert_worker.py` (declared: None, detected: L6)
- `cost_write_service.py` (declared: L4, detected: L6)
- ... and 4 more

**SPLIT_FILE** (1 files, HIGH effort)

- `detection_facade.py` (declared: L4, detected: L6)

---

### API_KEYS

**Files:** 3

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 1 | 2 | 0 | 0 | 0 |
| Declared | 0 | 1 | 2 | 0 | 0 | 0 |
| Dominant | 0 | 0 | 0 | 0 | 3 | 0 |

**Work Backlog:** 3 items

**EXTRACT_DRIVER** (3 files, MEDIUM effort)

- `api_keys_facade.py` (declared: L4, detected: L6)
- `keys_service.py` (declared: L4, detected: L6)
- `email_verification.py` (declared: L3, detected: L6)

---

### GENERAL

**Files:** 56

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 5 | 29 | 0 | 22 | 0 |
| Declared | 2 | 1 | 35 | 0 | 18 | 0 |
| Dominant | 3 | 1 | 1 | 0 | 45 | 6 |

**Work Backlog:** 38 items

**HEADER_FIX_ONLY** (4 files, LOW effort)

- `alerts_facade.py` (declared: L4, detected: L6)
- `compliance_facade.py` (declared: L4, detected: L6)
- `lifecycle_facade.py` (declared: L4, detected: L6)
- `common.py` (declared: L4, detected: L6)

**RECLASSIFY_ONLY** (14 files, LOW effort)

- `webhook_verify.py` (declared: L6, detected: L2)
- `alert_emitter.py` (declared: L3, detected: L6)
- `fatigue_controller.py` (declared: L4, detected: L6)
- `panel_invariant_monitor.py` (declared: L4, detected: L6)
- `ledger.py` (declared: L4, detected: L6)
- ... and 9 more

**EXTRACT_DRIVER** (19 files, MEDIUM effort)

- `monitors_facade.py` (declared: L4, detected: L6)
- `scheduler_facade.py` (declared: L4, detected: L6)
- `cus_health_service.py` (declared: L4, detected: L6)
- `cus_telemetry_service.py` (declared: L4, detected: L6)
- `knowledge_lifecycle_manager.py` (declared: L4, detected: L6)
- ... and 14 more

**EXTRACT_AUTHORITY** (1 files, HIGH effort)

- `pool_manager.py` (declared: L4, detected: L6)

---

### INCIDENTS

**Files:** 31

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 2 | 27 | 0 | 2 | 0 |
| Declared | 2 | 3 | 26 | 0 | 0 | 0 |
| Dominant | 0 | 0 | 5 | 0 | 22 | 4 |

**Work Backlog:** 27 items

**HEADER_FIX_ONLY** (2 files, LOW effort)

- `panel_verification_engine.py` (declared: L2, detected: L4)
- `evidence_report.py` (declared: L3, detected: L4)

**RECLASSIFY_ONLY** (10 files, LOW effort)

- `incident_driver.py` (declared: L4, detected: None)
- `guard_write_service.py` (declared: L4, detected: L6)
- `export_bundle_service.py` (declared: L3, detected: L6)
- `scoped_execution.py` (declared: L4, detected: L6)
- `panel_invariant_monitor.py` (declared: L4, detected: L6)
- ... and 5 more

**EXTRACT_DRIVER** (13 files, MEDIUM effort)

- `incidents_facade.py` (declared: L4, detected: L6)
- `policy_violation_service.py` (declared: L4, detected: L6)
- `incident_engine.py` (declared: L4, detected: L4)
- `postmortem_service.py` (declared: L4, detected: L6)
- `degraded_mode_checker.py` (declared: L4, detected: L6)
- ... and 8 more

**SPLIT_FILE** (2 files, HIGH effort)

- `prevention_engine.py` (declared: L4, detected: L6)
- `channel_service.py` (declared: L4, detected: L6)

---

### INTEGRATIONS

**Files:** 58

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 29 | 19 | 0 | 10 | 0 |
| Declared | 0 | 25 | 30 | 1 | 2 | 0 |
| Dominant | 5 | 5 | 2 | 0 | 46 | 0 |

**Work Backlog:** 47 items

**HEADER_FIX_ONLY** (4 files, LOW effort)

- `cost_safety_rails.py` (declared: L4, detected: L6)
- `integrations_facade.py` (declared: L4, detected: L6)
- `retrieval_facade.py` (declared: L4, detected: L6)
- `connectors_facade.py` (declared: L4, detected: L6)

**RECLASSIFY_ONLY** (16 files, LOW effort)

- `bridges.py` (declared: L4, detected: L6)
- `prevention_contract.py` (declared: L4, detected: L6)
- `dispatcher.py` (declared: L5, detected: L6)
- `learning_proof.py` (declared: L4, detected: L6)
- `events.py` (declared: L4, detected: L6)
- ... and 11 more

**EXTRACT_DRIVER** (20 files, MEDIUM effort)

- `cost_snapshots.py` (declared: L4, detected: L6)
- `customer_incidents_adapter.py` (declared: L3, detected: L6)
- `vector_stores_base.py` (declared: L3, detected: L6)
- `customer_killswitch_adapter.py` (declared: L3, detected: L6)
- `notifications_base.py` (declared: L3, detected: L6)
- ... and 15 more

**EXTRACT_AUTHORITY** (1 files, HIGH effort)

- `webhook_adapter.py` (declared: L3, detected: L6)

**SPLIT_FILE** (6 files, HIGH effort)

- `cost_bridges.py` (declared: L4, detected: L6)
- `founder_ops_adapter.py` (declared: L3, detected: L2)
- `serverless_base.py` (declared: L3, detected: L6)
- `customer_activity_adapter.py` (declared: L3, detected: L6)
- `customer_logs_adapter.py` (declared: L3, detected: L2)
- ... and 1 more

---

### LOGS

**Files:** 52

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 3 | 40 | 0 | 9 | 0 |
| Declared | 4 | 4 | 36 | 0 | 8 | 0 |
| Dominant | 3 | 1 | 2 | 0 | 40 | 6 |

**Work Backlog:** 41 items

**HEADER_FIX_ONLY** (3 files, LOW effort)

- `trace_facade.py` (declared: L4, detected: L3)
- `evidence_facade.py` (declared: L4, detected: L6)
- `evidence_report.py` (declared: L3, detected: L4)

**RECLASSIFY_ONLY** (12 files, LOW effort)

- `idempotency.py` (declared: L6, detected: L2)
- `job_execution.py` (declared: L4, detected: L6)
- `pdf_renderer.py` (declared: L3, detected: L6)
- `audit_models.py` (declared: L4, detected: L6)
- `panel_consistency_checker.py` (declared: L2, detected: L6)
- ... and 7 more

**EXTRACT_DRIVER** (23 files, MEDIUM effort)

- `logs_facade.py` (declared: L4, detected: L6)
- `cost_anomaly_detector.py` (declared: L4, detected: L6)
- `export_bundle_service.py` (declared: L3, detected: L6)
- `monitors_facade.py` (declared: L4, detected: L6)
- `notifications_facade.py` (declared: L4, detected: L6)
- ... and 18 more

**SPLIT_FILE** (3 files, HIGH effort)

- `certificate.py` (declared: L3, detected: L6)
- `replay_determinism.py` (declared: L4, detected: L2)
- `detection_facade.py` (declared: L4, detected: L6)

---

### OPS

**Files:** 1

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 0 | 0 | 0 | 1 | 0 |
| Declared | 0 | 0 | 1 | 0 | 0 | 0 |
| Dominant | 0 | 0 | 0 | 0 | 1 | 0 |

**Work Backlog:** 1 items

**HEADER_FIX_ONLY** (1 files, LOW effort)

- `ops.py` (declared: L4, detected: L6)

---

### OVERVIEW

**Files:** 1

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 1 | 0 | 0 | 0 | 0 |
| Declared | 0 | 0 | 1 | 0 | 0 | 0 |
| Dominant | 0 | 0 | 0 | 0 | 1 | 0 |

**Work Backlog:** 1 items

**EXTRACT_DRIVER** (1 files, MEDIUM effort)

- `overview_facade.py` (declared: L4, detected: L6)

---

### PLATFORM

**Files:** 7

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 1 | 5 | 0 | 1 | 0 |
| Declared | 0 | 1 | 5 | 0 | 1 | 0 |
| Dominant | 1 | 0 | 0 | 0 | 6 | 0 |

**Work Backlog:** 6 items

**RECLASSIFY_ONLY** (3 files, LOW effort)

- `sandbox_executor.py` (declared: L4, detected: L6)
- `job_scheduler.py` (declared: L4, detected: L6)
- `executor.py` (declared: L4, detected: L6)

**EXTRACT_DRIVER** (1 files, MEDIUM effort)

- `platform_health_service.py` (declared: L4, detected: L6)

**EXTRACT_AUTHORITY** (1 files, HIGH effort)

- `pool_manager.py` (declared: L4, detected: L6)

**SPLIT_FILE** (1 files, HIGH effort)

- `platform_eligibility_adapter.py` (declared: L3, detected: L2)

---

### POLICIES

**Files:** 102

| Metric | L2 | L3 | L4 | L5 | L6 | ? |
|--------|-----|-----|-----|-----|-----|---|
| Folder | 0 | 5 | 88 | 0 | 9 | 0 |
| Declared | 0 | 3 | 88 | 2 | 7 | 1 |
| Dominant | 6 | 1 | 5 | 0 | 84 | 6 |

**Work Backlog:** 82 items

**HEADER_FIX_ONLY** (3 files, LOW effort)

- `policy_driver.py` (declared: L4, detected: L2)
- `run_governance_facade.py` (declared: L4, detected: L3)
- `governance_facade.py` (declared: L4, detected: L6)

**RECLASSIFY_ONLY** (42 files, LOW effort)

- `logs_read_service.py` (declared: L4, detected: None)
- `recovery_write_service.py` (declared: L4, detected: L6)
- `ir_compiler.py` (declared: L4, detected: L6)
- `governance_signal_service.py` (declared: L6, detected: L6)
- `alert_emitter.py` (declared: L3, detected: L6)
- ... and 37 more

**EXTRACT_DRIVER** (34 files, MEDIUM effort)

- `policies_facade.py` (declared: L4, detected: L6)
- `limits_facade.py` (declared: L4, detected: L6)
- `controls_facade.py` (declared: L4, detected: L6)
- `policy_violation_service.py` (declared: L4, detected: L6)
- `prevention_engine.py` (declared: L4, detected: L6)
- ... and 29 more

**SPLIT_FILE** (3 files, HIGH effort)

- `certificate.py` (declared: L3, detected: L6)
- `policy_models.py` (declared: L4, detected: L6)
- `decisions.py` (declared: L4, detected: L6)

---

## Other Audiences Summary

| Audience | Domains | Files | Work Items |
|----------|---------|-------|------------|
| **API** | 4 | 84 | 62 |
| **FOUNDER** | 4 | 14 | 13 |
| **INTERNAL** | 12 | 243 | 176 |

---

## Recommended Execution Plan

1. **Phase 1: Quick Wins (LOW effort)**
   - HEADER_FIX_ONLY: Update file headers to match behavior
   - RECLASSIFY_ONLY: Move files to correct folders
   - Start with domains: policies, logs, general (high volume, low complexity)

2. **Phase 2: Driver Extraction (MEDIUM effort)**
   - EXTRACT_DRIVER: Extract DB operations to L6 drivers
   - Prioritize: policies (34), logs (23), integrations (20)
   - Use driver extraction templates

3. **Phase 3: Complex Work (HIGH effort)**
   - EXTRACT_AUTHORITY: Architectural review required
   - SPLIT_FILE: Careful refactoring needed
   - Focus domains: integrations (7 HIGH), incidents (2 HIGH)
