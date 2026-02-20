# PIN-592 HOC-Only Governance Scope and Non-HOC Tombstone Ledger

## Context
CI baseline debt included mixed violations under both `backend/app/hoc/**` and non-HOC surfaces. Execution focus for PR-1..PR-10 recovery requires deterministic HOC-only blocking gates.

## Decision (2026-02-20)
1. Keep blocking remediation scope limited to `backend/app/hoc/**`.
2. Mark non-HOC blocker violations as explicit tombstone debt with review/expiry targets.
3. Keep non-HOC debt visible in a dedicated ledger, but non-blocking for HOC closure flow.

## Implemented Changes
- Added HOC scope support to layer guard:
  - `scripts/ops/layer_segregation_guard.py` (`--scope hoc|all`)
- Updated CI workflows to HOC scope:
  - `.github/workflows/layer-segregation.yml`
  - `.github/workflows/import-hygiene.yml`
  - `.github/workflows/capability-registry.yml` (capability-linkage changed-file set)
- Added tombstone ledger:
  - `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
- Updated blocker queue to reflect HOC-only remediation scope:
  - `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
- Recorded in literature:
  - `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`

## Evidence Snapshot
- Layer guard:
  - all-scope: `99` violations
  - hoc-scope: `93` violations
  - non-HOC tombstoned delta: `6`
- Import hygiene relative-import files:
  - all app: `63`
  - hoc only: `34`
  - non-HOC tombstoned delta: `29`
- Capability linkage (`MISSING_CAPABILITY_ID`) working set:
  - total: `9`
  - hoc blocking: `5`
  - non-HOC tombstoned delta: `4`

## Why This Matters
This isolates active blocker burn-down to the HOC execution plane and preserves visibility of external debt without letting unrelated legacy files halt HOC PR closure.
