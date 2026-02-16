#!/bin/bash
# BA-02 — Unified Business Assurance Gatepack
#
# CI entrypoint that runs the full suite of business assurance gates
# in sequence. Each gate is executed independently; failures are tallied
# and reported in a summary at the end. The script exits non-zero if
# any gate fails, making it suitable as a blocking CI step.
set -e

cd "$(dirname "$0")/../.."
export PYTHONPATH=.

PASS=0
FAIL=0
TOTAL=16

echo "============================================"
echo " BA-02  Business Assurance Gatepack"
echo " Gates: ${TOTAL}"
echo "============================================"
echo ""

# --- Gate 1/15 -----------------------------------------------------------
echo "=== [1/16] Business Invariants Tests ==="
if python3 -m pytest tests/governance/t5/test_business_invariants_runtime.py -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [1/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [1/16] FAIL ---"
fi
echo ""

# --- Gate 2/15 -----------------------------------------------------------
echo "=== [2/16] Operation Spec Validation ==="
if python3 scripts/verification/check_operation_specs.py --strict; then
    PASS=$((PASS+1))
    echo "--- [2/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [2/16] FAIL ---"
fi
echo ""

# --- Gate 3/15 -----------------------------------------------------------
echo "=== [3/16] Operation Spec Tests ==="
if python3 -m pytest tests/governance/t5/test_operation_specs_enforced.py -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [3/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [3/16] FAIL ---"
fi
echo ""

# --- Gate 4/15 -----------------------------------------------------------
echo "=== [4/16] Mutation Gate ==="
if python3 scripts/verification/run_mutation_gate.py --strict; then
    PASS=$((PASS+1))
    echo "--- [4/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [4/16] FAIL ---"
fi
echo ""

# --- Gate 5/15 -----------------------------------------------------------
echo "=== [5/16] Property-Based Tests ==="
if python3 -m pytest tests/property/ -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [5/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [5/16] FAIL ---"
fi
echo ""

# --- Gate 6/15 -----------------------------------------------------------
echo "=== [6/16] Differential Replay ==="
if python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay/; then
    PASS=$((PASS+1))
    echo "--- [6/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [6/16] FAIL ---"
fi
echo ""

# --- Gate 7/15 -----------------------------------------------------------
echo "=== [7/16] Schema Drift Check ==="
if python3 scripts/verification/check_schema_drift.py --strict; then
    PASS=$((PASS+1))
    echo "--- [7/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [7/16] FAIL ---"
fi
echo ""

# --- Gate 8/15 -----------------------------------------------------------
echo "=== [8/16] Data Quality Check ==="
if python3 scripts/verification/check_data_quality.py --strict; then
    PASS=$((PASS+1))
    echo "--- [8/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [8/16] FAIL ---"
fi
echo ""

# --- Gate 9/15 -----------------------------------------------------------
echo "=== [9/16] Data Quality Tests ==="
if python3 -m pytest tests/verification/test_data_quality_gates.py -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [9/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [9/16] FAIL ---"
fi
echo ""

# --- Gate 10/15 ----------------------------------------------------------
echo "=== [10/16] Operation Ownership ==="
if python3 scripts/ci/check_operation_ownership.py --strict; then
    PASS=$((PASS+1))
    echo "--- [10/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [10/16] FAIL ---"
fi
echo ""

# --- Gate 11/15 ----------------------------------------------------------
echo "=== [11/16] Transaction Boundaries ==="
if python3 scripts/ci/check_transaction_boundaries.py --strict; then
    PASS=$((PASS+1))
    echo "--- [11/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [11/16] FAIL ---"
fi
echo ""

# --- Gate 12/15 ----------------------------------------------------------
echo "=== [12/16] Failure Injection Tests ==="
if python3 -m pytest tests/failure_injection/test_driver_fault_safety.py -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [12/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [12/16] FAIL ---"
fi
echo ""

# --- Gate 13/15 ----------------------------------------------------------
echo "=== [13/16] Incident Guardrail Linkage ==="
if python3 scripts/verification/check_incident_guardrail_linkage.py --strict; then
    PASS=$((PASS+1))
    echo "--- [13/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [13/16] FAIL ---"
fi
echo ""

# --- Gate 14/15 ----------------------------------------------------------
echo "=== [14/16] Incident Guardrail Tests ==="
if python3 -m pytest tests/governance/t5/test_incident_guardrail_linkage.py -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [14/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [14/16] FAIL ---"
fi
echo ""

# --- Gate 15/16 ----------------------------------------------------------
echo "=== [15/16] Differential Replay Tests ==="
if python3 -m pytest tests/verification/test_differential_replay.py -v --tb=short; then
    PASS=$((PASS+1))
    echo "--- [15/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [15/16] FAIL ---"
fi
echo ""

# --- Gate 16/16 ----------------------------------------------------------
echo "=== [16/16] CI Init Hygiene (Baseline) ==="
if python3 scripts/ci/check_init_hygiene.py --ci; then
    PASS=$((PASS+1))
    echo "--- [16/16] PASS ---"
else
    FAIL=$((FAIL+1))
    echo "--- [16/16] FAIL ---"
fi
echo ""

# --- Summary -------------------------------------------------------------
echo "============================================"
echo " BA-02  Gatepack Summary"
echo "============================================"
echo " Total gates : ${TOTAL}"
echo " Passed      : ${PASS}"
echo " Failed      : ${FAIL}"
echo "============================================"

if [ "${FAIL}" -gt 0 ]; then
    echo "RESULT: FAIL (${FAIL} gate(s) failed)"
    exit 1
else
    echo "RESULT: PASS (all ${TOTAL} gates passed)"
    exit 0
fi
