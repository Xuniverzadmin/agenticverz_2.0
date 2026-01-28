#!/bin/bash
# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Role: Post-edit validation hook — checks headers and generated file markers

# This hook runs after Edit/Write operations
# Exit 0 always (warnings only, non-blocking)

FILE="$1"

if [ -z "$FILE" ]; then
    exit 0
fi

# Check Python files for AUDIENCE and Layer headers
if [[ "$FILE" == *.py ]]; then
    if ! head -50 "$FILE" 2>/dev/null | grep -q "# AUDIENCE:"; then
        echo "⚠ AUDIENCE header missing: $FILE"
    fi
    if ! head -50 "$FILE" 2>/dev/null | grep -q "# Layer:"; then
        echo "⚠ Layer header missing: $FILE"
    fi
fi

# Check for generated file markers
if head -10 "$FILE" 2>/dev/null | grep -qi "GENERATED FILE\|AUTO-GENERATED"; then
    echo "⚠ WARNING: This is a generated file. Edit the SOURCE instead."
    echo "  Check: design/SOURCE_CHAIN_REGISTRY.yaml"
fi

# Check alembic migrations for contract header
if [[ "$FILE" == *alembic/versions/*.py ]]; then
    if ! head -20 "$FILE" 2>/dev/null | grep -q "MIGRATION_CONTRACT"; then
        echo "⚠ MIGRATION_CONTRACT header missing in migration: $FILE"
    fi
fi

exit 0
