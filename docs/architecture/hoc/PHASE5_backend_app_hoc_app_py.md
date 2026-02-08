# Phase 5 Design — `backend/app/hoc/app.py` (HOC Wiring Entry)

**Date:** 2026-02-07  
**Status:** IMPLEMENTED (2026-02-08)  
**Scope:** `backend/app/hoc/app.py` + `backend/app/hoc/api/facades/**`

---

## Goal

Create one HOC wiring node so `backend/app/main.py` does not import individual HOC routers.

This file is the Phase 5 severance prerequisite and the canonical place to:
- include all HOC routers (CUS + FDR + system surfaces)
- enforce “canonical 10 domains exist” invariants (import-time checks only)

---

## Public Surface

`backend/app/hoc/app.py` should expose:

- `include_hoc(app: FastAPI) -> None`
  - Includes all HOC routers into `app` via `include_router()`.

Optional (recommended for observability/testing):
- `hoc_router: APIRouter`
  - A single APIRouter that already includes the HOC surface.
  - `include_hoc(app)` can be implemented as `app.include_router(hoc_router)`.

---

## What It Includes

1. **CUS facades** (canonical 10 domains) from:
   - `backend/app/hoc/api/facades/cus/*.py`

2. **INT facades** (internal/system surfaces) from:
   - `backend/app/hoc/api/facades/int/*.py`

3. **Founder (FDR) surfaces** from:
   - `backend/app/hoc/api/facades/fdr/*.py`

---

## Contracts (First Principles)

`backend/app/hoc/app.py`:
- imports from `backend/app/hoc/api/facades/**` only
- must not import hoc_spine, engines, drivers, or DB
- must not define endpoints (it is wiring only)

---

## Acceptance Gates

Functional:
- Route snapshot unchanged after severance
- Phase 4 proof tests still pass

Structural:
- `backend/app/main.py` contains **0** `from .hoc.api...` router imports
- `backend/app/main.py` contains **0** `app.include_router(<hoc_router>)` calls for individual HOC routers
- All HOC router inclusion happens via `include_hoc(app)`

**Evidence (2026-02-08):**
- `backend/app/hoc/app.py` exists and imports facades only.
- `backend/app/main.py` calls `include_hoc(app)` and does not include individual HOC routers.

---

## Migration Path

1. Add L2.1 facades.
2. Add `backend/app/hoc/app.py` wiring (no entrypoint changes yet).
3. Update `backend/app/main.py` to call `include_hoc(app)` and remove direct includes.
