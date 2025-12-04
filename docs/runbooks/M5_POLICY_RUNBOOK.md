# M5 Policy API Runbook

**Service:** AOS Policy API
**Owner:** Platform Team
**Last Updated:** 2025-12-03

---

## Quick Reference

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Service health check |
| `POST /api/v1/policy/eval` | Sandbox policy evaluation |
| `POST /api/v1/policy/requests` | Create approval request |
| `GET /api/v1/policy/requests/{id}` | Get request status |
| `POST /api/v1/policy/requests/{id}/approve` | Approve request |
| `POST /api/v1/policy/requests/{id}/reject` | Reject request |
| `GET /api/v1/policy/requests?status=pending` | List pending requests |

---

## Health Checks

```bash
# API health
curl -s http://127.0.0.1:8000/health | jq .

# Pending approvals count
curl -s "http://127.0.0.1:8000/api/v1/policy/requests?status=pending" | jq 'length'

# DB connection check
docker exec nova_agent_manager python -c "from app.db import engine; print(engine.pool.status())"
```

---

## Key Metrics to Monitor

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| `nova_policy_decisions_total{decision="deny"}` | >10% of total | Policy denials |
| `nova_capability_violations_total` | >5/min | Capability violations |
| `nova_approval_requests_pending` | >100 backlog | Pending approval queue |
| `nova_webhook_failures_total` | >3 consecutive | Webhook delivery failures |
| `pg_stat_activity{state="active"}` | >40 connections | DB connection saturation |

---

## Escalation Cron

**Schedule:** Every minute
**Log:** `/var/log/aos/escalation.log`

```bash
# Check cron status
crontab -l | grep escalation

# View recent logs
tail -f /var/log/aos/escalation.log

# Manual run
docker exec nova_agent_manager python /app/scripts/run_escalation.py
```

---

## Common Issues & Fixes

### 1. Connection Pool Exhaustion

**Symptom:** `QueuePool limit reached, connection timed out`

**Fix:**
```bash
# Current pool status
docker exec nova_agent_manager python -c "from app.db import engine; print(engine.pool.status())"

# Restart backend (clears pool)
docker compose restart backend
```

### 2. Approval Backlog Growing

**Symptom:** Many pending requests, escalation not running

**Fix:**
```bash
# Check escalation cron
grep escalation /var/log/syslog | tail -20

# Manual escalation run
docker exec nova_agent_manager python /app/scripts/run_escalation.py

# Check pending count
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT status, COUNT(*) FROM approval_requests GROUP BY status;"
```

### 3. Webhook Delivery Failures

**Symptom:** `webhook_attempts` increasing, `last_webhook_status` shows errors

**Fix:**
```bash
# Check failed webhooks
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT id, webhook_url, webhook_attempts, last_webhook_status FROM approval_requests WHERE webhook_attempts > 0 AND last_webhook_status != 'success' LIMIT 10;"

# Disable webhooks temporarily (update requests)
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "UPDATE approval_requests SET webhook_url = NULL WHERE status = 'pending';"
```

---

## Emergency Procedures

### Disable Auto-Approve

```bash
# Set all policies to require manual approval
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "UPDATE policy_approval_levels SET approval_level = 'manual_approve';"

docker compose restart backend
```

### Pause Escalation Worker

```bash
# Remove from crontab temporarily
crontab -l | grep -v escalation | crontab -

# Re-enable later
(crontab -l; echo "* * * * * docker exec nova_agent_manager python /app/scripts/run_escalation.py >> /var/log/aos/escalation.log 2>&1") | crontab -
```

### Mass Reject Pending Requests

```bash
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "UPDATE approval_requests SET status = 'rejected', resolved_at = NOW() WHERE status = 'pending';"
```

### Rollback Migration

```bash
docker exec nova_agent_manager python -m alembic downgrade -1
docker compose restart backend
```

---

## Database Queries

```bash
# Request status distribution
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT status, COUNT(*) FROM approval_requests GROUP BY status;"

# Recent requests with audit trail
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT id, status, status_history_json, created_at FROM approval_requests ORDER BY created_at DESC LIMIT 10;"

# Table size
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT pg_size_pretty(pg_total_relation_size('approval_requests'));"

# Check indexes
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT indexname FROM pg_indexes WHERE tablename = 'approval_requests';"
```

---

## Load Test

```bash
cd /root/agenticverz2.0/backend

# Light load (baseline)
python scripts/load_test_approvals.py --concurrent 10 --total 50

# Heavy load (stress test)
python scripts/load_test_approvals.py --concurrent 50 --total 200
```

**Pass Criteria:**
- Success rate >= 99%
- p95 latency < 500ms

---

## Contacts

| Role | Contact |
|------|---------|
| Platform On-Call | #platform-oncall |
| Policy Owner | @policy-team |
| SRE Lead | @sre-lead |

---

## Prometheus Alerts

| Alert | Severity | Action |
|-------|----------|--------|
| `M5ApprovalBacklogHigh` | warning | Check escalation cron |
| `M5PolicyDenyRateHigh` | warning | Review policy config |
| `M5WebhookDeliveryFailing` | warning | Check webhook endpoints |
| `M5CapabilityViolationSpike` | critical | Investigate skill access |
| `M5BudgetRejectionSpike` | critical | Review budget limits |
