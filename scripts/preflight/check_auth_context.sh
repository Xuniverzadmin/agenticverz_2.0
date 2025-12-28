#!/usr/bin/env bash
# =============================================================================
# Auth Context Preflight Check
# =============================================================================
# Run before any authenticated API call.
# Verifies environment variables are loaded and valid.
#
# Usage: ./scripts/preflight/check_auth_context.sh
#
# Reference: docs/execution/API_CALL_TEMPLATE.md
# =============================================================================

set -e

echo "=== Auth Context Preflight ==="

# Check AOS_API_KEY
if [ -z "$AOS_API_KEY" ]; then
    echo "❌ AOS_API_KEY not set"
    echo ""
    echo "Fix: source /root/agenticverz2.0/.env"
    exit 1
fi

KEY_LEN=${#AOS_API_KEY}
if [ "$KEY_LEN" -lt 32 ]; then
    echo "❌ AOS_API_KEY too short ($KEY_LEN chars, need 32+)"
    exit 1
fi

echo "✅ AOS_API_KEY present ($KEY_LEN chars)"

# Check DATABASE_URL (optional but useful)
if [ -n "$DATABASE_URL" ]; then
    echo "✅ DATABASE_URL present"
else
    echo "⚠️  DATABASE_URL not set (may be needed for DB operations)"
fi

echo ""
echo "=== Preflight PASSED ==="
echo ""
echo "You may now make authenticated API calls using:"
echo "  curl -H \"X-AOS-Key: \$AOS_API_KEY\" <url>"
