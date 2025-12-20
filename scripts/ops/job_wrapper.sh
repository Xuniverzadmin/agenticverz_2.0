#!/bin/bash
# =============================================================================
# Job Wrapper - Auto-run Preflight/Postflight
# =============================================================================
#
# Automatically runs preflight before and postflight after any job.
#
# Usage:
#   ./scripts/ops/job_wrapper.sh "your command here"
#   ./scripts/ops/job_wrapper.sh "pytest backend/tests/ -v"
#   ./scripts/ops/job_wrapper.sh "python3 -m pytest tests/test_foo.py"
#
# Options:
#   --skip-preflight    Skip preflight check
#   --skip-postflight   Skip postflight check
#   --strict            Fail on any preflight/postflight issues
#
# =============================================================================

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

# Defaults
SKIP_PREFLIGHT=false
SKIP_POSTFLIGHT=false
STRICT_MODE=false
JOB_CMD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-preflight)
            SKIP_PREFLIGHT=true
            shift
            ;;
        --skip-postflight)
            SKIP_POSTFLIGHT=true
            shift
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        *)
            JOB_CMD="$1"
            shift
            ;;
    esac
done

if [[ -z "$JOB_CMD" ]]; then
    echo -e "${RED}Error: No command provided${NC}"
    echo ""
    echo "Usage: $0 [options] \"command to run\""
    echo ""
    echo "Options:"
    echo "  --skip-preflight    Skip preflight check"
    echo "  --skip-postflight   Skip postflight check"
    echo "  --strict            Fail on any preflight/postflight issues"
    exit 1
fi

# =============================================================================
# PREFLIGHT
# =============================================================================

if [[ "$SKIP_PREFLIGHT" == "false" ]]; then
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  PREFLIGHT CHECK${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""

    cd "$PROJECT_ROOT"

    if python3 scripts/ops/preflight.py --routes; then
        echo -e "${GREEN}Preflight PASSED${NC}"
    else
        echo -e "${RED}Preflight FAILED${NC}"
        if [[ "$STRICT_MODE" == "true" ]]; then
            echo -e "${RED}Strict mode enabled - aborting job${NC}"
            exit 1
        else
            echo -e "${YELLOW}Continuing despite preflight failure...${NC}"
        fi
    fi
fi

# =============================================================================
# RUN JOB
# =============================================================================

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  RUNNING JOB: ${JOB_CMD}${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

cd "$PROJECT_ROOT"
JOB_START=$(date +%s)

# Run the job and capture exit code
set +e
eval "$JOB_CMD"
JOB_EXIT_CODE=$?
set -e

JOB_END=$(date +%s)
JOB_DURATION=$((JOB_END - JOB_START))

if [[ $JOB_EXIT_CODE -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}Job completed successfully in ${JOB_DURATION}s${NC}"
else
    echo ""
    echo -e "${RED}Job failed with exit code $JOB_EXIT_CODE (duration: ${JOB_DURATION}s)${NC}"
fi

# =============================================================================
# POSTFLIGHT
# =============================================================================

if [[ "$SKIP_POSTFLIGHT" == "false" ]]; then
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  POSTFLIGHT CHECK${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""

    cd "$PROJECT_ROOT"

    # Run quick postflight (syntax, imports, security)
    if python3 scripts/ops/postflight.py --quick backend/ 2>&1 | tail -20; then
        echo ""
        echo -e "${GREEN}Postflight completed${NC}"
    else
        echo -e "${YELLOW}Postflight reported issues${NC}"
    fi
fi

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  JOB SUMMARY${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "  Command:  $JOB_CMD"
echo "  Duration: ${JOB_DURATION}s"
if [[ $JOB_EXIT_CODE -eq 0 ]]; then
    echo -e "  Status:   ${GREEN}SUCCESS${NC}"
else
    echo -e "  Status:   ${RED}FAILED (exit code $JOB_EXIT_CODE)${NC}"
fi
echo ""

exit $JOB_EXIT_CODE
