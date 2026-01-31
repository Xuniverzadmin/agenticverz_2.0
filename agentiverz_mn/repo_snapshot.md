# Repository Snapshot

**Last Updated:** 2026-01-28
**Current Phase:** G (Steady State Governance)
**Active Focus:** HOC Topology V2.0.0 Ratified + Migration Planning

---

## System Status

| Component | Status | Health |
|-----------|--------|--------|
| nova_agent_manager | ✅ Up 21h | Healthy |
| nova_worker | ✅ Up 21h | Running |
| nova_db | ✅ Up 21h | Healthy (5433→5432) |
| nova_pgbouncer | ✅ Up 21h | Healthy |
| nova_prometheus | ✅ Up 21h | Running |
| nova_alertmanager | ✅ Up 21h | Running |
| nova_grafana | ✅ Up 21h | Running |

**Running Containers:** 7
**Backend Health:** `{"status":"healthy","version":"1.0.0"}`

---

## Milestone Status

| Milestone | Status | PIN |
|-----------|--------|-----|
| M0-M7 | ✅ COMPLETE | PIN-009 to PIN-032 |
| M8: Demo + SDK + Auth | ✅ COMPLETE | PIN-033 |
| M9: Failure Catalog v2 | ✅ COMPLETE | PIN-048/049 |
| M10: Recovery Suggestion Engine | ✅ COMPLETE | PIN-050/057/061 |
| M11: Skill Expansion | ✅ COMPLETE | PIN-055/056/059/060 |
| M12: Multi-Agent System | ✅ COMPLETE | PIN-062/063 |
| M13: Console UI & Boundary | ✅ COMPLETE | PIN-064/067/068 |
| M14: BudgetLLM Safety | ✅ COMPLETE | PIN-070 |
| M15: SBA Foundations | ✅ COMPLETE | PIN-071/072/073 |
| M16: Agent Governance Console | ✅ COMPLETE | PIN-074 |
| M17: CARE Routing Engine | ✅ COMPLETE | PIN-075 |
| M18: CARE-L & SBA Evolution | ✅ COMPLETE | PIN-076/077 |
| M19: Policy Constitutional | ✅ COMPLETE | PIN-078 |
| M20: Policy Compiler & Runtime | ✅ COMPLETE | PIN-084 |
| M21: Tenant Auth Billing | ✅ COMPLETE | PIN-079 |
| M22: KillSwitch MVP | ✅ COMPLETE | PIN-096 |
| M23: AI Incident Console | ✅ COMPLETE | PIN-100 |
| M24: Ops Console Phase 2 | ✅ COMPLETE | PIN-105/111 |
| M25: Rollback Safe Release | ✅ COMPLETE | PIN-140 |
| M26: Cost Intelligence | ✅ COMPLETE | PIN-141 |
| M27: Cost Loop Enforcement | ✅ COMPLETE | PIN-143 |
| M28+ | ✅ Contract Framework | PIN-163/170 |

---

## Current Work (2026-01-28)

### HOC Domain Migration COMPLETE (PIN-483)

All 10 phases of HOC domain migration completed:

| Phase | Scope | Status |
|-------|-------|--------|
| P0 | Migration manifest | ✅ COMPLETE |
| P1-P5 | Core domain extraction | ✅ COMPLETE |
| P6 | Consolidation review (90+ candidates) | ✅ COMPLETE |
| P7 | Execution (40 deleted, 3 relocated, 14 edited) | ✅ COMPLETE |
| P8 | Domain locks (11 locks verified) | ✅ COMPLETE |
| P9-P10 | Final verification | ✅ COMPLETE |

**HOC Architecture:** `backend/app/hoc/` (7-layer topology v1.2.0)
- `api/` — L2 API facades
- `cus/` — Customer domain logic
- `int/` — Internal platform logic

### Infrastructure Optimizations

| PIN | Optimization | Status |
|-----|--------------|--------|
| PIN-475 | Worker pool manual restart (Neon cost control) | ✅ COMPLETE |
| PIN-476 | Amavis 1 worker + disable ClamAV | ✅ COMPLETE |
| PIN-477 | Journal limits + bloat audit | ✅ COMPLETE |
| PIN-478 | Claude context modularization | ✅ COMPLETE |

### Customer Console Architecture

Domain audits completed:
- Activity, Incidents, Policies, Logs, Analytics domains
- Connectivity, Limits Management, Cross-Domain audits

**Build Plan:** `docs/architecture/CUSTOMER_CONSOLE_BUILD_PLAN.md`

---

## Key Directories

```
/root/agenticverz2.0/
├── backend/app/           # FastAPI application
│   └── hoc/               # House of Cards layer topology
│       ├── api/           # L2 API facades
│       ├── cus/           # Customer domain (L3-L6)
│       └── int/           # Internal platform
├── sdk/python/            # Python SDK (aos_sdk_ prefixed)
├── sdk/js/                # JavaScript SDK
├── website/app-shell/     # Customer Console
├── docs/
│   ├── memory-pins/       # 476 PINs
│   ├── architecture/hoc/  # HOC architecture docs
│   ├── contracts/         # System contracts
│   └── governance/        # Governance (73 files)
├── scripts/
│   ├── ci/                # Guardrail scripts
│   └── ops/               # Operations scripts
└── design/l2_1/           # AURORA L2 projection pipeline
```

---

## Quick Commands

```bash
# Session start
./scripts/ops/session_start.sh

# Run guardrails
python scripts/ci/run_guardrails.py

# Check enforcement status
python scripts/ci/guardrail_enforcer.py --status

# Request bypass (emergency only)
python scripts/ci/guardrail_enforcer.py --authorize

# BLCA validation
python scripts/ops/layer_validator.py --backend --ci

# Service health
docker compose ps
curl http://localhost:8000/health
```

---

## Recent Changes

| Date | Change |
|------|--------|
| 2026-01-28 | **HOC Topology V2.0.0 RATIFIED** — L3 removed, single orchestrator (PIN-484) |
| 2026-01-28 | HOC literature generation plan added |
| 2026-01-27 | HOC domain migration P0-P10 all phases complete (PIN-483) |
| 2026-01-27 | P8 domain locks verified (11 locks) (PIN-482) |
| 2026-01-27 | P7 execution: 40 files deleted, 3 relocated, 14 edited (PIN-481) |
| 2026-01-27 | P6 consolidation review complete (PIN-480) |
| 2026-01-26 | Claude context modularization (PIN-478) |
| 2026-01-26 | Journal limits + bloat audit (PIN-477) |
| 2026-01-26 | Amavis optimization: 1 worker (PIN-476) |
| 2026-01-26 | Worker pool manual restart model (PIN-475) |

---

## Environment

| Variable | Value |
|----------|-------|
| DATABASE_URL | postgresql://...@localhost:6432/nova_aos |
| REDIS_URL | redis://localhost:6379/0 |
| AUTH_SERVICE | Clerk (production) |
| DB_AUTHORITY | neon (canonical) |

---

## Archived Files

Completed checklists moved to `agentiverz_mn/archive/`:
- m9_checklist.md (M9 complete)
- m9_blueprint.md
- m9_postmortem.md
- demo_checklist.md (complete)
- sdk_packaging_checklist.md (complete)
- auth_integration_checklist.md (complete)
- auth_blocker_notes.md (resolved)

---

## Notes

- HOC 7-layer topology ratified v1.2.0
- 11 domain locks verified (all customer domains)
- Worker pool requires manual restart for cost control
- Amavis running with 1 worker (PIN-476)
- Phase G steady state governance active
- 476 memory PINs (consider archiving older ones)
- BLCA validation required: `python3 scripts/ops/layer_validator.py --backend --ci`
