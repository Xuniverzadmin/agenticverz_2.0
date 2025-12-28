#!/bin/bash
# C5 Guardrails CI Runner
#
# Runs all 6 C5 guardrails checks.
# Reference: C5_CI_GUARDRAILS_DESIGN.md, PIN-232

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${BACKEND_DIR:-$(dirname "$SCRIPT_DIR")/../../backend}"

export BACKEND_DIR

echo "============================================"
echo "C5 Guardrails CI Runner"
echo "============================================"
echo "Reference: PIN-232, C5_CI_GUARDRAILS_DESIGN.md"
echo "Backend: $BACKEND_DIR"
echo ""

FAILED=0
PASSED=0
SKIPPED=0

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true

# CI-C5-1: Advisory-Only Output
echo ""
echo "Running CI-C5-1: Advisory-Only Output..."
echo "----------------------------------------"
if "$SCRIPT_DIR/check_advisory_only.sh"; then
    PASSED=$((PASSED + 1))
else
    result=$?
    if [ $result -eq 0 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
fi

# CI-C5-2: Human Approval Gate
echo ""
echo "Running CI-C5-2: Human Approval Gate..."
echo "----------------------------------------"
if "$SCRIPT_DIR/check_approval_gate.sh"; then
    PASSED=$((PASSED + 1))
else
    result=$?
    if [ $result -eq 0 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
fi

# CI-C5-3: Metadata Boundary
echo ""
echo "Running CI-C5-3: Metadata Boundary..."
echo "----------------------------------------"
if "$SCRIPT_DIR/check_metadata_boundary.sh"; then
    PASSED=$((PASSED + 1))
else
    result=$?
    if [ $result -eq 0 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
fi

# CI-C5-4: Suggestion Versioning
echo ""
echo "Running CI-C5-4: Suggestion Versioning..."
echo "----------------------------------------"
if "$SCRIPT_DIR/check_versioning.sh"; then
    PASSED=$((PASSED + 1))
else
    result=$?
    if [ $result -eq 0 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
fi

# CI-C5-5: Learning Disable Flag
echo ""
echo "Running CI-C5-5: Learning Disable Flag..."
echo "----------------------------------------"
if "$SCRIPT_DIR/check_disable_flag.sh"; then
    PASSED=$((PASSED + 1))
else
    result=$?
    if [ $result -eq 0 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
fi

# CI-C5-6: Kill-Switch Isolation
echo ""
echo "Running CI-C5-6: Kill-Switch Isolation..."
echo "----------------------------------------"
if "$SCRIPT_DIR/check_killswitch_isolation.sh"; then
    PASSED=$((PASSED + 1))
else
    result=$?
    if [ $result -eq 0 ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
fi

# Summary
echo ""
echo "============================================"
echo "C5 Guardrails Summary"
echo "============================================"
echo "Passed:  $PASSED / 6"
echo "Failed:  $FAILED / 6"
echo "Skipped: $SKIPPED / 6"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "C5 GUARDRAILS: PASS"
    echo ""
    echo "All guardrails verified. Learning layer is compliant."
    exit 0
else
    echo "C5 GUARDRAILS: FAIL"
    echo ""
    echo "Some guardrails failed. Review output above."
    exit 1
fi
