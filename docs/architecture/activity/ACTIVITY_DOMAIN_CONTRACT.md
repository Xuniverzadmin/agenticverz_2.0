# Activity Domain Contract

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All Activity domain code (L2 facade, L4 services)
**Reference:** Activity Domain System Design

---

## Prime Directive

> **L2 Facade Rule:** `/api/v1/activity/*` is a read-only facade. No writes. No side effects. No recomputation of L6 facts.

---

## 1. Layer Rules

### L2 — Product APIs (Facade)

**File:** `backend/app/api/activity.py`

**Allowed:**
- Query `v_runs_o2` view
- Apply filters and pagination
- Return shaped responses
- Call L4 services

**Forbidden:**
- INSERT, UPDATE, DELETE
- `session.add()`, `session.commit()`
- Direct business logic
- Cross-domain writes

### L4 — Domain Engines (Services)

**Path:** `backend/app/services/activity/`

**Allowed:**
- Read from L6 tables/views
- Compute derived values
- Statistical analysis
- Pattern detection

**Forbidden:**
- Write to any table
- Call other L4 services (except via L3 adapters)
- Import from L1, L2, L3, L5

### L6 — Platform Substrate (Data)

**Tables:**
- `runs` (with O2 columns)
- `aos_traces`
- `aos_trace_steps`

**View:**
- `v_runs_o2` (read-only projection)

---

## 2. Capability Rules

### Rule: One Capability, One Endpoint

Every endpoint must map to exactly one capability in the registry:

```yaml
# ACTIVITY_CAPABILITY_REGISTRY.yaml
capabilities:
  activity.completed_runs:
    endpoint:
      path: /api/v1/activity/runs
      method: GET
      filters:
        state: COMPLETED
```

### Rule: Capability Status Lifecycle

```
DECLARED → OBSERVED → TRUSTED → DEPRECATED
```

| Status | Meaning | CI Behavior | Panel State |
|--------|---------|-------------|-------------|
| DECLARED | Code exists, not validated | Block promotion | Disabled |
| OBSERVED | E2E validation passed | Normal enforcement | Enabled |
| TRUSTED | Stable, production-proven | Full enforcement | Enabled |
| DEPRECATED | Being removed | Warn on usage | Hidden |

### Rule: E2E Validation Gate (CAP-E2E-001)

> **Capabilities MUST remain DECLARED until E2E validation passes.**
> **Only when E2E validation passes can status change to OBSERVED.**

**Rationale:** Claim ≠ Truth. Code existing is not proof that it works correctly end-to-end.

**Enforcement:**
```python
# check_activity_domain.py
def validate_capability_status(capability):
    if capability.status == "OBSERVED":
        e2e_result = lookup_e2e_result(capability.id)
        if not e2e_result or e2e_result.status != "PASS":
            raise ValidationError(
                f"CAP-E2E-001: {capability.id} is OBSERVED but E2E validation not passed"
            )
```

**SDSR Scenario Required:**
Each capability promotion from DECLARED → OBSERVED requires:
1. SDSR scenario YAML in `backend/scripts/sdsr/scenarios/`
2. Scenario execution with `--wait` flag
3. Observation JSON emitted to `SDSR_OBSERVATION_*.json`
4. `AURORA_L2_apply_sdsr_observations.py` applied

**Transition Protocol:**
```
1. Implement capability (status: DECLARED)
2. Write SDSR scenario for capability
3. Run: python inject_synthetic.py --scenario <yaml> --wait
4. Verify: observation emitted, assertions passed
5. Run: python AURORA_L2_apply_sdsr_observations.py --observation <json>
6. Capability status updated: DECLARED → OBSERVED
```

### Rule: No Undeclared Endpoints

If an endpoint exists in `activity.py` but not in the registry → **CI FAIL**

---

## 3. Service Rules

### Rule: Service Responsibilities

Each service has declared responsibilities and forbidden actions:

```yaml
PatternDetectionService:
  responsibilities:
    - "Detect instability patterns in trace steps"
    - "Rule-based analysis only (no ML)"
  forbidden:
    - "Write to any table"
    - "Call other services"
    - "Use machine learning"
```

### Rule: No Cross-Service Calls

Services must not import from other services:

```python
# FORBIDDEN
from app.services.incidents import IncidentService

# ALLOWED
from app.services.activity.pattern_detection_service import PatternDetectionService
```

### Rule: Read Services Don't Write

Services declared as "read" must not contain:
- `INSERT INTO`
- `UPDATE ... SET`
- `DELETE FROM`
- `session.add()`
- `session.commit()`

---

## 4. SQL Rules

### Rule: Use v_runs_o2 View

Activity queries should use `v_runs_o2` view, not `runs` table directly:

```sql
-- PREFERRED
SELECT * FROM v_runs_o2 WHERE tenant_id = :tenant_id

-- AVOID (unless joining for agent_id)
SELECT * FROM runs WHERE tenant_id = :tenant_id
```

### Rule: Tenant Isolation Required

Every query must include tenant isolation:

```sql
-- REQUIRED
WHERE tenant_id = :tenant_id

-- NEVER
SELECT * FROM v_runs_o2  -- No tenant filter
```

### Rule: Index-Friendly Queries

Queries must use existing indexes:

| Query Pattern | Required Index |
|---------------|----------------|
| `state = 'COMPLETED'` | `idx_runs_tenant_state_started` |
| `risk_level = ANY(...)` | `idx_runs_tenant_risk` |
| `status = ANY(...)` | `idx_runs_tenant_status` |
| `provider_type GROUP BY` | `idx_runs_tenant_provider` |

---

## 5. Weight Constants (Frozen)

### Attention Queue Weights

```python
ATTENTION_WEIGHTS = {
    "risk": 0.35,
    "impact": 0.25,
    "latency": 0.15,
    "recency": 0.15,
    "evidence": 0.10,
}
```

**Rule:** Weights must sum to 1.0
**Rule:** Weights cannot be changed without governance approval

---

## 6. CI Enforcement

### Script

```bash
python scripts/preflight/check_activity_domain.py
```

### Rules Checked

| Rule ID | Description | Severity |
|---------|-------------|----------|
| ACT-REG-001 | Capability missing endpoint | ERROR |
| ACT-REG-002 | Capability missing service | ERROR |
| ACT-REG-003 | Undefined service reference | ERROR |
| ACT-REG-004 | Service not in L4 | ERROR |
| ACT-REG-005 | Weights don't sum to 1.0 | ERROR |
| ACT-L2-001 | Write operation in L2 facade | ERROR |
| ACT-SVC-001 | Service violates forbidden rule | ERROR |
| ACT-MAP-001 | TODO capability is implemented | WARNING |
| ACT-HDR-001 | Missing L2 header | ERROR |
| ACT-HDR-002 | Missing L4 header | ERROR |
| ACT-SQL-001 | Direct runs table access | WARNING |

### Integration with Preflight

Add to `run_all_checks.sh`:

```bash
run_check "Activity Domain" "python scripts/preflight/check_activity_domain.py"
```

---

## 7. Panel → Capability Binding

Every UI panel must bind to exactly one capability:

| Panel | Capability | Status | Notes |
|-------|------------|--------|-------|
| ACT-LLM-COMP-O1 | `activity.completed_runs` | OBSERVED | E2E validated |
| ACT-LLM-COMP-O2 | `activity.runs_list` | OBSERVED | E2E validated |
| ACT-LLM-COMP-O3 | `activity.summary_by_status` | DECLARED | Awaiting E2E |
| ACT-LLM-LIVE-O1 | `activity.live_runs` | OBSERVED | E2E validated |
| ACT-LLM-LIVE-O5 | `activity.runs_by_dimension` | DECLARED | Awaiting E2E |
| ACT-LLM-SIG-O3 | `activity.patterns` | DECLARED | Awaiting E2E |
| ACT-LLM-SIG-O4 | `activity.cost_analysis` | DECLARED | Awaiting E2E |
| ACT-LLM-SIG-O5 | `activity.attention_queue` | DECLARED | Awaiting E2E |

---

## 8. Data Flow (Authoritative)

```
SDK.create_run()
     ↓
runs table (L6)
     ↓
v_runs_o2 view (L5: pre-computed)
     ↓
Services (L4: analyze only)
     ↓
/api/v1/activity/* (L2: shape only)
     ↓
UI Panels (L1: render only)
```

**No reverse arrows. No bypasses.**

---

## 9. Related Documents

| Document | Purpose |
|----------|---------|
| `ACTIVITY_DOMAIN_SQL.md` | Exact SQL for each endpoint |
| `ACTIVITY_CAPABILITY_REGISTRY.yaml` | Capability → endpoint mapping |
| `check_activity_domain.py` | CI enforcement script |
| `ACTIVITY_DOMAIN_AUDIT.md` | Coverage analysis |

---

## 10. Violation Response

When CI fails:

1. **Read the error** — rule ID tells you exactly what's wrong
2. **Check the registry** — is the capability declared?
3. **Check the contract** — is the action forbidden?
4. **Fix the violation** — don't work around it

**Rule:** Contracts evolve through governance. Bypasses do not.
