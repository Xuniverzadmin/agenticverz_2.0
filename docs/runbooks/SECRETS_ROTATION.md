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

## Vault Integration (ACTIVE)

HashiCorp Vault is integrated and manages all secrets.

### Vault Architecture

| Component | Location |
|-----------|----------|
| Container | `vault` at `/opt/vault/` |
| Address | `http://127.0.0.1:8200` |
| UI | `http://127.0.0.1:8200/ui` |
| Keys file | `/opt/vault/.vault-keys` (mode 600) |
| Data directory | `/opt/vault/data/` |
| App integration | `backend/app/secrets/vault_client.py` |
| HOC driver | `backend/app/hoc/int/general/drivers/vault_client.py` |

### Unseal Vault (after restart)

```bash
./scripts/ops/vault/unseal_vault.sh
```

### Rotate via Vault Script (Preferred Method)

```bash
# Auto-generate new value (openssl rand -hex 32)
./scripts/ops/vault/rotate_secret.sh app-prod MACHINE_SECRET_TOKEN

# Set specific value
./scripts/ops/vault/rotate_secret.sh app-prod WEBHOOK_KEY "my-new-key"
```

The script:
1. Fetches current secrets from the path
2. Updates the specific key
3. Writes back to Vault
4. Verifies the update
5. Reports success/failure

### Load Secrets to Environment

```bash
source scripts/ops/vault/vault_env.sh app-prod
source scripts/ops/vault/vault_env.sh database
source scripts/ops/vault/vault_env.sh external-apis
```

### Application Reload After Rotation

| Method | Command | Downtime |
|--------|---------|----------|
| Container restart | `docker compose restart backend` | ~5s |
| Full rebuild | `docker compose up -d --build backend` | ~30s |

---

## Vault Secret Paths & Owners

| Vault Path | Keys | Owner | Rotation Frequency |
|------------|------|-------|-------------------|
| `agenticverz/app-prod` | AOS_API_KEY | Platform | Quarterly |
| `agenticverz/app-prod` | MACHINE_SECRET_TOKEN | Platform | Quarterly |
| `agenticverz/app-prod` | OIDC_CLIENT_SECRET | Auth | On provider change |
| `agenticverz/database` | POSTGRES_USER | Platform | Annually |
| `agenticverz/database` | POSTGRES_PASSWORD | Platform | Quarterly |
| `agenticverz/database` | DATABASE_URL | Platform | On password change |
| `agenticverz/database` | KEYCLOAK_DB_USER | Auth | Annually |
| `agenticverz/database` | KEYCLOAK_DB_PASSWORD | Auth | Quarterly |
| `agenticverz/external-apis` | ANTHROPIC_API_KEY | LLM | On compromise/expiry |
| `agenticverz/external-apis` | OPENAI_API_KEY | LLM | On compromise/expiry |
| `agenticverz/external-apis` | GITHUB_TOKEN | CI | Annually |
| `agenticverz/keycloak-admin` | KEYCLOAK_ADMIN | Auth | Never (static) |
| `agenticverz/keycloak-admin` | KEYCLOAK_ADMIN_PASSWORD | Auth | Quarterly |
| `secret/data/user/r2` | R2_ACCESS_KEY_ID | Storage | Annually |
| `secret/data/user/r2` | R2_SECRET_ACCESS_KEY | Storage | Annually |
| `secret/data/user/neon` | DATABASE_URL | Platform | On password change |
| `secret/data/user/upstash` | REDIS_URL | Platform | On token change |

---

## Vault Scripts Reference

| Script | Location | Purpose |
|--------|----------|---------|
| `unseal_vault.sh` | `scripts/ops/vault/` | Unseal Vault after restart |
| `vault_env.sh` | `scripts/ops/vault/` | Export secrets to env vars |
| `rotate_secret.sh` | `scripts/ops/vault/` | Rotate a single secret |
| `vault_client.py` | `backend/app/secrets/` | Application Vault SDK |

---

## Neon (PostgreSQL) Credential Rotation

### Rotation Flow

1. **Generate** new password in Neon Console → Project → Connection Details → Reset Password
2. **Build** new DATABASE_URL: `postgresql://<user>:<new-password>@<host>/nova_aos?sslmode=require`
3. **Update Vault:**
   ```bash
   ./scripts/ops/vault/rotate_secret.sh database DATABASE_URL
   ./scripts/ops/vault/rotate_secret.sh database POSTGRES_PASSWORD
   ```
4. **Update** `secret/data/user/neon` path in Vault with new DATABASE_URL
5. **Restart** backend: `docker compose restart backend worker`
6. **Verify:** `curl localhost:8000/health`

### Branch Management

- Neon branches auto-suspend after compute idle timeout
- Delete unused branches to avoid compute hour charges
- After branch deletion, local DB requires ORM bootstrap (PIN-542)

---

## Upstash (Redis) Token Rotation

### Rotation Flow

1. **Generate** new token in Upstash Console → Database → Configuration → Reset Password
2. **Build** new REDIS_URL: `rediss://default:<new-token>@<host>:6379`
3. **Update Vault:**
   ```bash
   ./scripts/ops/vault/rotate_secret.sh database REDIS_URL
   ```
4. **Update** `secret/data/user/upstash` path in Vault
5. **Restart** backend: `docker compose restart backend worker`
6. **Verify:** Check Redis connectivity in health endpoint

### Notes

- Upstash uses `rediss://` (TLS) not `redis://`
- Token rotation invalidates all existing connections immediately
- No grace period — deploy immediately after rotation

---

## Clerk (OIDC) Secret Rotation

### Rotation Flow

1. **Generate** new secret in Clerk Dashboard → API Keys → Secret Keys
2. **Update Vault:**
   ```bash
   ./scripts/ops/vault/rotate_secret.sh app-prod OIDC_CLIENT_SECRET
   ```
3. **Restart** backend: `docker compose restart backend`
4. **Verify:** Test JWT validation: `curl -H "Authorization: Bearer <jwt>" localhost:8000/api/v1/runtime/capabilities`

### Notes

- Clerk supports multiple active secret keys for zero-downtime rotation
- Old key remains valid until explicitly revoked in Clerk Dashboard
- OIDC_ISSUER_URL and OIDC_CLIENT_ID do not change during rotation

---

## Resend (Email) API Key Rotation

### Rotation Flow

1. **Generate** new API key in Resend Dashboard → API Keys → Create API Key
2. **Update Vault:**
   ```bash
   ./scripts/ops/vault/rotate_secret.sh external-apis RESEND_API_KEY
   ```
3. **Restart** backend: `docker compose restart backend`
4. **Verify:** Trigger test email or check logs for send failures

### Notes

- Resend keys are scoped per domain — ensure correct domain scope
- Old key can remain active during grace period
- Revoke old key in Resend Dashboard after 24 hours

---

## Security Notes

1. Never commit `/opt/vault/.vault-keys` or any Vault tokens
2. Never print secret values in logs or CI output
3. Vault root token and unseal key must be stored with mode 600
4. In production, use auto-unseal with AWS KMS / Azure Key Vault
5. Backup Vault data directory regularly
6. Monitor Vault audit logs for unauthorized access
7. Use TLS in production (current setup is localhost-only)
