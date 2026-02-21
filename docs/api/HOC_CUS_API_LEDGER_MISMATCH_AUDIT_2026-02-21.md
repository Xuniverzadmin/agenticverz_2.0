# HOC CUS API Ledger Mismatch Audit

- Generated UTC: `2026-02-21T07:00:46.478107+00:00`
- Ledger source: `/tmp/hoc-clean-ledger-1771656914/backend/.openapi_snapshot.json`
- Ledger raw rows: `502`
- Ledger unique method+path: `499`

## Contract Drift Summary
- Local docs OpenAPI (`docs/openapi.json`) `/hoc/api/cus/*` count: `0`
- Backend snapshot OpenAPI (`backend/.openapi_snapshot.json`) `/hoc/api/cus/*` count: `0`
- Missing in local docs OpenAPI: `499`
- Missing in backend snapshot OpenAPI: `499`

## Skeptical Findings
- `stagetest /openapi.json` parseable JSON: `False`
- Stagetest fetch currently returns HTML shell (likely frontend fallback/proxy), so runtime OpenAPI cannot be used as contract source in this wave.
- Current openapi files do not expose `/hoc/api/cus/*` prefixed paths; source fallback inventory is required for Wave 1 artifacting.
- Backend snapshot appears to use different route namespace prefixes (e.g., `/api/*`, `/ops/*`, `/customer/*`).

## Snapshot Prefix Counts (backend/.openapi_snapshot.json)
- `/customer/`: `4`
- `/api/`: `228`
- `/ops/`: `27`
- `/internal/`: `5`
- `/founder/`: `12`

## Missing in Local OpenAPI (sample first 40)
- `DELETE /hoc/api/cus/accounts/users/{user_id}`
- `DELETE /hoc/api/cus/alerts/routes/{route_id}`
- `DELETE /hoc/api/cus/alerts/rules/{rule_id}`
- `DELETE /hoc/api/cus/connectors/{connector_id}`
- `DELETE /hoc/api/cus/datasources/{source_id}`
- `DELETE /hoc/api/cus/embedding/cache`
- `DELETE /hoc/api/cus/integrations/mcp-servers/{server_id}`
- `DELETE /hoc/api/cus/integrations/{integration_id}`
- `DELETE /hoc/api/cus/limits/overrides/{override_id}`
- `DELETE /hoc/api/cus/memory/pins/{key}`
- `DELETE /hoc/api/cus/monitors/{monitor_id}`
- `DELETE /hoc/api/cus/policies/limits/{limit_id}`
- `DELETE /hoc/api/cus/policy-layer/cooldowns/{agent_id}`
- `DELETE /hoc/api/cus/scenarios/{scenario_id}`
- `DELETE /hoc/api/cus/scheduler/jobs/{job_id}`
- `DELETE /hoc/api/cus/tenant/api-keys/{key_id}`
- `DELETE /hoc/api/cus/traces/{run_id}`
- `DELETE /hoc/api/cus/v1/killswitch/key`
- `DELETE /hoc/api/cus/v1/killswitch/tenant`
- `DELETE /hoc/api/cus/workers/business-builder/runs/{run_id}`
- `GET /hoc/api/cus/account/users/list`
- `GET /hoc/api/cus/accounts/billing`
- `GET /hoc/api/cus/accounts/billing/invoices`
- `GET /hoc/api/cus/accounts/invitations`
- `GET /hoc/api/cus/accounts/profile`
- `GET /hoc/api/cus/accounts/projects`
- `GET /hoc/api/cus/accounts/projects/{project_id}`
- `GET /hoc/api/cus/accounts/support`
- `GET /hoc/api/cus/accounts/support/tickets`
- `GET /hoc/api/cus/accounts/tenant/users`
- `GET /hoc/api/cus/accounts/users`
- `GET /hoc/api/cus/accounts/users/{user_id}`
- `GET /hoc/api/cus/activity/attention-queue`
- `GET /hoc/api/cus/activity/completed`
- `GET /hoc/api/cus/activity/cost-analysis`
- `GET /hoc/api/cus/activity/live`
- `GET /hoc/api/cus/activity/metrics`
- `GET /hoc/api/cus/activity/patterns`
- `GET /hoc/api/cus/activity/risk-signals`
- `GET /hoc/api/cus/activity/runs`
