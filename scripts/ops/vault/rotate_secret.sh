#!/bin/bash
# Rotate a secret in Vault and verify app picks up the new value
#
# Usage: ./rotate_secret.sh <secret_path> <key> <new_value>
# Example: ./rotate_secret.sh app-prod WEBHOOK_KEY "new-webhook-key-value"

set -e

SECRET_PATH="${1:-}"
SECRET_KEY="${2:-}"
NEW_VALUE="${3:-}"

if [ -z "$SECRET_PATH" ] || [ -z "$SECRET_KEY" ]; then
    echo "Usage: $0 <secret_path> <key> [new_value]"
    echo ""
    echo "Examples:"
    echo "  $0 app-prod WEBHOOK_KEY               # Generate random value"
    echo "  $0 app-prod MACHINE_SECRET_TOKEN      # Generate random value"
    echo "  $0 app-prod AOS_API_KEY \"custom-value\" # Set specific value"
    echo ""
    echo "Available secret paths:"
    echo "  - app-prod (AOS_API_KEY, MACHINE_SECRET_TOKEN, OIDC_CLIENT_SECRET)"
    echo "  - database (POSTGRES_PASSWORD, etc.)"
    echo "  - external-apis (ANTHROPIC_API_KEY)"
    echo "  - keycloak-admin (KEYCLOAK_ADMIN_PASSWORD)"
    exit 1
fi

# Load Vault config
if [ -f /opt/vault/.vault-keys ]; then
    source /opt/vault/.vault-keys
fi

VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_ADDR

if [ -z "$VAULT_ROOT_TOKEN" ]; then
    echo "ERROR: VAULT_ROOT_TOKEN not set. Source /opt/vault/.vault-keys"
    exit 1
fi

export VAULT_TOKEN="$VAULT_ROOT_TOKEN"

# Generate random value if not provided
if [ -z "$NEW_VALUE" ]; then
    NEW_VALUE=$(openssl rand -hex 32)
    echo "Generated new value: ${NEW_VALUE:0:8}...(truncated)"
fi

echo "=== Rotating secret: agenticverz/$SECRET_PATH/$SECRET_KEY ==="

# Get current secret data
echo "1. Fetching current secrets..."
CURRENT_JSON=$(docker exec -e VAULT_TOKEN=$VAULT_TOKEN vault vault kv get -format=json agenticverz/$SECRET_PATH 2>/dev/null || echo '{"data":{"data":{}}}')
CURRENT_DATA=$(echo "$CURRENT_JSON" | jq -r '.data.data')

# Update the specific key
echo "2. Updating secret..."
UPDATED_DATA=$(echo "$CURRENT_DATA" | jq --arg key "$SECRET_KEY" --arg val "$NEW_VALUE" '. + {($key): $val}')

# Write back to Vault
echo "$UPDATED_DATA" | docker exec -i -e VAULT_TOKEN=$VAULT_TOKEN vault vault kv put agenticverz/$SECRET_PATH -

echo "3. Secret updated successfully!"

# Show version info
docker exec -e VAULT_TOKEN=$VAULT_TOKEN vault vault kv metadata get agenticverz/$SECRET_PATH 2>/dev/null | grep -E "version|created_time" | tail -4

echo ""
echo "=== Verification ==="

# Verify the update
VERIFY=$(docker exec -e VAULT_TOKEN=$VAULT_TOKEN vault vault kv get -field=$SECRET_KEY agenticverz/$SECRET_PATH 2>/dev/null)
if [ "${VERIFY:0:8}" = "${NEW_VALUE:0:8}" ]; then
    echo "Vault verification: PASS"
else
    echo "Vault verification: FAIL"
    exit 1
fi

echo ""
echo "=== Application Reload ==="
echo "To pick up new secrets without downtime:"
echo "  1. If app uses Vault polling: Wait for next poll cycle"
echo "  2. If app uses startup loading: docker compose restart backend"
echo ""
echo "For immediate reload:"
echo "  cd /root/agenticverz2.0 && docker compose restart backend"
