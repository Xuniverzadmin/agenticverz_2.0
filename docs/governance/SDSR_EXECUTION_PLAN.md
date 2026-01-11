# SDSR Execution Plan

**Status:** ACTIVE
**Effective:** 2026-01-11
**Reference:** SDSR_SCENARIO_TAXONOMY.md, SDSR_CAPABILITY_COVERAGE_MATRIX.md, PIN-395

---

## Current State

| Metric | Value |
|--------|-------|
| Scenarios Defined | 5 |
| Scenarios Passed | 1 (SDSR-E2E-004) |
| Scenarios Revoked | 1 (SDSR-E2E-001) |
| Scenarios Pending | 3 |
| Capabilities OBSERVED | 2 |
| Capabilities DISCOVERED | 8 |
| Panels BOUND | 1 |
| Panels DRAFT | 5 |

---

## Execution Order (Brutally Practical)

### Phase 1: Incident Capabilities

**Goal:** Unlock incident management panels

**Scenario:** SDSR-E2E-003 (Threshold Breach)

**Run Command:**
```bash
# Step 1: Run scenario
python3 backend/scripts/sdsr/inject_synthetic.py --scenario SDSR-E2E-003 --wait

# Step 2: Process observation
./scripts/tools/sdsr_observation_watcher.sh

# Step 3: Verify
curl https://preflight-console.agenticverz.com/precus/incidents
```

**Expected Capabilities:**
- ACKNOWLEDGE → OBSERVED
- ADD_NOTE → OBSERVED (if scenario covers it)

**Expected Panel State Changes:**
- INC-AI-OI-O2: DRAFT → BOUND (if ACKNOWLEDGE proven)

---

### Phase 2: Worker Execution Validation

**Goal:** Validate trace generation and success path

**Scenario:** SDSR-E2E-005 (Successful Worker Execution)

**Run Command:**
```bash
python3 backend/scripts/sdsr/inject_synthetic.py --scenario SDSR-E2E-005 --wait
./scripts/tools/sdsr_observation_watcher.sh
```

**Expected Capabilities:**
- None with action buttons (INFO panels only)

**Expected Outcome:**
- Validates trace chain is real
- LOG-ET-TD-* panels show real data

---

### Phase 3: Policy Activation

**Goal:** Unlock policy management panels

**Scenario:** SDSR-POL-ACTIVATE-001 (NEW - must create)

**Scenario Definition:**
```yaml
scenario_id: SDSR-POL-ACTIVATE-001
name: Policy Rule Activation Lifecycle
class: POLICY_ACTIVATION
execution_mode: non_executable

stimulus:
  type: synthetic_only
  injected_entities:
    - entity: policy_rule
      fields:
        is_active: false
        rule_type: BUDGET_LIMIT

expected_real_effects:
  db_changes:
    - table: policy_rules
      field: is_active
      from: false
      to: true

capabilities_to_prove:
  - ACTIVATE
  - DEACTIVATE

panels_affected:
  - POL-AP-AR-O3
  - POL-AP-BP-O3
  - POL-AP-RL-O3
```

**Expected Capabilities:**
- ACTIVATE → OBSERVED
- DEACTIVATE → OBSERVED

---

### Phase 4: Selectivity Proof (Negative Test)

**Goal:** Prove system doesn't unlock buttons incorrectly

**Scenario:** SDSR-THRESH-NEAR-001 (NEW - must create)

**Scenario Definition:**
```yaml
scenario_id: SDSR-THRESH-NEAR-001
name: Near-Violation Does Not Trigger Incident
class: NEAR_VIOLATION
execution_mode: non_executable

stimulus:
  type: synthetic_only
  injected_entities:
    - entity: run
      fields:
        cost_usd: 9.99  # Threshold is 10.00

expected_real_effects:
  db_changes:
    - table: incidents
      assertion: no_row_created  # CRITICAL
  warnings:
    - type: threshold_warning
      logged: true

capabilities_to_prove: []  # NONE - this is the point

observation_class: INFRASTRUCTURE
```

**Expected Capabilities:**
- NONE (observation_class = INFRASTRUCTURE)

**Purpose:** Proves SDSR correctly identifies when capabilities are NOT proven.

---

### Phase 5: Resolve Capability

**Goal:** Complete incident lifecycle

**Scenario:** SDSR-EXEC-FAIL-001 (Rewrite of revoked E2E-001)

**Expected Capabilities:**
- RESOLVE → OBSERVED

**Expected Panel State Changes:**
- INC-AI-ID-O3: DRAFT → BOUND

---

## Scenario Readiness Checklist

| Scenario | Defined | Valid | Run | Passed |
|----------|---------|-------|-----|--------|
| SDSR-E2E-001 | YES | NO (REVOKED) | - | - |
| SDSR-E2E-002 | YES | YES | NO | - |
| SDSR-E2E-003 | YES | YES | NO | - |
| SDSR-E2E-004 | YES | YES | YES | **YES** |
| SDSR-E2E-005 | YES | YES | NO | - |
| SDSR-POL-ACTIVATE-001 | NO | - | - | - |
| SDSR-THRESH-NEAR-001 | NO | - | - | - |
| SDSR-EXEC-FAIL-001 | NO | - | - | - |

---

## Immediate Next Action

**Run SDSR-E2E-003:**

```bash
cd /root/agenticverz2.0

# Ensure DB_AUTHORITY is set
export DB_AUTHORITY=neon

# Run the scenario
python3 backend/scripts/sdsr/inject_synthetic.py --scenario SDSR-E2E-003 --wait

# Process the observation
./scripts/tools/sdsr_observation_watcher.sh

# Check capability registry
cat backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_ACKNOWLEDGE.yaml | grep status
```

---

## Success Criteria (End State)

| Capability | Target Status | Scenario Required |
|------------|---------------|-------------------|
| APPROVE | OBSERVED | SDSR-E2E-004 ✓ |
| REJECT | OBSERVED | SDSR-E2E-004 ✓ |
| ACKNOWLEDGE | OBSERVED | SDSR-E2E-003 |
| RESOLVE | OBSERVED | SDSR-EXEC-FAIL-001 |
| ADD_NOTE | OBSERVED | SDSR-E2E-003 |
| ACTIVATE | OBSERVED | SDSR-POL-ACTIVATE-001 |
| DEACTIVATE | OBSERVED | SDSR-POL-ACTIVATE-001 |
| UPDATE_* | OBSERVED | Phase 5+ |

---

## Panel End State

| Panel | Current | Target | Blocked By |
|-------|---------|--------|------------|
| POL-PR-PP-O2 | BOUND | BOUND | - |
| INC-AI-OI-O2 | DRAFT | BOUND | ACKNOWLEDGE |
| INC-AI-ID-O3 | DRAFT | BOUND | ACKNOWLEDGE, RESOLVE, ADD_NOTE |
| POL-AP-AR-O3 | DRAFT | BOUND | ACTIVATE, DEACTIVATE |
| POL-AP-BP-O3 | DRAFT | BOUND | ACTIVATE, DEACTIVATE |
| POL-AP-RL-O3 | DRAFT | BOUND | ACTIVATE, DEACTIVATE |

---

## Timeline (No Dates, Just Order)

1. Run SDSR-E2E-003 → ACKNOWLEDGE + ADD_NOTE
2. Run SDSR-E2E-005 → Trace validation
3. Create + Run SDSR-POL-ACTIVATE-001 → ACTIVATE + DEACTIVATE
4. Create + Run SDSR-THRESH-NEAR-001 → Selectivity proof
5. Create + Run SDSR-EXEC-FAIL-001 → RESOLVE

After Step 3: **All 5 DRAFT panels can become BOUND**

---

## Related Documents

- [SDSR_SCENARIO_TAXONOMY.md](SDSR_SCENARIO_TAXONOMY.md)
- [SDSR_CAPABILITY_COVERAGE_MATRIX.md](SDSR_CAPABILITY_COVERAGE_MATRIX.md)
- [SDSR_PIPELINE_CONTRACT.md](SDSR_PIPELINE_CONTRACT.md)

---

**END OF PLAN**
