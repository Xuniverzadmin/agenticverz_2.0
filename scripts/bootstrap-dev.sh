#!/usr/bin/env bash
#
# AOS Development Environment Bootstrap Script
#
# This script ensures a consistent development environment for all engineers.
# Run this after cloning the repository.
#
# Usage:
#   ./scripts/bootstrap-dev.sh
#
# Requirements:
#   - Python 3.11+
#   - Docker & Docker Compose
#   - Redis (via Docker or local)
#   - PostgreSQL (via Docker or local)
#

set -e

echo "=============================================="
echo "  AOS Development Environment Bootstrap"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "   ${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "   ${RED}✗${NC} Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

# Check Docker
echo ""
echo "2. Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Docker found"
else
    echo -e "   ${RED}✗${NC} Docker not found. Please install Docker."
    exit 1
fi

# Check Docker Compose
echo ""
echo "3. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Docker Compose found"
else
    echo -e "   ${RED}✗${NC} Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Create virtual environment if not exists
echo ""
echo "4. Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "   ${GREEN}✓${NC} Virtual environment created"
else
    echo -e "   ${YELLOW}ℹ${NC} Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo ""
echo "5. Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q
pip install pytest pytest-cov pytest-asyncio httpx ruff mypy jsonschema -q
echo -e "   ${GREEN}✓${NC} Dependencies installed"

# Validate JSON schemas
echo ""
echo "6. Validating JSON schemas..."
python3 -c "
import json
import jsonschema
from pathlib import Path

schema_dir = Path('backend/app/schemas')
errors = []

for schema_file in schema_dir.glob('*.schema.json'):
    try:
        with open(schema_file) as f:
            schema = json.load(f)
        jsonschema.Draft7Validator.check_schema(schema)
    except Exception as e:
        errors.append(f'{schema_file.name}: {e}')

if errors:
    for e in errors:
        print(f'   ✗ {e}')
    exit(1)
print('   ✓ All schemas valid')
"

# Check required specification files
echo ""
echo "7. Checking required specifications..."
SPECS=(
    "backend/app/specs/error_taxonomy.md"
    "backend/app/specs/determinism_and_replay.md"
    "backend/app/schemas/structured_outcome.schema.json"
    "backend/app/schemas/skill_metadata.schema.json"
    "backend/app/schemas/resource_contract.schema.json"
    "backend/app/schemas/agent_profile.schema.json"
)

missing=0
for spec in "${SPECS[@]}"; do
    if [ -f "$spec" ]; then
        echo -e "   ${GREEN}✓${NC} $spec"
    else
        echo -e "   ${RED}✗${NC} $spec MISSING"
        missing=$((missing + 1))
    fi
done

if [ $missing -gt 0 ]; then
    echo -e "\n   ${RED}ERROR: $missing specification file(s) missing${NC}"
    exit 1
fi

# Run unit tests
echo ""
echo "8. Running unit tests..."
cd backend
if python -m pytest tests/schemas/ -v --tb=short -q 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} Unit tests passed"
else
    echo -e "   ${RED}✗${NC} Unit tests failed"
    exit 1
fi
cd ..

# Check if services are running (optional)
echo ""
echo "9. Checking services (optional)..."
if docker ps | grep -q nova_db; then
    echo -e "   ${GREEN}✓${NC} PostgreSQL container running"
else
    echo -e "   ${YELLOW}ℹ${NC} PostgreSQL not running. Start with: docker compose up -d db"
fi

if redis-cli ping &> /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Redis available"
else
    echo -e "   ${YELLOW}ℹ${NC} Redis not running. Start with: docker compose up -d redis"
fi

# Summary
echo ""
echo "=============================================="
echo "  Bootstrap Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Activate virtualenv:  source .venv/bin/activate"
echo "  2. Start services:       docker compose up -d"
echo "  3. Run full tests:       cd backend && pytest tests/ -v"
echo "  4. Start development:    docker compose up -d backend worker"
echo ""
echo "Documentation:"
echo "  - Memory PINs:           docs/memory-pins/INDEX.md"
echo "  - Error Taxonomy:        backend/app/specs/error_taxonomy.md"
echo "  - Determinism Spec:      backend/app/specs/determinism_and_replay.md"
echo "  - Test README:           backend/tests/README.md"
echo ""
echo -e "${GREEN}Ready for development!${NC}"
