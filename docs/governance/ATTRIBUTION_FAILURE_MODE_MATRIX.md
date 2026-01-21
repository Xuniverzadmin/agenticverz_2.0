# Attribution Failure-Mode Matrix

**Status:** RATIFIED
**Effective:** 2026-01-18
**Purpose:** Blast-radius map — what breaks if contracts are violated
**Reference:** ATTRIBUTION_ARCHITECTURE.md

---

## Purpose

This matrix defines the **consequences of violating attribution contracts**. It explains *why enforcement must exist* and what breaks at each layer.

---

## A. AOS SDK Attribution Contract Violations

| Violation | Immediate Effect | Downstream Breakage | Severity |
|-----------|------------------|---------------------|----------|
| `agent_id` missing | Run still created | LIVE-O5 "By Agent" invalid | CRITICAL |
| `actor_type` missing | Actor inference | Audit trail ambiguous | CRITICAL |
| `actor_type=HUMAN` but `actor_id` null | False automation | Compliance breach | CRITICAL |
| `actor_type=SYSTEM` but `actor_id` provided | False human | Audit trail polluted | CRITICAL |
| `origin_system_id` missing | No accountability | Forensics impossible | CRITICAL |
| SDK allows silent defaults | Dirty data persists | Impossible cleanup | CRITICAL |

**Conclusion:** SDK must be a **hard gate**. Any softness here permanently poisons analytics.

---

## B. Run Validation Rule Violations

| Violation | Effect | System Symptom | Severity |
|-----------|--------|----------------|----------|
| Mutable `agent_id` | Attribution drift | Signals lose ownership | CRITICAL |
| Mutable `actor_type` | Origin rewrite | Audit trail invalid | CRITICAL |
| Partial run persisted | Null buckets | "Unknown agent" noise | HIGH |
| Backend backfills identity | False truth | Trust erosion | CRITICAL |
| R4 violated (HUMAN without actor_id) | Phantom human | Compliance failure | CRITICAL |
| R5 violated (SYSTEM with actor_id) | False human | Analytics pollution | CRITICAL |

**Conclusion:** Runs must be **atomic + immutable** at creation.

---

## C. Schema / View Violations

| Violation | Effect | User Impact | Severity |
|-----------|--------|-------------|----------|
| `agent_id` not in base table | Storage gap | Cannot query by agent | CRITICAL |
| `agent_id` not in view | Projection gap | LIVE-O5 "By Agent" fails | CRITICAL |
| View omits declared dimension | Runtime error | Capability breaks | CRITICAL |
| Column nullable when invariant requires NOT NULL | Silent nulls | Data corruption | HIGH |

**Conclusion:** Schema is the single source of truth. Views must project all declared dimensions.

---

## D. SDSR / Capability Violations

| Violation | Effect | User Impact | Severity |
|-----------|--------|-------------|----------|
| Capability declares `agent_id`, view omits it | Runtime error | Broken LIVE-O5 | CRITICAL |
| UI hides missing dimension | Silent lie | False confidence | CRITICAL |
| Capability overclaims | Control-plane drift | Governance failure | CRITICAL |
| Dimension "planned but not projected" | False promise | User confusion | HIGH |
| Panel filters locally instead of trusting endpoint | Topic leak | Data exposure | CRITICAL |

**Conclusion:** **Claim ≠ Truth unless schema proves it.**

---

## E. Legacy Data Violations

| Violation | Effect | User Impact | Severity |
|-----------|--------|-------------|----------|
| Legacy data not backfilled | NULL values | Query failures | HIGH |
| Legacy marker not explicit | Ambiguous origin | Analytics confusion | MEDIUM |
| Legacy bucket hidden in UI | Silent omission | False totals | HIGH |
| Legacy merged into "Other" | Lost signal | Trend distortion | MEDIUM |
| New runs enter legacy bucket | Enforcement failure | Incident | CRITICAL |

**Conclusion:** Legacy must be **explicit, visible, and time-bounded**.

---

## Severity Legend

| Level | Meaning | Response |
|-------|---------|----------|
| CRITICAL | System integrity compromised | Block merge / Block deployment |
| HIGH | Significant degradation | Fix before release |
| MEDIUM | Quality impact | Fix in next sprint |
| LOW | Minor issue | Track and address |

---

## Contract-to-Failure Mapping

| Contract | Primary Failure Mode | Detection Point |
|----------|---------------------|-----------------|
| AOS_SDK_ATTRIBUTION_CONTRACT | Dirty data at ingress | SDK validation |
| RUN_VALIDATION_RULES | Structural incompleteness | Database constraints |
| SDSR_ATTRIBUTION_INVARIANT | Capability overclaim | SDSR scenario |
| CAPABILITY_SURFACE_RULES | Topic isolation breach | Endpoint audit |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | Ingress rules |
| `RUN_VALIDATION_RULES.md` | Structural invariants |
| `SDSR_ATTRIBUTION_INVARIANT.md` | Control-plane law |
| `CAPABILITY_REVIEW_GATE_TEMPLATE.md` | PR checklist |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
