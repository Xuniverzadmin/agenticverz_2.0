#!/bin/bash
# =============================================================================
# GR-4: Semantic Lint (WARNING)
# =============================================================================
# Rule: Prediction UI/API must not use authoritative language.
#       Predictions are advisory, not facts.
#
# Reference: PIN-222, FM-C2-6 (Semantic Leak)
# Enforcement: WARNING - Human review required if detected
# =============================================================================

BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"
FRONTEND_DIR="${2:-/root/agenticverz2.0/frontend}"

echo "GR-4: Checking for authoritative language..."
echo "============================================="

# Forbidden words in prediction-related contexts
FORBIDDEN_WORDS=(
    "confirmed"
    "will fail"
    "guaranteed"
    "detected root cause"
    "certain"
    "definitely"
    "must happen"
    "will occur"
)

WARNINGS=0

# Check prediction-related files in backend
if [ -d "$BACKEND_DIR/app/predictions" ]; then
    for word in "${FORBIDDEN_WORDS[@]}"; do
        if grep -ri "$word" "$BACKEND_DIR/app/predictions" 2>/dev/null; then
            echo "WARNING: Authoritative language '$word' found in backend predictions"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
fi

# Check prediction-related files in frontend
if [ -d "$FRONTEND_DIR" ]; then
    PREDICTION_FILES=$(find "$FRONTEND_DIR" -type f \( -name "*prediction*" -o -name "*advisory*" \) 2>/dev/null)
    for file in $PREDICTION_FILES; do
        for word in "${FORBIDDEN_WORDS[@]}"; do
            if grep -i "$word" "$file" 2>/dev/null; then
                echo "WARNING: Authoritative language '$word' found in $file"
                WARNINGS=$((WARNINGS + 1))
            fi
        done
    done
fi

if [ $WARNINGS -gt 0 ]; then
    echo ""
    echo "GR-4 WARNING: $WARNINGS instance(s) of authoritative language detected"
    echo "Human review required before merge."
    echo "Predictions must use advisory language (FM-C2-6)."
    # Exit 0 - this is a warning, not a blocker
    exit 0
fi

echo "GR-4 PASSED: No authoritative language detected"
exit 0
