#!/usr/bin/env bash
# Release Smoke Test Script
# Run after deployments to validate system health
#
# Usage:
#   ./scripts/smoke_release.sh                    # Uses defaults
#   API_BASE=http://localhost:8000 ./scripts/smoke_release.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - Health check failed
#   2 - Replay test failed
#   3 - Registry snapshot test failed

set -euo pipefail

API_BASE=${API_BASE:-"http://localhost:8000"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"

echo "=========================================="
echo "AOS Release Smoke Test"
echo "=========================================="
echo "API_BASE: $API_BASE"
echo "Time: $(date -Iseconds)"
echo ""

# 1. Health check
echo "[1/4] Health check..."
if curl -fsS "$API_BASE/health" >/dev/null 2>&1; then
    echo "  ✓ Health endpoint OK"
else
    echo "  ✗ Health endpoint FAILED"
    exit 1
fi

# 2. Metrics endpoint
echo "[2/4] Metrics check..."
if curl -fsS "$API_BASE/metrics" 2>/dev/null | grep -q "nova_"; then
    echo "  ✓ Metrics endpoint OK"
else
    echo "  ✗ Metrics endpoint FAILED (no nova_ metrics found)"
    exit 1
fi

# 3. Replay certification test
echo "[3/4] Replay certification..."
cd "$BACKEND_DIR"
if PYTHONPATH=. python3 -m pytest tests/workflow/test_replay_certification.py -q --tb=no 2>/dev/null; then
    echo "  ✓ Replay certification PASSED"
else
    echo "  ✗ Replay certification FAILED"
    exit 2
fi

# 4. Registry snapshot test
echo "[4/4] Registry snapshot..."
if PYTHONPATH=. python3 -m pytest tests/integration/test_registry_snapshot.py -q --tb=no 2>/dev/null; then
    echo "  ✓ Registry snapshot PASSED"
else
    echo "  ✗ Registry snapshot FAILED"
    exit 3
fi

echo ""
echo "=========================================="
echo "SMOKE TEST PASSED"
echo "=========================================="
exit 0
