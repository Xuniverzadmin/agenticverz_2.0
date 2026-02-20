# CI Baseline Remediation: Absolute Symlink Path Drift

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Trigger:** Mypy workflow setup failure (`EACCES` while stat-ing docs symlink target)

## Problem

CI runner failed during Python setup cache traversal with:

- `EACCES: permission denied, stat '.../docs/architecture/hoc/DOMAIN_TRUTH_MAP.csv'`

Root cause:
- Several docs under `docs/architecture/hoc/` were committed as absolute symlinks to `/root/agenticverz2.0/...`.
- On GitHub runners, `/root/...` is inaccessible/non-portable for workspace checkout users.

## Remediation

Converted absolute symlink targets to repository-relative symlinks:

- `docs/architecture/hoc/L2_ROUTER_INVENTORY.md`
- `docs/architecture/hoc/DOMAIN_TRUTH_MAP.csv`
- `docs/architecture/hoc/DOMAIN_TRUTH_MAP.md`
- `docs/architecture/hoc/L2_L4_CALL_MAP.csv`

All now resolve to:
- `../../../backend/docs/architecture/hoc/...`

## Verification

- Enumerated symlink targets and confirmed no remaining `/root/...` absolute links outside ignored dependency trees.
- Confirmed each remediated symlink resolves to in-repo path.

## Result

CI file stat/traversal is now portable across runner environments, removing the `EACCES` setup failure mode caused by host-specific absolute symlink targets.
