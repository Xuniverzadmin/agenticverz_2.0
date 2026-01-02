#!/bin/bash
# Apply all obligation migrations in order
# Usage: ./apply_all.sh [database_url]

set -e

# Get database URL from environment or argument
DB_URL="${1:-$DATABASE_URL}"

if [ -z "$DB_URL" ]; then
    echo "ERROR: DATABASE_URL not set and no argument provided"
    echo "Usage: ./apply_all.sh 'postgresql://user:password@host:port/db'"  # pragma: allowlist secret
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================="
echo "APPLYING OBLIGATION MIGRATIONS"
echo "=============================================="
echo "Database: ${DB_URL%@*}@..."  # Hide credentials
echo ""

# Apply in order: schema, tables, constraints, triggers, views
for obligation in PB-S1 PB-S2 PB-S4 M26; do
    echo "----------------------------------------------"
    echo "Obligation: $obligation"
    echo "----------------------------------------------"

    OB_DIR="$SCRIPT_DIR/$obligation"

    if [ ! -d "$OB_DIR" ]; then
        echo "  SKIP: Directory not found"
        continue
    fi

    for sql_file in "$OB_DIR"/0*.sql; do
        if [ -f "$sql_file" ]; then
            filename=$(basename "$sql_file")
            echo "  Applying: $filename"
            psql "$DB_URL" -f "$sql_file" -v ON_ERROR_STOP=1 2>&1 | sed 's/^/    /'
        fi
    done

    echo "  DONE: $obligation"
    echo ""
done

echo "=============================================="
echo "ALL MIGRATIONS APPLIED SUCCESSFULLY"
echo "=============================================="
