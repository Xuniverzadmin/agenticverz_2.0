# HANDOVER_UC_MONITORING_TO_CLAUDE.md

## Objective
Execute UC-MON implementation in controlled iterations and produce implementation evidence documents after each iteration.

## Canonical Inputs (Read First)
1. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_USECASE_PLAN.md`
2. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_IMPLEMENTATION_METHODS.md`
3. `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
4. `backend/app/hoc/docs/architecture/usecases/INDEX.md`

## Execution Mode
1. Local-first (non-CI-blocking) for first 2-3 iterations.
2. Use `uc_mon_validation.py` in advisory mode during early iterations.
3. Promote to strict and CI only after checks stabilize.

## Phase Plan for Claude

### Iteration 1 (Foundational)
1. Create route mapping artifact:
- `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_ROUTE_OPERATION_MAP.md`
2. Add UC-MON verifier script stubs:
- `backend/scripts/verification/uc_mon_route_operation_map_check.py`
- `backend/scripts/verification/uc_mon_event_contract_check.py`
- `backend/scripts/verification/uc_mon_storage_contract_check.py`
- `backend/scripts/verification/uc_mon_deterministic_read_check.py`
3. Keep checks advisory.

### Iteration 2 (Contracts + Storage)
1. Implement event-contract checks per UC-MON events (base + domain extension fields).
2. Add migrations for planned fields:
- `128_monitoring_activity_feedback_contracts.py`
- `129_monitoring_incident_resolution_recurrence.py`
- `130_monitoring_controls_binding_fields.py`
- `131_monitoring_analytics_reproducibility_fields.py`
- `132_monitoring_logs_replay_mode_fields.py`
3. Implement corresponding storage contract verifier logic.

### Iteration 3 (Deterministic Reads + Hardening)
1. Formalize `as_of` deterministic read behavior on priority read endpoints.
2. Implement deterministic-read verifier logic.
3. Add aggregate UC-MON runner:
- `backend/scripts/verification/uc_mon_validation.py` (already created; extend checks from advisory stubs to real checks).

## Required Deliverables

### A) Counter-Implementation Evidence Doc (required)
Create:
- `backend/app/hoc/docs/architecture/usecases/HANDOVER_UC_MONITORING_TO_CLAUDE_implemented.md`

Must include:
1. Iteration-by-iteration execution log.
2. Files created/modified per iteration.
3. Validation command outputs and summary table.
4. Remaining gaps (if any) with explicit blockers.
5. Recommendation: stay advisory / move strict / wire CI.

### B) Status Update
Update:
- `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_USECASE_PLAN.md`

Add:
1. Completed items.
2. Remaining items.
3. Current phase marker.

## Mandatory Validation Commands (Each Iteration)
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py
```

When relevant checks are implemented:
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_route_operation_map_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py
```

For strict adoption candidate:
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Acceptance Criteria for Handover Completion
1. Handover implementation evidence doc exists and is complete.
2. Route map doc exists with grep-checkable linkage.
3. UC-MON verifier scripts exist and run.
4. `uc_mon_validation.py` shows decreasing WARN trend across iterations.
5. No conflict with canonical authority boundaries (`policies` proposal != enforcement until canonical accept flow).

## Guardrails
1. Do not mark UC-MON as `GREEN` during advisory stage.
2. Do not wire strict checks into CI until explicitly approved after stable iteration evidence.
3. Keep all docs under canonical root:
- `backend/app/hoc/docs/architecture/usecases/`
