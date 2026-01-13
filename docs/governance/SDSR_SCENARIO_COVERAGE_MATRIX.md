# SDSR–Aurora Scenario Coverage Matrix

**Version:** 1.0
**Status:** LOCKED
**Effective:** 2026-01-11
**Authority:** Founder-ratified, immutable without explicit approval
**Foundation:** AOS Execution Integrity Contract v1.0 (Layer 0)

---

## Foundation Compliance

This matrix derives from and complies with the **AOS Execution Integrity Contract** (Layer 0).

| Foundation Principle | Matrix Compliance |
|----------------------|-------------------|
| P1_CAPTURE_ALL | All scenarios require Run Records |
| P2_INTEGRITY_OVER_COMPLETENESS | SC-TR-G explicitly tests blind-spot detection |
| P3_NO_FABRICATED_CERTAINTY | Capabilities require forensic evidence, not inference |

**Reference:** `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml`

---

## Contract Statement

> *Which real-world system behaviors must exist before a capability is allowed to become OBSERVED?*

This matrix is **authoritative**, **complete**, and **non-negotiable**.

---

## 1. Scenario Classes (Canonical, Non-Overlapping)

| Code    | Scenario Class          | Purpose                           |
|---------|-------------------------|-----------------------------------|
| SC-EX-S | Execution — Success     | Prove system can run work cleanly |
| SC-EX-F | Execution — Failure     | Prove failure produces artifacts  |
| SC-EX-D | Execution — Degraded    | Prove partial failure handling    |
| SC-TH-N | Near Threshold          | Prove detection without action    |
| SC-TH-B | Threshold Breach        | Prove incident creation           |
| SC-VI-A | Violation — Auto Action | Prove policy auto-enforcement     |
| SC-PO-H | Policy — HITL           | Prove human governance            |
| SC-PO-L | Policy — Lifecycle      | Prove activate/deactivate         |
| SC-TR-F | Trace — Full            | Prove end-to-end traceability     |
| SC-TR-G | Trace — Gap             | Prove blind-spot detection        |
| SC-ID-H | Identity — Human        | Prove human action path           |
| SC-ID-A | Identity — Agent        | Prove agent action path           |

**Invariant:** These 12 classes do not change. New scenarios are instances, not new classes.

---

## 2. Capability → Scenario Proof Matrix

A capability **may only become OBSERVED** if **at least one required scenario class** produces real effects.

### 2.1 Incident Capabilities

| Capability  | Required Scenario(s) | Real Effects Required      |
|-------------|----------------------|----------------------------|
| ACKNOWLEDGE | SC-TH-B or SC-EX-F   | incident.status OPEN → ACK |
| RESOLVE     | SC-EX-D or SC-VI-A   | incident.status → RESOLVED |
| ADD_NOTE    | SC-EX-F              | incident.notes += entry    |

**Hard Rule:** Near-threshold alone (SC-TH-N) **must not** unlock anything.

---

### 2.2 Policy Proposal Capabilities (HITL)

| Capability | Required Scenario(s) | Real Effects Required              |
|------------|----------------------|------------------------------------|
| APPROVE    | SC-PO-H              | proposal.status PENDING → APPROVED |
| REJECT     | SC-PO-H              | proposal.status PENDING → REJECTED |

**Proven by:** SDSR-E2E-004

---

### 2.3 Policy Lifecycle Capabilities

| Capability       | Required Scenario(s) | Real Effects Required          |
|------------------|----------------------|--------------------------------|
| ACTIVATE         | SC-PO-L or SC-VI-A   | policy.state INACTIVE → ACTIVE |
| DEACTIVATE       | SC-PO-L              | policy.state ACTIVE → INACTIVE |
| UPDATE_RULE      | SC-PO-L              | policy.rule_hash changed       |
| UPDATE_THRESHOLD | SC-PO-L              | threshold.value changed        |
| UPDATE_LIMIT     | SC-PO-L              | limit.value changed            |

**Hard Rule:** No state change = no OBSERVED, even if UI allowed action.

---

### 2.4 Execution & Trace Capabilities

| Capability           | Required Scenario(s) | Real Effects Required     |
|----------------------|----------------------|---------------------------|
| EXECUTE              | SC-EX-S              | worker completed          |
| TRACE                | SC-TR-F              | correlated trace_id chain |
| TRACE_GAP_DETECTED   | SC-TR-G              | audit warning or incident |
| VIEW_EXECUTION_GRAPH | SC-TR-F              | trace spans persisted     |

---

### 2.5 Identity-Sensitive Capabilities

| Capability      | Required Scenario(s) | Extra Constraint      |
|-----------------|----------------------|-----------------------|
| APPROVE (Human) | SC-ID-H              | auth_context = human  |
| APPROVE (Agent) | SC-ID-A              | auth_context = agent  |
| EXECUTE (Agent) | SC-ID-A              | agent identity logged |

**Invariant:** Aurora does not distinguish identity — SDSR evidence does.

---

## 3. Panel Binding Coverage (Derived, Not Declared)

Panels unlock **only when all required capabilities are OBSERVED**.

| Panel        | Required Capabilities                  |
|--------------|----------------------------------------|
| INC-AI-OI-O2 | ACKNOWLEDGE                            |
| INC-AI-ID-O3 | ACKNOWLEDGE, RESOLVE, ADD_NOTE         |
| POL-PR-PP-O2 | APPROVE, REJECT                        |
| POL-AP-AR-O3 | ACTIVATE, DEACTIVATE, UPDATE_RULE      |
| POL-AP-BP-O3 | ACTIVATE, DEACTIVATE, UPDATE_THRESHOLD |
| POL-AP-RL-O3 | ACTIVATE, DEACTIVATE, UPDATE_LIMIT     |

---

## 4. Scenario → Capability Yield Matrix

This prevents **overclaiming**.

| Scenario Class | May Produce OBSERVED                 |
|----------------|--------------------------------------|
| SC-EX-S        | EXECUTE, TRACE                       |
| SC-EX-F        | ACKNOWLEDGE, ADD_NOTE                |
| SC-EX-D        | RESOLVE                              |
| SC-TH-N        | ❌ NONE (must remain INFRASTRUCTURE) |
| SC-TH-B        | ACKNOWLEDGE                          |
| SC-VI-A        | ACTIVATE, DEACTIVATE, RESOLVE        |
| SC-PO-H        | APPROVE, REJECT                      |
| SC-PO-L        | ACTIVATE, UPDATE_*                   |
| SC-TR-F        | TRACE, VIEW_EXECUTION_GRAPH          |
| SC-TR-G        | TRACE_GAP_DETECTED                   |
| SC-ID-H        | (identity evidence only)             |
| SC-ID-A        | (identity evidence only)             |

**Hard Rule:** If a scenario tries to yield more than this → reject observation.

---

## 5. Execution Order (Enforced)

Scenarios must be run in this order:

| Order | Scenario Class | Unlocks                      |
|-------|----------------|------------------------------|
| 1     | SC-TH-B        | ACKNOWLEDGE                  |
| 2     | SC-EX-D        | RESOLVE                      |
| 3     | SC-EX-S + SC-TR-F | EXECUTE, TRACE            |
| 4     | SC-PO-L        | ACTIVATE, UPDATE_*           |
| 5     | SC-TH-N        | ❌ (verify no unlock happens) |
| 6     | SC-TR-G        | verify blind-spot detection  |

---

## 6. Implementation Contract

### What Changes in Code (Minimal)

**Aurora:** No changes.

**SDSR only:**
1. Add `scenario_class` to scenario metadata
2. Add capability inference guard: *"Is this capability allowed from this class?"*

That's it.

### Code Location

| Component | File | Change |
|-----------|------|--------|
| Scenario metadata | `backend/scripts/sdsr/Scenario_SDSR_output.py` | Add `scenario_class` field |
| Yield guard | `backend/scripts/sdsr/Scenario_SDSR_output.py` | Validate against Section 4 matrix |
| Schema | `sdsr/SDSR_OBSERVATION_SCHEMA.json` | Add `scenario_class` enum |

---

## 7. Invariants (Constitutional)

| ID | Invariant |
|----|-----------|
| INV-SCM-001 | No button can appear without forensic evidence |
| INV-SCM-002 | Near-misses (SC-TH-N) must never unlock capabilities |
| INV-SCM-003 | Human vs Agent proof exists in SDSR, not UI |
| INV-SCM-004 | Missing observability is a first-class failure |
| INV-SCM-005 | Scenario class determines maximum yield |
| INV-SCM-006 | Panel binding is derived from capability status |

---

## 8. Validation

```python
# Pseudo-code for yield guard
ALLOWED_YIELDS = {
    "SC-EX-S": {"EXECUTE", "TRACE"},
    "SC-EX-F": {"ACKNOWLEDGE", "ADD_NOTE"},
    "SC-EX-D": {"RESOLVE"},
    "SC-TH-N": set(),  # MUST BE EMPTY
    "SC-TH-B": {"ACKNOWLEDGE"},
    "SC-VI-A": {"ACTIVATE", "DEACTIVATE", "RESOLVE"},
    "SC-PO-H": {"APPROVE", "REJECT"},
    "SC-PO-L": {"ACTIVATE", "DEACTIVATE", "UPDATE_RULE", "UPDATE_THRESHOLD", "UPDATE_LIMIT"},
    "SC-TR-F": {"TRACE", "VIEW_EXECUTION_GRAPH"},
    "SC-TR-G": {"TRACE_GAP_DETECTED"},
    "SC-ID-H": set(),  # identity evidence only
    "SC-ID-A": set(),  # identity evidence only
}

def validate_capability_yield(scenario_class: str, capabilities: list[str]) -> bool:
    allowed = ALLOWED_YIELDS.get(scenario_class, set())
    for cap in capabilities:
        if cap not in allowed:
            raise YieldViolation(f"{cap} not allowed from {scenario_class}")
    return True
```

---

## Related Documents

### Foundation (Layer 0)

- `docs/contracts/AOS_EXECUTION_INTEGRITY_CONTRACT.yaml` — **Foundational contract (Layer 0)**
- PIN-403 — AOS Execution Integrity Contract PIN

### SDSR Governance

- `docs/governance/SDSR_SYSTEM_CONTRACT.md` — Core SDSR contract
- `docs/governance/SDSR_PIPELINE_CONTRACT.md` — Pipeline execution contract
- PIN-396 — SDSR Scenario Coverage Matrix (this document)
- PIN-395 — Scenario Taxonomy
- PIN-393 — Observation Class Discriminator
- PIN-370 — SDSR Activity/Incident Lifecycle

---

*This contract is machine-enforced. Non-compliant observations will be rejected.*
