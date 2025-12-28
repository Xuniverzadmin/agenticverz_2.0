#!/bin/bash
# =============================================================================
# GR-5: Redis Authority Protection (BLOCKER)
# =============================================================================
# Rule: At schema+CI phase, Redis must not be referenced in prediction code.
#       Redis enters later with explicit tests.
#
# Reference: PIN-222, Infrastructure Authority Map
# Enforcement: BLOCKER - Redis forbidden until explicitly approved
# =============================================================================

set -e

BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"

echo "GR-5: Checking Redis authority..."
echo "=================================="

VIOLATIONS=0

# Check if predictions directory exists
if [ -d "$BACKEND_DIR/app/predictions" ]; then
    # Check for actual Redis imports or usage (not comments about Redis policy)
    # Patterns: import redis, from redis, redis.Redis, upstash imports, redis_client
    if grep -rE "(import redis|from redis|redis\.Redis|from upstash|import upstash|redis_client|RedisClient)" "$BACKEND_DIR/app/predictions" 2>/dev/null; then
        echo "VIOLATION: Redis import or usage found in prediction code"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
fi

# Also check for Redis in any prediction-related test files
if [ -d "$BACKEND_DIR/tests" ]; then
    PREDICTION_TESTS=$(find "$BACKEND_DIR/tests" -name "*prediction*" -type f 2>/dev/null)
    for file in $PREDICTION_TESTS; do
        if grep -E "(redis|upstash|Redis)" "$file" 2>/dev/null; then
            # Allow in tests that explicitly test Redis behavior
            if ! grep -q "test_redis_loss\|redis_disabled\|without_redis" "$file"; then
                echo "WARNING: Redis reference in test file $file"
            fi
        fi
    done
fi

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "GR-5 FAILED: $VIOLATIONS violation(s) detected"
    echo "Redis must not be used in predictions until explicitly approved."
    echo "Redis enters C2 later with GR-5 simulation tests."
    exit 1
fi

echo "GR-5 PASSED: No unauthorized Redis references in prediction code"
exit 0
