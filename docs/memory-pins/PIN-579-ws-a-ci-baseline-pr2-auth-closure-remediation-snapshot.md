# PIN-579: WS-A CI Baseline + PR2 Auth Closure Remediation Snapshot

**Created:** 2026-02-20  
**Status:** IN_PROGRESS  
**Category:** CI / Auth / Migration / Documentation  
**Depends on:** PIN-578, PR #6 (`68903d3e`), branch `hoc/ws-a-ci-baseline-stabilization`

---

## Summary

Session state was consolidated around PR2 closure evidence and WS-A CI stabilization:

- PR2 post-deploy auth enforcement evidence was merged (PR #6) and anchored in memory/docs.
- Auth-positive verification path was completed through a tenant-bound DB-backed API key flow (machine auth), not Clerk-org human auth.
- PR2 closure evidence doc was remediated to remove incorrect claims and to align artifact paths.
- Evidence key revocation was executed and verified (`status=revoked`), and post-revocation endpoint probe returned `401`.
- CI stabilization work on WS-A was pushed in two commits:
  1. `27578228` - SQL misuse guard, Priority5 intent alignment, skill/runtime import scaffolding, CI role/env hardening, docs/literature refresh.
  2. `a22080ca` - migration hardening for legacy `signal_feedback` table collision (`071` vs `128`) in `alembic/versions/128_monitoring_activity_feedback_contracts.py`.

## Verification Snapshot

- Local deterministic checks were reported passing for guard scripts and skills test suite.
- GitHub checks showed previously failing gates turning green (SQL guard, Priority5 intent guard, unit tests).
- Migration gate collision was identified and patched with explicit backward-compatibility logic; rerun status became pending at handoff time.
- Skeptical follow-up audit/remediation pass completed:
  - fixed CI workflow env propagation for DB role gates (`c1`, `c2`, `integration`, `truth-preflight`).
  - fixed deterministic test collection syntax regression in `backend/tests/workflow/test_replay_certification.py`.
  - tightened SQLModel `DETACH002` detection to remove cross-function/docstring false positives while preserving ORM read-path blocking intent.
  - full audit gatepass rerun: `PASS` (`9/9`) at `artifacts/codebase_audit_gatepass/20260220T142258Z/`.
- Residual non-closed guards (separate debt workstreams): layer-segregation (`99` legacy violations), import-hygiene relative imports in `backend/app`, and capability-linkage metadata (`MISSING_CAPABILITY_ID`) for WS-A changed files.

## Governance Notes

- Session bootstrap strict check passed: required governance docs present; UC architecture states remained fully GREEN (40/40) with no missing required docs.
- No secrets are recorded in this PIN; only auth method and verification outcomes are captured.

## Next Actions

1. Confirm latest CI rerun completes green after migration hardening commit.
2. Cut clean PR from WS-A branch once checks are green.
3. Continue skill iteration for scoped commit/PR workflows (`git-commit-push` extension or dedicated PR-skill variant).
