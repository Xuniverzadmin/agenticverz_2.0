# Customer Console v1 Release

**Status:** FROZEN
**Release Date:** 2026-01-13
**Reference:** PIN-412 (Domain Design — Incidents & Policies)

---

## Summary

Customer Console v1 delivers the complete Incidents and Policies domain implementation with O2 runtime projection APIs, UX invariants enforcement, and architectural integrity guarantees.

---

## Deliverables

### 1. Schema (Migrations 087-090)

| Migration | Description |
|-----------|-------------|
| 087 | Incidents lifecycle repair (ACKED state) |
| 088 | Policy control plane foundation (policy_rules, limits, enforcements, breaches) |
| 089 | Policy rule integrity table + indexes + invariant trigger |
| 090 | Limit integrity table + indexes + invariant trigger |

### 2. Runtime Projection APIs

| API | Endpoint | Contract |
|-----|----------|----------|
| INC-RT-O2 | `GET /api/v1/runtime/incidents` | Incidents list with topic-based filtering |
| GOV-RT-O2 | `GET /api/v1/runtime/policies/rules` | Governance rules with integrity and enforcement stats |
| LIM-RT-O2 | `GET /api/v1/runtime/policies/limits` | Limits with integrity and breach stats |

### 3. Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Integrity tables | Option C: Separate tables per entity | Rules and limits do not share lifecycle semantics |
| ACKED state | Badge inside Active topic | Not a separate topic; UI shows badge when `lifecycle_state=ACKED` |
| Topic parameter | Replace `state` with `topic` | UX-driven filtering (ACTIVE topic includes ACTIVE + ACKED) |

---

## API Contract Summary

### INC-RT-O2: Incidents

```
GET /api/v1/runtime/incidents?topic=ACTIVE|RESOLVED
```

**Topic Mapping:**
- `ACTIVE` → returns `ACTIVE` + `ACKED` lifecycle states
- `RESOLVED` → returns `RESOLVED` only

**Response Shape:**
```json
{
  "items": [{
    "incident_id": "inc_...",
    "lifecycle_state": "ACTIVE|ACKED|RESOLVED",
    "severity": "critical|high|medium|low",
    "category": "...",
    "title": "...",
    "llm_run_id": "run_...",
    "cause_type": "LLM_RUN|SYSTEM|HUMAN",
    "created_at": "...",
    "resolved_at": "..."
  }],
  "total": 42,
  "has_more": true
}
```

### GOV-RT-O2: Governance Rules

```
GET /api/v1/runtime/policies/rules?status=ACTIVE|RETIRED
```

**Response Shape:**
```json
{
  "items": [{
    "rule_id": "PR-...",
    "name": "...",
    "description": "...",
    "rule_type": "...",
    "scope": "GLOBAL|TENANT|PROJECT|AGENT",
    "enforcement_mode": "BLOCK|WARN|LOG|DRY_RUN",
    "status": "ACTIVE|RETIRED",
    "integrity_status": "VERIFIED|DEGRADED|FAILED",
    "integrity_score": 0.95,
    "trigger_count_30d": 42,
    "last_triggered_at": "...",
    "created_at": "..."
  }],
  "total": 10,
  "has_more": false
}
```

### LIM-RT-O2: Limits

```
GET /api/v1/runtime/policies/limits?type=BUDGET|RATE|THRESHOLD
```

**Response Shape:**
```json
{
  "items": [{
    "limit_id": "LIM-...",
    "name": "...",
    "limit_category": "BUDGET|RATE|THRESHOLD",
    "limit_type": "COST_USD|TOKENS_*|REQUESTS_*",
    "scope": "GLOBAL|TENANT|PROJECT|AGENT|PROVIDER",
    "enforcement": "BLOCK|WARN|REJECT|QUEUE|DEGRADE|ALERT",
    "status": "ACTIVE|DISABLED",
    "max_value": 1000.00,
    "window_seconds": 3600,
    "reset_period": "DAILY|WEEKLY|MONTHLY|NONE",
    "integrity_status": "VERIFIED|DEGRADED|FAILED",
    "integrity_score": 0.998,
    "breach_count_30d": 5,
    "last_breached_at": "...",
    "created_at": "..."
  }],
  "total": 15,
  "has_more": false
}
```

---

## UX Invariants Enforced

### Terminology (Frozen)

| Concept | Locked Term | Forbidden |
|---------|-------------|-----------|
| Execution instance | LLM Run | Run, Job, Task |
| Governance rule | Policy Rule | Policy, Guard |
| Quantitative cap | Limit | Rule, Budget alone |
| Failure event | Incident | Alert, Error |

### Column Labels (Frozen)

| API Field | UI Label |
|-----------|----------|
| `max_value` | Limit Value |
| `integrity_status` | Integrity |
| `integrity_score` | Integrity Score |
| `trigger_count_30d` | Triggers (30d) |
| `breach_count_30d` | Breaches (30d) |
| `lifecycle_state` | Status |
| `enforcement_mode` | Enforcement |

### ACKED State Handling

- ACKED is **never** a separate topic/tab
- ACKED shown as badge inside Active topic
- API returns `lifecycle_state` field for badge rendering
- `topic=ACTIVE` query returns both ACTIVE and ACKED states

---

## DB Invariants (Trigger-Enforced)

### Policy Rule Integrity

```sql
-- Trigger: enforce_policy_rule_integrity
-- Every ACTIVE rule MUST have integrity row
INSERT INTO policy_rules (status = 'ACTIVE') → integrity row required
```

### Limit Integrity

```sql
-- Trigger: enforce_limit_integrity
-- Every ACTIVE limit MUST have integrity row
INSERT INTO limits (status = 'ACTIVE') → integrity row required
```

---

## Files Delivered

### Backend

```
backend/app/runtime_projections/
├── __init__.py
├── router.py
├── incidents/
│   ├── __init__.py
│   └── router.py          # INC-RT-O2
└── policies/
    ├── __init__.py
    ├── governance/
    │   ├── __init__.py
    │   └── router.py      # GOV-RT-O2
    └── limits/
        ├── __init__.py
        └── router.py      # LIM-RT-O2
```

### Migrations

```
backend/alembic/versions/
├── 087_incidents_lifecycle_repair.py
├── 088_policy_control_plane.py
├── 089_policy_rule_integrity_and_indexes.py
└── 090_limit_integrity_and_indexes.py
```

### Documentation

```
docs/contracts/
└── UX_INVARIANTS_CHECKLIST.md    # Updated with ACKED handling + column labels
```

---

## Verification Completed

- [x] All migrations applied to Neon
- [x] DB triggers active (policy_rule_integrity, limit_integrity)
- [x] Integrity tables created (policy_rule_integrity, limit_integrity)
- [x] UX invariants checklist updated
- [x] ACKED state returns with topic=ACTIVE
- [x] No forbidden terminology in API responses

---

## Frontend Tasks (Post-Freeze)

These are UI-only changes, not backend:

1. **Column label mapping** — Display `max_value` as "Limit Value"
2. **Empty state copy** — Use consistent "{entity_plural}" pattern
3. **ACKED badge** — Render badge when `lifecycle_state === "ACKED"`

---

## References

- PIN-412: Domain Design — Incidents & Policies
- PIN-411: Activity Domain (closed)
- `docs/contracts/UX_INVARIANTS_CHECKLIST.md`
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`
