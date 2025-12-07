# Claude Context File - AOS / Agenticverz 2.0

**Last Updated:** 2025-12-05

---

## Session Start Protocol (MANDATORY)

Before ANY work, run the hygiene check:

```bash
./scripts/ops/session_start.sh
```

This verifies:
- Working environment exists
- No stale checklists
- Services are healthy
- No blocking issues

Then read in order:
1. `agentiverz_mn/repo_snapshot.md` - Current state
2. `agentiverz_mn/milestone_plan.md` - What we're building
3. Pick the relevant checklist for your task

---

## Quick Start for AI Assistants

| Resource | Location | Purpose |
|----------|----------|---------|
| Memory PIN Index | `docs/memory-pins/INDEX.md` | Project status dashboard |
| M8 Working Environment | `agentiverz_mn/` | Focused context files |
| Current Roadmap | `docs/memory-pins/PIN-033-m8-m14-machine-native-realignment.md` | M8-M14 plan |

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

**M7 Complete → M8 Next**

### Milestone Status

| Milestone | Status |
|-----------|--------|
| M0-M7 | ✅ COMPLETE |
| M8: Demo + SDK + Auth | ⏳ NEXT |
| M9: Failure Persistence | Pending |
| M10: Recovery Engine | Pending |
| M11: Skill Expansion | Pending |
| M12: Beta Rollout | Pending |
| M13: Console UI | Pending |
| M14+: Self-Improving | Future |

### M8 Priorities (in order)

1. **Auth Integration** - Wire real auth provider (BLOCKING)
2. **SDK Packaging** - PyPI + npm publish
3. **Demo Productionization** - Screencasts, examples

See `agentiverz_mn/` for detailed checklists.

---

## Tech Stack

- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Worker:** ThreadPoolExecutor with graceful shutdown
- **Observability:** Prometheus + Alertmanager + Grafana
- **Container:** Docker Compose with host networking
- **LLM:** Anthropic Claude (claude-sonnet-4-20250514)
- **Connection Pool:** PgBouncer (port 6432)

---

## Key Directories

```
/root/agenticverz2.0/
├── agentiverz_mn/           # M8+ working environment (START HERE)
│   ├── repo_snapshot.md     # Current state
│   ├── milestone_plan.md    # M8-M14 roadmap
│   ├── auth_blocker_notes.md
│   ├── demo_checklist.md
│   ├── sdk_packaging_checklist.md
│   └── auth_integration_checklist.md
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── api/             # API routers
│   │   ├── auth/            # RBAC (uses stub - needs real auth)
│   │   ├── skills/          # 5 production skills
│   │   ├── worker/runtime/  # Machine-native runtime
│   │   ├── workflow/        # Workflow engine
│   │   └── costsim/         # Cost simulation V2
│   └── cli/aos.py           # CLI tool
├── sdk/
│   ├── python/              # Python SDK (10/10 tests, needs packaging)
│   └── js/                  # JS SDK (needs types, machine-native methods)
├── docs/
│   ├── memory-pins/         # 33 PINs
│   └── API_WORKFLOW_GUIDE.md
├── scripts/
│   └── ops/
│       ├── session_start.sh  # Run before each session
│       └── hygiene_check.sh  # Weekly automated check
└── monitoring/
```

---

## Services

| Service | Port | Status |
|---------|------|--------|
| nova_agent_manager | 8000 | Backend API |
| nova_worker | - | Run executor |
| nova_db | 5433 | PostgreSQL |
| nova_pgbouncer | 6432 | Connection pool |
| nova_prometheus | 9090 | Metrics |
| nova_alertmanager | 9093 | Alert routing |
| nova_grafana | 3000 | Dashboards |

---

## Machine-Native APIs (Implemented)

```python
# All implemented and working
POST /api/v1/runtime/simulate      # Plan feasibility check
POST /api/v1/runtime/query         # State queries
GET  /api/v1/runtime/capabilities  # Skills, budget, rate limits
GET  /api/v1/runtime/skills/{id}   # Skill details
POST /api/v1/runs                  # Create run
GET  /api/v1/runs/{id}             # Run status
```

---

## Common Commands

```bash
# Session start (ALWAYS RUN FIRST)
./scripts/ops/session_start.sh

# Weekly hygiene check
./scripts/ops/hygiene_check.sh

# Check services
docker compose ps

# View logs
docker compose logs backend --tail 100

# Check health
curl http://localhost:8000/health

# Check capabilities
curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities

# Run tests
cd backend && PYTHONPATH=. python -m pytest tests/ -v

# Rebuild after changes
docker compose up -d --build backend worker
```

---

## Environment Variables

```bash
# Key variables (in .env)
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
REDIS_URL=redis://localhost:6379/0
AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf
AUTH_SERVICE_URL=http://localhost:8001  # STUB - needs real auth for M8
RBAC_ENABLED=true
RBAC_ENFORCE=true
```

---

## Key Memory PINs

| PIN | Topic | Status |
|-----|-------|--------|
| PIN-033 | M8-M14 Machine-Native Realignment | ACTIVE (current roadmap) |
| PIN-032 | M7 RBAC Enablement | ENFORCED |
| PIN-009 | External Rollout (Auth Blocker) | BLOCKING M8 |
| PIN-005 | Machine-Native Architecture | PRIMARY (vision) |

---

## Hygiene Scripts

### session_start.sh
Run at the start of every session:
- Checks working environment
- Shows current phase
- Lists blockers
- Verifies services

### hygiene_check.sh
Run weekly (or via cron):
- Detects stale files
- Checks PIN count
- Validates INDEX.md freshness
- Flags completed checklists
- `--fix` mode for auto-cleanup
- `--json` mode for CI

---

## Session Workflow

1. **Start:** `./scripts/ops/session_start.sh`
2. **Read:** `agentiverz_mn/repo_snapshot.md`
3. **Plan:** Check `milestone_plan.md`
4. **Work:** Use relevant checklist
5. **Update:** Mark checklist items complete
6. **End:** Update `repo_snapshot.md` if major changes

---

## Notes

- Host networking required (systemd-resolved + Tailscale)
- Backend publicly accessible on 0.0.0.0:8000
- Auth currently uses STUB - must wire real provider before beta
- PgBouncer on 6432, not direct Postgres on 5433
- All sensitive tokens in `.env` (not committed)
