#!/usr/bin/env bash
set -euo pipefail
API_URL=${API_URL:-http://127.0.0.1:8000}
API_KEY=${API_KEY:-edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf}
export API_KEY
echo "Python SDK smoke test..."
python3 - <<PY
import os
from nova_sdk import NovaClient
api_key = os.environ.get("API_KEY", "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf")
c = NovaClient(api_key=api_key, base_url="$API_URL")
try:
    agent = c.create_agent("sdk-flow-agent")
    print("agent", agent)
    run = c.post_goal(agent, "ping", force_skill="http_call")
    print("run", run)
except Exception as e:
    print("py error", e)
PY

echo "Node SDK smoke test..."
node sdk/js/tests/test_js_sdk.js
