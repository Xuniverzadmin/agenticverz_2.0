# HOC_CUS_Strict_Stabilization_Pass_2026_02_21_plan_implemented

**Created:** 2026-02-21 07:41:41 UTC
**Executor:** Claude
**Last updated:** 2026-02-21 (remediation pass 5 — PR #33 blocker attribution correction)
**Status:** DONE (PR33-owned blockers resolved; gateway accessibility fix applied; runtime 200 pending deploy)
**Current PR:** https://github.com/Xuniverzadmin/agenticverz_2.0/pull/33 (`hoc/cus-publish-live`)
**Historical baseline:** PR #32 (`hoc/cus-stabilize-plan-20260221`) — code cherry-picked into PR #33

## 1. Execution Summary

- Overall result: T1-T12 DONE. Remediation TODOs 1-12 executed.
- Scope delivered: CUS publication endpoints via L2.1 facade, per-domain ledger artifacts (JSON+CSV+MD), 21 durable pytest tests, capability_id linkage, facade contract alignment.
- Scope not delivered: Runtime HTTP 200 for `/apis/*` endpoints — not yet deployed. Handler-level and structural tests prove correctness.
- Gateway fix delivered: `/apis/ledger/` and `/apis/swagger/` added to `PUBLIC_PATHS` in `gateway_policy.py` (PR #33).
- Publish-goal status: PARTIAL — endpoints wired, gateway unblocked, tested structurally; live HTTP 200 pending merge + deploy of PR #33.

## 2. Task Completion Matrix (Original Plan T1-T12)

| Task ID | Status | Evidence | Notes |
|---------|--------|----------|-------|
| T1 | DONE | Clean worktree on `hoc/cus-stabilize-plan-20260221`, layer boundaries PASS | Setup verified |
| T2 | DONE | OpenAPI snapshot: 394 routes PASS; CUS ledger: 502 endpoints; runtime /apis/ledger: 502, 499 unique mp | Baseline gap: OpenAPI has 0 `/hoc/api/cus/` paths (CUS uses `/cus/` prefix) |
| T3 | DONE | 4 endpoint contract: `/apis/ledger/cus`, `/apis/ledger/cus/{domain}`, `/apis/swagger/cus`, `/apis/swagger/cus/{domain}` | Design documented in `cus_publication.py` docstring |
| T4 | DONE | `_SEGMENT_TO_DOMAIN` mapping (40+ entries), `_resolve_domain()` resolves 502/502 endpoints | CUS routers use `/cus/{domain}` prefix not `/hoc/api/cus/`; ledger normalises to `/hoc/api/cus/` |
| T5 | DONE | `docs/api/HOC_CUS_API_LEDGER.json`: 502 endpoints, 499 unique mp | Regenerated via `build_cus_api_ledger.py` |
| T6 | DONE | `docs/api/cus/{domain}_ledger.json` x 10 domains, 502/502 resolved, 0 unresolved | All 10 canonical domains covered |
| T7 | PARTIAL | Handler tests pass (25/25); gateway fix applied (`PUBLIC_PATHS` updated); pre-deploy probe: 404/HTML (expected) | Runtime HTTP 200 pending deploy of PR #33. Root cause resolved: veil policy 404 due to missing public path. |
| T8 | DONE | `check_layer_boundaries.py`: CLEAN; `l5_spine_pairing_gap_detector.py`: 70 wired, 0 gaps, 0 orphaned | Full CUS dispatch conformance |
| T9 | DONE | Global: local 499 = runtime 499, ZERO DIFF; Per-domain: all 10 domains ZERO DIFF | Parity measured against pre-deploy runtime (existing ledger endpoint) |
| T10 | PARTIAL | Local gates pass; GitHub CI has 12 failures (0 PR33-owned, 12 repo-wide) | See CI Evidence section |
| T11 | DONE | This document | Corrected from initial overclaim pass |
| T12 | DONE | Commit + push + PR #33 created | See PR Hygiene Evidence |

## 3. Remediation TODO Completion Matrix

| TODO | Status | Evidence | Notes |
|------|--------|----------|-------|
| TODO-1 | DONE | Audit baseline: capability_registry_enforcer 3 BLOCKING (pre-fix), check_init_hygiene 0 blocking, check_layer_boundaries CLEAN, check_openapi_snapshot PASS | Exact baseline recorded |
| TODO-2 | DONE | `# capability_id: CAP-011` added to `apis/__init__.py`, `cus_publication.py`, `app.py`, `facades/apis/__init__.py` | `capability_registry_enforcer check-pr`: CI PASSED (4 advisory MISSING_EVIDENCE warnings, 0 blocking) |
| TODO-3 | DONE | Rewrote `from ..memory`, `from ..planners`, `from ..skills` comment patterns in `int/worker/runner.py:957-960` and `int/analytics/engines/runner.py:958-961` | Changed commented import examples to prose descriptions. `check_init_hygiene.py` already skips `#` lines; this prevents any other grep-based scanner from false-flagging. |
| TODO-4 | DONE | Created `app/hoc/api/facades/apis/__init__.py`; rewired `app.py` to import `APIS_ROUTERS` from facade | `app.py` now has facade-only imports (contract: "Imports facades (L2.1) only"). Direct `from app.hoc.api.apis` removed. |
| TODO-5 | DONE | Generated 10x `{domain}_ledger.csv` + 10x `{domain}_ledger.md` under `docs/api/cus/` | All 10 domains, 502 total endpoints |
| TODO-6 | DONE | `tests/api/test_cus_publication_api.py`: 21 tests, 7 classes | Tests: router structure (4), facade contract (4), app wiring (2), ledger data (3), domain resolution (2), per-domain artifacts (5), capability_id (1) |
| TODO-7 | DONE | This document rewritten | Corrected: T7 PARTIAL (not DONE); publish-goal PARTIAL (not ACHIEVED); no false "runtime 200" claims |
| TODO-8 | DONE | See Gates section below | All 5 gates executed and recorded |
| TODO-9 | DONE | See Baseline Known Issues section | 3 known exceptions (INT legacy imports) + 4 advisory MISSING_EVIDENCE warnings documented |
| TODO-10 | DONE | Commit on same branch, PR #33 updated | No force-push used for remediation commit |
| TODO-11 | DONE | Verified: no `--force`, no unrelated files | Staging is path-scoped |
| TODO-12 | DONE | This document | All statuses are DONE/PARTIAL/BLOCKED with concrete evidence |

## 4. Evidence and Validation

### Files Changed (Full PR #33 Inventory — 43 files)

**New code files:**
- `backend/app/hoc/api/apis/__init__.py` — APIs lane init, `# capability_id: CAP-011`
- `backend/app/hoc/api/apis/cus_publication.py` — 4 GET endpoints, domain resolution, `# capability_id: CAP-011`
- `backend/app/hoc/api/facades/apis/__init__.py` — L2.1 facade for APIs lane, `# capability_id: CAP-011`
- `backend/tests/api/test_cus_publication_api.py` — 25 durable tests, 8 classes (incl. 4 gateway public path tests)

**Modified code files:**
- `backend/app/hoc/app.py` — added `# capability_id: CAP-011`; rewired import from facade
- `backend/app/hoc/cus/hoc_spine/authority/gateway_policy.py` — added `/apis/ledger/`, `/apis/swagger/` to `PUBLIC_PATHS`; added `# capability_id: CAP-006`
- `backend/app/hoc/int/worker/runner.py` — added `# capability_id: CAP-012`; rewrote comment import examples
- `backend/app/hoc/int/analytics/engines/runner.py` — rewrote comment import examples (lines 958-961)

**New documentation files:**
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_STRICT_STABILIZATION_PASS_PLAN_2026-02-21.md` — original plan
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Strict_Stabilization_Pass_2026_02_21_plan.md` — refined plan
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Strict_Stabilization_Pass_2026_02_21_plan_implemented.md` — this document

**New ledger artifacts (31 files):**
- `docs/api/HOC_CUS_API_LEDGER.json` — global CUS ledger (502 endpoints)
- `docs/api/HOC_CUS_API_LEDGER.md` — global CUS ledger (markdown)
- `docs/api/cus/{domain}_ledger.json` x 10 — per-domain JSON ledgers
- `docs/api/cus/{domain}_ledger.csv` x 10 — per-domain CSV ledgers
- `docs/api/cus/{domain}_ledger.md` x 10 — per-domain MD ledgers

### Local Gates Executed

```
capability_registry_enforcer check-pr:  CI PASSED (4 advisory MISSING_EVIDENCE, 0 blocking) — after CAP-012 fix
check_init_hygiene.py --ci:             0 blocking violations (3 known INT exceptions)
check_layer_boundaries.py:              CLEAN — 0 violations
check_openapi_snapshot.py:              PASS — 394 routes, valid JSON
test_stagetest_read_api.py:             8/8 PASS
test_cus_publication_api.py:            25/25 PASS (incl. 4 gateway public path tests)
```

### GitHub CI Evidence (from `gh pr checks 33`)

**CI Snapshot Timestamp (UTC):** 2026-02-21 10:03:04 UTC
**Snapshot counts:** SUCCESS: 37, FAILURE: 7, IN_PROGRESS: 5, SKIPPED: 5
**Note:** Counts reflect a point-in-time capture; in-progress checks will settle to final pass/fail. Previous settled run: 39 pass, 12 fail, 5 skipped.

**PR33-owned checks:**

| Check | Status | Notes |
|-------|--------|-------|
| Capability Linkage Check | PASS | CAP-006 on gateway_policy.py, CAP-011 on apis files, CAP-012 on worker runner |

**Passing checks (39):**
Capability Linkage Check, CI Gate, Consistency Check, DB-AUTH-001 Compliance,
G1 Registry Mutation Guard, G2 Plane Purity Guard, G3 Taxonomy Lock Guard,
G4 Worker Auth Guard, G5 Authority Guard, GQ-L2-CONTRACT-READY Evaluation,
Layer Integration Tests, Mypy Type Safety, Qualifier Summary, SQLModel Pattern Lint (Full),
UI Expansion Guard, Validate OpenAPI Snapshot, Validate Registry,
cleanup-neon-branch, determinism, env-misuse-guard, feature-intent-guard,
frozen-files-guard, golden-replay-guard, governance-tripwire, integration,
lint-alerts, migration-check, mypy-check, priority4-intent-guard,
priority5-intent-guard, pyright-check, run-migrations, secrets-scan,
setup-neon-branch, sql-misuse-guard, ui-hygiene, unit-tests,
workflow-engine, workflow-golden-check

**Repo-wide failures (12, also fail on origin/main):**

| Check | Root Cause | PR33-owned? |
|-------|-----------|-------------|
| claude-authority-guard | CLAUDE_AUTHORITY.md hash mismatch (file identical to origin/main; CI YAML hash stale) | NO |
| Import Hygiene | 50+ `datetime.utcnow()` calls across untouched legacy files | NO |
| Enforce L4/L6 Boundaries | 93 layer-segregation violations, concentrated in `hoc/int` agent engines (e.g., `worker_engine.py`, `credit_engine.py`, `registry_engine.py`) | NO |
| layer-enforcement | 701 errors, 81 warnings across untouched model files | NO |
| Truth Preflight | `NoReferencedTableError`: `policy_rules_legacy` FK table missing in models | NO |
| Post-Flight Hygiene | 5 syntax errors in untouched files + 5804 warnings | NO |
| Browser Integration Tests | Migration failure: `relation "runs" does not exist` (`UndefinedTable` during `ALTER TABLE runs ADD COLUMN authorization_decision`) | NO |
| Integration Integrity Gate | Failed because `BIT_STATUS=failure` (downstream of Browser Integration Tests) | NO |
| e2e-tests | `ModuleNotFoundError`: no module `app.worker` | NO |
| costsim | `RuntimeError`: no current event loop in MainThread | NO |
| costsim-wiremock | `RuntimeError`: no current event loop in MainThread | NO |
| m10-tests | Assertion failures (e.g., "Published event should be claimed") | NO |

### Publication Evidence

- `GET /apis/ledger/cus`: Handler invocation returns `{total: 502, domains: [10], unique_method_path: 499}` — structural PASS
- `GET /apis/ledger/cus/{domain}`: All 10 domains return correct counts — structural PASS
- `GET /apis/swagger/cus`: Handler invocation returns filtered OpenAPI spec — structural PASS
- `GET /apis/swagger/cus/{domain}`: Handler invocation returns per-domain OpenAPI — structural PASS
- **Runtime HTTP 200: NOT YET VERIFIED** — pending deploy of PR #33 (gateway fix)

### Pre-Deploy Runtime Probes (2026-02-21, before PR #33 merge)

| Endpoint | HTTP | Content-Type | Verdict |
|----------|------|-------------|---------|
| `GET /apis/ledger/cus` | 404 | application/json | Veil policy 404 — route not deployed + path not public |
| `GET /apis/ledger/cus/activity` | 404 | application/json | Same — veil policy blocks unauthenticated |
| `GET /apis/swagger/cus` | 200 | text/html | Frontend SPA catch-all (not backend handler) |
| `GET /apis/swagger/cus/activity` | 200 | text/html | Frontend SPA catch-all (not backend handler) |

**Root cause identified and fixed:** Gateway `PUBLIC_PATHS` missing `/apis/ledger/` and `/apis/swagger/` prefixes.
**Fix applied:** PR #33 (`hoc/cus-publish-live`) — adds scoped prefix entries to `gateway_policy.py`.

### Parity Evidence

- Global CUS parity (local vs runtime `/apis/ledger`): **ZERO DIFF** (499 unique mp both sides)
- Per-domain parity (all measured against runtime):
  - account: 32/32, activity: 20/20, analytics: 33/33, api_keys: 13/13, controls: 7/7
  - incidents: 20/20, integrations: 54/54, logs: 47/47, overview: 5/5, policies: 268/268

## 5. Blocker Classification

### PR #33-owned (all resolved)

| Issue | Status | Fix |
|-------|--------|-----|
| `int/worker/runner.py` missing `capability_id` | FIXED | Added `# capability_id: CAP-012` |
| `gateway_policy.py` missing `capability_id` | FIXED | Added `# capability_id: CAP-006` |
| 4x `MISSING_EVIDENCE` for CAP-011 files | ADVISORY (non-blocking) | Register files in CAPABILITY_REGISTRY.yaml evidence paths |
| `/apis/*` not in gateway `public_paths` | FIXED | Added `/apis/ledger/` and `/apis/swagger/` to `PUBLIC_PATHS` in `gateway_policy.py` |

### Repo-wide canonical HOC backlog (not tombstoned)

| Issue | CI Check | Root Cause |
|-------|----------|-----------|
| CLAUDE_AUTHORITY.md hash mismatch | claude-authority-guard | CI YAML ratified hash stale vs actual file on main |
| 50+ `datetime.utcnow()` calls | Import Hygiene | Legacy code across INT/CUS/models not yet migrated to `datetime.now(tz=UTC)` |
| 93 layer-segregation violations | Enforce L4/L6 Boundaries | Concentrated in `hoc/int` agent engines (`worker_engine.py`, `credit_engine.py`, `registry_engine.py`, etc.) |
| 701 errors, 81 warnings in model files | layer-enforcement | Layer check overly broad against L7 model layer |
| `NoReferencedTableError: policy_rules_legacy` | Truth Preflight | Model FK references non-existent table; blocks app startup in CI |
| 5 syntax errors in untouched files | Post-Flight Hygiene | `integrated_runtime.py`, `stub_planner.py`, `cost_snapshots_engine.py` |
| Migration failure: `relation "runs" does not exist` | Browser Integration Tests | `UndefinedTable` during `ALTER TABLE runs ADD COLUMN authorization_decision` |
| `BIT_STATUS=failure` | Integration Integrity Gate | Downstream of Browser Integration Tests failure |
| `ModuleNotFoundError: app.worker` | e2e-tests | Missing worker module in test environment |
| `RuntimeError: no current event loop` | costsim, costsim-wiremock | Event loop not available in MainThread |
| Assertion failures | m10-tests | e.g., "Published event should be claimed" — test expectation drift |
| 3x legacy `from app.services` imports | check_init_hygiene (warning) | `int/analytics/engines/runner.py` — known exceptions, non-blocking |

## 6. PR Hygiene Evidence

- Clean worktree used: YES (`/tmp/hoc-cus-publish-live` on `hoc/cus-publish-live`)
- Scope-bounded file staging confirmed: YES
- Force push used (must be no): NO
- PR URL: https://github.com/Xuniverzadmin/agenticverz_2.0/pull/33
- PR body includes metrics/commands/blockers (yes/no): YES
- Historical baseline: PR #32 (`hoc/cus-stabilize-plan-20260221`) — code cherry-picked into PR #33

## 7. Deviations from Plan

- Deviation: T7 marked PARTIAL (was overclaimed as DONE)
- Reason: Gateway public-path fix applied in code (PR #33), but runtime HTTP 200 still unverified because PR is not yet merged/deployed — stagetest serves 404 (veil policy) or SPA fallback for `/apis/*` paths.
- Impact: LOW — structural correctness proven via 25 tests + handler invocation; root cause (missing public path) resolved in code.

- Deviation: `check_openapi_snapshot.py` was initially reported as missing
- Reason: Script is at repo root `scripts/ci/`, not under `backend/scripts/ci/`
- Impact: NONE — corrected in remediation; now runs and PASSES

- Deviation: TODO-3 comment rewrites are in INT files (out of original CUS-only scope)
- Reason: Explicitly requested in remediation TODO list
- Impact: NONE — changes are cosmetic (comment text only, no logic change)

## 8. Handoff Notes

- Follow-up recommendations:
  1. ~~**INT-scope PR needed:** Add `/apis/` to `gateway_config.py` `public_paths`~~ RESOLVED in PR #33 (`gateway_policy.py`)
  2. **Registry evidence:** Add CUS publication files to CAP-011 evidence paths in `CAPABILITY_REGISTRY.yaml` (resolves 4 advisory warnings)
  3. **CI drift detection:** Wire per-domain ledger comparison into PR gates
  4. **OpenAPI alias:** Formalize `/cus/X` → `/hoc/api/cus/X` mapping in OpenAPI spec generation
  5. **Pre-existing:** `policy_snapshots.policy_version` column needs migration (knowledge domain)
- Risks remaining:
  1. Runtime HTTP 200 unverified until deploy
  2. 3 duplicate method+path entries (502 total, 499 unique) — expected (public vs internal router overlap)
