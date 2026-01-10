# GOVERNANCE INVARIANT — DB-AUTH-001

**Database Authority Determinism**

**Status:** FOUNDATIONAL
**Severity:** CRITICAL
**Override:** Governance-only
**Auto-expiry:** NEVER
**Effective:** 2026-01-10
**Depends-On:** (none — this is a root invariant)

---

## 1. Invariant Statement (Normative)

> **At any point in time, for any session, task, script, or reasoning chain, the authoritative database MUST be explicitly declared and MUST NOT be inferred.**

Authority is **declared**, **validated**, and **enforced** — never discovered.

Violation of this invariant constitutes a **governance breach**.

---

## 2. Scope

This invariant applies to:

- Human-initiated sessions
- Claude / LLM reasoning sessions
- CLI scripts
- Background jobs
- Test runners
- Migration tools
- Synthetic data injectors (inject_synthetic.py)
- Capability validators
- Governance auditors
- SDSR E2E scenarios

If it touches data, it is bound by DB-AUTH-001.

---

## 3. Definitions

### 3.1 Database Authority

The database whose state is considered **canonical truth** for:

- Historical correctness
- Capability registry
- Run validation
- Governance decisions

### 3.2 Declared Authority

Authority explicitly set via:

- Environment variable (`DB_AUTHORITY`)
- Governance contract file (`docs/runtime/DB_AUTHORITY.md`)
- Script precondition

### 3.3 Forbidden Inference

Any attempt to determine authority by:

- Inspecting connection strings
- Querying timestamps
- Observing data recency
- Comparing record presence
- Trial queries across databases
- "Checking which has data"

Inference is **explicitly disallowed**.

---

## 4. Authority Contract

### 4.1 Canonical Assignment

| Database | Authority Level | Role |
|----------|-----------------|------|
| Neon | **Authoritative** | Canonical truth |
| Local / Docker | **Non-authoritative** | Ephemeral, disposable |

This mapping is **static** unless changed by an explicit governance decision.

### 4.2 Connection Identification

| Authority | DATABASE_URL Pattern |
|-----------|---------------------|
| neon | Contains `neon.tech` |
| local | Contains `localhost`, `127.0.0.1`, or Docker service name |

---

## 5. Mandatory Preconditions (Hard Gates)

### 5.1 Environment Declaration (Required)

Every execution context MUST define:

```env
DB_AUTHORITY=neon
DB_ENV=prod-like
```

Or for local:

```env
DB_AUTHORITY=local
DB_ENV=dev
```

Absence = **hard failure**.

### 5.2 Session Authority Declaration (LLM-Specific)

Before **any** DB-related reasoning or action, Claude MUST internally establish:

```
DB AUTHORITY DECLARATION
- Declared Authority: <neon | local>
- Intended Operation: <read | write | validate | test>
- Justification: <single sentence>
```

If not established → **session invalid**.

### 5.3 Script Authority Assertion

All scripts MUST assert expected authority:

```python
import os
import sys

expected = os.getenv("EXPECTED_DB_AUTHORITY")
actual = os.getenv("DB_AUTHORITY")

if expected and expected != actual:
    sys.exit(f"[DB-GUARD] Authority mismatch. Expected={expected}, Actual={actual}")
```

No override. No retry. No fallback.

---

## 6. Permitted Operations Matrix

| Operation Type | Neon | Local |
|----------------|------|-------|
| Read canonical history | ✅ | ❌ |
| Validate runs | ✅ | ❌ |
| Capability registry | ✅ | ❌ |
| Governance checks | ✅ | ❌ |
| SDSR scenario execution | ✅ | ❌ |
| Trace/incident verification | ✅ | ❌ |
| Schema experiments | ❌ | ✅ |
| Migration dry-runs | ❌ | ✅ |
| Disposable tests | ❌ | ✅ |
| Unit tests | ❌ | ✅ |
| Synthetic data (explicit) | ⚠️ | ⚠️ |

⚠️ = Requires explicit authority override with justification.

---

## 7. Prohibited Behaviors (Explicit)

The following are **governance violations**:

1. Inferring authority from data age
2. Switching databases mid-session
3. "Checking both" to decide correctness
4. Retrying against a different DB
5. Discovering authority after execution
6. Silent fallback from Neon → Local or vice-versa
7. Querying Docker DB when task requires canonical truth
8. Assuming localhost because "it's running"

These actions MUST trigger immediate halt.

---

## 8. Conflict Resolution Rule

If multiple databases are reachable:

> **Reachability is irrelevant. Authority is absolute.**

Connectivity does not imply legitimacy.

---

## 9. Audit & Enforcement

### 9.1 Audit Signals

- Missing `DB_AUTHORITY` environment variable
- Mismatched `EXPECTED_DB_AUTHORITY`
- Dual DB access in same session
- Authority declaration after DB access
- Docker DB queries for canonical data

Any signal = **Invariant Breach**.

### 9.2 Breach Handling

On breach:

1. Stop execution immediately
2. Log breach with timestamp + context
3. Do not auto-repair
4. Require explicit governance acknowledgment

### 9.3 Hard Failure Response

```
DB-AUTH-001 VIOLATION: Database authority mismatch or inference detected.

Expected authority: <declared>
Attempted operation: <description>
Violation type: <inference | mismatch | undeclared>

STATUS: BLOCKED
REQUIRED ACTION: Declare authority explicitly before proceeding.
Reference: docs/governance/DB_AUTH_001_INVARIANT.md
```

---

## 10. Claude Session Protocol

### 10.1 Before ANY Database Operation

Claude must output (internally, not to user):

```
DB AUTHORITY CHECK
- DB_AUTHORITY from env: neon
- Target DB: neon
- Operation: <read | write | validate>
- Reason: <one line justification>
```

### 10.2 Decision Flow

```
1. Is DB_AUTHORITY declared? → NO → STOP
2. Is target DB = declared authority? → NO → STOP
3. Is operation permitted for this authority? → NO → STOP
4. Proceed with operation
```

### 10.3 Never Do This

```
❌ "Let me check which database has the data"
❌ "I see Neon has more recent records, so..."
❌ "The Docker DB is running, let me query it"
❌ "Let me try local first, then Neon"
```

### 10.4 Always Do This

```
✅ "DB_AUTHORITY=neon, querying Neon for canonical truth"
✅ "This is a migration test, using local DB as declared"
✅ "SDSR verification requires Neon (authoritative)"
```

---

## 11. Invariant Summary (Non-Negotiable)

- Authority is **declared, not inferred**
- Neon is **canonical**
- Local is **ephemeral**
- Guessing is forbidden
- Discovery is a violation
- Retrying is not intelligence — it is drift

---

## 12. Related Documents

- `docs/runtime/DB_AUTHORITY.md` - Authority contract
- `backend/scripts/_db_guard.py` - Enforcement script
- `docs/playbooks/SESSION_PLAYBOOK.yaml` - Session rules

---

## 13. Monotonicity Enforcement (LOCKED)

**Rule:** Drift count must NEVER increase.

The drift detector enforces this with **exit code 3** (hard fail) when:
- `--record` is used
- Current count > previous count

This is not a warning. This is a build failure.

**Rationale:**
Increasing drift means someone added a DB-touching script without understanding DB-AUTH-001. That is exactly what this invariant exists to prevent.

```
Exit code 3 = REGRESSION DETECTED
Action: Fix immediately, no exceptions
```

### 13.1 Baseline Declaration

> **Baseline 2026-01-10: 58 HIGH-severity scripts.**
> **Any increase constitutes a governance incident.**

This number is history, not just data. It marks the moment DB-AUTH-001 became enforceable.

---

## 14. Foundational Status

**DB-AUTH-001 is declared FOUNDATIONAL.**

This means:

| Property | Implication |
|----------|-------------|
| **Dependency root** | New invariants may depend on DB-AUTH-001 |
| **Non-weakening** | No future invariant may weaken or contradict it |
| **Assumed truth** | It is assumed in all governance decisions, not re-argued |
| **Override authority** | Only explicit governance exception can suspend it |

**Rationale:**

Database authority determinism is not a policy choice—it is a precondition for trust. Without it, no other invariant can be verified. SDSR, traces, incidents, policies—all depend on knowing which database is canonical.

Reopening this question is not architecture. It is regression.

---

## 15. Changelog

| Date | Change |
|------|--------|
| 2026-01-10 | Initial creation |
| 2026-01-10 | Added monotonicity enforcement (exit code 3) |
| 2026-01-10 | Declared FOUNDATIONAL; baseline frozen at 58 |
