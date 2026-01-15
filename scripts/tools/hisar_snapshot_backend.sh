#!/usr/bin/env bash
# =============================================================================
# HISAR snapshot-backend — Authenticated OpenAPI Snapshot
# =============================================================================
#
# PURPOSE: Capture backend OpenAPI spec with OBSERVER authentication.
#          This snapshot is used by coherency checks to validate routes.
#
# ARCHITECTURAL RULES:
#   - No retries
#   - No loops
#   - No silent success
#   - Empty snapshot = hard fail
#   - CPU usage negligible
#
# INVARIANT: HISAR snapshots must be taken with OBSERVER auth.
#            Anonymous access may work, but auth provides belt-and-suspenders.
#
# Reference: PIN-419 (Intent Manifest Coherency Architecture)
# =============================================================================

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
SNAPSHOT_PATH="backend/.openapi_snapshot.json"

# Change to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "========================================"
echo "HISAR snapshot-backend (hardened)"
echo "========================================"

# Step 1: Verify AOS_API_KEY is set (not strictly required, but enforced for discipline)
if [[ -z "${AOS_API_KEY:-}" ]]; then
    echo "WARNING: AOS_API_KEY not set. Attempting anonymous fetch."
    echo "         Set AOS_API_KEY for authenticated snapshots."
    AUTH_HEADER=""
else
    AUTH_HEADER="-H X-AOS-Key: $AOS_API_KEY"
fi

# Step 2: Check backend health
echo "Checking backend health..."
if ! curl -sf "$BACKEND_URL/health" >/dev/null 2>&1; then
    echo "FATAL: Backend not healthy at $BACKEND_URL/health"
    echo "       Ensure backend is running: docker compose up -d backend"
    exit 1
fi
echo "  Backend healthy"

# Step 3: Fetch OpenAPI with optional auth
echo "Fetching OpenAPI spec..."
HTTP_CODE=$(curl -sS \
    ${AUTH_HEADER:-} \
    -w "%{http_code}" \
    -o "$SNAPSHOT_PATH.tmp" \
    "$BACKEND_URL/openapi.json")

# Step 4: Validate HTTP status
if [[ "$HTTP_CODE" != "200" ]]; then
    echo "FATAL: OpenAPI fetch failed with HTTP $HTTP_CODE"
    rm -f "$SNAPSHOT_PATH.tmp"
    exit 1
fi
echo "  HTTP 200 OK"

# Step 5: Validate non-empty response
if [[ ! -s "$SNAPSHOT_PATH.tmp" ]]; then
    echo "FATAL: OpenAPI snapshot is empty (0 bytes)"
    echo "       This indicates auth or backend issue."
    rm -f "$SNAPSHOT_PATH.tmp"
    exit 1
fi

SNAPSHOT_SIZE=$(stat -c%s "$SNAPSHOT_PATH.tmp" 2>/dev/null || stat -f%z "$SNAPSHOT_PATH.tmp" 2>/dev/null)
echo "  Size: $SNAPSHOT_SIZE bytes"

# Step 6: Validate JSON structure
echo "Validating JSON..."
if ! python3 - <<'EOF'
import json
import sys

with open("backend/.openapi_snapshot.json.tmp") as f:
    spec = json.load(f)

# Required fields
assert "paths" in spec, "Missing 'paths' key"
assert isinstance(spec["paths"], dict), "'paths' must be dict"
assert len(spec["paths"]) > 0, "'paths' is empty"

# Optional but expected
if "info" in spec:
    assert "title" in spec["info"], "Missing 'info.title'"

path_count = len(spec["paths"])
print(f"  Valid: {path_count} routes captured")
EOF
then
    echo "FATAL: OpenAPI snapshot is invalid JSON or missing structure"
    rm -f "$SNAPSHOT_PATH.tmp"
    exit 1
fi

# Step 7: Atomic move
mv "$SNAPSHOT_PATH.tmp" "$SNAPSHOT_PATH"

# Step 8: Report success
echo ""
echo "Snapshot locked:"
sha256sum "$SNAPSHOT_PATH"
echo ""
echo "SUCCESS: $SNAPSHOT_PATH updated"
