# SDSR Capability Coverage Matrix

**Status:** ACTIVE
**Effective:** 2026-01-11
**Reference:** SDSR_SCENARIO_TAXONOMY.md, PIN-395

---

## Purpose

This matrix maps every capability in the Aurora L2 registry to:
1. The scenario class(es) that can prove it
2. The current validation status
3. The panels blocked until proven

---

## Capability Status Summary

| Status | Count | Description |
|--------|-------|-------------|
| **OBSERVED** | 2 | Proven by SDSR, buttons enabled |
| **DISCOVERED** | 8 | Declared but unproven, buttons disabled |
| **TRUSTED** | 0 | Governance-approved, production-ready |

---

## Capability → Scenario Mapping

### OBSERVED Capabilities (Proven)

| Capability | Status | Proven By | Scenario Class | Observed On |
|------------|--------|-----------|----------------|-------------|
| **APPROVE** | OBSERVED | SDSR-E2E-004 | HUMAN_APPROVAL | 2026-01-11 |
| **REJECT** | OBSERVED | SDSR-E2E-004 | HUMAN_REJECTION | 2026-01-11 |

---

### DISCOVERED Capabilities (Pending Proof)

| Capability | Status | Required Scenario Class | Blocking Panels | Priority |
|------------|--------|------------------------|-----------------|----------|
| **ACKNOWLEDGE** | DISCOVERED | THRESHOLD_BREACH or FAILED_EXECUTION | INC-AI-OI-O2, INC-AI-ID-O3 | P1 |
| **RESOLVE** | DISCOVERED | THRESHOLD_BREACH or PARTIAL_SUCCESS | INC-AI-ID-O3 | P1 |
| **ADD_NOTE** | DISCOVERED | FAILED_EXECUTION or THRESHOLD_BREACH | INC-AI-ID-O3 | P2 |
| **ACTIVATE** | DISCOVERED | POLICY_ACTIVATION or AUTO_POLICY_ACTION | POL-AP-AR-O3, POL-AP-BP-O3, POL-AP-RL-O3 | P3 |
| **DEACTIVATE** | DISCOVERED | POLICY_ACTIVATION or AUTO_POLICY_ACTION | POL-AP-AR-O3, POL-AP-BP-O3, POL-AP-RL-O3 | P3 |
| **UPDATE_THRESHOLD** | DISCOVERED | POLICY_ACTIVATION | POL-AP-BP-O3 | P4 |
| **UPDATE_LIMIT** | DISCOVERED | POLICY_ACTIVATION | POL-AP-RL-O3 | P4 |
| **UPDATE_RULE** | DISCOVERED | POLICY_ACTIVATION | POL-AP-AR-O3 | P4 |

---

## Scenario Class → Capability Mapping

### Class 1: SUCCESSFUL_EXECUTION

**Capabilities Proven:**
- (none with action buttons)

**INFO Panels Validated:**
- ACT-EX-AR-* (Active Runs)
- ACT-EX-CR-* (Completed Runs)
- LOG-ET-TD-* (Trace Details)

**Required Scenario:** SDSR-E2E-005 (defined, NOT RUN)

---

### Class 2: FAILED_EXECUTION

**Capabilities Proven:**
- ACKNOWLEDGE
- ADD_NOTE
- (TRACE - implicit)

**Panels Unlocked:**
- INC-AI-OI-O2 (needs ACKNOWLEDGE)
- INC-AI-ID-O3 (needs ACKNOWLEDGE, ADD_NOTE)

**Required Scenario:** SDSR-E2E-001 (REVOKED, needs rewrite)

---

### Class 3: PARTIAL_SUCCESS

**Capabilities Proven:**
- ACKNOWLEDGE
- RESOLVE (low severity)
- ADD_NOTE

**Panels Unlocked:**
- INC-AI-ID-O3 (partial)

**Required Scenario:** None defined

---

### Class 4: NEAR_VIOLATION

**Capabilities Proven:**
- (none - proves selectivity)

**Panels Unlocked:**
- None (proves NO buttons unlock incorrectly)

**Required Scenario:** None defined

---

### Class 5: THRESHOLD_BREACH

**Capabilities Proven:**
- ACKNOWLEDGE
- ADD_NOTE

**Panels Unlocked:**
- INC-AI-OI-O2
- INC-AI-ID-O3

**Required Scenario:** SDSR-E2E-003 (defined, NOT RUN)

---

### Class 6: AUTO_POLICY_ACTION

**Capabilities Proven:**
- ACTIVATE
- DEACTIVATE
- RESOLVE

**Panels Unlocked:**
- POL-AP-AR-O3
- POL-AP-BP-O3
- POL-AP-RL-O3

**Required Scenario:** None defined

---

### Class 7: HUMAN_APPROVAL

**Capabilities Proven:**
- APPROVE

**Panels Unlocked:**
- POL-PR-PP-O2 (partial)

**Required Scenario:** SDSR-E2E-004 (PASSED)

---

### Class 8: HUMAN_REJECTION

**Capabilities Proven:**
- REJECT

**Panels Unlocked:**
- POL-PR-PP-O2

**Required Scenario:** SDSR-E2E-004 (PASSED)

---

### Class 9: POLICY_ACTIVATION

**Capabilities Proven:**
- ACTIVATE
- DEACTIVATE
- UPDATE_THRESHOLD
- UPDATE_LIMIT
- UPDATE_RULE

**Panels Unlocked:**
- POL-AP-AR-O3
- POL-AP-BP-O3
- POL-AP-RL-O3

**Required Scenario:** None defined (CRITICAL GAP)

---

### Class 10-13: TRACE & ACTOR

**Capabilities Proven:**
- (validation/audit, not action buttons)

**Required Scenarios:** None defined

---

## Panel Blocking Analysis

### Panels Currently BOUND (1)

| Panel | Capabilities Required | All OBSERVED? |
|-------|----------------------|---------------|
| POL-PR-PP-O2 | APPROVE, REJECT | YES |

### Panels Currently DRAFT (5)

| Panel | Capabilities Required | Missing |
|-------|----------------------|---------|
| INC-AI-OI-O2 | ACKNOWLEDGE | ACKNOWLEDGE |
| INC-AI-ID-O3 | ACKNOWLEDGE, RESOLVE, ADD_NOTE | ALL |
| POL-AP-AR-O3 | ACTIVATE, DEACTIVATE, UPDATE_RULE | ALL |
| POL-AP-BP-O3 | ACTIVATE, DEACTIVATE, UPDATE_THRESHOLD | ALL |
| POL-AP-RL-O3 | ACTIVATE, DEACTIVATE, UPDATE_LIMIT | ALL |

---

## Execution Priority

### P1 — Incident Capabilities (ACKNOWLEDGE, RESOLVE)

**Why First:**
- Most panels blocked by these
- Prerequisite for P2/P3

**Scenario to Run:** SDSR-E2E-003 (Threshold Breach)

**Expected Outcome:**
- ACKNOWLEDGE → OBSERVED
- Potentially ADD_NOTE → OBSERVED

---

### P2 — Note Capability (ADD_NOTE)

**Why Second:**
- Required for INC-AI-ID-O3 full unlock
- May be covered by P1

**Scenario to Run:** Same as P1 or SDSR-EXEC-FAIL-001

---

### P3 — Policy Activation (ACTIVATE, DEACTIVATE)

**Why Third:**
- Blocks 3 policy panels
- Requires approved policy to exist first

**Scenario to Create:** SDSR-POL-ACTIVATE-001

---

### P4 — Policy Update Capabilities

**Why Last:**
- Least critical
- Can be deferred

**Scenarios to Create:**
- SDSR-POL-UPDATE-THRESHOLD-001
- SDSR-POL-UPDATE-LIMIT-001
- SDSR-POL-UPDATE-RULE-001

---

## Scenario Execution Plan

| Order | Scenario | Class | Capabilities Proven | Panels Unlocked |
|-------|----------|-------|---------------------|-----------------|
| 1 | SDSR-E2E-003 | THRESHOLD_BREACH | ACKNOWLEDGE, ADD_NOTE | INC-AI-OI-O2 |
| 2 | SDSR-E2E-005 | SUCCESSFUL_EXECUTION | (INFO validation) | LOG-ET-TD-* |
| 3 | SDSR-POL-ACTIVATE-001 (NEW) | POLICY_ACTIVATION | ACTIVATE, DEACTIVATE | POL-AP-*-O3 |
| 4 | SDSR-THRESH-NEAR-001 (NEW) | NEAR_VIOLATION | (none - proves selectivity) | None |
| 5 | SDSR-EXEC-FAIL-001 (NEW) | FAILED_EXECUTION | RESOLVE | INC-AI-ID-O3 |

---

## Capability Inference Rules (Unchanged)

```python
# In Scenario_SDSR_output.py
CAPABILITY_ACCEPTANCE_CRITERIA = {
    ("policy_proposal", "status", "PENDING", "APPROVED"): "APPROVE",
    ("policy_proposal", "status", "PENDING", "REJECTED"): "REJECT",
    ("incident", "status", "OPEN", "ACKNOWLEDGED"): "ACKNOWLEDGE",
    ("incident", "status", "ACKNOWLEDGED", "RESOLVED"): "RESOLVE",
    ("policy_rule", "is_active", False, True): "ACTIVATE",
    ("policy_rule", "is_active", True, False): "DEACTIVATE",
    # ... etc
}
```

Aurora reads `capabilities_observed` from SDSR.
Aurora **never** infers capabilities.

---

## Related Documents

- [SDSR_SCENARIO_TAXONOMY.md](SDSR_SCENARIO_TAXONOMY.md) - Scenario classes
- [SDSR_PIPELINE_CONTRACT.md](SDSR_PIPELINE_CONTRACT.md) - Pipeline mechanics

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-11 | Initial coverage matrix |

---

**END OF MATRIX**
