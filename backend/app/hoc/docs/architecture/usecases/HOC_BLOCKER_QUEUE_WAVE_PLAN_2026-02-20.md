# HOC Blocker Queue Wave Plan (2026-02-20)

## Final Goal
Reduce HOC capability-linkage blockers from `550` to `0` under `backend/app/hoc/**` while keeping:
- layer segregation (`--scope hoc`) at `0`
- import hygiene in HOC at `0`
- changed-file capability checks green on each wave PR.

## Baseline
- Source command:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')`
- Baseline result:
  - blocking: `550`
  - warnings: `0`

## Execution Rules
1. HOC-only remediation. No non-HOC expansion.
2. Metadata-first changes (`# capability_id: CAP-xxx`) plus registry evidence synchronization.
3. No broad runtime refactors inside wave PRs.
4. Each wave is independently reviewable and auditable.

## Detailed Wave Plans (2026-02-21)
- Audit snapshot:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_W7_AUDIT_2026-02-21.md`
- W4 plan:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_CUS_DOMAINS_PLAN_2026-02-21.md`
  - file queue: `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_FILE_QUEUE_2026-02-21.txt`
- W5 plan:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_API_LANES_PLAN_2026-02-21.md`
  - file queue: `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_FILE_QUEUE_2026-02-21.txt`
- W6 plan:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W6_LONG_TAIL_PLAN_2026-02-21.md`
  - file queue: `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W6_FILE_QUEUE_2026-02-21.txt`
- W7 plan:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W7_CLOSURE_AUDIT_PLAN_2026-02-21.md`

## Wave Plan
| Step | Wave | Target Scope | Estimated Blockers | Goal | Status |
|---|---|---|---:|---|---|
| 1 | W0 | Baseline snapshot + cluster map | - | lock deterministic starting point | DONE |
| 2 | W1 | `backend/app/hoc/cus/hoc_spine/**` | 101 | clear largest CUS spine cluster | DONE (`550 -> 449`, warnings `0 -> 0`) |
| 3 | W2 | `backend/app/hoc/int/platform/**` + `backend/app/hoc/int/agent/**` | 91 | clear platform/agent integration cluster | DONE (`449 -> 358`, warnings `0 -> 0`) |
| 4 | W3 | `backend/app/hoc/int/general/**` + `backend/app/hoc/int/worker/**` + `backend/app/hoc/int/policies/**` | 78 | clear INT runtime/policy cluster | DONE (`358 -> 280`, warnings `0 -> 0`) |
| 5 | W4 | CUS business domains: `cus/account/**`, `cus/activity/**`, `cus/controls/**`, `cus/policies/**`, `cus/api_keys/**`, `cus/overview/**`, `cus/ops/**`, `cus/agent/**`, `cus/apis/**`, `cus/__init__.py` | 123 | clear remaining CUS domain internals | DONE (`280 -> 157`, warnings `0 -> 0`) |
| 6 | W5 | API lanes: `api/cus/**`, `api/facades/**`, `api/int/**`, `api/fdr/**` | 83 | clear API/facade linkage debt | DONE (`157 -> 74`, warnings `0 -> 0`) |
| 7 | W6 | residual long-tail: `int/recovery/**`, `int/logs/**`, `int/integrations/**`, `int/incidents/**`, `int/analytics/**`, `int/activity/**`, `int/account/**`, `int/__init__.py`, `fdr/ops/**`, `fdr/logs/**`, `fdr/agent/**`, `fdr/account/**`, `fdr/platform/**`, `fdr/__init__.py` | 74 | clear long-tail and reach zero | PENDING |
| 8 | W7 | Closure audit + pin/update queue docs | - | publish final closure evidence | PENDING |

## Per-Wave Checklist
1. Capture before counts (full sweep + target scope).
2. Add/verify `# capability_id: CAP-xxx` for wave files.
3. Sync `docs/capabilities/CAPABILITY_REGISTRY.yaml` evidence mappings.
4. Run changed-file capability check (must pass).
5. Re-run full HOC sweep and record delta.
6. Update:
   - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
   - `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
   - wave implementation artifact / PIN entry

## Success Criteria
1. Blocking count reaches `0`.
2. Warnings remain `0`.
3. Layer segregation remains `0` for `--scope hoc`.
4. HOC import hygiene remains `0`.

## W1 Execution Result
- Scope remediated: `backend/app/hoc/cus/hoc_spine/**` (`101` files).
- Capability header mapping:
  - `CAP-011`: `auth_wiring.py` + `authority/**`
  - `CAP-012`: remaining `hoc_spine/**`
- Registry evidence synchronized:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml` (CAP-011/CAP-012 engine evidence)
- Audit results:
  - W1 changed-file capability check: `✅ All checks passed`
  - Full HOC sweep: blocking `550 -> 449`, warnings `0 -> 0`
  - Layer segregation (`--scope hoc`): `PASS (0 violations)`
  - Import hygiene (`backend/app/hoc/**`, strict relative-import): `0`
- Artifact:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W1_HOC_SPINE_IMPLEMENTED_2026-02-20.md`

## W2 Execution Result
- Scope remediated:
  - `backend/app/hoc/int/platform/**`
  - `backend/app/hoc/int/agent/**`
  - (`91` files)
- Capability header mapping:
  - `CAP-008`: `int/agent/**`
  - `CAP-012`: `int/platform/**`
- Registry evidence synchronized:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml` (CAP-008/CAP-012 evidence)
- Audit results:
  - W2 changed-file capability check: `✅ All checks passed`
  - Full HOC sweep: blocking `449 -> 358`, warnings `0 -> 0`
  - Layer segregation (`--scope hoc`): `PASS (0 violations)`
  - Import hygiene (`backend/app/hoc/**`, strict relative-import): `0`
- Artifact:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W2_INT_PLATFORM_AGENT_IMPLEMENTED_2026-02-20.md`

## W3 Execution Result
- Scope remediated:
  - `backend/app/hoc/int/general/**`
  - `backend/app/hoc/int/worker/**`
  - `backend/app/hoc/int/policies/**`
  - (`78` files)
- Capability header mapping:
  - `CAP-006`: `int/general/**`
  - `CAP-012`: `int/worker/**`
  - `CAP-009`: `int/policies/**`
- Registry evidence synchronized:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml` (CAP-006/CAP-009/CAP-012 evidence)
- Audit results:
  - W3 changed-file capability check: `✅ All checks passed`
  - Full HOC sweep: blocking `358 -> 280`, warnings `0 -> 0`
  - Layer segregation (`--scope hoc`): `PASS (0 violations)`
  - Import hygiene (`backend/app/hoc/**`, strict relative-import): `0`
- Artifact:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W3_INT_GENERAL_WORKER_POLICIES_IMPLEMENTED_2026-02-20.md`

## W4 Execution Result
- Scope remediated:
  - `backend/app/hoc/cus/account/**`
  - `backend/app/hoc/cus/activity/**`
  - `backend/app/hoc/cus/controls/**`
  - `backend/app/hoc/cus/policies/**`
  - `backend/app/hoc/cus/api_keys/**`
  - `backend/app/hoc/cus/overview/**`
  - `backend/app/hoc/cus/ops/**`
  - `backend/app/hoc/cus/agent/**`
  - `backend/app/hoc/cus/apis/**`
  - `backend/app/hoc/cus/__init__.py`
  - (`123` files)
- Capability header mapping:
  - `CAP-012`: account/activity/overview/ops/apis + `cus/__init__.py`
  - `CAP-009`: controls/policies
  - `CAP-006`: api_keys
  - `CAP-008`: agent
- Registry evidence synchronized:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml` (directory evidence for CAP-012/CAP-009/CAP-006/CAP-008)
- Audit results:
  - W4 changed-file capability check: `✅ All checks passed`
  - Full HOC sweep: blocking `280 -> 157`, warnings `0 -> 0`
  - Layer segregation (`--scope hoc`): `PASS (0 violations)`
  - Import hygiene (`backend/app/hoc/**`, strict relative-import): `0`
- Artifact:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_CUS_DOMAINS_IMPLEMENTED_2026-02-21.md`

## W5 Execution Result
- Scope remediated:
  - `backend/app/hoc/api/cus/**`
  - `backend/app/hoc/api/facades/**`
  - `backend/app/hoc/api/int/**`
  - `backend/app/hoc/api/fdr/**`
  - (`83` files)
- Capability header mapping:
  - `CAP-012`: `api/cus/**`, `api/facades/**`, `api/int/**`
  - `CAP-005`: `api/fdr/**`
- Registry evidence synchronized:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml` (directory evidence for API lanes)
- Audit results:
  - W5 changed-file capability check: `✅ All checks passed`
  - Full HOC sweep: blocking `157 -> 74`, warnings `0 -> 0`
  - Layer segregation (`--scope hoc`): `PASS (0 violations)`
  - Import hygiene (`backend/app/hoc/**`, strict relative-import): `0`
- Artifact:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_API_LANES_IMPLEMENTED_2026-02-21.md`
