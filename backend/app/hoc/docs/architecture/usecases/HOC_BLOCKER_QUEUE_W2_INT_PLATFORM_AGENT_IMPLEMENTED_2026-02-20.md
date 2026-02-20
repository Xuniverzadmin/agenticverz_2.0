# HOC Blocker Queue W2 Implemented (int/platform + int/agent, 2026-02-20)

## Scope
- `backend/app/hoc/int/platform/**`
- `backend/app/hoc/int/agent/**`
- File count remediated: `91`

## Objective
Clear the second highest HOC capability-linkage cluster by adding missing file-level `capability_id` headers and synchronizing capability evidence mappings.

## Capability Mapping Applied
- `CAP-008`:
  - `backend/app/hoc/int/agent/**`
- `CAP-012`:
  - `backend/app/hoc/int/platform/**`

## Registry Synchronization
- Updated:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
- Changes:
  - Added W2 `int/agent` and `int/platform` evidence entries under CAP-008/CAP-012.

## Verification
- W2 changed-file capability check:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(cut -f1 /tmp/hoc_w2_map.tsv)`
  - Result: `✅ All checks passed`
- Full HOC capability sweep:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')`
  - Before: blocking `449`, warnings `0`
  - After: blocking `358`, warnings `0`
- Layer segregation:
  - `python3 scripts/ops/layer_segregation_guard.py --check --scope hoc`
  - Result: `PASS (0 violations)`
- Import hygiene (strict HOC relative-import):
  - `(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) | cut -d: -f1 | sort -u | wc -l`
  - Result: `0`

## Outcome
- W2 target cluster cleared:
  - `int/platform`: `66 -> 0`
  - `int/agent`: `25 -> 0`
- Global HOC blocking backlog reduced: `449 -> 358`
- Warning backlog held at `0`
