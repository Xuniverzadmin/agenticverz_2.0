# HOC Migration - Iteration 2 Audit Report

**Date:** 2026-01-23
**Status:** COMPLETE (L5/L6 Resolved)
**Reference:** ITERATION1_AUDIT_REPORT.md, PHASE1_MIGRATION_PLAN.md

---

## Executive Summary

Iteration 2 completes the manual review of 34 L5/L6 ambiguous services. **All services have been classified** based on file header analysis.

| Metric | Iteration 1 | Iteration 2 | Change |
|--------|-------------|-------------|--------|
| **L5/L6 Ambiguous** | 34 | 0 | -34 ✅ |
| **L4 Domain Engines** | 102 | 130 | +28 |
| **L6 Platform Substrate** | 124 | 128 | +4 |
| **L3 Boundary Adapters** | 77 | 78 | +1 |
| **DELETE** | 14 | 15 | +1 |

---

## L5/L6 Resolution Details

### Resolution Summary

| Resolution | Count | Description |
|------------|-------|-------------|
| → L4 | 28 | Domain Engines (business logic) |
| → L6 | 4 | Platform Substrate (data stores) |
| → L3 | 1 | Boundary Adapter |
| → DELETE | 1 | Quarantined duplicate |
| **Total** | 34 | All resolved |

### L4 Domain Engines (28 files)

Services with business logic, domain operations, and governance decisions:

| File | Domain | Reason |
|------|--------|--------|
| `app/auth/api_key_service.py` | Auth | API key validation logic |
| `app/services/activity/attention_ranking_service.py` | Activity | Ranking algorithm |
| `app/services/activity/cost_analysis_service.py` | Activity | Cost anomaly detection |
| `app/services/activity/pattern_detection_service.py` | Activity | Pattern detection logic |
| `app/services/activity/signal_feedback_service.py` | Activity | User feedback processing |
| `app/services/cus_credential_service.py` | Integrations | Credential encryption |
| `app/services/cus_enforcement_service.py` | Integrations | Policy evaluation |
| `app/services/cus_health_service.py` | Integrations | Health checking logic |
| `app/services/cus_integration_service.py` | Integrations | CRUD + lifecycle |
| `app/services/cus_telemetry_service.py` | Integrations | Telemetry ingestion |
| `app/services/iam/iam_service.py` | Platform | IAM decisions |
| `app/services/incidents/incident_pattern_service.py` | Incidents | Pattern detection |
| `app/services/incidents/postmortem_service.py` | Incidents | Postmortem analysis |
| `app/services/incidents/recurrence_analysis_service.py` | Incidents | Recurrence analysis |
| `app/services/keys_service.py` | API Keys | Key domain operations |
| `app/services/limits/override_service.py` | Policies | Override workflow |
| `app/services/limits/policy_limits_service.py` | Policies | Limit CRUD |
| `app/services/limits/policy_rules_service.py` | Policies | Rule validation |
| `app/services/limits/simulation_service.py` | Policies | Limit simulation |
| `app/services/llm_failure_service.py` | Activity | Failure fact persistence |
| `app/services/llm_threshold_service.py` | Policies | Threshold evaluation |
| `app/services/notifications/channel_service.py` | Integrations | Channel management |
| `app/services/ops_incident_service.py` | Ops | Ops incident translation |
| `app/services/platform/platform_health_service.py` | Platform | Health authority |
| `app/services/policy/snapshot_service.py` | Policies | Snapshot immutability |
| `app/services/policy_violation_service.py` | Policies | Violation persistence |
| `app/services/sandbox/sandbox_service.py` | Platform | Sandbox orchestration |
| `app/houseofcards/internal/platform/monitoring/platform_health_service.py` | Platform | Already in HOC |

### L6 Platform Substrate (4 files)

Services that primarily perform database read/write operations:

| File | Reason |
|------|--------|
| `app/services/tenant_service.py` | Tenant CRUD, API key management |
| `app/services/worker_registry_service.py` | Worker discovery, DB queries |
| `app/services/external_response_service.py` | Response persistence |
| `app/memory/memory_service.py` | Redis caching + DB persistence |

### L3 Boundary Adapter (1 file)

| File | Reason |
|------|--------|
| `app/services/export_bundle_service.py` | Console → Platform translation |

### DELETE (1 file)

| File | Reason |
|------|--------|
| `app/houseofcards/duplicate/integrations/credential_service.py` | Quarantined duplicate |

---

## Final Classification Results

### By Layer

| Layer | Count | % | Description |
|-------|-------|---|-------------|
| **L5** | 499 | 49.5% | Business logic / Engines |
| **L6** | 167 | 16.6% | Data Layer (schemas + drivers) |
| **L4** | 130 | 12.9% | Domain Engines (governance) |
| **L2** | 83 | 8.2% | HTTP APIs |
| **L3** | 78 | 7.7% | Boundary Adapters |
| **L7** | 30 | 3.0% | Database models (STAYS) |
| **DELETE** | 15 | 1.5% | Deprecated/duplicate files |
| **L2-Infra** | 4 | 0.4% | API middleware/dependencies |
| **N/A** | 3 | 0.3% | Files marked for deletion |
| **L5/L6** | 0 | 0% | ✅ All resolved |

**Note:** L5-Schema (39 files) was merged into L6. L6 is now the "Data Layer" containing:
- Schemas (data contracts, Pydantic models) - 39 files
- Drivers (database read/write operations) - 128 files

### By Audience

| Audience | Count | % | Target Root |
|----------|-------|---|-------------|
| **CUSTOMER** | 619 | 61.3% | `app/houseofcards/customer/` |
| **INTERNAL** | 342 | 33.9% | `app/houseofcards/internal/` |
| **FOUNDER** | 30 | 3.0% | `app/houseofcards/founder/` |
| **DEPRECATED** | 18 | 1.8% | DELETE |

### By Action

| Action | Count | % | Description |
|--------|-------|---|-------------|
| **TRANSFER** | 961 | 95.2% | Move to app/houseofcards/ |
| **STAYS** | 30 | 3.0% | L7 models stay in app/ |
| **DELETE** | 18 | 1.8% | Deprecated/duplicate files |

---

## Classification Methodology

### Layer Determination Criteria

For `_service.py` files, the layer was determined by examining:

1. **File Header** - Layer declaration in comments
2. **Role Description** - What the service does
3. **Callers** - Who calls this service
4. **Allowed Imports** - What layers it can import

**L4 Indicators:**
- Business logic, domain operations
- Policy evaluation, decisions
- Aggregation and analysis
- Orchestration (not execution)

**L6 Indicators:**
- Database CRUD operations
- Storage/persistence
- Registry/discovery queries
- Caching layer

**L3 Indicators:**
- Console → Platform translation
- < 200 LOC
- No business logic

---

## Validation Checklist

### Automated Checks (Passed)

- [x] All 1,009 files have audience assigned (0 UNKNOWN)
- [x] All 1,009 files have layer assigned (0 L5/L6 ambiguous)
- [x] All STAYS files are L7 models (30 files)
- [x] All DEPRECATED files have action = DELETE (18 files)
- [x] No facades assigned to L4/L5/L6 (all 78 L3)
- [x] No engines assigned to L6 (business logic → L4/L5)

### Manual Verification (Complete)

- [x] Reviewed 34 L5/L6 services
- [x] Verified layer matches file header declaration
- [x] Confirmed target_path patterns are correct
- [x] No cross-audience violations

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Iteration 1 CSV | `docs/architecture/migration/MIGRATION_INVENTORY_ITER1.csv` |
| Iteration 2 CSV | `docs/architecture/migration/MIGRATION_INVENTORY_ITER2.csv` |
| Classification Script | `scripts/migration/classify_inventory.py` |
| Iteration 1 Report | `docs/architecture/migration/ITERATION1_AUDIT_REPORT.md` |
| This Report | `docs/architecture/migration/ITERATION2_AUDIT_REPORT.md` |

---

## Next Steps

### Ready for Phase 2

With Iteration 2 complete, the inventory is ready for Phase 2 execution:

1. **Generate Migration Script:** Create `execute_migration.sh` from approved CSV
2. **Execute Migration:** Move files to `app/houseofcards/` structure
3. **Run BLCA:** Verify 0 violations
4. **Update Imports:** Fix all import statements
5. **Phase 5 Cleanup:** Delete `app/services/*` after validation

### Option B Architectural Decision

Per user decision, files migrate to `app/houseofcards/` (not outside `app/`).
Legacy code in `app/services/` will be deleted in Phase 5 after migration is complete and validated.

---

**Report Status:** COMPLETE
**Iteration Status:** ALL CLASSIFICATIONS RESOLVED
**Next Phase:** Phase 2 - Migration Execution
