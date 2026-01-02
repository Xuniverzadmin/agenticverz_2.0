# PIN-270: Infrastructure State Governance

**Status:** ACTIVE
**Created:** 2026-01-01
**Category:** Governance / Infrastructure
**Related PINs:** PIN-269 (Claude Authority), PIN-266 (Test Repair)

---

## Executive Summary

Establishes a formal tri-state model for infrastructure dependencies, eliminating ambiguity about when tests should skip vs fail vs run.

---

## Problem Statement

Before this PIN:
- Tests guessed whether infra was available
- Skips were ad-hoc (no central registry)
- CI couldn't distinguish "infra missing" from "test broken"
- Developers didn't know which infra to set up locally

---

## Solution: Tri-State Model

### State A — Chosen (Conceptual)

- **Meaning:** Infra selected for production, not wired locally
- **Local Strategy:** None (no API keys, no emulator)
- **Test Behavior:** MUST skip explicitly (Bucket B)
- **Example:** Clerk (RBAC), Prometheus (Metrics)

### State B — Local Substitute

- **Meaning:** Contract exercised via stub/emulator
- **Local Strategy:** Stub or local service
- **Test Behavior:** MUST run against substitute
- **Example:** Redis (local), future RBAC stub

### State C — Fully Wired

- **Meaning:** Required and available
- **Local Strategy:** Local service required
- **Test Behavior:** Failures are blocking (no skips)
- **Example:** PostgreSQL

---

## Bucket B Sub-Classification

### B1 — Production-Required, Locally Missing

These **will** cause regressions if not eventually exercised.

| Infra | Risk | Promotion Priority |
|-------|------|-------------------|
| Clerk/RBAC | Auth bypass, privilege escalation | HIGH |

### B2 — Optional / Future

These are **intentionally deferred** with documented justification.

| Infra | Justification | Review Trigger |
|-------|---------------|----------------|
| Prometheus | Observability, not correctness | First SLO |
| AgentsSchema | Internal capability (PIN-265) | M12 productization |

---

## Artifacts Created

| Path | Purpose |
|------|---------|
| `docs/infra/INFRA_REGISTRY.md` | Authoritative registry of all infra |
| `tests/helpers/infra.py` | `@requires_infra` decorator and state checking |
| `scripts/ci/check_infra_registry.py` | CI consistency validation |
| `CLAUDE_AUTHORITY.md §3.5` | Governance rule for infra declarations |

---

## Usage

### Declaring Infra Dependency

```python
from tests.helpers.infra import requires_infra

@requires_infra("Clerk")
def test_rbac_enforcement():
    ...
```

### Checking Infra State

```python
from tests.helpers.infra import check_infra_available, get_infra_skip_reason

if not check_infra_available("Prometheus"):
    pytest.skip(get_infra_skip_reason("Prometheus"))
```

---

## Rules (Codified in CLAUDE_AUTHORITY.md §3.5)

1. Tests **must declare** infra dependency via `@requires_infra("name")`
2. State A infra **must not cause test failures** (only skips)
3. State C infra **must not be skipped** (failures are real)
4. State transitions **require human approval**

---

## Current Registry Status

| Infra | State | Bucket | Promotion Plan |
|-------|-------|--------|----------------|
| PostgreSQL | C | — | Always required |
| Redis | B | — | Local Redis |
| Clerk | A | B1 | RBAC stub (next phase) |
| Prometheus | A | B2 | Post-traffic |
| Alertmanager | A | B2 | Post-traffic |
| Grafana | A | B2 | Post-traffic |
| AgentsSchema | A | B2 | M12 productization |
| LLMAPIs | A | B2 | Mocked in tests |
| Neon | A | B2 | Prod verification |

---

## Promotion Roadmap

### Phase 1: RBAC Stub (Recommended Next)

**Goal:** Clerk A → B

**Deliverables:**
- `tests/fixtures/auth_stub.py` — Deterministic role/claim issuer
- Contract shape matches Clerk response format
- No external API keys required

**Success Criteria:**
- All `@requires_infra("Clerk")` tests run (not skip)
- RBAC contract tests pass locally

### Phase 2: Prometheus (Deferred)

**Trigger:** First SLO requirement or traffic milestone

---

## CI Integration

The `check_infra_registry.py` script validates:
- All `@requires_infra` markers reference valid infra names
- State C infra is not being skipped
- Code registry matches documentation

---

## References

- CLAUDE_AUTHORITY.md §3.5 (Infrastructure State Declaration)
- PIN-269 (Claude Authority Spine)
- PIN-266 (Test Repair Execution Tracker)
- docs/infra/INFRA_REGISTRY.md
- tests/helpers/infra.py
