#!/bin/bash
# =============================================================================
# AOS Hygiene Check - Automated Context Health
# =============================================================================
# Run weekly (or on-demand) to detect context drift and staleness.
# Designed to be run by cron or CI.
#
# Usage: ./scripts/ops/hygiene_check.sh [--fix] [--json]
#
# Options:
#   --fix   Attempt auto-fixes where possible
#   --json  Output results as JSON (for CI integration)
# =============================================================================

set -e

cd "$(dirname "$0")/../.." || exit 1
ROOT=$(pwd)

FIX_MODE=false
JSON_MODE=false
for arg in "$@"; do
    case $arg in
        --fix) FIX_MODE=true ;;
        --json) JSON_MODE=true ;;
    esac
done

ISSUES=0
WARNINGS=0
FIXES=0

# Output helper
log() {
    if [ "$JSON_MODE" = false ]; then
        echo "$1"
    fi
}

# -----------------------------------------------------------------------------
# Check 1: Working environment structure
# -----------------------------------------------------------------------------
check_working_env() {
    log "[Check 1] Working environment structure..."

    REQUIRED_FILES=(
        "agentiverz_mn/README.md"
        "agentiverz_mn/milestone_plan.md"
        "agentiverz_mn/repo_snapshot.md"
    )

    for f in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$f" ]; then
            log "  ERROR: Missing required file: $f"
            ISSUES=$((ISSUES+1))
        fi
    done

    if [ "$ISSUES" -eq 0 ]; then
        log "  OK: Working environment structure valid"
    fi
}

# -----------------------------------------------------------------------------
# Check 2: PIN count and age
# -----------------------------------------------------------------------------
check_pins() {
    log ""
    log "[Check 2] PIN hygiene..."

    PIN_COUNT=$(ls docs/memory-pins/PIN-*.md 2>/dev/null | wc -l)
    log "  Total PINs: $PIN_COUNT"

    if [ "$PIN_COUNT" -gt 50 ]; then
        log "  ERROR: Too many PINs ($PIN_COUNT > 50) - archive old ones"
        ISSUES=$((ISSUES+1))
    elif [ "$PIN_COUNT" -gt 40 ]; then
        log "  WARN: Many PINs ($PIN_COUNT) - consider archiving"
        WARNINGS=$((WARNINGS+1))
    fi

    # Check for very old active PINs (>30 days without update)
    OLD_PINS=$(find docs/memory-pins -name "PIN-*.md" -mtime +30 2>/dev/null | wc -l)
    if [ "$OLD_PINS" -gt 10 ]; then
        log "  WARN: $OLD_PINS PINs not updated in >30 days"
        WARNINGS=$((WARNINGS+1))
    fi
}

# -----------------------------------------------------------------------------
# Check 3: Stale checklists
# -----------------------------------------------------------------------------
check_checklists() {
    log ""
    log "[Check 3] Checklist freshness..."

    for f in agentiverz_mn/*checklist*.md; do
        [ -f "$f" ] || continue

        NAME=$(basename "$f" .md)
        DAYS_OLD=$(( ($(date +%s) - $(stat -c %Y "$f")) / 86400 ))

        # Check completion status
        TOTAL=$(grep -E "^- \[ \]|^- \[x\]" "$f" 2>/dev/null | wc -l)
        DONE=$(grep -E "^- \[x\]" "$f" 2>/dev/null | wc -l)
        TOTAL=${TOTAL:-0}
        DONE=${DONE:-0}

        if [ "$TOTAL" -gt 0 ]; then
            PCT=$((DONE * 100 / TOTAL))

            # 100% complete but not archived
            if [ "$PCT" -eq 100 ]; then
                log "  WARN: $NAME is 100% complete - should be archived"
                WARNINGS=$((WARNINGS+1))

                if [ "$FIX_MODE" = true ]; then
                    ARCHIVE_DIR="agentiverz_mn/archive"
                    mkdir -p "$ARCHIVE_DIR"
                    mv "$f" "$ARCHIVE_DIR/"
                    log "  FIX: Moved to $ARCHIVE_DIR/"
                    FIXES=$((FIXES+1))
                fi
            fi

            # Stale and incomplete
            if [ "$DAYS_OLD" -gt 14 ] && [ "$PCT" -lt 100 ]; then
                log "  WARN: $NAME is $DAYS_OLD days old and only $PCT% complete"
                WARNINGS=$((WARNINGS+1))
            fi
        fi
    done

    if [ "$WARNINGS" -eq 0 ]; then
        log "  OK: All checklists current"
    fi
}

# -----------------------------------------------------------------------------
# Check 4: INDEX.md freshness
# -----------------------------------------------------------------------------
check_index() {
    log ""
    log "[Check 4] INDEX.md freshness..."

    if [ ! -f "docs/memory-pins/INDEX.md" ]; then
        log "  ERROR: INDEX.md missing"
        ISSUES=$((ISSUES+1))
        return
    fi

    DAYS_OLD=$(( ($(date +%s) - $(stat -c %Y "docs/memory-pins/INDEX.md")) / 86400 ))

    if [ "$DAYS_OLD" -gt 7 ]; then
        log "  ERROR: INDEX.md not updated in $DAYS_OLD days"
        ISSUES=$((ISSUES+1))
    elif [ "$DAYS_OLD" -gt 3 ]; then
        log "  WARN: INDEX.md not updated in $DAYS_OLD days"
        WARNINGS=$((WARNINGS+1))
    else
        log "  OK: INDEX.md updated $DAYS_OLD days ago"
    fi

    # Check if changelog is current
    LAST_CHANGELOG=$(grep "^| 202" docs/memory-pins/INDEX.md | head -1 | cut -d'|' -f2 | tr -d ' ')
    TODAY=$(date +%Y-%m-%d)
    YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

    if [ "$LAST_CHANGELOG" != "$TODAY" ] && [ "$LAST_CHANGELOG" != "$YESTERDAY" ]; then
        log "  WARN: Last changelog entry is $LAST_CHANGELOG (may be stale)"
        WARNINGS=$((WARNINGS+1))
    fi
}

# -----------------------------------------------------------------------------
# Check 5: repo_snapshot.md accuracy
# -----------------------------------------------------------------------------
check_snapshot() {
    log ""
    log "[Check 5] Repo snapshot accuracy..."

    SNAPSHOT="agentiverz_mn/repo_snapshot.md"
    if [ ! -f "$SNAPSHOT" ]; then
        log "  ERROR: repo_snapshot.md missing"
        ISSUES=$((ISSUES+1))
        return
    fi

    DAYS_OLD=$(( ($(date +%s) - $(stat -c %Y "$SNAPSHOT")) / 86400 ))

    if [ "$DAYS_OLD" -gt 7 ]; then
        log "  WARN: repo_snapshot.md is $DAYS_OLD days old - may be outdated"
        WARNINGS=$((WARNINGS+1))
    else
        log "  OK: repo_snapshot.md is $DAYS_OLD days old"
    fi

    # Check if documented services match running services
    if command -v docker &> /dev/null; then
        RUNNING=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -c "nova" || echo "0")
        DOCUMENTED=$(grep -c "nova_" "$SNAPSHOT" 2>/dev/null || echo "0")

        if [ "$RUNNING" -ne "$DOCUMENTED" ]; then
            log "  WARN: Running services ($RUNNING) don't match documented ($DOCUMENTED)"
            WARNINGS=$((WARNINGS+1))
        fi
    fi
}

# -----------------------------------------------------------------------------
# Check 6: Orphaned files
# -----------------------------------------------------------------------------
check_orphans() {
    log ""
    log "[Check 6] Orphaned/temporary files..."

    # Check for temp files in project root
    TEMP_FILES=$(find . -maxdepth 1 -name "*.tmp" -o -name "*.bak" -o -name "*~" 2>/dev/null | wc -l)
    if [ "$TEMP_FILES" -gt 0 ]; then
        log "  WARN: $TEMP_FILES temporary files in project root"
        WARNINGS=$((WARNINGS+1))

        if [ "$FIX_MODE" = true ]; then
            find . -maxdepth 1 \( -name "*.tmp" -o -name "*.bak" -o -name "*~" \) -delete
            log "  FIX: Removed temporary files"
            FIXES=$((FIXES+1))
        fi
    fi

    # Check for empty directories in agentiverz_mn
    EMPTY_DIRS=$(find agentiverz_mn -type d -empty 2>/dev/null | wc -l)
    if [ "$EMPTY_DIRS" -gt 0 ]; then
        log "  WARN: $EMPTY_DIRS empty directories in agentiverz_mn/"
        WARNINGS=$((WARNINGS+1))
    fi

    if [ "$TEMP_FILES" -eq 0 ] && [ "$EMPTY_DIRS" -eq 0 ]; then
        log "  OK: No orphaned files"
    fi
}

# -----------------------------------------------------------------------------
# Check 7: CLAUDE.md sync
# -----------------------------------------------------------------------------
check_claude_md() {
    log ""
    log "[Check 7] CLAUDE.md configuration..."

    if [ ! -f "CLAUDE.md" ]; then
        log "  ERROR: CLAUDE.md missing from project root"
        ISSUES=$((ISSUES+1))
        return
    fi

    # Check if session protocol is documented
    if ! grep -q "session_start.sh\|Session Start Protocol" CLAUDE.md 2>/dev/null; then
        log "  WARN: CLAUDE.md doesn't mention session start protocol"
        WARNINGS=$((WARNINGS+1))
    else
        log "  OK: Session protocol documented"
    fi
}

# -----------------------------------------------------------------------------
# Run all checks
# -----------------------------------------------------------------------------
log "=============================================="
log "  AOS Hygiene Check"
log "  $(date '+%Y-%m-%d %H:%M:%S')"
log "=============================================="

check_working_env
check_pins
check_checklists
check_index
check_snapshot
check_orphans
check_claude_md

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log ""
log "=============================================="
log "  Summary"
log "=============================================="
log "  Errors:   $ISSUES"
log "  Warnings: $WARNINGS"
if [ "$FIX_MODE" = true ]; then
    log "  Fixes:    $FIXES"
fi

# JSON output for CI
if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "issues": $ISSUES,
  "warnings": $WARNINGS,
  "fixes": $FIXES,
  "status": "$([ "$ISSUES" -eq 0 ] && echo "pass" || echo "fail")"
}
EOF
fi

log ""
if [ "$ISSUES" -gt 0 ]; then
    log "  STATUS: FAIL"
    exit 1
elif [ "$WARNINGS" -gt 5 ]; then
    log "  STATUS: WARN (many warnings)"
    exit 0
else
    log "  STATUS: PASS"
    exit 0
fi
