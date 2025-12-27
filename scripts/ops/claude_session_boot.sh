#!/bin/bash
#
# AgenticVerz — Claude Session Boot Script
#
# Run this at the start of every Claude session to:
# 1. Display the boot contract
# 2. Show current system state
# 3. Remind Claude of required acknowledgement
#
# Usage:
#   ./scripts/ops/claude_session_boot.sh
#
# This script outputs the boot prompt that should be given to Claude.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}      ${BOLD}AGENTICVERZ — CLAUDE SESSION BOOT SEQUENCE${NC}            ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check system state
echo -e "${YELLOW}[1/4] Checking system state...${NC}"

# Check alembic
cd "$PROJECT_ROOT/backend"
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
fi

ALEMBIC_CURRENT=""
ALEMBIC_HEADS=""

if command -v alembic &> /dev/null; then
    ALEMBIC_CURRENT=$(DATABASE_URL="$DATABASE_URL" alembic current 2>/dev/null | head -1 || echo "unknown")
    ALEMBIC_HEADS=$(DATABASE_URL="$DATABASE_URL" alembic heads 2>/dev/null | head -1 || echo "unknown")
fi

echo -e "   Alembic current: ${GREEN}${ALEMBIC_CURRENT:-unknown}${NC}"
echo -e "   Alembic heads:   ${GREEN}${ALEMBIC_HEADS:-unknown}${NC}"

# Check services
echo ""
echo -e "${YELLOW}[2/4] Checking services...${NC}"

BACKEND_STATUS="unknown"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    BACKEND_STATUS="healthy"
    echo -e "   Backend:    ${GREEN}✓ healthy${NC}"
else
    BACKEND_STATUS="unreachable"
    echo -e "   Backend:    ${RED}✗ unreachable${NC}"
fi

# Count memory pins
echo ""
echo -e "${YELLOW}[3/4] Checking memory pins...${NC}"

PIN_COUNT=$(ls -1 "$PROJECT_ROOT/docs/memory-pins/PIN-"*.md 2>/dev/null | wc -l || echo "0")
LATEST_PIN=$(ls -1t "$PROJECT_ROOT/docs/memory-pins/PIN-"*.md 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo "none")

echo -e "   Total PINs:  ${GREEN}${PIN_COUNT}${NC}"
echo -e "   Latest PIN:  ${GREEN}${LATEST_PIN}${NC}"

# Current phase
echo ""
echo -e "${YELLOW}[4/4] Determining current phase...${NC}"

# Check for phase indicators
if grep -q "PHASE A.5 CLOSURE" "$PROJECT_ROOT/CLAUDE.md" 2>/dev/null; then
    CURRENT_PHASE="B (Post A.5 Closure)"
else
    CURRENT_PHASE="Unknown"
fi

echo -e "   Phase:       ${GREEN}${CURRENT_PHASE}${NC}"

# Output boot prompt
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}CLAUDE BOOT PROMPT (Copy/paste to Claude):${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""

cat << 'EOF'
# AgenticVerz Session Start

You are operating as an engineering agent inside the AgenticVerz system.

## MANDATORY: Read these files FIRST
1. `CLAUDE.md` — Project context and behavior rules
2. `CLAUDE_BOOT_CONTRACT.md` — Session boot sequence
3. `CLAUDE_PRE_CODE_DISCIPLINE.md` — Pre-code task checklist

## REQUIRED ACKNOWLEDGEMENT

Before doing anything else, you must reply with:

> "AgenticVerz boot sequence acknowledged.
> I will comply with memory pins, lessons learned, and system contracts.
> Current phase: B"

## CURRENT SYSTEM STATE

EOF

echo "- Alembic current: $ALEMBIC_CURRENT"
echo "- Alembic heads: $ALEMBIC_HEADS"
echo "- Backend status: $BACKEND_STATUS"
echo "- Memory pins: $PIN_COUNT"
echo "- Latest PIN: $LATEST_PIN"
echo "- Current phase: $CURRENT_PHASE"
echo ""

cat << 'EOF'
## PRE-CODE DISCIPLINE REMINDER

If your task involves code changes, you MUST complete TASKS 0-6:
- TASK 0: Accept contract
- TASK 1: System state inventory
- TASK 2: Conflict & risk scan
- TASK 3: Migration intent (if applicable)
- TASK 4: Execution plan
- TASK 5: Act (code)
- TASK 6: Self-audit

**NO CODE until TASKS 0-4 are complete.**

## FORBIDDEN ACTIONS

- Mutate historical executions
- Assume schema state
- Create migrations without checking heads
- Skip SELF-AUDIT section

---

Please acknowledge the boot sequence and state your current phase.
EOF

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Boot prompt ready. Copy the above text to start your Claude session.${NC}"
echo ""
