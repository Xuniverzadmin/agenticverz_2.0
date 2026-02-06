# TODO — Iteration 3

**Date:** 2026-02-06  
**Purpose:** Track next‑iteration tasks following L2 purity completion.

---

## P1 ✅ COMPLETE (2026-02-06)

1. ✅ Validate hoc_spine authority/lifecycle checks with executable artifacts (test logs or run reports).
   - **Evidence:** `docs/architecture/hoc/P1_1_HOC_SPINE_AUTHORITY_VALIDATION_EVIDENCE.md`
   - 16/16 operation_registry tests passing
   - 0 L5/L6 direct imports in L2 (L2 purity verified)

2. ✅ Produce Phase‑2 coherence evidence: hoc_spine registry + handler verification report.
   - **Evidence:** `docs/architecture/hoc/P1_2_PHASE2_COHERENCE_EVIDENCE_REPORT.md`
   - 26 handlers, 11 bridges, 69 L2 files tracked
   - All bridge capabilities documented

## P2 — Phase-2 hoc_spine Import Audit (2026-02-06)

### Step 1-3 ✅ COMPLETE

**Evidence:** `docs/architecture/hoc/PHASE2_HOC_SPINE_IMPORT_AUDIT.md`

**Summary:**
- 68 import lines audited across 9 domains (see PHASE2 audit)
- 53 OK (services/schemas/utilities)
- 8 VIOLATIONS (orchestrator imports in L5 — requires L4 refactor)
- 7 REVIEW (authority imports in policies)

**Status Update (Iteration 3.1):**
- All L5 → L4 orchestrator/authority imports removed under strict first‑principles.
- Evidence: `docs/memory-pins/TODO_ITER3.1.md`

**Violations Identified (orchestrator in L5):**

| Domain | File | Import |
|--------|------|--------|
| activity | `L5_engines/__init__.py:33` | `run_governance_facade` |
| activity | `L5_engines/activity_facade.py:670,719,1152` | coordinators |
| incidents | `L5_engines/incident_engine.py:906` | `lessons_coordinator` |
| policies | `L5_engines/eligibility_engine.py:75` | `orchestrator.*` |
| analytics | `L5_engines/detection_facade.py:303` | `anomaly_incident_coordinator` |
| integrations | `L5_engines/cost_bridges_engine.py:50` | `create_incident_from_cost_anomaly_sync` |

**Deferred:** api_keys (gap — design needed after other violations fixed)

### Step 4-5 (Pending)

1. Convert remaining L2 files that bypass `operation_registry` (non‑registry usage) where feasible.
2. ✅ Align all Phase‑1 truth‑map artifacts into canonical `docs/architecture/hoc/` (symlink or copy audit).

## P3

1. Refresh domain canonical literature for any new L2 bridge patterns introduced in Iteration 3.

---

## Reality Update (2026-02-06)

This file is a high-level index. For detailed execution history and evidence artifacts, see:

1. `docs/memory-pins/TODO_ITER3.1.md` (Phase-2 import audit → first-principles removal of L5→hoc_spine orchestrator/authority imports)
2. `docs/memory-pins/TODO_ITER3.2.md` (L2 non-registry audit, classification, and conversion work)
3. `docs/memory-pins/TODO_ITER3.3.md` (hoc_spine import hardening + import guard tests)
4. `docs/memory-pins/TODO_ITER3.4.md` (runtime consolidation and shims)
5. `docs/memory-pins/TODO_ITER3.5.md` (sever legacy `app.services.*` imports in HOC runtime paths — plus remaining blockers)
6. `docs/memory-pins/TODO_ITER3.6.md` (global severance: remove legacy `app.services.*` imports outside `backend/app/services/**`)

**Current reality gate:** `cd backend && python3 scripts/ci/check_init_hygiene.py` reports `Blocking: 27 violations` (not green yet). The Iter3.5 scope has two actionable blockers captured in `docs/memory-pins/TODO_ITER3.5.md`.
