# PIN-602: HOC Blocker Queue Wave W2 — INT Platform + Agent Clearance

## Metadata
- Date: 2026-02-20
- Status: COMPLETE
- Scope: HOC-only (`backend/app/hoc/**`)
- Workstream: Active blocker queue Wave W2

## Why
After Wave W1 (`hoc_spine`) lowered HOC capability-linkage blockers to `449`, the next highest cluster was `int/platform + int/agent` (`91` files). W2 clears that cluster while preserving zero-warning and zero-layer/import regression state.

## What Changed
### Capability Header Remediation (91 files)
- Scope:
  - `backend/app/hoc/int/platform/**` (`66`)
  - `backend/app/hoc/int/agent/**` (`25`)
- Header mapping:
  - `CAP-008` -> `int/agent/**`
  - `CAP-012` -> `int/platform/**`

### Registry Evidence Synchronization
- Updated:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
- Added CAP-008/CAP-012 evidence entries for all W2 remediated files.

### Queue/Plan/Literature Updates
- Updated:
  - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
  - `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
  - `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`
- Added:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W2_INT_PLATFORM_AGENT_IMPLEMENTED_2026-02-20.md`

## Verification
- W2 changed-file capability check:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(cut -f1 /tmp/hoc_w2_map.tsv)`
  - Result: `✅ All checks passed`
- Full HOC capability sweep:
  - Before: blocking `449`, warnings `0`
  - After: blocking `358`, warnings `0`
- Layer segregation:
  - `python3 scripts/ops/layer_segregation_guard.py --check --scope hoc` -> `PASS`
- Import hygiene (strict relative-import):
  - `(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) | cut -d: -f1 | sort -u | wc -l` -> `0`

## Outcome
- W2 cleared both target clusters:
  - `int/platform`: `66 -> 0`
  - `int/agent`: `25 -> 0`
- Full HOC capability backlog reduced: `449 -> 358`
- Warning backlog remains stable at `0`

## Next Lane
- Proceed to Wave W3:
  - `backend/app/hoc/int/general/**`
  - `backend/app/hoc/int/worker/**`
  - `backend/app/hoc/int/policies/**`
