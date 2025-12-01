#!/bin/bash
# NOVA Agent Manager - Test Alert Routing
# Tests both Slack (warning) and Email (critical/page) paths
#
# Usage: ./test-alerts.sh [warning|page|critical|both|status]

set -e

ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://127.0.0.1:9093}"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

send_alert() {
    local name="$1"
    local severity="$2"
    local summary="$3"

    echo "Sending $severity alert: $name"
    curl -s -XPOST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "[{
            \"labels\": {\"alertname\":\"${name}\",\"severity\":\"${severity}\"},
            \"annotations\": {\"summary\":\"${summary}\",\"description\":\"Test alert sent at ${NOW}\"},
            \"startsAt\":\"${NOW}\"
        }]"
    echo ""
}

case "${1:-both}" in
    warning)
        send_alert "TestWarning" "warning" "Test Warning Alert - should go to Slack"
        ;;
    page)
        send_alert "TestPage" "page" "Test Page Alert - should go to Email"
        ;;
    critical)
        send_alert "TestCritical" "critical" "Test Critical Alert - should go to Email"
        ;;
    both)
        send_alert "TestWarning" "warning" "Test Warning Alert - should go to Slack"
        echo ""
        send_alert "TestCritical" "critical" "Test Critical Alert - should go to Email"
        ;;
    status)
        echo "=== Alertmanager Status ==="
        curl -s "${ALERTMANAGER_URL}/api/v2/status" | jq '.config.original' 2>/dev/null || curl -s "${ALERTMANAGER_URL}/api/v2/status"
        echo ""
        echo "=== Active Alerts ==="
        curl -s "${ALERTMANAGER_URL}/api/v2/alerts" | jq '.[] | {alertname: .labels.alertname, severity: .labels.severity, status: .status.state}' 2>/dev/null || echo "No alerts or jq not available"
        exit 0
        ;;
    *)
        echo "Usage: $0 [warning|page|critical|both|status]"
        echo ""
        echo "Commands:"
        echo "  warning   - Send warning alert (routes to Slack)"
        echo "  page      - Send page alert (routes to Email)"
        echo "  critical  - Send critical alert (routes to Email)"
        echo "  both      - Send warning + critical alerts"
        echo "  status    - Show Alertmanager config and active alerts"
        exit 1
        ;;
esac

echo ""
echo "Check:"
echo "  - Slack channel #alerts for warning alerts"
echo "  - ops@agenticverz.com inbox for critical/page alerts"
echo ""
echo "View active alerts: $0 status"
