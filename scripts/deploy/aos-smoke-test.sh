#!/bin/bash
# AOS Console + Backend Smoke Test
# Tests production endpoints at agenticverz.com

set -e

echo "=========================================="
echo "  Agenticverz AOS Smoke Test"
echo "=========================================="

BASE="${AOS_API_BASE:-https://agenticverz.com/api/v1}"
KEY="${AOS_API_KEY:-}"

if [ -z "$KEY" ]; then
    echo "WARNING: No API key provided. Set AOS_API_KEY environment variable."
    echo "Running unauthenticated tests only..."
    AUTH_HEADER=""
else
    AUTH_HEADER="Authorization: Bearer $KEY"
fi

echo ""
echo "API Base: $BASE"
echo ""

# Test 1: Health check (no auth required)
echo "[1/6] Checking /health ..."
HEALTH=$(curl -s --max-time 10 "${BASE%/api/v1}/health" 2>/dev/null || echo '{"error":"timeout"}')
echo "$HEALTH" | jq -r '.status // .error' 2>/dev/null || echo "$HEALTH"

# Test 2: Runtime capabilities
echo ""
echo "[2/6] Checking /runtime/capabilities ..."
if [ -n "$AUTH_HEADER" ]; then
    CAPS=$(curl -s --max-time 10 -H "$AUTH_HEADER" "$BASE/runtime/capabilities" 2>/dev/null || echo '{"error":"timeout"}')
    SKILL_COUNT=$(echo "$CAPS" | jq '.skills | length' 2>/dev/null || echo "0")
    echo "Skills available: $SKILL_COUNT"
    echo "Budget: $(echo "$CAPS" | jq -r '.budget.remaining_cents // "N/A"' 2>/dev/null) cents remaining"
else
    echo "Skipped (no auth)"
fi

# Test 3: Agents list
echo ""
echo "[3/6] Checking /agents ..."
if [ -n "$AUTH_HEADER" ]; then
    AGENTS=$(curl -s --max-time 10 -H "$AUTH_HEADER" "${BASE%/api/v1}/agents" 2>/dev/null || echo '[]')
    AGENT_COUNT=$(echo "$AGENTS" | jq 'if type == "array" then length else 0 end' 2>/dev/null || echo "0")
    echo "Agents registered: $AGENT_COUNT"
else
    echo "Skipped (no auth)"
fi

# Test 4: Failures endpoint
echo ""
echo "[4/6] Checking /failures/stats ..."
if [ -n "$AUTH_HEADER" ]; then
    FAILURES=$(curl -s --max-time 10 -H "$AUTH_HEADER" "$BASE/failures/stats" 2>/dev/null || echo '{}')
    echo "$FAILURES" | jq -r 'to_entries | .[:3] | .[] | "\(.key): \(.value)"' 2>/dev/null || echo "No failure stats"
else
    echo "Skipped (no auth)"
fi

# Test 5: Recovery candidates
echo ""
echo "[5/6] Checking /recovery/stats ..."
if [ -n "$AUTH_HEADER" ]; then
    RECOVERY=$(curl -s --max-time 10 -H "$AUTH_HEADER" "$BASE/recovery/stats" 2>/dev/null || echo '{}')
    echo "$RECOVERY" | jq -r 'to_entries | .[:3] | .[] | "\(.key): \(.value)"' 2>/dev/null || echo "No recovery stats"
else
    echo "Skipped (no auth)"
fi

# Test 6: Console static files
echo ""
echo "[6/6] Checking console static files ..."
CONSOLE_URL="${BASE%/api/v1}/console/"
CONSOLE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$CONSOLE_URL" 2>/dev/null || echo "000")
if [ "$CONSOLE_STATUS" = "200" ]; then
    echo "Console: OK (HTTP $CONSOLE_STATUS)"
else
    echo "Console: FAILED (HTTP $CONSOLE_STATUS)"
fi

echo ""
echo "=========================================="
echo "  Smoke Test Complete"
echo "=========================================="
