#!/bin/bash
# JSON Transform Demo - Runner Script
#
# Usage:
#   ./run.sh                     # Run demo
#   ./run.sh --check-determinism # Also verify determinism
#   ./run.sh --help              # Show help

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "JSON Transform Demo"
    echo ""
    echo "Usage: ./run.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --check-determinism    Verify transform produces identical output"
    echo "  --help                 Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  AOS_API_KEY       API key for AOS server"
    echo "  AOS_BASE_URL      AOS server URL (default: http://127.0.0.1:8000)"
    exit 0
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Check SDK
if ! python3 -c "import aos_sdk" 2>/dev/null; then
    echo -e "${YELLOW}Installing aos-sdk...${NC}"
    pip3 install aos-sdk
fi

# Set determinism check flag
if [[ "$1" == "--check-determinism" ]]; then
    export CHECK_DETERMINISM=true
fi

# Run
echo -e "${GREEN}Running JSON Transform Demo...${NC}"
echo ""

cd "$SCRIPT_DIR"
python3 demo.py

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}Demo completed successfully!${NC}"
else
    echo -e "${RED}Demo failed with exit code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
