# HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_T1_T8_Taskpack_plan

**Created:** 2026-02-21 19:10:06 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION

## 1. Objective

- Primary outcome: execute and close Pre-Wave0 `T1..T8` with deterministic evidence so Wave A can be started with explicit go/no-go confidence.
- Business/technical intent: lock in-house auth replacement direction (Clove canonical), define migration/security controls, and establish `hoc/*` observability + debugger baseline before frontend rebuild wave work.

## 2. Scope

- In scope:
- Execute all Pre-Wave0 tasks defined in `HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan.md`.
- Produce all 8 required artifacts (T1..T8) in `backend/app/hoc/docs/architecture/usecases/`.
- Update `...Pre_Wave0..._plan_implemented.md` with truthful statuses/evidence.
- Run required validation/gate commands and capture outputs.

- Out of scope:
- Wave A+ implementation work.
- Large code refactors unrelated to T1..T8 documentation/audit outputs.
- Repo-wide debt cleanup outside touched files.

## 3. Assumptions and Constraints

- Assumptions:
- Clove is canonical auth provider and Clerk is deprecated.
- `hoc/*` is canonical surface for future contracts.
- Stagetest remains primary runtime proving ground.

- Constraints:
- No force-push, no amend, no unrelated file edits.
- Maintain PR hygiene: only scoped doc/evidence changes unless a task requires code adjustment to validate facts.
- All claims must include concrete file/line or command evidence.

- Non-negotiables:
- Tenant-bound auth context and machine auth continuity must be explicitly addressed.
- Auth and observability designs must be actionable (not abstract).
- Wave A remains blocked unless T1..T8 are marked `DONE` with evidence.

## 4. Acceptance Criteria

1. All task artifacts T1..T8 are created and populated with concrete evidence.
2. `HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan_implemented.md` is updated with final statuses and command outputs.
3. Verification command pack runs and results are documented.
4. Go/No-Go statement for Wave A is explicit, date-stamped, and justified.
5. PR hygiene is preserved (scoped files, commit/push summary, no force push).

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Auth Audit | Inventory current auth behavior end-to-end (frontend/backend flows, guards, providers, machine path, route surfaces). | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Pre_Wave0_Auth_Audit_2026-02-21.md` | Must include frontend `/api/v1/*` call-site inventory with file:line and classification. |
| T2 | Auth Design | Produce first-party auth architecture spec and API contract for canonical `hoc/*`. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_FirstParty_Auth_Architecture_2026-02-21.md` | Must include selected auth model and rationale against alternatives. |
| T3 | Security | Produce threat model + minimum baseline controls and enforcement map. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Auth_Threat_Model_2026-02-21.md` | Depends on T2 output; include deny reason taxonomy. |
| T4 | Migration | Define Clerk sunset + phased cutover/rollback with runtime proof points. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Auth_Migration_Cutover_Plan_2026-02-21.md` | Must include machine-auth continuity checks at each phase. |
| T5 | Observability Audit | Baseline existing HOC telemetry/debug capability and identify gaps. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Observability_Baseline_Audit_2026-02-21.md` | Gap analysis against required standard (T6), not greenfield survey. |
| T6 | Observability Design | Define required observability standard for all canonical lanes. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Observability_Standard_2026-02-21.md` | Include required fields, correlation model, and dashboard minimums. |
| T7 | Debugger Design | Define operator debugger slice spec for triage/replay/root-cause. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_System_Debugger_Spec_2026-02-21.md` | Must map to stagetest runtime and release operations. |
| T8 | Gate Pack | Produce Pre-Wave0 go/no-go checklist + script refs + pass/fail matrix. | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Pre_Wave0_Gate_Checklist_2026-02-21.md` | Must state explicit Wave A start decision. |

## 6. Execution Order

1. T1 (Auth Audit)
2. T5 (Observability Audit)
3. T2 (Auth Design)
4. T3 (Security)
5. T4 (Migration)
6. T6 (Observability Design)
7. T7 (Debugger Design)
8. T8 (Gate Pack + Go/No-Go)
9. Update `...Pre_Wave0..._plan_implemented.md` and push changes

## 7. Verification Commands

```bash
# Bootstrap context
cd /root/agenticverz2.0
scripts/ops/hoc_session_bootstrap.sh --strict

# Auth inventory
rg -n "Clerk|clove|AUTH_PROVIDER|ProtectedRoute|FounderRoute|Authorization|X-AOS-Key|provider/status" website/app-shell/src backend/app/auth backend/app/hoc

# Canonical vs legacy route usage
rg -n "'/api/v1/|\"/api/v1/|/hoc/api/|/apis/ledger|/apis/swagger" website/app-shell/src backend/app/hoc

# Runtime probe baseline
curl -sS -o /tmp/prewave0_ledger.json -w "%{http_code}\n" https://stagetest.agenticverz.com/apis/ledger/cus
curl -sS -o /tmp/prewave0_swagger.json -w "%{http_code}\n" https://stagetest.agenticverz.com/apis/swagger/cus

# Governance checks for touched scope
python3 scripts/ci/check_layer_boundaries.py
python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_files>
```

## 8. Risks and Rollback

- Risks:
- Incomplete inventory could produce migration blind spots.
- Overly broad scope could delay Wave A without increasing confidence.
- Drift between plan claims and runtime may create false go/no-go confidence.

- Rollback plan:
- Keep taskpack outputs doc-only until explicitly approved for implementation.
- If any gate is ambiguous, mark `BLOCKED`, capture exact blocker, and do not promote Wave A.

## 9. Claude Fill Rules

1. Update each task status to `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Include concrete evidence paths and command outputs.
3. Do not claim completion without artifact file creation.
4. Keep statements date-specific and non-stale.
5. Update `HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan_implemented.md` as the canonical execution tracker.
6. Commit and push with scoped diff only.

## 10. Required Return Format

1. Files changed (grouped by task T1..T8)
2. Per-task status table with artifact links
3. Verification command outputs (key lines)
4. Explicit Wave A Go/No-Go decision and rationale
5. Commit SHA + PR link
6. Remaining blockers (PR-owned vs repo-wide)
