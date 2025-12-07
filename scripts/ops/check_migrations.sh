#!/bin/bash
# Migration Drift Guard
# Verifies that all Alembic migrations in the codebase match the database schema
# and that no uncommitted migrations exist.
#
# Usage:
#   ./scripts/ops/check_migrations.sh         # Check mode (default)
#   ./scripts/ops/check_migrations.sh --ci    # CI mode (stricter)
#
# Requires: DATABASE_URL environment variable

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"

CI_MODE=false
if [[ "$1" == "--ci" ]]; then
    CI_MODE=true
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Migration Drift Guard ==="
echo ""

# Check for uncommitted migration files
echo "Checking for uncommitted migration files..."
UNCOMMITTED_MIGRATIONS=$(git -C "$REPO_ROOT" ls-files --others --exclude-standard "$ALEMBIC_DIR" 2>/dev/null || true)
MODIFIED_MIGRATIONS=$(git -C "$REPO_ROOT" diff --name-only "$ALEMBIC_DIR" 2>/dev/null || true)

if [[ -n "$UNCOMMITTED_MIGRATIONS" ]]; then
    echo -e "${RED}ERROR: Found uncommitted migration files:${NC}"
    echo "$UNCOMMITTED_MIGRATIONS"
    if [[ "$CI_MODE" == true ]]; then
        exit 1
    fi
fi

if [[ -n "$MODIFIED_MIGRATIONS" ]]; then
    echo -e "${YELLOW}WARNING: Found modified migration files:${NC}"
    echo "$MODIFIED_MIGRATIONS"
    if [[ "$CI_MODE" == true ]]; then
        exit 1
    fi
fi

# Count migration files in repository
REPO_MIGRATIONS=$(ls -1 "$ALEMBIC_DIR"/*.py 2>/dev/null | grep -v "__pycache__" | grep -v "env.py" | wc -l)
echo "Repository migrations: $REPO_MIGRATIONS"

# Check database state if DATABASE_URL is available
if [[ -n "$DATABASE_URL" ]]; then
    echo ""
    echo "Checking database migration state..."

    cd "$BACKEND_DIR"

    # Get current database head
    DB_HEAD=$(PYTHONPATH=. python3 -c "
import os
os.environ.setdefault('DATABASE_URL', '$DATABASE_URL')
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

try:
    # Get DB current revision
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version_num FROM alembic_version'))
        row = result.fetchone()
        if row:
            print(row[0])
        else:
            print('EMPTY')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null || echo "ERROR: Could not connect to database")

    # Get repository head
    REPO_HEAD=$(PYTHONPATH=. python3 -c "
import os
os.environ.setdefault('DATABASE_URL', 'postgresql://localhost/dummy')
from alembic.config import Config
from alembic.script import ScriptDirectory

alembic_cfg = Config('alembic.ini')
script = ScriptDirectory.from_config(alembic_cfg)
heads = script.get_heads()
if heads:
    print(heads[0])
else:
    print('EMPTY')
" 2>/dev/null || echo "ERROR: Could not read alembic config")

    echo "Database head:   $DB_HEAD"
    echo "Repository head: $REPO_HEAD"

    if [[ "$DB_HEAD" == "$REPO_HEAD" ]]; then
        echo -e "${GREEN}OK: Database and repository are in sync${NC}"
    elif [[ "$DB_HEAD" == "EMPTY" ]]; then
        echo -e "${YELLOW}WARNING: Database has no migrations applied${NC}"
        if [[ "$CI_MODE" == true ]]; then
            echo "This may be expected for fresh databases in CI"
        fi
    elif [[ "$DB_HEAD" == ERROR* ]]; then
        echo -e "${YELLOW}WARNING: Could not check database state: $DB_HEAD${NC}"
    elif [[ "$REPO_HEAD" == ERROR* ]]; then
        echo -e "${RED}ERROR: Could not read repository migrations: $REPO_HEAD${NC}"
        exit 1
    else
        echo -e "${RED}DRIFT DETECTED: Database and repository migrations differ!${NC}"
        echo ""
        echo "To fix:"
        echo "  1. If DB is behind: alembic upgrade head"
        echo "  2. If new migrations needed: alembic revision --autogenerate -m 'description'"
        echo "  3. Commit all migration files before pushing"

        if [[ "$CI_MODE" == true ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}WARNING: DATABASE_URL not set, skipping database check${NC}"
fi

echo ""
echo "=== Migration files in repository ==="
ls -1 "$ALEMBIC_DIR"/*.py 2>/dev/null | grep -v "__pycache__" | xargs -I {} basename {} | sort

echo ""
echo -e "${GREEN}Migration drift check complete${NC}"
