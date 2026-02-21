# HOC_ANALYTICS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan

**Created:** 2026-02-20 UTC
**Domain:** analytics
**Anchor Invariant:** BI-ANALYTICS-001 (operation: cost_record.create)
**Status:** DONE

## Scope

Execute the analytics domain runtime-invariant delta closure:

1. **Baseline mapping**: Determine if any analytics.* L4 dispatch operation maps to cost_record.create
2. **Risk audit**: Check for _invariant_mode internal key leakage in handlers that forward **kwargs
3. **Runtime fix**: Strip _invariant_mode from kwargs before forwarding in FeedbackReadHandler, AnalyticsQueryHandler, and AnalyticsDetectionHandler
4. **Alias decision**: Determine whether to add INVARIANT_OPERATION_ALIASES entry
5. **Tests**: Create test_analytics_runtime_delta.py with fail-closed contracts, MONITOR/STRICT modes, dispatch proofs, production-wiring leakage proofs, non-trigger proofs
6. **Docs**: Plan + implemented docs, update tracker

## Tasks

| ID | Task | Acceptance |
|----|------|-----------|
| AN-DELTA-01 | Baseline mapping + alias decision | Document whether alias exists and why/why not |
| AN-DELTA-02 | Fix _invariant_mode leakage | analytics.feedback, analytics.query, analytics.detection strip internal keys |
| AN-DELTA-03 | Domain delta tests | All tests pass: contracts, modes, dispatch, leakage, non-trigger |
| AN-DELTA-04 | Verification | All 5 commands pass |
| AN-DELTA-05 | Docs + tracker | Plan, implemented, tracker updated |
