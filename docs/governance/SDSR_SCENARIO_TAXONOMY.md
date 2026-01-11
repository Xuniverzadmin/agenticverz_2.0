# SDSR Scenario Taxonomy (AUTHORITATIVE)

**Status:** LOCKED
**Effective:** 2026-01-11
**Authority:** System Design Document
**Reference:** PIN-395

---

## Core Principle (Non-Negotiable)

> **Only the stimulus is synthetic.
> All effects, errors, traces, policies, incidents, logs, and side-effects must be REAL.**

If a scenario does not:
- Hit real DB tables
- Trigger real workers / validators / guards
- Produce real logs, incidents, or policy transitions

...it **does not count** and must not produce OBSERVED capabilities.

---

## Scenario Class Taxonomy

### I. EXECUTION OUTCOME SCENARIOS

These verify: *Can the system execute work and survive reality?*

---

#### Class 1: SUCCESSFUL_EXECUTION (Clean Path)

**ID Pattern:** `SDSR-EXEC-SUCCESS-*`

**What's Injected:**
- Synthetic task / request / intent

**What Must Be Real:**
- Worker execution
- Logs
- Traces
- Metrics
- No incidents created

**Capabilities Proven:**
- EXECUTE
- TRACE
- LOG_ACCESS (read-only, INFO panels)

**Existing Scenario:** SDSR-E2E-005 (NOT YET RUN)

**Panels Unlocked:** LOG-ET-TD-*, ACT-EX-*

---

#### Class 2: FAILED_EXECUTION (Hard Failure)

**ID Pattern:** `SDSR-EXEC-FAIL-*`

**What's Injected:**
- Task guaranteed to fail (invalid input, timeout, dependency down)

**What Must Be Real:**
- Error logs
- Incident created
- Policy evaluation triggered

**Capabilities Proven:**
- ACKNOWLEDGE (incident)
- ADD_NOTE
- TRACE
- VIEW_FAILURE_CONTEXT

**Existing Scenario:** SDSR-E2E-001 (REVOKED - needs rewrite)

**Panels Unlocked:** INC-AI-*, LOG-ET-*

---

#### Class 3: PARTIAL_SUCCESS (Degraded Execution)

**ID Pattern:** `SDSR-EXEC-PARTIAL-*`

**What's Injected:**
- Task with mixed outcomes (one step succeeds, next fails)

**What Must Be Real:**
- Logs + warnings
- Incident with LOW/MEDIUM severity
- No policy block

**Capabilities Proven:**
- ACKNOWLEDGE
- RESOLVE (low severity)
- ADD_NOTE

**Critical:** This proves you don't binary-think.

**Existing Scenario:** None

**Panels Unlocked:** INC-AI-ID-O3 (partial)

---

### II. THRESHOLD & VIOLATION SCENARIOS

These verify: *Does the system enforce governance?*

---

#### Class 4: NEAR_VIOLATION (Threshold Not Crossed)

**ID Pattern:** `SDSR-THRESH-NEAR-*`

**What's Injected:**
- Repeated risky behavior just below threshold

**What Must Be Real:**
- Counters increment
- Warnings logged
- NO incident
- NO policy action

**Capabilities Proven:**
- VIEW_THRESHOLD
- TRACE
- AUDIT_ONLY (no action buttons)

**Critical:** This scenario **must NOT** unlock action buttons.

**Existing Scenario:** None

**Panels Unlocked:** None (proves selectivity)

---

#### Class 5: THRESHOLD_BREACH (Incident Triggered)

**ID Pattern:** `SDSR-THRESH-BREACH-*`

**What's Injected:**
- Same as Class 4, one more step

**What Must Be Real:**
- Incident OPENED
- Severity computed
- Policy proposal generated

**Capabilities Proven:**
- ACKNOWLEDGE
- ADD_NOTE

**Existing Scenario:** SDSR-E2E-003 (NOT YET RUN)

**Panels Unlocked:** INC-AI-OI-O2, INC-AI-ID-O3

---

#### Class 6: AUTO_POLICY_ACTION (Severe Violation)

**ID Pattern:** `SDSR-THRESH-AUTO-*`

**What's Injected:**
- Severe or repeated violation

**What Must Be Real:**
- Policy auto-ACTIVATED or DEACTIVATED
- Incident escalated

**Capabilities Proven:**
- ACTIVATE
- DEACTIVATE
- RESOLVE

**Critical:** Must use real policy evaluators.

**Existing Scenario:** None

**Panels Unlocked:** POL-AP-*-O3

---

### III. POLICY LIFECYCLE SCENARIOS

These verify: *Can humans govern the system?*

---

#### Class 7: HUMAN_APPROVAL

**ID Pattern:** `SDSR-POL-APPROVE-*`

**What's Injected:**
- Proposal that should be approved

**What Must Be Real:**
- Proposal APPROVED
- Policy rule created
- Prevention record written

**Capabilities Proven:**
- APPROVE

**Existing Scenario:** SDSR-E2E-004 (PASSED)

**Panels Unlocked:** POL-PR-PP-O2 (partial)

---

#### Class 8: HUMAN_REJECTION

**ID Pattern:** `SDSR-POL-REJECT-*`

**What's Injected:**
- Proposal that should be rejected

**What Must Be Real:**
- Proposal REJECTED
- Incident persists or escalates
- No policy rule created

**Capabilities Proven:**
- REJECT
- ADD_NOTE
- ESCALATE (if applicable)

**Critical:** Different downstream effects than approval.

**Existing Scenario:** SDSR-E2E-004 (PASSED - covers REJECT)

**Panels Unlocked:** POL-PR-PP-O2

---

#### Class 9: POLICY_ACTIVATION

**ID Pattern:** `SDSR-POL-ACTIVATE-*`

**What's Injected:**
- Approved policy with activation condition met

**What Must Be Real:**
- Policy state changes
- System behavior changes (even minimally)

**Capabilities Proven:**
- ACTIVATE
- DEACTIVATE

**Existing Scenario:** None

**Panels Unlocked:** POL-AP-AR-O3, POL-AP-BP-O3, POL-AP-RL-O3

---

### IV. TRACEABILITY & AUDIT SCENARIOS

These verify: *Can you prove what happened?*

---

#### Class 10: FULL_TRACE_CHAIN

**ID Pattern:** `SDSR-TRACE-FULL-*`

**What's Injected:**
- Task with multiple hops (agent → tool → DB → policy)

**What Must Be Real:**
- Correlated trace IDs
- Logs tied to execution
- Incident references trace

**Capabilities Proven:**
- TRACE
- VIEW_EXECUTION_GRAPH

**Unlocks:** Debug panels, not action buttons.

**Existing Scenario:** None (covered partially by SDSR-E2E-005)

**Panels Unlocked:** LOG-ET-TD-O3, LOG-ET-TD-O4

---

#### Class 11: TRACE_GAP_DETECTION (Negative Proof)

**ID Pattern:** `SDSR-TRACE-GAP-*`

**What's Injected:**
- Task that bypasses tracing accidentally

**What Must Be Real:**
- Detection of missing trace
- Audit warning or incident

**Capabilities Proven:**
- TRACE_GAP_DETECTED

**Critical:** Proves you detect your own blind spots.

**Existing Scenario:** None

**Panels Unlocked:** Audit panels

---

### V. ACTOR DIFFERENTIATION SCENARIOS

These verify: *Do you know WHO did it?*

---

#### Class 12: HUMAN_ACTION_PATH

**ID Pattern:** `SDSR-ACTOR-HUMAN-*`

**What's Injected:**
- UI-triggered action (approve, acknowledge)

**What Must Be Real:**
- Auth context = human
- Audit trail with human identity

**Capabilities Proven:**
- APPROVE (human context)
- ACKNOWLEDGE (human context)

**Existing Scenario:** SDSR-E2E-004 (implicitly human)

**Panels Unlocked:** All human-approval panels

---

#### Class 13: AGENT_ACTION_PATH

**ID Pattern:** `SDSR-ACTOR-AGENT-*`

**What's Injected:**
- Agent-triggered equivalent action

**What Must Be Real:**
- Agent identity
- Different policy checks
- Possibly stricter thresholds

**Capabilities Proven:**
- APPROVE (agent context)
- EXECUTE (agent context)

**Critical:** Same capability name, different evidence.

**Existing Scenario:** None

**Panels Unlocked:** None (differentiates audit, not UI)

---

## Scenario Definition Schema

Every scenario MUST declare:

```yaml
scenario_id: SDSR-{CLASS}-{VARIANT}-{SEQ}
name: Human-readable description
class: EXECUTION | THRESHOLD | POLICY | TRACE | ACTOR
subclass: SUCCESS | FAIL | PARTIAL | NEAR | BREACH | AUTO | etc.

stimulus:
  type: synthetic_only
  injected_entities:
    - entity: run
      fields: {status: queued, ...}

expected_real_effects:
  db_changes:
    - table: incidents
      assertion: row_created
  incidents:
    - severity: HIGH
      type: EXECUTION_FAILURE
  policies:
    - action: proposal_generated
  logs:
    - level: ERROR
      contains: "failure_code"
  traces:
    - status: completed
      step_count: ">= 1"

forbidden_shortcuts:
  - no_direct_registry_writes
  - no_fake_logs
  - no_simulated_incidents

capabilities_to_prove:
  - ACKNOWLEDGE
  - ADD_NOTE

panels_affected:
  - INC-AI-OI-O2
  - INC-AI-ID-O3
```

---

## Class Coverage Matrix

| Class | ID Pattern | Execution Mode | Real Effects Required |
|-------|------------|----------------|----------------------|
| 1. SUCCESSFUL_EXECUTION | SDSR-EXEC-SUCCESS-* | WORKER_EXECUTION | traces, logs, no incidents |
| 2. FAILED_EXECUTION | SDSR-EXEC-FAIL-* | WORKER_EXECUTION | traces, logs, incidents |
| 3. PARTIAL_SUCCESS | SDSR-EXEC-PARTIAL-* | WORKER_EXECUTION | traces, logs, low-severity incident |
| 4. NEAR_VIOLATION | SDSR-THRESH-NEAR-* | STATE_INJECTION | warnings, NO incidents |
| 5. THRESHOLD_BREACH | SDSR-THRESH-BREACH-* | STATE_INJECTION | incidents, proposals |
| 6. AUTO_POLICY_ACTION | SDSR-THRESH-AUTO-* | STATE_INJECTION | policy state change |
| 7. HUMAN_APPROVAL | SDSR-POL-APPROVE-* | STATE_INJECTION | proposal → approved |
| 8. HUMAN_REJECTION | SDSR-POL-REJECT-* | STATE_INJECTION | proposal → rejected |
| 9. POLICY_ACTIVATION | SDSR-POL-ACTIVATE-* | STATE_INJECTION | policy active/inactive |
| 10. FULL_TRACE_CHAIN | SDSR-TRACE-FULL-* | WORKER_EXECUTION | correlated traces |
| 11. TRACE_GAP_DETECTION | SDSR-TRACE-GAP-* | WORKER_EXECUTION | gap detected |
| 12. HUMAN_ACTION_PATH | SDSR-ACTOR-HUMAN-* | API_CALL | human audit trail |
| 13. AGENT_ACTION_PATH | SDSR-ACTOR-AGENT-* | API_CALL | agent audit trail |

---

## Forbidden Shortcuts (Violations)

The following are **explicit violations** of SDSR law:

| Shortcut | Why Forbidden |
|----------|---------------|
| Injecting incidents directly | Incidents are EFFECTS, not stimuli |
| Injecting policy rules directly | Rules are EFFECTS of approval |
| Injecting traces directly | Traces are EFFECTS of execution |
| Faking worker execution | Worker must actually run |
| Writing to capability registry from scenario | Aurora writes, SDSR observes |
| Creating "passing" scenarios that don't hit real tables | Fake progress |

---

## Related Documents

- [SDSR_PIPELINE_CONTRACT.md](SDSR_PIPELINE_CONTRACT.md) - Pipeline mechanics
- [SDSR_SYSTEM_CONTRACT.md](SDSR_SYSTEM_CONTRACT.md) - Core principles
- [CAPABILITY_STATUS_MODEL.yaml](../../backend/AURORA_L2_CAPABILITY_REGISTRY/CAPABILITY_STATUS_MODEL.yaml) - Lifecycle

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-11 | Initial taxonomy locked (13 classes) |

---

**END OF TAXONOMY**
