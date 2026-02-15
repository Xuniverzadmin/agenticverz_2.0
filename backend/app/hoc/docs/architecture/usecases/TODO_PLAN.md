# TODO_PLAN.md

## Objective
Close the remaining production-stability gap by enforcing connector authority boundaries:
- DB evidence is authoritative.
- In-memory connector registry is cache-only.

## Current Gap
- `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` still stores runtime state in `_connectors` / `_tenant_connectors`.
- This is acceptable only as non-authoritative cache, but that contract is not hard-enforced yet.

## Work Plan

### 1) Authority Contract Lock
1. Add explicit module contract comments in:
- `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`
2. State clearly:
- ConnectorRegistry is runtime cache only.
- Onboarding/activation must use DB evidence only (`cus_integrations`, validation evidence table if present).

### 2) Enforce Read Paths for Activation
1. Keep activation checks DB-based in:
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`
2. Add negative test to ensure activation does not read connector cache state.

### 3) Persisted Connector Validation Evidence
1. Ensure connector validation outcomes are persisted in durable storage.
2. If missing, add migration/table for validation evidence.
3. Update activation predicate checks to consume persisted validation state.

### 4) Guardrails in CI
1. Add CI/static check:
- fail if onboarding activation imports or queries `connector_registry_driver` in authoritative decision flow.
2. Keep `check_l2_domain_ownership` blocking.

### 5) Runtime Observability
1. Add log markers/metrics for:
- activation predicate input sources (DB vs cache)
- connector validation persistence success/failure
2. Ensure logs include tenant/project context without secrets.

## Acceptance Criteria
1. Activation path uses only persistent evidence for:
- `project_ready`
- `key_ready`
- `connector_validated`
- `sdk_attested`
2. ConnectorRegistry remains cache-only and non-authoritative by contract and tests.
3. CI fails if authoritative flow attempts to use in-memory connector cache as truth.
4. Usecase docs remain synchronized:
- `backend/app/hoc/docs/architecture/usecases/INDEX.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`

## Verification Checklist
1. `PYTHONPATH=. python3 backend/scripts/ci/check_init_hygiene.py --ci` passes.
2. Unit tests for activation predicate source-of-truth pass.
3. Integration test: connector cache empty + DB evidence present still activates correctly.
4. Integration test: cache populated + DB evidence absent does not activate.
