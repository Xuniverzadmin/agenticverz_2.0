# PIN-003: Phase 3 Completion - Production Hardening

**Serial:** PIN-003
**Created:** 2025-11-30
**Last Updated:** 2025-11-30
**Status:** Active
**Category:** Architecture / Milestone

---

## Executive Summary

Phase 3 (Production Hardening) is **complete**. The AOS platform now has:
- Full authentication and multi-tenancy support
- Rate limiting and concurrent run limits
- Budget tracking and cost controls
- Idempotency for safe retries
- Real Claude planner integration (Anthropic API)
- Comprehensive integration test suite
- CLI adapter for command-line operations

---

## 1. Completed Components

### Phase 2A-2D Summary (Prerequisites)

| Phase | Component | Status |
|-------|-----------|--------|
| 2A | Pydantic schemas for Plan/Skill I/O | ✅ Complete |
| 2A | Skill registry with decorator pattern | ✅ Complete |
| 2A | Validation wrapper for skills | ✅ Complete |
| 2B | Anthropic Claude planner | ✅ Complete |
| 2B | Memory retrieval for context | ✅ Complete |
| 2B | Step-level retries with backoff | ✅ Complete |
| 2C | `llm_invoke` skill (Claude/OpenAI) | ✅ Complete |
| 2C | Artifact storage (local + S3) | ✅ Complete |
| 2C | LLM cost/token metrics | ✅ Complete |
| 2D | Tenancy middleware | ✅ Complete |
| 2D | Idempotency checking | ✅ Complete |
| 2D | Rate limiter (Redis) | ✅ Complete |
| 2D | Concurrent runs limiter | ✅ Complete |
| 2D | Budget tracker | ✅ Complete |

### Phase 3 Deliverables

| Component | File(s) | Description |
|-----------|---------|-------------|
| Database Migration | `migrations/20251130_add_llm_costs.sql` | LLM cost tracking table, idempotency indexes |
| Environment Config | `.env.example` | Complete configuration template |
| Wired Goals Endpoint | `backend/app/main.py:517-637` | Integrated all utilities into goal submission |
| CLI Adapter | `backend/app/cli.py` | Command-line interface for agents |
| Integration Tests | `backend/tests/test_integration.py` | 20 tests covering full stack |

---

## 2. Architecture Overview

### Request Flow (Goal Submission)

```
Client Request
    │
    ▼
┌──────────────────────┐
│  TenancyMiddleware   │  ← Extract X-Tenant-Id header
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  API Key Auth        │  ← Verify X-AOS-Key header
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Idempotency Check   │  ← Return existing run if duplicate key
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Rate Limiter        │  ← 100 req/min per tenant (Redis)
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Concurrency Limiter │  ← Max 5 concurrent runs per agent
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Budget Pre-check    │  ← Verify agent has budget remaining
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Create Run          │  ← Store in PostgreSQL
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│  Execute (Async)     │  ← Background task or worker
└──────────────────────┘
```

### Utility Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `idempotency.py` | `backend/app/utils/` | Check/store idempotency keys with TTL |
| `rate_limiter.py` | `backend/app/utils/` | Redis token bucket rate limiting |
| `concurrent_runs.py` | `backend/app/utils/` | Redis semaphore for concurrency |
| `budget_tracker.py` | `backend/app/utils/` | LLM cost tracking and budget enforcement |
| `tenancy.py` | `backend/app/middleware/` | Multi-tenant header extraction |

---

## 3. Database Schema Additions

### New Table: `llm_costs`

```sql
CREATE TABLE llm_costs (
  id TEXT PRIMARY KEY,
  run_id TEXT REFERENCES runs(id),
  agent_id TEXT REFERENCES agents(id),
  tenant_id TEXT,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  input_tokens BIGINT DEFAULT 0,
  output_tokens BIGINT DEFAULT 0,
  cost_cents BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### New Columns on `runs`

```sql
ALTER TABLE runs
  ADD COLUMN idempotency_key TEXT NULL,
  ADD COLUMN tenant_id TEXT NULL;

CREATE UNIQUE INDEX idx_runs_idempotency_key
  ON runs (idempotency_key, tenant_id)
  WHERE idempotency_key IS NOT NULL;
```

### New Columns on `agents`

```sql
ALTER TABLE agents
  ADD COLUMN budget_cents BIGINT DEFAULT 0,
  ADD COLUMN spent_cents BIGINT DEFAULT 0,
  ADD COLUMN budget_alert_threshold FLOAT DEFAULT 0.8;
```

---

## 4. API Changes

### Goal Submission Endpoint

**Endpoint:** `POST /agents/{agent_id}/goals`

**New Request Fields:**
```json
{
  "goal": "Your goal text",
  "idempotency_key": "optional-unique-key"
}
```

**New Response Codes:**
- `402 Payment Required` - Budget exceeded
- `429 Too Many Requests` - Rate limit or concurrency limit exceeded

**New Headers:**
- `X-Tenant-Id` - Tenant identifier (optional, required if `ENFORCE_TENANCY=true`)

---

## 5. Skills Registry

### Registered Skills

| Skill | Version | Description |
|-------|---------|-------------|
| `http_call` | 0.2.0 | HTTP requests with retry support |
| `calendar_write` | 0.1.0 | Calendar event creation (mock) |
| `llm_invoke` | 1.0.0 | LLM inference (Claude/OpenAI) |

### Skill Manifest Endpoint

**Endpoint:** `GET /skills`

**Response:**
```json
{
  "skills": [
    {"name": "http_call", "version": "0.2.0"},
    {"name": "calendar_write", "version": "0.1.0"},
    {"name": "llm_invoke", "version": "1.0.0"}
  ],
  "manifest": [
    {"name": "http_call", "description": "...", "input_schema": {...}},
    ...
  ]
}
```

---

## 6. Planner Integration

### Anthropic Claude Planner

**Status:** ✅ Fully operational

**Configuration:**
```bash
PLANNER_BACKEND=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**Model:** `claude-sonnet-4-20250514`

**Features:**
- Intelligent plan generation with reasoning
- Tool manifest awareness
- Memory context integration
- Token usage tracking
- Automatic fallback to stub on errors

**Example Plan Output:**
```json
{
  "plan_id": "plan-9b121da578b0",
  "steps": [
    {
      "step_id": "fetch_quote",
      "skill": "http_call",
      "params": {"url": "https://zenquotes.io/api/random", "method": "GET"},
      "description": "Fetch a random inspirational quote from ZenQuotes API"
    }
  ],
  "metadata": {
    "planner": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "reasoning": "To get a random inspirational quote...",
    "input_tokens": 539,
    "output_tokens": 170,
    "latency_ms": 3860.83
  }
}
```

---

## 7. CLI Commands

### Available Commands

```bash
# Create agent
python -m app.cli create-agent --name "my-agent"

# List agents
python -m app.cli list-agents [--json]

# Run goal
python -m app.cli run --agent-id <id> --goal "your goal" [--verbose] [--json]

# Get run status
python -m app.cli get-run <run_id> [--json]
```

### Docker Usage

```bash
docker exec nova_agent_manager python -m app.cli list-agents
docker exec nova_agent_manager python -m app.cli run \
  --agent-id <id> --goal "Fetch data from API" --verbose
```

---

## 8. Integration Tests

### Test Coverage (20 tests)

| Category | Tests | Status |
|----------|-------|--------|
| Health Endpoint | 1 | ✅ Pass |
| Auth Middleware | 3 | ✅ Pass |
| Agent CRUD | 3 | ✅ Pass |
| Goal Submission | 2 | ✅ Pass |
| Idempotency | 1 | ✅ Pass |
| Rate Limiting | 1 | ✅ Pass |
| Concurrency Limiting | 2 | ✅ Pass |
| Budget Tracking | 1 | ✅ Pass |
| Skill Registry | 3 | ✅ Pass |
| Metrics Endpoint | 1 | ✅ Pass |
| CLI | 2 | ✅ Pass |

### Running Tests

```bash
docker exec nova_agent_manager python -m pytest /app/tests/test_integration.py -v
```

---

## 9. Environment Configuration

### Required Variables

```bash
# Core
DATABASE_URL=postgresql://nova:novapass@localhost:5433/nova_aos
REDIS_URL=redis://localhost:6379/0
AOS_API_KEY=your-api-key

# Planner
PLANNER_BACKEND=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Optional
ENFORCE_TENANCY=false  # Set true in production
DEFAULT_EST_COST_CENTS=50
BUDGET_ALERT_THRESHOLD=0.8
```

---

## 10. Services Status

### Running Services

| Service | Container | Status | Port |
|---------|-----------|--------|------|
| Backend | nova_agent_manager | Healthy | 8000 |
| Worker | nova_worker | Running | - |
| Database | nova_db | Healthy | 5433 |
| Prometheus | nova_prometheus | Running | 9090 |
| Alertmanager | nova_alertmanager | Running | 9093 |
| Grafana | nova_grafana | Running | 3000 |
| Redis | (system) | Running | 6379 |

---

## 11. Known Issues / Limitations

1. **Budget deduction not wired** - Budget check exists but post-run cost deduction needs integration
2. **Pydantic deprecation warnings** - Using class-based `config` instead of `ConfigDict`
3. **Dockerfile CMD warning** - Shell form instead of JSON array

---

## 12. Next Steps (Phase 4+)

### Immediate
- Wire budget deduction after run completion
- Add more skills (file I/O, postgres query)
- Production deployment guide

### Future
- Agent Packs (PAKs) packaging
- Multi-agent orchestration
- Human-in-loop workflows
- Event-driven pipelines

---

## 13. Related PINs

- [PIN-001](PIN-001-aos-roadmap-status.md) - Original roadmap (superseded sections)
- [PIN-002](PIN-002-critical-review.md) - Architecture review

---

## Changelog

| Date | Change |
|------|--------|
| 2025-11-30 | Initial creation - Phase 3 completion documentation |
