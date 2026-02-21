# HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20

## Purpose
Track active blocking governance debt under `backend/app/hoc/**` only.

## Scope Policy
- In scope: `backend/app/hoc/**`
- Out of scope (tombstoned legacy): non-`hoc/*` paths tracked in:
  - `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`

## Current Status Snapshot (2026-02-20)
| Guard | Current Status | Notes |
|---|---:|---|
| Layer segregation (`--scope hoc`) | `0` violations | green |
| Import hygiene (`backend/app/hoc/**`) | `0` files (`^\\s*from \\..`) | green |
| Capability linkage (`MISSING_CAPABILITY_ID`) | `74` files | active blocker lane |
| Capability warnings (`MISSING_EVIDENCE`) | `0` | green |

## Capability Missing-ID Distribution (74 total)
| Cluster Prefix | Missing `capability_id` Files |
|---|---:|
| `backend/app/hoc/fdr/ops/**` | 16 |
| `backend/app/hoc/int/recovery/**` | 12 |
| `backend/app/hoc/int/logs/**` | 10 |
| `backend/app/hoc/int/integrations/**` | 8 |
| `backend/app/hoc/int/incidents/**` | 8 |
| `backend/app/hoc/int/analytics/**` | 7 |
| `backend/app/hoc/int/activity/**` | 2 |
| `backend/app/hoc/int/account/**` | 2 |
| `backend/app/hoc/fdr/logs/**` | 2 |
| `backend/app/hoc/fdr/agent/**` | 2 |
| `backend/app/hoc/fdr/account/**` | 2 |
| `backend/app/hoc/int/__init__.py` | 1 |
| `backend/app/hoc/fdr/platform/**` | 1 |
| `backend/app/hoc/fdr/__init__.py` | 1 |

## Latest Wave Delta
- W1 (`hoc_spine`) completed:
  - `backend/app/hoc/cus/hoc_spine/**`: `101 -> 0`
  - full HOC backlog: `550 -> 449`
  - warnings remain `0`
- W2 (`int/platform` + `int/agent`) completed:
  - `backend/app/hoc/int/platform/**`: `66 -> 0`
  - `backend/app/hoc/int/agent/**`: `25 -> 0`
  - full HOC backlog: `449 -> 358`
  - warnings remain `0`
- W3 (`int/general` + `int/worker` + `int/policies`) completed:
  - `backend/app/hoc/int/general/**`: `28 -> 0`
  - `backend/app/hoc/int/worker/**`: `28 -> 0`
  - `backend/app/hoc/int/policies/**`: `22 -> 0`
  - full HOC backlog: `358 -> 280`
  - warnings remain `0`
- W4 (`cus/account` + `cus/activity` + `cus/controls` + `cus/policies` + `cus/api_keys` + `cus/overview` + `cus/ops` + `cus/agent` + `cus/apis` + `cus/__init__.py`) completed:
  - full W4 queue: `123 -> 0`
  - full HOC backlog: `280 -> 157`
  - warnings remain `0`
- W5 (`api/cus` + `api/facades` + `api/int` + `api/fdr`) completed:
  - full W5 queue: `83 -> 0`
  - full HOC backlog: `157 -> 74`
  - warnings remain `0`

## Execution Plan Link
- `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`

## Reproduction Commands
```bash
python3 scripts/ops/layer_segregation_guard.py --check --scope hoc

(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) \
  | cut -d: -f1 | sort -u | wc -l

python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  $(git ls-files 'backend/app/hoc/**/*.py')

# Cluster distribution (depth: backend/app/hoc/<domain>/<subdomain>)
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  $(git ls-files 'backend/app/hoc/**/*.py') > /tmp/hoc_cap_sweep_latest.txt 2>&1 || true
rg "^  \[MISSING_CAPABILITY_ID\]" /tmp/hoc_cap_sweep_latest.txt \
  | sed 's/^  \[MISSING_CAPABILITY_ID\] //' \
  | awk -F/ '{print $1"/"$2"/"$3"/"$4"/"$5}' \
  | sort | uniq -c | sort -nr
```
