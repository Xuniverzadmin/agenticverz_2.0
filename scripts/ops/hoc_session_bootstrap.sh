#!/usr/bin/env bash
# HOC Session Bootstrap Wrapper
#
# One-command bootstrap for HOC sessions.
# - Runs hoc-session-bootstrap status snapshot from installed Codex skill.
# - Optionally runs deterministic gate packs for architecture verification.
#
# Usage:
#   scripts/ops/hoc_session_bootstrap.sh --strict
#   scripts/ops/hoc_session_bootstrap.sh --strict --gates core
#   scripts/ops/hoc_session_bootstrap.sh --strict --gates full
#   scripts/ops/hoc_session_bootstrap.sh --json

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/ops/hoc_session_bootstrap.sh [options]

Options:
  --repo-root <path>       Repository root (default: auto-detect from script location)
  --strict                 Fail if required governance docs are missing
  --json                   Emit bootstrap status in JSON
  --gates <none|core|full> Run deterministic architecture gate pack (default: none)
  -h, --help               Show this help

Gate modes:
  none   Run bootstrap status only
  core   Run validators: cross-domain, layer boundaries, init hygiene, l5 pairing, uc-mon
  full   Run core validators plus governance pytest pack
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
STRICT=false
JSON=false
GATE_MODE="none"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo-root)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --repo-root requires a value" >&2
                exit 2
            fi
            REPO_ROOT="$2"
            BACKEND_DIR="${REPO_ROOT}/backend"
            shift 2
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        --json)
            JSON=true
            shift
            ;;
        --gates)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --gates requires one of: none|core|full" >&2
                exit 2
            fi
            GATE_MODE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown option '$1'" >&2
            usage
            exit 2
            ;;
    esac
done

if [[ "${GATE_MODE}" != "none" && "${GATE_MODE}" != "core" && "${GATE_MODE}" != "full" ]]; then
    echo "ERROR: --gates must be one of: none|core|full" >&2
    exit 2
fi

CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"
SKILL_STATUS_SCRIPT="${CODEX_HOME}/skills/hoc-session-bootstrap/scripts/hoc_bootstrap_status.py"

if [[ ! -f "${SKILL_STATUS_SCRIPT}" ]]; then
    echo "ERROR: skill script not found: ${SKILL_STATUS_SCRIPT}" >&2
    echo "Install the 'hoc-session-bootstrap' skill in ${CODEX_HOME}/skills first." >&2
    exit 1
fi

if [[ ! -d "${REPO_ROOT}" ]]; then
    echo "ERROR: repo root not found: ${REPO_ROOT}" >&2
    exit 1
fi

STATUS_CMD=(python3 "${SKILL_STATUS_SCRIPT}" --repo-root "${REPO_ROOT}")
if [[ "${STRICT}" == "true" ]]; then
    STATUS_CMD+=(--strict)
fi
if [[ "${JSON}" == "true" ]]; then
    STATUS_CMD+=(--json)
fi

echo "[hoc-session-bootstrap] running status snapshot..."
"${STATUS_CMD[@]}"

if [[ "${GATE_MODE}" == "none" ]]; then
    exit 0
fi

if [[ ! -d "${BACKEND_DIR}" ]]; then
    echo "ERROR: backend directory not found: ${BACKEND_DIR}" >&2
    exit 1
fi

echo "[hoc-session-bootstrap] running deterministic gates (${GATE_MODE})..."

run_gate() {
    local description="$1"
    shift
    echo "  - ${description}"
    (cd "${BACKEND_DIR}" && "$@")
}

run_gate "cross-domain validator" env PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json
run_gate "layer boundaries" env PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
run_gate "init hygiene" env PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
run_gate "l5-spine pairing gap detector" env PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json
run_gate "uc-mon strict validator" env PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict

if [[ "${GATE_MODE}" == "full" ]]; then
    run_gate "governance pytest pack" env PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py
fi

echo "[hoc-session-bootstrap] complete."
