# UC Script Coverage Program (2026-02-12)

## Objective
Close the gap between UC-level GREEN status and script-level UC linkage coverage under `app/hoc/cus/*`.

## Step 1 Output (Baseline)
- Classification inventory:
  - `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`
- Unlinked script backlog:
  - `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
- Core-6 unlinked backlog (activity/incidents/policies/controls/analytics/logs):
  - `app/hoc/docs/architecture/usecases/HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`

Baseline metrics:
- Total `hoc/cus` scripts: `573`
- UC-linked: `42`
- Unlinked delta: `531`
- Coverage: `7.3%`

Core-6 metrics:
- Total scripts: `260`
- UC-linked: `34`
- Unlinked delta: `226`
- Coverage: `13.1%`

## Post Wave-1 Canonical State
- Wave-1 (`policies + logs`) completion has been audited and reconciled.
- Updated classification totals:
  - `UC_LINKED`: `75`
  - `NON_UC_SUPPORT`: `97`
  - `UNLINKED`: `401`
- Updated core-6 residual (core-layer scope): `101`
- Audit reference:
  - `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_1_AUDIT_2026-02-12.md`

## Post Wave-2 Canonical State
- Wave-2 (`analytics + incidents + activity`) completion has been audited and reconciled.
- Updated classification totals:
  - `UC_LINKED`: `110`
  - `NON_UC_SUPPORT`: `142`
  - `UNLINKED`: `321`
- Updated core-6 residual (core-layer scope): `21` (`controls` only)
- Audit reference:
  - `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md`

## Post Wave-3 Canonical State
- Wave-3 (`controls + account`) completion has been audited and reconciled.
- Updated classification totals:
  - `UC_LINKED`: `129`
  - `NON_UC_SUPPORT`: `175`
  - `UNLINKED`: `269`
- Updated core-6 residual (core-layer scope): `0`
- Audit reference:
  - `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_AUDIT_2026-02-12.md`

## Post Wave-4 Canonical State
- Wave-4 (`hoc_spine + integrations + api_keys + overview + agent + ops + apis`) completion has been audited and reconciled.
- Updated classification totals:
  - `UC_LINKED`: `176`
  - `NON_UC_SUPPORT`: `278`
  - `UNLINKED`: `119`
- Wave-4 target-scope residual: `0` (all 150 target scripts classified).
- Core-6 residual (core-layer scope): `0` (unchanged from Wave-3).
- Governance suite status: `308 passed`.
- Audit reference:
  - `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_AUDIT_2026-02-12.md`

## Full-Scope UC Generation State (2026-02-12)
- Full-scope run was executed across all scripts, including wave-covered scripts.
- Proposal artifacts:
  - `app/hoc/docs/architecture/usecases/HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`
  - `app/hoc/docs/architecture/usecases/UC_FULL_SCOPE_USECASE_GENERATION_2026-02-12.md`
- Proposed new UC candidates:
  - `UC-033..UC-040` covering `88` currently unlinked non-init scripts.
- Init-only residual handling:
  - `31` scripts proposed for `NON_UC_SUPPORT` reclassification.

## GREEN Definition (Script Coverage)
Script coverage is `GREEN` only when all conditions hold:
1. `UNLINKED` count is `0` for the target scope.
2. Every script is classified as one of:
   - `UC_LINKED`
   - `NON_UC_SUPPORT` (explicit rationale)
   - `DEPRECATED` (explicit deprecation plan/reference)
3. No script remains `UNKNOWN` or `PENDING` classification.
4. UC linkage docs contain concrete script references and evidence sections.
5. Deterministic gates pass for each wave closure.

## Classification States
- `UC_LINKED`: script is covered by an existing UC and referenced in linkage docs.
- `PENDING`: script not yet reviewed in wave review.
- `NON_UC_SUPPORT`: utility/support script that should not own a UC, with rationale.
- `DEPRECATED`: legacy script scheduled for retirement or replacement.

## Non-Negotiable Constraints
- Preserve HOC topology: `L2 -> L4 -> L5 -> L6`.
- No direct L2 -> L5/L6 wiring.
- No cross-domain L6 imports.
- No DB/ORM imports in L5 engines.

## Execution Model
- Run domain waves in this order: `policies+logs`, then `analytics+incidents+activity`, then `controls+account`, then non-core domains.
- After each wave:
  - Recompute coverage deltas.
  - Run deterministic gates.
  - Patch only architecture-compliant code/docs.
  - Update literature and prod-readiness docs.
