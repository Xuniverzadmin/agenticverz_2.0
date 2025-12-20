#!/bin/bash
# =============================================================================
# dev_sync.sh - Development Sync & Consistency Checker
# =============================================================================
#
# PURPOSE: Auto-detect code changes and rebuild containers/assets as needed.
# RUN BEFORE: Starting any coding session
# RUN AFTER:  Finishing code changes (or use --watch mode)
#
# Usage:
#   ./scripts/ops/dev_sync.sh           # Check and rebuild if needed
#   ./scripts/ops/dev_sync.sh --force   # Force rebuild everything
#   ./scripts/ops/dev_sync.sh --check   # Check only, no rebuild
#   ./scripts/ops/dev_sync.sh --watch   # Watch mode (auto-rebuild on changes)
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.dev_sync"
BACKEND_HASH_FILE="$STATE_DIR/backend.hash"
FRONTEND_HASH_FILE="$STATE_DIR/frontend.hash"
WEBSITE_HASH_FILE="$STATE_DIR/website.hash"

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_action() {
    echo -e "${YELLOW}[ACTION]${NC} $1"
}

# Calculate hash of directory (excluding __pycache__, .pyc, etc.)
calc_hash() {
    local dir="$1"
    if [ -d "$dir" ]; then
        # Use simpler find with grep exclusions
        find "$dir" -type f -name "*.py" 2>/dev/null | \
            grep -v "__pycache__" | \
            grep -v ".pytest_cache" | \
            head -500 | \
            xargs md5sum 2>/dev/null | \
            sort | md5sum | cut -d' ' -f1
    else
        echo "missing"
    fi
}

# Calculate hash for JS/TS projects
calc_hash_js() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) 2>/dev/null | \
            grep -v "node_modules" | \
            grep -v ".next" | \
            grep -v "dist" | \
            head -500 | \
            xargs md5sum 2>/dev/null | \
            sort | md5sum | cut -d' ' -f1
    else
        echo "missing"
    fi
}

get_stored_hash() {
    local file="$1"
    if [ -f "$file" ]; then
        cat "$file"
    else
        echo "none"
    fi
}

store_hash() {
    local file="$1"
    local hash="$2"
    echo "$hash" > "$file"
}

# Check if container is running with latest image
check_container_sync() {
    local container="$1"
    local current_image=$(docker inspect --format='{{.Image}}' "$container" 2>/dev/null || echo "none")
    local built_image=$(docker images --format '{{.ID}}' "${container}" 2>/dev/null | head -1 || echo "none")

    if [ "$current_image" != "none" ] && [ "$built_image" != "none" ]; then
        if [ "$current_image" == "sha256:$built_image" ] || [[ "$current_image" == *"$built_image"* ]]; then
            return 0  # In sync
        fi
    fi
    return 1  # Out of sync
}

# =============================================================================
# Sync Checks
# =============================================================================

check_backend() {
    local current_hash=$(calc_hash "$PROJECT_ROOT/backend")
    local stored_hash=$(get_stored_hash "$BACKEND_HASH_FILE")

    if [ "$current_hash" != "$stored_hash" ]; then
        log_warning "Backend code changed since last sync"
        return 1
    fi

    # Also check if container is running latest
    if ! docker ps --format '{{.Names}}' | grep -q "nova_agent_manager"; then
        log_warning "Backend container not running"
        return 1
    fi

    return 0
}

check_frontend() {
    local console_dir="$PROJECT_ROOT/website/aos-console/console"
    if [ ! -d "$console_dir/src" ]; then
        return 0  # No frontend to check
    fi

    local current_hash=$(calc_hash_js "$console_dir/src")
    local stored_hash=$(get_stored_hash "$FRONTEND_HASH_FILE")

    if [ "$current_hash" != "$stored_hash" ]; then
        log_warning "Console frontend code changed since last sync"
        return 1
    fi

    return 0
}

check_website() {
    local landing_dir="$PROJECT_ROOT/website/landing"
    if [ ! -d "$landing_dir/src" ]; then
        return 0  # No website to check
    fi

    local current_hash=$(calc_hash_js "$landing_dir/src")
    local stored_hash=$(get_stored_hash "$WEBSITE_HASH_FILE")

    if [ "$current_hash" != "$stored_hash" ]; then
        log_warning "Website landing code changed since last sync"
        return 1
    fi

    return 0
}

# =============================================================================
# Rebuild Actions
# =============================================================================

rebuild_backend() {
    log_action "Rebuilding backend container..."
    cd "$PROJECT_ROOT"

    # Syntax check first
    if ! python3 -c "import ast; ast.parse(open('backend/app/main.py').read())" 2>/dev/null; then
        log_error "Backend syntax error in main.py - aborting rebuild"
        return 1
    fi

    # Check key files
    for file in backend/app/api/ops.py backend/app/api/guard.py backend/app/api/operator.py; do
        if [ -f "$file" ]; then
            if ! python3 -c "import ast; ast.parse(open('$file').read())" 2>/dev/null; then
                log_error "Syntax error in $file - aborting rebuild"
                return 1
            fi
        fi
    done

    log_success "Syntax checks passed"

    # Rebuild
    docker compose up -d --build backend

    # Wait for health
    log_info "Waiting for backend health..."
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend healthy"

            # Update hash
            local new_hash=$(calc_hash "$PROJECT_ROOT/backend")
            store_hash "$BACKEND_HASH_FILE" "$new_hash"
            return 0
        fi
        sleep 1
    done

    log_error "Backend failed to become healthy"
    docker compose logs backend --tail 20
    return 1
}

rebuild_frontend() {
    local console_dir="$PROJECT_ROOT/website/aos-console/console"
    if [ ! -d "$console_dir" ]; then
        return 0
    fi

    log_action "Rebuilding console frontend..."
    cd "$console_dir"

    # Install deps if needed
    if [ ! -d "node_modules" ]; then
        npm install
    fi

    # Build
    if npm run build; then
        log_success "Frontend build complete"

        # Update hash
        local new_hash=$(calc_hash_js "$console_dir/src")
        store_hash "$FRONTEND_HASH_FILE" "$new_hash"
        return 0
    else
        log_error "Frontend build failed"
        return 1
    fi
}

rebuild_website() {
    local landing_dir="$PROJECT_ROOT/website/landing"
    if [ ! -d "$landing_dir/src" ]; then
        return 0
    fi

    log_action "Rebuilding website landing..."
    cd "$landing_dir"

    # Install deps if needed
    if [ ! -d "node_modules" ]; then
        npm install
    fi

    # Build
    if npm run build; then
        log_success "Website build complete"

        # Update hash
        local new_hash=$(calc_hash_js "$landing_dir/src")
        store_hash "$WEBSITE_HASH_FILE" "$new_hash"
        return 0
    else
        log_error "Website build failed"
        return 1
    fi
}

# =============================================================================
# Main Sync
# =============================================================================

do_sync() {
    local force="${1:-false}"
    local check_only="${2:-false}"
    local needs_rebuild=false

    echo ""
    echo "=============================================="
    echo "  DEV SYNC - Consistency Check"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="
    echo ""

    # Check backend
    echo "Checking backend..."
    if ! check_backend || [ "$force" == "true" ]; then
        needs_rebuild=true
        if [ "$check_only" == "true" ]; then
            log_warning "Backend needs rebuild"
        else
            rebuild_backend || exit 1
        fi
    else
        log_success "Backend in sync"
    fi

    # Check frontend
    echo ""
    echo "Checking frontend..."
    if ! check_frontend || [ "$force" == "true" ]; then
        if [ "$check_only" == "true" ]; then
            log_warning "Frontend needs rebuild"
        else
            rebuild_frontend || true  # Don't fail on frontend
        fi
    else
        log_success "Frontend in sync (or not present)"
    fi

    # Check website
    echo ""
    echo "Checking website..."
    if ! check_website || [ "$force" == "true" ]; then
        if [ "$check_only" == "true" ]; then
            log_warning "Website needs rebuild"
        else
            rebuild_website || true  # Don't fail on website
        fi
    else
        log_success "Website in sync (or not present)"
    fi

    echo ""
    echo "=============================================="
    if [ "$check_only" == "true" ]; then
        echo "  Check complete"
    else
        echo "  Sync complete"
    fi
    echo "=============================================="
    echo ""
}

# =============================================================================
# Watch Mode
# =============================================================================

watch_mode() {
    log_info "Starting watch mode (Ctrl+C to stop)..."
    log_info "Watching: backend/, website/aos-console/console/src/, website/landing/src/"
    echo ""

    # Initial sync
    do_sync false false

    # Watch for changes (using inotifywait if available, else polling)
    if command -v inotifywait &> /dev/null; then
        while true; do
            inotifywait -r -e modify,create,delete \
                "$PROJECT_ROOT/backend" \
                "$PROJECT_ROOT/website/aos-console/console/src" \
                "$PROJECT_ROOT/website/landing/src" \
                2>/dev/null || true

            echo ""
            log_info "Change detected, syncing..."
            sleep 2  # Debounce
            do_sync false false
        done
    else
        log_warning "inotifywait not found, using polling (every 10s)"
        while true; do
            sleep 10

            # Check if any hash changed
            local backend_changed=false
            local frontend_changed=false
            local website_changed=false

            check_backend || backend_changed=true
            check_frontend || frontend_changed=true
            check_website || website_changed=true

            if [ "$backend_changed" == "true" ] || [ "$frontend_changed" == "true" ] || [ "$website_changed" == "true" ]; then
                echo ""
                log_info "Change detected, syncing..."
                do_sync false false
            fi
        done
    fi
}

# =============================================================================
# Quick Health Check (for session start)
# =============================================================================

quick_check() {
    echo ""
    echo "Quick health check..."

    # Backend health
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend: healthy"
    else
        log_error "Backend: not responding"
        return 1
    fi

    # Key endpoints
    if curl -sf http://localhost:8000/ops/playbooks > /dev/null 2>&1; then
        log_success "Ops API: responding"
    else
        log_warning "Ops API: may need rebuild"
    fi

    echo ""
    return 0
}

# =============================================================================
# Entry Point
# =============================================================================

cd "$PROJECT_ROOT"

case "${1:-}" in
    --force|-f)
        do_sync true false
        ;;
    --check|-c)
        do_sync false true
        ;;
    --watch|-w)
        watch_mode
        ;;
    --quick|-q)
        quick_check
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  (no args)    Check and rebuild if needed"
        echo "  --force, -f  Force rebuild everything"
        echo "  --check, -c  Check only, no rebuild"
        echo "  --watch, -w  Watch mode (auto-rebuild on changes)"
        echo "  --quick, -q  Quick health check"
        echo "  --help, -h   Show this help"
        ;;
    *)
        do_sync false false
        ;;
esac
