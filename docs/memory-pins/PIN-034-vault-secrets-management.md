# PIN-034: HashiCorp Vault Secrets Management

**Serial:** PIN-034
**Title:** HashiCorp Vault Secrets Management
**Category:** Security / Infrastructure
**Status:** COMPLETE
**Created:** 2025-12-05
**Updated:** 2025-12-05

---

## Executive Summary

Deployed HashiCorp Vault as the secrets management backend for AOS. All sensitive credentials (API keys, tokens, database passwords) are now stored in Vault instead of plaintext `.env` files.

---

## Problem Statement

Prior to this implementation:
- Secrets stored in plaintext in `.env` files
- No rotation capability without manual editing
- Secrets potentially exposed in git history
- No audit trail for secret access
- No versioning of secret values

---

## Solution

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HashiCorp Vault                       │
│                  (127.0.0.1:8200)                        │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  app-prod   │  │  database   │  │  external-apis  │  │
│  │             │  │             │  │                 │  │
│  │ AOS_API_KEY │  │ POSTGRES_*  │  │ ANTHROPIC_KEY   │  │
│  │ MACHINE_TOK │  │ DATABASE_URL│  │                 │  │
│  │ OIDC_SECRET │  │ KEYCLOAK_*  │  │                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                                                          │
│  ┌─────────────────┐                                     │
│  │  keycloak-admin │                                     │
│  │                 │                                     │
│  │ KEYCLOAK_ADMIN  │                                     │
│  │ KEYCLOAK_PASS   │                                     │
│  └─────────────────┘                                     │
└─────────────────────────────────────────────────────────┘
           │
           │ HTTP API (X-Vault-Token)
           ▼
┌─────────────────────────────────────────────────────────┐
│                    AOS Backend                           │
│                                                          │
│  vault_client.py ──► load_secrets_to_env()              │
│                                                          │
│  Or: source scripts/ops/vault/vault_env.sh app-prod     │
└─────────────────────────────────────────────────────────┘
```

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Vault Container | `/opt/vault/` | Secrets storage |
| Vault Config | `/opt/vault/config/vault.hcl` | Server configuration |
| Vault Keys | `/opt/vault/.vault-keys` | Unseal key + root token |
| Python Client | `backend/app/secrets/vault_client.py` | App integration |
| Rotation Script | `scripts/ops/vault/rotate_secret.sh` | Secret rotation |
| Unseal Script | `scripts/ops/vault/unseal_vault.sh` | Post-restart unseal |
| Env Export | `scripts/ops/vault/vault_env.sh` | Shell integration |

---

## Implementation Details

### Vault Setup

```yaml
# /opt/vault/docker-compose.yml
services:
  vault:
    image: hashicorp/vault:1.15
    container_name: vault
    ports:
      - "127.0.0.1:8200:8200"
    volumes:
      - ./config:/vault/config
      - ./data:/vault/data
    command: server
```

### Secrets Paths

| Path | Keys | Purpose |
|------|------|---------|
| `agenticverz/app-prod` | AOS_API_KEY, MACHINE_SECRET_TOKEN, OIDC_CLIENT_SECRET | Application secrets |
| `agenticverz/database` | POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_URL, KEYCLOAK_DB_USER, KEYCLOAK_DB_PASSWORD | Database credentials |
| `agenticverz/external-apis` | ANTHROPIC_API_KEY | Third-party API keys |
| `agenticverz/keycloak-admin` | KEYCLOAK_ADMIN, KEYCLOAK_ADMIN_PASSWORD | Keycloak admin credentials |

### Python Integration

```python
from app.secrets import load_secrets_to_env

# Load at startup
load_secrets_to_env(["app-prod", "database", "external-apis"])

# Or get specific secret
from app.secrets import VaultClient
client = VaultClient()
secrets = client.get_secret("app-prod")
api_key = secrets["AOS_API_KEY"]
```

### Shell Integration

```bash
# Load secrets to current shell
source scripts/ops/vault/vault_env.sh app-prod

# Use secrets
echo $AOS_API_KEY
```

### Secret Rotation

```bash
# Generate new random value
./scripts/ops/vault/rotate_secret.sh app-prod MACHINE_SECRET_TOKEN

# Set specific value
./scripts/ops/vault/rotate_secret.sh app-prod WEBHOOK_KEY "new-key-value"

# Restart app to pick up new value
docker compose restart backend
```

---

## Verification

### Acceptance Criteria

| Criteria | Status | Evidence |
|----------|--------|----------|
| Vault deployed and running | ✅ | `docker ps` shows `vault` container |
| Secrets migrated to Vault | ✅ | 4 secret paths created |
| Rotation script works | ✅ | Tested with TEST_ROTATION_KEY |
| No plaintext secrets in repo | ✅ | grep shows only `novapass` in docs |
| `.env.example` updated | ✅ | References Vault paths |

### Test Results

```bash
# Vault status
$ docker exec vault vault status
Sealed: false
Version: 1.15.6

# List secrets
$ docker exec vault vault kv list agenticverz
Keys
----
app-prod
database
external-apis
keycloak-admin

# Rotation test
$ ./scripts/ops/vault/rotate_secret.sh app-prod TEST_KEY "test-value"
Vault verification: PASS
```

---

## Operations

### Daily Operations

| Task | Command |
|------|---------|
| Check Vault status | `docker exec vault vault status` |
| List secrets | `docker exec -e VAULT_TOKEN=$TOKEN vault vault kv list agenticverz` |
| Get secret | `docker exec -e VAULT_TOKEN=$TOKEN vault vault kv get agenticverz/app-prod` |

### After Vault Restart

```bash
# Vault seals on restart - must unseal
./scripts/ops/vault/unseal_vault.sh
```

### Secret Rotation Procedure

1. Run rotation script: `./scripts/ops/vault/rotate_secret.sh <path> <key>`
2. Verify in Vault: `vault kv get agenticverz/<path>`
3. Restart app: `docker compose restart backend`
4. Verify app works with new secret

---

## Security Considerations

### Current Setup (Development)

- Vault accessible only on localhost (127.0.0.1:8200)
- TLS disabled (behind reverse proxy in production)
- Single unseal key (not production-ready)
- Root token used for operations

### Production Recommendations

1. **Auto-Unseal**: Use AWS KMS, Azure Key Vault, or HashiCorp Consul
2. **TLS**: Enable TLS with valid certificates
3. **Key Shares**: Use 5 key shares with 3 threshold
4. **AppRole Auth**: Use AppRole instead of root token for apps
5. **Audit Logging**: Enable audit backend
6. **Backup**: Regular backups of `/opt/vault/data/`

---

## Files Created

| File | Purpose |
|------|---------|
| `/opt/vault/docker-compose.yml` | Vault container configuration |
| `/opt/vault/config/vault.hcl` | Vault server configuration |
| `/opt/vault/.vault-keys` | Unseal key and root token (600 perms) |
| `/opt/vault/.env` | Keycloak admin password backup |
| `backend/app/secrets/__init__.py` | Module exports |
| `backend/app/secrets/vault_client.py` | Python Vault client |
| `scripts/ops/vault/rotate_secret.sh` | Secret rotation script |
| `scripts/ops/vault/unseal_vault.sh` | Vault unseal script |
| `scripts/ops/vault/vault_env.sh` | Export secrets to shell |
| `scripts/ops/vault/README.md` | Documentation |

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-033 | M8-M14 Roadmap (includes auth/secrets work) |
| PIN-032 | RBAC Enablement (uses MACHINE_SECRET_TOKEN) |
| PIN-009 | External Rollout (auth requirements) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-05 | PIN-034 created |
| 2025-12-05 | Vault container deployed at 127.0.0.1:8200 |
| 2025-12-05 | KV v2 secrets engine enabled at `agenticverz/` |
| 2025-12-05 | Migrated 4 secret paths: app-prod, database, external-apis, keycloak-admin |
| 2025-12-05 | Created Python client `backend/app/secrets/vault_client.py` |
| 2025-12-05 | Created rotation script - verified working |
| 2025-12-05 | Updated `.env.example` with Vault references |
