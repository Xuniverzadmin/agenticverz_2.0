# CI Baseline Remediation: Truth Preflight Backend Readiness

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Workflow:** `.github/workflows/truth-preflight.yml` + `scripts/verification/truth_preflight.sh`

## Problem

Truth preflight failed with `Cannot reach backend at http://localhost:8000`.

Primary causes:
- Workflow startup used fixed `sleep 15` with non-blocking health probe.
- Preflight script attempted a single immediate `/health` read in Check 1.

## Remediation

1. Workflow hardening (`truth-preflight.yml`)
- Replaced fixed sleep with bounded readiness loop (45 attempts, 2s interval).
- Added backend log dumps at mid-startup and final failure.
- Made startup step fail early if health endpoint never becomes reachable.

2. Script hardening (`truth_preflight.sh`)
- Added bounded Check 1 health retry (`PREFLIGHT_HEALTH_ATTEMPTS`, `PREFLIGHT_HEALTH_INTERVAL`).
- Added progress messages for startup wait and non-healthy status transitions.
- Replaced hardcoded backend path with repository-root derived path to avoid runner path drift.

## Verification

- `bash -n scripts/verification/truth_preflight.sh`
- Probe run with unreachable API base and short retry window:
  - `API_BASE=http://127.0.0.1:65530 PREFLIGHT_HEALTH_ATTEMPTS=2 PREFLIGHT_HEALTH_INTERVAL=0 bash scripts/verification/truth_preflight.sh`
- Check 1 now emits bounded wait diagnostics before fail-closed outcome.

## Result

Truth preflight now has deterministic backend readiness handling and actionable startup diagnostics, reducing false-negative failures caused by startup race conditions.
