# Attribution Architecture

**Status:** RATIFIED
**Effective:** 2026-01-18
**Last Verified:** 2026-01-18 (11/11 constraint tests passed)
**Authority:** Contract Chain — From Actor → Agent → Capability
**Reference:** AOS_SDK_ATTRIBUTION_CONTRACT, RUN_VALIDATION_RULES, SDSR_ATTRIBUTION_INVARIANT

---

## Purpose

This document defines the **authoritative contract chain** for run attribution in the AOS system. Attribution flows from actor through SDK to capability surface, with each layer enforcing invariants.

---

## Defense-in-Depth Model

Attribution is enforced at **three independent layers**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEFENSE-IN-DEPTH LAYERS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: SDK VALIDATION                                         │
│  ──────────────────────────────────────────────────────────────  │
│  File: sdk/python/aos_sdk/attribution.py                         │
│  Enforcement: BEFORE network call                                │
│  Mode: shadow → soft → hard (configurable)                       │
│  Errors: ATTR_AGENT_MISSING, ATTR_ACTOR_TYPE_INVALID, etc.       │
│                                                                  │
│  Layer 2: API VALIDATION                                         │
│  ──────────────────────────────────────────────────────────────  │
│  File: backend/app/api/runs.py                                   │
│  Enforcement: Pydantic schema validation                         │
│  Mode: Always HARD (400 Bad Request)                             │
│                                                                  │
│  Layer 3: DATABASE CONSTRAINTS                                   │
│  ──────────────────────────────────────────────────────────────  │
│  File: backend/alembic/versions/105_attribution_check_constraints│
│  Enforcement: PostgreSQL CHECK constraints + triggers            │
│  Mode: Always HARD (cannot bypass)                               │
│                                                                  │
│  CHECK CONSTRAINTS:                                              │
│    • chk_runs_actor_type_valid                                   │
│    • chk_runs_actor_id_human_required                            │
│    • chk_runs_actor_id_nonhuman_null                             │
│                                                                  │
│  TRIGGERS (Legacy Sentinel Rejection):                           │
│    • trg_runs_agent_id_not_legacy                                │
│    • trg_runs_origin_system_not_legacy                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Guarantee:** Even if SDK validation is bypassed, database constraints reject invalid attribution.

---

## Contract Chain Diagram (Authoritative)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ATTRIBUTION CONTRACT CHAIN                        │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ Human /      │
│ Automation   │
│ (Actor)      │
└──────┬───────┘
       │ actor_type + actor_id (explicit)
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ AOS SDK (Ingress Gate)                                                    │
│ ──────────────────────────────────────────────────────────────────────── │
│ Contract: AOS_SDK_ATTRIBUTION_CONTRACT.md                                 │
│                                                                           │
│ REQUIRED FIELDS:                                                          │
│   • agent_id    → Executing software entity (NOT NULL)                    │
│   • actor_type  → HUMAN | SYSTEM | SERVICE (NOT NULL)                     │
│   • actor_id    → Human identity (REQUIRED if HUMAN, NULL if SYSTEM)      │
│   • source      → SDK | API | SYSTEM (NOT NULL)                           │
│                                                                           │
│ ENFORCEMENT: HARD FAIL on violation — run not created                     │
└──────────┬───────────────────────────────────────────────────────────────┘
           │ attribution-complete run
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Runs Base Table (L6 — Platform Substrate)                                 │
│ ──────────────────────────────────────────────────────────────────────── │
│ Contract: RUN_VALIDATION_RULES.md                                         │
│                                                                           │
│ SCHEMA:                                                                   │
│   run_id       VARCHAR  NOT NULL  PK                                      │
│   agent_id     VARCHAR  NOT NULL  ← Attribution invariant                 │
│   actor_type   VARCHAR  NOT NULL  ← Attribution invariant                 │
│   actor_id     VARCHAR  NULLABLE  ← Ruled by actor_type                   │
│   source       VARCHAR  NOT NULL  ← Attribution invariant                 │
│   state        VARCHAR  NOT NULL  ← LIVE | COMPLETED                      │
│                                                                           │
│ CONSTRAINTS:                                                              │
│   R1-R8 invariants enforced                                               │
│   Immutability post-creation                                              │
│   No partial writes                                                       │
└──────────┬───────────────────────────────────────────────────────────────┘
           │ schema truth
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Analytical Views (v_runs_o2)                                              │
│ ──────────────────────────────────────────────────────────────────────── │
│ Contract: SDSR_ATTRIBUTION_INVARIANT.md                                   │
│                                                                           │
│ MUST PROJECT:                                                             │
│   • agent_id       ← Required for "By Agent" dimension                    │
│   • actor_id       ← Required for actor attribution                       │
│   • actor_type     ← Required for origin classification                   │
│   • state          ← Required for topic scoping                           │
│   • provider_type  ← Required for "By Provider" dimension                 │
│   • risk_level     ← Required for "By Risk" dimension                     │
│   • source         ← Required for "By Source" dimension                   │
│                                                                           │
│ RULE: Views cannot omit declared dimensions                               │
└──────────┬───────────────────────────────────────────────────────────────┘
           │ topic-bound query
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Topic-Scoped Endpoints (L2 — Product APIs)                                │
│ ──────────────────────────────────────────────────────────────────────── │
│ Contract: CAPABILITY_SURFACE_RULES.md (TOPIC-SCOPED-ENDPOINT-001)         │
│                                                                           │
│ ENDPOINTS:                                                                │
│   /api/v1/activity/runs/live/by-dimension                                 │
│     → state = LIVE (hardcoded, implicit binding)                          │
│                                                                           │
│   /api/v1/activity/runs/completed/by-dimension                            │
│     → state = COMPLETED (hardcoded, implicit binding)                     │
│                                                                           │
│ PARAMETERS:                                                               │
│   dim = agent_id | provider_type | source | risk_level | status           │
│                                                                           │
│ RULE: Topic determines scope, not caller                                  │
└──────────┬───────────────────────────────────────────────────────────────┘
           │ capability fulfillment
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Capability Surface                                                        │
│ ──────────────────────────────────────────────────────────────────────── │
│ Capability: activity.runs_by_dimension                                    │
│                                                                           │
│ PANELS SERVED:                                                            │
│   • LIVE-O5  "Distribution by dimension" (LIVE topic)                     │
│   • COMP-O5  "Distribution by dimension" (COMPLETED topic)                │
│                                                                           │
│ DIMENSION BUTTONS:                                                        │
│   • By Provider  → dim=provider_type                                      │
│   • By Agent     → dim=agent_id                                           │
│   • By Source    → dim=source                                             │
│   • By Risk      → dim=risk_level                                         │
│   • By Status    → dim=status                                             │
│                                                                           │
│ DOWNSTREAM CONSUMERS:                                                     │
│   • Cost analysis (agent attribution)                                     │
│   • Risk signals (ownership context)                                      │
│   • Audit trails (forensics)                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Key Guarantees (Diagram Truths)

| Guarantee | Enforcement Point |
|-----------|-------------------|
| Attribution is injected once, at SDK ingress | AOS_SDK_ATTRIBUTION_CONTRACT |
| Schema is the single source of truth | RUN_VALIDATION_RULES |
| Views cannot lie | SDSR_ATTRIBUTION_INVARIANT |
| Capabilities only reflect provable dimensions | CAPABILITY_SURFACE_RULES |
| Panels never filter or infer | TOPIC-SCOPED-ENDPOINT-001 |

---

## Contract Dependencies

```
AOS_SDK_ATTRIBUTION_CONTRACT
         │
         ▼
RUN_VALIDATION_RULES (R1-R8)
         │
         ▼
SDSR_ATTRIBUTION_INVARIANT (SDSR-ATTRIBUTION-INVARIANT-001)
         │
         ▼
CAPABILITY_SURFACE_RULES (RULE-CAP-007)
         │
         ▼
TOPIC-SCOPED-ENDPOINT-001
```

Breaking any link invalidates everything downstream.

---

## Failure Modes

| Broken Link | Consequence |
|-------------|-------------|
| SDK allows missing agent_id | Ungovernable runs enter system |
| Schema doesn't enforce NOT NULL | Silent nulls corrupt analytics |
| View omits agent_id | "By Agent" dimension fails |
| Endpoint accepts state param | Topic isolation violated |
| Panel filters locally | Frontend lies about scope |

---

## Database Constraint Verification

All attribution constraints have been tested and verified. Test results:

### Valid Cases (Should Insert Successfully)

| Test | Input | Result |
|------|-------|--------|
| SYSTEM attribution | `actor_type='SYSTEM', actor_id=NULL` | ✅ PASS |
| HUMAN attribution | `actor_type='HUMAN', actor_id='user-12345'` | ✅ PASS |
| SERVICE attribution | `actor_type='SERVICE', actor_id=NULL` | ✅ PASS |

### Invalid Cases (Should Be Rejected)

| Test | Input | Constraint | Result |
|------|-------|------------|--------|
| Invalid actor_type | `actor_type='BOT'` | chk_runs_actor_type_valid | ✅ REJECTED |
| Invalid actor_type | `actor_type='AGENT'` | chk_runs_actor_type_valid | ✅ REJECTED |
| HUMAN without actor_id | `actor_type='HUMAN', actor_id=NULL` | chk_runs_actor_id_human_required | ✅ REJECTED |
| HUMAN with empty actor_id | `actor_type='HUMAN', actor_id=''` | chk_runs_actor_id_human_required | ✅ REJECTED |
| SYSTEM with actor_id | `actor_type='SYSTEM', actor_id='user-12345'` | chk_runs_actor_id_nonhuman_null | ✅ REJECTED |
| SERVICE with actor_id | `actor_type='SERVICE', actor_id='user-12345'` | chk_runs_actor_id_nonhuman_null | ✅ REJECTED |
| Legacy agent_id | `agent_id='legacy-unknown'` | trg_runs_agent_id_not_legacy | ✅ REJECTED |
| Legacy origin_system_id | `origin_system_id='legacy-migration'` | trg_runs_origin_system_not_legacy | ✅ REJECTED |

**Total: 11/11 tests passed** (verified 2026-01-18)

---

## Related Documents

| Document | Location |
|----------|----------|
| SDK Attribution Enforcement | `docs/sdk/SDK_ATTRIBUTION_ENFORCEMENT.md` |
| SDK Attribution Alerts | `docs/sdk/SDK_ATTRIBUTION_ALERTS.md` |
| SDK Attribution Rollout Comms | `docs/sdk/SDK_ATTRIBUTION_ROLLOUT_COMMS.md` |
| SDK Attribution Module | `sdk/python/aos_sdk/attribution.py` |
| DB Constraints Migration | `backend/alembic/versions/105_attribution_check_constraints.py` |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Added defense-in-depth model, DB constraints, verification tests | Governance |
| 2026-01-18 | Initial creation | Governance |
