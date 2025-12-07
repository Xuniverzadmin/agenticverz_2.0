# Memory Pin Cleanup Runbook

**Last Updated:** 2025-12-05

## Overview

Memory pins are persistent key-value storage for agent context. The `machine` role intentionally lacks `delete` permission to maintain least privilege. This runbook covers cleanup procedures.

## Who Can Delete Memory Pins

| Role | Can Delete | Use Case |
|------|------------|----------|
| `infra` | ✅ Yes | Infrastructure maintenance |
| `admin` | ✅ Yes | Administrative cleanup |
| `machine` | ❌ No | Automation - use TTL instead |
| `dev` | ❌ No | Development - read-only |
| `readonly` | ❌ No | Monitoring only |

## Cleanup Methods

### Method 1: TTL-Based Expiration (Preferred for Automation)

Set `ttl_seconds` when creating pins - they auto-expire:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/memory/pins \
  -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "my-tenant",
    "key": "temp:session:123",
    "value": {"data": "temporary"},
    "ttl_seconds": 3600
  }'
```

TTL cleanup job runs hourly via cron.

### Method 2: Manual Delete (Admin/Infra Only)

Using admin JWT or infra credentials:

```bash
# Delete single pin
curl -X DELETE "http://127.0.0.1:8000/api/v1/memory/pins/my:key?tenant_id=my-tenant" \
  -H "Authorization: Bearer $ADMIN_JWT"

# Bulk cleanup via psql (emergency only)
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "
  DELETE FROM system.memory_pins
  WHERE tenant_id = 'cleanup-tenant'
  AND key LIKE 'temp:%';
"
```

### Method 3: Expired Pin Cleanup

Run the TTL expiration job manually:

```bash
./scripts/ops/expire_memory_pins.sh
```

## Common Cleanup Scenarios

### Scenario: Test Data Cleanup

```bash
# List test tenant pins
curl -s "http://127.0.0.1:8000/api/v1/memory/pins?tenant_id=test-tenant&limit=100" \
  -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" | jq '.pins[].key'

# Delete via admin (requires admin JWT)
for key in $(curl -s ... | jq -r '.pins[].key'); do
  curl -X DELETE "http://127.0.0.1:8000/api/v1/memory/pins/$key?tenant_id=test-tenant" \
    -H "Authorization: Bearer $ADMIN_JWT"
done
```

### Scenario: Orphaned Pins (No Active Tenant)

```sql
-- Find orphaned pins (tenant not in active list)
SELECT tenant_id, COUNT(*)
FROM system.memory_pins
WHERE tenant_id NOT IN (SELECT id FROM tenants WHERE active = true)
GROUP BY tenant_id;

-- Delete orphaned (after review)
DELETE FROM system.memory_pins
WHERE tenant_id NOT IN (SELECT id FROM tenants WHERE active = true);
```

### Scenario: Emergency Bulk Cleanup

```bash
# Backup first
pg_dump -h localhost -p 6432 -U nova -Fc nova_aos -t 'system.memory_pins' \
  > /root/agenticverz2.0/backups/memory_pins_backup_$(date +%Y%m%d).dump

# Then delete
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "
  DELETE FROM system.memory_pins WHERE created_at < now() - interval '90 days';
"
```

## Monitoring

Check for pins approaching cleanup thresholds:

```sql
-- Pins by age
SELECT
  DATE_TRUNC('day', created_at) as day,
  COUNT(*) as count
FROM system.memory_pins
GROUP BY 1 ORDER BY 1 DESC LIMIT 30;

-- Expired but not cleaned
SELECT COUNT(*) FROM system.memory_pins
WHERE expires_at IS NOT NULL AND expires_at < now();
```

## Related

- [PIN-032: M7 RBAC Enablement](../memory-pins/PIN-032-m7-rbac-enablement.md)
- TTL cleanup script: `scripts/ops/expire_memory_pins.sh`
- Cron config: `scripts/ops/cron/aos-maintenance.cron`
