# INFRA_REGISTRY.md

## Infrastructure Declaration & CI Behavior

**Status:** CANONICAL
**Reference:** PIN-270 (Infrastructure State Governance), PIN-266 (Infra Registry Canonicalization)
**Created:** 2026-01-01
**Last Updated:** 2026-01-02

---

## Purpose

This document is the **single source of truth** for all infrastructure dependencies.

**Invariant:** If an infrastructure item is not listed here, **it must not be assumed**.

**Design Principle:** CI behavior must be derived from this registry. No test may assume infra presence implicitly.

---

## Infra State Definitions

| State | Name | Meaning | Test Behavior |
|-------|------|---------|---------------|
| **A** | Chosen (Conceptual) | Infra selected for production, not wired locally | MUST skip explicitly (Bucket B) |
| **B** | Local Substitute | Contract exercised via stub/emulator | MUST run against substitute |
| **C** | Fully Wired | Required and available | Failures are blocking |

### State Transitions

```
A (Conceptual) → B (Substitute) → C (Fully Wired)
     ↓                ↓                ↓
  Skip (B1/B2)     Run tests      Required
```

**Rule:** State transitions require human approval. Claude may propose, not apply.

---

## Infra Registry (Canonical)

### Full Registry Table

| Infra Name | Category | Layer | State | Used By | Failure Mode | Stub Available | Local Strategy | Promotion Trigger | Owner |
|------------|----------|-------|-------|---------|--------------|----------------|----------------|-------------------|-------|
| PostgreSQL | DB | L6 | **C** | Tests, CI, Runtime | FAIL | No | Local DB (5433) | Always required | Platform |
| Redis | Cache/Queue | L6 | **B** | Tests, CI, Runtime | Skip | Yes (mock) | Local Redis (6379) | Worker correctness | Platform |
| Clerk | Auth | L6 | **B** | Tests, CI | Skip | **Yes** | Stub (app/auth/stub.py) | External users (→C) | Platform |
| M10 Recovery | DB Schema | L6 | **B** | Tests, CI, Runtime | FAIL | No | Canonical migration | Always required | Platform |
| Prometheus | Metrics | L7 | A | Runtime | Skip | No | None | First SLO | Ops |
| Alertmanager | Alerts | L7 | A | Runtime | Skip | No | None | Production alerts | Ops |
| Grafana | Dashboards | L7 | A | Ops | Skip | No | None | Ops visibility | Ops |
| AgentsSchema | DB | L6 | A | M12 | Skip | No | None (Neon only) | M12 productization | Platform |
| LLMAPIs | External | L6 | A | Runtime | XFail | Yes (mock) | Mocked | Cost-controlled | Platform |
| Neon | DB | L6 | A | Runtime | Skip | Yes | Local fallback | Prod verification | Platform |
| Backend | API | L2 | **B** | Tests | Skip | No | Docker compose | Integration tests | Platform |

### Quick Reference (State Summary)

| State | Count | Infra Items |
|-------|-------|-------------|
| **C** (Fully Wired) | 1 | PostgreSQL |
| **B** (Local Substitute) | 4 | Redis, Clerk, Backend, M10 Recovery |
| **A** (Conceptual) | 6 | Prometheus, Alertmanager, Grafana, AgentsSchema, LLMAPIs, Neon |

---

## Bucket Classification

### Bucket B1 — Production-Required, Locally Missing

These **will** cause regressions if not eventually exercised.

| Infra | Risk if Not Tested | Promotion Priority |
|-------|--------------------|--------------------|
| *(None currently — Clerk promoted to State B)* | — | — |

**Clerk/RBAC** was B1, promoted to State B on 2026-01-01 via stub implementation.
See: `app/auth/stub.py`, PIN-272

### Bucket B2 — Optional / Future

These are **intentionally deferred** with documented justification.

| Infra | Justification | Review Trigger |
|-------|---------------|----------------|
| Prometheus | Observability, not correctness | First SLO |
| Alertmanager | Operational, not behavioral | Production incidents |
| Agents Schema | Internal capability (PIN-265) | M12 productization |
| LLM APIs | Cost-bound, mocked adequately | External customer load |

---

## Rules (Non-Negotiable)

### R1: Explicit Declaration

Tests MUST declare infra dependency using `@requires_infra("name")` marker.

### R2: Skip Justification

Skipped tests MUST reference:
- Infra name
- Infra state (A/B/C)
- Bucket (B1/B2)

### R3: State A Safety

State A infra MUST NOT cause failing tests.
Failures from missing State A infra indicate:
- Missing `@requires_infra` marker
- Test incorrectly assumes infra availability

### R4: State C Integrity

State C infra MUST NOT be skipped.
If State C infra is unavailable, **CI should fail**, not skip.

### R5: Governance Gate

Changing infra state requires:
1. Human approval in session
2. Update to this registry
3. CI verification of new state

---

## Promotion Roadmap

### Phase 1: RBAC Stub — COMPLETE

**Target:** Clerk → State B ✅

**Completed:** 2026-01-01

**Deliverables:**
- Auth configured via CLERK_SECRET_KEY or DEV_AUTH_ENABLED
- Contract shape matches Clerk response format
- No external API keys required for dev mode
- Test fixtures in `tests/conftest.py` (test_admin_headers, etc.)

**Success Criteria:** ✅
- Dev auth mode implemented
- DEV_AUTH_ENABLED env var controls dev mode
- Permission checking helpers
- CI fixture integration

**Reference:** PIN-272 (Phase B.1 Test Isolation)

### Phase 1.5: M10 Recovery Schema — COMPLETE

**Target:** M10 Recovery → State B ✅

**Completed:** 2026-01-02

**Deliverables:**
- `migrations/versions/002_m10_recovery_outbox.py` — Canonical M10 migration
- m10_recovery schema with all tables, indexes, constraints, functions
- recovery_candidates table with upsert-safe constraints
- Test isolation fixtures in `tests/conftest.py` (clean_m10_tables, clean_recovery_candidates)

**Success Criteria:** ✅
- All M10 invariant tests pass
- Outbox E2E tests pass
- No test skips for M10 infra
- Schema matches production semantics

**Reference:** PIN-276 (Test Isolation)

### Phase 2: Prometheus (Deferred)

**Trigger:** First SLO requirement or traffic milestone

**Not before:**
- Real user traffic exists
- Alert fidelity matters

### Phase 3: M12 Agents (Deferred)

**Trigger:** M12 productization decision

**Governed by:** PIN-265 (M12 Boundary Strategy)

---

## CI Integration

### Helper Location

```
tests/helpers/infra.py
```

### Usage Pattern

```python
from tests.helpers.infra import requires_infra

@requires_infra("Clerk")
def test_rbac_enforcement():
    ...
```

### CI Check

```yaml
# .github/workflows/ci.yml
infra-registry-check:
  runs-on: ubuntu-latest
  steps:
    - name: Verify infra declarations
      run: python3 scripts/ci/check_infra_registry.py
```

---

## Ownership

| Role | Responsibility |
|------|----------------|
| Human | Approves state transitions |
| Claude | Proposes transitions, enforces rules |
| CI | Validates infra declarations |
| Tests | Declare dependencies explicitly |

---

## CI Rediscovery Mapping (No Drift)

This section clarifies the relationship between infra governance artifacts.

### Artifact Responsibility Matrix

| Artifact | Responsibility | Owns |
|----------|----------------|------|
| **CI_REDISCOVERY_MASTER_ROADMAP.md** | Progress tracking | Phases, slices, completion metrics |
| **CI_NORTH_STAR.md** | Invariants | The four CI invariants (I1–I4) |
| **INFRA_REGISTRY.md** (this file) | Ground truth | What infra exists and its state |
| **SESSION_PLAYBOOK.yaml** | Enforcement | How Claude behaves given infra state |
| **tests/helpers/infra.py** | Implementation | `@requires_infra` decorator |

### Who Does What

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         CI TRUTH DERIVATION                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   INFRA_REGISTRY.md (Ground Truth)                                       │
│         │                                                                │
│         ├──► CI_NORTH_STAR.md (Invariants that protect truth)            │
│         │                                                                │
│         ├──► tests/helpers/infra.py (Mechanical enforcement)             │
│         │         │                                                      │
│         │         └──► @requires_infra("X") decorators                   │
│         │                                                                │
│         ├──► SESSION_PLAYBOOK.yaml (Claude governance)                   │
│         │                                                                │
│         └──► CI_REDISCOVERY_MASTER_ROADMAP.md (Progress tracking)        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Anti-Drift Rule

> **No artifact may define infra state independently of this registry.**
>
> If CI_NORTH_STAR.md references infra → it must point here.
> If a test skips for infra → it must use `@requires_infra`.
> If Claude reasons about infra → it must check this registry first.

### North Star Alignment

| North Star Invariant | How This Registry Helps |
|---------------------|------------------------|
| I1: No Mystery Failures | Every failure is classifiable via State (A/B/C) |
| I2: No Silent Skips | `@requires_infra` forces explicit skip with reason |
| I3: No Flaky Tests | Stub availability (B state) enables determinism |
| I4: No Human Memory | Registry is self-documenting; no tribal knowledge |

---

## References

- PIN-266 (Infra Registry Canonicalization)
- PIN-270 (Infrastructure State Governance)
- PIN-271 (CI North Star Declaration)
- PIN-265 (Phase C.1 RBAC Stub Implementation)
- PIN-272 (Phase B.1 Test Isolation)
- CI_NORTH_STAR.md
- CI_REDISCOVERY_MASTER_ROADMAP.md
- SESSION_PLAYBOOK.yaml (governance_relationship)
