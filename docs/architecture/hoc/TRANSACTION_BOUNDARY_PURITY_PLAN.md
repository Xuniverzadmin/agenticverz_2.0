# Transaction Boundary Purity Plan (First-Principles)

**Status:** ACTIVE (Codex-owned)  
**Created:** 2026-02-07  
**Scope:** `backend/app/hoc/cus/**` + purity auditor `backend/scripts/ops/hoc_l5_l6_purity_audit.py`  
**Plan Ownership:** Only **Codex** updates this plan (Claude must not edit this file).

## Problem Statement

We currently have “green” purity outputs while transaction boundaries still occur in lower layers via implicit commit semantics:

- `engine.begin()` (sync SQLAlchemy) commits on context exit.
- `session.begin()` / `AsyncSession.begin()` commits on context exit.

These are **real transaction boundaries**, even when there are **no explicit** `.commit()` calls.

From first principles:

- Transaction boundaries must be **explicit** and **owned by a single authority** (orchestrator layer).
- Lower layers may *perform effects* but must not decide the “atomic unit” of persistence.

## Reality Audit (Concrete Gaps)

### Gap A — L6 owns transaction boundary via `begin()`

- Policies:
  - `backend/app/hoc/cus/policies/L6_drivers/policy_engine_driver.py:1451` uses `with engine.begin() as conn:` inside `_write_conn()`.
- Controls:
  - `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py:331` uses `async with session.begin():`
  - `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py:497` uses `async with session.begin():`
  - `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py:556` uses `async with session.begin():`
  - `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py:595` uses `async with session.begin():`
  - `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py:634` uses `async with session.begin():`
  - Same file constructs its own sessions (`AsyncSessionLocal()`) at multiple sites (e.g. around `:330`, `:496`, `:555`, `:594`, `:633`).

### Gap B — L5 owns transaction boundary via `begin()`

This is a second-order finding that blocks a fully uniform design:

- Policies:
  - `backend/app/hoc/cus/policies/L5_engines/policy_rules_engine.py:149` uses `async with self._session.begin():`
  - `backend/app/hoc/cus/policies/L5_engines/policy_rules_engine.py:241` uses `async with self._session.begin():`
  - `backend/app/hoc/cus/policies/L5_engines/policy_limits_engine.py:172` uses `async with self._session.begin():`
  - `backend/app/hoc/cus/policies/L5_engines/policy_limits_engine.py:265` uses `async with self._session.begin():`
- Incidents:
  - `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py:119` uses `with self._session.begin():`
  - `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py:189` uses `with self._session.begin():`
  - `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py:266` uses `with self._session.begin():`

### Gap C — Purity auditor does not currently detect `begin()` semantics

`backend/scripts/ops/hoc_l5_l6_purity_audit.py` flags commit/rollback/connect, but does **not** flag `.begin()` / `.begin_nested()`.

This allows “0 violations” even when implicit commit semantics exist.

## Target State

- L4 is the only layer that starts/ends transactions:
  - Async: `async with ctx.session.begin(): ...`
  - Sync: `with ctx.session.begin(): ...`
  - Engine/Connection based (Policies legacy): transaction context is created explicitly in L4 and passed down as a connection.
- L5 performs business logic only; no transaction context managers.
- L6 performs I/O only; no `begin()` or `commit()`/`rollback()` calls and no session creation.

## Implementation Phases

### Phase 0 — Make the Purity Auditor Catch `begin()` (Truth Instrument)

**Status:** PENDING  
Work:
- Update `backend/scripts/ops/hoc_l5_l6_purity_audit.py`:
  - Treat `begin()` / `begin_nested()` calls as transaction boundary violations in **L6** (always).
  - Treat `begin()` / `begin_nested()` calls on DB-ish receivers as violations in **L5**.

Acceptance:
- Auditor reports current `begin()` occurrences as violations before remediation starts.

### Phase 1 — Policies: Remove L6 Standalone Transactions (PolicyEngineDriver)

**Status:** PENDING  
Work:
- Remove `engine.begin()` from `backend/app/hoc/cus/policies/L6_drivers/policy_engine_driver.py:_write_conn`.
- Require write operations to run under an explicit L4-owned write context.
  - Option A (preferred): L4 opens transaction + passes a connection to driver calls.
  - Option B (acceptable transitional): L4 must explicitly call a context manager to begin the write transaction (even if implemented in driver), and standalone writes are forbidden.
- Update all callsites so policy writes cannot happen outside the L4 boundary.
  - Start search from `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` and the PolicyEngine call graph.

Acceptance:
- No `engine.begin()` or `.begin()` usage remains in `backend/app/hoc/cus/policies/L6_drivers/`.

### Phase 2 — Controls: Remove L6 Transaction Ownership (Circuit Breaker Async Driver)

**Status:** PENDING  
Work:
- Refactor `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py`:
  - Remove `async with session.begin():` usage in L6.
  - Eliminate internal session creation (`AsyncSessionLocal()`) for state mutations; require session injection from L4 handlers.
- Move begin/commit boundary to L4 handlers:
  - `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/circuit_breaker_handler.py`
  - `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`

Acceptance:
- No `session.begin()` remains in controls L6 drivers.
- All circuit breaker state mutations occur under an explicit L4 begin boundary.

### Phase 3 — L5 Engines: Remove Transaction Context Managers

**Status:** PENDING  
Work:
- Remove `session.begin()` usage from L5 engines (policies + incidents).
- Move begin/commit to L4 handlers for the corresponding write operations.

Acceptance:
- No `.begin()` usage remains under `backend/app/hoc/cus/**/L5_*` except TYPE_CHECKING or non-DB contexts.

## Verification (Run After Each Phase)

- `python3 backend/scripts/ci/check_init_hygiene.py --ci`
- `python3 backend/scripts/ci/check_layer_boundaries.py --ci`
- `python3 backend/scripts/ops/hoc_cross_domain_validator.py`
- `pytest -q backend/tests/hoc_spine/test_hoc_spine_import_guard.py`
- `python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --json --advisory`

## Risks / Expected Difficulties

- Policies: PolicyEngine is legacy “engine/connection” based rather than `AsyncSession` based; removing standalone writes can require wide callsite rewiring.
- Controls: circuit breaker logic currently self-manages sessions for correctness and locking; making L4 inject sessions will change several APIs and may touch callsites outside handlers.
- L5: some engines currently rely on `begin()` for atomic multi-step updates; moving this to L4 requires correct mapping of “write” operations in handlers.
