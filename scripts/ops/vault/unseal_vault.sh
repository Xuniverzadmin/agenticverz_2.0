#!/bin/bash
# Unseal Vault after container restart
#
# This script should be run after Vault container restarts.
# In production, consider using auto-unseal with AWS KMS, Azure Key Vault, or HashiCorp Consul.

set -e

if [ -f /opt/vault/.vault-keys ]; then
    source /opt/vault/.vault-keys
else
    echo "ERROR: /opt/vault/.vault-keys not found"
    exit 1
fi

VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"

echo "=== Checking Vault status ==="
STATUS=$(docker exec vault vault status -format=json 2>/dev/null || echo '{"sealed":true}')
SEALED=$(echo "$STATUS" | jq -r '.sealed')

if [ "$SEALED" = "false" ]; then
    echo "Vault is already unsealed"
    exit 0
fi

echo "Vault is sealed, unsealing..."
docker exec vault vault operator unseal "$VAULT_UNSEAL_KEY"

echo ""
echo "=== Vault status after unseal ==="
docker exec vault vault status
