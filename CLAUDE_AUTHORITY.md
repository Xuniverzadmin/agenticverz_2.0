# CLAUDE_AUTHORITY.md
## Absolute Authority & Execution Order

This document is the **highest non-human authority** governing Claude's behavior
in this repository. It overrides all other documents except **explicit instructions
from the human system owner in the current session**.

---

## 1. Order of Precedence (Non-Negotiable)

If any conflict exists, resolve strictly in this order:

1. Explicit human instruction in the **current chat**
2. **CLAUDE_AUTHORITY.md** (this file)
3. SESSION_PLAYBOOK.yaml
4. Memory PINs
5. CI rules and scripts
6. Tests
7. Existing code

**If ambiguity remains → STOP and ask the human.
Never resolve conflicts silently.**

---

## 2. Mandatory Pre-Flight (Before Writing or Modifying Code)

Before implementing *any* task, Claude **must first output**:

- Applicable FeatureIntent(s)
- Applicable TransactionIntent(s)
- Relevant invariants (by document name)
- Expected blast radius (L2/L3/L4/L5/L6)
- Expected artifacts to be created or modified

If this pre-flight step is skipped, the task is **invalid**.

---

## 3. Classification Before Fixing (Hard Rule)

No failure may be fixed unless it is **explicitly classified first**:

- **Bucket A** — Test is wrong
- **Bucket B** — Infrastructure missing
- **Bucket C** — System bug

Classification must be encoded via:
- pytest marker
- inline comment
- or invariant documentation

**Fixing without classification is prohibited.**

---

## 3.5. Infrastructure State Declaration (Hard Rule)

All infrastructure dependencies **must be declared** in `docs/infra/INFRA_REGISTRY.md`.

### Tri-State Model

| State | Name | Meaning | Test Behavior |
|-------|------|---------|---------------|
| **A** | Chosen (Conceptual) | Selected but not wired locally | MUST skip (Bucket B) |
| **B** | Local Substitute | Stub/emulator available | MUST run |
| **C** | Fully Wired | Required and available | Failures block CI |

### Bucket B Sub-Classification

- **B1** — Production-required, locally missing (must be fixed)
- **B2** — Optional/future (intentionally deferred)

### Rules

1. Tests **must declare** infra dependency via `@requires_infra("name")`
2. State A infra **must not cause test failures** (only skips)
3. State C infra **must not be skipped** (failures are real)
4. State transitions **require human approval**

If infrastructure state is unclear → **STOP and ask**.

---

## 4. Intent Is Not Optional

All non-trivial modules **must declare FeatureIntent**.

Hierarchy (must hold):

FeatureIntent (module)
→ TransactionIntent (function)
→ Primitive (implementation)

If intent is missing:
- Claude must STOP and request clarification
- Claude must NOT infer intent silently

---

## 5. Invariants Are Sacred

Any test marked `@pytest.mark.invariant`:
- Must never be weakened
- Must never be skipped without explicit human approval
- Must have documentation in `docs/invariants/`

If an invariant fails, Claude must ask:

> "Is the invariant wrong, or is the system wrong?"

---

## 6. Guidance Over Punishment Principle

The system must:
- Prefer **guidance before enforcement**
- Prefer **construction-time correctness**
- Prefer **clear affordances over CI failure**

If a rule only triggers *after* a mistake, Claude must propose
a **guidance upgrade** (template, boilerplate, example, or guardrail).

---

## 7. Artifact Accountability (Required Output Schema)

Any claim of completion **must end with**:

Artifacts Created:
- …

Artifacts Modified:
- …

Artifacts Deleted:
- …

Governance Updated:
- …

If none, state explicitly: **None**

---

## 8. Change Freezing & Ratification

When intent tables, invariants, or priority tiers are frozen:
- Claude may not alter them
- Claude may only propose changes
- Human ratification is required

---

## 9. Evolution Rule

Every incident, failure cluster, or production bug must result in **at least one**:
- New primitive
- New intent
- New invariant
- New CI guard
- New documentation

No learning may remain implicit.

---

## 10. Final Governing Principle

> **Claude may operate across roles (architecture, governance, implementation),
> but clarity, declared intent, and authority order always outrank cleverness.**

The correct path must be the easiest path.
Block only when guidance fails.

---

## 11. Claude Authority Model — Session & System Operations

### 11.1 Separation of Domains (HARD RULE)

Claude operates under **two mutually exclusive operational domains**:

| Domain | Protocol | Trigger | Scope |
|--------|----------|---------|-------|
| Work State | SESSION_RECONCILE (SR-01) | `session reconcile` | Build → Deploy → Test → Git |
| System Health | HOUSEKEEPING (HK-01) | `do housekeeping` | VPS resources only |

Claude **must never cross domains** in a single invocation.

**Reference:**
- `docs/ops/SESSION_RECONCILE_PROTOCOL.md`
- `docs/ops/HOUSEKEEPING_PROTOCOL.md`

---

### 11.2 Authority Boundaries

#### Claude MAY:

- Read state files
- Invoke approved scripts
- Verify execution results
- Produce audit artifacts
- Block exit when invariants fail

#### Claude MAY NOT:

- Perform undocumented actions
- Make discretionary cleanup decisions
- Override failures
- Mutate system state outside declared protocol
- Assume intent from conversation context

---

### 11.3 Exit Governance

A session is **exitable** only if:

```
SESSION_RECONCILE verdict == RECONCILED_EXIT_READY
```

Housekeeping **does not affect exit eligibility**.

Forced exit without reconciliation **MUST be recorded as DIRTY_EXIT**.

---

### 11.4 Failure Handling Doctrine

| Condition | Claude Action |
|-----------|---------------|
| Missing state file | BLOCK |
| Failed tests | STOP + REPORT |
| Partial pipeline | RECONCILE |
| System pressure | HOUSEKEEPING |
| Ambiguous intent | REFUSE |

Claude must prefer **blocking** over guessing.

---

### 11.5 Memory Discipline

Claude may only write **session pins** and **protocol artifacts**.
Claude must **re-read latest pin at session start** before reasoning.

**Artifact locations:**
- `artifacts/session_reconcile/SR-<session_id>.yaml`
- `artifacts/housekeeping/HK-<timestamp>.yaml`
- `memory/session_pins/<session_id>.yaml`

---

### 11.6 Protocol Verdicts

#### SESSION_RECONCILE (SR-01)

| Verdict | Meaning |
|---------|---------|
| `RECONCILED_EXIT_READY` | All steps passed, git pushed, safe to exit |
| `RECONCILIATION_BLOCKED` | Missing state or precondition failed |
| `FAILED_TESTS` | Tests failed, cannot proceed to git |

#### HOUSEKEEPING (HK-01)

| Result | Meaning |
|--------|---------|
| `services_protected: true` | All critical services verified healthy |
| `no_active_work_disrupted: true` | No work state was affected |

---

### 11.7 Domain Violation Response

If Claude detects a domain violation:

```
DOMAIN VIOLATION DETECTED

Attempted: [action]
Current Protocol: [SR-01 | HK-01]
Violation: [action] belongs to [other protocol]

STATUS: BLOCKED
REQUIRED: Switch to correct protocol or request approval
```

---

### 11.8 Block New Work Invariant (HARD RULE)

**Effective:** 2026-01-12
**Status:** MANDATORY

If the latest SESSION_RECONCILE verdict is NOT `RECONCILED_EXIT_READY`:

```
→ All new work commands are BLOCKED
→ Only permitted command: session reconcile
```

#### Enforcement at Session Start

Claude **MUST** at the start of every session:

1. Read the latest SR artifact from `artifacts/session_reconcile/`
2. Check verdict field
3. If verdict != `RECONCILED_EXIT_READY`:
   - Refuse all unrelated tasks
   - Output blocking notice
   - Only accept `session reconcile` command

#### Blocking Notice Format

```
SESSION STATE: BLOCKED

Latest reconciliation verdict: [verdict]
Session ID: [session_id]

The previous session did not complete cleanly.
All new work is BLOCKED until reconciliation succeeds.

ONLY PERMITTED COMMAND: session reconcile

To proceed with new work, you must first:
1. Run: python scripts/ops/session_reconcile.py
2. Verify verdict: RECONCILED_EXIT_READY
```

#### Forbidden Actions When Blocked

| Action | Status |
|--------|--------|
| New builds | BLOCKED |
| New tests | BLOCKED |
| Code modifications | BLOCKED |
| Agent work | BLOCKED |
| E2E scenarios | BLOCKED |
| SDSR pipelines | BLOCKED |
| Feature implementation | BLOCKED |

#### Only Permitted When Blocked

| Action | Status |
|--------|--------|
| `session reconcile` | ALLOWED |
| Read artifact status | ALLOWED |
| Query session state | ALLOWED |

---

### 11.9 Exit Gate Integration

The `session_exit.py` script is the **single authoritative exit arbiter**.

#### Exit Requirements

A session may only exit cleanly if **ALL** conditions are met:

| Check | Requirement |
|-------|-------------|
| SR Verdict | `RECONCILED_EXIT_READY` |
| Session State | Consistent with SR artifact |
| HK Freshness | Latest HK artifact age ≤ 24h |

#### Exit Artifact

Every exit attempt produces:

```
artifacts/session_exit/EXIT-<session_id>.yaml
```

#### Exit Commands

```bash
# Check exit eligibility
python scripts/ops/session_exit.py

# With custom HK freshness threshold
python scripts/ops/session_exit.py --hk-max-age 48
```

#### Exit Codes

| Code | Verdict | Meaning |
|------|---------|---------|
| 0 | CLEAN_EXIT | Session may terminate |
| 1 | EXIT_BLOCKED | Must resolve blockers first |
