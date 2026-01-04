#!/bin/bash
# =============================================================================
# AOS Session Start - Hygiene Check
# =============================================================================
# Run this at the start of every Claude session to ensure proper context.
#
# Usage: ./scripts/ops/session_start.sh
# =============================================================================

set -e

cd "$(dirname "$0")/../.." || exit 1
ROOT=$(pwd)

echo "=============================================="
echo "  AOS Session Hygiene Check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

ISSUES=0
WARNINGS=0

# -----------------------------------------------------------------------------
# 1. Verify working environment exists
# -----------------------------------------------------------------------------
echo "[1/10] Checking working environment..."
if [ ! -d "agentiverz_mn" ]; then
    echo "  ERROR: Working environment missing at agentiverz_mn/"
    echo "  Action: Create it or restore from backup"
    ISSUES=$((ISSUES+1))
else
    FILE_COUNT=$(ls agentiverz_mn/*.md 2>/dev/null | wc -l)
    echo "  OK: agentiverz_mn/ exists ($FILE_COUNT files)"
fi

# -----------------------------------------------------------------------------
# 2. Check for stale checklists (>7 days untouched)
# -----------------------------------------------------------------------------
echo ""
echo "[2/10] Checking for stale files..."
STALE_FILES=$(find agentiverz_mn -name "*.md" -mtime +7 2>/dev/null || true)
if [ -n "$STALE_FILES" ]; then
    echo "  WARN: Files not updated in >7 days:"
    echo "$STALE_FILES" | while read -r f; do
        DAYS=$(( ($(date +%s) - $(stat -c %Y "$f")) / 86400 ))
        echo "    - $f ($DAYS days old)"
    done
    WARNINGS=$((WARNINGS+1))
else
    echo "  OK: All files recently updated"
fi

# -----------------------------------------------------------------------------
# 3. Show current milestone status
# -----------------------------------------------------------------------------
echo ""
echo "[3/10] Current project phase..."
if [ -f "docs/memory-pins/INDEX.md" ]; then
    PHASE=$(grep -A2 "### Current Project Phase" docs/memory-pins/INDEX.md | tail -2 | head -1 | sed 's/^\*\*/  /' | sed 's/\*\*$//')
    echo "  $PHASE"

    # Check INDEX.md freshness
    LAST_UPDATE=$(stat -c %Y docs/memory-pins/INDEX.md)
    NOW=$(date +%s)
    DAYS_OLD=$(( (NOW - LAST_UPDATE) / 86400 ))
    if [ "$DAYS_OLD" -gt 3 ]; then
        echo "  WARN: INDEX.md not updated in $DAYS_OLD days"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo "  ERROR: INDEX.md not found"
    ISSUES=$((ISSUES+1))
fi

# -----------------------------------------------------------------------------
# 4. Show blocking items
# -----------------------------------------------------------------------------
echo ""
echo "[4/10] Checking for blockers..."
BLOCKERS=$(grep -l -i "BLOCKING\|BLOCKER" agentiverz_mn/*.md 2>/dev/null || true)
if [ -n "$BLOCKERS" ]; then
    echo "  BLOCKERS FOUND:"
    for f in $BLOCKERS; do
        NAME=$(basename "$f" .md)
        echo "    - $NAME"
    done
else
    echo "  OK: No blocking items flagged"
fi

# -----------------------------------------------------------------------------
# 5. Dev Sync Check (code vs container consistency)
# -----------------------------------------------------------------------------
echo ""
echo "[5/10] Dev sync status..."
if [ -x "$ROOT/scripts/ops/dev_sync.sh" ]; then
    if "$ROOT/scripts/ops/dev_sync.sh" --quick 2>&1 | grep -q "ERROR"; then
        echo "  WARN: Backend may need rebuild - run ./scripts/ops/dev_sync.sh"
        WARNINGS=$((WARNINGS+1))
    else
        echo "  OK: Backend responding"
    fi
else
    echo "  SKIP: dev_sync.sh not found"
fi

# -----------------------------------------------------------------------------
# 6. Check services status
# -----------------------------------------------------------------------------
echo ""
echo "[6/10] Service status..."
if command -v docker &> /dev/null; then
    RUNNING=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -c "nova" || echo "0")
    UNHEALTHY=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null | grep "nova" || true)

    echo "  Running containers: $RUNNING"
    if [ -n "$UNHEALTHY" ]; then
        echo "  WARN: Unhealthy containers: $UNHEALTHY"
        WARNINGS=$((WARNINGS+1))
    fi

    # Quick health check
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "  Backend: healthy"
    else
        echo "  WARN: Backend not responding"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo "  SKIP: Docker not available"
fi

# -----------------------------------------------------------------------------
# 7. PIN count check
# -----------------------------------------------------------------------------
echo ""
echo "[7/10] PIN hygiene..."
PIN_COUNT=$(ls docs/memory-pins/PIN-*.md 2>/dev/null | wc -l)
echo "  Total PINs: $PIN_COUNT"
if [ "$PIN_COUNT" -gt 40 ]; then
    echo "  WARN: Consider archiving old PINs (>40)"
    WARNINGS=$((WARNINGS+1))
fi

# Check for completed checklists
echo ""
echo "  Checklist status:"
for f in agentiverz_mn/*checklist*.md; do
    [ -f "$f" ] || continue
    NAME=$(basename "$f" .md)
    # Use grep with explicit patterns and handle empty results
    TOTAL=$(grep -E "^- \[ \]|^- \[x\]" "$f" 2>/dev/null | wc -l)
    DONE=$(grep -E "^- \[x\]" "$f" 2>/dev/null | wc -l)
    # Ensure numeric values
    TOTAL=${TOTAL:-0}
    DONE=${DONE:-0}
    if [ "$TOTAL" -gt 0 ]; then
        PCT=$((DONE * 100 / TOTAL))
        echo "    - $NAME: $DONE/$TOTAL ($PCT%)"
        if [ "$PCT" -eq 100 ]; then
            echo "      ^ Consider archiving (100% complete)"
        fi
    fi
done

# -----------------------------------------------------------------------------
# 8. BLCA Layer Validation
# -----------------------------------------------------------------------------
echo ""
echo "[8/10] BLCA layer validation..."
if [ -x "$ROOT/scripts/ops/layer_validator.py" ]; then
    BLCA_OUTPUT=$(python3 "$ROOT/scripts/ops/layer_validator.py" --backend --ci 2>&1)
    if echo "$BLCA_OUTPUT" | grep -q "VIOLATIONS.*[1-9]"; then
        echo "  ERROR: BLCA violations detected"
        echo "  Run: python3 scripts/ops/layer_validator.py --backend --ci"
        ISSUES=$((ISSUES+1))
        # Record governance signal for platform health
        if [ -n "$DATABASE_URL" ]; then
            python3 "$ROOT/scripts/ops/record_governance_signal.py" \
                --type BLCA_STATUS \
                --scope SYSTEM \
                --decision BLOCKED \
                --recorded-by BLCA \
                --reason "BLCA violations detected" \
                --quiet 2>/dev/null || true
        fi
    else
        BLCA_FILES=$(echo "$BLCA_OUTPUT" | grep -oP "Scanned \K[0-9]+" || echo "0")
        echo "  OK: BLCA CLEAN ($BLCA_FILES files)"
        # Record governance signal for platform health
        if [ -n "$DATABASE_URL" ]; then
            python3 "$ROOT/scripts/ops/record_governance_signal.py" \
                --type BLCA_STATUS \
                --scope SYSTEM \
                --decision CLEAN \
                --recorded-by BLCA \
                --reason "0 violations in $BLCA_FILES files" \
                --quiet 2>/dev/null || true
        fi
    fi
else
    echo "  SKIP: layer_validator.py not found"
fi

# -----------------------------------------------------------------------------
# 9. Lifecycle-Qualifier Coherence
# -----------------------------------------------------------------------------
echo ""
echo "[9/10] Lifecycle-qualifier coherence..."
if [ -x "$ROOT/scripts/ci/lifecycle_qualifier_guard.py" ]; then
    if python3 "$ROOT/scripts/ci/lifecycle_qualifier_guard.py" > /dev/null 2>&1; then
        echo "  OK: Lifecycle coherent with qualifiers"
        # Record governance signal for platform health
        if [ -n "$DATABASE_URL" ]; then
            python3 "$ROOT/scripts/ops/record_governance_signal.py" \
                --type LIFECYCLE_QUALIFIER_COHERENCE \
                --scope SYSTEM \
                --decision COHERENT \
                --recorded-by LIFECYCLE_GUARD \
                --reason "Lifecycle coherent with qualifiers" \
                --quiet 2>/dev/null || true
        fi
    else
        echo "  ERROR: Lifecycle/qualifier divergence detected"
        echo "  Run: python3 scripts/ci/lifecycle_qualifier_guard.py"
        ISSUES=$((ISSUES+1))
        # Record governance signal for platform health
        if [ -n "$DATABASE_URL" ]; then
            python3 "$ROOT/scripts/ops/record_governance_signal.py" \
                --type LIFECYCLE_QUALIFIER_COHERENCE \
                --scope SYSTEM \
                --decision INCOHERENT \
                --recorded-by LIFECYCLE_GUARD \
                --reason "Lifecycle/qualifier divergence detected" \
                --quiet 2>/dev/null || true
        fi
    fi
else
    echo "  SKIP: lifecycle_qualifier_guard.py not found"
fi

# -----------------------------------------------------------------------------
# 10. Health-Lifecycle Coherence (BOOTSTRAP GATE)
# -----------------------------------------------------------------------------
echo ""
echo "[10/10] Health-lifecycle coherence (bootstrap gate)..."
if [ -x "$ROOT/scripts/ci/health_lifecycle_coherence_guard.py" ]; then
    if [ -n "$DATABASE_URL" ]; then
        # Run the guard with --bootstrap flag (checks system health too)
        if python3 "$ROOT/scripts/ci/health_lifecycle_coherence_guard.py" --bootstrap > /dev/null 2>&1; then
            echo "  OK: Health coherent with lifecycle"
        else
            echo "  ERROR: Health-lifecycle coherence violation detected"
            echo "  Run: python3 scripts/ci/health_lifecycle_coherence_guard.py --bootstrap"
            echo ""
            echo "  BOOTSTRAP BLOCKED: A BLOCKED health state cannot coexist with COMPLETE lifecycle."
            echo "  Resolve the health issue or downgrade the lifecycle status."
            ISSUES=$((ISSUES+1))
        fi
    else
        echo "  SKIP: DATABASE_URL not set (health signals unavailable)"
    fi
else
    echo "  SKIP: health_lifecycle_coherence_guard.py not found"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo "  Errors:   $ISSUES"
echo "  Warnings: $WARNINGS"
echo ""

if [ "$ISSUES" -gt 0 ]; then
    echo "  STATUS: BLOCKED - Fix errors before proceeding"
    echo ""
    exit 1
fi

if [ "$WARNINGS" -gt 0 ]; then
    echo "  STATUS: OK (with warnings)"
else
    echo "  STATUS: OK"
fi

echo ""
echo "=============================================="
echo "  Start by reading:"
echo "=============================================="
echo "  1. agentiverz_mn/repo_snapshot.md"
echo "  2. agentiverz_mn/milestone_plan.md"
echo "  3. Check the relevant checklist for your task"
echo ""
echo "=============================================="
echo "  CLAUDE BEHAVIOR ENFORCEMENT (MANDATORY)"
echo "=============================================="
echo ""
echo "  Claude must follow the Pre-Code Discipline:"
echo ""
echo "  TASK 0: Accept contract"
echo "  TASK 1: System state inventory (PLAN)"
echo "  TASK 2: Conflict & risk scan (VERIFY)"
echo "  TASK 3: Migration intent (if applicable)"
echo "  TASK 4: Execution plan (PLAN)"
echo "  TASK 5: Act - write code (only after 0-4)"
echo "  TASK 6: Self-audit (VERIFY)"
echo ""
echo "  Required files:"
echo "    - CLAUDE.md"
echo "    - CLAUDE_BOOT_CONTRACT.md"
echo "    - CLAUDE_PRE_CODE_DISCIPLINE.md"
echo ""
echo "  Run './scripts/ops/claude_session_boot.sh' for full boot prompt."
echo ""
echo "  Responses validated by: scripts/ops/claude_response_validator.py"
echo ""
