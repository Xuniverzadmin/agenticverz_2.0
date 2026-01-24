# PIN-173: Phase 5B - Policy Pre-Check Matrix

**Status:** COMPLETE
**Category:** Contracts / Behavioral Changes
**Created:** 2025-12-26
**Frozen:** 2025-12-26
**Completed:** 2025-12-26
**Milestone:** Post-M28 Behavioral Changes

---

## Scope Lock

> **This matrix is FROZEN as of 2025-12-26.**
> Any modification requires a delta proposal reviewed against the contract framework.
> No exceptions.

---

## Executive Summary

Phase 5B implements policy pre-check enforcement - the second behavioral change after contract freeze. When a run request arrives, the system must pre-check policy constraints BEFORE execution begins. Failures surface as decisions (strict mode only) and block run creation.

---

## Prerequisites

| Prerequisite | Status |
|--------------|--------|
| Phase 5A complete (budget enforcement) | PENDING |
| Contracts frozen (`contracts-stable-v1`) | COMPLETE |
| Decision emission infrastructure | COMPLETE |
| PRE-RUN declaration infrastructure | COMPLETE |

---

## Phase 5B Objective (Singular)

> **Before execution starts, pre-check policies and either block (strict) or warn (advisory).**

Nothing more. No other behavioral changes allowed.

---

## Frozen Behavioral Matrix

| ID     | Behavior                                             | Posture  | Contract           | Decision Outcome   |
|--------|------------------------------------------------------|----------|--------------------|--------------------|
| 5B-01  | Block run if pre-check fails                         | strict   | PRE-RUN → DECISION | policy_blocked     |
| 5B-02  | Allow run with warnings if pre-check fails           | advisory | PRE-RUN            | N/A (no decision)  |
| 5B-03a | Block run if policy service unavailable              | strict   | CONSTRAINT         | policy_unavailable |
| 5B-03b | Allow run with warning if policy service unavailable | advisory | PRE-RUN            | N/A (warning only) |
| 5B-04  | Surface pre-check result in PRE-RUN declaration      | any      | PRE-RUN            | N/A (visibility)   |

---

## Decision Types (Frozen)

```python
class DecisionType(str, Enum):
    # ... existing ...
    POLICY_PRE_CHECK = "policy_pre_check"  # Phase 5B: Pre-execution policy block

class DecisionOutcome(str, Enum):
    # ... existing ...
    POLICY_BLOCKED = "policy_blocked"          # Pre-check failed (strict mode)
    POLICY_UNAVAILABLE = "policy_unavailable"  # Policy service down (strict mode)
    # NO POLICY_ALLOWED - success is not a decision, it's the default path
```

---

## Decision Emission Rule (Frozen)

```
EMIT decision record IF AND ONLY IF:
  - posture == strict
  - AND (pre_check_failed OR policy_service_unavailable)

DO NOT EMIT decision record IF:
  - pre_check passed (default path)
  - posture == advisory (warnings go in PRE-RUN declaration)
```

**Rationale:**
- Decisions emit on divergence from default, not on success
- This keeps the ledger meaningful (signal, not noise)
- "Allowed" status is visible in PRE-RUN declaration, not DECISION records

---

## Pre-Check Decision Record (When Emitted)

```python
DecisionRecord(
    decision_type=DecisionType.POLICY_PRE_CHECK,
    decision_source="system",
    decision_trigger="explicit",  # pre-check is proactive, not reactive
    decision_outcome=DecisionOutcome.POLICY_BLOCKED,  # or POLICY_UNAVAILABLE
    decision_reason="Pre-check failed: <rule_id> violated",
    decision_inputs={"policies_checked": [...], "violations": [...]},
    request_id=request_id,  # Always present (pre-run)
    run_id=None,            # Never set (run not created)
    causal_role="pre_run",
    details={"posture": "strict", "blocked": True}
)
```

---

## PRE-RUN Declaration Extension

```python
class PreRunDeclaration:
    # ... existing fields ...
    policy_status: PolicyPreCheckStatus

class PolicyPreCheckStatus:
    posture: Literal["strict", "advisory"]
    checked: bool
    passed: bool
    violations: List[str]  # Empty if passed
    warnings: List[str]    # Advisory mode only
    service_available: bool
```

---

## Allowed Changes (Exhaustive)

| File | Change |
|------|--------|
| `policy/engine.py` | Add `pre_check(request)` method |
| `api/runs.py` | Call pre_check before run creation |
| `api/runs.py` | Block run creation if strict + failed |
| `api/runs.py` | Emit decision record on block |
| `customer/pre_run.py` | Include policy_status in declaration |
| `contracts/models.py` | Add POLICY_PRE_CHECK, POLICY_BLOCKED, POLICY_UNAVAILABLE |

---

## Forbidden Changes

- Policy evaluation logic
- Routing behavior
- Recovery behavior
- Budget enforcement
- Memory behavior
- Post-execution policy checks
- Policy auto-remediation
- Plan mutation
- CARE routing

---

## Stop Conditions

Phase 5B must halt immediately if:
- New ledger entry required
- Decision emitted on "allowed" path
- Silent block (no decision record)
- Run created despite strict block
- Advisory mode emits decision record
- Scope creep suggestions

---

## E2E Test Matrix (FROZEN)

### Test Definitions

| Test ID | Scenario | Posture | Expected Outcome |
|---------|----------|---------|------------------|
| G5B-01 | Pre-check fails | strict | Run blocked, decision emitted, no run created |
| G5B-02 | Pre-check passes | strict | Run created, NO decision emitted |
| G5B-03 | Pre-check fails | advisory | Run created with warning in declaration, NO decision |
| G5B-04 | Pre-check passes | advisory | Run created, no warnings, NO decision |
| G5B-05 | Policy service unavailable | strict | Run blocked, policy_unavailable decision |
| G5B-06 | Policy service unavailable | advisory | Run proceeds with warning, NO decision |
| G5B-07 | Decision has correct causal_role | strict+blocked | pre_run |
| G5B-08 | PreRunDeclaration shows policy status | any | Includes policy_status field |
| G5B-09 | No run created on block | strict+blocked | Verify runs table unchanged |
| G5B-10 | Timeline shows pre-check before ACK | strict+blocked | Founder can reconstruct causality |

---

## E2E Test Implementations

### G5B-01: Pre-check fails (strict mode)

```python
async def test_g5b_01_precheck_fails_strict():
    """
    GIVEN: A policy that will fail pre-check
    AND: posture = strict
    WHEN: Run is requested
    THEN:
      - Run is NOT created
      - Decision record emitted with:
        - decision_type = POLICY_PRE_CHECK
        - decision_outcome = POLICY_BLOCKED
        - causal_role = pre_run
        - run_id = None
        - request_id = <generated>
      - PRE-RUN declaration shows policy_status.passed = False
    """
    # Setup: Configure policy that will fail
    policy_config = {"rules": [{"id": "DENY_ALL", "effect": "deny"}]}

    # Request run
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "strict"},
        headers={"X-Request-ID": request_id}
    )

    # Assert: Run blocked
    assert response.status_code == 403
    assert "policy_blocked" in response.json()["error"]

    # Assert: No run created
    runs_count = await db.execute("SELECT COUNT(*) FROM runs WHERE request_id = $1", request_id)
    assert runs_count == 0

    # Assert: Decision emitted
    decision = await db.fetchone(
        "SELECT * FROM decision_records WHERE request_id = $1",
        request_id
    )
    assert decision is not None
    assert decision["decision_type"] == "policy_pre_check"
    assert decision["decision_outcome"] == "policy_blocked"
    assert decision["causal_role"] == "pre_run"
    assert decision["run_id"] is None
```

### G5B-02: Pre-check passes (strict mode)

```python
async def test_g5b_02_precheck_passes_strict():
    """
    GIVEN: A policy that will pass pre-check
    AND: posture = strict
    WHEN: Run is requested
    THEN:
      - Run IS created
      - NO decision record emitted for policy_pre_check
      - PRE-RUN declaration shows policy_status.passed = True
    """
    # Setup: Configure policy that will pass
    policy_config = {"rules": [{"id": "ALLOW_ALL", "effect": "allow"}]}

    # Request run
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "strict"},
        headers={"X-Request-ID": request_id}
    )

    # Assert: Run created
    assert response.status_code == 201
    run_id = response.json()["run_id"]

    # Assert: NO decision emitted for pre-check
    decision = await db.fetchone(
        """SELECT * FROM decision_records
           WHERE request_id = $1 AND decision_type = 'policy_pre_check'""",
        request_id
    )
    assert decision is None  # Success is NOT a decision
```

### G5B-03: Pre-check fails (advisory mode)

```python
async def test_g5b_03_precheck_fails_advisory():
    """
    GIVEN: A policy that will fail pre-check
    AND: posture = advisory
    WHEN: Run is requested
    THEN:
      - Run IS created (advisory does not block)
      - NO decision record emitted
      - PRE-RUN declaration shows policy_status.warnings populated
    """
    # Setup: Configure policy that will fail
    policy_config = {"rules": [{"id": "DENY_ALL", "effect": "deny"}]}

    # Request run
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "advisory"},
        headers={"X-Request-ID": request_id}
    )

    # Assert: Run created despite failure
    assert response.status_code == 201
    run_id = response.json()["run_id"]

    # Assert: NO decision emitted
    decision = await db.fetchone(
        """SELECT * FROM decision_records
           WHERE request_id = $1 AND decision_type = 'policy_pre_check'""",
        request_id
    )
    assert decision is None  # Advisory mode: warnings only

    # Assert: Declaration has warnings
    declaration = await get_pre_run_declaration(run_id)
    assert declaration["policy_status"]["passed"] == False
    assert len(declaration["policy_status"]["warnings"]) > 0
```

### G5B-04: Pre-check passes (advisory mode)

```python
async def test_g5b_04_precheck_passes_advisory():
    """
    GIVEN: A policy that will pass pre-check
    AND: posture = advisory
    WHEN: Run is requested
    THEN:
      - Run IS created
      - NO decision record emitted
      - PRE-RUN declaration shows policy_status.passed = True, warnings empty
    """
    # Request run
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "advisory"},
        headers={"X-Request-ID": request_id}
    )

    # Assert: Run created
    assert response.status_code == 201

    # Assert: NO decision emitted
    decision = await db.fetchone(
        """SELECT * FROM decision_records
           WHERE request_id = $1 AND decision_type = 'policy_pre_check'""",
        request_id
    )
    assert decision is None
```

### G5B-05: Policy service unavailable (strict mode)

```python
async def test_g5b_05_service_unavailable_strict():
    """
    GIVEN: Policy service is unavailable
    AND: posture = strict
    WHEN: Run is requested
    THEN:
      - Run is NOT created
      - Decision record emitted with decision_outcome = policy_unavailable
    """
    # Setup: Mock policy service failure
    with mock_policy_service_down():
        request_id = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/runs",
            json={"goal": "test", "policy_posture": "strict"},
            headers={"X-Request-ID": request_id}
        )

    # Assert: Run blocked
    assert response.status_code == 503

    # Assert: No run created
    runs_count = await db.execute("SELECT COUNT(*) FROM runs WHERE request_id = $1", request_id)
    assert runs_count == 0

    # Assert: Decision emitted
    decision = await db.fetchone(
        "SELECT * FROM decision_records WHERE request_id = $1",
        request_id
    )
    assert decision["decision_outcome"] == "policy_unavailable"
```

### G5B-06: Policy service unavailable (advisory mode)

```python
async def test_g5b_06_service_unavailable_advisory():
    """
    GIVEN: Policy service is unavailable
    AND: posture = advisory
    WHEN: Run is requested
    THEN:
      - Run IS created (advisory proceeds with warning)
      - NO decision record emitted
      - PRE-RUN declaration shows service_available = False
    """
    # Setup: Mock policy service failure
    with mock_policy_service_down():
        request_id = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/runs",
            json={"goal": "test", "policy_posture": "advisory"},
            headers={"X-Request-ID": request_id}
        )

    # Assert: Run created
    assert response.status_code == 201

    # Assert: NO decision emitted
    decision = await db.fetchone(
        """SELECT * FROM decision_records
           WHERE request_id = $1 AND decision_type = 'policy_pre_check'""",
        request_id
    )
    assert decision is None

    # Assert: Declaration shows warning
    declaration = await get_pre_run_declaration(response.json()["run_id"])
    assert declaration["policy_status"]["service_available"] == False
```

### G5B-07: Causal role is pre_run

```python
async def test_g5b_07_causal_role_pre_run():
    """
    GIVEN: Pre-check fails in strict mode
    WHEN: Decision is emitted
    THEN: causal_role = pre_run
    """
    # Setup and trigger block
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "strict"},
        headers={"X-Request-ID": request_id}
    )

    # Assert causal_role
    decision = await db.fetchone(
        "SELECT causal_role FROM decision_records WHERE request_id = $1",
        request_id
    )
    assert decision["causal_role"] == "pre_run"
```

### G5B-08: PRE-RUN declaration includes policy status

```python
async def test_g5b_08_declaration_includes_policy_status():
    """
    GIVEN: Any run request
    WHEN: PRE-RUN declaration is generated
    THEN: Declaration includes policy_status field with all required subfields
    """
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "advisory"}
    )
    run_id = response.json()["run_id"]

    declaration = await get_pre_run_declaration(run_id)

    # Assert structure
    assert "policy_status" in declaration
    ps = declaration["policy_status"]
    assert "posture" in ps
    assert "checked" in ps
    assert "passed" in ps
    assert "violations" in ps
    assert "warnings" in ps
    assert "service_available" in ps
```

### G5B-09: No run created on block

```python
async def test_g5b_09_no_run_on_block():
    """
    GIVEN: Pre-check fails in strict mode
    WHEN: Block occurs
    THEN: runs table has no new row
    """
    # Get initial count
    initial_count = await db.fetchval("SELECT COUNT(*) FROM runs")

    # Trigger block
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "strict"},
        headers={"X-Request-ID": request_id}
    )

    assert response.status_code == 403

    # Assert count unchanged
    final_count = await db.fetchval("SELECT COUNT(*) FROM runs")
    assert final_count == initial_count
```

### G5B-10: Founder timeline reconstruction

```python
async def test_g5b_10_founder_timeline_reconstruction():
    """
    GIVEN: Pre-check blocks a run
    WHEN: Founder queries timeline
    THEN:
      - Decision appears in timeline
      - Ordered before any ACK (if ACK existed)
      - request_id links to blocked request
    """
    request_id = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/runs",
        json={"goal": "test", "policy_posture": "strict"},
        headers={"X-Request-ID": request_id}
    )

    # Query founder timeline
    timeline = await client.get(
        f"/fdr/timeline/decisions?request_id={request_id}"
    )

    decisions = timeline.json()["decisions"]
    assert len(decisions) >= 1

    # First decision should be pre-check
    precheck = decisions[0]
    assert precheck["decision_type"] == "policy_pre_check"
    assert precheck["request_id"] == request_id
    assert precheck["causal_role"] == "pre_run"
```

---

## Implementation Order

1. Add `PolicyPreCheckStatus` model
2. Add `POLICY_PRE_CHECK`, `POLICY_BLOCKED`, `POLICY_UNAVAILABLE` to enums
3. Implement `policy_engine.pre_check(request)` method
4. Wire pre-check into `/api/v1/runs` before run creation
5. Emit decision on strict + failure
6. Include policy_status in PRE-RUN declaration
7. Run all G5B tests

---

## Related Documents

- PIN-172: Phase 5A - Budget Enforcement
- PIN-170: System Contract Governance Framework
- `docs/contracts/CONSTRAINT_DECLARATION_CONTRACT.md`
- `docs/contracts/DECISION_RECORD_CONTRACT.md`

---

## Red Phase Results (2025-12-26)

### Test Execution

```
18 tests collected
5 FAILED, 13 PASSED (2.50s)
```

### Failures (Expected - Define Implementation Requirements)

| Test | Failure | Requirement Proven |
|------|---------|-------------------|
| `test_decision_record_emitted` | No decision emitted | strict + failure → must emit |
| `test_policy_unavailable_decision` | No decision emitted | strict + unavailable → must emit |
| `test_causal_role_is_pre_run` | No decision emitted | decision.causal_role = pre_run |
| `test_decision_in_timeline` | No decision emitted | Founder timeline visibility |
| `test_emission_rule_strict_failure_emits` | INVARIANT | strict + failure = emit |

### Passes (Invariants Already Hold)

- Advisory mode emits NO decisions (correct)
- Success path remains silent (correct)
- No accidental run creation
- Structural wiring is correct

### Red Phase Approval

**Status:** APPROVED (2025-12-26)
**Rationale:** All failures correspond 1:1 to missing behavior, not broken tests.

---

## Implementation Checklist (AUTHORITATIVE)

| Step | Task | Status |
|------|------|--------|
| 1 | Extend Decision Enums (additive only) | COMPLETE |
| 2 | Add emit_policy_precheck_decision() helper | COMPLETE |
| 3 | Add pre_check() to PolicyEngine | COMPLETE |
| 4 | Wire pre-check into PRE-RUN flow | COMPLETE |
| 5 | Add policy_status to PRE-RUN declaration | COMPLETE |
| 6 | Re-run tests (all green) | COMPLETE |

---

## Green Phase Results (2025-12-26)

### Test Execution

```
18 tests collected
18 PASSED, 0 FAILED (3.94s)
```

### Implementation Summary

| File | Change |
|------|--------|
| `app/contracts/decisions.py` | Added POLICY_PRE_CHECK, POLICY_BLOCKED, POLICY_UNAVAILABLE enums |
| `app/contracts/decisions.py` | Added emit_policy_precheck_decision() helper |
| `app/policy/engine.py` | Added pre_check() method |
| `app/api/workers.py` | Wired pre-check into run creation flow |
| `app/api/workers.py` | Added PolicyStatusModel and policy_status to response |

### Frozen Emission Rule Verified

✅ `strict + failure → emit POLICY_BLOCKED`
✅ `strict + unavailable → emit POLICY_UNAVAILABLE`
✅ `strict + success → NO EMIT` (success is not a decision)
✅ `advisory + anything → NO EMIT` (warnings in declaration only)
✅ `causal_role = pre_run` for all pre-check decisions
✅ `run_id = None` (run not created on block)
✅ `request_id` links to blocked request for timeline reconstruction

---

## Phase 5B Complete

**Status:** GREEN PHASE COMPLETE (2025-12-26)
**Outcome:** All 18 G5B tests pass, emission rules verified, contracts honored.
