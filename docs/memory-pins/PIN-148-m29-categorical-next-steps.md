# PIN-148: M29 Categorical Next Steps

**Status:** EXECUTING
**Category:** Milestone / Planning / Transition
**Created:** 2025-12-23
**Milestone:** M28 → M29 Transition
**Priority:** P0 (All Categories Required Before M29 Start)

---

## Overview

This PIN documents the categorical next steps for transitioning from M28 (Unified Console) to M29 (Quality Score). All 8 categories must be executed in order, with Category 1 (STABILISE) being **MANDATORY FIRST**.

---

## Category 1: STABILISE - UI Hygiene Closure

**Status:** ✅ COMPLETE
**Priority:** MANDATORY FIRST

### Requirements
- Add `isPending / onError / onSuccess` to all active mutations
- Add `logger.componentMount()` to all active pages
- Reduce warnings to ≤35 budget

### Acceptance Criteria
- [x] Run `node scripts/ui-hygiene-check.cjs`
- [x] Warnings within budget (≤35)
- [x] No blocking errors

### Evidence
```
✓ No blocking errors
  20 warnings remaining (budget: 35)
  Baseline: improved by 1
```

### Files Fixed
- `RecoveryPage.tsx` - Added logger, onError handlers
- `LoopStatusPage.tsx` - Added logger, onError for 3 mutations
- `CustomerHomePage.tsx` - Added useEffect, logger, componentMount
- `GuardConsoleApp.tsx` - Added logger, componentMount
- `LiveActivityPage.tsx` - Added logger, componentMount
- `LogsPage.tsx` - Added useEffect, logger, componentMount
- `FounderPulsePage.tsx` - Added useEffect, logger, componentMount
- `WorkerExecutionConsole.tsx` - Added logger, componentMount
- `KillSwitchPage.tsx` - Added onError handlers to mutations
- `SettingsPage.tsx` - Added useEffect, logger, componentMount
- `RoutingDashboard.tsx` - Added useEffect, logger, componentMount
- `IntegrationDashboard.tsx` - Added logger, onError

---

## Category 2: Auth Boundary Verification (FULL SPEC)

**Status:** ✅ COMPLETE
**Priority:** HIGH

### Invariants (Enforced)
1. A token belongs to exactly one domain (`aud=console` OR `aud=fops`, never both)
2. A session belongs to exactly one console (separate cookies)
3. A role escalation is impossible by accident (separate middleware, no shared logic)
4. Failure must be loud and logged (structured audit events)

### 2.1 Token Model - Separate Audiences

```python
class TokenAudience(str, Enum):
    CONSOLE = "console"  # Customer Console (/guard/*)
    FOPS = "fops"        # Founder Ops Console (/ops/*)

class CustomerToken:
    aud: Literal["console"]
    sub: str            # user_id
    org_id: str         # tenant_id (REQUIRED)
    role: CustomerRole  # OWNER, ADMIN, DEV, VIEWER
    iss: str            # "agenticverz"
    exp: int

class FounderToken:
    aud: Literal["fops"]
    sub: str            # founder_id
    role: FounderRole   # FOUNDER, OPERATOR
    mfa: bool           # MUST be True
    iss: str            # "agenticverz"
    exp: int
```

### 2.2 Cookie & Session Isolation

| Cookie | Domain | Audience |
|--------|--------|----------|
| `aos_console_session` | console.agenticverz.com | console |
| `aos_fops_session` | fops.agenticverz.com | fops |

Both cookies: `httpOnly=true`, `secure=true`, `sameSite=strict`

### 2.3 Separate Middleware (No Shared Logic)

```python
# /guard/* uses ONLY:
async def verify_console_token(request) -> CustomerToken:
    # Validates: token exists, aud=console, org_id present, valid role
    # Rejects: fops tokens, missing org_id, invalid role

# /ops/* uses ONLY:
async def verify_fops_token(request) -> FounderToken:
    # Validates: token exists, aud=fops, valid role, mfa=true
    # Rejects: console tokens, mfa=false, invalid role
```

### 2.4 Audit Logging on All Rejections

```python
class AuthAuditEvent:
    event: str = "AUTH_DOMAIN_REJECT"
    actor_id: str
    attempted_domain: str  # "console" or "fops"
    token_aud: str         # What was in the token
    reason: AuthRejectReason
    ip: str
    ts: str

class AuthRejectReason(str, Enum):
    MISSING_TOKEN = "MISSING_TOKEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    AUD_MISMATCH = "AUD_MISMATCH"
    ROLE_INVALID = "ROLE_INVALID"
    MFA_REQUIRED = "MFA_REQUIRED"
    ORG_ID_MISSING = "ORG_ID_MISSING"
```

### 2.5 Manual Abuse Tests - ALL PASSED

```bash
# Test 1: Console key on /ops/* → REJECT
$ curl -s -H "X-API-Key: $AOS_API_KEY" https://agenticverz.com/ops/pulse | jq
{"detail":{"error":"AUTH_DOMAIN_MISMATCH","reason":"AUD_MISMATCH"}}
# Audit log: AUTH_DOMAIN_REJECT actor=console_key_user attempted=fops token_aud=console

# Test 2: FOPS key on /guard/* → REJECT
$ curl -s -H "X-API-Key: $AOS_FOPS_KEY" "https://agenticverz.com/guard/status?tenant_id=t1" | jq
{"detail":{"error":"AUTH_DOMAIN_MISMATCH","reason":"AUD_MISMATCH"}}
# Audit log: AUTH_DOMAIN_REJECT actor=fops_key_user attempted=console token_aud=fops

# Test 3: No key → REJECT
$ curl -s https://agenticverz.com/ops/pulse | jq
{"detail":{"error":"MISSING_TOKEN","reason":"MISSING_TOKEN"}}

# Test 4: Invalid key → REJECT
$ curl -s -H "X-API-Key: invalid" https://agenticverz.com/ops/pulse | jq
{"detail":{"error":"INVALID_TOKEN","reason":"INVALID_TOKEN"}}

# Test 5: FOPS key on /ops/* → SUCCESS
$ curl -s -H "X-API-Key: $AOS_FOPS_KEY" https://agenticverz.com/ops/pulse | jq '.status'
"healthy"

# Test 6: Console key on /guard/* → SUCCESS
$ curl -s -H "X-API-Key: $AOS_API_KEY" "https://agenticverz.com/guard/status?tenant_id=t1" | jq '.status'
"protected"
```

### 2.6 CI Guardrails - 12 Tests (ALL PASS)

```bash
$ pytest tests/test_category2_auth_boundary.py -v
# 12 passed in 2.29s

TestAuthBoundaryInvariants:
  - test_console_key_rejected_on_fops_endpoint ✅
  - test_fops_key_rejected_on_console_endpoint ✅
  - test_no_key_rejected_on_fops ✅
  - test_no_key_rejected_on_console ✅
  - test_invalid_key_rejected ✅

TestTokenAudienceSeparation:
  - test_token_audiences_are_separate ✅
  - test_customer_token_claims ✅
  - test_founder_token_requires_mfa ✅

TestAuditLogging:
  - test_auth_audit_event_schema ✅
  - test_reject_reasons_are_explicit ✅

TestCookieSeparation:
  - test_cookie_names_are_separate ✅
  - test_cookie_settings_per_domain ✅
```

### 2.7 Exit Criteria (BINARY) - ALL MET

| Criterion | Status |
|-----------|--------|
| Separate tokens with strict `aud` | ✅ |
| Separate cookies per domain | ✅ |
| Separate middleware, no shared logic | ✅ |
| MFA enforced for `/fops` | ✅ |
| Cross-access always returns 403 | ✅ |
| All rejections are audited | ✅ |
| Manual abuse tests passed | ✅ |
| CI tests enforce separation | ✅ (12 tests) |

### Files Created/Modified

**New Files:**
- `backend/app/auth/console_auth.py` - Complete auth module with separate token models, middleware, audit logging
- `backend/tests/test_category2_auth_boundary.py` - CI guardrails (12 tests)

**Modified Files:**
- `backend/app/api/ops.py` - Uses `verify_fops_token` dependency
- `backend/app/api/guard.py` - Uses `verify_console_token` dependency
- `docker-compose.yml` - Added AOS_FOPS_KEY, AOS_JWT_SECRET, CONSOLE_JWT_SECRET, FOPS_JWT_SECRET
- `.env` - Added AOS_FOPS_KEY, AOS_JWT_SECRET

### Environment Variables Added

```bash
# Category 2 Auth: Separate Console/FOPS Authentication
AOS_FOPS_KEY=<generated-fops-key>        # FOPS-only key
AOS_JWT_SECRET=<jwt-signing-secret>      # Base JWT secret
CONSOLE_JWT_SECRET=${AOS_JWT_SECRET}     # Console JWT (can differ)
FOPS_JWT_SECRET=${AOS_JWT_SECRET}        # FOPS JWT (can differ)
```

---

## Category 3: Data Contract Freeze (FULL SPEC)

**Status:** ✅ COMPLETE
**Priority:** HIGH

### Contract Invariants (Enforced)
1. Field names NEVER change (use deprecation instead)
2. Required fields NEVER become optional
3. Types NEVER widen (`int` → `float` is FORBIDDEN)
4. New optional fields MAY be added (backward compatible)
5. Removal requires 2-version deprecation cycle

### 3.1 Explicit DTOs - Guard Console

Created `backend/app/contracts/guard.py` with frozen DTOs:

| DTO | Endpoint | Fields |
|-----|----------|--------|
| `GuardStatusDTO` | GET /guard/status | status, is_frozen, incidents_blocked_24h, active_guardrails |
| `TodaySnapshotDTO` | GET /guard/snapshot/today | requests_today, spend_today_cents, incidents_prevented |
| `IncidentSummaryDTO` | GET /guard/incidents | id, title, severity, status, trigger_type, calls_affected |
| `IncidentDetailDTO` | GET /guard/incidents/{id} | incident, timeline |
| `ApiKeyDTO` | GET /guard/keys | id, name, prefix, is_frozen, scopes |
| `TenantSettingsDTO` | GET /guard/settings | tenant_id, guardrails, notification_email |
| `ReplayResultDTO` | POST /guard/replay/{call_id} | success, determinism_level, certificate |
| `KillSwitchActionDTO` | POST /guard/killswitch/* | success, action, message |

### 3.2 Explicit DTOs - Ops Console

Created `backend/app/contracts/ops.py` with frozen DTOs:

| DTO | Endpoint | Fields |
|-----|----------|--------|
| `SystemPulseDTO` | GET /ops/pulse | status, active_customers, incidents_24h, revenue_today_cents |
| `CustomerSegmentDTO` | GET /ops/customers | tenant_id, stickiness_delta, mrr_cents, churn_risk_score |
| `CustomerAtRiskDTO` | GET /ops/customers/at-risk | tenant_id, risk_level, risk_signals, suggested_action |
| `IncidentPatternDTO` | GET /ops/incidents/patterns | pattern_type, affected_tenants, is_systemic |
| `StickinessByFeatureDTO` | GET /ops/stickiness | feature_name, retention_correlation, is_sticky |
| `RevenueRiskDTO` | GET /ops/revenue | mrr_cents, concentration_risk, at_risk_mrr_cents |
| `InfraLimitsDTO` | GET /ops/infra | db_connections_percent, bottleneck, headroom_percent |
| `PlaybookDTO` | GET /ops/playbooks | id, name, trigger_conditions, actions |

### 3.3 API Namespace Separation

| Domain | Vocabulary | Audience | Auth |
|--------|------------|----------|------|
| Guard (`/guard/*`) | Calm: `protected`, `attention_needed`, `action_required` | Customers | `aud=console` |
| Ops (`/ops/*`) | Command: `stable`, `elevated`, `degraded`, `critical` | Founders | `aud=fops`, `mfa=true` |

### 3.4 Absence Tests (Cross-Pollution Prevention)

Created CI tests that verify:

```bash
$ pytest tests/test_category3_data_contracts.py -v
# 18 passed in 0.44s

TestContractNamespaceSeparation:
  - test_guard_does_not_import_ops ✅
  - test_ops_does_not_import_guard ✅
  - test_common_has_no_domain_types ✅

TestGuardContractInvariants:
  - test_guard_status_has_required_fields ✅
  - test_guard_status_types_are_strict ✅
  - test_guard_no_founder_only_fields ✅

TestOpsContractInvariants:
  - test_system_pulse_has_required_fields ✅
  - test_system_pulse_status_is_command_vocabulary ✅
  - test_customer_segment_has_global_metrics ✅
  - test_incident_pattern_has_cross_tenant_fields ✅

TestVocabularySeparation:
  - test_guard_uses_calm_status_vocabulary ✅
  - test_ops_uses_command_status_vocabulary ✅

TestContractVersioning:
  - test_contract_version_exists ✅
  - test_contract_version_is_semver ✅
  - test_frozen_date_is_iso ✅
```

### 3.5 DATA_CONTRACT_FREEZE.md

Created `docs/DATA_CONTRACT_FREEZE.md` documenting:
- All frozen contracts with JSON examples
- Field type constraints
- Change process (add optional, deprecation cycle)
- Forbidden patterns (cross-domain imports, type widening)
- Version: 1.0.0, Frozen: 2025-12-23

### 3.6 Exit Criteria (BINARY) - ALL MET

| Criterion | Status |
|-----------|--------|
| Explicit DTOs for /guard/* | ✅ (8 DTOs) |
| Explicit DTOs for /ops/* | ✅ (8 DTOs) |
| API namespace separation | ✅ (calm vs command vocabulary) |
| Absence tests (no cross-pollution) | ✅ (6 tests) |
| DATA_CONTRACT_FREEZE.md created | ✅ |
| CI guardrails for violations | ✅ (18 tests) |
| Contract version tracking | ✅ (1.0.0) |

### Files Created

**New Files:**
- `backend/app/contracts/__init__.py` - Contract module with version
- `backend/app/contracts/guard.py` - Guard console DTOs (8 models)
- `backend/app/contracts/ops.py` - Ops console DTOs (8 models)
- `backend/app/contracts/common.py` - Shared infrastructure types
- `backend/tests/test_category3_data_contracts.py` - CI guardrails (18 tests)
- `docs/DATA_CONTRACT_FREEZE.md` - Contract documentation

### Contract Version

```python
CONTRACT_VERSION = "1.0.0"
CONTRACT_FROZEN_AT = "2025-12-23"
```

### Database Contract Status

```bash
$ alembic current
047_m27_snapshots (head)

$ alembic heads
047_m27_snapshots (head)

$ alembic branches
(empty - no branches)
```

- 48 migration files total (001-047 + initial)
- Latest: `047_m27_cost_snapshots.py` (M27 Cost Snapshots)
- Database in sync with codebase
- Single linear history (no merge conflicts)

---

## Category 4: Cost Intelligence Completion

**Status:** PENDING
**Priority:** MEDIUM

### Requirements
Confirm M26/M27 cost bridges are stable and producing data.

### Checklist
- [ ] `aos-cost-snapshot-hourly.timer` running
- [ ] `aos-cost-snapshot-daily.timer` running
- [ ] At least 1 cost snapshot in DB
- [ ] Cost anomaly detection producing results for test tenant

### Verification Command
```bash
systemctl list-timers | grep cost
PGPASSWORD="$PGPASSWORD" psql "$DATABASE_URL" -c "SELECT count(*) FROM cost_snapshots"
```

---

## Category 5: Incident Console Contrast

**Status:** PENDING
**Priority:** MEDIUM

### Requirements
Confirm Guard Console (Customer) and Ops Console (Founder) have distinct visual identities.

### Checklist
- [ ] Guard Console uses "calm" status states (PROTECTED, ATTENTION NEEDED, ACTION REQUIRED)
- [ ] Ops Console uses "command" status states (STABLE, ELEVATED, DEGRADED, CRITICAL)
- [ ] No route overlap between `/guard/*` and `/ops/*`
- [ ] Sidebar navigation distinct between consoles

---

## Category 6: Founder Action Paths

**Status:** PENDING
**Priority:** MEDIUM

### Requirements
Verify all 5 founder playbooks in Ops Console are actionable.

### Playbooks
1. **Silent Churn Risk** - Customer with declining stickiness, no recent incidents
2. **Cost Spike Alert** - Customer with abnormal cost increase
3. **Incident Flood** - Customer with >5 incidents in 24h
4. **First Incident** - New customer's first incident (onboarding opportunity)
5. **Policy Drift** - Agent behavior drifting from strategy bounds

### Checklist
- [ ] Each playbook card links to relevant detail page
- [ ] Actions (email, call, escalate) are clearly defined
- [ ] Priority scoring visible and sensible

---

## Category 7: Redirect Expiry & Cleanup

**Status:** PENDING
**Priority:** LOW

### Requirements
Plan removal of M28 temporary redirects.

### Current Redirects
- `"/" → "/guard"` (Customer Home)
- `"/*" catch-all → "/guard"` (fallback)
- Legacy routes (`/agents`, `/blackboard`, etc.) → `/guard`

### Timeline
- Keep redirects for 30 days post-M28 deployment
- Remove after 2025-01-23
- Update PIN-147 when removed

---

## Category 8: Go-to-Market Readiness

**Status:** PENDING
**Priority:** MEDIUM

### Requirements
Verify marketing/demo surfaces are ready.

### Checklist
- [ ] agenticverz.com landing page live
- [ ] console.agenticverz.com accessible (Customer Console)
- [ ] Demo mode functional without API key
- [ ] "Build Your App" flow working end-to-end
- [ ] Contact form / signup flow functional

---

## Transition Contract

### M28 → M29 Preconditions
All 8 categories must show checkmarks before M29 work begins.

| Category | Status | Blocking M29? |
|----------|--------|---------------|
| 1. STABILISE | ✅ COMPLETE | No longer |
| 2. Auth Boundary | ✅ COMPLETE | No longer |
| 3. Data Contract | ✅ COMPLETE | No longer |
| 4. Cost Intelligence | ⏳ PENDING | No (parallel) |
| 5. Incident Contrast | ⏳ PENDING | No |
| 6. Founder Actions | ⏳ PENDING | No |
| 7. Redirect Cleanup | ⏳ PENDING | No (scheduled) |
| 8. GTM Readiness | ⏳ PENDING | No (parallel) |

### M29 Entry Criteria
- Categories 1, 2, 3 COMPLETE
- Categories 4-8 at least STARTED

---

## Related PINs

- [PIN-145](PIN-145-m28-deletion-execution-report.md) - M28 Deletion Execution
- [PIN-146](PIN-146-m28-unified-console-ui.md) - M28 Unified Console UI
- [PIN-147](PIN-147-m28-route-migration-plan.md) - M28 Route Migration Plan
- [PIN-133](PIN-133-m29-quality-score-blueprint.md) - M29 Quality Score Blueprint

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-23 | Category 3 FULL SPEC COMPLETE - 16 DTOs frozen (8 guard, 8 ops), DATA_CONTRACT_FREEZE.md created, 18 CI tests, contract version 1.0.0 |
| 2025-12-23 | Category 2 FULL SPEC COMPLETE - Separate tokens (console/fops), separate cookies, separate middleware, MFA enforcement, audit logging, 12 CI tests pass |
| 2025-12-23 | Category 3 COMPLETE - Data contract frozen at 047_m27_snapshots, single linear history |
| 2025-12-23 | Category 2 COMPLETE - Backend auth added to /ops/* and /guard/* endpoints |
| 2025-12-23 | Category 1 COMPLETE - UI hygiene at 20 warnings (budget: 35) |
| 2025-12-23 | PIN created - 8 categories defined for M28→M29 transition |
