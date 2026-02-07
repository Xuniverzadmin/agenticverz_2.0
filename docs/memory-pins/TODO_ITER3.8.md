# TODO — Iteration 3.8 (Phase 3 Coherence Hardening)

**Created:** 2026-02-07  
**Last verified:** 2026-02-07  
**Status:** COMPLETE ✅  
**Purpose:** Continue Coherence Phase 3: stabilize canonical CUS domains + hoc_spine under strict layer rules.

---

## Reality Anchors (Evidence, 2026-02-07)

- L2 CUS coverage: `docs/architecture/hoc/CUS_HOC_SPINE_COMPONENT_COVERAGE.md`
  - 69 L2 APIRouter token files
  - 50 registry dispatch, 19 justified non-registry
- hoc_spine import matrix (CUS domains): `docs/architecture/hoc/HOC_SPINE_IMPORT_MATRIX_CUS.md`
  - `api_keys` domain has **0** `hoc_spine` imports (tracked as GAP)
  - 1 L6→L4 inversion detected: `policies/L6_drivers/policy_enforcement_write_driver.py` imports `hoc_spine.orchestrator.operation_registry`

---

## P1 — Fix L6 → L4 Inversion (Strict)

**Problem:** L6 drivers must not call L4 (`operation_registry`) or own orchestration.

**Target:** `backend/app/hoc/cus/policies/L6_drivers/policy_enforcement_write_driver.py` (currently imports `app.hoc.cus.hoc_spine.orchestrator.operation_registry`).

**Status:** COMPLETE ✅ (2026-02-07)

**First-principles fix:**
- Move registry dispatch to L4 handler (or L5 engine), not L6.
- Make L6 driver pure data access: accept `session`/`conn` and execute inserts only.

**Acceptance gates:**
- `rg -n "hoc_spine\\.orchestrator\\.operation_registry" backend/app/hoc/cus` → 0 matches outside hoc_spine itself (exit 1)
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci` → PASS
- `cd backend && PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py` → PASS

Optional hardening (if approved):
- Add a CI hygiene rule that blocks `hoc_spine.orchestrator` / `hoc_spine.authority` imports inside any `L6_drivers/**`.

---

## P2 — Canonical Domain Gap: `api_keys` hoc_spine Integration

**Reality:** `api_keys` has `L5_engines/` + `L6_drivers/` but imports **nothing** from `hoc_spine` today.

**Policy:** Canonical 10 CUS domains are non-optional; a “zero hoc_spine imports” domain is a coherence gap to design + implement.

**Work:**
- Audit `api_keys` domain end-to-end wiring:
  - L2 router(s) that expose API-key behavior
  - L4 handler(s) that own the operations
  - L5 engine(s) and L6 driver(s) used
- Decide the minimal required `hoc_spine` dependencies for `api_keys`:
  - Authority policy integration (RBAC + public paths)
  - Governance utilities (time, UUID, audit)
- Implement the minimal integration and refresh the matrix artifact.

**Acceptance gates:**
- `docs/architecture/hoc/HOC_SPINE_IMPORT_MATRIX_CUS.md` shows `api_keys` non-zero (post-design).
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci` → PASS

**Status:** COMPLETE ✅ (2026-02-07)

**Evidence:**
- `backend/app/hoc/cus/api_keys/L5_engines/keys_engine.py` now imports and uses `app.hoc.cus.hoc_spine.services.time.utc_now` instead of `datetime.now(timezone.utc)`.
- `docs/architecture/hoc/HOC_SPINE_IMPORT_MATRIX_CUS.md` shows `api_keys` with non-zero hoc_spine imports.
- Gates: CI hygiene PASS; `/api/v1` legacy-only pytest PASS.

---

## P3 — Controls Domain Shape (Optional Decision)

**Reality:** `backend/app/hoc/api/cus/controls/` has 0 L2 routers; Controls endpoints live under `backend/app/hoc/api/cus/policies/controls.py`.

**Decision needed (user):**
- Keep controls as a sub-surface under `policies/`; or
- Create `backend/app/hoc/api/cus/controls/` L2 routers and re-home endpoints.

---

## Current Status

- P1: COMPLETE ✅
- P2: COMPLETE ✅
- P3: SELECTED (user chose re-home to `backend/app/hoc/api/cus/controls/`) → READY
  - Execution plan: `docs/architecture/hoc/ITER3_8_P3_CONTROLS_REHOME_PLAN.md`

**P3 Status:** COMPLETE ✅ (Batches 1+2) — 2026-02-07  
Gates: CI hygiene PASS; `/api/v1` legacy-only PASS; no duplicate routes PASS.  
Controls routes: 6, module now `app.hoc.api.cus.controls.controls`.
