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

## System Runtime Gaps (HOC Spine)

**Plan:** `docs/architecture/hoc/HOC_SPINE_SYSTEM_RUNTIME_GAPS_AND_PLAN.md`

**Status (2026-02-07):**
- ✅ Batch 1 complete — RunGovernanceFacade wired at startup, fail-fast getter.
- ✅ Batch 2 complete — hoc_spine driver transaction purity (ledger/decisions).
- ✅ Batch 3a complete — ActivityDiscoveryHandler now owns connection + commit.
- ✅ Batch 3b complete — AuditStore integration (Phase A.6).
- ✅ Batch C complete — `backend/app/hoc/api/infrastructure/` removed (stale copies).

**Open Tasks (tracked):**
1. Consequences expansion beyond dispatch audit (e.g., export bundle adapter wiring) — track as future hardening.

---

## Reality Update (2026-02-07)

This file is a high-level index. For detailed execution history and evidence artifacts, see:

1. `docs/memory-pins/TODO_ITER3.1.md` (Phase-2 import audit → first-principles removal of L5→hoc_spine orchestrator/authority imports)
2. `docs/memory-pins/TODO_ITER3.2.md` (L2 non-registry audit, classification, and conversion work)
3. `docs/memory-pins/TODO_ITER3.3.md` (hoc_spine import hardening + import guard tests)
4. `docs/memory-pins/TODO_ITER3.4.md` (runtime consolidation and shims)
5. `docs/memory-pins/TODO_ITER3.5.md` (sever legacy `app.services.*` imports in HOC runtime paths — plus remaining blockers)
6. `docs/memory-pins/TODO_ITER3.6.md` (global severance: remove legacy `app.services.*` imports outside `backend/app/services/**`)
7. `docs/memory-pins/TODO_ITER3.7.md` (COMPLETE: refactor `hoc/api/cus/general/agents.py` to strict L2 first principles)
8. `docs/memory-pins/TODO_ITER3.8.md` (COMPLETE: Phase 3 coherence hardening — L6 inversion removed, api_keys spine gap closed, controls L2 re-homed)
9. `docs/architecture/hoc/HOC_SPINE_SYSTEM_RUNTIME_GAPS_AND_PLAN.md` (Batch 1–3a complete, Batch 3b + Batch C deferred)

**Current reality gate (2026-02-07):** `cd backend && python3 scripts/ci/check_init_hygiene.py --ci` reports **0 blocking violations (0 known exceptions)**.

**Known exceptions status (2026-02-06):** **0 known exceptions**.
- Evidence: `docs/architecture/hoc/KNOWN_EXCEPTIONS_ELIMINATION_EVIDENCE.md`

**L2 non-registry classification (re-verified 2026-02-07):** 69 total L2 token files; 50 registry dispatch; 19 justified non-registry.
- Evidence: `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md`
- Exceptions: `docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_EXCEPTIONS.md`

**Routing sanity (2026-02-06):** **0 duplicate (path, method) route pairs** on the FastAPI app.
- `/health` is owned by HOC L2 (`backend/app/hoc/api/cus/general/health.py`); `backend/app/main.py` does not define `/health`.
- `/api/v1/*` is now legacy-only (`410 Gone`), so versioned collisions are eliminated at the routing layer.
- Pytest guard: `backend/tests/hoc_spine/test_no_duplicate_routes.py`

**/api/v1 deprecation + /health ownership (2026-02-06):** `/api/v1/*` is legacy (410); `/health` is owned by HOC L2 and DB validation lives in hoc_spine.
- Evidence: `docs/architecture/hoc/API_V1_DEPRECATION_AND_HEALTH_OWNERSHIP_EVIDENCE.md`
