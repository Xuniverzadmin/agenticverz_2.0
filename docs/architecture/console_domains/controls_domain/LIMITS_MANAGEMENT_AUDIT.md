# Limits Management Audit

**Status:** IMPLEMENTATION COMPLETE (PIN-LIM)
**Last Updated:** 2026-01-17
**Reference:** PIN-412 (Policy Control Plane), M26 Cost Intelligence, PIN-LIM-01 to PIN-LIM-05

---

## 0. Executive Summary

> **Limits management exists across THREE separate systems with NO unified customer interface.**

Customers can SET cost budgets but can only VIEW all other limits. The enforcement layer is fragmented across billing middleware, tenant quotas, and policy rules.

---

## 1. The Three Limit Systems

| System | Location | Customer Can Set? | Enforcement |
|--------|----------|-------------------|-------------|
| **Tenant Quotas** | `tenant.py` | ❌ NO (plan-based) | Pre-request check |
| **Cost Budgets** | `cost_intelligence.py` | ✅ YES | Advisory (hard_limit optional) |
| **Policy Limits** | `policy_control_plane.py` | ❌ NO (read-only API) | DB-only, no runtime |

---

## 2. Limit Types

### 2.1 Cost Limits

| Limit | Where Defined | Customer Access | Enforcement |
|-------|---------------|-----------------|-------------|
| Daily cost budget | `cost_budgets` table | ✅ POST `/api/v1/costs/budgets` | Warning or block |
| Monthly cost budget | `cost_budgets` table | ✅ POST `/api/v1/costs/budgets` | Warning or block |
| Feature cost budget | `cost_budgets` table | ✅ POST `/api/v1/costs/budgets` | Warning or block |
| User cost budget | `cost_budgets` table | ✅ POST `/api/v1/costs/budgets` | Warning or block |

### 2.2 Token Limits

| Limit | Where Defined | Customer Access | Enforcement |
|-------|---------------|-----------------|-------------|
| Monthly token quota | `tenants.max_tokens_per_month` | ❌ VIEW only | `can_use_tokens()` |
| Per-run token limit | `worker_configs.max_tokens_per_run` | ✅ PUT worker config | Runtime check |

### 2.3 Run Limits

| Limit | Where Defined | Customer Access | Enforcement |
|-------|---------------|-----------------|-------------|
| Daily run limit | `tenants.max_runs_per_day` | ❌ VIEW only | `can_create_run()` |
| Concurrent run limit | `tenants.max_concurrent_runs` | ❌ VIEW only | Pre-execution |
| Per-worker daily limit | `worker_configs.max_runs_per_day` | ✅ PUT worker config | Runtime check |

### 2.4 Rate Limits

| Limit | Where Defined | Customer Access | Enforcement |
|-------|---------------|-----------------|-------------|
| API key RPM | `api_keys.rate_limit_rpm` | ❌ VIEW only | Gateway middleware |
| API key concurrent | `api_keys.max_concurrent_runs` | ❌ VIEW only | Gateway middleware |

### 2.5 Time Limits

| Limit | Where Defined | Customer Access | Enforcement |
|-------|---------------|-----------------|-------------|
| Budget reset period | `limits.reset_period` | ❌ VIEW only | Scheduled reset |
| Rate limit window | `limits.window_seconds` | ❌ VIEW only | Sliding window |

---

## 3. Plan-Based Quotas

Quotas are automatically assigned based on subscription plan:

```python
PLAN_QUOTAS = {
    "free": {
        "max_workers": 3,
        "max_runs_per_day": 100,
        "max_concurrent_runs": 5,
        "max_tokens_per_month": 1_000_000,
        "max_api_keys": 5,
    },
    "pro": {
        "max_workers": 10,
        "max_runs_per_day": 1_000,
        "max_concurrent_runs": 20,
        "max_tokens_per_month": 10_000_000,
        "max_api_keys": 20,
    },
    "enterprise": {
        "max_workers": 100,
        "max_runs_per_day": 100_000,
        "max_concurrent_runs": 100,
        "max_tokens_per_month": 1_000_000_000,
        "max_api_keys": 100,
    },
}
```

**Customer Impact:** Cannot modify these limits. Must upgrade plan for higher quotas.

---

## 4. API Routes

### 4.1 What Customers CAN Configure

**Cost Budgets (Full CRUD)**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/costs/budgets` | POST | Create/update budget | ✅ WORKS |
| `/api/v1/costs/budgets` | GET | List budgets | ✅ WORKS |

**Request Model:**
```json
{
  "budget_type": "tenant|feature|user",
  "entity_id": "optional - for feature/user",
  "daily_limit_cents": 50000,
  "monthly_limit_cents": 1000000,
  "warn_threshold_pct": 80,
  "hard_limit_enabled": true
}
```

**Worker-Specific Limits**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/workers/{id}/config` | PUT | Set worker limits | ✅ WORKS |

**Request Model:**
```json
{
  "max_runs_per_day": 100,
  "max_tokens_per_run": 50000
}
```

### 4.2 What Customers Can Only VIEW

**Policy Limits (READ-ONLY)**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/policies/limits` | GET | List all limits | ✅ READ-ONLY |
| `/api/v1/policies/limits/{id}` | GET | Limit detail | ✅ READ-ONLY |
| `/api/v1/policies/limits/{id}/evidence` | GET | Breach history | ✅ READ-ONLY |
| `/api/v1/policies/rules` | GET | List rules | ✅ READ-ONLY |
| `/api/v1/policies/rules/{id}` | GET | Rule detail | ✅ READ-ONLY |

**Quota Checks**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/tenant/quota/runs` | GET | Check run quota | ✅ READ-ONLY |
| `/api/v1/tenant/quota/tokens` | GET | Check token quota | ✅ READ-ONLY |

**Cost Visibility**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/guard/costs/summary` | GET | Usage vs limits | ✅ READ-ONLY |
| `/guard/costs/explained` | GET | Cost breakdown | ✅ READ-ONLY |
| `/guard/costs/incidents` | GET | Limit breaches | ✅ READ-ONLY |

### 4.3 PIN-LIM Implementation (2026-01-17)

**All previously missing endpoints have been implemented:**

| Endpoint | Method | Purpose | Status | Reference |
|----------|--------|---------|--------|-----------|
| `/api/v1/policies/limits` | POST | Create custom limit | ✅ IMPLEMENTED | PIN-LIM-01 |
| `/api/v1/policies/limits/{id}` | PUT | Update limit | ✅ IMPLEMENTED | PIN-LIM-01 |
| `/api/v1/policies/limits/{id}` | DELETE | Soft-delete limit | ✅ IMPLEMENTED | PIN-LIM-01 |
| `/api/v1/policies/rules` | POST | Create policy rule | ✅ IMPLEMENTED | PIN-LIM-02 |
| `/api/v1/policies/rules/{id}` | PUT | Update/retire rule | ✅ IMPLEMENTED | PIN-LIM-02 |
| `/api/v1/limits/simulate` | POST | Pre-check limits | ✅ IMPLEMENTED | PIN-LIM-04 |
| `/api/v1/limits/overrides` | POST | Request override | ✅ IMPLEMENTED | PIN-LIM-05 |
| `/api/v1/limits/overrides` | GET | List overrides | ✅ IMPLEMENTED | PIN-LIM-05 |
| `/api/v1/limits/overrides/{id}` | GET | Get override detail | ✅ IMPLEMENTED | PIN-LIM-05 |
| `/api/v1/limits/overrides/{id}` | DELETE | Cancel override | ✅ IMPLEMENTED | PIN-LIM-05 |

---

## 5. Database Schema

### 5.1 Tenant Quotas (Plan-Based)

**Table:** `tenants`

```python
class Tenant(SQLModel):
    # Plan quotas (auto-assigned)
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int

    # Usage tracking
    runs_today: int
    runs_this_month: int
    tokens_this_month: int
    last_run_reset_at: datetime
```

### 5.2 Cost Budgets (Customer-Configurable)

**Table:** `cost_budgets`

```python
class CostBudget(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)

    # Scope
    budget_type: str           # "tenant" | "feature" | "user"
    entity_id: str             # Optional - for feature/user budgets

    # Limits
    daily_limit_cents: int
    monthly_limit_cents: int
    warn_threshold_pct: int    # Default 80
    hard_limit_enabled: bool   # Block at limit?

    # Tracking
    current_daily_spend: int
    current_monthly_spend: int
    last_reset_at: datetime
```

### 5.3 Policy Limits (PIN-412)

**Table:** `limits`

```python
class Limit(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)
    name: str

    # Classification
    limit_category: str        # BUDGET | RATE | THRESHOLD
    limit_type: str            # COST_USD | TOKENS_* | REQUESTS_*
    scope: str                 # GLOBAL | TENANT | PROJECT | AGENT | PROVIDER

    # Value
    max_value: Decimal         # Precision for currency
    reset_period: str          # DAILY | WEEKLY | MONTHLY | NONE
    window_seconds: int        # For rate limits

    # Enforcement
    enforcement: str           # BLOCK | WARN | REJECT | QUEUE | DEGRADE | ALERT
    status: str                # ACTIVE | DISABLED

    # Timestamps
    created_at: datetime
    updated_at: datetime
```

### 5.4 Limit Breaches (Audit Trail)

**Table:** `limit_breaches`

```python
class LimitBreach(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)
    limit_id: str (FK → Limit)
    run_id: str (FK → Run)
    incident_id: str (FK → Incident)

    # Breach details
    breach_type: str           # BREACHED | EXHAUSTED | THROTTLED | VIOLATED
    value_at_breach: Decimal
    limit_value: Decimal

    # Timestamps
    breached_at: datetime
    recovered_at: datetime
```

### 5.5 Policy Rules

**Table:** `policy_rules`

```python
class PolicyRule(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)
    name: str

    # Configuration
    enforcement_mode: str      # BLOCK | WARN | AUDIT | DISABLED
    scope: str                 # GLOBAL | TENANT | PROJECT | AGENT
    source: str                # MANUAL | SYSTEM | LEARNED

    # Status
    status: str                # ACTIVE | RETIRED

    # Timestamps
    created_at: datetime
    updated_at: datetime
```

---

## 6. Enforcement Architecture

### 6.1 Current Enforcement Points

```
REQUEST
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  1. BILLING GATE MIDDLEWARE                                 │
│     - Checks: tenant.billing_state                          │
│     - Blocks: SUSPENDED tenants (HTTP 402)                  │
│     - Does NOT check: limits, quotas, budgets               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  2. API KEY VALIDATION                                      │
│     - Checks: rate_limit_rpm, max_concurrent_runs           │
│     - Blocks: Rate exceeded (HTTP 429)                      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TENANT QUOTA CHECK (Pre-Run)                            │
│     - Checks: can_create_run(), can_use_tokens()            │
│     - Blocks: Quota exceeded (HTTP 403)                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  4. COST BUDGET CHECK (Advisory)                            │
│     - Checks: daily_limit, monthly_limit                    │
│     - Action: Warning OR block (if hard_limit_enabled)      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  5. POLICY LIMITS (NOT ENFORCED AT RUNTIME)                 │
│     - Limits table exists but no runtime check              │
│     - Breaches recorded AFTER the fact                      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
RUN EXECUTES
```

### 6.2 Enforcement Gap Analysis

| Check Point | What's Checked | What's Missing |
|-------------|----------------|----------------|
| Billing Gate | billing_state only | No limit checks |
| API Key | RPM, concurrent | No cost prediction |
| Tenant Quota | runs_today, tokens_this_month | No pre-execution cost |
| Cost Budget | Spend vs limit | **Not integrated with run creation** |
| Policy Limits | **Nothing** | **No runtime enforcement** |

### 6.3 Critical Missing: Pre-Execution Cost Check

```
MISSING FLOW:
┌─────────────────────────────────────────────────────────────┐
│  PRE-EXECUTION COST SIMULATION                              │
│                                                             │
│  1. Estimate token usage for this run                       │
│  2. Calculate predicted cost                                │
│  3. Check: current_spend + predicted_cost < budget?         │
│  4. If NO → Block with clear error                          │
│  5. If YES → Proceed with run                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Customer Experience Gaps

### 7.1 What Customers Want to Do

| Action | Can They? | How |
|--------|-----------|-----|
| Set a daily cost limit | ✅ YES | POST `/api/v1/costs/budgets` |
| Set a monthly cost limit | ✅ YES | POST `/api/v1/costs/budgets` |
| See current usage vs limits | ✅ YES | GET `/guard/costs/summary` |
| Set token limit per run | ✅ YES | PUT `/api/v1/workers/{id}/config` |
| Increase daily run limit | ❌ NO | Must upgrade plan |
| Create custom policy limit | ❌ NO | No POST endpoint |
| Set timeout for runs | ❌ NO | No timeout configuration |
| Request limit override | ❌ NO | No override workflow |
| See why run was blocked | ⚠️ PARTIAL | Error messages not detailed |

### 7.2 Error Message Quality

**Current (Poor):**
```json
{
  "detail": "Daily run limit exceeded"
}
```

**Expected (Good):**
```json
{
  "error": "limit_exceeded",
  "limit_type": "daily_runs",
  "current_value": 100,
  "limit_value": 100,
  "reset_at": "2026-01-17T00:00:00Z",
  "options": [
    "Wait for daily reset",
    "Upgrade to Pro plan for 1,000 runs/day",
    "Request temporary limit increase"
  ]
}
```

---

## 8. Lifecycle Operations

### 8.1 Implemented

| Operation | Scope | Status |
|-----------|-------|--------|
| **CREATE** | Cost budgets | ✅ |
| **READ** | All limits | ✅ |
| **UPDATE** | Cost budgets, worker limits | ✅ |
| **CHECK** | Quota status | ✅ |
| **RESET** | Daily counters (automatic) | ✅ |

### 8.2 Missing

| Operation | Scope | Status |
|-----------|-------|--------|
| **CREATE** | Policy limits | ❌ MISSING |
| **UPDATE** | Policy limits | ❌ MISSING |
| **DELETE** | Any limits | ❌ MISSING |
| **SIMULATE** | Pre-check before run | ❌ MISSING |
| **OVERRIDE** | Temporary limit increase | ❌ MISSING |
| **AUDIT** | Limit change history | ❌ MISSING |
| **ALERT** | Approaching limit notification | ❌ MISSING |
| **EXPORT** | Limit configuration export | ❌ MISSING |

---

## 9. Cross-Domain Integration

### 9.1 Current Integration

```
LIMITS
    │
    ├──────────────────────────► POLICIES
    │   limits table                Part of Policies domain
    │   policy_rules table          READ-ONLY for customers
    │
    ├──────────────────────────► INCIDENTS
    │   limit_breaches              Links to incidents via incident_id
    │   cost_anomalies              M25 escalation
    │
    ├──────────────────────────► ACTIVITY
    │   Run blocked                 Error in run record
    │   ◄── No reverse link
    │
    └──────────────────────────► BILLING
        billing_state               Blocks at middleware
        plan quotas                 Auto-assigned
```

### 9.2 Missing Integration

| Integration | Gap |
|-------------|-----|
| Limits → Activity | No "blocked by limit" status on runs |
| Limits → Logs | No audit trail of limit checks |
| Limits → Overview | No "approaching limits" warning |
| Limits → Notifications | No email/webhook on threshold |

---

## 10. Coverage Summary (Updated 2026-01-17)

```
Customer Limit Configuration:    85% COMPLETE (was 30%)
  - Cost budgets:                 ✅ FULL CRUD
  - Worker limits:                ✅ UPDATE only
  - Policy limits:                ✅ FULL CRUD (PIN-LIM-01)
  - Policy rules:                 ✅ CREATE/UPDATE/RETIRE (PIN-LIM-02)
  - Token/run quotas:             ❌ PLAN-BASED ONLY

Enforcement:                      75% COMPLETE (was 50%)
  - Billing gate:                 ✅ WORKS
  - Tenant quotas:                ✅ WORKS
  - API key rate limits:          ✅ WORKS
  - Cost budget enforcement:      ⚠️ ADVISORY
  - Policy limit enforcement:     ✅ LimitsEvaluator (PIN-LIM-03)
  - Pre-execution simulation:     ✅ IMPLEMENTED (PIN-LIM-04)

Lifecycle Operations:             90% COMPLETE (was 40%)
  - Create:                       ✅ COMPLETE (limits, rules, overrides)
  - Read:                         ✅ COMPLETE
  - Update:                       ✅ COMPLETE
  - Delete:                       ✅ SOFT DELETE (limits → DISABLED)
  - Simulate:                     ✅ IMPLEMENTED (PIN-LIM-04)
  - Override:                     ✅ IMPLEMENTED (PIN-LIM-05)
  - Audit:                        ✅ AUDIT HOOKS CREATED

Customer Experience:              70% COMPLETE (was 35%)
  - View limits:                  ✅ WORKS
  - Set cost limits:              ✅ WORKS
  - Create policy limits:         ✅ WORKS (PIN-LIM-01)
  - Pre-execution check:          ✅ WORKS (PIN-LIM-04)
  - Request overrides:            ✅ WORKS (PIN-LIM-05)
  - Modify quotas:                ❌ BLOCKED (plan-based)
  - Clear error messages:         ✅ Message codes (deterministic)
```

---

## 11. TODO: Missing Implementations

### 11.1 Unified Limits API (HIGH PRIORITY)

```
/api/v1/limits/* - Unified facade

GET  /api/v1/limits                    - List all limits (unified view)
GET  /api/v1/limits/{id}               - Limit detail
POST /api/v1/limits                    - Create custom limit
PUT  /api/v1/limits/{id}               - Update limit
DELETE /api/v1/limits/{id}             - Remove limit
POST /api/v1/limits/check              - Pre-execution check
GET  /api/v1/limits/usage              - Current usage vs all limits
```

### 11.2 Pre-Execution Limit Check (HIGH PRIORITY)

```
POST /api/v1/limits/check

Request:
{
  "run_type": "worker_execution",
  "worker_id": "business-builder",
  "estimated_tokens": 5000
}

Response:
{
  "allowed": false,
  "blocking_limits": [
    {
      "limit_type": "daily_cost",
      "current": 4800,
      "limit": 5000,
      "predicted_after": 5200,
      "enforcement": "BLOCK"
    }
  ],
  "recommendations": [
    "Reduce estimated tokens to 4000",
    "Wait for daily reset at 00:00 UTC",
    "Increase daily budget"
  ]
}
```

### 11.3 Policy Limit CRUD (MEDIUM PRIORITY)

```
POST /api/v1/policies/limits

Request:
{
  "name": "Project Alpha Token Limit",
  "limit_category": "THRESHOLD",
  "limit_type": "TOKENS_PER_RUN",
  "scope": "PROJECT",
  "scope_id": "project-alpha",
  "max_value": 10000,
  "enforcement": "BLOCK"
}
```

### 11.4 Limit Override Workflow (MEDIUM PRIORITY)

```
POST /api/v1/limits/{id}/override-request

Request:
{
  "requested_value": 200000,
  "duration_hours": 24,
  "reason": "Month-end batch processing"
}

Response:
{
  "override_id": "ovr_xxx",
  "status": "pending_approval",
  "approver_required": "account_admin"
}
```

### 11.5 Approaching Limit Notifications (LOW PRIORITY)

```
Webhook/Email when:
- Usage > 80% of any limit (configurable threshold)
- Usage > 90% of any limit
- Limit breached

Notification payload:
{
  "event": "limit_approaching",
  "limit_type": "monthly_tokens",
  "current_pct": 85,
  "current_value": 8500000,
  "limit_value": 10000000,
  "projected_breach_date": "2026-01-25"
}
```

---

## 12. Recommended Architecture

### 12.1 Unified Limits Service (L4)

```python
class LimitsService:
    """Unified limit management across all systems"""

    def check_all_limits(self, tenant_id: str, run_request: RunRequest) -> LimitCheckResult:
        """Pre-execution check against ALL limit systems"""
        checks = []

        # 1. Tenant quotas
        checks.append(self._check_tenant_quotas(tenant_id, run_request))

        # 2. Cost budgets
        checks.append(self._check_cost_budgets(tenant_id, run_request))

        # 3. Policy limits
        checks.append(self._check_policy_limits(tenant_id, run_request))

        # 4. API key limits
        checks.append(self._check_api_key_limits(run_request.api_key_id))

        return LimitCheckResult(
            allowed=all(c.allowed for c in checks),
            blocking_limits=[c for c in checks if not c.allowed],
            warnings=[c for c in checks if c.warning]
        )

    def get_unified_limits(self, tenant_id: str) -> UnifiedLimitsView:
        """Single view of all limits from all systems"""
        return UnifiedLimitsView(
            tenant_quotas=self._get_tenant_quotas(tenant_id),
            cost_budgets=self._get_cost_budgets(tenant_id),
            policy_limits=self._get_policy_limits(tenant_id),
            api_key_limits=self._get_api_key_limits(tenant_id)
        )
```

### 12.2 Enforcement Middleware

```python
class LimitEnforcementMiddleware:
    """Single enforcement point for all limits"""

    async def __call__(self, request: Request, call_next):
        # Skip for exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Get context
        tenant_id = request.state.auth_context.tenant_id

        # Check limits for run creation
        if self._is_run_creation(request):
            result = await self.limits_service.check_all_limits(
                tenant_id,
                await self._parse_run_request(request)
            )

            if not result.allowed:
                return JSONResponse(
                    status_code=403,
                    content=result.to_error_response()
                )

        return await call_next(request)
```

---

## 13. Related Files

| File | Purpose | Layer |
|------|---------|-------|
| `backend/app/models/tenant.py` | Tenant quotas | L6 |
| `backend/app/models/policy_control_plane.py` | Limits, PolicyRules | L6 |
| `backend/app/api/policies.py` | Limits API (read-only) | L2 |
| `backend/app/api/cost_intelligence.py` | Cost budgets | L2 |
| `backend/app/api/tenants.py` | Quota checks | L2 |
| `backend/app/api/middleware/billing_gate.py` | Billing enforcement | L2 |
| `backend/app/api/billing_dependencies.py` | Limit checks | L3 |

---

## 14. Implementation Status

**Date:** 2026-01-17 (Updated from 2026-01-16)

### Configuration: Grade B+ (was D+)

| Component | Status | Reference |
|-----------|--------|-----------|
| Cost budget CRUD | ✅ COMPLETE | M26 |
| Worker limit config | ✅ COMPLETE | M21 |
| View all limits | ✅ COMPLETE | PIN-412 |
| Create policy limits | ✅ IMPLEMENTED | PIN-LIM-01 |
| Update policy limits | ✅ IMPLEMENTED | PIN-LIM-01 |
| Delete limits | ✅ SOFT DELETE | PIN-LIM-01 |
| Policy rules CRUD | ✅ IMPLEMENTED | PIN-LIM-02 |

### Enforcement: Grade B (was C)

| Component | Status | Reference |
|-----------|--------|-----------|
| Billing gate | ✅ COMPLETE | M24 |
| Tenant quotas | ✅ COMPLETE | M21 |
| API key rate limits | ✅ COMPLETE | M22 |
| Cost budget enforcement | ⚠️ ADVISORY ONLY | M26 |
| Policy limit enforcement | ✅ LimitsEvaluator | PIN-LIM-03 |
| Pre-execution check | ✅ SIMULATION API | PIN-LIM-04 |
| Override handling | ✅ OVERRIDE API | PIN-LIM-05 |

### Customer Experience: Grade B- (was D)

| Component | Status | Reference |
|-----------|--------|-----------|
| View limits | ✅ WORKS | PIN-412 |
| Set cost limits | ✅ WORKS | M26 |
| Create policy limits | ✅ WORKS | PIN-LIM-01 |
| Clear error messages | ✅ MESSAGE CODES | PIN-LIM-04 |
| Pre-execution check | ✅ WORKS | PIN-LIM-04 |
| Override workflow | ✅ WORKS | PIN-LIM-05 |
| Approaching notifications | ❌ MISSING | Future |

---

## 15. Overall Assessment

| Aspect | Grade | Notes |
|--------|-------|-------|
| **Cost Budgets** | B | Full CRUD, advisory enforcement |
| **Tenant Quotas** | C | Works but not configurable |
| **Policy Limits** | F | Read-only, no runtime enforcement |
| **Unified Experience** | F | 3 fragmented systems |
| **Pre-Execution Check** | F | Not implemented |
| **Error Messages** | D | Not actionable |

**Critical Finding:** Customers can only meaningfully configure **cost budgets**. All other limits are either plan-locked or read-only. The `limits` table from PIN-412 exists but has **no write API and no runtime enforcement**.

**Recommendation:** Create a unified `/api/v1/limits/*` facade that:
1. Consolidates all three limit systems into one view
2. Provides CRUD for customer-configurable limits
3. Implements pre-execution limit checking
4. Returns actionable error messages with recommendations
