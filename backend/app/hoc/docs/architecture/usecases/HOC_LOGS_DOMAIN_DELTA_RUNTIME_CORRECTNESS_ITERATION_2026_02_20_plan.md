# HOC_LOGS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan

**Created:** 2026-02-20 UTC
**Domain:** logs
**Anchor Invariant:** BI-LOGS-001 (operation: trace.append)
**Status:** DONE

## Scope

Execute the logs domain runtime-invariant delta closure:

1. **Baseline mapping**: Determine whether any `logs.*` L4 dispatch path semantically maps to `trace.append` (likely `logs.traces_api` with `method=store_trace`), and document the decision.
2. **Risk audit**: Check for `_invariant_mode` internal-key leakage in logs handlers that forward `**kwargs`.
3. **Runtime fix**: Strip `_`-prefixed internal keys before forwarding kwargs in logs handlers that use broad forwarding.
4. **Alias decision**: If required, add minimal alias wiring with method-aware invariant gating to avoid over-broad enforcement on non-append methods.
5. **Tests**: Create `test_logs_runtime_delta.py` with fail-closed contracts, MONITOR/STRICT mode proofs, dispatch proofs, production-wiring leakage proofs, and non-trigger/method-scope proofs.
6. **Docs**: Create implemented report and update tracker.

## Tasks

| ID | Task | Acceptance |
|----|------|-----------|
| LG-DELTA-01 | Baseline mapping + alias decision | Explicit yes/no decision with rationale and real dispatch-path evidence |
| LG-DELTA-02 | Fix `_invariant_mode` leakage | All logs handlers that use `**kwargs` strip `_`-prefixed internal keys |
| LG-DELTA-03 | Domain delta tests | All tests pass: contracts, modes, dispatch, leakage, non-trigger/scope |
| LG-DELTA-04 | Verification | All required commands pass |
| LG-DELTA-05 | Docs + tracker | Implemented doc completed and tracker updated to DONE with true counts |

## Required Verification Commands

Run from `/root/agenticverz2.0/backend`:

1. `PYTHONPATH=. pytest -q tests/governance/t5/test_logs_runtime_delta.py`
2. `PYTHONPATH=. pytest -q tests/governance/t5`
3. `PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py`
4. `PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py`
5. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`

## Guardrails

- Preserve HOC topology: L2.1 -> L2 -> L4 -> L5 -> L6 -> L7.
- No direct L2 -> L5/L6 bypass.
- Keep fixes minimal and logs-domain scoped.
- Do not introduce over-broad invariant enforcement on non-append logs operations.
- Any alias-based enforcement must include method-aware behavior proof (if alias is added).

