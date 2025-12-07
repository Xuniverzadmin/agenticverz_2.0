# Secrets Rotation Runbook

This runbook documents procedures for rotating sensitive credentials in the AOS system.

## Overview

Critical secrets that require periodic rotation:
1. **OpenAI API Key** - LLM provider authentication
2. **Clerk API Key** - Authentication service (future M8)
3. **Database Credentials** - PostgreSQL access
4. **Grafana API Key** - Dashboard management
5. **Webhook Signing Key** - Payload verification

## General Rotation Process

```
┌─────────────────────────────────────────────┐
│  1. Generate new secret                     │
│  2. Update secret store (Vault/.env)        │
│  3. Verify new secret works                 │
│  4. Deploy with new secret                  │
│  5. Monitor for errors                      │
│  6. Revoke old secret after grace period    │
└─────────────────────────────────────────────┘
```

## 1. OpenAI API Key Rotation

### Prerequisites
- Access to OpenAI dashboard
- Access to production secrets

### Procedure

1. **Generate new key** at https://platform.openai.com/api-keys

2. **Update secret store:**
```bash
# Using Vault
vault kv put secret/aos/openai api_key="sk-new-key..."

# Using .env (development only)
sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=sk-new-key.../' .env
```

3. **Verify new key:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-new-key..."
```

4. **Deploy:**
```bash
docker compose restart backend worker
```

5. **Monitor:**
```bash
# Check logs for auth errors
docker compose logs backend --tail 100 | grep -i "auth\|401\|403"

# Check metrics
curl localhost:9090/api/v1/query?query=llm_invoke_errors_total
```

6. **Revoke old key** after 24 hours in OpenAI dashboard.

---

## 2. Database Credentials Rotation

### Prerequisites
- PostgreSQL superuser access
- Downtime window (or hot-swap capability)

### Procedure

1. **Create new role:**
```sql
-- Connect as superuser
CREATE ROLE nova_new WITH LOGIN PASSWORD 'new_secure_password';
GRANT ALL ON DATABASE nova_aos TO nova_new;
GRANT ALL ON ALL TABLES IN SCHEMA public TO nova_new;
```

2. **Update connection string:**
```bash
# .env or Vault
DATABASE_URL="postgresql://nova_new:new_secure_password@localhost:6432/nova_aos"
```

3. **Hot-swap procedure (zero downtime):**
```bash
# Update PgBouncer auth
echo '"nova_new" "new_secure_password"' >> /etc/pgbouncer/userlist.txt
pkill -SIGHUP pgbouncer

# Rolling restart
docker compose restart backend --force-recreate
docker compose restart worker --force-recreate
```

4. **Verify:**
```bash
docker exec nova_db psql -U nova_new -d nova_aos -c "SELECT 1"
```

5. **Cleanup old role** after 48 hours:
```sql
DROP ROLE IF EXISTS nova_old;
```

---

## 3. Grafana API Key Rotation

### Prerequisites
- Grafana admin access

### Procedure

1. **Generate new key:**
```bash
curl -X POST http://admin:admin@localhost:3000/api/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"aos-automation-new","role":"Admin"}'
```

2. **Update deployment scripts:**
```bash
export GRAFANA_API_KEY="new-key-value"
```

3. **Test:**
```bash
./scripts/ops/m9_monitoring_deploy.sh
```

4. **Revoke old key:**
```bash
curl -X DELETE http://admin:admin@localhost:3000/api/auth/keys/{old_key_id}
```

---

## 4. Webhook Signing Key Rotation

### Prerequisites
- Access to webhook configuration

### Procedure

1. **Generate new key:**
```bash
./scripts/ops/webhook/rotate_webhook_key.sh
```

2. **Update consumers:**
   - Notify all webhook consumers of new key
   - Allow 24-hour dual-key verification window

3. **Deploy:**
```bash
docker compose restart backend worker
```

---

## Emergency Rotation (Compromised Secret)

If a secret is suspected compromised:

1. **Immediately revoke** at the source (OpenAI/Grafana/etc.)
2. **Generate replacement**
3. **Deploy immediately** (skip grace period)
4. **Audit logs** for unauthorized access
5. **File incident report**

```bash
# Emergency deploy
export SECRET_COMPROMISED=true
./scripts/ops/emergency_secret_rotation.sh
```

---

## Vault Integration (Future)

When HashiCorp Vault is integrated:

```bash
# Read current secret
vault kv get -field=api_key secret/aos/openai

# Rotate with audit
vault write sys/policies/password \
  rules='length=64 charset=alphanumeric'

vault kv put secret/aos/openai api_key=$(vault read -field=password sys/policies/password/generate)
```

---

## Rotation Schedule

| Secret | Rotation Frequency | Last Rotated | Next Due |
|--------|-------------------|--------------|----------|
| OpenAI API Key | 90 days | - | TBD |
| Database Password | 180 days | - | TBD |
| Grafana API Key | 90 days | - | TBD |
| Webhook Key | 180 days | - | TBD |

---

## Contacts

- **Security Team**: security@example.com
- **On-Call Platform**: pagerduty://aos-platform
- **Emergency**: [Internal emergency contacts]
