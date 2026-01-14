#!/usr/bin/env bash
# =============================================================================
# AURORA_L2 Pipeline Runner (Canonical)
# =============================================================================
# Purpose: Mechanically connect all pipeline stages
# Usage:   DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh [--dry-run] [--validate-only]
#
# CANONICAL DESIGN (LOCKED):
#   - Compiler generates SINGLE canonical projection
#   - Output: design/l2_1/ui_contract/ui_projection_lock.json
#   - Copy verbatim to: website/app-shell/public/projection/
#   - No merge scripts. No adapters. No dual formats.
#
# Pipeline:
#   1. Validate prerequisites (including DB_AUTHORITY)
#   2. Validate intent YAML structure
#   3. Validate semantics against registry
#   4. Run compiler → canonical projection
#   5. Verify canonical projection
#   5.5. Projection Diff Guard (HIL v1 - PIN-417)
#   6. Deploy to frontend public/
#   7. Emit compile report
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# =============================================================================
# PHASE 0: DB_AUTHORITY ENFORCEMENT (HARD FAIL)
# =============================================================================
if [[ -z "${DB_AUTHORITY:-}" ]]; then
    echo "[FATAL] DB_AUTHORITY not declared." >&2
    echo "        Authority is declared, not inferred." >&2
    echo "        Set DB_AUTHORITY=neon or DB_AUTHORITY=local before running." >&2
    echo "        Example: DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh" >&2
    echo "        Reference: docs/governance/DB_AUTH_001_INVARIANT.md" >&2
    exit 1
fi

if [[ "$DB_AUTHORITY" != "neon" && "$DB_AUTHORITY" != "local" ]]; then
    echo "[FATAL] Invalid DB_AUTHORITY: $DB_AUTHORITY" >&2
    echo "        Must be 'neon' or 'local'." >&2
    exit 1
fi

export DB_AUTHORITY

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
DRY_RUN=false
VALIDATE_ONLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: $0 [--dry-run] [--validate-only]"
            exit 1
            ;;
    esac
done

# Paths
INTENTS_DIR="$REPO_ROOT/design/l2_1/intents"
REGISTRY_PATH="$REPO_ROOT/design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"
SEMANTIC_REGISTRY="$REPO_ROOT/design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml"
EXPANSION_REGISTRY="$REPO_ROOT/design/l2_1/AURORA_L2_EXPANSION_MODE_REGISTRY.yaml"
EXPORTS_DIR="$REPO_ROOT/design/l2_1/exports"
COMPILER="$REPO_ROOT/backend/aurora_l2/compiler.py"
PUBLIC_PROJECTION="$REPO_ROOT/website/app-shell/public/projection"

# CANONICAL PROJECTION PATH (single source of truth)
UI_CONTRACT_DIR="$REPO_ROOT/design/l2_1/ui_contract"
CANONICAL_PROJECTION="$UI_CONTRACT_DIR/ui_projection_lock.json"

# Pipeline state
ERRORS=0
WARNINGS=0

log_step() {
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}[$1] $2${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
}

log_ok() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}  ✗ $1${NC}"
    ((ERRORS++))
}

log_info() {
    echo -e "  → $1"
}

# =============================================================================
# STAGE 1: Validate Prerequisites
# =============================================================================
stage_1_prerequisites() {
    log_step "1/7" "Validate Prerequisites"

    # Check intent registry exists
    if [[ -f "$REGISTRY_PATH" ]]; then
        log_ok "Intent registry found: $REGISTRY_PATH"
    else
        log_error "Intent registry not found: $REGISTRY_PATH"
        return 1
    fi

    # Check semantic registry exists
    if [[ -f "$SEMANTIC_REGISTRY" ]]; then
        log_ok "Semantic registry found: $SEMANTIC_REGISTRY"
    else
        log_error "Semantic registry not found: $SEMANTIC_REGISTRY"
        return 1
    fi

    # Check expansion registry exists
    if [[ -f "$EXPANSION_REGISTRY" ]]; then
        log_ok "Expansion registry found: $EXPANSION_REGISTRY"
    else
        log_error "Expansion registry not found: $EXPANSION_REGISTRY"
        return 1
    fi

    # Check intents directory
    if [[ -d "$INTENTS_DIR" ]]; then
        INTENT_COUNT=$(find "$INTENTS_DIR" -name "*.yaml" -type f | wc -l)
        log_ok "Intents directory found: $INTENT_COUNT YAML files"
    else
        log_error "Intents directory not found: $INTENTS_DIR"
        return 1
    fi

    # Check compiler exists
    if [[ -f "$COMPILER" ]]; then
        log_ok "Compiler found: $COMPILER"
    else
        log_error "Compiler not found: $COMPILER"
        return 1
    fi

    # Check Python available
    if command -v python3 &> /dev/null; then
        log_ok "Python3 available: $(python3 --version)"
    else
        log_error "Python3 not found"
        return 1
    fi

    # Check PyYAML available
    if python3 -c "import yaml" 2>/dev/null; then
        log_ok "PyYAML module available"
    else
        log_error "PyYAML module not found (pip install pyyaml)"
        return 1
    fi
}

# =============================================================================
# STAGE 2: Validate Intent YAMLs (Structural)
# =============================================================================
stage_2_validate_structure() {
    log_step "2/7" "Validate Intent YAML Structure"

    local valid=0
    local invalid=0

    for yaml_file in "$INTENTS_DIR"/*.yaml; do
        [[ "$(basename "$yaml_file")" == "README.md" ]] && continue
        [[ ! -f "$yaml_file" ]] && continue

        # Check YAML is parseable
        if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            # Check required fields
            if python3 -c "
import yaml
with open('$yaml_file') as f:
    data = yaml.safe_load(f)
    assert 'panel_id' in data, 'missing panel_id'
    assert 'metadata' in data, 'missing metadata'
    assert 'display' in data, 'missing display'
    assert 'data' in data, 'missing data'
    assert 'controls' in data, 'missing controls'
" 2>/dev/null; then
                ((valid++))
            else
                log_error "Missing required fields: $(basename "$yaml_file")"
                ((invalid++))
            fi
        else
            log_error "Invalid YAML: $(basename "$yaml_file")"
            ((invalid++))
        fi
    done

    log_info "Valid: $valid, Invalid: $invalid"

    if [[ $invalid -gt 0 ]]; then
        return 1
    fi
    log_ok "All $valid intent YAMLs are structurally valid"
}

# =============================================================================
# STAGE 3: Validate Semantics
# =============================================================================
stage_3_validate_semantics() {
    log_step "3/7" "Validate Semantics Against Registry"

    # Create a Python validation script inline
    python3 << 'PYEOF'
import yaml
import sys
from pathlib import Path

repo_root = Path(__file__).parent if '__file__' in dir() else Path.cwd()
# Handle being run from different directories
for p in [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]:
    if (p / "design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml").exists():
        repo_root = p
        break

semantic_path = repo_root / "design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml"
expansion_path = repo_root / "design/l2_1/AURORA_L2_EXPANSION_MODE_REGISTRY.yaml"
intents_dir = repo_root / "design/l2_1/intents"

# Load registries
with open(semantic_path) as f:
    semantic_reg = yaml.safe_load(f)

with open(expansion_path) as f:
    expansion_reg = yaml.safe_load(f)

valid_verbs = set(semantic_reg.get('verbs', {}).keys())
valid_modes = set(expansion_reg.get('modes', {}).keys())
valid_domains = {'Overview', 'Activity', 'Incidents', 'Policies', 'Logs'}

errors = []
warnings = []

for yaml_file in sorted(intents_dir.glob("*.yaml")):
    if yaml_file.name == "README.md":
        continue

    with open(yaml_file) as f:
        intent = yaml.safe_load(f)

    panel_id = intent.get('panel_id', yaml_file.stem)

    # Check domain
    domain = intent.get('metadata', {}).get('domain', '')
    if domain not in valid_domains:
        errors.append(f"{panel_id}: Invalid domain '{domain}'")

    # Check expansion mode
    mode = intent.get('display', {}).get('expansion_mode', 'INLINE')
    if mode not in valid_modes:
        errors.append(f"{panel_id}: Invalid expansion_mode '{mode}'")

    # Check control verbs
    controls = intent.get('controls', {}).get('control_set', [])
    for ctrl in controls:
        # Controls map to verbs
        if ctrl not in valid_verbs and ctrl not in {'SELECT_SINGLE', 'SELECT_MULTI'}:
            warnings.append(f"{panel_id}: Control '{ctrl}' not in semantic registry")

# Report
if errors:
    print("ERRORS:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)

if warnings:
    print("WARNINGS:")
    for w in warnings:
        print(f"  ⚠ {w}")

print(f"Semantic validation complete: {len(errors)} errors, {len(warnings)} warnings")
sys.exit(0)
PYEOF

    if [[ $? -eq 0 ]]; then
        log_ok "Semantic validation passed"
    else
        log_error "Semantic validation failed"
        return 1
    fi
}

# =============================================================================
# STAGE 4: Run Compiler (CANONICAL PROJECTION)
# =============================================================================
stage_4_compile() {
    log_step "4/7" "Run AURORA_L2 Compiler (Canonical)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run: DB_AUTHORITY=$DB_AUTHORITY python3 -m backend.aurora_l2.compiler"
        log_ok "Compiler dry-run complete"
        return 0
    fi

    cd "$REPO_ROOT"

    # Run compiler with DB_AUTHORITY - generates canonical projection
    if python3 -m backend.aurora_l2.compiler; then
        log_ok "Compiler succeeded"

        # Verify canonical projection was generated
        if [[ -f "$CANONICAL_PROJECTION" ]]; then
            local panels=$(python3 -c "import json; p=json.load(open('$CANONICAL_PROJECTION')); print(p['_statistics']['panel_count'])")
            local bound=$(python3 -c "import json; p=json.load(open('$CANONICAL_PROJECTION')); print(p['_statistics']['bound_panels'])")
            log_ok "Generated canonical projection: $panels panels, $bound BOUND"
        else
            log_error "Canonical projection not generated: $CANONICAL_PROJECTION"
            return 1
        fi

        # Legacy outputs (still generated for backward compatibility)
        if [[ -f "$EXPORTS_DIR/intent_store_compiled.json" ]]; then
            local count=$(python3 -c "import json; print(len(json.load(open('$EXPORTS_DIR/intent_store_compiled.json'))))")
            log_ok "Generated: intent_store_compiled.json ($count intents)"
        fi

        if [[ -f "$EXPORTS_DIR/intent_store_seed.sql" ]]; then
            local lines=$(wc -l < "$EXPORTS_DIR/intent_store_seed.sql")
            log_ok "Generated: intent_store_seed.sql ($lines lines)"
        fi
    else
        log_error "Compiler failed"
        return 1
    fi
}

# =============================================================================
# STAGE 5: Verify Projection (Already built by compiler)
# =============================================================================
stage_5_build_projection() {
    log_step "5/7" "Verify Canonical Projection"

    # CANONICAL DESIGN: Compiler already generated the projection
    # This stage just verifies it exists and is valid

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would verify canonical projection at $CANONICAL_PROJECTION"
        log_ok "Projection verification dry-run complete"
        return 0
    fi

    # Verify canonical projection exists
    if [[ ! -f "$CANONICAL_PROJECTION" ]]; then
        log_error "Canonical projection not found: $CANONICAL_PROJECTION"
        log_error "Compiler should have generated this in stage 4"
        return 1
    fi

    # Validate projection structure
    if python3 -c "
import json
import sys
with open('$CANONICAL_PROJECTION') as f:
    p = json.load(f)

# Required fields
assert '_meta' in p, 'Missing _meta'
assert '_statistics' in p, 'Missing _statistics'
assert '_contract' in p, 'Missing _contract'
assert 'domains' in p, 'Missing domains'

# _meta requirements
assert p['_meta']['type'] == 'ui_projection_lock', 'Invalid _meta.type'
assert p['_meta']['db_authority'] == '$DB_AUTHORITY', 'DB_AUTHORITY mismatch'

# _contract requirements
assert p['_contract']['binding_status_required'] == True, 'binding_status_required must be True'
assert p['_contract']['ui_must_not_infer'] == True, 'ui_must_not_infer must be True'

print('Canonical projection validated')
" 2>/dev/null; then
        log_ok "Canonical projection validated: $CANONICAL_PROJECTION"
    else
        log_error "Canonical projection validation failed"
        return 1
    fi
}

# =============================================================================
# STAGE 5.5: Projection Diff Guard (HIL v1 - PIN-417)
# =============================================================================
# PURPOSE: Prevent silent UI drift by detecting unauthorized changes
# PLACEMENT: After compile, before deploy
# RULES ENFORCED:
#   PDG-001: No silent panel creation/deletion
#   PDG-002: No domain/subdomain drift
#   PDG-003: Binding status changes are explicit
#   PDG-004: panel_class is immutable post-declaration
#   PDG-005: Provenance cannot be removed
# =============================================================================
stage_5_5_diff_guard() {
    log_step "5.5/7" "Projection Diff Guard"

    local diff_guard="$REPO_ROOT/backend/aurora_l2/tools/projection_diff_guard.py"
    local allowlist="$REPO_ROOT/backend/aurora_l2/tools/projection_diff_allowlist.json"
    local prev_projection="$PUBLIC_PROJECTION/ui_projection_lock.json"
    local new_projection="$CANONICAL_PROJECTION"
    local diff_result="$EXPORTS_DIR/projection_diff_result.json"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run projection diff guard"
        log_ok "Diff guard dry-run complete"
        return 0
    fi

    # Check if diff guard exists
    if [[ ! -f "$diff_guard" ]]; then
        log_warn "Diff guard not found: $diff_guard (skipping)"
        return 0
    fi

    # Check if previous projection exists (first run = no diff)
    if [[ ! -f "$prev_projection" ]]; then
        log_info "No previous projection found (first run)"
        log_ok "Diff guard passed (no baseline)"
        return 0
    fi

    # Run diff guard
    log_info "Comparing projections..."
    log_info "  Previous: $prev_projection"
    log_info "  New:      $new_projection"

    if python3 "$diff_guard" \
        --old "$prev_projection" \
        --new "$new_projection" \
        --allowlist "$allowlist" \
        --output "$diff_result"; then
        log_ok "Diff guard passed: No unauthorized changes"
    else
        log_error "Diff guard FAILED: Unauthorized changes detected"
        log_error "See details: $diff_result"

        # Show violations
        if [[ -f "$diff_result" ]]; then
            echo ""
            echo -e "${RED}Violations:${NC}"
            python3 -c "
import json
with open('$diff_result') as f:
    result = json.load(f)
for v in result.get('violations', []):
    print(f\"  [{v['rule']}] {v['panel_id']}: {v['message']}\")
"
            echo ""
        fi

        return 1
    fi
}

# =============================================================================
# STAGE 6: Deploy to Frontend (Verbatim Copy)
# =============================================================================
stage_6_deploy() {
    log_step "6/7" "Deploy to Frontend"

    # CANONICAL DESIGN: Copy verbatim from ui_contract/ to public/
    local projection_src="$CANONICAL_PROJECTION"
    local projection_dst="$PUBLIC_PROJECTION/ui_projection_lock.json"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would copy: $projection_src → $projection_dst"
        log_ok "Deploy dry-run complete"
        return 0
    fi

    # Ensure destination directory exists
    mkdir -p "$PUBLIC_PROJECTION"

    # Copy canonical projection verbatim
    if [[ -f "$projection_src" ]]; then
        cp "$projection_src" "$projection_dst"
        log_ok "Copied canonical projection to: $projection_dst"
    else
        log_error "Canonical projection not found: $projection_src"
        return 1
    fi

    # Generate compile report
    local report_path="$EXPORTS_DIR/AURORA_L2_COMPILE_REPORT.json"
    python3 << PYEOF
import json
from datetime import datetime, timezone
from pathlib import Path

report = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'pipeline_version': '2.0.0',  # Canonical design version
    'db_authority': '$DB_AUTHORITY',
    'stages': {
        'prerequisites': 'PASS',
        'structure_validation': 'PASS',
        'semantic_validation': 'PASS',
        'compilation': 'PASS',
        'projection_validation': 'PASS',
        'diff_guard': 'PASS',
        'deployment': 'PASS'
    },
    'canonical_design': {
        'single_projection_file': True,
        'location': 'design/l2_1/ui_contract/ui_projection_lock.json',
        'no_merge_scripts': True,
        'no_adapters': True
    },
    'artifacts': [
        'design/l2_1/ui_contract/ui_projection_lock.json',  # CANONICAL
        'website/app-shell/public/projection/ui_projection_lock.json',  # COPY
        'design/l2_1/exports/intent_store_compiled.json',  # Legacy
        'design/l2_1/exports/intent_store_seed.sql'  # Legacy
    ],
    'errors': $ERRORS,
    'warnings': $WARNINGS
}

with open('$report_path', 'w') as f:
    json.dump(report, f, indent=2)

print(f"Compile report written: $report_path")
PYEOF

    log_ok "Pipeline complete"
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           AURORA_L2 Pipeline Runner                          ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║  Mode: $(if $DRY_RUN; then echo 'DRY RUN'; elif $VALIDATE_ONLY; then echo 'VALIDATE ONLY'; else echo 'FULL RUN'; fi)"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    cd "$REPO_ROOT"

    # Run stages
    stage_1_prerequisites || { echo -e "${RED}Pipeline failed at stage 1${NC}"; exit 1; }
    stage_2_validate_structure || { echo -e "${RED}Pipeline failed at stage 2${NC}"; exit 1; }
    stage_3_validate_semantics || { echo -e "${RED}Pipeline failed at stage 3${NC}"; exit 1; }

    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        echo -e "\n${GREEN}Validation complete. Skipping compilation and deployment.${NC}"
        exit 0
    fi

    stage_4_compile || { echo -e "${RED}Pipeline failed at stage 4${NC}"; exit 1; }
    stage_5_build_projection || { echo -e "${RED}Pipeline failed at stage 5${NC}"; exit 1; }
    stage_5_5_diff_guard || { echo -e "${RED}Pipeline failed at stage 5.5 (Diff Guard)${NC}"; exit 1; }
    stage_6_deploy || { echo -e "${RED}Pipeline failed at stage 6${NC}"; exit 1; }

    # Summary
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}AURORA_L2 Pipeline Complete (Canonical Design)${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "  DB Authority: $DB_AUTHORITY"
    echo -e "  Errors:   $ERRORS"
    echo -e "  Warnings: $WARNINGS"
    echo -e ""
    echo -e "  ${GREEN}Canonical Projection:${NC}"
    echo -e "    → $CANONICAL_PROJECTION"
    echo -e "    → $PUBLIC_PROJECTION/ui_projection_lock.json (copy)"
    echo -e ""
    echo -e "  Legacy Artifacts:"
    echo -e "    → $EXPORTS_DIR/intent_store_compiled.json"
    echo -e "    → $EXPORTS_DIR/intent_store_seed.sql"
    echo -e "    → $EXPORTS_DIR/AURORA_L2_COMPILE_REPORT.json"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "\n${YELLOW}This was a dry run. No files were modified.${NC}"
    fi
}

main
