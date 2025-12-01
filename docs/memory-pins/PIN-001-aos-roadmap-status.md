# PIN-001: AOS Platform Status & Roadmap

**Serial:** PIN-001
**Created:** 2025-11-30
**Last Updated:** 2025-11-30
**Status:** Active
**Category:** Architecture / Roadmap

---

## Executive Summary

AOS (Agentic Operating System) infrastructure phase is 80-90% complete. The system is now **infra-complete but feature-light**. Ready to begin core agent framework development.

---

## 1. Current State

### Completed Infrastructure

| Component | Status | Details |
|-----------|--------|---------|
| Worker Service | ✅ Done | Separate container, graceful shutdown, signal handling |
| Prometheus Metrics | ✅ Done | 9 alert rules, queue depth, skill duration, run totals |
| Alertmanager | ✅ Done | Slack + Email routing, secrets injection ready |
| Grafana Dashboard | ✅ Done | Queue depth, skill metrics, run status panels |
| Rerun Tooling | ✅ Done | `/admin/rerun`, `/admin/failed-runs`, CLI scripts |
| Silences + Runbooks | ✅ Done | 48h silences active, 3 runbooks created |
| Secrets Pipeline | ✅ Done | `entrypoint.sh` + `config.yml.tmpl` for secure injection |

### Services Running

```
nova_db              - PostgreSQL 15 (healthy)
nova_agent_manager   - FastAPI backend (healthy)
nova_worker          - Worker pool process
nova_prometheus      - Metrics collection
nova_alertmanager    - Alert routing
nova_grafana         - Dashboards
```

### Key Metrics Exposed

- `nova_runs_total{status, planner}` - Run counts by status and planner
- `nova_runs_queued` - Current queue depth
- `nova_runs_failed_total` - Permanent failures
- `nova_skill_attempts_total{skill}` - Skill execution counts
- `nova_skill_duration_seconds{skill}` - Skill latency histogram
- `nova_worker_pool_size` - Worker concurrency

---

## 2. Platform Vision

### End Goal

Build AOS (Agentic Operating System) to power:
- Agenticverz platform
- Mobiverz automation
- Internal operations
- External developer agents
- Customer workflows
- Multi-agent swarm actions

### Core Capabilities (Target)

- Multi-agent planner + executor
- Unified skill library
- Execution monitoring + error recovery
- Human-in-loop pathways
- Plugin architecture for automation, data, APIs
- Event-driven pipeline
- Developer ecosystem + packaging (PAKs)

---

## 3. Phase Roadmap

### PHASE 1 — Runtime Foundation (80-90% Done)

**Completed:**
- Worker service
- Metrics & alerts
- Re-run tooling
- Queue monitoring
- Secrets injection
- Planner labels

**Remaining (defer unless needed):**
- Worker pool auto-scaling
- Dead-letter queue for hard failures
- Full backpressure model
- Persistent event logs (Kafka-lite or Postgres queue)

---

### PHASE 2 — Core Agent Framework (NEXT)

**Priority: HIGH - Start immediately**

Build internal architecture:
1. Planner → Task → Skill Execution Flow
2. Skill interfaces (schema, IO, metadata)
3. Agent definitions + capabilities
4. State/Context management per run
5. Error policies (retry, fallback, escalate)
6. Skill creation templates

**Target Structure:**
```
/app/skills/base.py
/app/skills/http.py
/app/skills/json.py
/app/agents/base.py
/app/planner/logic.py
```

---

### PHASE 3 — System Skills (Base Set)

**Tier 1 Skills (Required):**
- HTTP client skill
- Browser automation skill
- File/Blob read-write skill
- Shell/command skill (sandboxed)
- LLM invocation skill
- JSON transform skill
- Logging/report skill

**Tier 2 Skills (Platform-level):**
- Postgres query skill
- Caching skill (Redis optional)
- Scheduler/cron skill
- Notifier skill (Slack, email, SMS)

---

### PHASE 4 — Higher-level Agents

1. **Data Agent** - Fetch, clean, normalize, write to DB
2. **Research Agent** - Web fetch, reasoning, summaries
3. **Task Automation Agent** - Goal → plan → execute → report
4. **Monitoring Agent** - Internal health checks, alerting

---

### PHASE 5 — Developer Experience

- Agent Packs (PAKs)
- CLI for agent creation
- Template agent files
- Packaging + versioning
- Per-agent logging dashboards

---

### PHASE 6 — Production Infrastructure

- Separate production VPS
- Domain releases
- SSL termination
- Production alert channels
- Secrets hardening
- Backups & DR plan

---

## 4. Immediate Next Steps

### STEP 1: Core Agent/Skill Architecture
- Finalize JSON schemas for skill I/O
- Define error types and run logs
- Establish planner → worker contract
- Create skeleton files

### STEP 2: Build First 5 Baseline Skills
1. `http_request()`
2. `llm_invoke()`
3. `system_read_file()`
4. `system_write_file()`
5. `postgres_query()`

### STEP 3: Build Core Planner
- Goal → plan steps translation
- Skill invocation
- Partial failure handling
- Intelligent retry
- Progress reporting
- JSON report artifact

### STEP 4: First End-to-End Goal Test
```
Goal: Fetch HTML of google.com, extract headings, summarize them.
Flow: planner → http skill → extract → llm summarize → output → DB → Grafana
```

---

## 5. Anti-Patterns (What NOT to Do Now)

- ❌ Wire Slack prod channels before planners exist
- ❌ Optimize scaling prematurely
- ❌ Build Mobiverz-specific agents yet
- ❌ Integrate 3rd party APIs before core framework
- ❌ Spend time on deployment pipelines
- ❌ Mix staging/prod secrets

---

## 6. Key Files Reference

### Configuration
- `docker-compose.yml` - Service orchestration
- `monitoring/prometheus.yml` - Metrics scraping
- `monitoring/alertmanager/config.yml` - Alert routing
- `monitoring/rules/nova_alerts.yml` - Alert definitions

### Backend
- `backend/app/main.py` - FastAPI application
- `backend/app/worker/pool.py` - Worker pool
- `backend/app/worker/runner.py` - Run executor
- `backend/app/metrics.py` - Prometheus metrics
- `backend/app/skills/` - Skill implementations
- `backend/app/planners/` - Planner implementations

### Operations
- `scripts/rerun.sh` - Rerun failed runs
- `scripts/list-failed.sh` - List failed runs
- `scripts/test-alerts.sh` - Test alert routing
- `docs/runbooks/` - Incident runbooks

---

## 7. Related PINs

- PIN-002: Skill Interface Specification (pending)
- PIN-003: Planner Architecture (pending)
- PIN-004: Agent Definition Schema (pending)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-11-30 | Initial creation - captured Phase 1 completion and roadmap |
