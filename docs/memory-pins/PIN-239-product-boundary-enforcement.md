# PIN-239: Product Boundary Enforcement Framework

**Status:** COMPLETE
**Created:** 2025-12-29
**Category:** Infrastructure / Governance
**Milestone:** Post-M29 - Boundary Enforcement

---

## Summary

Implemented pre-build enforcement framework that blocks code existence unless provenance is declared. This is design-time enforcement, not runtime checks. The framework includes:

1. Product Boundary Contract (constitutional)
2. SESSION_PLAYBOOK.yaml Section 21 (5 blocking rules)
3. CLAUDE_BEHAVIOR_LIBRARY.md v1.5.0 (3 new BL-BOUNDARY-* rules)
4. Artifact Intent Schema (pre-build declaration)
5. Registry reclassification (4 mislabeled artifacts fixed)

---

## Problem Statement

### Original Analysis

The codebase registry showed:
- 31 artifacts labeled `product: ai-console` (28%)
- 81 artifacts labeled `product: system-wide` (72%)

### Investigation Results

Invocation-based analysis revealed:
- **4 artifacts mislabeled** (claimed ai-console but had non-console callers)
- **1 orphan artifact** (no production callers)
- **True AI Console count: 27** (not 31)

### Root Cause

Labels lie. Callers don't.

The registry was using **administrative labeling** instead of **invocation-based truth**.

---

## Solution: Pre-Build Enforcement

### Core Shift

From: "Verify correctness after code exists"
To: **"Block code existence unless provenance is declared"**

### Prime Invariant

> No code artifact may be created, modified, or reasoned about unless ALL of the following are declared and accepted:
> 1. Product ownership
> 2. Invocation ownership
> 3. Boundary classification
> 4. Failure jurisdiction

If ANY are unknown → **STOP and ask for clarification**.

---

## Deliverables

### New Files Created

| File | Purpose |
|------|---------|
| `docs/contracts/PRODUCT_BOUNDARY_CONTRACT.md` | Constitutional contract |
| `docs/codebase-registry/artifact-intent-schema.yaml` | Pre-build declaration schema |

### Updated Files

| File | Changes |
|------|---------|
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | v2.1 → v2.2, added Section 21 |
| `CLAUDE_BEHAVIOR_LIBRARY.md` | v1.4.0 → v1.5.0, added BL-BOUNDARY-* |
| `CLAUDE.md` | Added Product Boundary Enforcement section |
| 4 registry artifacts | Reclassified ai-console → system-wide |

---

## Blocking Rules Added

### SESSION_PLAYBOOK Section 21

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| BOUNDARY-001 | Artifact Registration Before Code | BLOCKING |
| BOUNDARY-002 | Three Blocking Questions | BLOCKING |
| BOUNDARY-003 | No Silent Assumptions | BLOCKING |
| BOUNDARY-004 | Bucket Classification Required | BLOCKING |
| BOUNDARY-005 | Invocation Ownership Rule | BLOCKING |

### Behavior Library Rules

| Rule ID | Name | Class |
|---------|------|-------|
| BL-BOUNDARY-001 | Product Boundary Declaration Required | product_boundary |
| BL-BOUNDARY-002 | Three Blocking Questions Gate | ownership_uncertainty |
| BL-BOUNDARY-003 | Caller Graph Determines Truth | invocation_drift |

---

## The Three Blocking Questions

Before creating or modifying code, Claude MUST answer:

| Question | Acceptable Answers | Unacceptable Answers |
|----------|-------------------|---------------------|
| Who calls this in production? | Specific modules/files | "Not sure", "Later", "Probably" |
| What breaks if AI Console is deleted? | Specific products/features | "I don't know", "Everything" |
| Who must NOT depend on this? | Specific restrictions | "Anyone can use it", "No restrictions" |

If ANY answer is uncertain → **BLOCK**.

---

## Bucket Classification

Every artifact MUST be classified:

| Bucket | Definition | Criteria |
|--------|------------|----------|
| **Surface** | User-facing, product-specific | Only product UI/routes call it |
| **Adapter** | Thin translation layer | < 200 LOC, no business logic, no state mutation |
| **Platform** | Shared infrastructure | Workers, SDK, or multiple products call it |
| **Orphan** | No production callers | ILLEGAL - integrate or delete |

---

## Boundary Violation Types

| Type | Definition | Resolution |
|------|------------|------------|
| BV-001 | Mislabeled Product | Reclassify to correct product |
| BV-002 | Adapter Creep | Split or promote to platform |
| BV-003 | Orphan Existence | Integrate or delete |
| BV-004 | Dual-Surface Hazard | Split into facades + shared core |
| BV-005 | Silent Platform Dependency | Make explicit or restructure |

---

## Artifacts Reclassified

These artifacts were mislabeled as `ai-console` but have non-console callers:

| Artifact ID | File | Violation | New Label |
|-------------|------|-----------|-----------|
| AOS-BE-SVC-RMT-001 | recovery_matcher.py | Called by workers | system-wide |
| AOS-BE-SVC-RRE-001 | recovery_rule_engine.py | Called by workers | system-wide |
| AOS-BE-SVC-EMT-001 | event_emitter.py | Serves founder console | system-wide |
| AOS-BE-SVC-CAD-001 | cost_anomaly_detector.py | Called by tests | system-wide |

### Known Issues (Pending Resolution)

| Artifact | Issue | Required Action |
|----------|-------|-----------------|
| pattern_detection.py | Orphan - no production callers | Delete or integrate |
| v1_killswitch.py | Dual-surface (console + SDK) | Document or split |

---

## Corrected Product Boundary

### Before (Label-Based)

```
AI Console: 31 artifacts (28%)
System-Wide: 81 artifacts (72%)
```

### After (Invocation-Based)

```
AI Console Surface:   20 artifacts (18%)
AI Console Adapters:   6 artifacts (5%)
Platform (corrected):  4 artifacts → moved to system-wide
Orphans:               1 artifact → pending resolution
```

**True AI Console: 27 artifacts (24%)**

---

## Enforcement Timeline

| Gate | When | Enforcer |
|------|------|----------|
| Design-time | Before code written | SESSION_PLAYBOOK Section 21 |
| Pre-commit | Before merge | Human review |
| CI | After merge | Automated caller graph (future) |
| Periodic | Weekly | Registry audit |

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│           PRODUCT BOUNDARY DISCIPLINE                        │
├─────────────────────────────────────────────────────────────┤
│  1. DECLARE: Product, bucket, callers, failure scope        │
│  2. ANSWER: Three blocking questions (no "probably")        │
│  3. CLASSIFY: Surface / Adapter / Platform                  │
│  4. VERIFY: Caller graph matches label                      │
│  5. NEVER ASSUME: Product from filename or directory        │
└─────────────────────────────────────────────────────────────┘
```

---

## One-Line Summary

> Code may only exist if its product boundary is declared, its callers are known, and its failure scope is explicit.

---

## References

- SESSION_PLAYBOOK.yaml Section 21
- PRODUCT_BOUNDARY_CONTRACT.md
- CLAUDE_BEHAVIOR_LIBRARY.md (BL-BOUNDARY-*)
- artifact-intent-schema.yaml
- PIN-237 (Codebase Registry Survey)
- PIN-238 (Code Registration & Evolution Governance)

---

## Related PINs

- [PIN-237](PIN-237-codebase-registry-survey.md) - Codebase Registry Survey (113 artifacts)
- [PIN-238](PIN-238-code-registration-evolution-governance.md) - Code Registration & Evolution Governance
- [PIN-235](PIN-235-products-first-architecture-migration.md) - Products-First Architecture Migration
