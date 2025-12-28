#!/bin/bash
# CI-C5-3: Metadata Boundary Check
#
# Verifies that learning operates on metadata tables only.
# Reference: C5_S1_CI_ENFORCEMENT.md, AC-S1-I3, AC-S1-B1

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
LEARNING_DIR="$BACKEND_DIR/app/learning"

echo "CI-C5-3: Metadata Boundary Check"
echo "===================================="

# Check if learning directory exists
if [ ! -d "$LEARNING_DIR" ]; then
    echo "  SKIP: Learning directory not found (not implemented yet)"
    exit 0
fi

FAILED=0

# Check 1: No runtime table imports
echo ""
echo "Check 1: No runtime table imports..."
# Forbidden runtime table model imports
FORBIDDEN_TABLES="Run|Step|MemoryEntry|ActiveEnvelope|EnvelopeState"
FORBIDDEN=$(grep -rniE "from app\.models\.(run|step|memory|tenant).*import" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$FORBIDDEN" ]; then
    echo "  FAIL: Forbidden runtime table import found:"
    echo "$FORBIDDEN"
    FAILED=1
else
    echo "  PASS: No runtime table imports"
fi

# Check 2: No session queries to runtime tables
echo ""
echo "Check 2: No runtime table session queries..."
RUNTIME_QUERY=$(grep -rniE "session\.query\((Run|Step|MemoryEntry|ActiveEnvelope|EnvelopeState)\)" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$RUNTIME_QUERY" ]; then
    echo "  FAIL: Direct runtime table query found:"
    echo "$RUNTIME_QUERY"
    FAILED=1
else
    echo "  PASS: No runtime table queries"
fi

# Check 3: Verify allowed table access pattern
echo ""
echo "Check 3: Allowed table access pattern..."
# S1 should access CoordinationAuditRecord
if grep -q "CoordinationAuditRecord" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null; then
    echo "  PASS: S1 uses CoordinationAuditRecord"
else
    echo "  INFO: CoordinationAuditRecord not directly used (may use passed-in data)"
fi

# Check 4: Tables boundary file exists
echo ""
echo "Check 4: Tables boundary file..."
if [ -f "$LEARNING_DIR/tables.py" ]; then
    echo "  PASS: Tables boundary file exists"

    # Verify it defines allowed and forbidden tables
    if grep -q "LEARNING_ALLOWED_TABLES" "$LEARNING_DIR/tables.py" && \
       grep -q "LEARNING_FORBIDDEN_TABLES" "$LEARNING_DIR/tables.py"; then
        echo "  PASS: Table sets defined"
    else
        echo "  WARN: Table sets not fully defined"
    fi
else
    echo "  WARN: Tables boundary file not found"
fi

# Check 5: No direct database writes to runtime tables
echo ""
echo "Check 5: No writes to runtime tables..."
WRITE_PATTERNS="\.add\(.*Run\|\.add\(.*Step\|INSERT INTO runs\|INSERT INTO steps"
WRITES=$(grep -rniE "$WRITE_PATTERNS" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$WRITES" ]; then
    echo "  FAIL: Direct writes to runtime tables found:"
    echo "$WRITES"
    FAILED=1
else
    echo "  PASS: No writes to runtime tables"
fi

echo ""
echo "===================================="
if [ $FAILED -eq 0 ]; then
    echo "CI-C5-3: PASS"
    exit 0
else
    echo "CI-C5-3: FAIL"
    exit 1
fi
