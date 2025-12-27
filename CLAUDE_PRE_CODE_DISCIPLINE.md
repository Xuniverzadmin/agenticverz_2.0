# AgenticVerz — Pre-Code Discipline Task Set (Claude Execution Contract)

**Version:** 1.0.0
**Effective:** 2025-12-27
**Status:** MANDATORY

---

## Non-Negotiable Rule

Claude **must not write or modify any code** until **ALL tasks below are completed and reported**.
If any task cannot be completed, Claude must **STOP and report BLOCKED**.

---

## TASK 0 — Accept Contract (MANDATORY)

Claude must explicitly respond with:

> "I accept the AgenticVerz Pre-Code Discipline. I will not write code until all required tasks are completed."

If this line is missing → response is invalid.

---

## TASK 1 — System State Inventory (PLAN)

Claude must collect and report **current system truth**.

### Required Checks

Claude must execute and paste results of:

1. **Migration state**
   * `alembic current`
   * `alembic heads`

2. **Database schema sanity**
   * Tables relevant to the task exist
   * Columns required by the task exist

3. **Behavioral reality check**
   * Current retry / rerun behavior
   * Whether original executions are mutated or immutable

### Output Format (MANDATORY)

```
SYSTEM STATE INVENTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Alembic current: <output>
- Alembic heads: <output>
- Relevant tables exist: YES / NO
- Required columns exist: YES / NO
- Current behavior: <mutates / creates new / unknown>
- Known invariants enforced: <list>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If any item is unknown → **STOP**

---

## TASK 2 — Conflict & Risk Scan (VERIFY)

Claude must analyze **before writing code**.

### Required Questions (Claude must answer all)

| Question | Answer |
|----------|--------|
| Does this task touch existing schema? | YES / NO |
| Does it introduce a new migration? | YES / NO |
| Does it overlap with unfinished or recent migrations? | YES / NO |
| Could this mutate historical data? | YES / NO |
| Does this conflict with any memory pin? | YES / NO |
| Does this violate any lesson learned? | YES / NO |

### Output Format

```
CONFLICT & RISK SCAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Schema change required: YES / NO
- New migration required: YES / NO
- Migration parent revision: <revision id or NONE>
- Risk of history mutation: YES / NO
- Memory pin conflict: YES / NO → <PIN-XXX if yes>
- Lesson violation risk: YES / NO → <LESSON-XXX if yes>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If **risk of history mutation = YES** and no mitigation is stated → **STOP**
If **memory pin conflict = YES** → **STOP**
If **lesson violation = YES** → **STOP**

---

## TASK 3 — Migration Intent Declaration (If Applicable)

**Only required if TASK 2 indicates a new migration.**

Claude must declare:

```
MIGRATION INTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Parent revision: <revision id>
- Expected new revision: <new revision id>
- Expected head after change: <revision id>
- Merge migration required: YES / NO
- Tables affected: <list>
- Columns added: <list>
- Columns modified: <list> (DANGER)
- Columns removed: <list> (DANGER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If Claude cannot identify the parent revision → **STOP**

---

## TASK 4 — Execution Plan (PLAN → ACT BRIDGE)

Claude must describe **what will be done**, not how yet.

```
EXECUTION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. WILL CHANGE:
   - <item 1>
   - <item 2>

2. WILL NOT CHANGE (explicit exclusions):
   - <item 1>
   - <item 2>

3. INVARIANTS THAT MUST REMAIN TRUE:
   - <invariant 1>
   - <invariant 2>

4. ROLLBACK STRATEGY (if applicable):
   - <how to undo if this fails>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

No code allowed in this task.

---

## TASK 5 — Act (Code / Schema Changes)

Only after **TASKS 0–4 are completed and accepted**, Claude may:

* write code
* write migrations
* modify retry behavior

Any code written before this task → invalid response.

---

## TASK 6 — Post-Action Self-Audit (MANDATORY)

Claude must end with:

```
SELF-AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Did I verify system state before coding?     YES / NO
- Did I check alembic current/heads?           YES / NO
- Did I read relevant memory pins?             YES / NO
- Did I check lessons learned?                 YES / NO
- Did I introduce new persistence?             YES / NO
- Did I risk historical mutation?              YES / NO
- If YES to any risk → mitigation: <explain>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If this section is missing → response is incomplete.

---

## Enforcement Rules

If Claude:

* skips a task → REJECT
* writes code early → REJECT
* answers vaguely → REJECT
* assumes state without evidence → REJECT
* missing SELF-AUDIT → REJECT

---

## Task Summary Matrix

| Task | Phase | Purpose | Required Output |
|------|-------|---------|-----------------|
| 0 | Accept | Acknowledge contract | Explicit statement |
| 1 | PLAN | Gather system state | SYSTEM STATE INVENTORY |
| 2 | VERIFY | Risk assessment | CONFLICT & RISK SCAN |
| 3 | PLAN | Migration intent | MIGRATION INTENT |
| 4 | PLAN | Describe changes | EXECUTION PLAN |
| 5 | ACT | Write code | Actual changes |
| 6 | VERIFY | Self-check | SELF-AUDIT |

---

## Quick Start

When starting *any* backend task, say:

> **"Execute TASKS 0–6 for this change. Do not write code until allowed."**

---

## Related Documents

* `CLAUDE_BOOT_CONTRACT.md` — Session boot sequence
* `CLAUDE.md` — Project context and conventions
* `docs/LESSONS_ENFORCED.md` — Failure prevention rules
* `docs/memory-pins/INDEX.md` — Active memory pins

---

*This discipline contract is machine-enforced. Non-compliant responses will be rejected.*
