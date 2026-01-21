# PIN-449: LOGS Domain V2 Implementation

**Status:** LOCKED
**Created:** 2026-01-19
**Category:** Architecture / Domain Migration

---

## Summary

Complete implementation of LOGS Domain V2 with unified facade at `/api/v1/logs/*`, establishing three topics (LLM_RUNS, SYSTEM_LOGS, AUDIT) with O1-O5 depth levels and global Evidence Metadata contract.

---

## Details

## Executive Summary

The LOGS domain underwent a **ground-up architecture implementation** on 2026-01-19, establishing a unified facade with proper O-level structure and audit-grade evidence handling.

## Implementation Outcome

| Property | Status |
|----------|--------|
| Unified facade | `/api/v1/logs/*` (19 GET endpoints) |
| Topics implemented | 3 (LLM_RUNS, SYSTEM_LOGS, AUDIT) |
| O-levels per topic | 5 (O1-O5) |
| Evidence metadata | INV-LOG-META-001 enforced |
| Mutation routes | 0 (read-only) |
| Security | Tenant-scoped, RBAC-protected |

## Key Components

### Endpoints (19 total)

**LLM_RUNS (6 endpoints)**
- `GET /llm-runs` - List runs
- `GET /llm-runs/{run_id}/envelope` - O1 canonical record
- `GET /llm-runs/{run_id}/trace` - O2 step-by-step
- `GET /llm-runs/{run_id}/governance` - O3 policy interaction
- `GET /llm-runs/{run_id}/replay` - O4 60-second window
- `GET /llm-runs/{run_id}/export` - O5 evidence bundle

**SYSTEM_LOGS (6 endpoints)**
- `GET /system` - List events
- `GET /system/{run_id}/snapshot` - O1 environment baseline
- `GET /system/{run_id}/telemetry` - O2 (STUB)
- `GET /system/{run_id}/events` - O3 infra events
- `GET /system/{run_id}/replay` - O4 infra replay
- `GET /system/audit` - O5 infrastructure attribution

**AUDIT (6 endpoints)**
- `GET /audit` - List entries
- `GET /audit/identity` - O1 identity lifecycle
- `GET /audit/authorization` - O2 access decisions
- `GET /audit/access` - O3 log access audit
- `GET /audit/integrity` - O4 tamper detection
- `GET /audit/exports` - O5 compliance exports

### Database Changes

| Change | Location |
|--------|----------|
| `log_exports` table | Migration 109 |
| `correlation_id` column | `audit_ledger` table |
| Immutability trigger | `log_exports` table |
| Tenant indexes | All log tables |

### Security Model

| Rule | Status |
|------|--------|
| LOGS_READ_PREFLIGHT | PUBLIC (temporary, expires 2026-03-01) |
| LOGS_READ_PRODUCTION | SESSION (logs.read permission) |
| Tenant scoping | 20 auth context checks |
| Mutation prevention | 0 POST/PUT/DELETE routes |

## Artifacts Created

| Artifact | Location |
|----------|----------|
| LOGS Facade | `backend/app/api/logs.py` |
| LogExport Model | `backend/app/models/log_exports.py` |
| Migration | `backend/alembic/versions/109_logs_domain_v2.py` |
| Contract | `docs/contracts/LOGS_DOMAIN_V2_CONTRACT.md` |
| Implementation Plan | `docs/contracts/LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md` |
| Architecture Doc | `docs/architecture/logs/LOGS_DOMAIN_V2_ARCHITECTURE.md` |
| RBAC Rules | `design/auth/RBAC_RULES.yaml` (LOGS_READ_*) |
| Gateway Config | `backend/app/auth/gateway_config.py` |

## File Reclassifications

| File | Before | After |
|------|--------|-------|
| `traces.py` | L2 Product API | L2a Internal/SDK API |
| `guard_logs.py` | L2a Product API | L2a Boundary Adapter (DEPRECATED) |

## Pipeline Results

| Phase | Status |
|-------|--------|
| Phase A Validation | PASSED (0 violations) |
| Aurora Compilation | 84 panels (15 LOGS) |
| Projection Copy | Completed |

## Capability Status

| Capability | Status | Panels |
|------------|--------|--------|
| logs.llm_runs | OBSERVED | 5 |
| logs.system_logs | DECLARED | 5 |
| logs.audit | OBSERVED | 5 |

## Future Work

1. **SDSR Scenarios**: Create and execute SDSR-LOG-* scenarios
2. **Export Downloads**: Implement signed URL downloads
3. **Telemetry Producer**: Implement SYSTEM_LOGS O2 producer
4. **Deprecation**: Finalize guard_logs.py migration

## Maintenance Rules

### DO NOT
- Add mutation routes to `/api/v1/logs/*`
- Bypass tenant scoping
- Remove immutability triggers
- Treat `traces.py` as the LOGS facade

### DO
- Use unified facade for all log viewing
- Include EvidenceMetadata in responses
- Update capability registry after SDSR
- Maintain correlation spine

---

## Related

- PIN-445: Incidents Domain V2 Migration (pattern reference)
- PIN-447: Policy Domain V2 Design
- LOGS_DOMAIN_V2_CONTRACT.md
- LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md
