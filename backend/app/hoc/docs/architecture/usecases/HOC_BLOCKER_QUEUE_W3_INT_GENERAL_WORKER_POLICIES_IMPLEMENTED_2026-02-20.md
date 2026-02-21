# HOC Blocker Queue W3 Implemented (int/general + int/worker + int/policies, 2026-02-20)

## Scope
- `backend/app/hoc/int/general/**`
- `backend/app/hoc/int/worker/**`
- `backend/app/hoc/int/policies/**`
- File count remediated: `78`

## Objective
Clear the INT runtime/policy capability-linkage cluster by adding missing file-level `capability_id` headers and synchronizing capability evidence mappings.

## Capability Mapping Applied
- `CAP-006`:
  - `backend/app/hoc/int/general/**`
- `CAP-012`:
  - `backend/app/hoc/int/worker/**`
- `CAP-009`:
  - `backend/app/hoc/int/policies/**`

## Registry Synchronization
- Updated:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
- Changes:
  - Added W3 evidence entries under CAP-006/CAP-009/CAP-012 for remediated INT files.

## Verification
- W3 changed-file capability check:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(cut -f1 /tmp/hoc_w3_map.tsv)`
  - Result: `✅ All checks passed`
- Full HOC capability sweep:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')`
  - Before: blocking `358`, warnings `0`
  - After: blocking `280`, warnings `0`
- Layer segregation:
  - `python3 scripts/ops/layer_segregation_guard.py --check --scope hoc`
  - Result: `PASS (0 violations)`
- Import hygiene (strict HOC relative-import):
  - `(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) | cut -d: -f1 | sort -u | wc -l`
  - Result: `0`

## Outcome
- W3 target clusters cleared:
  - `int/general`: `28 -> 0`
  - `int/worker`: `28 -> 0`
  - `int/policies`: `22 -> 0`
- Global HOC blocking backlog reduced: `358 -> 280`
- Warning backlog held at `0`
