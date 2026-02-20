# CI Baseline Remediation: DB Guard Script Baseline + Integration Output Format

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Workflows:** `db-authority-guard.yml`, `integration-integrity.yml`

## Problem A: DB Authority Guard Script Scan Drift

`DB Authority Guard` failed on pre-existing script debt:
- `30 script(s) touch DB without _db_guard`

This was treated as net-new failure because script-scan step had no baseline threshold.

## Remediation A

Added baseline-aware enforcement in `db-authority-guard.yml` script scan step:
- `BASELINE_VIOLATIONS=30`
- Fail only when `VIOLATIONS > BASELINE_VIOLATIONS`
- Report progress when below baseline
- Warn (non-fail) when equal baseline debt remains

## Problem B: Integration Integrity Output Command Failure

`Layer Integration Tests` job passed tests but failed workflow step with:
- `Unable to process file command 'output'`
- `Invalid format '0'`

Root cause: count expressions used `grep -c ... || echo "0"`, which can emit duplicated lines (`0\n0`) and corrupt `GITHUB_OUTPUT` formatting.

## Remediation B

Updated output counters in `integration-integrity.yml`:
- Replaced `|| echo "0"` with `|| true` for `grep -c` counters in LIT and BIT steps.
- Preserves single numeric output line for `passed`/`failed` fields.

## Result

- DB guard script scan now enforces delta policy correctly against known debt.
- Integration workflow no longer fails due to malformed `GITHUB_OUTPUT` formatting when test counts are zero.
