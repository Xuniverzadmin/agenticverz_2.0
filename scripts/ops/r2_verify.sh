#!/usr/bin/env bash
#
# R2 Object Storage Verification Script
#
# Verifies R2 connectivity and lists recent uploads.
#
# Usage:
#   ./scripts/ops/r2_verify.sh              # Check connectivity
#   ./scripts/ops/r2_verify.sh --list       # List recent objects
#   ./scripts/ops/r2_verify.sh --head KEY   # Get object metadata
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

check_config() {
    if [[ -z "$R2_ENDPOINT" ]] || [[ -z "$R2_ACCESS_KEY_ID" ]] || [[ -z "$R2_SECRET_ACCESS_KEY" ]]; then
        echo "ERROR: R2 not configured. Required:"
        echo "  - R2_ENDPOINT"
        echo "  - R2_ACCESS_KEY_ID"
        echo "  - R2_SECRET_ACCESS_KEY"
        exit 1
    fi
}

list_objects() {
    check_config
    echo "Listing objects in s3://${R2_BUCKET}/${R2_UPLOAD_PREFIX}/"
    echo

    aws --endpoint-url "$R2_ENDPOINT" s3 ls "s3://${R2_BUCKET}/${R2_UPLOAD_PREFIX}/" --recursive \
        | tail -20 \
        | while read -r line; do
            echo "  $line"
        done
}

head_object() {
    local key="$1"
    check_config
    echo "Getting metadata for: $key"
    echo

    aws --endpoint-url "$R2_ENDPOINT" s3api head-object \
        --bucket "$R2_BUCKET" \
        --key "$key" \
        --output json
}

check_connectivity() {
    check_config
    echo "Checking R2 connectivity..."
    echo "  Endpoint: $R2_ENDPOINT"
    echo "  Bucket: $R2_BUCKET"
    echo

    if aws --endpoint-url "$R2_ENDPOINT" s3 ls "s3://${R2_BUCKET}/" --max-items 1 >/dev/null 2>&1; then
        echo "SUCCESS: R2 bucket is accessible"

        # Count objects
        count=$(aws --endpoint-url "$R2_ENDPOINT" s3 ls "s3://${R2_BUCKET}/${R2_UPLOAD_PREFIX}/" --recursive 2>/dev/null | wc -l)
        echo "  Objects in ${R2_UPLOAD_PREFIX}/: $count"
    else
        echo "FAILED: Cannot access R2 bucket"
        exit 1
    fi
}

# Parse arguments
ACTION="check"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --list)
            ACTION="list"
            shift
            ;;
        --head)
            ACTION="head"
            OBJECT_KEY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--list | --head KEY]"
            exit 1
            ;;
    esac
done

# Execute
case "$ACTION" in
    list)
        list_objects
        ;;
    head)
        head_object "$OBJECT_KEY"
        ;;
    check)
        check_connectivity
        ;;
esac
