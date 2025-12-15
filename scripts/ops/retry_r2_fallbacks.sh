#!/usr/bin/env bash
#
# R2 Fallback Retry Worker
#
# Scans the local fallback directory for failed R2 uploads and attempts
# to re-upload them. Successfully uploaded files are moved to an archived
# directory.
#
# Usage:
#   ./scripts/ops/retry_r2_fallbacks.sh          # Process all pending files
#   ./scripts/ops/retry_r2_fallbacks.sh --dry-run # Show what would be processed
#   ./scripts/ops/retry_r2_fallbacks.sh --max 10  # Process at most 10 files
#
# Schedule via cron (every 15 minutes):
#   */15 * * * * /root/agenticverz2.0/scripts/ops/retry_r2_fallbacks.sh >> /var/log/aos/r2_retry.log 2>&1
#

set -euo pipefail

# Configuration
FALLBACK_DIR="${AGG_LOCAL_FALLBACK:-/opt/agenticverz/state/fallback-uploads}"
ARCHIVE_DIR="${FALLBACK_DIR}/archived"
BACKEND_DIR="/root/agenticverz2.0/backend"
MAX_FILES=50
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --max)
            MAX_FILES="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure directories exist
mkdir -p "$FALLBACK_DIR" "$ARCHIVE_DIR"

# Count pending files
PENDING_COUNT=$(find "$FALLBACK_DIR" -maxdepth 1 -name "*.json" -type f | wc -l)

if [[ "$PENDING_COUNT" -eq 0 ]]; then
    echo "[$(date -Iseconds)] No pending fallback files"
    exit 0
fi

echo "[$(date -Iseconds)] Found $PENDING_COUNT pending fallback files"

# Process files
PROCESSED=0
SUCCEEDED=0
FAILED=0

for filepath in "$FALLBACK_DIR"/*.json; do
    # Skip if no files match
    [[ -e "$filepath" ]] || continue

    # Respect max limit
    if [[ "$PROCESSED" -ge "$MAX_FILES" ]]; then
        echo "[$(date -Iseconds)] Reached max files limit ($MAX_FILES)"
        break
    fi

    filename=$(basename "$filepath")

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] Would process: $filename"
        PROCESSED=$((PROCESSED + 1))
        continue
    fi

    echo "[$(date -Iseconds)] Processing: $filename"

    # Attempt retry using Python helper
    cd "$BACKEND_DIR"

    result=$(PYTHONPATH=. python3 -c "
import json
import sys
from app.jobs.storage import retry_local_fallback

result = retry_local_fallback('$filepath')
print(json.dumps(result))
" 2>&1) || true

    # Parse result
    status=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','error'))" 2>/dev/null || echo "error")

    if [[ "$status" == "uploaded" ]]; then
        echo "[$(date -Iseconds)] SUCCESS: $filename uploaded to R2"
        SUCCEEDED=$((SUCCEEDED + 1))

        # File was already renamed by Python, but move to archive if still present
        if [[ -f "${filepath}.uploaded" ]]; then
            mv "${filepath}.uploaded" "$ARCHIVE_DIR/"
        fi
    else
        echo "[$(date -Iseconds)] FAILED: $filename - $result"
        FAILED=$((FAILED + 1))
    fi

    PROCESSED=$((PROCESSED + 1))
done

# Summary
echo "[$(date -Iseconds)] Retry complete: processed=$PROCESSED succeeded=$SUCCEEDED failed=$FAILED"

# Exit with failure if any retries failed
if [[ "$FAILED" -gt 0 ]]; then
    exit 1
fi

exit 0
