# RBAC Incident Response Runbook

**Last Updated:** 2025-12-05

## Quick Reference

### Rollback Commands

```bash
# Scripted rollback (preferred)
./scripts/ops/rbac_enable.sh disable

# Manual rollback
sed -i 's/RBAC_ENFORCE=true/RBAC_ENFORCE=false/' /root/agenticverz2.0/.env
docker compose up -d backend

# Verify rollback
curl -s http://127.0.0.1:8000/api/v1/rbac/info | jq '.enforce_mode'
# Should return: false
```

### DB Restore (Last Resort)

```bash
pg_restore -d "postgresql://nova:novapass@localhost:6432/nova_aos" \
  /root/agenticverz2.0/backups/m7_pre_enable_20251205T052016Z.dump
```

---

## Incident Types

### INC-1: Mass Unauthorized Denials

**Symptoms:**
- `rbac_decisions_total{decision="denied"}` spiking
- Automation failing with 403 errors
- On-call alerts firing

**Triage:**

```bash
# Check recent denials
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "
  SELECT subject, resource, action, reason, COUNT(*)
  FROM system.rbac_audit
  WHERE allowed = false AND ts > now() - interval '15 minutes'
  GROUP BY 1,2,3,4 ORDER BY 5 DESC LIMIT 10;
"
```

**Resolution:**

1. If `reason = 'no-credentials'`:
   - Check if MACHINE_SECRET_TOKEN is set in container env
   - Verify token matches `.env` value
   - Check client is sending `X-Machine-Token` header

2. If `reason = 'insufficient-permissions'`:
   - Check RBAC policy matrix for missing permission
   - If legitimate access needed, update policy and hot-reload

3. If widespread/unclear, **rollback immediately**:
   ```bash
   ./scripts/ops/rbac_enable.sh disable
   ```

---

### INC-2: RBAC Audit Write Failures

**Symptoms:**
- `rbac_audit_writes_total{status="error"}` incrementing
- Logs show "Failed to write audit log"

**Triage:**

```bash
# Check error count
curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="error"}'

# Check recent errors in logs
docker logs nova_agent_manager 2>&1 | grep -i "audit" | tail -20
```

**Known Causes:**

| Error Message | Cause | Fix |
|---------------|-------|-----|
| `'generator' object has no attribute 'execute'` | Session factory is generator | Fixed in session 2 - update code |
| `connection refused` | DB down | Check PgBouncer/PostgreSQL |
| `permission denied` | Missing INSERT on rbac_audit | Grant: `GRANT INSERT ON system.rbac_audit TO nova` |

**Resolution:**

1. If DB issue, fix database connectivity first
2. If code issue, deploy fix and restart
3. Audit write failures don't block requests - not critical for rollback

---

### INC-3: Memory Pin Operation Failures

**Symptoms:**
- `memory_pins_operations_total{status="error"}` incrementing
- Agents reporting context injection failures

**Triage:**

```bash
# Check error metrics
curl -s http://127.0.0.1:8000/metrics | grep 'memory_pins_operations_total'

# Check memory_audit for failures
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "
  SELECT ts, operation, tenant_id, key, error_message
  FROM system.memory_audit
  WHERE error_message IS NOT NULL
  ORDER BY ts DESC LIMIT 10;
"
```

**Resolution:**

1. If RBAC-related (403s), check machine token
2. If DB-related, check PgBouncer pool and PostgreSQL
3. If Redis-related (cache), check Redis connection - fallback to DB should work

---

### INC-4: Hot-Reload Failure

**Symptoms:**
- Policy changes not taking effect
- `rbac_policy_loads_total{status="error"}` incrementing

**Triage:**

```bash
# Check policy info
curl -s -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" \
  http://127.0.0.1:8000/api/v1/rbac/info | jq .

# Try manual reload
curl -X POST -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" \
  http://127.0.0.1:8000/api/v1/rbac/reload
```

**Resolution:**

1. Check policy file syntax if using external policy file
2. Restart backend to force reload: `docker compose restart backend`

---

## Monitoring Queries

### Key Metrics Dashboard

```promql
# RBAC decision rate
rate(rbac_decisions_total[5m])

# Denial ratio (alert if > 0.1)
sum(rate(rbac_decisions_total{decision="denied"}[5m])) /
sum(rate(rbac_decisions_total[5m]))

# Audit write error rate
rate(rbac_audit_writes_total{status="error"}[5m])

# Memory operation error rate
rate(memory_pins_operations_total{status="error"}[5m])
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Denial ratio | > 5% | > 20% |
| Audit errors/min | > 1 | > 10 |
| Memory errors/min | > 1 | > 10 |

---

## Escalation

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| P0 - Mass outage | Immediate | Rollback first, investigate after |
| P1 - Partial degradation | 15 min | On-call engineer |
| P2 - Single component | 1 hour | Next business day if after hours |

---

## Post-Incident

1. Capture metrics snapshot before fix
2. Document root cause
3. Update this runbook if new failure mode
4. Add monitoring/alerting for the failure mode
5. Schedule blameless postmortem if P0/P1

---

## Related

- [PIN-032: M7 RBAC Enablement](../memory-pins/PIN-032-m7-rbac-enablement.md)
- [Memory Pin Cleanup](./MEMORY_PIN_CLEANUP.md)
- Rollback script: `scripts/ops/rbac_enable.sh disable`
