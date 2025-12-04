#!/bin/bash
# Golden File Retention & Archival Script
# Manages golden file storage to prevent disk exhaustion

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_DIR="${ARCHIVE_DIR:-/root/archive/golden}"
GOLDEN_DIRS=(
    "/tmp/shadow_simulation_*/golden"
    "/var/lib/aos/golden"
)
RETENTION_DAYS="${RETENTION_DAYS:-7}"
LOG_FILE="/var/lib/aos/golden_retention.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

usage() {
    cat << EOF
Golden File Retention & Archival

Usage: $0 <command> [options]

Commands:
    status          Show current golden file usage
    archive         Archive old golden files (compress & move)
    cleanup         Delete golden files older than retention period
    verify          Verify archived files integrity
    restore <file>  Restore archived file to golden directory

Options:
    --days N        Retention period in days (default: 7)
    --dry-run       Show what would be done without doing it
    --force         Skip confirmation prompts

Environment:
    ARCHIVE_DIR     Archive location (default: /root/archive/golden)
    RETENTION_DAYS  Days to keep (default: 7)

Examples:
    $0 status
    $0 archive --days 1 --dry-run
    $0 cleanup --days 7
    $0 verify
EOF
}

cmd_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}           GOLDEN FILE STORAGE STATUS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Check each golden directory
    for pattern in "${GOLDEN_DIRS[@]}"; do
        for dir in $pattern; do
            if [ -d "$dir" ]; then
                local count=$(find "$dir" -name "*.json" -type f 2>/dev/null | wc -l)
                local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
                local oldest=$(find "$dir" -name "*.json" -type f -printf '%T+ %p\n' 2>/dev/null | sort | head -1 | cut -d' ' -f1)
                local newest=$(find "$dir" -name "*.json" -type f -printf '%T+ %p\n' 2>/dev/null | sort -r | head -1 | cut -d' ' -f1)

                echo -e "${GREEN}Directory:${NC} $dir"
                echo "  Files:    $count"
                echo "  Size:     $size"
                echo "  Oldest:   ${oldest:-N/A}"
                echo "  Newest:   ${newest:-N/A}"
                echo ""
            fi
        done
    done

    # Archive status
    if [ -d "$ARCHIVE_DIR" ]; then
        local archive_count=$(find "$ARCHIVE_DIR" -name "*.tgz" -o -name "*.tar.gz" 2>/dev/null | wc -l)
        local archive_size=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
        echo -e "${YELLOW}Archive Directory:${NC} $ARCHIVE_DIR"
        echo "  Archives: $archive_count"
        echo "  Size:     $archive_size"
    else
        echo -e "${YELLOW}Archive Directory:${NC} $ARCHIVE_DIR (not created)"
    fi

    echo ""

    # Disk usage
    echo -e "${BLUE}Disk Usage:${NC}"
    df -h /tmp /var/lib/aos /root 2>/dev/null | grep -v "^Filesystem"

    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

cmd_archive() {
    local days="${RETENTION_DAYS}"
    local dry_run=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --days) days="$2"; shift 2 ;;
            --dry-run) dry_run=true; shift ;;
            *) shift ;;
        esac
    done

    mkdir -p "$ARCHIVE_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)

    log "${BLUE}Archiving golden files older than $days days...${NC}"

    for pattern in "${GOLDEN_DIRS[@]}"; do
        for dir in $pattern; do
            if [ -d "$dir" ]; then
                local old_files=$(find "$dir" -name "*.json" -type f -mtime +$days 2>/dev/null)
                local count=$(echo "$old_files" | grep -c . || echo 0)

                if [ "$count" -gt 0 ]; then
                    local archive_name="golden_${timestamp}_$(basename $(dirname $dir)).tgz"

                    if [ "$dry_run" = true ]; then
                        log "${YELLOW}[DRY-RUN]${NC} Would archive $count files from $dir to $ARCHIVE_DIR/$archive_name"
                    else
                        log "Archiving $count files from $dir..."
                        echo "$old_files" | tar czf "$ARCHIVE_DIR/$archive_name" -T - 2>/dev/null || true

                        if [ -f "$ARCHIVE_DIR/$archive_name" ]; then
                            local archive_size=$(du -h "$ARCHIVE_DIR/$archive_name" | cut -f1)
                            log "${GREEN}Created:${NC} $ARCHIVE_DIR/$archive_name ($archive_size)"

                            # Remove archived files
                            echo "$old_files" | xargs rm -f 2>/dev/null || true
                            log "Removed $count archived files from $dir"
                        fi
                    fi
                else
                    log "No files older than $days days in $dir"
                fi
            fi
        done
    done

    log "${GREEN}Archive complete${NC}"
}

cmd_cleanup() {
    local days="${RETENTION_DAYS}"
    local dry_run=false
    local force=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --days) days="$2"; shift 2 ;;
            --dry-run) dry_run=true; shift ;;
            --force) force=true; shift ;;
            *) shift ;;
        esac
    done

    log "${YELLOW}Cleaning up golden files older than $days days...${NC}"

    local total_deleted=0

    for pattern in "${GOLDEN_DIRS[@]}"; do
        for dir in $pattern; do
            if [ -d "$dir" ]; then
                local old_files=$(find "$dir" -name "*.json" -type f -mtime +$days 2>/dev/null)
                local count=$(echo "$old_files" | grep -c . || echo 0)

                if [ "$count" -gt 0 ]; then
                    if [ "$dry_run" = true ]; then
                        log "${YELLOW}[DRY-RUN]${NC} Would delete $count files from $dir"
                    else
                        if [ "$force" = false ]; then
                            echo -e "${RED}About to delete $count files from $dir${NC}"
                            read -p "Continue? (y/N) " -n 1 -r
                            echo
                            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                                log "Skipped $dir"
                                continue
                            fi
                        fi

                        echo "$old_files" | xargs rm -f 2>/dev/null || true
                        log "${GREEN}Deleted $count files from $dir${NC}"
                        total_deleted=$((total_deleted + count))
                    fi
                fi
            fi
        done
    done

    log "${GREEN}Cleanup complete: $total_deleted files removed${NC}"
}

cmd_verify() {
    log "${BLUE}Verifying archived files...${NC}"

    if [ ! -d "$ARCHIVE_DIR" ]; then
        log "${YELLOW}No archive directory found${NC}"
        return 0
    fi

    local verified=0
    local failed=0

    for archive in "$ARCHIVE_DIR"/*.tgz "$ARCHIVE_DIR"/*.tar.gz; do
        if [ -f "$archive" ]; then
            if tar tzf "$archive" > /dev/null 2>&1; then
                local count=$(tar tzf "$archive" 2>/dev/null | wc -l)
                echo -e "${GREEN}✓${NC} $(basename $archive) - $count files"
                verified=$((verified + 1))
            else
                echo -e "${RED}✗${NC} $(basename $archive) - CORRUPTED"
                failed=$((failed + 1))
            fi
        fi
    done

    echo ""
    log "Verified: $verified, Failed: $failed"

    if [ "$failed" -gt 0 ]; then
        return 1
    fi
}

cmd_restore() {
    local archive="$1"
    local dest="${2:-/var/lib/aos/golden}"

    if [ ! -f "$archive" ]; then
        log "${RED}Archive not found: $archive${NC}"
        return 1
    fi

    mkdir -p "$dest"

    log "Restoring $archive to $dest..."
    tar xzf "$archive" -C "$dest"

    local count=$(tar tzf "$archive" | wc -l)
    log "${GREEN}Restored $count files to $dest${NC}"
}

# Main
case "${1:-}" in
    status)
        cmd_status
        ;;
    archive)
        shift
        cmd_archive "$@"
        ;;
    cleanup)
        shift
        cmd_cleanup "$@"
        ;;
    verify)
        cmd_verify
        ;;
    restore)
        shift
        cmd_restore "$@"
        ;;
    -h|--help|help|"")
        usage
        ;;
    *)
        echo "Unknown command: $1"
        usage
        exit 1
        ;;
esac
