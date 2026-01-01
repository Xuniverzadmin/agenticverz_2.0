# Wave-1: Import Direction Enforcement Plan

**STATUS: PLANNING — NO EXECUTION**

**Date:** 2026-01-01
**Phase:** 1.5 (Signal Promotion Planning)
**Wave:** 1 of 4
**Scope:** Layer import direction enforcement

---

## 1. Wave-1 Summary

```
WAVE-1: IMPORT DIRECTION ENFORCEMENT

Purpose: Prevent layer boundary violations via CI enforcement
Scope:   3 gaps → 1 new CI job
Impact:  Catches L5→L4, L2→L5, and other illegal imports before merge
```

---

## 2. Wave-1 Candidates

### 2.1 Gaps Addressed

| Gap ID | Boundary | Description | Current State |
|--------|----------|-------------|---------------|
| GAP-L8A-005 | L8↔All | No CI check for layer import direction | DOCUMENTED |
| GAP-L4L5-004 | L4↔L5 | No CI check for L5→L4 import direction | DOCUMENTED |
| GAP-L2L4-004 | L2↔L4 | No CI check for L2→L3→L4 import direction | DOCUMENTED |

### 2.2 Signals Affected

| Signal | Current Enforcement | Proposed Enhancement |
|--------|---------------------|---------------------|
| SIG-005 (integration-integrity) | LIT/BIT tests | Add layer import validation |
| NEW: SIG-023 | Does not exist | `layer-import-check.yml` |

### 2.3 Why Wave-1 First

1. **Highest Signal-to-Noise:** Import violations are unambiguous
2. **No False Positives:** Either an import violates the layer model or it doesn't
3. **Foundation for Wave-2:** Adapter creation requires knowing what's wrong
4. **Already Tooled:** BLCA (layer_validator.py) exists, just not in CI

---

## 3. Promotion Criteria

### 3.1 General Promotion Criteria

A signal is eligible for promotion when:

| Criterion | ID | Description |
|-----------|-----|-------------|
| **Definability** | PC-001 | The violation can be mechanically defined |
| **Detectability** | PC-002 | The violation can be detected without human judgment |
| **Actionability** | PC-003 | The violation can be fixed by the developer |
| **Stability** | PC-004 | The check produces consistent results (same commit = same result) |
| **Ownership** | PC-005 | The signal has a documented owner |

### 3.2 Wave-1 Specific Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| PC-001 (Definability) | SATISFIED | Layer model defined in L1-L8 architecture |
| PC-002 (Detectability) | SATISFIED | BLCA (layer_validator.py) detects violations |
| PC-003 (Actionability) | SATISFIED | Developer can change import or create adapter |
| PC-004 (Stability) | SATISFIED | AST-based, deterministic |
| PC-005 (Ownership) | SATISFIED | SIG-005 owned by Maheshwar VM |

---

## 4. Layer Import Rules (Reference)

### 4.1 Layer Model

| Layer | Name | Allowed Imports |
|-------|------|-----------------|
| L1 | Product Experience (UI) | L2 only |
| L2 | Product APIs | L3, L4, L6 |
| L3 | Boundary Adapters | L4, L6 |
| L4 | Domain Engines | L5, L6 |
| L5 | Execution & Workers | L6 only |
| L6 | Platform Substrate | None (leaf) |
| L7 | Ops & Deployment | L6 |
| L8 | Catalyst / Meta | Any (tests) |

### 4.2 Violation Types

| Violation | Example | Severity |
|-----------|---------|----------|
| Upward Import | L5 imports L4 | ERROR |
| Skip Layer | L2 imports L5 (skipping L3/L4) | ERROR |
| Circular Dependency | L4 imports L2 | ERROR |
| Undeclared Layer | File without `# Layer: L{x}` header | WARNING |

### 4.3 Known Violations (Current State)

From SCE evidence (`SCE_RUN_phase1-initial.json`):

| Pattern | Count | Example |
|---------|-------|---------|
| L5→L4 | 16 | `worker/runner.py` imports `planners`, `memory` |
| L2→L5 | 3 | `api/runtime.py` imports worker modules |
| L8→L4 | 140 | Tests importing domain modules (ALLOWED) |

---

## 5. Proposed CI Job

### 5.1 Job Specification (Planning Only)

```yaml
# PLANNING ONLY — NOT FOR EXECUTION

name: Layer Import Check
id: SIG-023

trigger:
  - push (main, develop)
  - PR (main, develop)
  paths:
    - 'backend/**/*.py'

enforcement: BLOCKING

job_steps:
  - name: Run BLCA
    command: python3 scripts/ops/layer_validator.py --backend --ci

  - name: Check violations
    condition: exit_code != 0
    action: fail_job

  - name: Report
    output: violation_count, violation_list
```

### 5.2 Owner Assignment (Proposed)

| Field | Value |
|-------|-------|
| Signal ID | SIG-023 |
| Name | Layer Import Check |
| Owner | Maheshwar VM (Founder / System Owner) |
| Classification | BLOCKING |
| Failure Mode | Hard fail - blocks merge |

---

## 6. Rollout Strategy (Planning Only)

### 6.1 Phased Rollout

| Phase | Mode | Duration | Purpose |
|-------|------|----------|---------|
| Phase A | WARNING | 1 week | Discover all violations, no blocking |
| Phase B | SOFT BLOCK | 1 week | Block new violations only |
| Phase C | HARD BLOCK | Ongoing | Block all violations |

### 6.2 Warning Mode Behavior

```
LAYER IMPORT WARNING (not blocking)

The following import violations were detected:

  - backend/app/worker/runner.py:379
    L5 imports L4: from ..planners import get_planner

  - backend/app/api/runtime.py:45
    L2 imports L5: from ..worker.pool import WorkerPool

These will become blocking errors in Phase B.
To fix: Create L3 adapter or restructure imports.

Reference: docs/ci/scd/WAVE_1_IMPORT_DIRECTION_PLAN.md
```

### 6.3 Soft Block Behavior

```
LAYER IMPORT VIOLATION (blocking new violations)

Your changes introduce new layer violations:

  - backend/app/api/new_endpoint.py:12
    L2 imports L5: from ..worker.runner import RunRunner

This merge is blocked. Fix the violation before proceeding.
Existing violations (grandfathered): 19

Reference: docs/ci/scd/WAVE_1_IMPORT_DIRECTION_PLAN.md
```

---

## 7. Existing Violation Handling

### 7.1 Baseline Strategy

| Strategy | Description | Recommendation |
|----------|-------------|----------------|
| **Grandfather** | Existing violations allowed, new blocked | RECOMMENDED |
| **Fix First** | All violations must be fixed before enabling | NOT RECOMMENDED |
| **Accept** | Some violations accepted permanently | CASE-BY-CASE |

### 7.2 Grandfathered Violations

These violations exist in the codebase and will be grandfathered:

| File | Violation | Reason for Grandfather |
|------|-----------|----------------------|
| `worker/runner.py:379-384` | L5→L4 (planners, memory) | Documented in GAP-L4L5-001 |
| `api/runtime.py` | L2→L5 | Documented in GAP-L2L4-002 |
| (others TBD) | | Baseline scan required |

### 7.3 Baseline Generation (Planning)

**STATUS:** Observation complete — discrepancy found

```
BASELINE OBSERVATION RESULT

Scan Date: 2026-01-01
Files Scanned: 599
BLCA-Detected Violations: 0

CRITICAL FINDING: BLCA allows L5→L4, but governance says L5→L6 only.
                  Resolution required before baseline can be accurate.

See: docs/ci/scd/IMPORT_VIOLATION_BASELINE.md
```

Before Phase A, the BLCA-governance discrepancy must be resolved:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| A | Update BLCA to match governance | Requires fixing ~16 L5→L4 imports |
| B | Update governance to match BLCA | Weakens layer model |
| C | Grandfather discrepancy | Inconsistent enforcement |

**Human decision required.**

---

## 8. Dependencies

### 8.1 Wave-1 Prerequisites

| Prerequisite | Status | Notes |
|--------------|--------|-------|
| Phase-1 Ratified | COMPLETE | 2026-01-01 |
| BLCA exists | COMPLETE | `scripts/ops/layer_validator.py` |
| Layer model documented | COMPLETE | L1-L8 in CLAUDE.md |
| CI infrastructure ready | COMPLETE | GitHub Actions |

### 8.2 Wave-1 → Wave-2 Dependency

Wave-2 (Adapter Creation) depends on Wave-1:

```
Wave-1 identifies violations
           ↓
Wave-2 creates adapters to fix them
           ↓
Wave-1 validates adapters work
```

---

## 9. Success Metrics

### 9.1 Wave-1 Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Violations detected | 100% of known | Compare against SCE evidence |
| False positives | 0 | Manual review of first run |
| CI stability | Same commit = same result | 3 consecutive identical runs |
| Rollout complete | Phase C active | CI enforcement enabled |

### 9.2 Failure Criteria

| Condition | Action |
|-----------|--------|
| False positive rate > 5% | Pause rollout, refine rules |
| CI flakiness detected | Pause rollout, investigate |
| Developer friction too high | Extend Phase A duration |

---

## 10. Scope Freeze Proposal

### 10.1 What Is In Scope

| Item | In Scope? |
|------|-----------|
| Layer import direction checking | YES |
| Python files in `backend/` | YES |
| BLCA as detection mechanism | YES |
| Grandfathering existing violations | YES |
| Phased rollout (A→B→C) | YES |

### 10.2 What Is Out of Scope

| Item | Out of Scope? | Reason |
|------|---------------|--------|
| Fixing existing violations | YES | Wave-2 |
| Creating adapters | YES | Wave-2 |
| Frontend import checking | YES | Future wave |
| TypeScript/JS layer checking | YES | Future wave |
| Modifying BLCA logic | YES | Phase-2 |

### 10.3 Scope Freeze Attestation

**SCOPE FREEZE PROPOSAL — REQUIRES HUMAN APPROVAL**

```
WAVE-1 SCOPE FREEZE

I approve the following scope for Wave-1:

[ ] Layer import direction checking for backend Python files
[ ] BLCA as the detection mechanism
[ ] Grandfathering existing violations
[ ] Phased rollout (Warning → Soft Block → Hard Block)
[ ] SIG-023 as the new signal ID

Out of scope (deferred to later waves):
[ ] Fixing existing violations
[ ] Creating adapters
[ ] Frontend/TypeScript checking

Signature: _________________________
Date: _________________________
```

---

## 11. Open Questions (Require Human Decision)

| Question | Options | Impact |
|----------|---------|--------|
| Grandfather all existing violations? | Yes / No / Selective | Determines baseline size |
| Phase A duration? | 1 week / 2 weeks / 1 month | Developer adjustment time |
| Include L7 (Ops) in checking? | Yes / No | Expands scope |
| Fail on WARNING (undeclared layer)? | Error / Warning / Ignore | Strictness level |

---

## 12. Next Steps (Planning Only)

After scope freeze approval:

1. ~~Identify Wave-1 candidates~~ ✅ DONE (this document)
2. ~~Define promotion criteria~~ ✅ DONE (Section 3)
3. Generate violation baseline (requires scan)
4. Draft CI workflow YAML (planning only)
5. Propose Phase A start date
6. Request Phase-2 authorization for execution

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-01 | Initial Wave-1 planning document |
| 2026-01-01 | Added baseline observation results (BLCA-governance discrepancy found) |

---

**END OF PLANNING DOCUMENT — NO EXECUTION**
