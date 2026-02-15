# UC HOLD Triage Backlog (2026-02-15)

**Status:** TRIAGED
**Source:** Iteration-3 Decision Table (`HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv`)
**Scope:** 15 HOLD rows classified with deterministic next actions. No row silently dropped.

---

## Classification Key

| Status | Meaning |
|--------|---------|
| `EVIDENCE_PENDING` | Needs stronger handler operation or test evidence to assign a canonical UC |
| `NON_UC_SUPPORT` | Infrastructure/helper script that supports multiple UCs without owning any |
| `REFACTOR_REQUIRED` | Too broad to map safely; needs structural decomposition before UC assignment |

---

## Triage Table

| # | Script | Domain | Layer | Status | Rationale | Next Action | Owner |
|---|--------|--------|-------|--------|-----------|-------------|-------|
| 1 | `activity/L5_engines/activity_facade.py` | activity | L5_ENGINE | **NON_UC_SUPPORT** | Broad facade delegating to 6+ operations (query, signal_feedback, telemetry, discovery, orphan_recovery, signal_fingerprint). Acts as L5 routing layer for the entire activity domain. | None — correctly classified as multi-UC support facade. | activity-domain |
| 2 | `activity/L5_engines/cus_telemetry_engine.py` | activity | L5_ENGINE | **EVIDENCE_PENDING** | Only legacy UC-MON evidence (UC-024, UC-027). No canonical UC-001 anchor despite handling telemetry ingestion which is core to run monitoring. | Wire `cus_telemetry_engine.py` into UC-001 via handler operation trace: `activity.telemetry` -> L5 `cus_telemetry_engine` -> L6 `cus_telemetry_driver`. Add test asserting the L4->L5->L6 chain for telemetry ingest. | activity-domain |
| 3 | `activity/L6_drivers/activity_read_driver.py` | activity | L6_DRIVER | **NON_UC_SUPPORT** | Broad read driver serving `activity.query` which spans UC-001 (runs, signals, metrics, patterns, cost-analysis). Pure data access with no UC-specific logic. | None — correctly classified as multi-UC L6 support. | activity-domain |
| 4 | `activity/L6_drivers/cus_telemetry_driver.py` | activity | L6_DRIVER | **EVIDENCE_PENDING** | Only legacy UC-MON evidence. Persistence layer for telemetry data (linked to `cus_telemetry_engine.py` above). | Wire into UC-001 alongside `cus_telemetry_engine.py`. Same handler chain evidence needed. | activity-domain |
| 5 | `activity/adapters/customer_activity_adapter.py` | activity | ADAPTER | **NON_UC_SUPPORT** | Adapter-level facade for cross-domain consumption. Not a UC owner. | None — adapter correctly classified. | activity-domain |
| 6 | `analytics/L5_engines/feedback_read_engine.py` | analytics | L5_ENGINE | **EVIDENCE_PENDING** | Route-map has `analytics.feedback` and `analytics.prediction_read` but no explicit canonical UC anchor for these operations. Likely UC-025 (Prediction Cycle) or UC-027 (Snapshot + Baseline). | Extract handler operation mapping for `analytics.feedback` -> L5 `feedback_read_engine`. Verify which L4 operation dispatches to this engine. Assign UC based on dominant operation. | analytics-domain |
| 7 | `analytics/L6_drivers/feedback_read_driver.py` | analytics | L6_DRIVER | **EVIDENCE_PENDING** | Route-map evidence for `analytics.feedback`/`analytics.prediction_read` exists but no canonical UC anchor. Persistence pair for `feedback_read_engine.py`. | Wire alongside `feedback_read_engine.py` (row 6) once handler chain is established. | analytics-domain |
| 8 | `hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py` | hoc_spine | L4_COORDINATOR | **EVIDENCE_PENDING** | Coordinator evidence is legacy UC-MON only (UC-001, UC-027, UC-MON-04). No canonical UC anchor. Coordinators are cross-domain L4 components. | Verify if this coordinator is still called by any handler. If dead code, reclassify as NON_UC_SUPPORT. If active, map to dominant handler's UC. | hoc-spine |
| 9 | `incidents/L5_engines/anomaly_bridge.py` | incidents | L5_ENGINE | **EVIDENCE_PENDING** | Legacy UC-MON evidence (UC-030, UC-031, UC-MON-07). Bridges anomaly detection to incident creation. Likely UC-030 (Policy Violation Truth Pipeline). | Trace handler chain: which L4 operation dispatches to `anomaly_bridge`? If `incidents.write` or a dedicated anomaly operation, assign to UC-030. | incidents-domain |
| 10 | `incidents/L5_engines/incident_engine.py` | incidents | L5_ENGINE | **EVIDENCE_PENDING** | Broad incident engine (UC-030, UC-031, UC-MON-07). Creates incidents for runs. Core to UC-007 (Incident Lifecycle) but overlaps UC-030 (Policy Violation). | Verify: does `incident_engine.create_incident_for_run()` serve `incidents.write` only, or also policy-violation paths? Assign based on primary caller. | incidents-domain |
| 11 | `incidents/L5_engines/incidents_facade.py` | incidents | L5_ENGINE | **NON_UC_SUPPORT** | Broad facade delegating to incidents.query, incidents.write, incidents.cost_guard, incidents.export, incidents.recovery_rules, incidents.recurrence. Acts as L5 routing for entire incidents domain. | None — correctly classified as multi-UC support facade. | incidents-domain |
| 12 | `incidents/L6_drivers/cost_guard_driver.py` | incidents | L6_DRIVER | **EVIDENCE_PENDING** | Legacy UC-MON evidence only. Persistence for cost guard queries (spend_totals, budget, baseline). Likely UC-007 (serves `incidents.cost_guard`). | Verify L4 operation chain: `incidents.cost_guard` -> L5 -> `cost_guard_driver`. If confirmed, assign to UC-007. | incidents-domain |
| 13 | `incidents/L6_drivers/incident_aggregator.py` | incidents | L6_DRIVER | **EVIDENCE_PENDING** | Legacy UC-MON evidence only. Aggregates call data into incidents. Likely UC-007 (core incident creation). | Verify caller chain and assign to UC-007 if `incident_aggregator` is called from `incident_engine` -> `incidents.write`. | incidents-domain |
| 14 | `incidents/L6_drivers/incidents_facade_driver.py` | incidents | L6_DRIVER | **NON_UC_SUPPORT** | Broad L6 facade for incident reads. Serves `incidents.query` which spans UC-007 reads. Pure data access delegation. | None — correctly classified as multi-UC L6 support. | incidents-domain |
| 15 | `incidents/adapters/customer_incidents_adapter.py` | incidents | ADAPTER | **NON_UC_SUPPORT** | Adapter-level facade for cross-domain consumption. Not a UC owner. | None — adapter correctly classified. | incidents-domain |

---

## Summary by Status

| Status | Count | Scripts |
|--------|-------|---------|
| **EVIDENCE_PENDING** | 9 | rows 2, 4, 6, 7, 8, 9, 10, 12, 13 |
| **NON_UC_SUPPORT** | 6 | rows 1, 3, 5, 11, 14, 15 |
| **REFACTOR_REQUIRED** | 0 | (none needed) |

## Summary by Domain

| Domain | EVIDENCE_PENDING | NON_UC_SUPPORT |
|--------|-----------------|----------------|
| activity | 2 | 3 |
| analytics | 2 | 0 |
| hoc_spine | 1 | 0 |
| incidents | 4 | 3 |

---

## Next Actions (Priority Order)

1. **Activity telemetry chain** (rows 2, 4): Wire `cus_telemetry_engine.py` + `cus_telemetry_driver.py` into UC-001 via `activity.telemetry` handler operation trace.
2. **Analytics feedback chain** (rows 6, 7): Extract handler operation for `analytics.feedback` -> assign UC-025 or UC-027.
3. **Incidents anomaly/engine** (rows 9, 10): Trace `anomaly_bridge` and `incident_engine` caller chains to assign UC-030 or UC-007.
4. **Incidents cost/aggregator** (rows 12, 13): Trace `cost_guard_driver` and `incident_aggregator` to UC-007.
5. **HOC spine coordinator** (row 8): Verify if `signal_feedback_coordinator.py` is still active or dead code.

---

## Architecture Notes

- No HOLD row is force-fitted into a UC.
- All NON_UC_SUPPORT classifications follow the established pattern from Waves 1-4 (309 scripts previously classified as NON_UC_SUPPORT).
- EVIDENCE_PENDING rows have concrete next-step actions (handler operation trace extraction).
- No new UC IDs required — all pending assignments map within UC-001..UC-040.
