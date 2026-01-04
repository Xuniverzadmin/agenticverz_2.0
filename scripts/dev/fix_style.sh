#!/usr/bin/env bash
# =============================================================================
# fix_style.sh - Explicit Code Style Mutation
# =============================================================================
#
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Human-initiated code style mutation
# Reference: PIN-290 (Non-Mutating Tooling Invariant)
#
# =============================================================================
# NON-MUTATING TOOLING INVARIANT (Constitutional)
# =============================================================================
#
# This script is the ONLY authorized way to auto-fix code style.
#
# Why this exists:
#   - Pre-commit hooks are CHECK-ONLY (no auto-fix)
#   - CI is CHECK-ONLY (no auto-fix)
#   - All mutation must be EXPLICIT and HUMAN-INITIATED
#   - This prevents stash conflicts during constitutional commits
#   - This preserves audit trails and intentional diffs
#
# Workflow:
#   1. Write code
#   2. Run: ./scripts/dev/fix_style.sh (or: make lint-fix)
#   3. Review changes
#   4. Stage: git add <files>
#   5. Commit: git commit (check-only hooks verify)
#
# Reference: PIN-290, GOVERNANCE_CHECKLIST.md
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$SCRIPT_DIR"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  EXPLICIT CODE STYLE MUTATION${NC}"
echo -e "${CYAN}  (Non-Mutating Tooling Invariant - PIN-290)${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check for required tools
if ! command -v ruff &> /dev/null; then
    echo -e "${YELLOW}Warning: ruff not found. Installing...${NC}"
    pip install ruff
fi

echo -e "${CYAN}[1/4] Fixing trailing whitespace...${NC}"
find backend sdk scripts -name "*.py" -o -name "*.ts" -o -name "*.tsx" \
    -o -name "*.js" -o -name "*.jsx" -o -name "*.sh" 2>/dev/null | \
    xargs -I{} sed -i 's/[[:blank:]]*$//' {} 2>/dev/null || true

echo -e "${CYAN}[2/4] Fixing EOF newlines...${NC}"
find backend sdk scripts -name "*.py" -o -name "*.ts" -o -name "*.tsx" \
    -o -name "*.js" -o -name "*.jsx" -o -name "*.sh" 2>/dev/null | \
    while read f; do
        if [ -f "$f" ] && [ -s "$f" ]; then
            # Add newline at EOF if missing
            sed -i -e '$a\' "$f" 2>/dev/null || true
        fi
    done

echo -e "${CYAN}[3/4] Fixing lint errors...${NC}"
ruff check . --fix || true

echo -e "${CYAN}[4/4] Formatting code...${NC}"
ruff format .

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  STYLE FIXES COMPLETE${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Review changes: ${YELLOW}git diff${NC}"
echo -e "  2. Stage changes:  ${YELLOW}git add <files>${NC}"
echo -e "  3. Commit:         ${YELLOW}git commit${NC}"
echo ""
echo -e "${CYAN}Pre-commit hooks will VERIFY (not fix) during commit.${NC}"
echo ""
