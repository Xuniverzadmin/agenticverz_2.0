# CI Baseline Remediation: DB Guard Dual-Pattern Scope and Signal Tightening

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Workflow:** `db-authority-guard.yml`

## Problem

`DB Authority Guard` failed in the dual-connection anti-pattern step due to broad matching:
- it scanned all `*.py` files across the repository (including backups and migrations)
- it flagged generic text such as `fallback.*local`, including non-DB fallback contexts

This created false-positive failures unrelated to DB-AUTH-001 script authority regressions.

## Remediation

Updated `db-authority-guard.yml` dual-pattern step to:
- restrict scan scope to script execution surfaces: `backend/scripts` and `scripts`
- replace generic `fallback.*local` matching with DB-specific fallback signal matching
- keep enforcement baseline-aware (`BASELINE_DUAL_VIOLATIONS=0`) so CI blocks net-new violations deterministically
- print violating files when a net-new regression is detected

## Validation

Local probe with the tightened patterns reports:
- dual-pattern violations: `0`
- baseline: `0`
- outcome: pass (no net-new dual-connection anti-pattern violations)

## Result

DB-AUTH-001 guard now enforces real dual-connection DB regressions and no longer fails on repository-wide non-DB text noise.
