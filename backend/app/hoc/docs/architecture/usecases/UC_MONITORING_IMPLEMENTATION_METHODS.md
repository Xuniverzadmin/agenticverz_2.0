# UC_MONITORING_IMPLEMENTATION_METHODS.md

## Purpose
Define implementation methods for the monitoring usecase gap closures, grounded in current codebase layout.

## Source Plan
- `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_USECASE_PLAN.md`

## 1) Route -> Handler -> Engine -> Store Mapping (grep-checkable)

### Current L2 anchors (confirmed)
- `backend/app/hoc/api/cus/activity/activity.py`
- `backend/app/hoc/api/cus/incidents/incidents.py`
- `backend/app/hoc/api/cus/controls/controls.py`
- `backend/app/hoc/api/cus/analytics/*.py`
- `backend/app/hoc/api/cus/logs/*.py`
- `backend/app/hoc/api/cus/policies/*.py`

### Domain L5/L6 anchors (confirmed)
- Activity: `backend/app/hoc/cus/activity/L5_engines/activity_facade.py`, `backend/app/hoc/cus/activity/L5_engines/signal_feedback_engine.py`, `backend/app/hoc/cus/activity/L6_drivers/activity_read_driver.py`
- Incidents: `backend/app/hoc/cus/incidents/L5_engines/incidents_facade.py`, `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py`, `backend/app/hoc/cus/incidents/L6_drivers/incident_*`
- Controls: `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`, `backend/app/hoc/cus/controls/L5_engines/threshold_engine.py`, `backend/app/hoc/cus/controls/L6_drivers/*`
- Analytics: `backend/app/hoc/cus/analytics/L5_engines/analytics_facade.py`, `backend/app/hoc/cus/analytics/L5_engines/detection_facade.py`, `backend/app/hoc/cus/analytics/L6_drivers/analytics_read_driver.py`
- Logs: `backend/app/hoc/cus/logs/L5_engines/trace_api_engine.py`, `backend/app/hoc/cus/logs/L5_engines/replay_determinism.py`, `backend/app/hoc/cus/logs/L6_drivers/pg_store.py`
- Policies: `backend/app/hoc/cus/policies/L5_engines/policy_proposal_engine.py`, `backend/app/hoc/cus/policies/L5_engines/policy_rules_engine.py`, `backend/app/hoc/cus/policies/L6_drivers/policy_*`

### Required mapping artifact
Create:
- `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_ROUTE_OPERATION_MAP.md`

Per row include:
1. Route (`method + path`)
2. L2 function (`module:function`)
3. L4 operation key
4. L5 entry function
5. L6 driver/store function
6. Required event emissions
7. Deterministic read behavior (`as_of` required/optional)

### Grep checks (mandatory)
```bash
cd /root/agenticverz2.0/backend
rg -n \"@router\\.(get|post|put|delete|patch)\" app/hoc/api/cus/activity/activity.py app/hoc/api/cus/incidents/incidents.py app/hoc/api/cus/controls/controls.py app/hoc/api/cus/analytics app/hoc/api/cus/logs app/hoc/api/cus/policies
rg -n \"OperationContext|get_operation_registry|registry\\.execute\" app/hoc/api/cus
rg -n \"activity\\.query|incidents\\.query|controls\\.query|analytics\\.|logs\\.|policies\\.\" app/hoc/api/cus app/hoc/cus/hoc_spine
```

## 2) Event Schema Payload Contract (per event type)

### Base contract (already canonical)
Use validator:
- `backend/app/hoc/cus/hoc_spine/authority/event_schema_contract.py`

Required fields:
- `event_id`, `event_type`, `tenant_id`, `project_id`, `actor_type`, `actor_id`, `decision_owner`, `sequence_no`, `schema_version`

### Domain extension fields (new requirement)
1. Activity feedback events:
- `signal_id`, `feedback_state`, `as_of`, `ttl_seconds`, `expires_at`, `bulk_action_id?`, `target_set_hash?`
2. Incident lifecycle events:
- `incident_id`, `incident_state`, `resolution_type?`, `recurrence_signature?`, `signature_version?`
3. Controls evaluation events:
- `run_id`, `control_set_version`, `override_ids_applied`, `resolver_version`, `decision`
4. Analytics dataset events:
- `dataset_id`, `dataset_version`, `input_window_hash`, `as_of`, `compute_code_version`
5. Logs replay events:
- `run_id`, `replay_attempt_id`, `replay_mode`, `replay_artifact_version`, `reason?`

### Validation failure behavior (must implement)
1. Reject emission with `EventSchemaViolation` (fail-closed in authoritative paths).
2. Emit structured logger warning/error with missing/invalid keys.
3. Return non-2xx from write endpoint when authoritative event emission is required and fails.

## 3) DB/Storage Contract + Migrations

### New/extended persistence fields
1. Activity feedback store:
- `ttl_seconds`, `expires_at`, `bulk_action_id`, `target_set_hash`, `target_count`
2. Incident store:
- `resolution_type`, `resolution_summary`, `postmortem_artifact_id`, `recurrence_signature`, `signature_version`
3. Controls evaluation evidence:
- `control_set_version`, `override_ids_applied` (json), `resolver_version`
4. Analytics artifact store:
- `dataset_version`, `input_window_hash`, `as_of`, `compute_code_version`
5. Logs replay store:
- `replay_mode` (`FULL|TRACE_ONLY`), `replay_attempt_id`, `replay_artifact_version`, `trace_completeness_status`

### Migration plan
Create sequential Alembic migrations under:
- `backend/alembic/versions/`

Recommended split:
1. `128_monitoring_activity_feedback_contracts.py`
2. `129_monitoring_incident_resolution_recurrence.py`
3. `130_monitoring_controls_binding_fields.py`
4. `131_monitoring_analytics_reproducibility_fields.py`
5. `132_monitoring_logs_replay_mode_fields.py`

## 4) CI/Verifier Scripts (UC-MON pack)

Create:
1. `backend/scripts/verification/uc_mon_route_operation_map_check.py`
2. `backend/scripts/verification/uc_mon_event_contract_check.py`
3. `backend/scripts/verification/uc_mon_storage_contract_check.py`
4. `backend/scripts/verification/uc_mon_deterministic_read_check.py`
5. `backend/scripts/verification/uc_mon_validation.py` (aggregator)

Update CI gate:
- `backend/scripts/ci/check_init_hygiene.py`

Add blocking checks:
1. UC-MON route mapping file exists and passes verifier.
2. Authoritative emitters for new UC-MON events call `validate_event_payload`.
3. No direct L2->L5/L6 bypass in new/updated UC-MON endpoints.
4. Deterministic read endpoints enforce or accept `as_of` consistently.

### Local-first validation scaffold (active now)
- `backend/scripts/verification/uc_mon_validation.py`

Run (advisory mode, current default):
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py
```

Run strict (future CI candidate):
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

Adoption policy:
1. Keep advisory for first 2-3 implementation iterations.
2. Move to strict locally once first verifier + migration checks land.
3. Wire strict mode into CI only after stable green runs across consecutive iterations.

## 5) Deterministic Read Contract (`as_of`)

### Contract
1. Read endpoints serving derived/ranked/filtered data must accept `as_of` (ISO-8601 UTC).
2. If absent, service generates `as_of` once per request and returns it in response metadata.
3. Same query filters + same `as_of` + same dataset/version must produce stable ordering and values.
4. Any TTL/expiry logic must evaluate against `as_of`, not wall-clock mid-query.

### Endpoints to formalize first
1. Activity reads in `backend/app/hoc/api/cus/activity/activity.py`
2. Incident reads in `backend/app/hoc/api/cus/incidents/incidents.py`
3. Analytics reads in `backend/app/hoc/api/cus/analytics/*.py`
4. Logs trace/replay reads in `backend/app/hoc/api/cus/logs/traces.py` and related logs routes

### Response metadata requirement
All deterministic reads return:
- `as_of`
- `data_version` (or equivalent dataset/control/policy version reference)
- `query_hash` (optional but recommended)

## Skeptical Review Gate
Before status promotion, run a skeptical pass:
1. Try to falsify deterministic behavior by re-running same request with same `as_of`.
2. Try to bypass policy authority by accepting proposal through non-canonical endpoint.
3. Try to mutate replay mode without corresponding event/version updates.

Promotion to `YELLOW`/`GREEN` blocked unless skeptical checks pass and are documented.
