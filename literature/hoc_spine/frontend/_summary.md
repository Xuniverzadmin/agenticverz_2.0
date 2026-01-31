# Frontend — RELOCATED

**Status:** RELOCATED
**Date:** 2026-01-30
**Previous path:** `backend/app/hoc/hoc_spine/frontend/`
**New path:** `frontend/app/projections/`

---

## Decision

`hoc_spine/frontend/` does NOT belong in backend. Projection code belongs in the frontend application tree.

**Action taken:** Entire subtree moved to `frontend/app/`. Import in `orchestrator/__init__.py` commented out (broken intentionally). Will be re-wired during L1 design. hoc_spine script count adjusted from 66 to 65.
