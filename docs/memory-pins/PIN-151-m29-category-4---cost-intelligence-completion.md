# PIN-151: M29 Categories 4-6 - Cost Intelligence + Incident Contrast + Founder Actions

**Status:** Category 4-5 ✅ COMPLETE | Category 6 Backend ✅ COMPLETE
**Created:** 2025-12-24
**Category:** M29 Transition / Cost Intelligence / Incident Contrast / Founder Actions
**Milestone:** M29

---

## Summary

Full cost visibility implementation with domain separation for Founder/Customer consoles. Category 6 introduces controlled founder intervention paths.

---

## Details

## Overview

M29 Category 4 completes the Cost Intelligence system with full domain separation between Founder Ops Console and Customer Guard Console.

**THE INVARIANT:** All values derive from complete snapshots, never live data. Customers never see cross-tenant data.

## Domain Separation

### Founder Console (/ops/cost/*)
- **Auth:** `aud=fops`, `mfa=true`
- **Vocabulary:** Command (stable, elevated, degraded, critical, increasing, decreasing)
- **Scope:** Cross-tenant aggregation, affected_tenants counts, systemic issue detection
- **Endpoints:**
  - `GET /ops/cost/overview` - Global cost overview with anomaly summary
  - `GET /ops/cost/anomalies` - Cross-tenant anomaly aggregation
  - `GET /ops/cost/tenants` - Per-tenant cost drilldown
  - `GET /ops/cost/customers/{id}` - Deep-dive cost analysis for single customer (2025-12-24)

### Customer Console (/guard/costs/*)
- **Auth:** `aud=console`, `org_id` required
- **Vocabulary:** Calm (normal, rising, spike, protected, attention_needed, resolved)
- **Scope:** Tenant-scoped only, no cross-tenant leakage
- **Endpoints:**
  - `GET /guard/costs/summary` - Cost summary with trend and projection
  - `GET /guard/costs/explained` - Breakdown by feature/model/user
  - `GET /guard/costs/incidents` - Cost-related incidents

## Implementation Files

### Frozen Contracts (Category 3)
- `backend/app/contracts/ops.py` - Founder DTOs:
  - `FounderCostOverviewDTO`
  - `FounderCostAnomalyDTO`
  - `FounderCostAnomalyListDTO`
  - `FounderCostTenantDTO`
  - `FounderCostTenantListDTO`
  - `FounderCustomerCostDrilldownDTO` (2025-12-24)
  - `CostDailyBreakdownDTO` (2025-12-24)
  - `CostByFeatureDTO` (2025-12-24)
  - `CostByUserDTO` (2025-12-24)
  - `CostByModelDTO` (2025-12-24)
  - `CustomerAnomalyHistoryDTO` (2025-12-24)

- `backend/app/contracts/guard.py` - Customer DTOs:
  - `CustomerCostSummaryDTO`
  - `CostBreakdownItemDTO`
  - `CustomerCostExplainedDTO`
  - `CustomerCostIncidentDTO`
  - `CustomerCostIncidentListDTO`

### API Routers
- `backend/app/api/cost_ops.py` - Founder cost visibility API (FOPS auth)
- `backend/app/api/cost_guard.py` - Customer cost visibility API (Console auth)

### Tests
- `backend/tests/test_category4_cost_intelligence.py` - 25 tests covering:
  - Domain separation (no cross-domain imports)
  - Vocabulary compliance (calm vs command)
  - Contract field validation (cents = int, pct = float)
  - Auth boundary structure
  - Snapshot invariant enforcement
  - Cross-domain leakage prevention

## Key Design Decisions

1. **Vocabulary Separation:** Customers see calm language (normal/rising/spike), founders see command language (stable/elevated/critical)

2. **No Cross-Tenant Leakage:** Customer DTOs never include `affected_tenants`, `is_systemic`, `churn_risk`, or any cross-tenant comparison fields

3. **Snapshot-Based Data:** All cost data comes from complete snapshots for deterministic results. `snapshot_status` field tracks freshness (fresh/stale/missing)

4. **Cost → Incident Integration:** Existing `run_anomaly_detection_with_m25` in `cost_anomaly_detector.py` escalates HIGH/CRITICAL anomalies to M25 incident loop

## M29 Category 4.1: Anomaly Rules Alignment (2025-12-24)

### Aligned Thresholds

| Parameter | Old Value | New Value | Rationale |
|-----------|-----------|-----------|-----------|
| Absolute Spike | 2x (200%) | 1.4x (40%) | Catch issues earlier |
| Consecutive Intervals | 1 | 2 | Reduce false positives |
| Sustained Drift | N/A | 1.25x (25%) | Early warning |
| Drift Days Required | N/A | 3 | Confirm sustained trend |

### Severity Bands

| Severity | Range | Action |
|----------|-------|--------|
| LOW | +15% to +25% | Alert only |
| MEDIUM | +25% to +40% | Alert + investigate |
| HIGH | >40% | Escalate to M25 incident loop |

**Note:** CRITICAL severity removed - HIGH is the maximum. This aligns with the principle that anomalies should fire earlier, not louder.

### New Fields Added

**FounderCostAnomalyDTO:**
- `derived_cause: Optional[str]` - Root cause: RETRY_LOOP, PROMPT_GROWTH, FEATURE_SURGE, TRAFFIC_GROWTH, UNKNOWN
- `breach_count: int = 1` - Consecutive intervals that breached threshold

**CustomerCostIncidentDTO:**
- `cause_explanation: Optional[str]` - Customer-friendly explanation of why this happened

### Migration 048

```
backend/alembic/versions/048_m29_anomaly_rules_alignment.py
```

Tables created:
- `cost_breach_history` - Tracks consecutive interval breaches
- `cost_drift_tracking` - Tracks sustained drift days

Columns added to `cost_anomalies`:
- `derived_cause` - Root cause enum value
- `breach_count` - Consecutive breach count

## Test Results

```
100 passed total (Category 4 + Category 5)

Category 4 Tests (44 passed):
- TestDomainSeparation: 4 tests
- TestVocabularyCompliance: 5 tests
- TestContractFieldValidation: 4 tests
- TestDTOInstantiation: 5 tests
- TestAuthBoundaryStructure: 2 tests
- TestSnapshotInvariant: 3 tests
- TestCrossDomainLeakagePrevention: 2 tests
- TestAnomalyRulesAlignment: 8 tests
- TestCustomerCostDrilldown: 11 tests

Category 5 Tests (56 passed):
- Contrast Rules: 22 tests (test_category5_incident_contrast.py)
- Absence Tests: 34 tests (test_category5_absence.py)
```

## Checklist

### Phase 1: Domain Separation (Complete)
- [x] Map existing snapshot tables to new endpoints
- [x] Create Founder Cost DTOs
- [x] Create Customer Cost DTOs
- [x] Implement /ops/cost/* endpoints
- [x] Implement /guard/costs/* endpoints
- [x] Register routers in main.py
- [x] Cost → Incident auto-creation (verified existing)
- [x] CI tests for cost intelligence (25 tests)

### Phase 2: Anomaly Rules Alignment (Complete - 2025-12-24)
- [x] Replace absolute spike logic (1.4x + 2 consecutive intervals)
- [x] Add sustained drift detection (7d > 1.25x for 3 days)
- [x] Align severity bands (LOW 15-25%, MED 25-40%, HIGH >40%)
- [x] Add breach_count tracking for consecutive intervals
- [x] Add derived_cause field to DTOs (ops.py and guard.py)
- [x] Create migration 048 for new tables (cost_breach_history, cost_drift_tracking)
- [x] Update tests for new thresholds (8 new tests)
- [x] Apply migration to production

### Phase 3: Customer Cost Drilldown (Complete - 2025-12-24)
- [x] Create FounderCustomerCostDrilldownDTO with supporting DTOs
- [x] Implement GET /ops/cost/customers/{tenant_id} endpoint
- [x] Add daily breakdown, feature/user/model attribution
- [x] Add anomaly history and trend analysis
- [x] Add 11 new tests for drilldown DTOs and endpoint
- [x] Update memory PIN and INDEX.md

## M29 Category 4.2: Customer Cost Drilldown (2025-12-24)

### New Endpoint

`GET /ops/cost/customers/{tenant_id}` - Deep-dive cost analysis for a single customer.

Answers: "Why is this customer spending so much?"

### Response DTO: `FounderCustomerCostDrilldownDTO`

Provides:
- **Spend Summary:** today, MTD, 7d, 30d
- **Baseline Comparison:** deviation from 7-day average
- **Budget Status:** monthly budget, usage %, projected month-end, days until exhausted
- **Daily Breakdown:** last 7 days with spend and request count
- **Cost Attribution:**
  - By feature (top 10)
  - By user (top 10, with anomaly flag)
  - By model (all models)
- **Largest Cost Driver:** Which dimension (feature/user/model) is driving cost
- **Anomaly History:** last 5 anomalies for this customer
- **Trend Analysis:** 7-day trend with human-readable message

### Supporting DTOs

| DTO | Purpose |
|-----|---------|
| `CostDailyBreakdownDTO` | Daily cost data point |
| `CostByFeatureDTO` | Feature cost attribution |
| `CostByUserDTO` | User cost attribution (with anomaly flag) |
| `CostByModelDTO` | Model cost attribution (includes tokens) |
| `CustomerAnomalyHistoryDTO` | Recent anomaly for this customer |

### Files Modified

- `backend/app/contracts/ops.py` - Added 6 new DTOs
- `backend/app/api/cost_ops.py` - Added `/customers/{tenant_id}` endpoint

---

## M29 Category 5: Incident Console Contrast (2025-12-24)

**Core Invariant:** One incident ID. Two narratives. Zero contradictions.

### Founder View (Truth & Causality)

**Endpoint:** `GET /ops/incidents/{incident_id}`
**Response:** `FounderIncidentDetailDTO`

Sections:
1. **Header** - incident_type, severity, tenant, current_state (dense facts)
2. **Timeline** - Full decision timeline (DETECTION_SIGNAL, TRIGGER_CONDITION, etc.)
3. **Root Cause** - derived_cause, evidence, confidence, threshold_breached
4. **Blast Radius** - requests_affected, cost_impact_cents/pct, duration, customer_visible_degradation
5. **Recurrence Risk** - similar_incidents_7d/30d, risk_level, suggested_prevention

### Customer View (Impact & Reassurance)

**Endpoint:** `GET /guard/incidents/{incident_id}/narrative`
**Response:** `CustomerIncidentNarrativeDTO`

Sections:
1. **Summary** - Plain language (e.g., "We detected unusual AI usage...")
2. **Impact** - requests_affected (yes/no/some), service_interrupted, cost_impact (calm vocabulary)
3. **Resolution** - status (investigating/mitigating/resolved/monitoring), reassuring message
4. **Customer Actions** - Only if necessary (review_usage, adjust_limits, contact_support, none)

### Contrast Rules (Enforced by Tests)

| Element | Founder View | Customer View |
|---------|--------------|---------------|
| Policy names | Yes | Never |
| Internal severity | Yes | Never |
| Baselines/thresholds | Yes | Never |
| Root cause enum | Yes | Rephrased |
| Timelines | Full | Summarized |
| Recovery mechanics | Detailed | Outcome only |
| Confidence/risk scores | Yes | Never |

### New DTOs Added

**Founder (ops.py):**
- `FounderIncidentDetailDTO`
- `FounderIncidentHeaderDTO`
- `FounderDecisionTimelineEventDTO`
- `FounderRootCauseDTO`
- `FounderBlastRadiusDTO`
- `FounderRecurrenceRiskDTO`
- `FounderIncidentListDTO`
- `FounderIncidentListItemDTO`

**Customer (guard.py):**
- `CustomerIncidentNarrativeDTO`
- `CustomerIncidentImpactDTO`
- `CustomerIncidentResolutionDTO`
- `CustomerIncidentActionDTO`

### Category 5 Test Results

```
22 passed in 3.87s

- TestIncidentContrastRules: 7 tests
- TestFounderIncidentDTOStructure: 4 tests
- TestCustomerIncidentDTOStructure: 3 tests
- TestDTOInstantiation: 2 tests
- TestEndpointRegistration: 2 tests
- TestCrossDomainLeakage: 3 tests
- TestIncidentLifecycle: 1 test
```

### Category 5 Files Modified

- `backend/app/contracts/ops.py` - Added 8 Founder Incident DTOs
- `backend/app/contracts/guard.py` - Added 4 Customer Incident DTOs
- `backend/app/api/ops.py` - Added `/ops/incidents/{id}` and `/ops/incidents` endpoints
- `backend/app/api/guard.py` - Added `/guard/incidents/{id}/narrative` endpoint
- `backend/tests/test_category5_incident_contrast.py` - Created (22 tests)

### Phase 4: Incident Console Contrast (Complete - 2025-12-24)
- [x] Map existing incident schema and DTOs
- [x] Design FounderIncidentDetailDTO with all required sections
- [x] Design CustomerIncidentNarrativeDTO with calm vocabulary
- [x] Implement GET /ops/incidents/{id} founder endpoint
- [x] Implement GET /ops/incidents founder list endpoint
- [x] Implement GET /guard/incidents/{id}/narrative customer endpoint
- [x] Add 22 contrast rule tests
- [x] Update memory PIN

### Phase 5: Category 5 Absence Tests (Complete - 2025-12-24)
- [x] Create ForbiddenKnowledge registry with 9 categories
- [x] Implement field name absence tests (8 tests)
- [x] Implement Literal value absence tests (7 tests)
- [x] Implement source code absence tests (3 tests)
- [x] Implement structural absence tests (5 tests)
- [x] Implement cross-domain isolation tests (3 tests)
- [x] Implement comprehensive forbidden scan tests (2 tests)
- [x] Implement API endpoint absence tests (4 tests)
- [x] Implement regression prevention tests (2 tests)
- [x] All 34 absence tests passing

---

## M29 Category 5.1: Absence Tests (2025-12-24)

**Purpose:** Make the founder/customer contrast IRREVERSIBLE.

These tests don't verify correctness - they verify IMPOSSIBILITY. If a forbidden field appears in a customer DTO, the test fails. This prevents accidental leakage during future development.

### Forbidden Knowledge Matrix

| Category | Examples | Count |
|----------|----------|-------|
| Quantitative Internals | baseline, deviation_pct, threshold, ratio, confidence | 25+ |
| Severity Semantics | LOW, MEDIUM, HIGH, CRITICAL, severity | 10+ |
| Root Cause Mechanics | derived_cause, RETRY_LOOP, PROMPT_GROWTH, evidence | 12+ |
| Policy Internals | policy, policy_id, guardrail, rule, killswitch_id | 10+ |
| Infrastructure Actors | actor, recovery, escalation, mitigation_step | 12+ |
| Cross-Tenant Data | affected_tenants, is_systemic, similar_incidents_7d | 12+ |
| Founder Lifecycle | DETECTED, TRIAGED, MITIGATED, current_state | 12+ |
| Blast Radius | blast_radius, requests_blocked, cost_impact_cents | 8+ |
| Recurrence | recurrence_risk, same_tenant_recurrence, is_recurring | 9+ |

### Test Classes

1. **TestFieldNameAbsence** (8 tests)
   - Verifies Category 5 DTOs have no forbidden field names
   - Comprehensive scan of ALL customer DTOs

2. **TestLiteralValueAbsence** (7 tests)
   - Verifies no forbidden Literal values in type hints
   - Enforces calm vocabulary compliance

3. **TestSourceCodeAbsence** (3 tests)
   - Verifies no founder terminology in comments
   - Verifies no imports from ops.py
   - Verifies no founder vocabulary in field definitions

4. **TestStructuralAbsence** (5 tests)
   - Verifies data_exposed is always "no"
   - Verifies no timeline/events exposure
   - Verifies no raw count fields
   - Verifies Literals over numeric types

5. **TestCrossDomainIsolation** (3 tests)
   - Verifies no shared base classes
   - Verifies no shared field types
   - Verifies router uses only guard DTOs

6. **TestComprehensiveForbiddenScan** (2 tests)
   - Final comprehensive scan for ANY leakage
   - Tests all customer DTOs against all forbidden terms

7. **TestAPIEndpointAbsence** (4 tests)
   - Verifies endpoint existence
   - Verifies correct auth (console vs fops)

8. **TestRegressionPrevention** (2 tests)
   - Demonstrates detection of forbidden additions
   - Verifies ForbiddenKnowledge registry completeness

### Absence Test Results

```
56 passed in 2.79s (Category 5 total)

- TestFieldNameAbsence: 8 tests
- TestLiteralValueAbsence: 7 tests
- TestSourceCodeAbsence: 3 tests
- TestStructuralAbsence: 5 tests
- TestCrossDomainIsolation: 3 tests
- TestComprehensiveForbiddenScan: 2 tests
- TestAPIEndpointAbsence: 4 tests
- TestRegressionPrevention: 2 tests
```

### Legacy DTO Exceptions

The following legacy DTOs are grandfathered with known forbidden fields:
- `IncidentSummaryDTO`: `severity`, `duration_seconds` (pre-Category 5, migration planned)

### Files Created

- `backend/tests/test_category5_absence.py` - 34 absence tests

---

## M29 Category 6: Founder Action Paths (SPEC READY - 2025-12-24)

**Status:** 📋 SPEC READY (after Category 5 COMPLETE)
**Purpose:** Allow founders to intervene **safely, deliberately, and reversibly**

### 6.0 What Category 6 Is (and Is Not)

**Category 6 IS:**
- Controlled intervention
- Risk containment
- Blast-radius reduction
- Explicit accountability

**Category 6 IS NOT:**
- Automation playground
- "One-click fixes"
- Customer-visible controls
- Policy editing UI

If this feels empowering in a flashy way, it's wrong.

### 6.1 Core Invariants (NON-NEGOTIABLE)

1. **No action from Pulse** - Actions never on dashboards
2. **Every action requires context** - Must see why before acting
3. **Every action is reversible** (unless explicitly destructive)
4. **Every action is logged** with actor + reason
5. **Customers never trigger these paths**

Founder action ≠ convenience
Founder action = **responsibility**

### 6.2 Action Taxonomy (EXACTLY 4 ACTIONS)

No more. No variants.

| Action | Purpose | Scope | Reversible |
|--------|---------|-------|------------|
| **FREEZE_TENANT** | Stop damage immediately | Entire tenant | Yes |
| **THROTTLE_TENANT** | Slow damage without outage | Tenant rate limits | Yes |
| **FREEZE_API_KEY** | Isolate faulty integration | Single API key | Yes |
| **OVERRIDE_INCIDENT** | Human judgment supersedes automation | Single incident | Limited |

#### A. FREEZE TENANT
**Effect:** All API keys disabled, requests rejected fast, incidents continue to log
**Use when:** Severe policy breach, runaway cost + unknown cause, suspected abuse

#### B. THROTTLE TENANT
**Effect:** Requests at reduced rate, retries suppressed, cost slope flattened
**Use when:** Cost anomaly detected, retry loops, sudden traffic surges

#### C. FREEZE API KEY
**Effect:** Requests using key rejected, other keys unaffected
**Use when:** Single client misbehaving, SDK bug isolated, integration testing gone wrong

#### D. OVERRIDE INCIDENT (ACK / RESOLVE)
**Effect:** Marks incident acknowledged/resolved, stops escalation, does NOT delete evidence
**Use when:** False positive, known safe pattern, customer already mitigated externally

### 6.3 Where Actions Live (Strict Navigation)

Actions **never** live on summary screens.

| Action | Entry Screen |
|--------|--------------|
| Freeze tenant | `/fops/customers/{id}` |
| Throttle tenant | `/fops/customers/{id}/cost` |
| Freeze API key | `/fops/customers/{id}/keys` |
| Override incident | `/fops/incidents/{id}` |

**FORBIDDEN:** No action buttons on Pulse, lists, tables, or dashboards.

### 6.4 Action Flow Pattern (MANDATORY 4-STEP)

All actions follow the same flow:

**Step 1 — Context Panel (Read-Only)**
- Why this action is available
- What signals triggered it
- What will change
- No buttons yet

**Step 2 — Reason Capture (Required)**
```
Reason (required):
[ ] Cost anomaly
[ ] Policy violation
[ ] Retry loop
[ ] Abuse suspected
[ ] False positive
[ ] Other: __________
```
- No default selection
- Cannot proceed without reason

**Step 3 — Confirmation (Explicit)**
```
"This will freeze tenant acme-prod and block all AI requests.
This action is reversible and will be logged."

[CONFIRM FREEZE]
```

**Step 4 — Post-Action State**
- Action applied
- Timestamp
- Actor
- How to reverse

### 6.5 Audit & Evidence

Every action emits an immutable audit record.

```json
{
  "action": "FREEZE_TENANT",
  "target": "tenant:acme-prod",
  "actor_id": "founder_mahesh",
  "reason": "Cost anomaly",
  "source_incident_id": "inc_82af",
  "timestamp": "2025-xx-xxTxx:xx:xxZ",
  "reversible": true
}
```

Audit records:
- Cannot be edited
- Cannot be deleted
- Visible in `/fops/audit`

### 6.6 Customer Visibility Rules

Customers:
- **Never see the action UI**
- **May see the outcome**, phrased calmly

Examples:
- "Requests were temporarily limited to protect your account."
- "One API key was disabled due to unusual usage."

**NEVER show:** Founder identity, internal reason codes, action names (freeze/throttle)

### 6.7 Safety Rails

**6.7.1 Rate-limit actions:** Max N actions per founder per hour
**6.7.2 No chaining:** Cannot freeze + throttle simultaneously, must undo one first
**6.7.3 MFA required:** Every action requires recent MFA verification

### 6.8 Category 6 Exit Criteria (Binary)

Category 6 is **COMPLETE** only if:

- [ ] Exactly 4 actions exist (no more)
- [ ] No actions on Pulse or lists
- [ ] Every action requires a reason
- [ ] Every action is audited immutably
- [ ] Actions are reversible where defined
- [ ] Customers only see calm outcomes
- [ ] No customer-triggered paths exist
- [ ] MFA enforced for all actions

### Phase 6: Founder Action Paths (SPEC READY - 2025-12-24)
- [x] Define action taxonomy (exactly 4 actions)
- [x] Define core invariants (5 non-negotiable rules)
- [x] Define entry points (strict navigation)
- [x] Define 4-step action flow pattern
- [x] Define audit schema requirements
- [x] Define customer visibility rules
- [x] Define safety rails
- [x] Define exit criteria (8 checkboxes)
- [ ] Design founder action UX flows
- [ ] Define backend action APIs
- [ ] Write audit schema + tests
- [ ] Review safety rails edge cases
- [ ] Implement FREEZE_TENANT action
- [ ] Implement THROTTLE_TENANT action
- [ ] Implement FREEZE_API_KEY action
- [ ] Implement OVERRIDE_INCIDENT action
- [ ] Category 6 tests passing

---


---

## Updates

### Update (2025-12-24)

## 2025-12-24: Category 6 Backend APIs - COMPLETE

### Backend Implementation
- **FounderAction Model**: Added to `backend/app/models/tenant.py`
  - Immutable audit records for all founder actions
  - Tracks action_type, target, reason, founder, timestamps
  - is_active and is_reversible status tracking

- **Action DTOs**: Added to `backend/app/contracts/ops.py`
  - FounderActionRequestDTO (unified command model)
  - FounderActionResponseDTO (status, action_id, reversible, undo_hint)
  - FounderAuditRecordDTO (immutable audit record)
  - FounderReversalRequestDTO (action_id to reverse)
  - FounderActionListDTO / FounderActionSummaryDTO (audit trail)

- **Founder Actions Router**: Created `backend/app/api/founder_actions.py`
  - 4 action endpoints: freeze-tenant, throttle-tenant, freeze-api-key, override-incident
  - 3 reversal endpoints: unfreeze-tenant, unthrottle-tenant, unfreeze-api-key
  - 2 audit endpoints: /audit (list), /audit/{action_id} (detail)

### Safety Rails Implemented
- Rate limit: MAX_ACTIONS_PER_HOUR = 10
- Mutual exclusion: FREEZE_TENANT and THROTTLE_TENANT cannot coexist
- MFA enforcement: All actions require mfa=true in FounderToken
- OVERRIDE_INCIDENT is NOT reversible

### Test Results
- `test_category6_founder_actions.py`: **31 tests, 31 passed**
  - TestActionDTOStructure: 6 tests
  - TestResponseDTOStructure: 2 tests
  - TestAuditDTOStructure: 2 tests
  - TestReversalDTOStructure: 1 test
  - TestFounderActionModel: 2 tests
  - TestEndpointRegistration: 4 tests
  - TestSafetyRails: 5 tests
  - TestDTOInstantiation: 4 tests
  - TestInvariants: 5 tests

### Files Created/Modified
- Created: `backend/app/api/founder_actions.py` (~570 lines)
- Created: `backend/tests/test_category6_founder_actions.py` (~380 lines)
- Modified: `backend/app/contracts/ops.py` (+220 lines for DTOs)
- Modified: `backend/app/models/tenant.py` (+90 lines for FounderAction model)
- Modified: `backend/app/main.py` (router registration)

## Related PINs

- [PIN-148](PIN-148-.md)
- [PIN-149](PIN-149-.md)
- [PIN-150](PIN-150-.md)
