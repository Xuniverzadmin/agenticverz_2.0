# codex_agents_agenticverz2.md

## Scope
This guidance applies to the agent when working in:
- `backend/app/hoc/**`
- `backend/app/**` (when touching HOC-related wiring)

## Canonical Sources (Read First)
If any conflict exists, prefer newer/binding docs:
1. `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md` (RATIFIED, binding)
2. `docs/architecture/architecture_core/LAYER_MODEL.md` (LOCKED)
3. `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md` (LOCKED)
4. `docs/architecture/architecture_core/ARCH_DECLARATION.md` (FROZEN)
5. `docs/architecture/hoc/L4_L5_CONTRACTS_V1.md` (DRAFT, legacy paths)
6. `docs/architecture/hoc/AUTHORITY_VIOLATION_SPEC_V1.md` (DRAFT, legacy paths)

## HOC Topology (Binding)
Execution path is linear and enforced:
L2.1 Facade -> L2 API -> L4 hoc_spine -> L5 Engine -> L6 Driver -> L7 Models

- L3 does NOT exist in HOC topology.
- hoc_spine is the single execution authority.
- Cross-domain coordination only in L4 hoc_spine.
- L2 must call L4, never L5/L6 directly.

## Layer Rules (Non-Negotiable)
From LAYER_MODEL + HOC topology:
- L2 API: HTTP boundary only. Input validation, auth/tenant extraction, translate to operation.
- L4 hoc_spine: orchestration only, no domain logic.
- L5 engines: business logic only, no DB/ORM imports, no cross-domain calls.
- L6 drivers: DB I/O only, no business conditionals.
- L7 models: data definition only.

## Driver/Engine Pattern (Locked)
- Engines decide. Drivers touch.
- `*_service.py` is banned in HOC.
- L4 must be `*_engine.py`, L6 must be `*_driver.py`.
- No DB/ORM imports inside engines.

## HOC API Wiring Rules
- All HOC routers must be included by an entrypoint.
- Allowed entrypoints:
  - `backend/app/main.py`
  - `backend/app/hoc/api/int/agent/main.py`
- Orchestrator handlers must be imported to populate registry at startup.

## Authority & Contracts (Legacy but Still Informative)
- Time, transaction, orchestration, and state authority must be centralized.
- Violations: direct time access, cross-domain DB writes, multiple orchestrators.

## Governance / Enforcement Scripts (Run When Relevant)
- `scripts/ci/check_layer_boundaries.py`
- `scripts/ops/hoc_cross_domain_validator.py`
(If these fail, do not proceed without approval.)

## Audit Expectations
When auditing HOC:
- Verify router wiring (include_router)
- Verify handler registry is imported
- Flag missing modules or imports
- Check L2 -> L4 -> L5 -> L6 path is respected
- Report dead/unused code with context (wiring + registry)

## Change Discipline
- Never delete or move files without explicit approval.
- Prefer minimal, reversible changes.
- If unsure about authority or ownership, pause and ask.
