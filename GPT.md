# GPT Context File - AOS / Agenticverz 2.0

**Last Updated:** 2025-12-01

---

## Instructions for GPT/ChatGPT

When working on this project, read these files in order for full context:

1. **Memory PIN Index:** `docs/memory-pins/INDEX.md`
2. **Full Milestone Plan:** `docs/memory-pins/PIN-008-v1-milestone-plan-full.md` (PRIMARY)
3. **Machine-Native Architecture:** `docs/memory-pins/PIN-005-machine-native-architecture.md`

---

## Project Overview

**AOS (Agentic Operating System)** is a deterministic SDK for building machine-native agents.

### Mission
> Build the most predictable, reliable, deterministic SDK for machine-native agents — with skills, budgets, safety, state management, and observability built-in.

### What "Machine-Native" Means
- Agents operate autonomously without human babysitting
- Queryable execution context (not log parsing)
- Capability contracts (not just tool lists)
- Structured outcomes (never throws exceptions)
- Failure as navigable data (not opaque errors)
- Pre-execution simulation for cost/feasibility
- Resource contracts declared upfront

---

## Current Status

**Phase:** Strategic Pivot → Machine-Native SDK Build

### v1 Milestones

| # | Milestone | Duration | Status |
|---|-----------|----------|--------|
| M0 | Foundations & Contracts | 1 week | ⏳ Next |
| M1 | Runtime Interfaces | 2 weeks | Pending |
| M2 | Skill Registration + Stubs | 2 weeks | Pending |
| M2.5 | Planner Abstraction | 1 week | Pending |
| M3 | Core Skills Implementation | 4 weeks | Pending |
| M3.5 | CLI + 60s Demo | 2 weeks | Pending |
| M4 | Internal Workflow Validation | 2 weeks | Pending |
| M5 | Failure Catalog v1 | 1 week | Pending |
| M5.5 | Simulation Engine v1 | 1.5 weeks | Pending |
| M6 | Feature Freeze + Observability | 2 weeks | Pending |
| M7 | Memory Integration | 1 week | Pending |

**Total v1:** ~19.5 weeks (~5 months with small team)

### What's Already Built (Pre-Pivot)
- Runtime foundation (worker pool, metrics, alerts)
- Production hardening (security, budget protection)
- 65 tests passing (97% coverage)
- Planner with Anthropic Claude
- Basic skills (http_call, llm_invoke, json_transform)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + SQLModel |
| Database | PostgreSQL (port 5433) |
| Worker | ThreadPoolExecutor |
| Monitoring | Prometheus + Alertmanager + Grafana |
| Container | Docker Compose (host networking) |
| LLM | Anthropic Claude (claude-sonnet-4-20250514) |

---

## Repository Structure

```
/root/agenticverz2.0/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── db.py             # SQLModel models
│   │   ├── worker/           # Worker pool & runtime
│   │   │   └── runtime/      # [M1] Machine-native interfaces
│   │   ├── skills/           # Skill implementations
│   │   │   └── stubs/        # [M2] Test stubs
│   │   ├── planner/          # [M2.5] Planner interface
│   │   ├── memory/           # [M7] Memory retrieval
│   │   ├── schemas/          # [M0] Core schemas
│   │   ├── runtime/          # [M5] Failure catalog
│   │   ├── specs/            # [M0] Specifications
│   │   └── observability/    # [M6] Prometheus metrics
│   ├── cli/                  # [M3.5] CLI tools
│   └── tests/                # Test suite
├── docs/
│   └── memory-pins/          # Project knowledge base
├── monitoring/               # Prometheus/Grafana configs
└── scripts/                  # Utility scripts
```

---

## M0 Deliverables (Current Focus)

### Schemas to Create

1. **StructuredOutcome** (`backend/app/schemas/structured_outcome.py`)
   - Fields: success, result, error (with code, category, message, retryable, suggestions)
   - Never throws - all skill calls return this

2. **SkillMetadata** (`backend/app/schemas/skill_metadata.py`)
   - Fields: name, version, cost_estimate_cents, avg_latency_ms, side_effects, permissions_required

3. **ResourceContract** (`backend/app/schemas/resource_contract.py`)
   - Fields: resource_type, permissions, rate_limits, budget_limits

4. **AgentProfile** (`backend/app/schemas/agent_profile.py`)
   - Fields: id, allowed_skills, planner_type, budget_cents, memory_backend

### Specs to Create

5. **Error Taxonomy** (`backend/app/specs/error_taxonomy.md`)
   ```
   Categories:
   - TRANSIENT    → retry might work (TIMEOUT, DNS_FAILURE, HTTP_5XX)
   - PERMANENT    → don't retry (HTTP_4XX, INVALID_INPUT)
   - RESOURCE     → budget/rate limit (RATE_LIMITED, BUDGET_EXCEEDED)
   - PERMISSION   → not allowed (PERMISSION_DENIED)
   - VALIDATION   → bad input (SCHEMA_VALIDATION_FAILED)
   ```

6. **Determinism & Replay** (`backend/app/specs/determinism_and_replay.md`)
   - Define what "replay" means
   - What's deterministic (runtime behavior) vs what's not (external APIs)

### CI Setup

7. **GitHub Actions** (`.github/workflows/ci.yml`)
   - Unit tests job
   - Integration tests job
   - Coverage threshold

---

## Key Interfaces (M1 Target)

```python
# Runtime interfaces - never throw, always return StructuredOutcome
runtime.execute(skill, params)        # Execute skill
runtime.describe_skill(name)          # Get SkillMetadata
runtime.query(key, params)            # Query state/budget/history
runtime.get_resource_contract(id)     # Get ResourceContract
runtime.simulate(plan)                # Pre-execution simulation (M5.5)
```

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| nova_agent_manager | 8000 | FastAPI backend |
| nova_worker | - | Run executor |
| nova_db | 5433 | PostgreSQL |
| nova_prometheus | 9090 | Metrics |
| nova_alertmanager | 9093 | Alerts |
| nova_grafana | 3000 | Dashboards |

---

## API Key

```
AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf
```

---

## Common Commands

```bash
# Service management
docker compose ps
docker compose logs backend --tail 100

# Metrics
curl -s http://127.0.0.1:8000/metrics | grep nova_

# Testing
docker exec nova_agent_manager python -m pytest /app/tests/ -v

# Rebuild
DOCKER_BUILDKIT=1 docker build --network=host -t nova_agent_manager ./backend
docker compose up -d backend worker
```

---

## Vision Pillars Checklist

When implementing, verify against these pillars:

| # | Pillar | Milestone | Check |
|---|--------|-----------|-------|
| 1 | Deterministic state | M1, M6 | Same inputs → same runtime behavior |
| 2 | Replayable runs | M6 | Can re-execute stored plans |
| 3 | Budget & cost contracts | M0, M1, M3 | All skills declare costs |
| 4 | Skill contracts | M0, M2, M3 | All skills have metadata |
| 5 | System policies | M1, M5 | Failure catalog drives retries |
| 6 | Observability | M6 | Prometheus metrics for everything |
| 7 | Planner modularity | M2.5 | Pluggable planner interface |
| 8 | Zero silent failures | M0, M1, M5 | StructuredOutcome always returned |
| 9 | Adaptive runtime | M13 | Deferred to Phase 2 |

---

## Solo Developer Path

If working alone, use this minimal 10-week path:

1. **M0** (1 week) - Schemas + specs
2. **M1** (2 weeks) - Runtime interfaces
3. **M2+M2.5** (2 weeks) - Skills + planner stubs
4. **M3** (3 weeks) - Only http_call + llm_invoke
5. **M3.5** (1.5 weeks) - CLI + demo

**Ship it. Then iterate.**

---

## Memory PINs Reference

| PIN | Title | Use For |
|-----|-------|---------|
| PIN-005 | Machine-Native Architecture | Understanding the "why" |
| PIN-006 | Execution Plan Review | Historical context |
| PIN-007 | v1 Milestone Plan (Summary) | Quick reference |
| PIN-008 | v1 Milestone Plan (Full) | Detailed implementation guide |

---

## Important Notes

- **Host networking required** - systemd-resolved + Tailscale
- **All services bind to 127.0.0.1**
- **Feature freeze at M6** - no new skills after
- **Memory is runtime infra**, not a skill (can add after freeze)
- **Demo uses mock notifier** - real notifications in M9

---

## GPT-Specific Guidelines

When generating code for this project:

1. **Always use Pydantic v2** for schemas
2. **Never use `raise` in skills** - return StructuredOutcome instead
3. **Include type hints** on all functions
4. **Follow existing patterns** in the codebase
5. **Test coverage required** for new code
6. **Error codes must match taxonomy** in error_taxonomy.md

When generating tests:

1. Use pytest with fixtures from `conftest.py`
2. Mock external calls (HTTP, LLM)
3. Test both success and failure paths
4. Verify StructuredOutcome fields
