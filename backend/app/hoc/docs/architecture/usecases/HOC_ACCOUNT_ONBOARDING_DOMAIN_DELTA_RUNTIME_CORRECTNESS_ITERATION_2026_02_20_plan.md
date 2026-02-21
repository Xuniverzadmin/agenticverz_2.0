# HOC Account Onboarding Domain Delta — Runtime Correctness Plan

**Date:** 2026-02-20
**Domain:** account_onboarding
**Anchor Invariant:** BI-ONBOARD-001 (`onboarding.activate`)
**Status:** DONE

## Objective

Close runtime correctness for the onboarding activation operation by proving
BI-ONBOARD-001 is fail-closed via:
- Invariant contract tests (predicate logic)
- MONITOR mode (non-blocking) behavior
- STRICT mode (blocking) behavior
- Real OperationRegistry.execute() dispatch proof

## Acceptance Criteria

1. `test_account_onboarding_runtime_delta.py` exists in `tests/governance/t5/`
2. All tests pass: `PYTHONPATH=. pytest -q tests/governance/t5/test_account_onboarding_runtime_delta.py`
3. Full t5 suite passes: `PYTHONPATH=. pytest -q tests/governance/t5/`
4. CI checks pass: `check_operation_ownership.py`, `check_transaction_boundaries.py`, `check_init_hygiene.py --ci`
5. Tracker updated with account_onboarding row

## Task Matrix

| ID | Task | Status |
|----|------|--------|
| T1 | Analyze BI-ONBOARD-001 invariant contract in business_invariants.py | DONE |
| T2 | Analyze activation predicate logic in onboarding_handler.py | DONE |
| T3 | Analyze check_activation_predicate in onboarding_policy.py | DONE |
| T4 | Create test_account_onboarding_runtime_delta.py with fail-closed negatives | DONE |
| T5 | Add positive activation pass case | DONE |
| T6 | Add MONITOR mode behavior test | DONE |
| T7 | Add STRICT mode behavior test | DONE |
| T8 | Add real OperationRegistry dispatch proof | DONE |
| T9 | Run verification commands (6 checks) | DONE |
| T10 | Update completion tracker | DONE |

## Verification Commands

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/governance/t5/test_account_onboarding_runtime_delta.py
PYTHONPATH=. pytest -q tests/governance/t5
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
```

## Blockers

None identified.
