# HOC CUS Script vs UC Coverage Audit (2026-02-12)

## Scope
- Audit scripts under `backend/app/hoc/cus/*`.
- Compare script inventory to UC linkage evidence in:
  - `app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
  - `app/hoc/docs/architecture/usecases/INDEX.md`
- Report delta count for scripts without UC linkage.

## UC Linkage Status
- Usecase registry count (`INDEX.md`): `32` total, `32` GREEN.
- Linkage document sections (`HOC_USECASE_CODE_LINKAGE.md`): `32` GREEN.

## Method
Two linkage passes were used to avoid undercounting:

1. Strict path linkage
- A script is linked only if its full path appears in `HOC_USECASE_CODE_LINKAGE.md`.

2. Filename-assisted linkage (non-ambiguous)
- Also counts scripts where a `.py` filename appears in linkage doc and that filename is unique under `app/hoc/cus`.
- Ambiguous duplicate basenames are excluded.

Primary delta in this report uses `filename-assisted linkage` (strict + non-ambiguous filename union).

## Inventory Summary (All `hoc/cus` Python Scripts)
- Total scripts: `573`
- Linked scripts (strict path only): `29`
- Linked scripts (filename-assisted union): `42`
- **Delta scripts without UC linkage (union basis): `531`**
- Stale linkage references to non-existent `app/hoc/cus/*.py` paths: `0`

## Core Layer Surface Summary
Definition:
- `L5_engines`, `L5_schemas`, `L6_drivers`, `adapters`
- `hoc_spine/orchestrator/handlers`
- `hoc_spine/orchestrator/coordinators`
- `hoc_spine/authority`

Counts:
- Total core-layer scripts: `449`
- Linked core-layer scripts: `42`
- **Delta core-layer scripts without UC linkage: `407`**

## Primary 6 Domains (mission focus)
Domains: `activity`, `incidents`, `policies`, `controls`, `analytics`, `logs`

Aggregate:
- Total scripts: `260`
- Linked scripts: `34`
- **Delta scripts without UC linkage: `226`**
- Coverage: `13.1%`

Per-domain:

| Domain | Total | Linked | Unlinked Delta | Coverage |
| --- | ---: | ---: | ---: | ---: |
| activity | 20 | 2 | 18 | 10.0% |
| analytics | 41 | 9 | 32 | 22.0% |
| controls | 23 | 2 | 21 | 8.7% |
| incidents | 37 | 7 | 30 | 18.9% |
| logs | 42 | 5 | 37 | 11.9% |
| policies | 97 | 9 | 88 | 9.3% |
| **ALL_6** | **260** | **34** | **226** | **13.1%** |

## Artifacts Produced
- Full unlinked list (all `hoc/cus`):  
  `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
- Unlinked list (core 6 domains only):  
  `app/hoc/docs/architecture/usecases/HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`

## Interpretation
- UC registry status is fully GREEN (`32/32`), but script-level UC linkage is still sparse.
- The backlog to generate additional UC linkages from existing code context is currently:
  - `531` scripts across all `hoc/cus` Python modules, or
  - `226` scripts across the primary 6 domain core layers.

## Post Wave-1 Update (2026-02-12)
- Wave-1 (`policies + logs`) was completed and then independently audited.
- Canonical coverage artifacts were reconciled to Wave-1 outcomes.

Updated canonical totals:
- Total scripts: `573`
- `UC_LINKED`: `75`
- `NON_UC_SUPPORT`: `97`
- `UNLINKED` residual: `401` (down from `531`)

Updated core-6 residual:
- Core-6 unlinked residual (core-layer scope): `101` (down from `226`)

Reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_1_AUDIT_2026-02-12.md`

## Post Wave-2 Update (2026-02-12)
- Wave-2 (`analytics + incidents + activity`) was completed and independently audited.
- Canonical coverage artifacts were reconciled to Wave-2 outcomes.

Updated canonical totals:
- Total scripts: `573`
- `UC_LINKED`: `110`
- `NON_UC_SUPPORT`: `142`
- `UNLINKED` residual: `321` (down from `401`)

Updated core-6 residual:
- Core-6 unlinked residual (core-layer scope): `21` (down from `101`)
- Current core-6 residual domain: `controls` only.

Reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md`

## Post Wave-3 Update (2026-02-12)
- Wave-3 (`controls + account`) was completed and independently audited.
- Canonical coverage artifacts were reconciled to Wave-3 outcomes.

Updated canonical totals:
- Total scripts: `573`
- `UC_LINKED`: `129`
- `NON_UC_SUPPORT`: `175`
- `UNLINKED` residual: `269` (down from `321`)

Updated core-6 residual:
- Core-6 unlinked residual (core-layer scope): `0` (down from `21`)
- Core-6 script coverage is now fully classified for core-layer scope.

Reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_AUDIT_2026-02-12.md`

## Post Wave-4 Update (2026-02-12)
- Wave-4 (`hoc_spine + integrations + api_keys + overview + agent + ops + apis`) was completed and independently audited.
- Canonical coverage artifacts and tracking docs were reconciled to Wave-4 outcomes.

Updated canonical totals:
- Total scripts: `573`
- `UC_LINKED`: `176`
- `NON_UC_SUPPORT`: `278`
- `UNLINKED` residual: `119` (down from `269`)

Updated scope residuals:
- Wave-4 target residual (target list of `150` scripts): `0`
- Core-6 residual (core-layer scope): `0` (unchanged)

Reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_AUDIT_2026-02-12.md`

## Full-Scope UC Generation Run (2026-02-12)
- User-directed full-scope run executed across all scripts (including wave-covered scripts), not just residual gaps.
- Generated:
  - `app/hoc/docs/architecture/usecases/HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`
  - `app/hoc/docs/architecture/usecases/UC_FULL_SCOPE_USECASE_GENERATION_2026-02-12.md`

Full-scope action summary:
- `KEEP_EXISTING_UC`: `176`
- `KEEP_NON_UC_SUPPORT`: `278`
- `RECLASSIFY_NON_UC_SUPPORT` (init): `31`
- `NEW_UC_LINK` (new UC candidates `UC-033..UC-040`): `88`
