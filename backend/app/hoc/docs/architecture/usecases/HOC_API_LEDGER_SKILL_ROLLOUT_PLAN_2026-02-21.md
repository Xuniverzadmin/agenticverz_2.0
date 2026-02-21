# HOC API Ledger Skill Rollout Plan (hoc/*)

**Date:** 2026-02-21  
**Scope:** `backend/app/hoc/**`  
**Primary Skill:** `/root/.codex/skills/hoc-cus-api-ledger-rollout`  
**Status:** IN_PROGRESS (Wave 1-2 COMPLETE; Wave 3-4 PENDING)

## Final Goal
Produce a deterministic, governance-compliant API ledger for all HOC API surfaces (`hoc/*`), with OpenAPI-backed registry artifacts and a stagetest-published ledger endpoint (`/apis/ledger`) that returns `200 OK` with non-empty HOC data.

## Step-by-Step Goals
1. Confirm governance context and architecture invariants before any rollout edits.
2. Expand execution from `cus/*` to all HOC API surfaces (`cus`, `fdr`, `int`, shared HOC API roots).
3. Generate deterministic ledger artifacts (JSON/CSV/MD) per scope and merged HOC-wide output.
4. Ensure OpenAPI contract alignment for every registered route.
5. Publish/verify HOC ledger response at stagetest evidence route (`/apis/ledger`).
6. Re-audit architecture gates and capability gates with skeptical reporting.
7. Land in clean, wave-scoped PRs with memory pins and index updates.

## Execution Snapshot (2026-02-21)
- `Phase 0`: COMPLETE (strict bootstrap executed, dirty-tree preserved via stash, clean worktree created).
- `Phase 1`: COMPLETE for `cus/*` and `fdr/*` baseline inventory.
- `Phase 2`: IN_PROGRESS.
  - Generated: `docs/api/HOC_CUS_API_LEDGER.json`
  - Generated: `docs/api/HOC_CUS_API_LEDGER.csv`
  - Generated: `docs/api/HOC_CUS_API_LEDGER.md`
  - Generated: `docs/api/HOC_FDR_API_LEDGER.json`
  - Generated: `docs/api/HOC_FDR_API_LEDGER.csv`
  - Generated: `docs/api/HOC_FDR_API_LEDGER.md`
  - Generated: `docs/api/HOC_API_LEDGER_ALL.json`
  - Generated: `docs/api/HOC_API_LEDGER_ALL.csv`
  - Generated: `docs/api/HOC_API_LEDGER_ALL.md`
- `Phase 3`: IN_PROGRESS.
  - Generated mismatch audit: `docs/api/HOC_CUS_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
  - Generated mismatch summary: `docs/api/HOC_CUS_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
  - Generated mismatch audit: `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
  - Generated mismatch summary: `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
  - Current skeptical finding: local `docs/openapi.json` has `0` rows under both `/hoc/api/cus/*` and `/hoc/api/fdr/*` while source-derived ledgers report active routes.
- `Phase 4`: COMPLETE.
  - `https://stagetest.agenticverz.com/openapi.json` => `200 application/json`
  - `https://stagetest.agenticverz.com/apis/ledger` => `200 application/json` (Wave 1 evidence)
  - Wave 2 publication logic updated to return merged HOC ledger (`CUS+FDR`) when available.
- `Phase 5`: COMPLETE for Wave 2 changed files (changed-file checks pass; legacy HOC scope debt remains open).
- `Phase 6`: COMPLETE for Wave 2 PR scope updates; remaining waves still pending.

## Execution Model

### Phase 0 — Bootstrap and Guardrails
- Run: `scripts/ops/hoc_session_bootstrap.sh --strict`
- Load mandatory governance/architecture docs.
- Validate current branch hygiene; if dirty, use clean worktree PR flow.

### Phase 1 — HOC Surface Inventory (Read-Only)
- Enumerate route surfaces under:
  - `backend/app/hoc/api/cus/**`
  - `backend/app/hoc/api/fdr/**`
  - `backend/app/hoc/api/int/**`
  - any additional `backend/app/hoc/api/**` direct route files
- Build baseline inventory from OpenAPI and source fallback.
- Output baseline summary (counts by domain/scope).

### Phase 2 — Skill Generalization for hoc/*
- Keep current `hoc-cus-api-ledger-rollout` intact.
- Extend execution usage for other prefixes with parameters:
  - `--path-prefix /hoc/api/cus/`
  - `--path-prefix /hoc/api/fdr/`
  - `--path-prefix /hoc/api/int/`
- Generate per-scope artifacts:
  - `docs/api/HOC_CUS_API_LEDGER.*`
  - `docs/api/HOC_FDR_API_LEDGER.*`
  - `docs/api/HOC_INT_API_LEDGER.*`
- Generate merged artifact:
  - `docs/api/HOC_API_LEDGER_ALL.*`

### Phase 3 — OpenAPI Contract Alignment
- For each scope, compare ledger rows vs OpenAPI paths.
- Classify each mismatch:
  - `OPENAPI_MISSING_PATH`
  - `OPENAPI_STALE_OPERATION`
  - `SOURCE_ONLY_LEGACY_ROUTE`
- Remediate in small batches until mismatch count is zero or explicitly tombstoned with rationale.

### Phase 4 — Publication and Runtime Evidence
- Ensure publication endpoint returns HOC ledger view:
  - target: `https://stagetest.agenticverz.com/apis/ledger`
- Evidence checks:
  - HTTP 200
  - JSON content type
  - includes HOC rows (not empty)
  - includes generation timestamp + source marker

### Phase 5 — Governance Audit with Skepticism
Run and record:
- `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
- `python3 scripts/ops/layer_segregation_guard.py --scope hoc`
- `python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_py_files>`
- OpenAPI snapshot check: `python3 scripts/ci/check_openapi_snapshot.py`

### Phase 6 — PR and Documentation Closure
Per wave PR requirements:
- plan + implemented doc status updates
- ledger artifact links in docs
- memory pin + `docs/memory-pins/INDEX.md` update
- explicit before/after metrics in PR body

## Wave Plan

### Wave 1 (CUS) — Stabilize existing skill lane
- Generate/refresh `HOC_CUS_API_LEDGER.*`
- Resolve OpenAPI mismatches for CUS only
- Publish CUS evidence in `/apis/ledger`

### Wave 2 (FDR) — Founder surfaces
- Generate `HOC_FDR_API_LEDGER.*`
- Align stagetest/founder endpoints with OpenAPI
- Verify publication includes FDR rows

### Wave 3 (INT) — Internal surfaces
- Generate `HOC_INT_API_LEDGER.*`
- Align internal route coverage and auth metadata
- Verify publication includes INT rows (if intended for exposure)

### Wave 4 (HOC-All Merge)
- Generate merged `HOC_API_LEDGER_ALL.*`
- Complete mismatch/tombstone decisions
- Final evidence snapshot and signoff pin

## Acceptance Criteria
1. Ledger artifacts exist for CUS/FDR/INT plus merged HOC-all.
2. OpenAPI mismatch backlog for in-scope lanes is closed or tombstoned with explicit rationale.
3. `/apis/ledger` returns `200` with non-empty HOC data on stagetest.
4. Governance checks pass for changed files.
5. PRs are wave-scoped and reproducible.

## PR Hygiene Rules
- One wave per PR.
- No unrelated file staging.
- Use clean worktree when local tree is dirty.
- No force-push unless explicitly approved.
- Include exact command evidence and exit codes.

## Risks and Mitigations
- **Risk:** stale OpenAPI snapshot hides live routes.  
  **Mitigation:** source fallback inventory + runtime OpenAPI fetch.
- **Risk:** cross-scope drift between route files and publication payload.  
  **Mitigation:** deterministic artifact generation + merged ledger diff check.
- **Risk:** broad hoc/* scope creates oversized PRs.  
  **Mitigation:** strict wave split (CUS/FDR/INT/merge).

## Immediate Next Action
Start **Wave 3 (INT)** execution and extend merged ledger generation to include `HOC_INT_API_LEDGER.*`.
