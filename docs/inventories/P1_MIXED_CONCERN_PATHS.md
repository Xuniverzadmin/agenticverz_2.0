# P1-3.2 Mixed-Concern Paths Inventory

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Mixed-Layer Directories | 3 | DOCUMENT |
| Files Spanning Multiple Layers | 0 | PASS |
| BLCA Violations | 0 | PASS |

**Overall Status:** Import integrity verified. Mixed-layer directories exist but do not violate layer boundaries.

---

## Mixed-Layer Directories

### 1. events/ (Mixed L3/L6)

| File | Layer | Purpose |
|------|-------|---------|
| `__init__.py` | L6 | Platform Substrate |
| `publisher.py` | L3 | Boundary Adapter |
| `redis_publisher.py` | L3 | Boundary Adapter |
| `nats_adapter.py` | L3 | Boundary Adapter |

**Analysis:**
- Package marker (`__init__.py`) declares L6
- Actual implementations are L3 adapters
- This is organizationally confusing but import-safe

**Recommendation:**
- Either move adapters to `adapters/events/`
- Or change `__init__.py` to L3

### 2. workflow/ (Mixed L4/L6)

| File | Layer | Purpose |
|------|-------|---------|
| `engine.py` | L4 | Domain Engine |
| `canonicalize.py` | L4 | Domain Engine |
| `checkpoint.py` | L4 | Domain Engine |
| `errors.py` | L4 | Domain Engine |
| `external_guard.py` | L4 | Domain Engine |
| `golden.py` | L4 | Domain Engine |
| `planner_sandbox.py` | L4 | Domain Engine |
| `policies.py` | L4 | Domain Engine |
| `health.py` | L6 | Platform Substrate |
| `logging_context.py` | L6 | Platform Substrate |
| `metrics.py` | L6 | Platform Substrate |

**Analysis:**
- Domain logic (L4) mixed with infrastructure (L6)
- L4 imports from L6 are allowed
- Organizational concern only

**Recommendation:**
- Move `health.py`, `logging_context.py`, `metrics.py` to `infra/workflow/`

### 3. optimization/ (Mixed L4/L5/L6)

| File | Layer | Purpose |
|------|-------|---------|
| `envelope.py` | L4 | Domain Engine |
| `killswitch.py` | L4 | Domain Engine |
| `coordinator.py` | L5 | Execution & Workers |
| `manager.py` | L5 | Execution & Workers |
| `audit_persistence.py` | L6 | Platform Substrate |

**Analysis:**
- Three layers coexist in one directory
- Import directions are correct (L5 can import L4, L6)
- Organizational concern only

**Recommendation:**
- Split into subdirectories:
  - `optimization/domain/` for L4
  - `optimization/execution/` for L5
  - Move persistence to `infra/optimization/`

---

## Import Integrity Check

### L2 → L6 Direct Imports (Allowed)

The following API files import directly from `app.db`:

| File | Import | Status |
|------|--------|--------|
| `api/cost_guard.py` | `from app.db import get_session` | ALLOWED |
| `api/guard.py` | `from app.db import get_session` | ALLOWED |
| `api/cost_intelligence.py` | `from app.db import ...` | ALLOWED |
| `api/status_history.py` | `from app.db import StatusHistory` | ALLOWED |
| `api/cost_ops.py` | `from app.db import get_session` | ALLOWED |
| `api/v1_proxy.py` | `from app.db import get_session` | ALLOWED |
| `api/platform.py` | `from app.db import get_session` | ALLOWED |
| `api/policy_layer.py` | `from app.db_async import ...` | ALLOWED |

**Note:** L2 can import from L6. This is by design (APIs need database access).

### Forbidden Import Patterns (None Found)

| Pattern | Description | Found |
|---------|-------------|-------|
| L4 → L2 | Domain importing API | 0 |
| L6 → L4 | Platform importing domain | 0 |
| L6 → L3 | Platform importing adapter | 0 |

---

## BLCA Verification

```
Files scanned: 708
Violations found: 0
Status: CLEAN
```

**Import boundaries are correct. BLCA passes.**

---

## No Changes Required (Phase 1)

Per Phase 1 scope ("Structure-only. No logic."):

1. **Document** mixed-layer directories (done)
2. **Do NOT extract** files during Phase 1
3. **Flag** for future cleanup

### Future Work (Phase 2+)

| Priority | Action | Impact |
|----------|--------|--------|
| Low | Split `events/` adapters to `adapters/` | 3 files |
| Low | Extract workflow infrastructure to `infra/` | 3 files |
| Low | Split `optimization/` by layer | 5 files |

---

## Acceptance Criteria

- [x] Mixed-concern directories identified
- [x] Import integrity verified (BLCA clean)
- [x] No files serving two layers (L4 infra files are L6, not dual-layer)
- [x] Recommendations documented
- [x] No structural changes made (inventory only)

---

## Conclusion

**No cross-layer contamination exists** (BLCA passes with 0 violations).

Mixed-layer directories exist for organizational convenience:
- Import directions are correct
- Files have clear single-layer assignments
- Co-location is intentional (feature cohesion)

**No blocking issues for Phase 1 completion.**
