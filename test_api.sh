#!/bin/bash
# NOVA Agent Manager - API Test Suite v2.0
# Run this after 'make up' to test all endpoints
# Updated for Phase 2 async flow

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${AOS_API_KEY:-nova-dev-key-change-me}"

echo "======================================"
echo "NOVA Agent Manager - API Test Suite"
echo "======================================"
echo "API URL: $API_URL"
echo "API Key: $API_KEY"
echo ""

# 1. Health Check (no auth required)
echo "1. Health Check"
echo "---------------"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

# 2. Version Info
echo "2. Version Info"
echo "---------------"
curl -s "$API_URL/version" | python3 -m json.tool
echo ""

# 3. Create Agent
echo "3. Create Agent"
echo "---------------"
AGENT_RESPONSE=$(curl -s -X POST "$API_URL/agents" \
  -H "Content-Type: application/json" \
  -H "X-AOS-Key: $API_KEY" \
  -d '{"name":"nova-test-agent"}')

echo "$AGENT_RESPONSE" | python3 -m json.tool

AGENT_ID=$(echo "$AGENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['agent_id'])")
echo ""
echo "Agent ID: $AGENT_ID"
echo ""

# 4. Get Agent
echo "4. Get Agent"
echo "------------"
curl -s "$API_URL/agents/$AGENT_ID" \
  -H "X-AOS-Key: $API_KEY" | python3 -m json.tool
echo ""

# 5. Post Goal (async - returns 202)
echo "5. Post Goal (expect 202 Accepted)"
echo "-----------------------------------"
GOAL_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/agents/$AGENT_ID/goals" \
  -H "Content-Type: application/json" \
  -H "X-AOS-Key: $API_KEY" \
  -d '{"goal":"fetch github zen wisdom"}')

HTTP_CODE=$(echo "$GOAL_RESPONSE" | tail -n 1)
BODY=$(echo "$GOAL_RESPONSE" | head -n -1)

echo "HTTP Status: $HTTP_CODE"
echo "$BODY" | python3 -m json.tool

RUN_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['run_id'])")
echo ""
echo "Run ID: $RUN_ID"
echo ""

# 6. Poll Run Status
echo "6. Poll Run Status"
echo "------------------"
echo "Waiting for run to complete..."
sleep 2

RUN_RESPONSE=$(curl -s "$API_URL/agents/$AGENT_ID/runs/$RUN_ID" \
  -H "X-AOS-Key: $API_KEY")

echo "$RUN_RESPONSE" | python3 -m json.tool

FINAL_STATUS=$(echo "$RUN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
echo ""
echo "Final Status: $FINAL_STATUS"
echo ""

# 7. List Runs for Agent
echo "7. List Runs"
echo "------------"
curl -s "$API_URL/agents/$AGENT_ID/runs?limit=5" \
  -H "X-AOS-Key: $API_KEY" | python3 -m json.tool
echo ""

# 8. Recall Memory
echo "8. Recall Memory"
echo "----------------"
curl -s "$API_URL/agents/$AGENT_ID/recall?query=Skill&k=5" \
  -H "X-AOS-Key: $API_KEY" | python3 -m json.tool
echo ""

# 9. Get Provenance List
echo "9. Get Provenance List"
echo "----------------------"
curl -s "$API_URL/agents/$AGENT_ID/provenance?limit=5" \
  -H "X-AOS-Key: $API_KEY" | python3 -m json.tool
echo ""

# 10. Test Auth Rejection
echo "10. Test Auth Rejection (should fail)"
echo "--------------------------------------"
REJECT_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/agents" \
  -H "X-AOS-Key: wrong-key")
REJECT_CODE=$(echo "$REJECT_RESPONSE" | tail -n 1)
echo "HTTP Status: $REJECT_CODE (expected: 401)"
echo ""

# Summary
echo "======================================"
echo "Test Suite Complete!"
echo "======================================"
if [ "$HTTP_CODE" == "202" ] && [ "$FINAL_STATUS" == "succeeded" ] && [ "$REJECT_CODE" == "401" ]; then
    echo "Result: ALL TESTS PASSED"
else
    echo "Result: SOME TESTS FAILED"
    echo "  - Goal POST: $HTTP_CODE (expected 202)"
    echo "  - Run Status: $FINAL_STATUS (expected succeeded)"
    echo "  - Auth Reject: $REJECT_CODE (expected 401)"
fi
echo "======================================"
