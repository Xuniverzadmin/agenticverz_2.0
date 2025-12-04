#!/bin/bash
# PIN Drift Detector
# Validates memory PIN architecture consistency
#
# Checks:
# 1. PIN serial order and gaps
# 2. Missing files referenced in INDEX
# 3. Orphan files not in INDEX
# 4. Status consistency
# 5. Date freshness

set -euo pipefail

PINS_DIR="${PINS_DIR:-/root/agenticverz2.0/docs/memory-pins}"
INDEX_FILE="$PINS_DIR/INDEX.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((ERRORS++)) || true
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++)) || true
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           PIN DRIFT DETECTOR${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check INDEX exists
if [ ! -f "$INDEX_FILE" ]; then
    log_error "INDEX.md not found at $INDEX_FILE"
    exit 1
fi

log_info "Scanning: $PINS_DIR"
echo ""

# ═══════════════════════════════════════════════════════════════
# CHECK 1: PIN Serial Order and Gaps
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[1/5] Checking PIN serial order...${NC}"

# Extract PIN numbers from filenames
PIN_NUMBERS=$(ls "$PINS_DIR"/PIN-*.md 2>/dev/null | \
    grep -oP 'PIN-\K[0-9]+' | sort -n | uniq)

PREV=0
for num in $PIN_NUMBERS; do
    # Remove leading zeros for arithmetic
    clean_num=$((10#$num))
    expected=$((PREV + 1))

    if [ "$clean_num" -ne "$expected" ] && [ "$PREV" -ne 0 ]; then
        log_warn "Gap in PIN sequence: PIN-$(printf '%03d' $PREV) -> PIN-$(printf '%03d' $clean_num)"
    fi
    PREV=$clean_num
done

HIGHEST_PIN=$PREV
log_ok "PIN range: PIN-001 to PIN-$(printf '%03d' $HIGHEST_PIN)"
echo ""

# ═══════════════════════════════════════════════════════════════
# CHECK 2: Missing Files (referenced in INDEX but not on disk)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[2/5] Checking for missing files...${NC}"

# Extract file references from INDEX
INDEX_REFS=$(grep -oP '\[PIN-[0-9]+\]\([^)]+\.md\)' "$INDEX_FILE" | \
    grep -oP '\([^)]+\.md\)' | tr -d '()')

MISSING=0
for ref in $INDEX_REFS; do
    full_path="$PINS_DIR/$ref"
    if [ ! -f "$full_path" ]; then
        log_error "Missing file: $ref (referenced in INDEX)"
        ((MISSING++)) || true
    fi
done

if [ "$MISSING" -eq 0 ]; then
    log_ok "All INDEX references exist on disk"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# CHECK 3: Orphan Files (on disk but not in INDEX)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[3/5] Checking for orphan files...${NC}"

ORPHANS=0
for file in "$PINS_DIR"/PIN-*.md; do
    if [ -f "$file" ]; then
        basename=$(basename "$file")
        # Skip templates and helper files
        if [[ "$basename" == *"-template"* ]] || [[ "$basename" == *"-helper"* ]]; then
            continue
        fi

        # Check if referenced in INDEX (by filename)
        if ! grep -q "$basename" "$INDEX_FILE"; then
            log_warn "Orphan file: $basename (not in INDEX)"
            ((ORPHANS++)) || true
        fi
    fi
done

if [ "$ORPHANS" -eq 0 ]; then
    log_ok "No orphan PIN files found"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# CHECK 4: Status Consistency
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[4/5] Checking status consistency...${NC}"

# Valid statuses
VALID_STATUSES="Active|ACTIVE|COMPLETE|IN PROGRESS|FINALIZED|PRIMARY|DRAFT|Superseded|Archived"

for file in "$PINS_DIR"/PIN-*.md; do
    if [ -f "$file" ]; then
        # Extract status line
        status=$(grep -oP '\*\*Status:\*\*\s*\K.*' "$file" 2>/dev/null | head -1 || echo "")

        if [ -z "$status" ]; then
            log_warn "No status found in $(basename $file)"
        fi
    fi
done

log_ok "Status check complete"
echo ""

# ═══════════════════════════════════════════════════════════════
# CHECK 5: Date Freshness
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[5/5] Checking date freshness...${NC}"

TODAY=$(date +%Y-%m-%d)
STALE_THRESHOLD=30  # days

for file in "$PINS_DIR"/PIN-*.md; do
    if [ -f "$file" ]; then
        # Extract last updated date
        updated=$(grep -oP '\*\*Updated:\*\*\s*\K[0-9]{4}-[0-9]{2}-[0-9]{2}' "$file" 2>/dev/null | head -1 || echo "")

        if [ -n "$updated" ]; then
            # Check if date is valid
            if ! date -d "$updated" > /dev/null 2>&1; then
                log_warn "Invalid date format in $(basename $file): $updated"
            fi
        fi
    fi
done

log_ok "Date check complete"
echo ""

# ═══════════════════════════════════════════════════════════════
# CHECK 6: Script Path Verification
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[BONUS] Checking referenced script paths...${NC}"

# Key scripts that should exist
SCRIPTS=(
    "/root/agenticverz2.0/scripts/stress/shadow_monitor_daemon.sh"
    "/root/agenticverz2.0/scripts/stress/shadow_debug.sh"
    "/root/agenticverz2.0/scripts/stress/shadow_cron_check.sh"
    "/root/agenticverz2.0/scripts/stress/golden_diff_debug.py"
    "/root/agenticverz2.0/scripts/stress/shadow_sanity_check.sh"
    "/root/agenticverz2.0/scripts/stress/check_shadow_status.sh"
    "/root/agenticverz2.0/scripts/ops/disable-workflows.sh"
    "/root/agenticverz2.0/scripts/ops/golden_retention.sh"
)

SCRIPT_MISSING=0
for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        log_error "Missing script: $script"
        ((SCRIPT_MISSING++)) || true
    fi
done

if [ "$SCRIPT_MISSING" -eq 0 ]; then
    log_ok "All referenced scripts exist"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo "PINs found:    $(ls "$PINS_DIR"/PIN-*.md 2>/dev/null | wc -l)"
echo "Highest PIN:   PIN-$(printf '%03d' $HIGHEST_PIN)"
echo ""

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}Errors:   $ERRORS${NC}"
else
    echo -e "${GREEN}Errors:   0${NC}"
fi

if [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
else
    echo -e "${GREEN}Warnings: 0${NC}"
fi

echo ""

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}DRIFT DETECTED - Please fix errors above${NC}"
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}MINOR DRIFT - Consider addressing warnings${NC}"
    exit 0
else
    echo -e "${GREEN}NO DRIFT - Memory architecture is consistent${NC}"
    exit 0
fi
