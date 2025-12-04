#!/bin/bash
# M4 Migration Deployment Script
# Run this in staging/production to apply workflow checkpoint migrations
#
# Prerequisites:
#   - DATABASE_URL set or passed as argument
#   - PostgreSQL client tools installed
#   - Alembic installed (pip install alembic)
#
# Usage:
#   ./scripts/deploy_migrations.sh                    # Uses DATABASE_URL env
#   ./scripts/deploy_migrations.sh --dry-run          # Preview SQL only
#   ./scripts/deploy_migrations.sh --rollback         # Rollback last migration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
DRY_RUN=false
ROLLBACK=false
TARGET_REV=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --target)
            TARGET_REV="$2"
            shift 2
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Check DATABASE_URL
if [[ -z "${DATABASE_URL:-}" ]]; then
    log_error "DATABASE_URL environment variable not set"
    exit 1
fi

cd "$BACKEND_DIR"

# Step 1: Show current migration state
log_info "Current migration state:"
alembic current 2>/dev/null || echo "No migrations applied yet"

# Step 2: Show pending migrations
log_info "Pending migrations:"
alembic history --indicate-current

if [[ "$DRY_RUN" == "true" ]]; then
    log_info "=== DRY RUN MODE - Generating SQL preview ==="

    # Generate SQL for each pending migration
    log_info "SQL for migration 002_fix_status_enum:"
    alembic upgrade 001_workflow_checkpoints:002_fix_status_enum --sql 2>/dev/null || true

    log_info "SQL for migration 003_add_workflow_id_index:"
    alembic upgrade 002_fix_status_enum:003_add_workflow_id_index --sql 2>/dev/null || true

    log_info "=== DRY RUN COMPLETE ==="
    exit 0
fi

if [[ "$ROLLBACK" == "true" ]]; then
    log_warn "=== ROLLBACK MODE ==="

    if [[ -n "$TARGET_REV" ]]; then
        log_info "Rolling back to: $TARGET_REV"
        alembic downgrade "$TARGET_REV"
    else
        log_info "Rolling back one step..."
        alembic downgrade -1
    fi

    log_info "Current state after rollback:"
    alembic current
    exit 0
fi

# Step 3: Pre-migration safety checks
log_info "=== PRE-MIGRATION SAFETY CHECKS ==="

# Check for active connections
log_info "Checking for active connections to workflow_checkpoints..."
ACTIVE_QUERIES=$(psql "$DATABASE_URL" -t -c "
    SELECT count(*) FROM pg_stat_activity
    WHERE state = 'active'
    AND query ILIKE '%workflow_checkpoints%'
    AND pid != pg_backend_pid();
" 2>/dev/null || echo "0")

if [[ "$ACTIVE_QUERIES" -gt 0 ]]; then
    log_warn "Found $ACTIVE_QUERIES active queries on workflow_checkpoints"
    log_warn "Consider waiting for queries to complete or running in maintenance window"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 4: Create backup point
log_info "Creating pre-migration backup marker..."
BACKUP_MARKER="pre_migration_$(date +%Y%m%d_%H%M%S)"
psql "$DATABASE_URL" -c "COMMENT ON TABLE workflow_checkpoints IS 'backup_marker: $BACKUP_MARKER';" 2>/dev/null || true

# Step 5: Apply migrations
log_info "=== APPLYING MIGRATIONS ==="

if [[ -n "$TARGET_REV" ]]; then
    log_info "Upgrading to specific revision: $TARGET_REV"
    alembic upgrade "$TARGET_REV"
else
    log_info "Upgrading to head..."
    alembic upgrade head
fi

# Step 6: Post-migration verification
log_info "=== POST-MIGRATION VERIFICATION ==="

# Verify status enum constraint
log_info "Verifying status constraint..."
CONSTRAINT_CHECK=$(psql "$DATABASE_URL" -t -c "
    SELECT constraint_name
    FROM information_schema.table_constraints
    WHERE table_name = 'workflow_checkpoints'
    AND constraint_name = 'ck_valid_status';
" 2>/dev/null)

if [[ -n "$CONSTRAINT_CHECK" ]]; then
    log_info "✓ Status constraint verified"
else
    log_error "✗ Status constraint not found!"
fi

# Verify indexes
log_info "Verifying indexes..."
INDEX_CHECK=$(psql "$DATABASE_URL" -t -c "
    SELECT indexname
    FROM pg_indexes
    WHERE tablename = 'workflow_checkpoints'
    AND indexname LIKE 'ix_workflow_checkpoints_workflow%';
" 2>/dev/null)

if [[ -n "$INDEX_CHECK" ]]; then
    log_info "✓ Workflow indexes verified"
else
    log_warn "Workflow indexes may not be applied yet"
fi

# Test write with new status
log_info "Testing write with new status enum..."
TEST_RESULT=$(psql "$DATABASE_URL" -t -c "
    INSERT INTO workflow_checkpoints (run_id, status, version)
    VALUES ('__migration_test__', 'budget_exceeded', 1)
    ON CONFLICT (run_id) DO UPDATE SET status = 'budget_exceeded'
    RETURNING run_id;
" 2>/dev/null)

if [[ -n "$TEST_RESULT" ]]; then
    log_info "✓ New status enum write successful"
    # Cleanup test row
    psql "$DATABASE_URL" -c "DELETE FROM workflow_checkpoints WHERE run_id = '__migration_test__';" 2>/dev/null
else
    log_error "✗ New status enum write failed!"
fi

# Step 7: Show final state
log_info "=== MIGRATION COMPLETE ==="
log_info "Current migration state:"
alembic current

log_info "Table indexes:"
psql "$DATABASE_URL" -c "
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'workflow_checkpoints';
" 2>/dev/null || true

log_info "Constraint check:"
psql "$DATABASE_URL" -c "
    SELECT constraint_name, check_clause
    FROM information_schema.check_constraints
    WHERE constraint_name LIKE 'ck_%';
" 2>/dev/null || true

log_info "Migration deployment complete!"
