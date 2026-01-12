# SESSION_LIFECYCLE_SCENARIO_MATRIX

**Version:** 1.0
**Status:** AUTHORITATIVE
**Effective:** 2026-01-12
**Purpose:** Source of truth for all E2E and agent testing

---

## Overview

This document defines **all valid session states** and their associated behaviors.
It is the mandatory reference for scenario testing, multi-agent runs, and exit decisions.

**Until this document exists, scenario testing and multi-agent runs are NOT ALLOWED.**

---

## Session State Model

A session exists in one of the following pipeline positions:

```
[FRESH] → [SCRIPTS] → [CONTAINER] → [DEPLOY] → [TESTS] → [GIT_STAGED] → [GIT_PUSHED] → [EXIT_READY]
              ↓            ↓            ↓          ↓           ↓              ↓
           FAILED       FAILED       FAILED     FAILED      FAILED         FAILED
```

Each position has sub-states based on:
- **Completion status**: completed | failed | interrupted
- **HK freshness**: fresh (≤24h) | stale (>24h) | missing
- **SR artifact**: present | missing | stale

---

## State Enumeration

### S01: FRESH_SESSION

**Description:** New session, no work done yet.

| Property | Value |
|----------|-------|
| Pipeline position | None |
| Scripts | Not run |
| Container | Not built |
| Deploy | Not deployed |
| Tests | Not run |
| Git | Clean or dirty (pre-session) |
| SR artifact | Missing or previous session |
| HK artifact | May be fresh or stale |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES | - |
| `do housekeeping` | YES | - |
| New work | **BLOCKED if previous SR != RECONCILED_EXIT_READY** | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| None required | Fresh session |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | No SR artifact with RECONCILED_EXIT_READY |

---

### S02: SCRIPTS_COMPLETED

**Description:** Build scripts ran successfully.

| Property | Value |
|----------|-------|
| Pipeline position | scripts |
| Scripts | Completed |
| Container | Not built |
| Deploy | Not deployed |
| Tests | Not run |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (continue pipeline) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Build logs | Script output |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Pipeline incomplete |

---

### S03: SCRIPTS_FAILED

**Description:** Build scripts failed.

| Property | Value |
|----------|-------|
| Pipeline position | scripts (failed) |
| Scripts | Failed |
| Container | Not built |
| Deploy | Not deployed |
| Tests | Not run |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (retry from scripts) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |
| Fix code | BLOCKED until reconcile attempted | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| SR artifact | verdict: RECONCILIATION_BLOCKED |
| Error logs | Script failure output |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Scripts must pass |

---

### S04: CONTAINER_BUILT

**Description:** Container images built successfully.

| Property | Value |
|----------|-------|
| Pipeline position | container |
| Scripts | Completed |
| Container | Built |
| Deploy | Not deployed |
| Tests | Not run |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (continue to deploy) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Docker images | Built images |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Pipeline incomplete |

---

### S05: CONTAINER_FAILED

**Description:** Container build failed.

| Property | Value |
|----------|-------|
| Pipeline position | container (failed) |
| Scripts | Completed |
| Container | Failed |
| Deploy | Not deployed |
| Tests | Not run |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (retry from container) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| SR artifact | verdict: RECONCILIATION_BLOCKED |
| Docker build logs | Failure output |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Container must build |

---

### S06: DEPLOYED

**Description:** Services deployed and running.

| Property | Value |
|----------|-------|
| Pipeline position | deploy |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Not run |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (continue to tests) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Running containers | Service health checks |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Tests not run |

---

### S07: DEPLOY_FAILED

**Description:** Service deployment failed.

| Property | Value |
|----------|-------|
| Pipeline position | deploy (failed) |
| Scripts | Completed |
| Container | Built |
| Deploy | Failed |
| Tests | Not run |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (retry deploy) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| SR artifact | verdict: RECONCILIATION_BLOCKED |
| Deploy logs | Failure output |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Services must deploy |

---

### S08: TESTS_PASSED

**Description:** All tests passed.

| Property | Value |
|----------|-------|
| Pipeline position | tests |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Passed |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (continue to git) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Test results | Pass count, coverage |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Git not pushed |

---

### S09: TESTS_FAILED

**Description:** Tests failed.

| Property | Value |
|----------|-------|
| Pipeline position | tests (failed) |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Failed |
| Git | Dirty |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (will emit FAILED_TESTS) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |
| Fix code | BLOCKED until reconcile | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| SR artifact | verdict: FAILED_TESTS |
| Test results | Failure details |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Tests must pass |

---

### S10: GIT_STAGED

**Description:** Changes staged but not committed.

| Property | Value |
|----------|-------|
| Pipeline position | git_commit (pending) |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Passed |
| Git | Staged, not committed |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (commit and push) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Staged files | git status shows staged |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Git not pushed |

---

### S11: GIT_COMMITTED

**Description:** Changes committed but not pushed.

| Property | Value |
|----------|-------|
| Pipeline position | git_push (pending) |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Passed |
| Git | Committed, not pushed |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (push) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Local commit | git log shows commit |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Git not pushed |

---

### S12: GIT_PUSH_FAILED

**Description:** Git push failed.

| Property | Value |
|----------|-------|
| Pipeline position | git_push (failed) |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Passed |
| Git | Committed, push failed |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (retry push) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| SR artifact | verdict: RECONCILIATION_BLOCKED |
| Push error | Network/auth failure |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Push must succeed |

---

### S13: RECONCILED_EXIT_READY

**Description:** Full pipeline completed successfully.

| Property | Value |
|----------|-------|
| Pipeline position | Complete |
| Scripts | Completed |
| Container | Built |
| Deploy | Deployed |
| Tests | Passed |
| Git | Pushed |
| SR artifact | verdict: RECONCILED_EXIT_READY |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (no-op, already clean) | - |
| `do housekeeping` | YES | - |
| New work | YES | - |
| Exit | **ALLOWED (if HK fresh)** | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| SR artifact | verdict: RECONCILED_EXIT_READY |
| Session pin | memory/session_pins/<id>.yaml |

| Exit Verdict | Condition |
|--------------|-----------|
| CLEAN_EXIT | SR=RECONCILED_EXIT_READY AND HK fresh |
| EXIT_BLOCKED | HK stale (>24h) |

---

### S14: RECONCILE_INTERRUPTED

**Description:** Reconciliation was interrupted mid-execution.

| Property | Value |
|----------|-------|
| Pipeline position | Unknown (partial) |
| Scripts | Unknown |
| Container | Unknown |
| Deploy | Unknown |
| Tests | Unknown |
| Git | Unknown |
| SR artifact | Missing or partial |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (restart from beginning) | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Partial SR artifact | May be incomplete |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Reconcile must complete |

---

### S15: HK_STALE

**Description:** Housekeeping artifact is stale (>24h).

| Property | Value |
|----------|-------|
| HK artifact | Age > 24h |
| SR artifact | May be RECONCILED_EXIT_READY |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES | - |
| `do housekeeping` | YES (required to refresh) | - |
| New work | Depends on SR state | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| Stale HK artifact | Age exceeds threshold |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | HK must be fresh for exit |

---

### S16: HK_MISSING

**Description:** No housekeeping artifact exists.

| Property | Value |
|----------|-------|
| HK artifact | Missing |
| SR artifact | May be any state |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES | - |
| `do housekeeping` | YES (required) | - |
| New work | Depends on SR state | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| None | HK artifact missing |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | HK must exist for exit |

---

### S17: FORCED_EXIT_ATTEMPT

**Description:** User attempts to exit without proper reconciliation.

| Property | Value |
|----------|-------|
| SR artifact | Not RECONCILED_EXIT_READY |
| Exit attempt | Forced |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES | - |
| `do housekeeping` | YES | - |
| New work | BLOCKED | - |
| Exit | **MUST record DIRTY_EXIT** | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| EXIT artifact | verdict: DIRTY_EXIT |
| Warning log | Forced exit recorded |

| Exit Verdict | Condition |
|--------------|-----------|
| DIRTY_EXIT | Forced without reconciliation |

---

### S18: SERVICES_UNHEALTHY_PRE_HK

**Description:** Protected services unhealthy before housekeeping.

| Property | Value |
|----------|-------|
| Services | Unhealthy |
| HK attempt | Blocked |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES (may fix services) | - |
| `do housekeeping` | BLOCKED (services must be healthy) | - |
| New work | Depends on SR state | - |
| Exit | Depends on SR state | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| HK artifact | result.services_protected: false |

| Exit Verdict | Condition |
|--------------|-----------|
| Depends on SR | HK blocked but exit depends on SR |

---

### S19: SERVICES_UNHEALTHY_POST_HK

**Description:** Services became unhealthy after housekeeping.

| Property | Value |
|----------|-------|
| Services | Unhealthy (post-cleanup) |
| HK status | Completed with warning |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES | - |
| `do housekeeping` | YES (re-run with caution) | - |
| New work | BLOCKED | - |
| Exit | BLOCKED | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| HK artifact | services_post_check shows unhealthy |
| Alert | Service degradation alert |

| Exit Verdict | Condition |
|--------------|-----------|
| EXIT_BLOCKED | Service health issue |

---

### S20: TIER2_PENDING_APPROVAL

**Description:** Tier-2 housekeeping actions identified, awaiting token.

| Property | Value |
|----------|-------|
| HK scan | Completed |
| Tier-2 actions | Identified |
| Approval token | Not provided |

| Command | Allowed | Blocked |
|---------|---------|---------|
| `session reconcile` | YES | - |
| `do housekeeping` | YES (Tier-1 only without token) | - |
| `do housekeeping --tier2-token <token>` | YES (executes Tier-2) | - |
| New work | Depends on SR state | - |
| Exit | Depends on SR and HK state | - |

| Expected Artifacts | Description |
|-------------------|-------------|
| HK artifact | tier_2_actions.requested populated |

| Exit Verdict | Condition |
|--------------|-----------|
| Depends on SR/HK | Tier-2 approval optional for exit |

---

## State Transition Matrix

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    STATE TRANSITIONS                         │
                    └─────────────────────────────────────────────────────────────┘

  S01 (FRESH)
    │
    ├── session reconcile ──► S02 (SCRIPTS_COMPLETED) or S03 (SCRIPTS_FAILED)
    │
    └── do housekeeping ──► S01 (FRESH) with fresh HK artifact

  S02 (SCRIPTS_COMPLETED)
    │
    └── session reconcile ──► S04 (CONTAINER_BUILT) or S05 (CONTAINER_FAILED)

  S04 (CONTAINER_BUILT)
    │
    └── session reconcile ──► S06 (DEPLOYED) or S07 (DEPLOY_FAILED)

  S06 (DEPLOYED)
    │
    └── session reconcile ──► S08 (TESTS_PASSED) or S09 (TESTS_FAILED)

  S08 (TESTS_PASSED)
    │
    └── session reconcile ──► S10 (GIT_STAGED) ──► S11 (GIT_COMMITTED) ──► S13 (EXIT_READY)
                                                                            or S12 (PUSH_FAILED)

  S13 (RECONCILED_EXIT_READY)
    │
    ├── HK fresh ──► CLEAN_EXIT allowed
    │
    └── HK stale ──► S15 (HK_STALE) ──► do housekeeping ──► S13 (EXIT_READY)

  ANY_STATE + forced exit ──► S17 (FORCED_EXIT_ATTEMPT) ──► DIRTY_EXIT recorded
```

---

## Exit Decision Matrix

| SR Verdict | HK Freshness | Services | Exit Allowed | Exit Verdict |
|------------|--------------|----------|--------------|--------------|
| RECONCILED_EXIT_READY | Fresh (≤24h) | Healthy | YES | CLEAN_EXIT |
| RECONCILED_EXIT_READY | Stale (>24h) | Healthy | NO | EXIT_BLOCKED |
| RECONCILED_EXIT_READY | Missing | Healthy | NO | EXIT_BLOCKED |
| RECONCILED_EXIT_READY | Fresh | Unhealthy | NO | EXIT_BLOCKED |
| FAILED_TESTS | Any | Any | NO | EXIT_BLOCKED |
| RECONCILIATION_BLOCKED | Any | Any | NO | EXIT_BLOCKED |
| Missing | Any | Any | NO | EXIT_BLOCKED |
| Any | Any | Any (forced) | RECORDED | DIRTY_EXIT |

---

## Command Permission Matrix (Summary)

| State | `session reconcile` | `do housekeeping` | New Work | Exit |
|-------|---------------------|-------------------|----------|------|
| S01 FRESH | YES | YES | BLOCKED* | BLOCKED |
| S02 SCRIPTS_COMPLETED | YES | YES | BLOCKED | BLOCKED |
| S03 SCRIPTS_FAILED | YES | YES | BLOCKED | BLOCKED |
| S04 CONTAINER_BUILT | YES | YES | BLOCKED | BLOCKED |
| S05 CONTAINER_FAILED | YES | YES | BLOCKED | BLOCKED |
| S06 DEPLOYED | YES | YES | BLOCKED | BLOCKED |
| S07 DEPLOY_FAILED | YES | YES | BLOCKED | BLOCKED |
| S08 TESTS_PASSED | YES | YES | BLOCKED | BLOCKED |
| S09 TESTS_FAILED | YES | YES | BLOCKED | BLOCKED |
| S10 GIT_STAGED | YES | YES | BLOCKED | BLOCKED |
| S11 GIT_COMMITTED | YES | YES | BLOCKED | BLOCKED |
| S12 GIT_PUSH_FAILED | YES | YES | BLOCKED | BLOCKED |
| S13 RECONCILED_EXIT_READY | YES | YES | **YES** | **ALLOWED*** |
| S14 RECONCILE_INTERRUPTED | YES | YES | BLOCKED | BLOCKED |
| S15 HK_STALE | YES | YES | Depends | BLOCKED |
| S16 HK_MISSING | YES | YES | Depends | BLOCKED |

*BLOCKED if previous SR != RECONCILED_EXIT_READY
*ALLOWED only if HK fresh

---

## Artifact Requirements Matrix

| State | SR Artifact | HK Artifact | EXIT Artifact | Session Pin |
|-------|-------------|-------------|---------------|-------------|
| S01 | Optional (previous) | Optional | No | No |
| S02 | In progress | Optional | No | No |
| S03 | RECONCILIATION_BLOCKED | Optional | No | No |
| S04 | In progress | Optional | No | No |
| S05 | RECONCILIATION_BLOCKED | Optional | No | No |
| S06 | In progress | Optional | No | No |
| S07 | RECONCILIATION_BLOCKED | Optional | No | No |
| S08 | In progress | Optional | No | No |
| S09 | FAILED_TESTS | Optional | No | No |
| S10 | In progress | Optional | No | No |
| S11 | In progress | Optional | No | No |
| S12 | RECONCILIATION_BLOCKED | Optional | No | No |
| S13 | RECONCILED_EXIT_READY | Required (fresh) | On exit | Yes |
| S14 | Partial/missing | Optional | No | No |
| S15 | Any | Stale | No | No |
| S16 | Any | Missing | No | No |
| S17 | Any | Any | DIRTY_EXIT | Optional |

---

## Validation Rules

### V01: Pipeline Order Invariant
```
scripts → container → deploy → tests → git_commit → git_push
```
No step may be skipped. Order is absolute.

### V02: Block New Work Invariant
```
IF latest_sr_verdict != RECONCILED_EXIT_READY
THEN new_work = BLOCKED
```

### V03: Exit Gate Invariant
```
IF sr_verdict == RECONCILED_EXIT_READY
   AND hk_age <= 24h
   AND services_healthy
THEN exit = CLEAN_EXIT
ELSE exit = EXIT_BLOCKED
```

### V04: Domain Separation Invariant
```
SR-01 NEVER executes HK-01 actions
HK-01 NEVER executes SR-01 actions
```

### V05: Session State Protection Invariant
```
ONLY session_reconcile.py MAY write .session_state.yaml
```

---

## Test Scenario Checklist

For each state S01-S20, the following must be verified:

- [ ] State can be entered via defined transitions
- [ ] Allowed commands execute correctly
- [ ] Blocked commands are rejected with proper error
- [ ] Expected artifacts are created
- [ ] Exit verdict is correct
- [ ] No undefined behavior exists

---

## References

- CLAUDE_AUTHORITY.md - Section 11 (Authority Model)
- SESSION_RECONCILE_PROTOCOL.md - SR-01 specification
- HOUSEKEEPING_PROTOCOL.md - HK-01 specification
- scripts/ops/session_exit.py - Exit gate implementation
- scripts/ops/session_reconcile.py - Reconciliation implementation
- scripts/ops/housekeeping_scan.py - Housekeeping implementation
