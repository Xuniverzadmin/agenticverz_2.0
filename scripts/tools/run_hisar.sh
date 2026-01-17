#!/usr/bin/env bash
#
# HISAR — Human Intent → SDSR → Aurora → Rendering
#
# EXECUTION CONTRACT:
#
# 1. Human Intent is the ONLY source of meaning.
# 2. SDSR is the ONLY source of truth.
# 3. Aurora may ONLY run AFTER SDSR success.
# 4. Rendering may ONLY reflect OBSERVED or TRUSTED capabilities.
# 5. Invariants are IMMUTABLE — SDSR reveals gaps, not hides them.
#
# FORBIDDEN:
# - Inventing endpoints
# - Skipping coherency
# - Running Aurora before SDSR
# - Forcing state transitions
# - Changing invariants to match backend (GOVERNANCE VIOLATION)
# - Softening assertions to "make tests pass"
#
# INVARIANT IMMUTABILITY LAW:
# - When SDSR fails, the BACKEND is wrong, not the invariant
# - Report failures as backend gaps
# - Fix backend to satisfy intent
# - Re-run SDSR after backend fix
#
# FAILURE SEMANTICS:
# - Any failure MUST stop execution.
# - Report the exact phase and invariant that blocked progress.
#
# If this script exits 0 → rendered UI reflects proven reality.
# If this script exits non-zero → NOTHING downstream is allowed to run.
#
# Usage:
#   ./run_hisar.sh <PANEL_ID>
#   ./run_hisar.sh --all
#   ./run_hisar.sh --dry-run <PANEL_ID>
#
# Examples:
#   ./run_hisar.sh OVR-SUM-HL-O1
#   ./run_hisar.sh --all
#   ./run_hisar.sh --dry-run OVR-SUM-HL-O2
#

set -euo pipefail

# -------------------------------
# Config
# -------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TOOLS_DIR="$ROOT_DIR/backend/aurora_l2/tools"

PANEL_ID=""
MODE="single"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      MODE="all"
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      echo "HISAR — Human Intent → SDSR → Aurora → Rendering"
      echo ""
      echo "Usage:"
      echo "  ./run_hisar.sh <PANEL_ID>        Run for single panel"
      echo "  ./run_hisar.sh --all             Run for all panels"
      echo "  ./run_hisar.sh --dry-run <ID>    Show what would run"
      echo ""
      echo "Phases:"
      echo "  [G] 0    Snapshot Gate (MANDATORY)"
      echo "  [G] 0.1  Universe Validation (BLOCKING) — ALL intents coherent"
      echo "  [H] 1    Human Intent Validation"
      echo "  [H] 2    Intent Specification"
      echo "  [A] 3    Capability Declaration"
      echo "  [S] 3.5  Coherency Gate (BLOCKING)"
      echo "  [S] 4    SDSR Verification"
      echo "  [S] 5    Observation Application"
      echo "  [S] 5.5  Trust Evaluation"
      echo "  [A] 6    Aurora Compilation"
      echo "  [A] 6.5  UI Plan Bind"
      echo "  [A] 7    Projection Diff Guard (BLOCKING)"
      echo "  [R] 8    Rendering"
      echo "  [M] 9    Memory PIN Generation (Automation - PIN-432)"
      exit 0
      ;;
    *)
      PANEL_ID="$1"
      shift
      ;;
  esac
done

# Validate arguments
if [[ "$MODE" == "single" && -z "$PANEL_ID" ]]; then
  echo "ERROR: Panel ID required (or use --all)"
  echo "Usage: ./run_hisar.sh <PANEL_ID>"
  exit 1
fi

cd "$ROOT_DIR"

echo "══════════════════════════════════════════════════════════════════════"
echo "▶ HISAR RUNNER START"
echo "══════════════════════════════════════════════════════════════════════"
echo "▶ Mode: $MODE"
[[ "$MODE" == "single" ]] && echo "▶ Panel: $PANEL_ID"
[[ "$DRY_RUN" == true ]] && echo "▶ DRY RUN: Commands will be shown but not executed"
echo "▶ Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Helper function for dry run
run_cmd() {
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [DRY] $*"
  else
    "$@"
  fi
}

# -------------------------------
# Phase 0: Snapshot Gate (MANDATORY)
# -------------------------------
# INVARIANT: HISAR never talks to a live compiler.
# Coherency depends on immutable snapshot input.
# -------------------------------
echo "▶ [G] Phase 0 — Snapshot Gate (MANDATORY)"
echo "──────────────────────────────────────────────────────────────────────"

SNAPSHOT_PATH="$ROOT_DIR/backend/.openapi_snapshot.json"

# Check snapshot exists
if [[ ! -f "$SNAPSHOT_PATH" ]]; then
    echo "  FATAL: OpenAPI snapshot missing."
    echo "         File: $SNAPSHOT_PATH"
    echo "         Run:  ./scripts/tools/hisar_snapshot_backend.sh"
    exit 1
fi

# Check snapshot non-empty
if [[ ! -s "$SNAPSHOT_PATH" ]]; then
    echo "  FATAL: OpenAPI snapshot is empty (0 bytes)."
    echo "         File: $SNAPSHOT_PATH"
    echo "         Run:  ./scripts/tools/hisar_snapshot_backend.sh"
    exit 1
fi

# Validate snapshot JSON
if ! python3 -c "
import json
with open('$SNAPSHOT_PATH') as f:
    spec = json.load(f)
assert 'paths' in spec and len(spec['paths']) > 0, 'Invalid snapshot'
print(f'  Snapshot valid: {len(spec[\"paths\"])} routes')
" 2>/dev/null; then
    echo "  FATAL: OpenAPI snapshot is corrupt or invalid."
    echo "         File: $SNAPSHOT_PATH"
    echo "         Run:  ./scripts/tools/hisar_snapshot_backend.sh"
    exit 1
fi

echo "✓ Snapshot gate passed"
echo ""

# -------------------------------
# Phase 0.1: Universe Validation (MANDATORY - BLOCKING)
# -------------------------------
# INVARIANT: HISAR never starts with an incoherent universe.
# All APPROVED intents must be resolvable before ANY phase runs.
# This is the SINGLE CHOKE POINT that prevents all downstream thrash.
# -------------------------------
echo "▶ [G] Phase 0.1 — Universe Validation (BLOCKING)"
echo "──────────────────────────────────────────────────────────────────────"

UNIVERSE_CHECK="/tmp/hisar_universe_check_$$.json"

# Run global coherency check
# Note: --refresh-routes prints text before JSON, so we refresh first, then get JSON
if [[ "$DRY_RUN" == true ]]; then
    echo "  [DRY] Would run: aurora_coherency_check.py --all --json"
else
    # First refresh routes (this prints text to stdout, we discard it)
    python3 "$TOOLS_DIR/aurora_coherency_check.py" --refresh-routes > /dev/null 2>&1

    # Now run coherency check with JSON output (no refresh, so pure JSON)
    python3 "$TOOLS_DIR/aurora_coherency_check.py" --all --json > "$UNIVERSE_CHECK" 2>&1
    UNIVERSE_EXIT=$?

    if [[ $UNIVERSE_EXIT -ne 0 ]]; then
        echo "  FATAL: Universe coherency check failed to run."
        echo "         Exit code: $UNIVERSE_EXIT"
        cat "$UNIVERSE_CHECK" 2>/dev/null || true
        rm -f "$UNIVERSE_CHECK"
        exit 1
    fi

    # Check for failures using jq
    FAILURES=$(jq -r '.total_failures // 0' "$UNIVERSE_CHECK" 2>/dev/null)

    if [[ "$FAILURES" -gt 0 ]]; then
        echo "  FATAL: Universe incoherent. HISAR blocked."
        echo ""
        echo "  Found $FAILURES coherency violations in APPROVED intents."
        echo "  The following panels have unresolvable state:"
        echo ""
        # Show failed panels
        jq -r '.results | to_entries[] | select(.value[].status == "FAIL") | "    \(.key): \(.value[] | select(.status == "FAIL") | .message)"' "$UNIVERSE_CHECK" 2>/dev/null | head -20
        echo ""
        echo "  Fix these violations before running HISAR."
        echo "  Pipeline BLOCKED at Phase 0.1."
        rm -f "$UNIVERSE_CHECK"
        exit 1
    fi

    TOTAL_PANELS=$(jq -r '.total_panels // 0' "$UNIVERSE_CHECK" 2>/dev/null)
    echo "  Validated $TOTAL_PANELS panels against snapshot."
    rm -f "$UNIVERSE_CHECK"
fi

echo "✓ Universe validation passed — all APPROVED intents resolvable"
echo ""

# -------------------------------
# Phase 1: Human Intent
# -------------------------------
echo "▶ [H] Phase 1 — Human Intent Validation"
echo "──────────────────────────────────────────────────────────────────────"

if [[ "$MODE" == "single" ]]; then
  # Check intent YAML exists (new naming convention with legacy fallback)
  INTENT_FILE="$ROOT_DIR/design/l2_1/intents/AURORA_L2_INTENT_${PANEL_ID}.yaml"
  INTENT_FILE_LEGACY="$ROOT_DIR/design/l2_1/intents/${PANEL_ID}.yaml"
  if [[ -f "$INTENT_FILE" ]]; then
    echo "  Intent YAML exists: $INTENT_FILE"
  elif [[ -f "$INTENT_FILE_LEGACY" ]]; then
    echo "  Intent YAML exists (legacy): $INTENT_FILE_LEGACY"
    INTENT_FILE="$INTENT_FILE_LEGACY"
  else
    echo "  Intent YAML not found: $INTENT_FILE"
    echo "  Scaffolding new intent..."
    run_cmd python3 "$TOOLS_DIR/aurora_intent_scaffold.py" --panel "$PANEL_ID"
  fi
else
  echo "  Checking all intent files..."
  run_cmd python3 "$TOOLS_DIR/aurora_intent_registry_sync.py" --list
fi

echo "✓ Human intent accepted"
echo ""

# -------------------------------
# Phase 2: Intent Specification
# -------------------------------
echo "▶ [H] Phase 2 — Intent Specification"
echo "──────────────────────────────────────────────────────────────────────"

if [[ "$MODE" == "single" ]]; then
  run_cmd python3 "$TOOLS_DIR/aurora_intent_registry_sync.py" --panel "$PANEL_ID"

  # Check if approved - NO INTERACTIVE PROMPTS
  # INVARIANT: HISAR runs unattended. DRAFT intents block execution.
  echo "  Checking approval status..."
  REGISTRY_FILE="$ROOT_DIR/design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"
  # Note: registry entries are indented, so we match with optional leading whitespace
  if grep -A5 "^[[:space:]]*${PANEL_ID}:" "$REGISTRY_FILE" 2>/dev/null | grep -q "status: APPROVED"; then
    echo "  Status: APPROVED"
  else
    echo "  FATAL: Intent not APPROVED. Pipeline blocked."
    echo ""
    echo "  Status: DRAFT (requires approval before HISAR can run)"
    echo ""
    echo "  To approve, run:"
    echo "    python3 $TOOLS_DIR/aurora_intent_registry_sync.py --approve $PANEL_ID"
    echo ""
    echo "  Then re-run HISAR."
    exit 1
  fi
else
  run_cmd python3 "$TOOLS_DIR/aurora_intent_registry_sync.py" --all
fi

echo "✓ Intent specification valid"
echo ""

# -------------------------------
# Phase 3: Capability Declaration
# -------------------------------
echo "▶ [A] Phase 3 — Capability Declaration"
echo "──────────────────────────────────────────────────────────────────────"

CAPABILITY_FAILURES=0
if [[ "$MODE" == "single" ]]; then
  # Extract capability ID from intent (look under capability: block, not panel_id)
  # New naming convention with fallback to legacy
  INTENT_FILE="$ROOT_DIR/design/l2_1/intents/AURORA_L2_INTENT_${PANEL_ID}.yaml"
  if [[ ! -f "$INTENT_FILE" ]]; then
    INTENT_FILE="$ROOT_DIR/design/l2_1/intents/${PANEL_ID}.yaml"  # Legacy fallback
  fi
  CAP_ID=$(grep -A1 "^capability:" "$INTENT_FILE" | grep "id:" | awk '{print $2}' | tr -d "'\"")
  CAP_FILE="$ROOT_DIR/backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_${CAP_ID}.yaml"

  if [[ -f "$CAP_FILE" ]]; then
    echo "  Capability already exists: $CAP_ID (skipping scaffold)"
  else
    run_cmd python3 "$TOOLS_DIR/aurora_capability_scaffold.py" --panel "$PANEL_ID"
    if [[ $? -ne 0 ]]; then
      echo "  FATAL: Capability scaffold failed for $PANEL_ID"
      exit 1
    fi
  fi
else
  echo "  Scaffolding capabilities for all panels..."
  # Process each intent file
  for intent in "$ROOT_DIR/design/l2_1/intents"/*.yaml; do
    if [[ -f "$intent" ]]; then
      panel=$(basename "$intent" .yaml)
      # Extract capability ID (look under capability: block)
      cap_id=$(grep -A1 "^capability:" "$intent" | grep "id:" | awk '{print $2}' | tr -d "'\"")
      cap_file="$ROOT_DIR/backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_${cap_id}.yaml"

      if [[ -f "$cap_file" ]]; then
        echo "  Exists: $cap_id"
      else
        run_cmd python3 "$TOOLS_DIR/aurora_capability_scaffold.py" --panel "$panel"
        if [[ $? -ne 0 ]]; then
          echo "  WARNING: Capability scaffold failed for $panel"
          CAPABILITY_FAILURES=$((CAPABILITY_FAILURES + 1))
        fi
      fi
    fi
  done
  if [[ $CAPABILITY_FAILURES -gt 0 ]]; then
    echo "  FATAL: $CAPABILITY_FAILURES capability scaffolds failed. Pipeline blocked."
    exit 1
  fi
fi

echo "✓ Capability scaffolded (DECLARED)"
echo ""

# -------------------------------
# Phase 3.5: Coherency Gate (BLOCKING)
# -------------------------------
# INVARIANT: This gate MUST block if coherency fails.
# No workarounds, no "continue anyway".
# -------------------------------
echo "▶ [S] Phase 3.5 — Coherency Gate (BLOCKING)"
echo "──────────────────────────────────────────────────────────────────────"

if [[ "$MODE" == "single" ]]; then
  run_cmd python3 "$TOOLS_DIR/aurora_coherency_check.py" --panel "$PANEL_ID" --refresh-routes
  COHERENCY_EXIT=$?
else
  run_cmd python3 "$TOOLS_DIR/aurora_coherency_check.py" --all --refresh-routes
  COHERENCY_EXIT=$?
fi

if [[ $COHERENCY_EXIT -ne 0 ]]; then
  echo ""
  echo "  FATAL: Coherency gate failed. Pipeline blocked."
  echo "         Fix the coherency violations before continuing."
  echo "         Exit code: $COHERENCY_EXIT"
  exit 1
fi

echo "✓ Coherency verified"
echo ""

# -------------------------------
# Phase 4: SDSR Verification
# -------------------------------
echo "▶ [S] Phase 4 — SDSR Verification"
echo "──────────────────────────────────────────────────────────────────────"

if [[ "$MODE" == "single" ]]; then
  # Generate scenario if needed
  SCENARIO_FILE="$ROOT_DIR/backend/scripts/sdsr/scenarios/SDSR-${PANEL_ID}-001.yaml"
  if [[ ! -f "$SCENARIO_FILE" ]]; then
    echo "  Generating SDSR scenario..."
    run_cmd python3 "$TOOLS_DIR/aurora_sdsr_synth.py" --panel "$PANEL_ID"
  fi

  # Run SDSR - exit code MUST be checked
  run_cmd python3 "$TOOLS_DIR/aurora_sdsr_runner.py" --panel "$PANEL_ID"
  SDSR_EXIT=$?
  if [[ $SDSR_EXIT -ne 0 ]]; then
    echo "  FATAL: SDSR verification failed for $PANEL_ID"
    echo "         Exit code: $SDSR_EXIT"
    exit 1
  fi
else
  # Run all scenarios
  run_cmd python3 "$TOOLS_DIR/aurora_sdsr_schedule.py" --all
  SDSR_EXIT=$?
  if [[ $SDSR_EXIT -ne 0 ]]; then
    echo "  FATAL: SDSR schedule failed. Pipeline blocked."
    echo "         Exit code: $SDSR_EXIT"
    exit 1
  fi
fi

echo "✓ SDSR observation complete"
echo ""

# -------------------------------
# Phase 5: Observation Application
# -------------------------------
echo "▶ [S] Phase 5 — Apply Observation"
echo "──────────────────────────────────────────────────────────────────────"

OBSERVATION_FAILURES=0
if [[ "$MODE" == "single" ]]; then
  # Find the observation file - use capability.id not panel_id
  # New naming convention with fallback to legacy
  INTENT_FILE="$ROOT_DIR/design/l2_1/intents/AURORA_L2_INTENT_${PANEL_ID}.yaml"
  if [[ ! -f "$INTENT_FILE" ]]; then
    INTENT_FILE="$ROOT_DIR/design/l2_1/intents/${PANEL_ID}.yaml"  # Legacy fallback
  fi
  if [[ -f "$INTENT_FILE" ]]; then
    CAP_ID=$(grep -A1 "^capability:" "$INTENT_FILE" | grep "id:" | awk '{print $2}' | tr -d "'\"")
    if [[ -n "$CAP_ID" ]]; then
      run_cmd python3 "$TOOLS_DIR/aurora_apply_observation.py" --capability "$CAP_ID"
      if [[ $? -ne 0 ]]; then
        echo "  FATAL: Observation application failed for $CAP_ID"
        exit 1
      fi
    else
      echo "  FATAL: Could not extract capability ID from intent"
      exit 1
    fi
  else
    echo "  FATAL: Intent file not found: $INTENT_FILE"
    exit 1
  fi
else
  # Apply all observations - track failures
  for obs in "$ROOT_DIR/backend/scripts/sdsr/observations"/*.json; do
    if [[ -f "$obs" ]]; then
      cap_id=$(basename "$obs" .json | sed 's/SDSR_OBSERVATION_//')
      run_cmd python3 "$TOOLS_DIR/aurora_apply_observation.py" --capability "$cap_id"
      if [[ $? -ne 0 ]]; then
        echo "  WARNING: Observation application failed for $cap_id"
        OBSERVATION_FAILURES=$((OBSERVATION_FAILURES + 1))
      fi
    fi
  done
  if [[ $OBSERVATION_FAILURES -gt 0 ]]; then
    echo "  FATAL: $OBSERVATION_FAILURES observation applications failed. Pipeline blocked."
    exit 1
  fi
fi

echo "✓ Observation applied (OBSERVED)"
echo ""

# -------------------------------
# Phase 5.5: Trust Evaluation
# -------------------------------
echo "▶ [S] Phase 5.5 — Trust Evaluation"
echo "──────────────────────────────────────────────────────────────────────"

if [[ "$MODE" == "single" ]]; then
  # New naming convention with fallback to legacy
  INTENT_FILE="$ROOT_DIR/design/l2_1/intents/AURORA_L2_INTENT_${PANEL_ID}.yaml"
  if [[ ! -f "$INTENT_FILE" ]]; then
    INTENT_FILE="$ROOT_DIR/design/l2_1/intents/${PANEL_ID}.yaml"  # Legacy fallback
  fi
  if [[ -f "$INTENT_FILE" ]]; then
    CAP_ID=$(grep "id:" "$INTENT_FILE" | grep -v "topic_id" | head -1 | awk '{print $2}' | tr -d "'\"")
    if [[ -n "$CAP_ID" ]]; then
      run_cmd python3 "$TOOLS_DIR/aurora_trust_evaluator.py" --capability "$CAP_ID" -v
    fi
  fi
else
  run_cmd python3 "$TOOLS_DIR/aurora_trust_evaluator.py" --all -v
fi

echo "✓ Trust state evaluated"
echo ""

# -------------------------------
# Phase 6: Aurora Compilation
# -------------------------------
echo "▶ [A] Phase 6 — Aurora Compilation"
echo "──────────────────────────────────────────────────────────────────────"

run_cmd python3 "$ROOT_DIR/backend/aurora_l2/SDSR_UI_AURORA_compiler.py"
COMPILE_EXIT=$?
if [[ $COMPILE_EXIT -ne 0 ]]; then
  echo "  FATAL: Aurora compilation failed. Pipeline blocked."
  echo "         Exit code: $COMPILE_EXIT"
  exit 1
fi

echo "✓ Aurora compilation complete"
echo ""

# -------------------------------
# Phase 6.5: UI Plan Bind
# -------------------------------
echo "▶ [A] Phase 6.5 — UI Plan Bind"
echo "──────────────────────────────────────────────────────────────────────"

BIND_FAILURES=0
if [[ "$MODE" == "single" ]]; then
  run_cmd python3 "$TOOLS_DIR/aurora_ui_plan_bind.py" --panel "$PANEL_ID"
  if [[ $? -ne 0 ]]; then
    echo "  FATAL: UI Plan bind failed for $PANEL_ID"
    exit 1
  fi
else
  # Bind all panels that have OBSERVED capabilities - track failures
  for intent in "$ROOT_DIR/design/l2_1/intents"/*.yaml; do
    if [[ -f "$intent" ]]; then
      panel=$(basename "$intent" .yaml)
      run_cmd python3 "$TOOLS_DIR/aurora_ui_plan_bind.py" --panel "$panel"
      if [[ $? -ne 0 ]]; then
        echo "  WARNING: UI Plan bind failed for $panel"
        BIND_FAILURES=$((BIND_FAILURES + 1))
      fi
    fi
  done
  if [[ $BIND_FAILURES -gt 0 ]]; then
    echo "  FATAL: $BIND_FAILURES UI Plan binds failed. Pipeline blocked."
    exit 1
  fi
fi

echo "✓ UI Plan synchronized"
echo ""

# -------------------------------
# Phase 7: Projection Diff Guard (BLOCKING)
# -------------------------------
# INVARIANT: PDG violations block the pipeline. No interactive bypass.
# If PDG fails, fix the projection or update the allowlist.
# -------------------------------
echo "▶ [A] Phase 7 — Projection Diff Guard (BLOCKING)"
echo "──────────────────────────────────────────────────────────────────────"

OLD_PROJ="$ROOT_DIR/website/app-shell/public/projection/ui_projection_lock.json"
NEW_PROJ="$ROOT_DIR/design/l2_1/ui_contract/ui_projection_lock.json"

if [[ -f "$OLD_PROJ" && -f "$NEW_PROJ" ]]; then
  run_cmd python3 "$TOOLS_DIR/projection_diff_guard.py" --old "$OLD_PROJ" --new "$NEW_PROJ" --audit
  PDG_EXIT=$?
  if [[ $PDG_EXIT -ne 0 ]]; then
    echo ""
    echo "  FATAL: PDG detected violations. Pipeline blocked."
    echo ""
    echo "  To proceed, you must either:"
    echo "    1. Fix the projection to remove violations"
    echo "    2. Update the PDG allowlist if changes are intentional"
    echo ""
    echo "  Exit code: $PDG_EXIT"
    exit 1
  fi
else
  echo "  Skipping PDG (no previous projection to compare)"
fi

echo "✓ Projection diff validated"
echo ""

# -------------------------------
# Phase 8: Rendering
# -------------------------------
echo "▶ [R] Phase 8 — Rendering"
echo "──────────────────────────────────────────────────────────────────────"

SRC="$ROOT_DIR/design/l2_1/ui_contract/ui_projection_lock.json"
DST="$ROOT_DIR/website/app-shell/public/projection/ui_projection_lock.json"

if [[ -f "$SRC" ]]; then
  run_cmd cp "$SRC" "$DST"
  echo "  Copied: ui_projection_lock.json → public/projection/"
else
  echo "  Warning: No projection to copy"
fi

echo "✓ Rendering updated"
echo ""

# -------------------------------
# Phase 9: Memory PIN Generation (Automation)
# -------------------------------
# POST-PIPELINE AUTOMATION (PIN-432):
# Auto-generate memory PIN summarizing the pipeline run.
# This replaces manual PIN creation after HISAR execution.
# -------------------------------
echo "▶ [M] Phase 9 — Memory PIN Generation"
echo "──────────────────────────────────────────────────────────────────────"

# Generate pipeline summary
PIPELINE_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PROJECTION_FILE="$ROOT_DIR/design/l2_1/ui_contract/ui_projection_lock.json"

if [[ -f "$PROJECTION_FILE" && "$DRY_RUN" == false ]]; then
  # Extract stats from projection
  TOTAL_PANELS=$(jq '[.domains[].panels[]? // empty] | length' "$PROJECTION_FILE" 2>/dev/null || echo "0")
  BOUND_PANELS=$(jq '[.domains[].panels[]? | select(.binding_status == "BOUND")] | length' "$PROJECTION_FILE" 2>/dev/null || echo "0")
  DOMAINS_COUNT=$(jq '.domains | length' "$PROJECTION_FILE" 2>/dev/null || echo "0")

  echo "  Pipeline stats:"
  echo "    Total panels: $TOTAL_PANELS"
  echo "    BOUND panels: $BOUND_PANELS"
  echo "    Domains: $DOMAINS_COUNT"

  # Generate PIN content
  PIN_TITLE="HISAR Pipeline Run"
  [[ "$MODE" == "single" ]] && PIN_TITLE="HISAR Pipeline Run: $PANEL_ID"

  # Include proper PIN header in content (memory_trail.py --from-file uses raw content)
  # Note: Don't include "# PIN:" since memory_trail.py handles titling
  PIN_CONTENT=$(cat <<EOF
**Status:** COMPLETE
**Created:** $(date +%Y-%m-%d)
**Category:** HISAR / Pipeline Execution

---

## Summary

HISAR pipeline executed successfully.

- **Mode:** $MODE
$([[ "$MODE" == "single" ]] && echo "- **Panel:** $PANEL_ID")
- **Timestamp:** $PIPELINE_TIMESTAMP
- **Total Panels:** $TOTAL_PANELS
- **BOUND Panels:** $BOUND_PANELS
- **Domains:** $DOMAINS_COUNT

## Phases Completed

| Phase | Name | Status |
|-------|------|--------|
| 0 | Snapshot Gate | ✓ PASSED |
| 0.1 | Universe Validation | ✓ PASSED |
| 1 | Human Intent Validation | ✓ PASSED |
| 2 | Intent Specification | ✓ PASSED |
| 3 | Capability Declaration | ✓ PASSED |
| 3.5 | Coherency Gate | ✓ PASSED |
| 4 | SDSR Verification | ✓ PASSED |
| 5 | Observation Application | ✓ PASSED |
| 5.5 | Trust Evaluation | ✓ PASSED |
| 6 | Aurora Compilation | ✓ PASSED |
| 6.5 | UI Plan Bind | ✓ PASSED |
| 7 | Projection Diff Guard | ✓ PASSED |
| 8 | Rendering | ✓ PASSED |

## Automation Features (PIN-432)

- Observation-preserving sync (prevents status regression)
- PDG allowlist auto-append (auto-permits binding transitions)
- Post-pipeline PIN generation (this document)
EOF
)

  # Try to generate PIN using memory_trail.py (optional - don't fail pipeline if unavailable)
  MEMORY_TRAIL="$ROOT_DIR/scripts/ops/memory_trail.py"
  if [[ -x "$MEMORY_TRAIL" || -f "$MEMORY_TRAIL" ]]; then
    # Write content to temp file
    TEMP_PIN_CONTENT="/tmp/hisar_pin_content_$$.md"
    echo "$PIN_CONTENT" > "$TEMP_PIN_CONTENT"

    # Generate PIN (suppress errors, this is optional)
    if python3 "$MEMORY_TRAIL" pin \
        --title "$PIN_TITLE" \
        --category "HISAR / Pipeline Execution" \
        --status "COMPLETE" \
        --from-file "$TEMP_PIN_CONTENT" 2>/dev/null; then
      echo "  ✅ Memory PIN generated automatically"
    else
      echo "  ⚠️  Memory PIN generation skipped (memory_trail.py not configured)"
    fi

    rm -f "$TEMP_PIN_CONTENT"
  else
    echo "  ⚠️  Memory PIN generation skipped (memory_trail.py not found)"
  fi
else
  echo "  Skipping PIN generation (dry run or no projection)"
fi

echo "✓ Pipeline documentation complete"
echo ""

# -------------------------------
# Summary
# -------------------------------
echo "══════════════════════════════════════════════════════════════════════"
echo "✔ HISAR COMPLETE — Intent rendered as truth"
echo "══════════════════════════════════════════════════════════════════════"
echo ""
echo "  Mode:   $MODE"
[[ "$MODE" == "single" ]] && echo "  Panel:  $PANEL_ID"
echo "  Time:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "  Phases completed:"
echo "    [G] 0    Snapshot Gate                ✓"
echo "    [G] 0.1  Universe Validation          ✓"
echo "    [H] 1    Human Intent Validation      ✓"
echo "    [H] 2    Intent Specification         ✓"
echo "    [A] 3    Capability Declaration       ✓"
echo "    [S] 3.5  Coherency Gate               ✓"
echo "    [S] 4    SDSR Verification            ✓"
echo "    [S] 5    Observation Application      ✓"
echo "    [S] 5.5  Trust Evaluation             ✓"
echo "    [A] 6    Aurora Compilation           ✓"
echo "    [A] 6.5  UI Plan Bind                 ✓"
echo "    [A] 7    Projection Diff Guard        ✓"
echo "    [R] 8    Rendering                    ✓"
echo "    [M] 9    Memory PIN Generation        ✓"
echo ""
