# Why SDSR Execution Is Safe, Repeatable, and Auditable

**Version:** 1.0.0
**Status:** LOCKED
**Effective:** 2026-01-10
**Reference:** PIN-379, SDSR_E2E_TESTING_PROTOCOL.md

---

This system supports repeatable synthetic executions without compromising trace integrity or audit guarantees. This is intentional and enforced by design.

---

## Core Principles

### 1. Execution Identity Is Immutable

Each execution is uniquely identified by a `run_id`.

- **Scenario IDs may repeat**
- **Execution IDs must not**

This guarantees:
- No trace collisions
- No silent overwrites
- Clear lineage across runs

**Format:**
```
run-{scenario_id}-{UTC_YYYYMMDDTHHMMSSZ}
```

**Example:**
```
run-sdsr-e2e-001-20260110T075609Z
run-sdsr-e2e-001-20260110T075706Z
```

---

### 2. Traces Are Append-Only

Trace data (`aos_traces`, `aos_trace_steps`) is immutable.

- **No DELETE**
- **No UPDATE** (except archival metadata)
- **No conditional upserts**

This preserves:
- Forensic integrity
- Audit reliability
- Historical truth

**S6 Immutability Contract:**
```sql
-- This is FORBIDDEN
DELETE FROM aos_traces WHERE ...

-- This is ALLOWED (archival only)
UPDATE aos_traces SET archived_at = NOW() WHERE ...
```

---

### 3. Cleanup Is Logical, Not Physical

Synthetic cleanup behaves differently by domain:

| Domain | Cleanup Strategy |
|--------|------------------|
| Traces | **ARCHIVE** (`archived_at`) |
| All others | DELETE |

**Why:**
- Trace immutability (S6) must never be weakened
- Synthetic data must still be isolatable
- Provenance is preserved for audit

---

### 4. Re-Execution Never Reuses Identity

Re-running SDSR with the same scenario creates a **new execution**, not a replacement.

**Example after two runs:**
```
trace_run-sdsr-e2e-001-20260110T075609Z  →  ARCHIVED
trace_run-sdsr-e2e-001-20260110T075706Z  →  ACTIVE
```

Older executions are archived, not erased.

---

## What This Prevents (Real Failures We Avoided)

| Failure Mode | How We Prevent It |
|--------------|-------------------|
| Silent trace creation skips (`ON CONFLICT DO NOTHING`) | Unique run_id per execution |
| Cleanup scripts "succeeding" while doing nothing | Fail-fast error handling |
| Accidental weakening of immutability guarantees | S6 triggers + archive-only cleanup |
| One-shot SDSR systems that can't be re-run safely | SDSR Identity Rule |

---

## Non-Negotiable Rules for Contributors

| Rule | Status |
|------|--------|
| Never reuse `run_id` | **LOCKED** |
| Never DELETE from trace tables | **LOCKED** |
| Never bypass preflight or regression guards | **LOCKED** |
| Never add SDSR exceptions to immutability triggers | **LOCKED** |

**If a change violates any of the above, it is rejected.**

---

## Regression Guard: RG-SDSR-01

**Location:** `scripts/preflight/rg_sdsr_execution_identity.py`

**Rule:** A `run_id` MUST be unique per execution. Reuse is forbidden.

**What it prevents:**
- `ON CONFLICT DO NOTHING` silently skipping trace inserts
- Reuse of archived trace identifiers
- Ambiguous execution provenance

**Guard Logic:**
```bash
python scripts/preflight/rg_sdsr_execution_identity.py "$RUN_ID"
# Exit 0 = PASS (unique)
# Exit 4 = FAIL (reuse detected)
```

**Failure Semantics:**
- Exit code ≠ 0 → **STOP**
- No fallback
- No auto-suffixing
- No regeneration inside the guard

If the guard fails, `inject_synthetic.py` must not run.

---

## The Result

Because of these rules:

- SDSR executions are **deterministic**
- Failures are **real**, not tooling artifacts
- Evidence remains **trustworthy**
- The system can be **re-executed indefinitely**

---

**This is not accidental.**
**This is enforced.**

---

## Related Documents

- `SDSR_E2E_TESTING_PROTOCOL.md` — Full testing protocol
- `SDSR.md` — SDSR architecture overview
- `CLAUDE.md` — Session governance

---

*This document is governance-locked. Changes require explicit approval.*
