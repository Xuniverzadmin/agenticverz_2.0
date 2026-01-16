# Repository Snapshot

**Last Updated:** 2026-01-16
**Current Phase:** G (Steady State Governance)
**Active Focus:** Customer Console Architecture & Governance Enforcement

---

## System Status

| Component | Status | Health |
|-----------|--------|--------|
| Backend API | ✅ Running | Healthy |
| Worker | ✅ Running | Healthy |
| PostgreSQL | ✅ Running | Healthy |
| PgBouncer | ✅ Running | Healthy |
| Prometheus | ✅ Running | Healthy |
| Alertmanager | ✅ Running | Healthy |
| Grafana | ✅ Running | Healthy |

**Running Containers:** 7

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

## Current Work (2026-01-16)

### Governance Enforcement System (PIN-436)

Implemented 17 CI guardrail scripts with 3-layer enforcement:

| Layer | Hook | Purpose |
|-------|------|---------|
| 1 | pre-commit | Blocks commits with violations |
| 2 | post-commit | Records bypass usage |
| 3 | pre-push | Blocks unauthorized bypasses |

**Guardrail Categories:**
- DOMAIN (3): Ownership, boundaries, read-only
- DATA (2): Foreign keys, tenant isolation
- CROSS-DOMAIN (2): Propagation, bidirectional
- LIMITS (3): Single source, pre-check, audit
- AUDIT (2): Governance actions, completeness
- CAPABILITY (3): Endpoints, console, status
- API (2): Facade, envelope

**Current Status:** 7/17 passing, 41 violations to fix

### Customer Console Architecture

Domain audits completed:
- Activity Domain Audit
- Incidents Domain Audit
- Policies Domain Audit
- Logs Domain Audit
- Analytics Domain Audit
- Connectivity Domain Audit
- Limits Management Audit
- Cross-Domain Audit

**Build Plan:** `docs/architecture/CUSTOMER_CONSOLE_BUILD_PLAN.md`
**Guardrails:** `docs/architecture/GOVERNANCE_GUARDRAILS.md`

---

## Key Directories

```
/root/agenticverz2.0/
├── backend/app/           # FastAPI application
├── sdk/python/            # Python SDK
├── sdk/js/                # JavaScript SDK
├── website/app-shell/     # Customer Console
├── docs/
│   ├── memory-pins/       # 436 PINs
│   ├── architecture/      # Domain audits & guardrails
│   ├── contracts/         # System contracts
│   └── governance/        # Governance documents
├── scripts/
│   ├── ci/                # 17 guardrail scripts + enforcer
│   └── ops/               # Operations scripts
└── design/l2_1/           # UI projection pipeline
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
| 2026-01-16 | Installed 3-layer governance enforcement (PIN-436) |
| 2026-01-16 | Created 17 guardrail CI scripts |
| 2026-01-16 | Completed domain audits for customer console |
| 2026-01-16 | Panel adapter layer implementation (PIN-434) |
| 2026-01-15 | HISAR schema split and verification (PIN-429) |
| 2026-01-15 | Logs domain HISAR verification (PIN-432) |
| 2026-01-15 | Analytics domain promoted to OBSERVED (PIN-428) |

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

- Pre-commit hook blocks guardrail violations
- Bypass requires authorization code + audit trail
- 41 baseline violations to fix (see PIN-436)
- Customer console build plan ready for implementation
- Phase G steady state governance active
