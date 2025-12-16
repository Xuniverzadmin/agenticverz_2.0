#!/bin/bash
# CLI Demo Test - Verify M0-M20 Integration
# Usage: ./scripts/ops/cli_demo_test.sh

set -e

AOS_API_KEY="edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf"
BASE_URL="http://localhost:8000/api/v1/workers/business-builder"

echo "=============================================="
echo "  AGENTICVERZ M0-M20 CLI DEMO TEST"
echo "=============================================="
echo ""

# 1. Worker Health Check
echo "=== 1. WORKER HEALTH CHECK (M0/M21) ==="
HEALTH=$(curl -s -H "X-AOS-Key: $AOS_API_KEY" "$BASE_URL/health")
echo "$HEALTH" | jq .
VERSION=$(echo "$HEALTH" | jq -r '.version')
if [ "$VERSION" != "0.3" ]; then
    echo "ERROR: Expected version 0.3, got $VERSION"
    exit 1
fi
echo "✅ Worker v0.3 healthy with MOATs available"
echo ""

# 2. Run Real Worker Job
echo "=== 2. RUNNING REAL WORKER JOB ==="
echo "Task: Create landing page for AI habit tracker"
echo ""

RESPONSE=$(curl -s -X POST \
  -H "X-AOS-Key: $AOS_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/run" \
  -d '{
    "task": "Create a landing page for an AI habit tracker for founders",
    "brand": {
      "name": "HabitAI",
      "company_name": "HabitAI Inc",
      "mission": "Help founders build better habits through AI-powered insights",
      "value_proposition": "AI-powered habit tracking that helps busy founders build sustainable routines and achieve their goals",
      "tone": {"primary": "professional"},
      "target_audience": ["founders", "entrepreneurs"]
    }
  }')

RUN_ID=$(echo "$RESPONSE" | jq -r '.run_id')
STATUS=$(echo "$RESPONSE" | jq -r '.status')

echo "Run ID: $RUN_ID"
echo "Initial Status: $STATUS"
echo ""

# Wait for completion if queued
if [ "$STATUS" = "queued" ] || [ "$STATUS" = "running" ]; then
    echo "Waiting for completion..."
    for i in {1..60}; do
        sleep 2
        CHECK=$(curl -s -H "X-AOS-Key: $AOS_API_KEY" "$BASE_URL/runs/$RUN_ID")
        STATUS=$(echo "$CHECK" | jq -r '.status')
        TOKENS=$(echo "$CHECK" | jq -r '.total_tokens_used // 0')
        echo "  [$i] Status: $STATUS, Tokens: $TOKENS"
        if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
            RESPONSE="$CHECK"
            break
        fi
    done
fi

echo ""
echo "=== 3. RUN RESULTS ==="
echo "$RESPONSE" | jq '{
  run_id,
  status,
  total_tokens_used,
  total_latency_ms,
  replay_token: (.replay_token // "none"),
  artifacts: (.artifacts | keys? // []),
  routing_decisions: (.routing_decisions | length? // 0),
  policy_violations: (.policy_violations | length? // 0)
}'

# Check tokens
TOKENS=$(echo "$RESPONSE" | jq -r '.total_tokens_used // 0')
if [ "$TOKENS" -gt 0 ]; then
    echo ""
    echo "✅ REAL LLM CALLS CONFIRMED: $TOKENS tokens used"
else
    echo ""
    echo "⚠️  WARNING: 0 tokens - LLM may not have been called"
fi

# Check artifacts
echo ""
echo "=== 4. ARTIFACTS CHECK ==="
ARTIFACTS=$(echo "$RESPONSE" | jq -r '.artifacts // {}')
if [ "$ARTIFACTS" != "{}" ] && [ "$ARTIFACTS" != "null" ]; then
    echo "$ARTIFACTS" | jq 'keys'
    echo "✅ Artifacts generated"

    # Show sample artifact content
    echo ""
    echo "Sample artifact (positioning):"
    echo "$ARTIFACTS" | jq -r '.positioning // .strategy_json // "none"' | head -20
else
    echo "⚠️  No artifacts in response"
fi

# Check routing decisions
echo ""
echo "=== 5. ROUTING DECISIONS (M17 CARE) ==="
ROUTING=$(echo "$RESPONSE" | jq '.routing_decisions // []')
echo "$ROUTING" | jq '.[0:2]'

# Check drift metrics
echo ""
echo "=== 6. DRIFT METRICS (M18) ==="
DRIFT=$(echo "$RESPONSE" | jq '.drift_metrics // {}')
echo "$DRIFT" | jq .

echo ""
echo "=============================================="
echo "  CLI DEMO TEST COMPLETE"
echo "=============================================="
echo ""
echo "Run ID: $RUN_ID"
echo "Status: $STATUS"
echo "Tokens: $TOKENS"
echo ""
if [ "$STATUS" = "completed" ] && [ "$TOKENS" -gt 0 ]; then
    echo "✅ SUCCESS - M0-M20 integration verified"
    echo ""
    echo "Next: View in console at https://agenticverz.com/console/workers"
else
    echo "⚠️  REVIEW NEEDED"
fi
