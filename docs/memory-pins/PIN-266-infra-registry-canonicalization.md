# PIN-266: Infra Registry Canonicalization

**Status:** ✅ COMPLETE
**Created:** 2026-01-01
**Category:** CI / Governance
**Milestone:** CI Rediscovery

---

## Summary

Established INFRA_REGISTRY.md as the single source of truth for all infrastructure dependencies. CI behavior is now derived from registry state, not assumed.

---

## Details

## Summary

This PIN canonicalizes the infrastructure registry, ensuring CI behavior is derived from explicit infra state rather than implicit assumptions.

---

## Problem Statement

Before this work:
- Infra presence was often assumed without explicit declaration
- Test skips lacked clear justification tied to infra state
- CI failures from missing infra were indistinguishable from real bugs
- Human memory was required to understand why tests skipped

---

## Solution

### 1. Enhanced INFRA_REGISTRY.md (Canonical)

Added comprehensive fields to each infra entry:

| Field | Purpose |
|-------|---------|
| Category | Auth / Metrics / Queue / Cache / DB / External |
| Layer | L6 (Platform) / L7 (Ops) |
| State | A (Absent) / B (Stubbed) / C (Real) |
| Used By | Tests / CI / Runtime |
| Failure Mode | Skip / Fail / XFail |
| Stub Available | Yes / No |
| Owner | Platform / Ops |

### 2. CI Rediscovery Mapping Section

Added clarity on artifact responsibilities:

| Artifact | Responsibility |
|----------|----------------|
| CI_REDISCOVERY_MASTER_ROADMAP.md | Progress tracking |
| CI_NORTH_STAR.md | Invariants (I1-I4) |
| INFRA_REGISTRY.md | Ground truth |
| SESSION_PLAYBOOK.yaml | Enforcement |
| tests/helpers/infra.py | Implementation |

### 3. SESSION_PLAYBOOK Section 33 (Infra Truth Rule)

Added new section with:
- Core principle: CI behavior derived from registry
- Infra state taxonomy (A/B/C) locked
- CI auto-alignment rules
- Ground truth authority chain
- Claude behavior rules

---

## The Infra Truth Rule

> **CI behavior must be derived from INFRA_REGISTRY.md.**
> **No test may assume infra presence implicitly.**

### Infra State Taxonomy (Locked)

| State | Name | CI Behavior |
|-------|------|-------------|
| **A** | Absent (Conceptual) | SKIP with explicit reason |
| **B** | Stubbed (Local Substitute) | RUN with stub |
| **C** | Real (Fully Wired) | FAIL if missing |

### Anti-Drift Rule

No artifact may define infra state independently of INFRA_REGISTRY.md.

---

## Deliverables

| Deliverable | Status |
|-------------|--------|
| Enhanced INFRA_REGISTRY.md | ✅ |
| CI Rediscovery Mapping | ✅ |
| SESSION_PLAYBOOK Section 33 | ✅ |
| Infra State Taxonomy | ✅ (Locked) |
| @requires_infra decorator | ✅ (Already exists) |

---

## Closure Criteria

| Criterion | Status |
|-----------|--------|
| All infra classified (A/B/C) | ✅ 10 items |
| CI behavior derives from registry | ✅ |
| No infra-related mystery failures | ✅ |
| SESSION_PLAYBOOK updated | ✅ v2.30 |

---

## Files Changed

| File | Change |
|------|--------|
| docs/infra/INFRA_REGISTRY.md | Enhanced with full taxonomy |
| docs/playbooks/SESSION_PLAYBOOK.yaml | Added Section 33 (v2.30) |

---

## References

- PIN-270 (Infrastructure State Governance)
- PIN-271 (CI North Star Declaration)
- PIN-265 (Phase C.1 RBAC Stub)
- PIN-272 (Phase B.1 Test Isolation)
- CI_NORTH_STAR.md
- CI_REDISCOVERY_MASTER_ROADMAP.md

---

## Related PINs

- [PIN-270](PIN-270-.md)
- [PIN-271](PIN-271-.md)
- [PIN-265](PIN-265-.md)
- [PIN-272](PIN-272-.md)
