#!/usr/bin/env bash
#
# Webhook Key Rotation Script
#
# Rotates webhook signing keys with zero-downtime using version headers.
# Supports Vault KV v2, AWS SSM, or local file storage.
#
# Usage:
#   ./rotate_webhook_key.sh <new_version> [options]
#
# Options:
#   --backend TYPE       Key storage backend: vault, ssm, file (default: file)
#   --grace VERSIONS     Comma-separated previous versions to accept (e.g., "v1,v2")
#   --deploy DEPLOYMENT  Kubernetes deployment name (default: nova-backend)
#   --namespace NS       Kubernetes namespace (default: aos)
#   --docker             Use docker-compose instead of Kubernetes
#   --dry-run            Preview changes without applying
#   --help               Show this help
#
# Environment Variables:
#   VAULT_ADDR           Vault server address (for vault backend)
#   VAULT_TOKEN          Vault authentication token
#   AWS_REGION           AWS region (for ssm backend)
#   WEBHOOK_KEYS_PATH    Path for key storage (default: /var/lib/aos/webhook-keys)
#
# Examples:
#   # Rotate to v2, keep v1 in grace period (file backend)
#   ./rotate_webhook_key.sh v2 --grace v1
#
#   # Rotate using Vault
#   ./rotate_webhook_key.sh v3 --backend vault --grace v2,v1
#
#   # Dry run to preview
#   ./rotate_webhook_key.sh v2 --dry-run
#

set -uo pipefail

# Defaults
NEW_VERSION=""
BACKEND="file"
GRACE_VERSIONS=""
K8S_DEPLOYMENT="nova-backend"
K8S_NAMESPACE="aos"
USE_DOCKER=false
DRY_RUN=false
WEBHOOK_KEYS_PATH="${WEBHOOK_KEYS_PATH:-/var/lib/aos/webhook-keys}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

show_help() {
    sed -n '/^# Usage/,/^[^#]/p' "$0" | grep '^#' | sed 's/^# //'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend)
            BACKEND="$2"
            shift 2
            ;;
        --grace)
            GRACE_VERSIONS="$2"
            shift 2
            ;;
        --deploy)
            K8S_DEPLOYMENT="$2"
            shift 2
            ;;
        --namespace)
            K8S_NAMESPACE="$2"
            shift 2
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        -*)
            log_error "Unknown option: $1"
            exit 2
            ;;
        *)
            if [[ -z "$NEW_VERSION" ]]; then
                NEW_VERSION="$1"
            else
                log_error "Unexpected argument: $1"
                exit 2
            fi
            shift
            ;;
    esac
done

if [[ -z "$NEW_VERSION" ]]; then
    log_error "New version is required"
    echo "Usage: $0 <new_version> [options]"
    exit 2
fi

# Validate version format
if [[ ! "$NEW_VERSION" =~ ^v[0-9]+$ ]]; then
    log_warn "Version should follow format 'vN' (e.g., v1, v2). Got: $NEW_VERSION"
fi

log_info "=== Webhook Key Rotation ==="
log_info "New version: $NEW_VERSION"
log_info "Backend: $BACKEND"
log_info "Grace versions: ${GRACE_VERSIONS:-none}"
log_info "Dry run: $DRY_RUN"
echo ""

# Generate new key (32 bytes = 256 bits)
NEW_KEY_HEX=$(openssl rand -hex 32)
log_info "Generated new key: ${NEW_KEY_HEX:0:8}...${NEW_KEY_HEX: -8} (64 hex chars)"

# Store key based on backend
store_key() {
    local version="$1"
    local key="$2"

    case "$BACKEND" in
        vault)
            if [[ -z "${VAULT_TOKEN:-}" ]]; then
                log_error "VAULT_TOKEN environment variable required for vault backend"
                exit 2
            fi
            if [[ -z "${VAULT_ADDR:-}" ]]; then
                log_error "VAULT_ADDR environment variable required for vault backend"
                exit 2
            fi

            log_info "Storing key in Vault at secret/webhook/keys#$version"
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "[DRY RUN] Would run: vault kv patch secret/webhook/keys $version=<key>"
            else
                vault kv patch secret/webhook/keys "$version"="$key" 2>/dev/null || \
                vault kv put secret/webhook/keys "$version"="$key"
            fi
            ;;

        ssm)
            if [[ -z "${AWS_REGION:-}" ]]; then
                log_error "AWS_REGION environment variable required for ssm backend"
                exit 2
            fi

            local param_name="/aos/webhook/keys/$version"
            log_info "Storing key in AWS SSM at $param_name"
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "[DRY RUN] Would run: aws ssm put-parameter --name $param_name --type SecureString --value <key>"
            else
                aws ssm put-parameter \
                    --name "$param_name" \
                    --type SecureString \
                    --value "$key" \
                    --overwrite \
                    --region "$AWS_REGION"
            fi
            ;;

        file)
            log_info "Storing key in file at $WEBHOOK_KEYS_PATH/$version"
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "[DRY RUN] Would create: $WEBHOOK_KEYS_PATH/$version"
            else
                mkdir -p "$WEBHOOK_KEYS_PATH"
                chmod 700 "$WEBHOOK_KEYS_PATH"
                echo "$key" > "$WEBHOOK_KEYS_PATH/$version"
                chmod 600 "$WEBHOOK_KEYS_PATH/$version"
            fi
            ;;

        *)
            log_error "Unknown backend: $BACKEND"
            exit 2
            ;;
    esac
}

# Update application configuration
update_app_config() {
    local version="$1"
    local grace="$2"

    if [[ "$USE_DOCKER" == "true" ]]; then
        log_info "Updating Docker container environment..."
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would update docker-compose.yml with:"
            log_info "  WEBHOOK_KEY_VERSION=$version"
            log_info "  WEBHOOK_KEY_GRACE_VERSIONS=$grace"
        else
            # For docker-compose, we need to update .env or docker-compose.yml
            ENV_FILE="/root/agenticverz2.0/.env"
            if [[ -f "$ENV_FILE" ]]; then
                # Update or add variables
                grep -q "^WEBHOOK_KEY_VERSION=" "$ENV_FILE" && \
                    sed -i "s/^WEBHOOK_KEY_VERSION=.*/WEBHOOK_KEY_VERSION=$version/" "$ENV_FILE" || \
                    echo "WEBHOOK_KEY_VERSION=$version" >> "$ENV_FILE"

                grep -q "^WEBHOOK_KEY_GRACE_VERSIONS=" "$ENV_FILE" && \
                    sed -i "s/^WEBHOOK_KEY_GRACE_VERSIONS=.*/WEBHOOK_KEY_GRACE_VERSIONS=$grace/" "$ENV_FILE" || \
                    echo "WEBHOOK_KEY_GRACE_VERSIONS=$grace" >> "$ENV_FILE"
            else
                echo "WEBHOOK_KEY_VERSION=$version" > "$ENV_FILE"
                echo "WEBHOOK_KEY_GRACE_VERSIONS=$grace" >> "$ENV_FILE"
            fi

            log_info "Updated $ENV_FILE"
            log_info "Restart backend with: docker compose up -d --build backend"
        fi
    else
        log_info "Updating Kubernetes deployment..."
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would run:"
            log_info "  kubectl -n $K8S_NAMESPACE set env deployment/$K8S_DEPLOYMENT WEBHOOK_KEY_VERSION=$version"
            log_info "  kubectl -n $K8S_NAMESPACE set env deployment/$K8S_DEPLOYMENT WEBHOOK_KEY_GRACE_VERSIONS=$grace"
            log_info "  kubectl -n $K8S_NAMESPACE rollout restart deployment/$K8S_DEPLOYMENT"
        else
            kubectl -n "$K8S_NAMESPACE" set env deployment/"$K8S_DEPLOYMENT" \
                WEBHOOK_KEY_VERSION="$version" \
                WEBHOOK_KEY_GRACE_VERSIONS="$grace"
            kubectl -n "$K8S_NAMESPACE" rollout restart deployment/"$K8S_DEPLOYMENT"
            log_info "Waiting for rollout..."
            kubectl -n "$K8S_NAMESPACE" rollout status deployment/"$K8S_DEPLOYMENT" --timeout=120s
        fi
    fi
}

# Main rotation flow
log_info "Step 1: Storing new key..."
store_key "$NEW_VERSION" "$NEW_KEY_HEX"

echo ""
log_info "Step 2: Updating application configuration..."
update_app_config "$NEW_VERSION" "$GRACE_VERSIONS"

echo ""
log_info "=== Rotation Summary ==="
log_info "New active key version: $NEW_VERSION"
if [[ -n "$GRACE_VERSIONS" ]]; then
    log_info "Grace period versions: $GRACE_VERSIONS"
    log_info "Both new and grace versions will be accepted for signature verification"
fi

echo ""
log_info "=== Post-Rotation Checklist ==="
echo "1. Verify webhooks are being sent with X-Webhook-Key-Version: $NEW_VERSION"
echo "2. Monitor receiver acceptance rates for any signature failures"
echo "3. After grace period (recommended: 72 hours), remove old versions:"

if [[ -n "$GRACE_VERSIONS" ]]; then
    IFS=',' read -ra VERSIONS <<< "$GRACE_VERSIONS"
    for v in "${VERSIONS[@]}"; do
        v=$(echo "$v" | tr -d ' ')
        case "$BACKEND" in
            vault)
                echo "   vault kv patch secret/webhook/keys $v="
                ;;
            ssm)
                echo "   aws ssm delete-parameter --name /aos/webhook/keys/$v"
                ;;
            file)
                echo "   rm $WEBHOOK_KEYS_PATH/$v"
                ;;
        esac
    done
fi

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
    log_warn "=== DRY RUN COMPLETE - No changes were made ==="
else
    log_info "=== Rotation Complete ==="
fi
