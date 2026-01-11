# SDSR PIPELINE CONTRACT (AUTHORITATIVE)

**Status:** Active
**Scope:** SDSR execution, observation, and downstream propagation
**Applies to:** `sdsr_e2e_orchestrator.py`, `inject_synthetic.py`, `sdsr_observation_watcher.sh`, SDSR output & AURORA integration
**Last updated:** 2026-01-11 (v3 - One-Way Causality Architecture)
**Reference:** PIN-391, PIN-392, PIN-394, SDSR_SYSTEM_CONTRACT.md

---

## 1. Purpose

This document defines the **canonical SDSR pipeline**, authority boundaries, and execution contracts.

Its goals are to:

* Prevent silent SDSR failures
* Enforce separation of orchestration vs injection
* Ensure SDSR observes **system truth**, not invented semantics
* Make downstream behavior (AURORA / UI) mechanically reliable

This document is **binding**.

---

## 2. Canonical SDSR Pipeline

### 2.1 High-Level Flow (One-Way Causality)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        SDSR LAYER (Upstream)                               │
│                                                                            │
│  inject_synthetic.py --wait                                                │
│    ├─ inject synthetic context                                             │
│    ├─ trigger real execution                                               │
│    ├─ observe canonical backend truth                                      │
│    ├─ materialize SDSR truth (Scenario_SDSR_output.py)                    │
│    └─ emit .sdsr_observation_ready signal  ◄── ONLY DOWNSTREAM OUTPUT     │
│                                                                            │
│  DOES NOT: Call Aurora scripts directly (violates one-way causality)      │
└────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ signal file

┌────────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (Downstream)                        │
│                                                                            │
│  sdsr_observation_watcher.sh                                               │
│    ├─ detects .sdsr_observation_ready signal                               │
│    ├─ calls AURORA_L2_apply_sdsr_observations.py                          │
│    │     └─ apply observation to capability registry                       │
│    │     └─ emit .aurora_needs_preflight_recompile signal                 │
│    ├─ calls run_aurora_l2_pipeline_preflight.sh                           │
│    │     └─ recompile UI projection                                        │
│    │     └─ deploy to dist-preflight/                                      │
│    └─ clears all signals                                                   │
└────────────────────────────────────────────────────────────────────────────┘
```

Downstream steps **MUST NOT** execute unless the SDSR observation artifact exists.

### 2.2 Signal Files

| Signal | Created By | Consumed By | Contents |
|--------|-----------|-------------|----------|
| `.sdsr_observation_ready` | inject_synthetic.py | sdsr_observation_watcher.sh | observation_path, scenario_id, class, count |
| `.aurora_needs_preflight_recompile` | apply_observations.py | preflight pipeline | trigger source, observation path |

---

## 3. Authority & Responsibility Model

### 3.1 sdsr_e2e_orchestrator.py (TOP-LEVEL ORCHESTRATOR)

**Location:** `scripts/sdsr/sdsr_e2e_orchestrator.py`

**Owns:**

* Scenario lifecycle
* Phase sequencing
* Artifact existence checks
* Downstream triggering
* Exit discipline

**Must:**

* Treat missing artifacts as hard failure
* Fail fast on contract violation
* Trigger downstream steps mechanically

**Must NOT:**

* Inject data
* Wait on workers
* Inspect canonical tables
* Materialize SDSR truth

---

### 3.2 inject_synthetic.py (INJECTOR + TRUTH PRODUCER)

**Location:** `backend/scripts/sdsr/inject_synthetic.py`

**Owns:**

* Synthetic context creation (tenant, agent, api key)
* Run creation
* Waiting for execution
* Observing canonical backend truth
* Truth materialization
* Observation emission
* Signal emission (`.sdsr_observation_ready`)

**Must:**

* Observe canonical tables only
* Materialize truth for **all terminal executions**
* Emit observation artifact when truth exists
* Emit `.sdsr_observation_ready` signal with observation path
* Exit with explicit, meaningful exit codes

**Must NOT:**

* Act as an orchestrator
* **Call Aurora scripts directly** (one-way causality violation)
* Trigger UI pipeline
* Decide end-to-end SDSR success

---

### 3.2.1 sdsr_observation_watcher.sh (DOWNSTREAM ORCHESTRATOR) — NEW

**Location:** `scripts/tools/sdsr_observation_watcher.sh`

**Owns:**

* Detecting `.sdsr_observation_ready` signal
* Triggering downstream Aurora steps
* Triggering preflight compilation
* Clearing all signal files

**Must:**

* Only execute when signal file exists
* Call apply_observations.py with correct observation path
* Call preflight pipeline after successful application
* Clear signals after successful completion
* Support `--dry-run` mode for validation

**Must NOT:**

* Inject data
* Modify observations
* Make decisions about observation validity

---

### 3.3 Scenario_SDSR_output.py (PURE MODEL)

**Location:** `backend/scripts/sdsr/Scenario_SDSR_output.py`

**Owns:**

* SDSR data structures (`ScenarioSDSROutput`)

**Must NOT:**

* Perform I/O
* Perform orchestration
* Perform execution or decision logic

---

### 3.4 SDSR_output_emit_AURORA_L2.py (WITNESS / SERIALIZER)

**Location:** `backend/scripts/sdsr/SDSR_output_emit_AURORA_L2.py`

**Owns:**

* Serialization of SDSR truth
* Writing observation artifact to filesystem

**Must:**

* Be deterministic
* Fail loudly on invalid input

**Must NOT:**

* Decide whether truth exists
* Mutate backend or AURORA directly

---

### 3.5 Downstream Consumers (AURORA / UI)

**Location:** `scripts/tools/AURORA_L2_apply_sdsr_observations.py`, `scripts/tools/run_aurora_l2_pipeline.sh`

**Owns:**

* Capability belief updates
* UI projection compilation

**Must:**

* Act **only if** SDSR observation exists

**Must NOT:**

* Compensate for missing SDSR truth
* Infer success heuristically

---

## 4. inject_synthetic.py — Execution Contract

### 4.1 Inputs

```
--scenario <SCENARIO_ID | PATH>
--wait
--timeout <seconds>
--dry-run (optional)
--case <case_id> (optional)
```

---

### 4.2 Outputs (Hard Guarantees)

Exactly **one** of the following must occur:

#### SUCCESS

* Observation file created:

```
sdsr/observations/SDSR_OBSERVATION_<scenario_id>.json
```

* File contains serialized `ScenarioSDSROutput`
* Exit code = `0`

#### FAILURE

* No observation file
* Exit code ≠ `0`
* Failure reason is explicit

**Silent failure is forbidden.**

---

### 4.3 Exit Codes

| Code | Meaning                                                            |
| ---- | ------------------------------------------------------------------ |
| 0    | Execution + truth materialization + observation emission succeeded |
| 2    | Execution terminal but truth could not be materialized             |
| 3    | Execution did not reach terminal state (timeout / infra)           |
| 4    | Scenario invalid / preconditions failed                            |
| 5    | Internal injector error                                            |

> **Exit code 0 is illegal unless observation exists.**

---

## 5. Truth Materialization Rules

### 5.1 Canonical Truth Sources

* `runs`
* `aos_traces`
* `aos_trace_steps`
* `incidents`
* `policy_proposals`

### 5.2 Mandatory Behavior

* Truth **must** be materialized for **all terminal executions**
* Observation emission may be gated
* Truth materialization may **not** be gated

---

## 6. Status Semantics (Observed, Not Invented)

### 6.1 runs.status (Authoritative)

| Status           | Meaning                  |
| ---------------- | ------------------------ |
| succeeded        | Successful terminal      |
| failed           | Failure terminal         |
| halted           | Controlled stop terminal |
| retry            | Non-terminal             |
| pending_approval | Non-terminal             |
| running          | Non-terminal             |
| queued           | Non-terminal             |

### 6.2 aos_traces.status (Observability Only)

| Status    | Meaning        |
| --------- | -------------- |
| completed | Trace finished |
| failed    | Trace failed   |

### 6.3 SDSR Rule

> SDSR **observes** status vocabulary.
> SDSR **must not impose** its own.

---

## 7. Orchestrator ↔ Injector Handshake

### 7.1 Execution

```bash
python backend/scripts/sdsr/inject_synthetic.py \
  --scenario X.yaml \
  --wait \
  --timeout N
```

### 7.2 Validation (Mandatory)

The orchestrator must verify:

1. Exit code
2. Observation file existence
3. Observation schema validity

Failure of any check **halts the pipeline**.

---

## 8. Downstream Triggering

Downstream steps **must only run** if observation exists:

```
AURORA_L2_apply_sdsr_observations.py
↓
run_aurora_l2_pipeline.sh
```

No manual steps. No heuristics.

---

## 9. Prohibited Anti-Patterns

The following are **explicit violations**:

* inject_synthetic acting as orchestrator
* Truth materialization gated on "PASSED" only
* Observation absence treated as success
* Downstream systems compensating for missing truth
* Status vocabulary hard-coded outside mapping layer

---

## 10. Design Principle (Final)

> **SDSR exists to observe system truth.
> If the system changes, SDSR must adapt — not the other way around.**

---

## 11. Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| This Contract | `docs/governance/SDSR_PIPELINE_CONTRACT.md` | Authority |
| Orchestrator | `scripts/sdsr/sdsr_e2e_orchestrator.py` | Pipeline coordination |
| Injector | `backend/scripts/sdsr/inject_synthetic.py` | Execution + truth + signal emission |
| **Observation Watcher (NEW)** | `scripts/tools/sdsr_observation_watcher.sh` | Downstream orchestration |
| SDSR Output Model | `backend/scripts/sdsr/Scenario_SDSR_output.py` | Data structures |
| Observation Emitter | `backend/scripts/sdsr/SDSR_output_emit_AURORA_L2.py` | Artifact serialization |
| AURORA Applier | `scripts/tools/AURORA_L2_apply_sdsr_observations.py` | Capability updates |
| Preflight Pipeline | `scripts/tools/run_aurora_l2_pipeline_preflight.sh` | Preflight compile + deploy |
| UI Pipeline | `scripts/tools/run_aurora_l2_pipeline.sh` | Production projection recompilation |

---

## 12. Related Documents

- [SDSR_SYSTEM_CONTRACT.md](SDSR_SYSTEM_CONTRACT.md) - Core SDSR principles
- [SDSR_E2E_TESTING_PROTOCOL.md](SDSR_E2E_TESTING_PROTOCOL.md) - Testing guardrails
- [PIN-370](../memory-pins/PIN-370-sdsr-activity-incident-lifecycle.md) - SDSR Activity/Incident Lifecycle
- [PIN-379](../memory-pins/PIN-379-sdsr-e2e-pipeline-gap-closure.md) - E2E Pipeline Gap Closure
- [PIN-394](../memory-pins/PIN-394-sdsr-aurora-one-way-causality-pipeline.md) - One-Way Causality Pipeline

---

## 13. SDSR EXECUTION & ANALYSIS PROTOCOL (MANDATORY FOR ALL AGENTS)

### 13.0 Core Mental Model

> **SDSR does not know what a capability is.**
> **SDSR only knows what happened.**

Capabilities:

* do **not** exist before SDSR
* are **not** referenced by SDSR
* are **not** asserted by SDSR

Capabilities are **beliefs inferred later by Aurora**.

---

### 13.1 Allowed Scope for SDSR

SDSR is allowed to reason about **only**:

* canonical backend entities
* canonical fields
* state transitions
* triggers (API calls, worker steps)
* timestamps and causality

SDSR is **not allowed** to reason about:

* UI affordances
* capability lifecycle states
* DECLARED / OBSERVED / TRUSTED
* Aurora registries
* intent YAML semantics

If an agent mentions these during SDSR analysis → **STOP**.

---

### 13.2 SDSR Execution Steps (Strict Order)

#### STEP 1 — Baseline Hygiene

Before running any SDSR scenario, Claude must:

1. Verify no synthetic data exists:
   * `runs`
   * `aos_traces`
   * `incidents`
   * `policy_proposals`
2. Verify no SDSR observation files exist.
3. Verify Aurora belief state is reset to **pre-SDSR**.

If any condition fails:
* Report
* Do not proceed

---

#### STEP 2 — Scenario Classification (MANDATORY)

Claude must classify the scenario **before execution**:

* **Infrastructure scenario**
  * validates worker / execution / traces
  * expected `capabilities_observed = []`

* **Effect scenario**
  * produces irreversible state transition
  * expected non-empty observed effects

Claude must state explicitly:

```
This scenario is expected to observe effects: YES / NO
```

No assumptions allowed.

---

#### STEP 3 — Execute via Orchestrator Only

Claude must run SDSR **only** via:

```bash
sdsr_e2e_orchestrator.py
```

Claude must **not**:

* run `inject_synthetic.py` directly (except for debugging)
* skip Aurora steps
* run partial pipelines

---

#### STEP 4 — Verify Injector Contract

After execution, Claude must verify:

1. Injector exit code
2. Observation file existence
3. Observation schema validity

If exit code = 0 and observation missing → **CRITICAL VIOLATION**

Stop immediately.

---

### 13.3 SDSR Observation Rules (Non-Negotiable)

Claude must interpret SDSR observation as:

* **raw system truth**
* **not capability proof**
* **not UI validation**

Claude must check only:

* entities
* fields
* from → to transitions
* triggers

Claude must **not**:

* invent capability IDs
* retrofit capabilities into SDSR output
* add `capabilities_tested` to make Aurora "happy"

Empty `capabilities_observed` is **valid**.

---

### 13.4 Capability Handling Rules (CRITICAL)

Claude must follow this rule:

> **Capabilities are inferred ONLY after SDSR, and ONLY by Aurora.**

Therefore:

* SDSR YAML must not declare capabilities
* SDSR observation must not mention capability lifecycle
* SDSR analysis must stop at "effects observed"

If no meaningful state transition occurred:

```
capability inference = NOT POSSIBLE
```

That is a **successful SDSR run**, not a failure.

---

### 13.5 Aurora Interaction Rules

Claude may analyze Aurora **only after** SDSR observation exists.

Claude may:

* check whether Aurora inferred capabilities
* check whether UI projection changed

Claude may **not**:

* blame SDSR for Aurora refusing empty observations
* modify SDSR to satisfy Aurora
* move capability logic upstream

If Aurora rejects an observation:

* Diagnose Aurora rules
* Do not mutate SDSR truth

---

### 13.6 Debugging Discipline

When something fails, Claude must:

1. Identify the **first violated contract**
2. Report the exact layer:
   * Injector
   * Orchestrator
   * Aurora
3. Stop

Claude must **not**:

* patch forward
* apply compensating logic
* "fix" downstream symptoms upstream

---

### 13.7 Forbidden Moves (Immediate Stop)

Claude must stop if it attempts to:

* Add capability IDs into SDSR YAML
* Read Aurora capability registry during SDSR
* Infer capabilities inside `materialize_and_emit_truth`
* Treat "no capability observed" as failure
* Bypass orchestrator
* Assume UI must change for SDSR to pass

These are **architectural violations**.

---

### 13.8 Success Criteria (Explicit)

An SDSR run is considered **successful** if:

* Execution completed as expected
* Truth was materialized
* Observation artifact exists
* All effects (or lack thereof) are accurately captured

UI change is **not required**.

Capability inference is **not required**.

---

### 13.9 Layer Separation Reminder

> **SDSR proves reality.**
> **Aurora interprets it.**
> **UI reflects belief.**

Do not collapse these layers.

---

### 13.10 When Claude May Propose Changes

Claude may propose changes **only if**:

* A contract is violated
* A boundary is crossed
* A silent failure occurs

Claude must never propose changes merely to:

* advance a capability
* satisfy UI
* remove emptiness

---

## 14. Quick Reference — SDSR vs Aurora vs UI

| Layer | Responsibility | Allowed to Know |
|-------|----------------|-----------------|
| **SDSR** | Observe what happened | Entities, fields, transitions |
| **Aurora** | Infer capabilities | SDSR observations, capability registry |
| **UI** | Reflect beliefs | Aurora binding status |

**SDSR must never know about Aurora.**
**Aurora must never modify SDSR.**
**UI must never drive state.**

---

## 15. Observation Classification (MECHANICAL DISCRIMINATOR)

### 15.1 The Problem This Solves

Without a mechanical discriminator, Claude and downstream systems must **infer** whether empty `capabilities_observed` is valid. This leads to:

* Misinterpretation of infrastructure scenarios
* Incorrect Aurora applier rejections
* Ambiguous pipeline failures

### 15.2 The Solution: observation_class

Every `ScenarioSDSROutput` must declare exactly one of:

| Class | Meaning | Empty Capabilities |
|-------|---------|-------------------|
| **INFRASTRUCTURE** | Validates worker/execution/traces | VALID |
| **EFFECT** | Produces irreversible state transitions | INVALID |

### 15.3 Classification Rule (Mechanical)

In `ScenarioSDSROutputBuilder.from_execution()`:

```python
if observed_effects:
    observation_class = "EFFECT"
else:
    observation_class = "INFRASTRUCTURE"
```

No YAML flags. No Aurora knowledge. No human interpretation. Pure truth.

### 15.4 Aurora Applier Gate

```python
if observation.observation_class == "INFRASTRUCTURE":
    return NO_OP  # explicitly valid, no capability updates
```

This is alignment with truth semantics, not loosening Aurora.

---

## 16. Four Locked Invariants (CONSTITUTIONAL)

These invariants are **locked** and must not be violated:

### INV-SDSR-001: SDSR_output is the sole authority for naming observed capabilities

No other module may add capabilities to an observation:
* NOT inject_synthetic.py
* NOT Aurora applier
* NOT scenario YAML
* NOT step definitions

### INV-SDSR-002: SDSR never updates capability registry or belief state

SDSR materializes truth. Aurora updates beliefs.

If SDSR wrote to the registry, it would collapse truth and belief, violate layer separation, and break replayability.

### INV-SDSR-003: Aurora never infers capabilities — it only applies belief transitions

Aurora reads `capabilities_observed` from SDSR observations.
Aurora never asks "Did this prove capability X?"
Aurora only asks "Should I transition this capability's status?"

### INV-SDSR-004: Empty capabilities_observed is valid for INFRASTRUCTURE observations

This is not a bug. This is not a gap.
Infrastructure scenarios validate system machinery, not capabilities.

---

## 17. Capability Inference (Acceptance Criteria)

### 17.1 Where Capability Names Come From

`Scenario_SDSR_output.py` contains `CAPABILITY_ACCEPTANCE_CRITERIA`:

```python
CAPABILITY_ACCEPTANCE_CRITERIA = {
    ("policy_proposal", "status", "PENDING", "APPROVED"): "APPROVE",
    ("policy_proposal", "status", "PENDING", "REJECTED"): "REJECT",
}
```

### 17.2 Inference Rule

Capabilities are named **only if**:

1. Execution status is PASSED
2. At least one observed effect exists
3. That effect matches acceptance criteria in the mapping

### 17.3 Key Distinction

> **Naming a capability ≠ asserting a capability exists**

SDSR says: "This behavior occurred."
Aurora decides: "Should I update my beliefs?"

---

## 18. Observation JSON Schema (Updated)

```json
{
  "scenario_id": "SDSR-E2E-005",
  "status": "PASSED",
  "observation_class": "INFRASTRUCTURE",  // REQUIRED: mechanical discriminator
  "observed_at": "2026-01-11T14:20:52Z",
  "observed_effects": [],                  // REQUIRED: may be empty
  "capabilities_observed": [],             // REQUIRED: may be empty for INFRASTRUCTURE
  "metadata": {
    "run_id": "...",
    "runner_version": "inject_synthetic.py v1.0",
    "notes": "..."
  }
}
```

Required fields:
* `scenario_id`
* `status`
* `observation_class` (NEW)
* `observed_at`
* `observed_effects` (NEW)
* `capabilities_observed`

---

## 19. Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-11 | v3 | **One-Way Causality Architecture:** Added `sdsr_observation_watcher.sh`, refactored inject_synthetic.py to emit signals only, updated flow diagrams (PIN-394) |
| 2026-01-11 | v2 | Added Agent Execution Protocol (Section 13-18) |
| 2026-01-10 | v1 | Initial contract |

---

**END OF SPEC**
