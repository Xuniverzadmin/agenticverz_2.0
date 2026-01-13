# PIN-403: AOS Execution Integrity Contract

**Status:** FOUNDATIONAL
**Created:** 2026-01-12
**Category:** Governance / Contracts / Layer 0
**Milestone:** Phase G Steady State

---

## Summary

Established the AOS Execution Integrity Contract v1.0 - the foundational Layer 0 contract that defines minimum truth guarantees for all LLM, agent, and human-initiated executions. All higher-level governance (SDSR, Aurora, policies, UI) must derive from this foundation.

---

## Contract Location

| File | Format | Purpose |
|------|--------|---------|
| `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml` | YAML | Source of truth |
| `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.json` | JSON | Derived (machine-parseable) |

---

## Core Principles (Constitutional)

| ID | Principle | Enforcement |
|----|-----------|-------------|
| **P1_CAPTURE_ALL** | Every execution attempt must result in a Run Record. Silence is a violation. | HARD BLOCK |
| **P2_INTEGRITY_OVER_COMPLETENESS** | The system must not assume complete visibility. Missing data must be explicitly represented. | HARD BLOCK |
| **P3_NO_FABRICATED_CERTAINTY** | Absence of evidence must never be interpreted as success. | HARD BLOCK |

---

## Canonical Statement

> **We capture everything we can. We never pretend to capture everything. We make the difference visible.**

---

## What This Contract Guarantees

The system **does** promise:

- To capture reality as completely as possible
- To make uncertainty explicit
- To ensure integrity of what *is* captured
- To never fabricate certainty

The system **does not** promise:

- Perfect visibility
- Zero blind spots
- Correct judgments from day one

---

## Run Definition (Canonical)

A **Run** is:

> Any attempt by a human, agent, or system to invoke an LLM or LLM-backed capability that could produce an effect.

This includes:

- Successful calls
- Failed calls
- Retries
- Partial responses
- Blocked or rejected attempts
- Streaming or non-streaming calls

**Invariant:** If something was attempted, it is a Run.

---

## Execution Capture Contract (v1.1 - PIN-407 Correction)

**CORE PRINCIPLE:** Every execution produces a complete governance footprint. Success is data, not silence.

### What Every Run MUST Produce

| Category | Mandatory | Description |
|----------|-----------|-------------|
| **Activity** | YES | A run is itself an activity record |
| **Incident** | YES | Incident with outcome: SUCCESS, FAILURE, PARTIAL, BLOCKED |
| **Policy** | YES | Policy evaluation: NO_VIOLATION, VIOLATION, ADVISORY, NOT_APPLICABLE |
| **Logs** | YES | Entry + exit logs correlated by run_id |
| **Traces** | YES | Trace + steps finalized as COMPLETE or ABORTED |

### Critical Correction

**Wrong mental model:**
> "A run *might* produce activity / incident / policy"

**Correct mental model:**
> A run IS a first-class activity that ALWAYS produces:
> - Activity record
> - Incident outcome
> - Policy outcome
> - Logs
> - Traces

**What varies:** Classification and content
**What does NOT vary:** Existence

### Success as First-Class Data

A "success incident" is **still an incident**:
- It asserts NO harm, NO violation
- It is EVIDENCE, not absence

If success records are missing → **capture failure**, not "nothing to capture"

### Consequences of Violation

If you DON'T capture success as data:
- "Success" becomes indistinguishable from "nothing happened"
- Cannot learn from success patterns
- Cannot derive preventive policies
- Cannot show regulators WHY something was safe
- SDSR loses half its value

---

## Layering Model

| Layer | Name | Description | Judgment |
|-------|------|-------------|----------|
| **0** | Runs | Raw truth - everything captured | None |
| 1 | Notability | Hypothesis - potentially interesting runs | Tentative |
| 2 | Incidents | Committed memory - explicitly promoted | Explicit |
| 3 | Policies | Governance - human or system-approved | Enforceable |

**This contract governs Layer 0 only. Higher layers may never bypass it.**

---

## Forbidden Behaviors (Hard Violations)

| ID | Behavior | Description |
|----|----------|-------------|
| FB_001 | silent_run_drop | Dropping runs silently |
| FB_002 | infer_success_from_absence | Inferring success from absence of failure |
| FB_003 | treat_missing_as_clean | Treating missing telemetry as "clean" |
| FB_004 | incident_without_run | Generating incidents without Run Records |
| FB_005 | policy_without_evidence | Generating policies without traceable Run evidence |

---

## SDSR Verification Mapping

| SDSR Checklist Item | Verified By |
|---------------------|-------------|
| No silent failures | `P1_CAPTURE_ALL` |
| Explicit uncertainty | `explicit_absence` |
| Observation integrity | `integrity_model` |
| No fake inference | `P3_NO_FABRICATED_CERTAINTY` |
| Upstream truth only | `layer_0` |
| Aurora never assumes | `guarantees.downstream` |

---

## Integrity Model

### Expectations

| ID | Condition | Requires |
|----|-----------|----------|
| EXPECT_RESPONSE | response_expected == true | response_received == true |
| EXPECT_TRACE | trace_expected == true | trace_received == true |

### Integrity Events

When expectations are violated, the system emits an **Observability Integrity Event**:

- NOT an incident by default
- NOT a policy violation
- A statement of uncertainty

---

## Agent Instructions (Claude / Others)

When reasoning about executions, governance, incidents, or policies:

1. **Always start from Run Records**
2. **Never assume absence means success**
3. **Treat missing data as a signal**
4. **Defer judgment if integrity is low**

If integrity is uncertain, the correct action is:

> "Surface uncertainty, not confidence."

---

## Guarantees to Downstream Systems

By adhering to this contract, the system guarantees:

- All observed effects trace back to Runs
- Missing data is explicit
- Confidence is computable
- Trust can be graded, not assumed

Downstream systems (SDSR, Aurora, UI) must:

- Respect uncertainty
- Avoid over-inference
- Surface integrity gaps honestly

---

## Related Documents

| Document | Location |
|----------|----------|
| Contract (YAML) | `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml` |
| Contract (JSON) | `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.json` |
| Contracts INDEX | `docs/contracts/INDEX.md` |
| SDSR System Contract | `docs/governance/SDSR_SYSTEM_CONTRACT.md` |
| SDSR Scenario Coverage Matrix | `docs/governance/SDSR_SCENARIO_COVERAGE_MATRIX.md` |

---


---

## Index Entry

### Update (2026-01-12)

Added to INDEX.md on 2026-01-12

## Related PINs

- [PIN-396](PIN-396-sdsr-scenario-coverage-matrix-locked.md) - SDSR Scenario Coverage Matrix
- [PIN-394](PIN-394-sdsr-aurora-one-way-causality-pipeline.md) - Aurora One-Way Causality Pipeline
- [PIN-393](PIN-393-sdsr-observation-class-mechanical-discriminator.md) - Observation Class Discriminator
- [PIN-370](PIN-370-sdsr-activity-incident-lifecycle.md) - SDSR Activity/Incident Lifecycle

---

*This PIN establishes a foundational contract. All higher-level governance must cite and comply with it.*
