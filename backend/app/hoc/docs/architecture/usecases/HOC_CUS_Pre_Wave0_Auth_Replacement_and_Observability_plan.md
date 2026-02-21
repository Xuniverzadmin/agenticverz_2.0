# HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan

**Created:** 2026-02-21 14:07:38 UTC
**Executor:** Claude
**Status:** APPROVAL_PENDING

## 1. Objective

- Primary outcome: approve and lock a Pre-Wave 0 program that designs the in-house auth system and a canonical HOC observability/debugger baseline before any new frontend Wave A work starts.
- Business/technical intent: remove Clerk dependency, move to first-party auth and canonical `hoc/*` contracts, and guarantee deterministic runtime debugability for stagetest and rollout.

## 2. Scope

- In scope:
  - Full current-state audit of auth across frontend and backend.
  - Auth replacement architecture and migration/cutover plan.
  - HOC observability/debugger architecture and minimum implementation backlog.
  - Gate definitions that must pass before Wave A (new frontend build) can start.
- Out of scope:
  - Wave A frontend rebuild implementation.
  - Non-HOC repo-wide debt lane cleanup.
  - Bulk INT/FDR remediation outside auth/observability dependency edges.

## 3. Assumptions and Constraints

- Assumptions:
  - `hoc/*` is canonical and target authority for new surface contracts.
  - Stagetest is the execution proving ground before broader release.
  - CUS slice is the first productized release target.
- Constraints:
  - No reliance on Clerk for steady-state auth.
  - No `/api/v1/*` contract expansion for new work; canonical `hoc/*` only.
  - Must preserve machine-auth path for operational probes and service workflows.
- Non-negotiables:
  - Tenant-bound authorization context for CUS runtime endpoints.
  - Request correlation (`X-Request-ID` or equivalent) preserved end-to-end.
  - No Wave A coding until Pre-Wave 0 gates are met.

## 4. Acceptance Criteria

1. Current auth flows and call sites are fully inventoried with concrete file/endpoint mapping.
2. Replacement auth design is documented: identity, credentials, token/session model, refresh/revocation, tenant mapping, RBAC linkage, API key compatibility.
3. Threat model and minimum security controls are documented and approved.
4. Migration plan from Clerk to first-party auth is phased with rollback points and cutover criteria.
5. Observability design for `hoc/*` is documented: logs, metrics, traces, error taxonomy, correlation propagation.
6. System debugger scope is documented: required runtime views, filters, and drill-down paths for incident triage.
7. Verification command pack exists for pre/post-cutover checks in stagetest.
8. Pre-Wave 0 implemented report template is ready for evidence capture.
9. Explicit go/no-go gate is recorded: Wave A starts only when T1-T8 are `DONE`.
10. Machine auth (`X-AOS-Key`) flow is verified functional at each migration phase boundary via stagetest runtime probe.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Auth Audit | Inventory current auth behavior end-to-end (frontend guards/clients, backend gateway/context/rules, key paths, login/session flows). | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_Pre_Wave0_Auth_Audit_2026-02-21.md | Include exact source file references and runtime probe evidence. Enumerate all frontend `/api/v1/*` call sites with `file:line` and purpose classification (`auth-dependent` vs `data-only`). |
| T2 | Auth Design | Produce first-party auth architecture spec and contract (endpoints, payloads, token/session rules, revocation, tenant binding, RBAC interaction). | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_FirstParty_Auth_Architecture_2026-02-21.md | Must include canonical `hoc/*` endpoint map. Evaluate and select from: (a) session+password, (b) self-issued JWT, (c) lightweight OIDC provider. Decision criteria: implementation complexity (target <= 2 weeks for V1), OWASP-aligned baseline controls, and compatibility with existing `X-AOS-Key` machine path. Out of scope for V1: social login and MFA expansion. |
| T3 | Security | Produce threat model + baseline controls (credential policy, replay/CSRF/session fixation controls, key rotation, audit logging). | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_Auth_Threat_Model_2026-02-21.md | Map each control to enforcement point. Depends: T2 `DONE` (threat model targets approved design, not candidates). |
| T4 | Migration | Define Clerk sunset and migration/cutover plan with rollback and staged verification. | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_Auth_Migration_Cutover_Plan_2026-02-21.md | Include dual-run strategy and kill-switches. |
| T5 | Observability Audit | Audit existing HOC telemetry and debugging affordances; identify gaps blocking fast root-cause analysis. | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_Observability_Baseline_Audit_2026-02-21.md | Gap analysis against T6 standard (not greenfield inventory). Include logs/metrics/traces/dashboard coverage grid, and identify coverage gaps for per-endpoint latency, auth decision tracing, cross-domain correlation propagation, and structured error taxonomy. |
| T6 | Observability Design | Define required observability standard for all `hoc/*` API lanes and runtime pipelines. | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_Observability_Standard_2026-02-21.md | Must define schema keys and mandatory dimensions. |
| T7 | Debugger Design | Define system debugger product slice (operator views, filters, request replay hooks, failure taxonomy panels). | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_System_Debugger_Spec_2026-02-21.md | Target stagetest-first evidence operations. |
| T8 | Gate Pack | Produce Pre-Wave 0 gate checklist and execution script references; mark Wave A start criteria. | TODO | backend/app/hoc/docs/architecture/usecases/HOC_CUS_Pre_Wave0_Gate_Checklist_2026-02-21.md | Must include pass/fail matrix and command list. |

## 6. Execution Order

1. T1 (Auth Audit)
2. T5 (Observability Audit)
3. T2 (Auth Design)
4. T3 (Security)
5. T4 (Migration)
6. T6 (Observability Design)
7. T7 (Debugger Design)
8. T8 (Gate Pack + Wave A Go/No-Go)

## 7. Verification Commands

```bash
# 1) Session bootstrap (strict)
scripts/ops/hoc_session_bootstrap.sh --strict

# 2) Frontend auth call-site inventory
rg -n "Clerk|ProtectedRoute|FounderRoute|VITE_AUTH_BYPASS|Authorization|X-AOS-Key" website/app-shell/src

# 3) Backend auth/gateway inventory
rg -n "PUBLIC_PATHS|RBAC_RULES|not_authenticated|_authenticate|api_key|tenant_id|Authorization" backend/app/hoc

# 4) Canonical vs legacy route usage snapshot
rg -n "'/api/v1/|\"/api/v1/|/hoc/api/|/apis/ledger|/apis/swagger" website/app-shell/src backend/app/hoc

# 5) Runtime probe baseline (stagetest)
curl -sS -o /tmp/ledger.json -w "%{http_code}\n" https://stagetest.agenticverz.com/apis/ledger/cus
curl -sS -o /tmp/swagger.json -w "%{http_code}\n" https://stagetest.agenticverz.com/apis/swagger/cus

# 6) Gate checks (as applicable to touched scope)
python3 backend/scripts/ci/check_layer_boundaries.py
python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_files>
```

## 8. Risks and Rollback

- Risks:
  - Hidden dependencies on Clerk session semantics across UI components.
  - Auth cutover may break existing machine-auth or tenant mapping if not dual-validated.
  - Observability schema churn can fragment dashboards if not versioned.
- Rollback plan:
  - Keep migration staged with explicit revert points per phase.
  - Preserve current auth path behind a temporary kill-switch until new path is proven.
  - Freeze Wave A rollout if Pre-Wave 0 gates regress on auth correctness or debugability.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan_implemented.md`.

## 10. North Star Wave Map (Post Pre-Wave 0)

Precondition for all waves below: Pre-Wave 0 T1-T8 are `DONE`.

### Wave A: Cutover Decision + Isolation

- Freeze current `website/app-shell` via git tag `app-shell-freeze-v1`.
- Add CI advisory guard to block new commits to `website/app-shell/src/` after freeze tag date (tighten to blocking before Wave D completion).
- Create new frontend workspace (clean root, clean routing, no Clerk deps).
- Add compatibility notes so old suites are explicitly non-blocking for migration branch work.
- Entry requires: Pre-Wave 0 T1-T8 all `DONE`.
- Exit: new frontend lane exists and is isolated from legacy path coupling.

### Wave B: Native Auth (Own System)

- Implement first-party auth runtime from approved Pre-Wave 0 design.
- Frontend auth client uses only first-party token/session contract.
- Remove Clerk dependency from active runtime path.
- Entry requires: Wave A exit criteria met.
- Exit: login/session/tenant-bound auth works without Clerk.

### Wave C: Canonical API Contract

- Define and lock frontend-consumable canonical `hoc/*` endpoints.
- No new `/api/v1/*` usage; existing legacy references mapped or deprecated.
- Publish authoritative OpenAPI for canonical slice contracts.
- Entry requires: Wave B exit criteria met.
- Exit: contract lock with CI drift checks.

### Wave D: New Frontend Slice

- Build production-style shell for selected CUS slice.
- Wire pages/buttons/functions only to canonical `hoc/*` APIs.
- Add in-browser response visibility for debugging (`200/401/403/500`).
- Entry requires: Wave C exit criteria met.
- Exit: one end-to-end user slice functionally operable in stagetest.

### Wave E: Demo/Test Data + Ledger Publication

- Seed deterministic demo tenant data for repeatable tests.
- Ensure ledger/swagger publish domain-grouped APIs from canonical registry.
- Fix ledger emptiness by binding publication to live route registry.
- Entry requires: Wave D exit criteria met.
- Exit: deterministic test inputs and accurate API publication artifacts.

### Wave F: Observability + Debug

- Enforce end-to-end request ID propagation (UI -> API -> logs/metrics/traces).
- Provide slice dashboards (latency, auth failures, error class, top failing endpoints).
- Deliver operator debugger view with correlation-based failure triage.
- Entry requires: Wave E exit criteria met.
- Exit: incident triage from user report to root cause is deterministic.

### Wave G: E2E + Release

- Rewrite Playwright/UAT packs for new routes and auth model.
- Add release gate: contract pass + E2E pass + runtime probe pass.
- Release one product slice first, then expand domain-by-domain.
- Entry requires: Wave F exit criteria met.
- Exit: productionization-ready release packet for first slice.

## 11. Cross-Wave Required Safeguards

1. Auth threat model and minimum security baseline:
   - password/session policy, token expiry/rotation, CSRF/session strategy, audit logging.
2. Migration/deprecation policy:
   - old frontend and old endpoints have explicit deprecation windows and removal criteria.
3. Rollback policy:
   - clear rollback checkpoints for auth cutover and frontend cutover.
4. Page-level Definition of Done:
   - UI parity + API parity + observability parity + E2E coverage parity.
5. Enforcement:
   - All safeguards are enforced through T8 gate checklist criteria with explicit pass/fail evidence links.
