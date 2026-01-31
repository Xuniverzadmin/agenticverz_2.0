# HOC Documentation Index

**Version:** 1.0.0
**Created:** 2026-01-24
**Status:** ACTIVE
**Purpose:** Master index for all House of Cards (HOC) migration and architecture documentation

---

## Quick Navigation

| Category | Document | Status |
|----------|----------|--------|
| **Canonical Architecture** | [HOC_LAYER_TOPOLOGY_V1.md](../HOC_LAYER_TOPOLOGY_V1.md) | RATIFIED |
| **Master Migration Plan** | [HOC_MIGRATION_PLAN.md](../HOC_MIGRATION_PLAN.md) | v1.1.0 DRAFT |
| **Phase 1 Plan** | [migration/PHASE1_MIGRATION_PLAN.md](migration/PHASE1_MIGRATION_PLAN.md) | COMPLETE |
| **Phase 2 Plan** | [migration/PHASE2_MIGRATION_PLAN.md](migration/PHASE2_MIGRATION_PLAN.md) | IN PROGRESS |

---

## 1. Canonical Reference Documents

These are the authoritative documents for HOC architecture.

| Document | Location | Version | Status | Description |
|----------|----------|---------|--------|-------------|
| **Layer Topology** | [`../HOC_LAYER_TOPOLOGY_V1.md`](../HOC_LAYER_TOPOLOGY_V1.md) | 1.2.0 | RATIFIED | L1-L8 layer model, naming rules, import contracts |
| **Master Migration Plan** | [`../HOC_MIGRATION_PLAN.md`](../HOC_MIGRATION_PLAN.md) | 1.1.0 | DRAFT | 5-phase migration overview (P1-P5) |
| **Driver-Engine Contract** | [`../../../backend/app/hoc/DRIVER_ENGINE_CONTRACT.md`](../../../backend/app/hoc/DRIVER_ENGINE_CONTRACT.md) | — | ACTIVE | L5/L6 boundary rules |

---

## 2. Migration Phase Documents

### Phase 1: Inventory & Classification (COMPLETE)

| Document | Location | Status | Description |
|----------|----------|--------|-------------|
| Phase 1 Plan | [`migration/PHASE1_MIGRATION_PLAN.md`](migration/PHASE1_MIGRATION_PLAN.md) | COMPLETE | File inventory and classification |
| Phase 1 Completion | [`migration/PHASE1_COMPLETION_REPORT.md`](migration/PHASE1_COMPLETION_REPORT.md) | COMPLETE | Final status report |
| Iteration 1 Audit | [`migration/ITERATION1_AUDIT_REPORT.md`](migration/ITERATION1_AUDIT_REPORT.md) | COMPLETE | 958/1009 files classified |
| Iteration 2 Audit | [`migration/ITERATION2_AUDIT_REPORT.md`](migration/ITERATION2_AUDIT_REPORT.md) | COMPLETE | L5/L6 ambiguity resolved |

**Inventory Files:**
- `migration/MIGRATION_INVENTORY.csv` — Initial inventory (1,009 files)
- `migration/MIGRATION_INVENTORY_ITER1.csv` — After iteration 1
- `migration/MIGRATION_INVENTORY_ITER2.csv` — After iteration 2
- `migration/MIGRATION_INVENTORY_ITER3.csv` — Final validated inventory
- `migration/MIGRATION_INVENTORY_PHASE2.csv` — Phase 2 execution inventory

### Phase 2: Migration Execution (IN PROGRESS)

| Document | Location | Status | Description |
|----------|----------|--------|-------------|
| Phase 2 Plan | [`migration/PHASE2_MIGRATION_PLAN.md`](migration/PHASE2_MIGRATION_PLAN.md) | IN PROGRESS | Physical file migration |
| Step 0 Audit | [`migration/PHASE2_STEP0_AUDIT.md`](migration/PHASE2_STEP0_AUDIT.md) | COMPLETE | Pre-migration duplicate check |
| Step 3 Layer Criteria | [`migration/PHASE2_STEP3_LAYER_CRITERIA.md`](migration/PHASE2_STEP3_LAYER_CRITERIA.md) | COMPLETE | Layer assignment rules |
| Extraction Playbook | [`migration/PHASE2_EXTRACTION_PLAYBOOK.md`](migration/PHASE2_EXTRACTION_PLAYBOOK.md) | ACTIVE | L4/L6 extraction procedures |
| Extraction Protocol | [`migration/PHASE2_EXTRACTION_PROTOCOL.md`](migration/PHASE2_EXTRACTION_PROTOCOL.md) | ACTIVE | Step-by-step extraction guide |

**Layer Fit Analysis:**
- `migration/layer_fit_summary.md` — Summary of layer assignments
- `migration/layer_fit_detailed_report.md` — Detailed layer analysis
- `migration/layer_fit_customer_domains.md` — Customer domain specifics
- `migration/layer_fit_report.json` — Machine-readable analysis

**Supporting Files:**
- `migration/phase2_backlog.yaml` — Execution backlog
- `migration/ALLOWED_VIOLATIONS.yaml` — Tolerated violations
- `migration/driver_templates/` — Driver code templates

### Phase 2.5A: Structural Layering (ACTIVE)

This sub-phase focuses on L4/L6 separation within already-migrated domains.

| Domain | Status | Lock Document |
|--------|--------|---------------|
| **analytics** | LOCKED | [`backend/.../analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md) |
| **policies** | LOCKED | [`backend/.../policies/POLICIES_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/policies/POLICIES_DOMAIN_LOCK_FINAL.md) |
| **activity** | LOCKED | [`backend/.../activity/ACTIVITY_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/activity/ACTIVITY_DOMAIN_LOCK_FINAL.md) |
| **logs** | LOCKED | [`backend/.../logs/LOGS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/logs/LOGS_DOMAIN_LOCK_FINAL.md) |
| **incidents** | LOCKED | [`backend/.../incidents/INCIDENTS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/incidents/INCIDENTS_DOMAIN_LOCK_FINAL.md) |
| **overview** | LOCKED | [`backend/.../overview/OVERVIEW_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/overview/OVERVIEW_DOMAIN_LOCK_FINAL.md) |
| **api_keys** | LOCKED | [`implementation/API_KEYS_DOMAIN_LOCK_FINAL.md`](implementation/API_KEYS_DOMAIN_LOCK_FINAL.md) |
| **account** | LOCKED | [`implementation/ACCOUNT_DOMAIN_LOCK_FINAL.md`](implementation/ACCOUNT_DOMAIN_LOCK_FINAL.md) |
| **integrations** | LOCKED (debt) | [`implementation/INTEGRATIONS_DOMAIN_LOCK_FINAL.md`](implementation/INTEGRATIONS_DOMAIN_LOCK_FINAL.md) |
| general | LOCKED | [`backend/.../general/GENERAL_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/general/GENERAL_DOMAIN_LOCK_FINAL.md) |

### Phase 3: Directory Restructure (COMPLETE)

| Document | Location | Status | Description |
|----------|----------|--------|-------------|
| Phase 3 Plan | [`migration/PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md`](migration/PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md) | **COMPLETE** | Layer-prefixed directory restructure + package rename |

**Completion Summary (2026-01-24):**
- **10 customer domains migrated:** overview, api_keys, account, activity, incidents, policies, logs, analytics, integrations, **general**
- **Package & audience rename applied:** `houseofcards` → `hoc`, `customer` → `cus`, `founder` → `fdr`, `internal` → `int`
- **Layer-prefixed folders deployed:** `L3_adapters/`, `L5_engines/`, `L5_schemas/`, `L6_drivers/`
- **L4 centralized:** Only in `general/L4_runtime/` (as per HOC Layer Topology)
- **Facades merged:** All domain `facades/` folders eliminated; files moved to `L5_engines/` or `L3_adapters/`
- **Headers fixed:** All L4 headers in L5_engines converted to L5

**General Domain Structure (L4 is here only):**
```
hoc/cus/general/
├── L3_mcp/           # MCP adapters
├── L4_runtime/       # Runtime control plane (ONLY L4 location)
├── L5_controls/      # Control engines
├── L5_engines/       # Business logic
├── L5_lifecycle/     # Lifecycle management
├── L5_schemas/       # Domain schemas
├── L5_ui/            # UI utilities
├── L5_utils/         # Shared utilities
├── L5_workflow/      # Workflow engines
└── L6_drivers/       # Database drivers
```

**All paths now use new structure:** `backend/app/hoc/cus/{domain}/L{n}_{folder}/`

### Phase 3B: SQLAlchemy Extraction (COMPLETE)

Phase 3B focuses on extracting SQLAlchemy imports from L5 engines to L6 drivers.

| Document | Location | Status | Description |
|----------|----------|--------|-------------|
| P3 Completion Report | [`PHASE3B_P3_COMPLETION_REPORT.md`](PHASE3B_P3_COMPLETION_REPORT.md) | **COMPLETE** | P3 design-first extractions |
| Scanner | [`scripts/ops/phase_3b_scanner.py`](../../../scripts/ops/phase_3b_scanner.py) | ACTIVE | SQLAlchemy violation scanner |

**Phase 3B Status Summary:**

| Priority | Files | Status |
|----------|-------|--------|
| P1-P2 (mechanical) | 6 files | COMPLETE |
| P3 (design-first) | 2 files | COMPLETE |
| FROZEN (M25 debt) | 3 files | Deferred |

**P3 Extractions Completed (2026-01-25):**

1. **policy_proposal.py** → Reclassified L3→L5, split into:
   - `policy_proposal_engine.py` (L5)
   - `policy_proposal_read_driver.py` (L6)
   - `policy_proposal_write_driver.py` (L6)

2. **policies_facade.py** → Split into 3 query engines:
   - `policies_rules_query_engine.py` + `policy_rules_read_driver.py`
   - `policies_limits_query_engine.py` + `limits_read_driver.py`
   - `policies_proposals_query_engine.py` + `proposals_read_driver.py`

**Scanner Results:**
```
BLOCKING violations: 0
DEFERRED (P3): 0
FROZEN (M25): 3
```

### Phase 4: Wiring (IN PROGRESS)

Phase 4 focuses on wiring general domain services to other customer domains.

| Document | Location | Status | Description |
|----------|----------|--------|-------------|
| **L2→L4→L5 Construction Plan** | [`L2-L4-L5_CONSTRUCTION_PLAN.md`](L2-L4-L5_CONSTRUCTION_PLAN.md) | **PROPOSED** | 3-phase plan: 32 loop constructions (A), 153 orphan classifications (B), CI freeze (C) |

| Document | Location | Status | Description |
|----------|----------|--------|-------------|
| General Domain Wiring Phase 1 | [`GENERAL_DOMAIN_WIRING_PHASE1.md`](GENERAL_DOMAIN_WIRING_PHASE1.md) | **RESEARCH COMPLETE** | Analysis of general→domain wiring gaps |
| General Domain Wiring Phase 2 | [`GENERAL_DOMAIN_WIRING_PHASE2.md`](GENERAL_DOMAIN_WIRING_PHASE2.md) | **RESEARCH COMPLETE** | Comprehensive function catalog of general domain |
| Authority Violation Spec v1 | [`AUTHORITY_VIOLATION_SPEC_V1.md`](AUTHORITY_VIOLATION_SPEC_V1.md) | **DRAFT** | First-principles authority enforcement specification |
| Runtime Context Model v1 | [`RUNTIME_CONTEXT_MODEL.md`](RUNTIME_CONTEXT_MODEL.md) | **DRAFT** | How authority constraints enter the system via context objects |
| L4/L5 Contracts v1 | [`L4_L5_CONTRACTS_V1.md`](L4_L5_CONTRACTS_V1.md) | **DRAFT** | Protocol-based contracts enforced by type system |
| **Authority Analyzer** | [`scripts/ops/hoc_authority_analyzer.py`](../../../scripts/ops/hoc_authority_analyzer.py) | **ACTIVE** | Mechanical enforcer of authority contracts |
| Authority Violations Report | [`HOC_AUTHORITY_VIOLATIONS.yaml`](HOC_AUTHORITY_VIOLATIONS.yaml) | **GENERATED** | Automated violation scan output |
| **TRANSACTION_BYPASS Checklist** | [`TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md`](TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md) | **ACTIVE** | Step-by-step remediation for session.commit violations |
| **Remediation Report** | [`TRANSACTION_BYPASS_REMEDIATION_REPORT_2026-01-25.md`](TRANSACTION_BYPASS_REMEDIATION_REPORT_2026-01-25.md) | **IN PROGRESS** | Progress report: 2/5 P1 files, 6 commits removed, 131 CRITICAL remaining |
| **L5 Pairing Gap Detector** | [`scripts/ops/l5_spine_pairing_gap_detector.py`](../../../scripts/ops/l5_spine_pairing_gap_detector.py) | **ACTIVE** | AST-based scanner: L5 engines wired via L4 vs direct L2→L5 gaps |
| **Spine Literature Validator** | [`scripts/ops/hoc_spine_study_validator.py`](../../../scripts/ops/hoc_spine_study_validator.py) | **UPGRADED** | Now generates Export Contract, Import Boundary, L5 Pairing Declaration sections |
| **Spine Literature Index** | [`literature/INDEX.md`](../../../literature/INDEX.md) | **REGENERATED** | Master index with violation roll-up |

**L5 Pairing Gap Summary (PIN-491, 2026-01-30):**

| Metric | Initial | After A.1 |
|--------|---------|-----------|
| Total L5 engines | 185 | 185 |
| Wired via L4 orchestrator | 0 | **10** |
| Direct L2→L5 (gaps) | 32 | **22** |
| Orphaned (no callers) | 153 | 153 |

**Construction Plan Progress:**
- **A.0** ✅ `operation_registry.py` + `OperationHandler` protocol + 16 invariant tests
- **A.1** ✅ 10 facade-pattern operations wired (6 handler modules, 10 L2 files updated, 72 registry calls)
- **A.2** 🔧 Logs compound facades (6 operations)
- **A.3–A.5** ⬜ Controls, Activity, Policies (15 operations)

**Phase 4 Research Summary (2026-01-25):**

| Category | Files Affected | Status |
|----------|----------------|--------|
| DateTime standardization | 9 files | Identified |
| Governance orchestrator duplication | 2 files | CRITICAL - needs consolidation analysis |
| Transaction coordinator duplication | 2 files | CRITICAL - needs consolidation analysis |
| Missing orchestration wiring | 19 files | Identified |
| Multi-model writes without coordinator | 4 files | Identified |

**Phase 2 Function Catalog (2026-01-25):**

| Folder | Files | Classes | Functions | Wiring Candidates |
|--------|-------|---------|-----------|-------------------|
| L4_runtime | 6 | 12+ | 40+ | 19 files |
| L5_lifecycle | 6 | 15+ | 60+ | 8 files |
| L5_controls | 2 | 2 | 12 | 4 files |
| L5_workflow | 1 | 3 | 25+ | 3 files |
| L5_engines | 24 | 20+ | 100+ | 17 files |
| **TOTAL** | **39** | **52+** | **237+** | **51 files** |

**Key Findings:**
- `policies/L5_engines/governance_orchestrator.py` duplicates `general/L4_runtime/engines/governance_orchestrator.py`
- `policies/L6_drivers/transaction_coordinator.py` duplicates `general/L4_runtime/drivers/transaction_coordinator.py`
- L4_runtime services have **0 imports** from other domains (only `utc_now` utility is used)
- General domain provides 237+ functions across 39 files that other domains could leverage
- 51 files across 6 domains identified as wiring candidates

### Phase 5: Cleanup (PLANNED)

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 5: Cleanup | PLANNED | Delete `app/services/*` legacy code |

---

## 3. Domain Analysis Documents

Pre-migration analysis of each customer domain.

| Domain | Analysis Document | Status |
|--------|-------------------|--------|
| activity | [`analysis/HOC_activity_analysis_v1.md`](analysis/HOC_activity_analysis_v1.md) | COMPLETE |
| incidents | [`analysis/HOC_incidents_analysis_v1.md`](analysis/HOC_incidents_analysis_v1.md) | COMPLETE |
| policies | [`analysis/HOC_policies_analysis_v1.md`](analysis/HOC_policies_analysis_v1.md) | COMPLETE |
| logs | [`analysis/HOC_logs_analysis_v1.md`](analysis/HOC_logs_analysis_v1.md) | COMPLETE |
| analytics | [`analysis/HOC_analytics_analysis_v1.md`](analysis/HOC_analytics_analysis_v1.md) | COMPLETE |
| integrations | [`analysis/HOC_integrations_analysis_v1.md`](analysis/HOC_integrations_analysis_v1.md) | COMPLETE |
| api_keys | [`analysis/HOC_api_keys_analysis_v1.md`](analysis/HOC_api_keys_analysis_v1.md) | COMPLETE |
| account | [`analysis/HOC_account_analysis_v1.md`](analysis/HOC_account_analysis_v1.md) | COMPLETE |
| **account (Phase 2.5B)** | [`analysis/ACCOUNT_DOMAIN_ANALYSIS_REPORT.md`](analysis/ACCOUNT_DOMAIN_ANALYSIS_REPORT.md) | **ANALYSIS COMPLETE** |
| overview | [`analysis/HOC_overview_analysis_v1.md`](analysis/HOC_overview_analysis_v1.md) | COMPLETE |
| general | [`analysis/HOC_general_analysis_v1.md`](analysis/HOC_general_analysis_v1.md) | COMPLETE |
| (remaining) | [`analysis/HOC_remaining_domains_analysis_v1.md`](analysis/HOC_remaining_domains_analysis_v1.md) | COMPLETE |

**Consolidated Reports:**
- [`analysis/HOC_consolidation_report_v1.md`](analysis/HOC_consolidation_report_v1.md) — Cross-domain consolidation
- [`analysis/HOC_general_detailed_report_v1.md`](analysis/HOC_general_detailed_report_v1.md) — General domain deep dive
- [`analysis/HOC_general_domain_constitution_v1.md`](analysis/HOC_general_domain_constitution_v1.md) — General domain governance

**Design Documents:**
- [`analysis/HOUSEOFCARDS_DIRECTORY_DESIGN.md`](analysis/HOUSEOFCARDS_DIRECTORY_DESIGN.md) — Directory structure design
- [`analysis/HOUSEOFCARDS_IMPLEMENTATION_PLAN.md`](analysis/HOUSEOFCARDS_IMPLEMENTATION_PLAN.md) — Initial implementation plan

---

## 4. Domain Audit Reports

Internal audit reports for each domain (located in domain folders for proximity).

| Domain | Audit Report | Status |
|--------|--------------|--------|
| activity | [`backend/.../activity/HOC_activity_deep_audit_report.md`](../../../backend/app/hoc/cus/activity/HOC_activity_deep_audit_report.md) | CLEAN |
| incidents | [`backend/.../incidents/HOC_incidents_deep_audit_report.md`](../../../backend/app/hoc/cus/incidents/HOC_incidents_deep_audit_report.md) | QUARANTINED |
| incidents | [`backend/.../incidents/INCIDENTS_DOMAIN_ANALYSIS_REPORT.md`](../../../backend/app/hoc/cus/incidents/INCIDENTS_DOMAIN_ANALYSIS_REPORT.md) | Phase 2.5B Analysis |
| incidents | [`backend/.../incidents/INCIDENTS_BLCA_REPORT.md`](../../../backend/app/hoc/cus/incidents/INCIDENTS_BLCA_REPORT.md) | BLCA Baseline |
| policies | [`backend/.../policies/HOC_policies_detailed_audit_report.md`](../../../backend/app/hoc/cus/policies/HOC_policies_detailed_audit_report.md) | CLEAN |
| policies | [`backend/.../policies/HOC_policies_deep_audit_report.md`](../../../backend/app/hoc/cus/policies/HOC_policies_deep_audit_report.md) | CLEAN |
| logs | [`backend/.../logs/HOC_logs_detailed_audit_report.md`](../../../backend/app/hoc/cus/logs/HOC_logs_detailed_audit_report.md) | CLEAN |
| analytics | [`backend/.../analytics/HOC_analytics_detailed_audit_report.md`](../../../backend/app/hoc/cus/analytics/HOC_analytics_detailed_audit_report.md) | CLEAN |
| integrations | [`backend/.../integrations/HOC_integrations_detailed_audit_report.md`](../../../backend/app/hoc/cus/integrations/HOC_integrations_detailed_audit_report.md) | QUARANTINED |
| api_keys | [`backend/.../api_keys/HOC_api_keys_detailed_audit_report.md`](../../../backend/app/hoc/cus/api_keys/HOC_api_keys_detailed_audit_report.md) | CLEAN |
| account | [`backend/.../account/HOC_account_detailed_audit_report.md`](../../../backend/app/hoc/cus/account/HOC_account_detailed_audit_report.md) | HEALTHY |
| overview | [`backend/.../overview/HOC_overview_detailed_audit_report.md`](../../../backend/app/hoc/cus/overview/HOC_overview_detailed_audit_report.md) | EXCELLENT |
| general | [`backend/.../general/HOC_general_deep_audit_report.md`](../../../backend/app/hoc/cus/general/HOC_general_deep_audit_report.md) | RESOLVED |
| general | [`backend/.../general/HOC_general_audit_domain.md`](../../../backend/app/hoc/cus/general/HOC_general_audit_domain.md) | — |

---

## 5. Domain Lock Documents

Final lock documents for domains that have completed L4/L6 structural layering.

| Domain | Lock Document | Lock Date | Status |
|--------|---------------|-----------|--------|
| **analytics** | [`ANALYTICS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **policies** | [`POLICIES_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/policies/POLICIES_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **activity** | [`ACTIVITY_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/activity/ACTIVITY_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **logs** | [`LOGS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/logs/LOGS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **incidents** | [`INCIDENTS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/incidents/INCIDENTS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **overview** | [`OVERVIEW_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/overview/OVERVIEW_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **api_keys** | [`API_KEYS_DOMAIN_LOCK_FINAL.md`](implementation/API_KEYS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **account** | [`ACCOUNT_DOMAIN_LOCK_FINAL.md`](implementation/ACCOUNT_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **integrations** | [`INTEGRATIONS_DOMAIN_LOCK_FINAL.md`](implementation/INTEGRATIONS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED (debt) |
| **general** | [`GENERAL_DOMAIN_LOCK_FINAL.md`](../../../backend/app/hoc/cus/general/GENERAL_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |

---

## 6. Implementation Plans

Active implementation plans for Phase 2.5A domain extraction.

| Domain | Implementation Plan | Status |
|--------|---------------------|--------|
| activity | [`ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED |
| logs | [`LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED |
| incidents | [`INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED |
| overview | [`OVERVIEW_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/OVERVIEW_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED |
| **api_keys** | [`API_KEYS_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/API_KEYS_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED |
| **account** | [`ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED |
| **integrations** | [`INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md`](implementation/INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md) | COMPLETE → LOCKED (debt) |

### Phase 2.5B Customer Domain Audit

| Document | Location | Status |
|----------|----------|--------|
| Customer Domain Audit | [`backend/.../cus/HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md`](../../../backend/app/hoc/cus/HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md) | COMPLETE |

---

## 7. Directory Structure

```
docs/architecture/
├── HOC_LAYER_TOPOLOGY_V1.md          # CANONICAL layer architecture
├── HOC_MIGRATION_PLAN.md             # Master migration plan (5 phases)
│
└── hoc/                              # HOC Documentation Hub
    ├── INDEX.md                      # THIS FILE - Master index
    │
    ├── analysis/                     # Pre-migration domain analysis
    │   ├── HOC_activity_analysis_v1.md
    │   ├── HOC_incidents_analysis_v1.md
    │   ├── HOC_policies_analysis_v1.md
    │   ├── HOC_logs_analysis_v1.md
    │   ├── HOC_analytics_analysis_v1.md
    │   ├── HOC_integrations_analysis_v1.md
    │   ├── HOC_api_keys_analysis_v1.md
    │   ├── HOC_account_analysis_v1.md
    │   ├── HOC_overview_analysis_v1.md
    │   ├── HOC_general_analysis_v1.md
    │   ├── HOC_remaining_domains_analysis_v1.md
    │   ├── HOC_consolidation_report_v1.md
    │   ├── HOC_general_detailed_report_v1.md
    │   ├── HOC_general_domain_constitution_v1.md
    │   ├── HOUSEOFCARDS_DIRECTORY_DESIGN.md
    │   └── HOUSEOFCARDS_IMPLEMENTATION_PLAN.md
    │
    ├── migration/                    # Migration execution docs
    │   ├── PHASE1_MIGRATION_PLAN.md
    │   ├── PHASE1_COMPLETION_REPORT.md
    │   ├── ITERATION1_AUDIT_REPORT.md
    │   ├── ITERATION2_AUDIT_REPORT.md
    │   ├── PHASE2_MIGRATION_PLAN.md
    │   ├── PHASE2_STEP0_AUDIT.md
    │   ├── PHASE2_STEP3_LAYER_CRITERIA.md
    │   ├── PHASE2_EXTRACTION_PLAYBOOK.md
    │   ├── PHASE2_EXTRACTION_PROTOCOL.md
    │   ├── layer_fit_*.md
    │   ├── MIGRATION_INVENTORY_*.csv
    │   └── driver_templates/
    │
    └── implementation/               # Phase 2.5A implementation plans
        └── ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md (to be created)

backend/app/hoc/
├── DRIVER_ENGINE_CONTRACT.md         # L5/L6 contract
├── INVENTORY.md                      # File inventory
│
└── cus/                              # Customer audience (was: customer/)
    ├── overview/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── api_keys/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── account/
    │   ├── L5_engines/
    │   ├── L5_notifications/
    │   ├── L5_schemas/
    │   ├── L5_support/
    │   └── L6_drivers/
    ├── activity/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── incidents/
    │   ├── L3_adapters/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── policies/
    │   ├── L5_controls/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── logs/
    │   ├── L3_adapters/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── analytics/
    │   ├── L3_adapters/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   └── L6_drivers/
    ├── integrations/
    │   ├── L3_adapters/
    │   ├── L5_engines/
    │   ├── L5_schemas/
    │   ├── L5_vault/
    │   └── L6_drivers/
    └── general/                       # Cross-domain + L4 runtime
        ├── L3_mcp/
        ├── L4_runtime/               # ONLY L4 location
        ├── L5_controls/
        ├── L5_engines/
        ├── L5_lifecycle/
        ├── L5_schemas/
        ├── L5_ui/
        ├── L5_utils/
        ├── L5_workflow/
        └── L6_drivers/
```

---

## 8. Cross-Reference: CLAUDE.md

This index is referenced in `/CLAUDE.md` under:
- **BL-HOC-LAYER-001** — HOC Layer Topology canonical reference
- **Session Bootstrap** — `hoc_layer_topology_loaded: YES`

---

## 9. Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-24 | Initial index created | Claude |
| 2026-01-24 | Consolidated analysis docs from backend/docs/architecture/ | Claude |
| 2026-01-24 | Moved migration/ to hoc/migration/ | Claude |
| 2026-01-24 | Logs domain LOCKED (Phase 2.5B complete) | Claude |
| 2026-01-24 | CORRECTION: Restored logs_facade.py + export_bundle_service.py with L4/L6 split | Claude |
| 2026-01-24 | Full logs domain audit: 56 files, AUDIENCE header gaps identified | Claude |
| 2026-01-24 | Incidents Phase 2.5B Phase I-II complete, BLCA updated with HOC Layer Topology V1 | Claude |
| 2026-01-24 | Added INCIDENTS_BLCA_REPORT.md, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md | Claude |
| 2026-01-24 | **Incidents domain LOCKED** — 5/5 fixes complete, INCIDENTS_DOMAIN_LOCK_FINAL.md created | Claude |
| 2026-01-24 | Customer domain audit complete — overview selected as next Phase 2.5B candidate | Claude |
| 2026-01-24 | Added OVERVIEW_PHASE2.5_IMPLEMENTATION_PLAN.md, overview domain IN PROGRESS | Claude |
| 2026-01-24 | **Overview domain LOCKED** — 1/1 fix complete, OVERVIEW_DOMAIN_LOCK_FINAL.md created | Claude |
| 2026-01-24 | **API Keys domain LOCKED** — 7/7 fixes complete, L4/L6 extraction done, API_KEYS_DOMAIN_LOCK_FINAL.md created | Claude |
| 2026-01-24 | **Account domain analysis COMPLETE** — 9 violations found (3 CRITICAL, 6 MEDIUM), ACCOUNT_DOMAIN_ANALYSIS_REPORT.md created | Claude |
| 2026-01-24 | **Account domain LOCKED** — 9/9 fixes complete, L4/L6 extraction done, ACCOUNT_DOMAIN_LOCK_FINAL.md created | Claude |
| 2026-01-24 | **Integrations domain LOCKED (with debt)** — 12 fixes complete, 3 HYBRID files (M25 debt), INTEGRATIONS_DOMAIN_LOCK_FINAL.md created | Claude |
| 2026-01-24 | **General domain LOCKED** — 31 files reclassified (13 engines L4→L5, 5 facades →L3, 6 schemas →L5, 4 utils/drivers →L5, 1 file moved engines→drivers), GENERAL_DOMAIN_LOCK_FINAL.md created | Claude |
| 2026-01-24 | **Phase 2.5C BANNED_NAMING** — All customer domain `*_service.py` files renamed to `*_engine.py` or `*_driver.py`. 0 customer BANNED_NAMING violations remaining. | Claude |
| 2026-01-24 | **Phase 2.5D HEADER_CLAIM_MISMATCH** — 19 customer domain files reclassified L6→L5 (no DB ops). Includes: logs (6 files), incidents (4 files), integrations (3 files), general (4 files), account (2 files). 0 customer HEADER_CLAIM_MISMATCH errors remaining. | Claude |
| 2026-01-24 | **Phase 2.5E MISSING_HEADER + RELOCATION** — Added L5 headers to 15 customer domain files (analytics/engines, general/controls, policies/engines, duplicates). Relocated 9 L5 engine files from policies/drivers/ → policies/engines/. **HOC customer domain BLCA: 0 errors, 0 warnings.** | Claude |
| 2026-01-24 | **Phase 2.5E VERIFICATION COMPLETE** — All 10 customer domain lock documents updated with BLCA verification status (0 errors, 0 warnings across all 6 check types): ACTIVITY v1.2.0, ANALYTICS v1.1.0, GENERAL v1.1.0, INCIDENTS v1.3.0, LOGS v1.4.0, OVERVIEW v1.1.0, POLICIES v1.2.0, API_KEYS, ACCOUNT, INTEGRATIONS. | Claude |
| 2026-01-24 | **Phase 3 APPROVED** — Directory restructure plan approved. Layer-prefixed folders (L3_adapters/, L5_engines/, L6_drivers/). L4 centralized to general/L4_runtime/. API nesting (L2.1 + L2). HOC_LAYER_TOPOLOGY_V1.md updated to v1.3.0. | Claude |
| 2026-01-24 | **Phase 3 UPDATE** — Package & audience rename added: `hoc` → `hoc`, `customer` → `cus`, `founder` → `fdr`, `internal` → `int`. Saves 14 chars per import. PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md updated to v1.1.0. HOC_LAYER_TOPOLOGY_V1.md updated to v1.4.0. | Claude |
| 2026-01-24 | **Phase 3 COMPLETE** — All 10 customer domains migrated (overview, api_keys, account, activity, incidents, policies, logs, analytics, integrations, general). Layer-prefixed folders deployed. Facades merged into L5_engines or L3_adapters. L4 centralized to general/L4_runtime/ only. | Claude |
| 2026-01-24 | **Phase 3 L5/L6 FIX** — Relocated 52 L5 engine files from L6_drivers/ to L5_engines/ based on content analysis. Files declared L5 with no DB ops. Domains: policies (18), general (13), logs (6), integrations (6), incidents (4), account (2), analytics (2), activity (1). BLCA customer domain: 0 structure errors. PIN-470. | Claude |
| 2026-01-25 | **Phase 3B P3 COMPLETE** — SQLAlchemy extraction from L5 to L6 complete. `policy_proposal.py` reclassified L3→L5 and split (engine + read/write drivers). `policies_facade.py` split into 3 query engines (`policies_rules_query_engine.py`, `policies_limits_query_engine.py`, `policies_proposals_query_engine.py`) with corresponding L6 drivers. Scanner: 0 BLOCKING, 0 DEFERRED. 3 FROZEN files remain (M25 debt). | Claude |
| 2026-01-25 | **Phase 4 Research COMPLETE** — General domain wiring analysis. Found: 9 datetime gaps, 2 CRITICAL governance/transaction coordinator duplicates (policies vs general), 19 files needing orchestration wiring, 4 multi-model write gaps. L4_runtime services have 0 imports from other domains. GENERAL_DOMAIN_WIRING_PHASE1.md created. | Claude |
| 2026-01-25 | **Phase 4 Phase 2 Research COMPLETE** — Comprehensive function catalog of general domain. Documented: 39 files, 52+ classes, 237+ functions across L4_runtime (6), L5_lifecycle (6), L5_controls (2), L5_workflow (1), L5_engines (24). Identified 51 wiring candidate files across 6 domains (policies, incidents, analytics, account, logs, integrations). GENERAL_DOMAIN_WIRING_PHASE2.md created. | Claude |
| 2026-01-25 | **Authority Violation Spec v1.0 DRAFT** — First-principles specification defining 4 authorities (TIME, TRANSACTION, ORCHESTRATION, STATE) and 6 violation categories (TIME_LEAK, STATE_MACHINE_DUPLICATION, TRANSACTION_BYPASS, ORCHESTRATION_LEAK, AUTHORITY_LEAK, DECISION_VS_EXECUTION). Includes severity matrix, decision tables, and CI enforcement phases. AUTHORITY_VIOLATION_SPEC_V1.md created. | Claude |
| 2026-01-25 | **Runtime Context Model v1.0 DRAFT** — Defines how authority constraints enter the system via 4 context objects (TimeContext, TransactionContext, OrchestrationContext, StateContext). Core rule: "Contexts are PASSED, never fetched." Includes construction rules, passing rules, forbidden patterns, and migration path. RUNTIME_CONTEXT_MODEL.md created. | Claude |
| 2026-01-25 | **L4/L5 Contracts v1.0 DRAFT** — Protocol-based contracts for each layer: RuntimeCoordinatorContract (L4), OrchestratorContract (L4), DomainEngineContract (L5), TransactionalEngineContract (L5), StatefulEngineContract (L5_workflow), PersistenceDriverContract (L6). Enforced by type system (mypy) + analyzer. Forbidden dependency matrix defined. L4_L5_CONTRACTS_V1.md created. | Claude |
| 2026-01-25 | **Authority Analyzer v1.0 ACTIVE** — Mechanical enforcer implemented at `scripts/ops/hoc_authority_analyzer.py`. Scans HOC customer domains for authority violations. First scan: 448 files, 1147 violations (137 CRITICAL, 1010 HIGH). Violations by type: TIME_LEAK (903), TRANSACTION_BYPASS (116), AUTHORITY_LEAK (109), ORCHESTRATION_LEAK (19). Top domains: general (235), policies (227), logs (198). Supports `--check` for CI integration. | Claude |
| 2026-01-25 | **TRANSACTION_BYPASS Remediation Checklist v1.0** — Step-by-step guide for eliminating session.commit() from L6 drivers. Target: 116→0 violations. Defines session injection patterns (constructor, method, context), common pitfalls, verification steps, and CI gate criteria. Fixed transaction_coordinator.py header (L6→L4). | Claude |
| 2026-01-25 | **TRANSACTION_BYPASS Remediation: 2/5 P1 files complete** — Remediated `policies/L6_drivers/alert_emitter.py` (4 commits removed) and `policies/L6_drivers/recovery_matcher.py` (2 commits removed). Applied 6 governing principles: L6 no commit, session required, no session creation, no singletons, orphans valid targets, one-way dependency. CRITICAL: 137→131 (-6). Report: `TRANSACTION_BYPASS_REMEDIATION_REPORT_2026-01-25.md`. | Claude |
| 2026-01-30 | **PIN-491 HOC Spine Literature Upgrade + L5 Pairing Gap Detector** — Upgraded 65 literature files with Export Contract, Import Boundary, L5 Pairing Declaration sections. Created `l5_spine_pairing_gap_detector.py`: 185 L5 engines scanned, 0 wired via L4, 32 direct L2→L5 gaps, 153 orphaned. Validator upgraded with boundary validation. | Claude |
| 2026-01-30 | **Phase A.0 COMPLETE** — Built `operation_registry.py` (OperationRegistry, OperationHandler protocol, OperationContext, OperationResult). 16 invariant tests at `hoc_spine/tests/test_operation_registry.py`. Created `handlers/__init__.py` with `register_all_handlers()`. | Claude |
| 2026-01-30 | **Phase A.1 COMPLETE** — Wired 10 facade-pattern operations through L4 registry. Created 6 handler modules (overview, account, analytics, api_keys, incidents, integrations). Updated 10 L2 API files (72 registry.execute() calls). Gap detector: 32→22 gaps, 0→10 wired. | Claude |

---

## 10. Usage

**Finding a document:**
1. Use this index to locate documents by category
2. Domain-specific audits/locks are in their domain folders
3. Migration execution docs are in `hoc/migration/`
4. Pre-migration analysis docs are in `hoc/analysis/`

**Adding new documents:**
1. Place in appropriate subfolder
2. Update this INDEX.md
3. Add cross-references to related documents

**Referencing from code:**
```python
# Layer: L5 — Domain Engine
# Reference: docs/architecture/hoc/INDEX.md → Phase 2.5A
```

---

**END OF INDEX**
