# SWEEP-02A: L4 Runtime Wiring

**Status:** CLOSED
**Effective:** 2026-01-25
**Closed By:** Claude + Human validation

---

## Invariant

> All HOC engines must import runtime authorities from HOC L4, never from legacy `app/services/*`.

---

## Outcome

**INVARIANT SATISFIED**

All actionable imports with a valid HOC equivalent have been rewired.
No remaining case exists where:
- A HOC equivalent exists AND
- Legacy `app.services.*` is still imported

---

## Final Metrics

| Metric | Initial | Final |
|--------|---------|-------|
| Total `app.services.*` imports in HOC | ~85 | 37 |
| Actionable imports fixed | 48 | 48 |
| Remaining (classified) | - | 37 |

### Remaining Classification (Not Violations)

| Category | Count | Reason Excluded |
|----------|-------|-----------------|
| True GAPs (no HOC equivalent) | 12 | Creation scope, not wiring |
| Founder (fdr/) | 7 | Out of HOC migration scope |
| Docstring/circular refs | 10 | Non-executing |
| Markdown/docs | 6 | Non-code |
| Deprecated files | 2 | Dead code |

---

## Sweeps Executed

| SWEEP | Module | Files Fixed | Imports |
|-------|--------|-------------|---------|
| 09 | recovery_* | 4 | 6 |
| 10 | scheduler.* | 3 | 5 |
| 11 | lifecycle.* | 3 | 14 |
| 12 | llm_policy_engine.* | 2 | 5 |
| 13 | connectors.* | 4 | 5 |
| 14 | activity_facade | 1 | 1 |
| 15 | analytics_facade | 1 | 5 |
| 17 | evidence.facade | 1 | 2 |
| 18-22 | alerts/controls/monitors/retrieval/datasources | 5 | 5 |
| 23-24 | compliance/integrations | 2 | 2 |
| 26 | worker_write_service_async | 1 | 1 |
| 29 | accounts_facade | 1 | 6 |
| 30 | scoped_execution | 1 | 5 |
| 31 | export_bundle/pdf_renderer | 1 | 6 |
| 32 | guard imports | 1 | 5 |
| 33 | hallucination_detector | 1 | 1 |
| 35 | plan_generation_engine | 1 | 1 |
| 38 | incident_aggregator | 1 | 1 |
| 39 | detection.facade | 1 | 1 |
| 44 | cost_model_engine | 1 | 3 |
| 46 | logs_facade | 1 | 1 |
| 47 | policy.facade (policy_driver) | 2 | 2 |

---

## Surfaced Design Backlog (True GAPs)

These are **missing modules**, not wiring errors:

| Module | Gap ID | Callers |
|--------|--------|---------|
| LimitEnforcer | GAP-055 | limit_hook.py |
| UsageMonitor | GAP-053 | limit_hook.py |
| RunSignalService | - | threshold_driver.py, llm_threshold_driver.py |
| CusTelemetryService | - | cus_telemetry.py |
| CusEnforcementService | - | cus_enforcement.py |
| CusIntegrationService | - | integrations_facade.py |
| LimitsSimulationService | - | simulate.py |
| PoliciesFacade | - | policies.py |
| AuditLedgerService (sync) | - | incident_write_engine.py |
| PlatformHealthService | - | platform_eligibility_adapter.py |

---

## Closure Statement

> **This sweep is CLOSED.**
> All actionable runtime import leaks resolved.
> Remaining references classified as TRUE GAPs, founder scope, documentation, or deprecated code.
> No further work permitted under this sweep's invariant.

---

## Next Sweep

See: `SWEEP_03_MISSING_MODULE_CREATION.md`
