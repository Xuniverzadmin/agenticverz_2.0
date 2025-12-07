#!/bin/bash
# Export secrets from Vault to environment variables
#
# Usage: source ./vault_env.sh [secret_path]
# Example: source ./vault_env.sh app-prod

SECRET_PATH="${1:-app-prod}"

if [ -f /opt/vault/.vault-keys ]; then
    source /opt/vault/.vault-keys
fi

VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_ADDR
export VAULT_TOKEN="$VAULT_ROOT_TOKEN"

if [ -z "$VAULT_TOKEN" ]; then
    echo "ERROR: VAULT_TOKEN not set"
    return 1 2>/dev/null || exit 1
fi

echo "Loading secrets from agenticverz/$SECRET_PATH..."

# Get secrets as JSON and export each key
SECRETS=$(docker exec -e VAULT_TOKEN=$VAULT_TOKEN vault vault kv get -format=json agenticverz/$SECRET_PATH 2>/dev/null | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"')

while IFS= read -r line; do
    if [ -n "$line" ]; then
        export "$line"
        KEY=$(echo "$line" | cut -d'=' -f1)
        echo "  Exported: $KEY"
    fi
done <<< "$SECRETS"

echo "Done."
