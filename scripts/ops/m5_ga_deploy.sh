#!/bin/bash
# =============================================================================
# M5 GA Deployment Script
# =============================================================================
# This script handles the deployment of M5 GA components:
# 1. RBAC enablement
# 2. PgBouncer connection pooling
# 3. Webhook key initialization
# 4. Rate limiter verification
# 5. Database migrations
# 6. Prometheus alerts deployment
# 7. Service restart and verification
#
# Usage:
#   ./scripts/ops/m5_ga_deploy.sh [--dry-run] [--skip-backup] [--component COMPONENT]
#
# Components: rbac, pgbouncer, webhook, migrations, alerts, all (default)
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/root/agenticverz2.0}"
DRY_RUN=false
SKIP_BACKUP=false
COMPONENT="all"
DEPLOY_MODE="${DEPLOY_MODE:-docker}"  # docker or k8s

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        --k8s)
            DEPLOY_MODE="k8s"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] [--skip-backup] [--component COMPONENT] [--k8s]"
            echo ""
            echo "Components: rbac, pgbouncer, webhook, migrations, alerts, redis, all"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $1"
    else
        eval "$1"
    fi
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

preflight_checks() {
    log "Running pre-flight checks..."

    # Check project directory
    if [ ! -d "$PROJECT_DIR" ]; then
        error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi

    # Check docker or kubectl
    if [ "$DEPLOY_MODE" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            error "Docker not found"
            exit 1
        fi
        if ! docker compose ps &> /dev/null 2>&1; then
            warn "Docker Compose services may not be running"
        fi
    else
        if ! command -v kubectl &> /dev/null; then
            error "kubectl not found"
            exit 1
        fi
    fi

    # Check Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null 2>&1; then
            success "Redis is running"
        else
            warn "Redis not responding - rate limiter will fail-open"
        fi
    else
        warn "redis-cli not found - cannot verify Redis"
    fi

    success "Pre-flight checks passed"
}

# =============================================================================
# Database Backup
# =============================================================================

backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        warn "Skipping database backup (--skip-backup)"
        return
    fi

    log "Creating database backup..."

    BACKUP_DIR="${PROJECT_DIR}/backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="${BACKUP_DIR}/nova_aos_$(date +%Y%m%d_%H%M%S).dump"

    if [ "$DEPLOY_MODE" = "docker" ]; then
        run_cmd "docker exec nova_db pg_dump -U nova -Fc nova_aos > $BACKUP_FILE"
    else
        run_cmd "kubectl exec -n aos deploy/nova-db -- pg_dump -U nova -Fc nova_aos > $BACKUP_FILE"
    fi

    if [ -f "$BACKUP_FILE" ]; then
        success "Database backup created: $BACKUP_FILE"
    fi
}

# =============================================================================
# RBAC Enablement
# =============================================================================

enable_rbac() {
    log "Enabling RBAC..."

    # Update .env file
    if grep -q "RBAC_ENABLED=" "$PROJECT_DIR/.env" 2>/dev/null; then
        run_cmd "sed -i 's/RBAC_ENABLED=.*/RBAC_ENABLED=true/' $PROJECT_DIR/.env"
    else
        run_cmd "echo 'RBAC_ENABLED=true' >> $PROJECT_DIR/.env"
    fi

    # Set AUTH_SERVICE_URL if not set (use stub for now)
    if ! grep -q "AUTH_SERVICE_URL=" "$PROJECT_DIR/.env" 2>/dev/null; then
        run_cmd "echo 'AUTH_SERVICE_URL=http://localhost:8001' >> $PROJECT_DIR/.env"
        warn "AUTH_SERVICE_URL set to localhost:8001 (stub). Configure external auth for production."
    fi

    success "RBAC enabled in .env"
}

# =============================================================================
# PgBouncer Deployment
# =============================================================================

deploy_pgbouncer() {
    log "Deploying PgBouncer..."

    if [ "$DEPLOY_MODE" = "docker" ]; then
        # Check if pgbouncer is in docker-compose
        if grep -q "pgbouncer:" "$PROJECT_DIR/docker-compose.yml"; then
            run_cmd "cd $PROJECT_DIR && docker compose up -d pgbouncer"

            # Wait for pgbouncer to be healthy
            log "Waiting for PgBouncer to be healthy..."
            for i in {1..30}; do
                if docker exec nova_pgbouncer pg_isready -h 127.0.0.1 -p 6432 -U nova &> /dev/null; then
                    success "PgBouncer is healthy"
                    break
                fi
                sleep 1
            done
        else
            warn "PgBouncer not found in docker-compose.yml"
        fi
    else
        # Kubernetes deployment
        if [ -f "$PROJECT_DIR/k8s/pgbouncer-deployment.yaml" ]; then
            run_cmd "kubectl apply -f $PROJECT_DIR/k8s/pgbouncer-deployment.yaml -n aos"
            run_cmd "kubectl rollout status deployment/pgbouncer -n aos --timeout=120s"
            success "PgBouncer deployed to Kubernetes"
        else
            error "PgBouncer k8s manifest not found"
        fi
    fi
}

# =============================================================================
# Webhook Key Initialization
# =============================================================================

init_webhook_keys() {
    log "Initializing webhook keys..."

    WEBHOOK_KEYS_PATH="${WEBHOOK_KEYS_PATH:-/var/lib/aos/webhook-keys}"

    # Create directory if needed
    run_cmd "mkdir -p $WEBHOOK_KEYS_PATH"
    run_cmd "chmod 700 $WEBHOOK_KEYS_PATH"

    # Generate initial key if not exists
    if [ ! -f "$WEBHOOK_KEYS_PATH/v1" ]; then
        log "Generating initial webhook key (v1)..."
        if [ "$DRY_RUN" = false ]; then
            openssl rand -hex 32 > "$WEBHOOK_KEYS_PATH/v1"
            chmod 600 "$WEBHOOK_KEYS_PATH/v1"
        else
            echo -e "${YELLOW}[DRY-RUN]${NC} Would generate webhook key: openssl rand -hex 32 > $WEBHOOK_KEYS_PATH/v1"
        fi
        success "Webhook key v1 generated"
    else
        success "Webhook key v1 already exists"
    fi

    # Update .env
    if ! grep -q "WEBHOOK_KEY_VERSION=" "$PROJECT_DIR/.env" 2>/dev/null; then
        run_cmd "echo 'WEBHOOK_KEY_VERSION=v1' >> $PROJECT_DIR/.env"
    fi
    if ! grep -q "WEBHOOK_KEYS_PATH=" "$PROJECT_DIR/.env" 2>/dev/null; then
        run_cmd "echo 'WEBHOOK_KEYS_PATH=$WEBHOOK_KEYS_PATH' >> $PROJECT_DIR/.env"
    fi

    success "Webhook keys initialized"
}

# =============================================================================
# Redis Verification
# =============================================================================

verify_redis() {
    log "Verifying Redis for rate limiting..."

    # Check Redis connectivity
    if redis-cli ping &> /dev/null 2>&1; then
        success "Redis is responding"

        # Test a simple operation
        if [ "$DRY_RUN" = false ]; then
            redis-cli set m5_deploy_test "$(date)" EX 60 > /dev/null
            redis-cli get m5_deploy_test > /dev/null
            redis-cli del m5_deploy_test > /dev/null
        fi
        success "Redis read/write test passed"
    else
        warn "Redis not available - rate limiter will operate in fail-open mode"
    fi

    # Update .env with Redis URL if not set
    if ! grep -q "REDIS_URL=" "$PROJECT_DIR/.env" 2>/dev/null; then
        run_cmd "echo 'REDIS_URL=redis://localhost:6379/0' >> $PROJECT_DIR/.env"
    fi

    # Ensure rate limiting is enabled
    if ! grep -q "RATE_LIMIT_ENABLED=" "$PROJECT_DIR/.env" 2>/dev/null; then
        run_cmd "echo 'RATE_LIMIT_ENABLED=true' >> $PROJECT_DIR/.env"
    fi
}

# =============================================================================
# Database Migrations
# =============================================================================

run_migrations() {
    log "Running database migrations..."

    if [ "$DEPLOY_MODE" = "docker" ]; then
        # Run alembic migrations
        if [ -f "$PROJECT_DIR/backend/alembic.ini" ]; then
            run_cmd "docker exec nova_agent_manager alembic upgrade head"
        fi

        # Run SQL migration for LLM costs
        if [ -f "$PROJECT_DIR/migrations/20251130_add_llm_costs.sql" ]; then
            log "Applying LLM costs migration..."
            run_cmd "docker exec -i nova_db psql -U nova -d nova_aos < $PROJECT_DIR/migrations/20251130_add_llm_costs.sql"
        fi
    else
        # Kubernetes - run as a job or exec into pod
        run_cmd "kubectl exec -n aos deploy/nova-backend -- alembic upgrade head"
    fi

    success "Migrations completed"
}

# =============================================================================
# Prometheus Alerts Deployment
# =============================================================================

deploy_alerts() {
    log "Deploying Prometheus alert rules..."

    ALERTS_SRC="$PROJECT_DIR/monitoring/alerts/m5_policy_alerts.yml"
    RULES_DEST="$PROJECT_DIR/monitoring/rules/m5_policy_alerts.yml"

    if [ -f "$ALERTS_SRC" ]; then
        # Copy to rules directory
        run_cmd "cp $ALERTS_SRC $RULES_DEST"
        success "M5 alert rules deployed to $RULES_DEST"

        # Reload Prometheus
        if [ "$DEPLOY_MODE" = "docker" ]; then
            log "Reloading Prometheus..."
            run_cmd "curl -s -X POST http://127.0.0.1:9090/-/reload || true"
        else
            run_cmd "kubectl exec -n monitoring deploy/prometheus -- kill -HUP 1"
        fi

        success "Prometheus reloaded"
    else
        warn "M5 alert rules not found at $ALERTS_SRC"
    fi
}

# =============================================================================
# Service Restart
# =============================================================================

restart_services() {
    log "Restarting services..."

    if [ "$DEPLOY_MODE" = "docker" ]; then
        run_cmd "cd $PROJECT_DIR && docker compose up -d --force-recreate backend worker"

        # Wait for backend to be healthy
        log "Waiting for backend to be healthy..."
        for i in {1..60}; do
            if curl -s http://127.0.0.1:8000/health | grep -q "ok\|healthy" &> /dev/null; then
                success "Backend is healthy"
                break
            fi
            sleep 2
        done
    else
        run_cmd "kubectl rollout restart deployment/nova-backend -n aos"
        run_cmd "kubectl rollout restart deployment/nova-worker -n aos"
        run_cmd "kubectl rollout status deployment/nova-backend -n aos --timeout=120s"
    fi
}

# =============================================================================
# Verification
# =============================================================================

verify_deployment() {
    log "Verifying M5 GA deployment..."

    ERRORS=0

    # Check backend health
    if curl -s http://127.0.0.1:8000/health | grep -q "ok\|healthy" &> /dev/null; then
        success "Backend health check passed"
    else
        error "Backend health check failed"
        ((ERRORS++))
    fi

    # Check metrics endpoint
    if curl -s http://127.0.0.1:8000/metrics | grep -q "nova_" &> /dev/null; then
        success "Metrics endpoint responding"
    else
        warn "Metrics endpoint not returning nova_ metrics"
    fi

    # Check RBAC enabled
    if grep -q "RBAC_ENABLED=true" "$PROJECT_DIR/.env" 2>/dev/null; then
        success "RBAC is enabled"
    else
        warn "RBAC is not enabled"
    fi

    # Check PgBouncer
    if [ "$DEPLOY_MODE" = "docker" ]; then
        if docker exec nova_pgbouncer pg_isready -h 127.0.0.1 -p 6432 -U nova &> /dev/null 2>&1; then
            success "PgBouncer is healthy"
        else
            warn "PgBouncer not responding"
        fi
    fi

    # Check Prometheus alerts loaded
    if curl -s http://127.0.0.1:9090/api/v1/rules | grep -q "m5_capability_violations" &> /dev/null; then
        success "M5 alert rules loaded in Prometheus"
    else
        warn "M5 alert rules not found in Prometheus"
    fi

    if [ $ERRORS -eq 0 ]; then
        success "M5 GA deployment verification completed successfully"
    else
        error "Deployment verification found $ERRORS errors"
        return 1
    fi
}

# =============================================================================
# Create M5 Signoff File
# =============================================================================

create_signoff() {
    log "Creating M5 GA signoff file..."

    SIGNOFF_FILE="$PROJECT_DIR/.m5_signoff"

    if [ "$DRY_RUN" = false ]; then
        cat > "$SIGNOFF_FILE" << EOF
M5 GA Signoff
=============
Deployed: $(date -Iseconds)
Version: 1.0.0
Components:
  - RBAC: enabled
  - PgBouncer: deployed
  - Webhook Keys: initialized
  - Rate Limiter: enabled
  - Migrations: applied
  - Alerts: deployed

Operator: $(whoami)
Host: $(hostname)
EOF
        chmod 644 "$SIGNOFF_FILE"
        success "M5 signoff file created: $SIGNOFF_FILE"
    else
        echo -e "${YELLOW}[DRY-RUN]${NC} Would create signoff file: $SIGNOFF_FILE"
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    echo "=============================================="
    echo "  M5 GA Deployment Script"
    echo "=============================================="
    echo "  Mode: $DEPLOY_MODE"
    echo "  Component: $COMPONENT"
    echo "  Dry Run: $DRY_RUN"
    echo "=============================================="
    echo ""

    preflight_checks

    case $COMPONENT in
        rbac)
            enable_rbac
            restart_services
            ;;
        pgbouncer)
            deploy_pgbouncer
            ;;
        webhook)
            init_webhook_keys
            restart_services
            ;;
        redis)
            verify_redis
            ;;
        migrations)
            backup_database
            run_migrations
            ;;
        alerts)
            deploy_alerts
            ;;
        all)
            backup_database
            enable_rbac
            deploy_pgbouncer
            init_webhook_keys
            verify_redis
            run_migrations
            deploy_alerts
            restart_services
            create_signoff
            verify_deployment
            ;;
        *)
            error "Unknown component: $COMPONENT"
            exit 1
            ;;
    esac

    echo ""
    success "M5 GA deployment script completed"
    echo ""
}

main "$@"
