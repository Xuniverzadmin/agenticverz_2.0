#!/usr/bin/env bash
# check_no_datetime_now.sh
#
# Lint check to prevent datetime.now() in canonical output functions.
# This ensures deterministic outputs are not polluted with timestamps.
#
# Usage: ./scripts/check_no_datetime_now.sh
# Exit codes:
#   0 - No violations found
#   1 - datetime.now() found in canonical functions

set -e

echo "=== Checking for datetime.now() in canonical output functions ==="

cd "$(dirname "$0")/.."

# Files/patterns where datetime.now() is FORBIDDEN
FORBIDDEN_PATTERNS=(
    "to_canonical"
    "canonical_json"
    "to_deterministic"
    "content_hash"
    "stable_fields"
)

# Build grep pattern for functions
FUNCTION_PATTERN=$(IFS="|"; echo "${FORBIDDEN_PATTERNS[*]}")

# Find files that have both datetime.now() AND one of the forbidden patterns
VIOLATIONS=0

echo "Scanning app/ for violations..."

# Check each Python file
for file in $(find app -name "*.py" -type f 2>/dev/null); do
    # Check if file has datetime.now()
    if grep -q "datetime\.now\(\)" "$file" 2>/dev/null; then
        # Check if file also has canonical/deterministic functions
        if grep -qE "$FUNCTION_PATTERN" "$file" 2>/dev/null; then
            # Get line numbers of datetime.now() usage
            LINES=$(grep -n "datetime\.now\(\)" "$file" | grep -v "# non-deterministic" | grep -v "# timestamp ok")
            if [ -n "$LINES" ]; then
                echo ""
                echo "⚠ POTENTIAL VIOLATION: $file"
                echo "$LINES"

                # Check if it's inside a canonical function
                while IFS= read -r line; do
                    LINE_NUM=$(echo "$line" | cut -d: -f1)
                    # Check surrounding context (±5 lines)
                    CONTEXT=$(sed -n "$((LINE_NUM-5)),$((LINE_NUM+5))p" "$file" 2>/dev/null)
                    if echo "$CONTEXT" | grep -qE "$FUNCTION_PATTERN"; then
                        echo "  ✗ Line $LINE_NUM appears inside/near a canonical function!"
                        VIOLATIONS=$((VIOLATIONS + 1))
                    fi
                done <<< "$LINES"
            fi
        fi
    fi
done

echo ""

if [ $VIOLATIONS -gt 0 ]; then
    echo "✗ FAIL: Found $VIOLATIONS potential datetime.now() violations in canonical functions"
    echo ""
    echo "To fix:"
    echo "  1. Remove datetime.now() from canonical/deterministic functions"
    echo "  2. Use a lazy property pattern for timestamps (see PlanMetadata._generated_at)"
    echo "  3. Add '# non-deterministic' comment if intentional (e.g., logging)"
    exit 1
fi

echo "✓ PASS: No datetime.now() violations found in canonical functions"
exit 0
