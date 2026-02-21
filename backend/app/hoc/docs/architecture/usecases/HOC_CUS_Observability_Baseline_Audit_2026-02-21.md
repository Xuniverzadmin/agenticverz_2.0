# HOC_CUS_Observability_Baseline_Audit_2026-02-21

**Created:** 2026-02-21
**Task:** T5 — Observability Audit
**Status:** DONE

---

## 1. Objective

Baseline existing HOC telemetry/debug capability. Identify gaps against the required standard (T6) so Wave A can proceed with clear observability requirements.

---

## 2. Logging Infrastructure

### 2.1 Current Setup

| Component | File | Status |
|-----------|------|--------|
| JSON Formatter | `app/logging_config.py` | Custom `JSONFormatter` with timestamp, level, logger, message |
| Logger namespace | `"nova"` | Single namespace — no domain hierarchy |
| Output | stdout via `StreamHandler` | Docker captures → local files |
| Manual log helpers | `log_request()`, `log_provenance()` | Available but not universally used |

### 2.2 HOC Layer Coverage

| Layer | Logging Pattern | Coverage |
|-------|----------------|----------|
| L2 API | Minimal — mostly error paths | LOW |
| L4 Orchestrator | Handler errors with tenant_id, operation name | MODERATE |
| L5 Engines | Varies by domain (policies: HIGH, account: NONE) | MIXED |
| L6 Drivers | Sparse — error paths only | LOW |

### 2.3 Gaps

- **No correlation ID propagation** across L2→L4→L5→L6 chain
- **No per-domain logger hierarchy** (e.g., `nova.hoc.cus.policies`)
- **No async context inheritance** for request tracking
- **No structured request context manager**

---

## 3. Metrics / Prometheus

### 3.1 Defined Metrics (`app/metrics.py`)

| Metric | Type | Labels |
|--------|------|--------|
| `nova_runs_total` | Counter | status, planner |
| `nova_runs_failed_total` | Counter | — |
| `nova_skill_attempts_total` | Counter | skill |
| `nova_skill_duration_seconds` | Histogram | skill |
| `nova_worker_pool_size` | Gauge | — |
| `nova_llm_tokens_total` | Counter | provider, model, token_type, tenant_id, agent_id |
| `nova_llm_cost_cents_total` | Counter | provider, model, tenant_id, agent_id |
| `nova_llm_duration_seconds` | Histogram | provider, model, tenant_id |

### 3.2 Auth Metrics

| Metric | File | Type |
|--------|------|------|
| `AUTH_SUCCESS_COUNTER` | `app/auth/gateway_audit.py:259` | Counter (auth_source, plane) |
| `AUTH_FAILURE_COUNTER` | `app/auth/gateway_audit.py:265` | Counter (auth_source, error_code) |
| RBAC decision latency | `app/auth/rbac_middleware.py:114` | Histogram |
| Authorization metrics | `app/auth/authorization_metrics.py` | Counter + Histogram |

### 3.3 HOC Domain Metrics

| Domain | Metrics File | Status |
|--------|-------------|--------|
| Activity | `activity/L6_drivers/run_metrics_driver.py` | EXISTS |
| Analytics | `analytics/L5_engines/metrics_engine.py` | EXISTS (sparse) |
| Integrations | `integrations/L5_engines/cus_health_engine.py` | Health checks only |
| Policies | — | NONE |
| Incidents | — | NONE |
| Account | — | NONE |
| Controls | — | NONE |
| Logs | — | NONE |

### 3.4 Gaps

- **No per-domain operation metrics** — can't measure L4→L5→L6 latency per domain
- **No L6 driver latency histograms** — DB performance invisible
- **No error classification metrics** — only success/failure, no type breakdown

---

## 4. Tracing

### 4.1 Current Implementation

| Component | File | Status |
|-----------|------|--------|
| Trace storage | `logs/L5_engines/trace_api_engine.py` | Operational |
| Trace comparison | `logs/L5_engines/trace_mismatch_engine.py` | Operational |
| Trace L2 API | `app/hoc/api/cus/logs/traces.py` | 6+ endpoints |
| Determinism validation | Root hash + step hashes | Operational |
| `as_of` watermark | UC-MON contract | Wired to 9 endpoints |

### 4.2 NOT Implemented

- **OpenTelemetry** — no imports found anywhere
- **Distributed tracing** — no cross-service span correlation
- **Automatic instrumentation** — none
- **Critical path analysis** — none

---

## 5. Health Checks

### 5.1 Endpoints (`app/hoc/api/int/general/health.py`)

| Endpoint | Checks | Status |
|----------|--------|--------|
| `GET /health` | Calls `system.health` operation | Operational |
| `GET /health/ready` | DB, Redis, Skills registry | PARTIAL — DB/Redis always "unknown" |
| `GET /health/determinism` | Last replay hash, drift detection | Operational |
| `GET /health/adapters` | LLM adapter registry | Operational |
| `GET /health/skills` | Skill registry | Operational |

### 5.2 Gaps

- Readiness probe does NOT actually check DB or Redis connectivity
- No per-domain health checks (can't detect if incidents/policies are healthy)
- No dependency chain verification (L4→L5→L6)

---

## 6. Debug Endpoints

| Endpoint | File | Status |
|----------|------|--------|
| `/__debug/openapi_nocache` | `gateway_policy.py:56` | Public |
| `/__debug/openapi_inspect` | `gateway_policy.py:57` | Public |
| `/hoc/api/stagetest/*` | `hoc/fdr/ops/` | Stagetest evidence console |
| `/hoc/api/auth/provider/status` | `hoc/api/auth/routes.py:72` | Auth diagnostics |

**Missing:** No operation registry introspection, no L4 handler trace, no cached policy inspection.

---

## 7. Event / Audit Trail

### 7.1 Event Schema Contract

`hoc_spine/authority/event_schema_contract.py` — 9-field fail-closed validator:
`event_id`, `event_type`, `tenant_id`, `project_id`, `actor_type`, `actor_id`, `decision_owner`, `sequence_no`, `schema_version`.

### 7.2 Decision Records

`hoc_spine/drivers/decisions.py` — 9 emit functions covering routing, recovery, memory, policy, budget decisions.

### 7.3 Gaps

- **Event emission not wired to persistent storage** — events validated but dropped after emit
- **No event bus** — synchronous emit only
- **Decision records sparsely used** — <20% of operations emit decisions
- **No global event ordering** for cross-domain debugging

---

## 8. Grafana Dashboards

| Dashboard | File | Focus |
|-----------|------|-------|
| NOVA Basic | `nova_basic_dashboard.json` | Runs, skills, workers |
| AOS Traces v2 | `aos_traces_dashboard_v2.json` | Trace analysis |
| Workflow Engine | `workflow-engine.json` | Workflow metrics |
| Embedding Cost | `embedding-cost-dashboard.json` | Cost tracking |
| M7 RBAC Memory | `m7_rbac_memory_dashboard.json` | RBAC metrics |
| M9 Failure Catalog | `m9_failure_catalog_v2.json` | Failure categorization |

**Alert rules:** 10 rule files in `monitoring/rules/` covering run failures, slow skills, worker pool, policy violations, recovery, RBAC, integrations.

**Remote write:** Metrics sent to Grafana Cloud (`prometheus.yml:5-15`).

---

## 9. Domain Observability Matrix

| Domain | Logging | Metrics | Health | Events | Tracing | Overall |
|--------|---------|---------|--------|--------|---------|---------|
| Activity | MODERATE | YES | NO | NO | NO | PARTIAL |
| Incidents | HIGH | NO | NO | NO | NO | PARTIAL |
| Policies | HIGH | NO | NO | NO | NO | PARTIAL |
| Analytics | LOW | SPARSE | NO | NO | NO | LOW |
| Integrations | LOW | NO | YES | NO | NO | PARTIAL |
| Logs/Traces | MODERATE | NO | NO | NO | YES | PARTIAL |
| Account | NONE | NO | NO | NO | NO | NONE |
| Controls | LOW | NO | NO | NO | NO | LOW |

---

## 10. Critical Gaps Summary

| # | Gap | Severity | Impact |
|---|-----|----------|--------|
| 1 | No correlation ID thread L2→L4→L5→L6 | HIGH | Cannot trace request origin |
| 2 | No per-domain logger hierarchy | HIGH | Cannot filter logs by domain |
| 3 | No L6 driver latency metrics | HIGH | DB performance invisible |
| 4 | Event emission not persisted | MEDIUM | Events lost after emit |
| 5 | Readiness check doesn't verify DB/Redis | MEDIUM | False health confidence |
| 6 | No per-domain operation metrics | MEDIUM | Cannot measure domain latency |
| 7 | Account domain has zero observability | MEDIUM | Blind spot for user lifecycle |
| 8 | No OpenTelemetry integration | LOW | Industry-standard gap (acceptable pre-Wave0) |
