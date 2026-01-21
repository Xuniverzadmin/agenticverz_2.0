#!/usr/bin/env bash
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: developer (manual) or CI
#   Execution: sync
# Role: Build preflight console for L2.1 UI pipeline testing
# Reference: Preflight Console Governance

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_SHELL="$REPO_ROOT/website/app-shell"

echo "=========================================="
echo "Building Preflight Console"
echo "=========================================="
echo ""

# Step 1: Validate L2.1 projection lock
echo "Step 1/5: Validating L2.1 projection lock..."
python3 "$REPO_ROOT/scripts/ci/validate_projection_lock.py" --skip-regenerate
if [ $? -ne 0 ]; then
    echo "FAIL: Projection lock validation failed"
    echo "Run the L2.1 pipeline first: ./scripts/tools/run_l2_pipeline.sh"
    exit 1
fi
echo "PASS: Projection lock valid"
echo ""

# Step 2: Validate UI consumes projection lock
echo "Step 2/5: Validating UI consumes projection lock..."
UI_GATE_PASS=true
UI_ISSUES=""

# Check ProjectionSidebar exists
if [ -f "$APP_SHELL/src/components/layout/ProjectionSidebar.tsx" ]; then
    echo "  ✓ ProjectionSidebar component exists"
else
    UI_GATE_PASS=false
    UI_ISSUES+="Missing ProjectionSidebar.tsx, "
fi

# Check DomainPage exists
if [ -f "$APP_SHELL/src/pages/domains/DomainPage.tsx" ]; then
    echo "  ✓ DomainPage component exists"
else
    UI_GATE_PASS=false
    UI_ISSUES+="Missing DomainPage.tsx, "
fi

# Check routes configured
if grep -q "OverviewPage\|ActivityPage\|IncidentsPage\|PoliciesPage\|LogsPage" "$APP_SHELL/src/routes/index.tsx" 2>/dev/null; then
    echo "  ✓ L2.1 domain routes configured"
else
    UI_GATE_PASS=false
    UI_ISSUES+="Domain routes not configured, "
fi

# Check AppLayout uses ProjectionSidebar
if grep -q "ProjectionSidebar" "$APP_SHELL/src/components/layout/AppLayout.tsx" 2>/dev/null; then
    echo "  ✓ AppLayout uses ProjectionSidebar"
else
    UI_GATE_PASS=false
    UI_ISSUES+="AppLayout not using ProjectionSidebar, "
fi

# Check projection loader is used
if grep -q "loadProjection\|getEnabledPanels" "$APP_SHELL/src/components/layout/ProjectionSidebar.tsx" 2>/dev/null; then
    echo "  ✓ ProjectionSidebar uses projection loader"
else
    UI_GATE_PASS=false
    UI_ISSUES+="ProjectionSidebar not using loader, "
fi

if [ "$UI_GATE_PASS" = true ]; then
    echo "PASS: UI correctly configured to consume projection lock"
else
    echo "FAIL: UI not consuming projection: ${UI_ISSUES%%, }"
    echo ""
    echo "The UI must consume the projection lock, not hardcode domains/panels."
    echo "See: docs/memory-pins/PIN-352-l21-ui-projection-pipeline-preflight-console.md"
    exit 1
fi
echo ""

# Step 3: Install dependencies
echo "Step 3/5: Installing dependencies..."
cd "$APP_SHELL"
npm install --silent
echo ""

# Step 4: Copy projection lock to public assets
# V2 CONSTITUTION SOURCE - Decoupled from AURORA pipeline (2026-01-20)
# DO NOT change back to design/l2_1/ui_contract/ - that is AURORA-generated
echo "Step 4/5: Copying V2 Constitution projection lock to build..."
mkdir -p "$APP_SHELL/public/projection"
cp "$REPO_ROOT/design/v2_constitution/ui_projection_lock.json" "$APP_SHELL/public/projection/"
echo "Copied V2 Constitution ui_projection_lock.json to public/projection/"
echo ""

# Step 5: Build with preflight environment
echo "Step 5/5: Building with preflight environment..."
cp "$APP_SHELL/.env.preflight" "$APP_SHELL/.env.production"
npm run build

# Move to preflight directory
rm -rf "$APP_SHELL/dist-preflight"
mv "$APP_SHELL/dist" "$APP_SHELL/dist-preflight"

# Restore production env
git checkout "$APP_SHELL/.env.production" 2>/dev/null || true

echo ""
echo "=========================================="
echo "Preflight build complete!"
echo "=========================================="
echo ""
echo "Output: $APP_SHELL/dist-preflight"
echo "URL: https://preflight-console.agenticverz.com"
echo ""
echo "Next steps:"
echo "  1. Enable Apache site: sudo a2ensite preflight-console.agenticverz.com.conf"
echo "  2. Reload Apache: sudo systemctl reload apache2"
echo "  3. Add DNS record in Cloudflare for preflight-console.agenticverz.com"
echo "  4. Test the preflight console"
echo "  5. Run promotion validation: ./scripts/ops/promote_to_production.sh --validate"
