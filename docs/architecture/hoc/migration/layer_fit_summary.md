# HOC Layer Fit Analysis Report

**Generated:** 2026-01-23
**Files Analyzed:** 717

---

## 1. Executive Summary

| Status | Count | % |
|--------|-------|---|
| **LAYER_FIT** | 346 | 48.3% |
| **MISFIT** | 371 | 51.7% |

## 2. Violation Breakdown

| Violation | Count | Severity |
|-----------|-------|----------|
| DRIFT | 217 | HIGH |
| DATA_LEAK | 206 | HIGH |
| LAYER_JUMP | 93 | HIGH |
| TEMPORAL_LEAK | 18 | MEDIUM |
| AUTHORITY_LEAK_HTTP | 9 | HIGH |

## 3. Layer Distribution (by dominant signals)

| Layer | Name | Files |
|-------|------|-------|
| L2 | APIs | 130 |
| L3 | Adapters | 11 |
| L4 | Engines | 22 |
| L5 | Workers | 0 |
| L6 | Drivers/Schemas | 482 |

## 4. Signal Distribution (from Pass 1)

| Signal Type | Count |
|-------------|-------|
| L6_DRIVER | 1242 |
| L2_API | 814 |
| L6_SCHEMA | 784 |
| L4_ENGINE | 104 |
| L4_ENGINE_GOOD | 77 |
| L3_ADAPTER | 75 |
| L5_WORKER | 48 |
| TEMPORAL_LEAK | 34 |
| RETRY_PATTERN | 2 |

## 5. Misfit Files (Requiring Remediation)

### DATA_LEAK (75 files)

- `app/houseofcards/founder/ops/engines/founder_review.py`
  - Declared: L2, Dominant: L2
  - Issue: L2 file has 1 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/infrastructure/tenant.py`
  - Declared: L2, Dominant: L2
  - Issue: L2 file has 1 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/founder/ops/founder_actions.py`
  - Declared: ?, Dominant: L2
  - Issue: L2 file has 5 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/founder/agent/founder_contract_review.py`
  - Declared: L2, Dominant: L2
  - Issue: L2 file has 1 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/founder/account/founder_explorer.py`
  - Declared: L2, Dominant: L2
  - Issue: L2 file has 4 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/founder/logs/founder_timeline.py`
  - Declared: ?, Dominant: L2
  - Issue: L2 file has 1 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/customer/ops/cost_ops.py`
  - Declared: ?, Dominant: L6
  - Issue: L2 file has 7 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/customer/recovery/recovery.py`
  - Declared: L2, Dominant: L2
  - Issue: L2 file has 5 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/customer/recovery/recovery_ingest.py`
  - Declared: ?, Dominant: L2
  - Issue: L2 file has 2 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- `app/houseofcards/api/customer/policies/policy_rules_crud.py`
  - Declared: L2, Dominant: L2
  - Issue: L2 file has 2 L6_DRIVER signals (DB access)
  - Remediation: Extract DB operations to a L6 Driver service
- ... and 65 more

### DRIFT (217 files)

- `app/houseofcards/founder/ops/drivers/ops_write_service.py`
  - Declared: L4, Dominant: L6
  - Issue: Declared L4 but dominant signals are L6 (5 vs 0 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/founder/ops/engines/founder_action_write_service.py`
  - Declared: L4, Dominant: L6
  - Issue: Declared L4 but dominant signals are L6 (8 vs 1 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/founder/ops/engines/ops_incident_service.py`
  - Declared: L4, Dominant: L6
  - Issue: Declared L4 but dominant signals are L6 (6 vs 1 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/founder/agent/drivers/founder_action_write_service.py`
  - Declared: L4, Dominant: L6
  - Issue: Declared L4 but dominant signals are L6 (8 vs 0 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/founder/agent/drivers/ops_write_service.py`
  - Declared: L4, Dominant: L6
  - Issue: Declared L4 but dominant signals are L6 (5 vs 0 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/founder/incidents/engines/ops_incident_service.py`
  - Declared: L4, Dominant: L6
  - Issue: Declared L4 but dominant signals are L6 (6 vs 1 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/api/founder/logs/founder_review.py`
  - Declared: L2, Dominant: L6
  - Issue: Declared L2 but dominant signals are L6 (6 vs 5 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/api/founder/incidents/ops.py`
  - Declared: L2, Dominant: L6
  - Issue: Declared L2 but dominant signals are L6 (11 vs 6 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/api/customer/policies/guard.py`
  - Declared: L2, Dominant: L6
  - Issue: Declared L2 but dominant signals are L6 (10 vs 8 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- `app/houseofcards/api/customer/policies/policy.py`
  - Declared: L2, Dominant: L6
  - Issue: Declared L2 but dominant signals are L6 (14 vs 8 signals)
  - Remediation: Update header to declare L6 OR refactor to match declared layer
- ... and 207 more

### LAYER_JUMP (53 files)

- `app/houseofcards/customer/policies/drivers/logs_read_service.py`
  - Declared: L4, Dominant: ?
  - Issue: Folder suggests L6 but declares L4
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/policies/drivers/policy_driver.py`
  - Declared: L2, Dominant: L2
  - Issue: Folder suggests L6 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/policies/facades/governance_facade.py`
  - Declared: L6, Dominant: L6
  - Issue: Folder suggests L3 but declares L6
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/semantic_validator.py`
  - Declared: L2, Dominant: ?
  - Issue: Folder suggests L4 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/intent_guardrails.py`
  - Declared: L2, Dominant: ?
  - Issue: Folder suggests L4 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/panel_spec_loader.py`
  - Declared: L2, Dominant: ?
  - Issue: Folder suggests L4 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/panel_metrics_emitter.py`
  - Declared: L2, Dominant: ?
  - Issue: Folder suggests L4 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/validator_engine.py`
  - Declared: L2, Dominant: ?
  - Issue: Folder suggests L4 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/panel_signal_collector.py`
  - Declared: L6, Dominant: L6
  - Issue: Folder suggests L4 but declares L6
  - Remediation: Move file to correct folder matching declared layer
- `app/houseofcards/customer/agent/engines/panel_dependency_resolver.py`
  - Declared: L2, Dominant: ?
  - Issue: Folder suggests L4 but declares L2
  - Remediation: Move file to correct folder matching declared layer
- ... and 43 more

### SIGNAL_MISMATCH (25 files)

- `app/houseofcards/founder/ops/facades/founder_review_adapter.py`
  - Declared: L3, Dominant: L2
  - Remediation: Review signals - dominant is L2, verify layer assignment
- `app/houseofcards/customer/platform/facades/platform_eligibility_adapter.py`
  - Declared: L3, Dominant: L2
  - Remediation: Review signals - dominant is L2, verify layer assignment
- `app/houseofcards/customer/policies/schemas/policy_rules.py`
  - Declared: L6, Dominant: L2
  - Remediation: Review signals - dominant is L2, verify layer assignment
- `app/houseofcards/customer/analytics/facades/v2_adapter.py`
  - Declared: L3, Dominant: L6
  - Remediation: Review signals - dominant is L6, verify layer assignment
- `app/houseofcards/customer/analytics/engines/config.py`
  - Declared: ?, Dominant: L6
  - Remediation: Review signals - dominant is L6, verify layer assignment
- `app/houseofcards/customer/analytics/engines/divergence.py`
  - Declared: ?, Dominant: L6
  - Remediation: Review signals - dominant is L6, verify layer assignment
- `app/houseofcards/customer/analytics/engines/datasets.py`
  - Declared: ?, Dominant: L6
  - Remediation: Review signals - dominant is L6, verify layer assignment
- `app/houseofcards/customer/analytics/engines/provenance.py`
  - Declared: ?, Dominant: L6
  - Remediation: Review signals - dominant is L6, verify layer assignment
- `app/houseofcards/customer/integrations/facades/founder_ops_adapter.py`
  - Declared: L3, Dominant: L2
  - Remediation: Review signals - dominant is L2, verify layer assignment
- `app/houseofcards/customer/integrations/facades/customer_policies_adapter.py`
  - Declared: L3, Dominant: L6
  - Remediation: Review signals - dominant is L6, verify layer assignment
- ... and 15 more

### TEMPORAL_LEAK (1 files)

- `app/houseofcards/internal/agent/engines/retry_policy.py`
  - Declared: ?, Dominant: L6
  - Issue: Temporal pattern (sleep/retry) in L4
  - Remediation: Move temporal logic (sleep, retry) to L5 Worker or runtime infrastructure

## 6. Layer Fit Confidence

| Confidence | Count |
|------------|-------|
| HIGH | 271 |
| MEDIUM | 27 |
| LOW | 48 |

---

## 7. WORK BACKLOG (By Refactor Action)

> **This is the actionable migration plan.**
> Execute in this order for minimal risk and maximum efficiency.

| # | Action | Files | Effort | Description |
|---|--------|-------|--------|-------------|
| 1 | **RECLASSIFY_ONLY** | 89 | LOW | Move file to correct folder, update header |
| 2 | **EXTRACT_DRIVER** | 232 | MEDIUM | Extract DB operations to new L6 Driver service |
| 3 | **EXTRACT_AUTHORITY** | 13 | HIGH | Move HTTP/decisions to appropriate layer |
| 4 | **SPLIT_FILE** | 20 | HIGH | Split file into multiple single-responsibility files |
| 5 | **NO_ACTION** | 363 | NONE | File is correctly placed and classified |

### Effort Summary

| Effort Level | Files |
|--------------|-------|
| LOW (quick wins) | 89 |
| MEDIUM (standard) | 240 |
| HIGH (complex) | 25 |
| **Total Work Items** | **354** |

### Sample Files by Action

#### RECLASSIFY_ONLY (89 files)

- `app/houseofcards/founder/ops/drivers/ops_write_service.py` (declared: L4, detected: L6)
- `app/houseofcards/founder/agent/drivers/founder_action_write_service.py` (declared: L4, detected: L6)
- `app/houseofcards/founder/agent/drivers/ops_write_service.py` (declared: L4, detected: L6)
- `app/houseofcards/customer/policies/drivers/logs_read_service.py` (declared: L4, detected: ?)
- `app/houseofcards/customer/policies/drivers/recovery_write_service.py` (declared: L4, detected: L6)
- ... and 84 more

#### EXTRACT_DRIVER (232 files)

- `app/houseofcards/founder/ops/engines/founder_action_write_service.py` (declared: L4, detected: L6)
- `app/houseofcards/founder/ops/engines/founder_review.py` (declared: L2, detected: L2)
- `app/houseofcards/founder/ops/engines/ops_incident_service.py` (declared: L4, detected: L6)
- `app/houseofcards/founder/incidents/engines/ops_incident_service.py` (declared: L4, detected: L6)
- `app/houseofcards/api/infrastructure/tenant.py` (declared: L2, detected: L2)
- ... and 227 more

#### EXTRACT_AUTHORITY (13 files)

- `app/houseofcards/customer/platform/engines/pool_manager.py` (declared: L4, detected: L6)
- `app/houseofcards/customer/general/lifecycle/engines/pool_manager.py` (declared: L4, detected: L6)
- `app/houseofcards/customer/integrations/facades/webhook_adapter.py` (declared: L3, detected: L6)
- `app/houseofcards/internal/platform/engines/engine.py` (declared: L4, detected: L6)
- `app/houseofcards/internal/policies/engines/rbac.py` (declared: L4, detected: L2)
- ... and 8 more

#### SPLIT_FILE (20 files)

- `app/houseofcards/founder/ops/facades/founder_review_adapter.py` (declared: L3, detected: L2)
- `app/houseofcards/customer/platform/facades/platform_eligibility_adapter.py` (declared: L3, detected: L2)
- `app/houseofcards/customer/policies/engines/certificate.py` (declared: L3, detected: L6)
- `app/houseofcards/customer/policies/engines/policy_models.py` (declared: L4, detected: L6)
- `app/houseofcards/customer/policies/engines/decisions.py` (declared: L4, detected: L6)
- ... and 15 more

---

## 8. Recommended Migration Order

1. **HEADER_FIX_ONLY** - Fast wins, improves signal accuracy
2. **RECLASSIFY_ONLY** - Folder hygiene, zero logic risk
3. **QUARANTINE_DUPLICATE** - Reduces noise, prevents double work
4. **EXTRACT_DRIVER** - Biggest category, needs conventions first
5. **EXTRACT_AUTHORITY** - High risk, requires L4 runtime stability
6. **SPLIT_FILE** - Last, architectural surgery
