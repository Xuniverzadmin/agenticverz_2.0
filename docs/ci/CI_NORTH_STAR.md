# CI North Star

**Status:** FROZEN
**Created:** 2026-01-01
**Reference:** PIN-271 (CI North Star Declaration)

---

## The One Principle

> **CI must tell the truth about system health, deterministically, without requiring human memory or heroics.**

This is non-negotiable. Everything else serves this.

---

## What CI IS

| Role | Meaning |
|------|---------|
| **Truth Surface** | CI reflects actual system state, not aspirational state |
| **Regression Detector** | Passing code that later fails is a CI failure, not a code failure |
| **Governance Enforcement** | Rules declared in governance docs are mechanically enforced |
| **Design Feedback Loop** | Hard-to-test code is a design problem, not a testing problem |

---

## What CI is NOT

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| A gate to keep code out | Gates without signal are bureaucracy |
| A place to "eventually make green" | Deferred green is hidden red |
| A dumping ground for future work | Skips without governance are lies |
| A hero's burden | If CI requires memory, CI is broken |

---

## The Four Invariants

### I1: No Mystery Failures

Every CI failure must be classifiable within 30 seconds:

- **Bucket A** — Test is wrong
- **Bucket B** — Infrastructure missing (see INFRA_REGISTRY.md)
- **Bucket C** — System bug

If classification takes longer, the failure is under-documented.

### I2: No Silent Skips

Every skipped test must have:

- Explicit marker (`@requires_infra`, `@pytest.mark.skip`)
- Documented reason
- Governance status (B1 = must fix, B2 = intentional)

If a skip has no governance, it's a lie.

### I3: No Flaky Tests

A test that passes sometimes is not a test. It's noise.

Flaky tests must be:

- Fixed (if determinism is possible)
- Marked as chaos/stress (if intentional non-determinism)
- Deleted (if neither)

### I4: No Human Memory Required

If understanding a CI failure requires:

- Reading Slack history
- Asking "who touched this?"
- Remembering past incidents

...then CI has failed its job.

---

## Artifact Linkage

Every CI-related artifact must declare which North Star principle it serves.

| Artifact | Serves Principle |
|----------|------------------|
| CLAUDE_AUTHORITY.md | Governance Enforcement |
| INFRA_REGISTRY.md | I2 (No Silent Skips) |
| `@requires_infra` | I1 (No Mystery Failures) |
| Bucket markers | I1 (No Mystery Failures) |
| Invariant docs | I4 (No Human Memory) |
| Feature Intent system | Design Feedback Loop |

---

## Closure Criteria (When Is CI "Done"?)

CI Rediscovery is complete when:

1. **All failures are classified** (Bucket A/B/C)
2. **All skips are governed** (B1/B2 with reason)
3. **No flaky tests remain** (or are marked chaos)
4. **Pass rate is stable** (< 1% variance over 7 days)
5. **No mystery failures** (every failure explainable in 30s)

When these hold, CI is a **reliable narrator**.

---

## The Meta-Rule

> **No new product feature work unless CI rediscovery remains green for N consecutive days.**

This prevents regressions while allowing forward progress.

Suggested N: 3 days for active development, 7 days before external users.

---

## References

- PIN-271 (CI North Star Declaration)
- PIN-270 (Infrastructure State Governance)
- PIN-269 (Claude Authority Spine)
- PIN-266 (Test Repair Execution Tracker)
- INFRA_REGISTRY.md
- CLAUDE_AUTHORITY.md §3 (Classification)
