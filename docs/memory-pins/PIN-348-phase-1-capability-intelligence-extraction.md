# PIN-348: Phase 1 Capability Intelligence Extraction

**Status:** COMPLETE
**Created:** 2026-01-07
**Category:** L2.1 / Capability Intelligence
**Milestone:** L2.1 Epistemic Orchestration Layer
**Related PINs:** PIN-347 (L2.1 Epistemic Layer — Table-First Design)

---

## Executive Summary

Completed **Phase 1 — Capability Intelligence Extraction** for:
- **5 L2.1 Core Lens domains**: Overview, Activity, Incidents, Policies, Logs (20 capabilities)
- **2 Secondary Navigation sections**: Connectivity, Account (18 capabilities)

**Total: 38 capabilities** documented with evidence-backed intelligence tables, adapter/operator crosswalks, and risk reports.

**Core Principle Applied:**
> "We know what the system can do. We know how it actually behaves. We know where documentation lies or is incomplete. We know which assumptions are risky."

**Key Distinction:**
- **Core Lens domains** (5) are governed by L2.1 epistemic surfaces
- **Secondary sections** (Connectivity, Account) are NOT in L2.1 seed per Customer Console v1 Constitution

---

## Key Findings

### Capability Distribution — Core Lens Domains (L2.1)

| Domain | Capabilities Found | Architecture | L2.1 Alignment |
|--------|-------------------|--------------|----------------|
| **Overview** | 5 | ❌ BYPASSED | ❌ NO Customer API |
| **Activity** | 2 | ✅ CLEAN | ✅ GOOD |
| **Incidents** | 8 | ✅ CLEAN | ⚠️ PARTIAL |
| **Policies** | 2 | ✅ CLEAN | ⚠️ PARTIAL |
| **Logs** | 3 | ✅ CLEAN | ⚠️ PARTIAL |
| **Subtotal** | **20** | 4/5 Clean | - |

### Capability Distribution — Secondary Navigation (NOT in L2.1)

| Section | Capabilities Found | Architecture | Notes |
|---------|-------------------|--------------|-------|
| **Connectivity** | 6 | ✅ MIXED | API Keys: L2→L3→L4, Admin: L2→L4 |
| **Account** | 12 | ⚠️ DIRECT | Auth: L2→L4, Settings: L2→L6 (bypasses L3/L4) |
| **Subtotal** | **18** | - | NOT in L2.1 seed |

### Grand Total: 38 Capabilities

### Mode Distribution (All Domains)

| Mode | Count | Layer Route |
|------|-------|-------------|
| READ | 28 | L2_1 / Direct |
| WRITE | 10 | GC_L / Direct |
| DOWNLOAD | 3 | L2_1 |

---

## Critical Issues Identified

### 1. Overview Domain — CRITICAL GAP

**Problem:** L2.1 surfaces (`OVERVIEW.SYSTEM_HEALTH.*`) are defined in seed, but:
- Current API (`/platform/*`) serves **Founder Console only**
- Data is **cross-tenant** (system-wide health)
- L2.1 surfaces require **tenant isolation**

**Resolution Required:**
- Option A: Create tenant-scoped health API for Customer Console
- Option B: Remove `OVERVIEW.*` from L2.1 seed

### 2. GC_L Policy Mutations — NOT IMPLEMENTED

ALL 8 GC_L (write/activate) actions for Policies domain are seeded but have NO backend code:
- `ACT-POLICY-BUDGET-CREATE/UPDATE/ACTIVATE/DEACTIVATE`
- `ACT-POLICY-RATE-UPDATE/ACTIVATE`
- `ACT-POLICY-APPROVAL-CREATE/ACTIVATE`

### 3. Incident Escalate — ORPHANED

`ACT-INCIDENT-ESCALATE` is seeded but has NO backend implementation.

### 4. Audit Surfaces — SEMANTIC MISMATCH

`LOGS.AUDIT_LOGS.SYSTEM_AUDIT` and `LOGS.AUDIT_LOGS.USER_AUDIT` return execution traces, NOT actual audit logs.

### 5. Connectivity — Integrations NOT IMPLEMENTED

Customer Console has NO integration management:
- No webhook configuration
- No external system connections
- No OAuth app management
- `integration.py` serves Founder Console only (M25 Learning Loop)

### 6. Account — Billing NOT IMPLEMENTED

Customer Console Account section missing:
- No billing/subscription API
- No account deletion endpoint
- No account suspension endpoint
- RBAC admin is Founder Console only (`rbac_api.py`)

---

## Seed vs Code Gap Analysis

### Seeded but NOT Implemented (13 Actions)

| Action ID | Domain | Mode |
|-----------|--------|------|
| ACT-INCIDENT-ESCALATE | Incidents | WRITE |
| ACT-ACTIVITY-COMPLETED-DOWNLOAD | Activity | DOWNLOAD |
| ACT-ACTIVITY-DETAIL-DOWNLOAD | Activity | DOWNLOAD |
| ACT-POLICY-BUDGET-CREATE | Policies | WRITE |
| ACT-POLICY-BUDGET-UPDATE | Policies | WRITE |
| ACT-POLICY-BUDGET-ACTIVATE | Policies | ACTIVATE |
| ACT-POLICY-BUDGET-DEACTIVATE | Policies | ACTIVATE |
| ACT-POLICY-RATE-UPDATE | Policies | WRITE |
| ACT-POLICY-RATE-ACTIVATE | Policies | ACTIVATE |
| ACT-POLICY-APPROVAL-CREATE | Policies | WRITE |
| ACT-POLICY-APPROVAL-ACTIVATE | Policies | ACTIVATE |
| ACT-POLICY-AUDIT-VIEW | Policies | READ |
| ACT-POLICY-AUDIT-DOWNLOAD | Policies | DOWNLOAD |

### Implemented but NOT Seeded (4 Capabilities)

| Capability | Domain | Mode |
|------------|--------|------|
| CAP-INC-SEARCH | Incidents | READ |
| CAP-INC-TIMELINE | Incidents | READ |
| CAP-INC-NARRATIVE | Incidents | READ |
| CAP-INC-EXPORT | Incidents | READ |

---

## Architectural Assessment

### Layer Compliance

| Domain | L2→L3→L4 Compliance | Notes |
|--------|---------------------|-------|
| Overview | ❌ BYPASSED | Direct SQL in L2, adapter exists but unused |
| Activity | ✅ CLEAN | Proper layering |
| Incidents | ✅ CLEAN | Proper layering |
| Policies | ✅ CLEAN | Proper layering |
| Logs | ✅ CLEAN | Async, proper layering |

### Adapter Inventory — Core Lens Domains

| Adapter | Used? | Methods |
|---------|-------|---------|
| PlatformEligibilityAdapter | ❌ NO | 4 methods (bypassed for performance) |
| CustomerActivityAdapter | ✅ YES | list_activities, get_activity |
| CustomerIncidentsAdapter | ✅ YES | list, get, acknowledge, resolve |
| CustomerPoliciesAdapter | ✅ YES | get_policy_constraints, get_guardrail_detail |
| CustomerLogsAdapter | ✅ YES | list_logs, get_log, export_logs |

### Adapter Inventory — Secondary Navigation

| Adapter | Used? | Methods |
|---------|-------|---------|
| CustomerKeysAdapter | ✅ YES | list_keys, freeze_key, unfreeze_key |
| (none - direct) | - | Auth/Session: OAuth providers, email verification |
| (none - direct) | - | Tenant: TenantService direct access |
| (none - direct) | - | Settings: Direct SQL in L2 |

---

## Risk Summary

### CRITICAL

1. **Overview Domain Gap** — L2.1 surfaces exist but NO Customer Console API
2. **GC_L Not Implemented** — ALL policy write/activate actions missing
3. **Escalate Orphaned** — Seeded but no code

### HIGH

1. **WRITE Reversibility** — Incident acknowledge/resolve cannot be undone
2. **Idempotency Unknown** — WRITE operations lack idempotency contract

### MEDIUM

1. **CSV Injection** — Logs export may be vulnerable
2. **Audit Mismatch** — AUDIT_LOGS surfaces return execution traces

---

## Phase 2 Elicitation Questions

1. Should Overview surfaces be removed from L2.1 seed (Founder-only)?
2. Should incidents be reopenable after resolution?
3. What is idempotency contract for acknowledge/resolve?
4. Are GC_L policy mutations planned for v1?
5. Should `ACT-INCIDENT-ESCALATE` be implemented or removed?

---

## Artifacts Produced

### Intelligence Reports — Core Lens Domains (L2.1)

| File | Domain |
|------|--------|
| `PHASE_1_OVERVIEW_CAPABILITY_INTELLIGENCE.md` | Overview |
| `PHASE_1_ACTIVITY_CAPABILITY_INTELLIGENCE.md` | Activity |
| `PHASE_1_INCIDENTS_CAPABILITY_INTELLIGENCE.md` | Incidents |
| `PHASE_1_POLICIES_CAPABILITY_INTELLIGENCE.md` | Policies |
| `PHASE_1_LOGS_CAPABILITY_INTELLIGENCE.md` | Logs |
| `PHASE_1_CONSOLIDATED_INTELLIGENCE_REPORT.md` | ALL Core Lens |

### Intelligence Reports — Secondary Navigation

| File | Section |
|------|---------|
| `PHASE_1_CONNECTIVITY_CAPABILITY_INTELLIGENCE.md` | Connectivity (API Keys) |
| `PHASE_1_ACCOUNT_CAPABILITY_INTELLIGENCE.md` | Account (Auth, Settings) |

### CSV Exports

| File | Contents |
|------|----------|
| `capability_intelligence_all_domains.csv` | All 38 capabilities |
| `capability_intelligence_incidents.csv` | Incidents detail |
| `adapter_operator_crosswalk_incidents.csv` | Incidents adapter mapping |

All artifacts located in: `design/l2_1/elicitation/`

---

## Consolidated Capability Table

| ID | Domain | Mode | Confidence | L2.1 Aligned |
|----|--------|------|------------|--------------|
| CAP-OVW-HEALTH | Overview | READ | HIGH | ❌ |
| CAP-OVW-CAPS | Overview | READ | HIGH | ❌ |
| CAP-OVW-DOMAIN | Overview | READ | HIGH | ❌ |
| CAP-OVW-CAP-DETAIL | Overview | READ | HIGH | ❌ |
| CAP-OVW-ELIGIBILITY | Overview | READ | HIGH | ❌ |
| CAP-ACT-LIST | Activity | READ | HIGH | ✅ |
| CAP-ACT-DETAIL | Activity | READ | HIGH | ✅ |
| CAP-INC-LIST | Incidents | READ | HIGH | ✅ |
| CAP-INC-GET | Incidents | READ | HIGH | ✅ |
| CAP-INC-ACK | Incidents | WRITE | MEDIUM | ✅ |
| CAP-INC-RESOLVE | Incidents | WRITE | MEDIUM | ✅ |
| CAP-INC-SEARCH | Incidents | READ | HIGH | ⚠️ |
| CAP-INC-TIMELINE | Incidents | READ | HIGH | ⚠️ |
| CAP-INC-NARRATIVE | Incidents | READ | HIGH | ⚠️ |
| CAP-INC-EXPORT | Incidents | READ | HIGH | ⚠️ |
| CAP-POL-CONSTRAINTS | Policies | READ | HIGH | ✅ |
| CAP-POL-GUARDRAIL | Policies | READ | HIGH | ✅ |
| CAP-LOG-LIST | Logs | READ | HIGH | ✅ |
| CAP-LOG-DETAIL | Logs | READ | HIGH | ✅ |
| CAP-LOG-EXPORT | Logs | READ | MEDIUM | ✅ |

### Secondary Navigation — Connectivity (NOT in L2.1)

| ID | Section | Mode | Confidence | L2.1 Aligned |
|----|---------|------|------------|--------------|
| CAP-KEY-LIST | Connectivity | READ | HIGH | N/A |
| CAP-KEY-FREEZE | Connectivity | WRITE | HIGH | N/A |
| CAP-KEY-UNFREEZE | Connectivity | WRITE | HIGH | N/A |
| CAP-KEY-LIST-ADMIN | Connectivity | READ | HIGH | N/A |
| CAP-KEY-CREATE | Connectivity | WRITE | HIGH | N/A |
| CAP-KEY-REVOKE | Connectivity | WRITE | HIGH | N/A |

### Secondary Navigation — Account (NOT in L2.1)

| ID | Section | Mode | Confidence | L2.1 Aligned |
|----|---------|------|------------|--------------|
| CAP-AUTH-LOGIN-GOOGLE | Account | READ | HIGH | N/A |
| CAP-AUTH-LOGIN-AZURE | Account | READ | HIGH | N/A |
| CAP-AUTH-SIGNUP-EMAIL | Account | WRITE | HIGH | N/A |
| CAP-AUTH-VERIFY-EMAIL | Account | WRITE | HIGH | N/A |
| CAP-AUTH-REFRESH | Account | WRITE | HIGH | N/A |
| CAP-AUTH-LOGOUT | Account | WRITE | HIGH | N/A |
| CAP-AUTH-ME | Account | READ | HIGH | N/A |
| CAP-AUTH-PROVIDERS | Account | READ | HIGH | N/A |
| CAP-TENANT-GET | Account | READ | HIGH | N/A |
| CAP-TENANT-USAGE | Account | READ | HIGH | N/A |
| CAP-SETTINGS-GET | Account | READ | HIGH | N/A |

---

## Phase 1 Completion Attestation

| Criterion | Status |
|-----------|--------|
| All 5 Core Lens domains analyzed | ✅ |
| All 2 Secondary Navigation sections analyzed | ✅ |
| All capabilities documented | ✅ (38 total: 20 Core Lens + 18 Secondary) |
| All adapters mapped | ✅ (6 adapters) |
| All UNKNOWNs explicit | ✅ |
| All risks surfaced | ✅ (12 risks) |
| No UI assumptions | ✅ |
| Seed gaps identified | ✅ (13 missing, 4 extra in Core Lens) |
| Secondary sections NOT in L2.1 seed | ✅ (per Constitution) |

**PHASE 1 STATUS: COMPLETE**

---

## Next Steps

1. **Phase 2: Elicitation** — Resolve ambiguities identified in Phase 1
2. **Phase 3: Binding** — Map capabilities to L2.1 surfaces with action routing
3. **Phase 4: Database Application** — Apply schemas to Neon

---

## References

- `design/l2_1/elicitation/` — All Phase 1 artifacts
- `design/l2_1/seeds/l2_1_action_capabilities.seed.sql` — L2.1 seed data
- `design/l2_1/seeds/l2_1_surface_registry.seed.sql` — L2.1 surfaces
- PIN-347 — L2.1 Epistemic Layer Table-First Design
- Customer Console v1 Constitution

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-07 | Created PIN-348 |
| 2026-01-07 | Phase 1 complete: 20 capabilities across 5 Core Lens domains |
| 2026-01-07 | Critical findings: Overview gap, GC_L not implemented, escalate orphaned |
| 2026-01-07 | 6 intelligence reports + 3 CSV exports produced |
| 2026-01-07 | Extended Phase 1 to Secondary Navigation: CONNECTIVITY (6 caps) + ACCOUNT (12 caps) |
| 2026-01-07 | Total capabilities: 38 (20 Core Lens + 18 Secondary Navigation) |
| 2026-01-07 | New critical findings: Integrations NOT IMPLEMENTED, Billing NOT IMPLEMENTED |
| 2026-01-07 | Added 2 new intelligence reports (CONNECTIVITY, ACCOUNT) |
