#!/bin/bash
# Synthetic Alert Verification Script
# Fires test metrics to verify Prometheus -> Alertmanager -> notification flow
#
# Usage:
#   ./scripts/ci/synthetic_alert.sh                    # Fire all test alerts
#   ./scripts/ci/synthetic_alert.sh --alert replay     # Fire specific alert
#   ./scripts/ci/synthetic_alert.sh --verify           # Verify alert fired in Alertmanager

set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://127.0.0.1:9093}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse args
ALERT_TYPE="all"
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --alert)
            ALERT_TYPE="$2"
            shift 2
            ;;
        --verify)
            VERIFY_ONLY=true
            shift
            ;;
        *)
            log_error "Unknown arg: $1"
            exit 1
            ;;
    esac
done

# Check services are up
check_services() {
    log_info "Checking service availability..."

    if ! curl -sf "$PROMETHEUS_URL/-/ready" > /dev/null 2>&1; then
        log_error "Prometheus not ready at $PROMETHEUS_URL"
        return 1
    fi
    log_info "✓ Prometheus ready"

    if ! curl -sf "$ALERTMANAGER_URL/-/ready" > /dev/null 2>&1; then
        log_error "Alertmanager not ready at $ALERTMANAGER_URL"
        return 1
    fi
    log_info "✓ Alertmanager ready"

    if ! curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_warn "Backend not responding at $BACKEND_URL (may be expected)"
    else
        log_info "✓ Backend ready"
    fi

    return 0
}

# Fire synthetic replay failure metric
fire_replay_failure() {
    log_info "Firing synthetic replay failure metric..."

    # Push metric via pushgateway or direct increment
    # Since we don't have pushgateway, we'll use a test endpoint

    # Create a Python script to increment the metric
    python3 << 'EOF'
import sys
sys.path.insert(0, '/root/agenticverz2.0/backend')

try:
    from app.workflow.metrics import record_replay_verification
    # Fire 3 failures to trigger alert (threshold is > 0 in 5m)
    for _ in range(3):
        record_replay_verification(passed=False, failure_type="synthetic_test", spec_id="test-workflow")
    print("✓ Replay failure metrics fired")
except Exception as e:
    print(f"✗ Failed to fire metrics: {e}")
    sys.exit(1)
EOF
}

# Fire synthetic checkpoint failure metric
fire_checkpoint_failure() {
    log_info "Firing synthetic checkpoint failure metric..."

    python3 << 'EOF'
import sys
sys.path.insert(0, '/root/agenticverz2.0/backend')

try:
    from app.workflow.metrics import record_checkpoint_operation
    # Fire failures
    for _ in range(3):
        record_checkpoint_operation(operation="save", success=False, duration_seconds=0.5)
    print("✓ Checkpoint failure metrics fired")
except Exception as e:
    print(f"✗ Failed to fire metrics: {e}")
    sys.exit(1)
EOF
}

# Fire synthetic budget exceeded metric
fire_budget_exceeded() {
    log_info "Firing synthetic budget exceeded metric..."

    python3 << 'EOF'
import sys
sys.path.insert(0, '/root/agenticverz2.0/backend')

try:
    from app.workflow.metrics import record_workflow_failure
    # Fire budget exceeded errors
    for _ in range(6):  # Threshold is > 5 in 15m
        record_workflow_failure(
            error_code="BUDGET_EXCEEDED",
            spec_id="test-workflow",
            tenant_id="test-tenant"
        )
    print("✓ Budget exceeded metrics fired")
except Exception as e:
    print(f"✗ Failed to fire metrics: {e}")
    sys.exit(1)
EOF
}

# Verify alerts in Alertmanager
verify_alerts() {
    log_info "Waiting 30s for alerts to propagate..."
    sleep 30

    log_info "Checking Alertmanager for firing alerts..."

    ALERTS=$(curl -sf "$ALERTMANAGER_URL/api/v2/alerts" 2>/dev/null || echo "[]")

    if [[ "$ALERTS" == "[]" ]]; then
        log_warn "No alerts currently firing"
        return 1
    fi

    echo "$ALERTS" | python3 -c "
import sys
import json

alerts = json.load(sys.stdin)
print(f'Found {len(alerts)} firing alert(s):')
for alert in alerts:
    labels = alert.get('labels', {})
    name = labels.get('alertname', 'unknown')
    severity = labels.get('severity', 'unknown')
    state = alert.get('status', {}).get('state', 'unknown')
    print(f'  - {name} (severity={severity}, state={state})')
"
    return 0
}

# Check alert rules are loaded
check_alert_rules() {
    log_info "Checking Prometheus alert rules..."

    RULES=$(curl -sf "$PROMETHEUS_URL/api/v1/rules" 2>/dev/null)

    if [[ -z "$RULES" ]]; then
        log_error "Could not fetch rules from Prometheus"
        return 1
    fi

    echo "$RULES" | python3 -c "
import sys
import json

data = json.load(sys.stdin)
groups = data.get('data', {}).get('groups', [])
total_rules = 0
alert_rules = []

for group in groups:
    for rule in group.get('rules', []):
        if rule.get('type') == 'alerting':
            total_rules += 1
            alert_rules.append(rule.get('name', 'unknown'))

print(f'Found {total_rules} alert rules:')
for name in sorted(set(alert_rules)):
    print(f'  - {name}')
"
}

# Main execution
main() {
    if ! check_services; then
        log_error "Service check failed"
        exit 1
    fi

    check_alert_rules

    if [[ "$VERIFY_ONLY" == "true" ]]; then
        verify_alerts
        exit $?
    fi

    case "$ALERT_TYPE" in
        replay)
            fire_replay_failure
            ;;
        checkpoint)
            fire_checkpoint_failure
            ;;
        budget)
            fire_budget_exceeded
            ;;
        all)
            fire_replay_failure
            fire_checkpoint_failure
            fire_budget_exceeded
            ;;
        *)
            log_error "Unknown alert type: $ALERT_TYPE"
            log_info "Valid types: replay, checkpoint, budget, all"
            exit 1
            ;;
    esac

    log_info "Metrics fired. Waiting for alert evaluation..."
    log_info "Run with --verify in 2-5 minutes to check if alerts fired"
}

main
