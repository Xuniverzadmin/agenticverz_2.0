# HOC CUS Strict Stabilization Pass Plan

**Date:** 2026-02-21  
**Scope:** `hoc/cus/*` only  
**Status:** DRAFT (awaiting approval)

## Final Goal
Stabilize `hoc/cus/*` so CUS contract truth is internally consistent and auditable across:
1. OpenAPI visibility for CUS routes.
2. CUS ledger and runtime publication parity.
3. CUS-only governance evidence refresh with reproducible command output.
4. Domain-by-domain registry and Swagger grouping for consumer-ready publication.

## Audit Baseline (2026-02-21)
1. Local OpenAPI CUS rows (`docs/openapi.json` `/hoc/api/cus/*`): `0`
2. Runtime OpenAPI CUS rows (`https://stagetest.agenticverz.com/openapi.json`): `0`
3. Local CUS ledger rows (`docs/api/HOC_CUS_API_LEDGER.json`): `502` rows (`499` unique method+path)
4. Runtime `/apis/ledger` CUS rows: `502` rows (`499` unique method+path)
5. CUS ledger parity (local vs runtime, unique method+path): `0` diff both ways
6. `check_layer_boundaries.py`: PASS
7. `layer_segregation_guard.py --scope hoc`: `93` violations (active HOC canonical debt; outside this CUS-only pass)

## Scope Lock
In scope:
- `backend/app/hoc/api/cus/**`
- `backend/app/hoc/cus/**` only if required to restore CUS route/spec parity
- CUS ledger artifacts and CUS evidence docs/pins

Out of scope (deferred):
- `backend/app/hoc/api/fdr/**`
- `backend/app/hoc/api/int/**`
- Hoc-wide canonical debt remediation unrelated to CUS contract stabilization

## Domain-by-Domain Working Method (Mandatory)
Execution must run per CUS domain, not as a single undifferentiated CUS block.

CUS domains:
1. `overview`
2. `activity`
3. `incidents`
4. `policies`
5. `controls`
6. `logs`
7. `analytics`
8. `integrations`
9. `api_keys`
10. `account`

Additional required lanes (not CUS business domains):
1. `apis` lane: registry/Swagger publication utilities and grouped publication surfaces.
2. `hoc_spine` lane: orchestration/wiring conformance checks for CUS route dispatch.

Per-domain loop:
1. Discover routes from source + OpenAPI for `<domain>`.
2. Build domain registry artifact.
3. Validate domain OpenAPI slice and tags.
4. Run domain parity check against runtime ledger subset.
5. Record domain evidence and only then proceed to next domain.

Per-additional-lane loop:
1. `apis` lane: verify grouped endpoints (`/apis/ledger/cus/<domain>`, `/apis/swagger/cus/<domain>`) and utility contracts.
2. `hoc_spine` lane: verify each CUS L2 route maps via approved execution path (`L2 -> L4 hoc_spine -> L5 -> L6`) with no direct L2->L5/L6 bypass.

## Registry + Swagger Grouping Contract
Registry must be grouped and published by domain.

Required grouped artifacts:
1. `docs/api/cus/HOC_CUS_<DOMAIN>_API_LEDGER.json`
2. `docs/api/cus/HOC_CUS_<DOMAIN>_API_LEDGER.csv`
3. `docs/api/cus/HOC_CUS_<DOMAIN>_API_LEDGER.md`
4. `docs/api/cus/HOC_CUS_<DOMAIN>_MISMATCH_AUDIT_YYYY-MM-DD.{md,json}`

Required grouped publication views:
1. Domain registry view: `/apis/ledger/cus/<domain>`
2. Domain OpenAPI/Swagger view: `/apis/swagger/cus/<domain>` (or documented equivalent path alias)

Required supporting surfaces:
1. API registry index view: `/apis/ledger/cus`
2. Swagger/domain index view: `/apis/swagger/cus`

Acceptance for grouped publication:
1. Domain endpoint returns `200` JSON.
2. Domain payload is non-empty when domain has routes.
3. Domain payload matches local registry (`method+path` parity zero diff).
4. Index views list all in-scope CUS domains and route to valid domain pages.

## Canonical HOC Debt Lane (Deferred, Not Dismissed)
HOC is canonical and the `93` segregation violations are active debt to be resolved.

This CUS pass defers that remediation only to keep execution scope tight.

Follow-on lane after CUS stabilization:
1. Execute dedicated `hoc/*` layer-segregation remediation waves.
2. Reduce `93` violations to `0` with file-by-file closure evidence.
3. Keep `fdr/*` and `int/*` remediation in explicit PR-bounded batches.

## Step-by-Step Execution Goals

### Step 1: Freeze CUS Baseline Artifacts
Goal:
- Rebuild CUS ledger from canonical process and lock deterministic snapshot.

Outputs:
- Refresh `docs/api/HOC_CUS_API_LEDGER.{json,csv,md}`
- Refresh CUS mismatch audit doc/json for current branch state
- Generate per-domain CUS ledger artifacts under `docs/api/cus/`

Exit criteria:
- Re-run produces stable counts and deterministic ordering.

### Step 2: Close CUS OpenAPI Drift
Goal:
- Ensure CUS contract appears in canonical OpenAPI source of truth for the chosen namespace.

Actions:
1. Enumerate current CUS routers wired under L2 facades/entrypoint.
2. Identify why `/hoc/api/cus/*` is absent in generated OpenAPI.
3. Implement minimal wiring/spec correction (no FDR/INT touches).
4. Regenerate OpenAPI snapshot and verify `/hoc/api/cus/*` rows > 0.
5. Verify each domain has a valid OpenAPI grouping surface (tags/slice) for Swagger publication.

Exit criteria:
- Local `docs/openapi.json` shows non-zero `/hoc/api/cus/*` routes.
- Runtime OpenAPI endpoint path policy is documented (same prefix or explicit mapped alias).
- Each CUS domain is discoverable via grouped Swagger/OpenAPI view contract.

### Step 3: Re-validate CUS Ledger/Runtime Parity
Goal:
- Guarantee runtime publication does not drift from CUS ledger.

Actions:
1. Compare local `HOC_CUS_API_LEDGER.json` against runtime `/apis/ledger` CUS subset.
2. Fail if any method+path mismatch.
3. Repeat parity check per domain using `/apis/ledger/cus/<domain>` subset.
4. Record diff report artifacts (must be zero diff for global CUS and each domain).

Exit criteria:
- `local_minus_runtime=0`
- `runtime_minus_local=0`

### Step 4: CUS-Only Governance Evidence Refresh
Goal:
- Produce fresh, merge-ready evidence for CUS stabilization changes.

Mandatory checks:
1. `PYTHONPATH=. python3 backend/scripts/ci/check_layer_boundaries.py`
2. `python3 scripts/ci/check_openapi_snapshot.py`
3. `python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_py_files>`
4. CUS targeted tests (existing + any new parity/openapi tests)

Exit criteria:
- All blocking checks pass.
- Warnings are explicitly documented with rationale.

### Step 5: Documentation + Pin Closure
Goal:
- Record stabilization evidence and decision trail.

Outputs:
1. CUS stabilization audit doc (dated).
2. Memory pin + `docs/memory-pins/INDEX.md` update.
3. Plan-implemented status doc update.
4. Domain registry index for CUS grouped outputs.

Exit criteria:
- All evidence paths are linkable and reproducible.

## Deliverables
1. Code/spec fixes for CUS OpenAPI drift closure.
2. Updated CUS ledger + mismatch + parity evidence artifacts.
3. CUS-only governance evidence doc.
4. New memory pin for stabilization pass.
5. Domain-grouped registry + Swagger publication evidence for each CUS domain.

## Risks
1. OpenAPI generation may intentionally use non-canonical aliases instead of `/hoc/api/cus/*`.
   - Mitigation: document canonical namespace decision and enforce one mapping.
2. Runtime proxy may present transformed spec independent of local snapshot.
   - Mitigation: verify both local and runtime and capture explicit mapping evidence.
3. Concurrent sessions may dirty unrelated files.
   - Mitigation: execute in clean worktree and path-scoped commits only.

## Approval Gate
Execution starts only after explicit approval on this plan.
