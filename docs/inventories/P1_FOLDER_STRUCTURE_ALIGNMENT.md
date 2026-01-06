# P1-3.1 Folder Structure Alignment Assessment

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Layer-Aligned Directories | 35 | PASS |
| Duplicate-Named Directories | 2 pairs | FLAG |
| Unclear-Purpose Directories | 5 | REVIEW |
| BLCA Violations | 0 | PASS |

**Overall Status:** Structure is functional (0 BLCA violations). Naming could be improved.

---

## Layer Architecture (L1-L8)

| Layer | Name | Backend Directories |
|-------|------|---------------------|
| L1 | Product Experience | (frontend only) |
| L2 | Product APIs | `api/` |
| L3 | Boundary Adapters | `adapters/` |
| L4 | Domain Engines | `services/`, `models/`, `auth/`, `workflow/`, etc. |
| L5 | Execution & Workers | `worker/`, `workers/`, `jobs/`, `tasks/` |
| L6 | Platform Substrate | `infra/`, `db.py`, `storage/`, `stores/` |
| L7 | Ops & Deployment | (scripts, systemd) |
| L8 | Catalyst / Meta | (tests, CI) |

---

## Directory Classification

### L2 - Product APIs
| Directory | Files | Status |
|-----------|-------|--------|
| `api/` | 43 | ALIGNED |

### L3 - Boundary Adapters
| Directory | Files | Status |
|-----------|-------|--------|
| `adapters/` | 37 | ALIGNED |

### L4 - Domain Engines
| Directory | Purpose | Status |
|-----------|---------|--------|
| `services/` | Business logic | ALIGNED |
| `models/` | Domain models | ALIGNED |
| `auth/` | Authorization engine | ALIGNED |
| `workflow/` | Workflow engine | ALIGNED |
| `skills/` | Skill implementations | ALIGNED |
| `agents/` | Agent domain | ALIGNED |
| `routing/` | CARE routing | ALIGNED |
| `costsim/` | Cost simulation | ALIGNED |
| `memory/` | Memory domain | ALIGNED |
| `policy/` | Policy engine | ALIGNED |
| `discovery/` | Discovery ledger | ALIGNED |
| `learning/` | Learning pipeline | ALIGNED |
| `optimization/` | Optimization engine | ALIGNED |
| `predictions/` | Prediction plane | ALIGNED |
| `domain/` | Domain utilities | ALIGNED |
| `traces/` | Trace handling | ALIGNED |
| `contracts/` | Domain contracts | ALIGNED |
| `integrations/` | Integration platform | ALIGNED |

### L5 - Execution & Workers
| Directory | Purpose | Status |
|-----------|---------|--------|
| `worker/` | Worker runtime | ALIGNED |
| `workers/` | Worker implementations | **DUPLICATE** |
| `jobs/` | Job definitions | ALIGNED |
| `tasks/` | Task definitions | ALIGNED |

### L6 - Platform Substrate
| Directory | Purpose | Status |
|-----------|---------|--------|
| `infra/` | Infrastructure | ALIGNED |
| `storage/` | Storage abstraction | ALIGNED |
| `stores/` | Store implementations | **REVIEW** |
| `middleware/` | HTTP middleware | ALIGNED |
| `observability/` | Metrics/tracing | ALIGNED |
| `secrets/` | Secret management | ALIGNED |
| `security/` | Security utilities | ALIGNED |

### Unclear Purpose
| Directory | Issue | Recommendation |
|-----------|-------|----------------|
| `planner/` | Singular naming | Merge with `planners/` |
| `planners/` | Plural naming | Merge with `planner/` |
| `commands/` | CLI or domain? | Clarify layer |
| `events/` | Domain or infra? | Clarify layer |
| `runtime/` | Overlaps with `worker/runtime/` | Clarify ownership |
| `specs/` | Test specs or domain? | Clarify layer |
| `utils/` | Generic utilities | Review for L4/L6 split |
| `config/` | Configuration | Clarify layer |
| `data/` | Static data | Clarify purpose |
| `schemas/` | API schemas | Clarify layer (L2 or L4) |

---

## Duplicate-Named Directory Pairs

### 1. worker/ vs workers/

| Directory | Purpose | Files |
|-----------|---------|-------|
| `worker/` | Worker runtime engine | Main worker logic |
| `workers/` | Worker implementations | `business_builder/` |

**Analysis:** Different purposes but confusing naming.

**Recommendation:** Consider renaming:
- `worker/` → `worker_runtime/` or keep as primary
- `workers/` → Move contents to `worker/implementations/`

### 2. planner/ vs planners/

| Directory | Purpose | Files |
|-----------|---------|-------|
| `planner/` | Planner abstraction | `__init__.py` |
| `planners/` | Planner implementations | `__init__.py` |

**Analysis:** Likely intentional abstraction/implementation split.

**Recommendation:** Document as intentional or merge.

---

## Alignment Verification

### BLCA Status
```
Files scanned: 708
Violations found: 0
Status: CLEAN
```

**Import boundaries are correct despite naming inconsistencies.**

---

## Recommendations

### No Changes Required (Phase 1)

Per Phase 1 scope ("Inventory, classification, quarantine, and structural alignment only"):

1. **Document** the naming inconsistencies (done)
2. **Flag** duplicate directories for future cleanup
3. **Do NOT rename** during Phase 1 - requires import updates

### Future Work (Phase 2+)

| Priority | Action | Impact |
|----------|--------|--------|
| Low | Merge `planner/` and `planners/` | 2 directories |
| Low | Clarify `worker/` vs `workers/` | Documentation |
| Low | Add layer headers to unclear directories | 5 directories |

---

## Acceptance Criteria

- [x] Every directory classified to a layer
- [x] Duplicate-named directories identified
- [x] Unclear-purpose directories flagged
- [x] BLCA verification passed (0 violations)
- [x] No structural changes made (inventory only)

---

## Conclusion

**The folder structure is functionally correct** (BLCA passes with 0 violations).

Naming inconsistencies exist but do not affect runtime:
- 2 duplicate-named directory pairs
- 5 unclear-purpose directories

**No blocking issues for Phase 1 completion.**
