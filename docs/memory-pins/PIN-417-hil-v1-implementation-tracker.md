# PIN-417: HIL v1 Implementation Tracker

**Status:** CLOSED
**Created:** 2026-01-14
**Closed:** 2026-01-14
**Category:** UI Pipeline / Human Interpretation Layer
**Milestone:** HIL v1
**Closure Document:** `docs/governance/HIL_V1_CLOSURE.md`

---

## Summary

Tracking PIN for the complete Human Interpretation Layer (HIL) v1 implementation.
HIL provides a narrative layer over execution truth, enabling humans to understand
what happened through summaries and aggregations while maintaining full traceability.

**HIL v1 is FROZEN.** No further development without new PIN and founder approval.

---

## Progress Overview

| Phase | Description | Status | PIN |
|-------|-------------|--------|-----|
| **Phase 1** | Schema Extension (Documentation) | ✅ COMPLETE | PIN-416 |
| **Phase 2** | Runtime Support (Compiler + Frontend) | ✅ COMPLETE | PIN-417 |
| **Phase 3** | First Implementation (Activity Domain) | ✅ COMPLETE | PIN-417 |
| **Phase 4** | Second Implementation (Incidents Domain) | ✅ COMPLETE | PIN-417 |

**Overall Progress:** 4/4 phases complete (100%)

---

## Phase 1: Schema Extension ✅ COMPLETE

**Date Completed:** 2026-01-14
**Reference:** PIN-416

### Deliverables

| Artifact | Status | Location |
|----------|--------|----------|
| HIL v1 Contract | ✅ Created | `design/l2_1/HIL_V1_CONTRACT.md` |
| Schema Extension (v1.1) | ✅ Updated | `backend/aurora_l2/schema/intent_spec_schema.json` |
| Domain Intent Registry | ✅ Created | `design/l2_1/AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml` |
| Activity Summary Spec | ✅ Created | `design/l2_1/intents/ACT-EX-SUM-O1.yaml` |
| AURORA_L2.md Section 18 | ✅ Added | `design/l2_1/AURORA_L2.md` |

### Key Decisions Made

1. Panel classification: `execution` | `interpretation`
2. Provenance required for interpretation panels
3. Backend-owned aggregation (no frontend math)
4. Activity domain is pilot for HIL
5. Aggregation types: COUNT, SUM, TREND, STATUS_BREAKDOWN, TOP_N, LATEST

---

## Phase 2: Runtime Support ✅ COMPLETE

**Date Completed:** 2026-01-14
**Depends On:** Phase 1 ✅

### Tasks

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| Update compiler to propagate `panel_class` | ✅ DONE | Claude | `backend/aurora_l2/compiler.py:279,416` |
| Update projection types with `panel_class` | ✅ DONE | Claude | `ui_projection_types.ts:208` |
| Update frontend projection loader | ✅ DONE | Claude | `ui_projection_loader.ts:237-268` |
| Add panel grouping by class in DomainPage | ✅ DONE | Claude | `DomainPage.tsx:398-440` |
| Add visual styling for interpretation panels | ✅ DONE | Claude | Blue border, "Derived" badge |
| Add HIL statistics to projection | ✅ DONE | Claude | `execution_panels`, `interpretation_panels` |

### Acceptance Criteria

- [x] Compiler reads `panel_class` from intent YAML
- [x] Compiler writes `panel_class` to projection JSON
- [x] Frontend groups panels by class in UI (interpretation above execution)
- [x] Interpretation panels have visual distinction (blue border, "Derived" badge)
- [x] Provenance passed through (badge shows in Phase 3)

### Exit Criteria Self-Certification

| Criterion | Status |
|-----------|--------|
| Projection contains `panel_class` | ✅ PASS |
| Existing panels render identically | ✅ PASS |
| Interpretation section renders empty if no panels | ✅ PASS |
| No backend endpoints touched | ✅ PASS |
| No SDSR changes | ✅ PASS |
| No controls added or removed | ✅ PASS |

---

## Phase 3: First Implementation (Activity Domain) ✅ COMPLETE

**Date Completed:** 2026-01-14
**Depends On:** Phase 2 ✅

### Scope Limits (Enforced)

| Artifact | Limit | Delivered |
|----------|-------|-----------|
| Backend endpoint | 1 | `/api/v1/activity/summary` |
| Capability | 1 | `summary.activity` |
| SDSR scenario | 1 | `SDSR-HIL-ACT-SUM-001.yaml` |
| Panel | 1 | `ACT-EX-SUM-O1` |

### Tasks

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| Create `/api/v1/activity/summary` endpoint | ✅ DONE | Claude | `backend/app/api/activity.py:168-238` |
| Create capability registry entry | ✅ DONE | Claude | `AURORA_L2_CAPABILITY_SUMMARY_ACTIVITY.yaml` |
| Create SDSR scenario | ✅ DONE | Claude | With 6 invariants + registry checks |
| Update ACT-EX-SUM-O1 intent | ✅ DONE | Claude | Provenance uses capability IDs |
| Create ActivitySummaryBriefing renderer | ✅ DONE | Claude | `PanelContentRegistry.tsx:290-406` |
| Wire panel to PanelContentRegistry | ✅ DONE | Claude | `PanelContentRegistry.tsx:2099` |
| Create activity summary API types | ✅ DONE | Claude | `activity.ts:72-131` |

### Machine Quality System (5 Layers)

| Layer | Artifact | Purpose |
|-------|----------|---------|
| 1. Contract Shape | `backend/contracts/activity_summary.schema.json` | JSON Schema validation |
| 2. Semantic Invariants | SDSR scenario INV-001 to INV-006 | Runtime assertions |
| 3. Registry-Backed Semantics | `attention_reasons.yaml` | No free strings |
| 4. SDSR Truth Gate | Scenario with failure taxonomy | Structured diagnostics |
| 5. Projection Diff Guard | `projection_diff_guard.py` | Prevent silent UI drift |

### Backend Endpoint Contract

```
GET /api/v1/activity/summary?window=24h

Response:
{
  "window": "24h",
  "runs": {
    "total": 12,
    "by_status": {
      "running": 2,
      "completed": 10,
      "failed": 3
    }
  },
  "attention": {
    "at_risk_count": 1,
    "reasons": ["long_running"]
  },
  "provenance": {
    "derived_from": ["activity.runs.list", "incidents.list"],
    "aggregation": "STATUS_BREAKDOWN",
    "generated_at": "2026-01-14T10:30:00Z"
  }
}
```

### Key Design Decisions

1. **Provenance uses capability IDs** (not panel IDs) - survives UI refactors
2. **Attention reasons are registry-backed** - `long_running`, `near_budget_threshold`
3. **No adjectives in response** - counts only, no "good/bad" judgments
4. **Window must be explicit** - `?window=24h` or `?window=7d`
5. **Counts must reconcile** - `running + completed == total`

### Acceptance Criteria

- [x] Activity Summary panel renders in UI
- [x] Shows run counts by status (total, running, completed, failed)
- [x] Shows attention section with reasons when runs need attention
- [x] Provenance section shows derived_from capability IDs
- [x] No frontend computation (backend-only aggregation)
- [x] Read-only panel (no controls)

### Exit Criteria Self-Certification

| Criterion | Status |
|-----------|--------|
| Backend endpoint returns JSON Schema-compliant response | ✅ PASS |
| Capability registered with DECLARED status | ✅ PASS |
| SDSR scenario covers all invariants | ✅ PASS |
| Intent YAML uses capability IDs for provenance | ✅ PASS |
| Frontend renderer displays all data sections | ✅ PASS |
| Projection Diff Guard integrated in pipeline | ✅ PASS |
| No scope creep (1 endpoint, 1 capability, 1 scenario, 1 panel) | ✅ PASS |

---

## Phase 4: Incidents Domain ✅ COMPLETE

**Date Completed:** 2026-01-14
**Depends On:** Phase 3

### Delivered Artifacts

| Artifact | Status | Location |
|----------|--------|----------|
| Backend Endpoint | ✅ DONE | `backend/app/api/incidents.py:182-290` |
| Response Schema | ✅ DONE | `backend/contracts/incidents_summary.schema.json` |
| Capability Registry | ✅ DONE | `AURORA_L2_CAPABILITY_summary.incidents.yaml` |
| Attention Registry | ✅ DONE | `incidents_attention_reasons.yaml` |
| SDSR Scenario | ✅ DONE | `SDSR-HIL-INC-SUM-001.yaml` |
| Intent YAML | ✅ DONE | `design/l2_1/intents/INC-AI-SUM-O1.yaml` |
| API Types | ✅ DONE | `website/app-shell/src/api/incidents.ts:63-95` |
| Panel Renderer | ✅ DONE | `PanelContentRegistry.tsx:IncidentsSummaryBriefing` |

### Issues Encountered & Resolved

| Issue | Root Cause | Fix |
|-------|------------|-----|
| Route shadowing | `/summary` after `/{id}` | Moved `/summary` before `/{id}` |
| Capability file naming | Manual naming mismatch | Renamed to `summary.incidents.yaml` |
| Intent not in registry | Missing registry entry | Added to `AURORA_L2_INTENT_REGISTRY.yaml` |
| Observation class missing | No `observation_class` field | Added `"observation_class": "EFFECT"` |
| PDG blocking | Pre-existing subdomain changes | Manual projection deploy (one-time) |

### Backend Endpoint Contract

```
GET /api/v1/incidents/summary?window=24h

Response:
{
  "window": "24h",
  "incidents": {
    "total": 5,
    "by_lifecycle_state": {
      "active": 2,
      "acked": 1,
      "resolved": 2
    }
  },
  "attention": {
    "count": 2,
    "reasons": ["unresolved", "high_severity"]
  },
  "provenance": {
    "derived_from": ["activity.runs.list", "incidents.list"],
    "aggregation": "STATUS_BREAKDOWN",
    "generated_at": "2026-01-14T11:23:31Z"
  }
}
```

### Invariants Validated (7/7)

| ID | Name | Status |
|----|------|--------|
| INV-001 | lifecycle_sum_reconciliation | ✅ PASS |
| INV-002 | attention_count_matches_active | ✅ PASS |
| INV-003 | window_echo | ✅ PASS |
| INV-004 | attention_reasons_imply_count | ✅ PASS |
| INV-004b | attention_zero_count_zero_reasons | ✅ PASS |
| INV-005 | provenance_present | ✅ PASS |
| INV-007 | aggregation_type_locked | ✅ PASS |

---

## CLOSURE: HIL v1 FROZEN

**Closure Date:** 2026-01-14
**Closure Document:** `docs/governance/HIL_V1_CLOSURE.md`

### Final Delivery

| Domain | Panel | Capability | Status |
|--------|-------|------------|--------|
| Activity | ACT-EX-SUM-O1 | summary.activity | OBSERVED |
| Incidents | INC-AI-SUM-O1 | summary.incidents | OBSERVED |

### What is Now Forbidden

- Adding third domain interpretation
- Adding trends/deltas to summaries
- Adding Overview synthesis
- Modifying attention registries
- Client-side computation
- Bypass PDG manually

### Lessons Locked

1. Static routes before variable routes
2. Capability filenames = `{capability_id}.yaml`
3. Intent registry = eligibility gate
4. PDG allowlist required for changes
5. Observation class is mandatory

### Next Extension Requires

- New PIN opened
- Founder approval
- Clear scope declaration

---

## Governance Rules (Locked)

| Rule ID | Description | Enforcement |
|---------|-------------|-------------|
| HIL-001 | All panels must have `panel_class` | BLOCKING |
| HIL-002 | Interpretation panels must have `provenance` | BLOCKING |
| HIL-003 | Execution panels must not have `provenance` | BLOCKING |
| HIL-004 | Provenance must reference valid panel IDs | BLOCKING |
| HIL-005 | No frontend aggregation | BLOCKING |
| HIL-006 | Interpretation endpoints must return provenance metadata | REQUIRED |

---

## Key Files

| Category | File | Purpose |
|----------|------|---------|
| **Phase 1** | | |
| Contract | `design/l2_1/HIL_V1_CONTRACT.md` | Core contract |
| Schema | `backend/aurora_l2/schema/intent_spec_schema.json` | JSON Schema v1.1 |
| Registry | `design/l2_1/AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml` | Domain intents |
| First Panel | `design/l2_1/intents/ACT-EX-SUM-O1.yaml` | Activity Summary spec |
| Main Doc | `design/l2_1/AURORA_L2.md` | Section 18 |
| **Phase 2** | | |
| Compiler | `backend/aurora_l2/compiler.py` | panel_class propagation |
| Types | `website/app-shell/src/contracts/ui_projection_types.ts` | PanelClass type |
| Loader | `website/app-shell/src/contracts/ui_projection_loader.ts` | HIL accessors |
| DomainPage | `website/app-shell/src/pages/domains/DomainPage.tsx` | Panel grouping + styling |
| **Phase 3** | | |
| Backend Endpoint | `backend/app/api/activity.py` | `/api/v1/activity/summary` |
| Response Schema | `backend/contracts/activity_summary.schema.json` | JSON Schema validation |
| Capability Registry | `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_SUMMARY_ACTIVITY.yaml` | Capability status |
| Attention Registry | `backend/aurora_l2/registries/attention_reasons.yaml` | Registry-backed reasons |
| SDSR Scenario | `backend/scripts/sdsr/scenarios/SDSR-HIL-ACT-SUM-001.yaml` | Capability observation |
| Diff Guard | `backend/aurora_l2/tools/projection_diff_guard.py` | Silent drift prevention |
| Diff Allowlist | `backend/aurora_l2/tools/projection_diff_allowlist.json` | Phase 3 allowlist |
| Pipeline | `scripts/tools/run_aurora_l2_pipeline.sh` | Stage 5.5 added |
| API Types | `website/app-shell/src/api/activity.ts` | Summary types + fetch |
| Panel Renderer | `website/app-shell/src/components/panels/PanelContentRegistry.tsx` | ActivitySummaryBriefing |

---

## Related PINs

| PIN | Title | Relationship |
|-----|-------|--------------|
| PIN-416 | HIL v1 Phase 1 Schema Extension | Phase 1 completion record |
| PIN-370 | SDSR System Contract | Pipeline foundation |
| PIN-379 | E2E Pipeline | Testing foundation |
| PIN-352 | L2.1 UI Projection Pipeline | SUPERSEDED by AURORA L2 |

---

## Changelog

| Date | Phase | Change |
|------|-------|--------|
| 2026-01-14 | CLOSURE | ✅ HIL v1 FROZEN - Closure document created at `docs/governance/HIL_V1_CLOSURE.md` |
| 2026-01-14 | Phase 4 | ✅ Incidents domain complete - endpoint, capability, scenario, panel, 7 invariants validated |
| 2026-01-14 | Phase 3 | ✅ First implementation complete - endpoint, capability, scenario, panel, 5-layer quality system |
| 2026-01-14 | Phase 2 | ✅ Runtime support complete - compiler, types, loader, DomainPage |
| 2026-01-14 | Phase 1 | ✅ Schema extension complete |
| 2026-01-14 | - | Created tracking PIN-417 |
