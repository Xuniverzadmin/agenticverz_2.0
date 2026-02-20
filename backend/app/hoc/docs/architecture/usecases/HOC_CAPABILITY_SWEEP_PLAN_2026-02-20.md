# HOC Full Capability Sweep Plan (2026-02-20)

## Final Goal
Drive full-HOC `MISSING_CAPABILITY_ID` debt down in deterministic waves with explicit evidence mapping updates.

## Baseline
- Source: `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')`
- Baseline at plan creation: `965` blocking + `13` warnings.

## Step Plan
| Step | Goal | Status | Evidence |
|---|---|---|---|
| 1 | Capture missing-ID cluster distribution and select low-risk Wave 1 cluster | DONE | top clusters computed from `.tmp_cap_final.txt` |
| 2 | Implement Wave 1 capability headers for `hoc/int/agent/engines/*` residual set | DONE | 28 agent-engine files tagged (`CAP-008`) including residual 3-file tail |
| 3 | Sync capability registry evidence for changed files | DONE | `docs/capabilities/CAPABILITY_REGISTRY.yaml` updated for CAP-005/CAP-014/CAP-016 evidence paths |
| 4 | Re-run full HOC capability sweep and measure delta | DONE | full sweep rerun: blocking `965 -> 929`, warnings stable at `13` |
| 5 | Record wave artifact and backlog status | DONE | changed-file capability check PASS; blocker queue/ledger refreshed |

## Wave 1 Scope
- Directory: `backend/app/hoc/int/agent/engines/`
- Capability target: `CAP-008` for orchestration surfaces not already tagged.

## Exit Criteria
- Blocking count reduced from baseline.
- Changed-file capability check passes.

## Outcome
- Full HOC capability sweep: blocking `965 -> 929` (`-36`), warnings `13 -> 13`.
- Changed-file capability check: PASS (`backend/app/hoc/**/*.py` changed set clear).
- Wave 1 target cluster (`int/agent/engines`) is cleared for missing capability IDs.
