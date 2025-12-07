# Repository Snapshot

**Date:** 2025-12-05
**Milestone:** M8 Auth Complete, SDK/Demo Next

---

## Project Status

| Milestone | Status |
|-----------|--------|
| M0: Foundations & Contracts | ✅ FINALIZED |
| M1-M2.5: Runtime + Skills + Planner | ✅ COMPLETE |
| M3-M3.5: Core Skills + CLI + Demo | ✅ COMPLETE |
| M4: Workflow Engine v1 | ✅ SIGNED OFF |
| M5: Policy API & Approval Workflow | ✅ COMPLETE |
| M5.5: Machine-Native APIs | ✅ COMPLETE |
| M6: CostSim V2 + Drift + Audit | ✅ COMPLETE |
| M6.5: Webhook Externalization | ✅ VALIDATED |
| M7: Memory Integration | ✅ COMPLETE |
| M7: RBAC Enforcement | ✅ ENFORCED |
| **M8: Auth Integration** | ✅ **COMPLETE** |
| **M8: SDK Packaging** | ⏳ NEXT |
| **M8: Demo Productionization** | ⏳ NEXT |

---

## Running Services

| Service | Container | Status | Port |
|---------|-----------|--------|------|
| Backend | nova_agent_manager | healthy | 8000 |
| Worker | nova_worker | running | - |
| Database | nova_db | healthy | 5433 |
| PgBouncer | nova_pgbouncer | healthy | 6432 |
| Prometheus | nova_prometheus | running | 9090 |
| Grafana | nova_grafana | running | 3000 |
| Alertmanager | nova_alertmanager | running | 9093 |
| **Keycloak** | keycloak | healthy | 8080 (internal) |

**External Access:**
- **Auth:** https://auth-dev.xuniverz.com (Keycloak via Apache + Cloudflare)

---

## Auth Integration (COMPLETE)

| Component | Status | Details |
|-----------|--------|---------|
| Auth Provider | ✅ Keycloak | auth-dev.xuniverz.com |
| Realm | ✅ Created | agentiverz-dev |
| OIDC Client | ✅ Configured | aos-backend (confidential) |
| OIDC Provider | ✅ Implemented | `backend/app/auth/oidc_provider.py` |
| RBAC Wiring | ✅ Complete | Keycloak JWT → AOS roles |
| Test User | ✅ Created | devuser (admin role) |
| API Verified | ✅ Working | Memory pins API tested |
| Cloudflare | ✅ Proxied | TLS + CDN |

---

## Directory Structure

```
/root/agenticverz2.0/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── db.py             # SQLModel models
│   │   ├── api/              # API routers
│   │   ├── auth/             # RBAC, OIDC provider
│   │   ├── skills/           # Skill implementations
│   │   ├── worker/           # Worker pool, runtime
│   │   ├── workflow/         # Workflow engine
│   │   ├── memory/           # Memory store
│   │   ├── costsim/          # Cost simulation V2
│   │   ├── schemas/          # JSON schemas
│   │   └── specs/            # Specifications
│   ├── cli/
│   │   └── aos.py            # CLI tool
│   └── tests/                # Test suite
├── sdk/
│   ├── python/               # Python SDK (10/10 tests)
│   └── js/                   # JS SDK (needs work)
├── docs/
│   ├── memory-pins/          # 33 PINs
│   └── runbooks/             # Operations guides
├── monitoring/
│   ├── prometheus.yml
│   ├── alertmanager/
│   ├── dashboards/
│   └── rules/
├── scripts/
│   ├── ops/                  # Operations scripts
│   ├── stress/               # Load testing
│   └── smoke/                # Smoke tests
├── tools/
│   └── webhook_receiver/     # Webhook K8s deployment
├── secrets/
│   └── keycloak_oidc.env     # OIDC credentials (600)
├── docker-compose.yml
└── .env                      # Environment config
```

---

## Key Files for M8 (Remaining)

### SDK Packaging

| File | Purpose |
|------|---------|
| `sdk/python/` | Python SDK (needs pyproject.toml) |
| `sdk/python/tests/test_python_sdk.py` | 10/10 tests passing |
| `sdk/js/nova-sdk/` | JS SDK (needs package.json, types) |

### Demo

| File | Purpose |
|------|---------|
| `sdk/python/tests/test_python_sdk.py:test_sixty_second_demo_scenario` | Demo test |
| `backend/cli/aos.py` | CLI tool |

### Skills Available

| Skill | File | Status |
|-------|------|--------|
| http_call | `backend/app/skills/http_call.py` | Production |
| llm_invoke | `backend/app/skills/llm_invoke.py` | Production |
| json_transform | `backend/app/skills/json_transform.py` | Production |
| postgres_query | `backend/app/skills/postgres_query.py` | Production |
| calendar_write | `backend/app/skills/calendar_write.py` | Production |

---

## API Endpoints (Machine-Native)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/runtime/capabilities` | GET | Skills, budget, rate limits |
| `/api/v1/runtime/simulate` | POST | Plan simulation |
| `/api/v1/runtime/query` | POST | State queries |
| `/api/v1/runtime/skills/{id}` | GET | Skill details |
| `/api/v1/runs` | POST | Create run |
| `/api/v1/runs/{id}` | GET | Run status |
| `/api/v1/memory/pins` | GET/POST | Memory pins |

---

## Test Status

| Suite | Count | Status |
|-------|-------|--------|
| Total tests | ~1040 | Passing |
| Python SDK | 10/10 | Passing |
| Integration | 18/20 | Passing (2 skipped) |
| Workflow | All | Passing |
| RBAC | 16/16 | Passing |

---

## Database Tables

| Table | Purpose |
|-------|---------|
| runs | Agent run records |
| approval_requests | Policy approvals |
| memory_pins | Key-value memory |
| failure_matches | (M9) Failure persistence |
| recovery_candidates | (M10) Recovery suggestions |
| rbac_audit | RBAC decision audit |
| memory_audit | Memory operation audit |

---

## Environment Variables

```bash
# Current .env (key variables)
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
REDIS_URL=redis://localhost:6379/0
AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf
ANTHROPIC_API_KEY=<set>
RBAC_ENABLED=true
RBAC_ENFORCE=true
MACHINE_SECRET_TOKEN=<set>

# OIDC (NEW - Keycloak)
OIDC_ISSUER_URL=https://auth-dev.xuniverz.com/realms/agentiverz-dev
OIDC_CLIENT_ID=aos-backend
OIDC_CLIENT_SECRET=<see secrets/keycloak_oidc.env>
OIDC_VERIFY_SSL=true
```

---

## Documentation Index

| Document | Location |
|----------|----------|
| Memory PINs Index | `docs/memory-pins/INDEX.md` |
| M8-M14 Roadmap | `docs/memory-pins/PIN-033-m8-m14-machine-native-realignment.md` |
| Auth Integration | `agentiverz_mn/auth_integration_checklist.md` (COMPLETE) |
| API Workflow Guide | `docs/API_WORKFLOW_GUIDE.md` |
| OpenAPI Spec | `docs/openapi.yaml` |

---

## Quick Commands

```bash
# Check service health
curl http://localhost:8000/health

# Check capabilities
curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities

# Get Keycloak token
source /root/agenticverz2.0/secrets/keycloak_oidc.env
TOKEN=$(curl -sk -X POST "https://auth-dev.xuniverz.com/realms/agentiverz-dev/protocol/openid-connect/token" \
  -d "username=devuser" -d "password=devuser123" -d "grant_type=password" \
  -d "client_id=aos-backend" -d "client_secret=$OIDC_CLIENT_SECRET" | jq -r '.access_token')

# API call with OIDC token
curl -s http://localhost:8000/api/v1/memory/pins -H "Authorization: Bearer $TOKEN"

# Run tests
cd /root/agenticverz2.0/backend && PYTHONPATH=. python -m pytest tests/ -v

# Rebuild backend
cd /root/agenticverz2.0 && docker compose up -d --build backend worker
```

---

## M8 Status

**Completed:**
- ✅ Real auth provider (Keycloak at auth-dev.xuniverz.com)
- ✅ OIDC integration with RBAC middleware
- ✅ Cloudflare proxy with TLS

**Remaining:**
- ⏳ pyproject.toml for Python SDK
- ⏳ package.json + types for JS SDK
- ⏳ Productized demo scripts
- ⏳ Screencast/documentation

**Next task:** SDK packaging (see `sdk_packaging_checklist.md`)
