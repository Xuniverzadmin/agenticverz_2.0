# Claude Context File - AOS / Agenticverz 2.0

**Last Updated:** 2025-12-01

---

## Quick Start for AI Assistants

When resuming work on this project, read these files in order:

1. **Memory PIN Index:** `docs/memory-pins/INDEX.md`
2. **Full Milestone Plan:** `docs/memory-pins/PIN-008-v1-milestone-plan-full.md` (PRIMARY)
3. **Machine-Native Architecture:** `docs/memory-pins/PIN-005-machine-native-architecture.md`

---

## Project Summary

**AOS (Agentic Operating System)** - The most predictable, reliable, deterministic SDK for building machine-native agents.

### Mission Statement
> AOS is the most predictable, reliable, deterministic SDK for building machine-native agents — with skills, budgets, safety, state management, and observability built-in.

### What "Machine-Native" Means
- Designed for agents to operate efficiently, not humans to babysit
- Queryable execution context (not log parsing)
- Capability contracts (not just tool lists)
- Structured outcomes (never throws exceptions)
- Failure as data (navigable, not opaque)
- Pre-execution simulation
- Resource contracts declared upfront

---

## Current Phase

**Strategic Pivot:** Machine-Native SDK Build

### v1 Milestone Progress (Target: ~5 months small team, ~8 months solo)

| Milestone | Status | Duration |
|-----------|--------|----------|
| M0: Foundations & Contracts | ⏳ Next | 1 week |
| M1: Runtime Interfaces | Pending | 2 weeks |
| M2: Skill Registration + Stubs | Pending | 2 weeks |
| M2.5: Planner Abstraction | Pending | 1 week |
| M3: Core Skills (http_call, llm_invoke, json_transform) | Pending | 4 weeks |
| M3.5: CLI + Demo | Pending | 2 weeks |
| M4: Internal Workflow Validation | Pending | 2 weeks |
| M5: Failure Catalog v1 | Pending | 1 week |
| M5.5: Simulation Engine v1 | Pending | 1.5 weeks |
| M6: Feature Freeze + Observability | Pending | 2 weeks |
| M7: Memory Integration | Pending | 1 week |

**Total v1:** ~19.5 weeks

### Completed Foundation (Pre-Pivot)
- ✅ Phase 1: Runtime Foundation (worker, metrics, alerts)
- ✅ Phase 2-5: Production hardening, security, budget protection
- ✅ 65 tests passing (97%)

---

## Tech Stack

- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Worker:** ThreadPoolExecutor with graceful shutdown
- **Observability:** Prometheus + Alertmanager + Grafana
- **Container:** Docker Compose with host networking
- **LLM:** Anthropic Claude (claude-sonnet-4-20250514)

---

## Key Directories

```
/root/agenticverz2.0/
├── backend/app/
│   ├── main.py              # FastAPI application
│   ├── db.py                # SQLModel models
│   ├── worker/
│   │   ├── pool.py          # Worker pool
│   │   ├── runner.py        # Run executor
│   │   └── runtime/         # [M1] Machine-native runtime interfaces
│   ├── skills/
│   │   ├── registry.py      # [M2] Skill registration
│   │   ├── stubs/           # [M2] Stub implementations
│   │   ├── http_call.py     # [M3] HTTP skill
│   │   ├── llm_invoke.py    # [M3] LLM skill
│   │   └── json_transform.py # [M3] Transform skill
│   ├── planner/
│   │   ├── interface.py     # [M2.5] PlannerInterface protocol
│   │   ├── claude_adapter.py
│   │   └── stub_planner.py  # [M2.5] Rule-based for tests
│   ├── memory/
│   │   ├── store.py         # PostgresMemoryStore
│   │   └── retriever.py     # [M7] MemoryRetriever
│   ├── schemas/
│   │   ├── structured_outcome.py  # [M0] StructuredOutcome
│   │   ├── skill_metadata.py      # [M0] SkillMetadata
│   │   ├── resource_contract.py   # [M0] ResourceContract
│   │   └── agent_profile.py       # [M0] AgentProfile
│   ├── runtime/
│   │   └── failure_catalog.py     # [M5] Failure catalog
│   ├── utils/
│   │   ├── plan_inspector.py
│   │   ├── input_sanitizer.py
│   │   ├── budget_tracker.py
│   │   └── rate_limiter.py
│   ├── specs/
│   │   ├── error_taxonomy.md      # [M0] Error codes
│   │   └── determinism_and_replay.md # [M0] Replay definition
│   └── observability/
│       └── prometheus_metrics.py  # [M6] Metrics
├── backend/cli/                   # [M3.5] CLI tools
│   └── aos.py
├── docs/
│   └── memory-pins/               # Project knowledge base (8 PINs)
├── monitoring/
└── scripts/
```

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| nova_agent_manager | 8000 | FastAPI backend |
| nova_worker | - | Run executor |
| nova_db | 5433 | PostgreSQL |
| nova_prometheus | 9090 | Metrics |
| nova_alertmanager | 9093 | Alert routing |
| nova_grafana | 3000 | Dashboards |

---

## Machine-Native Runtime Interfaces (v1 Target)

```python
# Core interfaces to implement (M1)
runtime.execute(skill, params)      # Never throws, returns StructuredOutcome
runtime.describe_skill(name)        # Returns SkillMetadata
runtime.query(key, params)          # Query budget, state, history
runtime.get_resource_contract(id)   # Returns ResourceContract
runtime.simulate(plan)              # Pre-execution cost/feasibility check (M5.5)
```

---

## Error Taxonomy (M0 Deliverable)

```
Categories:
- TRANSIENT    → retry might work
- PERMANENT    → don't retry
- RESOURCE     → budget/rate limit
- PERMISSION   → not allowed
- VALIDATION   → bad input

Key Codes:
TIMEOUT, DNS_FAILURE, HTTP_4XX, HTTP_5XX, RATE_LIMITED,
BUDGET_EXCEEDED, PERMISSION_DENIED, INVALID_INPUT, SCHEMA_VALIDATION_FAILED
```

---

## Common Commands

```bash
# Check services
docker compose ps

# View logs
docker compose logs backend --tail 100

# Check metrics
curl -s http://127.0.0.1:8000/metrics | grep nova_

# Run tests
docker exec nova_agent_manager python -m pytest /app/tests/ -v

# Rebuild after changes
DOCKER_BUILDKIT=1 docker build --network=host -t nova_agent_manager ./backend
docker compose up -d backend worker
```

---

## API Key

```
AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf
```

---

## Next Immediate Actions (M0)

1. Define `StructuredOutcome` Pydantic schema
2. Define `SkillMetadata` Pydantic schema
3. Define `ResourceContract` Pydantic schema
4. Define `AgentProfile` Pydantic schema
5. Create `error_taxonomy.md` with categories + codes
6. Create `determinism_and_replay.md` spec
7. Set up CI pipeline (`.github/workflows/ci.yml`)

---

## Key Memory PINs

| PIN | Topic | Priority |
|-----|-------|----------|
| PIN-005 | Machine-Native Architecture Definition | PRIMARY |
| PIN-006 | Execution Plan Review | Reference |
| PIN-007 | v1 Milestone Plan (Summary) | Reference |
| PIN-008 | v1 Milestone Plan (Full Detail) | PRIMARY |

---

## Vision Pillars (Must Verify Against)

| # | Pillar | v1 Coverage |
|---|--------|-------------|
| 1 | Deterministic state | M1, M6 |
| 2 | Replayable runs | M6 |
| 3 | Budget & cost contracts | M0, M1, M3 |
| 4 | Skill contracts | M0, M2, M3 |
| 5 | System policies | M1, M5 |
| 6 | Observability | M6 |
| 7 | Planner modularity | M2.5 |
| 8 | Zero silent failures | M0, M1, M5 |
| 9 | Adaptive runtime | M13 (Phase 2) |

---

## Solo Developer Path

If working solo, use minimal path (~10 weeks):

1. M0 (1 week) - Foundations
2. M1 (2 weeks) - Runtime Interfaces
3. M2 + M2.5 combined (2 weeks)
4. M3: Only http_call + llm_invoke (3 weeks)
5. M3.5: CLI + demo (1.5 weeks)

**Stop. Ship. Iterate.**

---

## Notes

- Host networking required (systemd-resolved + Tailscale)
- All services bind to 127.0.0.1
- Feature freeze at M6 (no new skills after)
- Memory integration is runtime infra, not a skill
- Demo uses mock notifier until M9
