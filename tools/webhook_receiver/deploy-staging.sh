#!/usr/bin/env bash
# deploy-staging.sh - Deploy webhook receiver to staging Kubernetes cluster
#
# Usage:
#   IMAGE_SHA=abc123def456 ./deploy-staging.sh
#
# Environment Variables:
#   IMAGE_SHA        - Required. Docker image SHA tag to deploy
#   NAMESPACE        - Kubernetes namespace (default: aos-staging)
#   KUBE_CONTEXT     - kubectl context to use (optional)
#   REDIS_URL        - Redis URL for rate limiting (will prompt if not set)
#   HMAC_SECRET      - HMAC secret for webhook validation (will prompt if not set)
#   GRAFANA_API_KEY  - Optional. Import dashboard if provided
#   GRAFANA_URL      - Grafana URL (default: http://localhost:3000)
#   DRY_RUN          - If set to "true", only print what would be done
#
# Requirements:
#   - kubectl configured with cluster access
#   - kustomize installed
#   - curl for smoke tests

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Configuration
NAMESPACE="${NAMESPACE:-aos-staging}"
REGISTRY="${REGISTRY:-ghcr.io/aos/webhook-receiver}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/k8s"
OVERLAY_DIR="${K8S_DIR}/overlay-staging"

# Validate required environment
if [[ -z "${IMAGE_SHA:-}" ]]; then
    log_error "IMAGE_SHA environment variable is required"
    echo "Usage: IMAGE_SHA=abc123def456 ./deploy-staging.sh"
    exit 1
fi

log_info "Deploying webhook-receiver with IMAGE_SHA=${IMAGE_SHA}"
log_info "Namespace: ${NAMESPACE}"

# Check if dry run
if [[ "${DRY_RUN:-false}" == "true" ]]; then
    log_warn "DRY_RUN mode - no changes will be made"
fi

# Switch kubectl context if specified
if [[ -n "${KUBE_CONTEXT:-}" ]]; then
    log_info "Using kubectl context: ${KUBE_CONTEXT}"
    kubectl config use-context "${KUBE_CONTEXT}"
fi

# Verify cluster access
log_info "Verifying cluster access..."
if ! kubectl cluster-info &>/dev/null; then
    log_error "Cannot connect to Kubernetes cluster"
    exit 1
fi
log_success "Cluster access verified"

# Create namespace if it doesn't exist
if ! kubectl get namespace "${NAMESPACE}" &>/dev/null; then
    log_info "Creating namespace ${NAMESPACE}..."
    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        kubectl create namespace "${NAMESPACE}"
    fi
    log_success "Namespace created"
fi

# Create or update secrets
create_secrets() {
    log_info "Checking secrets..."

    # Check if secret exists
    if kubectl -n "${NAMESPACE}" get secret webhook-secret &>/dev/null; then
        log_info "Secret webhook-secret already exists"
        return 0
    fi

    # Prompt for values if not provided
    if [[ -z "${REDIS_URL:-}" ]]; then
        log_warn "REDIS_URL not set. Using placeholder value."
        REDIS_URL="redis://redis:6379/0"
    fi

    if [[ -z "${HMAC_SECRET:-}" ]]; then
        log_warn "HMAC_SECRET not set. Generating random secret."
        HMAC_SECRET=$(openssl rand -hex 32)
    fi

    log_info "Creating webhook-secret..."
    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        kubectl -n "${NAMESPACE}" create secret generic webhook-secret \
            --from-literal=REDIS_URL="${REDIS_URL}" \
            --from-literal=HMAC_SECRET="${HMAC_SECRET}" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    log_success "Secret created/updated"
}

# Update kustomize with image SHA
update_kustomize() {
    log_info "Updating kustomize overlay with image SHA..."

    cd "${OVERLAY_DIR}"

    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        # Use kustomize edit to set the image
        kustomize edit set image "webhook-receiver=${REGISTRY}:${IMAGE_SHA}"
    fi

    log_success "Kustomize overlay updated"
}

# Apply manifests
apply_manifests() {
    log_info "Applying Kubernetes manifests..."

    cd "${OVERLAY_DIR}"

    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log_info "Would apply:"
        kustomize build . | kubectl apply --dry-run=client -f - 2>&1 | head -20
    else
        kustomize build . | kubectl apply -f -
    fi

    log_success "Manifests applied"
}

# Wait for rollout
wait_for_rollout() {
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log_info "Would wait for rollout..."
        return 0
    fi

    log_info "Waiting for deployment rollout..."
    if kubectl -n "${NAMESPACE}" rollout status deployment/webhook-receiver --timeout=300s; then
        log_success "Deployment rolled out successfully"
    else
        log_error "Deployment rollout failed or timed out"
        kubectl -n "${NAMESPACE}" get pods -l app=webhook-receiver
        kubectl -n "${NAMESPACE}" describe deployment webhook-receiver
        exit 1
    fi
}

# Run smoke tests
run_smoke_tests() {
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log_info "Would run smoke tests..."
        return 0
    fi

    log_info "Running smoke tests..."

    # Port forward in background
    kubectl -n "${NAMESPACE}" port-forward svc/webhook-receiver 8081:80 &
    PF_PID=$!
    trap "kill ${PF_PID} 2>/dev/null || true" EXIT

    # Wait for port forward to be ready
    sleep 5

    # Health check
    log_info "Testing /health endpoint..."
    if curl -sf http://localhost:8081/health; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        kill ${PF_PID} 2>/dev/null || true
        exit 1
    fi

    echo ""

    # Webhook test
    log_info "Testing /webhook endpoint..."
    RESPONSE=$(curl -sf -X POST http://localhost:8081/webhook \
        -H "Content-Type: application/json" \
        -d '{"test": "smoke-test", "timestamp": "'"$(date -Iseconds)"'"}')

    if [[ -n "${RESPONSE}" ]]; then
        log_success "Webhook test passed"
        echo "Response: ${RESPONSE}"
    else
        log_error "Webhook test failed"
        kill ${PF_PID} 2>/dev/null || true
        exit 1
    fi

    # Metrics check
    log_info "Testing /metrics endpoint..."
    if curl -sf http://localhost:8081/metrics | grep -q "webhooks_received_total"; then
        log_success "Metrics endpoint working"
    else
        log_warn "Metrics endpoint returned unexpected response"
    fi

    # Rate limit test (should allow first request)
    log_info "Testing rate limiter..."
    for i in {1..5}; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8081/webhook \
            -H "Content-Type: application/json" \
            -H "X-Tenant-ID: test-tenant" \
            -d '{"test": "rate-limit-'"${i}"'"}')
        echo "  Request ${i}: HTTP ${STATUS}"
    done

    log_success "Smoke tests completed"

    # Cleanup port forward
    kill ${PF_PID} 2>/dev/null || true
}

# Import Grafana dashboard
import_grafana_dashboard() {
    if [[ -z "${GRAFANA_API_KEY:-}" ]]; then
        log_info "GRAFANA_API_KEY not set, skipping dashboard import"
        return 0
    fi

    DASHBOARD_FILE="${SCRIPT_DIR}/../../monitoring/dashboards/webhook-receiver.json"

    if [[ ! -f "${DASHBOARD_FILE}" ]]; then
        log_warn "Dashboard file not found: ${DASHBOARD_FILE}"
        return 0
    fi

    log_info "Importing Grafana dashboard..."

    # Wrap dashboard in import payload
    PAYLOAD=$(jq -n --slurpfile dashboard "${DASHBOARD_FILE}" \
        '{dashboard: $dashboard[0], overwrite: true, folderId: 0}')

    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        RESPONSE=$(curl -sf -X POST "${GRAFANA_URL}/api/dashboards/db" \
            -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
            -H "Content-Type: application/json" \
            -d "${PAYLOAD}")

        if echo "${RESPONSE}" | jq -e '.uid' &>/dev/null; then
            UID=$(echo "${RESPONSE}" | jq -r '.uid')
            log_success "Dashboard imported: ${GRAFANA_URL}/d/${UID}"
        else
            log_warn "Dashboard import response: ${RESPONSE}"
        fi
    fi
}

# Print deployment summary
print_summary() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Deployment Summary${NC}"
    echo "=========================================="
    echo "Namespace:    ${NAMESPACE}"
    echo "Image:        ${REGISTRY}:${IMAGE_SHA}"
    echo ""

    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        echo "Pods:"
        kubectl -n "${NAMESPACE}" get pods -l app=webhook-receiver -o wide
        echo ""
        echo "Service:"
        kubectl -n "${NAMESPACE}" get svc webhook-receiver
    fi

    echo ""
    echo "Next steps:"
    echo "  1. Verify ingress/load balancer is configured"
    echo "  2. Update DNS if needed"
    echo "  3. Test with real webhook from Alertmanager"
    echo ""
}

# Main execution
main() {
    log_info "Starting deployment..."

    create_secrets
    update_kustomize
    apply_manifests
    wait_for_rollout
    run_smoke_tests
    import_grafana_dashboard
    print_summary

    log_success "Deployment completed successfully!"
}

main "$@"
