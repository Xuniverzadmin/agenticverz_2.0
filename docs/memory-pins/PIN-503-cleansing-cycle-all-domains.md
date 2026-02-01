# PIN-503 — Cleansing Cycle: All 10 Customer Domains

**Status:** COMPLETE
**Date:** 2026-01-31
**Category:** Architecture / HOC Migration
**Depends On:** PIN-493 through PIN-502 (canonical consolidation), PIN-485 (cus/general abolition), PIN-484 (HOC Topology V2.0.0)
**Blocks:** PIN-487 Part 2 (Loop Model construction)

---

## Purpose

Post-consolidation cleansing of all 10 HOC customer domains. Eliminates dead imports to abolished `cus/general/`, disconnects active legacy `app.services` imports, corrects stale docstring references, and adds deterministic cleansing checks to all tally scripts.

---

## Violation Categories

| Category | Description | Action | Count |
|----------|-------------|--------|-------|
| A | Dead imports to abolished `cus/general/` | Repoint to `hoc_spine` equivalent | 2 |
| B (active) | Active `app.services` imports | Disconnect + stub with TODO | 2 |
| B (docstring) | Stale `app.services` in docstrings/Usage examples | Update to HOC path | 9 |
| C | Already-disconnected stubs | No action (wait for rewire phase) | 4 files |
| D | L2→L5 bypass violations | DOCUMENT ONLY — requires Loop Model | ~26 |
| E | Cross-domain L5→L5/L6 violations | DOCUMENT ONLY — requires L4 Coordinator | ~24 |
| F | L5→L4 reaching-up violations | DOCUMENT ONLY — requires event/callback | 3 |

---

## Category A: Dead Imports Repointed (2)

| # | Domain | File | Old Import | New Import |
|---|--------|------|-----------|------------|
| A1 | controls | `adapters/customer_killswitch_adapter.py` | `app.hoc.cus.general.L5_controls.engines.guard_write_engine.GuardWriteService` | `app.hoc.cus.hoc_spine.authority.guard_write_engine.GuardWriteService` |
| A2 | policies | `adapters/founder_contract_review_adapter.py` | `app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine.ContractState` | `app.hoc.cus.hoc_spine.authority.contracts.contract_engine.ContractState` |

---

## Category B: Active Legacy Imports Disconnected (2)

| # | Domain | File | Old Import | New State |
|---|--------|------|-----------|-----------|
| B1 | logs | `L5_engines/trace_facade.py` line 239 | `from app.services.audit.models import AuditAction, AuditDomain, DomainAck` | Repointed to `app.hoc.cus.hoc_spine.schemas.rac_models` (100% match per Phase 5 D738/D747) |
| B2 | activity | `L5_engines/cus_telemetry_engine.py` line 44 | `from app.services.cus_telemetry_engine import BatchIngestResult, CusTelemetryEngine, IngestResult, get_cus_telemetry_engine` | Disconnected — stub classes with `NotImplementedError`, TODO rewire |

---

## Category B: Stale Docstring References Corrected (9)

| # | Domain | File | Old Reference | New Reference |
|---|--------|------|--------------|---------------|
| 1 | controls | `L5_engines/alert_fatigue_engine.py` | `from app.services.alert_fatigue import ...` | `from app.hoc.cus.controls.L5_engines.alert_fatigue_engine import ...` |
| 2 | controls | `L5_engines/controls_facade.py` | `from app.services.controls.facade import ...` | `from app.hoc.cus.controls.L5_engines.controls_facade import ...` |
| 3 | policies | `L5_engines/failure_mode_handler.py` | `app.services.governance.profile` | `app.hoc.cus.hoc_spine.authority.profile_policy_mode` |
| 4 | logs | `L5_engines/trace_facade.py` | `from app.services.observability.trace_facade import ...` | `from app.hoc.cus.logs.L5_engines.trace_facade import ...` |
| 5 | logs | `L5_engines/evidence_facade.py` | `from app.services.evidence.facade import ...` | `from app.hoc.cus.logs.L5_engines.evidence_facade import ...` |
| 6 | logs | `L5_engines/certificate.py` | `from app.services.certificate import ...` | `from app.hoc.cus.logs.L5_engines.certificate import ...` |
| 7 | activity | `L5_engines/cus_telemetry_engine.py` | `Re-exports from existing cus_telemetry_engine.py` | `Legacy import disconnected (PIN-503)` |
| 8 | analytics | `L5_engines/detection_facade.py` | `from app.services.detection.facade import ...` | `from app.hoc.cus.analytics.L5_engines.detection_facade import ...` |
| 9 | integrations | `L5_engines/datasources_facade.py` | `from app.services.datasources.facade import ...` | `from app.hoc.cus.integrations.L5_engines.datasources_facade import ...` |

---

## Per-Domain Results

| # | Domain | PIN | Cat A | Cat B (active) | Cat B (docstring) | Cleansing Checks | Tally |
|---|--------|-----|-------|----------------|-------------------|-----------------|-------|
| 1 | controls | PIN-499 | 1 repointed | 0 | 2 fixed | 3 added | ALL PASS |
| 2 | policies | PIN-495 | 1 repointed | 0 | 1 fixed | 4 added | ALL PASS |
| 3 | logs | PIN-496 | 0 | 1 disconnected | 3 fixed | 4 added | ALL PASS |
| 4 | activity | PIN-494 | 0 | 1 disconnected | 1 fixed | 4 added | ALL PASS |
| 5 | analytics | PIN-497 | 0 | 0 | 1 fixed | 3 added | ALL PASS |
| 6 | integrations | PIN-498 | 0 | 0 | 1 fixed | 3 added | ALL PASS |
| 7 | incidents | PIN-493 | 0 | 0 | 0 | 3 added | ALL PASS |
| 8 | account | PIN-500 | 0 | 0 | 0 | 3 added | ALL PASS |
| 9 | api_keys | PIN-501 | 0 | 0 | 0 | 2 added | ALL PASS |
| 10 | overview | PIN-502 | 0 | 0 | 0 | 2 added | ALL PASS |

**Totals:** 2 dead imports repointed, 2 legacy imports disconnected, 9 docstring references fixed, 31 cleansing checks added, 10 literature files updated.

---

## Tally Scripts Modified

| Script | Checks Added |
|--------|-------------|
| `scripts/ops/hoc_controls_tally.py` | `check_no_abolished_general`, `check_dead_import_repointed`, `check_no_active_legacy_all` |
| `scripts/ops/hoc_policies_tally.py` | `check_no_abolished_general`, `check_dead_import_repointed`, `check_no_active_legacy_all`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_logs_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all`, `check_trace_facade_repointed`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_activity_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all`, `check_legacy_disconnected`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_analytics_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_integrations_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_incidents_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_account_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all`, `check_no_docstring_legacy` |
| `scripts/ops/hoc_api_keys_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all` |
| `scripts/ops/hoc_overview_tally.py` | `check_no_abolished_general`, `check_no_active_legacy_all` |

---

## Literature Files Updated

| Domain | File |
|--------|------|
| controls | `literature/hoc_domain/controls/CONTROLS_CANONICAL_SOFTWARE_LITERATURE.md` |
| policies | `literature/hoc_domain/policies/POLICIES_CANONICAL_SOFTWARE_LITERATURE.md` |
| logs | `literature/hoc_domain/logs/LOGS_CANONICAL_SOFTWARE_LITERATURE.md` |
| activity | `literature/hoc_domain/activity/ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md` |
| analytics | `literature/hoc_domain/analytics/ANALYTICS_CANONICAL_SOFTWARE_LITERATURE.md` |
| integrations | `literature/hoc_domain/integrations/INTEGRATIONS_CANONICAL_SOFTWARE_LITERATURE.md` |
| incidents | `literature/hoc_domain/incidents/INCIDENT_CANONICAL_SOFTWARE_LITERATURE.md` |
| account | `literature/hoc_domain/account/ACCOUNT_CANONICAL_SOFTWARE_LITERATURE.md` |
| api_keys | `literature/hoc_domain/api_keys/API_KEYS_CANONICAL_SOFTWARE_LITERATURE.md` |
| overview | `literature/hoc_domain/overview/OVERVIEW_CANONICAL_SOFTWARE_LITERATURE.md` |

---

## Deferred Violations (Loop Model — PIN-487 Part 2)

### Category D: L2→L5 Bypass Violations (~26)

| L2 File | Violations | Domains Reached |
|---------|------------|-----------------|
| `policies/aos_accounts.py` | 7 | account L5 |
| `recovery/recovery.py` | 8 | incidents L5, policies L6, controls L6 |
| `policies/analytics.py` | 4 | analytics L5 |
| `policies/guard.py` | 1 | logs L5 |
| `policies/simulate.py` | 1 | controls L5_schemas |
| `policies/override.py` | 1 | controls L6 |
| `incidents/incidents.py` | 3 | incidents L6 |
| `policies/workers.py` | 2 | policies L6 |
| `recovery/recovery_ingest.py` | 1 | policies L6 |

**Resolution:** Requires Loop Model infrastructure — Registry + Executor + Coordinator (PIN-487 Part 2).

### Category E: Cross-Domain L5→L5/L6 Violations (~24)

Key violations:

| Source Domain | Source File | Target Domain | Target |
|--------------|------------|---------------|--------|
| incidents | `incident_write_engine.py` | logs | `audit_ledger_engine` |
| policies | `policy_limits_engine.py` | logs | `audit_ledger_driver` |
| policies | `policy_proposal_engine.py` | logs | `audit_ledger_driver` |
| policies | `policy_rules_engine.py` | logs | `audit_ledger_driver` |
| integrations | `customer_logs_adapter.py` | logs | `logs_read_engine` |
| controls | `threshold_driver.py` | activity | `run_signal_driver` |
| activity | `L6_drivers/__init__.py` | controls | `threshold_driver` |

**Resolution:** Requires L4 Coordinator to mediate cross-domain operations.

### Category F: L5→L4 Reaching Up (3)

| File | Calls |
|------|-------|
| `cost_bridges_engine` | `orchestrator.create_incident_from_cost_anomaly_sync` |
| `activity/__init__` | `orchestrator.run_governance_facade` |
| `eligibility_engine` | `orchestrator` |

**Resolution:** Requires event/callback pattern (inversion of control).

---

## Verification Commands

```bash
# Run all 10 tally scripts
for domain in controls policies logs activity analytics integrations incidents account api_keys overview; do
  python3 scripts/ops/hoc_${domain}_tally.py
done

# Verify zero active app.services imports in hoc/cus/
grep -r "from app.services" backend/app/hoc/cus/ --include="*.py" | grep -v "#" | grep -v '"""' | grep -v "'''" | grep -v ".deprecated"
# Expected: only DISCONNECTED/Previously markers in docstrings

# Verify zero cus.general imports
grep -r "cus.general" backend/app/hoc/cus/ --include="*.py" | grep -v "#"
# Expected: ZERO matches
```

---

## What This PIN Achieved

1. **Zero active `app.services` imports** across all 10 customer domains
2. **Zero `cus.general` imports** (abolished domain fully disconnected)
3. **Zero stale docstring references** to legacy paths
4. **31 deterministic cleansing checks** added to tally scripts (regression guard)
5. **10 literature files updated** with cleansing sections
6. **Complete documentation** of deferred violations for Loop Model phase

## What Remains (Next Phase)

- **PIN-487 Part 2:** Loop Model construction (Registry + Executor + Coordinator)
- **L2→L5 bypass resolution:** ~26 imports require L4 routing
- **Cross-domain L5→L5/L6 resolution:** ~24 imports require L4 Coordinator mediation
- **L5→L4 inversion:** 3 files require event/callback pattern
- **TODO stub rewiring:** 4 disconnected engines require HOC-native implementations
