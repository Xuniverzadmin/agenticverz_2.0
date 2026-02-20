# PR1_PR10_STEP6_RECOVERY_AUDIT_2026-02-20

## Scope
Audit of Step 6 completion status from `PR1_PR10_COURSE_CORRECTION_PLAN_2026-02-20.md`.

## Final Goal Mapping
Step 6 requires clean recovery PR execution for PR-10, PR-1, and PR-3..PR-9 from `origin/main`.

## Recovery PR Matrix
| Slice | PR | Branch | Status |
|---|---|---|---|
| PR-2 (pre-existing Step 5 output) | #8 | `hoc/pr2-incidents-list-recovery-clean` | OPEN |
| PR-10 | #11 | `hoc/pr10-account-users-recovery-clean` | OPEN |
| PR-1 | #12 | `hoc/pr1-runs-recovery-clean` | OPEN |
| PR-3 | #13 | `hoc/pr3-policies-recovery-clean` | OPEN |
| PR-4 | #14 | `hoc/pr4-controls-recovery-clean` | OPEN |
| PR-5 | #15 | `hoc/pr5-logs-recovery-clean` | OPEN |
| PR-6 | #16 | `hoc/pr6-overview-recovery-clean` | OPEN |
| PR-7 | #17 | `hoc/pr7-analytics-recovery-clean` | OPEN |
| PR-8 | #18 | `hoc/pr8-integrations-recovery-clean` | OPEN |
| PR-9 | #19 | `hoc/pr9-api-keys-recovery-clean` | OPEN |

## Skeptical Findings
1. Route wiring gaps existed for recovered public facades in current `main` topology.
- Impact: endpoint not registered under `build_hoc_router()` despite domain module landing.
- Evidence: initial failures in each recovered slice test for route-count assertion (`paths.count(...) == 0`).
- Remediation applied: explicit wiring in L2.1 facade routers:
  - `backend/app/hoc/api/facades/cus/account.py`
  - `backend/app/hoc/api/facades/cus/policies.py`
  - `backend/app/hoc/api/facades/cus/controls.py`
  - `backend/app/hoc/api/facades/cus/logs.py`
  - `backend/app/hoc/api/facades/cus/overview.py`
  - `backend/app/hoc/api/facades/cus/analytics.py`
  - `backend/app/hoc/api/facades/cus/integrations.py`
  - `backend/app/hoc/api/facades/cus/api_keys.py`

2. Legacy memory-pin numbering conflict discovered for PR-1 salvage pin.
- Impact: old salvage pin serial overlapped with current main pin index numbering.
- Remediation applied: PR-1 recovery was scoped to code/tests/contract docs; pin renumbering deferred.

## Test Evidence
| Slice | Command | Result |
|---|---|---|
| PR-10 | `PYTHONPATH=. pytest -q tests/api/test_account_public_facade_pr10.py` | 13 passed |
| PR-1 | `PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py` | 14 passed |
| PR-3 | `PYTHONPATH=. pytest -q tests/api/test_policies_public_facade_pr3.py` | 14 passed |
| PR-4 | `PYTHONPATH=. pytest -q tests/api/test_controls_public_facade_pr4.py` | 14 passed |
| PR-5 | `PYTHONPATH=. pytest -q tests/api/test_logs_public_facade_pr5.py` | 13 passed |
| PR-6 | `PYTHONPATH=. pytest -q tests/api/test_overview_public_facade_pr6.py` | 5 passed |
| PR-7 | `PYTHONPATH=. pytest -q tests/api/test_analytics_public_facade_pr7.py` | 12 passed |
| PR-8 | `PYTHONPATH=. pytest -q tests/api/test_integrations_public_facade_pr8.py` | 12 passed |
| PR-9 | `PYTHONPATH=. pytest -q tests/api/test_api_keys_public_facade_pr9.py` | 11 passed |

## Step 6 Verdict
- **Status:** COMPLETE
- **Condition:** complete at PR-opened, slice-validated level; merge-order/rebasing remains pending operationally.

## Remaining Plan Work
- Step 7 (frontend ledger sync after corresponding backend merges): TODO.
