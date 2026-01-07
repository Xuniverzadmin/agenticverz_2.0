# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Domain: Overview

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**L2.1 Surfaces:**
- `OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS`
- `OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS`

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Capability: CAP-OVW-HEALTH (Get Platform Health)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-OVW-HEALTH` | `platform.py:63` |
| capability_name | Get Platform Health | `GET /platform/health` |
| description | Get system health overview (BLCA status, lifecycle coherence) | `platform.py:64-118` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single system-wide snapshot |
| mutates_state | **NO** | Read-only DB queries |
| bulk_support | **NO** | System singleton |
| latency_profile | **LOW** | 2 SQL queries only |
| execution_style | **SYNC** | `platform.py:64` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Founder audience (no tenant scope) |
| adapters | `PlatformEligibilityAdapter` (available but NOT used in API) | `platform_eligibility_adapter.py:129` |
| operators | Direct SQL queries in route | `platform.py:80-103` |
| input_contracts | None (system-wide) | Route signature |
| output_contracts | `{state, blca_status, lifecycle_coherence, last_checked}` | `platform.py:112-118` |
| side_effects | **NONE** | Pure read |
| failure_modes | DB connection failure | Implicit |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `platform.py:63-118`, `platform_eligibility_adapter.py:174-189` |
| risk_flags | **ADAPTER BYPASSED** - Direct SQL in L2 route instead of using L3 adapter |

---

### Capability: CAP-OVW-CAPS (Get Capabilities Eligibility)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-OVW-CAPS` | `platform.py:121` |
| capability_name | Get Capabilities Eligibility | `GET /platform/capabilities` |
| description | Get all capabilities with eligibility status | `platform.py:122-187` |
| mode | **READ** | No state mutation |
| scope | **BULK** | Returns all 17 capabilities |
| mutates_state | **NO** | Read-only |
| bulk_support | **YES** | Returns full capability list |
| latency_profile | **LOW** | Single SQL query + iteration |
| execution_style | **SYNC** | `platform.py:122` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Founder audience |
| adapters | `PlatformEligibilityAdapter.to_eligibility_response()` (available but NOT used) | `platform_eligibility_adapter.py:191-235` |
| operators | Direct SQL + hardcoded DOMAIN_CAPABILITIES map | `platform.py:137-144` |
| input_contracts | None | Route signature |
| output_contracts | `{total, eligible_count, blocked_count, capabilities[]}` | `platform.py:181-187` |
| side_effects | **NONE** | Pure read |
| failure_modes | DB connection failure | Implicit |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `platform.py:121-187`, `platform_eligibility_adapter.py:191-235` |
| risk_flags | **ADAPTER BYPASSED** - Direct SQL; **HARDCODED MAP** - capabilities list hardcoded in route |

---

### Capability: CAP-OVW-DOMAIN (Get Domain Health)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-OVW-DOMAIN` | `platform.py:190` |
| capability_name | Get Domain Health | `GET /platform/domains/{domain_name}` |
| description | Get health for specific domain with per-capability breakdown | `platform.py:190-272` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single domain |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single domain per request |
| latency_profile | **LOW** | Single SQL query |
| execution_style | **SYNC** | `platform.py:190` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Founder audience |
| adapters | `PlatformEligibilityAdapter.domain_to_view()` (NOT used) | `platform_eligibility_adapter.py:162-172` |
| operators | Direct SQL + hardcoded map | `platform.py:209-216` |
| input_contracts | `domain_name: str` | Route param |
| output_contracts | `{domain, state, healthy_count, blocked_count, capabilities[]}` | `platform.py:265-272` |
| side_effects | **NONE** | Pure read |
| failure_modes | 404 Domain not found | `platform.py:219-223` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `platform.py:190-272` |
| risk_flags | **ADAPTER BYPASSED**; **HARDCODED MAP** |

---

### Capability: CAP-OVW-CAP-DETAIL (Get Capability Health)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-OVW-CAP-DETAIL` | `platform.py:275` |
| capability_name | Get Capability Health | `GET /platform/capabilities/{capability_name}` |
| description | Get health for specific capability with blocking reasons | `platform.py:275-374` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single capability |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single capability |
| latency_profile | **LOW** | Single SQL query |
| execution_style | **SYNC** | `platform.py:275` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Founder audience |
| adapters | `PlatformEligibilityAdapter.capability_to_view()` (NOT used) | `platform_eligibility_adapter.py:150-160` |
| operators | Direct SQL + hardcoded map | `platform.py:318-347` |
| input_contracts | `capability_name: str` | Route param |
| output_contracts | `{capability, domain, state, is_eligible, reasons[]}` | `platform.py:367-374` |
| side_effects | **NONE** | Pure read |
| failure_modes | 404 Capability not found | `platform.py:311-315` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `platform.py:275-374` |
| risk_flags | **ADAPTER BYPASSED**; **HARDCODED DISQUALIFICATION** (KILLSWITCH_STATUS) |

---

### Capability: CAP-OVW-ELIGIBILITY (Quick Eligibility Check)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-OVW-ELIGIBILITY` | `platform.py:377` |
| capability_name | Quick Eligibility Check | `GET /platform/eligibility/{capability_name}` |
| description | Fast eligibility check for single capability | `platform.py:377-449` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single capability |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single capability |
| latency_profile | **VERY LOW** | Single COUNT query |
| execution_style | **SYNC** | `platform.py:377` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Founder audience |
| adapters | None used | Direct SQL |
| operators | Single COUNT SQL | `platform.py:424-432` |
| input_contracts | `capability_name: str` | Route param |
| output_contracts | `{capability, is_eligible, state, checked_at}` | `platform.py:444-449` |
| side_effects | **NONE** | Pure read |
| failure_modes | 404 Capability not found | `platform.py:417-421` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `platform.py:377-449` |
| risk_flags | **ADAPTER BYPASSED** |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

| adapter_id | operator_name | capability_id | sync/async | side_effects | l2_1_surface | notes |
|------------|---------------|---------------|------------|--------------|--------------|-------|
| (direct SQL) | get_platform_health | CAP-OVW-HEALTH | sync | None | OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS | L3 adapter exists but bypassed |
| (direct SQL) | get_capabilities_eligibility | CAP-OVW-CAPS | sync | None | OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS | L3 adapter exists but bypassed |
| (direct SQL) | get_domain_health | CAP-OVW-DOMAIN | sync | None | (not in seed) | Detail view |
| (direct SQL) | get_capability_health | CAP-OVW-CAP-DETAIL | sync | None | (not in seed) | Detail view |
| (direct SQL) | check_capability_eligibility | CAP-OVW-ELIGIBILITY | sync | None | (not in seed) | Quick check |
| PlatformEligibilityAdapter | system_to_view() | (unused) | sync | None | - | Available but not wired |
| PlatformEligibilityAdapter | domain_to_view() | (unused) | sync | None | - | Available but not wired |
| PlatformEligibilityAdapter | capability_to_view() | (unused) | sync | None | - | Available but not wired |
| PlatformEligibilityAdapter | to_eligibility_response() | (unused) | sync | None | - | Available but not wired |

### Layer Architecture (ANOMALOUS)

```
L2 (platform.py) — DIRECT SQL (bypasses L3)
      ↓
L6 (governance_signals table)

L3 (PlatformEligibilityAdapter) — EXISTS BUT UNUSED
      ↓
L4 (PlatformHealthService) — EXISTS BUT TOO SLOW (~90 queries)
```

**Architectural Anomaly:** L3 adapter and L4 service exist but are bypassed for performance reasons.

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### CAP-OVW-HEALTH

**Risk Flags:**

1. **ADAPTER BYPASS**
   - L3 `PlatformEligibilityAdapter` exists with `system_to_view()` method
   - Route uses direct SQL instead "for performance"
   - Comment: "~90 queries for full system health" via L4 service
   - **Governance Concern:** Violates L2→L3→L4 layer model

2. **NO TENANT SCOPE**
   - This is Founder Console only
   - Returns system-wide data
   - **L2.1 Mapping Concern:** L2.1 surfaces are tenant-scoped; this is cross-tenant

**Confidence:** MEDIUM (architecture violation)

---

### CAP-OVW-CAPS

**Risk Flags:**

1. **HARDCODED CAPABILITY MAP**
   - `DOMAIN_CAPABILITIES` dictionary hardcoded in route
   - Not derived from registry or database
   - Drift risk if capabilities change

2. **ADAPTER BYPASS**
   - Same concern as CAP-OVW-HEALTH

**Confidence:** MEDIUM

---

### All Overview Capabilities

**Shared Risk:**
- **Founder-Only Audience:** These endpoints serve Ops/Founder Console, not Customer Console
- **L2.1 Surface Mismatch:** L2.1 surfaces are Customer Console only per Constitution
- **Cross-Tenant Data:** System health is cross-tenant; L2.1 requires tenant isolation

---

## STOP CONDITIONS ENCOUNTERED

| Condition | Capability | Resolution Required |
|-----------|------------|---------------------|
| Adapter bypassed | ALL | Design decision: refactor to use L3 or accept bypass |
| Hardcoded capability map | CAP-OVW-CAPS, CAP-OVW-DOMAIN | Registry integration needed |
| Founder vs Customer Console | ALL | L2.1 surface scope clarification |

---

## L2.1 SURFACE MAPPING

**Critical Issue:** Overview domain API serves **Founder Console**, not Customer Console.

Per Customer Console v1 Constitution:
- L2.1 surfaces are for **Customer Console only**
- Founder Console has separate jurisdiction

| Capability ID | Current Console | L2.1 Applicable? | Notes |
|---------------|-----------------|------------------|-------|
| CAP-OVW-HEALTH | Founder | **NO** | System-wide, cross-tenant |
| CAP-OVW-CAPS | Founder | **NO** | System-wide, cross-tenant |
| CAP-OVW-DOMAIN | Founder | **NO** | System-wide, cross-tenant |
| CAP-OVW-CAP-DETAIL | Founder | **NO** | System-wide, cross-tenant |
| CAP-OVW-ELIGIBILITY | Founder | **NO** | System-wide, cross-tenant |

**Gap Identified:** L2.1 seed defines `OVERVIEW.SYSTEM_HEALTH.*` surfaces, but NO Customer Console API exists for Overview domain.

---

## ADDITIONAL CAPABILITIES REQUIRED (For L2.1 Alignment)

If L2.1 Overview surfaces are to be populated, Customer Console needs:

| Needed Capability | Description | Notes |
|-------------------|-------------|-------|
| CAP-OVW-CUSTOMER-STATUS | Tenant-scoped system status | "Is MY system okay?" |
| CAP-OVW-CUSTOMER-METRICS | Tenant-scoped health metrics | Usage, limits, health |

These do NOT exist. The current `platform.py` serves Founder Console only.

---

## PHASE 1 COMPLETION STATUS

| Criterion | Status |
|-----------|--------|
| All capabilities present in intelligence table | ✅ 5 capabilities documented |
| All adapters/operators cross-referenced | ✅ Adapter exists but bypassed |
| All UNKNOWNs explicit | ✅ None |
| All risks surfaced | ✅ 4 risk categories |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Overview domain)

**Critical Finding:** Overview L2.1 surfaces have NO Customer Console implementation.

---

## References

- `backend/app/api/platform.py` — L2 API routes (Founder only)
- `backend/app/adapters/platform_eligibility_adapter.py` — L3 adapter (unused)
- `backend/app/services/platform/platform_health_service.py` — L4 service (too slow)
- PIN-284 — Platform Monitoring System
