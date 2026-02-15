# HANDOVER_BATCH_02_LOGS_ACTIVITY.md

## Objective
Close logs/activity core-function gaps and promote related UCs from `YELLOW/RED` toward `GREEN`.

## UC Scope
- `UC-003`, `UC-006`, `UC-010`, `UC-017`

## Tasks
1. Implement activity feedback lifecycle end-to-end:
- ack/suppress with TTL
- expiry/reopen semantics
- bulk feedback with `target_set_hash` and `target_count`
2. Wire required activity events:
- `SignalAcknowledged`, `SignalSuppressed`, `SignalFeedbackExpired|SignalFeedbackEvaluated`, `BulkSignalFeedbackApplied`
3. Complete logs replay-mode contract:
- `FULL|TRACE_ONLY` runtime labeling
- replay attempt artifact/version persistence
- redaction version lineage eventing
4. Ensure `as_of` determinism remains stable for activity/log read surfaces and response metadata includes effective `as_of`.

## Deliverables
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_02_LOGS_ACTIVITY_implemented.md`
2. Evidence queries and example payloads for activity/log events.

## Validation Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Exit Criteria
1. Activity lifecycle behaviors are implemented and auditable.
2. Replay mode labeling and integrity versioning implemented in runtime paths.
3. No determinism regressions.
