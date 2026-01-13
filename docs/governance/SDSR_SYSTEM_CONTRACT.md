# SDSR System Contract

**Status:** LOCKED
**Effective:** 2026-01-09
**Authority:** Founder-approved, immutable without explicit approval
**Reference:** PIN-370, PIN-379
**Foundation:** AOS Execution Integrity Contract v1.0 (Layer 0)

---

## 0. Foundation Compliance

This contract derives from and complies with the **AOS Execution Integrity Contract** (Layer 0).

| Foundation Principle | SDSR Compliance |
|----------------------|-----------------|
| P1_CAPTURE_ALL | All runs captured via inject_synthetic.py |
| P2_INTEGRITY_OVER_COMPLETENESS | Missing data explicit via explicit_absence |
| P3_NO_FABRICATED_CERTAINTY | Effects come from engines, not scenarios |

**Reference:** `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml`

---

## 1. Purpose

This document defines the **execution law** for Scenario-Driven System Realization (SDSR).
It is not guidance. It is not a best practice. It is **the contract**.

Claude must reference this contract, never re-derive it.

---

## 2. Core Principle (Non-Negotiable)

> **Scenarios inject causes. Engines create effects. UI reveals truth.**

If downstream state appears without an engine creating it → **the system is lying**.

---

## 3. inject_synthetic.py Authority

`inject_synthetic.py` is the **ONLY** allowed scenario realization entry point.

### 3.1 What It Does

- Parses scenario YAML
- Creates preconditions (tenant, api_key, agent)
- Creates runs with `status="queued"`
- Triggers real worker execution
- Cleans up by `synthetic_scenario_id`

### 3.2 What It NEVER Does

- Write to engine-owned tables
- Simulate causality
- Bypass worker execution
- Create "helpful" shortcuts

### 3.3 Exit Codes (Contract v1.0)

| Code | Meaning |
|------|---------|
| 0 | Inputs created + execution triggered |
| 1 | Validation failure |
| 2 | Partial write (rollback) |
| 3 | Forbidden write (guardrail violation) |

---

## 4. Table Ownership (HARD BOUNDARY)

### 4.1 Scenario-Writable Tables

These tables may be written by `inject_synthetic.py`:

| Table | Owner |
|-------|-------|
| tenants | inject_synthetic.py |
| api_keys | inject_synthetic.py |
| agents | inject_synthetic.py |
| runs | inject_synthetic.py |

All rows MUST include:
- `is_synthetic = true`
- `synthetic_scenario_id = <scenario_id>`

### 4.2 Engine-Owned Tables (FORBIDDEN)

These tables are created by backend engines, **NEVER** by scenarios:

| Table | Owner Engine |
|-------|--------------|
| aos_traces | TraceStore (worker runner) |
| aos_trace_steps | TraceStore (worker runner) |
| incidents | IncidentEngine |
| policy_proposals | PolicyProposalEngine |
| prevention_records | PolicyEngine |
| policy_rules | PolicyEngine |

**Any script writing to these tables is a HARD VIOLATION.**

Exit code 3 is triggered. No exceptions.

---

## 5. Engine Responsibility Matrix

| Cause | Effect | Responsible Engine |
|-------|--------|-------------------|
| Run created | Trace started | TraceStore |
| Step executed | Trace step recorded | TraceStore |
| Run failed | Incident created | IncidentEngine |
| Incident created (HIGH/CRITICAL) | Proposal created | PolicyProposalEngine |
| Proposal approved | Policy rule created | PolicyEngine |
| Policy violated | Prevention record | PolicyEngine |

If any effect is missing when the cause exists → **the engine is broken**, not the scenario.

---

## 6. Scenario Rules

### 6.1 Scenarios Define Inputs Only

```yaml
# CORRECT - defines cause
steps:
  - action: create_run
    data:
      status: queued
      failure_code: EXECUTION_TIMEOUT

# WRONG - defines effect
steps:
  - action: create_incident  # FORBIDDEN
```

### 6.2 Scenarios Never Define Outputs

Scenarios may have `expected_propagation` sections for **validation**, but these are:
- Read-only assertions
- Verified by querying canonical tables
- Never written by the scenario

### 6.3 Cross-Domain Behavior

Scenarios MUST NOT simulate cross-domain behavior.

If a failed run does NOT create an incident:
- The scenario is correct
- The UI is correct
- **The IncidentEngine is broken**

---

## 7. Claude Session Rules

Claude MUST:
- Reference this contract, never re-derive it
- Treat inject_synthetic.py contract as immutable
- Never create new tables or APIs without explicit user approval
- Fix canonical structures, not fork them
- Stop and ask when unsure

Claude MUST NOT:
- Simulate system behavior in scripts
- Create shortcut UI-only flows
- Invent transitional or "temporary" paths
- Write to engine-owned tables from any script
- Bypass L2.1 → projection → UI pipeline

---

## 8. STOP-AND-ASK Rule

Claude MUST pause and ask for approval when:

1. Need to create a new table
2. Need to add a new API
3. Need to bypass L2.1 → projection → UI pipeline
4. Need to write data that an engine should generate
5. Need to modify this contract

When this happens, Claude must respond with:

```
SDSR CONTRACT CHECK

1. Problem: [what I need to do]
2. Why canonical structure is insufficient: [reason]
3. Options:
   A. [option with tradeoffs]
   B. [option with tradeoffs]
   C. [option with tradeoffs]
4. Recommendation: [which option and why]
5. Question: [explicit yes/no question]
```

**No implementation before approval.**

---

## 9. Violation Handling

| Violation | Response |
|-----------|----------|
| Script writes to engine-owned table | Exit code 3, abort |
| Scenario defines effects | Validation failure |
| Claude bypasses pipeline | Session blocked |
| New table without approval | Hard stop |
| New API without approval | Hard stop |

---

## 10. Contract Evolution

This contract may only be modified by:
1. Founder explicit approval
2. Documented in a PIN
3. Updated in this file
4. Claude informed of the change

Silent modifications are FORBIDDEN.

---

## Related Documents

### Foundation (Layer 0)

- [AOS_EXECUTION_INTEGRITY_CONTRACT.yaml](../contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml) - **Foundational contract (Layer 0)**
- [PIN-403](../memory-pins/PIN-403-aos-execution-integrity-contract.md) - Execution Integrity Contract PIN

### SDSR Governance

- [PIN-370](../memory-pins/PIN-370-sdsr-scenario-driven-system-realization.md) - SDSR Foundation
- [PIN-379](../memory-pins/PIN-379-sdsr-e2e-pipeline-gap-closure.md) - E2E Pipeline & Gap Closure
- [PIN-396](../memory-pins/PIN-396-sdsr-scenario-coverage-matrix-locked.md) - SDSR Scenario Coverage Matrix
- [SDSR_SCENARIO_COVERAGE_MATRIX.md](SDSR_SCENARIO_COVERAGE_MATRIX.md) - Scenario Coverage Matrix
- [gap_registry.yaml](../../design/gaps/gap_registry.yaml) - Gap Taxonomy
