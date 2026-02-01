# Claude Context File - AOS / Agenticverz 2.0

**Last Updated:** 2026-01-28

---

## Project Context

Read `.claude/project-context.md` for vision, mission, objectives, and current status.

## Governance

Rules auto-load from `.claude/rules/` (path-scoped). Hooks enforce via `.claude/settings.json`.

| Rule File | Scope | Always On? |
|-----------|-------|-----------|
| governance-core.md | `**` | Yes |
| artifact-registration.md | `**` | Yes |
| hoc-layer-topology.md | `hoc/**`, `backend/app/hoc/**` | No |
| auth-architecture.md | `backend/app/auth/**`, `backend/app/api/**` | No |
| database-authority.md | `backend/alembic/**`, `backend/app/db/**` | No |
| sdsr-contract.md | `backend/scripts/sdsr/**`, `backend/aurora_l2/**` | No |
| ui-pipeline.md | `design/**`, `website/**` | No |
| audience-classification.md | `backend/**/*.py` | No |

Full governance docs: `docs/governance/` (73 files)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + SQLModel + PostgreSQL |
| Worker | ThreadPoolExecutor (manual restart, PIN-475) |
| Database | Neon PostgreSQL (authoritative) + local Postgres (staging) |
| Frontend | Vite app-shell, Apache serves dist/ |
| Observability | Prometheus + Alertmanager + Grafana |
| Container | Docker Compose with host networking |
| LLM | Anthropic Claude (claude-sonnet-4-20250514) |
| Pool | PgBouncer (port 6432) |
| Mail | Postfix + amavisd (1 worker, PIN-476) |
| Auth | Clerk JWT (human) + X-AOS-Key (machine) |

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| nova_agent_manager | 8000 | Backend API |
| nova_db | 5433 | PostgreSQL |
| nova_pgbouncer | 6432 | Connection pool |
| nova_prometheus | 9090 | Metrics |
| nova_alertmanager | 9093 | Alert routing |
| nova_grafana | 3000 | Dashboards |

---

## Key Directories

```
/root/agenticverz2.0/
├── agentiverz_mn/              # Working environment (START HERE)
├── backend/app/                # FastAPI application
│   └── hoc/                    # HOC layer topology V2.0.0
│       ├── hoc_spine/          # System constitution (L4 orchestrator)
│       ├── api/                # L2 HTTP layer
│       └── cus/                # Customer domains (L5 + L6)
├── design/l2_1/                # AURORA L2 intents + projection
├── website/app-shell/          # Frontend (Vite)
├── sdk/python/ + js/           # SDKs
├── docs/memory-pins/           # 477+ PINs (project memory)
├── docs/governance/            # Governance (73 files)
├── docs/contracts/             # System contracts
├── docs/architecture/topology/ # HOC Topology V2.0.0 (RATIFIED)
├── docs/architecture/hoc/      # HOC architecture docs
├── scripts/ops/                # Ops scripts (session_start, bloat audit)
├── scripts/preflight/          # Contract scanner (cron 30min)
├── scripts/hooks/              # Claude hooks (post-edit, post-bash)
└── monitoring/                 # Prometheus + Grafana configs
```

---

## Common Commands

```bash
# Session start (ALWAYS RUN FIRST)
./scripts/ops/session_start.sh

# Check services
docker compose ps

# View logs
docker compose logs backend --tail 100

# Health check
curl http://localhost:8000/health

# Run tests
cd backend && PYTHONPATH=. python -m pytest tests/ -v

# Rebuild backend
docker compose up -d --build backend

# BLCA layer validation
python3 scripts/ops/layer_validator.py --backend --ci

# Contract scan
python3 scripts/preflight/agen_internal_system_scan.py

# System bloat audit
./scripts/ops/system_bloat_audit.sh

# Memory trail
python scripts/ops/memory_trail.py find "keyword"
python scripts/ops/memory_trail.py pin --title "Title" --category "Cat" --summary "..."
python scripts/ops/memory_trail.py update 123 --section "Updates" --content "..."

# Artifact lookup
python scripts/ops/artifact_lookup.py <name>
python scripts/ops/artifact_lookup.py --id <ID>

# Change record
python scripts/ops/change_record.py create --purpose "..." --type bugfix --artifacts <ID>

# HOC scaffolding (PIN-509)
python3 scripts/ops/new_l5_engine.py <domain> <engine_name>    # Scaffold L5 engine
python3 scripts/ops/new_l6_driver.py <domain> <driver_name>    # Scaffold L6 driver

# Tombstone auto-collapse (PIN-509)
python3 scripts/ops/collapse_tombstones.py            # Dry run
python3 scripts/ops/collapse_tombstones.py --apply    # Delete zero-dependent tombstones

# HOC CI checks (PIN-507 + PIN-508 + PIN-509, 18 checks)
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
```

---

## Environment Variables

```bash
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
REDIS_URL=redis://localhost:6379/0
AOS_API_KEY=<in .env>
RBAC_ENABLED=true
RBAC_ENFORCE=true
```

---

## Bootstrap Sequence

Before ANY work, Claude must:
1. Run `./scripts/ops/session_start.sh` (health checks)
2. Acknowledge BLCA status (legacy debt tolerated per PIN-438)
3. Provide SESSION_BOOTSTRAP_CONFIRMATION

Rules loaded from `.claude/rules/` enforce governance automatically.

---

## Session Workflow

1. **Start:** `./scripts/ops/session_start.sh`
2. **Read:** `agentiverz_mn/repo_snapshot.md`
3. **Plan:** Check `agentiverz_mn/milestone_plan.md`
4. **Work:** Use relevant checklist
5. **Update:** Mark items complete
6. **End:** Update `repo_snapshot.md` if major changes

---

## Behavior Library Triggers

| Rule ID | Trigger | Required Section |
|---------|---------|-----------------|
| BL-BOOT-001 | First response | SESSION_BOOTSTRAP_CONFIRMATION |
| BL-ENV-001 | Testing endpoints | RUNTIME SYNC CHECK |
| BL-DB-001 | datetime operations | TIMESTAMP SEMANTICS CHECK |
| BL-AUTH-001 | Auth errors (401/403) | AUTH CONTRACT CHECK |
| BL-MIG-001 | Migrations | MIGRATION HEAD CHECK |
| BL-AUD-001 | ALL .py files | AUDIENCE_CLASSIFICATION_CHECK |

---

## Web Server Infrastructure

```
INTERNET (80/443) → APACHE → serves all sites
                         └→ mail.xuniverz.com → NGINX (127.0.0.1:8081) → iRedMail
```

| Domain | Config | DocumentRoot |
|--------|--------|--------------|
| console.agenticverz.com | console.agenticverz.com.conf | dist/ |
| preflight-console.agenticverz.com | preflight-console.agenticverz.com.conf | dist-preflight/ |

Console routes: Customer `/cus/*`, Preflight `/precus/*`

---

## Machine-Native APIs

```
POST /api/v1/runtime/simulate      # Plan feasibility
POST /api/v1/runtime/query         # State queries
GET  /api/v1/runtime/capabilities  # Skills, budget, limits
POST /api/v1/runs                  # Create run
GET  /api/v1/runs/{id}             # Run status
```

Auth: `X-AOS-Key` (machine) or `Authorization: Bearer <jwt>` (human)
Public: /health, /metrics, /api/v1/auth/, /docs, /openapi.json

---

## HOC Layer Topology V2.0.0 (RATIFIED)

**Spec:** `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`

**6-Layer Execution-Centric Architecture:**

```
L2.1 Facade → L2 API → L4 hoc_spine → L5 Engine → L6 Driver → L7 Model
                           ↑
                    SINGLE ORCHESTRATOR
```

| Layer | Location | Responsibility |
|-------|----------|----------------|
| L2.1 | `hoc/api/facades/cus/` | Groups routers by domain |
| L2 | `hoc/api/cus/{domain}/` | HTTP boundary (thin) |
| L4 | `hoc/cus/hoc_spine/` | Single orchestrator, cross-domain owner |
| L5 | `hoc/cus/{domain}/L5_engines/` | Domain business logic |
| L6 | `hoc/cus/{domain}/L6_drivers/` | Domain DB operations |
| L7 | `app/models/` | ORM tables |

**Key Constraints:**
- NO L3 layer (removed)
- NO L5 engines in hoc_spine
- L4 owns ALL cross-domain coordination
- L5 engines never call other domains

---

## Key Memory PINs

| PIN | Topic | Status |
|-----|-------|--------|
| PIN-484 | HOC Topology V2.0.0 Ratification | RATIFIED |
| PIN-477 | Journal limits + bloat audit | COMPLETE |
| PIN-476 | Amavis optimization (1 worker) | COMPLETE |
| PIN-475 | Worker pool manual restart | COMPLETE |
| PIN-474 | Validator → scheduled scan | COMPLETE |
| PIN-470 | HOC Layer Inventory | ACTIVE |
| PIN-438 | Linting Technical Debt | ACKNOWLEDGED |
| PIN-370 | SDSR System Contract | LOCKED |
| PIN-271 | RBAC Architecture Directive | ACTIVE |
| PIN-245 | Architecture Governor | ACTIVE |
| PIN-005 | Machine-Native Architecture | PRIMARY |

Full index: `docs/memory-pins/INDEX.md`

---

## Notes

- Host networking required (systemd-resolved + Tailscale)
- Backend publicly accessible on 0.0.0.0:8000
- Auth uses Clerk (prod) + stub (dev, AUTH_STUB_ENABLED=true)
- PgBouncer on 6432, not direct Postgres on 5433
- All sensitive tokens in `.env` (not committed)
- Original CLAUDE.md backed up: CLAUDE.md.bak.20260127
