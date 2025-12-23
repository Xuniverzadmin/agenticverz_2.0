# PIN-145: M28 Deletion Execution Report

**Status:** COMPLETE
**Date:** 2025-12-23
**Milestone:** M28 Unified Console (Preparation Phase)

---

## Summary

This PIN documents the execution of the M28 Exact Deletion Checklist. All 17 routes identified for deletion have been removed or archived.

---

## Deletion Statistics

| Category | Count | Status |
|----------|-------|--------|
| Demo artifacts | 3 | DELETED |
| Operator redundancy | 1 (entire file) | ARCHIVED |
| Job UIs | 2 | DELETED |
| SDK-only UI | 2 | DELETED |
| Worker duplication | 1 | DELETED |
| Metrics vanity | 1 | DELETED |
| Failure duplication | 1 (entire file) | ARCHIVED |
| Legacy redirects | 4 | DELETED |
| Dashboard shell | 1 | DELETED |
| **TOTAL** | **17** | **COMPLETE** |

---

## Backend Changes

### Files Archived (Renamed to .m28_deleted)

| File | Original Path | Reason |
|------|---------------|--------|
| `failures.py.m28_deleted` | `backend/app/api/failures.py` | Duplicates `/ops/incidents/patterns` |
| `operator.py.m28_deleted` | `backend/app/api/operator.py` | Redundant with `/ops/*` |

### Files Modified

#### `backend/app/main.py`
- Removed `failures_router` import and include
- Removed `operator_router` import and include
- Added deletion comments for traceability

#### `backend/app/api/guard.py`
- **DELETED:** `/guard/demo/seed-incident` endpoint (lines 1655-1806)
- **DELETED:** `/guard/validate/content-accuracy` endpoint (lines 1838-1887)
- Reason: Demo artifacts violate evidence integrity

#### `backend/app/api/v1_killswitch.py`
- **DELETED:** `/v1/demo/simulate-incident` endpoint (lines 584-726)
- Removed `DemoSimulationRequest`, `DemoSimulationResult` imports
- Reason: Sales demo tool, not product feature

---

## Frontend Changes

### Directories Archived (Renamed to .m28_deleted)

| Directory | Reason |
|-----------|--------|
| `pages/skills.m28_deleted` | SDK concept, not customer value |
| `pages/jobs.m28_deleted` | Simulation tools → SDK/CLI |
| `pages/failures.m28_deleted` | Duplicates `/ops/incidents/patterns` |
| `pages/metrics.m28_deleted` | Grafana mirror |
| `pages/dashboard.m28_deleted` | Shell route, merged into `/guard` |
| `pages/blackboard.m28_deleted` | Legacy naming |
| `pages/operator.m28_deleted` | All operator UI pages |

### Routes Removed (`routes/index.tsx`)

| Route | Reason |
|-------|--------|
| `/dashboard` | Merged into `/guard` |
| `/skills` | SDK concept |
| `/simulation` | SDK/CLI tool |
| `/replay` | SDK/CLI tool |
| `/failures` | Duplicates ops incidents |
| `/memory` | Legacy naming |
| `/metrics` | Grafana mirror |
| `/workers/history` | Duplication |
| `/agents` (redirect) | Dead mental model |
| `/blackboard` (redirect) | Legacy naming |
| `/jobs/*` (redirect) | Legacy naming |
| `/messaging` (redirect) | Dead feature |

### New Default Behavior

- Root `/` now redirects to `/guard` (unified console)
- Catch-all `/*` redirects to `/guard`

---

## Post-Deletion Validation

### Syntax Checks
- [x] `guard.py` - Compiles successfully
- [x] `v1_killswitch.py` - Compiles successfully
- [x] `main.py` - Compiles successfully
- [x] `routes/index.tsx` - Valid JSX structure

### Forbidden Words Check
After deletion, NONE of these words appear in active routes:
- [x] `demo` - REMOVED
- [x] `simulation` - REMOVED (only in deletion comment)
- [x] `jobs` - REMOVED (only in deletion comment)
- [x] `metrics` - REMOVED (only in deletion comment)
- [x] `operator` - REMOVED
- [x] `skills` - REMOVED (only in deletion comment)
- [x] `failures` - REMOVED (only in deletion comment)
- [x] `dashboard` - REMOVED (only in deletion comment)

---

## Recovery Instructions

All deleted files are archived with `.m28_deleted` suffix. To recover:

```bash
# Backend
mv backend/app/api/failures.py.m28_deleted backend/app/api/failures.py
mv backend/app/api/operator.py.m28_deleted backend/app/api/operator.py

# Frontend
mv website/aos-console/console/src/pages/skills.m28_deleted website/aos-console/console/src/pages/skills
# ... etc
```

Then restore imports in `main.py` and routes in `routes/index.tsx`.

---

## Next Steps (M28 Continuation)

1. **Build Unified Control Center** - Implement 4-view layout per PIN-132
2. **Actor Attribution Migration** - Add `actor_id` columns (migration 045)
3. **UnifiedSearch Component** - Cross-view search with Cmd+K
4. **MetricsStrip Component** - Top-level metrics bar

---

## Related PINs

- PIN-132: M28 Unified Console Blueprint
- PIN-140: M25 Complete - ROLLBACK_SAFE
- PIN-143: M27 Real Cost Enforcement Proof

---

## Conclusion

> Most platforms fail not because they lack features,
> but because they refuse to delete lies.
>
> This checklist removed lies.

All 17 routes deleted. No silent survivors. M28 foundation clean.
