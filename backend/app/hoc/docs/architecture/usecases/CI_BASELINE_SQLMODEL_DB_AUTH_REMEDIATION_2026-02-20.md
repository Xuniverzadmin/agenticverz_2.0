# CI Baseline Remediation: SQLModel Linter DB Authority Contract

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Invariant:** DB-AUTH-001 (authority declared, not inferred)

## Problem

SQLModel linter execution failed in CI contexts when `DB_AUTHORITY` was not set.

- Failure mode: `scripts._db_guard` exits with violation when authority is missing.
- Impact: SQLModel linter jobs and tool entrypoints could fail before pattern checks run.

## Remediation

Set explicit local authority for non-DB operational lint contexts.

1. `.github/workflows/sqlmodel-patterns.yml`
- Added `DB_AUTHORITY: local` in linter job env.

2. `.pre-commit-config.yaml`
- Updated SQLModel staged hook entry to include `DB_AUTHORITY=local`.

3. `scripts/ops/ci_consistency_check.sh`
- Updated SQLModel pattern check invocation to run with:
  - `CHECK_SCOPE=full`
  - `DB_AUTHORITY=local`

## Verification

- `DB_AUTHORITY=local CHECK_SCOPE=full python3 scripts/ops/lint_sqlmodel_patterns.py backend/app/api/` runs without DB guard violation.
- Workflow/pre-commit/consistency script now all declare authority explicitly at invocation.

## Result

DB-AUTH-001 contract is now enforced consistently for SQLModel linter tooling surfaces, eliminating missing-authority execution failures in CI baseline runs.
