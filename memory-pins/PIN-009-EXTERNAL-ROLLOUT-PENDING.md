# PIN-009: Pending To-Do for External Rollout

> **Created:** 2025-12-04
> **Status:** ACTIVE
> **Priority:** HIGH (before external/production rollout)
> **Last Updated:** 2025-12-04
> **Related:** PIN-023 (Consistency Analysis)

---

## Strategic Context (PIN-023 Review)

**IMPORTANT:** This PIN tracks operational readiness for the "M5 Policy API" deployment. However, PIN-023 identified significant drift from the original machine-native vision (PIN-005).

### Current Label vs Vision

| Label | Actual State |
|-------|--------------|
| "M5 GA" | Policy API + Approval Workflow deployed |
| Machine-Native | **NOT READY** - core APIs not exposed |

### What's Missing for True GA (PIN-023)

| Component | Status | Impact |
|-----------|--------|--------|
| `runtime.simulate()` | NOT BUILT | Agents can't evaluate plans before execution |
| `runtime.query()` API | INTERNAL ONLY | Agents can't query capabilities |
| CLI (`aos simulate`) | MISSING | No demo of machine-native behavior |
| Python SDK | BROKEN | External integrations blocked |

### Recommended Path

1. **Complete this PIN** - Operational GA prerequisites
2. **Implement M5.5** - Machine-native API exposure (see PIN-023)
3. **Fix SDK** - Before external rollout
4. **Then label as GA** - When 60-second demo works

---

## Purpose

This PIN tracks all items that MUST be completed before M5 Policy API can be rolled out to external users or production environments. Items are categorized by priority and include specific acceptance criteria.

**Note:** This achieves "Operational GA" - see PIN-023 for "Machine-Native GA" requirements.

---

## Blocking Items (Must Complete Before External Rollout)

### 1. Wire RBAC to Real Auth Service

| Field | Value |
|-------|-------|
| **Priority** | CRITICAL |
| **Current State** | Stub returning mock roles (team_member, level 3) |
| **Risk if Deferred** | Unauthorized actions, compliance/security violations |
| **Owner** | Platform Team |

**Requirements:**
- [ ] Deploy external auth service or auth-stub
- [ ] Configure `AUTH_SERVICE_URL` with real endpoint
- [ ] Provide API credentials if required
- [ ] Run RBAC smoke tests with real auth
- [ ] Verify 403 responses for unauthorized actors
- [ ] Test level 5 (owner override) audit logging

**Acceptance Criteria:**
```bash
# Must return 403 for insufficient permissions
curl -X POST http://localhost:8000/api/v1/policy/requests/{id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "low_level_user", "level": 5}'
# Expected: HTTP 403 with authorization_denied error
```

**Files Affected:**
- `backend/app/api/policy.py:745-783`
- `backend/app/auth/rbac.py`
- `.env` (AUTH_SERVICE_URL)

---

### 2. ~~Switch DATABASE_URL to PgBouncer~~ COMPLETED

| Field | Value |
|-------|-------|
| **Priority** | ~~CRITICAL~~ **DONE** |
| **Current State** | ~~Backend connects directly to Postgres:5433~~ **Switched to PgBouncer:6432** |
| **Risk if Deferred** | ~~Connection exhaustion under load, p95 latency issues~~ N/A |
| **Owner** | Platform Team |
| **Completed** | 2025-12-04 |

**Requirements:**
- [x] Verify PgBouncer is healthy on port 6432
- [x] Take database backup before switch
- [x] Update `DATABASE_URL` to `postgresql://nova:novapass@localhost:6432/nova_aos`
- [x] Restart backend and worker services
- [x] Run load test (20 concurrent connections - PASSED)
- [x] Verify backend healthy after switch

**Acceptance Criteria:**
```bash
# Connection through PgBouncer works
PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos -c "SELECT 1"

# Backend health check passes
curl -s http://localhost:8000/health | jq .status
# Expected: "healthy"
```

**Configuration Change:**
```bash
# In .env, change:
DATABASE_URL=postgresql://nova:novapass@localhost:5433/nova_aos
# To:
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
```

---

### 3. Secure Webhook Keys & Enable Rotation

| Field | Value |
|-------|-------|
| **Priority** | HIGH |
| **Current State** | File-based key at `/var/lib/aos/webhook-keys/v1` |
| **Risk if Deferred** | Key compromise, rotation cumbersome |
| **Owner** | Security Team |

**Requirements:**
- [ ] Verify key file permissions are 600
- [ ] Test key rotation script in dry-run mode
- [ ] Document rotation procedure
- [ ] (Optional) Configure Vault or AWS SSM backend
- [ ] Test webhook signature verification at receiver

**For Production (Choose One):**

**Option A: Vault Backend**
```bash
export VAULT_ADDR="https://vault.example.com"
export VAULT_TOKEN="<token>"
./scripts/ops/webhook/rotate_webhook_key.sh --backend vault
```

**Option B: AWS SSM Backend**
```bash
export AWS_REGION="us-east-1"
./scripts/ops/webhook/rotate_webhook_key.sh --backend ssm
```

**Option C: File Backend (Current)**
```bash
# Ensure permissions
chmod 600 /var/lib/aos/webhook-keys/v1
chown root:root /var/lib/aos/webhook-keys/v1
```

---

### 4. Ensure Redis is Available for Rate Limiting

| Field | Value |
|-------|-------|
| **Priority** | HIGH |
| **Current State** | System Redis running, fail-open mode available |
| **Risk if Deferred** | No enforced rate limits, abuse risk |
| **Owner** | Platform Team |

**Requirements:**
- [ ] Verify Redis connectivity
- [ ] Configure `REDIS_URL` in environment
- [ ] Test rate limiter with burst traffic
- [ ] Verify 429 responses when limit exceeded

**Acceptance Criteria:**
```bash
# Redis responds
redis-cli ping
# Expected: PONG

# Rate limit triggers (after 60 requests/min)
for i in {1..70}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    "http://localhost:8000/api/v1/policy/eval" \
    -H "Content-Type: application/json" \
    -d '{"skill_id":"test","tenant_id":"test","payload":{}}'
done | grep 429
# Expected: Some 429 responses after limit exceeded
```

---

### 5. Database Backup & Restore Verification

| Field | Value |
|-------|-------|
| **Priority** | CRITICAL |
| **Current State** | Backup created at deployment, restore untested |
| **Risk if Deferred** | Data loss risk, unverified recovery |
| **Owner** | DBA / Platform Team |

**Requirements:**
- [ ] Take full database backup
- [ ] Restore to test database
- [ ] Verify data integrity
- [ ] Document recovery procedure
- [ ] Set up automated backup schedule

**Commands:**
```bash
# Create backup
docker exec nova_db pg_dump -U nova -Fc nova_aos > /root/agenticverz2.0/backups/nova_aos_$(date +%Y%m%d).dump

# Restore to test database (on separate instance)
docker exec -i nova_db pg_restore -U nova -d nova_aos_test < backup.dump

# Verify tables exist
docker exec nova_db psql -U nova -d nova_aos_test -c "\dt"
```

---

### 6. Prometheus Alert Lifecycle

| Field | Value |
|-------|-------|
| **Priority** | MEDIUM |
| **Current State** | Lifecycle API disabled, restart required for rule changes |
| **Risk if Deferred** | Operational friction, slower alert updates |
| **Owner** | SRE Team |

**Requirements:**
- [ ] Enable `--web.enable-lifecycle` flag OR
- [ ] Document restart-based workflow for rule changes
- [ ] Verify M5 alert rules are loaded
- [ ] Test at least one alert fires correctly

**To Enable Lifecycle API:**
```yaml
# In docker-compose.yml, prometheus command section add:
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.path=/prometheus'
  - '--web.listen-address=127.0.0.1:9090'
  - '--web.enable-lifecycle'  # ADD THIS LINE
```

**Verification:**
```bash
# Check alert rules loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].name' | grep m5

# Test reload (after enabling lifecycle)
curl -X POST http://localhost:9090/-/reload
```

---

### 7. PgBouncer Auth Hardening

| Field | Value |
|-------|-------|
| **Priority** | MEDIUM |
| **Current State** | `auth_type=any` (trusts all connections) |
| **Risk if Deferred** | Unauthorized database access if network breached |
| **Owner** | Security Team |

**Requirements:**
- [ ] Create `userlist.txt` with MD5 hashed passwords
- [ ] Change `auth_type` from `any` to `md5`
- [ ] Test connection with credentials
- [ ] Verify unauthorized connections rejected

**Configuration:**
```ini
# In config/pgbouncer/pgbouncer.ini
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
```

**userlist.txt format:**
```
"nova" "md5<hash_of_password>"
```

---

## High Priority (Complete Before Scale)

### 8. Load Test Validation

| Field | Value |
|-------|-------|
| **Priority** | HIGH |
| **Current State** | Not tested at scale |
| **Target** | 30+ concurrent connections, p95 < 500ms |

**Requirements:**
- [ ] Run stress test with 30+ workers
- [ ] Measure p50/p95/p99 latencies
- [ ] Verify no connection pool exhaustion
- [ ] Check Prometheus metrics during load

**Script:**
```bash
# Using existing stress test infrastructure
STRESS_WORKERS=30 STRESS_OPS_PER_WORKER=100 \
  /root/agenticverz2.0/scripts/stress/run_stress_test.sh
```

---

### 9. Archival Job Verification

| Field | Value |
|-------|-------|
| **Priority** | MEDIUM |
| **Current State** | Script exists, 7-day verification pending |

**Requirements:**
- [ ] Run archival job for 7 days
- [ ] Verify completed runs are archived
- [ ] Test `all_approval_requests` audit view
- [ ] Confirm retention policy works

---

## Medium Priority (Complete Before GA)

### 10. Grafana Dashboards

| Field | Value |
|-------|-------|
| **Priority** | MEDIUM |
| **Current State** | Provisioning configured, no M5 dashboards |

**Requirements:**
- [ ] Create M5 Policy dashboard
- [ ] Create Approval Workflow dashboard
- [ ] Add budget/cost tracking panels
- [ ] Import or create on-call dashboard

---

### 11. Fix PgBouncer Health Check

| Field | Value |
|-------|-------|
| **Priority** | LOW |
| **Current State** | Uses `pg_isready` which isn't in container |

**Fix in docker-compose.yml:**
```yaml
# Change from:
healthcheck:
  test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -p 6432 -U nova || exit 1"]
# To:
healthcheck:
  test: ["CMD-SHELL", "nc -z 127.0.0.1 6432 || exit 1"]
```

---

## Low Priority (Post-GA)

| Item | Notes |
|------|-------|
| Pydantic V2 migration | 10 deprecation warnings, non-blocking |
| pytest-asyncio integration | For async test support |
| Push to GitHub | Enable CI/CD |
| Kubernetes monitoring manifests | For K8s deployments |

---

## Environment Variables Checklist

```bash
# CRITICAL - Must be set before external rollout
AUTH_SERVICE_URL=<real-auth-service>     # Currently: http://localhost:8001 (stub)
DATABASE_URL=<pgbouncer-url>             # Switch to port 6432
REDIS_URL=redis://localhost:6379/0       # Verify Redis available
RBAC_ENABLED=true                        # Already set

# HIGH - Should be set
WEBHOOK_KEYS_PATH=/var/lib/aos/webhook-keys
WEBHOOK_KEY_VERSION=v1
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT_RPM=60

# MEDIUM - Recommended
AUTH_SERVICE_TIMEOUT=5.0
M5_SIGNOFF_PATH=/root/agenticverz2.0/.m5_signoff
```

---

## Quick Deployment Checklist

Before external rollout, run these commands in order:

```bash
# 1. Take backup
docker exec nova_db pg_dump -U nova -Fc nova_aos > backups/pre_rollout_$(date +%Y%m%d).dump

# 2. Verify Redis
redis-cli ping

# 3. Verify PgBouncer
nc -zv 127.0.0.1 6432

# 4. Switch to PgBouncer (after backup)
sed -i 's/:5433/:6432/' /root/agenticverz2.0/.env

# 5. Restart services
cd /root/agenticverz2.0 && docker compose up -d --force-recreate backend worker

# 6. Verify health
curl -s http://localhost:8000/health

# 7. Run smoke tests
/root/agenticverz2.0/scripts/smoke/rbac_smoke.sh

# 8. Check Prometheus alerts
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | length'

# 9. Verify signoff exists
cat /root/agenticverz2.0/.m5_signoff
```

---

## Recommended Learning Path (Low-Friction Sequence)

Follow this sequence to learn and stage components safely before production cutover:

### Phase 1: Current State (Safe to Learn)
```
┌─────────────────────────────────────────────────────────────┐
│  RBAC stub active (mock roles)           ✅ DONE            │
│  PgBouncer deployed (not yet primary)    ✅ DONE            │
│  Webhook keys (file backend)             ✅ DONE            │
│  Redis available (system Redis)          ✅ DONE            │
│  Rate limiter enabled (fail-open ok)     ✅ DONE            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Testing & Validation (Do This Next)

**Step 1: Test RBAC Logic with Stub**
```bash
# RBAC is enabled but uses mock roles - safe to test logic
curl -X POST http://localhost:8000/api/v1/policy/requests \
  -H "Content-Type: application/json" \
  -d '{
    "policy_type": "cost",
    "skill_id": "test_skill",
    "tenant_id": "test_tenant",
    "requested_by": "user123",
    "justification": "Testing RBAC flow"
  }'

# Test approval with different levels
curl -X POST http://localhost:8000/api/v1/policy/requests/{id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "manager1", "level": 4}'
```

**Step 2: Test PgBouncer Connection (Without Switching Production)**
```bash
# Test connection through PgBouncer directly
PGPASSWORD=novapass psql -h 127.0.0.1 -p 6432 -U nova -d nova_aos -c "SELECT 1;"

# Run a simple load test through PgBouncer
for i in {1..50}; do
  PGPASSWORD=novapass psql -h 127.0.0.1 -p 6432 -U nova -d nova_aos \
    -c "SELECT pg_sleep(0.1);" &
done
wait
echo "Load test complete"
```

**Step 3: Test Webhook Rotation Script (Dry Run)**
```bash
# Dry run - no changes made
/root/agenticverz2.0/scripts/ops/webhook/rotate_webhook_key.sh --dry-run --backend file

# Verify current key
cat /var/lib/aos/webhook-keys/v1 | head -c 20
echo "..."
```

**Step 4: Test Rate Limiter**
```bash
# Verify Redis connection
redis-cli ping

# Test rate limiting (should get 429 after ~60 requests)
for i in {1..70}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8000/api/v1/policy/eval \
    -H "Content-Type: application/json" \
    -d '{"skill_id":"test","tenant_id":"rate_test","payload":{}}')
  echo "Request $i: $STATUS"
  [ "$STATUS" = "429" ] && echo "Rate limit hit!" && break
done
```

### Phase 3: Staging Validation

**Step 5: Run Load Test (Before Production Switch)**
```bash
# Run stress test with current configuration
cd /root/agenticverz2.0
STRESS_WORKERS=30 STRESS_OPS_PER_WORKER=50 \
  ./scripts/stress/run_stress_test.sh 2>&1 | tee /tmp/load_test_results.txt

# Check results
grep -E "p50|p95|p99|errors" /tmp/load_test_results.txt
```

**Step 6: Verify Prometheus Alerts Fire**
```bash
# Check alert rules are loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].name'

# Trigger a test condition (optional - be careful in production)
# Example: Check if metrics are being collected
curl -s http://localhost:8000/metrics | grep nova_policy
```

### Phase 4: Production Cutover Window

**When you're comfortable and tests pass, schedule a maintenance window:**

```bash
# === PRODUCTION CUTOVER SCRIPT ===
# Run these commands in sequence during maintenance window

# 1. Notify stakeholders
echo "Starting M5 GA production cutover at $(date)"

# 2. Take database backup
docker exec nova_db pg_dump -U nova -Fc nova_aos > \
  /root/agenticverz2.0/backups/pre_cutover_$(date +%Y%m%d_%H%M%S).dump
echo "Backup complete"

# 3. Switch DATABASE_URL to PgBouncer
sed -i 's/:5433/:6432/' /root/agenticverz2.0/.env
echo "DATABASE_URL updated to use PgBouncer"

# 4. Restart services
cd /root/agenticverz2.0
docker compose up -d --force-recreate backend worker
echo "Services restarted"

# 5. Wait for health
sleep 30
curl -s http://localhost:8000/health | jq .

# 6. Run quick smoke test
./scripts/smoke/rbac_smoke.sh

# 7. Monitor for 15 minutes
echo "Monitoring... check Grafana/Prometheus"
echo "Cutover complete at $(date)"
```

### Phase 5: Real Auth Service (Last Step)

**Do this just before external rollout when you have auth credentials:**

```bash
# 1. Get your auth service URL and credentials
# AUTH_SERVICE_URL=https://auth.yourcompany.com
# AUTH_API_KEY=<your-api-key>

# 2. Update .env
echo "AUTH_SERVICE_URL=https://auth.yourcompany.com" >> /root/agenticverz2.0/.env
# Add any API key config as needed

# 3. Restart backend
docker compose up -d --force-recreate backend worker

# 4. Test with real credentials
curl -X POST http://localhost:8000/api/v1/policy/requests/{id}/approve \
  -H "Authorization: Bearer <real-token>" \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "real_user", "level": 3}'
```

### Progress Tracker

Use this to track your progress through the learning path:

```
[x] Phase 1: Verify current state (RBAC stub, PgBouncer, Redis, webhook keys)
[x] Phase 2, Step 1: Test RBAC with stub (approval requests created, level 5 tested)
[x] Phase 2, Step 2: Test PgBouncer connection (20 concurrent connections - PASSED)
[x] Phase 2, Step 3: Test webhook rotation (dry-run - PASSED)
[x] Phase 2, Step 4: Test rate limiter (6/70 got 429 - PASSED)
[x] Phase 3, Step 5: Run load test (20 concurrent, backend healthy)
[x] Phase 3, Step 6: Verify Prometheus alerts (43 rules loaded, WorkerPoolDown firing)
[x] Phase 4: Production cutover (DATABASE_URL switched to PgBouncer port 6432)
[ ] Phase 5: Wire real auth service (requirements documented, pending auth provider)
```

**Completed:** 2025-12-04
**Auth Requirements Doc:** `/root/agenticverz2.0/docs/AUTH_SERVICE_REQUIREMENTS.md`

---

## Signoff Requirements

Before marking external rollout complete:

- [ ] All CRITICAL items completed
- [ ] All HIGH priority items completed
- [ ] Load test passed with SLA metrics
- [ ] Backup/restore verified
- [ ] On-call runbook reviewed
- [ ] Alerting verified (at least one test alert)
- [ ] Security review completed

**Signoff Command:**
```bash
# After all items complete
echo "External Rollout Approved: $(date -Iseconds)" >> /root/agenticverz2.0/.m5_signoff
echo "Approved by: $(whoami)" >> /root/agenticverz2.0/.m5_signoff
```

---

---

## Machine-Native GA Checklist (From PIN-023) - ✅ COMPLETE

**Status: ALL ITEMS COMPLETE (2025-12-04)**

### M5.5: Machine-Native API Exposure - ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Implement `runtime.simulate()` | ✅ DONE | `POST /api/v1/runtime/simulate` working |
| Expose runtime query API | ✅ DONE | `POST /api/v1/runtime/query` working |
| Expose capabilities API | ✅ DONE | `GET /api/v1/runtime/capabilities` working |
| Build `aos` CLI | ✅ DONE | `/usr/local/bin/aos` with simulate, skills, capabilities, query |
| Add composition_hints to skills | ✅ DONE | Included in `/api/v1/runtime/skills/{id}` |
| Fix Python SDK | ✅ DONE | 10/10 tests passing, machine-native methods added |

### 60-Second Demo Readiness - ✅ VERIFIED

```
Goal: "Fetch BTC price and notify on Slack"

Required capabilities:
[x] Workflow execution (M4)
[x] Failure as data (StructuredOutcome)
[x] Retry with backoff (catalog-driven)
[x] Agent queries capabilities - /api/v1/runtime/capabilities
[x] Agent simulates plan - /api/v1/runtime/simulate
[x] CLI demonstration - aos simulate, aos capabilities
```

**Demo commands:**
```bash
# Query capabilities
aos capabilities
# Shows 7 skills with costs, latency, rate limits

# Simulate plan
aos simulate --plan '[{"skill": "http_call", "params": {"url": "https://api.coingecko.com/..."}}, {"skill": "json_transform", "params": {"query": ".bitcoin.usd"}}, {"skill": "webhook_send", "params": {"url": "https://hooks.slack.com/..."}}]' --budget 100
# Shows: FEASIBLE, 0c cost, 810ms latency, TIMEOUT risks
```

### Exit Criteria for True GA - ✅ ALL MET

- [x] 60-second demo from PIN-005 runs end-to-end
- [x] External agent can call `/api/v1/runtime/simulate`
- [x] Python SDK passes collection without errors (10/10 tests)
- [x] `aos simulate` CLI command works

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-04 | ✅ **M5.5 Machine-Native APIs COMPLETE** - All exit criteria met |
| 2025-12-04 | Implemented `POST /api/v1/runtime/simulate` - Plan simulation working |
| 2025-12-04 | Implemented `POST /api/v1/runtime/query` - Runtime state queries |
| 2025-12-04 | Implemented `GET /api/v1/runtime/capabilities` - Skills/budget/rate-limits |
| 2025-12-04 | Created `aos` CLI at `/usr/local/bin/aos` (6 commands) |
| 2025-12-04 | Fixed Python SDK - Added machine-native methods, 10/10 tests passing |
| 2025-12-04 | 60-second demo verified in SDK integration test |
| 2025-12-04 | Upgraded maturity: L2 → L4 (Machine-native primitives exposed) |
| 2025-12-04 | PIN created with 11 pending items |
| 2025-12-04 | Added recommended low-friction learning path (5 phases) |
| 2025-12-04 | Fixed PgBouncer health check (nc -z probe) |
| 2025-12-04 | Enabled Prometheus lifecycle API |
| 2025-12-04 | Added strategic context and machine-native GA checklist (PIN-023) |

