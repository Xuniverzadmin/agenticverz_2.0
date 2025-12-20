#!/bin/bash
# deploy_website.sh - Deploy landing page and console with integrity validation
# Created: 2025-12-16 (Post-incident hardening)
#
# This script prevents the "wrong dist in wrong location" failure mode that
# caused the blank page incident on 2025-12-16.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Deployment targets
SITE_DIST="/opt/agenticverz/apps/site/dist"
CONSOLE_DIST="/opt/agenticverz/apps/console/dist"

# Source directories
LANDING_SRC="$PROJECT_ROOT/website/landing"
CONSOLE_SRC="$PROJECT_ROOT/website/aos-console/console"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate build artifacts before deployment
validate_landing_build() {
    local dist="$1"
    local index="$dist/index.html"

    if [[ ! -f "$index" ]]; then
        log_error "Landing dist missing index.html: $index"
        return 1
    fi

    # Fingerprint check
    if ! grep -q 'app-role" content="site-root"' "$index"; then
        log_error "Landing build missing fingerprint: app-role=\"site-root\""
        log_error "This is not a landing page build!"
        return 1
    fi

    # Must NOT have /console/ paths
    if grep -q '/console/assets/' "$index"; then
        log_error "Landing build has /console/ paths - this is a console build!"
        return 1
    fi

    log_info "Landing build validated: $dist"
    return 0
}

validate_console_build() {
    local dist="$1"
    local index="$dist/index.html"

    if [[ ! -f "$index" ]]; then
        log_error "Console dist missing index.html: $index"
        return 1
    fi

    # Fingerprint check
    if ! grep -q 'app-role" content="console-app"' "$index"; then
        log_error "Console build missing fingerprint: app-role=\"console-app\""
        log_error "This is not a console build!"
        return 1
    fi

    # Must have /console/ paths (built with base: '/console/')
    if ! grep -q '/console/assets/' "$index"; then
        log_error "Console build missing /console/ base path"
        return 1
    fi

    log_info "Console build validated: $dist"
    return 0
}

build_landing() {
    log_info "Building landing page..."
    cd "$LANDING_SRC"
    npm install --silent
    npm run build

    validate_landing_build "$LANDING_SRC/dist"
}

build_console() {
    log_info "Building console..."
    cd "$CONSOLE_SRC"
    npm install --silent
    npm run build

    validate_console_build "$CONSOLE_SRC/dist"
}

deploy() {
    log_info "Deploying to production paths..."

    # Validate source builds exist
    if [[ ! -d "$LANDING_SRC/dist" ]]; then
        log_error "Landing dist not found. Run: $0 --build"
        exit 1
    fi
    if [[ ! -d "$CONSOLE_SRC/dist" ]]; then
        log_error "Console dist not found. Run: $0 --build"
        exit 1
    fi

    # Validate builds before copying
    validate_landing_build "$LANDING_SRC/dist" || exit 1
    validate_console_build "$CONSOLE_SRC/dist" || exit 1

    # Deploy landing to site root
    log_info "Deploying landing → $SITE_DIST"
    rm -rf "$SITE_DIST"/*
    cp -r "$LANDING_SRC/dist"/* "$SITE_DIST/"
    chmod 644 "$SITE_DIST/logo.svg" 2>/dev/null || true
    chmod -R 755 "$SITE_DIST/assets" 2>/dev/null || true

    # Deploy console
    log_info "Deploying console → $CONSOLE_DIST"
    rm -rf "$CONSOLE_DIST"/*
    cp -r "$CONSOLE_SRC/dist"/* "$CONSOLE_DIST/"
    chmod 644 "$CONSOLE_DIST/logo.svg" 2>/dev/null || true
    chmod -R 755 "$CONSOLE_DIST/assets" 2>/dev/null || true

    # Post-deploy validation
    log_info "Post-deploy validation..."
    validate_landing_build "$SITE_DIST" || { log_error "Post-deploy validation failed for site!"; exit 1; }
    validate_console_build "$CONSOLE_DIST" || { log_error "Post-deploy validation failed for console!"; exit 1; }

    # Reload web server
    log_info "Reloading Apache..."
    systemctl reload apache2

    # Run smoke tests
    sleep 1  # Brief pause for Apache reload
    smoke_test || { log_error "Smoke tests failed! Deployment may be broken."; exit 1; }

    log_info "Deployment complete!"
    echo ""
    echo "  Site root: https://agenticverz.com"
    echo "  Console:   https://agenticverz.com/console/"
}

smoke_test() {
    log_info "Running smoke tests (user-path verification)..."

    local errors=0
    local BASE_URL="${SMOKE_TEST_URL:-https://agenticverz.com}"

    # Test 1: Site root title
    local site_title=$(curl -s "$BASE_URL" | grep -o '<title>[^<]*</title>' | head -1)
    if [[ "$site_title" == *"Agenticverz"* ]]; then
        log_info "✓ Site root title: OK"
    else
        log_error "✗ Site root title missing 'Agenticverz': $site_title"
        ((errors++))
    fi

    # Test 2: Site root JS loads as JavaScript
    local site_js=$(curl -s "$BASE_URL" | grep -oE 'src="/assets/index-[^"]+\.js"' | head -1 | sed 's/src="//;s/"//')
    if [[ -n "$site_js" ]]; then
        local js_type=$(curl -sI "$BASE_URL$site_js" | grep -i "content-type" | head -1)
        if [[ "$js_type" == *"javascript"* ]]; then
            log_info "✓ Site JS bundle: OK ($site_js)"
        else
            log_error "✗ Site JS wrong content-type: $js_type"
            ((errors++))
        fi
    else
        log_error "✗ Site JS bundle not found in HTML"
        ((errors++))
    fi

    # Test 3: Console title
    local console_title=$(curl -s "$BASE_URL/console/" | grep -o '<title>[^<]*</title>' | head -1)
    if [[ "$console_title" == *"Console"* ]]; then
        log_info "✓ Console title: OK"
    else
        log_error "✗ Console title missing 'Console': $console_title"
        ((errors++))
    fi

    # Test 4: Console JS loads as JavaScript
    local console_js=$(curl -s "$BASE_URL/console/" | grep -oE 'src="/console/assets/index-[^"]+\.js"' | head -1 | sed 's/src="//;s/"//')
    if [[ -n "$console_js" ]]; then
        local cjs_type=$(curl -sI "$BASE_URL$console_js" | grep -i "content-type" | head -1)
        if [[ "$cjs_type" == *"javascript"* ]]; then
            log_info "✓ Console JS bundle: OK ($console_js)"
        else
            log_error "✗ Console JS wrong content-type: $cjs_type"
            ((errors++))
        fi
    else
        log_error "✗ Console JS bundle not found in HTML"
        ((errors++))
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Smoke tests failed with $errors errors"
        return 1
    fi

    log_info "All smoke tests passed"
    return 0
}

validate_production() {
    log_info "Validating production deployment..."

    local errors=0

    # Check site root
    if [[ -f "$SITE_DIST/index.html" ]]; then
        if ! grep -q 'app-role" content="site-root"' "$SITE_DIST/index.html"; then
            log_error "Site root has wrong build (missing site-root fingerprint)"
            ((errors++))
        fi
        if grep -q '/console/assets/' "$SITE_DIST/index.html"; then
            log_error "Site root has console paths (WRONG BUILD DEPLOYED)"
            ((errors++))
        fi
    else
        log_error "Site root index.html missing"
        ((errors++))
    fi

    # Check console
    if [[ -f "$CONSOLE_DIST/index.html" ]]; then
        if ! grep -q 'app-role" content="console-app"' "$CONSOLE_DIST/index.html"; then
            log_error "Console has wrong build (missing console-app fingerprint)"
            ((errors++))
        fi
        if ! grep -q '/console/assets/' "$CONSOLE_DIST/index.html"; then
            log_error "Console missing /console/ base path"
            ((errors++))
        fi
    else
        log_error "Console index.html missing"
        ((errors++))
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Validation failed with $errors errors"
        return 1
    fi

    log_info "Production deployment validated successfully"
    return 0
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --build       Build both landing and console"
    echo "  --deploy      Deploy built artifacts to production"
    echo "  --all         Build and deploy (default)"
    echo "  --validate    Validate current production deployment"
    echo "  --smoke       Run smoke tests only"
    echo "  --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --all          # Full build + deploy + smoke"
    echo "  $0 --validate     # Check file integrity"
    echo "  $0 --smoke        # Check user-visible correctness"
}

# Main
case "${1:-}" in
    --build)
        build_landing
        build_console
        ;;
    --deploy)
        deploy
        ;;
    --all|"")
        build_landing
        build_console
        deploy
        ;;
    --validate)
        validate_production
        ;;
    --smoke)
        smoke_test
        ;;
    --help|-h)
        usage
        ;;
    *)
        log_error "Unknown option: $1"
        usage
        exit 1
        ;;
esac
