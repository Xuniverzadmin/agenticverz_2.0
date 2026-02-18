#!/usr/bin/env bash
set -euo pipefail

# capability_id: CAP-CUS-ACT-RUNS-REALDATA-PR2
# PR2 verification harness for activity runs auth-path rollout.
# Captures stagetest evidence for live/completed endpoints with and without fixture headers.

BASE_URL="${1:-https://stagetest.agenticverz.com}"
AUTH_COOKIE="${AUTH_COOKIE:-}"
OUT_DIR="${OUT_DIR:-artifacts/pr2_runs_rollout}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="${OUT_DIR}/pr2_runs_rollout_${TS}.md"

mkdir -p "${OUT_DIR}"

run_probe() {
  local name="$1"
  local url="$2"
  local header_name="${3:-}"
  local header_value="${4:-}"
  local cookie="${5:-}"

  local body_file="${OUT_DIR}/${name}_${TS}.body"
  local headers_file="${OUT_DIR}/${name}_${TS}.headers"

  local -a args
  args=( -ksS -D "${headers_file}" -o "${body_file}" -w "%{http_code} %{content_type}" )
  if [[ -n "${header_name}" && -n "${header_value}" ]]; then
    args+=( -H "${header_name}: ${header_value}" )
  fi
  if [[ -n "${cookie}" ]]; then
    args+=( -H "Cookie: ${cookie}" )
  fi
  args+=( "${url}" )

  local result
  result="$(curl "${args[@]}")"
  local code content_type
  code="${result%% *}"
  content_type="${result#* }"

  {
    echo "### ${name}"
    echo "- URL: \`${url}\`"
    if [[ -n "${header_name}" && -n "${header_value}" ]]; then
      echo "- Header: \`${header_name}: ${header_value}\`"
    else
      echo "- Header: none"
    fi
    if [[ -n "${cookie}" ]]; then
      echo "- Cookie: provided"
    else
      echo "- Cookie: none"
    fi
    echo "- HTTP: ${code}"
    echo "- Content-Type: ${content_type}"
    echo "- Response excerpt:"
    echo '```json'
    sed -n '1,40p' "${body_file}"
    echo '```'
    echo
  } >> "${OUT_FILE}"
}

{
  echo "# PR2 Runs Auth Rollout Verification"
  echo
  echo "- capability_id: \`CAP-CUS-ACT-RUNS-REALDATA-PR2\`"
  echo "- generated_at_utc: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  echo "- base_url: \`${BASE_URL}\`"
  echo
} > "${OUT_FILE}"

LIVE_URL="${BASE_URL}/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0"
COMPLETED_URL="${BASE_URL}/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0"

run_probe "live_no_header" "${LIVE_URL}"
run_probe "completed_no_header" "${COMPLETED_URL}"
run_probe "live_with_fixture_header" "${LIVE_URL}" "X-HOC-Scaffold-Fixture" "pr1-runs-live-v1"
run_probe "completed_with_fixture_header" "${COMPLETED_URL}" "X-HOC-Scaffold-Fixture" "pr1-runs-completed-v1"

if [[ -n "${AUTH_COOKIE}" ]]; then
  run_probe "live_authenticated" "${LIVE_URL}" "" "" "${AUTH_COOKIE}"
  run_probe "completed_authenticated" "${COMPLETED_URL}" "" "" "${AUTH_COOKIE}"
fi

echo "Wrote ${OUT_FILE}"
