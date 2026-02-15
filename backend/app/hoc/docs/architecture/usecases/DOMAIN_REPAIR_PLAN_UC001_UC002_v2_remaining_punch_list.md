# UC-001/UC-002 v2 Remaining-Only Punch List

## Scope
Only unresolved items are listed. Completed items are excluded.

## P0 Blockers (Must Close for UC-002 RED -> YELLOW)

1. Fix integrations L2 session wiring for write operations.
- Edit `backend/app/hoc/api/cus/integrations/aos_cus_integrations.py`.
- Add sync session DI: `session=Depends(get_sync_session_dep)` on write endpoints:
- `POST /integrations`
- `PUT /integrations/{integration_id}`
- `DELETE /integrations/{integration_id}`
- `POST /integrations/{integration_id}/enable`
- `POST /integrations/{integration_id}/disable`
- `POST /integrations/{integration_id}/test`
- Dispatch pattern must pass:
- `OperationContext(session=None, tenant_id=..., params={"method": ..., "sync_session": session, ...})`
- Keep list/read endpoints on existing read path unless they require sync writes.

2. Align integrations handler contract stripping.
- Edit `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/integrations_handler.py`.
- Ensure `sync_session` is stripped from kwargs before facade method calls.
- Required pattern in all 3 handlers:
- `kwargs = {k: v for k, v in ctx.params.items() if k not in {"method", "sync_session"}}`

3. Replace connector in-memory source-of-truth with persistent store.
- Edit `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py`.
- Remove authoritative use of:
- `self._connectors`
- `self._tenant_connectors`
- Implement DB-backed CRUD/read/list methods for connectors.
- Keep transaction ownership consistent (L4 commit boundary, L6 no commit).
- Add/adjust schemas/drivers as needed for persistent connector entities.

4. Ensure activation predicate uses persistent connector evidence.
- Edit `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`.
- In `_check_activation_conditions` and `_async_check_activation_conditions`, confirm connector readiness is computed from persistent connector validation evidence (not in-memory registry state).
- Predicate keys must remain:
- `project_ready`, `key_ready`, `connector_validated`, `sdk_attested`.

## P1 Closure (Required for Clean Canonical Status)

5. Canonicalize UC statuses and evidence in this docs root.
- Edit `backend/app/hoc/docs/architecture/usecases/INDEX.md`.
- Keep `UC-001 = YELLOW`, `UC-002 = RED` until P0 closes.
- Edit `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`.
- Keep unresolved blockers explicit with file references.

6. De-authorize stale duplicate docs.
- Add deprecation header to files under `backend/docs/doc/architecture/usecases/*` stating non-canonical status.
- Point to canonical root: `backend/app/hoc/docs/architecture/usecases/`.

## P2 (Needed for GREEN, not for RED->YELLOW)

7. Event schema runtime enforcement.
- Add runtime validator in event write path(s) for:
- `event_id`, `event_type`, `tenant_id`, `project_id`, `actor_type`, `actor_id`, `decision_owner`, `sequence_no`, `schema_version`.
- Update tests for fail-closed behavior when fields are missing.

8. API key URL unification decision execution (optional policy debt).
- Current policy accepted split:
- read: `/api-keys`
- write: `/tenant/api-keys`
- If unified, edit:
- `backend/app/hoc/api/cus/api_keys/aos_api_key.py`
- `backend/app/hoc/api/cus/api_keys/api_key_writes.py`
- `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`
- Update route tests and docs accordingly.

## Verification Checklist
1. `PYTHONPATH=. python3 backend/scripts/ci/check_init_hygiene.py --ci` returns 0 blocking.
2. Integration write endpoint tests verify non-null `sync_session` dispatch.
3. Connector persistence tests verify durable create/read/list/delete across process restart.
4. Onboarding activation tests fail when connector evidence missing.
5. Canonical docs status remains synchronized in this root.
