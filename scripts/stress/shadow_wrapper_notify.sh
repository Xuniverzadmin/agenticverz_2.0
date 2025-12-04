#!/usr/bin/env bash
# M4 Shadow Run Wrapper with Webhook Notifications
# Usage: ./shadow_wrapper_notify.sh [HOURS] [WORKERS] [SHADOW]
# Environment: SHADOW_HOOK=https://webhook.site/your-uuid

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

WORKDIR="/tmp/m4-shadow-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$WORKDIR"
LOG="$WORKDIR/run.log"
ART="$WORKDIR/artifacts"
mkdir -p "$ART"

# Configuration
SHADOW_SCRIPT="$SCRIPT_DIR/run_shadow_simulation.sh"
HOURS=${1:-24}
WORKERS=${2:-3}
GOLDEN_DIR="${GOLDEN_DIR:-/var/lib/aos/golden}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG"; }

# Send notification to webhook
notify() {
    local status="$1"
    local message="$2"

    if [ -n "${SHADOW_HOOK:-}" ]; then
        local payload=$(cat <<EOF
{
    "timestamp": "$(date --iso-8601=seconds)",
    "status": "$status",
    "message": "$message",
    "workdir": "$WORKDIR",
    "hours": $HOURS,
    "workers": $WORKERS,
    "host": "$(hostname)"
}
EOF
)
        curl -sS -X POST -H "Content-Type: application/json" -d "$payload" "$SHADOW_HOOK" >/dev/null 2>&1 || true
    fi
}

# Cleanup handler
cleanup() {
    log_info "Cleaning up..."
    notify "cleanup" "Shadow run cleanup triggered"
}
trap cleanup EXIT

# Header
log_info "═══════════════════════════════════════════════════════════════"
log_info "         M4 Shadow Run - Webhook Notification Wrapper"
log_info "═══════════════════════════════════════════════════════════════"
log_info "  Hours:      $HOURS"
log_info "  Workers:    $WORKERS"
log_info "  Golden Dir: $GOLDEN_DIR"
log_info "  Work Dir:   $WORKDIR"
log_info "  Webhook:    ${SHADOW_HOOK:-NOT SET}"
log_info "═══════════════════════════════════════════════════════════════"

# Notify start
notify "started" "Shadow run started: ${HOURS}h, ${WORKERS} workers"

log_info "Webhook test notification sent"

# Check prerequisites
if [ ! -x "$SHADOW_SCRIPT" ]; then
    log_error "Shadow script not found or not executable: $SHADOW_SCRIPT"
    notify "error" "Shadow script not found"
    exit 1
fi

if [ ! -d "$GOLDEN_DIR" ]; then
    log_warn "Golden directory does not exist, creating: $GOLDEN_DIR"
    mkdir -p "$GOLDEN_DIR"
fi

# Run shadow script
log_info "Starting shadow simulation at $(date)"
RC=0

# Run with timeout slightly longer than specified hours
TIMEOUT_SECS=$((HOURS * 3600 + 600))  # hours + 10 min buffer

timeout "$TIMEOUT_SECS" "$SHADOW_SCRIPT" \
    --hours "$HOURS" \
    --workers "$WORKERS" \
    2>&1 | tee -a "$LOG" || RC=${PIPESTATUS[0]:-$?}

log_info "Shadow simulation completed at $(date) with exit code: $RC"

# Collect artifacts
log_info "Collecting artifacts..."

# Copy golden files
if [ -d "$GOLDEN_DIR" ] && [ "$(ls -A "$GOLDEN_DIR" 2>/dev/null)" ]; then
    cp -r "$GOLDEN_DIR"/* "$ART/" 2>/dev/null || true
    log_info "Copied golden files to artifacts"
else
    log_warn "No golden files found in $GOLDEN_DIR"
fi

# Copy stress history if exists
if [ -d "/var/lib/aos/stress-history" ]; then
    cp -r /var/lib/aos/stress-history "$ART/stress-history" 2>/dev/null || true
fi

# Create summary
SUMMARY_FILE="$WORKDIR/summary.json"
cat > "$SUMMARY_FILE" <<EOF
{
    "timestamp": "$(date --iso-8601=seconds)",
    "workdir": "$WORKDIR",
    "hours": $HOURS,
    "workers": $WORKERS,
    "exit_code": $RC,
    "golden_dir": "$GOLDEN_DIR",
    "golden_file_count": $(find "$ART" -name "*.jsonl" 2>/dev/null | wc -l),
    "log_lines": $(wc -l < "$LOG"),
    "host": "$(hostname)"
}
EOF

log_info "Summary written to $SUMMARY_FILE"

# Package artifacts
ARTIFACT_TAR="$WORKDIR/artifacts.tgz"
tar -czf "$ARTIFACT_TAR" -C "$ART" . 2>/dev/null || true
log_info "Artifacts packaged: $ARTIFACT_TAR ($(du -h "$ARTIFACT_TAR" | cut -f1))"

# Final notification with summary
FINAL_STATUS="completed"
[ $RC -ne 0 ] && FINAL_STATUS="failed"

FINAL_PAYLOAD=$(cat <<EOF
{
    "timestamp": "$(date --iso-8601=seconds)",
    "status": "$FINAL_STATUS",
    "exit_code": $RC,
    "workdir": "$WORKDIR",
    "hours": $HOURS,
    "workers": $WORKERS,
    "golden_files": $(find "$ART" -name "*.jsonl" 2>/dev/null | wc -l),
    "artifact_size": "$(du -h "$ARTIFACT_TAR" 2>/dev/null | cut -f1 || echo 'unknown')",
    "log_tail": "$(tail -n 50 "$LOG" | sed 's/"/\\"/g' | tr '\n' ' ' | head -c 2000)"
}
EOF
)

if [ -n "${SHADOW_HOOK:-}" ]; then
    log_info "Sending final notification to webhook..."
    curl -sS -X POST -H "Content-Type: application/json" -d "$FINAL_PAYLOAD" "$SHADOW_HOOK" || true

    # Optionally upload artifacts to transfer.sh
    if [ -f "$ARTIFACT_TAR" ] && [ "${UPLOAD_ARTIFACTS:-true}" = "true" ]; then
        log_info "Uploading artifacts to transfer.sh..."
        UPLOAD_URL=$(curl -sS --upload-file "$ARTIFACT_TAR" "https://transfer.sh/m4-shadow-$(date +%Y%m%d).tgz" 2>/dev/null || echo "")
        if [ -n "$UPLOAD_URL" ]; then
            log_info "Artifacts uploaded: $UPLOAD_URL"
            curl -sS -X POST -H "Content-Type: application/json" \
                -d "{\"artifact_url\": \"$UPLOAD_URL\"}" "$SHADOW_HOOK" || true
        else
            log_warn "Failed to upload artifacts to transfer.sh"
        fi
    fi
fi

# Final summary
echo ""
log_info "═══════════════════════════════════════════════════════════════"
if [ $RC -eq 0 ]; then
    log_info "         ✅ SHADOW RUN COMPLETED SUCCESSFULLY"
else
    log_error "         ❌ SHADOW RUN FAILED (exit code: $RC)"
fi
log_info "═══════════════════════════════════════════════════════════════"
log_info "  Artifacts: $WORKDIR"
log_info "  Log:       $LOG"
log_info "  Summary:   $SUMMARY_FILE"
log_info "═══════════════════════════════════════════════════════════════"

exit $RC
