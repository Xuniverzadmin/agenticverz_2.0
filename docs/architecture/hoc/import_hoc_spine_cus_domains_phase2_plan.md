# Phase 2 Plan — hoc_spine Imports in CUS L5 Engines

**Date:** 2026-02-06  
**Scope:** `backend/app/hoc/cus/**/L5_engines/*.py`  
**Goal:** Audit and align CUS L5 engine dependencies on hoc_spine authority, execution, orchestration, consequences, and governance.

---

## Reality (Evidence Summary)

**CUS domains (canonical 10):** overview, activity, incidents, policies, controls, logs, analytics, integrations, api_keys, account  
**Files scanned:** L5_engines, L5_schemas, L6_drivers under cus domains  
**Total hoc_spine import lines:** 47  
**Domains with hoc_spine imports:** 9  
**Gap:** api_keys has zero hoc_spine imports — this is a **design/development gap**, not an exemption.

### Domains and Import Lines (L5/L6/L5_schemas)

**account**
- `account/L5_engines/tenant_engine.py:50` — `hoc_spine.services.time.utcnow`
 - `account/L6_drivers/tenant_driver.py:15` — `hoc_spine.services.time.utcnow`
 - `account/L6_drivers/tenant_driver.py:16` — `hoc_spine.drivers.cross_domain.generate_uuid`

**activity**
- `activity/L5_engines/pattern_detection_engine.py:26` — `hoc_spine.services.time.utcnow`
- `activity/L5_engines/attention_ranking_engine.py:26` — `hoc_spine.services.time.utcnow`
- `activity/L5_engines/signal_feedback_engine.py:26` — `hoc_spine.services.time.utcnow`
- `activity/L5_engines/cost_analysis_engine.py:26` — `hoc_spine.services.time.utcnow`
- `activity/L5_engines/__init__.py:33` — `hoc_spine.orchestrator.run_governance_facade`
 - `activity/L6_drivers/orphan_recovery_driver.py:27` — `hoc_spine.services.time.utcnow`

**analytics**
- `analytics/L5_engines/pattern_detection_engine.py:55` — `hoc_spine.services.time.utcnow`
- `analytics/L5_engines/prediction_engine.py:66` — `hoc_spine.services.time.utcnow`
- `analytics/L5_engines/metrics_engine.py:34` — `hoc_spine.services.costsim_metrics`
- `analytics/L5_engines/config_engine.py:34` — `hoc_spine.services.costsim_config`
 - `analytics/L6_drivers/analytics_snapshot_driver.py:31` — `hoc_spine.services.time.utcnow`
 - `analytics/L6_drivers/analytics_snapshot_driver.py:32` — `hoc_spine.schemas.rac_models`

**incidents**
- `incidents/L5_engines/incident_engine.py:75` — `hoc_spine.services.time.utcnow`
- `incidents/L5_engines/recurrence_analysis_engine.py:45` — `hoc_spine.services.time.utcnow`
- `incidents/L5_engines/incident_pattern_engine.py:65` — `hoc_spine.services.time.utcnow`
- `incidents/L5_engines/anomaly_bridge.py:64` — `hoc_spine.schemas.anomaly_types`
 - `incidents/L6_drivers/incident_ledger_driver.py:27` — `hoc_spine.services.time.utcnow`

**integrations**
- `integrations/L5_engines/cus_health_engine.py:64` — `hoc_spine.services.cus_credential_engine`
- `integrations/L5_engines/mcp_tool_invocation_engine.py:63` — `hoc_spine.schemas.protocols`
- `integrations/L5_engines/cost_bridges_engine.py:50` — `hoc_spine.orchestrator.create_incident_from_cost_anomaly_sync`

**logs**
- `logs/L5_engines/mapper.py:34` — `hoc_spine.services.time.utcnow`
- `logs/L5_engines/mapper.py:35` — `hoc_spine.services.control_registry`
- `logs/L5_engines/audit_reconciler.py:50` — `hoc_spine.schemas.rac_models`
- `logs/L5_engines/audit_reconciler.py:58` — `hoc_spine.services.audit_store`

**overview**
- `overview/L5_engines/overview_facade.py:68` — `hoc_spine.services.time.utcnow`
 - `overview/L6_drivers/overview_read_driver.py:27` — `hoc_spine.services.time.utcnow`

**policies**
- `policies/L5_engines/eligibility_engine.py:75` — `hoc_spine.orchestrator.*`
- `policies/L5_engines/policy_limits_engine.py:56` — `hoc_spine.services.time.utcnow`
- `policies/L5_engines/policy_limits_engine.py:57` — `hoc_spine.drivers.cross_domain.generate_uuid`
- `policies/L5_engines/policy_rules_engine.py:57` — `hoc_spine.services.time.utcnow`
- `policies/L5_engines/policy_rules_engine.py:58` — `hoc_spine.drivers.cross_domain.generate_uuid`
- `policies/L5_engines/lessons_engine.py:63` — `hoc_spine.services.time.utcnow`
- `policies/L5_engines/recovery_evaluation_engine.py:57` — `hoc_spine.utilities.recovery_decisions`
- `policies/L5_engines/policy_proposal_engine.py:40` — `hoc_spine.services.time.utcnow`
 - `policies/L6_drivers/ledger_driver.py:45` — `hoc_spine.services.time.utcnow`
 - `policies/L6_drivers/policy_driver.py:36` — `hoc_spine.services.time.utcnow`
 - `policies/L6_drivers/policy_limits_driver.py:40` — `hoc_spine.services.time.utcnow`

---

## Phase 2 Plan

### Step 1 — Classify Each hoc_spine Import (Matrix-Driven)

Classify each import line into one of:
- **Authority/Orchestration:** `hoc_spine.orchestrator.*`
- **Governance/Consequences:** `hoc_spine.services.audit_store`, `hoc_spine.services.control_registry`
- **Shared Services:** `hoc_spine.services.time`, `hoc_spine.services.costsim_*`, `hoc_spine.services.cus_credential_engine`
- **Schemas/Protocols:** `hoc_spine.schemas.*`
- **Utilities:** `hoc_spine.utilities.*`
- **Drivers (cross-domain):** `hoc_spine.drivers.*`

Output: a table mapping import → category → justification (see `HOC_SPINE_IMPORT_MATRIX_CUS.md`).

### Step 2 — Validate Layer Compliance

For each import category:
- Confirm it is allowed for L5 engines under HOC topology rules.
- Flag any L5 engine importing **orchestrator** or **authority** directly (candidate violation or exception).

Output: compliance verdict per file (OK / REVIEW / VIOLATION).

### Step 2B — Skeptic Audit (Import Search)

Run a second-pass scan for any hoc_spine imports that do **not** use the
`app.hoc.cus.hoc_spine` prefix (relative or aliased imports). If found, add
them to the matrix as `uncategorized` and flag for review.

### Step 3 — Identify Required Refactors (If Any)

If any imports are **orchestrator authority** or **execution** calls:
- Move the access to L4 (hoc_spine) and expose via a bridge or registry operation.
- Replace direct calls in L5 with a capability passed from L4.

Output: refactor list (file, import, proposed L4 replacement).

### Step 4 — Update Canonical Literature

For each affected domain:
- Update domain canonical literature to reflect the allowed hoc_spine dependencies.
- Document any new bridges or L4 operations created during refactor.

### Step 5 — Evidence Report

Produce: `docs/architecture/hoc/PHASE2_HOC_SPINE_IMPORT_AUDIT.md`
- Summary stats
- Per‑domain tables
- Compliance verdicts
- Refactor actions (if any)

---

## Acceptance Criteria

1. Every hoc_spine import in L5 engines is classified and justified.
2. Any L5 engine importing `hoc_spine.orchestrator` is either explicitly approved or refactored to L4.
3. Evidence report exists with per‑domain compliance status.
