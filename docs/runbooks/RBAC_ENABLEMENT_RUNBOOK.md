# RBAC Enablement Runbook

**Status:** Production Ready
**Last Updated:** 2025-12-05
**Related PINs:** PIN-031 (M7 Memory Integration)

---

## Overview

This runbook provides step-by-step instructions for enabling RBAC enforcement safely in staging/production environments.

**Key Scripts:**
- `scripts/ops/rbac_enable.sh` - Main enablement script
- `scripts/ops/rbac_enable_smoke.sh` - Smoke test suite
- `monitoring/rules/m7_rbac_memory_alerts.yml` - Prometheus alert rules

---

## Quick Start

```bash
# Full enablement sequence (interactive)
./scripts/ops/rbac_enable.sh full

# Or step-by-step:
./scripts/ops/rbac_enable.sh preflight  # Check prerequisites
./scripts/ops/rbac_enable.sh backup     # Backup database
./scripts/ops/rbac_enable.sh enable     # Enable RBAC_ENFORCE=true
./scripts/ops/rbac_enable.sh smoke      # Run smoke tests
./scripts/ops/rbac_enable.sh verify     # Verify audit entries

# Emergency rollback
./scripts/ops/rbac_enable.sh disable
```

---

## Important Schema Notes

**CORRECTED:** The original instructions referenced incorrect table names. Here are the correct schemas:

| Original Instruction | Correct Schema |
|---------------------|----------------|
| `auth.rbac_audit` | `system.rbac_audit` |
| `principal_id` column | `subject` column |
| `reason='not_permitted'` | `reason='insufficient-permissions'` |

---

## Section A: RBAC Enforcement Workflow

### A1: Verify Machine Token Access

```bash
# With MACHINE_SECRET_TOKEN set
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/api/v1/memory/pins \
  -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","key":"emergency_test","value":{"x":1}}'
```

**Expected:** `200` or `201`

### A2: Enable RBAC_ENFORCE=true

```bash
# Via script (recommended)
./scripts/ops/rbac_enable.sh enable

# Or manually
echo "RBAC_ENFORCE=true" >> .env
docker compose up -d backend
```

### A3: Verify Unauthorized Access Blocked

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","key":"forbidden","value":{}}'
```

**Expected:** `403` (when RBAC_ENFORCE=true)

### A4: Pre-conditions

Before enabling RBAC:

1. **Emergency Admin Token in Vault** (or accessible)
2. **Database credentials documented** (for emergency unblocking)
3. **Rollback command prepared** (see Section F)

---

## Section B: RBAC Audit Verification

**CORRECTED SQL (uses `system.rbac_audit`, `subject` column):**

```sql
SELECT ts, subject, resource, action, allowed, reason
FROM system.rbac_audit
ORDER BY ts DESC
LIMIT 20;
```

### Expected Results:

| subject | resource | action | allowed | reason |
|---------|----------|--------|---------|--------|
| machine | memory_pin | write | true | role:machine |
| unknown | memory_pin | write | false | insufficient-permissions |

**If table is empty:** RBAC audit logging may not be wired. Check `RBAC_AUDIT_ENABLED=true`.

---

## Section C: Memory Audit Verification

```sql
SELECT ts, operation, tenant_id, key, success, new_value_hash, latency_ms
FROM system.memory_audit
ORDER BY ts DESC
LIMIT 20;
```

### Expected:

| operation | success | new_value_hash | latency_ms |
|-----------|---------|----------------|------------|
| upsert | true | a1b2c3d4e5f6g7h8 | 12.5 |
| get | true | NULL | 3.2 |
| delete | true | NULL | 8.1 |

**Privacy check:** `new_value_hash` should be 16 characters (SHA256 prefix), NOT full JSON.

---

## Section D: TTL Expiration Verification

### Dry Run:

```bash
./scripts/ops/expire_memory_pins.sh --dry-run
```

### Run Cleanup:

```bash
./scripts/ops/expire_memory_pins.sh
```

### Validate No Expired Pins:

```sql
SELECT count(*)
FROM system.memory_pins
WHERE expires_at IS NOT NULL
AND expires_at < now();
```

**Expected:** `0`

### Install Cron Job:

```bash
crontab scripts/ops/cron/aos-maintenance.cron
crontab -l  # Verify
```

---

## Section E: CostSim Memory Integration Test

### Step 1: Baseline (no memory)

```bash
curl -s -X POST http://localhost:8000/costsim/v2/simulate \
  -H "Content-Type: application/json" \
  -d '{"plan":[{"skill":"noop","params":{}}],
       "budget_cents":1000,
       "tenant_id":"test",
       "workflow_id":"w1",
       "inject_memory":false}' \
  | jq > baseline.json
```

### Step 2: With Memory Injection

```bash
curl -s -X POST http://localhost:8000/costsim/v2/simulate \
  -H "Content-Type: application/json" \
  -d '{"plan":[{"skill":"noop","params":{}}],
       "budget_cents":1000,
       "tenant_id":"test",
       "workflow_id":"w1",
       "inject_memory":true}' \
  | jq > with_memory.json
```

### Step 3: Verify Memory Context Keys

```bash
jq '.memory_context_keys' with_memory.json
# Expected: ["config", "cost_history", ...] or null if no context
```

---

## Section F: Rollback & Operational Safeguards

### F1: Soft Rollback (Disable RBAC)

```bash
# Via script
./scripts/ops/rbac_enable.sh disable

# Manual (docker-compose)
sed -i 's/RBAC_ENFORCE=true/RBAC_ENFORCE=false/' .env
docker compose up -d backend

# Manual (systemd)
sudo sed -i 's/RBAC_ENFORCE=true/RBAC_ENFORCE=false/' /opt/agenticverz/.env
sudo systemctl restart agenticverz-backend
```

### F2: Database Snapshot

```bash
# Via script
./scripts/ops/rbac_enable.sh backup

# Manual
pg_dump -Fc "$DATABASE_URL" \
  -f /tmp/m7_pre_enable_$(date -u +"%Y%m%dT%H%M%SZ").dump
```

### F3: Prometheus Alerts

Install M7 alert rules:

```bash
cp monitoring/rules/m7_rbac_memory_alerts.yml /etc/prometheus/rules/
curl -X POST http://localhost:9090/-/reload
```

Key alerts:
- `RBACDeniedAnomaly` - >5 denials in 5 minutes
- `MemoryPinOperationFailed` - Memory operation failures
- `MemoryDriftScoreHigh` - Drift score > 0.3

---

## Section G: Enablement Timeline

### T-15 minutes: Pre-check

```bash
./scripts/ops/rbac_enable.sh preflight
./scripts/ops/rbac_enable.sh backup
```

### T-10 minutes: Enable on ONE instance

```bash
RBAC_ENFORCE=true docker compose up -d backend
```

### T+2 minutes: Smoke tests

```bash
./scripts/ops/rbac_enable_smoke.sh
```

### T+30 minutes: Monitor

Watch for:
- `rbac_engine_decisions_total{decision="denied"}`
- `memory_pins_operations_total{status="error"}`
- API latency anomalies

### If Stable 1-2 hours: Roll out to remaining nodes

### If Stable 24 hours: Schedule production rollout

---

## Section H: Verification One-Liners

```bash
# RBAC audit count
psql "$DATABASE_URL" -c "SELECT count(*) FROM system.rbac_audit;"

# Memory audit recent entries
psql "$DATABASE_URL" -c \
  "SELECT ts, operation, tenant_id, key
   FROM system.memory_audit ORDER BY ts DESC LIMIT 10;"

# Expired pins check
psql "$DATABASE_URL" -c \
  "SELECT count(*) FROM system.memory_pins
   WHERE expires_at IS NOT NULL AND expires_at < now();"

# Prometheus metrics
curl -sS http://localhost:8000/metrics \
  | grep -E 'rbac_engine_decisions_total|memory_pins_operations_total' | head
```

---

## Troubleshooting

### RBAC Denials Not Logged

1. Check `RBAC_AUDIT_ENABLED=true` in environment
2. Verify database connectivity from backend
3. Check `system.rbac_audit` table exists

### Machine Token Not Working

1. Verify `MACHINE_SECRET_TOKEN` is set in backend environment
2. Use `X-Machine-Token` header (not `Authorization: Bearer`)
3. Check RBAC policy has `machine` role with required permissions

### Memory Audit Missing Value Hashes

1. Check `write_memory_audit()` is called in API endpoints
2. Verify SHA256 hashing is working (not base64)
3. Ensure `success=true` entries have hashes for upserts

---

## Related Files

| File | Purpose |
|------|---------|
| `scripts/ops/rbac_enable.sh` | Main enablement script |
| `scripts/ops/rbac_enable_smoke.sh` | Smoke test suite |
| `monitoring/rules/m7_rbac_memory_alerts.yml` | Prometheus alerts |
| `backend/app/auth/rbac_engine.py` | RBAC implementation |
| `backend/app/config/rbac_policies.json` | Policy matrix |
| `scripts/ops/expire_memory_pins.sh` | TTL cleanup |
| `scripts/ops/cron/aos-maintenance.cron` | Cron configuration |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-05 | Created runbook with corrected SQL schemas |
| 2025-12-05 | Added smoke test and enablement scripts |
| 2025-12-05 | Added M7 Prometheus alert rules |
