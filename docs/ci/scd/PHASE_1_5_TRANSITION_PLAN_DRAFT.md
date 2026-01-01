# Phase-1.5 Signal Closure & Promotion Transition Plan

**STATUS: DRAFT — PLANNING ONLY — NO EXECUTION**

**Date Drafted:** 2025-12-31
**Drafted By:** Claude (Governance Assistant)
**Requires:** Phase-1 Exit Ratification

---

## 1. Phase Model Overview

```
Phase-1   → Structural Closure (COMPLETE pending ratification)
Phase-1.5 → Signal Promotion Planning (THIS DOCUMENT)
Phase-2   → Mechanical Enforcement (FUTURE)
```

---

## 2. What Phase-1.5 Is

Phase-1.5 is the **planning bridge** between structural closure (Phase-1) and mechanical enforcement (Phase-2).

**Purpose:**
- Sequence which signals get promoted first
- Identify dependencies between promotions
- Document what enforcement mechanisms are needed
- Create a prioritized backlog for Phase-2

**What Phase-1.5 IS NOT:**
- Not execution
- Not CI changes
- Not code modifications
- Not enforcement activation

---

## 3. What Becomes ALLOWED in Phase-1.5

| Activity | Allowed? | Reason |
|----------|----------|--------|
| Read existing CI workflows | YES | Observation |
| Document promotion sequences | YES | Planning |
| Identify enforcement dependencies | YES | Planning |
| Propose CI modifications | YES | Planning (not execution) |
| Prioritize gap remediation | YES | Planning |
| Estimate effort for Phase-2 | YES | Planning |

---

## 4. What Remains FORBIDDEN in Phase-1.5

| Activity | Forbidden? | Reason |
|----------|------------|--------|
| Modify CI workflows | YES | Phase-2 activity |
| Add new CI checks | YES | Phase-2 activity |
| Change enforcement levels | YES | Phase-2 activity |
| Fix layer import violations | YES | Phase-2 activity |
| Create adapters for APIs | YES | Phase-2 activity |
| Promote signals without plan | YES | Governance violation |

---

## 5. Signal Promotion Candidates

### 5.1 Promotion Priority Matrix

| Priority | Signals | Reason | Dependencies |
|----------|---------|--------|--------------|
| P1 | SIG-001 | Main CI - most critical | None |
| P1 | SIG-003, SIG-006, SIG-007 | Governance signals | None |
| P2 | SIG-005 | Integration integrity | Layer import checker |
| P2 | SIG-008, SIG-013 | Determinism/M4 | None |
| P3 | SIG-010, SIG-011 | SDK publish | SDK team capacity |
| P4 | SIG-015, SIG-016 | Performance | Baseline required |
| P4 | SIG-017 | Nightly smoke | Environment stability |

### 5.2 What "Promotion" Means

```
Signal Promotion = Adding mechanical enforcement

Before: "Owner notified on failure" (human process)
After:  "CI blocks action on failure" (mechanical enforcement)
```

### 5.3 Promotion Prerequisites

| Signal | Current State | Promotion Prerequisite |
|--------|---------------|------------------------|
| SIG-001 | Runs, blocks merge | Decomposition (68KB is too large) |
| SIG-003 | Runs, blocks merge | Already promoted |
| SIG-005 | Runs, blocks merge | Add layer import checker |
| SIG-006 | Runs, blocks merge | Already promoted |
| SIG-007 | Runs, blocks merge | Already promoted |
| SIG-008 | Runs, blocks merge | Add nightly hash verification |
| SIG-012 | Zone A blocks | Expand to Zone B |
| SIG-013 | Runs, blocks merge | Add golden file freshness check |

---

## 6. Gap Remediation Sequencing

### 6.1 Recommended Sequence (Planning Only)

```
WAVE 1: Import Direction Enforcement
├── GAP-L8A-005: Add layer import direction checker to CI
├── GAP-L4L5-004: Enforce L5→L4 import rules
└── GAP-L2L4-004: Enforce L2→L3→L4 import rules

WAVE 2: Boundary Adapter Creation
├── GAP-L2L4-001: Create L3 adapters for 30 API files
├── GAP-L2L4-002: Route runtime.py through L3 adapter
└── GAP-L4L5-001: Add adapter for L5→L4 planner access

WAVE 3: Resilience & Platform
├── GAP-L5L6-003: Add circuit breaker for HTTP calls
├── GAP-L5L6-004: Add retry logic for DB failures
└── GAP-L5L6-001: Create L6 abstraction layer

WAVE 4: Governance Automation
├── GAP-L8A-006: CI→governance artifact pipeline
└── GAP-L8A-007: Manual override ratification process
```

### 6.2 Estimated Effort (Planning Estimate Only)

| Wave | Scope | Effort Estimate | Risk |
|------|-------|-----------------|------|
| Wave 1 | 3 gaps | Small (1 new CI job) | Low |
| Wave 2 | 3 gaps | Medium (code changes) | Medium |
| Wave 3 | 3 gaps | Medium (infrastructure) | Medium |
| Wave 4 | 2 gaps | Large (governance tooling) | High |

---

## 7. Enforcement Mechanisms Needed

### 7.1 New CI Jobs Required

| Job Name | Purpose | Gaps Addressed |
|----------|---------|----------------|
| `layer-import-check.yml` | Validate import direction | GAP-L8A-005, GAP-L4L5-004, GAP-L2L4-004 |
| `adapter-size-check.yml` | Ensure L3 adapters < 200 LOC | GAP-L2L4-005 |
| `governance-sync.yml` | Update governance artifacts on CI completion | GAP-L8A-006 |

### 7.2 Existing CI Modifications Required

| Workflow | Modification | Gaps Addressed |
|----------|--------------|----------------|
| `ci.yml` | Decompose into smaller jobs | SIG-001 maintainability |
| `integration-integrity.yml` | Add BLCA step | GAP-L8A-004 |
| `m7-nightly-smoke.yml` | Fix environment dependencies | GAP-L8A-003 |

---

## 8. Transition Dependencies

### 8.1 Phase-1.5 → Phase-2 Gate

Phase-2 may not begin until:

| Condition | Status |
|-----------|--------|
| Phase-1 Exit ratified | PENDING |
| Promotion sequence approved | PENDING |
| Wave 1 scope defined | DRAFT (this document) |
| Resource allocation confirmed | PENDING |

### 8.2 Internal Dependencies

```
Wave 1 (Import Checker) has no dependencies
Wave 2 (Adapters) depends on Wave 1 for validation
Wave 3 (Resilience) has no dependencies (can parallel)
Wave 4 (Governance) depends on Waves 1-3 completion
```

---

## 9. Risk Assessment (Planning Only)

### 9.1 Promotion Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| False positives from import checker | Medium | High | Staged rollout, warning-first |
| Adapter creation breaks callers | Low | High | LIT tests before promotion |
| SIG-001 decomposition regression | Medium | High | Parallel run old + new |
| Governance automation complexity | High | Medium | Start simple, iterate |

### 9.2 Sequencing Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| Parallel execution conflict | Waves executed in wrong order | Document dependencies clearly |
| Scope creep | Waves grow beyond original scope | Strict scope freeze per wave |
| Owner unavailability | Consolidated owner becomes bottleneck | Plan delegation points |

---

## 10. Success Criteria for Phase-2 Entry

Phase-2 may begin when:

| Criterion | Verification |
|-----------|--------------|
| Phase-1 Exit ratified | Human signature |
| This transition plan approved | Human signature |
| Wave 1 scope frozen | Human signature |
| Resource commitment confirmed | Human signature |
| First enforcement target selected | Human decision |

---

## 11. What Happens After Phase-2

```
Phase-2   → Mechanical Enforcement (CI changes, enforcement activation)
Phase-2.5 → Enforcement Tuning (false positive reduction)
Phase-3   → Signal Expansion (new boundaries, new circuits)
```

---

## 12. Open Questions (Require Human Decision)

| Question | Options | Decision Required By |
|----------|---------|---------------------|
| Start with import checker or adapters? | Wave 1 or Wave 2 first | Founder |
| Accept SIG-001 as-is or decompose first? | Decompose / Accept | Founder |
| Parallel Waves 1 and 3? | Yes / No | Founder |
| Hire before Phase-2 or after? | Before / During / After | Founder |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial draft created by Claude |

---

**END OF DRAFT — PLANNING ONLY — NO EXECUTION**
