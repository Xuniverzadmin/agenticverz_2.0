> **DEPRECATED (2026-02-11):** This file is NON-CANONICAL. The canonical linkage map is at:
> `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
> Do not update this file. All changes must go to the canonical root.

# HOC Usecase-to-Code Linkage Map

> Maps each usecase to its code artifacts, audit results, and status evidence.
> Companion to `INDEX.md` — statuses must stay synchronized.

---

## UC-001: LLM Run Monitoring

**Status:** YELLOW
**Audience:** cust, int, fdr
**Last Audit:** 2026-02-11

### CUS Routes (Customer)

| Route File | Domain | L4 Operation | Bypasses |
|-----------|--------|-------------|----------|
| `activity/*.py` | activity | activity.query | 0 |
| `incidents/*.py` | incidents | incidents.query | 0 |
| `logs/*.py` | logs | logs.query, account.tenant | 0 |

**Result:** 0 bypasses verified.

### INT Routes (Internal)

| Route File | L4 Operation | Bypasses | Notes |
|-----------|-------------|----------|-------|
| `int/general/sdk.py` | account.sdk_attestation | 0 | SDK handshake + attestation persistence |
| `int/general/health.py` | system.health | 0 | Platform health check |
| `int/recovery/recovery.py` | policies.recovery.match/read/write | 0 | Recovery suggest/approve/CRUD |
| `int/recovery/recovery_ingest.py` | policies.recovery.write | 0 | Recovery ingest |
| `int/agent/platform.py` | platform.health | 0 | Platform capabilities/eligibility |
| `int/agent/discovery.py` | agent.discovery_stats | 0 | Agent discovery |
| `int/agent/agents.py` | Multiple agent ops | 0 | Agent management (uses L4 bridges) |

**Result:** 7 files, 7 L4 ops, 0 blocking violations. Bridge imports are L4-level (compliant).

### FDR Routes (Founder)

| Route File | L4 Operation | Bypasses | Notes |
|-----------|-------------|----------|-------|
| `fdr/ops/retrieval_admin.py` | knowledge.planes.*, knowledge.evidence.* | 0 | Retrieval plane management |
| `fdr/ops/cost_ops.py` | ops.cost | 0 | Cost overview/anomalies/tenants |
| `fdr/account/founder_lifecycle.py` | account.lifecycle.query/transition | 0 | Lifecycle suspend/resume/terminate |
| `fdr/logs/founder_review.py` | — | 0 | **FIXED:** `text()` → `sql_text()`, removed `session.commit()` |

**Result:** 3 files with registry dispatch, 4 L4 ops, 0 blocking violations.

### Endpoint-to-Handler Mapping (v2 audit)

**Completed 2026-02-11:** Full audit across all 3 audiences.

| Audience | Files | Endpoints | L4 Ops | Violations |
|----------|-------|-----------|--------|------------|
| CUS | 44 | ~200+ | 31 | 0 blocking |
| INT | 7 | ~30+ | 7 | 0 blocking |
| FDR | 3 | 18 | 4 | 0 blocking |
| **Total** | **54** | **248+** | **42** | **0** |

### Remaining for GREEN

- Event schema enforcement deferred (documented in Phase 5.2)

---

## UC-002: Customer Onboarding

**Status:** YELLOW
**Audience:** cust, int, fdr
**Last Audit:** 2026-02-11

### Domain Authority Migration (Phase 1)

| Source | Destination | Status |
|--------|------------|--------|
| `policies/aos_accounts.py` | `account/aos_accounts.py` | MOVED (**tombstone deleted**) |
| `policies/aos_cus_integrations.py` | `integrations/aos_cus_integrations.py` | MOVED (**tombstone deleted**) |
| `policies/aos_api_key.py` | `api_keys/aos_api_key.py` | MOVED (**tombstone deleted**) |
| `logs/tenants.py` API key endpoints | `api_keys/api_key_writes.py` | EXTRACTED |

### Onboarding Gate Fix (Phase 2)

- `/tenant/api-keys` added to `ENDPOINT_STATE_REQUIREMENTS` (IDENTITY_VERIFIED)
- `/tenant/api-keys(/.*)?` added to `ENDPOINT_PATTERN_REQUIREMENTS` (IDENTITY_VERIFIED)
- Activation predicate (`check_activation_predicate`) added to `onboarding_policy.py`

### Functional Fixes (Phase 3)

| Fix | File | Status |
|-----|------|--------|
| Integration session wiring | `integrations_handler.py` | FIXED (connectors + datasources handlers now pass session) |
| Connector persistence | `connectors_facade.py` | FIXED (delegates to L6 `connector_registry_driver.py`) |
| SDK attestation persistence | `account/L5_schemas/sdk_attestation.py`, `account/L6_drivers/sdk_attestation_driver.py` | CREATED |
| SDK attestation L4 op | `account_handler.py` | ADDED (`account.sdk_attestation` operation) |
| SDK endpoint persistence | `int/general/sdk.py` | UPDATED (persists attestation via L4 dispatch) |
| Project create capability | `account/aos_accounts.py`, `accounts_facade.py`, `accounts_facade_driver.py` | ADDED (POST /accounts/projects) |

### Facade Wiring

| Facade | Imports From | Status |
|--------|-------------|--------|
| `facades/cus/account.py` | `account/aos_accounts.py` | CANONICAL |
| `facades/cus/integrations.py` | `integrations/aos_cus_integrations.py` | CANONICAL |
| `facades/cus/api_keys.py` | `api_keys/aos_api_key.py` + `api_keys/api_key_writes.py` | CANONICAL |

### CI Enforcement (Phase 5)

- Check 34 (`check_l2_domain_ownership`): BLOCKING — scans L2 files for cross-domain L4 dispatch

### V2 Gap Fixes (2026-02-11)

| Fix | Status | Evidence |
|-----|--------|----------|
| Tombstones deleted (3 files) | DONE | `policies/aos_accounts.py`, `policies/aos_cus_integrations.py`, `policies/aos_api_key.py` deleted |
| Activation predicate wired to L4 | DONE | `onboarding_handler.py` — sync + async paths, founder override supported |
| SDK attestation handshake fix | DONE | `sdk.py` — real sync session via DI, errors logged explicitly |
| SDK attestation DB migration | DONE | `alembic/versions/127_create_sdk_attestations.py` — table with UPSERT constraint |
| Connector facade session fix | DONE | Singleton pattern cleaned, session accepted for forward-compat |
| Handler param contract hardening | DONE | `_STRIP_PARAMS` pattern in all 3 integrations handlers |
| Project-create path verified | DONE | Full L2→L4→L5→L6 chain confirmed |
| API key URL policy | DECIDED | Keep split (read `/api-keys`, write `/tenant/api-keys`), domain authority by directory |

### Remaining for GREEN

- Event schema enforcement deferred (documented in Phase 5.2)
- URL unification deferred (policy decision: keep split for backward compatibility)

---

## Minimum Event Schema (Shared Contract)

Required fields for all domain events (UC-001 and UC-002):

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | UUID | Unique event identifier |
| `event_type` | string | Event type (e.g., `RUN_STARTED`, `KEY_CREATED`) |
| `tenant_id` | UUID | Tenant context |
| `project_id` | UUID | Project context |
| `actor_type` | string | `CUSTOMER`, `INTERNAL`, `FOUNDER`, `SYSTEM` |
| `actor_id` | string | Actor identifier |
| `decision_owner` | string | Domain that owns this decision |
| `sequence_no` | int | Monotonic sequence within tenant |
| `schema_version` | string | Schema version (semver) |

**Runtime enforcement:** Deferred. Documented as contract for UC-001 and UC-002.
