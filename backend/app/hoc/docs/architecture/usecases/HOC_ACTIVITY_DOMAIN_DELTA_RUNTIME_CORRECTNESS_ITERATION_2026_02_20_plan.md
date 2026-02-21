# HOC_ACTIVITY_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan

**Created:** 2026-02-20 UTC
**Domain:** activity
**Anchor Invariant:** BI-ACTIVITY-001 (operation: run.create)
**Status:** DONE

## Scope

Execute the activity domain runtime-invariant delta closure:

1. **Baseline mapping**: Determine if any activity.* L4 dispatch operation maps to run.create
2. **Risk audit**: Check for _invariant_mode internal key leakage in handlers that forward **kwargs
3. **Runtime fix**: Strip _invariant_mode from kwargs before forwarding in ActivityQueryHandler and ActivityTelemetryHandler
4. **Alias decision**: Determine whether to add INVARIANT_OPERATION_ALIASES entry
5. **Tests**: Create test_activity_runtime_delta.py with fail-closed contracts, MONITOR/STRICT modes, dispatch proofs, leakage regression, non-trigger proofs
6. **Docs**: Plan + implemented docs, update tracker

## Tasks

| ID | Task | Acceptance |
|----|------|-----------|
| AC-DELTA-01 | Baseline mapping + alias decision | Document whether alias exists and why/why not |
| AC-DELTA-02 | Fix _invariant_mode leakage | activity.query and activity.telemetry strip internal keys |
| AC-DELTA-03 | Domain delta tests | All tests pass: contracts, modes, dispatch, leakage, non-trigger |
| AC-DELTA-04 | Verification | All 6 commands pass |
| AC-DELTA-05 | Docs + tracker | Plan, implemented, tracker updated |
