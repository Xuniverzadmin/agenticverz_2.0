# SESSION_RECONCILE Protocol (SR-01)

**Version:** 1.0
**Status:** ACTIVE
**Trigger:** `session reconcile`

---

## Purpose

Reconcile the **work pipeline state** into a **single, exit-ready terminal state** by invoking *approved automation scripts* and validating outcomes.

Claude's job is to **drive convergence**, not cleanup.

---

## Domain

| Domain | Protocol | Scope |
|--------|----------|-------|
| **Work State** | SESSION_RECONCILE (SR-01) | Build → Deploy → Test → Git |

This protocol is **mutually exclusive** with HOUSEKEEPING (HK-01).
Claude **must never cross domains** in a single invocation.

---

## Pipeline Order (STRICT)

```
scripts → container → deploy → tests → git
```

This order is **non-negotiable**. No step may be skipped or reordered.

---

## Claude Responsibilities (MANDATORY)

### 1. Load and Validate State

Claude **MUST** read and validate:

- [ ] `.session_state.yaml` (REQUIRED - block if missing)
- [ ] Previous session pin from `memory/session_pins/` (if exists)

### 2. Derive Reconciliation Plan

- [ ] Identify missing pipeline steps
- [ ] Verify current state of each step
- [ ] Enforce strict order (no skipping, no reordering)

### 3. Invoke Only Approved Scripts

| Step | Approved Action | Script/Command |
|------|-----------------|----------------|
| scripts | Run build scripts | `./scripts/build.sh` or equivalent |
| container | Build containers | `docker compose build` |
| deploy | Deploy services | `docker compose up -d` |
| tests | Run test suite | `pytest tests/ -v` |
| git commit | Commit changes | `git add -A && git commit` |
| git push | Push to remote | `git push origin main` |

### 4. Verify Post-Execution State

After each step, Claude **MUST**:

- [ ] Verify step completed successfully
- [ ] Check exit code
- [ ] Validate expected state change
- [ ] Stop if step failed

### 5. Emit Artifacts

Claude **MUST** create:

```
artifacts/session_reconcile/SR-<session_id>.yaml
memory/session_pins/<session_id>.yaml
```

### 6. Declare Verdict

One of the following **MUST** be declared:

| Verdict | Meaning |
|---------|---------|
| `RECONCILED_EXIT_READY` | All steps passed, git pushed, safe to exit |
| `RECONCILIATION_BLOCKED` | Missing state or precondition failed |
| `FAILED_TESTS` | Tests failed, cannot proceed to git |

---

## Claude Is Explicitly FORBIDDEN To

| Action | Reason |
|--------|--------|
| Skip pipeline steps | Breaks invariants |
| Reverse pipeline order | Causes inconsistent state |
| Kill processes or services | Domain violation (belongs to HK-01) |
| Free memory or disk | Domain violation (belongs to HK-01) |
| Prune Docker globally | Domain violation (belongs to HK-01) |
| Override failed tests | Tests are truth gate |
| Proceed without `.session_state.yaml` | State is required for reconciliation |

If a required state is missing → **BLOCK reconciliation**.

---

## Success Condition

```yaml
exit_ready: true
git: pushed
tests: passed
```

**Nothing else qualifies.**

---

## Artifact Schema

### SR-<session_id>.yaml

```yaml
schema_version: "1.0"
protocol: "SR-01"
session_id: "<uuid>"
timestamp: "<ISO-8601>"
triggered_by: "user"

pipeline:
  scripts:
    status: "completed|skipped|failed"
    output: "<summary>"
  container:
    status: "completed|skipped|failed"
    images_built: []
  deploy:
    status: "completed|skipped|failed"
    services_started: []
  tests:
    status: "passed|failed"
    passed: <int>
    failed: <int>
    skipped: <int>
  git_commit:
    status: "completed|skipped|failed"
    commit_hash: "<hash>"
    files_changed: <int>
  git_push:
    status: "completed|skipped|failed"
    remote: "origin/main"

verdict: "RECONCILED_EXIT_READY|RECONCILIATION_BLOCKED|FAILED_TESTS"
exit_ready: true|false
blocking_reason: "<reason if blocked>"
```

---

## Session Pin Schema

### memory/session_pins/<session_id>.yaml

```yaml
session_id: "<uuid>"
started_at: "<ISO-8601>"
ended_at: "<ISO-8601>"
verdict: "<verdict>"
exit_ready: true|false

work_summary:
  commits: []
  files_changed: <int>
  tests_passed: <int>
  pins_created: []

next_session_context:
  pending_work: []
  blockers: []
  notes: "<free text>"
```

---

## Failure Handling

| Condition | Claude Action |
|-----------|---------------|
| Missing `.session_state.yaml` | BLOCK - emit `RECONCILIATION_BLOCKED` |
| Failed tests | STOP - emit `FAILED_TESTS` |
| Git push failed | RETRY once, then STOP |
| Container build failed | STOP - report error |
| Ambiguous state | REFUSE - ask for clarification |

Claude must prefer **blocking** over guessing.

---

## Integration with Exit Governance

A session is **exitable** only if:

```
SESSION_RECONCILE verdict == RECONCILED_EXIT_READY
```

Forced exit without reconciliation **MUST be recorded as DIRTY_EXIT**.

---

## Artifact Freshness Rules (TODO-05)

**Status:** MANDATORY
**Effective:** 2026-01-12

### SR Artifact Freshness

| Rule | Requirement |
|------|-------------|
| SR-FRESH-001 | SR artifacts must be the latest for a given session |
| SR-FRESH-002 | Stale SR artifacts must not be used for exit decisions |
| SR-FRESH-003 | If SR artifact is missing, exit is BLOCKED |

### Freshness Definition

An SR artifact is considered **fresh** if:

1. It was created during the current session (matching session_id)
2. Its verdict reflects the actual pipeline state
3. It has not been superseded by a newer SR artifact

### Stale Artifact Handling

If a stale SR artifact is detected:

```
SR ARTIFACT STALE WARNING

SR artifact: <path>
Age: <age>
Current session: <session_id>

STATUS: BLOCKED
ACTION REQUIRED: Run 'session reconcile' to create fresh artifact
```

**Never silently accept stale artifacts.**

---

## Non-Goals (Protocol Lock) (TODO-06)

**Status:** LOCKED
**Effective:** 2026-01-12

This section documents what SESSION_RECONCILE (SR-01) **will NEVER do**.
These are architectural constraints, not temporary limitations.

### Never-Goals

| Non-Goal | Rationale |
|----------|-----------|
| Auto-schedule reconciliation | Reconciliation is human-triggered only |
| Bypass test failures | Tests are truth gates, not suggestions |
| Skip pipeline steps | Pipeline order is non-negotiable |
| Cross into HK-01 domain | Domain separation is absolute |
| Modify session state from other scripts | Only session_reconcile.py may write |
| Proceed without explicit state | Missing state = BLOCK, not inference |
| Auto-fix broken state | Fixing requires human judgment |
| Silent retries | All retries must be visible and auditable |
| Infer intent from context | Intent must be declared explicitly |

### Why These Are Locked

1. **Human-Triggered Only**: Automation of session reconciliation would remove human oversight at critical junctures.

2. **Test Failure Bypass**: Tests represent system truth. Bypassing them corrupts the trust model.

3. **Pipeline Order**: The strict order ensures dependencies are satisfied. Reordering breaks invariants.

4. **Domain Separation**: Mixing work state and system health creates ambiguous authority.

5. **Session State Protection**: Single-writer pattern prevents race conditions and corruption.

### Evolution Disclaimer

These non-goals may only be changed via:

1. Explicit human approval in session
2. Amendment to this document
3. Update to CLAUDE_AUTHORITY.md Section 11

**Undocumented evolution is forbidden.**

---

## References

- CLAUDE_AUTHORITY.md - Authority model
- HOUSEKEEPING_PROTOCOL.md - System health (separate domain)
- .session_state.yaml - Session state file
