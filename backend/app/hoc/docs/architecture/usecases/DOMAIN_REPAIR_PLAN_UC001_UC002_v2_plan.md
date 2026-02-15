# DOMAIN_REPAIR_PLAN_UC001_UC002 v2 Plan

## Purpose
Execution-ready v2 plan to:
- remove tombstones and complete canonical domain migration
- close remaining UC-001 and UC-002 critical gaps
- enforce CI-level ownership invariants
- reconcile dual documentation sources into one canonical path

## Scope Lock (Mandatory)
1. Canonical domain namespace:
- folder/domain name: `account`
- HTTP route namespace: `/accounts`

2. Canonical usecase docs root:
- `backend/app/hoc/docs/architecture/usecases/*`

3. Non-canonical duplicate docs:
- `backend/docs/doc/architecture/usecases/*` must be merged into canonical docs or removed from authority usage.

## Phase 1: De-Tombstone Migration
Goal: complete migration by deleting compatibility wrappers and forcing canonical imports.

1. Verify importer zero-state for old module paths:
- `app.hoc.api.cus.policies.aos_accounts`
- `app.hoc.api.cus.policies.aos_cus_integrations`
- `app.hoc.api.cus.policies.aos_api_key`

2. Delete old tombstone modules:
- `backend/app/hoc/api/cus/policies/aos_accounts.py`
- `backend/app/hoc/api/cus/policies/aos_cus_integrations.py`
- `backend/app/hoc/api/cus/policies/aos_api_key.py`

3. Fix all broken imports after deletion to canonical owners:
- `backend/app/hoc/api/cus/account/aos_accounts.py`
- `backend/app/hoc/api/cus/integrations/aos_cus_integrations.py`
- `backend/app/hoc/api/cus/api_keys/aos_api_key.py`

4. Update stale architecture/audit references to migrated paths:
- `backend/docs/architecture/hoc/L2_L4_CALL_MAP.csv`
- `backend/docs/architecture/hoc/L2_ROUTER_INVENTORY.md`
- `backend/docs/architecture/hoc/DOMAIN_TRUTH_MAP.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`

## Phase 2: Onboarding Gate and Activation Predicate (Critical)
Goal: ensure onboarding gate semantics align with moved endpoints and activation invariants.

1. Keep `/tenant/api-keys` mapping and pattern in:
- `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`

2. Wire activation predicate into runtime flow (not definition-only):
- `check_activation_predicate(...)` must be called by onboarding completion/advance path in L4.

3. Activation requirements must be enforced as one deterministic gate:
- `project_ready`
- `key_ready`
- `connector_validated`
- `sdk_attested`

## Phase 3: UC-002 Functional Gap Closure
Goal: close non-structural onboarding gaps.

1. Project creation capability under canonical account domain:
- keep/validate `POST /accounts/projects` in `backend/app/hoc/api/cus/account/aos_accounts.py`
- verify full L2 -> L4 -> L5 -> L6 execution chain.

2. Integrations session wiring and contract integrity:
- `backend/app/hoc/api/cus/integrations/aos_cus_integrations.py` must stop write dispatch with `session=None`.
- pass required session object via accepted L4 contract (`ctx.session` or `params["sync_session"]`).
- verify enable/disable/delete/test contract dispatch consistency.

3. Connector persistence hardening:
- remove in-memory connector registry behavior as source-of-truth.
- migrate connector state to persistent driver-backed storage with auditable reads/writes.
- primary target: `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py`.

4. SDK attestation artifact path completion:
- `backend/app/hoc/api/int/general/sdk.py` must pass valid session context to `account.sdk_attestation`.
- ensure L4 handler no longer fails with missing session in normal handshake flow.
- add Alembic migration for `sdk_attestations` table to satisfy L6 driver writes.

## Phase 4: CI Ownership Enforcement (Blocking)
Goal: enforce canonical domain ownership as hard CI invariant.

1. Keep `check_l2_domain_ownership` in:
- `backend/scripts/ci/check_init_hygiene.py`

2. Ensure onboarding authority violations are blocking (not advisory).

3. Add fail-loud check for deleted old module imports.

4. Allowlist policy:
- no new frozen allowlist entries for onboarding authority drift without explicit governance sign-off.

## Phase 5: UC-001 Audit Correctness
Goal: ensure UC-001 status reflects complete and accurate evidence.

1. Re-audit real `int` and `fdr` route files only.

2. Remove any non-existent endpoint file references from usecase docs.

3. Keep UC-001 at `YELLOW` until endpoint-to-operation mapping is complete for all 3 audiences.

## Phase 6: API Key URL Coherence
Goal: resolve split URL semantics while keeping single canonical domain owner.

1. Decide canonical lifecycle URL policy:
- Option A (preferred): unify read/write under `/api-keys`
- Option B: keep read `/api-keys` + write `/tenant/api-keys` with explicit invariants and rationale

2. Update onboarding policy endpoint map to chosen policy.

3. Update tests and docs to chosen policy.

4. Maintain single write authority in `api_keys` domain regardless of URL shape.

## Phase 7: Documentation Reconciliation
Goal: eliminate dual-source governance drift.

1. Merge or port updates from:
- `backend/docs/doc/architecture/usecases/*`
into:
- `backend/app/hoc/docs/architecture/usecases/*`

2. Canonical files to update:
- `backend/app/hoc/docs/architecture/usecases/INDEX.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
- `backend/app/hoc/docs/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002.md`
- this file (`DOMAIN_REPAIR_PLAN_UC001_UC002_v2_plan.md`)

4. Strict unresolved-only items live in:
- `backend/app/hoc/docs/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002_v2_remaining_punch_list.md`

3. Mark canonical source-of-truth in project awareness doc.

## Verification Gate (Before Status Changes)
1. CI:
- `PYTHONPATH=. python3 backend/scripts/ci/check_init_hygiene.py --ci`
- expected: `0` blocking violations

2. Import hygiene:
- zero imports of deleted old modules

3. Endpoint coverage checks:
- accounts project create
- integrations create/update/enable/disable/test with valid session wiring
- api keys list/create/revoke on chosen canonical URL policy
- sdk handshake persists attestation record

4. DB checks:
- `sdk_attestations` table exists
- handshake produces persisted attestation row

5. Usecase status criteria:
- `UC-002`: `RED -> YELLOW` only after ownership + critical functional fixes + verification gate pass
- `UC-002`: `YELLOW -> GREEN` only after activation gate wiring + audit evidence completeness + CI enforcement closure
- `UC-001`: remain `YELLOW` until full endpoint-to-operation mapping is documented and verified

## PR Sequencing (Recommended)
1. PR-1: Phase 1 de-tombstone migration + import fixes
2. PR-2: Phase 2 onboarding gate wiring + Phase 3 session/attestation fixes
3. PR-3: Phase 3 connector persistence + Alembic migration for SDK attestation
4. PR-4: Phase 4 CI enforcement hardening
5. PR-5: Phase 5 UC-001 audit corrections + Phase 6 API key URL decision implementation
6. PR-6: Phase 7 docs reconciliation + final status synchronization
