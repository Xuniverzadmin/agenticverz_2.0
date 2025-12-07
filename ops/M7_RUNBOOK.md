# M7 Runbook: Memory Integration & Operational Hardening

**Version:** 1.0.0
**Last Updated:** 2025-12-04
**Status:** ACTIVE

---

## Owners

| Role | Contact | PagerDuty |
|------|---------|-----------|
| Primary | infra@agenticverz.com | PD_SERVICE_AOS_INFRA |
| Backup | devlead@agenticverz.com | PD_SERVICE_AOS_DEV |
| Escalation | oncall@agenticverz.com | PD_SERVICE_AOS_ONCALL |

---

## Purpose

Execute M7: Memory Integration milestone including:
- Memory pins table and API
- RBAC middleware enforcement
- Prometheus lifecycle management
- Chaos experiments (staging only)
- Operational dashboards

---

## Maintenance Windows

| Environment | Window | Approval Required |
|-------------|--------|-------------------|
| Staging | Any time | No |
| Production | **NOT PART OF M7** | N/A |

**Important:** M7 explicitly excludes production deployment. All work is staging-only.

---

## Preflight Checks

Run before any M7 operation:

```bash
# 1. Verify DB backup exists
pg_dump --dbname=$DATABASE_URL --file=/tmp/pgdump_$(date +%Y%m%d_%H%M%S).sql
echo "Backup created: $(ls -la /tmp/pgdump_*.sql | tail -1)"

# 2. Test restore on staging (optional but recommended)
createdb -h localhost -p 5433 aos_restore_test
pg_restore -h localhost -p 5433 -d aos_restore_test /tmp/pgdump_*.sql
dropdb -h localhost -p 5433 aos_restore_test

# 3. Verify health endpoints
curl -sf http://localhost:8000/health && echo "✓ /health OK"
curl -sf http://localhost:8000/ready && echo "✓ /ready OK"

# 4. Check Redis connectivity
redis-cli ping && echo "✓ Redis OK"

# 5. Verify Prometheus is scraping
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
```

---

## Cancellation Criteria

**STOP IMMEDIATELY if any of these occur:**

1. **Synthetic Check Failures:** >5% of staging health checks failing after change
2. **DB Connection Errors:** >1 error/min sustained for >5 minutes
3. **Prometheus Silenced:** Alerts unexpectedly silenced (possible operator error)
4. **Memory Pins API:** >10% error rate on POST/GET operations
5. **RBAC Lockout:** Any report of legitimate users blocked by RBAC

**Recovery Steps:**
1. Rollback migration: `alembic downgrade -1`
2. Disable RBAC: `RBAC_ENFORCE=false`
3. Restart services: `docker compose restart backend worker`

---

## Blast Radius Controls

| Control | Implementation |
|---------|----------------|
| Namespace isolation | All chaos in `aos-staging` namespace only |
| Feature flags | `RBAC_ENFORCE`, `CHAOS_ALLOWED`, `MEMORY_PINS_ENABLED` |
| Rate limiting | Memory pins API: 100 RPM per tenant |
| Circuit breaker | Auto-disable on >50 errors/min |

**Chaos Experiment Guards:**

```bash
# Chaos scripts MUST check this
if [ "$CHAOS_ALLOWED" != "true" ]; then
    echo "ERROR: CHAOS_ALLOWED not set. Aborting."
    exit 1
fi
```

---

## Postmortem Requirements

Any experiment causing >1h outage in staging requires:
1. Written postmortem in `ops/postmortems/YYYY-MM-DD-<title>.md`
2. Root cause analysis
3. Action items with owners
4. Timeline with UTC timestamps

---

## Run Steps (High-Level)

### Phase 1: Memory Integration

```bash
# 1. Apply migration
cd /root/agenticverz2.0/backend
alembic upgrade head

# 2. Verify table exists
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "\d system.memory_pins"

# 3. Deploy API changes
docker compose up -d backend

# 4. Test API
curl -X POST http://localhost:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" \
  -d '{"tenant_id":"test","key":"test-key","value":{"foo":"bar"}}'
```

### Phase 2: Seed Memory Pins

```bash
# Seed with machine token
MACHINE_JWT=$MACHINE_SECRET_TOKEN python3 ops/seed_memory_pins.py \
  --file ops/memory_pins_seed.json \
  --base http://localhost:8000

# Verify
curl http://localhost:8000/api/v1/memory/pins/test-key?tenant_id=global
```

### Phase 3: Prometheus Lifecycle

```bash
# 1. Validate rules
promtool check rules ops/prometheus_rules/*.yml

# 2. Test reload (requires proxy token)
curl -X POST http://localhost:9090/-/reload \
  -H "Authorization: Bearer $PROM_RELOAD_TOKEN"

# 3. Verify rule loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | length'
```

### Phase 4: RBAC Enforcement

```bash
# 1. Deploy with flag OFF
RBAC_ENFORCE=false docker compose up -d backend

# 2. Test baseline (should work)
curl -X POST http://localhost:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"t1","key":"k","value":{}}'

# 3. Enable RBAC
RBAC_ENFORCE=true docker compose up -d backend

# 4. Test blocked (no token)
curl -X POST http://localhost:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"t1","key":"k","value":{}}'
# Expected: 403 Forbidden

# 5. Test allowed (with token)
curl -X POST http://localhost:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" \
  -d '{"tenant_id":"t1","key":"k","value":{}}'
# Expected: 201 Created
```

### Phase 5: Chaos Experiments

**Only run if `CHAOS_ALLOWED=true`**

1. **Redis Disconnect:** Kill Redis, verify fail-open behavior
2. **DB Connection Exhaustion:** Spike connections, verify pool limits
3. **Memory Pin Storm:** 1000 rapid writes, verify rate limiting

```bash
# Example: Redis chaos
CHAOS_ALLOWED=true ./scripts/chaos/redis_disconnect.sh
```

### Phase 6: Dashboards

1. Import `observability/grafana/m7_memory_pins.json`
2. Import `observability/grafana/m7_rbac_dashboard.json`
3. Verify panels show data

---

## Contacts & Escalation

| Severity | Contact | Response Time |
|----------|---------|---------------|
| P1 (Outage) | PagerDuty PD_SERVICE_AOS_ONCALL | 15 min |
| P2 (Degraded) | Slack #ops-alerts | 1 hour |
| P3 (Warning) | Email infra@agenticverz.com | 4 hours |

---

## Environment Variables

```bash
# Required for M7
RBAC_ENFORCE=true              # Enable RBAC middleware
MACHINE_SECRET_TOKEN=xxxx      # Machine-to-machine auth token
PROM_RELOAD_TOKEN=yyyy         # CI Prometheus reload token
CHAOS_ALLOWED=true             # Must be explicit for chaos scripts
MEMORY_PINS_ENABLED=true       # Enable memory pins API

# Database
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## Rollback Procedures

### Memory Pins Migration Rollback

```bash
# Downgrade migration
cd /root/agenticverz2.0/backend
alembic downgrade -1

# Verify
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "\dt system.memory_pins"
# Should show: Did not find any relation
```

### RBAC Rollback

```bash
# Disable RBAC
RBAC_ENFORCE=false docker compose up -d backend

# Verify
curl -X POST http://localhost:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"t1","key":"k","value":{}}'
# Should: 201 Created (no auth required)
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Memory Pins API latency p95 | <100ms |
| RBAC enforcement accuracy | 100% |
| Prometheus rule reload success | 100% |
| Chaos experiment recovery time | <5 min |
| Zero production impact | Mandatory |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-04 | Initial M7 runbook created | Claude |
