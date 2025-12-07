#!/bin/bash
# BTC Price to Slack Demo - Runner Script
#
# Usage:
#   ./run.sh              # Run demo
#   ./run.sh --simulate   # Simulate only (no execution)
#   ./run.sh --help       # Show help
#
# Environment:
#   AOS_API_KEY      - Required
#   AOS_BASE_URL     - Optional (default: http://127.0.0.1:8000)
#   SLACK_WEBHOOK_URL - Required for real execution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "BTC Price to Slack Demo"
    echo ""
    echo "Usage: ./run.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --simulate    Simulate only, don't execute"
    echo "  --help        Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  AOS_API_KEY       API key for AOS server (required)"
    echo "  AOS_BASE_URL      AOS server URL (default: http://127.0.0.1:8000)"
    echo "  SLACK_WEBHOOK_URL Slack webhook for notifications"
    exit 0
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Check SDK installed
if ! python3 -c "import aos_sdk" 2>/dev/null; then
    echo -e "${YELLOW}Warning: aos-sdk not installed. Installing...${NC}"
    pip3 install aos-sdk
fi

# Check API key
if [[ -z "$AOS_API_KEY" ]]; then
    echo -e "${YELLOW}Warning: AOS_API_KEY not set. Demo will run in simulation-only mode.${NC}"
fi

# Run demo
echo -e "${GREEN}Running BTC Price to Slack Demo...${NC}"
echo ""

cd "$SCRIPT_DIR"

if [[ "$1" == "--simulate" ]]; then
    # Simulate only - modify the script behavior
    python3 -c "
import os
os.environ['SIMULATE_ONLY'] = 'true'
exec(open('demo.py').read())
"
else
    python3 demo.py
fi

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}Demo completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}Demo failed with exit code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
