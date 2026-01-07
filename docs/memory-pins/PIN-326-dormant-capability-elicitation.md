# PIN-326: Dormant → Declared Capability Elicitation (Layer-Safe)

**Status:** COMPLETE
**Created:** 2026-01-06
**Category:** Governance / Capability Elicitation
**Scope:** Full System Elicitation
**Prerequisites:** PIN-325 (Shadow Capability Forensic Audit)

---

## Objective

Elicit ALL dormant/shadow executable power into declared latent capabilities, enforcing layer sanity and flagging violations for human action.

**Operating Mode:** Elicitation ONLY — no fixes, no deletions, no quarantining, no re-architecture.

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Latent Capabilities Discovered | 103 | DECLARED as DORMANT |
| HTTP Routes Enumerated | 365 | 100% coverage |
| Workers Enumerated | 9 | 100% coverage |
| CLI Commands Enumerated | 31 | 100% coverage |
| SDK Methods Enumerated | 31 | 100% coverage |
| Layer Violations Flagged | 2 | For human decision |
| Authority Gaps Documented | 14 | For human decision |
| Shadow → Dormant Conversion | 100% | COMPLETE |

---

## Key Achievement

**Before PIN-326 (Shadow):**
- Unknown executable paths
- Unassessable risk
- 92% of routes unmapped

**After PIN-326 (Dormant):**
- All paths discovered and declared
- Risk is assessable
- 0% undiscovered (100% declared)

---

## Phase Execution Summary

| Phase | Task | Status |
|-------|------|--------|
| 1.1 | Enumerate executable power by vector | COMPLETE |
| 1.2 | Detect layer boundary violations | COMPLETE |
| 2.1 | Behavioral clustering into latent capabilities | COMPLETE |
| 2.2 | Declare latent capabilities as DORMANT | COMPLETE |
| 3.1 | Capability-layer consistency check | COMPLETE |
| 4.1 | Negative assertion (re-answer) | COMPLETE |
| 5 | Produce elicitation report | COMPLETE |

---

## Latent Capability Distribution

### By Layer

| Layer | LCAP Count | Entry Points |
|-------|------------|--------------|
| L1 (SDK) | 31 | 31 methods |
| L2 (API) | 59 | 365 routes |
| L5 (Worker) | 3 | 9 workers |
| L7 (CLI) | 10 | 31 commands |
| **Total** | **103** | **436** |

### By Power Type

| Power Type | Count | Percentage |
|------------|-------|------------|
| READ_ONLY | 52 | 50% |
| EXECUTE | 24 | 23% |
| WRITE | 15 | 15% |
| CONTROL | 9 | 9% |
| AUTO_EXECUTE | 3 | 3% |

### By Governance Status

| Status | Count | Note |
|--------|-------|------|
| SHADOW (unmapped to CAP) | 67 | No CAP-XXX exists |
| PARTIAL (partial CAP mapping) | 33 | Routes not in allowed_routes |
| FULL (properly governed) | 3 | Correctly in allowed_routes |

---

## Critical Findings

### 1. Agent Autonomy System (45 routes)

All routes in `/agents/*` are SHADOW - no allowed_routes defined for CAP-008 despite the capability being "CLOSED".

### 2. Auto-Execution Without Gates

LCAP-WKR-002 (Recovery Processing) auto-executes recovery actions at confidence >= 0.8 without explicit capability gate.

### 3. CLI/SDK Have No Governance

31 CLI commands and 31 SDK methods have zero capability governance - no L7 or L1 capabilities exist.

### 4. Layer Violations

- `integration.py` (L2) directly calls database (L6) - 13 instances
- `cost_intelligence.py` (L2) directly calls database (L6) - 8 instances

---

## Negative Assertion Update

**Question:** Is there undiscovered executable power?

**PIN-325 Answer:** YES (92% shadow)
**PIN-326 Answer:** NO (0% shadow, 100% dormant)

**Caveat:** Dormant ≠ Governed. Discovery is complete, governance is not.

---

## Human Decisions Required

1. **Registry Updates:** Add 103 LCAP to CAPABILITY_REGISTRY?
2. **Auto-Execution Gates:** Gate LCAP-WKR-002 recovery auto-execute?
3. **CLI/SDK Governance:** Create CAP-019 (CLI) and CAP-020 (SDK)?
4. **Layer Violations:** Fix L2→L6 direct access?

---

## Artifacts

| Artifact | Path |
|----------|------|
| Latent Capabilities YAML | `l2_1/evidence/pin_326/LATENT_CAPABILITIES_DORMANT.yaml` |
| Layer Consistency Check | `l2_1/evidence/pin_326/CAPABILITY_LAYER_CONSISTENCY.md` |
| Negative Assertion | `l2_1/evidence/pin_326/NEGATIVE_ASSERTION.md` |
| Elicitation Report | `l2_1/evidence/pin_326/ELICITATION_REPORT.md` |

---

## References

- PIN-325: Shadow Capability Forensic Audit
- PIN-324: Capability Console Classification
- PIN-323: L2-L2.1 Audit Reinforcement
- CAPABILITY_REGISTRY.yaml
- CONSOLE_CLASSIFICATION.yaml

---

## Updates

### 2026-01-06: PIN Created and Completed

- All 5 phases executed successfully
- 103 latent capabilities declared as DORMANT
- 436 execution entry points enumerated
- 2 layer violations flagged
- 14 authority gaps documented
- Negative assertion re-answered: NO undiscovered power
- Ready for human decision on governance actions
