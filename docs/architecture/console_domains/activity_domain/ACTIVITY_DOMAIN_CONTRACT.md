# Activity Domain Contract

**Status:** ENFORCED
**Version:** 2.0
**Effective:** 2026-01-19
**Scope:** All Activity domain code (L2 facade, L4 services)
**Reference:** Activity Domain System Design, ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md

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

### L4 — Activity Domain Facade

**File:** `backend/app/services/activity_facade.py`
**Getter:** `get_activity_facade()` (singleton)

The Activity Facade is the single entry point for all activity business logic. L2 API routes
must call facade methods rather than implementing inline SQL queries or calling services directly.

**Pattern:**
```python
from app.services.activity_facade import get_activity_facade

facade = get_activity_facade()
result = await facade.get_runs(session, tenant_id, ...)
```

**Operations Provided:**
- `get_runs()` - List runs with filters (V1)
- `get_run_detail()` - Run detail O3
- `get_run_evidence()` - Run evidence O4
- `get_run_proof()` - Run integrity proof O5
- `get_status_summary()` - Status breakdown
- `get_live_runs()` - V2 live runs with policy context
- `get_completed_runs()` - V2 completed runs with policy context
- `get_signals()` - V2 synthesized attention signals
- `get_metrics()` - V2 activity metrics
- `get_threshold_signals()` - V2 threshold proximity signals
- `get_risk_signals()` - Risk signal aggregates
- `get_patterns()` - Pattern detection (SIG-O3)
- `get_cost_analysis()` - Cost anomalies (SIG-O4)
- `get_attention_queue()` - Attention ranking (SIG-O5)
- `acknowledge_signal()` - Signal acknowledgment
- `suppress_signal()` - Signal suppression

**Facade Rules:**
- L2 routes call facade methods, never direct SQL
- Facade returns typed dataclass results (not ORM objects)
- Facade handles tenant isolation internally
- Facade delegates to specialized services where appropriate

**Service Delegation:**

The facade delegates signal analysis operations to specialized L4 services:

| Facade Method | L4 Service | Service Method |
|---------------|------------|----------------|
| `get_patterns()` | `PatternDetectionService` | `detect_patterns()` |
| `get_cost_analysis()` | `CostAnalysisService` | `analyze_costs()` |
| `get_attention_queue()` | `AttentionRankingService` | `get_attention_queue()` |
| `acknowledge_signal()` | `SignalFeedbackService` | `acknowledge_signal()` |
| `suppress_signal()` | `SignalFeedbackService` | `suppress_signal()` |

**L2-to-L4 Result Type Mapping:**

L2 endpoints contain mapping logic to transform L4 domain results into L2 response models.
This preserves API backwards compatibility while allowing L4 services to evolve independently.

| L4 Service Result | L2 Response Model | Mapping Notes |
|-------------------|-------------------|---------------|
| `PatternDetectionResult` | `PatternDetectionResponse` | `window_start/end` computed from `generated_at + window_hours` |
| `DetectedPattern` | `PatternMatchResponse` | `run_id` from `affected_run_ids[0]`, `details` built from fields |
| `CostAnalysisResult` | `CostAnalysisResponse` | `anomalies` mapped to `agents` for backwards compat |
| `AttentionQueueResult` | `AttentionQueueResponse` | `items` mapped to `queue` with field transformation |
| `AcknowledgeResult` | `SignalAckResponse` | Direct field mapping |
| `SuppressResult` | `SignalSuppressResponse` | `signal_id` → `signal_fingerprint` |

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

### Rule: Topic-Scoped Endpoints (TOPIC-SCOPED-ENDPOINT-001)

**Status:** MANDATORY
**Effective:** 2026-01-18
**Reference:** `docs/governance/CAPABILITY_SURFACE_RULES.md`, `design/l2_1/INTENT_LEDGER.md`

When a capability serves panels in different topics (LIVE vs COMPLETED), the data scope MUST be enforced at the API boundary via **topic-scoped endpoints**.

**Pattern:**
```
/api/v1/activity/runs/{topic}/by-dimension
```

**Examples:**
- `/api/v1/activity/runs/live/by-dimension` → state=LIVE (hardcoded)
- `/api/v1/activity/runs/completed/by-dimension` → state=COMPLETED (hardcoded)

**Rules:**

| DO | DON'T |
|----|-------|
| Create topic-scoped endpoints with hardcoded state | Expose optional state filter to panels |
| Inject state at the endpoint boundary | Accept state from query params for panel use |
| Name endpoints to reflect topic: `/runs/live/...` | Use generic endpoints for topic-bound panels |

**Generic Endpoint Disposition:**
- Generic endpoints (e.g., `/runs/by-dimension`) MUST be marked as internal/admin-only
- Generic endpoints MUST NOT be bound to panels
- Generic endpoints SHOULD be deprecated if no admin use case exists

**Rationale:** Topic determines what data a panel sees. Caller-controlled filtering creates data leakage risk.

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

Every UI panel must bind to one or more capabilities:

| Panel | Capability | Status | Notes |
|-------|------------|--------|-------|
| ACT-LLM-LIVE-O1 | `activity.live_runs` | OBSERVED | E2E validated |
| ACT-LLM-LIVE-O2 | `activity.risk_signals` | DECLARED | Uses `/risk-signals` endpoint |
| ACT-LLM-LIVE-O3 | `activity.live_runs` | OBSERVED | Near-threshold runs |
| ACT-LLM-LIVE-O4 | `activity.runtime_traces` | OBSERVED | Telemetry/evidence status |
| ACT-LLM-LIVE-O5 | `activity.runs_by_dimension` | DECLARED | Topic-scoped: `/runs/live/by-dimension` |
| ACT-LLM-LIVE-O5 | `activity.summary_by_status` | OBSERVED | Shared with COMP-O2, COMP-O3 |
| ACT-LLM-LIVE-O5 | `activity.cost_analysis` | DECLARED | Shared with SIG-O4 |
| ACT-LLM-COMP-O1 | `activity.completed_runs` | OBSERVED | E2E validated |
| ACT-LLM-COMP-O2 | `activity.summary_by_status` | OBSERVED | Success count from status breakdown |
| ACT-LLM-COMP-O3 | `activity.summary_by_status` | OBSERVED | Failed count from FAILED bucket |
| ACT-LLM-COMP-O4 | `activity.completed_runs` | OBSERVED | Near-limit runs |
| ACT-LLM-COMP-O5 | `activity.run_detail` | OBSERVED | Aborted/cancelled runs |
| ACT-LLM-SIG-O1 | `activity.signals` | OBSERVED | Attention surface |
| ACT-LLM-SIG-O2 | `activity.signals` | OBSERVED | Threshold proximity |
| ACT-LLM-SIG-O3 | `activity.patterns` | OBSERVED | Temporal patterns |
| ACT-LLM-SIG-O4 | `activity.cost_analysis` | DECLARED | Economic deviations |
| ACT-LLM-SIG-O5 | `activity.signals` | OBSERVED | Attention queue |

**Notes:**
- ACT-LLM-LIVE-O5 and ACT-LLM-COMP-O5 share `activity.runs_by_dimension` capability but use topic-scoped endpoints per TOPIC-SCOPED-ENDPOINT-001.
- ACT-LLM-LIVE-O2 was wired to `activity.risk_signals` on 2026-01-18 (previously EMPTY).
- ACT-LLM-COMP-O3 was wired to `activity.summary_by_status` on 2026-01-18 (previously EMPTY).

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
| `docs/governance/CAPABILITY_SURFACE_RULES.md` | Topic-scoped endpoint rules |
| `design/l2_1/INTENT_LEDGER.md` | Panel intent and capability definitions |

---

## 10. Violation Response

When CI fails:

1. **Read the error** — rule ID tells you exactly what's wrong
2. **Check the registry** — is the capability declared?
3. **Check the contract** — is the action forbidden?
4. **Fix the violation** — don't work around it

**Rule:** Contracts evolve through governance. Bypasses do not.

---

## V2 EXTENSIONS (2026-01-19)

The following sections are added for Activity V2 migration with policy context integration.

---

## 11. Policy Context Integration (V2)

### Policy Context Shape (Mandatory)

Every Activity response that returns runs or signals MUST include:

```json
{
  "policy_context": {
    "policy_id": "lim-123",
    "policy_name": "Default Cost Guard",
    "policy_scope": "TENANT",
    "limit_type": "COST_USD",
    "threshold_value": 1.00,
    "threshold_unit": "USD",
    "threshold_source": "TENANT_OVERRIDE",
    "evaluation_outcome": "NEAR_THRESHOLD",
    "actual_value": 0.85
  }
}
```

### Policy Resolution Order (Deterministic)

When determining which policy limit applies to a run, resolve in this order:

```
1. Tenant-scoped ACTIVE limit (limits.scope = 'TENANT')
2. Project-scoped ACTIVE limit (limits.scope = 'PROJECT')
3. Agent-scoped ACTIVE limit (limits.scope = 'AGENT')
4. Provider-scoped ACTIVE limit (limits.scope = 'PROVIDER')
5. Global ACTIVE limit (limits.scope = 'GLOBAL')
6. SYSTEM_DEFAULT (virtual, no database record)
```

**Rules:**
- First match wins
- Only `status = 'ACTIVE'` limits are considered
- If no limit matches, use SYSTEM_DEFAULT
- Resolution is **deterministic** — same run always gets same limit

---

## 12. Evaluation Outcome Semantics (V2)

| Outcome | Definition | Trigger Condition |
|---------|------------|-------------------|
| `OK` | Run within all applicable limits | `actual_value < threshold * 0.8` |
| `NEAR_THRESHOLD` | Run approaching limit | `actual_value >= threshold * 0.8 AND actual_value < threshold` |
| `BREACH` | Run exceeded limit | `actual_value >= threshold` |
| `OVERRIDDEN` | Human override applied | `limit_breaches.breach_type = 'OVERRIDDEN'` |
| `ADVISORY` | System default, informational | No tenant/project/agent limit exists |

**Threshold Proximity:**
- `< 80%` → OK
- `80% - 99%` → NEAR_THRESHOLD
- `>= 100%` → BREACH

---

## 13. Signal Derivation Rules (V2)

Signals are **projections**, not stored entities. They are computed at query time.

### Signal Types

| signal_type | Derivation Rule |
|-------------|-----------------|
| `CRITICAL_FAILURE` | `status = 'failed' AND (risk_level = 'VIOLATED' OR incident_count > 0)` |
| `CRITICAL_SUCCESS` | `status = 'succeeded' AND incident_count = 0 AND policy_violation = false` |
| `NEAR_THRESHOLD` | `evaluation_outcome = 'NEAR_THRESHOLD'` |
| `AT_RISK` | `risk_level IN ('AT_RISK', 'VIOLATED')` |
| `EVIDENCE_DEGRADED` | `evidence_health IN ('DEGRADED', 'MISSING')` |

### Severity Mapping

| risk_level | severity |
|------------|----------|
| `VIOLATED` | `HIGH` |
| `AT_RISK` | `HIGH` |
| `NEAR_THRESHOLD` | `MEDIUM` |
| `NORMAL` | `LOW` |

### Reason Generation

| Condition | Reason Template |
|-----------|-----------------|
| Cost threshold | `"Cost at {proximity}% of ${threshold} limit"` |
| Time threshold | `"Execution time at {proximity}% of {threshold}ms limit"` |
| Token threshold | `"Token usage at {proximity}% of {threshold} limit"` |
| Incident created | `"Run created {count} incident(s)"` |
| Policy violation | `"Policy {policy_name} violated"` |

### Signal Rejection Rule

> **If a signal cannot cite a policy context, it must not exist.**

Signals without policy justification are invalid and must be filtered out.

### Signal Identity Rule — LOCKED

> Signals are attention cues, not compliance records.
> Authoritative state always resides with runs and policy evaluation.

**Signals Are:**
- Derived (computed at query time)
- Ephemeral (not stored)
- Ranked (by severity)
- Policy-justified (every signal cites policy_context)

**Signals Are NOT:**
- Stored entities
- Acknowledgeable actions
- Mutable records
- Authoritative compliance proof

**Never Do:**
- Create a `signals` table
- Add "acknowledge" or "dismiss" actions to signals
- Treat signals as durable records
- Use signals for audit/compliance purposes

---

## 14. Policy Context Non-Nullability (V2) — LOCKED RULE

**Authoritative Rule (POLICY-CONTEXT-001):**

> `policy_context` MUST be a **required, non-null field** in all V2 response models.

**Affected Models:**
- `RunSummaryV2`
- `SignalProjection`
- `ThresholdSignal`

**Fallback Behavior:**

If policy extraction fails (no matching limit):
```json
{
  "policy_context": {
    "policy_id": "SYSTEM_DEFAULT",
    "policy_name": "Default Safety Thresholds",
    "policy_scope": "GLOBAL",
    "limit_type": null,
    "threshold_value": null,
    "threshold_unit": null,
    "threshold_source": "SYSTEM_DEFAULT",
    "evaluation_outcome": "ADVISORY",
    "actual_value": null,
    "risk_type": null,
    "proximity_pct": null
  }
}
```

**Guarantees:**
- Schema truth — no optional/nullable policy_context
- No "silent missing governance"
- SYSTEM_DEFAULT makes governance visible from day zero

**Never Return:**
```json
{
  "policy_context": null  // FORBIDDEN
}
```

---

## 15. Advisory vs Authoritative Fields (V2)

### Authoritative (Source of Truth)

| Field | Source | Mutability |
|-------|--------|------------|
| `run_id` | runs table | Immutable |
| `state` | runs table | System-controlled |
| `status` | runs table | System-controlled |
| `started_at` | runs table | Immutable |
| `completed_at` | runs table | Immutable |
| `duration_ms` | Computed | Immutable |

### Advisory (Projections)

| Field | Source | Note |
|-------|--------|------|
| `risk_level` | v_runs_o2 | Derived from thresholds |
| `latency_bucket` | v_runs_o2 | Derived from duration |
| `evidence_health` | v_runs_o2 | Derived from trace presence |
| `policy_context` | JOIN to limits | Resolved at query time |
| `signal_type` | Computed | Projection over runs |
| `attention_score` | v_runs_o2 | Composite score |

**Rule:** Advisory fields may change if underlying policies change. Authoritative fields are immutable.

---

## 15. SYSTEM_DEFAULT Behavior (V2)

For new tenants or runs without applicable limits:

```json
{
  "policy_context": {
    "policy_id": "SYSTEM_DEFAULT",
    "policy_name": "Default Safety Thresholds",
    "policy_scope": "GLOBAL",
    "limit_type": null,
    "threshold_value": null,
    "threshold_unit": null,
    "threshold_source": "SYSTEM_DEFAULT",
    "evaluation_outcome": "ADVISORY",
    "actual_value": null
  }
}
```

**Purpose:**
- Prevents empty dashboards
- Makes governance visible from day zero
- Signals that no tenant-specific policy exists

---

## 16. Multi-Limit Handling (V2) — LOCKED RULE

**Scenario:** A run may trigger multiple limits (e.g., both COST and TIME).

**Authoritative Rule (MOST-SEVERE-WINS-001):**

> If multiple limits apply to a run, the evaluation with the highest severity
> (BREACH > OVERRIDDEN > NEAR_THRESHOLD > OK > ADVISORY) is authoritative.

**Resolution Order:**
1. `policy_context` contains the **most severe** evaluation
2. Severity order: `BREACH > OVERRIDDEN > NEAR_THRESHOLD > OK > ADVISORY`
3. If same severity, prefer by risk type: `COST > TIME > TOKENS > RATE`
4. Resolution is **deterministic** — same inputs always produce same output

**Invariants:**
- This rule is **non-optional** and **non-negotiable**
- Prevents ambiguous policy_context
- Prevents frontend misinterpretation
- Makes multi-limit behavior deterministic

**Future Enhancement:**
```json
{
  "policy_context": { /* most severe */ },
  "additional_limits": [
    { /* secondary limit 1 */ },
    { /* secondary limit 2 */ }
  ]
}
```

---

## 17. Evaluation Time Semantics (V2) — LOCKED RULE

**Scenario:** Admin updates a threshold while a run is LIVE.

**Authoritative Rule (EVAL-TIME-001):**

> Evaluation is performed against **the active limit set at evaluation time**.
> Historical views do **not retroactively re-evaluate** runs.

**Resolution:**
- Evaluation uses **limit value at evaluation time** (query time)
- Historical breach records preserve `limit_value` at breach time
- Run detail shows current evaluation, not historical
- `limit_breaches` table stores `limit_value` for audit trail

**Implications:**
1. A run's `evaluation_outcome` may change if queried after limit update
2. This is **intentional** — live dashboards reflect current policy state
3. For historical accuracy, consult `limit_breaches` table directly

**Why This Matters:**
- Prevents disputes when limits change
- Protects historical analytics integrity
- Makes "what if" analysis possible (compare current vs historical thresholds)

**Never Do:**
- Retroactively update historical breach records
- Re-evaluate completed runs against new limits for compliance purposes
- Assume `evaluation_outcome` is immutable

---

## 18. V2 Endpoint Invariants

### `/activity/live` (NEW)

| Invariant | Enforcement |
|-----------|-------------|
| Returns only `state = 'LIVE'` | Hardcoded WHERE clause |
| Includes `policy_context` | Response model validation |
| Never accepts `state` query param | Param not exposed |

### `/activity/completed` (NEW)

| Invariant | Enforcement |
|-----------|-------------|
| Returns only `state = 'COMPLETED'` | Hardcoded WHERE clause |
| Sorted by `completed_at DESC` | Hardcoded ORDER BY |
| Includes `policy_context` | Response model validation |

### `/activity/signals` (NEW)

| Invariant | Enforcement |
|-----------|-------------|
| Returns `SignalProjection`, not runs | Response model |
| Every signal has `policy_context` | Validation filter |
| Signals without policy are rejected | Pre-filter |

### `/activity/runs` (DEPRECATED)

| Invariant | Enforcement |
|-----------|-------------|
| Returns deprecation warning | Log + header |
| Not bound to any panel | CI guard |
| Blocked in production (future) | Feature flag |

---

## 19. V2 CI Enforcement Rules

| Rule ID | Description | Script |
|---------|-------------|--------|
| ACT-V2-001 | No panel may bind to `/runs` | `check_activity_deprecation.py` |
| ACT-V2-002 | Topic endpoints must not accept `state` param | OpenAPI validation |
| ACT-V2-003 | All responses must include `policy_context` | Response schema validation |
| ACT-V2-004 | Signals without policy must not exist | Projection filter |

---

## 20. Known Gaps (To Resolve During SDSR)

### GAP-SDSR-1: Additional Scenarios Needed

| Scenario | Panel Coverage |
|----------|----------------|
| LIVE run with evidence_health=DEGRADED | LIVE-O4 |
| COMPLETED run aborted by policy | COMP-O5 |
| Retry pattern detection | SIG-O3 |
| Cost anomaly detection | SIG-O4 |

### GAP-EDGE-1: Multi-Limit Handling

Document that `policy_context` returns the most severe evaluation.

### GAP-EDGE-2: Mid-Run Limit Change

Document that evaluation uses limit value at evaluation time.

### GAP-PHASE2: limit_breaches Extension

Deferred: Extend `limit_breaches` table with `evaluation_type` column.

---

## 21. Signal Feedback Rules

### SIGNAL-FEEDBACK-001
**Status:** ENFORCED

> Feedback annotations do not alter run state, policy evaluation, or signal derivation.

Feedback is **overlay metadata** stored in `audit_ledger`. It does not:
- Change the underlying run's status
- Affect policy evaluation logic
- Alter signal derivation rules

Signals remain computed projections. Feedback affects only visibility and ranking.

### SIGNAL-SUPPRESS-001
**Status:** ENFORCED

> Suppression is temporary (15-1440 minutes) and non-authoritative. Expiry is mandatory.

**Constraints:**
- Minimum duration: 15 minutes
- Maximum duration: 1440 minutes (24 hours)
- No permanent silencing allowed
- After expiry, signal reappears if still active

**Implementation:**
- `suppress_until` timestamp stored in `audit_ledger.after_state`
- Attention queue filters out suppressed signals where `suppress_until > NOW()`
- Signals endpoint includes `suppressed_until` in feedback field

### SIGNAL-ACK-001
**Status:** ENFORCED

> Acknowledgement records responsibility but does not silence signals.
> Acknowledged signals receive 0.6x ranking dampener (ATTN-DAMP-001).

**Guarantees:**
- Acknowledged signals remain visible
- `feedback.acknowledged = true` in responses
- Attention score dampened by 0.6x (idempotent)
- Audit trail preserved in `audit_ledger`

### SIGNAL-ID-001 (Canonical Fingerprint Source)
**Status:** LOCKED

> Signal identity MUST be derived from backend-computed projection, never client input.

**Implementation:**
- Fingerprint format: `sig-{sha256[:16]}`
- Derived from: `{run_id}:{signal_type}:{risk_type}:{evaluation_outcome}`
- Module: `app/services/activity/signal_identity.py`

**Never:**
- Accept client-supplied fingerprint as authoritative
- Trust path parameter fingerprint without validation
- Compute fingerprint from request body fields

### ATTN-DAMP-001 (Idempotent Dampening)
**Status:** FROZEN

> Acknowledgement dampening is idempotent and non-stacking (apply once, 0.6x).

**Constant:** `ACK_DAMPENER = 0.6` (frozen in `attention_ranking_service.py`)

**Logic:**
```python
if feedback.event_type == 'SignalAcknowledged':
    effective_score = base_score * 0.6
else:
    effective_score = base_score
# NEVER compound: no *= or repeated multiplication
```

### AUDIT-SIGNAL-CTX-001 (Structured Context)
**Status:** ENFORCED

> signal_context fields are fixed and versioned (no free-form blobs).

**Schema (v1.0):**
```python
class SignalContext(TypedDict):
    run_id: str
    signal_type: str           # COST_RISK, TIME_RISK, etc.
    risk_type: str             # COST, TIME, TOKENS, RATE
    evaluation_outcome: str    # BREACH, NEAR_THRESHOLD, OK
    policy_id: Optional[str]   # Governing policy if any
    schema_version: str        # "1.0"
```

### SIGNAL-SCOPE-001 (Tenant-Scoped Suppression)
**Status:** ENFORCED

> Suppression applies tenant-wide. actor_id is for accountability, not scoping.

**Implications:**
- A suppressed signal is hidden for all users in the tenant
- `actor_id` in audit entry shows who suppressed (accountability)
- No per-user suppression scope

---

## 22. Signal Feedback Endpoints

### POST `/api/v1/activity/signals/{signal_fingerprint}/ack`

**Purpose:** Acknowledge a signal to record responsibility.

**Request:**
```json
{
  "run_id": "run-abc",
  "signal_type": "COST_RISK",
  "risk_type": "COST",
  "comment": "Acknowledged"
}
```

**Response:**
```json
{
  "data": {
    "signal_fingerprint": "sig-a1b2c3d4e5f6g7h8",
    "acknowledged": true,
    "acknowledged_by": "user-123",
    "acknowledged_at": "2026-01-19T17:00:00Z"
  }
}
```

**Error Codes:**
- `409 Conflict`: Signal not currently visible

### POST `/api/v1/activity/signals/{signal_fingerprint}/suppress`

**Purpose:** Suppress a signal temporarily.

**Request:**
```json
{
  "run_id": "run-abc",
  "signal_type": "COST_RISK",
  "risk_type": "COST",
  "duration_minutes": 60,
  "reason": "Known issue"
}
```

**Response:**
```json
{
  "data": {
    "signal_fingerprint": "sig-a1b2c3d4e5f6g7h8",
    "suppressed_until": "2026-01-19T18:00:00Z"
  }
}
```

**Error Codes:**
- `400 Bad Request`: Invalid duration (must be 15-1440)
- `409 Conflict`: Signal not currently visible

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-19 | 2.1 | Added Signal Feedback Rules (Section 21-22) |
| 2026-01-19 | 2.0 | Policy context integration, V2 migration, topic-scoped endpoints |
| 2026-01-17 | 1.0 | Initial domain contract |
