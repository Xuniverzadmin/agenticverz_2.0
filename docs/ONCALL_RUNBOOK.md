# AOS On-Call Runbook

**Last Updated:** 2025-12-06

---

## Quick Reference

| Service | Port | Health Check |
|---------|------|--------------|
| Backend API | 8000 | `curl http://localhost:8000/health` |
| PgBouncer | 6432 | `PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "SELECT 1"` |
| Postgres | 5433 | `docker exec nova_db pg_isready -U nova` |
| Prometheus | 9090 | `curl http://localhost:9090/-/healthy` |
| Grafana | 3000 | `curl -u admin:admin http://localhost:3000/api/health` |
| Alertmanager | 9093 | `curl http://localhost:9093/api/v2/status` |

---

## Service Management

### Check All Services
```bash
docker compose ps
```

### Restart a Service
```bash
docker compose restart backend
docker compose restart worker
docker compose restart prometheus
```

### View Logs
```bash
# Backend logs
docker logs nova_agent_manager --tail 100 -f

# Worker logs
docker logs nova_worker --tail 100 -f

# All logs
docker compose logs -f --tail 100
```

---

## Common Issues

### 1. Backend Health Check Failing

**Symptoms:** `/health` returns non-200 or times out

**Diagnosis:**
```bash
# Check container status
docker ps | grep nova_agent_manager

# Check logs for errors
docker logs nova_agent_manager --tail 50

# Check database connectivity
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "SELECT 1"
```

**Resolution:**
```bash
# Restart backend
docker compose restart backend

# If DB issue, restart PgBouncer
docker compose restart pgbouncer
```

---

### 2. Rate Limiting Issues

**Symptoms:** Unexpected 429 responses, or rate limiting not working

**Diagnosis:**
```bash
# Check Redis connectivity
curl -s http://localhost:8000/metrics | grep aos_rate_limit_redis

# Expected: aos_rate_limit_redis_connected 1.0

# Check current rate limit counters
curl -s http://localhost:8000/metrics | grep aos_rate_limit
```

**Resolution:**
- If `redis_connected=0`: Check Redis URL in `.env` and restart backend
- If counters wrong: Wait for window to reset (1 minute)

---

### 3. Docker Container Network Failure

**Symptoms:** Containers can't reach external internet, builds hang

**Diagnosis:**
```bash
# Test container network
docker run --rm alpine ping -c 2 8.8.8.8

# Check nftables rules
sudo nft list chain inet filter forward | grep docker
```

**Resolution:**
```bash
# Run the fix script
/root/scripts/fix-nft-docker.sh

# Or manually add rules
sudo nft add rule inet filter forward iifname "docker0" accept
sudo nft add rule inet filter forward oifname "docker0" accept
```

---

### 4. Database Connection Errors

**Symptoms:** `connection refused` or `too many connections`

**Diagnosis:**
```bash
# Check PgBouncer
docker exec nova_pgbouncer pgbouncer -R /etc/pgbouncer/pgbouncer.ini

# Check active connections
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "SELECT count(*) FROM pg_stat_activity"
```

**Resolution:**
```bash
# Restart PgBouncer
docker compose restart pgbouncer

# If still failing, restart Postgres (causes brief downtime)
docker compose restart db
```

---

### 5. Trace Storage Errors

**Symptoms:** 500 errors when storing/retrieving traces

**Diagnosis:**
```bash
# Check trace count
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "SELECT COUNT(*) FROM aos_traces"

# Check for table issues
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "\d aos_traces"
```

**Resolution:**
- Ensure `USE_POSTGRES_TRACES=true` in docker-compose.yml
- Check migration status: `alembic current`

---

## Mismatch Investigation

When a determinism mismatch is detected:

1. **Get mismatch details:**
```bash
curl -s -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/traces/{trace_id}/mismatches
```

2. **Compare traces:**
```bash
# Use aos diff command
PYTHONPATH=backend python3 backend/cli/aos.py diff <run_id_1> <run_id_2>
```

3. **Check for common causes:**
- Timestamp drift (non-deterministic zone)
- External API response changes
- Seed not being respected

---

## Metrics to Monitor

### Critical Alerts
- `aos_rate_limit_redis_connected == 0` - Redis down
- `aos_rate_limit_redis_errors_total` increasing - Redis issues
- Backend health check failing

### Warning Alerts
- `aos_rate_limit_blocked_total` high - May need tier adjustment
- Trace storage errors increasing

### Dashboards
- **NOVA Basic Dashboard** - Overall health
- **NOVA M4 Workflow Engine** - Workflow metrics
- **M4.5 Failure Catalog** - Error tracking
- **AOS Traces & Determinism** - Trace metrics

---

## Recovery Procedures

### Full Service Recovery
```bash
cd /root/agenticverz2.0

# Stop all services
docker compose down

# Start fresh
docker compose up -d

# Verify health
sleep 30 && docker compose ps
curl http://localhost:8000/health
```

### Database Recovery
```bash
# Check latest backup
ls -la /var/lib/aos/backups/

# Restore from backup (if needed)
PGPASSWORD=novapass pg_restore -h localhost -p 5433 -U nova -d nova_aos /path/to/backup.dump
```

---

## Escalation

If issues persist after running through this runbook:

1. Check recent deployments/changes
2. Review full error logs
3. Contact on-call SRE
4. Create incident in tracking system

---

## Environment Variables

Key environment variables in `.env`:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection (use 6432 for PgBouncer) |
| `REDIS_URL` | Upstash Redis for rate limiting |
| `AOS_API_KEY` | API authentication key |
| `RBAC_ENABLED` | RBAC enforcement |
| `USE_POSTGRES_TRACES` | Use Postgres for trace storage |

---

## Useful Commands

```bash
# Check migration status
PGPASSWORD=novapass DATABASE_URL="postgresql://nova:novapass@localhost:6432/nova_aos" alembic current

# Run migrations
PGPASSWORD=novapass DATABASE_URL="postgresql://nova:novapass@localhost:6432/nova_aos" alembic upgrade head

# Test API
source .env && curl -s -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities | jq

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```
