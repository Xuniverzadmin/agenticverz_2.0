# PIN-382: DB-AUTH-001 Database Authority Governance

**Status:** FOUNDATIONAL
**Created:** 2026-01-10
**Category:** Governance / Infrastructure
**Severity:** CRITICAL
**Baseline:** 58 HIGH-severity scripts (2026-01-10)

---

## Summary

Establishes formal governance for database authority determinism. Authority is declared, not inferred. This eliminates the "Neon vs Local discovery loop" problem permanently.

**DB-AUTH-001 is FOUNDATIONAL:** New invariants may depend on it. None may weaken it. It is assumed, not re-argued.

---

## Root Cause Analysis

Claude "discovers" Neon repeatedly because:

1. Both DBs are reachable
2. Scripts are not environment-locked
3. Authority is implicit, not declared
4. Claude has no invariant to check before acting
5. Session memory is not binding behavior

This is a governance failure, not an intelligence issue.

---

## Solution: 4-Layer Authority System

### Layer 1: Authority Contract

**File:** `docs/runtime/DB_AUTHORITY.md`

Declares:
- `AUTHORITATIVE_DB = neon`
- `LOCAL_DB_ROLE = ephemeral, test-only`

This is law, not documentation.

### Layer 2: Machine-Readable Authority Flag

**Environment Variables:**
```env
DB_AUTHORITY=neon
DB_ENV=prod-like
```

Now Claude doesn't infer. It reads.

### Layer 3: Mandatory Preflight Check

**File:** `backend/scripts/_db_guard.py`

Hard gate enforcement script:
- Exit code 5: DB_AUTHORITY not declared
- Exit code 6: Authority mismatch
- Exit code 7: DATABASE_URL not found
- Exit code 8: URL doesn't match authority

### Layer 4: Claude Session Self-Awareness Protocol

Mandatory pre-check before any DB operation:
```
DB AUTHORITY DECLARATION
- Declared Authority: <neon | local>
- Intended Operation: <read | write | validate | test>
- Justification: <single sentence>
```

---

## Key Invariant

> **Claude must never infer database authority from evidence. Authority is declared, not discovered.**

---

## Permitted Operations Matrix

| Operation Type | Neon | Local |
|----------------|------|-------|
| Read canonical history | ✅ | ❌ |
| Validate runs | ✅ | ❌ |
| SDSR scenario execution | ✅ | ❌ |
| Schema experiments | ❌ | ✅ |
| Migration dry-runs | ❌ | ✅ |
| Unit tests | ❌ | ✅ |

---

## Prohibited Behaviors

1. Inferring authority from data age
2. Switching databases mid-session
3. "Checking both" to decide correctness
4. Retrying against a different DB
5. Discovering authority after execution
6. Silent fallback from Neon → Local

---

## Files Created

| File | Purpose |
|------|---------|
| `docs/runtime/DB_AUTHORITY.md` | Authority contract (law) |
| `docs/governance/DB_AUTH_001_INVARIANT.md` | Formal governance invariant |
| `backend/scripts/_db_guard.py` | Enforcement script |

## Files Modified

| File | Change |
|------|--------|
| `CLAUDE.md` | Added DB-AUTH-001 blocking rule |
| `.env` | Added `DB_AUTHORITY=neon` and `DB_ENV=prod-like` |

---

## Exit Codes (_db_guard.py)

| Code | Meaning |
|------|---------|
| 5 | DB_AUTHORITY not declared |
| 6 | Authority mismatch |
| 7 | DATABASE_URL not found |
| 8 | URL doesn't match authority |

---

## Usage

```python
# In scripts that touch DB:
from scripts._db_guard import assert_db_authority, get_db_url

# Assert expected authority:
assert_db_authority("neon")

# Get validated URL:
db_url = get_db_url()
```

Or use convenience functions:
```python
from scripts._db_guard import require_neon

db_url = require_neon()  # Fails if authority != neon
```

---

## Enforcement Mechanisms (Phase 2)

### A. CI Enforcement

**File:** `.github/workflows/db-authority-guard.yml`

Fails the build if:
- DB_AUTHORITY is missing from env files
- Scripts touch DB without `_db_guard.py`
- Dual-connection anti-patterns detected

### B. Dual-Connection Detection

**In:** `backend/scripts/_db_guard.py`

Runtime assertion that prevents both Neon and Local connections in one process.

```python
register_connection("neon")  # OK
register_connection("local") # ABORT - exit code 9
```

If both connection strings are initialized → Immediate abort.
This kills the "check both" anti-pattern permanently.

### C. Governance Drift Detector

**File:** `backend/scripts/ops/db_authority_drift_detector.py`

Weekly audit that scans for:
- New scripts without `_db_guard.py`
- New env files without `DB_AUTHORITY`
- New docs mentioning DB usage without authority declaration

```bash
python db_authority_drift_detector.py --output json
python db_authority_drift_detector.py --pin  # Generate memory PIN
```

Log → Pin → Review. No auto-fix.

### D. Override Protocol

For when exceptions are necessary (they will happen):

```env
GOVERNANCE_OVERRIDE=DB-AUTH-001
OVERRIDE_REASON=Migration requires both DBs for comparison
OVERRIDE_TTL=2026-01-11T12:00:00Z
```

Rules:
- No TTL → invalid override
- Expired TTL → hard fail (exit code 10)
- Override is logged for audit

---

## Exit Codes Summary

| Code | Meaning | Source |
|------|---------|--------|
| 0 | Clean (no drift) | drift_detector |
| 1 | Drift detected | drift_detector |
| 2 | Error during scan | drift_detector |
| 3 | **REGRESSION** (drift count increased) | drift_detector |
| 5 | DB_AUTHORITY not declared | _db_guard |
| 6 | Authority mismatch | _db_guard |
| 7 | DATABASE_URL not found | _db_guard |
| 8 | URL doesn't match authority | _db_guard |
| 9 | Dual-connection detected | _db_guard |
| 10 | Override expired or invalid | _db_guard |

---

## Debt Containment Strategy

**File:** `docs/governance/DB_AUTH_001_DEBT_CLASSIFICATION.md`

The 58 HIGH severity scripts are classified into buckets:

| Bucket | Count | Action |
|--------|-------|--------|
| A: Dead/Obsolete | ~25 | DELETE |
| B: Local-Only | ~15 | Add `assert_db_authority("local")` |
| C: Authority-Sensitive | ~20 | Add full `require_neon()` |

**Golden Rule:** Never weaken DB-AUTH-001 to reduce the count. Reduce the count to satisfy DB-AUTH-001.

---

## Trend Tracking & Monotonicity Enforcement

**History File:** `.db_authority_drift_history.json`

The drift detector tracks drift count over time:

```bash
# Record current count to history
python db_authority_drift_detector.py --record

# Show trend over time
python db_authority_drift_detector.py --trend
```

### Monotonicity Enforcement (LOCKED)

**Rule:** Drift count must NEVER increase.

When `--record` is used and current count > previous count:
- Exit code 3 (HARD FAIL)
- Clear error message identifying the regression
- Build/CI fails immediately

This is not a warning. This is a failure.

**Current Baseline:** 58 HIGH severity scripts (2026-01-10)

Any increase beyond 58 triggers exit code 3.

---

## Verification

```bash
# Test regression detection (should exit 3)
echo '[{"timestamp": "2026-01-09T00:00:00+00:00", "count": 50}]' > .db_authority_drift_history.json
python backend/scripts/ops/db_authority_drift_detector.py --record
# Expected: Exit code 3, REGRESSION DETECTED

# Normal operation (should exit 1 for drift, 0 for clean)
python backend/scripts/ops/db_authority_drift_detector.py
```

---

## Related

- PIN-381: SDSR E2E Testing Protocol
- `docs/governance/DB_AUTH_001_INVARIANT.md`
- `docs/governance/DB_AUTH_001_DEBT_CLASSIFICATION.md`
- `docs/runtime/DB_AUTHORITY.md`
