# SDSR E2E TESTING PROTOCOL (WITH GUARDRAILS)

**Version:** 1.0.0
**Effective:** 2026-01-10
**Status:** MANDATORY
**Scope:** All SDSR (Scenario-Driven System Realization) testing

---

## Purpose (Non-Negotiable)

Validate **real system behavior** across domains:

**Activity → Incident → Policy Proposal → Logs**

UI is **observational only**.
Backend execution is the source of truth.

---

## SECTION 1 — HARD GUARDRAILS FOR CLAUDE (MANDATORY)

Claude **MUST STOP** if any rule below would be violated.

---

### GR-1: No Direct DB Mutation Outside Alembic

**Forbidden**

* `ALTER TABLE`, `DROP`, `DELETE`, `UPDATE` via raw SQL
* Editing `alembic_version`
* Applying partial migrations manually

**Allowed**

* Propose migration files
* Verify migration state (`alembic current`, `heads`)
* Abort execution if schema mismatch is detected

**Enforcement**

> If schema mismatch exists → STOP and REPORT.
> No "temporary SQL fixes" allowed.

---

### GR-2: No Trigger / Constraint Changes Without Approval

**Triggers = architectural invariants**

Claude may:

* Inspect triggers
* Report conflicts

Claude may NOT:

* Modify triggers
* Add exception paths (even for SDSR)

**If cleanup is blocked**
→ propose **dedicated cleanup mechanism**, not trigger edits.

---

### GR-3: Canonical Tables Only

Claude must NOT:

* Create new domain tables
* Create `*sdsr*` prefixed copies

Claude must:

* Extend canonical tables only
* Reuse existing engines

If fragmentation is needed:
→ **present options + ask for decision**

---

### GR-4: No Silent Compatibility Fallbacks

Patterns like:

```python
getattr(obj, "field", None)
```

Are allowed **only if**:

* Logged explicitly
* Marked TEMPORARY
* Followed by a required migration

Otherwise → STOP.

---

### GR-5: No "Fix While Investigating"

Claude must follow:

1. Diagnose
2. Summarize root cause
3. Propose fix
4. Wait for approval
5. Implement
6. Verify

Never skip steps 3–4.

---

### GR-6: UI Never Drives State

UI:

* Reads
* Displays
* Triggers APIs

UI must NEVER:

* Create domain entities directly
* Simulate backend success

If backend doesn't emit data → UI stays empty.

---

## SECTION 2 — SCHEMA REALITY GATE (MANDATORY PRECHECK)

Before **any** E2E run, Claude must perform and log:

### SR-1: Migration Consistency Check

**Canonical Implementation:** `backend/scripts/preflight/sr1_migration_check.py`

**GOVERNANCE RULE (NON-NEGOTIABLE):**

> Alembic migration state MUST be verified via Alembic runtime APIs.
> Parsing CLI output with grep/regex is **FORBIDDEN**.

SR-1 PASSES if and only if:

* Database is reachable
* `alembic_version` table exists
* Exactly **one head** exists
* Current DB revision == that head

**Verification Command:**

```bash
python3 backend/scripts/preflight/sr1_migration_check.py
```

Exit code 0 = PASS, Exit code 1 = FAIL (with explicit reason).

**Forbidden Patterns:**

```bash
# NEVER DO THIS
alembic current | grep ...
alembic heads | awk ...
```

These are fragile and will break with descriptive revision names.

---

### SR-2: Required Columns Assertion

Claude must verify presence of:

**runs**

* is_synthetic
* synthetic_scenario_id

**incidents**

* source_run_id
* is_synthetic
* synthetic_scenario_id

**policy_proposals**

* status
* triggering_feedback_ids

**aos_traces**

* run_id
* incident_id
* is_synthetic
* synthetic_scenario_id
* status

**aos_trace_steps**

* trace_id
* level
* source

If any missing → STOP.

---

### SR-3: Worker Version Check (Capability-Based)

**GOVERNANCE RULE (NON-NEGOTIABLE):**

> Capability presence must be validated **semantically**, not by brittle paths.
> Path-specific checks are **PROHIBITED** unless the path is itself contractual.

SR-3 verifies that the **running worker container** contains TraceStore integration.

**Verification Command:**

```bash
docker compose exec -T worker \
  sh -c 'grep -R "PostgresTraceStore" /app/app/worker >/dev/null'
```

Exit code 0 = PASS, non-zero = FAIL.

**What This Checks:**

* TraceStore import exists somewhere in worker code
* TraceStore instantiation is present
* Capability is present regardless of file location

**Forbidden Patterns:**

```bash
# NEVER DO THIS - path-specific checks break on refactors
grep "TraceStore" /app/app/worker/runtime/runner.py
grep "TraceStore" /app/app/worker/specific_file.py
```

If not present → rebuild container **before** testing:

```bash
docker compose up -d --build worker
```

---

## SECTION 3 — E2E SCENARIO CONTRACT (NO CODE)

### Scenario ID

```
SDSR-E2E-001
```

### Intent

> A failed activity run produces:
>
> * an incident
> * a draft policy proposal
> * execution traces and steps
>   all correlated and visible in UI

---

### Scenario Inputs (YAML-level)

```yaml
scenario_id: SDSR-E2E-001
tenant:
  id: sdsr-tenant-e2e
agent:
  id: sdsr-agent-e2e

run:
  id: run-sdsr-e2e-001
  goal: "Trigger deterministic failure"
  force_terminal_failure: true
  max_attempts: 1
```

**Important**

* No fake skills
* No retry loops
* Failure must be **terminal on first execution**

---

## SECTION 4 — EXECUTION FLOW (CANONICAL)

### Step 1 — Inject Preconditions

* tenant
* api_key
* agent
* run (status = queued)

Done via `inject_synthetic.py`
Script must NOT touch downstream tables

---

### Step 2 — Worker Executes Run

Expected:

* TraceStore.start_trace()
* aos_traces row created
* aos_trace_steps written

---

### Step 3 — Run Fails Terminally

Expected:

* run.status = failed
* TraceStore.complete_trace("failed")

---

### Step 4 — Incident Engine Fires

Condition:

* run.status == failed

Expected:

* incidents row created
* incidents.source_run_id = run.id
* aos_traces.incident_id populated

---

### Step 5 — Policy Proposal Engine Fires

Condition:

* incident.severity ∈ {HIGH, CRITICAL}

Expected:

* policy_proposals row
* status = draft
* triggering_feedback_ids includes incident_id

---

## SECTION 5 — VERIFICATION CHECKLIST (MANDATORY)

Claude must output **this exact checklist** with PASS/FAIL:

### Backend Assertions

| Check                   | Expected |
| ----------------------- | -------- |
| Run exists              | PASS     |
| Run failed              | PASS     |
| Trace exists            | PASS     |
| Trace status = failed   | PASS     |
| Trace linked to run     | PASS     |
| Incident exists         | PASS     |
| Incident linked to run  | PASS     |
| Proposal exists         | PASS     |
| Proposal status = draft | PASS     |

---

### UI Observations (Read-Only)

Claude must **not claim UX correctness**, only data presence.

| Domain    | Panel        | Expected               |
| --------- | ------------ | ---------------------- |
| Activity  | Runs list    | SDSR badge visible     |
| Incidents | Open list    | Incident visible       |
| Policies  | Proposals    | Draft proposal visible |
| Logs      | Trace detail | ERROR step visible     |

---

## SECTION 6 — CLEANUP PROTOCOL (SAFE)

Claude may cleanup ONLY IF:

* is_synthetic = true
* synthetic_scenario_id matches

### S6 Immutability Contract (MANDATORY)

**Trace tables are protected by S6 immutability triggers.**

| Table | Cleanup Method | Reason |
|-------|----------------|--------|
| aos_traces | **ARCHIVE** (UPDATE archived_at) | S6 prohibits DELETE |
| aos_trace_steps | **ARCHIVE** (UPDATE archived_at) | S6 prohibits DELETE |
| All other tables | DELETE | Standard cleanup |

**Governance Rule:**

> S6 Immutability prohibits DELETE, not archival state transitions.
> SDSR cleanup archives synthetic trace data; physical deletion is forbidden.

**Archived Data:**
- Remains in database (provenance preserved)
- Excluded from active views via `WHERE archived_at IS NULL`
- May be queried for audit purposes

### Cleanup Order (Topological)

1. policy_proposals (DELETE)
2. prevention_records (DELETE)
3. incidents (DELETE)
4. aos_trace_steps (**ARCHIVE**)
5. aos_traces (**ARCHIVE**)
6. runs (DELETE)
7. worker_runs (DELETE)
8. agents (DELETE)
9. api_keys (DELETE)
10. tenants (DELETE)

If blocked → REPORT, do NOT bypass.

### SDSR Identity Rule (MANDATORY)

**Canonical Rule:**

> SDSR re-execution must never reuse identifiers that participate in uniqueness constraints.
> `run_id` is execution identity and must be unique per execution.

**Implementation:**

| Identifier | Scope | Format |
|------------|-------|--------|
| scenario_id | Stable across executions | `SDSR-E2E-001` |
| run_id | Unique per execution | `run-{scenario_id}-{UTC_YYYYMMDDTHHMMSSZ}` |
| trace_id | Derived from run_id | `trace-{run_id}` |

**Example:**
```
run-sdsr-e2e-001-20260110T084845Z
```

**Rationale:**

S6 immutability uses `ON CONFLICT DO NOTHING` for trace inserts. If an archived trace
exists with the same trace_id, new trace creation is silently skipped. Unique run_id
per execution ensures each trace tree is fresh while preserving S6 immutability.

---

## SECTION 7 — SUCCESS CRITERIA (FREEZE POINT)

The E2E loop is considered **DONE** only when:

* Backend artifacts exist without manual DB edits
* Worker produces traces automatically
* UI reflects data without simulation
* No guardrail was violated

Only then:

> Move to next domain or next scenario.

---

## Hard Failure Response

If Claude is about to violate any guardrail:

```
SDSR GUARDRAIL VIOLATION

Guardrail: GR-{N}
Action attempted: {description}
Reason blocked: {explanation}

STATUS: BLOCKED
REQUIRED ACTION: {what is needed to proceed safely}
```

---

## Related Documents

* `CLAUDE.md` — Session bootstrap and behavior enforcement
* `docs/governance/SDSR.md` — SDSR architecture overview
* `backend/scripts/preflight/sdsr_e2e_preflight.sh` — Automated pre-checks

---

*This protocol is machine-enforced. Non-compliant executions are invalid.*
