# HOC_ACTIVITY_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented

**Created:** 2026-02-20 UTC
**Executor:** Claude
**Status:** DONE

## 1. Execution Summary

- Overall result: ALL 5 TASKS COMPLETE — activity domain runtime-invariant correctness closed with fail-closed proofs, _invariant_mode leakage fix, production-wiring leakage proofs, and explicit no-alias rationale (final: 24 tests, 246 t5 suite)
- Scope delivered: BI-ACTIVITY-001 fail-closed enforcement for run.create (tenant_id + project_id), _invariant_mode internal key stripping in ActivityQueryHandler + ActivityTelemetryHandler, MONITOR/STRICT mode proofs, OperationRegistry dispatch proofs, production-wiring leakage proofs (real registry.execute() path), non-trigger proofs, real handler registration proof
- Scope not delivered: None — full plan scope delivered

## 2. Task Completion Matrix

| Task ID | Status | Evidence | Notes |
|---------|--------|----------|-------|
| AC-DELTA-01 | DONE | Section 3 — Alias Decision | No alias added: activity.* operations do not create runs. BI-ACTIVITY-001 guards run.create wherever it occurs. |
| AC-DELTA-02 | DONE | `activity_handler.py` — 2 handlers fixed | Stripped `_invariant_mode` and all `_`-prefixed keys from kwargs in ActivityQueryHandler + ActivityTelemetryHandler |
| AC-DELTA-03 | DONE | `tests/governance/t5/test_activity_runtime_delta.py` — 24 tests, 6 classes | All 24 green |
| AC-DELTA-04 | DONE | Section 4 below | 5/5 verification commands pass: 24 domain, 246 t5 suite, CI all green |
| AC-DELTA-05 | DONE | This file + tracker row updated | activity row DONE (2026-02-20), update log appended |

## 3. Alias Decision — NO ALIAS ADDED

**Question:** Does any real L4 dispatch operation in the activity domain correspond to `run.create`?

**Answer:** No. The activity domain registers these L4 operations:
- `activity.query` — read operations (get_runs, get_run_detail, etc.)
- `activity.signal_fingerprint` — pure computation
- `activity.signal_feedback` — feedback write operations
- `activity.telemetry` — telemetry ingestion/query
- `activity.discovery` — discovery ledger
- `activity.orphan_recovery` — orphan run recovery

None of these semantically represent "creating a run." Run creation occurs in the agent/runtime domain, not the activity monitoring domain. Adding an alias would be semantically incorrect and could cause false invariant failures on read operations.

**Rationale:** The activity domain **monitors** runs — it does not **create** them. BI-ACTIVITY-001 is correctly scoped to `run.create` and will fire whenever run creation is dispatched through the registry, regardless of which domain handler owns that operation. No activity-domain alias is needed or appropriate.

## 4. Evidence and Validation

### Files Changed (self-reported; both plan docs are untracked)

| File | Change | Git Status |
|------|--------|------------|
| `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py` | Stripped `_`-prefixed internal keys from kwargs in ActivityQueryHandler (line 118-121) and ActivityTelemetryHandler (line 344-349) | `M` (tracked) |
| `tests/governance/t5/test_activity_runtime_delta.py` | **CREATED** — 24 tests across 6 classes (re-audit: +3 production-wiring leakage proofs) | `??` (untracked) |
| `app/hoc/docs/architecture/usecases/HOC_DOMAIN_RUNTIME_INVARIANT_COMPLETION_TRACKER_2026_02_20.md` | activity row: PENDING→DONE, 24 tests, update log entry | `??` (untracked) |
| `app/hoc/docs/architecture/usecases/HOC_ACTIVITY_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan.md` | **CREATED** | `??` (untracked) |
| `app/hoc/docs/architecture/usecases/HOC_ACTIVITY_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented.md` | **CREATED** (this file) | `??` (untracked) |

### _invariant_mode Leakage Fix

**Before (buggy):**
```python
# ActivityQueryHandler.execute():
kwargs = dict(ctx.params)
kwargs.pop("method", None)
data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
# ↑ _invariant_mode from enriched_params leaks into facade method kwargs
```

**After (fixed):**
```python
# ActivityQueryHandler.execute():
kwargs = {
    k: v for k, v in ctx.params.items()
    if k != "method" and not k.startswith("_")
}
data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
# ↑ _invariant_mode and all _-prefixed internal keys are stripped
```

Same pattern applied to `ActivityTelemetryHandler.execute()`.

### Test Coverage (24 tests, 6 classes)

| Class | Count | Coverage |
|-------|-------|----------|
| `TestActivityInvariantContracts` | 6 | Fail-closed: missing tenant_id, missing project_id, both missing, empty tenant_id, empty project_id. Positive: valid tenant_id + project_id |
| `TestActivityInvariantModes` | 5 | MONITOR: non-raise + failure details. STRICT: raises on missing fields, raises on missing project_id, passes valid context |
| `TestActivityRegistryDispatch` | 4 | MONITOR allows bad context, STRICT blocks bad context, STRICT passes valid context, unregistered operation fails |
| `TestActivityInvariantModeLeakage` | 2 | activity.query strips _invariant_mode (unit-level facade kwargs captured), activity.telemetry strips _invariant_mode (unit-level engine kwargs captured) |
| `TestActivityProductionWiringLeakage` | 3 | Production-wiring: activity.query (get_runs) MONITOR via registry.execute(), activity.telemetry (get_usage_summary) MONITOR via registry.execute(), activity.query STRICT via registry.execute() — all prove _invariant_mode NOT forwarded |
| `TestActivityNonTriggerProofs` | 4 | activity.query non-trigger, activity.telemetry non-trigger, no activity.* alias exists, real handler registration exists |

### Verification Commands

```bash
# 1. Domain-specific runtime delta proof
$ cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/governance/t5/test_activity_runtime_delta.py
24 passed in 3.20s

# 2. Full governance t5 regression suite
$ PYTHONPATH=. pytest -q tests/governance/t5
246 passed in 4.80s

# 3. CI: operation ownership
$ PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
Operations audited: 123, Conflicts found: 0

# 4. CI: transaction boundaries
$ PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
Files checked: 253, Violations found: 0

# 5. CI: init hygiene
$ PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
All checks passed
```

## 5. Repository State Disclosure

- Workspace is dirty (40+ modified/untracked files from prior sessions)
- Activity plan docs are untracked (`??`), test file is untracked (`??`)
- Only `activity_handler.py` is a tracked (`M`) change from this iteration
- Runtime test evidence (24/24 domain, 246/246 t5) is independently reproducible

## 6. Open Blockers

None — all acceptance criteria met.

## 7. Handoff Notes

- **Alias decision:** NO alias added. Activity domain monitors runs, does not create them. BI-ACTIVITY-001 guards `run.create` wherever it occurs in the system (e.g., agent/runtime domain).
- **_invariant_mode leakage:** Fixed in ActivityQueryHandler and ActivityTelemetryHandler by stripping `_`-prefixed internal keys from kwargs before forwarding to L5 methods. This is a pattern other handlers should adopt if they use `**kwargs` forwarding.
- **Remaining PENDING domains:** 2 of 10 — `analytics` (BI-ANALYTICS-001) and `logs` (BI-LOGS-001).
- **t5 suite progression:** 222 → 246 (24 new activity tests, including 3 production-wiring leakage proofs).
