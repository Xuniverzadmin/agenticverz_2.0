# CI Candidate Matrix

**Status:** DISCOVERY (Observational Only)
**Date:** 2025-12-30
**Reference:** PIN-250, PHASE2_COMPLETION_GATE.md

---

## Purpose

This matrix identifies **what CI signals are now possible** after Phase 2 structural alignment.

> **This is reconnaissance, not enforcement.**
> No CI checks will be added from this matrix.
> Signals are mapped to phases for future implementation.

---

## Matrix

| Invariant / Signal | Now True? | Stable? | CI Type | Phase Eligible | Notes |
|--------------------|-----------|---------|---------|----------------|-------|
| No DB writes in L2 APIs | ✅ Yes | ✅ Yes | Static grep | Phase 3 | `session.add`, `session.commit`, `session.execute` absent in api/ |
| No import-time DB connection | ✅ Yes | ✅ Yes | Import test | Phase 3 | main.py init moved to lifespan (Phase 2A) |
| Write-only services | ⚠️ Mostly | ⚠️ Medium | AST scan | Phase 3 | 8 services; some have read helpers (by design) |
| Transaction ownership in services | ✅ Yes | ✅ Yes | Grep | Phase 3 | `.commit()` only in services, not API |
| Service write boundaries | ✅ Yes | ✅ Yes | Import analysis | Phase 3 | Services don't import other services |
| Async/sync execution purity | ❌ No | ❌ No | — | Phase 3+ | recovery files: sync session in async route |
| Auth boundary purity (L3/L4) | ❌ No | ❌ No | — | Phase 2C | Hybrid auth/ not yet split |
| No circular dependencies | ✅ Yes | ✅ Yes | Import graph | Phase 3 | Zero cycles detected in Phase 1 |
| Layer import direction | ⚠️ Mostly | ⚠️ Medium | Import analysis | Phase 3 | Most correct; some L2→L5 (known debt) |
| Planner module clarity | ❌ No | ❌ No | — | Phase 2D | planner/ vs planners/ duplication |
| Worker module clarity | ❌ No | ❌ No | — | Phase 2D | worker/ vs workers/ collision |
| tasks/ module wired | ✅ Yes | ✅ Yes | Import test | Phase 3 | Wired in Phase 2A |
| jobs/ module complete | ❌ No | ⚠️ Medium | Static analysis | Phase 2D | 7 lines, documented as unscheduled |

---

## Eligible for Phase 3 CI (Dry-Run)

These signals are **stable and true** — candidates for dry-run CI that warns but never fails:

| Signal | Check Method | Implementation |
|--------|--------------|----------------|
| No DB writes in L2 | `grep -r "session\.\(add\|commit\|execute\)" backend/app/api/` | Shell script |
| No import-time DB | `python -c "from app.main import app"` + verify no connections | Import test |
| Transaction in services | `grep -r "\.commit()" backend/app/api/` should return 0 | Shell script |
| No circular deps | `import_graph_check.py` | Python script |

---

## Explicitly Blocked from CI

These signals are **unstable or untrue** — CI would encode lies:

| Signal | Why Blocked | Unblock Condition |
|--------|-------------|-------------------|
| Async/sync purity | recovery files use sync in async | Phase 3 alignment |
| Auth L3/L4 separation | auth/ is hybrid | Phase 2C completion |
| Planner module clarity | Duplication exists | Phase 2D consolidation |
| Worker module clarity | Naming collision | Phase 2D rename |

---

## CI Implementation Ladder

| Rung | Phase | Behavior | Current |
|------|-------|----------|---------|
| 1 | Discovery | Observe, record, propose | ← **HERE** |
| 2 | Dry-Run CI | Warn only, never fail | Phase 3 |
| 3 | Soft Gates | Fail new violations, grandfather existing | Mid Phase 3 |
| 4 | Hard Gates | Full enforcement | Phase 4 |

---

## Observations (No Action Required)

1. **6 signals are CI-ready** — Can implement dry-run checks
2. **4 signals are blocked** — Require structural work first
3. **3 signals are partially ready** — Need cleanup before enforcement
4. **Most valuable CI: "No DB writes in L2"** — Protects the core invariant

---

## What This Matrix Does NOT Do

- ❌ Add CI checks
- ❌ Fail any builds
- ❌ Change any code
- ❌ Fix any issues
- ❌ Enforce any rules

This is **signal reconnaissance only**.

---

## Next Steps (For Human Review)

1. Review eligible signals for Phase 3 dry-run CI
2. Confirm blocked signals should remain blocked
3. Approve governance rule addition (CI discovery after structural alignment)
4. Decide whether to proceed to Phase 3 or Phase 2C first
