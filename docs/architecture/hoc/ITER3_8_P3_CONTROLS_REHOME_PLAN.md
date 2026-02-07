# ITER3.8 P3 — Re-Home Controls L2 Surface (Design + Execution Notes)

**Created:** 2026-02-07  
**Status:** READY TO EXECUTE  
**Owner:** Claude (implementation)  
**Goal:** Make the canonical 10 CUS domains impossible to miss by re-homing Controls L2 endpoints into `backend/app/hoc/api/cus/controls/`.

---

## First Principles

- Canonical CUS domains are non-optional: `overview`, `activity`, `incidents`, `policies`, `controls`, `logs`, `analytics`, `integrations`, `api_keys`, `account`.
- L2 is HTTP boundary only. It may call L4 via `registry.execute(...)`.
- No workarounds: do not introduce allowlists, duplicate logic, or long-lived shims unless explicitly commanded.
- No assumptions: every “done” requires gates + evidence scans.

---

## Current Reality (Pre-Execution)

- Controls L2 endpoints currently live at `backend/app/hoc/api/cus/policies/controls.py`.
- `backend/app/hoc/api/cus/controls/` is absent/empty (canonical domain surface missing).
- Entry point wiring is in `backend/app/main.py` (imports + `app.include_router(...)`).

---

## Target Design

### Canonical location

- New canonical L2 module:
  - `backend/app/hoc/api/cus/controls/controls.py`

### Domain folder semantics

- `backend/app/hoc/api/cus/controls/**` contains only Controls endpoints.
- The URL surface does **not** change unless explicitly commanded:
  - The router `prefix=` and routes remain identical to current behavior.

### Entry point

- `backend/app/main.py` must import Controls router from:
  - `from .hoc.api.cus.controls.controls import router as controls_router`
- and include it with `app.include_router(controls_router)` in the same place as before.

---

## Execution Plan (Streamed)

### Batch 0 — Preflight Evidence (Read-only)

1. Inventory imports that reference the current location:
   - `rg -n "hoc\\.api\\.cus\\.policies\\.controls|cus/policies/controls\\.py" backend/app`
2. Capture current route surface for `/controls` (and tags if needed):

```bash
cd backend
python3 - <<'PY'
from app.main import app
hits=[(r.path, sorted(getattr(r, "methods", []) or []), getattr(getattr(r, "endpoint", None), "__module__", "")) for r in app.routes if getattr(r, "path", "").startswith("/controls")]
print("controls_routes", len(hits))
for p,m,mod in sorted(hits):
    print(p, m, mod)
PY
```

### Batch 1 — Re-home Module (Minimal change)

1. Create directory `backend/app/hoc/api/cus/controls/` (and `__init__.py` only if needed by existing package conventions).
2. Move the file:
   - `git mv backend/app/hoc/api/cus/policies/controls.py backend/app/hoc/api/cus/controls/controls.py`
3. Fix any broken relative imports inside the moved module (only if they exist).
4. Update all imports referencing old module path to the new module path.

### Batch 2 — Rewire Entry Point

1. Update `backend/app/main.py`:
   - Replace old import for controls router with the new canonical import.
   - Ensure `include_router` call remains present and unchanged.

### Batch 3 — Proof + Truth-Map Updates (Docs)

Update these artifacts to reflect the new reality:

1. `docs/architecture/hoc/CUS_HOC_SPINE_COMPONENT_COVERAGE.md`
   - Controls should show non-zero L2 files under `cus/controls/`.
   - Remove/adjust the note about controls living under `policies/`.
2. `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md`
   - Replace `policies/controls.py` in the registry dispatch list with `controls/controls.py`.
   - Re-run the doc’s reproducible scan to ensure file lists match.
3. `docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_EXCEPTIONS.md`
   - Should remain consistent after the move (counts likely unchanged).

---

## Gates (Run After Each Batch That Changes Code)

```bash
cd backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py
PYTHONPATH=. pytest -q tests/hoc_spine/test_no_duplicate_routes.py
```

Acceptance scans:

```bash
rg -n "hoc\\.api\\.cus\\.policies\\.controls" backend/app || true
```

Route stability (post-change must match pre-change output):

```bash
cd backend
python3 - <<'PY'
from app.main import app
hits=[(r.path, sorted(getattr(r, "methods", []) or []), getattr(getattr(r, "endpoint", None), "__module__", "")) for r in app.routes if getattr(r, "path", "").startswith("/controls")]
print("controls_routes", len(hits))
for p,m,mod in sorted(hits):
    print(p, m, mod)
PY
```

---

## Output Contract (Claude)

After each batch, respond with:
- gates results
- `rg` residual count for old imports
- updated `/controls` route inventory (count + list)

Do not update any docs unless the user explicitly commands “update docs” for this task (this plan is an explicit doc update authorization only when executing Batch 3).

