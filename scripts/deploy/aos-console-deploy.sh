#!/bin/bash
# AOS App Shell Production Deployment Script
# Target: agenticverz.com
# Note: app-shell is the routing + auth handoff layer only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_SHELL_DIR="$PROJECT_ROOT/website/app-shell"
DEPLOY_TARGET="/opt/agenticverz/apps/console"

echo "=========================================="
echo "  AOS App Shell Production Deployment"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "App Shell:    $APP_SHELL_DIR"
echo "Deploy Target: $DEPLOY_TARGET"
echo ""

# Step 1: Build
echo "[1/5] Building production bundle..."
cd "$CONSOLE_DIR"
npm ci --silent
npm run build

if [ ! -d "dist" ]; then
    echo "ERROR: Build failed - no dist directory"
    exit 1
fi

echo "Build completed. Bundle size:"
du -sh dist/

# Step 2: Backup existing deployment
echo ""
echo "[2/5] Backing up existing deployment..."
BACKUP_DIR="/opt/agenticverz/backups/console-$(date +%Y%m%d-%H%M%S)"
if [ -d "$DEPLOY_TARGET/dist" ]; then
    mkdir -p "$BACKUP_DIR"
    cp -R "$DEPLOY_TARGET/dist" "$BACKUP_DIR/"
    echo "Backup created: $BACKUP_DIR"
else
    echo "No existing deployment to backup"
fi

# Step 3: Deploy
echo ""
echo "[3/5] Deploying to production..."
mkdir -p "$DEPLOY_TARGET"
rm -rf "$DEPLOY_TARGET/dist"
cp -R dist "$DEPLOY_TARGET/"

# Step 4: Verify deployment
echo ""
echo "[4/5] Verifying deployment..."
if [ -f "$DEPLOY_TARGET/dist/index.html" ]; then
    echo "index.html: OK"
else
    echo "ERROR: index.html not found!"
    exit 1
fi

ASSET_COUNT=$(find "$DEPLOY_TARGET/dist/assets" -type f | wc -l)
echo "Assets deployed: $ASSET_COUNT files"

# Step 5: Reload Apache
echo ""
echo "[5/5] Reloading Apache..."
if command -v systemctl &> /dev/null; then
    sudo systemctl reload apache2 || echo "Apache reload skipped (may need manual reload)"
else
    echo "systemctl not found - manual Apache reload required"
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Console URL: https://agenticverz.com/console"
echo ""
echo "Run smoke test:"
echo "  /opt/agenticverz/scripts/aos-smoke-test.sh"
echo ""
