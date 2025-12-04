# AOS On-Call Quick Reference

**Version:** 1.0
**Last Updated:** 2025-12-03
**Scope:** M4 Workflow Engine + M5 Policy API

---

## Quick Health Checks (30 seconds)

```bash
# 1. API Health
curl -s http://127.0.0.1:8000/health | jq .

# 2. Policy API Health
curl -s http://127.0.0.1:8000/api/v1/policy/eval -X POST \
  -H "Content-Type: application/json" \
  -d '{"policy_type":"cost","capability":"test","tenant_id":"health"}' | jq .allowed

# 3. Container Status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep nova

# 4. DB Connections
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT state, count(*) FROM pg_stat_activity WHERE datname='nova_aos' GROUP BY state;"

# 5. Pending Approvals
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT status, count(*) FROM approval_requests GROUP BY status;"
```

---

## Key Metrics to Monitor

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `nova_policy_decisions_total{decision="deny"}` | >10/min | >50/min | Check policy config |
| `nova_approval_requests_pending` | >50 | >200 | Check escalation worker |
| `nova_webhook_delivery_failures_total` | >5/hour | >20/hour | Check webhook endpoints |
| `pg_stat_activity active` | >30 | >50 | Scale DB / add pooler |
| API p95 latency | >500ms | >2000ms | Check DB locks |

---

## Common Issues & Fixes

### 1. High API Latency (p95 > 500ms)

**Symptoms:** Slow responses, timeouts

```bash
# Check DB connections
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT pid, state, wait_event_type, query FROM pg_stat_activity WHERE state='active';"

# Check for locks
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT * FROM pg_locks WHERE NOT granted;"

# Fix: Restart stuck connections
docker exec nova_agent_manager kill -HUP 1
```

### 2. Approval Backlog Growing

**Symptoms:** `nova_approval_requests_pending` increasing

```bash
# Check escalation cron
tail -50 /var/log/aos/escalation.log

# Manual escalation run
docker exec nova_agent_manager python /app/scripts/run_escalation.py

# Check expired requests
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT count(*) FROM approval_requests WHERE status='pending' AND expires_at < NOW();"
```

### 3. Webhook Failures

**Symptoms:** `last_webhook_status` showing errors

```bash
# Check webhook errors
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT last_webhook_status, count(*) FROM approval_requests
   WHERE webhook_url IS NOT NULL GROUP BY last_webhook_status;"

# Retry failed webhooks (manual)
curl -X POST http://127.0.0.1:8000/api/v1/policy/requests/{id}/retry-webhook
```

### 4. Connection Pool Exhausted

**Symptoms:** "QueuePool limit reached" errors

```bash
# Immediate: Restart backend
docker restart nova_agent_manager

# Check pool settings (should be pool_size=20, max_overflow=30)
docker exec nova_agent_manager grep -A5 "pool_size" /app/app/db.py

# Long-term: Deploy PgBouncer
kubectl apply -f k8s/pgbouncer-deployment.yaml
```

### 5. Prometheus Alerts Not Firing

```bash
# Check Prometheus targets
curl -s http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Check alert rules loaded
curl -s http://127.0.0.1:9090/api/v1/rules | jq '.data.groups[].name'

# Reload Prometheus
docker exec nova_prometheus kill -HUP 1
```

---

## Emergency Procedures

### EMERGENCY: Disable All Approvals

```bash
# 1. Disable auto-approve
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "UPDATE feature_flags SET enabled=false WHERE flag_name LIKE '%auto_approve%';"

# 2. Mass reject pending (DESTRUCTIVE)
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "UPDATE approval_requests SET status='rejected', resolved_at=NOW() WHERE status='pending';"
```

### EMERGENCY: Stop Escalation

```bash
# Remove cron job
crontab -l | grep -v "run_escalation.py" | crontab -

# Or kill running process
pkill -f "run_escalation.py"
```

### EMERGENCY: Database Overload

```bash
# 1. Kill long-running queries
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state='active' AND query_start < NOW() - INTERVAL '5 minutes';"

# 2. Reduce app connections
docker stop nova_worker  # Stop worker to reduce load
```

---

## Key Files & Paths

| Component | Path |
|-----------|------|
| Backend logs | `docker logs nova_agent_manager` |
| Escalation logs | `/var/log/aos/escalation.log` |
| Shadow logs | `/var/lib/aos/shadow_monitor.log` |
| Alert rules | `monitoring/rules/m5_policy_alerts.yml` |
| Policy API | `backend/app/api/policy.py` |
| DB config | `backend/app/db.py` |
| Runbooks | `docs/runbooks/` |

---

## Contacts

| Role | Contact | When |
|------|---------|------|
| Platform Lead | @platform-oncall | Architecture decisions |
| Security | @security-oncall | Webhook compromise, auth issues |
| Database | @db-oncall | Connection issues, locks |

---

## Diagnostic Commands Summary

```bash
# Full diagnostics
./scripts/ops/diagnostics/db_diagnostics.sh

# Quick JSON status
./scripts/ops/diagnostics/db_diagnostics.sh --json

# Shadow simulation status
./scripts/stress/check_shadow_status.sh

# Load test (caution in prod)
python backend/scripts/load_test_approvals.py --concurrent 10 --total 50
```

---

## Escalation Matrix

| Severity | Response Time | Who to Page |
|----------|---------------|-------------|
| SEV1 (outage) | 15 min | Platform + DB on-call |
| SEV2 (degraded) | 1 hour | Platform on-call |
| SEV3 (minor) | Next business day | Ticket |

---

*Generated: 2025-12-03 | M5 Policy API v1.0*
