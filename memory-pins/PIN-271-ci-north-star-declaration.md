# PIN-271: CI North Star Declaration

**Status:** ACTIVE (FROZEN)
**Created:** 2026-01-01
**Category:** CI / Governance
**Related PINs:** PIN-270 (Infra Governance), PIN-269 (Claude Authority), PIN-266 (Test Repair)

---

## Executive Summary

Declares the single governing principle for CI: **CI must tell the truth about system health, deterministically, without requiring human memory or heroics.**

---

## The North Star Principle

> **CI must tell the truth about system health, deterministically, without requiring human memory or heroics.**

This is non-negotiable. All CI work serves this.

---

## The Four Invariants

| ID | Invariant | Meaning |
|----|-----------|---------|
| I1 | No Mystery Failures | Every failure classifiable in 30s (Bucket A/B/C) |
| I2 | No Silent Skips | Every skip has marker + reason + governance |
| I3 | No Flaky Tests | Tests that pass sometimes are not tests |
| I4 | No Human Memory Required | CI failures self-explain |

---

## CI Rediscovery Closure Criteria

CI Rediscovery is **complete** when ALL of these hold:

| # | Criterion | Measurement |
|---|-----------|-------------|
| 1 | All failures classified | Bucket A/B/C marker on every failing test |
| 2 | All skips governed | B1/B2 with documented reason |
| 3 | No flaky tests | Or marked as chaos/stress |
| 4 | Pass rate stable | < 1% variance over 7 days |
| 5 | No mystery failures | Every failure explainable in 30s |

**Exit Gate:** When these hold, declare "CI Rediscovery Closure" and tag it.

---

## Artifact Linkage

| Artifact | Serves Principle |
|----------|------------------|
| CLAUDE_AUTHORITY.md | Governance Enforcement |
| INFRA_REGISTRY.md | I2 (No Silent Skips) |
| `@requires_infra` | I1 (No Mystery Failures) |
| Bucket markers | I1 (No Mystery Failures) |
| Invariant docs | I4 (No Human Memory) |
| Feature Intent system | Design Feedback Loop |

---

## Meta-Rule

> **No new product feature work unless CI rediscovery remains green for N consecutive days.**

- Active development: N = 3 days
- Before external users: N = 7 days

---

## Phase Map

| Phase | Goal | Status |
|-------|------|--------|
| Phase A | CI North Star Lock | COMPLETE (this PIN) |
| Phase B | Finish CI Rediscovery | IN PROGRESS |
| Phase C | RBAC A→B Promotion | PENDING |
| Phase D | CI Rediscovery Closure | PENDING |

---

## What This Enables

Once CI Rediscovery is closed:

1. **Product feature work resumes safely**
2. **L1 consoles can be built confidently**
3. **External users can be onboarded**
4. **Regressions are caught, not discovered**

---

## References

- `docs/ci/CI_NORTH_STAR.md` (frozen document)
- PIN-270 (Infrastructure State Governance)
- PIN-269 (Claude Authority Spine)
- PIN-266 (Test Repair Execution Tracker)
- `docs/ci/CI_REDISCOVERY_MASTER_ROADMAP.md`
