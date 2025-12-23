#!/bin/bash
# =============================================================================
# M26 Prevention Mechanism: Environment Variable Misuse Guard
# =============================================================================
#
# INVARIANT: Direct os.environ.get() for secrets is FORBIDDEN outside secrets.py
#            All secret access MUST go through app.config.secrets.Secrets
#
# BASELINE: 33 violations exist as of 2025-12-23 (pre-M26 technical debt)
#           CI will WARN on these but only FAIL if count increases
#
# =============================================================================

set -e

echo "======================================"
echo "M26 Environment Misuse Guard"
echo "======================================"
echo "INVARIANT: Secret access must go through app.config.secrets.Secrets"
echo ""

BACKEND_DIR="${1:-backend/app}"
BASELINE_COUNT=33  # Known violations as of M26 freeze (2025-12-23)

if [ ! -d "$BACKEND_DIR" ]; then
    echo "ERROR: Directory $BACKEND_DIR does not exist"
    exit 1
fi

# Patterns that indicate secret access
SECRET_PATTERNS=(
    'os\.environ\.get\s*\(\s*["\x27].*KEY'
    'os\.environ\.get\s*\(\s*["\x27].*SECRET'
    'os\.environ\.get\s*\(\s*["\x27].*TOKEN'
    'os\.environ\.get\s*\(\s*["\x27].*PASSWORD'
    'os\.environ\.get\s*\(\s*["\x27]DATABASE_URL'
    'os\.environ\.get\s*\(\s*["\x27]REDIS_URL'
    'os\.environ\s*\[\s*["\x27].*KEY'
    'os\.environ\s*\[\s*["\x27].*SECRET'
    'os\.environ\s*\[\s*["\x27].*TOKEN'
)

# Files allowed to use os.environ for secrets
ALLOWED_FILES=(
    "config/secrets.py"
    "tests/"
    "__pycache__"
)

VIOLATION_COUNT=0

for pattern in "${SECRET_PATTERNS[@]}"; do
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            file=$(echo "$line" | cut -d: -f1)

            is_allowed=false
            for allowed in "${ALLOWED_FILES[@]}"; do
                if [[ "$file" == *"$allowed"* ]]; then
                    is_allowed=true
                    break
                fi
            done

            if [ "$is_allowed" = false ]; then
                VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
            fi
        fi
    done < <(grep -rn -E "$pattern" "$BACKEND_DIR" 2>/dev/null || true)
done

echo "Violations found: $VIOLATION_COUNT"
echo "Baseline (M26 freeze): $BASELINE_COUNT"
echo ""

if [ $VIOLATION_COUNT -gt $BASELINE_COUNT ]; then
    DELTA=$((VIOLATION_COUNT - BASELINE_COUNT))
    echo -e "\033[0;31m======================================"
    echo "FAIL: $DELTA NEW violations introduced!"
    echo "======================================\033[0m"
    echo ""
    echo "New code is accessing secrets directly instead of using Secrets module."
    echo ""
    echo "FIX: Use app.config.secrets.Secrets instead of os.environ.get()"
    echo ""
    echo "  from app.config.secrets import Secrets"
    echo "  key = Secrets.openai_api_key()  # Not os.environ.get(...)"
    echo ""
    exit 1
elif [ $VIOLATION_COUNT -lt $BASELINE_COUNT ]; then
    FIXED=$((BASELINE_COUNT - VIOLATION_COUNT))
    echo -e "\033[0;32mPROGRESS: $FIXED violations fixed! ($VIOLATION_COUNT remaining)\033[0m"
    echo ""
    echo "Consider updating BASELINE_COUNT in this script to $VIOLATION_COUNT"
else
    echo -e "\033[0;33mWARN: $BASELINE_COUNT legacy violations remain (technical debt)\033[0m"
    echo "These existed before M26 freeze and are tracked for future cleanup."
fi

echo ""
echo -e "\033[0;32m======================================"
echo "Environment Misuse Guard: COMPLETE"
echo "======================================\033[0m"
