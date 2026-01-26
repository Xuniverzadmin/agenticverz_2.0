# Transaction Bypass Remediation Checklist v1.0

**Date:** 2026-01-25
**Status:** ACTIVE
**Target:** 116 TRANSACTION_BYPASS violations → 0
**Reference:** AUTHORITY_VIOLATION_SPEC_V1.md, L4_L5_CONTRACTS_V1.md

---

## I. Governing Principle

> **L6 drivers MUST NOT commit transactions.**
> **L4 coordinators OWN the commit authority.**

A driver that can commit is an uncontrolled authority.
Partial writes corrupt invariants.
Commit authority must be singular.

---

## II. Current Violation Pattern

The analyzer detected 116 instances of `session.commit()` in L6 drivers.

**Root Cause:**
```python
# L6 driver (WRONG)
class PolicyDriver:
    def save_policy(self, policy: Policy):
        session = get_session()       # Driver creates session
        session.add(policy)
        session.commit()              # ← VIOLATION: L6 commits
```

**Why This Is Dangerous:**
- Partial writes if subsequent operations fail
- No rollback coordination across domains
- Events may fire before all operations complete
- Inconsistent state visible to readers

---

## III. Target Pattern

```python
# L6 driver (CORRECT)
class PolicyDriver:
    def save_policy(self, session: Session, policy: Policy):
        session.add(policy)
        # NO COMMIT - caller owns transaction boundary
```

**Caller (L4 or L5 coordinator):**
```python
# L4 coordinator (CORRECT)
class TransactionCoordinator:
    def execute(self, ...):
        with Session(engine) as session:
            self.policy_driver.save_policy(session, policy)
            self.incident_driver.save_incident(session, incident)
            session.commit()  # ← L4 owns commit
```

---

## IV. Remediation Steps (Per File)

### Step 1: Identify the File

```bash
# List all L6 files with session.commit
grep -rn "session.commit" backend/app/hoc/cus/*/L6_drivers/*.py
```

### Step 2: Classify the Commit Type

| Pattern | Classification | Action |
|---------|----------------|--------|
| Single-model write | SIMPLE | Remove commit, add session parameter |
| Multi-model write (same domain) | COMPOUND | Remove commit, ensure caller coordinates |
| Cross-domain write | ORCHESTRATION | Must route through L4 coordinator |

### Step 3: Apply the Fix

#### For SIMPLE (single-model) commits:

**Before:**
```python
def create_alert(self, alert: Alert) -> Alert:
    session = self._get_session()
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert
```

**After:**
```python
def create_alert(self, session: Session, alert: Alert) -> Alert:
    session.add(alert)
    session.flush()  # Get ID without committing
    session.refresh(alert)
    return alert
```

#### For COMPOUND (multi-model, same domain) commits:

**Before:**
```python
def create_policy_with_rules(self, policy: Policy, rules: List[Rule]):
    session = self._get_session()
    session.add(policy)
    for rule in rules:
        rule.policy_id = policy.id
        session.add(rule)
    session.commit()
```

**After:**
```python
def create_policy_with_rules(self, session: Session, policy: Policy, rules: List[Rule]):
    session.add(policy)
    session.flush()  # Get policy.id
    for rule in rules:
        rule.policy_id = policy.id
        session.add(rule)
    # NO COMMIT - caller owns boundary
```

#### For ORCHESTRATION (cross-domain) commits:

These MUST go through `RunCompletionTransaction` or equivalent L4 coordinator.

**Before:**
```python
def finalize_run(self, run_id: str):
    session = self._get_session()
    run = session.get(Run, run_id)
    incident = Incident(run_id=run_id)
    session.add(incident)
    policy_eval = PolicyEvaluation(run_id=run_id)
    session.add(policy_eval)
    session.commit()  # ← Cross-domain commit
```

**After:**
```python
# This operation should NOT exist in L6
# Route to L4 coordinator instead:

from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import (
    get_transaction_coordinator,
)

coordinator = get_transaction_coordinator()
result = coordinator.execute(run_id=run_id, ...)
```

### Step 4: Update Callers

Every caller of the modified driver must now:
1. Create or receive a `Session`
2. Pass it to the driver
3. Own the commit decision

**Before (caller):**
```python
def process_alert(self, data):
    driver = AlertDriver()
    driver.create_alert(Alert(**data))
```

**After (caller):**
```python
def process_alert(self, session: Session, data):
    driver = AlertDriver()
    driver.create_alert(session, Alert(**data))
```

### Step 5: Verify

```bash
# Re-run analyzer on specific file
python3 scripts/ops/hoc_authority_analyzer.py --mode full --domain policies | grep "TRANSACTION_BYPASS"
```

---

## V. Files to Remediate (Priority Order)

### Priority 1: L6 Drivers with Multiple Commits (Highest Risk)

These files have multiple `session.commit()` calls, indicating complex transaction patterns:

| File | Commits | Priority |
|------|---------|----------|
| `policies/L6_drivers/alert_emitter.py` | 4 | P1 |
| `policies/L6_drivers/transaction_coordinator.py` | 1 | P1 (header mismatch) |
| `policies/L6_drivers/recovery_matcher.py` | 2 | P1 |
| `policies/L6_drivers/capture.py` | 2+ | P1 |
| `analytics/L6_drivers/circuit_breaker.py` | 2+ | P1 |

### Priority 2: L6 Drivers with Single Commit (Mechanical Fix)

These are straightforward session parameter additions.

### Priority 3: L5 Engines with Commits

L5 engines should not commit either—they should delegate to L4.

---

## VI. Session Injection Pattern

### Option A: Constructor Injection (Preferred for Stateful Drivers)

```python
class PolicyDriver:
    def __init__(self, session: Session):
        self._session = session

    def save(self, policy: Policy):
        self._session.add(policy)
```

### Option B: Method Injection (Preferred for Stateless Drivers)

```python
class PolicyDriver:
    def save(self, session: Session, policy: Policy):
        session.add(policy)
```

### Option C: Context Protocol (For L4 Coordination)

```python
@dataclass
class TransactionContext:
    session: Session
    correlation_id: str
    timestamp: datetime

class PolicyDriver:
    def save(self, ctx: TransactionContext, policy: Policy):
        ctx.session.add(policy)
```

**Recommendation:** Start with Option B (method injection) for mechanical fixes.
Migrate to Option C when `TransactionContext` is fully implemented.

---

## VII. Common Pitfalls

### Pitfall 1: Using `session.flush()` as Hidden Commit

`flush()` is NOT a commit—it writes to DB but doesn't commit the transaction.
Use `flush()` when you need generated IDs before commit.

```python
session.add(policy)
session.flush()  # Writes to DB, gets ID, but still in transaction
policy_id = policy.id  # Now available
```

### Pitfall 2: Forgetting to Propagate Session to Nested Calls

```python
# WRONG
def create_policy(self, session: Session, data):
    policy = Policy(**data)
    session.add(policy)
    self._create_default_rules(policy)  # ← Missing session!

# CORRECT
def create_policy(self, session: Session, data):
    policy = Policy(**data)
    session.add(policy)
    session.flush()
    self._create_default_rules(session, policy)  # ← Session passed
```

### Pitfall 3: Mixing Commit-Owning Code

Never have both patterns in the same codebase:
```python
# DANGEROUS MIX
driver.save_with_commit(policy)      # Commits internally
driver.save_without_commit(session, rule)  # Expects external commit
```

Pick one pattern and enforce it universally.

---

## VIII. Verification Checklist

For each remediated file:

- [ ] `session.commit()` removed from L6 driver
- [ ] `session` parameter added to affected methods
- [ ] All callers updated to pass `session`
- [ ] `session.flush()` used where IDs needed before commit
- [ ] Analyzer reports 0 TRANSACTION_BYPASS for this file
- [ ] Unit tests updated to use session fixtures
- [ ] Integration tests verify transaction boundaries

---

## IX. CI Gate

After all 116 violations are fixed:

```yaml
# .github/workflows/authority-check.yml
- name: Authority Violations Check
  run: |
    python3 scripts/ops/hoc_authority_analyzer.py --mode full --check
    if [ $? -ne 0 ]; then
      echo "CRITICAL authority violations detected"
      exit 1
    fi
```

---

## X. Success Criteria

| Metric | Before | Target |
|--------|--------|--------|
| TRANSACTION_BYPASS count | 116 | 0 |
| L6 files with `session.commit` | 30+ | 0 |
| L4 coordinators owning commit | 1 | 1 (verified) |
| CI gate enabled | No | Yes |

---

## XI. Execution Order

1. **Fix Priority 1 files** (highest risk, multiple commits)
2. **Fix Priority 2 files** (mechanical, single commits)
3. **Fix L5 engines** (delegate to L4)
4. **Enable CI gate**
5. **Verify with full scan**

---

## XII. Reference

- **Authority Violation Spec:** `docs/architecture/hoc/AUTHORITY_VIOLATION_SPEC_V1.md`
- **L4/L5 Contracts:** `docs/architecture/hoc/L4_L5_CONTRACTS_V1.md`
- **Transaction Coordinator:** `backend/app/hoc/cus/general/L4_runtime/drivers/transaction_coordinator.py`
- **Analyzer:** `scripts/ops/hoc_authority_analyzer.py`

---

**Checklist Author:** Claude (First-Principles Analysis)
**Review Status:** PENDING HUMAN RATIFICATION
