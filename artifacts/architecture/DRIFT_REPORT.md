# Architecture Drift Report

**Generated:** 2026-01-02
**Status:** CLEAN
**BLCA:** 0 violations

---

## Summary

| Metric | Value | Target | Status |
|--------|------:|-------:|--------|
| Total files scanned | 326 | - | - |
| Total routes | 336 | - | - |
| Layer header coverage | 71.5% | 70% | ✅ PASS |
| Declared files | 233 | - | - |
| Blocking issues | 0 | 0 | ✅ PASS |
| Warnings | 2 | < 5 | ✅ PASS |

---

## Layer Breakdown

| Layer | Files | Purpose |
|-------|------:|---------|
| L2 | 34 | Product APIs |
| L3 | 27 | Boundary Adapters |
| L4 | 165 | Domain Engines |
| L5 | 24 | Execution & Workers |
| L6 | 76 | Platform Substrate |

---

## Route Categories

| Category | Routes | Percentage |
|----------|-------:|----------:|
| core | 45 | 13.4% |
| monitoring | 39 | 11.6% |
| governance | 120 | 35.7% |
| operations | 36 | 10.7% |
| supporting | 30 | 8.9% |
| internal | 35 | 10.4% |
| unassigned | 31 | 9.2% |

---

## Issues

**None.** Architecture is consistent with declaration.

---

## Warnings

### 1. Routes Without Frontend Category (31)

These routes are not yet categorized for frontend journey planning:

- Routes in `legacy_routes` domain
- Routes in `unknown` domain (need classification)

**Action:** Classify during frontend planning phase.

### 2. Files Without Declared Purpose (107)

Files missing `FEATURE_INTENT` or `Role` header comments.

**Action:** Add purpose declarations during next governance sweep.

**Note:** This is a documentation gap, not a structural issue.

---

## Validation Checks

| Check | Result | Notes |
|-------|--------|-------|
| No UNKNOWN layers | ✅ PASS | All files classified |
| All layers have files | ✅ PASS | L2-L6 populated |
| Layer coverage > 70% | ✅ PASS | 71.5% |
| L2 routes exist | ✅ PASS | 34 files with routes |
| API inventory complete | ✅ PASS | 336 routes extracted |
| BLCA clean | ✅ PASS | 0 violations |

---

## Reconciliation Status

```
Architecture Declaration  ←→  Repo State
         ↓                        ↓
    ARCH_DECLARATION.md      component_inventory.json
    L2_API_CONTRACT.md       L2_API_INVENTORY.json
         ↓                        ↓
         └────── RECONCILED ──────┘
```

**Conclusion:** The declared architecture matches the actual codebase state.

---

## Next Steps

1. **Frontend planning can proceed** — Architecture is stable
2. **Classify 31 unassigned routes** — During journey mapping
3. **Add purpose to 107 files** — Lower priority, documentation

---

## Artifacts Produced

| Artifact | Path | Purpose |
|----------|------|---------|
| ARCH_SCOPE.yaml | docs/architecture/ | Extraction scope |
| component_inventory.json | artifacts/architecture/ | Full component list |
| ARCH_GRAPH.md | docs/architecture/ | Visual connections |
| ARCH_DECLARATION.md | docs/architecture/ | Frozen declaration |
| L2_API_INVENTORY.json | artifacts/apis/ | Route inventory |
| L2_API_CONTRACT.md | docs/apis/ | Frontend contracts |
| DRIFT_REPORT.json | artifacts/architecture/ | Machine-readable |
| DRIFT_REPORT.md | artifacts/architecture/ | Human-readable |

---

## Validation Command

```bash
# Run BLCA
python3 scripts/ops/layer_validator.py --backend --ci

# Re-run extraction
python3 /tmp/extract_architecture_v2.py
python3 /tmp/extract_l2_api.py
```

---

**Signed:** Architecture extraction complete, ready for frontend handoff.
