# CHANGELOG_2026-02-11_HOC_DOC_SYNC.md

## Purpose
Single consolidated changelog for the 2026-02-11 HOC documentation sync.

## Scope
- Canonical usecase docs relocation and reconciliation
- UC-001 / UC-002 status alignment
- TODO plan audit signoff artifacts
- Domain literature updates for `integrations`, `account`, `api_keys`
- Project awareness pointer updates

## Canonical Root Decision
- Canonical usecase documentation root is now:
- `backend/app/hoc/docs/architecture/usecases/`

## Usecase Docs Changes

### Created
1. `backend/app/hoc/docs/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002_v2_remaining_punch_list.md`
- Strict unresolved-only punch list with exact file edits.

2. `backend/app/hoc/docs/architecture/usecases/AUDIT_SIGNOFF.md`
- Pass/fail matrix, verified evidence, residual risk note, signoff decision.

3. `backend/app/hoc/docs/architecture/usecases/TODO_PLAN.md`
- Focused plan to enforce DB-as-authority and cache-only connector registry contract.

4. `backend/app/hoc/docs/architecture/usecases/CHANGELOG_2026-02-11_HOC_DOC_SYNC.md`
- This file.

### Migrated/Relocated
1. Prior usecase docs from `docs/doc/architecture/usecases/` were moved to:
- `backend/app/hoc/docs/architecture/usecases/`

### Updated
1. `backend/app/hoc/docs/architecture/usecases/INDEX.md`
- Updated active documents list.
- Registered TODO and audit artifacts.
- Status reflects current canonical state (`UC-001 YELLOW`, `UC-002 YELLOW`).

2. `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
- Rewritten to canonical status snapshot.
- Captures implemented items and remaining-for-green items.

3. `backend/app/hoc/docs/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002_v2_plan.md`
- Path references updated to canonical root.
- Added link to strict remaining punch list.

4. `backend/app/hoc/docs/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002_v2_plan_implemented.md`
- Added staleness warning header:
- instructs readers to treat canonical linkage + remaining punch list as source of truth.

## Legacy Docs De-Authorization
- Added deprecation headers to non-canonical duplicates under:
- `backend/docs/doc/architecture/usecases/*`
- Headers point to canonical root:
- `backend/app/hoc/docs/architecture/usecases/`

## Project Awareness Update
1. `project_aware_agenticverz2.md`
- Updated load-order and quick-location pointers from old path:
- `docs/doc/architecture/usecases/*`
- to canonical path:
- `backend/app/hoc/docs/architecture/usecases/*`

## Domain Literature Deltas (2026-02-11 sections added)

### Integrations
1. `literature/hoc_domain/integrations/SOFTWARE_BIBLE.md`
2. `literature/hoc_domain/integrations/DOMAIN_CAPABILITY.md`
3. `literature/hoc_domain/integrations/INTEGRATIONS_CANONICAL_SOFTWARE_LITERATURE.md`

Added/updated:
- Canonical integrations L2 route ownership
- Write-path session wiring correction via `sync_session`
- L4 `_STRIP_PARAMS` contract hardening
- Cache-only authority contract for connector registry
- DB-only onboarding activation evidence + CI check 35 guardrail

### Account
1. `literature/hoc_domain/account/SOFTWARE_BIBLE.md`
2. `literature/hoc_domain/account/DOMAIN_CAPABILITY.md`
3. `literature/hoc_domain/account/ACCOUNT_CANONICAL_SOFTWARE_LITERATURE.md`

Added/updated:
- `POST /accounts/projects` canonical onboarding path
- SDK attestation persistence path and L4 dispatch
- Alembic migration reference for `sdk_attestations`
- Activation predicate enforcement for COMPLETE transitions

### API Keys
1. `literature/hoc_domain/api_keys/SOFTWARE_BIBLE.md`
2. `literature/hoc_domain/api_keys/DOMAIN_CAPABILITY.md`
3. `literature/hoc_domain/api_keys/API_KEYS_CANONICAL_SOFTWARE_LITERATURE.md`

Added/updated:
- Read/write ownership consolidated under `api_keys` domain directory
- Split URL policy documented (read `/api-keys`, write `/tenant/api-keys`)
- Legacy policy-path onboarding wrappers removed
- Onboarding advance hook retained in key creation flow

## Verification Notes
1. CI hygiene:
- `PYTHONPATH=. python3 backend/scripts/ci/check_init_hygiene.py --ci`
- result: pass, 0 blocking.

2. Activation predicate authority tests:
- `PYTHONPATH=. pytest -q tests/governance/t4/test_activation_predicate_authority.py`
- result: 9 passed.

## Residual Risk (Documented, Accepted)
- `connector_registry_driver` remains runtime in-memory cache for live connector instances.
- Authority boundary is now explicit: activation relies on persistent DB evidence only.
- CI check 35 blocks cache import/use inside activation predicate section.

## GREEN Closure (2026-02-11)

### GREEN_CLOSURE_PLAN_UC001_UC002 Execution

**Phase 1: Event Schema Contract**
- Created `event_schema_contract.py` — 9 required fields, fail-closed validation
- Wired into 3 emitters: lifecycle_provider, runtime_switch, onboarding_handler
- CI check 36 (`check_event_schema_contract_usage`) — BLOCKING
- 12 tests in `test_event_schema_contract.py` — all pass

**Phase 4: Activation Predicate Hardening**
- Full 2^4 test matrix (16 combinations) added
- Indirect cache coupling regression test added
- Total: 11 tests in `test_activation_predicate_authority.py` — all pass

**Phase 3: API Key Surface Policy Lock**
- Split URL policy documented as closed (not deferred)
- Invariant comments in aos_api_key.py, api_key_writes.py, onboarding_policy.py
- 11 tests in `test_api_key_surface_policy.py` — all pass

**Phase 2: UC-001 Endpoint-to-Operation Evidence**
- 48 canonical routes mapped (22 CUS, 21 INT, 5 FDR)
- Verifier: `scripts/verification/uc001_route_operation_map_check.py` — 100/100 checks pass

**Phase 5: Status Promotion**
- UC-001: `YELLOW` → `GREEN` in linkage doc
- UC-002: `YELLOW` → `GREEN` in linkage doc
- INDEX.md promotion deferred per user instruction

### Verification Results (2026-02-11)
1. CI hygiene: 36/36 checks pass, 0 blocking
2. Activation tests: 11/11 pass
3. Event schema tests: 12/12 pass
4. API key policy tests: 11/11 pass
5. Route mapping: 100/100 checks pass
6. UC validation: 19/19 pass
