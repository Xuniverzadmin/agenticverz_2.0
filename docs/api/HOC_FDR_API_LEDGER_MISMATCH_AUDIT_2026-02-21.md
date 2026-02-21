# HOC FDR API Ledger Mismatch Audit (Wave 2)

- Generated (UTC): `2026-02-21T07:19:42.687293+00:00`
- Prefix: `/hoc/api/fdr/`
- Source ledger rows: `66` (`66` unique)
- OpenAPI rows under prefix: `0` (`0` unique)
- Source-only mismatches: `66`
- OpenAPI-only mismatches: `0`

## Skeptical Finding
OpenAPI currently exposes zero `/hoc/api/fdr/*` operations in `docs/openapi.json`, while source-derived ledger reports active FDR routes. This is namespace/spec drift and must be reconciled before using OpenAPI as canonical for this prefix.

## Source-only (first 50)
| Method | Path |
|---|---|
| GET | `/hoc/api/fdr/explorer/info` |
| GET | `/hoc/api/fdr/explorer/patterns` |
| GET | `/hoc/api/fdr/explorer/summary` |
| GET | `/hoc/api/fdr/explorer/system/health` |
| GET | `/hoc/api/fdr/explorer/tenant/{tenant_id}/diagnostics` |
| GET | `/hoc/api/fdr/explorer/tenants` |
| GET | `/hoc/api/fdr/fdr/contracts/review-queue` |
| GET | `/hoc/api/fdr/fdr/contracts/{contract_id}` |
| GET | `/hoc/api/fdr/fdr/lifecycle/{tenant_id}` |
| GET | `/hoc/api/fdr/fdr/lifecycle/{tenant_id}/history` |
| GET | `/hoc/api/fdr/fdr/onboarding/stalled` |
| GET | `/hoc/api/fdr/fdr/review/auto-execute` |
| GET | `/hoc/api/fdr/fdr/review/auto-execute/stats` |
| GET | `/hoc/api/fdr/fdr/review/auto-execute/{invocation_id}` |
| GET | `/hoc/api/fdr/fdr/timeline/count` |
| GET | `/hoc/api/fdr/fdr/timeline/decisions` |
| GET | `/hoc/api/fdr/fdr/timeline/decisions/{decision_id}` |
| GET | `/hoc/api/fdr/fdr/timeline/run/{run_id}` |
| GET | `/hoc/api/fdr/hoc/api/stagetest/apis` |
| GET | `/hoc/api/fdr/hoc/api/stagetest/apis/ledger` |
| GET | `/hoc/api/fdr/hoc/api/stagetest/runs` |
| GET | `/hoc/api/fdr/hoc/api/stagetest/runs/{run_id}` |
| GET | `/hoc/api/fdr/hoc/api/stagetest/runs/{run_id}/cases` |
| GET | `/hoc/api/fdr/hoc/api/stagetest/runs/{run_id}/cases/{case_id}` |
| GET | `/hoc/api/fdr/ops/actions/audit` |
| GET | `/hoc/api/fdr/ops/actions/audit/{action_id}` |
| GET | `/hoc/api/fdr/ops/cost/anomalies` |
| GET | `/hoc/api/fdr/ops/cost/customers/{tenant_id}` |
| GET | `/hoc/api/fdr/ops/cost/overview` |
| GET | `/hoc/api/fdr/ops/cost/tenants` |
| GET | `/hoc/api/fdr/ops/customers` |
| GET | `/hoc/api/fdr/ops/customers/at-risk` |
| GET | `/hoc/api/fdr/ops/customers/{tenant_id}` |
| GET | `/hoc/api/fdr/ops/events` |
| GET | `/hoc/api/fdr/ops/incidents` |
| GET | `/hoc/api/fdr/ops/incidents/infra-summary` |
| GET | `/hoc/api/fdr/ops/incidents/patterns` |
| GET | `/hoc/api/fdr/ops/incidents/{incident_id}` |
| GET | `/hoc/api/fdr/ops/infra` |
| GET | `/hoc/api/fdr/ops/playbooks` |
| GET | `/hoc/api/fdr/ops/playbooks/{playbook_id}` |
| GET | `/hoc/api/fdr/ops/pulse` |
| GET | `/hoc/api/fdr/ops/revenue` |
| GET | `/hoc/api/fdr/ops/stickiness` |
| GET | `/hoc/api/fdr/retrieval/evidence` |
| GET | `/hoc/api/fdr/retrieval/evidence/{evidence_id}` |
| GET | `/hoc/api/fdr/retrieval/planes` |
| GET | `/hoc/api/fdr/retrieval/planes/{plane_id}` |
| POST | `/hoc/api/fdr/fdr/contracts/{contract_id}/review` |
| POST | `/hoc/api/fdr/fdr/lifecycle/archive` |

## OpenAPI-only (first 50)
| Method | Path |
|---|---|
