#!/bin/bash
# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Role: Weekly system bloat audit — reviews memory, disk, journals, processes
# Schedule: cron weekly (Sunday 03:00) or on-demand
# Output: stdout (for session_start.sh) + archived report

set -euo pipefail

ROOT="/root/agenticverz2.0"
REPORT_DIR="$ROOT/docs/ops-reports/bloat-audits"
TIMESTAMP=$(date '+%Y-%m-%d_%H%M')
DATE_HUMAN=$(date '+%Y-%m-%d %H:%M:%S')

# Thresholds (trigger warnings)
JOURNAL_WARN_MB=180
PROCESS_WARN_MB=300
TOTAL_USED_WARN_GB=6

# Ensure report dir exists
mkdir -p "$REPORT_DIR"

# =============================================================================
# Collectors
# =============================================================================

collect_memory() {
    free -m | awk '/Mem:/ {
        printf "total_mb=%s used_mb=%s free_mb=%s available_mb=%s\n", $2, $3, $4, $7
    }'
}

collect_journal() {
    journalctl --disk-usage 2>/dev/null | grep -oP '[0-9.]+[MG]' | head -1
}

collect_top_processes() {
    ps aux --sort=-%mem | awk 'NR<=11 && NR>1 {
        printf "%s|%s|%s|%s\n", $11, $6/1024, $4, $1
    }'
}

collect_amavis() {
    local count rss_total
    count=$(ps aux | grep -c "[a]mavisd" || echo 0)
    rss_total=$(ps aux | grep "[a]mavisd" | awk '{sum+=$6} END {printf "%.0f", sum/1024}')
    echo "${count}|${rss_total:-0}"
}

collect_worker_pool() {
    if ps aux | grep -q "[a]pp.worker.pool"; then
        local rss
        rss=$(ps aux | grep "[a]pp.worker.pool" | awk '{sum+=$6} END {printf "%.0f", sum/1024}')
        echo "running|${rss}"
    else
        echo "stopped|0"
    fi
}

collect_validator_daemon() {
    if ps aux | grep -q "[c]ontinuous_validator"; then
        local rss
        rss=$(ps aux | grep "[c]ontinuous_validator" | awk '{sum+=$6} END {printf "%.0f", sum/1024}')
        echo "running|${rss}"
    else
        echo "stopped|0"
    fi
}

# =============================================================================
# Run audit
# =============================================================================

MEM=$(collect_memory)
TOTAL_MB=$(echo "$MEM" | grep -oP 'total_mb=\K[0-9]+')
USED_MB=$(echo "$MEM" | grep -oP 'used_mb=\K[0-9]+')
AVAIL_MB=$(echo "$MEM" | grep -oP 'available_mb=\K[0-9]+')

JOURNAL_SIZE=$(collect_journal)
JOURNAL_MB=$(echo "$JOURNAL_SIZE" | sed 's/G/*1024/' | sed 's/M//' | bc 2>/dev/null || echo 0)

AMAVIS_INFO=$(collect_amavis)
AMAVIS_COUNT=$(echo "$AMAVIS_INFO" | cut -d'|' -f1)
AMAVIS_MB=$(echo "$AMAVIS_INFO" | cut -d'|' -f2)

WORKER_INFO=$(collect_worker_pool)
WORKER_STATUS=$(echo "$WORKER_INFO" | cut -d'|' -f1)
WORKER_MB=$(echo "$WORKER_INFO" | cut -d'|' -f2)

VALIDATOR_INFO=$(collect_validator_daemon)
VALIDATOR_STATUS=$(echo "$VALIDATOR_INFO" | cut -d'|' -f1)
VALIDATOR_MB=$(echo "$VALIDATOR_INFO" | cut -d'|' -f2)

# =============================================================================
# Evaluate warnings
# =============================================================================

WARNINGS=0
WARNING_LIST=""

USED_GB=$((USED_MB / 1024))
if [ "$USED_GB" -ge "$TOTAL_USED_WARN_GB" ]; then
    WARNINGS=$((WARNINGS + 1))
    WARNING_LIST="${WARNING_LIST}\n  - RAM used ${USED_GB}Gi exceeds ${TOTAL_USED_WARN_GB}Gi threshold"
fi

if [ "${JOURNAL_MB%.*}" -ge "$JOURNAL_WARN_MB" ] 2>/dev/null; then
    WARNINGS=$((WARNINGS + 1))
    WARNING_LIST="${WARNING_LIST}\n  - Journal size ${JOURNAL_SIZE} exceeds ${JOURNAL_WARN_MB}MB threshold"
fi

if [ "$AMAVIS_COUNT" -gt 2 ]; then
    WARNINGS=$((WARNINGS + 1))
    WARNING_LIST="${WARNING_LIST}\n  - Amavis has ${AMAVIS_COUNT} processes (expected <=2)"
fi

if [ "$AMAVIS_MB" -gt "$PROCESS_WARN_MB" ]; then
    WARNINGS=$((WARNINGS + 1))
    WARNING_LIST="${WARNING_LIST}\n  - Amavis using ${AMAVIS_MB}MB (threshold ${PROCESS_WARN_MB}MB)"
fi

if [ "$WORKER_STATUS" = "running" ] && [ "$WORKER_MB" -gt "$PROCESS_WARN_MB" ]; then
    WARNINGS=$((WARNINGS + 1))
    WARNING_LIST="${WARNING_LIST}\n  - Worker pool using ${WORKER_MB}MB (threshold ${PROCESS_WARN_MB}MB)"
fi

if [ "$VALIDATOR_STATUS" = "running" ]; then
    WARNINGS=$((WARNINGS + 1))
    WARNING_LIST="${WARNING_LIST}\n  - continuous_validator daemon is running (should use cron scan instead, PIN-474)"
fi

# =============================================================================
# Banner output (for session_start.sh / terminal)
# =============================================================================

if [ "${1:-}" != "--quiet" ]; then
    echo ""
    if [ "$WARNINGS" -gt 0 ]; then
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║  ⚠  SYSTEM BLOAT AUDIT — ${WARNINGS} WARNING(S)                       ║"
        echo "╠══════════════════════════════════════════════════════════════╣"
    else
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║  ✓  SYSTEM BLOAT AUDIT — CLEAN                             ║"
        echo "╠══════════════════════════════════════════════════════════════╣"
    fi
    printf "║  %-60s║\n" "RAM: ${USED_MB}MB / ${TOTAL_MB}MB (${AVAIL_MB}MB available)"
    printf "║  %-60s║\n" "Journal: ${JOURNAL_SIZE} (limit: 200M, retain: 7d)"
    printf "║  %-60s║\n" "Amavis: ${AMAVIS_COUNT} proc, ${AMAVIS_MB}MB"
    printf "║  %-60s║\n" "Worker pool: ${WORKER_STATUS} (${WORKER_MB}MB)"
    printf "║  %-60s║\n" "Validator daemon: ${VALIDATOR_STATUS} (${VALIDATOR_MB}MB)"

    # Top 5 processes by memory
    echo "║                                                              ║"
    printf "║  %-60s║\n" "Top 5 by memory:"
    collect_top_processes | head -5 | while IFS='|' read -r cmd mb pct user; do
        cmd_short=$(echo "$cmd" | sed 's|.*/||' | cut -c1-25)
        printf "║    %-23s %6.0fMB  %5s%%  %-12s  ║\n" "$cmd_short" "$mb" "$pct" "$user"
    done

    if [ "$WARNINGS" -gt 0 ]; then
        echo "║                                                              ║"
        printf "║  %-60s║\n" "Warnings:"
        echo -e "$WARNING_LIST" | while read -r line; do
            [ -z "$line" ] && continue
            printf "║  %-60s║\n" "$line"
        done
    fi

    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
fi

# =============================================================================
# Archive report (markdown)
# =============================================================================

REPORT_FILE="$REPORT_DIR/bloat-audit-${TIMESTAMP}.md"

cat > "$REPORT_FILE" << EOF
# System Bloat Audit — ${DATE_HUMAN}

## Status: $([ "$WARNINGS" -gt 0 ] && echo "⚠ ${WARNINGS} WARNING(S)" || echo "✓ CLEAN")

## Memory
| Metric | Value |
|--------|-------|
| Total | ${TOTAL_MB} MB |
| Used | ${USED_MB} MB |
| Available | ${AVAIL_MB} MB |

## Tracked Services
| Service | Status | Memory |
|---------|--------|--------|
| Amavis | ${AMAVIS_COUNT} processes | ${AMAVIS_MB} MB |
| Worker pool | ${WORKER_STATUS} | ${WORKER_MB} MB |
| Validator daemon | ${VALIDATOR_STATUS} | ${VALIDATOR_MB} MB |
| Journal | — | ${JOURNAL_SIZE} on disk |

## Top Processes by Memory
| Process | RSS (MB) | %MEM | User |
|---------|----------|------|------|
$(collect_top_processes | head -10 | while IFS='|' read -r cmd mb pct user; do
    cmd_short=$(echo "$cmd" | sed 's|.*/||' | cut -c1-40)
    printf "| %s | %.0f | %s | %s |\n" "$cmd_short" "$mb" "$pct" "$user"
done)

## Warnings
$(if [ "$WARNINGS" -gt 0 ]; then
    echo -e "$WARNING_LIST" | while read -r line; do
        [ -z "$line" ] && continue
        echo "- $line"
    done
else
    echo "None"
fi)

## Thresholds
| Check | Threshold | Current | Status |
|-------|-----------|---------|--------|
| RAM used | <${TOTAL_USED_WARN_GB}Gi | ${USED_GB}Gi | $([ "$USED_GB" -lt "$TOTAL_USED_WARN_GB" ] && echo "✓" || echo "⚠") |
| Journal size | <${JOURNAL_WARN_MB}MB | ${JOURNAL_SIZE} | $([ "${JOURNAL_MB%.*}" -lt "$JOURNAL_WARN_MB" ] 2>/dev/null && echo "✓" || echo "⚠") |
| Amavis memory | <${PROCESS_WARN_MB}MB | ${AMAVIS_MB}MB | $([ "$AMAVIS_MB" -lt "$PROCESS_WARN_MB" ] && echo "✓" || echo "⚠") |
| Amavis processes | <=2 | ${AMAVIS_COUNT} | $([ "$AMAVIS_COUNT" -le 2 ] && echo "✓" || echo "⚠") |
| Validator daemon | stopped | ${VALIDATOR_STATUS} | $([ "$VALIDATOR_STATUS" = "stopped" ] && echo "✓" || echo "⚠") |

## Reference PINs
- PIN-474: continuous_validator → scheduled scan
- PIN-475: Worker pool manual restart model
- PIN-476: Amavis optimization
- PIN-477: Journal limits + bloat audit
EOF

# Keep only last 12 reports (3 months of weekly)
ls -t "$REPORT_DIR"/bloat-audit-*.md 2>/dev/null | tail -n +13 | xargs rm -f 2>/dev/null || true

echo "Report archived: $REPORT_FILE"

exit "$WARNINGS"
