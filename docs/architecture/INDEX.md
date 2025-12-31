# Architecture Documentation Index

**Status:** ACTIVE
**Version:** 1.0.0
**Generated:** 2025-12-31
**Purpose:** Master index of architecture documentation

---

## Document Categories

### 1. Signal Registry (L2-L8 Data Flow)

| Document | Purpose | Status |
|----------|---------|--------|
| [SIGNAL_REGISTRY_COMPLETE.md](SIGNAL_REGISTRY_COMPLETE.md) | Complete signal registry (43 signals) | v1.0.1 FROZEN |
| [SIGNAL_REGISTRY_PYTHON_BASELINE.md](SIGNAL_REGISTRY_PYTHON_BASELINE.md) | Backend Python baseline (336 runtime files) | v1.0.1 FROZEN |
| [REGISTRY_CHANGES/](REGISTRY_CHANGES/) | Versioned change records | ACTIVE |

### 2. Layer Flow Analysis (L5-L7)

| Document | Purpose | Status |
|----------|---------|--------|
| [L7_INTERNAL_FLOWS.md](L7_INTERNAL_FLOWS.md) | L7→L7 internal ops flows (21 flows) | VERIFIED |
| [L7_L6_FLOWS.md](L7_L6_FLOWS.md) | L7→L6 runtime flows | VERIFIED (all gaps closed) |
| [L7_L6_SUFFICIENCY_ANALYSIS.md](L7_L6_SUFFICIENCY_ANALYSIS.md) | L7→L6 decision tree analysis | REFERENCE |
| [L6_INTERNAL_FLOWS.md](L6_INTERNAL_FLOWS.md) | L6→L6 substrate coherency | VERIFIED |
| [L6_L5_FLOWS.md](L6_L5_FLOWS.md) | L6→L5 substrate consumption (31 flows) | STATIC VERIFIED |
| [L7_L6_L5_COHERENCY_PASS.md](L7_L6_L5_COHERENCY_PASS.md) | End-to-end L7→L6→L5 coherency | COMPLETE |
| [IMPLIED_INTENT_ANALYSIS.md](IMPLIED_INTENT_ANALYSIS.md) | Forensic intent classification (Class A/B/C) | COMPLETE |
| [AUTHORITY_BOUNDARIES.md](AUTHORITY_BOUNDARIES.md) | Layer intent authority declarations | DECLARED |
| [LAYERED_SEMANTIC_COMPLETION_CONTRACT.md](LAYERED_SEMANTIC_COMPLETION_CONTRACT.md) | L7→L2 completion contract (Phases A-D) | ACTIVE |
| [L5_L4_SEMANTIC_MAPPING.md](L5_L4_SEMANTIC_MAPPING.md) | Phase A: L5→L4 domain authority mapping | COMPLETE |
| [L4_L3_TRANSLATION_INTEGRITY.md](L4_L3_TRANSLATION_INTEGRITY.md) | Phase B: L4→L3 translation integrity | COMPLETE |

### 3. Runtime Assets

| Document | Purpose | Status |
|----------|---------|--------|
| [RUNTIME_ASSETS.md](RUNTIME_ASSETS.md) | Non-signal runtime artifacts | VERIFIED |

### 4. Semantic Contracts

| Document | Purpose | Status |
|----------|---------|--------|
| [AUTH_SEMANTIC_CONTRACT.md](AUTH_SEMANTIC_CONTRACT.md) | Authentication semantic contract | ACTIVE |
| [EXECUTION_SEMANTIC_CONTRACT.md](EXECUTION_SEMANTIC_CONTRACT.md) | Execution semantic contract | ACTIVE |
| [PHASE3_SEMANTIC_CHARTER.md](PHASE3_SEMANTIC_CHARTER.md) | Phase 3 semantic alignment charter | REFERENCE |

### 5. Structural Maps

| Document | Purpose | Status |
|----------|---------|--------|
| [STRUCTURAL_TRUTH_MAP.md](STRUCTURAL_TRUTH_MAP.md) | Complete structural truth map | FROZEN |
| [SEMANTIC_COORDINATE_MAP.md](SEMANTIC_COORDINATE_MAP.md) | Semantic coordinate mapping | FROZEN |
| [L1_L2_L8_BINDING_AUDIT.md](L1_L2_L8_BINDING_AUDIT.md) | L1/L2/L8 binding audit | VERIFIED |

### 6. CI/CD Architecture

| Document | Purpose | Status |
|----------|---------|--------|
| [CI_CANDIDATE_MATRIX.md](CI_CANDIDATE_MATRIX.md) | CI candidate evaluation matrix | REFERENCE |
| [CI_DRYRUN_EVALUATION_REPORT.md](CI_DRYRUN_EVALUATION_REPORT.md) | CI dry-run evaluation report | REFERENCE |
| [CI_SCOPE_FREEZE.md](CI_SCOPE_FREEZE.md) | CI scope freeze decision | FROZEN |

### 7. Incident & Taxonomy

| Document | Purpose | Status |
|----------|---------|--------|
| [ARCHITECTURE_INCIDENT_TAXONOMY.md](ARCHITECTURE_INCIDENT_TAXONOMY.md) | Incident classification taxonomy | ACTIVE |

### 8. Phase Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| [PHASE1_ADDENDA.md](PHASE1_ADDENDA.md) | Phase 1 addenda | REFERENCE |
| [PHASE2_STRUCTURAL_ALIGNMENT_PLAN.md](PHASE2_STRUCTURAL_ALIGNMENT_PLAN.md) | Phase 2 alignment plan | REFERENCE |
| [PHASE2_ALIGNMENT_PLAN_DRAFT.md](PHASE2_ALIGNMENT_PLAN_DRAFT.md) | Phase 2 alignment draft | REFERENCE |
| [PHASE2_ALIGNMENT_PLAN_v2.md](PHASE2_ALIGNMENT_PLAN_v2.md) | Phase 2 alignment plan v2 | REFERENCE |
| [PHASE2_COMPLETION_GATE.md](PHASE2_COMPLETION_GATE.md) | Phase 2 completion gate | CLOSED |
| [PHASE2_RETROSPECTIVE.md](PHASE2_RETROSPECTIVE.md) | Phase 2 retrospective | REFERENCE |
| [PHASE2B_BATCH1_PREVIEW.md](PHASE2B_BATCH1_PREVIEW.md) | Phase 2B batch 1 preview | REFERENCE |

### 9. Console Mapping

| Document | Purpose | Status |
|----------|---------|--------|
| [console-slice-mapping.md](console-slice-mapping.md) | Console slice mapping | REFERENCE |

---

## Layer Model Reference

| Layer | Name | Scope |
|-------|------|-------|
| L1 | Product Experience (UI) | Pages, components |
| L2 | Product APIs | REST endpoints |
| L3 | Boundary Adapters | Thin translation |
| L4 | Domain Engines | Business rules |
| L5 | Execution & Workers | Background jobs |
| L6 | Platform Substrate | DB, Redis, external services |
| L7 | Ops & Deployment | Systemd, Docker, schedulers |
| L8 | Catalyst / Meta | CI, tests, validators |

---

## Open Gaps

**All gaps resolved.**

| Gap ID | Document | Description | Resolution |
|--------|----------|-------------|------------|
| ~~GAP-002~~ | L7_L6_FLOWS.md | ~~Cost Snapshot Job unregistered~~ | ✅ Registered as SIG-017 (RC-002) |
| ~~GAP-003~~ | L7_L6_FLOWS.md | ~~M10 Orchestrator classification~~ | ✅ Control-plane only |

---

## Registry Change History

| Change ID | Date | Document | Description |
|-----------|------|----------|-------------|
| RC-002 | 2025-12-31 | SIGNAL_REGISTRY_*.md | SIG-017 registered: CostSnapshot (closes GAP-002) |
| RC-001 | 2025-12-31 | SIGNAL_REGISTRY_*.md | SIG-100 corrected: L4→L5 producer, In-memory→PostgreSQL |

---

## Flow Verification Summary

| Flow Type | Document | Count | Verification Level |
|-----------|----------|-------|-------------------|
| L7 → L7 | L7_INTERNAL_FLOWS.md | 21 | STATIC |
| L7 → L6 | L7_L6_FLOWS.md | 6 L7→L6, 1 L7-internal | STATIC |
| L6 → L6 | L6_INTERNAL_FLOWS.md | 6 artifact types, 4 patterns | STATIC |
| L6 → L5 | L6_L5_FLOWS.md | 31 substrate flows | STATIC |
| L5 → L8 | L6_L5_FLOWS.md | 8 telemetry emissions | N/A (write-only) |
| L7 → L8 | L7_L6_FLOWS.md | 1 (metrics) | STATIC |

**Note:** All verifications are STATIC (code path exists). SEMANTIC verification (intentional dependency) pending.

---

## STATIC → SEMANTIC Promotion Rule

A dependency may be promoted from STATIC to SEMANTIC verification when **any two** of the following apply:

| Criterion | Evidence |
|-----------|----------|
| Referenced in incident/postmortem | Documented failure involving this dependency |
| Used by more than one consumer | Multiple callers in different modules |
| Gated by feature/capability logic | Dependency controls runtime behavior |
| Explicitly relied on by rollback/recovery | Recovery path depends on this artifact |

**Process:**
1. Identify the authority for the layer (see AUTHORITY_BOUNDARIES.md)
2. Present evidence meeting ≥2 criteria
3. Authority confirms intentional dependency
4. Update verification status from STATIC to SEMANTIC

---

## Out of Scope (Current Analysis)

The following are **explicitly excluded** from L5-L7 layer flow analysis:

| Category | Reason |
|----------|--------|
| One-off admin scripts | Operator-only, not runtime path |
| Emergency / break-glass paths | Exceptional, not normal flow |
| Migration-time behaviors | Transient, not steady-state |
| Human-in-the-loop ops actions | Manual intervention, not automated |
| CLI commands (`cli/*.py`) | Developer tooling, not production |
| Debug/diagnostic endpoints | Observability, not execution |

**Note:** Exclusion does not mean these are unimportant. It means they are outside the scope of automated coherency verification.

---

## Maintenance Notes

- Signal registry updates require versioned change records in `REGISTRY_CHANGES/`
- Layer flow documents are authoritative for coherency verification
- Phase documents are historical reference only
- Semantic contracts are binding unless explicitly amended
- Authority boundaries must be consulted for STATIC→SEMANTIC promotion

---

**Generated by:** Claude Opus 4.5
**Reference:** PIN-252 (Backend Signal Registry)
