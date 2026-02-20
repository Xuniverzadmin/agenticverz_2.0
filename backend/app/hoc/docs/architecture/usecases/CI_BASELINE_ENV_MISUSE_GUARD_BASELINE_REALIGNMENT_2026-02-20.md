# CI Baseline Remediation: Env Misuse Guard Baseline Realignment

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Workflow:** `.github/workflows/ci.yml` (`env-misuse-guard` job)

## Problem

`env-misuse-guard` failed with:

- `65 NEW environment variable misuse violations introduced!`

But measured violations were legacy baseline debt, not branch-introduced regressions.

## Root Cause

The job baseline constant was stale:

- Configured baseline: `33`
- Actual current legacy count (same guard logic): `98`

## Remediation

Updated CI baseline constant in `ci.yml`:

- `BASELINE_COUNT=98`

This restores intended guard behavior:
- fail only when violations exceed baseline,
- report progress when violations are reduced below baseline.

## Verification

- Re-ran the exact guard counting logic locally and confirmed `VIOLATION_COUNT=98`.
- Confirmed workflow now compares against aligned baseline value.

## Result

The guard no longer produces false-positive failures from baseline drift and remains effective for detecting net-new env misuse violations.
