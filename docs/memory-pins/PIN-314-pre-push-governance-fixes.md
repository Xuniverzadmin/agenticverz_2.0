# PIN-314: Pre-Push Governance Fixes

**Status:** COMPLETE
**Created:** 2026-01-05
**Completed:** 2026-01-05
**Category:** Governance / CI / Hooks

---

## Summary

Correct pre-push hook scope to validate only committed delta (not workspace state), and fix lint rule false positives for replay URL identifiers.

---

## Problem Statement

1. **Pre-push hook scans workspace** instead of git-scoped committed delta
   - Untracked files (e.g., CAP-006 WIP) block pushes of unrelated work
   - Requires `--no-verify` bypass (governance violation)

2. **Lint rule mismatch** with backend API
   - Rule `incident_id_in_replay_url` expects `call_id`
   - Backend replay API (H1 Replay UX) uses `incident_id` by design
   - False positive on correct code

---

## Resolution

### Root Cause Analysis

1. **Hook Scope Issue**: `check_frontend_api_calls()` in `ci_consistency_check.sh` was scanning entire workspace using `find` instead of git delta.

2. **Lint Rule Issue**: Two replay API systems exist:
   - **H1 Replay UX** (NEW): `/replay/{incident_id}/slice|summary|timeline` — uses `incident_id`
   - **Legacy Replay**: `/guard/replay/{call_id}` — uses `call_id`

   The lint rule incorrectly expected `call_id` for all replay URLs.

### Fixes Applied

1. **Git-Scoped File Discovery**: Modified hook to use `git diff --name-only origin/main...HEAD`
2. **Lint Script Enhancement**: Added `--files` flag for selective file checking
3. **Lint Rule Update**: Removed incorrect rules, updated ENDPOINT_ID_CONTRACTS
4. **Regression Tests**: 14 tests covering valid and invalid patterns

---

## Task Groups

### G-1: Pre-Push Hook Scope Correction (MANDATORY)

| Task | Description | Status |
|------|-------------|--------|
| G-1.1 | Identify current hook scope | COMPLETE |
| G-1.2 | Restrict to committed delta | COMPLETE |
| G-1.3 | Fail fast on empty file set | COMPLETE |
| G-1.4 | Document hook scope contract | COMPLETE |

**Files Modified:**
- `scripts/ops/ci_consistency_check.sh` — Git-scoped file discovery
- `scripts/ops/lint_frontend_api_calls.py` — Added `--files` flag
- `docs/governance/PRE_PUSH_SCOPE_CONTRACT.md` — Scope contract documentation

### G-2: Lint Rule Correction (INCIDENT ID MISMATCH)

| Task | Description | Status |
|------|-------------|--------|
| G-2.1 | Identify failing lint rule | COMPLETE |
| G-2.2 | Verify backend replay contract | COMPLETE |
| G-2.3 | Update lint rule to match API | COMPLETE |
| G-2.4 | Add regression test | COMPLETE |

**Files Modified:**
- `scripts/ops/lint_frontend_api_calls.py` — Updated ID_TYPE_PATTERNS and ENDPOINT_ID_CONTRACTS
- `scripts/ops/tests/test_lint_frontend_api_calls.py` — 14 regression tests

**API Contract Verification:**
```
H1 Replay UX (backend/app/api/replay.py):
  - GET /replay/{incident_id}/slice     → incident_id
  - GET /replay/{incident_id}/summary   → incident_id
  - GET /replay/{incident_id}/timeline  → incident_id
  - POST /replay/{incident_id}/explain/ → incident_id

Legacy Replay:
  - POST /guard/replay/{call_id}        → call_id
  - POST /v1/replay/{call_id}           → call_id
```

### G-3: Governance-Correct Enhancement (OPTIONAL - DEFERRED)

| Task | Description | Status |
|------|-------------|--------|
| G-3.1 | Introduce CAP scope awareness | DEFERRED |
| G-3.2 | Teach hook CAP scope respect | DEFERRED |
| G-3.3 | Add STOP for ambiguous ownership | DEFERRED |

**Deferral Reason:** G-3 is optional enhancement work. Core fixes (G-1, G-2) resolve the blocking issues. CAP scope awareness documented in `docs/governance/CAP_SCOPE_SCHEMA.md` for future implementation.

---

## Exit Criteria

- [x] Pre-push hook ignores untracked files
- [x] Pre-push hook ignores uncommitted work
- [x] Pre-push hook enforces committed delta only
- [x] Lint rules match backend API reality
- [x] Lint rules have regression coverage
- [x] Enforcement strength unchanged
- [x] No `--no-verify` needed going forward

---

## Evidence

### Test Results

```
Results: 14 passed, 0 failed

Test Classes:
- TestH1ReplayUrlPatterns (4 tests)
- TestH1ReplayCallIdErrors (3 tests)
- TestIncidentEndpointPatterns (2 tests)
- TestEndpointIdContracts (3 tests)
- TestNoFalsePositives (2 tests)
```

### Hook Scope Contract

Key invariants (PRE_PUSH_SCOPE_CONTRACT.md):
1. Pre-push hook MUST NOT scan workspace
2. Pre-push hook MUST use git delta
3. Pre-push hook MUST pass on empty delta
4. Pre-push hook MUST NOT block unrelated work

---

## Related PINs

- [PIN-313](PIN-313-governance-hardening-gap-closure.md) — Governance Hardening
- [PIN-306](PIN-306-capability-registry-governance.md) — Capability Registry

## Related Documents

- [PRE_PUSH_SCOPE_CONTRACT.md](../governance/PRE_PUSH_SCOPE_CONTRACT.md) — Hook scope contract
- [CAP_SCOPE_SCHEMA.md](../governance/CAP_SCOPE_SCHEMA.md) — CAP scope schema (future work)
