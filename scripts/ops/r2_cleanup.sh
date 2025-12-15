#!/usr/bin/env bash
# scripts/ops/r2_cleanup.sh
# Cleanup test/old objects from R2 bucket
#
# Usage:
#   ./scripts/ops/r2_cleanup.sh --dry-run           # List objects to delete
#   ./scripts/ops/r2_cleanup.sh --prefix failure_patterns/2025/12/08  # Delete specific prefix
#   ./scripts/ops/r2_cleanup.sh --older-than 30     # Delete objects older than 30 days
#   ./scripts/ops/r2_cleanup.sh --test-only         # Delete only test uploads
#
# Environment:
#   R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET
#   Or uses Vault if VAULT_ADDR and VAULT_TOKEN are set

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
DRY_RUN=false
PREFIX=""
OLDER_THAN=""
TEST_ONLY=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        --older-than)
            OLDER_THAN="$2"
            shift 2
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run          List objects without deleting"
            echo "  --prefix PATH      Delete objects with specific prefix"
            echo "  --older-than DAYS  Delete objects older than N days"
            echo "  --test-only        Only delete test uploads (based on today's date)"
            echo "  --force            Skip confirmation prompt"
            echo "  -h, --help         Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Load environment
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Python script for cleanup
CLEANUP_SCRIPT=$(cat <<'PYTHON'
import os
import sys
import json
from datetime import datetime, timezone, timedelta

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

def load_vault_secrets():
    """Load R2 secrets from Vault if available."""
    try:
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        if not vault_addr or not vault_token:
            return {}

        import requests
        resp = requests.get(
            f"{vault_addr}/v1/secret/data/agenticverz/r2-storage",
            headers={"X-Vault-Token": vault_token},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("data", {})
            return {
                "R2_ACCESS_KEY_ID": data.get("access_key_id", ""),
                "R2_SECRET_ACCESS_KEY": data.get("secret_access_key", ""),
                "R2_ENDPOINT": data.get("endpoint", ""),
                "R2_BUCKET": data.get("bucket", ""),
            }
    except Exception:
        pass
    return {}

# Load config
vault_secrets = load_vault_secrets()

R2_ACCESS_KEY_ID = vault_secrets.get("R2_ACCESS_KEY_ID") or os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = vault_secrets.get("R2_SECRET_ACCESS_KEY") or os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT = vault_secrets.get("R2_ENDPOINT") or os.getenv("R2_ENDPOINT", "")
R2_BUCKET = vault_secrets.get("R2_BUCKET") or os.getenv("R2_BUCKET", "candidate-failure-patterns")

# Parse args
dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
prefix = os.getenv("PREFIX", "")
older_than = os.getenv("OLDER_THAN", "")
test_only = os.getenv("TEST_ONLY", "false").lower() == "true"

if not all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT]):
    print("ERROR: R2 credentials not configured")
    sys.exit(1)

# Create client
client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=Config(signature_version="s3v4"),
)

# List objects
list_kwargs = {"Bucket": R2_BUCKET}
if prefix:
    list_kwargs["Prefix"] = prefix
elif test_only:
    # Test objects are from today
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    list_kwargs["Prefix"] = f"failure_patterns/{today}"

objects_to_delete = []
total_size = 0

try:
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(**list_kwargs):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size = obj["Size"]
            last_modified = obj["LastModified"]

            # Filter by age if specified
            if older_than:
                cutoff = datetime.now(timezone.utc) - timedelta(days=int(older_than))
                if last_modified > cutoff:
                    continue

            objects_to_delete.append({
                "Key": key,
                "Size": size,
                "LastModified": last_modified.isoformat(),
            })
            total_size += size

except Exception as e:
    print(f"ERROR: Failed to list objects: {e}")
    sys.exit(1)

if not objects_to_delete:
    print("No objects found matching criteria")
    sys.exit(0)

# Print summary
print(f"\nObjects to delete: {len(objects_to_delete)}")
print(f"Total size: {total_size / 1024:.2f} KB")
print("\nObjects:")
for obj in objects_to_delete:
    print(f"  - {obj['Key']} ({obj['Size']} bytes, {obj['LastModified']})")

if dry_run:
    print("\n[DRY RUN] No objects deleted")
    sys.exit(0)

# Delete objects
print("\nDeleting objects...")
deleted = 0
errors = 0

for obj in objects_to_delete:
    try:
        client.delete_object(Bucket=R2_BUCKET, Key=obj["Key"])
        print(f"  Deleted: {obj['Key']}")
        deleted += 1
    except Exception as e:
        print(f"  ERROR deleting {obj['Key']}: {e}")
        errors += 1

print(f"\nSummary: {deleted} deleted, {errors} errors")
sys.exit(0 if errors == 0 else 1)
PYTHON
)

# Export vars for Python
export DRY_RUN="$DRY_RUN"
export PREFIX="$PREFIX"
export OLDER_THAN="$OLDER_THAN"
export TEST_ONLY="$TEST_ONLY"

echo -e "${YELLOW}R2 Cleanup Script${NC}"
echo "=================="
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}[DRY RUN MODE]${NC}"
fi

if [[ -n "$PREFIX" ]]; then
    echo "Prefix filter: $PREFIX"
fi

if [[ -n "$OLDER_THAN" ]]; then
    echo "Age filter: older than $OLDER_THAN days"
fi

if [[ "$TEST_ONLY" == "true" ]]; then
    echo "Filter: test uploads only (today's date)"
fi

echo ""

# Confirmation prompt (unless --force or --dry-run)
if [[ "$DRY_RUN" != "true" && "$FORCE" != "true" ]]; then
    read -p "Continue with deletion? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Run cleanup
python3 -c "$CLEANUP_SCRIPT"
