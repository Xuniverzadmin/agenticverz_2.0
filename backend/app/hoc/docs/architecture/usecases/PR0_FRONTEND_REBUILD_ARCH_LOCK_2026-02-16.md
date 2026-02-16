# PR0_FRONTEND_REBUILD_ARCH_LOCK_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-0 Architecture Lock (planning + governance only)
- Linked Loop: `L001`
- Execution mode: strategy-first, no frontend implementation in this PR

## Objective
Lock a production-safe rebuild strategy for frontend delivery that aligns with live HOC architecture (`backend/app/hoc/*`) and avoids extending legacy app-shell complexity.

## Authoritative Baseline
- Live HOC API wiring: `backend/app/hoc/app.py`
- Canonical customer domains: `backend/app/hoc/api/facades/cus/__init__.py`
- Legacy API prefix behavior: `backend/app/hoc/api/int/general/legacy_routes.py`
- Frontend reference app (legacy/reference mode): `website/app-shell`

## Locked Decisions
1. Build a new frontend app package in parallel; do not extend `website/app-shell` feature scope.
2. Execute in small PR sequence with explicit acceptance gates.
3. No mock adapter track for this rebuild.
4. Validation environments are real only:
- `stagetest.agenticverz.com`
- `preflight.agenticverz.com`
5. Typed API boundary remains mandatory in new frontend app (single client, runtime validation, request-id propagation).
6. Backend must harden CUS facade exposure at HTTP edge before broad frontend cutover.
7. Existing app-shell remains reference-only and is declared legacy/deprecation path; final state is 410/legacy for replaced surfaces.

## Architecture Direction

### 1) Frontend Packaging Model
- New app package (parallel run) becomes primary target for new features.
- `website/app-shell` remains read-only/reference for migration knowledge.

### 2) Backend Exposure Model (Facade-First)
- Keep domain ownership in canonical CUS domain structure.
- Introduce explicit CUS facade exposure at HTTP edge (grouped by domain) to avoid direct scattered L2 endpoint exposure.
- Runs feature pack starts first (PR-1) as facade hardening anchor.

### 3) Legacy Prefix Policy
- `/api/v1/*` is treated as legacy and is not a target for new frontend work.
- Migration must map old consumers to canonical/facade paths and remove dependency on version-prefixed routes.

## PR Sequence (Locked)
1. PR-0: strategy and contract lock (this document + compatibility matrix).
2. PR-1: backend Runs facade hardening plan + verification contract.
3. PR-2: new frontend app scaffold + strict API boundary setup.
4. PR-3: `/runs` read-only vertical slice with server pagination.
5. PR-4+: feature-pack iterations (replay, incidents, policies, controls).

## Non-Negotiables to Carry Forward
- Small reviewable increments only.
- Deterministic ordering for replay/timeline data (composite key, not timestamp-only).
- Observable errors and request correlation visibility in UI.
- No direct network calls in UI components.

## Exit Criteria for PR-0
1. Strategy lock documented and approved.
2. Endpoint compatibility matrix created from current frontend vs live HOC exposure.
3. PR-1 hardening plan and verification checklists authored.

## Evidence
- `artifacts/strategic_thinker_loops/L001/L001_micro_execution_plan.md`
- `docs/memory-pins/PIN-573-frontend-rebuild-strategy-lock-pr-0-and-pr-1.md`
