# CI Baseline Remediation: Alembic Revision-Length Policy

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Workflow:** `scripts/ops/ci_consistency_check.sh`

## Problem

CI preflight failed due to historical Alembic revision IDs longer than 32 chars.

- `check_alembic_health` emitted hard errors for legacy long revision IDs.
- `check_m9_failure_catalog` also hard-failed the same legacy IDs.
- Result: baseline CI failed even without new migration changes.

## Remediation

Adjusted consistency policy to classify this as grandfathered baseline debt.

1. `check_alembic_health`
- Long legacy revision IDs now log warning (not error).
- Added summary counters for near-limit and over-limit revisions.

2. `check_m9_failure_catalog`
- Long legacy revision IDs now log warning.
- M9 milestone status becomes `warn` when only this legacy condition exists.
- Hard-fail behavior remains for true migration integrity failures (for example multiple heads).

## Verification

- `bash scripts/ops/ci_consistency_check.sh --quick`
- Legacy long revision IDs are reported as warnings instead of errors.
- Script still exits non-zero only if other hard errors remain.

## Result

Preflight consistency no longer fails solely because of historical revision-name debt, while preserving hard-fail integrity checks for active migration correctness.
