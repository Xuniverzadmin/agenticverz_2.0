#!/bin/bash
# M9 Monitoring Deployment Script
#
# Automates:
# 1. Grafana dashboard import
# 2. Prometheus rules reload
# 3. Alertmanager config reload
#
# Usage:
#   ./scripts/ops/m9_monitoring_deploy.sh
#   GRAFANA_API_KEY=xxx ./scripts/ops/m9_monitoring_deploy.sh
#
# Environment variables:
#   GRAFANA_URL      - Grafana URL (default: http://localhost:3000)
#   GRAFANA_API_KEY  - Grafana API key (optional, uses admin/admin if not set)
#   PROMETHEUS_URL   - Prometheus URL (default: http://localhost:9090)
#   ALERTMANAGER_URL - Alertmanager URL (default: http://localhost:9093)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Defaults
GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
PROMETHEUS_URL=${PROMETHEUS_URL:-http://localhost:9090}
ALERTMANAGER_URL=${ALERTMANAGER_URL:-http://localhost:9093}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== M9 Monitoring Deployment ==="
echo "Grafana:     $GRAFANA_URL"
echo "Prometheus:  $PROMETHEUS_URL"
echo "Alertmanager: $ALERTMANAGER_URL"
echo ""

# Track results
RESULTS=()

# 1. Import Grafana Dashboard
import_grafana_dashboard() {
    echo -e "${YELLOW}[1/3] Importing Grafana dashboard...${NC}"

    DASHBOARD_FILE="$PROJECT_ROOT/monitoring/dashboards/m9_failure_catalog_v2.json"

    if [[ ! -f "$DASHBOARD_FILE" ]]; then
        echo -e "${RED}  ✗ Dashboard file not found: $DASHBOARD_FILE${NC}"
        RESULTS+=("Grafana dashboard: FAILED (file not found)")
        return 1
    fi

    # Build auth header
    if [[ -n "$GRAFANA_API_KEY" ]]; then
        AUTH_HEADER="Authorization: Bearer $GRAFANA_API_KEY"
    else
        # Use basic auth with admin/admin
        AUTH_HEADER="Authorization: Basic $(echo -n 'admin:admin' | base64)"
    fi

    # Wrap dashboard in import format
    IMPORT_JSON=$(jq '{dashboard: ., overwrite: true}' "$DASHBOARD_FILE")

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$GRAFANA_URL/api/dashboards/db" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        --data "$IMPORT_JSON" 2>/dev/null)

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
        DASHBOARD_URL=$(echo "$BODY" | jq -r '.url // "unknown"')
        echo -e "${GREEN}  ✓ Dashboard imported successfully${NC}"
        echo "    URL: $GRAFANA_URL$DASHBOARD_URL"
        RESULTS+=("Grafana dashboard: SUCCESS")
        return 0
    else
        echo -e "${RED}  ✗ Failed to import dashboard (HTTP $HTTP_CODE)${NC}"
        echo "    Response: $BODY"
        RESULTS+=("Grafana dashboard: FAILED (HTTP $HTTP_CODE)")
        return 1
    fi
}

# 2. Reload Prometheus
reload_prometheus() {
    echo -e "${YELLOW}[2/3] Reloading Prometheus rules...${NC}"

    # Check if Prometheus is reachable
    if ! curl -s "$PROMETHEUS_URL/-/healthy" > /dev/null 2>&1; then
        echo -e "${RED}  ✗ Prometheus not reachable at $PROMETHEUS_URL${NC}"
        RESULTS+=("Prometheus reload: FAILED (not reachable)")
        return 1
    fi

    # Reload
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$PROMETHEUS_URL/-/reload" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo -e "${GREEN}  ✓ Prometheus reloaded successfully${NC}"
        RESULTS+=("Prometheus reload: SUCCESS")
        return 0
    else
        echo -e "${RED}  ✗ Failed to reload Prometheus (HTTP $HTTP_CODE)${NC}"
        RESULTS+=("Prometheus reload: FAILED (HTTP $HTTP_CODE)")
        return 1
    fi
}

# 3. Reload Alertmanager
reload_alertmanager() {
    echo -e "${YELLOW}[3/3] Reloading Alertmanager...${NC}"

    # Check if Alertmanager is reachable
    if ! curl -s "$ALERTMANAGER_URL/-/healthy" > /dev/null 2>&1; then
        echo -e "${RED}  ✗ Alertmanager not reachable at $ALERTMANAGER_URL${NC}"
        RESULTS+=("Alertmanager reload: FAILED (not reachable)")
        return 1
    fi

    # Reload
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ALERTMANAGER_URL/-/reload" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo -e "${GREEN}  ✓ Alertmanager reloaded successfully${NC}"
        RESULTS+=("Alertmanager reload: SUCCESS")
        return 0
    else
        echo -e "${RED}  ✗ Failed to reload Alertmanager (HTTP $HTTP_CODE)${NC}"
        RESULTS+=("Alertmanager reload: FAILED (HTTP $HTTP_CODE)")
        return 1
    fi
}

# 4. Validate M9 alert rules
validate_alert_rules() {
    echo -e "${YELLOW}[4/4] Validating M9 alert rules...${NC}"

    RESPONSE=$(curl -s "$PROMETHEUS_URL/api/v1/rules" 2>/dev/null)

    if [[ -z "$RESPONSE" ]]; then
        echo -e "${YELLOW}  ⚠ Could not fetch rules${NC}"
        return 0
    fi

    # Check for M9-specific rules
    M9_RULES=$(echo "$RESPONSE" | jq -r '.data.groups[]?.rules[]?.name // empty' 2>/dev/null | grep -i "failure" || true)

    if [[ -n "$M9_RULES" ]]; then
        echo -e "${GREEN}  ✓ M9 alert rules found:${NC}"
        echo "$M9_RULES" | while read -r rule; do
            echo "    - $rule"
        done
    else
        echo -e "${YELLOW}  ⚠ No M9-specific alert rules found${NC}"
    fi

    return 0
}

# Main
main() {
    echo ""

    import_grafana_dashboard || true
    echo ""

    reload_prometheus || true
    echo ""

    reload_alertmanager || true
    echo ""

    validate_alert_rules || true
    echo ""

    # Summary
    echo "=== Summary ==="
    for result in "${RESULTS[@]}"; do
        if [[ "$result" == *"SUCCESS"* ]]; then
            echo -e "${GREEN}  ✓ $result${NC}"
        else
            echo -e "${RED}  ✗ $result${NC}"
        fi
    done

    # Check if all passed
    FAILED=$(printf '%s\n' "${RESULTS[@]}" | grep -c "FAILED" || true)
    if [[ "$FAILED" -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}All monitoring deployments successful!${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}$FAILED deployment(s) failed${NC}"
        exit 1
    fi
}

main "$@"
