#!/usr/bin/env bash
# check_pydantic_config.sh
#
# Lint check to prevent deprecated Pydantic V1 class Config patterns.
# Ensures all models use model_config = ConfigDict(...) instead.
#
# Usage: ./scripts/check_pydantic_config.sh
# Exit codes:
#   0 - No violations found
#   1 - class Config found in Pydantic models

set -e

echo "=== Checking for deprecated Pydantic class Config usage ==="

cd "$(dirname "$0")/.."

# Find all class Config usages in Python files
VIOLATIONS=$(grep -rn "class Config:" app/ --include="*.py" 2>/dev/null || true)

if [ -n "$VIOLATIONS" ]; then
    echo ""
    echo "✗ FAIL: Found deprecated 'class Config:' usage"
    echo ""
    echo "$VIOLATIONS"
    echo ""
    echo "To fix:"
    echo "  1. Replace 'class Config:' with 'model_config = ConfigDict(...)'"
    echo "  2. Import ConfigDict: 'from pydantic import ConfigDict'"
    echo "  3. See: https://docs.pydantic.dev/latest/migration/"
    exit 1
fi

echo "✓ PASS: No deprecated class Config usages found"
exit 0
