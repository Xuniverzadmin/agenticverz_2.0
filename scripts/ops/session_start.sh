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
echo "[1/11] Checking working environment..."
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
echo "[2/11] Checking for stale files..."
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
echo "[3/11] Current project phase..."
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
echo "[4/11] Checking for blockers..."
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
echo "[5/11] Dev sync status..."
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
echo "[6/11] Service status..."
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
echo "[7/11] PIN hygiene..."
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
# 8. Contract Scan (agen_internal_system_scan)
# -----------------------------------------------------------------------------
echo ""
echo "[8/11] Contract scan..."
SCAN_OUTPUT=$(python3 "$ROOT/scripts/preflight/agen_internal_system_scan.py" 2>&1)
SCAN_EXIT=$?
echo "$SCAN_OUTPUT"
if [ "$SCAN_EXIT" -ne 0 ]; then
    ISSUES=$((ISSUES+1))
fi

# -----------------------------------------------------------------------------
# 9. System Bloat Audit
# -----------------------------------------------------------------------------
echo ""
echo "[9/12] System bloat audit..."
BLOAT_OUTPUT=$("$ROOT/scripts/ops/system_bloat_audit.sh" 2>&1)
BLOAT_EXIT=$?
echo "$BLOAT_OUTPUT"
if [ "$BLOAT_EXIT" -gt 0 ]; then
    echo "  WARN: $BLOAT_EXIT bloat warning(s) detected"
    WARNINGS=$((WARNINGS+BLOAT_EXIT))
fi

# -----------------------------------------------------------------------------
# 10. BLCA Layer Validation
# -----------------------------------------------------------------------------
echo ""
echo "[10/12] BLCA layer validation..."
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
echo "[11/12] Lifecycle-qualifier coherence..."
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
echo "[12/12] Health-lifecycle coherence (bootstrap gate)..."
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
echo "  PROJECT CONTEXT"
echo "=============================================="
echo ""

# Recent PINs (last 5)
echo "  Recent PINs:"
if [ -d "$ROOT/docs/memory-pins" ]; then
    ls -t "$ROOT/docs/memory-pins"/PIN-*.md 2>/dev/null | head -5 | while read -r pin; do
        PIN_NUM=$(basename "$pin" .md | grep -oP 'PIN-\K[0-9]+')
        PIN_TITLE=$(head -1 "$pin" | sed 's/^# //' | sed 's/^PIN-[0-9]*[: -]*//' | cut -c1-50)
        PIN_STATUS=$(grep -oP 'Status:\*\* \K[^\n]*' "$pin" 2>/dev/null | head -1 || echo "?")
        printf "    | PIN-%-3s | %-50s | %-10s |\n" "$PIN_NUM" "$PIN_TITLE" "$PIN_STATUS"
    done
fi

echo ""

# HOC Domain Status
echo "  HOC Domain Status:"
if [ -f "$ROOT/docs/architecture/hoc/HOC_LAYER_INVENTORY.csv" ]; then
    awk -F',' 'NR>1 {domains[$2]++} END {for (d in domains) printf "    %-20s %d files\n", d":", domains[d]}' \
        "$ROOT/docs/architecture/hoc/HOC_LAYER_INVENTORY.csv" 2>/dev/null | sort -t: -k2 -rn | head -6
else
    echo "    (inventory not found)"
fi

echo ""
echo "  Start by reading:"
echo "    1. agentiverz_mn/repo_snapshot.md"
echo "    2. agentiverz_mn/milestone_plan.md"
echo "    3. Check the relevant checklist for your task"
echo ""
echo "  Governance: .claude/rules/ (8 files, path-scoped)"
echo "  Hooks: .claude/settings.json (post-edit, post-bash)"
echo "  Full docs: docs/governance/ (73 files)"
echo "  Context: .claude/project-context.md"
echo ""
