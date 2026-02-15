# GREEN_CLOSURE_PLAN_UC001_UC002.md

## Objective
Move `UC-001` and `UC-002` from `YELLOW` to `GREEN` using code/test/doc completeness only.
No real customer LLM key or real customer environment is required in this phase.

## Scope Boundaries
1. In scope: architecture correctness, authoritative ownership, runtime event-contract enforcement, endpoint-to-handler evidence, CI/test guardrails.
2. Out of scope: production go-live validation with real customer secrets/infrastructure.

## GREEN Definition (This Repo)
1. `UC-001` is `GREEN` when canonical endpoint-to-operation mapping is complete for `cust,int,fdr` and minimum event schema is enforced at runtime for monitored event emission paths.
2. `UC-002` is `GREEN` when onboarding authority paths are stable, activation predicate remains DB-authoritative, minimum event schema is enforced for onboarding lifecycle events, and API key URL policy is explicitly locked and tested.

## Phase 1: Lock Canonical Event Schema Contract
### Target files
- `backend/app/hoc/cus/hoc_spine/authority/runtime_switch.py`
- `backend/app/hoc/cus/hoc_spine/authority/lifecycle_provider.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`
- `backend/scripts/ci/check_init_hygiene.py`
- `backend/tests/governance/t4/` (new tests)

### Work
1. Add a shared event payload validator module (new):
- `backend/app/hoc/cus/hoc_spine/authority/event_schema_contract.py`
2. Enforce required fields at emit time:
- `event_id`, `event_type`, `tenant_id`, `project_id`, `actor_type`, `actor_id`, `decision_owner`, `sequence_no`, `schema_version`.
3. Wire validator into onboarding/lifecycle/governance emitters.
4. Add CI check that fails when known emitters bypass validator.

### Acceptance
1. Missing required field causes structured rejection/error path (no silent pass).
2. CI includes blocking check for contract usage in authoritative emitters.
3. Tests prove valid payload passes and invalid payload fails.

## Phase 2: UC-001 Complete Endpoint-to-Operation Evidence
### Target files
- `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
- `backend/app/hoc/docs/architecture/usecases/AUDIT_SIGNOFF.md`
- `backend/scripts/verification/` (new mapping verifier)

### Work
1. Publish explicit endpoint->L4 operation tables for:
- `cust`
- `int`
- `fdr`
2. Include file-path evidence per route family.
3. Add verifier script (new):
- `backend/scripts/verification/uc001_route_operation_map_check.py`
4. Script checks:
- every documented endpoint has operation mapping evidence;
- no documented endpoint bypasses L4 dispatch patterns.

### Acceptance
1. Canonical linkage doc has complete mapping coverage for UC-001 audiences.
2. Verification script passes in CI/test run.

## Phase 3: UC-002 API Key Surface Policy Lock
### Target files
- `backend/app/hoc/api/cus/api_keys/aos_api_key.py`
- `backend/app/hoc/api/cus/api_keys/api_key_writes.py`
- `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`
- `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
- `backend/tests/governance/t4/` (new policy tests)

### Work
1. Keep split URLs (`/api-keys` read, `/tenant/api-keys` write) as explicit canonical policy.
2. Add invariant comments and tests proving:
- onboarding gate uses `/tenant/api-keys` semantics;
- read-only flows do not imply onboarding progression.
3. Document this as final policy decision in canonical linkage doc.

### Acceptance
1. Policy tests fail on accidental route/gate drift.
2. Canonical docs state split is intentional and closed, not deferred.

## Phase 4: UC-002 Activation Predicate Hardening
### Target files
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`
- `backend/tests/governance/t4/test_activation_predicate_authority.py`
- `backend/scripts/ci/check_init_hygiene.py`

### Work
1. Keep activation predicate DB-authoritative for key/connector/sdk evidence.
2. Add test matrix for negative and positive transitions with synthetic fixtures only.
3. Keep check 35 blocking and add one regression case for indirect cache coupling.

### Acceptance
1. Predicate cannot become true from cache-only state.
2. All authority tests pass.

## Phase 5: Canonical Docs and Status Promotion
### Target files
- `backend/app/hoc/docs/architecture/usecases/INDEX.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
- `backend/app/hoc/docs/architecture/usecases/CHANGELOG_2026-02-11_HOC_DOC_SYNC.md`
- `backend/app/hoc/docs/architecture/usecases/AUDIT_SIGNOFF.md`

### Work
1. Update UC sections with closure evidence references.
2. Promote statuses:
- `UC-001`: `YELLOW -> GREEN`
- `UC-002`: `YELLOW -> GREEN`
3. Append changelog entries for each closure item.

### Acceptance
1. `INDEX.md` and linkage doc show matching `GREEN` statuses.
2. Signoff doc references exact verification commands and outputs.

## Execution Order for Claude
1. Phase 1 (event schema contract).
2. Phase 4 (activation hardening safety net).
3. Phase 3 (API key policy lock + tests).
4. Phase 2 (UC-001 mapping publication + verifier).
5. Phase 5 (status promotion + docs sync).

## Mandatory Verification Commands
1. `cd /root/agenticverz2.0/backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
2. `cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/governance/t4/test_activation_predicate_authority.py`
3. `cd /root/agenticverz2.0/backend && PYTHONPATH=. python3 scripts/verification/uc001_uc002_validation.py --run-ci --run-tests`
4. `cd /root/agenticverz2.0/backend && PYTHONPATH=. python3 scripts/verification/uc001_route_operation_map_check.py`

## Final Deliverables
1. Updated code, tests, and CI checks per phases above.
2. Updated canonical docs showing `GREEN` with evidence.
3. New implementation evidence file:
- `backend/app/hoc/docs/architecture/usecases/GREEN_CLOSURE_PLAN_UC001_UC002_implemented.md`
