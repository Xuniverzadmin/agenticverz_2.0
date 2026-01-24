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
| **Driver-Engine Contract** | [`../../../backend/app/houseofcards/DRIVER_ENGINE_CONTRACT.md`](../../../backend/app/houseofcards/DRIVER_ENGINE_CONTRACT.md) | — | ACTIVE | L5/L6 boundary rules |

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
| **analytics** | LOCKED | [`backend/.../analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md) |
| **policies** | LOCKED | [`backend/.../policies/POLICIES_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/policies/POLICIES_DOMAIN_LOCK_FINAL.md) |
| **activity** | LOCKED | [`backend/.../activity/ACTIVITY_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/activity/ACTIVITY_DOMAIN_LOCK_FINAL.md) |
| **logs** | LOCKED | [`backend/.../logs/LOGS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/logs/LOGS_DOMAIN_LOCK_FINAL.md) |
| **incidents** | LOCKED | [`backend/.../incidents/INCIDENTS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/incidents/INCIDENTS_DOMAIN_LOCK_FINAL.md) |
| **overview** | LOCKED | [`backend/.../overview/OVERVIEW_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/overview/OVERVIEW_DOMAIN_LOCK_FINAL.md) |
| **api_keys** | LOCKED | [`implementation/API_KEYS_DOMAIN_LOCK_FINAL.md`](implementation/API_KEYS_DOMAIN_LOCK_FINAL.md) |
| **account** | LOCKED | [`implementation/ACCOUNT_DOMAIN_LOCK_FINAL.md`](implementation/ACCOUNT_DOMAIN_LOCK_FINAL.md) |
| **integrations** | LOCKED (debt) | [`implementation/INTEGRATIONS_DOMAIN_LOCK_FINAL.md`](implementation/INTEGRATIONS_DOMAIN_LOCK_FINAL.md) |
| general | LOCKED | [`backend/.../general/GENERAL_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/general/GENERAL_DOMAIN_LOCK_FINAL.md) |

### Phase 3-5: (PLANNED)

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 3: Gap Development | PLANNED | Build missing L2.1, L4, L6 components |
| Phase 4: Wiring | PLANNED | Connect all layers, validate contracts |
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
| activity | [`backend/.../activity/HOC_activity_deep_audit_report.md`](../../../backend/app/houseofcards/customer/activity/HOC_activity_deep_audit_report.md) | CLEAN |
| incidents | [`backend/.../incidents/HOC_incidents_deep_audit_report.md`](../../../backend/app/houseofcards/customer/incidents/HOC_incidents_deep_audit_report.md) | QUARANTINED |
| incidents | [`backend/.../incidents/INCIDENTS_DOMAIN_ANALYSIS_REPORT.md`](../../../backend/app/houseofcards/customer/incidents/INCIDENTS_DOMAIN_ANALYSIS_REPORT.md) | Phase 2.5B Analysis |
| incidents | [`backend/.../incidents/INCIDENTS_BLCA_REPORT.md`](../../../backend/app/houseofcards/customer/incidents/INCIDENTS_BLCA_REPORT.md) | BLCA Baseline |
| policies | [`backend/.../policies/HOC_policies_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/policies/HOC_policies_detailed_audit_report.md) | CLEAN |
| policies | [`backend/.../policies/HOC_policies_deep_audit_report.md`](../../../backend/app/houseofcards/customer/policies/HOC_policies_deep_audit_report.md) | CLEAN |
| logs | [`backend/.../logs/HOC_logs_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/logs/HOC_logs_detailed_audit_report.md) | CLEAN |
| analytics | [`backend/.../analytics/HOC_analytics_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/analytics/HOC_analytics_detailed_audit_report.md) | CLEAN |
| integrations | [`backend/.../integrations/HOC_integrations_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/integrations/HOC_integrations_detailed_audit_report.md) | QUARANTINED |
| api_keys | [`backend/.../api_keys/HOC_api_keys_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/api_keys/HOC_api_keys_detailed_audit_report.md) | CLEAN |
| account | [`backend/.../account/HOC_account_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/account/HOC_account_detailed_audit_report.md) | HEALTHY |
| overview | [`backend/.../overview/HOC_overview_detailed_audit_report.md`](../../../backend/app/houseofcards/customer/overview/HOC_overview_detailed_audit_report.md) | EXCELLENT |
| general | [`backend/.../general/HOC_general_deep_audit_report.md`](../../../backend/app/houseofcards/customer/general/HOC_general_deep_audit_report.md) | RESOLVED |
| general | [`backend/.../general/HOC_general_audit_domain.md`](../../../backend/app/houseofcards/customer/general/HOC_general_audit_domain.md) | — |

---

## 5. Domain Lock Documents

Final lock documents for domains that have completed L4/L6 structural layering.

| Domain | Lock Document | Lock Date | Status |
|--------|---------------|-----------|--------|
| **analytics** | [`ANALYTICS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **policies** | [`POLICIES_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/policies/POLICIES_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **activity** | [`ACTIVITY_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/activity/ACTIVITY_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **logs** | [`LOGS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/logs/LOGS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **incidents** | [`INCIDENTS_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/incidents/INCIDENTS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **overview** | [`OVERVIEW_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/overview/OVERVIEW_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **api_keys** | [`API_KEYS_DOMAIN_LOCK_FINAL.md`](implementation/API_KEYS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **account** | [`ACCOUNT_DOMAIN_LOCK_FINAL.md`](implementation/ACCOUNT_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |
| **integrations** | [`INTEGRATIONS_DOMAIN_LOCK_FINAL.md`](implementation/INTEGRATIONS_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED (debt) |
| **general** | [`GENERAL_DOMAIN_LOCK_FINAL.md`](../../../backend/app/houseofcards/customer/general/GENERAL_DOMAIN_LOCK_FINAL.md) | 2026-01-24 | LOCKED |

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
| Customer Domain Audit | [`backend/.../customer/HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md`](../../../backend/app/houseofcards/customer/HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md) | COMPLETE |

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

backend/app/houseofcards/
├── DRIVER_ENGINE_CONTRACT.md         # L5/L6 contract
├── INVENTORY.md                      # File inventory
│
└── customer/
    ├── analytics/
    │   ├── ANALYTICS_DOMAIN_LOCK_FINAL.md    # LOCKED
    │   └── HOC_analytics_detailed_audit_report.md
    ├── policies/
    │   ├── POLICIES_DOMAIN_LOCK_FINAL.md     # LOCKED
    │   └── HOC_policies_*_audit_report.md
    ├── activity/
    │   └── HOC_activity_deep_audit_report.md
    ├── incidents/
    │   └── HOC_incidents_deep_audit_report.md
    ├── logs/
    │   └── HOC_logs_detailed_audit_report.md
    ├── integrations/
    │   └── HOC_integrations_detailed_audit_report.md
    ├── api_keys/
    │   └── HOC_api_keys_detailed_audit_report.md
    ├── account/
    │   └── HOC_account_detailed_audit_report.md
    ├── overview/
    │   └── HOC_overview_detailed_audit_report.md
    └── general/
        ├── HOC_general_deep_audit_report.md
        └── HOC_general_audit_domain.md
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
