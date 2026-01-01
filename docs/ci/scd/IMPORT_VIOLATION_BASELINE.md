# Import Violation Baseline

**STATUS: OBSERVATION COMPLETE (Phase-1.5)**

**Date Generated:** 2026-01-01
**Purpose:** Baseline for Wave-1 Import Direction Enforcement
**Reference:** WAVE_1_IMPORT_DIRECTION_PLAN.md

---

## 1. Baseline Summary

```
IMPORT VIOLATION BASELINE

Scan Date: 2026-01-01
Tool Used: scripts/ops/layer_validator.py (BLCA)
Scan Scope: backend/**/*.py
Files Scanned: 599

BLCA-Detected Violations: 0
Governance-Model Violations: ~19 (per SCD evidence)
```

---

## 2. Critical Finding: BLCA-Governance Discrepancy

### 2.1 The Discrepancy

| Source | L5 Allowed Imports | L2 Forbidden Imports |
|--------|-------------------|---------------------|
| **CLAUDE.md (Governance)** | L6 only | L5 |
| **BLCA (layer_validator.py)** | L4, L5, L6 | L5 |

The BLCA allows L5→L4 imports, but the governance model says L5 should only import L6.

### 2.2 BLCA Configuration (Current)

From `scripts/ops/layer_validator.py:146-154`:

```python
ALLOWED_IMPORTS = {
    "L1": {"L1", "L2", "L3"},
    "L2": {"L2", "L3", "L4", "L6"},  # L5 forbidden
    "L3": {"L3", "L4", "L6"},
    "L4": {"L4", "L5", "L6"},
    "L5": {"L4", "L5", "L6"},        # L4 ALLOWED (mismatch!)
    "L6": {"L6"},
    "L7": {"L1", "L2", "L3", "L4", "L5", "L6", "L7"},
}
```

### 2.3 Governance Model (CLAUDE.md)

```
| Layer | Name | Allowed Imports |
|-------|------|-----------------|
| L5 | Execution & Workers | L6 only |
```

### 2.4 Resolution Path

This discrepancy must be resolved before Wave-1 CI enforcement can work:

| Option | Description | Recommendation |
|--------|-------------|----------------|
| A | Update BLCA to match governance (L5 → L6 only) | Requires fixing existing violations first |
| B | Update governance to match BLCA (L5 → L4, L6) | Weakens layer boundaries |
| C | Grandfather discrepancy, enforce for new code | RECOMMENDED for Phase-1.5 |

**Decision Required:** Human must choose resolution path.

---

## 3. Known Violations (From SCD Evidence)

These violations were documented during Phase-1 SCD but are NOT detected by BLCA due to the discrepancy:

### 3.1 L5→L4 Violations (Not Enforced)

| File | Line | Import | Gap ID |
|------|------|--------|--------|
| `worker/runner.py` | 379-384 | `from ..planners import *` | GAP-L4L5-001 |
| `worker/runner.py` | 379-384 | `from ..memory import *` | GAP-L4L5-001 |

**Note:** These are identified in `SCD-L4-L5-BOUNDARY.md` but BLCA allows them.

### 3.2 L2→L5 Violations (Enforced)

BLCA **does** enforce L2→L5 violations. Current status:

| File | Status | Notes |
|------|--------|-------|
| `api/runtime.py` | CLEAN | Header states: "Forbidden Imports: L1, L5" |

The L2→L5 violations documented in GAP-L2L4-002 may have been fixed by Phase F-3 refactoring.

---

## 4. Files with Layer Headers

A sample of files with explicit layer declarations:

| File | Declared Layer | Allowed Imports | Forbidden Imports |
|------|----------------|-----------------|-------------------|
| `worker/runner.py` | L5 | L6 | L1, L2, L3 |
| `api/runtime.py` | L2 | L3, L4, L6 | L1, L5 |
| `commands/runtime_command.py` | L4 | L5, L6 | - |
| `adapters/runtime_adapter.py` | L3 | L4, L6 | - |

**Observation:** File headers declare stricter rules than BLCA enforces.

---

## 5. Baseline for Grandfathering

### 5.1 Violations to Grandfather (If Option A Chosen)

If BLCA is updated to match governance, these existing L5→L4 imports would become violations:

| File | Import Pattern | Count |
|------|---------------|-------|
| `worker/runner.py` | `from ..contracts.*` | TBD |
| `worker/runner.py` | `from ..planners.*` | TBD |
| `worker/runner.py` | `from ..utils.*` | TBD |
| `worker/pool.py` | TBD | TBD |

### 5.2 Baseline Generation (Deferred)

Full baseline scan requires:
1. Resolving BLCA-governance discrepancy
2. Running updated BLCA
3. Capturing all violations

**Current state:** Cannot generate accurate baseline until discrepancy resolved.

---

## 6. Open Questions (Human Decision Required)

| # | Question | Impact |
|---|----------|--------|
| 1 | Should BLCA match governance (L5 → L6 only)? | Determines baseline size |
| 2 | If yes, should existing violations be grandfathered? | Determines rollout strategy |
| 3 | Should file headers override BLCA configuration? | Determines enforcement mechanism |

---

## 7. Wave-1 Implications

### 7.1 What Can Proceed

- L2→L5 enforcement (BLCA already enforces this)
- Undeclared layer warnings (files without `# Layer:` header)

### 7.2 What Is Blocked

- L5→L4 enforcement (requires BLCA update or governance change)
- Accurate baseline generation (requires discrepancy resolution)

### 7.3 Recommended Wave-1 Scope Adjustment

Given the discrepancy, Wave-1 should be scoped to:

| In Scope | Out of Scope (Wave-2) |
|----------|----------------------|
| L2→L5 enforcement | L5→L4 enforcement |
| Undeclared layer warnings | BLCA configuration update |
| New violation blocking | Existing violation baseline |

---

## 8. Evidence References

| Document | Content |
|----------|---------|
| `SCD-L4-L5-BOUNDARY.md` | L5→L4 gap documentation |
| `SCD-L2-L4-BOUNDARY.md` | L2→L5 gap documentation |
| `SCE_RUN_phase1-initial.json` | Layer assignment evidence |
| `WAVE_1_IMPORT_DIRECTION_PLAN.md` | Wave-1 planning document |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-01 | Initial baseline observation (Phase-1.5) |

---

**OBSERVATION COMPLETE — HUMAN DECISION REQUIRED FOR RESOLUTION**
