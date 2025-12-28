#!/bin/bash
# CI-C4-8: Audit Isolation Check
# Reference: C4_COORDINATION_AUDIT_SCHEMA.md Section 6
#
# Ensures no learning imports in coordinator
# C4 code must not import from C5 learning modules

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
OPTIMIZATION_DIR="$BACKEND_DIR/app/optimization"

echo "🔍 CI-C4-8: Checking audit isolation..."

# Check for learning imports in optimization code
LEARNING_IMPORTS=$(grep -rn "from app\.learning\|import.*learning" "$OPTIMIZATION_DIR" 2>/dev/null | grep -v "__pycache__\|\.pyc" || true)

if [ -n "$LEARNING_IMPORTS" ]; then
    echo "❌ CI-C4-8 FAILED: Found learning imports in optimization code"
    echo ""
    echo "Matches found:"
    echo "$LEARNING_IMPORTS"
    echo ""
    echo "C4 optimization code must NOT import from C5 learning modules."
    echo "This maintains isolation between coordination and learning."
    exit 1
fi

# Verify isolation: learning modules should not import from killswitch/coordinator
LEARNING_DIR="$BACKEND_DIR/app/learning"
if [ -d "$LEARNING_DIR" ]; then
    KS_IMPORT=$(grep -rn "from app\.optimization\.killswitch\|from app\.optimization\.coordinator" "$LEARNING_DIR" 2>/dev/null | grep -v "__pycache__\|\.pyc\|MUST NOT" || true)

    if [ -n "$KS_IMPORT" ]; then
        echo "❌ CI-C4-8 FAILED: Found coordinator/killswitch imports in learning code"
        echo ""
        echo "Matches found:"
        echo "$KS_IMPORT"
        echo ""
        echo "C5 learning code must NOT import from C4 coordinator/killswitch."
        exit 1
    fi
fi

echo "✅ CI-C4-8 PASSED: Audit isolation maintained"
