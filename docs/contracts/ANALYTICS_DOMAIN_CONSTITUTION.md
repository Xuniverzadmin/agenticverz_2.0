# Analytics Domain Constitution

**Status:** RATIFIED
**Effective:** 2026-01-17
**Reference:** PIN-411, ANALYTICS_DOMAIN_AUDIT.md

---

## Preamble

This constitution establishes the permanent governance framework for the Analytics domain.
It cannot be amended without explicit founder approval and must be enforced mechanically.

The Analytics domain answers: **"How much am I spending and where?"**

---

## Article I: Domain Identity

### ANL-IDENT-001: Analytics is a First-Class Domain

> Analytics is the 6th primary domain in the Customer Console sidebar.

**Position:** 6 (after Logs, before Account)
**Icon:** BarChart2
**Status:** FROZEN

This position cannot be changed without constitutional amendment.

### ANL-IDENT-002: Subdomain Structure

```
Analytics
 └─ Statistics
     ├─ Usage (Topic v1)
     └─ Cost (Topic v2)
```

Future topics (Budgets, Anomalies) must be added under Statistics or as new subdomains.

---

## Article II: Unified Facade

### ANL-FACADE-001: Single Entry Point

> All Analytics data access MUST go through the unified facade at `/api/v1/analytics/*`.

**Rationale:** Prevents fragmentation, ensures consistent auth, enables capability discovery.

**Enforcement:**
- Location: `backend/app/api/analytics.py`
- Direct access to cost services is FORBIDDEN from API routes
- All endpoints must be registered in the facade router

```python
# CORRECT: Access via facade
GET /api/v1/analytics/statistics/cost

# FORBIDDEN: Direct service access from routes
from app.services.cost_write_service import CostWriteService  # NO
```

### ANL-FACADE-002: Capability Discovery

> The `_status` endpoint MUST accurately reflect all available topics and their capabilities.

**Enforcement:**
- Location: `GET /api/v1/analytics/_status`
- Must return: domain, subdomains, topics with read/write/signals_bound
- Topics MUST NOT be listed if endpoints don't exist

```json
{
  "domain": "analytics",
  "subdomains": ["statistics"],
  "topics": {
    "usage": {"read": true, "write": false, "signals_bound": 3},
    "cost": {"read": true, "write": false, "signals_bound": 1}
  }
}
```

---

## Article III: Signal Source Authority

### ANL-SIGNAL-001: Cost Data Source

> Cost statistics MUST be sourced from the `cost_records` table only.

**Rationale:** Single source of truth for attributed spend.

**Schema Contract:**
```sql
cost_records (
  tenant_id,      -- Tenant isolation
  user_id,        -- Actor attribution
  feature_tag,    -- Feature attribution
  model,          -- Model attribution
  cost_cents,     -- Spend amount
  input_tokens,   -- Input consumption
  output_tokens,  -- Output consumption
  created_at      -- Timestamp
)
```

### ANL-SIGNAL-002: Usage Data Sources

> Usage statistics MAY be reconciled from multiple signal sources.

**Authorized Sources:**
| Signal | Table | Semantic |
|--------|-------|----------|
| `cost_records` | cost_records | Token consumption |
| `llm.usage` | runs | LLM execution count |
| `worker.execution` | aos_traces | Worker execution count |
| `gateway.metrics` | (derived) | API request count |

**Reconciliation Rules:** See `SIGNAL_RECONCILIATION_RULES_V1.md`

---

## Article IV: Tenant Isolation

### ANL-TENANT-001: Mandatory Tenant Scoping

> All Analytics queries MUST be scoped to the authenticated tenant.

**Rationale:** Prevents cross-tenant data leakage.

**Enforcement:**
```python
# MANDATORY in every query
WHERE tenant_id = :tenant_id
```

**Violation Response:**
```
ANL-TENANT-001 VIOLATION: Query missing tenant scope.

All Analytics queries MUST include:
  WHERE tenant_id = :tenant_id

Cross-tenant queries are FORBIDDEN.
```

### ANL-TENANT-002: API Key Tenant Binding

> API keys MUST resolve to exactly one tenant_id.

**Governance Reference:** `docs/governance/API_KEY_GOVERNANCE.md`

**Enforcement:**
- API key hash → tenant_id mapping in `api_keys` table
- MachineCapabilityContext MUST have tenant_id attribute
- Missing tenant_id → 401 Unauthorized

---

## Article V: Export Parity

### ANL-EXPORT-001: Bit-Equivalent Exports

> CSV and JSON exports MUST be bit-equivalent to the read API response.

**Rationale:** Exports are for audit/compliance; drift creates liability.

**Enforcement:**
- Same aggregation logic for read and export
- Same time window validation
- Same tenant scoping

```python
# Shared helper ensures parity
async def _get_cost_data(session, tenant_id, from_ts, to_ts, resolution):
    # Used by BOTH /statistics/cost AND /statistics/cost/export.*
```

### ANL-EXPORT-002: CSV Header Contract

> CSV exports MUST use the documented header format.

**Usage CSV:**
```
timestamp,requests,compute_units,tokens
```

**Cost CSV:**
```
timestamp,spend_cents,requests,input_tokens,output_tokens
```

These headers are FROZEN. Changes require constitutional amendment.

---

## Article VI: Time Window Constraints

### ANL-TIME-001: Maximum Window Duration

> Time window MUST NOT exceed 90 days.

**Rationale:** Performance, cost, cardinality control.

**Enforcement:**
```python
if (to_ts - from_ts).days > 90:
    raise HTTPException(400, "Time window cannot exceed 90 days")
```

### ANL-TIME-002: Resolution Options

> Resolution MUST be one of: `hour`, `day`.

**Enforcement:**
```python
class ResolutionType(str, Enum):
    HOUR = "hour"
    DAY = "day"
```

---

## Article VII: Breakdowns

### ANL-BREAKDOWN-001: By-Model Breakdown

> Cost statistics MUST include breakdown by model.

**Response Contract:**
```json
{
  "by_model": [
    {
      "model": "claude-sonnet-4-20250514",
      "spend_cents": 4.0,
      "requests": 2,
      "input_tokens": 893,
      "output_tokens": 2085,
      "pct_of_total": 100.0
    }
  ]
}
```

### ANL-BREAKDOWN-002: By-Feature Breakdown

> Cost statistics MUST include breakdown by feature tag.

**Response Contract:**
```json
{
  "by_feature": [
    {
      "feature_tag": "agent-execution",
      "spend_cents": 3.0,
      "requests": 1,
      "pct_of_total": 75.0
    }
  ]
}
```

---

## Article VIII: Error Handling

### ANL-ERROR-001: Graceful Degradation

> Empty results are valid; errors must be explicit.

**Valid Response (no data):**
```json
{
  "totals": {"spend_cents": 0, "requests": 0, ...},
  "series": [],
  "by_model": [],
  "by_feature": [],
  "signals": {"sources": ["none"], "freshness_sec": 0}
}
```

**Error Response:**
```json
{
  "detail": "Time window cannot exceed 90 days"
}
```

### ANL-ERROR-002: Signal Freshness

> Response MUST include signal metadata with freshness indicator.

**Enforcement:**
```json
{
  "signals": {
    "sources": ["cost_records"],
    "freshness_sec": 1952443
  }
}
```

`freshness_sec` = seconds since most recent data point.

---

## Article IX: Amendment Process

This constitution can only be amended with:
1. Explicit founder approval
2. Documented rationale in PIN
3. Mechanical enforcement update
4. Update to ANALYTICS_DOMAIN_AUDIT.md

"Temporary" exceptions are prohibited. Optionalization is prohibited.

---

## Article X: Verification Requirements

### ANL-VERIFY-001: E2E Testing Required

> Any change to Analytics endpoints MUST be verified with E2E tests.

**Test Requirements:**
1. Use real database (Neon)
2. Use valid API key with tenant mapping
3. Verify response structure matches contract
4. Verify export parity

**Reference:** `ANALYTICS_DOMAIN_AUDIT.md` Section 11 (E2E Verification)

---

## Signatures

- **Author:** Claude (Analytics Cost Wiring)
- **Date:** 2026-01-17
- **Status:** RATIFIED (pending founder ratification)
