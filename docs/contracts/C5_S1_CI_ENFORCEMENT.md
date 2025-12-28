# C5-S1 CI Guardrails Enforcement

**Version:** 1.0
**Status:** DESIGN
**Phase:** C5 Learning & Evolution
**Reference:** C5_CI_GUARDRAILS_DESIGN.md, C5_S1_LEARNING_SCENARIO.md

---

## Purpose

This document maps the 6 C5 CI guardrails (CI-C5-1 through CI-C5-6) to the specific implementation of C5-S1 (Learning from Rollback Frequency).

Each guardrail has:
- Concrete checks for C5-S1
- File patterns to verify
- Expected passing conditions

---

## Guardrail Mapping

| Guardrail | C5-S1 Application |
|-----------|-------------------|
| CI-C5-1 | Rollback suggestions are advisory only |
| CI-C5-2 | No bounds change without human approval |
| CI-C5-3 | Only reads `coordination_audit_records` |
| CI-C5-4 | All suggestions versioned in `learning_suggestions` |
| CI-C5-5 | Disabled flag prevents rollback observation |
| CI-C5-6 | Zero imports from kill-switch in S1 |

---

## CI-C5-1: Advisory-Only Output (C5-S1)

### What C5-S1 Produces

C5-S1 generates `LearningSuggestion` records with:
- `suggestion_type = "advisory"` (immutable)
- `suggestion_text` using observational language only
- No direct calls to `EnvelopeManager`, `CoordinationManager`

### Concrete Checks

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/s1_check_advisory_only.sh

set -e

echo "CI-C5-1: Advisory-Only Output (C5-S1)"

# Check 1: No direct envelope modification
echo "  Checking for forbidden envelope modification patterns..."
FORBIDDEN=$(grep -rn "envelope.bounds\s*=" backend/app/learning/ 2>/dev/null || true)
if [ -n "$FORBIDDEN" ]; then
  echo "  FAIL: Direct envelope modification found"
  echo "$FORBIDDEN"
  exit 1
fi

# Check 2: No coordinator apply calls
echo "  Checking for forbidden coordinator calls..."
FORBIDDEN=$(grep -rn "coordinator.apply\|coordinator.update" backend/app/learning/ 2>/dev/null || true)
if [ -n "$FORBIDDEN" ]; then
  echo "  FAIL: Direct coordinator call found"
  echo "$FORBIDDEN"
  exit 1
fi

# Check 3: Suggestion type is advisory
echo "  Checking suggestion type enforcement..."
TYPE_CHECK=$(grep -rn "suggestion_type.*=" backend/app/learning/ 2>/dev/null | grep -v "advisory" || true)
if [ -n "$TYPE_CHECK" ]; then
  echo "  FAIL: Non-advisory suggestion type found"
  echo "$TYPE_CHECK"
  exit 1
fi

# Check 4: Forbidden language in suggestion text
echo "  Checking for forbidden language patterns..."
PATTERNS="should|must|will improve|recommends|apply this|better than"
FORBIDDEN_LANG=$(grep -rniE "suggestion_text.*($PATTERNS)" backend/app/learning/ 2>/dev/null || true)
if [ -n "$FORBIDDEN_LANG" ]; then
  echo "  FAIL: Forbidden language in suggestion text"
  echo "$FORBIDDEN_LANG"
  exit 1
fi

echo "  PASS: Advisory-only output verified"
```

### Expected Files (C5-S1)

| File | Expected Content |
|------|------------------|
| `app/learning/s1_rollback.py` | Observation logic, emit_suggestion() only |
| `app/learning/suggestions.py` | LearningSuggestion with advisory=True |

---

## CI-C5-2: Human Approval Gate (C5-S1)

### What C5-S1 Requires

No bounds adjustment happens automatically based on rollback suggestions. The suggestion only:
- Records the observation
- Sets `status = 'pending_review'`
- Waits for human action

### Concrete Checks

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/s1_check_approval_gate.sh

set -e

echo "CI-C5-2: Human Approval Gate (C5-S1)"

# Check 1: No auto-approval logic
echo "  Checking for auto-approval patterns..."
AUTO_APPROVE=$(grep -rn "approved\s*=\s*True" backend/app/learning/s1_rollback.py 2>/dev/null || true)
if [ -n "$AUTO_APPROVE" ]; then
  echo "  FAIL: Auto-approval detected in S1"
  echo "$AUTO_APPROVE"
  exit 1
fi

# Check 2: No confidence-based approval
echo "  Checking for confidence-based approval..."
CONF_APPROVE=$(grep -rn "if.*confidence.*approved" backend/app/learning/ 2>/dev/null || true)
if [ -n "$CONF_APPROVE" ]; then
  echo "  FAIL: Confidence-based approval detected"
  echo "$CONF_APPROVE"
  exit 1
fi

# Check 3: Applied flag starts False
echo "  Checking applied flag default..."
APPLIED_TRUE=$(grep -rn "applied\s*=\s*True" backend/app/learning/s1_rollback.py 2>/dev/null || true)
if [ -n "$APPLIED_TRUE" ]; then
  echo "  FAIL: Applied flag defaulting to True"
  echo "$APPLIED_TRUE"
  exit 1
fi

# Check 4: Status starts as pending_review
echo "  Checking status default..."
if ! grep -q "status.*pending_review" backend/app/learning/s1_rollback.py 2>/dev/null; then
  echo "  FAIL: Status should default to pending_review"
  exit 1
fi

echo "  PASS: Human approval gate verified"
```

### State Transitions (C5-S1)

```
created → pending_review → acknowledged → dismissed | applied_externally
                                        ↑
                                        Only human action changes status
```

---

## CI-C5-3: Metadata Boundary (C5-S1)

### What C5-S1 Accesses

C5-S1 reads ONLY from `coordination_audit_records` table.

| Allowed | Forbidden |
|---------|-----------|
| `coordination_audit_records` | `active_envelopes` |
| (read only) | `runs` |
| | `steps` |
| | `killswitch_state` |

### Concrete Checks

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/s1_check_metadata_boundary.sh

set -e

echo "CI-C5-3: Metadata Boundary (C5-S1)"

# Check 1: Only allowed table imports
echo "  Checking table access patterns..."
FORBIDDEN_TABLES="ActiveEnvelope|Run|Step|KillswitchState|EnvelopeState"
FORBIDDEN=$(grep -rniE "from app.models.*($FORBIDDEN_TABLES)" backend/app/learning/s1_rollback.py 2>/dev/null || true)
if [ -n "$FORBIDDEN" ]; then
  echo "  FAIL: Forbidden table access in S1"
  echo "$FORBIDDEN"
  exit 1
fi

# Check 2: Verify allowed table is used
echo "  Checking for required table access..."
if ! grep -q "CoordinationAuditRecord\|coordination_audit_records" backend/app/learning/s1_rollback.py 2>/dev/null; then
  echo "  FAIL: S1 should access coordination_audit_records"
  exit 1
fi

# Check 3: No direct session queries to runtime tables
echo "  Checking session query patterns..."
RUNTIME_QUERY=$(grep -rniE "session.query\((ActiveEnvelope|Run|Step|EnvelopeState)\)" backend/app/learning/ 2>/dev/null || true)
if [ -n "$RUNTIME_QUERY" ]; then
  echo "  FAIL: Direct runtime table query found"
  echo "$RUNTIME_QUERY"
  exit 1
fi

echo "  PASS: Metadata boundary verified"
```

### Query Pattern (C5-S1)

```python
# ALLOWED (C5-S1)
from app.models.coordination import CoordinationAuditRecord

def observe_rollbacks(window_start: datetime, window_end: datetime):
    return session.query(CoordinationAuditRecord).filter(
        CoordinationAuditRecord.action == 'revert',
        CoordinationAuditRecord.created_at.between(window_start, window_end)
    ).all()
```

---

## CI-C5-4: Suggestion Versioning (C5-S1)

### What C5-S1 Stores

All rollback suggestions are stored in `learning_suggestions` with:
- `id` (UUID, immutable)
- `version` (integer, monotonic)
- `created_at` (timestamp)
- Trigger enforcing immutability

### Concrete Checks

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/s1_check_versioning.sh

set -e

echo "CI-C5-4: Suggestion Versioning (C5-S1)"

# Check 1: Version field required
echo "  Checking version field in suggestion creation..."
if ! grep -q "version" backend/app/learning/s1_rollback.py 2>/dev/null; then
  echo "  FAIL: Version field missing in S1 suggestion creation"
  exit 1
fi

# Check 2: No UPDATE patterns in S1
echo "  Checking for forbidden UPDATE patterns..."
UPDATE=$(grep -rniE "\.update\(|UPDATE.*learning_suggestions" backend/app/learning/s1_rollback.py 2>/dev/null || true)
if [ -n "$UPDATE" ]; then
  echo "  FAIL: Direct UPDATE on suggestions in S1"
  echo "$UPDATE"
  exit 1
fi

# Check 3: No DELETE patterns
echo "  Checking for forbidden DELETE patterns..."
DELETE=$(grep -rniE "\.delete\(|DELETE.*learning_suggestions" backend/app/learning/ 2>/dev/null || true)
if [ -n "$DELETE" ]; then
  echo "  FAIL: DELETE on suggestions found"
  echo "$DELETE"
  exit 1
fi

# Check 4: Immutability trigger exists
echo "  Checking migration for immutability trigger..."
if ! grep -q "prevent_suggestion_mutation" backend/alembic/versions/*learning_suggestions*.py 2>/dev/null; then
  echo "  FAIL: Immutability trigger not found in migration"
  exit 1
fi

echo "  PASS: Suggestion versioning verified"
```

### Schema Pattern (C5-S1)

```sql
-- Must exist in migration
CREATE TRIGGER learning_suggestion_immutable
    BEFORE UPDATE ON learning_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION prevent_suggestion_mutation();
```

---

## CI-C5-5: Learning Disable Flag (C5-S1)

### What C5-S1 Checks

Before observing rollbacks, C5-S1 must check `LEARNING_ENABLED`:
- If False → No observation, no suggestion
- If True → Normal operation

### Concrete Checks

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/s1_check_disable_flag.sh

set -e

echo "CI-C5-5: Learning Disable Flag (C5-S1)"

# Check 1: Flag check exists in S1 entry point
echo "  Checking for flag check in S1..."
if ! grep -q "LEARNING_ENABLED\|learning_enabled" backend/app/learning/s1_rollback.py 2>/dev/null; then
  echo "  FAIL: No LEARNING_ENABLED check in S1"
  exit 1
fi

# Check 2: Flag check is guard pattern
echo "  Checking guard pattern..."
if ! grep -q "@require_learning_enabled\|if not.*learning_enabled" backend/app/learning/s1_rollback.py 2>/dev/null; then
  echo "  FAIL: Guard pattern not found in S1"
  exit 1
fi

# Check 3: Flag defaults to False
echo "  Checking flag default..."
if grep -q "LEARNING_ENABLED\s*=\s*True" backend/app/learning/config.py 2>/dev/null; then
  echo "  FAIL: LEARNING_ENABLED defaults to True (should be False)"
  exit 1
fi

echo "  PASS: Learning disable flag verified"
```

### Guard Pattern (C5-S1)

```python
# REQUIRED in s1_rollback.py
from app.learning.config import learning_enabled

def observe_rollback_frequency(window_start: datetime, window_end: datetime):
    if not learning_enabled():
        log.info("Learning disabled, skipping S1 observation")
        return None

    # Only then proceed
    return do_observation(window_start, window_end)
```

---

## CI-C5-6: Kill-Switch Isolation (C5-S1)

### What C5-S1 Must NOT Do

C5-S1 must have zero imports from:
- `app/optimization/killswitch.py`
- `app/optimization/coordinator.py`

### Concrete Checks

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/s1_check_killswitch_isolation.sh

set -e

echo "CI-C5-6: Kill-Switch Isolation (C5-S1)"

# Check 1: No kill-switch imports in S1
echo "  Checking for kill-switch imports..."
KS_IMPORT=$(grep -rn "from app.optimization.killswitch\|import killswitch" backend/app/learning/ 2>/dev/null || true)
if [ -n "$KS_IMPORT" ]; then
  echo "  FAIL: Kill-switch import found in learning module"
  echo "$KS_IMPORT"
  exit 1
fi

# Check 2: No coordinator imports in S1
echo "  Checking for coordinator imports..."
COORD_IMPORT=$(grep -rn "from app.optimization.coordinator\|import coordinator" backend/app/learning/ 2>/dev/null || true)
if [ -n "$COORD_IMPORT" ]; then
  echo "  FAIL: Coordinator import found in learning module"
  echo "$COORD_IMPORT"
  exit 1
fi

# Check 3: No reverse imports (learning in killswitch)
echo "  Checking for reverse imports in killswitch..."
REV_IMPORT=$(grep -rn "from app.learning\|import.*learning" backend/app/optimization/killswitch.py 2>/dev/null || true)
if [ -n "$REV_IMPORT" ]; then
  echo "  FAIL: Learning import found in killswitch module"
  echo "$REV_IMPORT"
  exit 1
fi

echo "  PASS: Kill-switch isolation verified"
```

### Module Boundary (C5-S1)

```
app/optimization/killswitch.py  ──────────────┐
                                              │ NO IMPORTS
app/learning/s1_rollback.py    ──────────────┘

                                    ↕
                     (completely separate)
```

---

## Combined Runner (C5-S1)

```bash
#!/bin/bash
# scripts/ci/c5_guardrails/run_s1_checks.sh

set -e

echo "============================================"
echo "C5-S1 CI Guardrails Verification"
echo "Scenario: Learning from Rollback Frequency"
echo "============================================"
echo ""

FAILED=0
PASSED=0

# Run all S1-specific checks
./scripts/ci/c5_guardrails/s1_check_advisory_only.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
./scripts/ci/c5_guardrails/s1_check_approval_gate.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
./scripts/ci/c5_guardrails/s1_check_metadata_boundary.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
./scripts/ci/c5_guardrails/s1_check_versioning.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
./scripts/ci/c5_guardrails/s1_check_disable_flag.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
./scripts/ci/c5_guardrails/s1_check_killswitch_isolation.sh && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

echo ""
echo "============================================"
echo "C5-S1 Guardrails Summary"
echo "============================================"
echo "Passed: $PASSED / 6"
echo "Failed: $FAILED / 6"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "C5-S1 GUARDRAILS: PASS"
  exit 0
else
  echo "C5-S1 GUARDRAILS: FAIL"
  exit 1
fi
```

---

## Acceptance Criteria Mapping

| Guardrail | Acceptance Criteria Covered |
|-----------|----------------------------|
| CI-C5-1 | AC-S1-I1, AC-S1-B4 |
| CI-C5-2 | AC-S1-I2, AC-S1-I8, AC-S1-H1-H4 |
| CI-C5-3 | AC-S1-I3, AC-S1-B1 |
| CI-C5-4 | AC-S1-I4, AC-S1-M1-M3 |
| CI-C5-5 | AC-S1-I5, AC-S1-D1-D3 |
| CI-C5-6 | AC-S1-I6, AC-S1-B2-B3 |

---

## Implementation Order (When C5-S1 Implemented)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Create CI scripts (stubs, fail by default) | 🔒 LOCKED |
| 2 | Create `app/learning/` directory | 🔒 LOCKED |
| 3 | Create `s1_rollback.py` (observation only) | 🔒 LOCKED |
| 4 | Create `learning_suggestions` migration | 🔒 LOCKED |
| 5 | Run CI scripts (should pass) | 🔒 LOCKED |
| 6 | Create unit tests | 🔒 LOCKED |
| 7 | Create integration tests | 🔒 LOCKED |
| 8 | Certify C5-S1 | 🔒 LOCKED |

---

## Truth Anchor

> Every CI check exists because a silent failure could destroy trust.
> Every pattern restriction exists because flexibility enables escape.
> Every isolation rule exists because coupling enables interference.
>
> If a check can be skipped, it will be.
> If a pattern can be bent, it will be.
> If an import can happen, it will happen.
>
> The guardrails are the only things standing between learning and chaos.
