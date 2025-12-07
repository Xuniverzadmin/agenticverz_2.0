# HashiCorp Vault Secrets Management

AOS uses HashiCorp Vault for secrets management. All sensitive credentials are stored in Vault instead of plaintext in `.env` files.

## Vault Location

- **Container:** `vault` at `/opt/vault/`
- **Address:** http://127.0.0.1:8200
- **UI:** http://127.0.0.1:8200/ui (requires token)

## Quick Start

### 1. Unseal Vault (after restart)

```bash
./scripts/ops/vault/unseal_vault.sh
```

### 2. Load secrets to environment

```bash
# Load app secrets
source scripts/ops/vault/vault_env.sh app-prod

# Load database secrets
source scripts/ops/vault/vault_env.sh database

# Load API keys
source scripts/ops/vault/vault_env.sh external-apis
```

### 3. Rotate a secret

```bash
# Generate new random value
./scripts/ops/vault/rotate_secret.sh app-prod MACHINE_SECRET_TOKEN

# Or set specific value
./scripts/ops/vault/rotate_secret.sh app-prod WEBHOOK_KEY "my-new-key"
```

## Secret Paths

| Path | Contents |
|------|----------|
| `agenticverz/app-prod` | AOS_API_KEY, MACHINE_SECRET_TOKEN, OIDC_CLIENT_SECRET |
| `agenticverz/database` | POSTGRES_USER/PASSWORD, DATABASE_URL, KEYCLOAK_DB_* |
| `agenticverz/external-apis` | ANTHROPIC_API_KEY, OPENAI_API_KEY, EMBEDDING_* |
| `agenticverz/keycloak-admin` | KEYCLOAK_ADMIN, KEYCLOAK_ADMIN_PASSWORD |

## Vault Keys

Root token and unseal key are stored in `/opt/vault/.vault-keys` (mode 600).

**IMPORTANT:** In production, use auto-unseal with AWS KMS, Azure Key Vault, or similar.

## Scripts

| Script | Purpose |
|--------|---------|
| `unseal_vault.sh` | Unseal Vault after container restart |
| `vault_env.sh` | Export secrets to environment variables |
| `rotate_secret.sh` | Rotate a secret with optional auto-generation |

## Application Integration

The app can load secrets at startup using `backend/app/secrets/vault_client.py`:

```python
from app.secrets import load_secrets_to_env

# Load all secrets
load_secrets_to_env(["app-prod", "database", "external-apis"])

# Or require Vault (fail if unavailable)
load_secrets_to_env(required=True)
```

## Security Notes

1. **Never commit** `/opt/vault/.vault-keys` or any Vault tokens
2. **Rotate tokens** regularly using `rotate_secret.sh`
3. **Backup** Vault data directory (`/opt/vault/data/`)
4. **Monitor** Vault audit logs for unauthorized access
5. **Use TLS** in production (current setup is localhost only)
