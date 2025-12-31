# SCE Registry Hints

**Generated:** 2025-12-31T20:24:08.479432+00:00
**Status:** NON-AUTHORITATIVE - Do NOT apply automatically
**Reference:** SCE_CONTRACT.yaml

---

## Candidate Signals

These patterns LOOK like signals but may not be. Confidence = LOW until human-ratified.

| Pattern | File | Severity |
|---------|------|----------|
| call to get_publisher matches signal pat | backend/app/main.py | HIGH |
| call to send_response matches signal pat | backend/tests/test_m10_outbox_e2e.py | MEDIUM |
| call to send_response matches signal pat | backend/tests/test_m10_outbox_e2e.py | MEDIUM |
| call to send_response matches signal pat | backend/tests/test_m10_outbox_e2e.py | MEDIUM |
| call to send_response matches signal pat | backend/tests/test_m10_outbox_e2e.py | MEDIUM |
| call to send_header matches signal patte | backend/tests/test_m10_outbox_e2e.py | MEDIUM |
| call to LoggingPublisher matches signal  | backend/tests/test_worker_pool.py | HIGH |
| call to publish matches signal pattern | backend/tests/test_worker_pool.py | HIGH |
| call to get_publisher matches signal pat | backend/tests/test_worker_pool.py | HIGH |
| call to EventEmitter matches signal patt | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to EventEmitter matches signal patt | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit_api_call matches signal pat | backend/tests/test_m24_ops_console.py | HIGH |
| call to EventEmitter matches signal patt | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit_llm_call matches signal pat | backend/tests/test_m24_ops_console.py | HIGH |
| call to EventEmitter matches signal patt | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to EventEmitter matches signal patt | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to EventEmitter matches signal patt | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m24_ops_console.py | HIGH |
| call to IntentEmitter matches signal pat | backend/tests/test_m20_runtime.py | HIGH |
| call to IntentEmitter matches signal pat | backend/tests/test_m20_runtime.py | HIGH |
| call to IntentEmitter matches signal pat | backend/tests/test_m20_runtime.py | HIGH |
| call to IntentEmitter matches signal pat | backend/tests/test_m20_runtime.py | HIGH |
| call to emit matches signal pattern | backend/tests/test_m20_runtime.py | HIGH |
| call to get_emitted matches signal patte | backend/tests/test_m20_runtime.py | HIGH |

---

## Candidate Gaps

These signals are DECLARED but no mechanical evidence was found.

| Signal | File | Severity |
|--------|------|----------|
| Track when policies cause harm (Gate 2) | backend/alembic/versions/043_m25_learning_proof.py | MEDIUM |
| - SEMANTIC_DRIFT | scripts/ops/sce/passes/pass_4_diff.py | MEDIUM |
| ) | scripts/ops/sce/passes/pass_2_metadata.py | MEDIUM |
| Dict from analyze_output() | budgetllm/core/output_analysis.py | MEDIUM |
| Dict from analyze_output() | budgetllm/core/risk_formula.py | MEDIUM |
| Dict from analyze_output() | budgetllm/core/safety.py | MEDIUM |

---

## Candidate Drift

These signals show direction or boundary mismatches.

*No drift candidates found.*

---

## Important

This file is **NOT applied automatically**.

Human review is required before:
- Adding signals to CI_SIGNAL_REGISTRY.md
- Closing any gaps
- Modifying any code
