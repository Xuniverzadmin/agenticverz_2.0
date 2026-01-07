# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Domain: Connectivity (Sidebar Secondary Section)

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**Category:** Secondary Navigation / Connectivity
**L2.1 Surfaces:** NOT IN L2.1 SEED (sidebar secondary section)

---

## EXECUTIVE SUMMARY

The Connectivity domain covers **API Keys** and **Integrations**:
- **API Keys:** IMPLEMENTED (Customer Console via guard.py + tenants.py)
- **Integrations:** NOT IMPLEMENTED for Customer Console

**Critical Finding:** This domain is NOT in the L2.1 frozen seed surfaces. The L2.1 seed only covers the 5 Core Lens domains (Overview, Activity, Incidents, Policies, Logs).

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Capability: CAP-KEY-LIST (List API Keys - Customer)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-KEY-LIST` | `guard.py:1078` |
| capability_name | List API Keys | `GET /guard/keys` |
| description | List API keys with status for customer tenant | `guard.py:1078-1099` |
| mode | **READ** | No state mutation |
| scope | **BULK** | List of keys |
| mutates_state | **NO** | Read-only |
| bulk_support | **YES** | Returns all keys |
| latency_profile | **LOW** | L3→L4 query |
| execution_style | **SYNC** | `guard.py:1079` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerKeysAdapter` | `customer_keys_adapter.py:86` |
| operators | `CustomerKeysAdapter.list_keys()` | `customer_keys_adapter.py:104-153` |
| input_contracts | `tenant_id (REQUIRED via query param)` | Route signature |
| output_contracts | `List[CustomerKeyInfo]` | `customer_keys_adapter.py:51-62` |
| side_effects | **NONE** | Pure read |
| failure_modes | 500 Internal error | Standard |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `guard.py:1078-1099`, `customer_keys_adapter.py:104-153` |
| l2_1_aligned | **NOT IN SEED** | CONNECTIVITY not in L2.1 |
| risk_flags | Key prefix exposure only (secure by design) |

---

### Capability: CAP-KEY-FREEZE (Freeze API Key)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-KEY-FREEZE` | `guard.py:1107` |
| capability_name | Freeze API Key | `POST /guard/keys/{key_id}/freeze` |
| description | Freeze an API key - blocks all requests using this key | `guard.py:1107-1137` |
| mode | **WRITE** | Mutates key status |
| scope | **SINGLE** | Single key |
| mutates_state | **YES** | Sets is_frozen = true |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | L3→L4 write |
| execution_style | **SYNC** | `guard.py:1108` |
| reversibility | **YES** | Can unfreeze |
| authority_required | **HUMAN** | Console token (implicit) |
| adapters | `CustomerKeysAdapter` | `customer_keys_adapter.py:86` |
| operators | `CustomerKeysAdapter.freeze_key()` → `KeysWriteService.freeze_key()` | `customer_keys_adapter.py:195-233` |
| input_contracts | `key_id (REQUIRED)`, `tenant_id (REQUIRED via query param)` | Route params |
| output_contracts | `{status, key_id, message}` | `guard.py:1135` |
| side_effects | **Key blocked** | All requests using key rejected |
| failure_modes | 404 Key not found | `guard.py:1133` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Idempotent |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:1107-1137`, `customer_keys_adapter.py:195-233` |
| l2_1_aligned | **NOT IN SEED** | CONNECTIVITY not in L2.1 |
| risk_flags | Idempotent (freeze twice = same result) |

---

### Capability: CAP-KEY-UNFREEZE (Unfreeze API Key)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-KEY-UNFREEZE` | `guard.py:1139` |
| capability_name | Unfreeze API Key | `POST /guard/keys/{key_id}/unfreeze` |
| description | Unfreeze an API key - resumes request processing | `guard.py:1139-1155` |
| mode | **WRITE** | Mutates key status |
| scope | **SINGLE** | Single key |
| mutates_state | **YES** | Sets is_frozen = false |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | L3→L4 write |
| execution_style | **SYNC** | `guard.py:1140` |
| reversibility | **YES** | Can freeze again |
| authority_required | **HUMAN** | Console token (implicit) |
| adapters | `CustomerKeysAdapter` | `customer_keys_adapter.py:86` |
| operators | `CustomerKeysAdapter.unfreeze_key()` → `KeysWriteService.unfreeze_key()` | `customer_keys_adapter.py:235-273` |
| input_contracts | `key_id (REQUIRED)`, `tenant_id (REQUIRED via query param)` | Route params |
| output_contracts | `{status, key_id, message}` | `guard.py:1155` |
| side_effects | **Key unblocked** | Requests now processed |
| failure_modes | 404 Key not found | `guard.py:1152` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Idempotent |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:1139-1155`, `customer_keys_adapter.py:235-273` |
| l2_1_aligned | **NOT IN SEED** | CONNECTIVITY not in L2.1 |
| risk_flags | Idempotent (unfreeze twice = same result) |

---

### Capability: CAP-KEY-LIST-ADMIN (List API Keys - Admin)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-KEY-LIST-ADMIN` | `tenants.py:275` |
| capability_name | List API Keys (Admin) | `GET /api/v1/api-keys` |
| description | List all API keys for tenant (admin-only) | `tenants.py:275-305` |
| mode | **READ** | No state mutation |
| scope | **BULK** | List of keys |
| mutates_state | **NO** | Read-only |
| bulk_support | **YES** | Returns all keys |
| latency_profile | **LOW** | L4 service query |
| execution_style | **ASYNC** | `tenants.py:276` |
| reversibility | **N/A** | Read operation |
| authority_required | **ADMIN** | `admin:*` or `keys:read` |
| adapters | None (direct service) | - |
| operators | `TenantService.list_api_keys()` | `tenants.py:291` |
| input_contracts | `include_revoked (optional)`, TenantContext | Route params |
| output_contracts | `List[APIKeyResponse]` | `tenants.py:88-98` |
| side_effects | **NONE** | Pure read |
| failure_modes | 403 Permission denied | `tenants.py:286-289` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `tenants.py:275-305` |
| l2_1_aligned | **NOT IN SEED** | CONNECTIVITY not in L2.1 |
| risk_flags | Requires explicit permission |

---

### Capability: CAP-KEY-CREATE (Create API Key)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-KEY-CREATE` | `tenants.py:308` |
| capability_name | Create API Key | `POST /api/v1/api-keys` |
| description | Create new API key for tenant | `tenants.py:308-354` |
| mode | **WRITE** | Creates new key |
| scope | **SINGLE** | Single key |
| mutates_state | **YES** | Inserts new API key |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | L4 service write |
| execution_style | **ASYNC** | `tenants.py:309` |
| reversibility | **PARTIAL** | Key can be revoked but not deleted |
| authority_required | **ADMIN** | `admin:*` or `keys:create` |
| adapters | None (direct service) | - |
| operators | `TenantService.create_api_key()` | `tenants.py:327-337` |
| input_contracts | `APIKeyCreateRequest` | `tenants.py:77-85` |
| output_contracts | `APIKeyCreatedResponse` (includes full key ONCE) | `tenants.py:101-104` |
| side_effects | **Key created** | New key usable immediately |
| failure_modes | 403 Permission denied, 429 Quota exceeded | `tenants.py:322-325, 351-354` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **NO** | Non-idempotent (creates new ID each time) |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `tenants.py:308-354` |
| l2_1_aligned | **NOT IN SEED** | CONNECTIVITY not in L2.1 |
| risk_flags | **FULL KEY SHOWN ONCE** - store immediately |

---

### Capability: CAP-KEY-REVOKE (Revoke API Key)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-KEY-REVOKE` | `tenants.py:357` |
| capability_name | Revoke API Key | `DELETE /api/v1/api-keys/{key_id}` |
| description | Permanently revoke an API key | `tenants.py:357-385` |
| mode | **WRITE** | Revokes key permanently |
| scope | **SINGLE** | Single key |
| mutates_state | **YES** | Sets key status to revoked |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | L4 service write |
| execution_style | **ASYNC** | `tenants.py:358` |
| reversibility | **NO** | Cannot un-revoke |
| authority_required | **ADMIN** | `admin:*` or `keys:revoke` |
| adapters | None (direct service) | - |
| operators | `TenantService.revoke_api_key()` | `tenants.py:376-381` |
| input_contracts | `key_id (REQUIRED)`, `reason (optional query)` | Route params |
| output_contracts | `{success, message}` | `tenants.py:382` |
| side_effects | **Key permanently disabled** | All requests rejected |
| failure_modes | 403 Permission denied, 404 Key not found | `tenants.py:371-374, 384-385` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Idempotent (revoke twice = same result) |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `tenants.py:357-385` |
| l2_1_aligned | **NOT IN SEED** | CONNECTIVITY not in L2.1 |
| risk_flags | **IRREVERSIBLE** - create new key instead |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

| adapter_id | operator_name | capability_id | sync/async | side_effects | l2_1_surface | layer_route |
|------------|---------------|---------------|------------|--------------|--------------|-------------|
| CustomerKeysAdapter | list_keys() | CAP-KEY-LIST | sync | None | (not seeded) | L2_1 |
| CustomerKeysAdapter | freeze_key() | CAP-KEY-FREEZE | sync | Key blocked | (not seeded) | GC_L |
| CustomerKeysAdapter | unfreeze_key() | CAP-KEY-UNFREEZE | sync | Key unblocked | (not seeded) | GC_L |
| (direct) | TenantService.list_api_keys() | CAP-KEY-LIST-ADMIN | async | None | (not seeded) | L2_1 |
| (direct) | TenantService.create_api_key() | CAP-KEY-CREATE | async | Key created | (not seeded) | GC_L |
| (direct) | TenantService.revoke_api_key() | CAP-KEY-REVOKE | async | Key revoked | (not seeded) | GC_L |

### Layer Architecture

**Customer Console API Keys (guard.py):**
```
L2 (guard.py) — API routes + console auth
      ↓
L3 (CustomerKeysAdapter) — Translation + tenant isolation
      ↓
L4 (KeysReadService/KeysWriteService) — Domain logic
      ↓
L6 (Database)
```

**Admin API Keys (tenants.py):**
```
L2 (tenants.py) — API routes + permission check
      ↓
L4 (TenantService) — Domain logic (NO L3 adapter)
      ↓
L6 (Database)
```

**Architectural Status:** MIXED
- Customer Console keys: CLEAN (L2→L3→L4)
- Admin keys: BYPASSES L3 (direct L2→L4)

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### API Keys Capabilities

**Risk Flags:**

1. **IRREVERSIBLE REVOCATION**
   - CAP-KEY-REVOKE cannot be undone
   - Customer must create new key after revocation
   - **Mitigation:** Use freeze/unfreeze for temporary blocks

2. **FULL KEY EXPOSURE (Once)**
   - CAP-KEY-CREATE shows full key in response ONCE
   - Never shown again
   - **Mitigation:** Customer must store immediately

3. **ADMIN PERMISSION REQUIRED**
   - CAP-KEY-CREATE, CAP-KEY-REVOKE, CAP-KEY-LIST-ADMIN require admin permission
   - CAP-KEY-LIST, CAP-KEY-FREEZE, CAP-KEY-UNFREEZE available to all console users
   - **Risk:** Permission boundary between admin and regular user

**Confidence:** HIGH

---

### Integrations (NOT IMPLEMENTED)

**Critical Gap:** Customer Console has NO integration management:
- No webhook configuration
- No external system connections
- No OAuth app management
- No notification channel setup

**Current State:**
- `integration.py` exists but serves Founder Console only (M25 Learning Loop)
- Webhooks mentioned in settings response as `notification_slack_webhook: None`

**Recommendation:**
- Phase 2 question: Should Integrations be implemented for Customer Console v1?
- If yes: Create L2.1 surfaces for CONNECTIVITY.INTEGRATIONS.*

---

## STOP CONDITIONS ENCOUNTERED

1. **Integrations NOT IMPLEMENTED** — No Customer Console integration endpoints exist

---

## L2.1 SURFACE MAPPING

**CRITICAL FINDING: CONNECTIVITY is NOT in L2.1 seed.**

The L2.1 surface registry only contains the 5 Core Lens domains:
- Overview, Activity, Incidents, Policies, Logs

CONNECTIVITY (API Keys, Integrations) is a **sidebar secondary section** and is NOT governed by L2.1 epistemic surfaces.

### Proposed L2.1 Extension (If Required)

| Proposed Surface | Domain | Subdomain | Topic |
|------------------|--------|-----------|-------|
| CONNECTIVITY.API_KEYS.KEY_LIST | Connectivity | API_KEYS | KEY_LIST |
| CONNECTIVITY.API_KEYS.KEY_DETAILS | Connectivity | API_KEYS | KEY_DETAILS |
| CONNECTIVITY.INTEGRATIONS.WEBHOOK_LIST | Connectivity | INTEGRATIONS | WEBHOOK_LIST |
| CONNECTIVITY.INTEGRATIONS.WEBHOOK_DETAILS | Connectivity | INTEGRATIONS | WEBHOOK_DETAILS |

---

## PHASE 1 COMPLETION STATUS

| Criterion | Status |
|-----------|--------|
| All capabilities documented | ✅ 6 API Key capabilities |
| All adapters/operators cross-referenced | ✅ |
| All UNKNOWNs explicit | ✅ |
| All risks surfaced | ✅ Revocation irreversible, key exposure |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Connectivity domain)

**Overall Assessment:**
- API Keys: IMPLEMENTED (6 capabilities)
- Integrations: NOT IMPLEMENTED
- NOT in L2.1 seed (sidebar secondary section)

---

## References

- `backend/app/api/guard.py` — Customer Console API (keys endpoints)
- `backend/app/api/tenants.py` — Admin API (keys CRUD)
- `backend/app/adapters/customer_keys_adapter.py` — L3 adapter
- `backend/app/services/keys_service.py` — L4 service
- PIN-280, PIN-281 — L2 Promotion Governance

