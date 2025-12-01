#!/usr/bin/env bash
# NOVA API SSH Tunnel
# Usage: ./nova-tunnel.sh [VPS_IP]
# Creates secure tunnel to NOVA API on port 8000

set -euo pipefail

VPS_IP="${1:-YOUR_VPS_IP}"
LOCAL_PORT=8000
REMOTE_PORT=8000

if [ "$VPS_IP" = "YOUR_VPS_IP" ]; then
    echo "Usage: $0 <VPS_IP>"
    echo "Example: $0 203.0.113.50"
    exit 1
fi

echo "=== NOVA API Tunnel ==="
echo "Connecting to $VPS_IP..."
echo ""
echo "Once connected, access NOVA at:"
echo "  http://localhost:$LOCAL_PORT/health"
echo "  http://localhost:$LOCAL_PORT/agents"
echo ""
echo "Press Ctrl+C to disconnect"
echo "========================="
echo ""

ssh -N -L ${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT} root@${VPS_IP}
