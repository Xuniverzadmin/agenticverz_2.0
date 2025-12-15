#!/usr/bin/env bash
#
# R2 Lifecycle Configuration Script
#
# Configures object retention/expiration rules for R2 bucket.
#
# Usage:
#   ./scripts/ops/r2_lifecycle.sh --apply     # Apply lifecycle rules
#   ./scripts/ops/r2_lifecycle.sh --show      # Show current rules
#   ./scripts/ops/r2_lifecycle.sh --remove    # Remove lifecycle rules
#

set -euo pipefail

# Load environment
if [[ -f /root/agenticverz2.0/.env ]]; then
    export $(grep -v '^#' /root/agenticverz2.0/.env | xargs)
fi

# Configuration
R2_ENDPOINT="${R2_ENDPOINT:-}"
R2_BUCKET="${R2_BUCKET:-candidate-failure-patterns}"
R2_UPLOAD_PREFIX="${R2_UPLOAD_PREFIX:-failure_patterns}"
R2_RETENTION_DAYS="${R2_RETENTION_DAYS:-90}"

check_config() {
    if [[ -z "$R2_ENDPOINT" ]] || [[ -z "$R2_ACCESS_KEY_ID" ]] || [[ -z "$R2_SECRET_ACCESS_KEY" ]]; then
        echo "ERROR: R2 not configured. Required:"
        echo "  - R2_ENDPOINT"
        echo "  - R2_ACCESS_KEY_ID"
        echo "  - R2_SECRET_ACCESS_KEY"
        exit 1
    fi
}

show_lifecycle() {
    check_config
    echo "Current lifecycle configuration for s3://${R2_BUCKET}/"
    echo

    aws --endpoint-url "$R2_ENDPOINT" s3api get-bucket-lifecycle-configuration \
        --bucket "$R2_BUCKET" \
        --output json 2>/dev/null || echo "No lifecycle rules configured"
}

apply_lifecycle() {
    check_config
    echo "Applying lifecycle rules to s3://${R2_BUCKET}/"
    echo "  Prefix: ${R2_UPLOAD_PREFIX}/"
    echo "  Retention: ${R2_RETENTION_DAYS} days"
    echo

    # Create lifecycle configuration JSON
    cat > /tmp/lifecycle-config.json <<EOF
{
    "Rules": [
        {
            "ID": "expire-failure-patterns",
            "Filter": {
                "Prefix": "${R2_UPLOAD_PREFIX}/"
            },
            "Status": "Enabled",
            "Expiration": {
                "Days": ${R2_RETENTION_DAYS}
            }
        }
    ]
}
EOF

    aws --endpoint-url "$R2_ENDPOINT" s3api put-bucket-lifecycle-configuration \
        --bucket "$R2_BUCKET" \
        --lifecycle-configuration file:///tmp/lifecycle-config.json

    echo "SUCCESS: Lifecycle rules applied"
    rm -f /tmp/lifecycle-config.json

    # Show applied rules
    echo
    show_lifecycle
}

remove_lifecycle() {
    check_config
    echo "Removing lifecycle rules from s3://${R2_BUCKET}/"
    echo

    aws --endpoint-url "$R2_ENDPOINT" s3api delete-bucket-lifecycle \
        --bucket "$R2_BUCKET" 2>/dev/null || true

    echo "SUCCESS: Lifecycle rules removed"
}

# Parse arguments
ACTION=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply)
            ACTION="apply"
            shift
            ;;
        --show)
            ACTION="show"
            shift
            ;;
        --remove)
            ACTION="remove"
            shift
            ;;
        --days)
            R2_RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--apply | --show | --remove] [--days N]"
            exit 1
            ;;
    esac
done

if [[ -z "$ACTION" ]]; then
    echo "Usage: $0 [--apply | --show | --remove] [--days N]"
    echo
    echo "Options:"
    echo "  --apply   Apply lifecycle rules (default: ${R2_RETENTION_DAYS} day retention)"
    echo "  --show    Show current lifecycle configuration"
    echo "  --remove  Remove all lifecycle rules"
    echo "  --days N  Set retention period (use with --apply)"
    exit 1
fi

# Execute
case "$ACTION" in
    apply)
        apply_lifecycle
        ;;
    show)
        show_lifecycle
        ;;
    remove)
        remove_lifecycle
        ;;
esac
