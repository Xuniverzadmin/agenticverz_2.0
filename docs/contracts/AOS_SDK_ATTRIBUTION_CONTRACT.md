# AOS SDK Attribution Contract

**Status:** RATIFIED
**Effective:** 2026-01-18
**Authority:** Ingress Authority — First Line of Truth
**Scope:** All runs entering the system via AOS SDK

---

## Purpose

To guarantee that **every run entering the system is attribution-complete** at the moment of creation. Attribution is not inferred, repaired, or defaulted downstream.

> **Attribution is an ingress invariant, not an analytics concern.**

---

## Contract: Run Attribution Envelope (Mandatory)

Every run emitted via AOS SDK **MUST** include the following fields:

| Field        | Type   | Required    | Semantics                 |
|--------------|--------|-------------|---------------------------|
| `agent_id`   | string | YES         | Executing software entity |
| `actor_type` | enum   | YES         | Origin class              |
| `actor_id`   | string | Nullable    | Human or service identity |
| `source`     | enum   | YES         | SDK / API / SYSTEM        |

---

## actor_type Enumeration (Closed Set)

| Value     | Meaning                     |
|-----------|-----------------------------|
| `HUMAN`   | User-initiated execution    |
| `SYSTEM`  | Automation / cron / policy  |
| `SERVICE` | Non-human service principal |

**Rules:**

- `actor_id` **REQUIRED** if `actor_type = HUMAN`
- `actor_id` **MUST be NULL** if `actor_type = SYSTEM`
- No inference allowed

---

## SDK Enforcement Rules

### Hard Fail Conditions

The SDK **MUST reject run creation** if:

- `agent_id` is missing or empty
- `actor_type` is missing
- `actor_type = HUMAN` and `actor_id` is missing

### Forbidden Behaviors

| Behavior | Status |
|----------|--------|
| Silent defaults | FORBIDDEN |
| Backend backfilling | FORBIDDEN |
| Post-hoc enrichment | FORBIDDEN |
| UI-driven attribution | FORBIDDEN |

---

## Contractual Guarantee

> **Any run accepted by AOS SDK is attribution-complete by definition.**

This guarantee propagates through:

- Cost analysis
- Risk analysis
- LIVE-O5 distributions
- Signals and audits

---

## Violation Response

If a run is submitted without complete attribution:

```
SDK_ATTRIBUTION_VIOLATION

Field: {missing_field}
Rule: {violated_rule}
Action: REJECTED (run not created)

Reference: docs/contracts/AOS_SDK_ATTRIBUTION_CONTRACT.md
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `RUN_VALIDATION_RULES.md` | Structural completeness definition |
| `SDSR_ATTRIBUTION_INVARIANT.md` | Control-plane law for dimensions |
| `CAPABILITY_SURFACE_RULES.md` | Topic-scoped endpoint governance |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial ratification | Governance |
