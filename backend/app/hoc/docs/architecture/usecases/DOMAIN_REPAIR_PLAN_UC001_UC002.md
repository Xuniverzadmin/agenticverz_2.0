# Domain Repair Plan: UC-001 and UC-002

## Purpose
Execution-ready repair plan to enforce canonical domain authority, remove ownership drift, and make onboarding and monitoring auditable end-to-end.

## Scope Lock
Canonical domain authority is fixed as:
- `integrations`: onboarding integration setup authority (BYOK/managed LLM selection, credential refs, connector and environment setup, AOS SDK install and confirmation, project integration lifecycle)
- `accounts`: signup, subscription, and team/sub-tenant authority
- `api_keys`: Agenticverz access-key authority for authenticated platform actions
- `policies`: LLM run-governance authority only (not onboarding setup authority)

`UC-002` remains `RED` until write-path ownership migration is completed.

## Repair Sequence

### Phase 1: UC-002 First (Customer Onboarding)
High-risk path with current authority drift and fragmented write ownership.

1. Create canonical L2 route surfaces:
- `backend/app/hoc/api/cus/accounts/`
- `backend/app/hoc/api/cus/integrations/`
- `backend/app/hoc/api/cus/api_keys/`

2. Migrate ownership violations:
- Move account onboarding handlers from `backend/app/hoc/api/cus/policies/aos_accounts.py` to canonical `accounts` routes.
- Move integration onboarding handlers from `backend/app/hoc/api/cus/policies/aos_cus_integrations.py` to canonical `integrations` routes.
- Move API key write handlers from `backend/app/hoc/api/cus/logs/tenants.py` to canonical `api_keys` routes.
- Consolidate API key read and write authority in `api_keys`; do not split across domains.

3. Preserve compatibility during migration:
- Keep compatibility wrappers in old paths that delegate to canonical handlers.
- Mark wrappers deprecated with explicit target removal version/date.

4. Rewrite onboarding activation authority gate:
- Update `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`.
- Gate conditions must reference canonical domain ownership only.
- Activation predicate must require:
- project ready
- key/integration ready
- connector validated
- SDK attested

5. Harden integrations path:
- Fix runtime session wiring for integration writes (`session` must be valid and consistent through L2-L4-L5-L6).
- Resolve facade/engine contract mismatches on enable/delete/test flows.
- Replace in-memory or demo connector setup behavior with persistent validated flow.
- Add explicit AOS SDK attestation artifact model and persistence.

6. Harden API key path:
- Canonical operations: issue, revoke, rotate, read under `api_keys`.
- Persist only hashed/derived key material.
- Emit auditable lifecycle events for all key operations.

### Phase 2: UC-001 Second (LLM Run Monitoring)
Stabilize linkage and orchestration integrity after onboarding authority is corrected.

1. Execute endpoint-to-operation call-chain audit for:
- `cust` monitoring routes
- `int` platform monitoring and recovery routes
- `fdr` founder metrics and operations routes

2. Enforce layer integrity:
- L2 -> L4 (`hoc_spine`) -> L5 -> L6
- detect and remove unauthorized direct bypasses where orchestration is mandated

3. Normalize legacy contract drift:
- document or refactor ambiguous `L5_engines` and `L6_drivers` contracts where they hide layer drift

4. Enforce monitoring invariants in runtime validation:
- required metadata for each run: `run_id`, `tenant_id`, `project_id`, policy/control versions, sequence continuity

## Shared Event and Audit Model
Apply to both UC-001 and UC-002:

1. Enforce minimum event schema:
- `event_id`
- `event_type`
- `tenant_id`
- `project_id`
- `actor_type`
- `actor_id`
- `decision_owner`
- `sequence_no`
- `schema_version`

2. Add ownership-violation detector:
- CI audit check fails when onboarding capability appears outside canonical domain path ownership.

3. Define immutable evidence queries per use case:
- project and state transitions
- key lifecycle events
- connector validation evidence
- SDK attestation evidence
- run sequence and trace continuity

## Test Plan

1. Unit tests:
- canonical route ownership tests per domain
- onboarding activation predicate tests
- API key lifecycle tests (issue/revoke/rotate/read)

2. Integration tests:
- UC-ONB-01 managed LLM onboarding flow
- UC-ONB-02 BYOK onboarding flow
- connector validation failure flows
- SDK attestation failure flows

3. Regression tests:
- legacy wrapper routes remain functional during deprecation window
- `UC-001` monitoring paths still emit expected metrics and events

## PR Delivery Order

1. PR-1: docs + authority lock + index/status updates
2. PR-2: canonical `accounts` route migration + tests
3. PR-3: canonical `integrations` route migration + connector/session/SDK attestation fixes
4. PR-4: canonical `api_keys` consolidation + lifecycle audit events
5. PR-5: `onboarding_policy.py` activation gate rewrite + full UC-002 integration tests
6. PR-6: UC-001 call-chain hardening + orchestration bypass fixes
7. PR-7: remove deprecated wrappers after downstream adoption

## Definition of Done

1. `UC-002`: `RED -> YELLOW` only when ownership violations are migrated and covered by tests.
2. `UC-002`: `YELLOW -> GREEN` only when activation gate and audit evidence checks pass in CI.
3. `UC-001`: `YELLOW -> GREEN` only when endpoint call-chain verification is complete and no unauthorized bypass remains.
