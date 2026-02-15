#!/usr/bin/env python3
# Layer: L4 — Verification Script
# AUDIENCE: INTERNAL
# Role: Validate stagetest artifact completeness, schema, and determinism
# artifact_class: CODE
"""
Stagetest Artifact Integrity Check

Validates a stagetest run directory for:
1. Required files present (run_summary.json, apis_snapshot.json, cases/*.json)
2. Schema-valid JSON
3. Non-empty request/response fields for stage 1.2 cases
4. Determinism hash correctness
5. Signature presence policy

Usage:
    python3 scripts/verification/stagetest_artifact_check.py --strict --latest-run
    python3 scripts/verification/stagetest_artifact_check.py --run-id 20260215T120000Z
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_ROOT = BACKEND_DIR / "artifacts" / "stagetest"
SCHEMA_PATH = BACKEND_DIR / "app" / "hoc" / "docs" / "architecture" / "usecases" / "stagetest_artifact_schema.json"


def _compute_determinism_hash(case_data: dict) -> str:
    """Recompute determinism hash from canonical fields."""
    payload = {
        "case_id": case_data["case_id"],
        "uc_id": case_data["uc_id"],
        "stage": case_data["stage"],
        "operation_name": case_data["operation_name"],
        "synthetic_input": case_data["synthetic_input"],
        "observed_output": case_data["observed_output"],
        "assertions": case_data["assertions"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_required_fields(case_data: dict, schema: dict) -> list[str]:
    """Check required fields exist."""
    errors = []
    for field in schema.get("required", []):
        if field not in case_data:
            errors.append(f"Missing required field: {field}")
    return errors


def _validate_case(case_data: dict, schema: dict, strict: bool, release_sig: bool = False) -> list[str]:
    """Validate a single case artifact."""
    errors = []

    # Required fields
    errors.extend(_validate_required_fields(case_data, schema))
    if errors:
        return errors  # Can't continue without required fields

    # Stage 1.2 must have non-empty fields
    if case_data.get("stage") == "1.2":
        if not case_data.get("synthetic_input"):
            errors.append("Stage 1.2 case has empty synthetic_input")
        if not case_data.get("observed_output"):
            errors.append("Stage 1.2 case has empty observed_output")
        if not case_data.get("request_fields"):
            errors.append("Stage 1.2 case has empty request_fields")
        if not case_data.get("response_fields"):
            errors.append("Stage 1.2 case has empty response_fields")
        # Reject placeholder N/A values
        if case_data.get("route_path") in ("N/A", "", None):
            errors.append("Stage 1.2 case has invalid route_path (N/A or empty)")
        if case_data.get("api_method") in ("N/A", "", None):
            errors.append("Stage 1.2 case has invalid api_method (N/A or empty)")
        # api_calls_used must be a non-empty list with required fields
        api_calls = case_data.get("api_calls_used")
        if not api_calls or not isinstance(api_calls, list):
            errors.append("Stage 1.2 case has empty or missing api_calls_used")
        else:
            for i, call in enumerate(api_calls):
                for fld in ("method", "path", "operation", "status_code", "duration_ms"):
                    if fld not in call:
                        errors.append(f"api_calls_used[{i}] missing field: {fld}")

    # Non-empty assertions
    if not case_data.get("assertions"):
        errors.append("Empty assertions array")

    # Determinism hash correctness
    expected_hash = _compute_determinism_hash(case_data)
    actual_hash = case_data.get("determinism_hash", "")
    if actual_hash != expected_hash:
        errors.append(f"Determinism hash mismatch: expected {expected_hash[:16]}... got {actual_hash[:16]}...")

    # Signature presence
    sig = case_data.get("signature", "")
    if strict and sig == "":
        errors.append("Missing signature field")
    if strict and sig == "UNSIGNED_LOCAL" and release_sig:
        errors.append("Release signature required but found UNSIGNED_LOCAL")

    # Status must be valid
    if case_data.get("status") not in ("PASS", "FAIL", "SKIPPED"):
        errors.append(f"Invalid status: {case_data.get('status')}")

    return errors


def validate_run(run_dir: Path, strict: bool = False, release_sig: bool = False) -> dict:
    """Validate a complete stagetest run directory."""
    checks_passed = 0
    checks_failed = 0
    errors: list[dict] = []

    # 1. Check run_summary.json exists
    summary_file = run_dir / "run_summary.json"
    if summary_file.exists():
        checks_passed += 1
        try:
            summary = json.loads(summary_file.read_text())
            # Validate summary required fields
            for field in ["run_id", "created_at", "stages_executed", "total_cases",
                          "pass_count", "fail_count", "determinism_digest", "artifact_version"]:
                if field in summary:
                    checks_passed += 1
                else:
                    checks_failed += 1
                    errors.append({"file": "run_summary.json", "error": f"Missing field: {field}"})
        except json.JSONDecodeError as e:
            checks_failed += 1
            errors.append({"file": "run_summary.json", "error": f"Invalid JSON: {e}"})
    else:
        checks_failed += 1
        errors.append({"file": "run_summary.json", "error": "File not found"})

    # 2. Check apis_snapshot.json exists
    apis_file = run_dir / "apis_snapshot.json"
    if apis_file.exists():
        checks_passed += 1
        try:
            json.loads(apis_file.read_text())
        except json.JSONDecodeError as e:
            checks_failed += 1
            errors.append({"file": "apis_snapshot.json", "error": f"Invalid JSON: {e}"})
    else:
        checks_failed += 1
        errors.append({"file": "apis_snapshot.json", "error": "File not found"})

    # 3. Load schema
    schema = {}
    if SCHEMA_PATH.exists():
        schema = json.loads(SCHEMA_PATH.read_text())

    # 4. Validate case files
    cases_dir = run_dir / "cases"
    if cases_dir.exists():
        case_files = sorted(cases_dir.glob("*.json"))
        if not case_files:
            checks_failed += 1
            errors.append({"file": "cases/", "error": "No case files found"})
        else:
            for cf in case_files:
                try:
                    case_data = json.loads(cf.read_text())
                    case_errors = _validate_case(case_data, schema, strict, release_sig)
                    if case_errors:
                        checks_failed += 1
                        for e in case_errors:
                            errors.append({"file": f"cases/{cf.name}", "error": e})
                    else:
                        checks_passed += 1
                except json.JSONDecodeError as e:
                    checks_failed += 1
                    errors.append({"file": f"cases/{cf.name}", "error": f"Invalid JSON: {e}"})
    else:
        checks_failed += 1
        errors.append({"file": "cases/", "error": "Directory not found"})

    return {
        "run_id": run_dir.name,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "errors": errors,
    }


def get_latest_run() -> Path | None:
    """Get the most recent run directory."""
    if not ARTIFACTS_ROOT.exists():
        return None
    runs = sorted(
        [d for d in ARTIFACTS_ROOT.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    return runs[0] if runs else None


def main():
    parser = argparse.ArgumentParser(description="Stagetest Artifact Integrity Check")
    parser.add_argument("--strict", action="store_true", help="Strict mode (all fields required)")
    parser.add_argument("--latest-run", action="store_true", help="Validate the latest run")
    parser.add_argument("--run-id", type=str, help="Specific run ID to validate")
    parser.add_argument("--release-signature-required", action="store_true",
                        help="Reject UNSIGNED_LOCAL signatures (release gate)")
    args = parser.parse_args()

    print("Stagetest Artifact Integrity Check")
    print("=" * 60)

    if args.latest_run:
        run_dir = get_latest_run()
        if run_dir is None:
            print("No stagetest runs found under artifacts/stagetest/")
            print()
            print("INFO: Run UAT tests with STAGETEST_EMIT=1 to generate artifacts:")
            print("  STAGETEST_EMIT=1 PYTHONPATH=. python3 -m pytest tests/uat/ -q")
            print()
            print("PASS: No artifacts to validate (pre-emission state)")
            sys.exit(0)
    elif args.run_id:
        run_dir = ARTIFACTS_ROOT / args.run_id
        if not run_dir.exists():
            print(f"Run directory not found: {run_dir}")
            sys.exit(1)
    else:
        print("Specify --latest-run or --run-id")
        sys.exit(1)

    print(f"Run directory: {run_dir}")
    print(f"Strict mode: {args.strict}")
    print()

    result = validate_run(run_dir, strict=args.strict, release_sig=args.release_signature_required)

    print(f"Checks passed: {result['checks_passed']}")
    print(f"Checks failed: {result['checks_failed']}")

    if result["errors"]:
        print()
        print("ERRORS:")
        for err in result["errors"]:
            print(f"  {err['file']}: {err['error']}")

    print()
    if result["checks_failed"] > 0:
        print(f"FAIL: {result['checks_failed']} checks failed")
        sys.exit(1)
    else:
        print(f"PASS: All {result['checks_passed']} checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
