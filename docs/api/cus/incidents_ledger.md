# CUS Domain Ledger: incidents

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 20
**Unique method+path:** 20

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/incidents | list_incidents | List incidents with unified query filters. Tenant-scoped. |
| GET | /hoc/api/cus/incidents/active | list_active_incidents | List ACTIVE incidents. Topic enforced at endpoint boundary. |
| GET | /hoc/api/cus/incidents/by-run/{run_id} | get_incidents_for_run | Get all incidents linked to a specific run. Tenant-scoped. |
| GET | /hoc/api/cus/incidents/cost-impact | analyze_cost_impact | Analyze cost impact across incidents. Tenant-scoped. |
| GET | /hoc/api/cus/incidents/historical | list_historical_incidents | List HISTORICAL incidents (resolved beyond retention). Topic |
| GET | /hoc/api/cus/incidents/historical/cost-trend | get_historical_cost_trend | Get historical cost trend. Backend-computed, deterministic. |
| GET | /hoc/api/cus/incidents/historical/distribution | get_historical_distribution | Get historical distribution. Backend-computed, deterministic |
| GET | /hoc/api/cus/incidents/historical/trend | get_historical_trend | Get historical trend. Backend-computed, deterministic. |
| GET | /hoc/api/cus/incidents/list | list_incidents_public |  |
| GET | /hoc/api/cus/incidents/metrics | get_incident_metrics | Get incident metrics. Backend-computed, deterministic. |
| GET | /hoc/api/cus/incidents/patterns | detect_patterns | Detect incident patterns. Tenant-scoped. |
| GET | /hoc/api/cus/incidents/recurring | analyze_recurrence | Analyze recurring incident patterns. Tenant-scoped. |
| GET | /hoc/api/cus/incidents/resolved | list_resolved_incidents | List RESOLVED incidents. Topic enforced at endpoint boundary |
| GET | /hoc/api/cus/incidents/{incident_id} | get_incident_detail | Get incident detail (O3). Tenant isolation enforced. |
| GET | /hoc/api/cus/incidents/{incident_id}/evidence | get_incident_evidence | Get incident evidence (O4). Preflight console only. |
| POST | /hoc/api/cus/incidents/{incident_id}/export/evidence | export_evidence | Export incident evidence bundle. |
| POST | /hoc/api/cus/incidents/{incident_id}/export/executive-debrief | export_executive_debrief | Export executive debrief as PDF. |
| POST | /hoc/api/cus/incidents/{incident_id}/export/soc2 | export_soc2 | Export SOC2-compliant bundle as PDF. |
| GET | /hoc/api/cus/incidents/{incident_id}/learnings | get_incident_learnings | Get post-mortem learnings for an incident. Tenant-scoped. |
| GET | /hoc/api/cus/incidents/{incident_id}/proof | get_incident_proof | Get incident proof (O5). Preflight console only. |
